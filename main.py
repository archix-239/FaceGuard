import argparse
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision.drawing_utils import draw_landmarks as mp_draw_landmarks, DrawingSpec as MpDrawingSpec
from mediapipe.tasks.python.vision.face_landmarker import FaceLandmarksConnections
import tensorflow as tf
import numpy as np
from collections import deque
import math
import os
import time

from faceguard.profiling import Timer, FrameTimings, RunProfiler


def parse_args():
    parser = argparse.ArgumentParser(description="FaceGuard runtime")
    parser.add_argument("--record", action="store_true", help="Record processed session video + metrics")
    parser.add_argument("--replay", type=str, default=None, help="Replay from an existing video file")
    parser.add_argument("--no-ui", action="store_true", help="Disable OpenCV window rendering")
    parser.add_argument("--outdir", type=str, default="runs", help="Output directory for runs")
    parser.add_argument("--record-overlay", action="store_true", help="Record annotated frames instead of raw frames")
    return parser.parse_args()


def make_run_id(prefix: str = "run"):
    return f"{prefix}_{time.strftime('%Y%m%d_%H%M%S')}"


def create_run_dir(outdir: str, replay_path: str | None):
    run_prefix = "replay" if replay_path else "run"
    run_id = make_run_id(run_prefix)
    run_dir = os.path.join(outdir, run_id)
    os.makedirs(run_dir, exist_ok=True)
    return run_id, run_dir


print("\n" + "="*50)
print("🚀 DÉMARRAGE DE FACEGUARD V2.0 (SYSTÈME COMPLET) 🚀")
print("="*50 + "\n")

args = parse_args()
if args.record and args.replay:
    raise SystemExit("❌ --record et --replay ne peuvent pas être utilisés ensemble.")
if args.replay and not os.path.exists(args.replay):
    raise SystemExit(f"❌ Fichier replay introuvable: {args.replay}")

run_id, run_dir = create_run_dir(args.outdir, args.replay)
metrics_path = os.path.join(run_dir, "metrics.jsonl")
video_path = os.path.join(run_dir, "video.mp4")

# ==========================================
# 1. CHARGEMENT DU "TANK" IA (CONVNEXT)
# ==========================================
MODEL_PATH = 'models/faceguard_best_model_Version_25-065Epochs.keras'

print(f"[⏳] Chargement du modèle IA lourd ({MODEL_PATH})... Cela peut prendre 30 secondes.")
try:
    emotion_model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    print("[✅] Modèle IA chargé avec succès dans la RAM !")
except Exception as e:
    print(f"[❌] ERREUR FATALE : Impossible de charger l'IA.\n{e}")
    exit()

EMOTION_CLASSES = ['ANGRY', 'CONTEMPT', 'DISGUST', 'FEAR', 'HAPPY', 'NEUTRAL', 'SAD', 'SURPRISE']

# Buffer de lissage (15 frames = ~0.5 sec)
preds_buffer = deque(maxlen=15)

# ==========================================
# 2. SETUP MEDIAPIPE & CLAHE
# ==========================================
print("[⏳] Initialisation des capteurs géométriques...")
base_options = python.BaseOptions(model_asset_path='models/face_landmarker.task')
options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)
detector = vision.FaceLandmarker.create_from_options(options)

clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

# ==========================================
# 3. MOTEUR MATHÉMATIQUE (ASYMÉTRIE)
# ==========================================
SYMMETRY_PAIRS = [
    (55, 285), (105, 334), (70, 300), (133, 362), (33, 263),
    (159, 386), (240, 460), (61, 291), (37, 267), (17, 314), (58, 288), (172, 397)
]


def get_head_pose(landmarks):
    nose_tip, left_cheek, right_cheek = landmarks[1], landmarks[454], landmarks[234]
    dist_left = abs(nose_tip.x - left_cheek.x)
    dist_right = abs(right_cheek.x - nose_tip.x)
    if dist_right == 0:
        return "PROFIL"
    ratio = dist_left / dist_right
    if ratio > 2.0:
        return "PROFIL_GAUCHE"
    elif ratio < 0.5:
        return "PROFIL_DROIT"
    return "FACE"


def rotate_point(point, center, angle_rad):
    x, y, cx, cy = point[0], point[1], center[0], center[1]
    new_x = cx + (x - cx) * math.cos(angle_rad) - (y - cy) * math.sin(angle_rad)
    new_y = cy + (x - cx) * math.sin(angle_rad) + (y - cy) * math.cos(angle_rad)
    return new_x, new_y


