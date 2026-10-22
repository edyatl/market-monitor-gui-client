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

Contract details for implementers: [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) (verified against the live OpenAPI document).

## Authentication model

1. Operator provides the **application secret** (same value the server knows as the client secret).
2. Client calls `POST /api/v1/auth/app-login` with `{"client_secret": "..."}`.
3. Server sets a session cookie; the client keeps it in an in-memory HTTPX cookie jar.
4. All other `/api/v1/*` calls send that cookie. The secret and the session are **not** written to SQLite or config files.
5. On `401`, a safe **read** may trigger **one** coordinated re-login if a secret is available; **writes are never replayed** — the screen refreshes and shows server state.

### API origin and secret precedence

- `API_BASE_URL` is an **origin only** (scheme + host + optional port); a trailing `/api/v1` is tolerated and stripped on load.
- Automatic login uses the environment / `.env` secret (`APP_SECRET`, or legacy `API_APP_KEY`) first, then the saved encrypted secret. A secret typed in the login dialog is used for that login only.

### Connection and app secret

The app tracks two independent things: whether a **secret** is available (environment
override or the encrypted store) and the current **session** (signed out, connecting,
signed in, or expired).

- On startup the app signs in automatically when a secret resolves; otherwise it shows
  the authentication screen and opens the login dialog.
- The login dialog has a «keep the secret on this computer» checkbox, **checked by
  default**. The secret is written only **after a successful login**.
- If an automatic sign-in is rejected, the login dialog opens in manual-entry mode with
  the error. Network-only failures just update the status line; retry with «Sign in».
- **Connection settings** shows whether a secret is saved (as a masked placeholder, never
  the value), allows replacing it, and offers **Forget secret**. Unchecking the store box
  and saving also deletes it.
- **Disconnect** (main menu) ends the session only: cookies are dropped, the saved secret
  stays, and the authentication screen appears. **Forget secret** in Connection settings
  deletes the stored secret without ending the current session; the next sign-in needs
  the secret again.
- An `APP_SECRET` (or `API_APP_KEY`) override takes precedence over the stored secret and
  cannot be removed from the UI; Connection settings says so when it is active.

## Configuration and data locations

| Item | Purpose |
|------|---------|
| `.env` (dev) | `APP_SECRET`, `API_BASE_URL` — never commit real secrets |
| `config.json` | Non-secret config (API origin) in the per-user data directory |
| `secret.key` / `secret.enc` | Fernet key + encrypted secret (owner-only permissions) |
| `state.db` (SQLite) | UI state (theme, last screen, window geometry) and last successful API responses for display |

Everything lives in a **per-user data directory**: `$XDG_DATA_HOME`/`~/.local/share/market-monitor-gui` (Linux) or `%LOCALAPPDATA%\MarketMonitor` (Windows). Override with `MARKET_MONITOR_GUI_DATA_DIR`. Nothing is written beside the executable or into a Nuitka one-file extraction directory.

### Optional local reference: backend Russian texts

To keep wording aligned with the Telegram bot, you may place a **local, git-ignored**
copy of the backend's Russian strings at `reference/backend_texts_ru.py`. This path
is listed in `.gitignore` and is **not** imported by runtime code — it is a manual
reference only. Never commit backend bot texts or real secrets.

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

Nuitka is the packaging tool for Linux and Windows. Windows releases are built by
GitHub Actions (see below); the same commands work locally. Nuitka lives in the
non-default `packaging` dependency group so a build never installs the `dev` group
(mypy, pytest, ruff, …) into the freeze environment — Nuitka follows
`pydantic.mypy`, which imports `mypy.*`, and would otherwise compile the whole type
checker into the bundle. A Linux smoke build:

```bash
uv sync --frozen --no-default-groups --group packaging
uv run --frozen --exact --no-default-groups --group packaging nuitka \
  --standalone --assume-yes-for-downloads --enable-plugin=tk-inter \
  --output-dir=build --output-filename=MarketMonitor \
  --include-data-dir=src/market_monitor_gui/assets=market_monitor_gui/assets \
  src/market_monitor_gui/main.py
```

Nuitka's built-in package configuration already ships `certifi` (`cacert.pem`) and
`customtkinter` (`assets/`, including the themes and Roboto fonts), so no
`--include-package-data` flags are needed. Run `uv sync` afterwards to restore the
`dev` group for local work.

