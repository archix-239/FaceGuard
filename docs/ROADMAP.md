# Roadmap FaceGuard V2 — Liste complète des améliorations

> Basé exclusivement sur :
> - **[Jan2017]** — Asim Jan, *Deep Learning based Facial Expression Recognition and its Applications*, Brunel University London, 2017
> - **[Deramgozin2023]** — MohammadMahdi Deramgozin, *Développement de modèles de reconnaissance des expressions faciales à base d'apprentissage profond pour les applications embarquées*, Université de Lorraine, 2023

Chaque entrée indique : **complexité** (1=trivial → 5=refonte majeure), **priorité** (P0=critique → P3=nice-to-have), **référence**, **effort estimé**.

---

## TIER 1 — Quick wins runtime (complexité 1–2, aucune modification du modèle)

Ces améliorations s'appliquent au code existant, sans retraining ni changement d'architecture.

### 1.1 — ~~Afficher la confiance de la prédiction (%) dans l'UI~~ FAIT
- **Complexité** : 1/5 — **Priorité** : P0 — **Effort** : 15 min
- **Statut** : **FAIT** (2026-04-16) — déjà implémenté dans `draw_face()` : `f"{emo}  {conf:.0%}"`
- Ajout du flag `--backend` en CLI et lecture auto de la taille d'entrée depuis le backend

### 1.2 — ~~Buffer de probabilités par piste (historique court)~~ FAIT
- **Complexité** : 2/5 — **Priorité** : P1 — **Effort** : 30 min
- **Statut** : **FAIT** (2026-04-16) — `prob_history` (deque, 10 entrées) + sparkline confiance sous chaque bbox
- **Réf.** : [Deramgozin2023] Ch.2

### 1.3 — ~~Exposer les paramètres d'augmentation CLAHE dans la config~~ FAIT
- **Complexité** : 1/5 — **Priorité** : P2 — **Effort** : 10 min
- **Statut** : **FAIT** (2026-04-16) — `clip_limit`, `tile_grid_size` et toggle `enabled` dans `default.yaml`

### 1.4 — ~~Toggle runtime GPU/CPU (hotkey ou flag CLI)~~ FAIT
- **Complexité** : 2/5 — **Priorité** : P2 — **Effort** : 1h
- **Statut** : **FAIT** (2026-04-16) — flag `--cpu` désactive le GPU via config

### 1.5 — ~~Snapshot sur touche (capture du visage aligné actuel)~~ FAIT
- **Complexité** : 2/5 — **Priorité** : P2 — **Effort** : 30 min
- **Statut** : **FAIT** (2026-04-16) — touche `S` sauvegarde crop + probas dans `captures/`

---

## TIER 2 — Préprocessing amélioré (complexité 2–3, code seulement)

Améliorations de qualité sans retraining du modèle principal.

### 2.1 — ~~Tracking quality score (qualité du visage)~~ FAIT
- **Complexité** : 2/5 — **Priorité** : P1 — **Effort** : 2h
- **Statut** : **FAIT** (2026-04-16) — `face_quality()` évalue taille, angle, netteté ; seuil configurable `quality_threshold`
- **Réf.** : [Jan2017] Ch.1, Section 1.2.1

### 2.2 — ~~Crop élargi avec marge contextuelle~~ FAIT
- **Complexité** : 2/5 — **Priorité** : P1 — **Effort** : 1h
- **Statut** : **FAIT** (2026-04-16) — `eye_width_ratio` (0.40→0.34) et `eye_y_position` (0.38→0.36) configurables
- **Réf.** : [Deramgozin2023] Ch.2

### 2.3 — Détection de visage via FaceMesh plutôt que bbox MediaPipe
- **Complexité** : 3/5 — **Priorité** : P2 — **Effort** : 3h
- **Description** : Dériver le bbox depuis l'enveloppe convexe des 468 landmarks → plus stable qu'un bbox direct
- **Réf.** : [Jan2017] Ch.4.3.2 — alignment par landmarks donne des crops cohérents

### 2.4 — ~~Normalisation d'intensité globale (histogramme ou z-score)~~ FAIT
- **Complexité** : 2/5 — **Priorité** : P2 — **Effort** : 1h
- **Statut** : **FAIT** (2026-04-16) — `preprocessing.normalize` configurable (`minmax` ou `zscore`)
- **Réf.** : [Jan2017] Ch.3

---

## TIER 3 — Interprétabilité & explicabilité (complexité 2–3)

Ajoute de la visibilité sur les décisions du modèle, sans changer le modèle.

### 3.1 — ~~Grad-CAM overlay sur le visage~~ FAIT
- **Complexité** : 3/5 — **Priorité** : P1 — **Effort** : 4h
- **Statut** : **FAIT** (2026-04-16) — heatmap Grad-CAM superposée sur le bbox (35% opacité, JET colormap)
- **Réf.** : [Deramgozin2023] Ch.3.5.3

