# FaceGuard V2.0 - Intelligence Affective & Sécurité Industrielle

FaceGuard est un système de vision par ordinateur haute performance conçu pour la détection d'intentions humaines et l'analyse d'émotions en milieu industriel.

## Fonctionnalités (V2.0)
- **Cerveau IA :** Architecture ConvNeXt-Base entraînée sur AffectNet (224x224).
- **Vision Adaptative :** Prétraitement CLAHE pour la robustesse en basse luminosité.
- **Interface AR :** Rendu "Wireframe" 3D et stabilisation temporelle (YouTube Look).
- **Analyse Comportementale :** Score de menace basé sur les émotions et l'asymétrie faciale.

## Stack Technique
- **Langage :** Python 3.10+
- **IA :** TensorFlow / Keras 3
- **Vision :** OpenCV, MediaPipe (Tasks API)
- **Modèle :** ConvNeXt-Base

## Installation
1. `python -m venv venv`
2. `source venv/bin/activate`  # ou `.\venv\Scripts\activate` sur Windows
3. `pip install -r requirements.txt`

## Exécution

### Démarrage standard (config par défaut)
```bash
python main.py
```

### Démarrage explicite avec config YAML
```bash
python main.py --config configs/default.yaml
```

### Override simple (ex: largeur caméra)
1. Copier la config par défaut:
```bash
cp configs/default.yaml configs/custom.yaml
```
2. Modifier `configs/custom.yaml`:
```yaml
camera:
  width: 1920
```
3. Lancer avec la config custom:
```bash
python main.py --config configs/custom.yaml
```

- Mode UI minimal (sans tesselation):
```bash
python main.py --ui min
```
- Mode UI off (pas de fenêtre, logs/profiling actifs):
```bash
python main.py --ui off
```

- Run benchmark headless avec durée max:
```bash
python main.py --ui off --max-seconds 30
```

- Downscale pipeline (work frame) via config:
```yaml
work_frame:
  enabled: true
  width: 640
  height: 360
```

- Scheduler inférence (cadence décorrélée de la caméra):
```yaml
inference:
  fps: 8.0
```
- `inference.fps: 0` (ou `null`) désactive l’inférence (mode mesure pipeline sans IA).

- Tracking ROI (detect rarely, track often):
```yaml
tracking:
  enabled: true
  detect_every_n_frames: 15
  tracker_type: MOSSE
  max_missed_frames: 30
```

## Record / Replay
- Enregistrer une session:
```bash
python main.py --record
```
- Enregistrer la vidéo annotée (overlay):
```bash
python main.py --record --record-overlay
```
- Rejouer offline sans UI:
```bash
python main.py --replay runs/<run_id>/video.mp4 --no-ui
```

## Structure du projet
- `main.py` : runtime principal.
- `configs/` : configuration YAML.
- `faceguard/` : modules support (profiling, config, etc.).
- `models/` : modèles pré-entraînés (non inclus sur Git - voir .gitignore).
- `runs/` : sorties des exécutions (vidéo + metrics JSONL).