def calculate_global_asymmetry(landmarks, w, h):
    total_deviation = 0
    eye_l = (landmarks[33].x * w, landmarks[33].y * h)
    eye_r = (landmarks[263].x * w, landmarks[263].y * h)

    delta_x, delta_y = eye_r[0] - eye_l[0], eye_r[1] - eye_l[1]
    angle_rad = math.atan2(delta_y, delta_x)
    nose_pivot = (landmarks[1].x * w, landmarks[1].y * h)
    eye_dist = math.sqrt(delta_x**2 + delta_y**2)
    if eye_dist == 0:
        return 0

    for (idx_l, idx_r) in SYMMETRY_PAIRS:
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

    return (total_deviation / len(SYMMETRY_PAIRS)) * 100


# ==========================================
# 4. FONCTION D'INTERFACE (UI)
# ==========================================
def draw_transparent_box(image, x, y, w, h, alpha=0.6):
    overlay = image.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), (30, 30, 30), -1)
    return cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)


# ==========================================
# 5. BOUCLE PRINCIPALE (LE COEUR DU SYSTÈME)
# ==========================================
input_source = args.replay if args.replay else 0
print("[✅] Démarrage de la caméra... (Appuyez sur ECHAP pour quitter)" if not args.replay else f"[✅] Replay vidéo: {args.replay}")
cap = cv2.VideoCapture(input_source)
if not args.replay:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

profiler = RunProfiler(output_path=metrics_path)
frame_idx = 0
writer = None