### 3.2 — LIME pour expliquer les prédictions à la demande
- **Complexité** : 4/5 — **Priorité** : P3 — **Effort** : 1 jour
- **Description** : Touche `L` pour lancer LIME sur le crop courant et afficher les super-pixels discriminants
- **Réf.** : [Deramgozin2023] Ch.2.3, Section LIME

### 3.3 — ~~Mapping émotion → AU affichées en surimpression~~ FAIT
- **Complexité** : 2/5 — **Priorité** : P2 — **Effort** : 2h
- **Statut** : **FAIT** (2026-04-16) — table FACS `EMOTION_AUS` + AU affichées sous le bbox
- **Réf.** : [Deramgozin2023] Table 3.1

---

## TIER 4 — Data augmentation & retraining léger (complexité 3)

Modifications nécessitant un fine-tuning (pas un entraînement from scratch).

### 4.1 — Fine-tuner le ConvNeXt avec augmentation [Jan2017/Deramgozin2023]
- **Complexité** : 3/5 — **Priorité** : P1 — **Effort** : 1–2 jours
- **Description** : Fine-tuning sur RAF-DB ou AffectNet avec augmentation standardisée :
  - Rotation aléatoire ±30°
  - Cisaillement 0.3
  - Zoom 0.3
  - Flip horizontal 50%
  - Normalisation /255
- **Réf.** : [Deramgozin2023] Ch.2.4.2 — pipeline d'augmentation validé expérimentalement

### 4.2 — Weighted cross-entropy pour classes déséquilibrées
- **Complexité** : 3/5 — **Priorité** : P1 — **Effort** : 4h
- **Description** : Lors du fine-tuning, utiliser l'entropie croisée pondérée (poids inversement proportionnels à la fréquence des classes) pour améliorer CONTEMPT/DISGUST/FEAR sous-représentés
- **Réf.** : [Deramgozin2023] Ch.3 — pondération résout le déséquilibre RAFdb/FER2013+

### 4.3 — Retrainer avec landmarks alignés cohérents
- **Complexité** : 3/5 — **Priorité** : P2 — **Effort** : 1 jour
- **Description** : Régénérer le dataset d'entraînement en utilisant exactement le même `align_face()` que celui utilisé à l'inférence, pour éliminer le décalage train/inference
- **Réf.** : [Jan2017] Ch.4.3.2 — consistency d'alignement train/test critique

---

## TIER 5 — Architecture avancée (complexité 4, retraining complet)

Modifications de l'architecture du modèle. Nécessitent un entraînement from scratch ou transfer learning lourd.

### 5.1 — Intégration du mécanisme d'attention CBAM (canal + spatial)
- **Complexité** : 4/5 — **Priorité** : P0 — **Effort** : 3–5 jours
- **Description** : Insérer deux blocs CBAM (Woo et al. 2018) dans le backbone ConvNeXt :
  - Bloc 1 : après les premières couches conv (features bas niveau)
  - Bloc 2 : après les dernières couches conv (features haut niveau)
- **Gains mesurés par Deramgozin** : RAFdb 60% → 83% → **94.87%** avec attention ; FER2013+ 81.4% → **92.15%**
- **Réf.** : [Deramgozin2023] Ch.4 — résultats publiés, architecture open

### 5.2 — Classification multi-label sur Action Units + décodage FACS
- **Complexité** : 4/5 — **Priorité** : P0 — **Effort** : 1 semaine
- **Description** : Remplacer la classification directe 8 classes par :
  1. Détection multi-label de 13 AU (sortie sigmoïde, une par AU)
  2. Décodage FACS vers émotion via distance euclidienne au vecteur de référence Ekman
- **Gains mesurés** : DISFA F1 0.92 (SOTA) — meilleur sur CONTEMPT/DISGUST car l'AU9 (nez) et AU14 (dimpler) sont explicitement détectés
- **Réf.** : [Deramgozin2023] Ch.3 — architecture complète + Table 3.1

### 5.3 — Apprentissage joint des parties faciales (facial parts joint learning)
- **Complexité** : 5/5 — **Priorité** : P2 — **Effort** : 2 semaines
- **Description** : Au lieu d'un CNN sur le visage entier, extraire 4 crops (bouche, yeux, sourcils, nez) et les traiter par un CNN multi-branches avec Joint Bayesian pour la classification finale
- **Gains mesurés par Jan** : +1.6% whole face → parts ; +5.78% individual part → best combination (Mouth+Eyes+Nose = 80.30%)
- **Réf.** : [Jan2017] Ch.4 — Experiment 4A+4B, architecture et résultats
- **Note** : Complexe car nécessite extraction des parts via les 468 landmarks MediaPipe puis pipeline multi-entrées

---

## TIER 6 — Optimisation déploiement (complexité 3–4)

Pour le déploiement sur machines modestes ou embarqué.

