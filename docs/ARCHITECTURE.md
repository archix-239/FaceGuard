# FaceGuard — Cartographie actuelle & plan de refactor minimal

## 1) Cartographie rapide du dépôt

### Point d’entrée / exécution
- **Entrée principale actuelle** : `main.py` (script monolithique lancé directement avec Python).
- **Scripts historiques / itérations** :
  - `sprint2_vision.py` (pipeline détection + CLAHE + inférence simplifiée),
  - `sprint3_youtube_look.py` (rendu "YouTube look" + lissage),
  - `sprint4_geometrie.py` (moteur de symétrie/pose).

### Modules logiques (aujourd’hui implicites dans `main.py`)
- **Chargement modèle IA** : TensorFlow/Keras (`tf.keras.models.load_model`) pour le classifieur d’émotions.
- **Détection visage / landmarks** : MediaPipe Tasks FaceLandmarker.
- **Prétraitement image** : crop visage + niveaux de gris + CLAHE + conversion RGB + resize (48x48).
- **Inférence** : modèle émotion sur tenseur image.
- **Scoring** : score menace basé sur émotion dominante + asymétrie faciale.
- **UI OpenCV** : wireframe landmarks, boîtes d’info, barres/texte et alertes visuelles.

### Configuration / dépendances
- **Dépendances Python** : `requirements.txt`.
- **Config “en dur” dans le code** (à ce stade) :
  - chemins modèles (`models/*.keras`, `models/face_landmarker.task`),
  - seuils menace/asymétrie,
  - paramètres caméra,
  - tailles buffer/lissage.
- **UI web séparée** : dossier `frontend/` (Next.js), non branché au runtime `main.py` actuel.

---

## 2) Pipeline actuel (capture → détection → preprocess → inférence → scoring → UI)

```text
┌──────────────┐
│ Webcam frame │
└──────┬───────┘
       │
       v
┌──────────────────────────────┐
│ MediaPipe Face Landmarker    │
│ - landmarks 3D visage        │
└──────┬───────────────────────┘
       │
       │ (si visage détecté)
       v
┌──────────────────────────────┐
│ Préprocess visage            │
│ - ROI via landmarks          │
│ - grayscale + CLAHE          │
│ - RGB + resize 48x48         │
└──────┬───────────────────────┘
       │
       v
┌──────────────────────────────┐
│ Inférence TensorFlow         │
│ - logits/probas émotions     │
│ - lissage temporel (deque)   │
└──────┬───────────────────────┘
       │
       v
┌──────────────────────────────┐
│ Scoring menace               │
│ - règles émotion             │
│ - asymétrie faciale (géom.)  │
└──────┬───────────────────────┘
       │
       v
┌──────────────────────────────┐
│ Rendu OpenCV temps réel      │
│ - wireframe + HUD + alertes  │
└──────────────────────────────┘
```

---

## 3) Points de coût (CPU/GPU, latence, maintenance)

1. **Chargement initial modèle Keras lourd**
   - Coût de démarrage élevé (I/O disque + désérialisation).
2. **Détection landmarks à chaque frame**
   - Coût CPU significatif, dominant quand résolution caméra élevée.
3. **Prétraitement frame par frame**
   - Conversions couleur + CLAHE + resize sur chaque image.
4. **Inférence TensorFlow en continu**
   - Coût principal en runtime (surtout si pas d’accélération matérielle).
5. **Rendu UI OpenCV dense**
   - Multiples appels de dessin/texte par frame, impacte FPS.
6. **Code monolithique**
   - Coût de maintenance élevé : faible testabilité, couplage fort, évolution risquée.

---

## 4) Plan de refactor minimal (sans casser l’exécution)

Objectif: **conserver le comportement actuel** tout en découpant en modules fins, avec un point d’entrée stable.

### Étape A — Extraire la configuration (sans changer les valeurs)
- Nouveau module proposé: `faceguard/config.py`
- Responsabilités:
  - centraliser chemins modèles, classes d’émotions,
  - seuils (asymétrie/menace), tailles image, caméra, buffer.

### Étape B — Isoler les services techniques
- `faceguard/services/model_loader.py`
  - charge et expose le modèle émotion.
- `faceguard/services/landmark_detector.py`
  - initialise MediaPipe FaceLandmarker et exécute `detect`.
- `faceguard/services/preprocess.py`
  - fonctions ROI visage + CLAHE + tensorisation.

### Étape C — Isoler la logique métier
- `faceguard/domain/asymmetry.py`
  - `get_head_pose`, `rotate_point`, `calculate_global_asymmetry`.
- `faceguard/domain/threat_scoring.py`
  - règles de scoring à partir émotions + asymétrie.

### Étape D — Isoler le rendu
- `faceguard/ui/overlay.py`
  - primitives UI (boîte transparente, textes, lignes).
- `faceguard/ui/frame_renderer.py`
  - orchestration du HUD complet.

### Étape E — Orchestrateur runtime conservateur
- `faceguard/app.py`
  - boucle principale capture/traitement/rendu.
- `main.py`
  - point d’entrée minimal qui appelle `faceguard.app.run()`.

### Étape F — Validation non-régressive
- Vérifier démarrage caméra, détection, inférence et HUD identiques.
- Ajouter tests unitaires ciblés sur:
  - calcul asymétrie,
  - règles de scoring,
  - fonctions pures de prétraitement.

> Cette trajectoire minimise le risque: on découpe **à comportement constant** avant toute optimisation lourde (batching, async, quantization, etc.).
