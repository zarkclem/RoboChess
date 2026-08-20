# Data Model: Calibration du Plateau

## Calibration

Représente une séquence de calibration, en cours ou confirmée. Une seule calibration `confirmed` est active à la fois (cf. Assumptions du spec).

| Champ | Type | Description |
|---|---|---|
| `status` | enum (`draft`, `confirmed`) | `draft` tant que les 4 points ne sont pas tous validés ; `confirmed` une fois la grille superposée acceptée par l'opérateur (FR-004). |
| `corner_points` | dict[`a1`\|`h1`\|`a8`\|`h8` → {x, y}] | Coordonnées pixel des 4 clics de l'opérateur dans le repère de l'image caméra (FR-001). Rempli progressivement pendant `draft`. |
| `created_at` | timestamp | Horodatage de confirmation (utile pour l'affichage "dernière calibration du ..." lors de la reprise automatique, US3). |
| `squares` | list[Square] (64 éléments) | Généré uniquement quand `status = confirmed`, à partir de `corner_points` (Phase 0 §1). |

**Règles de validation**:
- `corner_points` doit contenir exactement 4 entrées, une par coin, avant tout calcul de grille (FR-001).
- Les 4 points ne doivent pas être quasi-alignés ni trop rapprochés (aire du quadrilatère sous un seuil minimal) — une calibration violant cette règle ne peut pas passer en `confirmed` (FR-006).
- Une seule `Calibration` avec `status = confirmed` existe à un instant donné : en confirmer une nouvelle remplace l'ancienne de façon atomique (US2, FR-010) — l'ancienne reste valide jusqu'à ce que la nouvelle soit effectivement confirmée.

**Transitions d'état**:

```text
(aucune calibration active)
        │ opérateur clique 4 points
        ▼
     draft ──── opérateur annule/recommence ────▶ draft (points réinitialisés)
        │ opérateur confirme (grille valide, FR-006 passé)
        ▼
    confirmed ──── opérateur déclenche une recalibration (US2) ────▶ draft (nouvelle séquence, l'ancienne "confirmed" reste active tant que non remplacée)
```

## Square

Une case du plateau, dérivée d'une `Calibration` confirmée. Toujours au nombre de 64 par calibration.

| Champ | Type | Description |
|---|---|---|
| `id` | string (`a1` … `h8`) | Identifiant algébrique standard de la case. |
| `image_region` | polygon (4 points pixel) | Quadrilatère de la case dans l'image caméra, dérivé de l'homographie (FR-007). |
| `depth_region` | polygon (4 points pixel, sous-ensemble de `image_region`) | Région resserrée utilisée pour l'échantillonnage de profondeur (Phase 0 §2) ; consommée par la future feature de détection d'occupation, pas de logique de diff ici. |

**Relationships**: `Square` appartient à exactement une `Calibration` (composition — n'existe pas indépendamment ; régénéré entièrement à chaque confirmation).