### 6.1 — Restructuration du modèle (réduction des filtres)
- **Complexité** : 3/5 — **Priorité** : P2 — **Effort** : 2 jours
- **Description** : Réduire drastiquement le nombre de filtres du ConvNeXt (Deramgozin passe de 32/64/128/128/64 → 16/16/32/32/32 → ×26 réduction taille sans perte de précision)
- **Gains mesurés** : 1.5M params → 57K params ; 5.4 MB → 280 KB, précision FER2013+ : 92.12% → 92.11%
- **Réf.** : [Deramgozin2023] Ch.5.3.1, Algorithme 1 + Table 5.1

### 6.2 — Pruning pondéral par amplitude (50% → 80%)
- **Complexité** : 3/5 — **Priorité** : P2 — **Effort** : 1 jour
- **Description** : Pruner progressivement les poids les plus petits du modèle (TF Model Optimization Toolkit)
- **Réf.** : [Deramgozin2023] Ch.5.3.2 — méthode magnitude-based pruning

### 6.3 — Quantification TFLite (INT8 / Float16 / Dynamic range)
- **Complexité** : 3/5 — **Priorité** : P1 — **Effort** : 1 jour
- **Description** : Trois modes :
  - **Dynamic range** : poids 32b → 8b (la plus petite taille)
  - **Float16** : optimal pour GPU accelerators
  - **Float32** : compat max
- **Gains mesurés** : 74 KB → 30 KB (dynamic range) sans perte significative
- **Réf.** : [Deramgozin2023] Ch.5.3.2 + Table 5.3

### 6.4 — Distillation de connaissance (ConvNeXt → modèle léger)
- **Complexité** : 4/5 — **Priorité** : P3 — **Effort** : 1 semaine
- **Description** : Utiliser le ConvNeXt 1.7 GB comme professeur pour entraîner un modèle étudiant beaucoup plus petit (type MobileNetV3 ou Deramgozin-57K)
- **Réf.** : [Deramgozin2023] Ch.5.2 — discussion des stratégies d'optimisation

---

## TIER 7 — Temporel avancé (complexité 4–5)

Exploitation de la dimension temporelle au-delà de l'EMA.

### 7.1 — FDHH (Feature Dynamic History Histogram) pour émotions dynamiques
- **Complexité** : 5/5 — **Priorité** : P3 — **Effort** : 2–3 semaines
- **Description** : Implémenter le descripteur temporel FDHH de Jan pour capturer l'évolution d'une expression sur une séquence vidéo
- **Réf.** : [Jan2017] Ch.6 — état de l'art pour la détection de dépression, adapté à la FER temporelle
- **Usage cible** : Distinguer les émotions spontanées des expressions feintes

### 7.2 — Buffer long avec confirmation d'émotion stable
- **Complexité** : 3/5 — **Priorité** : P2 — **Effort** : 4h
- **Description** : Considérer une émotion comme « confirmée » seulement après N frames consécutives au-dessus d'un seuil de confiance
- **Réf.** : [Deramgozin2023] Ch.2 — stabilité temporelle des prédictions

---

## Récapitulatif : plan de route recommandé

### Phase 1 — Polish immédiat (1 semaine, impact élevé / effort faible)
1. **1.1** Afficher la confiance dans l'UI
2. **2.1** Tracking quality score (filtre qualité)
3. **2.2** Crop élargi avec marge
4. **3.1** Grad-CAM overlay
5. **3.3** Mapping émotion→AU affiché

### Phase 2 — Qualité de reconnaissance (2–4 semaines)
6. **4.1** Fine-tuning avec augmentation standard
7. **4.2** Weighted cross-entropy
8. **6.3** Export TFLite quantifié (pour déploiement)

### Phase 3 — Breakthrough qualité (1–2 mois)
9. **5.1** Mécanisme d'attention CBAM (+13% sur FER2013+ selon Deramgozin)
10. **5.2** AU multi-label + décodage FACS (SOTA sur DISFA)

### Phase 4 — Embarqué (optionnel, 1 mois)
11. **6.1** Restructuration filtres (×26 réduction)
12. **6.2** Pruning
13. **6.4** Distillation

### Phase 5 — Recherche avancée (optionnel)
14. **5.3** Facial parts joint learning
15. **7.1** FDHH temporel

---

## Matrice priorité × complexité

```
Priorité ↓   Complexité →   1          2          3          4          5
P0 (critique)              1.1        -          -          5.1, 5.2   -
P1 (élevée)                -          2.1, 2.2   3.1, 4.1   -          -
                                      1.2        4.2, 6.3
P2 (moyenne)               1.3        1.5, 3.3   2.3, 2.4   6.1, 6.2   5.3
                                      1.4        7.2        -          -
P3 (faible)                -          -          -          3.2, 6.4   7.1
```

**Règle d'or** : commencer par les cases P0/P1 avec complexité 1–3 → maximum d'impact pour un effort minimal.

---

## Sources (rappel)

- **[Jan2017]** — Contribution principale au projet : préprocessing (CLAHE LAB, alignment), facial parts, augmentation, FDHH temporel
- **[Deramgozin2023]** — Contribution principale au projet : architecture CBAM, AU multi-label, quantification TFLite, restructuration embarqué
