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

- Backend inférence (Keras ou TFLite CPU/XNNPACK):
```yaml
inference:
  fps: 8.0
  backend: keras          # keras | tflite
  tflite_model_path: models/faceguard_fp32.tflite
  tflite_num_threads: 4
  warmup_runs: 3
```

- Export modèle Keras -> TFLite fp32:
```bash
python tools/export_tflite.py --in models/<model>.keras --out models/faceguard_fp32.tflite
```


- Multi-visages (IDs stables + TTL):
```yaml
tracking:
  enabled: true
  max_faces: 2
  ttl_ms: 2000
  match:
    w_iou: 0.6
    w_dist: 0.4
    iou_min: 0.05
    dist_max_norm: 0.15
  reacquire:
    enabled: true
    grace_ms: 800
    dist_max_norm_multiplier: 1.5
```
- Chaque visage garde un `person_id` stable via matching coût global (IoU + distance centroïde + gating) + fenêtre de réacquisition permissive avant création d’un nouvel ID.
- Les logs JSONL incluent `match_events`, `new_ids_created`, `unmatched_dets` pour diagnostiquer les resets d’ID.
- NMS est appliqué avant association pour supprimer les doublons detector, puis un garde-fou bloque la création de nouvel ID si la détection chevauche fortement un ID existant.

- Tracking ROI (detect rarely, track often):
```yaml
tracking:
  enabled: true
  detect_every_ms: 400      # prioritaire si > 0
  detect_every_n_frames: 15 # fallback si detect_every_ms absent/null/<=0
  tracker_type: MOSSE
  max_missed_frames: 30
```

- Override runtime de la cadence d’inférence (sans éditer YAML):
```bash
python main.py --fps-infer 2 --ui off --max-seconds 20
```


## Pipeline multi-thread (FG-G3)
- Deux threads :
  - **Capture/UI** : lecture caméra/replay, affichage OpenCV, enregistrement vidéo.
  - **Traitement** : MediaPipe/Tracker + preprocess + inférence + scoring + logs JSONL.
- Queue bornée configurable (`runtime.queue_maxsize`, défaut 8) avec politique configurable (`runtime.queue_drop_policy`).
  - Recommandé tracking temps réel: `drop_newest` (conserve la continuité des frames déjà en queue).
  - Option `block` possible en `ui off` pour ralentir la capture au lieu de jeter.
- Quand backlog > 1 et tracking actif, le processing draine les frames intermédiaires en **track-only** (tracker.update uniquement, sans detect/infer), puis exécute le pipeline normal sur la dernière frame.
- En replay, l’horloge de traitement utilise `CAP_PROP_POS_MSEC` (fallback index/FPS si non disponible).
- **Métrique `total`** dans le profiling = temps **total du thread traitement** par frame (aussi exposé comme `total_processing`).

## Record / Replay
- `duration_sec` et `effective_infer_fps` sont calculés depuis l’horloge source des frames (replay: `CAP_PROP_POS_MSEC`, live: timestamp système), pas depuis le wall-clock de processing.
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
- Rejouer à vitesse réelle (throttle horloge source):
```bash
python main.py --replay runs/<run_id>/video.mp4 --replay-realtime
```

## Structure du projet
- `main.py` : runtime principal.
- `configs/` : configuration YAML.
- `faceguard/` : modules support (profiling, config, etc.).
- `models/` : modèles pré-entraînés (non inclus sur Git - voir .gitignore).
- `runs/` : sorties des exécutions (vidéo + metrics JSONL).
