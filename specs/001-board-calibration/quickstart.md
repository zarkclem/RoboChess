# Quickstart: Valider la Calibration du Plateau

## Prérequis

- Jetson Orin allumé, plateau et caméra ZED X installés et branchés, accessible via VS Code Remote-SSH (Principe IV).
- Workspace ROS 2 buildé (`colcon build`) avec les packages `robochess_vision` et `robochess_web`.
- Un plateau d'échecs physique (idéalement deux plateaux visuellement différents pour valider SC-003) entièrement visible dans le champ de la caméra.
- Un appareil (Mac ou téléphone) connecté au même Wi-Fi local que le Jetson.

## Tests automatisables (sans matériel)

```bash
cd ros2_ws
colcon test --packages-select robochess_vision robochess_web
colcon test-result --verbose
```

Couvre `grid_mapping.py` : calcul de la grille à partir de 4 points, détection de quadrilatère dégénéré (FR-003, FR-006). N'exerce pas la caméra réelle ni le flux ROS 2 — voir research.md §5.

## Validation manuelle de bout en bout (nécessite le matériel)

1. **Lancement** : depuis le Jetson, exécuter le script de lancement manuel du projet (démarre uniquement les nœuds nécessaires — Principe III). Ne pas utiliser de service persistant.
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
