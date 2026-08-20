# Feature Specification: Calibration du Plateau

**Feature Branch**: `001-board-calibration`

**Created**: 2026-08-20

**Status**: Draft

**Input**: User description: "Calibration manuelle du plateau d'échecs : l'utilisateur clique 4 points (coins internes des cases a1, h1, a8, h8) sur le flux vidéo de la caméra ZED X pour localiser la grille de jeu. Le système doit ensuite pouvoir mapper chacune des 64 cases à une région de l'image (et à une région de profondeur correspondante) à partir de ces 4 points, sans hypothèse codée en dur sur la taille, la couleur ou la bordure du plateau. Cette calibration se fait une fois par plateau/session et sert de fondation à la détection d'occupation par profondeur (feature suivante). Une détection automatique de la grille pourra être ajoutée plus tard en complément best-effort, mais n'est pas dans le scope de cette feature."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Calibrer le plateau en début de partie (Priority: P1)

Avant de commencer une partie, l'opérateur clique successivement sur les quatre coins internes du plateau (a1, h1, a8, h8) dans l'image de la caméra en direct. Le système affiche alors la grille des 64 cases calculée en superposition sur l'image, pour que l'opérateur vérifie visuellement que chaque case correspond bien à la réalité avant de confirmer.

**Why this priority**: Sans cette étape, aucune autre fonctionnalité du robot (détection de coup, sécurité de manipulation) ne peut savoir où se trouvent les cases. C'est le prérequis absolu de toute partie.

**Independent Test**: Peut être testé seul en plaçant un plateau devant la caméra, en réalisant la séquence de 4 clics, et en vérifiant que la grille superposée correspond visuellement aux 64 cases réelles.

**Acceptance Scenarios**:

