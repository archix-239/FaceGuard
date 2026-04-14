# Journal des Améliorations — FaceGuard V2
> Reconnaissance d'émotions · Détection · IA · Pipeline

Chaque entrée documente : **quoi**, **pourquoi**, et **résultat observé**.

---

## [2026-04-14] — Simplification du projet (focus reconnaissance d'émotions)

### Modifications
- Suppression du système FSM (états CALM / SUSPECT / THREAT)
- Suppression du threat scoring (asymétrie faciale, score 0-100)
- Suppression du buffer temporel 60 s et de l'extraction de features à 1 Hz
- Suppression du track health evaluation
- Suppression du recording / replay / profiling JSONL
- `main.py` réduit de 1156 lignes → 265 lignes
- Backend d'inférence par défaut changé de Keras → TFLite (17 MB vs 31 MB)

### Pourquoi
Le projet était devenu trop complexe avec des fonctionnalités hors-scope (menace, sécurité).
L'objectif recentré est uniquement la **reconnaissance d'émotions fiable et légère**.

### Résultat
- Démarrage plus rapide (modèle TFLite vs Keras)
- Code plus lisible et maintenable
- Pipeline clair : MediaPipe → MOSSE → TFLite → affichage émotion

---

## [2026-04-14] — Pack d'améliorations qualité de reconnaissance

### 1. Passage au modèle ConvNeXt + résolution 224×224

**Modification**
- Remplacement de `faceguard_best_model_Version_25-065Epochs.keras` (48×48, 31 MB)
  par `faceguard_convnext.keras` (224×224, 1.7 GB)
- Résolution d'entrée : 48×48 → **224×224**
- Backend repassé sur Keras (le ConvNeXt n'a pas encore d'export TFLite)

**Pourquoi**
À 48×48 pixels, une grande partie du détail facial est perdue (micro-expressions, coins de bouche,
plissement du nez). Le ConvNeXt-Base est une architecture bien plus puissante et a été entraîné
spécifiquement sur AffectNet en RGB 224×224.

**Résultat attendu**
- Meilleure précision globale sur toutes les émotions
- Amélioration notable sur CONTEMPT et DISGUST (très sensibles aux détails fins)

---

### 2. Utilisation de la couleur réelle (RGB)

**Modification**
- Suppression de la conversion `BGR → GRAY → RGB` (3 canaux identiques, zéro info couleur)
- Le crop du visage est maintenant traité en **BGR → RGB** directement
- Le modèle reçoit de vraies informations de teinte et saturation

**Pourquoi**
L'ancienne pipeline convertissait en niveaux de gris puis reconstituait une image RGB avec
3 canaux identiques. Le modèle ConvNeXt ayant été entraîné sur des images RGB, il ne recevait
aucune information couleur utile.

**Résultat attendu**
- Meilleure discrimination entre émotions proches (ex. FEAR vs SURPRISE)
- Utilisation complète des capacités du modèle

---

### 3. Alignement facial par landmarks (yeux)

**Modification**
- Ajout de la fonction `align_face()` utilisant les landmarks MediaPipe
- Landmarks utilisés : coins intérieur/extérieur des deux yeux
  (indices 33, 133, 362, 263 du mesh 468 points)
- Transformation affine : rotation pour horizontaliser les yeux + centrage + mise à l'échelle
- Yeux placés à 38% du haut de l'image (standard de normalisation faciale)
- Distance inter-oculaire normalisée à 40% de la largeur cible

**Pourquoi**
Sans alignement, un visage incliné ou excentré produit un crop mal normalisé.
Le modèle a été entraîné sur des visages alignés — lui donner des visages non-alignés
dégrade significativement les prédictions.

**Résultat attendu**
- Robustesse aux rotations de tête (jusqu'à ±30°)
- Crops plus cohérents d'une frame à l'autre
- Réduction des faux positifs sur les émotions

---

### 4. CLAHE sur canal L (espace LAB) au lieu du niveau de gris

**Modification**
- Remplacement de `clahe.apply(gray_crop)` par `apply_clahe_lab(bgr_crop)`
- Pipeline : `BGR → LAB → CLAHE sur L → LAB → BGR`
- `clip_limit` ajusté de 2.5 → 2.0 (moins agressif, préserve mieux les détails)

**Pourquoi**
Appliquer CLAHE sur une image en niveaux de gris détruisait l'information couleur.
Appliquer CLAHE sur le canal L de l'espace LAB normalise la luminance **sans toucher
à la chrominance** (canaux A et B), préservant ainsi les informations de teinte et saturation.

**Résultat attendu**
- Meilleure robustesse aux conditions d'éclairage (contre-jour, faible lumière)
- Couleurs préservées après normalisation du contraste

---

### 5. Lissage temporel EMA (Exponential Moving Average)

**Modification**
- Remplacement du vote majoritaire sur 8 frames par une **moyenne mobile exponentielle**
  appliquée directement sur les vecteurs de probabilités
- Formule : `smooth = α × new_probs + (1-α) × smooth_probs`  avec α = 0.35
- L'émotion affichée est dérivée du vecteur lissé `argmax(smooth_probs)`

**Pourquoi**
Le vote majoritaire introduisait des sauts brusques entre émotions (ex. HAPPY → NEUTRAL → HAPPY).
L'EMA produit des **transitions graduelles** proportionnelles à la confiance du modèle.
Un α = 0.35 offre un bon compromis réactivité / stabilité.

**Résultat attendu**
- Affichage de l'émotion beaucoup plus stable et fluide
- Transitions naturelles lors des changements d'expression
- Moins de "clignotement" entre deux émotions proches

---

## Métriques de référence (à remplir après tests)

| Version | Modèle | Résolution | Backend | FPS moyen | Précision subjective |
|---------|--------|------------|---------|-----------|----------------------|
| v1 (avant simplification) | Keras 31 MB | 48×48 | Keras | — | — |
| v2 (simplification) | TFLite 17 MB | 48×48 | TFLite | — | — |
| v3 (pack améliorations) | ConvNeXt 1.7 GB | 224×224 | Keras | — | — |

> Remplir cette table après chaque session de test en conditions réelles.
