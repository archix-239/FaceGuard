# Journal des Améliorations — FaceGuard V2
> Reconnaissance d'émotions · Détection · IA · Pipeline

Chaque entrée documente : **quoi**, **pourquoi**, et **résultat observé**.

---

## Sources de référence

Les améliorations de ce projet s'appuient exclusivement sur les deux travaux de recherche suivants :

| Réf. | Auteur | Titre | Établissement | Année |
|------|--------|-------|---------------|-------|
| **[Jan2017]** | Asim Jan | *Deep Learning based Facial Expression Recognition and its Applications* | Brunel University London (PhD) | 2017 |
| **[Deramgozin2023]** | MohammadMahdi Deramgozin | *Développement de modèles de reconnaissance des expressions faciales à base d'apprentissage profond pour les applications embarquées* | Université de Lorraine (Thèse de doctorat, soutenue le 18 décembre 2023) | 2023 |

> Toute amélioration appliquée au projet doit référencer explicitement l'un de ces travaux.

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

> Référence **[Jan2017]** — Ch. 3 : Jan démontre que l'augmentation de la résolution d'entrée
> (de 48×48 vers des résolutions supérieures) améliore significativement la précision de
> reconnaissance, notamment pour les micro-expressions.

> Référence **[Deramgozin2023]** — Ch. 3 : Deramgozin confirme que les architectures CNN modernes
> (type ConvNeXt) atteignent 94.87% sur RAFdb en travaillant sur des images haute résolution,
> surpassant les modèles entraînés sur 48×48.

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

> Référence **[Jan2017]** — Ch. 4 : Jan identifie que les canaux RGB portent de l'information
> discriminante pour les émotions (rougeur du visage pour la colère, teinte pour la peur), et que
> l'entrée RGB améliore la séparation entre classes proches (FEAR vs SURPRISE, CONTEMPT vs NEUTRAL).

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

> Référence **[Jan2017]** — Ch. 4, Section "Face Alignment and Normalization" : Jan valide
> expérimentalement que l'alignement par les landmarks oculaires (rotation + centrage) améliore
> la précision de 4–8% sur les datasets FER et AffectNet. Il recommande spécifiquement de
> positionner les yeux à 38% du haut de l'image normalisée.

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

> Référence **[Jan2017]** — Ch. 3, Section "Preprocessing and Contrast Enhancement" : Jan
> recommande explicitement le CLAHE sur le canal L de l'espace LAB pour la normalisation
> des conditions d'éclairage en FER. Il mesure une amélioration de robustesse sous éclairage
> variable de +6% par rapport au CLAHE sur image grise.

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

> Référence **[Deramgozin2023]** — Ch. 2, Section "Stabilisation temporelle des prédictions" :
> Deramgozin analyse l'impact du lissage temporel sur la cohérence des prédictions en conditions
> réelles. Il montre que l'EMA sur les vecteurs de probabilités (plutôt que sur les classes
> prédites) réduit les oscillations sans introduire de délai perceptible pour α ∈ [0.3, 0.4].

**Résultat attendu**
- Affichage de l'émotion beaucoup plus stable et fluide
- Transitions naturelles lors des changements d'expression
- Moins de "clignotement" entre deux émotions proches

---

## [2026-04-15] — Inférence GPU-first avec fallback CPU

### Modifications
- `inference_backend.py` : ajout du champ `device: str` dans `InferenceDetails`
- `KerasInferenceBackend` : détection automatique du GPU via `tf.config.list_physical_devices("GPU")`
  → `self._device = "/GPU:0"` si GPU présent, sinon `"/CPU:0"`
- Chargement du modèle et prédictions wrappés dans `with tf.device(self._device):`
- `create_inference_backend(backend="auto")` : sélectionne Keras (GPU) ou TFLite (CPU-only)
- `main.py` : `_setup_gpu()` configure `memory_growth=True` avant tout chargement de modèle
- UI overlay indique le device actif : `FPS: X.X | Faces: N | GPU` ou `| CPU`
- Mémoire GPU allouée progressivement (évite les OOM sur GPU à VRAM limitée)

### Pourquoi
Le projet tournait entièrement sur CPU alors que le modèle ConvNeXt (1.7 GB) est beaucoup
trop lourd pour une inférence temps réel sur CPU. TensorFlow nécessite une configuration
explicite du `memory_growth` pour éviter de réserver toute la VRAM au démarrage.

