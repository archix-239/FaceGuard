import argparse
import os
import threading
import queue
import time
from collections import deque
from datetime import datetime

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.vision import RunningMode
import numpy as np
import tensorflow as tf

from faceguard.config import load_config
from faceguard.services.inference_backend import create_inference_backend


EMOTION_COLORS = {
    "ANGRY":    ( 30,  30, 230),
    "CONTEMPT": ( 80,  80,   0),
    "DISGUST":  (  0, 130,  80),
    "FEAR":     (150,   0, 200),
    "HAPPY":    (  0, 210,   0),
    "NEUTRAL":  (180, 180, 180),
    "SAD":      (180,  80,   0),
    "SURPRISE": (  0, 190, 255),
}

# Table FACS — AU attendues par émotion (Ekman & Friesen, Deramgozin2023 Table 3.1)
EMOTION_AUS = {
    "ANGRY":    "AU4+5+7+23",
    "CONTEMPT": "AU12+14",
    "DISGUST":  "AU9+15+17",
    "FEAR":     "AU1+2+4+5+7+20+26",
    "HAPPY":    "AU6+12",
    "NEUTRAL":  "—",
    "SAD":      "AU1+4+15",
    "SURPRISE": "AU1+2+5+26",
}

# MediaPipe 468-point mesh — eye corner indices
_L_EYE_INNER = 133
_L_EYE_OUTER = 33
_R_EYE_INNER = 362
_R_EYE_OUTER = 263


# ---------------------------------------------------------------------------
# Per-face state
# ---------------------------------------------------------------------------

class FaceTrack:
    """MOSSE tracker + EMA emotion smoothing for one face."""

    EMA_ALPHA = 0.35  # higher = more reactive, lower = smoother
    HISTORY_LEN = 10  # nombre de vecteurs de probabilités conservés

    def __init__(self, frame_gray: np.ndarray, bbox: tuple) -> None:
        self.bbox = bbox
        self.missed = 0
        self.last_landmarks = None
        self.quality: dict | None = None
        self.gradcam_map: np.ndarray | None = None
        self._smooth_probs: np.ndarray | None = None
        self.prob_history: deque = deque(maxlen=self.HISTORY_LEN)
        self._tracker = cv2.legacy.TrackerMOSSE.create()
        self._tracker.init(frame_gray, bbox)

    def reinit(self, frame_gray: np.ndarray, bbox: tuple, landmarks=None) -> None:
        self.bbox = bbox
        self.missed = 0
        if landmarks is not None:
            self.last_landmarks = landmarks
        self._tracker = cv2.legacy.TrackerMOSSE.create()
        self._tracker.init(frame_gray, bbox)

    def update(self, frame_gray: np.ndarray) -> bool:
        ok, raw = self._tracker.update(frame_gray)
        if ok:
            self.bbox = tuple(int(v) for v in raw)
        else:
            self.missed += 1
        return ok

    def add_prediction(self, probs: np.ndarray) -> None:
        if self._smooth_probs is None:
            self._smooth_probs = probs.copy()
        else:
            self._smooth_probs = (
                self.EMA_ALPHA * probs + (1.0 - self.EMA_ALPHA) * self._smooth_probs
            )
        self.prob_history.append(self._smooth_probs.copy())

    def dominant_emotion(self, emotion_classes: list) -> tuple:
        if self._smooth_probs is None:
            return None, 0.0
        idx = int(np.argmax(self._smooth_probs))
        return emotion_classes[idx], float(self._smooth_probs[idx])


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def landmarks_to_bbox(landmarks, w: int, h: int) -> tuple:
    xs = [lm.x * w for lm in landmarks]
    ys = [lm.y * h for lm in landmarks]
    x = max(0, int(min(xs)))
    y = max(0, int(min(ys)))
    bw = min(w - x, int(max(xs) - min(xs)))
    bh = min(h - y, int(max(ys) - min(ys)))
    return (x, y, bw, bh)


def bbox_iou(a: tuple, b: tuple) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix1, iy1 = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# Face quality assessment
# ---------------------------------------------------------------------------

