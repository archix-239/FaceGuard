# Étude détaillée du projet FaceGuard

## Objectif produit
FaceGuard combine vision embarquée temps réel et scoring comportemental pour la surveillance industrielle. Le runtime Python capte un flux vidéo (caméra ou replay), détecte/tracke plusieurs visages, exécute une inférence émotionnelle (Keras ou TFLite), calcule un score de menace, puis rend un HUD OpenCV. En parallèle, un frontend Next.js existe comme interface dashboard (mockée actuellement) mais n’est pas encore branchée au runtime.

## Cartographie technique

### Backend runtime (Python)
- **Entrée principale :** `main.py`.
- **Configuration :** YAML (`configs/default.yaml`) chargé/fusionné via `faceguard/config.py`.
- **Détection visage/landmarks :** MediaPipe FaceLandmarker.
- **Tracking multi-personnes :** `faceguard/tracking.py` + trackers OpenCV (MOSSE/KCF/CSRT).
- **Inférence émotions :** abstraction `faceguard/services/inference_backend.py` (backend `keras` ou `tflite`).
- **Profiling et métriques :** `faceguard/profiling.py` (timings JSONL par frame + résumé final).

### Frontend (Next.js)
- Dossier `frontend/` en App Router.
- Dashboard statique orienté supervision (`VideoWall`, `ThreatGauge`, `AlertTicker`).
- État actuel: interface visuelle prête, sans API/data live branchée au moteur Python.

## Pipeline runtime observé
1. Lecture frame (caméra/replay).
2. Downscale optionnel en **work frame** pour limiter coût CPU.
3. Scheduling détection (périodique temporel ou every-N-frames) + tracking intermédiaire.
4. Extraction ROI visage, prétraitement (grayscale + CLAHE + resize + RGB).
5. Inférence émotion (batch possible selon backend/support).
6. Calcul menace + asymétrie faciale.
7. Rendering UI (`full|min|off`) + enregistrement vidéo/métriques optionnels.

## Conception déjà robuste
- **Config centralisée et mergée proprement** (override utilisateur sans casser les valeurs par défaut).
- **Abstraction d’inférence claire** (fallback batch générique + implémentations natives).
- **Concurrence séparée capture/traitement** avec queue bornée (`maxsize=2`) et politique anti-latence.
- **Mode replay** utile pour benchmark reproductible.
- **Profiling structuré** facilitant l’optimisation ciblée (capture, mediapipe, matching, inference, render...).

## Zones de dette / risques techniques
- `main.py` reste très volumineux et concentre orchestration, logique métier, tracking, UI et I/O.
- Dépendance forte aux assets modèles locaux (`models/*.keras`, `models/*.task`) non versionnés.
- Couplage encore élevé entre pipeline temps réel et logique d’affichage OpenCV.
- Frontend séparé du moteur: pas de contrat API partagé ni flux d’événements unifié.

## Tests et qualité
- Présence d’un fichier de tests ciblé sur la logique batch d’inférence (`tests/test_batch_inference.py`).
- Couverture orientée unit tests/fakes (comportement backend), mais peu de tests d’intégration pipeline bout-en-bout.

## Recommandations prioritaires (court terme)
1. Extraire le cœur de `main.py` en modules `app/services/domain/ui` déjà esquissés dans `docs/ARCHITECTURE.md`.
2. Introduire un schéma d’événements runtime (JSON/WS) consommable par le frontend.
3. Ajouter tests d’intégration “offline replay” pour verrouiller non-régression latence/FPS/outputs métriques.
4. Versionner un “profil de config de perf” (CPU faible vs qualité max) pour industrialiser les déploiements.

## Commandes utiles pour prise en main
- Lancer runtime standard:
  - `python main.py`
- Lancer headless benchmark:
  - `python main.py --ui off --max-seconds 30`
- Forcer backend TFLite:
  - config `inference.backend: tflite` + `python main.py --config configs/default.yaml`
- Lancer frontend:
  - `cd frontend && pnpm dev`
