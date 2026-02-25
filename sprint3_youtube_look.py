import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import tensorflow as tf
import numpy as np
from collections import deque
import os
from mediapipe.tasks.python.vision.drawing_utils import draw_landmarks as mp_draw_landmarks, DrawingSpec as MpDrawingSpec
from mediapipe.tasks.python.vision.face_landmarker import FaceLandmarksConnections

# ==========================================
# 1. CHARGEMENT IA & LISSAGE (SMOOTHING)
# ==========================================
MODEL_PATH = 'models/faceguard_convnext.keras'
print(f"[INFO] Chargement du modèle : {MODEL_PATH}")

try:
    emotion_model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    model_loaded = True
except Exception as e:
    print(f"⚠️ AVERTISSEMENT : Impossible de charger l'IA. Mode visuel seul.")
    model_loaded = False

# Ordre d'affichage comme sur ta capture YouTube
EMOTION_CLASSES = ['anger', 'contempt', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']

# Le Buffer pour la stabilisation (Moyenne sur les 10 dernières frames)
BUFFER_SIZE = 30
preds_buffer = deque(maxlen=BUFFER_SIZE)

# ==========================================
# 2. SETUP MEDIAPIPE (Avec utilitaires de dessin)
# ==========================================

base_options = python.BaseOptions(model_asset_path='models/face_landmarker.task')
options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)
detector = vision.FaceLandmarker.create_from_options(options)

clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

# ==========================================
# 3. FONCTIONS D'INTERFACE (UI)
# ==========================================
def draw_transparent_box(image, x, y, w, h, alpha=0.6):
    """ Dessine un rectangle semi-transparent """
    overlay = image.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), (50, 50, 50), -1) # Gris foncé
    return cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)

# ==========================================
# 4. BOUCLE PRINCIPALE
# ==========================================
print("[INFO] Démarrage de la caméra... (ECHAP pour quitter)")
cap = cv2.VideoCapture(0)

# On force une haute résolution pour la webcam pour avoir un beau rendu
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while cap.isOpened():
    success, image = cap.read()
    if not success: break
    image = cv2.flip(image, 1)
    img_h, img_w, _ = image.shape
    
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    res = detector.detect(mp_image)

    if res.face_landmarks:
        landmarks = res.face_landmarks[0]
        
        # --- A. DESSIN DU MASQUE FILAIRE (Wireframe) ---
        # Conversion des landmarks pour l'utilitaire de dessin
        # Dessin de la toile blanche fine (Tasks API — pas besoin de protobuf)
        mp_draw_landmarks(
            image=image,
            landmark_list=landmarks,
            connections=FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=MpDrawingSpec(color=(255, 255, 255), thickness=1, circle_radius=0)
        )

        # --- B. PRÉTRAITEMENT & PRÉDICTION ---
        x_vals = [l.x for l in landmarks]; y_vals = [l.y for l in landmarks]
        x_min, x_max = max(0, int(min(x_vals) * img_w) - 10), min(img_w, int(max(x_vals) * img_w) + 10)
        y_min, y_max = max(0, int(min(y_vals) * img_h) - 20), min(img_h, int(max(y_vals) * img_h) + 10)

        averaged_preds = np.zeros(len(EMOTION_CLASSES))
        
        if (x_max - x_min) > 40 and model_loaded:
            face_crop = image[y_min:y_max, x_min:x_max]
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            clahe_img = clahe.apply(gray)
            final_input = cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2RGB)

            ai_input = cv2.resize(final_input, (224, 224))
            tensor = np.expand_dims(ai_input, axis=0)
            
            raw_preds = emotion_model(tensor, training=False)[0].numpy()
            
            # Application du lissage (On ajoute au buffer)
            preds_buffer.append(raw_preds)
            averaged_preds = np.mean(preds_buffer, axis=0) # Moyenne des 10 dernières frames

        # --- C. REPRODUCTION DU "YOUTUBE LOOK" ---
        if len(preds_buffer) > 0:
            # Récupération des 2 meilleures émotions
            top_2_idx = averaged_preds.argsort()[-2:][::-1]
            dom_emo = EMOTION_CLASSES[top_2_idx[0]]
            sec_emo = EMOTION_CLASSES[top_2_idx[1]]
            activation = averaged_preds[top_2_idx[0]] * 100

            # 1. La Ligne directrice (Du front vers la boîte droite)
            # Landmark 10 est le haut du front
            forehead_x, forehead_y = int(landmarks[10].x * img_w), int(landmarks[10].y * img_h)
            box_right_x = min(x_max + 30, img_w - 200) # Évite de sortir de l'écran
            box_right_y = max(30, y_min - 20)
            cv2.line(image, (forehead_x, forehead_y), (box_right_x, box_right_y), (255, 255, 255), 1)

            # 2. La Boîte Droite (Détail de toutes les émotions)
            # Ordre d'affichage inspiré de la vidéo
            display_order = ['anger', 'contempt', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
            
            image = draw_transparent_box(image, box_right_x, box_right_y, 200, 180, alpha=0.5)
            
            y_offset = box_right_y + 20
            for emo in display_order:
                # Trouve l'index de cette émotion dans nos classes
                idx = EMOTION_CLASSES.index(emo)
                score = averaged_preds[idx] * 100
                text = f"{emo.capitalize()} {score:.2f}%"
                
                # Met en gras (thickness 2) si c'est l'émotion dominante
                thickness = 2 if emo == dom_emo else 1
                cv2.putText(image, text, (box_right_x + 10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), thickness)
                y_offset += 20

            # 3. La Boîte Gauche (Résumé & Activation)
            box_left_x = max(10, x_min - 220)
            box_left_y = max(30, y_min + 50)
            
            image = draw_transparent_box(image, box_left_x, box_left_y, 200, 100, alpha=0.5)
            
            # Ligne de séparation dans la boîte
            cv2.line(image, (box_left_x, box_left_y + 25), (box_left_x + 200, box_left_y + 25), (200, 200, 200), 1)
            
            cv2.putText(image, f"{dom_emo.capitalize()}", (box_left_x + 10, box_left_y + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(image, f"{sec_emo.capitalize()}", (box_left_x + 10, box_left_y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.putText(image, f"Activation: {activation:.2f}%", (box_left_x + 10, box_left_y + 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Ligne directrice gauche vers le visage (Joue gauche)
            cheek_x, cheek_y = int(landmarks[234].x * img_w), int(landmarks[234].y * img_h)
            cv2.line(image, (box_left_x + 200, box_left_y + 50), (cheek_x, cheek_y), (255, 255, 255), 1)

    cv2.imshow('FaceGuard - UI YouTube', image)
    if cv2.waitKey(5) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()