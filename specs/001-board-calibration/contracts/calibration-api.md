# Contract: API de Calibration (`robochess_web`)

API REST exposée par `robochess_web` (FastAPI), consommée par la page `static/calibration/index.html`. Toutes les réponses sont en JSON. Cette API ne couvre que la calibration ; le flux vidéo brut (MJPEG/WebRTC) exposé par ailleurs pour afficher l'image live n'est pas détaillé ici (dépend du choix déjà fait pour `zed-ros2-wrapper`, hors scope de cette feature).

## `GET /api/calibration/status`

Retourne l'état de la calibration active, utilisé au chargement de la page (US3 — reprise automatique).

**Response 200**:
```json
{
  "status": "confirmed",
  "created_at": "2026-08-20T10:15:00Z"
}
```
ou, si aucune calibration confirmée n'existe encore :
```json
{ "status": "none" }
```

## `POST /api/calibration/start`

Démarre (ou redémarre — US2) une séquence de calibration `draft`, en réinitialisant tout point précédemment saisi dans la séquence en cours. N'affecte pas la calibration `confirmed` existante tant que la nouvelle n'est pas confirmée (FR-010).

**Response 200**:
```json
{ "status": "draft", "next_corner": "a1" }
```

## `POST /api/calibration/point`

Enregistre le clic de l'opérateur pour le prochain coin attendu (FR-001, FR-002 — l'ordre est imposé par le serveur, pas choisi par le client).

**Request**:
```json
{ "x": 412, "y": 187 }
```

**Response 200** (points restants) :
```json
{ "status": "draft", "next_corner": "h1", "points_collected": ["a1"] }
```

**Response 200** (dernier point reçu, quadrilatère valide) :
```json
{
  "status": "draft",
  "next_corner": null,
  "points_collected": ["a1", "h1", "a8", "h8"],
  "preview_grid": "<64 polygones image, pour overlay>"
}
```

**Response 422** (quadrilatère dégénéré détecté après le 4e point — FR-006) :
```json
{ "error": "degenerate_quadrilateral", "message": "Les points sont trop proches ou alignés." }
```

## `POST /api/calibration/confirm`

Confirme la calibration `draft` en cours (4 points valides déjà collectés). Calcule les 64 `Square`, persiste la calibration (research.md §3), et la promeut en `confirmed`, remplaçant l'ancienne le cas échéant (FR-007, FR-008, FR-009, FR-010).

**Response 200**:
```json
{ "status": "confirmed", "created_at": "2026-08-20T10:15:00Z" }
```

**Response 409** (moins de 4 points collectés) :
```json
{ "error": "incomplete", "message": "4 points requis avant confirmation." }
```

## `POST /api/calibration/discard`

Abandonne la séquence `draft` en cours (FR-005). La calibration `confirmed` précédente (s'il y en a une) reste inchangée.

**Response 200**:
```json
{ "status": "confirmed", "created_at": "2026-08-20T09:40:00Z" }
```
ou `{ "status": "none" }` s'il n'y avait pas de calibration confirmée avant ce `draft`.

## Erreurs communes

| Code | Cas |
|---|---|
| `503` | Flux caméra indisponible/interrompu au moment de l'appel (FR-011) — le body précise `{ "error": "camera_unavailable" }`. |
