import argparse
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
from collections import deque
import math
import os
import time
import threading
import queue
from dataclasses import dataclass, field

from faceguard.config import load_config
from faceguard.profiling import Timer, FrameTimings, RunProfiler
from faceguard.services.inference_backend import create_inference_backend


UI_MODES = ("full", "min", "off")


def parse_args():
    parser = argparse.ArgumentParser(description="FaceGuard runtime")
    parser.add_argument("--config", type=str, default=None, help="Path to YAML configuration file")
    parser.add_argument("--record", action="store_true", help="Record processed session video + metrics")
    parser.add_argument("--replay", type=str, default=None, help="Replay from an existing video file")
    parser.add_argument("--no-ui", action="store_true", help="Disable OpenCV window rendering")
    parser.add_argument("--ui", choices=UI_MODES, default=None, help="UI rendering mode override: full|min|off")
    parser.add_argument("--outdir", type=str, default=None, help="Output directory for runs")
    parser.add_argument("--record-overlay", action="store_true", help="Record annotated frames instead of raw frames")
    parser.add_argument("--max-seconds", type=float, default=None, help="Maximum runtime duration in seconds")
    parser.add_argument("--fps-infer", type=float, default=None, help="Override inference fps scheduler")
    parser.add_argument("--replay-realtime", action="store_true", help="Throttle replay playback to real-time source clock")
    return parser.parse_args()


def make_run_id(prefix: str = "run"):
    return f"{prefix}_{time.strftime('%Y%m%d_%H%M%S')}"


def create_run_dir(outdir: str, replay_path: str | None):
    run_prefix = "replay" if replay_path else "run"
    run_id = make_run_id(run_prefix)
    run_dir = os.path.join(outdir, run_id)
    os.makedirs(run_dir, exist_ok=True)
    return run_id, run_dir


def clip_bbox_xywh(x: int, y: int, w: int, h: int, frame_w: int, frame_h: int):
    x = max(0, min(frame_w - 1, int(x)))
    y = max(0, min(frame_h - 1, int(y)))
    w = max(1, min(frame_w - x, int(w)))
    h = max(1, min(frame_h - y, int(h)))
    return x, y, w, h


def create_tracker(tracker_type: str):
    t = tracker_type.upper()

    def ctor_list(name: str):
        if name == "MOSSE":
            return [lambda: cv2.TrackerMOSSE_create(), lambda: cv2.legacy.TrackerMOSSE_create()]
        if name == "KCF":
            return [lambda: cv2.TrackerKCF_create(), lambda: cv2.legacy.TrackerKCF_create()]
        if name == "CSRT":
            return [lambda: cv2.TrackerCSRT_create(), lambda: cv2.legacy.TrackerCSRT_create()]
        return []

    order = ["MOSSE", "KCF"] if t == "MOSSE" else [t]
    for name in order:
        for ctor in ctor_list(name):
            try:
                return ctor()
            except Exception:
                continue
    return None


def get_head_pose(landmarks):
    nose_tip, left_cheek, right_cheek = landmarks[1], landmarks[454], landmarks[234]
    dist_left = abs(nose_tip.x - left_cheek.x)
    dist_right = abs(right_cheek.x - nose_tip.x)
    if dist_right == 0:
        return "PROFIL"
    ratio = dist_left / dist_right
    if ratio > 2.0:
        return "PROFIL_GAUCHE"
    if ratio < 0.5:
        return "PROFIL_DROIT"
    return "FACE"


def rotate_point(point, center, angle_rad):
    x, y, cx, cy = point[0], point[1], center[0], center[1]
    new_x = cx + (x - cx) * math.cos(angle_rad) - (y - cy) * math.sin(angle_rad)
    new_y = cy + (x - cx) * math.sin(angle_rad) + (y - cy) * math.cos(angle_rad)
    return new_x, new_y


