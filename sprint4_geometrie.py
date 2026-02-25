import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import math
import os

# ==========================================
# 1. SETUP MEDIAPIPE
# ==========================================
MODEL_PATH = 'models/face_landmarker.task' 
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = 'face_landmarker.task' # Fallback

base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)
detector = vision.FaceLandmarker.create_from_options(options)

# ==========================================
# 2. CONSTANTES DE SYMÉTRIE
# ==========================================
SYMMETRY_PAIRS = [
    (55, 285), (105, 334), (70, 300),   # Sourcils
    (133, 362), (33, 263), (159, 386),  # Yeux
    (240, 460),                         # Nez
    (61, 291), (37, 267), (17, 314),    # Bouche
    (58, 288), (172, 397)               # Mâchoire
]

# ==========================================
# 3. MOTEUR MATHÉMATIQUE (LA VERSION STABLE : ROTATION)
# ==========================================

def get_head_pose(landmarks):
    """ Vérifie si la tête est de profil. """
    nose_tip = landmarks[1]
    left_cheek = landmarks[454]  
    right_cheek = landmarks[234]
    
    dist_left = abs(nose_tip.x - left_cheek.x)
    dist_right = abs(right_cheek.x - nose_tip.x)
    
    if dist_right == 0: return "PROFIL"
    ratio = dist_left / dist_right
    
    if ratio > 2.0: return "PROFIL_GAUCHE"
    elif ratio < 0.5: return "PROFIL_DROIT"
    return "FACE"

def rotate_point(point, center, angle_rad):
    """ Fait tourner un point autour d'un centre (Redressement 2D) """
    x, y = point
    cx, cy = center
    new_x = cx + (x - cx) * math.cos(angle_rad) - (y - cy) * math.sin(angle_rad)
    new_y = cy + (x - cx) * math.sin(angle_rad) + (y - cy) * math.cos(angle_rad)
    return new_x, new_y

def calculate_global_asymmetry(landmarks, w, h):
    """
    Calcule l'asymétrie avec la méthode de redressement rotationnel.
    (La plus stable selon nos tests).
    """
    total_deviation = 0
    asymmetric_points = []
    
    # 1. Calcul de l'angle d'inclinaison de la tête (Roll)
    eye_l = (landmarks[33].x * w, landmarks[33].y * h)
    eye_r = (landmarks[263].x * w, landmarks[263].y * h)
    
    delta_x = eye_r[0] - eye_l[0]
    delta_y = eye_r[1] - eye_l[1]
    angle_rad = math.atan2(delta_y, delta_x)
    
    nose_pivot = (landmarks[1].x * w, landmarks[1].y * h)
    
    # Distance de référence pour normaliser le calcul
    eye_dist = math.sqrt(delta_x**2 + delta_y**2)
    if eye_dist == 0: return 0, []

    for (idx_l, idx_r) in SYMMETRY_PAIRS:
        pl_raw = (landmarks[idx_l].x * w, landmarks[idx_l].y * h)
        pr_raw = (landmarks[idx_r].x * w, landmarks[idx_r].y * h)
        
        # REDRESSEMENT : On tourne les points pour mettre le visage droit
        pl = rotate_point(pl_raw, nose_pivot, -angle_rad)
        pr = rotate_point(pr_raw, nose_pivot, -angle_rad)
        
        # Comparaison des hauteurs (Y)
        height_diff = abs(pl[1] - pr[1])
        
        # Comparaison des écartements (X)
        dist_l_x = abs(pl[0] - nose_pivot[0])
        dist_r_x = abs(pr[0] - nose_pivot[0])
        width_diff = abs(dist_l_x - dist_r_x)
        
        # Formule de déviation (On donne plus de poids au décalage vertical)
        local_score = (width_diff + (height_diff * 1.5)) / eye_dist
        total_deviation += local_score
        
        if local_score > 0.15: 
            asymmetric_points.append((idx_l, idx_r))

    final_score = (total_deviation / len(SYMMETRY_PAIRS)) * 100
    return final_score, asymmetric_points

# ==========================================
# 4. BOUCLE PRINCIPALE
# ==========================================
print("[INFO] Démarrage Analyse Symétrie (Version Stable)...")
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while cap.isOpened():
    success, image = cap.read()
    if not success: break
    image = cv2.flip(image, 1)
    h, w, _ = image.shape
    
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    res = detector.detect(mp_image)

    threat_score = 0
    pose_text = "INCONNU"
    asym_score = 0.0

    if res.face_landmarks:
        landmarks = res.face_landmarks[0]
        
        # 1. Pose
        pose_text = get_head_pose(landmarks)
        
        # 2. Asymétrie
        if pose_text == "FACE":
            asym_score, bad_pairs = calculate_global_asymmetry(landmarks, w, h)
            
            if asym_score > 20:
                threat_score += int(asym_score)
                for (l, r) in bad_pairs:
                    pt_l = (int(landmarks[l].x * w), int(landmarks[l].y * h))
                    pt_r = (int(landmarks[r].x * w), int(landmarks[r].y * h))
                    cv2.line(image, pt_l, pt_r, (0, 0, 255), 2) # Ligne Rouge (Alerte)
            else:
                # Dessin discret (Vert)
                key_pairs = [(33, 263), (61, 291), (105, 334)]
                for (l, r) in key_pairs:
                    pt_l = (int(landmarks[l].x * w), int(landmarks[l].y * h))
                    pt_r = (int(landmarks[r].x * w), int(landmarks[r].y * h))
                    cv2.line(image, pt_l, pt_r, (0, 255, 0), 1)

    # --- HUD ---
    cv2.rectangle(image, (10, 10), (450, 150), (0, 0, 0), -1)
    cv2.putText(image, f"ASYMETRIE (STABLE) : {asym_score:.1f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    bar_width = int(min(asym_score * 3, 300))
    bar_color = (0, 255, 0)
    if asym_score > 15: bar_color = (0, 165, 255)
    if asym_score > 25: bar_color = (0, 0, 255)
    
    cv2.rectangle(image, (20, 50), (20 + bar_width, 65), bar_color, -1)
    cv2.rectangle(image, (20, 50), (320, 65), (255, 255, 255), 1)

    cv2.putText(image, f"Pose : {pose_text}", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    msg = "Normal"
    if asym_score > 15: msg = "Micro-expression"
    if asym_score > 25: msg = "! ANOMALIE / DOUTE !"
    cv2.putText(image, msg, (20, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.6, bar_color, 2)

    cv2.imshow('FaceGuard - Sprint 4', image)
    if cv2.waitKey(5) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()