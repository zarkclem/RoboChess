# Phase 0 Research: Calibration du Plateau

## 1. Calcul de la grille à partir des 4 points

**Decision**: Utiliser une transformation perspective (homographie) calculée par `cv2.getPerspectiveTransform` à partir des 4 coins cliqués (a1, h1, a8, h8) mappés vers un carré normalisé 8×8, puis projeter les 64 sous-carrés normalisés vers l'image d'origine via l'homographie inverse pour obtenir le quadrilatère de chaque case.

**Rationale**: C'est l'approche standard pour dériver une grille régulière à partir de 4 points de coin en présence de perspective (le plateau n'est pas nécessairement vu du dessus) — exactement le cas d'usage couvert par le Principe I ("aucune hypothèse sur la taille, la couleur ou la largeur de bordure"). OpenCV est une dépendance légère, déjà quasi incontournable pour tout traitement d'image ROS 2, et ne contredit aucun principe de la constitution.

**Alternatives considered**:
- Interpolation bilinéaire simple (grille régulière sans homographie) : rejetée car suppose une vue orthogonale (caméra parfaitement au-dessus), ce qui n'est pas garanti et romprait le Principe I dès qu'un angle de caméra existe.
- Détection automatique de coins/lignes (Hough) pour affiner les clics : hors scope de cette feature (explicitement exclu par la description utilisateur et le Principe I, qui la réserve à un complément best-effort futur).

## 2. Association région image → région de profondeur par case

**Decision**: Pour chaque case, définir une région de profondeur = une sous-fenêtre centrée (ex. 50% de la surface de la case) à l'intérieur du quadrilatère image de la case, afin de limiter l'échantillon de profondeur aux pixels les plus susceptibles d'appartenir à une pièce posée au centre de la case plutôt qu'aux bords partagés avec les cases voisines.

**Rationale**: Réduit le risque de contamination du signal de profondeur par une pièce sur une case adjacente ou par le bord de la case, sans introduire d'hypothèse sur le plateau lui-même (le facteur de réduction s'applique uniformément, indépendamment de la taille réelle de la case). Reste une donnée pure de calibration (pas de logique de diff/occupation, qui appartient à la feature suivante).

**Alternatives considered**:
- Région de profondeur = quadrilatère complet de la case : rejetée, trop sensible aux pièces des cases voisines en vue oblique.
- Un unique point central (au lieu d'une sous-région) : rejeté, trop sensible au bruit ponctuel du capteur de profondeur ; une petite région permet une moyenne/médiane plus robuste (détail d'implémentation pour la feature de détection d'occupation, mais la région doit être définie ici).

## 3. Persistance de la calibration

**Decision**: Sérialiser la calibration confirmée (points cliqués + métadonnées + régions dérivées) en un fichier YAML unique (`config/calibration.yaml`) sur le disque du Jetson, chargé automatiquement au démarrage du node de calibration s'il existe.

**Rationale**: FR-009 (SC-004) exige une reprise sans recalibration après redémarrage tant que le plateau/la caméra n'ont pas bougé. Un fichier plat est suffisant pour un seul profil de calibration actif (cf. Assumptions du spec : un seul plateau à la fois) — pas besoin d'une base de données. YAML reste lisible/inspectable manuellement pendant le développement, cohérent avec le reste de la config ROS 2 (launch files, params).

**Alternatives considered**:
- Base de données (SQLite) : rejetée, sur-dimensionnée pour un seul enregistrement actif à la fois.
- JSON : équivalent techniquement à YAML ; YAML retenu par cohérence avec les fichiers de config ROS 2 typiques du reste du projet.

## 4. Pont entre le node ROS 2 (caméra/calibration) et le backend web FastAPI

**Decision**: `robochess_web` communique avec `robochess_vision` via les mécanismes standard ROS 2 (services/topics `rclpy`), en exécutant un client ROS 2 minimal dans le processus FastAPI (ou dans un thread dédié) plutôt que d'accéder directement au SDK ZED depuis le backend web.

**Rationale**: Respecte la séparation des responsabilités du Principe III (isolation, un seul point d'accès au périphérique caméra) et l'architecture ROS 2 déjà retenue pour le reste du projet (constitution : ROS 2 + `zed-ros2-wrapper`). Évite les conflits d'accès matériel si plusieurs clients tentaient d'ouvrir la caméra directement.

**Alternatives considered**:
- Accès direct au SDK ZED depuis FastAPI, en parallèle du node ROS 2 : rejeté, risque de conflit d'accès au périphérique caméra et duplication de la gestion du flux profondeur déjà exposée par `zed-ros2-wrapper`.
- `rosbridge_suite` (WebSocket JSON) entre navigateur et ROS 2 directement, sans backend FastAPI intermédiaire : rejeté pour cette feature — FastAPI reste nécessaire pour servir l'UI et sera réutilisé par les futures features (sélection de difficulté, suivi de partie déjà prévues dans la constitution), autant centraliser le pont ROS 2↔HTTP à un seul endroit.

## 5. Stratégie de test

**Decision**: Couvrir par tests unitaires `pytest` uniquement la logique pure sans dépendance matérielle (`grid_mapping.py` : calcul d'homographie, dérivation des 64 régions, détection de quadrilatère dégénéré — FR-003, FR-006). Les scénarios nécessitant la caméra physique (US1, US2, US3 de bout en bout) sont validés manuellement via `quickstart.md`, non exécutables en CI.

**Rationale**: Cohérent avec le Principe IV (le code s'exécute sur le Jetson, pas de simulation caméra/ROS2 sur le Mac) — une CI classique n'a pas accès à la caméra ZED X ni au Jetson. Séparer la logique pure (`grid_mapping.py`) du node ROS 2 (`calibration_node.py`) permet malgré tout une couverture automatisée significative sur la partie la plus sujette aux erreurs (géométrie, validation).

**Alternatives considered**:
- Mock complet du SDK ZED pour simuler des tests d'intégration en CI : jugé disproportionné pour cette feature ; à reconsidérer si la complexité de `calibration_node.py` augmente dans une itération future.