1. **Given** le flux vidéo de la caméra affiche un plateau d'échecs entièrement visible, **When** l'opérateur clique successivement les coins internes a1, h1, a8, h8, **Then** le système superpose une grille de 64 cases sur l'image et invite l'opérateur à confirmer ou recommencer.
2. **Given** la grille superposée correspond visuellement aux 64 cases réelles, **When** l'opérateur confirme, **Then** la calibration est enregistrée comme active pour la session et chaque case est associée à une région d'image et à une région de profondeur correspondante.
3. **Given** la grille superposée ne correspond pas au plateau réel (mauvais clic), **When** l'opérateur choisit de recommencer, **Then** les 4 points sont réinitialisés et la séquence de clic repart de zéro sans que l'ancienne calibration confirmée (s'il y en avait une) ne soit affectée.

---

### User Story 2 - Recalibrer après un déplacement de la caméra ou du plateau (Priority: P2)

Si la caméra ou le plateau a été déplacé depuis la dernière calibration, l'opérateur déclenche explicitement une nouvelle calibration, qui remplace l'ancienne une fois confirmée.

**Why this priority**: Le montage (bras, caméra, plateau) est manipulé manuellement entre les sessions (Principe III de la constitution) ; un moyen simple de recalibrer évite de devoir redémarrer tout le système pour corriger un désalignement.

**Independent Test**: Peut être testé en confirmant une première calibration, en déplaçant légèrement la caméra, puis en déclenchant une nouvelle calibration et en vérifiant que la nouvelle grille remplace bien l'ancienne.

**Acceptance Scenarios**:

1. **Given** une calibration déjà confirmée existe, **When** l'opérateur déclenche une nouvelle calibration, **Then** le système relance la séquence de 4 clics sans supprimer la calibration précédente tant que la nouvelle n'est pas confirmée.
2. **Given** une nouvelle calibration vient d'être confirmée, **When** le système traite la position suivante, **Then** il utilise exclusivement la nouvelle grille (l'ancienne n'est plus utilisée).

---

### User Story 3 - Reprendre une session sans recalibrer (Priority: P3)

Au lancement du système, si le plateau et la caméra n'ont pas bougé depuis la dernière calibration confirmée, l'opérateur peut reprendre directement sans repasser par la séquence de 4 clics.

**Why this priority**: Confort d'usage — évite une étape répétitive à chaque lancement manuel (Principe III), mais le système reste pleinement fonctionnel sans cette fonctionnalité (l'opérateur peut toujours recalibrer manuellement via l'US2).

**Independent Test**: Peut être testé en confirmant une calibration, en redémarrant le système, et en vérifiant que la dernière calibration est proposée/rechargée automatiquement avec une option explicite pour la refaire si besoin.

**Acceptance Scenarios**:

1. **Given** une calibration a été confirmée lors d'une session précédente, **When** le système redémarre sans qu'aucune nouvelle calibration n'ait été déclenchée, **Then** la dernière calibration confirmée est rechargée automatiquement et l'opérateur peut commencer à jouer directement.
2. **Given** une calibration précédente est rechargée automatiquement, **When** l'opérateur constate qu'elle ne correspond plus au plateau actuel, **Then** il peut déclencher une recalibration manuelle (US2) à tout moment.

### Edge Cases

- Que se passe-t-il si les 4 points cliqués sont presque alignés ou trop proches les uns des autres (quadrilatère dégénéré, mapping de case impossible) ?
- Comment le système réagit-il si le plateau n'est que partiellement visible dans le champ de la caméra (un ou plusieurs coins hors cadre) ?
- Que se passe-t-il si le flux vidéo de la caméra se fige ou est interrompu pendant la séquence de clics ?
- Comment l'opérateur corrige-t-il un clic imprécis sur un coin avant d'avoir terminé les 4 clics (sans devoir tout recommencer) ?
- Que se passe-t-il si l'opérateur tente de démarrer une partie alors qu'aucune calibration (ni nouvelle, ni précédente rechargée) n'est active ?
- Comment le système se comporte-t-il face à un plateau fortement incliné ou vu avec un angle de caméra prononcé (perspective non orthogonale) ?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le système DOIT permettre à l'opérateur de désigner les quatre coins internes du plateau (cases a1, h1, a8, h8) en cliquant sur l'image du flux vidéo en direct, un coin à la fois.
- **FR-002**: Le système DOIT indiquer clairement, à chaque étape de la séquence, quel coin (a1, h1, a8 ou h8) l'opérateur doit cliquer ensuite, afin de lever toute ambiguïté sur l'orientation du plateau.
- **FR-003**: Le système DOIT calculer les limites des 64 cases uniquement à partir des quatre points cliqués, sans aucune hypothèse codée en dur sur la taille, la couleur ou la largeur de bordure du plateau.
- **FR-004**: Le système DOIT superposer la grille des 64 cases calculée sur l'image en direct, pour permettre à l'opérateur de vérifier visuellement l'alignement avant de confirmer.
- **FR-005**: Le système DOIT permettre à l'opérateur d'abandonner la tentative en cours et de recommencer la séquence de clics si la grille superposée ne correspond pas au plateau réel.
- **FR-006**: Le système DOIT rejeter une tentative de calibration dont les quatre points sont quasi-alignés ou trop rapprochés pour former un quadrilatère exploitable, et inviter l'opérateur à recommencer.
- **FR-007**: Une fois confirmée, la calibration DOIT associer chacune des 64 cases à la fois à une région de l'image et à une région de mesure de profondeur correspondante, prêtes à être utilisées par la détection d'occupation.
- **FR-008**: Une calibration confirmée DOIT rester valide pour le reste de la session, sans que l'opérateur ait à la répéter avant chaque coup.
- **FR-009**: Le système DOIT conserver la calibration confirmée de façon à pouvoir la réutiliser automatiquement au prochain lancement, sans forcer l'opérateur à recalibrer si le plateau et la caméra n'ont pas bougé.
- **FR-010**: Le système DOIT permettre à l'opérateur de déclencher explicitement une nouvelle calibration à tout moment (par exemple après un déplacement de la caméra ou un changement de plateau), qui remplace la précédente une fois confirmée.
- **FR-011**: Le système DOIT avertir clairement l'opérateur si le flux vidéo de la caméra est indisponible ou interrompu pendant la séquence de calibration, plutôt que de continuer silencieusement avec des données obsolètes.

### Key Entities

- **Calibration**: représente le résultat d'une séquence de calibration confirmée — les quatre points désignés par l'opérateur, la grille des 64 cases qui en découle, l'horodatage de confirmation, et pour chaque case sa région d'image et sa région de profondeur associées. Une seule calibration est active à la fois.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un opérateur peut réaliser une calibration complète (4 clics + vérification visuelle + confirmation) en moins de 60 secondes.
- **SC-002**: Après confirmation, 100% des 64 cases sont identifiables individuellement sur la grille superposée, sans chevauchement ni case manquante.
- **SC-003**: La calibration fonctionne sans changement de configuration sur au moins deux plateaux visuellement différents (couleur ou largeur de bordure différente).
- **SC-004**: Après un redémarrage du système sans déplacement du plateau ni de la caméra, l'opérateur peut reprendre une partie sans repasser par la séquence de calibration.
- **SC-005**: 100% des tentatives de calibration dégénérée (points mal placés) sont détectées et rejetées avant de pouvoir affecter la détection de coup ultérieure.

## Assumptions

- Un seul plateau et une seule caméra sont actifs à la fois ; la gestion de plusieurs profils de calibration en parallèle est hors scope pour cette version.
- La calibration est déclenchée manuellement par un opérateur humain ; la détection automatique de la grille est hors scope de cette feature (voir Principe I de la constitution — un complément best-effort pourra être ajouté plus tard).
- La calibration confirmée est conservée localement (persistée au-delà de la session en cours) et reste valable tant qu'elle n'est pas explicitement refaite.
- Le plateau reste statique (non déplacé) pendant toute la durée d'une partie une fois la calibration confirmée.
- L'opérateur interagit avec l'image en direct via l'interface web du projet (clic souris ou tactile), déjà prévue par ailleurs dans la stack du projet.
