import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import math

# ==========================================
# 1. SETUP MEDIAPIPE
# ==========================================
base_options = python.BaseOptions(model_asset_path='models/face_landmarker.task')
options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)
detector = vision.FaceLandmarker.create_from_options(options)

# ==========================================
# 2. MOTEUR GÉOMÉTRIQUE AVANCÉ
# ==========================================

def get_head_pose(landmarks):
    """
    Vérifie si la tête est de profil (Gauche/Droite) ou de face.
    On compare la distance entre le nez et les bords du visage.
    """
    nose_tip = landmarks[1]
    left_cheek = landmarks[234]
    right_cheek = landmarks[454]
    
    # Distances horizontales
    dist_left = abs(nose_tip.x - left_cheek.x)
    dist_right = abs(right_cheek.x - nose_tip.x)
    
    # Ratio de symétrie du visage
    if dist_right == 0: return "PROFIL_DROIT"
    ratio = dist_left / dist_right
    
    if ratio > 2.0: return "PROFIL_GAUCHE"
    elif ratio < 0.5: return "PROFIL_DROIT"
    return "FACE"

def get_angle(p1, p2):
    """ Calcule l'angle (en degrés) d'une ligne formée par 2 points """
    dy = p2.y - p1.y
    dx = p2.x - p1.x
    return math.degrees(math.atan2(dy, dx))

def check_robust_asymmetry(landmarks):
    """
    Calcule l'asymétrie en utilisant les angles (insensible à l'inclinaison de la tête).
    """
    # 1. Ligne de référence : Les Yeux (Points extérieurs 33 et 263)
    eye_angle = get_angle(landmarks[33], landmarks[263])
    
    # 2. Ligne de la Bouche (Coins 61 et 291)
    mouth_angle = get_angle(landmarks[61], landmarks[291])
    
    # 3. Ligne des Sourcils (Milieux 105 et 334)
    brow_angle = get_angle(landmarks[105], landmarks[334])
    
    # Calcul de la différence absolue par rapport à la ligne des yeux
    mouth_diff = abs(mouth_angle - eye_angle)
    brow_diff = abs(brow_angle - eye_angle)
    
    # Seuils de tolérance (en degrés)
    is_mouth_asym = mouth_diff > 3.5  # Si la bouche dévie de plus de 3.5 degrés
    is_brow_asym = brow_diff > 4.0    # Si un sourcil se lève bizarrement
    
    return is_mouth_asym, is_brow_asym, mouth_diff

def get_gaze_direction(landmarks):
    """ Gaze tracking nettoyé """
    iris_x = landmarks[468].x
    inner_x, outer_x = landmarks[133].x, landmarks[33].x
    
    if outer_x - inner_x == 0: return "CENTRE"
    ratio = (iris_x - inner_x) / (outer_x - inner_x)
    
    if ratio < 0.42: return "DROITE"
    elif ratio > 0.58: return "GAUCHE"
    return "CENTRE"

# ==========================================
# 3. BOUCLE PRINCIPALE (Test unitaire Sprint 4)
# ==========================================
print("[INFO] Démarrage du Moteur Géométrique... (ECHAP pour quitter)")
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
    status_texts = []

    if res.face_landmarks:
        landmarks = res.face_landmarks[0]
        
        # --- 1. VÉRIFICATION DU PROFIL ---
        head_pose = get_head_pose(landmarks)
        
        # --- 2. EXTRACTION DES DONNÉES ---
        gaze_dir = get_gaze_direction(landmarks)
        if gaze_dir != "CENTRE":
            threat_score += 15 # Regard fuyant = Comportement de repérage
            status_texts.append(f"Regard Fuyant (+15)")

        # On ne calcule l'asymétrie QUE si la personne est de Face !
        if head_pose == "FACE":
            is_mouth_asym, is_brow_asym, mouth_diff = check_robust_asymmetry(landmarks)
            
            if is_mouth_asym:
                threat_score += 30
                status_texts.append(f"Sourire Narquois (+30) [Dev: {mouth_diff:.1f} deg]")
            if is_brow_asym:
                threat_score += 20
                status_texts.append("Doute/Mechant (+20)")
                
            # Dessin de la ligne des yeux et bouche pour debug
            pt_eye_l = (int(landmarks[33].x * w), int(landmarks[33].y * h))
            pt_eye_r = (int(landmarks[263].x * w), int(landmarks[263].y * h))
            cv2.line(image, pt_eye_l, pt_eye_r, (255, 0, 0), 1) # Ligne bleue (Horizon)
            
            pt_mouth_l = (int(landmarks[61].x * w), int(landmarks[61].y * h))
            pt_mouth_r = (int(landmarks[291].x * w), int(landmarks[291].y * h))
            cv2.line(image, pt_mouth_l, pt_mouth_r, (0, 0, 255), 1) # Ligne rouge (Bouche)
        else:
            status_texts.append(f"Visage de {head_pose} (Geometrie desactivee)")

    # --- AFFICHAGE HUD ---
    cv2.rectangle(image, (10, 10), (450, 160), (0, 0, 0), -1)
    
    color = (0, 0, 255) if threat_score >= 40 else (0, 255, 0)
    cv2.putText(image, f"SCORE GEOMETRIQUE : {threat_score}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(image, f"Pose Tete : {head_pose}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    y_offset = 100
    for text in status_texts:
        cv2.putText(image, text, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
        y_offset += 25

    cv2.imshow('FaceGuard - Sprint 4 (Geometrie Robuste)', image)
    if cv2.waitKey(5) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()