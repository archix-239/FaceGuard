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

## InstallationS
1. `python -m venv venv`
2. `source venv/bin/activate`  # ou .\venv\Scripts\activate sur Windows
3. `pip install -r requirements.txt`

## Structure du projet
- `src/` : Code source (Core, Utils, UI)
- `models/` : Modèles pré-entraînés (non inclus sur Git - voir .gitignore)
- `data/` : Logs et captures de sécurité