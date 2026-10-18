# API contract — verified

**Verified:** 2026-10-18 against `GET https://api.market-resale-signal.xubi.org/openapi.json`
(FastAPI, OpenAPI 3.1.0, `info.version` `0.1.0`). Unauthenticated `401` body and HTTP/2/TLS
were checked with `curl` (no credentials).

This file is the GUI source of truth for HTTP integration. Do not invent fields or endpoints.
If the backend changes, re-fetch OpenAPI and update this file.

## Base URL and origin normalization

The client stores a single **origin** (scheme + host + optional port, **no path**).
Inputs are normalized on load (env, `config.json`, or operator input):

| Input | Normalized |
| ----- | ---------- |
| `https://api.market-resale-signal.xubi.org` | same |
| `https://api.market-resale-signal.xubi.org/` | strip trailing `/` |
| `https://api.market-resale-signal.xubi.org/api/v1` | strip `/api/v1` |
| `https://api.market-resale-signal.xubi.org/api/v1/` | strip `/api/v1/` |
| `http://localhost:8000/api/v1` | `http://localhost:8000` |

URL construction:

- API: `{origin}/api/v1/<path>` (example: `{origin}/api/v1/auth/app-login`)
- Liveness: `{origin}/health/live` (**public**, outside `/api/v1`)

Default origin: `https://api.market-resale-signal.xubi.org`.  
Only `http` and `https` are accepted.

## Authentication

1. Operator supplies the shared application **secret**.
2. `POST {origin}/api/v1/auth/app-login` with JSON `{"client_secret": "<secret>"}` (`AppLoginRequest`).
3. Success: `200` `AppLoginResponse` `{ "authenticated": true, "expires_in": <seconds> }` and a
   **session cookie** set by the server. Expected name: **`gui_session`** (product convention;
   **not declared in OpenAPI** — confirm on one manual login). Cookie stays in the in-memory
   httpx jar only; never disk or logs.
4. Protected `/api/v1/*` calls rely on that cookie.
5. `GET {origin}/health/live` needs no authentication.

**GUI policy:** do **not** send `X-App-Key` on normal API calls.  
Note: OpenAPI text for `GET /api/v1/auth/check` mentions “session cookie or app key”; that is a
**server** capability. The GUI still uses **cookie session after app-login** only.

### Session check

`GET {origin}/api/v1/auth/check` → `200` `AuthCheckResponse` `{ "authenticated": <bool> }`.

## Endpoints

Protected unless marked public. Bodies are JSON. List endpoints return **bare arrays** (no envelope).
No pagination or list query parameters in OpenAPI.

| Method | Path | Request | Success | Notes |
| ------ | ---- | ------- | ------- | ----- |
| GET | `/health/live` | — | `200 LiveResponse` | **public** |
| POST | `/api/v1/auth/app-login` | `AppLoginRequest` | `200 AppLoginResponse` | sets cookie |
| GET | `/api/v1/auth/check` | — | `200 AuthCheckResponse` | |
| GET | `/api/v1/health/ready` | — | `200 ReadyResponse` | |
| GET | `/api/v1/health/status` | — | `200 HealthStatusResponse` | |
| GET | `/api/v1/dashboard/summary` | — | `200 DashboardSummaryResponse` | |
| GET | `/api/v1/settings` | — | `200 SettingsResponse` | |
| PATCH | `/api/v1/settings` | `SettingsPatchRequest` | `200 SettingsResponse` | |
| GET | `/api/v1/groups` | — | `200 GroupResponse[]` | |
| POST | `/api/v1/groups` | `GroupCreateRequest` | `201 GroupResponse` | |
| GET | `/api/v1/groups/{group_id}` | path `group_id: int` | `200 GroupResponse` | |
| PATCH | `/api/v1/groups/{group_id}` | `GroupPatchRequest` | `200 GroupResponse` | omitted fields unchanged |
| DELETE | `/api/v1/groups/{group_id}` | path `group_id: int` | `204` | see **Group delete / 409** |
| GET | `/api/v1/filters` | — | `200 FilterResponse[]` | |
| POST | `/api/v1/filters` | `FilterCreateRequest` | `201 FilterResponse` | body: `phrase` only |
| DELETE | `/api/v1/filters/{filter_id}` | path `filter_id: int` | `204` | |

OpenAPI lists `422` on several mutating routes via `HTTPValidationError`.

## Models

`*` = required. Datetimes are JSON strings with `format: date-time`.

### Auth / health (simple)

```text
AppLoginRequest
  client_secret: string *

AppLoginResponse
  authenticated: boolean *
  expires_in: integer *

AuthCheckResponse
  authenticated: boolean *

LiveResponse
  status: string  # OpenAPI const "ok" (default "ok")

ReadyResponse
  status: string    # OpenAPI const "ready"
  database: string  # OpenAPI const "ok"
```