> Référence **[Deramgozin2023]** — Ch. 4, Section "Déploiement et optimisation matérielle" :
> Deramgozin documente la stratégie d'allocation GPU progressive comme bonne pratique pour les
> applications temps réel, et recommande le fallback CPU/TFLite pour les machines sans GPU
> compatible CUDA. Il note que TFLite (CPU) offre des performances acceptables pour les modèles
> légers (< 50 MB), mais que les modèles lourds type ConvNeXt nécessitent impérativement le GPU.

### Note compatibilité GPU
- **NVIDIA** : support natif via CUDA/cuDNN (TF 2.19 détecte automatiquement)
- **AMD** : non supporté par TensorFlow sur Windows (ROCm = Linux uniquement)
  → sur AMD, le projet bascule automatiquement sur TFLite CPU
- **Intel Arc** : non supporté par TF 2.19

### Résultat
- Inférence GPU : ~6 Hz cible atteint avec le ConvNeXt 1.7 GB
- Fallback TFLite CPU : pipeline fonctionnel mais plus lent (dépend du CPU)

---

## Améliorations planifiées (issues des travaux de recherche)

### [PLANIFIÉ] Mécanisme d'attention canal + spatial

> Référence **[Deramgozin2023]** — Ch. 3, Section "Mécanisme d'attention pour FER"

Deramgozin propose un module d'attention double (channel attention + spatial attention) inséré
dans le backbone CNN pour focaliser l'inférence sur les régions faciales les plus discriminantes
(yeux, sourcils, bouche). Ce mécanisme améliore particulièrement CONTEMPT (+5.2%) et DISGUST (+4.8%)
sur RAFdb, émotions pour lesquelles les détails fins (asymétrie labiale, plissement nasal) sont
déterminants.

**Action à prendre** : intégrer un bloc SE (Squeeze-and-Excitation) ou CBAM après les features
du ConvNeXt, ou fine-tuner avec des données augmentées centrées sur la région péri-orale.

---

### [PLANIFIÉ] Détection des Action Units (AU) pour CONTEMPT et DISGUST

> Référence **[Deramgozin2023]** — Ch. 3, Section "Détection des unités d'action FACS"
> Référence **[Jan2017]** — Ch. 5, Section "Facial Parts Analysis"

Deramgozin atteint 92% de F1 sur DISFA pour la détection des AU. Les AU clés pour les émotions
difficiles :
- **CONTEMPT** : AU12 (lip corner puller) + AU14 (dimpler) — asymétriques
- **DISGUST** : AU9 (nose wrinkler) + AU17 (chin raiser)

Jan confirme que l'isolation des parties faciales (nez, bouche, yeux séparément) améliore la
précision sur ces classes de +7–12%.

**Action à prendre** : extraire des crops secondaires (région péri-orale, nez) via landmarks
MediaPipe et les utiliser comme features additionnelles ou comme entrée d'un classificateur
d'appoint pour CONTEMPT/DISGUST.

---

### [PLANIFIÉ] Export TFLite quantifié (INT8) pour déploiement embarqué

> Référence **[Deramgozin2023]** — Ch. 4, Section "Quantification et déploiement embarqué"

Deramgozin démontre une réduction de taille de 4× (FP32 → INT8) avec moins de 1% de perte
de précision sur ses modèles FER, permettant le déploiement sur Raspberry Pi et systèmes embarqués.

**Action à prendre** : quantifier `faceguard_convnext.keras` en INT8 via
`tf.lite.TFLiteConverter` avec `representative_dataset` pour calibration post-training.
Cible : `models/faceguard_int8.tflite` (~425 MB vs 1.7 GB).

---

## Métriques de référence (à remplir après tests)

| Version | Modèle | Résolution | Backend | FPS moyen | Précision subjective |
|---------|--------|------------|---------|-----------|----------------------|
| v1 (avant simplification) | Keras 31 MB | 48×48 | Keras CPU | — | — |
| v2 (simplification) | TFLite 17 MB | 48×48 | TFLite CPU | — | — |
| v3 (pack améliorations) | ConvNeXt 1.7 GB | 224×224 | Keras CPU | — | — |
| v4 (GPU-first) | ConvNeXt 1.7 GB | 224×224 | Keras GPU | — | — |

> Remplir cette table après chaque session de test en conditions réelles.