def face_quality(frame_bgr: np.ndarray, landmarks, bbox: tuple) -> dict:
    """
    Évalue la qualité d'un visage détecté.
    Retourne un dict avec les scores individuels et un score global [0, 1].
    """
    h, w = frame_bgr.shape[:2]
    _, _, bw, bh = bbox

    # 1. Taille minimale — bbox trop petite = détails insuffisants
    min_dim = min(bw, bh)
    size_score = min(1.0, min_dim / 64.0)

    # 2. Angle inter-oculaire — rotation excessive = mauvaise normalisation
    lx = (landmarks[_L_EYE_INNER].x + landmarks[_L_EYE_OUTER].x) / 2 * w
    ly = (landmarks[_L_EYE_INNER].y + landmarks[_L_EYE_OUTER].y) / 2 * h
    rx = (landmarks[_R_EYE_INNER].x + landmarks[_R_EYE_OUTER].x) / 2 * w
    ry = (landmarks[_R_EYE_INNER].y + landmarks[_R_EYE_OUTER].y) / 2 * h
    angle = abs(float(np.degrees(np.arctan2(ry - ly, rx - lx))))
    angle_score = max(0.0, 1.0 - angle / 30.0)

    # 3. Netteté — variance du Laplacien sur le crop
    x, y = bbox[0], bbox[1]
    crop = frame_bgr[max(0,y):min(h,y+bh), max(0,x):min(w,x+bw)]
    if crop.size > 0:
        gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        sharpness = float(cv2.Laplacian(gray_crop, cv2.CV_64F).var())
        sharp_score = min(1.0, sharpness / 100.0)
    else:
        sharp_score = 0.0

    overall = size_score * 0.3 + angle_score * 0.4 + sharp_score * 0.3

    return {
        "size": size_score,
        "angle": angle_score,
        "sharpness": sharp_score,
        "overall": overall,
    }


# ---------------------------------------------------------------------------
# Face alignment & preprocessing
# ---------------------------------------------------------------------------

def align_face(frame_bgr: np.ndarray, landmarks, target_size: int = 224,
               eye_width_ratio: float = 0.34, eye_y_position: float = 0.36):
    """
    Affine-warp the frame so the face is centered, upright and consistently
    scaled.  eye_width_ratio contrôle la marge contextuelle (plus petit = plus
    de marge autour du visage).
    """
    h, w = frame_bgr.shape[:2]

    lx = (landmarks[_L_EYE_INNER].x + landmarks[_L_EYE_OUTER].x) / 2 * w
    ly = (landmarks[_L_EYE_INNER].y + landmarks[_L_EYE_OUTER].y) / 2 * h
    rx = (landmarks[_R_EYE_INNER].x + landmarks[_R_EYE_OUTER].x) / 2 * w
    ry = (landmarks[_R_EYE_INNER].y + landmarks[_R_EYE_OUTER].y) / 2 * h

    dx, dy = rx - lx, ry - ly
    angle = float(np.degrees(np.arctan2(dy, dx)))
    eye_dist = float(np.hypot(dx, dy))
    if eye_dist < 1.0:
        return None

    scale = (target_size * eye_width_ratio) / eye_dist
    eye_cx, eye_cy = (lx + rx) / 2.0, (ly + ry) / 2.0

    M = cv2.getRotationMatrix2D((eye_cx, eye_cy), angle, scale)
    M[0, 2] += target_size / 2.0 - eye_cx
    M[1, 2] += target_size * eye_y_position - eye_cy

    return cv2.warpAffine(
        frame_bgr, M, (target_size, target_size),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )


def apply_clahe_lab(img_bgr: np.ndarray, clahe) -> np.ndarray:
    """CLAHE on L channel only — preserves hue and saturation."""
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)


