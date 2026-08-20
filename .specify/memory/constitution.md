<!--
Sync Impact Report
- Version change: (none) → 1.0.0
- Modified principles: n/a (initial ratification)
- Added sections:
  - Core Principles: I. Vision Agnostique au Plateau, II. Occupation par Profondeur (pas de Classification de Pièces),
    III. Bonne Citoyenneté sur Jetson Partagé, IV. Développement Distant / Exécution Cible, V. Manipulation Sûre
    (NON-NEGOTIABLE), VI. Difficulté = Paramètre du Moteur
  - Contraintes Matérielles & Stack Technique
  - Workflow de Développement & Déploiement
  - Governance
- Removed sections: n/a
- Deferred TODOs: none — RATIFICATION_DATE set from session date; revisit stack choices in /speckit-plan.
-->

# RoboChess Constitution
<!-- Working title — bras robotique UFACTORY Lite 6 + caméra ZED X jouant aux échecs sur Jetson Orin. Renommer librement. -->

## Core Principles

### I. Vision Agnostique au Plateau
Le système DOIT localiser la grille de jeu (coins internes des cases a1/h1/a8/h8), jamais les
bords extérieurs du plateau, car certains échiquiers ont une marge/bordure blanche entre le
cadre et le début des cases. La calibration manuelle en 4 points (l'utilisateur clique les coins
de la grille une fois par plateau) est la méthode de référence, fiable quel que soit le style de
plateau. Une détection automatique de la grille (best-effort, ex. lignes de Hough ou modèle
entraîné) peut être ajoutée en complément, mais DOIT se replier sur la calibration manuelle en
cas d'échec ou de confiance faible. Aucune hypothèse sur la taille, la couleur ou la largeur de
bordure d'un plateau ne doit être codée en dur.

### II. Occupation par Profondeur, pas Classification de Pièces
La détection de présence d'une pièce sur une case DOIT s'appuyer sur la profondeur/hauteur
(caméra ZED X) plutôt que sur la reconnaissance visuelle de la pièce (couleur, forme, style).
Le coup joué par l'humain DOIT être déduit d'un diff d'occupation (case libérée / case occupée)
entre deux tours, recoupé avec la liste des coups légaux que le moteur d'échecs calcule pour la
position courante — jamais d'une classification "quelle pièce est-ce". Cette approche généralise
à n'importe quel jeu de pièces (matière, couleur, style) sans ré-entraînement.

### III. Bonne Citoyenneté sur Jetson Partagé
Le Jetson Orin est une ressource partagée avec d'autres projets de l'école. Le projet NE DOIT PAS
démarrer automatiquement au boot (pas de service systemd auto-lancé, pas de container à
`restart: always`). Il DOIT se lancer manuellement via une commande/script dédié qui ne démarre
que les nœuds nécessaires au projet, et DOIT libérer proprement les périphériques (caméra, bras)
à l'arrêt. Les dépendances Python DOIVENT être isolées (venv, puis Docker) et ne jamais être
installées globalement sur le système partagé. Le projet DOIT utiliser un `ROS_DOMAIN_ID` dédié
pour ne pas interférer avec le graphe ROS2 d'un autre utilisateur exécuté au même moment sur le
même réseau.

### IV. Développement Distant, Exécution Cible
Le code s'écrit et s'exécute sur le Jetson via VS Code Remote-SSH depuis le Mac — le Mac ne fait
jamais tourner les drivers CUDA/ROS2/ZED en local, il n'est qu'un client d'édition. Git est
l'unique source de vérité du code ; aucune copie/synchronisation manuelle de fichiers entre Mac et
Jetson n'est permise en dehors de git push/pull.

### V. Manipulation Sûre (NON-NEGOTIABLE)
Tout mouvement du bras DOIT passer par une planification de trajectoire consciente des collisions
(MoveIt2) — jamais de commande de déplacement point-à-point non vérifiée à proximité de pièces ou
de personnes. Toute nouvelle séquence de mouvement DOIT être validée en simulation ou à vitesse
réduite avant exécution à vitesse nominale.

### VI. Difficulté = Paramètre du Moteur
Le niveau de difficulté exposé dans l'interface DOIT mapper directement sur les paramètres natifs
du moteur d'échecs (Skill Level / limitation d'Elo / profondeur de recherche Stockfish), jamais sur
une heuristique maison qui dégraderait artificiellement la qualité de jeu.

## Contraintes Matérielles & Stack Technique

- Matériel fixe : Jetson Orin 64GB (JetPack/Ubuntu, aarch64) ; bras UFACTORY Lite 6 avec pince ;
  caméra ZED X (GMSL2/FAKRA) ; plateau de test = tapis souple 5.5cm/case, lettré/chiffré, pièces
  en bois — mais le logiciel DOIT rester utilisable avec un autre échiquier (voir Principe I).
- Stack cœur : ROS 2 (Humble) + MoveIt2 comme middleware et planification ; `xarm_ros2` (driver
  officiel UFACTORY) pour le bras ; `zed-ros2-wrapper` pour la caméra ; Stockfish piloté via
  `python-chess` comme moteur de jeu ; interface web légère (FastAPI + HTML/JS) pour la sélection
  de difficulté et le suivi de partie, accessible en Wi-Fi local depuis Mac ou téléphone.
- Ces choix de stack sont réévalués en détail lors de `/speckit-plan`, mais les contraintes
  matérielles et les principes ci-dessus sont fixes.

## Workflow de Développement & Déploiement

- Édition via VS Code Remote-SSH connecté au Jetson ; le Mac reste le poste de développement,
  jamais d'exécution.
- Git comme source de vérité unique ; le déploiement se fait par `git pull` sur le Jetson, jamais
  par copie manuelle.
- Lancement strictement manuel : un unique script/launch file démarre exactement les nœuds requis
  par le projet, à la demande, et permet un arrêt propre. Aucun service ne persiste après l'arrêt
  volontaire.
- Isolation des dépendances : environnement virtuel Python dédié dès le départ ; conteneurisation
  Docker (image basée sur `l4t-base` NVIDIA) envisagée ensuite pour figer CUDA/ROS2 sans gêner les
  autres utilisateurs du Jetson.

## Governance

Cette constitution prévaut sur toute autre pratique ou convention informelle du projet. Toute
modification (ajout, suppression ou reformulation d'un principe) DOIT être documentée dans le
Sync Impact Report en tête de ce fichier et accompagnée d'une justification. Le versionnage suit
SemVer : MAJOR pour un retrait ou une redéfinition incompatible d'un principe, MINOR pour l'ajout
d'un principe ou d'une section, PATCH pour une clarification sans changement de sens. Toute
revue de plan (`/speckit-plan`) ou de tâches (`/speckit-tasks`) DOIT vérifier sa conformité aux
principes ci-dessus ; toute dérogation doit être justifiée explicitement dans le document
concerné plutôt que silencieusement ignorée.

**Version**: 1.0.0 | **Ratified**: 2026-08-20 | **Last Amended**: 2026-08-20