while cap.isOpened():
    frame_start = time.perf_counter()
    frame_ts_ms = int(time.time() * 1000)
    frame_timings = FrameTimings(ts_ms=frame_ts_ms, frame_idx=frame_idx)
    frame_idx += 1

    with Timer(frame_timings.timings_ms, "capture"):
        success, frame_raw = cap.read()
        if success and not args.replay:
            frame_raw = cv2.flip(frame_raw, 1)

    if not success:
        break

    frame_vis = frame_raw.copy()
    img_h, img_w, _ = frame_raw.shape

    if args.record and writer is None:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 30.0
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(video_path, fourcc, fps, (img_w, img_h))

    with Timer(frame_timings.timings_ms, "mediapipe"):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame_raw, cv2.COLOR_BGR2RGB))
        res = detector.detect(mp_image)

    threat_score = 0
    dom_emo = "SCANNING..."
    activation = 0.0
    pose_text = "INCONNU"
    valid_quality = False
    is_asymmetric = False

    frame_timings.has_face = bool(res.face_landmarks)

    if res.face_landmarks:
        landmarks = res.face_landmarks[0]

        pose_text = get_head_pose(landmarks)

        if pose_text == "FACE":
            asym_score = calculate_global_asymmetry(landmarks, img_w, img_h)
            if asym_score > 20:
                is_asymmetric = True
                threat_score += 40

        x_vals = [l.x for l in landmarks]
        y_vals = [l.y for l in landmarks]
        x_min, x_max = max(0, int(min(x_vals) * img_w) - 10), min(img_w, int(max(x_vals) * img_w) + 10)
        y_min, y_max = max(0, int(min(y_vals) * img_h) - 20), min(img_h, int(max(y_vals) * img_h) + 10)

        averaged_preds = np.zeros(len(EMOTION_CLASSES))

        if (x_max - x_min) > 40:
            with Timer(frame_timings.timings_ms, "preprocess"):
                face_crop = frame_raw[y_min:y_max, x_min:x_max]
                gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
                clahe_img = clahe.apply(gray)
                final_input = cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2RGB)

                ai_input = cv2.resize(final_input, (48, 48))
                tensor = np.expand_dims(ai_input, axis=0)

            with Timer(frame_timings.timings_ms, "infer"):
                raw_preds = emotion_model(tensor, training=False)[0].numpy()
                preds_buffer.append(raw_preds)
                averaged_preds = np.mean(preds_buffer, axis=0)

            valid_quality = True

        if len(preds_buffer) > 0:
            top_2_idx = averaged_preds.argsort()[-2:][::-1]
            dom_emo = EMOTION_CLASSES[top_2_idx[0]]
            activation = averaged_preds[top_2_idx[0]] * 100

            if dom_emo in ['ANGRY', 'CONTEMPT']:
                threat_score += 60
            if dom_emo in ['FEAR']:
                threat_score += 30

    with Timer(frame_timings.timings_ms, "ui"):
        if not args.no_ui and res.face_landmarks:
            landmarks = res.face_landmarks[0]

            mp_draw_landmarks(
                image=frame_vis,
                landmark_list=landmarks,
                connections=FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=MpDrawingSpec(color=(255, 255, 255), thickness=1, circle_radius=0)
            )

            if len(preds_buffer) > 0:
                forehead_x, forehead_y = int(landmarks[10].x * img_w), int(landmarks[10].y * img_h)
                box_right_x = min(x_max + 30, img_w - 200)
                box_right_y = max(30, y_min - 20)
                cv2.line(frame_vis, (forehead_x, forehead_y), (box_right_x, box_right_y), (255, 255, 255), 1)

                display_order = ['NEUTRAL', 'HAPPY', 'SURPRISE', 'ANGRY', 'DISGUST', 'FEAR', 'SAD', 'CONTEMPT']
                frame_vis = draw_transparent_box(frame_vis, box_right_x, box_right_y, 200, 180, alpha=0.5)

                y_offset = box_right_y + 20
                for emo in display_order:
                    idx = EMOTION_CLASSES.index(emo)
                    score = averaged_preds[idx] * 100
                    thickness = 2 if emo == dom_emo else 1
                    color = (255, 255, 255) if emo == dom_emo else (180, 180, 180)
                    cv2.putText(frame_vis, f"{emo:<10} {score:5.2f}%", (box_right_x + 10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, thickness)
                    y_offset += 20

                box_left_x = max(10, x_min - 220)
                box_left_y = max(30, y_min + 50)

                ts_color = (0, 255, 0)
                if threat_score >= 40:
                    ts_color = (0, 165, 255)
                if threat_score >= 70:
                    ts_color = (0, 0, 255)

                frame_vis = draw_transparent_box(frame_vis, box_left_x, box_left_y, 200, 110, alpha=0.6)
                cv2.line(frame_vis, (box_left_x, box_left_y + 25), (box_left_x + 200, box_left_y + 25), (200, 200, 200), 1)

                cv2.putText(frame_vis, f"{dom_emo}", (box_left_x + 10, box_left_y + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame_vis, f"THREAT SCORE: {threat_score}", (box_left_x + 10, box_left_y + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, ts_color, 2)

                if is_asymmetric:
                    cv2.putText(frame_vis, "⚠️ ASYMETRIE", (box_left_x + 10, box_left_y + 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

                cheek_x, cheek_y = int(landmarks[234].x * img_w), int(landmarks[234].y * img_h)
                cv2.line(frame_vis, (box_left_x + 200, box_left_y + 50), (cheek_x, cheek_y), (255, 255, 255), 1)

        if not args.no_ui and threat_score >= 70:
            cv2.rectangle(frame_vis, (0, 0), (img_w, img_h), (0, 0, 255), 4)
            cv2.putText(frame_vis, "INTENTION HOSTILE DETECTEE", (img_w//2 - 200, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        if not args.no_ui:
            cv2.imshow('FaceGuard V2.0 - Edition Industrielle', frame_vis)
            should_quit = (cv2.waitKey(5) & 0xFF == 27)
        else:
            should_quit = False

    if writer is not None:
        writer.write(frame_vis if args.record_overlay else frame_raw)

    frame_timings.timings_ms["total"] = (time.perf_counter() - frame_start) * 1000.0
    frame_timings.pose = pose_text
    frame_timings.valid_quality = valid_quality
    frame_timings.emotion_top1 = dom_emo
    frame_timings.emotion_p = float(activation / 100.0)
    frame_timings.threat_score = int(threat_score)
    profiler.write_frame(frame_timings)

    if should_quit:
        break

cap.release()
if writer is not None:
    writer.release()
if not args.no_ui:
    cv2.destroyAllWindows()
profiler.print_summary()
profiler.close()

print(f"[✅] Run ID: {run_id}")
print(f"[✅] Metrics: {metrics_path}")
if writer is not None:
    mode = "overlay" if args.record_overlay else "raw"
    print(f"[✅] Video: {video_path} ({mode})")
