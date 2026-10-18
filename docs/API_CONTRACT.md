# API contract — verified

**Verified:** 2026-10-18, by fetching `GET https://api.market-resale-signal.xubi.org/openapi.json`
(FastAPI, OpenAPI 3.1.0, `info.version` 0.1.0). Unauthenticated 401 body and HTTP/2/TLS
negotiation were probed with `curl` (no credentials sent).

This file is the source of truth for the GUI. Do not invent fields or endpoints.
If the backend changes, re-fetch the OpenAPI document and update this file.

## Base URL and origin normalization

The client stores a single **origin** (scheme + host + optional port, no path).
Accepted inputs are normalized on load (env, `config.json`, or operator input):

| Input | Normalized |
|---|---|
| `https://api.market-resale-signal.xubi.org` | `https://api.market-resale-signal.xubi.org` |
| `https://api.market-resale-signal.xubi.org/` | `https://api.market-resale-signal.xubi.org` |
| `https://api.market-resale-signal.xubi.org/api/v1` | `https://api.market-resale-signal.xubi.org` |
| `https://api.market-resale-signal.xubi.org/api/v1/` | `https://api.market-resale-signal.xubi.org` |
| `http://localhost:8000/api/v1` | `http://localhost:8000` |

URLs are then built as:

- API calls: `{origin}/api/v1/<path>` (e.g. `{origin}/api/v1/auth/app-login`)
- Liveness: `{origin}/health/live` (public, **outside** `/api/v1`)

Default origin: `https://api.market-resale-signal.xubi.org`.
Only `http` and `https` schemes are accepted.

## Authentication

1. Operator provides the shared application **secret**.
2. `POST {origin}/api/v1/auth/app-login`, body `{"client_secret": "<secret>"}`.
3. Server responds `200` with `{"authenticated": true, "expires_in": <seconds>}` and
   sets a session cookie. Expected cookie name: **`gui_session`** (per product docs;
   **confirm on one manual login** — the OpenAPI document does not declare it).
4. Every protected `/api/v1/*` call carries that cookie. It lives only in the
   in-memory httpx cookie jar; it is never written to disk or logs.
5. `GET {origin}/health/live` needs no authentication.

**Do not** send `X-App-Key` on normal API calls, and do not design a flow that needs it.

### Session check

`GET {origin}/api/v1/auth/check` → `200 {"authenticated": <bool>}`.

## Endpoints

All protected unless marked public. All request/response bodies are JSON.

| Method | Path | Request | Success | Notes |
|---|---|---|---|---|
| GET | `/health/live` | — | `200 LiveResponse` | **public** |
| POST | `/api/v1/auth/app-login` | `AppLoginRequest` | `200 AppLoginResponse` | sets cookie |
| GET | `/api/v1/auth/check` | — | `200 AuthCheckResponse` | |
| GET | `/api/v1/health/ready` | — | `200 ReadyResponse` | |
| GET | `/api/v1/health/status` | — | `200 HealthStatusResponse` | |
| GET | `/api/v1/dashboard/summary` | — | `200 DashboardSummaryResponse` | |
| GET | `/api/v1/settings` | — | `200 SettingsResponse` | |
| PATCH | `/api/v1/settings` | `SettingsPatchRequest` | `200 SettingsResponse` | |
| GET | `/api/v1/groups` | — | `200 [GroupResponse]` | |
| POST | `/api/v1/groups` | `GroupCreateRequest` | `201 GroupResponse` | |
| GET | `/api/v1/groups/{group_id}` | — | `200 GroupResponse` | `group_id` int |
| PATCH | `/api/v1/groups/{group_id}` | `GroupPatchRequest` | `200 GroupResponse` | |
| DELETE | `/api/v1/groups/{group_id}` | — | `204` no body | see caveats |
| GET | `/api/v1/filters` | — | `200 [FilterResponse]` | |
| POST | `/api/v1/filters` | `FilterCreateRequest` | `201 FilterResponse` | |
| DELETE | `/api/v1/filters/{filter_id}` | — | `204` no body | `filter_id` int |

No pagination, query parameters, or filtering parameters are defined on the list
endpoints. `GET` list responses have no envelope — they are bare JSON arrays.