def preprocess_face(
    frame_bgr: np.ndarray,
    landmarks,
    clahe,
    target_size: int = 224,
    eye_width_ratio: float = 0.34,
    eye_y_position: float = 0.36,
    normalize: str = "minmax",
) -> np.ndarray | None:
    """Full pipeline: align → CLAHE on L (LAB) → RGB → normalize."""
    aligned = align_face(frame_bgr, landmarks, target_size, eye_width_ratio, eye_y_position)
    if aligned is None:
        return None
    if clahe is not None:
        aligned = apply_clahe_lab(aligned, clahe)
    rgb = cv2.cvtColor(aligned, cv2.COLOR_BGR2RGB).astype(np.float32)

    if normalize == "zscore":
        mean = rgb.mean()
        std = rgb.std() + 1e-6
        rgb = (rgb - mean) / std
    else:
        rgb = rgb / 255.0

    return rgb


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _draw_prob_sparkline(
    frame: np.ndarray,
    history: deque,
    x: int, y: int, w: int, h: int,
    color: tuple,
) -> None:
    """Mini-graphe de l'évolution de la confiance dominante (sparkline)."""
    if len(history) < 2:
        return
    confs = [float(np.max(p)) for p in history]
    n = len(confs)
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
    step = w / max(n - 1, 1)
    for i in range(n - 1):
        x1 = int(x + i * step)
        y1 = int(y + h - confs[i] * h)
        x2 = int(x + (i + 1) * step)
        y2 = int(y + h - confs[i + 1] * h)
        cv2.line(frame, (x1, y1), (x2, y2), color, 2)


def _draw_prob_bars(
    frame: np.ndarray,
    probs: np.ndarray,
    emotion_classes: list,
    x: int, y: int,
    bar_w: int = 100,
    bar_h: int = 14,
    gap: int = 2,
) -> None:
    """Barres horizontales de probabilité pour chaque émotion, à droite du bbox."""
    font, scale, thick = cv2.FONT_HERSHEY_SIMPLEX, 0.38, 1
    panel_h = len(emotion_classes) * (bar_h + gap)
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + bar_w + 70, y + panel_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    dominant_idx = int(np.argmax(probs))
    for i, cls in enumerate(emotion_classes):
        py = y + i * (bar_h + gap)
        p = float(probs[i])
        color = EMOTION_COLORS.get(cls, (180, 180, 180))
        fill_w = int(p * bar_w)
        if i == dominant_idx:
            cv2.rectangle(frame, (x, py), (x + bar_w, py + bar_h), color, 1)
        cv2.rectangle(frame, (x, py), (x + fill_w, py + bar_h), color, -1)
        txt = f"{cls[:3]} {p:.0%}"
        cv2.putText(frame, txt, (x + bar_w + 4, py + bar_h - 2), font, scale, (220, 220, 220), thick)


