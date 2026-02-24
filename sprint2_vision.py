import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import tensorflow as tf
import numpy as np
import os
import urllib.request

# Dossier où ranger le modèle
MODEL_DIR = 'models'
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

TASK_FILE_PATH = os.path.join(MODEL_DIR, 'face_landmarker.task')

if not os.path.exists(TASK_FILE_PATH):
    print("[INFO] Téléchargement du moteur MediaPipe (face_landmarker.task)...")
    url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    urllib.request.urlretrieve(url, TASK_FILE_PATH)
    print("✅ Téléchargement terminé.")

# ==========================================
# 1. CHARGEMENT ALIGNÉ
# ==========================================
MODEL_PATH = 'models/faceguard_best_model_Version_25-065Epochs.keras' 

print(f"[INFO] Chargement du modèle Keras 3 : {MODEL_PATH}")

try:
    # On charge le modèle. compile=False est toujours recommandé pour l'inférence
    emotion_model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    print("✅ SUCCÈS : Le modèle est chargé et prêt.")
except Exception as e:
    print("\n" + "!"*60)
    print("ERREUR DE CHARGEMENT :")
    print(e)
    print("!"*60)
    print("\nCONSEIL : Vérifie que tes versions correspondent à Colab.")
    exit()

EMOTION_CLASSES = ['ANGRY', 'CONTEMPT', 'DISGUST', 'FEAR', 'HAPPY', 'NEUTRAL', 'SAD', 'SURPRISE']

# ==========================================
# 2. MEDIAPIPE & CLAHE (Le Sprint 2)
# ==========================================
base_options = python.BaseOptions(model_asset_path='models/face_landmarker.task')
options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)
detector = vision.FaceLandmarker.create_from_options(options)

# Notre filtre industriel
clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

# ==========================================
# 3. BOUCLE PRINCIPALE
# ==========================================
cap = cv2.VideoCapture(0)
last_emotion = "---"

while cap.isOpened():
    success, image = cap.read()
    if not success: break
    image = cv2.flip(image, 1)
    h, w, _ = image.shape
    
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    res = detector.detect(mp_image)

    if res.face_landmarks:
        landmarks = res.face_landmarks[0]
        x_vals = [l.x for l in landmarks]
        y_vals = [l.y for l in landmarks]
        x_min, x_max = max(0, int(min(x_vals) * w) - 10), min(w, int(max(x_vals) * w) + 10)
        y_min, y_max = max(0, int(min(y_vals) * h) - 20), min(h, int(max(y_vals) * h) + 10)

        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 1)

        if (x_max - x_min) > 40:
            # PRÉTRAITEMENT CLAHE
            face_crop = image[y_min:y_max, x_min:x_max]
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            clahe_img = clahe.apply(gray)
            final_input = cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2RGB)

            # DEBUG VISUEL (Fenêtre séparée pour voir l'effet CLAHE)
            cv2.imshow('Filtre CLAHE (Vision IA)', cv2.resize(final_input, (200, 200)))

            # PRÉDICTION
            ai_input = cv2.resize(final_input, (48, 48))
            tensor = np.expand_dims(ai_input, axis=0)
            
            # Note : En Keras 3, model.predict() est parfois lent en boucle. 
            # On peut utiliser model(tensor, training=False) pour plus de vitesse.
            preds = emotion_model(tensor, training=False)
            idx = np.argmax(preds[0])
            if preds[0][idx] > 0.40:
                last_emotion = EMOTION_CLASSES[idx]

    # HUD
    cv2.putText(image, f"Emotion: {last_emotion}", (20, 40), 1, 2, (255, 255, 255), 2)
    cv2.imshow('FaceGuard - Sprint 2', image)
    
    if cv2.waitKey(5) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()