## Models

`*` marks required fields. Datetimes are ISO-8601 strings (`date-time`).

```text
AppLoginRequest          client_secret: str *
AppLoginResponse         authenticated: bool *, expires_in: int *
AuthCheckResponse        authenticated: bool *
LiveResponse             status: str
ReadyResponse            status: str, database: str

GroupCreateRequest       name: str *, url: str *, enabled: bool (optional)
GroupPatchRequest        name: str|null (1..200), url: str|null (min 1),
                         enabled: bool|null, sort_order: int|null (>=0)
GroupResponse            id: int *, name: str *, url: str *, enabled: bool *,
                         sort_order: int *, created_at: str *, updated_at: str *

FilterCreateRequest      phrase: str *
FilterResponse           id: int *, phrase: str *, normalized_phrase: str *,
                         enabled: bool *, created_at: str *, updated_at: str *

SettingsPatchRequest     price_drop_threshold_percent: float|null (0.1..100)
SettingsResponse         price_drop_threshold_percent: float *

WorkerHealthSummary      worker_id: str *, status: str *, is_alive: bool *,
                         last_heartbeat_at: str *,
                         last_scan_started_at: str|null, last_scan_finished_at: str|null,
                         last_successful_scan_at: str|null, last_error_at: str|null,
                         details: object|null
LatestScanRunSummary     id: int|null, status: str *, started_at: str *,
                         finished_at: str|null, groups_total: int, groups_success: int,
                         groups_failed: int, products_seen: int, new_products: int,
                         price_drops: int, errors: int, duration_ms: int|null,
                         error_summary: str|null
HealthStatusResponse     worker: WorkerHealthSummary|null,
                         latest_scan_run: LatestScanRunSummary|null,
                         enabled_groups: int, total_groups: int, products_count: int,
                         pending_deliveries: int, failed_deliveries: int,
                         last_successful_scan_at: str|null
DashboardSummaryResponse groups_total: int, groups_enabled: int, products_total: int,
                         products_active: int, products_missing: int,
                         pending_deliveries: int, failed_deliveries: int,
                         worker_status: str|null, worker_last_heartbeat_at: str|null,
                         last_successful_scan_at: str|null
```

The price-drop threshold is a **percentage** (`price_drop_threshold_percent`), range
**0.1–100**, and is a **global** server setting (not per operator). The GUI accepts a
comma or a dot as the decimal separator in input and sends a JSON number.

## Error responses

- **401 Unauthorized** — `Content-Type: application/problem+json` (RFC 7807):

  ```json
  {"type":"about:blank","title":"Unauthorized","status":401,
   "detail":"Authentication required","instance":"/api/v1/auth/check"}
  ```

  The GUI maps it to: one coordinated re-login for **reads** only, then show "session
  expired". Writes are never replayed. The problem `detail` is never shown raw to the
  operator.

- **422 Unprocessable Entity** — FastAPI validation error:

  ```json
  {"detail":[{"loc":["body","price_drop_threshold_percent"],
              "msg":"Input should be less than or equal to 100",
              "type":"less_than_equal","input":123,"ctx":{...}}]}
  ```

  Mapped to inline, plain-Russian field messages; the raw `msg` is not displayed.

- **`409 Conflict` is not declared anywhere in the OpenAPI document** (group delete
  documents only `204` and `422`). The client still maps `409` defensively — for a group
  delete it means "in use, disable instead" — but this behaviour is unverified.

Guard against `403`, `404`, `429`, and `5xx`; responses may not always be JSON, so a
non-JSON error body must not crash the client.

## Transport

- HTTPS with verification on (never disabled). `certifi` bundle in packaged builds.
- Prefer HTTP/2 — the server negotiates `h2` over ALPN; HTTP/1.1 fallback is fine.
- Explicit connect/read/write/pool timeouts; one shared client (connection reuse).
- Follow redirects: no.

## Caveats to confirm with the backend owner

1. Session cookie name (`gui_session`) — not in OpenAPI; confirm once by logging in.
2. `409` semantics on group delete — not documented.
3. Whether `POST /api/v1/filters` accepts an `enabled` flag — not in the schema.
