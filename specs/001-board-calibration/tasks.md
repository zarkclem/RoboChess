---

description: "Task list template for feature implementation"
---

# Tasks: Calibration du Plateau

**Input**: Design documents from `/specs/001-board-calibration/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/calibration-api.md](./contracts/calibration-api.md), [quickstart.md](./quickstart.md)

**Tests**: Le plan (`plan.md`) désigne explicitement `test/test_grid_mapping.py` et `test/test_calibration_router.py` comme livrables (research.md §5 : logique pure testable en CI, reste validé manuellement via quickstart.md). Les tâches de test ci-dessous se limitent à cette portée — pas de TDD exhaustif sur chaque couche.

**Organization**: Tâches groupées par user story (spec.md) pour permettre une implémentation et une validation indépendantes de chacune.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut être fait en parallèle (fichiers différents, pas de dépendance sur une tâche non terminée)
- **[Story]**: US1 (P1), US2 (P2) ou US3 (P3) — cf. spec.md
- Chemins de fichiers exacts inclus dans chaque description

## Path Conventions

Workspace ROS 2 à deux packages, cf. `plan.md` § Project Structure : `ros2_ws/src/robochess_vision/` (calibration pure + node ROS 2) et `ros2_ws/src/robochess_web/` (backend FastAPI + UI).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialisation du workspace et des deux packages

- [X] T001 Créer le squelette des deux packages ROS 2 (`package.xml`, `setup.py`, `__init__.py`) pour `ros2_ws/src/robochess_vision/` et `ros2_ws/src/robochess_web/` selon la structure de `plan.md`
- [X] T002 [P] Créer un venv Python dédié au workspace et déclarer les dépendances (`opencv-python`, `fastapi`, `uvicorn`, `pyyaml`, `pytest`) dans `ros2_ws/requirements.txt` (Principe III — isolation des dépendances)
- [X] T003 [P] Documenter un `ROS_DOMAIN_ID` dédié au projet dans `ros2_ws/.env.example` (Principe III — pas d'interférence avec le graphe ROS2 d'un autre utilisateur)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cœur partagé par les trois user stories

**⚠️ CRITICAL**: Aucune user story ne peut être testée avant la fin de cette phase

- [X] T004 Implémenter `compute_grid(corner_points) -> list[Square]` (homographie 4 points → 64 régions image + régions de profondeur resserrées, rejet des quadrilatères dégénérés — research.md §1-2, data-model.md) dans `ros2_ws/src/robochess_vision/robochess_vision/grid_mapping.py`
- [X] T005 [P] Tests unitaires de `compute_grid` (4 points valides → 64 cases correctement dérivées ; points quasi alignés/trop proches → rejet, FR-006) dans `ros2_ws/src/robochess_vision/test/test_grid_mapping.py`
- [X] T006 Implémenter `calibration_node.py` : node `rclpy` détenant la `Calibration` en mémoire (machine à états `draft`/`confirmed`, ordre de saisie des coins a1→h1→a8→h8) avec les opérations `start_draft`/`add_point`/`confirm`/`discard` (data-model.md) dans `ros2_ws/src/robochess_vision/robochess_vision/calibration_node.py`
- [X] T007 Implémenter le squelette FastAPI (`app.py`) montant le router de calibration et le dossier `static/`, plus le pont client `rclpy` vers `calibration_node` (research.md §4) dans `ros2_ws/src/robochess_web/robochess_web/app.py`
- [X] T008 [P] Ébaucher `static/calibration/index.html` et `calibration.js` (affichage du flux caméra en direct, gestionnaire de clic minimal, sans appel API pour l'instant) dans `ros2_ws/src/robochess_web/robochess_web/static/calibration/`

**Checkpoint**: infrastructure prête — les user stories peuvent commencer.

---

## Phase 3: User Story 1 - Calibrer le plateau en début de partie (Priority: P1) 🎯 MVP

**Goal**: L'opérateur clique les 4 coins, vérifie la grille superposée, confirme — la calibration est active pour la session (spec.md US1).

**Independent Test**: Suivre `quickstart.md` étapes 1-3 : lancer le système, ouvrir la page de calibration, cliquer les 4 coins, vérifier l'overlay, confirmer, vérifier le rejet d'un quadrilatère dégénéré.

- [X] T009 [US1] Implémenter `POST /api/calibration/start` dans `ros2_ws/src/robochess_web/robochess_web/routers/calibration.py`
- [X] T010 [US1] Implémenter `POST /api/calibration/point` (collecte ordonnée des coins, `next_corner` dans la réponse — FR-002, calcul de `preview_grid` au 4e point, `422 degenerate_quadrilateral` si rejeté — FR-006) dans `ros2_ws/src/robochess_web/robochess_web/routers/calibration.py`
- [X] T011 [US1] Implémenter `POST /api/calibration/confirm` (exige 4 points valides, calcule les 64 `Square` finales via `grid_mapping`, promeut `draft` → `confirmed` — FR-007) dans `ros2_ws/src/robochess_web/robochess_web/routers/calibration.py`
- [X] T012 [US1] Implémenter `POST /api/calibration/discard` (FR-005) dans `ros2_ws/src/robochess_web/robochess_web/routers/calibration.py`
- [X] T013 [P] [US1] Tests des endpoints start/point/confirm/discard (y compris les cas d'erreur 422/409) dans `ros2_ws/src/robochess_web/test/test_calibration_router.py`
- [X] T014 [P] [US1] Implémenter le flux de clic UI : mise en évidence du prochain coin attendu (FR-002), envoi des clics à `/point`, rendu de l'overlay de grille retourné dans `ros2_ws/src/robochess_web/robochess_web/static/calibration/calibration.js`
- [X] T015 [P] [US1] Implémenter les contrôles UI de confirmation/annulation avec retour visuel (FR-004, FR-005) dans `ros2_ws/src/robochess_web/robochess_web/static/calibration/index.html`
- [X] T016 [US1] Afficher un avertissement clair dans l'UI si le flux caméra est indisponible pendant la séquence (`503 camera_unavailable`, FR-011) dans `ros2_ws/src/robochess_web/robochess_web/static/calibration/calibration.js`

**Checkpoint**: US1 livrable et testable seule — calibration manuelle complète sur une session.

---

## Phase 4: User Story 2 - Recalibrer après un déplacement de la caméra ou du plateau (Priority: P2)

**Goal**: L'opérateur déclenche une nouvelle calibration à tout moment ; l'ancienne reste active jusqu'à confirmation de la nouvelle (spec.md US2).

**Independent Test**: Suivre `quickstart.md` étape 4 : après une calibration confirmée, déplacer légèrement la caméra, déclencher `/start`, confirmer une nouvelle calibration, vérifier que l'ancienne n'est plus utilisée.

- [X] T017 [US2] S'assurer que `start_draft()` dans `calibration_node.py` ne modifie pas la `Calibration` `confirmed` existante tant que le nouveau `confirm()` n'a pas réussi (remplacement atomique — FR-010) dans `ros2_ws/src/robochess_vision/robochess_vision/calibration_node.py`
- [X] T018 [P] [US2] Ajouter un contrôle "Recalibrer" persistant dans l'UI, visible dès qu'une calibration confirmée est active, déclenchant `POST /api/calibration/start` dans `ros2_ws/src/robochess_web/robochess_web/static/calibration/index.html`

**Checkpoint**: US2 livrable et testable seule, par-dessus US1.

---

## Phase 5: User Story 3 - Reprendre une session sans recalibrer (Priority: P3)

**Goal**: Au redémarrage, la dernière calibration confirmée est rechargée automatiquement si rien n'a bougé (spec.md US3).

**Independent Test**: Suivre `quickstart.md` étape 5 : après une calibration confirmée, redémarrer le système, vérifier via `GET /api/calibration/status` que la calibration précédente est active sans repasser par la séquence de clics.

- [X] T019 [US3] Implémenter la persistance YAML : écrire la `Calibration` confirmée dans `ros2_ws/src/robochess_vision/config/calibration.yaml` à chaque confirmation (research.md §3, FR-009) dans `ros2_ws/src/robochess_vision/robochess_vision/calibration_node.py`
- [X] T020 [US3] Charger `config/calibration.yaml` au démarrage de `calibration_node.py` s'il existe, en restaurant l'état `confirmed` automatiquement (FR-009, SC-004) dans `ros2_ws/src/robochess_vision/robochess_vision/calibration_node.py`
- [X] T021 [P] [US3] Implémenter `GET /api/calibration/status` dans `ros2_ws/src/robochess_web/robochess_web/routers/calibration.py`
- [X] T022 [P] [US3] Au chargement de la page, appeler `/api/calibration/status` et passer directement à la vue "prêt à jouer" si `confirmed`, en proposant "Recalibrer" plutôt que d'imposer la séquence de clics dans `ros2_ws/src/robochess_web/robochess_web/static/calibration/calibration.js`

**Checkpoint**: US3 livrable et testable seule, par-dessus US1 (+ US2 si présente).

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T023 [P] Ajouter un launch file démarrant `robochess_vision` + `robochess_web` ensemble, avec libération propre de la caméra à l'arrêt (Principe III) dans `ros2_ws/src/robochess_vision/launch/calibration.launch.py`
- [ ] T024 [P] Exécuter le protocole de validation manuelle complet de `specs/001-board-calibration/quickstart.md` sur le matériel réel (deux plateaux visuellement différents) et consigner les résultats face à SC-001–SC-005 dans `specs/001-board-calibration/quickstart.md`

---

## Dependencies & Execution Order

- **Phase 1 (Setup)** : aucune dépendance, démarre en premier.
- **Phase 2 (Foundational)** : dépend de Phase 1 ; bloque toutes les user stories.
- **Phase 3 (US1, P1)** : dépend de Phase 2 uniquement — c'est le MVP.
- **Phase 4 (US2, P2)** : dépend de Phase 3 (réutilise `/start`/`/confirm` et l'état `confirmed` établis par US1).
- **Phase 5 (US3, P3)** : dépend de Phase 3 (persiste/recharge la calibration confirmée établie par US1) ; indépendante de Phase 4 — US2 et US3 peuvent être menées en parallèle par deux personnes/threads différents une fois US1 terminée.
- **Phase 6 (Polish)** : après les user stories ciblées pour la release.

## Parallel Execution Examples

- Dans Phase 2 : T005, T007, T008 peuvent être menées en parallèle une fois T004 et T006 disponibles (fichiers distincts).
- Dans Phase 3 : T013, T014, T015 sont parallélisables entre elles (fichiers distincts) une fois T009-T012 en place.
- Entre phases : après Phase 3, Phase 4 (T017-T018) et Phase 5 (T019-T022) peuvent être menées en parallèle par deux personnes distinctes.

## Implementation Strategy

**MVP = Phase 1 + Phase 2 + Phase 3 (US1)** : une calibration manuelle complète, fonctionnelle pour une session, sans recalibration ni persistance entre redémarrages. Livre déjà la valeur centrale du Principe I de la constitution et débloque la feature suivante (détection d'occupation).

**Incrément 2 = + Phase 4 (US2)** : confort opérationnel pour corriger un désalignement sans redémarrer tout le système.

**Incrément 3 = + Phase 5 (US3)** : confort d'usage au quotidien (pas de recalibration répétée à chaque lancement manuel).

**Phase 6** : à mener avant de considérer la feature "terminée", en particulier T024 (validation matérielle réelle) puisque rien dans les phases précédentes n'a été vérifié sur le vrai plateau/la vraie caméra.
