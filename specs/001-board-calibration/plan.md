# Implementation Plan: Calibration du Plateau

**Branch**: `001-board-calibration` | **Date**: 2026-08-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-board-calibration/spec.md`

## Summary

L'opérateur désigne les quatre coins internes du plateau (a1, h1, a8, h8) en cliquant sur le flux vidéo en direct de la caméra ZED X, exposé via une page web. Le backend calcule une transformation perspective (homographie) à partir de ces 4 points pour dériver les 64 cases, superpose la grille résultante sur l'image pour validation visuelle, puis — une fois confirmée — persiste la calibration (région image + région de profondeur par case) dans un fichier de configuration afin qu'elle soit réutilisable au prochain lancement sans hypothèse codée en dur sur le plateau physique.

## Technical Context

**Language/Version**: Python 3.10 (version fournie par JetPack/Ubuntu 22.04 sous ROS 2 Humble)

**Primary Dependencies**: ROS 2 Humble (rclpy), `zed-ros2-wrapper` (flux image + profondeur de la ZED X), OpenCV (`cv2.getPerspectiveTransform` / calcul d'homographie et de régions de case — nouvelle dépendance légère, cohérente avec le traitement d'image déjà requis, à confirmer en Phase 0), FastAPI (endpoints de calibration + page HTML/JS de clic sur l'image)

**Storage**: fichier de configuration local (YAML), un par calibration active, sur le système de fichiers du Jetson — pas de base de données (choix confirmé en Phase 0)

**Testing**: pytest pour la logique pure (calcul de grille à partir de 4 points, validation de quadrilatère) ; validation manuelle guidée (`quickstart.md`) pour les scénarios nécessitant la caméra physique, non automatisable en CI

**Target Platform**: Jetson Orin 64GB (JetPack/Ubuntu, aarch64) ; interface consultée via navigateur (Mac ou téléphone) sur le Wi-Fi local — aucune exécution CUDA/ROS2/ZED côté client

**Project Type**: service web + package ROS 2, au sein d'un workspace ROS 2 partagé par les futures features du projet

**Performance Goals**: aperçu de la grille superposée mis à jour en moins de 200ms après chaque clic ; calibration complète (4 clics + vérification + confirmation) réalisable en moins de 60s (SC-001)

**Constraints**: aucun démarrage automatique au boot (Principe III) ; lancement/arrêt manuel avec libération propre de la caméra ; dépendances Python isolées dans un venv dédié au workspace ; `ROS_DOMAIN_ID` dédié au projet ; aucune action sur le bras dans cette feature (pas de MoveIt2 impliqué)

**Scale/Scope**: un seul opérateur, un seul plateau/une seule caméra actifs à la fois ; 64 cases par calibration

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Évaluation |
|---|---|
| I. Vision Agnostique au Plateau | **Conforme** — cette feature est l'implémentation directe du Principe I : calibration manuelle 4 points comme référence, aucune hypothèse codée en dur sur taille/couleur/bordure du plateau (FR-003). |
| II. Occupation par Profondeur | **Conforme** — cette feature ne fait aucune classification de pièce ; elle prépare uniquement la région de profondeur par case (FR-007) que la feature suivante (détection d'occupation) consommera. |
| III. Bonne Citoyenneté sur Jetson Partagé | **Conforme, à vérifier en implémentation** — le node caméra/calibration doit démarrer uniquement via le script de lancement manuel du projet, libérer la caméra ZED X proprement à l'arrêt, et utiliser le `ROS_DOMAIN_ID` dédié du projet. Aucun service `restart: always`. |
| IV. Développement Distant, Exécution Cible | **Conforme** — l'interface est une page web servie depuis le Jetson ; le Mac ne fait qu'afficher un navigateur, aucun driver local requis. |
| V. Manipulation Sûre | **N/A pour cette feature** — aucun mouvement du bras n'est impliqué dans la calibration du plateau. |
| VI. Difficulté = Paramètre du Moteur | **N/A pour cette feature** — aucune interaction avec le moteur d'échecs. |

Aucune violation ; la section Complexity Tracking reste vide.

## Project Structure

### Documentation (this feature)

```text
specs/001-board-calibration/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── calibration-api.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
ros2_ws/
└── src/
    ├── robochess_vision/                    # package ROS 2 : calibration + accès caméra/profondeur
    │   ├── robochess_vision/
    │   │   ├── grid_mapping.py              # pur Python/OpenCV : 4 points -> 64 régions image+profondeur (unit-testable sans ROS ni caméra)
    │   │   └── calibration_node.py          # node rclpy : détient la calibration active, expose les services utilisés par robochess_web, persiste/charge le YAML
    │   ├── config/
    │   │   └── calibration.yaml             # calibration persistée (créée/écrasée à l'exécution, pas versionnée)
    │   ├── test/
    │   │   └── test_grid_mapping.py
    │   ├── package.xml
    │   └── setup.py
    │
    └── robochess_web/                       # package ROS 2 : backend FastAPI + UI de calibration
        ├── robochess_web/
        │   ├── app.py                       # app FastAPI, monte les routers et les fichiers statiques
        │   ├── routers/
        │   │   └── calibration.py           # endpoints définis dans contracts/calibration-api.md
        │   └── static/
        │       └── calibration/
        │           ├── index.html           # flux vidéo + gestion des clics + overlay de grille
        │           └── calibration.js
        ├── test/
        │   └── test_calibration_router.py
        ├── package.xml
        └── setup.py
```

**Structure Decision**: workspace ROS 2 (`ros2_ws/src/`) avec deux packages : `robochess_vision` (logique de calibration pure + accès caméra/profondeur côté ROS 2) et `robochess_web` (backend FastAPI + UI web). Cette séparation isole la logique testable sans matériel (`grid_mapping.py`) du reste, et anticipe la réutilisation de `robochess_web` par les futures features (sélection de difficulté, suivi de partie) sans coupler l'UI au détail d'implémentation ROS 2. Les futures features (détection d'occupation, contrôle du bras, moteur d'échecs) ajouteront leurs propres packages dans le même workspace plutôt que de modifier cette structure.

## Complexity Tracking

*Aucune violation de la Constitution Check — section non applicable.*