def calculate_global_asymmetry(landmarks, w, h, symmetry_pairs):
    total_deviation = 0
    eye_l = (landmarks[33].x * w, landmarks[33].y * h)
    eye_r = (landmarks[263].x * w, landmarks[263].y * h)

    delta_x, delta_y = eye_r[0] - eye_l[0], eye_r[1] - eye_l[1]
    angle_rad = math.atan2(delta_y, delta_x)
    nose_pivot = (landmarks[1].x * w, landmarks[1].y * h)
    eye_dist = math.sqrt(delta_x**2 + delta_y**2)
    if eye_dist == 0:
        return 0

    for (idx_l, idx_r) in symmetry_pairs:
        pl_raw = (landmarks[idx_l].x * w, landmarks[idx_l].y * h)
        pr_raw = (landmarks[idx_r].x * w, landmarks[idx_r].y * h)
        pl = rotate_point(pl_raw, nose_pivot, -angle_rad)
        pr = rotate_point(pr_raw, nose_pivot, -angle_rad)

        height_diff = abs(pl[1] - pr[1])
        dist_l_x = abs(pl[0] - nose_pivot[0])
        dist_r_x = abs(pr[0] - nose_pivot[0])
        width_diff = abs(dist_l_x - dist_r_x)

        local_score = (width_diff + (height_diff * 1.5)) / eye_dist
        total_deviation += local_score

    return (total_deviation / len(symmetry_pairs)) * 100


def draw_transparent_box(image, x, y, w, h, alpha=0.6):
    overlay = image.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), (30, 30, 30), -1)
    return cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)


@dataclass
class PersonState:
    person_id: int
    bbox_xywh: tuple[int, int, int, int]
    last_seen_ts_ms: int
    tracker: object | None = None
    track_ok: bool = False
    missed_frames: int = 0
    preds_buffer: deque = field(default_factory=lambda: deque(maxlen=15))
    last_prediction: np.ndarray = field(default_factory=lambda: np.zeros(8, dtype=np.float32))
    threat_score: int = 0
    dom_emo: str = "SCANNING..."
    activation: float = 0.0
    pose_text: str = "INCONNU"
    valid_quality: bool = False
    infer_ran: bool = False
    is_asymmetric: bool = False
    next_infer_ts_ms: float | None = None


@dataclass
class PersonOverlay:
    person_id: int
    bbox: tuple[int, int, int, int] | None
    threat_score: int
    dom_emo: str
    pose_text: str
    valid_quality: bool
    infer_ran: bool
    track_ok: bool
    detect_ran: bool
    activation: float


@dataclass
class OverlayState:
    frame_idx: int = -1
    detect_ran: bool = False
    people: list[PersonOverlay] = field(default_factory=list)


class SharedState:
    def __init__(self):
        self._lock = threading.Lock()
        self.overlay = OverlayState()
        self.infer_count = 0
        self.capture_loop_ms: list[float] = []
        self.first_clock_ts_ms: int | None = None
        self.last_clock_ts_ms: int | None = None

    def update_overlay(self, overlay: OverlayState):
        with self._lock:
            self.overlay = overlay

    def get_overlay(self) -> OverlayState:
        with self._lock:
            return OverlayState(
                frame_idx=self.overlay.frame_idx,
                detect_ran=self.overlay.detect_ran,
                people=[
                    PersonOverlay(
                        person_id=p.person_id,
                        bbox=p.bbox,
                        threat_score=p.threat_score,
                        dom_emo=p.dom_emo,
                        pose_text=p.pose_text,
                        valid_quality=p.valid_quality,
                        infer_ran=p.infer_ran,
                        track_ok=p.track_ok,
                        detect_ran=p.detect_ran,
                        activation=p.activation,
                    ) for p in self.overlay.people
                ],
            )

    def inc_infer_count(self):
        with self._lock:
            self.infer_count += 1

    def get_infer_count(self) -> int:
        with self._lock:
            return self.infer_count

    def update_source_clock(self, clock_ts_ms: int):
        with self._lock:
            if self.first_clock_ts_ms is None:
                self.first_clock_ts_ms = int(clock_ts_ms)
            self.last_clock_ts_ms = int(clock_ts_ms)

    def get_source_duration_sec(self) -> float | None:
        with self._lock:
            if self.first_clock_ts_ms is None or self.last_clock_ts_ms is None:
                return None
            delta_ms = max(0, self.last_clock_ts_ms - self.first_clock_ts_ms)
            return delta_ms / 1000.0


