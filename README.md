# Market Monitor — Desktop GUI

Operator control panel for the **Market Monitor** backend.  
Manage monitoring groups, shared price-drop settings, and exclusion filters; view worker health and dashboard counts. The app talks to the existing FastAPI API over HTTPS and does **not** scrape the marketplace or send Telegram messages itself.

## Features (v1)

- Sign in with the shared application secret (`POST /api/v1/auth/app-login`); session continues via the `gui_session` cookie
- Overview: API connectivity, worker health, last scan, summary counters
- Monitoring groups: list, add, edit, enable/disable, delete (with clear handling of conflicts)
- Settings: global price-drop threshold (%)
- Exclusion filters: add/remove phrases (normalization is done on the server)
- Help screen with short operator tips
- Local SQLite cache for last successful data and UI state (offline-friendly display only)
- Secret stored encrypted on disk (Fernet); optional `.env` for development

## Non-goals

- Telegram bot UI, invites, or user roles
- Starting/stopping scans (scheduler/worker own that)
- Direct access to PostgreSQL or Redis
- Marketplace scraping or price logic in the client

## Requirements

- **Development:** Python 3.14+, [uv](https://github.com/astral-sh/uv)
- **Runtime (from source):** Linux recommended first; Windows supported with the same codebase
- **Network:** HTTPS access to the API (default production host below)
- **Packaged builds:** Nuitka (Linux first, then Windows) — see packaging notes later in this file

## Quick start (development)

```bash
git clone <this-repo-url>
cd market-monitor-gui   # or your clone directory name
uv sync
cp .env.example .env
# Edit .env:
#   APP_SECRET=<same shared secret as API API_APP_KEY>
#   API_BASE_URL=https://api.market-resale-signal.xubi.org
uv run python -m market_monitor_gui
```

If `APP_SECRET` is set in `.env`, the app can log in without a saved encrypted secret.  
You can still save the secret from **Connection settings** for subsequent runs without `.env`.

### Default API

| Setting        | Default                                              |
|----------------|------------------------------------------------------|
| API base URL   | `https://api.market-resale-signal.xubi.org`          |
| Auth           | `POST /api/v1/auth/app-login` → cookie `gui_session` |
| Protected API  | Cookie only (do not rely on `X-App-Key` in the GUI)  |

Contract details for implementers: [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) (add when bootstrap is done).

## Authentication model

1. Operator provides the **application secret** (same value the server knows as the client secret / `API_APP_KEY`).
2. Client calls `POST /api/v1/auth/app-login` with `{"client_secret": "..."}`.
3. Server sets HttpOnly session cookie; client keeps it in an in-memory HTTPX cookie jar.
4. All other `/api/v1/*` calls send that cookie. Session JWT is **not** written to SQLite or config files.
5. On `401`, the client may try **one** coordinated re-login if the secret is available; otherwise it shows the login UI.

## Configuration and data locations

| Item | Purpose |
|------|---------|
| `.env` (dev) | `APP_SECRET`, `API_BASE_URL` — never commit real secrets |
| Encrypted config + key file | Persisted secret (Fernet); next to the executable or in a per-user app data directory |
| SQLite DB | UI state (theme, last screen, window geometry) and last successful API responses for display |

One-file Nuitka builds extract to a temp directory: **never** store config/DB only inside that extract path; resolve the real executable location or use a user data directory.

## Project layout (target)

```text
src/market_monitor_gui/
  texts/ru.py          # All operator-facing Russian strings
  api/                 # HTTPX transport, typed client, errors, DTOs
  auth/                # Session lifecycle
  config/              # Config + encrypted secret store
  db/                  # SQLite cache and UI state
  services/            # Feature operations used by screens
  background/          # Off-UI-thread tasks
  ui/                  # CustomTkinter windows, screens, dialogs
  platforms/linux|windows/
```

See **AGENTS.md** and **CONVENTIONS.md** for agent and coding rules.

## Quality checks

```bash
uv run ruff format .
uv run ruff check --fix .
uv run mypy --strict src
uv run pytest
```

Russian UI strings live only under `texts/ru.py` (Ruff rule exceptions configured in `pyproject.toml`).

## Packaging (Nuitka)

1. Run and test from source on Linux.
2. Build standalone, verify TLS, HTTP/2 negotiation, secret save/load, and UI assets.
3. Optionally build one-file; re-test config path next to the real binary.
4. Repeat for Windows when Linux is stable.

Exact build commands will live under `scripts/` once packaging tasks are implemented.

## Security notes

- Prefer verified HTTPS; do not disable TLS verification.
- Prefer HTTP/2 when the stack negotiates it; HTTP/1.1 fallback is acceptable.
- Encrypted secret on disk reduces casual exposure; it does **not** protect against malware running as the same user.
- Do not log secrets, cookies, or full sensitive response bodies.

## Related systems

| Component | Role |
|-----------|------|
| FastAPI control plane | Auth, settings, groups, filters, health, dashboard |
| Worker | Scraping, baseline/lifecycle, notification events |
| Telegram bot | Operator notifications and bot-side admin UX |
| This GUI | Desktop configuration and status for the same shared monitoring data |

## License

MIT: [LICENSE](./LICENSE)
