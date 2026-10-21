## Market Monitor — Desktop GUI {{version}}

Portable build for **Windows 10/11 x64**. Python is not required.

### Download
`{{asset}}` — extract the whole archive to any folder and run
`MarketMonitor\MarketMonitor.exe`. Start the executable from inside the extracted folder:
it needs the files shipped next to it.

### First run
1. Start `MarketMonitor.exe`.
2. Open **Settings** (the application UI is in Russian) and set the API origin (default:
   `https://api.market-resale-signal.xubi.org`).
3. Enter the shared application secret (APP_SECRET) there and save it. It is kept only on
   this computer, encrypted, under `%LOCALAPPDATA%\market-monitor-gui`.
4. Connect and check the **Overview** screen.

The secret is **not** part of the build and is never shipped with it.

### SmartScreen and antivirus
The build is not code-signed. Windows may show "Windows protected your PC": click
**"More info" → "Run anyway"**. Some antivirus products may warn about an unknown
executable — the bundle is built automatically from source in GitHub Actions.

### If the application does not start
- `MarketMonitor.exe --version` prints the version; this confirms the executable is intact.
- If Windows reports a missing `VCRUNTIME140.dll`, install the
  "Microsoft Visual C++ 2015–2022 Redistributable (x64)".

---

Operator notes in Russian are attached to this release as `release-notes.russian.md`.

Build date: {{date}} · tag: `{{tag}}`