def xywh_to_xyxy(bbox_xywh: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x, y, w, h = bbox_xywh
    return x, y, x + w, y + h


def iou_xywh(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax1, ay1, ax2, ay2 = xywh_to_xyxy(a)
    bx1, by1, bx2, by2 = xywh_to_xyxy(b)
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(1, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(1, (bx2 - bx1) * (by2 - by1))
    union = area_a + area_b - inter
    return float(inter / max(union, 1))


def centroid_distance_norm(
    a: tuple[int, int, int, int],
    b: tuple[int, int, int, int],
    image_diag: float,
) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    acx, acy = ax + aw / 2.0, ay + ah / 2.0
    bcx, bcy = bx + bw / 2.0, by + bh / 2.0
    dist = math.sqrt((acx - bcx) ** 2 + (acy - bcy) ** 2)
    return dist / max(image_diag, 1.0)


def smooth_bbox_xywh(
    old_bbox: tuple[int, int, int, int],
    new_bbox: tuple[int, int, int, int],
    alpha: float,
    frame_w: int,
    frame_h: int,
) -> tuple[int, int, int, int]:
    a = min(1.0, max(0.0, float(alpha)))
    ox, oy, ow, oh = old_bbox
    nx, ny, nw, nh = new_bbox
    sx = int(round(a * nx + (1.0 - a) * ox))
    sy = int(round(a * ny + (1.0 - a) * oy))
    sw = int(round(a * nw + (1.0 - a) * ow))
    sh = int(round(a * nh + (1.0 - a) * oh))
    return clip_bbox_xywh(sx, sy, sw, sh, frame_w, frame_h)


def bbox_from_landmarks(landmarks, work_w, work_h, img_w, img_h, scale_x, scale_y):
    x_vals = [l.x for l in landmarks]
    y_vals = [l.y for l in landmarks]
    x_min_w, x_max_w = max(0, int(min(x_vals) * work_w) - 10), min(work_w, int(max(x_vals) * work_w) + 10)
    y_min_w, y_max_w = max(0, int(min(y_vals) * work_h) - 20), min(work_h, int(max(y_vals) * work_h) + 10)
    x_min = max(0, min(img_w, int(x_min_w * scale_x)))
    x_max = max(0, min(img_w, int(x_max_w * scale_x)))
    y_min = max(0, min(img_h, int(y_min_w * scale_y)))
    y_max = max(0, min(img_h, int(y_max_w * scale_y)))
    bx, by, bw, bh = clip_bbox_xywh(x_min, y_min, max(1, x_max - x_min), max(1, y_max - y_min), img_w, img_h)
    return int(bx), int(by), int(bw), int(bh)


def associate_detections(
    detections: list[dict],
    people: dict[int, PersonState],
    iou_match_threshold: float,
    centroid_match_threshold: float,
    image_diag: float,
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    if not detections or not people:
        return [], list(range(len(detections))), list(people.keys())

    candidates = []
    for det_idx, det in enumerate(detections):
        db = det["bbox_xywh"]
        for person_id, person in people.items():
            pb = person.bbox_xywh  # bbox trackée courante
            iou_score = iou_xywh(db, pb)
            dist_norm = centroid_distance_norm(db, pb, image_diag)
            iou_ok = iou_score >= iou_match_threshold
            dist_ok = dist_norm <= centroid_match_threshold
            if iou_ok or dist_ok:
                # iou-first priority, then better IoU, then shorter centroid distance
                candidates.append((1 if iou_ok else 0, iou_score, -dist_norm, det_idx, person_id))

    candidates.sort(reverse=True)
    used_det = set()
    used_person = set()
    matches: list[tuple[int, int]] = []

    for _, _, _, det_idx, person_id in candidates:
        if det_idx in used_det or person_id in used_person:
            continue
        used_det.add(det_idx)
        used_person.add(person_id)
        matches.append((det_idx, person_id))

    unmatched_det = [i for i in range(len(detections)) if i not in used_det]
    unmatched_people = [pid for pid in people.keys() if pid not in used_person]
    return matches, unmatched_det, unmatched_people


print("\n" + "=" * 50)
print("🚀 DÉMARRAGE DE FACEGUARD V2.0 (SYSTÈME COMPLET) 🚀")
print("=" * 50 + "\n")

args = parse_args()
config = load_config(args.config)

if args.record and args.replay:
    raise SystemExit("❌ --record et --replay ne peuvent pas être utilisés ensemble.")
if args.replay and not os.path.exists(args.replay):
    raise SystemExit(f"❌ Fichier replay introuvable: {args.replay}")

config_ui_mode = str(config["ui"].get("mode", "full")).lower()
ui_mode = "off" if args.no_ui else (args.ui if args.ui else config_ui_mode)
if ui_mode not in UI_MODES:
    raise SystemExit(f"❌ Mode UI invalide: {ui_mode}. Valeurs supportées: {', '.join(UI_MODES)}")

run_outdir = args.outdir if args.outdir else config["runtime"]["outdir"]
run_id, run_dir = create_run_dir(run_outdir, args.replay)
metrics_path = os.path.join(run_dir, config["runtime"]["metrics_filename"])
video_path = os.path.join(run_dir, config["runtime"]["video_filename"])

MODEL_PATH = config["models"]["emotion_model_path"]
FACE_LANDMARKER_PATH = config["models"]["face_landmarker_path"]
EMOTION_CLASSES = config["emotion"]["classes"]
WORK_FRAME_ENABLED = bool(config.get("work_frame", {}).get("enabled", False))
WORK_FRAME_WIDTH = int(config.get("work_frame", {}).get("width", 640))
WORK_FRAME_HEIGHT = int(config.get("work_frame", {}).get("height", 360))

inference_cfg = config.get("inference", {})
infer_cfg_fps = args.fps_infer if args.fps_infer is not None else inference_cfg.get("fps", 8.0)
INFER_FPS = float(infer_cfg_fps) if infer_cfg_fps is not None else 0.0
INFER_ENABLED = INFER_FPS > 0.0
INFER_INTERVAL_MS = (1000.0 / INFER_FPS) if INFER_ENABLED else None
INFER_BACKEND = str(inference_cfg.get("backend", "keras")).lower()
TFLITE_MODEL_PATH = inference_cfg.get("tflite_model_path")
TFLITE_NUM_THREADS = int(inference_cfg.get("tflite_num_threads", 1))
INFER_WARMUP_RUNS = int(inference_cfg.get("warmup_runs", 0))

TRACKING_ENABLED = bool(config.get("tracking", {}).get("enabled", True))
tracking_cfg = config.get("tracking", {})
detect_every_ms_raw = tracking_cfg.get("detect_every_ms")
DETECT_EVERY_MS = float(detect_every_ms_raw) if detect_every_ms_raw is not None else None
if DETECT_EVERY_MS is not None and DETECT_EVERY_MS <= 0:
    DETECT_EVERY_MS = None
DETECT_EVERY_N_FRAMES = max(1, int(tracking_cfg.get("detect_every_n_frames", 15)))
TRACKER_TYPE = str(tracking_cfg.get("tracker_type", "MOSSE"))
MAX_MISSED_FRAMES = max(0, int(tracking_cfg.get("max_missed_frames", 30)))
MAX_FACES = max(1, int(tracking_cfg.get("max_faces", 2)))
TTL_MS = max(0, int(tracking_cfg.get("ttl_ms", 2000)))
IOU_MATCH_THRESHOLD = float(tracking_cfg.get("iou_match_threshold", 0.2))
CENTROID_MATCH_THRESHOLD = float(tracking_cfg.get("centroid_match_threshold", 0.15))
BBOX_SMOOTH_ALPHA = 0.6

print(f"[⏳] Initialisation backend inférence: {INFER_BACKEND}")
try:
    inference_engine = create_inference_backend(
        backend=INFER_BACKEND,
        keras_model_path=MODEL_PATH,
        tflite_model_path=TFLITE_MODEL_PATH,
        tflite_num_threads=TFLITE_NUM_THREADS,
    )
    engine_details = inference_engine.details()
    print(
        "[✅] Backend inférence prêt: "
        f"backend={engine_details.backend}, model={engine_details.model_path}, "
        f"input(shape={engine_details.input_shape}, dtype={engine_details.input_dtype}), "
        f"output(shape={engine_details.output_shape}, dtype={engine_details.output_dtype})"
    )
except Exception as e:
    raise SystemExit(f"[❌] ERREUR FATALE : Impossible d'initialiser le backend d'inférence.\n{e}")

if INFER_WARMUP_RUNS > 0:
    print(f"[⏳] Warmup backend inférence ({INFER_WARMUP_RUNS} runs)...")
    inference_engine.warmup(input_shape=(1, 48, 48, 3), runs=INFER_WARMUP_RUNS)

print("[⏳] Initialisation des capteurs géométriques...")
base_options = python.BaseOptions(model_asset_path=FACE_LANDMARKER_PATH)
options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=MAX_FACES)
detector = vision.FaceLandmarker.create_from_options(options)

clahe = cv2.createCLAHE(
    clipLimit=float(config["clahe"]["clip_limit"]),
    tileGridSize=tuple(config["clahe"]["tile_grid_size"]),
)

SYMMETRY_PAIRS = [
    (55, 285), (105, 334), (70, 300), (133, 362), (33, 263),
    (159, 386), (240, 460), (61, 291), (37, 267), (17, 314), (58, 288), (172, 397)
]

input_source = args.replay if args.replay else int(config["camera"]["index"])
max_seconds = args.max_seconds if args.max_seconds is not None else config["runtime"].get("max_seconds")
max_seconds = float(max_seconds) if max_seconds is not None else None

print("[✅] Démarrage de la caméra... (Appuyez sur ECHAP pour quitter)" if not args.replay else f"[✅] Replay vidéo: {args.replay}")
cap = cv2.VideoCapture(input_source)
if not args.replay:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(config["camera"]["width"]))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(config["camera"]["height"]))

replay_fps = cap.get(cv2.CAP_PROP_FPS) if args.replay else 0.0
if args.replay and (not replay_fps or replay_fps <= 0):
    replay_fps = 30.0

profiler = RunProfiler(output_path=metrics_path)
frame_queue: queue.Queue[tuple[int, int, int, float, np.ndarray]] = queue.Queue(maxsize=2)
shared_state = SharedState()
stop_event = threading.Event()
writer = None
interrupted = False
run_start = time.perf_counter()


def render_overlay(frame_raw: np.ndarray, overlay: OverlayState):
    frame_vis = frame_raw.copy()

    if ui_mode in ("full", "min"):
        for idx, person in enumerate(overlay.people):
            if person.bbox is None:
                continue
            x_min, y_min, x_max, y_max = person.bbox
            cv2.rectangle(frame_vis, (x_min, y_min), (x_max, y_max), (255, 255, 255), 1)
            label = f"ID {person.person_id} | {person.dom_emo} | TH {person.threat_score}"
            cv2.putText(frame_vis, label, (x_min, max(15, y_min - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

            if ui_mode == "full":
                y0 = min(frame_vis.shape[0] - 10, y_max + 18 + (idx * 40))
                cv2.putText(
                    frame_vis,
                    f"ID:{person.person_id} track:{'ok' if person.track_ok else 'ko'} detect:{'ran' if person.detect_ran else 'no'} p:{person.activation:5.1f}%",
                    (max(10, x_min), y0),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (180, 180, 180),
                    1,
                )

    if ui_mode == "min":
        cv2.putText(frame_vis, f"PEOPLE: {len(overlay.people)}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame_vis, f"DETECT: {'ran' if overlay.detect_ran else 'not'}", (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    return frame_vis


def processing_loop():
    people: dict[int, PersonState] = {}
    next_person_id = 1
    next_detect_ts_ms = None

    while not stop_event.is_set() or not frame_queue.empty():
        try:
            frame_ts_ms, frame_idx, clock_ts_ms, capture_ms, frame_raw = frame_queue.get(timeout=0.1)
            shared_state.update_source_clock(clock_ts_ms)
        except queue.Empty:
            continue

        frame_start = time.perf_counter()
        frame_timings = FrameTimings(ts_ms=frame_ts_ms, frame_idx=frame_idx)
        frame_timings.timings_ms["capture"] = capture_ms

        img_h, img_w, _ = frame_raw.shape
        if WORK_FRAME_ENABLED:
            work_frame = cv2.resize(frame_raw, (WORK_FRAME_WIDTH, WORK_FRAME_HEIGHT))
        else:
            work_frame = frame_raw
        work_h, work_w, _ = work_frame.shape
        scale_x = img_w / work_w
        scale_y = img_h / work_h

        detect_ran = False
        tracker_ran = False
        need_detect_reason = ""

        # purge TTL
        expired_ids = [pid for pid, p in people.items() if (clock_ts_ms - p.last_seen_ts_ms) > TTL_MS]
        for pid in expired_ids:
            people.pop(pid, None)

        need_detect = not TRACKING_ENABLED or len(people) == 0
        if not need_detect:
            if DETECT_EVERY_MS is not None:
                if next_detect_ts_ms is None:
                    next_detect_ts_ms = clock_ts_ms
                need_detect = clock_ts_ms >= next_detect_ts_ms
                if need_detect:
                    need_detect_reason = "periodic_ms"
            else:
                need_detect = (frame_idx % DETECT_EVERY_N_FRAMES == 0)
                if need_detect:
                    need_detect_reason = "periodic_frame"

        detections: list[dict] = []
        if need_detect:
            detect_ran = True
            with Timer(frame_timings.timings_ms, "mediapipe"):
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(work_frame, cv2.COLOR_BGR2RGB))
                res = detector.detect(mp_image)

            if DETECT_EVERY_MS is not None:
                next_detect_ts_ms = clock_ts_ms + DETECT_EVERY_MS

            for landmarks in (res.face_landmarks or [])[:MAX_FACES]:
                bbox_xywh = bbox_from_landmarks(landmarks, work_w, work_h, img_w, img_h, scale_x, scale_y)
                detections.append({"bbox_xywh": bbox_xywh, "landmarks": landmarks})

            image_diag = math.sqrt(float(img_w * img_w + img_h * img_h))
            matches, unmatched_det, _ = associate_detections(
                detections,
                people,
                IOU_MATCH_THRESHOLD,
                CENTROID_MATCH_THRESHOLD,
                image_diag,
            )
            for det_idx, person_id in matches:
                det = detections[det_idx]
                person = people[person_id]
                person.bbox_xywh = smooth_bbox_xywh(person.bbox_xywh, det["bbox_xywh"], BBOX_SMOOTH_ALPHA, img_w, img_h)
                person.last_seen_ts_ms = clock_ts_ms
                person.missed_frames = 0
                person.track_ok = True
                person.tracker = create_tracker(TRACKER_TYPE) if TRACKING_ENABLED else None
                if person.tracker is not None:
                    with Timer(frame_timings.timings_ms, "tracker"):
                        person.track_ok = person.tracker.init(frame_raw, tuple(int(v) for v in person.bbox_xywh))
                    tracker_ran = True

            if len(detections) == 1 and len(unmatched_det) > 1:
                unmatched_det = unmatched_det[:1]
            for det_idx in unmatched_det:
                det = detections[det_idx]
                preds_len = int(config["emotion"]["preds_buffer_maxlen"])
                person = PersonState(
                    person_id=next_person_id,
                    bbox_xywh=det["bbox_xywh"],
                    last_seen_ts_ms=clock_ts_ms,
                    preds_buffer=deque(maxlen=preds_len),
                    last_prediction=np.zeros(len(EMOTION_CLASSES), dtype=np.float32),
                )
                if TRACKING_ENABLED:
                    person.tracker = create_tracker(TRACKER_TYPE)
                    if person.tracker is not None:
                        with Timer(frame_timings.timings_ms, "tracker"):
                            person.track_ok = person.tracker.init(frame_raw, tuple(int(v) for v in person.bbox_xywh))
                        tracker_ran = True
                people[next_person_id] = person
                next_person_id += 1
        elif TRACKING_ENABLED:
            need_detect_reason = "track_only"
            for person in list(people.values()):
                if person.tracker is None:
                    person.track_ok = False
                    person.missed_frames += 1
                    continue
                with Timer(frame_timings.timings_ms, "tracker"):
                    ok, bbox = person.tracker.update(frame_raw)
                tracker_ran = True
                if ok:
                    x, y, w, h = clip_bbox_xywh(int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]), img_w, img_h)
                    person.bbox_xywh = smooth_bbox_xywh(person.bbox_xywh, (x, y, w, h), BBOX_SMOOTH_ALPHA, img_w, img_h)
                    person.track_ok = True
                    person.last_seen_ts_ms = clock_ts_ms
                    person.missed_frames = 0
                else:
                    person.track_ok = False
                    person.missed_frames += 1
                    if person.missed_frames > MAX_MISSED_FRAMES:
                        person.tracker = None

        # per-person inference/scoring
        people_payload = []
        overlays: list[PersonOverlay] = []
        for person_id in sorted(list(people.keys())):
            person = people[person_id]
            bbox_xywh = person.bbox_xywh
            x, y, w, h = bbox_xywh
            x_min, y_min, x_max, y_max = x, y, x + w, y + h

            person.valid_quality = False
            person.infer_ran = False
            person.pose_text = "INCONNU"
            person.is_asymmetric = False
            person.threat_score = 0

            # pose/asym only if we have detect landmarks this frame and matched person
            matched_landmarks = None
            if detect_ran:
                for det in detections:
                    if det["bbox_xywh"] == bbox_xywh:
                        matched_landmarks = det["landmarks"]
                        break
            if matched_landmarks is not None:
                person.pose_text = get_head_pose(matched_landmarks)
                if person.pose_text == "FACE":
                    asym_score = calculate_global_asymmetry(matched_landmarks, work_w, work_h, SYMMETRY_PAIRS)
                    if asym_score > float(config["asymmetry"]["threshold"]):
                        person.is_asymmetric = True
                        person.threat_score += 40

            x_min_w = max(0, min(work_w - 1, int(x_min / scale_x)))
            x_max_w = max(0, min(work_w, int(x_max / scale_x)))
            y_min_w = max(0, min(work_h - 1, int(y_min / scale_y)))
            y_max_w = max(0, min(work_h, int(y_max / scale_y)))

            if (x_max_w - x_min_w) > 40 and INFER_ENABLED:
                if person.next_infer_ts_ms is None:
                    person.next_infer_ts_ms = clock_ts_ms
                should_infer = clock_ts_ms >= person.next_infer_ts_ms
                if should_infer:
                    with Timer(frame_timings.timings_ms, "preprocess"):
                        face_crop = work_frame[y_min_w:y_max_w, x_min_w:x_max_w]
                        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
                        clahe_img = clahe.apply(gray)
                        final_input = cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2RGB)
                        ai_input = cv2.resize(final_input, (48, 48))
                        tensor = np.expand_dims(ai_input, axis=0)

                    with Timer(frame_timings.timings_ms, "infer"):
                        raw_preds = inference_engine.predict(tensor)

                    person.preds_buffer.append(raw_preds)
                    person.last_prediction = np.mean(person.preds_buffer, axis=0)
                    person.infer_ran = True
                    shared_state.inc_infer_count()
                    person.next_infer_ts_ms = clock_ts_ms + INFER_INTERVAL_MS

                person.valid_quality = True

            if len(person.preds_buffer) > 0:
                top_2_idx = person.last_prediction.argsort()[-2:][::-1]
                person.dom_emo = EMOTION_CLASSES[top_2_idx[0]]
                person.activation = float(person.last_prediction[top_2_idx[0]] * 100)
                if person.dom_emo in ['ANGRY', 'CONTEMPT']:
                    person.threat_score += int(config["threat"]["angry_contempt_bonus"])
                if person.dom_emo in ['FEAR']:
                    person.threat_score += int(config["threat"]["fear_bonus"])

            people_payload.append(
                {
                    "id": int(person.person_id),
                    "bbox": list(person.bbox_xywh),
                    "track_ok": bool(person.track_ok),
                    "threat_score": int(person.threat_score),
                    "emotion_top1": person.dom_emo,
                    "emotion_p": float(person.activation / 100.0),
                    "infer_ran": bool(person.infer_ran),
                    "valid_quality": bool(person.valid_quality),
                }
            )
            overlays.append(
                PersonOverlay(
                    person_id=int(person.person_id),
                    bbox=(x_min, y_min, x_max, y_max),
                    threat_score=int(person.threat_score),
                    dom_emo=person.dom_emo,
                    pose_text=person.pose_text,
                    valid_quality=person.valid_quality,
                    infer_ran=person.infer_ran,
                    track_ok=person.track_ok,
                    detect_ran=detect_ran,
                    activation=float(person.activation),
                )
            )

        frame_timings.timings_ms["total"] = (time.perf_counter() - frame_start) * 1000.0
        frame_timings.timings_ms["total_processing"] = frame_timings.timings_ms["total"]
        frame_timings.has_face = len(people) > 0
        frame_timings.detect_ran = detect_ran
        frame_timings.tracker_ran = tracker_ran
        frame_timings.track_ok = any(p.track_ok for p in people.values())
        frame_timings.need_detect_reason = need_detect_reason
        frame_timings.detect_every_ms = DETECT_EVERY_MS
        if overlays:
            top_person = max(overlays, key=lambda p: p.threat_score)
            frame_timings.bbox = list(people[top_person.person_id].bbox_xywh)
            frame_timings.pose = top_person.pose_text
            frame_timings.valid_quality = top_person.valid_quality
            frame_timings.infer_ran = any(p.infer_ran for p in overlays)
            frame_timings.emotion_top1 = top_person.dom_emo
            frame_timings.emotion_p = top_person.activation / 100.0
            frame_timings.threat_score = top_person.threat_score
        frame_timings.people = people_payload
        profiler.write_frame(frame_timings)

        shared_state.update_overlay(OverlayState(frame_idx=frame_idx, detect_ran=detect_ran, people=overlays))


def capture_loop():
    nonlocal_writer = {"writer": None}
    frame_idx = 0
    prev_replay_clock_ts_ms = None
    last_replay_wall_ts = None

    while cap.isOpened() and not stop_event.is_set():
        capture_loop_start = time.perf_counter()
        if max_seconds is not None and (time.perf_counter() - run_start) >= max_seconds:
            print(f"[ℹ️] Durée max atteinte ({max_seconds:.2f}s). Arrêt propre.")
            stop_event.set()
            break

        cap_t0 = time.perf_counter()
        success, frame_raw = cap.read()
        capture_ms = (time.perf_counter() - cap_t0) * 1000.0
        if not success:
            stop_event.set()
            break

        if not args.replay:
            frame_raw = cv2.flip(frame_raw, 1)

        frame_ts_ms = int(time.time() * 1000)
        if args.replay:
            pos_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
            if pos_msec and pos_msec > 0:
                clock_ts_ms = int(pos_msec)
            else:
                clock_ts_ms = int((frame_idx / replay_fps) * 1000.0)

            if args.replay_realtime:
                now_wall = time.perf_counter()
                if prev_replay_clock_ts_ms is not None and last_replay_wall_ts is not None:
                    source_delta_s = max(0.0, (clock_ts_ms - prev_replay_clock_ts_ms) / 1000.0)
                    target_wall_ts = last_replay_wall_ts + source_delta_s
                    sleep_s = target_wall_ts - now_wall
                    if sleep_s > 0:
                        time.sleep(sleep_s)
                last_replay_wall_ts = time.perf_counter()
                prev_replay_clock_ts_ms = clock_ts_ms
        else:
            clock_ts_ms = int(time.time() * 1000.0)

        try:
            frame_queue.put_nowait((frame_ts_ms, frame_idx, clock_ts_ms, capture_ms, frame_raw.copy()))
        except queue.Full:
            # Politique: drop oldest pour conserver la frame la plus récente et minimiser la latence UI.
            try:
                _ = frame_queue.get_nowait()
            except queue.Empty:
                pass
            frame_queue.put_nowait((frame_ts_ms, frame_idx, clock_ts_ms, capture_ms, frame_raw.copy()))

        overlay = shared_state.get_overlay()
        frame_vis = render_overlay(frame_raw, overlay)

        if args.record:
            if nonlocal_writer["writer"] is None:
                img_h, img_w, _ = frame_raw.shape
                fps = cap.get(cv2.CAP_PROP_FPS)
                if not fps or fps <= 0:
                    fps = 30.0
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                nonlocal_writer["writer"] = cv2.VideoWriter(video_path, fourcc, fps, (img_w, img_h))
            nonlocal_writer["writer"].write(frame_vis if args.record_overlay else frame_raw)

        if ui_mode != "off":
            cv2.imshow(config["ui"]["window_name"], frame_vis)
            if (cv2.waitKey(1) & 0xFF) == 27:
                stop_event.set()
                break

        frame_idx += 1
        shared_state.capture_loop_ms.append((time.perf_counter() - capture_loop_start) * 1000.0)

    writer_obj = nonlocal_writer["writer"]
    return writer_obj


writer_holder = {"writer": None}


def capture_runner():
    writer_holder["writer"] = capture_loop()


processing_thread = threading.Thread(target=processing_loop, name="processing", daemon=True)
capture_thread = threading.Thread(target=capture_runner, name="capture_ui", daemon=True)

try:
    processing_thread.start()
    capture_thread.start()

    while capture_thread.is_alive() or processing_thread.is_alive():
        time.sleep(0.05)
        if stop_event.is_set() and not capture_thread.is_alive():
            break
except KeyboardInterrupt:
    interrupted = True
    print("\n[ℹ️] Interruption clavier reçue (CTRL-C). Arrêt propre en cours...")
    stop_event.set()
finally:
    stop_event.set()
    capture_thread.join(timeout=3.0)
    processing_thread.join(timeout=5.0)
    cap.release()
    writer = writer_holder["writer"]
    if writer is not None:
        writer.release()
    if ui_mode != "off":
        cv2.destroyAllWindows()
    profiler.print_summary()
    profiler.close()

source_duration_sec = shared_state.get_source_duration_sec()
run_duration_sec = source_duration_sec if source_duration_sec is not None and source_duration_sec > 0 else max(time.perf_counter() - run_start, 1e-9)
infer_count = shared_state.get_infer_count()
effective_infer_fps = infer_count / max(run_duration_sec, 1e-9)

print(f"[✅] Run ID: {run_id}")
print(f"[✅] Metrics: {metrics_path}")
if writer_holder["writer"] is not None:
    mode = "overlay" if args.record_overlay else "raw"
    print(f"[✅] Video: {video_path} ({mode})")
if interrupted:
    print("[✅] Run interrompu proprement.")
print(f"[✅] infer_count: {infer_count}")
print(f"[✅] duration_sec: {run_duration_sec:.2f}")
if source_duration_sec is not None:
    print(f"[✅] source_duration_sec: {source_duration_sec:.2f}")
print(f"[✅] effective_infer_fps: {effective_infer_fps:.2f}")
print(f"[✅] fps_infer_config: {INFER_FPS:.2f}")
