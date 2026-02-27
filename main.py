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
class OverlayState:
    frame_idx: int = -1
    has_face: bool = False
    bbox: tuple[int, int, int, int] | None = None
    dom_emo: str = "SCANNING..."
    threat_score: int = 0
    pose_text: str = "INCONNU"
    valid_quality: bool = False
    infer_ran: bool = False
    detect_ran: bool = False
    track_ok: bool = False
    last_prediction: np.ndarray = field(default_factory=lambda: np.zeros(8, dtype=np.float32))
    is_asymmetric: bool = False


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
                has_face=self.overlay.has_face,
                bbox=self.overlay.bbox,
                dom_emo=self.overlay.dom_emo,
                threat_score=self.overlay.threat_score,
                pose_text=self.overlay.pose_text,
                valid_quality=self.overlay.valid_quality,
                infer_ran=self.overlay.infer_ran,
                detect_ran=self.overlay.detect_ran,
                track_ok=self.overlay.track_ok,
                last_prediction=np.array(self.overlay.last_prediction, copy=True),
                is_asymmetric=self.overlay.is_asymmetric,
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
options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)
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
    img_h, img_w, _ = frame_vis.shape
    bbox = overlay.bbox
    if ui_mode in ("full", "min") and bbox is not None:
        x_min, y_min, x_max, y_max = bbox
        cv2.rectangle(frame_vis, (x_min, y_min), (x_max, y_max), (255, 255, 255), 1)

    if ui_mode == "full":
        if bbox is not None and overlay.last_prediction.size > 0:
            x_min, y_min, x_max, y_max = bbox
            display_order = ['NEUTRAL', 'HAPPY', 'SURPRISE', 'ANGRY', 'DISGUST', 'FEAR', 'SAD', 'CONTEMPT']
            forehead_x = x_min + (x_max - x_min) // 2
            forehead_y = y_min
            box_right_x = min(x_max + 30, img_w - 200)
            box_right_y = max(30, y_min - 20)
            cv2.line(frame_vis, (forehead_x, forehead_y), (box_right_x, box_right_y), (255, 255, 255), 1)
            frame_vis = draw_transparent_box(frame_vis, box_right_x, box_right_y, 200, 180, alpha=0.5)
            y_offset = box_right_y + 20
            for emo in display_order:
                idx = EMOTION_CLASSES.index(emo)
                score = overlay.last_prediction[idx] * 100
                thickness = 2 if emo == overlay.dom_emo else 1
                color = (255, 255, 255) if emo == overlay.dom_emo else (180, 180, 180)
                cv2.putText(frame_vis, f"{emo:<10} {score:5.2f}%", (box_right_x + 10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, thickness)
                y_offset += 20

            box_left_x = max(10, x_min - 220)
            box_left_y = max(30, y_min + 50)
            ts_color = (0, 255, 0)
            if overlay.threat_score >= 40:
                ts_color = (0, 165, 255)
            if overlay.threat_score >= 70:
                ts_color = (0, 0, 255)
            frame_vis = draw_transparent_box(frame_vis, box_left_x, box_left_y, 200, 110, alpha=0.6)
            cv2.line(frame_vis, (box_left_x, box_left_y + 25), (box_left_x + 200, box_left_y + 25), (200, 200, 200), 1)
            cv2.putText(frame_vis, f"{overlay.dom_emo}", (box_left_x + 10, box_left_y + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame_vis, f"THREAT SCORE: {overlay.threat_score}", (box_left_x + 10, box_left_y + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, ts_color, 2)
            if overlay.is_asymmetric:
                cv2.putText(frame_vis, "⚠️ ASYMETRIE", (box_left_x + 10, box_left_y + 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

        if overlay.threat_score >= 70:
            cv2.rectangle(frame_vis, (0, 0), (img_w, img_h), (0, 0, 255), 4)
            cv2.putText(frame_vis, "INTENTION HOSTILE DETECTEE", (img_w // 2 - 200, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    elif ui_mode == "min":
        cv2.putText(frame_vis, f"EMO: {overlay.dom_emo}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame_vis, f"THREAT: {overlay.threat_score}", (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame_vis, f"POSE: {overlay.pose_text}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame_vis, f"INFER_OK: {overlay.valid_quality}", (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame_vis, f"INFER_RAN: {overlay.infer_ran}", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame_vis, f"TRACK: {'ok' if overlay.track_ok else 'failed'}", (20, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame_vis, f"DETECT: {'ran' if overlay.detect_ran else 'not'}", (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    return frame_vis


def processing_loop():
    preds_buffer = deque(maxlen=int(config["emotion"]["preds_buffer_maxlen"]))
    last_prediction = np.zeros(len(EMOTION_CLASSES), dtype=np.float32)
    next_infer_ts_ms = None
    next_detect_ts_ms = None
    tracker = None
    tracked_bbox = None
    missed_frames = 0
    last_track_ok = False

    while not stop_event.is_set() or not frame_queue.empty():
        try:
            frame_ts_ms, frame_idx, clock_ts_ms, capture_ms, frame_raw = frame_queue.get(timeout=0.1)
            shared_state.update_source_clock(clock_ts_ms)
        except queue.Empty:
            continue

        frame_start = time.perf_counter()
        frame_timings = FrameTimings(ts_ms=frame_ts_ms, frame_idx=frame_idx)
        frame_timings.timings_ms["capture"] = capture_ms

        frame_vis = frame_raw
        img_h, img_w, _ = frame_vis.shape

        if WORK_FRAME_ENABLED:
            work_frame = cv2.resize(frame_raw, (WORK_FRAME_WIDTH, WORK_FRAME_HEIGHT))
        else:
            work_frame = frame_raw

        work_h, work_w, _ = work_frame.shape
        scale_x = img_w / work_w
        scale_y = img_h / work_h

        detect_ran = False
        tracker_ran = False
        track_ok = False
        need_detect_reason = ""
        landmarks = None
        roi_bbox = None

        if TRACKING_ENABLED:
            missing_tracker = (tracker is None or tracked_bbox is None)
            too_many_missed = (missed_frames > MAX_MISSED_FRAMES)
            need_detect = missing_tracker or (not last_track_ok) or too_many_missed
            if missing_tracker:
                need_detect_reason = "no_tracker"
            elif not last_track_ok:
                need_detect_reason = "track_not_ok"
            elif too_many_missed:
                need_detect_reason = "missed_limit"

            if not need_detect:
                if DETECT_EVERY_MS is not None:
                    if next_detect_ts_ms is None:
                        next_detect_ts_ms = clock_ts_ms
                    if clock_ts_ms >= next_detect_ts_ms:
                        need_detect = True
                        need_detect_reason = "periodic_ms"
                else:
                    periodic_due = (frame_idx % DETECT_EVERY_N_FRAMES == 0)
                    if periodic_due:
                        need_detect = True
                        need_detect_reason = "periodic_frame"

            if not need_detect:
                need_detect_reason = "track_only"
                roi_bbox = tracked_bbox
                with Timer(frame_timings.timings_ms, "tracker"):
                    ok, bbox = tracker.update(frame_raw)
                tracker_ran = True

                if ok:
                    x, y, w, h = clip_bbox_xywh(int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]), img_w, img_h)
                    tracked_bbox = (x, y, w, h)
                    roi_bbox = tracked_bbox
                    track_ok = True
                    missed_frames = 0
                else:
                    track_ok = False
                    missed_frames += 1
                    need_detect = True
                    need_detect_reason = "track_failed"
                    tracker = None

            if need_detect:
                detect_ran = True
                with Timer(frame_timings.timings_ms, "mediapipe"):
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(work_frame, cv2.COLOR_BGR2RGB))
                    res = detector.detect(mp_image)
                if DETECT_EVERY_MS is not None:
                    next_detect_ts_ms = clock_ts_ms + DETECT_EVERY_MS

                if res.face_landmarks:
                    landmarks = res.face_landmarks[0]
                    x_vals = [l.x for l in landmarks]
                    y_vals = [l.y for l in landmarks]
                    x_min_w, x_max_w = max(0, int(min(x_vals) * work_w) - 10), min(work_w, int(max(x_vals) * work_w) + 10)
                    y_min_w, y_max_w = max(0, int(min(y_vals) * work_h) - 20), min(work_h, int(max(y_vals) * work_h) + 10)

                    x_min = max(0, min(img_w, int(x_min_w * scale_x)))
                    x_max = max(0, min(img_w, int(x_max_w * scale_x)))
                    y_min = max(0, min(img_h, int(y_min_w * scale_y)))
                    y_max = max(0, min(img_h, int(y_max_w * scale_y)))
                    bx, by, bw, bh = clip_bbox_xywh(x_min, y_min, max(1, x_max - x_min), max(1, y_max - y_min), img_w, img_h)
                    tracked_bbox = (int(bx), int(by), int(bw), int(bh))
                    roi_bbox = tracked_bbox

                    tracker = create_tracker(TRACKER_TYPE)
                    if tracker is not None:
                        with Timer(frame_timings.timings_ms, "tracker"):
                            track_ok = tracker.init(frame_raw, tuple(int(v) for v in tracked_bbox))
                        tracker_ran = True
                    else:
                        track_ok = False
                    missed_frames = 0
                else:
                    missed_frames += 1
                    if missed_frames > MAX_MISSED_FRAMES:
                        tracker = None
                        tracked_bbox = None
                    track_ok = False
            last_track_ok = track_ok
        else:
            need_detect_reason = "tracking_disabled"
            detect_ran = True
            with Timer(frame_timings.timings_ms, "mediapipe"):
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(work_frame, cv2.COLOR_BGR2RGB))
                res = detector.detect(mp_image)

            if res.face_landmarks:
                landmarks = res.face_landmarks[0]
                x_vals = [l.x for l in landmarks]
                y_vals = [l.y for l in landmarks]
                x_min_w, x_max_w = max(0, int(min(x_vals) * work_w) - 10), min(work_w, int(max(x_vals) * work_w) + 10)
                y_min_w, y_max_w = max(0, int(min(y_vals) * work_h) - 20), min(work_h, int(max(y_vals) * work_h) + 10)

                x_min = max(0, min(img_w, int(x_min_w * scale_x)))
                x_max = max(0, min(img_w, int(x_max_w * scale_x)))
                y_min = max(0, min(img_h, int(y_min_w * scale_y)))
                y_max = max(0, min(img_h, int(y_max_w * scale_y)))
                bx, by, bw, bh = clip_bbox_xywh(x_min, y_min, max(1, x_max - x_min), max(1, y_max - y_min), img_w, img_h)
                roi_bbox = (int(bx), int(by), int(bw), int(bh))
                tracked_bbox = None
                tracker = None
                track_ok = False
                missed_frames = 0
            else:
                tracked_bbox = None
                track_ok = False
                missed_frames += 1
            last_track_ok = False

        threat_score = 0
        dom_emo = "SCANNING..."
        activation = 0.0
        pose_text = "INCONNU"
        valid_quality = False
        infer_ran = False
        is_asymmetric = False

        x_min = y_min = x_max = y_max = None
        if roi_bbox is not None:
            bx, by, bw, bh = roi_bbox
            x_min, y_min = bx, by
            x_max, y_max = bx + bw, by + bh

        frame_timings.has_face = roi_bbox is not None

        if landmarks is not None:
            pose_text = get_head_pose(landmarks)
            if pose_text == "FACE":
                asym_score = calculate_global_asymmetry(landmarks, work_w, work_h, SYMMETRY_PAIRS)
                if asym_score > float(config["asymmetry"]["threshold"]):
                    is_asymmetric = True
                    threat_score += 40

        if roi_bbox is not None:
            x_min_w = max(0, min(work_w - 1, int(x_min / scale_x)))
            x_max_w = max(0, min(work_w, int(x_max / scale_x)))
            y_min_w = max(0, min(work_h - 1, int(y_min / scale_y)))
            y_max_w = max(0, min(work_h, int(y_max / scale_y)))

            if (x_max_w - x_min_w) > 40:
                if INFER_ENABLED:
                    if next_infer_ts_ms is None:
                        next_infer_ts_ms = clock_ts_ms
                    should_infer = clock_ts_ms >= next_infer_ts_ms
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

                        preds_buffer.append(raw_preds)
                        last_prediction = np.mean(preds_buffer, axis=0)
                        infer_ran = True
                        shared_state.inc_infer_count()
                        next_infer_ts_ms = clock_ts_ms + INFER_INTERVAL_MS

                    valid_quality = True

            if len(preds_buffer) > 0:
                top_2_idx = last_prediction.argsort()[-2:][::-1]
                dom_emo = EMOTION_CLASSES[top_2_idx[0]]
                activation = last_prediction[top_2_idx[0]] * 100
                if dom_emo in ['ANGRY', 'CONTEMPT']:
                    threat_score += int(config["threat"]["angry_contempt_bonus"])
                if dom_emo in ['FEAR']:
                    threat_score += int(config["threat"]["fear_bonus"])

        frame_timings.timings_ms["total"] = (time.perf_counter() - frame_start) * 1000.0
        frame_timings.timings_ms["total_processing"] = frame_timings.timings_ms["total"]
        frame_timings.pose = pose_text
        frame_timings.valid_quality = valid_quality
        frame_timings.infer_ran = infer_ran
        frame_timings.detect_ran = detect_ran
        frame_timings.tracker_ran = tracker_ran
        frame_timings.track_ok = track_ok
        frame_timings.need_detect_reason = need_detect_reason
        frame_timings.detect_every_ms = DETECT_EVERY_MS
        frame_timings.bbox = list(tracked_bbox) if tracked_bbox is not None else None
        frame_timings.emotion_top1 = dom_emo
        frame_timings.emotion_p = float(activation / 100.0)
        frame_timings.threat_score = int(threat_score)
        profiler.write_frame(frame_timings)

        overlay_bbox = (x_min, y_min, x_max, y_max) if roi_bbox is not None else None
        shared_state.update_overlay(
            OverlayState(
                frame_idx=frame_idx,
                has_face=roi_bbox is not None,
                bbox=overlay_bbox,
                dom_emo=dom_emo,
                threat_score=int(threat_score),
                pose_text=pose_text,
                valid_quality=valid_quality,
                infer_ran=infer_ran,
                detect_ran=detect_ran,
                track_ok=track_ok,
                last_prediction=np.array(last_prediction, copy=True),
                is_asymmetric=is_asymmetric,
            )
        )


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
