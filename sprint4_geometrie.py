import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import math

# ==========================================
# 1. SETUP & CONSTANTES (Paires Symétriques)
# ==========================================
base_options = python.BaseOptions(model_asset_path='models/face_landmarker.task')
options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)
detector = vision.FaceLandmarker.create_from_options(options)

# Liste des paires de points (Gauche, Droite) couvrant tout le visage
SYMMETRY_PAIRS = [
    (61, 291), (39, 269), (37, 267), (267, 37), (84, 314), # Bouche (Coins et lèvres)
    (55, 285), (65, 295), (52, 282), (53, 283),            # Sourcils (Intérieur/Extérieur)
    (33, 263), (133, 362),                                 # Yeux (Coins)
    (119, 348), (205, 425), (50, 280), (118, 347),         # Joues (Pommettes et creux)
    (130, 359), (247, 467),                                # Tempes
    (150, 379), (149, 378), (136, 365), (132, 361)         # Mâchoire (Ligne inférieure)
]

# ==========================================
# 2. MOTEUR GÉOMÉTRIQUE HOLISTIQUE
# ==========================================

def rotate_point(cx, cy, angle_rad, p):
    """ Fait tourner un point autour d'un centre """
    s = math.sin(angle_rad)
    c = math.cos(angle_rad)
    px = p.x - cx
    py = p.y - cy
    x_new = px * c - py * s
    y_new = px * s + py * c
    return x_new + cx, y_new + cy

def get_head_pose(landmarks):
    """ Vérifie si la tête est de profil """
    dist_left = abs(landmarks[1].x - landmarks[234].x)
    dist_right = abs(landmarks[454].x - landmarks[1].x)
    if dist_right == 0: return "PROFIL"
    ratio = dist_left / dist_right
    if ratio > 2.0 or ratio < 0.5: return "PROFIL"
    return "FACE"

def calculate_holistic_asymmetry(landmarks):
    """
    Calcule l'asymétrie sur tout le visage après l'avoir redressé mathématiquement.
    Retourne le score global et la liste des paires en anomalie.
    """
    # 1. Trouver l'angle d'inclinaison de la tête (Ligne Front 10 -> Menton 152)
    dx = landmarks[152].x - landmarks[10].x
    dy = landmarks[152].y - landmarks[10].y
    angle_rad = math.atan2(dx, dy) # Angle pour remettre la ligne verticale
    
    # Centre de rotation (Nez)
    cx, cy = landmarks[1].x, landmarks[1].y
    face_height = math.hypot(dx, dy) # Pour normaliser les distances
    
    total_asymmetry = 0
    anomalies = [] # Pour stocker les paires qui "déconnent"

    # 2. Vérifier toutes les paires
    for left_idx, right_idx in SYMMETRY_PAIRS:
        # Redressement virtuel des deux points
        _, left_y_rot = rotate_point(cx, cy, angle_rad, landmarks[left_idx])
        _, right_y_rot = rotate_point(cx, cy, angle_rad, landmarks[right_idx])
        
        # Différence de hauteur normalisée par la taille du visage
        diff_y = abs(left_y_rot - right_y_rot) / face_height
        total_asymmetry += diff_y
        
        # Si une zone spécifique est très asymétrique (Seuil de tolérance local)
        if diff_y > 0.012: 
            anomalies.append((left_idx, right_idx))

    # Score global lissé (Multiplié par 1000 pour être lisible, ex: 15.4)
    global_score = (total_asymmetry / len(SYMMETRY_PAIRS)) * 1000
    return global_score, anomalies

# ==========================================
# 3. BOUCLE PRINCIPALE (Test unitaire Sprint 4 V2)
# ==========================================
print("[INFO] Démarrage du Moteur Holistique... (ECHAP pour quitter)")
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
    head_pose = "INCONNU"
    global_asym_score = 0

    if res.face_landmarks:
        landmarks = res.face_landmarks[0]
        
        # Vérification du profil
        head_pose = get_head_pose(landmarks)
        
        if head_pose == "FACE":
            # --- CALCUL HOLISTIQUE ---
            global_asym_score, anomalies = calculate_holistic_asymmetry(landmarks)
            
            # Logique d'Alerte : Un visage normal a un score entre 5 et 10.
            # Au dessus de 12-15, c'est une grimace, un mépris, ou un fort doute.
            if global_asym_score > 12.0:
                threat_score += int(global_asym_score * 2) # Poids dans le score final
                
            # --- DESSIN DEBUG "AR YOUTUBE" ---
            # On dessine une fine ligne verte entre toutes les paires analysées
            for left_idx, right_idx in SYMMETRY_PAIRS:
                pt1 = (int(landmarks[left_idx].x * w), int(landmarks[left_idx].y * h))
                pt2 = (int(landmarks[right_idx].x * w), int(landmarks[right_idx].y * h))
                
                # Si cette paire fait partie des anomalies, on la dessine en ROUGE EPAIS
                if (left_idx, right_idx) in anomalies:
                    cv2.line(image, pt1, pt2, (0, 0, 255), 2)
                    cv2.circle(image, pt1, 3, (0, 0, 255), -1)
                    cv2.circle(image, pt2, 3, (0, 0, 255), -1)
                else:
                    cv2.line(image, pt1, pt2, (255, 255, 255), 1) # Blanc fin normal
        else:
            cv2.putText(image, "GEOMETRIE DESACTIVEE (PROFIL)", (w//2 - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # --- AFFICHAGE HUD ---
    cv2.rectangle(image, (10, 10), (450, 120), (0, 0, 0), -1)
    
    color = (0, 0, 255) if global_asym_score > 12.0 else (0, 255, 0)
    
    cv2.putText(image, f"Indice Asymetrie Global : {global_asym_score:.1f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(image, f"Menace (Geometrie) : {threat_score}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(image, f"Tete : {head_pose}", (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    cv2.imshow('FaceGuard - Sprint 4 (Holistic Asymmetry)', image)
    if cv2.waitKey(5) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()