The window icon is resolved **relative to the package**, never the working directory, so
frozen builds must ship the icon assets:

- `src/market_monitor_gui/assets/icons/app.ico` — window icon on Windows, and the
  recommended executable icon when packaging:
  `--windows-icon-from-ico=src/market_monitor_gui/assets/icons/app.ico`
- `src/market_monitor_gui/assets/icons/app-256.png` — window icon on Linux/macOS and the
  About-dialog logo

Include both with `--include-package-data=market_monitor_gui` (or
`--include-data-dir=src/market_monitor_gui/assets=market_monitor_gui/assets`). A build
without them still starts, just without an icon. Wheel/editable installs already ship the
files as package data.

The full Windows command (including the exe icon, hidden console, and version metadata)
lives in `scripts/build_windows.ps1`; see `scripts/build_windows.md`.

## Windows release (GitHub Actions)

`.github/workflows/release-windows.yml` builds the portable Windows x64 bundle on
`windows-latest` with Nuitka `--standalone` (onedir), zips it as
**`MarketMonitor-windows-x64.zip`** (a top-level `MarketMonitor/` folder with
`MarketMonitor.exe`), uploads a workflow artifact, and attaches the zip to the GitHub
Release for the tag. The job installs only runtime dependencies plus the `packaging`
group (`uv sync --frozen --no-default-groups --group packaging`), verifies that the
Nuitka report contains no dev tooling (mypy/pytest/pyright/ruff), and checks that the
`certifi` CA bundle and CustomTkinter theme/font assets are present in the bundle.

### Tagging a release

```bash
git tag -a v0.1.0 -m "Market Monitor GUI 0.1.0"
git push origin v0.1.0
```

The version comes from the tag: `v0.1.0` → `0.1.0`, `v1.0.0-alpha` → `1.0.0a0`.
`__version__` in `src/market_monitor_gui/__init__.py` is the single source of truth
(hatchling reads it for the wheel); CI rewrites it from the tag on the checked-out tree
only — that mutation is never committed.

### Running the workflow manually

Actions → **release-windows** → **Run workflow**:

- with a **tag** input (e.g. `v0.1.0`) → rebuild and replace the asset on that tag's
  release;
- **without** a tag → build the selected ref and keep the zip as a workflow artifact only
  (no Release).

The job needs only `GITHUB_TOKEN` (`contents: write`); no repository secrets are used.

### What the operator downloads

`MarketMonitor-windows-x64.zip` from the release page → extract the whole `MarketMonitor`
folder → run `MarketMonitor.exe`. Python is not required.

- The shared application secret is **entered in the app** (Settings screen; the UI is in
  Russian) and stored encrypted under `%LOCALAPPDATA%\market-monitor-gui`; it is never
  baked into the build.
- The build is unsigned. Windows SmartScreen may show "Windows protected your PC": click
  **"More info" → "Run anyway"**. Antivirus products may warn about an unknown
  executable; code signing is a later step.
- The API origin is pre-filled with the production default and can be changed in Settings.
- If Windows reports a missing `VCRUNTIME140.dll`, install the Microsoft Visual C++
  2015–2022 Redistributable (x64).

Russian operator notes are attached to every release as `release-notes.russian.md`
(the English text below is the release body).

### Windows 10 VM smoke checklist

1. Fresh Windows 10 x64 VM without Python.
2. Extract the zip and run `MarketMonitor.exe` — the window opens with the app icon.
3. `MarketMonitor.exe --version` in a console prints the version.
4. Open Settings → check the API origin → enter APP_SECRET → save → connect.
5. Overview/Groups/Filters load; make one harmless change and reload to confirm it stuck.
6. Restart the app: the secret and API origin survive; no `.env` exists in the app folder.
7. `%LOCALAPPDATA%\market-monitor-gui` contains `config.json`, `secret.key`, `secret.enc`.

### Fallback

If the Nuitka/MSVC toolchain is unavailable, the PyInstaller path in
`scripts/build_windows.md` (`pwsh -File scripts/build_windows.ps1 -Freezer PyInstaller`)
produces the same `MarketMonitor-windows-x64.zip` layout without a C compiler.

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