def draw_face(
    frame: np.ndarray,
    bbox: tuple,
    track: FaceTrack,
    emotion_classes: list,
) -> None:
    x, y, w, h = bbox
    emo, conf = track.dominant_emotion(emotion_classes)
    color = EMOTION_COLORS.get(emo, (200, 200, 200)) if emo else (200, 200, 200)
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

    if track.gradcam_map is not None and w > 10 and h > 10:
        fh, fw = frame.shape[:2]
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(fw, x + w), min(fh, y + h)
        roi_w, roi_h = x2 - x1, y2 - y1
        if roi_w > 0 and roi_h > 0:
            cam_resized = cv2.resize(track.gradcam_map, (roi_w, roi_h),
                                     interpolation=cv2.INTER_LINEAR)
            heatmap = cv2.applyColorMap((cam_resized * 255).astype(np.uint8), cv2.COLORMAP_JET)
            roi = frame[y1:y2, x1:x2]
            cv2.addWeighted(heatmap, 0.5, roi, 0.5, 0, roi)

    if emo:
        label = f"{emo}  {conf:.0%}"
        font, scale, thick = cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2
        (tw, th), _ = cv2.getTextSize(label, font, scale, thick)
        cv2.rectangle(frame, (x, y - th - 10), (x + tw + 6, y), color, -1)
        cv2.putText(frame, label, (x + 3, y - 5), font, scale, (0, 0, 0), thick)

    if emo and emo in EMOTION_AUS:
        au_label = EMOTION_AUS[emo]
        cv2.putText(frame, au_label, (x, y + h + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

    if track.quality is not None:
        q = track.quality["overall"]
        q_color = (0, 200, 0) if q >= 0.6 else (0, 200, 255) if q >= 0.3 else (0, 0, 200)
        q_label = f"Q:{q:.0%}"
        cv2.putText(frame, q_label, (x, y + h + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, q_color, 1)

    if track._smooth_probs is not None:
        _draw_prob_bars(frame, track._smooth_probs, emotion_classes, x + w + 8, y)

    if len(track.prob_history) >= 2:
        spark_h = max(20, h // 5)
        _draw_prob_sparkline(frame, track.prob_history, x, y + h + 4, w, spark_h, color)


# ---------------------------------------------------------------------------
# GPU setup
# ---------------------------------------------------------------------------

def _setup_gpu(gpu_cfg: dict) -> str:
    """
    Configure TensorFlow GPU memory growth.
    Retourne le label du device actif : 'GPU:0', 'GPU:1', ... ou 'CPU'.
    """
    if not gpu_cfg.get("enabled", True):
        tf.config.set_visible_devices([], "GPU")
        print("[GPU] Désactivé par configuration — CPU uniquement")
        return "CPU"

    gpus = tf.config.list_physical_devices("GPU")
    if not gpus:
        print("[GPU] Aucun GPU détecté — utilisation du CPU")
        return "CPU"

    try:
        if gpu_cfg.get("memory_growth", True):
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
        names = ", ".join(g.name.split("physical_device:")[-1] for g in gpus)
        print(f"[GPU] {len(gpus)} GPU détecté(s) : {names}")
        return f"GPU ({len(gpus)})"
    except RuntimeError as e:
        print(f"[GPU] Erreur configuration : {e} — fallback CPU")
        return "CPU"


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(cfg: dict) -> None:
    # --- GPU ---
    device_label = _setup_gpu(cfg.get("gpu", {}))

    # --- MediaPipe ---
    landmarker = mp_vision.FaceLandmarker.create_from_options(
        mp_vision.FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(
                model_asset_path=cfg["models"]["face_landmarker_path"]
            ),
            running_mode=RunningMode.VIDEO,
            num_faces=cfg["tracking"]["max_faces"],
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    )

    # --- Inference backend ---
    inf_cfg = cfg["inference"]
    backend = create_inference_backend(
        backend=inf_cfg["backend"],
        keras_model_path=cfg["models"]["emotion_model_path"],
        tflite_model_path=inf_cfg.get("tflite_model_path"),
        tflite_num_threads=inf_cfg.get("tflite_num_threads", 2),
    )
    details = backend.details()
    input_size = details.input_shape[1] if details.input_shape else cfg.get("model_input_size", 224)
    print(f"[Backend] {details.backend.upper()} sur {details.device} — entrée {input_size}x{input_size}")
    backend.warmup((1, input_size, input_size, 3), runs=inf_cfg.get("warmup_runs", 2))

    # --- Alignment & preprocessing ---
    align_cfg = cfg.get("alignment", {})
    eye_width_ratio = align_cfg.get("eye_width_ratio", 0.34)
    eye_y_position = align_cfg.get("eye_y_position", 0.36)
    prep_cfg = cfg.get("preprocessing", {})
    normalize_mode = prep_cfg.get("normalize", "minmax")

    # --- CLAHE ---
    clahe_cfg = cfg.get("clahe", {})
    if clahe_cfg.get("enabled", True):
        clahe = cv2.createCLAHE(
            clipLimit=clahe_cfg.get("clip_limit", 2.0),
            tileGridSize=tuple(clahe_cfg.get("tile_grid_size", [8, 8])),
        )
        print(f"[CLAHE] clip_limit={clahe_cfg.get('clip_limit', 2.0)}, tile={clahe_cfg.get('tile_grid_size', [8, 8])}")
    else:
        clahe = None
        print("[CLAHE] Désactivé")

    # --- Camera ---
    cam_cfg = cfg["camera"]
    cap = cv2.VideoCapture(cam_cfg["index"])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_cfg["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_cfg["height"])
    if not cap.isOpened():
        raise RuntimeError("Impossible d'ouvrir la caméra.")

    # --- Work frame ---
    wf_cfg = cfg.get("work_frame", {})
    use_wf = wf_cfg.get("enabled", True)
    wf_w = wf_cfg.get("width", 640)
    wf_h = wf_cfg.get("height", 360)

    emotion_classes = cfg["emotion"]["classes"]
    detect_interval_ms = cfg["tracking"]["detect_every_ms"]
    infer_interval_ms = inf_cfg.get("infer_every_ms", 150)
    max_missed = cfg["tracking"]["max_missed_frames"]
    quality_threshold = cfg["tracking"].get("quality_threshold", 0.3)

    tracks: list = []
    last_detect_ms = 0.0
    last_infer_ms = 0.0
    fps_times: deque = deque(maxlen=30)
    last_t = time.perf_counter()

    # --- Capture thread ---
    frame_q: queue.Queue = queue.Queue(maxsize=2)
    stop = threading.Event()

    def _capture() -> None:
        while not stop.is_set():
            ret, frame = cap.read()
            if not ret:
                stop.set()
                return
            if frame_q.full():
                try:
                    frame_q.get_nowait()
                except queue.Empty:
                    pass
            frame_q.put(frame)

    threading.Thread(target=_capture, daemon=True).start()

    # --- Inference thread (non-bloquant pour l'UI) ---
    infer_q: queue.Queue = queue.Queue(maxsize=1)
    infer_lock = threading.Lock()

    def _infer_worker() -> None:
        while not stop.is_set():
            try:
                job = infer_q.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                batch, job_tracks = job
                if backend.supports_batch:
                    preds = backend.predict_batch(batch)
                else:
                    preds = np.stack(
                        [backend.predict(batch[i:i+1]) for i in range(batch.shape[0])]
                    )
                with infer_lock:
                    for i, (track, pred) in enumerate(zip(job_tracks, preds)):
                        track.add_prediction(pred)
                        cam = backend.gradcam(batch[i:i+1])
                        if cam is not None:
                            track.gradcam_map = cam
            except Exception:
                if stop.is_set():
                    break

    threading.Thread(target=_infer_worker, daemon=True).start()

    ui_mode = cfg["ui"]["mode"]
    window_name = cfg["ui"]["window_name"]
    if ui_mode != "off":
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    try:
        while not stop.is_set():
            try:
                frame = frame_q.get(timeout=1.0)
            except queue.Empty:
                continue

            now_ms = time.perf_counter() * 1000

            # FPS counter
            t = time.perf_counter()
            fps_times.append(t - last_t)
            last_t = t
            fps = len(fps_times) / sum(fps_times) if fps_times else 0.0

            # Work frame
            if use_wf:
                h_orig, w_orig = frame.shape[:2]
                work = cv2.resize(frame, (wf_w, wf_h))
                proc_w, proc_h = wf_w, wf_h
                sx, sy = w_orig / wf_w, h_orig / wf_h
            else:
                work = frame
                proc_h, proc_w = frame.shape[:2]
                sx = sy = 1.0

            gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)

            # ----------------------------------------------------------------
            # Detection phase — MediaPipe (~2.5 Hz)
            # ----------------------------------------------------------------
            if now_ms - last_detect_ms >= detect_interval_ms:
                last_detect_ms = now_ms
                mp_img = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=cv2.cvtColor(work, cv2.COLOR_BGR2RGB),
                )
                result = landmarker.detect_for_video(mp_img, int(now_ms))

                det_bboxes = []
                det_landmarks = []
                if result.face_landmarks:
                    for lm_list in result.face_landmarks:
                        det_bboxes.append(landmarks_to_bbox(lm_list, proc_w, proc_h))
                        det_landmarks.append(lm_list)

                # Match detections → existing tracks (IoU)
                n_existing = len(tracks)
                used_tracks: set = set()
                used_dets: set = set()

                for di, det_bb in enumerate(det_bboxes):
                    best_iou, best_ti = 0.3, -1
                    for ti in range(n_existing):
                        if ti in used_tracks:
                            continue
                        iou = bbox_iou(det_bb, tracks[ti].bbox)
                        if iou > best_iou:
                            best_iou, best_ti = iou, ti
                    if best_ti >= 0:
                        tracks[best_ti].reinit(gray, det_bb, det_landmarks[di])
                        used_tracks.add(best_ti)
                        used_dets.add(di)

                # New detections → new tracks
                for di, det_bb in enumerate(det_bboxes):
                    if di not in used_dets:
                        new_track = FaceTrack(gray, det_bb)
                        new_track.last_landmarks = det_landmarks[di]
                        tracks.append(new_track)

                # Increment missed for unmatched existing tracks
                for ti in range(n_existing):
                    if ti not in used_tracks:
                        tracks[ti].missed += 1

                tracks = [t for t in tracks if t.missed <= max_missed]

            else:
                # ------------------------------------------------------------
                # Tracking phase — MOSSE (every frame between detections)
                # ------------------------------------------------------------
                for track in tracks:
                    track.update(gray)
                tracks = [t for t in tracks if t.missed <= max_missed]

            # ----------------------------------------------------------------
            # Inference — envoi au thread (non-bloquant)
            # ----------------------------------------------------------------
            if tracks and now_ms - last_infer_ms >= infer_interval_ms:
                last_infer_ms = now_ms
                batch_faces = []
                batch_tracks = []
                for track in tracks:
                    if track.last_landmarks is None:
                        continue
                    q = face_quality(work, track.last_landmarks, track.bbox)
                    track.quality = q
                    if q["overall"] < quality_threshold:
                        continue
                    face = preprocess_face(work, track.last_landmarks, clahe, input_size,
                                           eye_width_ratio, eye_y_position, normalize_mode)
                    if face is not None:
                        batch_faces.append(face)
                        batch_tracks.append(track)

                if batch_faces and infer_q.empty():
                    batch = np.stack(batch_faces, axis=0)
                    try:
                        infer_q.put_nowait((batch, list(batch_tracks)))
                    except queue.Full:
                        pass

            # ----------------------------------------------------------------
            # Render
            # ----------------------------------------------------------------
            if ui_mode != "off":
                display = frame.copy()
                for track in tracks:
                    x, y, w, h = track.bbox
                    scaled = (int(x * sx), int(y * sy), int(w * sx), int(h * sy))
                    draw_face(display, scaled, track, emotion_classes)

                cv2.putText(
                    display,
                    f"FPS: {fps:.1f}  |  Faces: {len(tracks)}  |  {device_label}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 80), 2,
                )
                cv2.imshow(window_name, display)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key == ord("s"):
                    cap_dir = "captures"
                    os.makedirs(cap_dir, exist_ok=True)
                    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                    saved = 0
                    for i, track in enumerate(tracks):
                        if track.last_landmarks is None or track._smooth_probs is None:
                            continue
                        face = preprocess_face(work, track.last_landmarks, clahe, input_size,
                                               eye_width_ratio, eye_y_position, normalize_mode)
                        if face is None:
                            continue
                        img_bgr = cv2.cvtColor((face * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
                        path = f"{cap_dir}/{ts}_face{i}.png"
                        cv2.imwrite(path, img_bgr)
                        emo, conf = track.dominant_emotion(emotion_classes)
                        probs_str = ", ".join(
                            f"{c}: {p:.1%}" for c, p in zip(emotion_classes, track._smooth_probs)
                        )
                        with open(f"{cap_dir}/{ts}_face{i}.txt", "w") as f:
                            f.write(f"emotion: {emo} ({conf:.1%})\n{probs_str}\n")
                        print(f"[Capture] {path} — {emo} {conf:.0%}")
                        saved += 1
                    if saved == 0:
                        print("[Capture] Aucune prédiction disponible — attendre quelques secondes")

    finally:
        stop.set()
        cap.release()
        cv2.destroyAllWindows()
        landmarker.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="FaceGuard – Emotion Recognition")
    parser.add_argument("--config", default=None, help="Chemin vers un fichier YAML de config")
    parser.add_argument("--ui", choices=("full", "off"), default=None)
    parser.add_argument("--backend", choices=("auto", "keras", "tflite"), default=None,
                        help="Forcer le backend d'inférence")
    parser.add_argument("--cpu", action="store_true",
                        help="Forcer l'utilisation du CPU (désactive le GPU)")
    parser.add_argument("--camera", type=int, default=None, help="Index de la caméra")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.ui:
        cfg["ui"]["mode"] = args.ui
    if args.backend:
        cfg["inference"]["backend"] = args.backend
    if args.cpu:
        cfg["gpu"]["enabled"] = False
    if args.camera is not None:
        cfg["camera"]["index"] = args.camera

    run(cfg)


if __name__ == "__main__":
    main()
