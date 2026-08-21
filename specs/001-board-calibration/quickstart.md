# Quickstart: Valider la Calibration du Plateau

## Prérequis

- Jetson Orin allumé, plateau et caméra ZED X installés et branchés, accessible via VS Code Remote-SSH (Principe IV).
- Workspace ROS 2 buildé (`colcon build`) avec les packages `robochess_vision` et `robochess_web`.
- Un plateau d'échecs physique (idéalement deux plateaux visuellement différents pour valider SC-003) entièrement visible dans le champ de la caméra.
- Un appareil (Mac ou téléphone) connecté au même Wi-Fi local que le Jetson.

### Installation matérielle/logicielle de la ZED X (une fois)

Jetson AGX Orin Developer Kit + carte de capture GMSL2 ZED Link Duo (confirmé compatible JetPack 7.2.0 / L4T 39.2.1 au 2026-08-21, driver v1.4.3).

1. **Montage physique** (Jetson éteinte et débranchée) :
   - Visser la carte de capture GMSL2 dans le connecteur "Camera connector" au dessous de la carte AGX Orin (entretoises/vis fournies).
   - Câble Fakra GMSL2 : extrémité femelle → caméra ZED X (clic), extrémité mâle → entrée GMSL2 de la carte de capture (clic).
   - Pas d'alimentation externe pour la carte de capture (alimentée par la Jetson).
   - Rallumer la Jetson.
2. **Driver GMSL2** (sur la Jetson) :
   ```bash
   wget https://download.stereolabs.com/drivers/zedx/1.4.3/R39.2/stereolabs-zedlink-duo_1.4.3-LI-MAX96712-L4T39.2.1_arm64.deb
   sudo apt install ./stereolabs-zedlink-duo_1.4.3-LI-MAX96712-L4T39.2.1_arm64.deb
   sudo reboot
   ```
3. **SDK ZED** (après reboot, sur la Jetson) :
   ```bash
   wget https://stereolabs.sfo2.cdn.digitaloceanspaces.com/zedsdk/5.4/ZED_SDK_Tegra_L4T39.2_v5.4.1.zstd.run
   chmod +x ZED_SDK_Tegra_L4T39.2_v5.4.1.zstd.run
   ./ZED_SDK_Tegra_L4T39.2_v5.4.1.zstd.run
   ```
4. **zed-ros2-wrapper** (dépendance tierce, pas vendorée dans ce repo — voir `.gitignore`) :
   ```bash
   cd ros2_ws/src
   git clone --branch v5.4.1 --depth 1 https://github.com/stereolabs/zed-ros2-wrapper.git
   git clone --depth 1 https://github.com/stereolabs/zed-ros2-interfaces.git
   cd ..
   rosdep install --from-paths src --ignore-src -r -y
   ```
5. Rebuild : `colcon build --symlink-install` (avec le `.venv` du workspace activé — voir note ci-dessous).
6. Vérifier la détection : `v4l2-ctl --list-devices` doit lister la ZED X, et `dmesg | grep -i max96712` ne doit montrer aucune erreur.

## Tests automatisables (sans matériel)

```bash
cd ros2_ws
colcon test --packages-select robochess_vision robochess_web
colcon test-result --verbose
```

Couvre `grid_mapping.py` (calcul de la grille à partir de 4 points, détection de quadrilatère dégénéré — FR-003, FR-006) et `camera_feed.py` (décodage des encodages image ROS2 vers JPEG). N'exerce pas la caméra réelle ni le flux ROS 2 — voir research.md §5.

## Validation manuelle de bout en bout (nécessite le matériel)

1. **Lancement** : depuis le Jetson,
   ```bash
   source /opt/ros/jazzy/setup.bash
   source ~/RoboChess/ros2_ws/install/setup.bash
   source ~/RoboChess/ros2_ws/.venv/bin/activate
   ros2 launch robochess_vision calibration.launch.py
   ```
   Démarre `zed_wrapper` (camera_model=zedx) et `robochess_web_server` (Principe III — pas de service persistant). Ctrl+C arrête les deux et libère la caméra.
2. **US1 — Calibration initiale** :
   - Ouvrir `http://<ip-jetson>:<port>/calibration` depuis le navigateur du Mac/téléphone.
   - Cliquer successivement les 4 coins internes indiqués par l'interface (a1, h1, a8, h8).
   - Vérifier que la grille de 64 cases superposée correspond visuellement au plateau réel, case par case (SC-002).
   - Confirmer. Vérifier via `GET /api/calibration/status` que `status: "confirmed"` est renvoyé.
   - Chronométrer l'opération complète : doit rester sous 60s (SC-001).
3. **US1 — Rejet d'une calibration dégénérée** : recommencer une séquence en cliquant volontairement 4 points quasi alignés ; vérifier que le système refuse (réponse `422 degenerate_quadrilateral`) et invite à recommencer (SC-005).
4. **US2 — Recalibration** : légèrement déplacer la caméra, déclencher une nouvelle calibration (`POST /api/calibration/start`), la confirmer ; vérifier que la grille affichée reflète la nouvelle position et que l'ancienne calibration n'est plus utilisée.
5. **US3 — Reprise sans recalibration** : après une calibration confirmée, redémarrer le système (relancer le script de lancement) sans toucher au plateau ni à la caméra ; vérifier via `GET /api/calibration/status` que la calibration précédente est rechargée automatiquement et que l'opérateur peut continuer sans repasser par la séquence de clics (SC-004).
6. **Multi-plateaux (SC-003)** : répéter l'étape 2 avec un second plateau visuellement différent (couleur/bordure) ; vérifier que la calibration fonctionne sans changement de configuration.
7. **Arrêt propre** : arrêter le système via le script d'arrêt ; vérifier que le node caméra libère la ZED X (aucun processus zombie ne retient le périphérique — Principe III).

## Résultat attendu

Toutes les étapes ci-dessus passent sans intervention manuelle sur le code, et les critères de succès SC-001 à SC-005 du spec sont observés.
