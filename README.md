# FaceGuard V2 — Reconnaissance d'Émotions en Temps Réel

Système de vision par ordinateur focalisé sur la **détection et reconnaissance d'émotions faciales** en temps réel, optimisé pour une faible consommation de ressources.

## Fonctionnalités

- **Modèle ConvNeXt-Base** entraîné sur AffectNet — 8 émotions (ANGRY, CONTEMPT, DISGUST, FEAR, HAPPY, NEUTRAL, SAD, SURPRISE)
- **Alignement facial automatique** via landmarks MediaPipe (transformation affine sur les yeux)
- **Prétraitement couleur RGB** avec CLAHE sur canal L (espace LAB) — robustesse en basse luminosité
- **Lissage EMA** (Exponential Moving Average) sur les probabilités — affichage stable et fluide
- **Tracking MOSSE** entre les détections — légèreté CPU
- **Architecture multi-thread** : thread capture + thread traitement

## Stack technique

| Composant | Technologie |
|---|---|
| Langage | Python 3.10+ |
| Détection visage | MediaPipe FaceLandmarker (VIDEO mode) |
| Modèle émotion | ConvNeXt-Base — Keras 3 / TensorFlow 2.19 |
| Vision | OpenCV 4.13 |
| Tracking | MOSSE (opencv-contrib) |
| Config | YAML |

## Installation

> **Python 3.12 requis.** TensorFlow 2.19 ne supporte pas Python 3.13+.
> Télécharger Python 3.12 : https://www.python.org/downloads/release/python-3120/

```bash
# Windows — créer le venv explicitement avec Python 3.12
py -3.12 -m venv venv
venv\Scripts\activate

# Linux/macOS
python3.12 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

> Les modèles (dossier `models/`) ne sont pas inclus dans le dépôt Git (trop lourds).
> Fichiers requis :
> - `models/faceguard_convnext.keras` — modèle émotion ConvNeXt
> - `models/face_landmarker.task` — détecteur MediaPipe

## Utilisation

```bash
# Démarrage standard
python main.py

# Autre caméra
python main.py --camera 1

# Sans interface (headless)
python main.py --ui off

# Config personnalisée
python main.py --config configs/custom.yaml
```

## Configuration (`configs/default.yaml`)

```yaml
model_input_size: 224        # taille d'entrée ConvNeXt

inference:
  backend: keras             # keras | tflite
  infer_every_ms: 150        # fréquence d'inférence (~6 Hz)

tracking:
  detect_every_ms: 400       # fréquence détection MediaPipe (~2.5 Hz)
  max_faces: 4

work_frame:
  enabled: true
  width: 640
  height: 360                # résolution de travail interne (économie CPU)

clahe:
  clip_limit: 2.0            # CLAHE appliqué sur canal L (espace LAB)
```

Pour personnaliser sans modifier le fichier par défaut :
```bash
cp configs/default.yaml configs/custom.yaml
# éditer custom.yaml
python main.py --config configs/custom.yaml
```

## Pipeline

```
Caméra (1280×720)
    └── Work frame (640×360)
            ├── MediaPipe FaceLandmarker (~2.5 Hz)
            │       └── Landmarks 468 points → bbox + alignement
            ├── MOSSE tracker (chaque frame)
            └── Inférence (~6 Hz)
                    ├── align_face()    — transformation affine yeux
                    ├── CLAHE sur L     — normalisation luminance
                    ├── BGR → RGB       — couleur réelle
                    ├── ConvNeXt 224×224 → 8 probas
                    └── EMA lissage     — affichage stable
```

## Structure du projet

```
FaceGuard_V2/
├── main.py                    # pipeline principal
├── configs/default.yaml       # configuration
├── faceguard/
│   ├── config.py              # chargement YAML
│   └── services/
│       └── inference_backend.py  # Keras / TFLite
├── models/                    # modèles (non versionnés — voir .gitignore)
├── docs/
│   └── AMELIORATIONS.md       # journal des améliorations
└── tools/
    └── export_tflite.py       # export Keras → TFLite
```

## Export TFLite (optionnel)

Pour convertir le ConvNeXt en TFLite FP32 et alléger l'inférence :
```bash
python tools/export_tflite.py --in models/faceguard_convnext.keras --out models/faceguard_fp32.tflite
```
Puis dans la config :
```yaml
inference:
  backend: tflite
  tflite_model_path: models/faceguard_fp32.tflite
  tflite_num_threads: 4
```
