# Building the Windows release

The release workflow (`.github/workflows/release-windows.yml`) runs exactly this on
`windows-latest`; the same steps work on a developer Windows machine.

## Prerequisites

- Windows 10/11 x64
- [uv](https://docs.astral.sh/uv/) (installs Python 3.14 itself)
- For the default Nuitka build: Visual Studio 2022 (or newer) **Build Tools** with the
  "Desktop development with C++" workload and the English language pack
- PyInstaller fallback needs no compiler

## Steps

```powershell
git clone <repo>
cd market-monitor-gui
git checkout v0.1.0

uv sync --python 3.14
uv run python scripts/set_version.py v0.1.0   # version comes from the release tag
pwsh -File scripts/build_windows.ps1
```

Output:

```text
build/MarketMonitor/MarketMonitor.exe   # plus runtime files and package data
MarketMonitor-windows-x64.zip           # top-level MarketMonitor/ folder
```

The script checks the icon assets, derives the 4-part file version, builds with a hidden
console, and zips the folder. `-NoZip` skips the zip; `-OutputDir <dir>` moves the build
root (keep it short: Windows MAX_PATH).

## What must be inside the build

```powershell
Test-Path build/MarketMonitor/MarketMonitor.exe
Test-Path build/MarketMonitor/market_monitor_gui/assets/icons/app.ico
Test-Path build/MarketMonitor/market_monitor_gui/assets/icons/app-256.png
```

Missing icons do not stop the app, but the window/About dialog has no icon. The zip must
not contain `.env`, `secret.key`, or `secret.enc` — the operator enters the shared secret
in the app and it is stored encrypted under `%LOCALAPPDATA%\market-monitor-gui`.

## PyInstaller fallback

If Nuitka cannot find MSVC (`cl.exe`) or the compile step fails:

```powershell
pwsh -File scripts/build_windows.ps1 -Freezer PyInstaller
```

It produces the same `MarketMonitor-windows-x64.zip` layout and needs no C toolchain.
PyInstaller is installed on demand via `uv run --with 'pyinstaller>=6.15,<7'`; it is not a
project dependency.

## Troubleshooting

- **`Cannot find MSVC` / `The system cannot find the file cl.exe`** — install VS 2022
  Build Tools with C++ and the English language pack, or use the PyInstaller fallback.
- **Long path errors** — build from a short root (`C:\mmgui`), keep `-OutputDir` short.
- **Antivirus/SmartScreen flags the exe** — expected for an unsigned build; the release
  notes tell operators how to proceed. Code signing is a later step.
- **App starts without a window** — run `MarketMonitor.exe --version` from a console; a
  non-zero exit code means the frozen import failed (check the VC++ 2015-2022 x64
  redistributable on the target machine).