### Groups

```text
GroupCreateRequest  (additionalProperties: false)
  name: string *     # minLength 1, maxLength 200
  url: string *      # minLength 1
  enabled: boolean   # optional; OpenAPI default true

GroupPatchRequest  (additionalProperties: false)
  name: string | null       # 1..200 when set
  url: string | null        # minLength 1 when set
  enabled: boolean | null
  sort_order: integer | null  # minimum 0

GroupResponse
  id: integer *
  name: string *
  url: string *
  enabled: boolean *
  sort_order: integer *
  created_at: date-time *
  updated_at: date-time *
```

### Filters

```text
FilterCreateRequest  (additionalProperties: false)
  phrase: string *   # minLength 1, maxLength 500
  # no `enabled` on create in OpenAPI

FilterResponse
  id: integer *
  phrase: string *
  normalized_phrase: string *
  enabled: boolean *
  created_at: date-time *
  updated_at: date-time *
```

### Settings

```text
SettingsPatchRequest  (additionalProperties: false)
  price_drop_threshold_percent: number | null  # minimum 0.1, maximum 100

SettingsResponse
  price_drop_threshold_percent: number *
```

Threshold is a **percent** (0.1–100), **global** on the server (not per GUI user).  
GUI may accept comma or dot in the form and must send a JSON number.

### Dashboard / detailed health

```text
DashboardSummaryResponse
  groups_total: integer (default 0)
  groups_enabled: integer (default 0)
  products_total: integer (default 0)
  products_active: integer (default 0)
  products_missing: integer (default 0)
  pending_deliveries: integer (default 0)
  failed_deliveries: integer (default 0)
  worker_status: string | null
  worker_last_heartbeat_at: date-time | null
  last_successful_scan_at: date-time | null

WorkerHealthSummary
  worker_id: string *
  status: string *
  is_alive: boolean *
  last_heartbeat_at: date-time *
  last_scan_started_at: date-time | null
  last_scan_finished_at: date-time | null
  last_successful_scan_at: date-time | null
  last_error_at: date-time | null
  details: object | null

LatestScanRunSummary
  id: integer | null
  status: string *
  started_at: date-time *
  finished_at: date-time | null
  groups_total: integer (default 0)
  groups_success: integer (default 0)
  groups_failed: integer (default 0)
  products_seen: integer (default 0)
  new_products: integer (default 0)
  price_drops: integer (default 0)
  errors: integer (default 0)
  duration_ms: integer | null
  error_summary: string | null

HealthStatusResponse
  worker: WorkerHealthSummary | null
  latest_scan_run: LatestScanRunSummary | null
  enabled_groups: integer (default 0)
  total_groups: integer (default 0)
  products_count: integer (default 0)
  pending_deliveries: integer (default 0)
  failed_deliveries: integer (default 0)
  last_successful_scan_at: date-time | null
```

## Error responses

### 401 Unauthorized

Observed `Content-Type: application/problem+json` (RFC 7807-style), example:

```json
{
  "type": "about:blank",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Authentication required",
  "instance": "/api/v1/auth/check"
}
```

GUI: one coordinated re-login for **safe reads** only; **never replay writes**; never show raw `detail` to the operator.

### 422 Unprocessable Entity

Schema `HTTPValidationError`:

```json
{
  "detail": [
    {
      "loc": ["body", "price_drop_threshold_percent"],
      "msg": "…",
      "type": "…",
      "input": …,
      "ctx": { }
    }
  ]
}
```

GUI: map to plain-language field errors; do not show raw English `msg` as the primary copy.

### Group delete and 409

OpenAPI **operation description** for `DELETE /api/v1/groups/{group_id}`:

> Hard-delete a group, or **409 when referenced by history.**

OpenAPI **`responses`** for that operation list only **`204`** and **`422`** — **409 is not declared**.

GUI should still handle **`409` defensively** (treat as conflict / “in use”; prefer disable over delete) and keep operator messaging for that case. Treat full 409 contract as **implementation-backed**, not fully specified in `responses`.

### Other statuses

Guard **403**, **404**, **429**, **5xx**. Bodies may be non-JSON; decoding failures must not crash the client.

## Transport (GUI requirements)

- TLS verification **on** (never disable). Use `certifi` in packaged builds.
- Prefer HTTP/2 when ALPN negotiates `h2`; HTTP/1.1 fallback is acceptable.
- Explicit connect/read/write/pool timeouts; shared httpx client; **no** redirect following by default.

## Operator / backend confirmations

1. Session cookie **name** (expected `gui_session`) — missing from OpenAPI.
2. Runtime **409** on group delete when history references the group — described in prose, absent from formal `responses`.
3. No `enabled` on `FilterCreateRequest` — create sends **`phrase` only**; `enabled` appears only on `FilterResponse`.
