<#
.SYNOPSIS
    Build the Windows release bundle for Market Monitor GUI.

.DESCRIPTION
    Builds a self-contained Windows x64 application and zips it as
    ``MarketMonitor-windows-x64.zip`` with a top-level ``MarketMonitor\`` folder that
    contains ``MarketMonitor.exe``.

    The package version must already be set (CI runs
    ``uv run python scripts/set_version.py <tag>`` first); this script only reads it.

    Default freezer is Nuitka ``--standalone`` (directory build). If the MSVC toolchain
    is unavailable or the Nuitka build fails, use ``-Freezer PyInstaller`` as a fallback;
    it produces the same layout and zip name.

    Both freezers run in a runtime-only environment (``--no-default-groups``), with the
    freeze tool from the ``packaging`` group or an ephemeral ``--with`` overlay. Dev
    tools must not be installed during a build: Nuitka follows ``pydantic.mypy`` and
    would otherwise compile all of ``mypy`` into the bundle. Run ``uv sync`` afterwards
    to restore the ``dev`` group for day-to-day work.

.PARAMETER Freezer
    ``Nuitka`` (default) or ``PyInstaller``.

.PARAMETER OutputDir
    Build root. Defaults to ``build`` at the repository root, which keeps paths short.

.PARAMETER NoZip
    Skip creating ``MarketMonitor-windows-x64.zip``.

.EXAMPLE
    pwsh -File scripts/build_windows.ps1

.EXAMPLE
    pwsh -File scripts/build_windows.ps1 -Freezer PyInstaller
#>
[CmdletBinding()]
param(
    [ValidateSet('Nuitka', 'PyInstaller')]
    [string]$Freezer = 'Nuitka',
    [string]$OutputDir = 'build',
    [switch]$NoZip
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $iconPath = 'src/market_monitor_gui/assets/icons/app.ico'
    $pngPath = 'src/market_monitor_gui/assets/icons/app-256.png'
    foreach ($asset in @($iconPath, $pngPath)) {
        if (-not (Test-Path -LiteralPath $asset)) {
            throw "Missing icon asset: $asset"
        }
    }

    $version = (uv run --no-project python scripts/set_version.py --get).Trim()
    if ($version -notmatch '^(?<major>\d+)\.(?<minor>\d+)\.(?<patch>\d+)') {
        throw "Cannot derive a numeric file version from '$version'"
    }
    $fileVersion = '{0}.{1}.{2}.0' -f $Matches.major, $Matches.minor, $Matches.patch
    Write-Host "Building Market Monitor $version (file version $fileVersion) with $Freezer"

    if (Test-Path -LiteralPath $OutputDir) {
        Remove-Item -LiteralPath $OutputDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $OutputDir | Out-Null

    $exePath = Join-Path $OutputDir 'MarketMonitor/MarketMonitor.exe'

    if ($Freezer -eq 'Nuitka') {
        $nuitkaArgs = @(
            '--standalone',
            '--enable-plugin=tk-inter',
            '--assume-yes-for-downloads',
            "--output-dir=$OutputDir",
            '--output-filename=MarketMonitor.exe',
            "--windows-icon-from-ico=$iconPath",
            '--windows-console-mode=disable',
            '--include-data-dir=src/market_monitor_gui/assets=market_monitor_gui/assets',
            '--nofollow-import-to=mypy',
            '--nofollow-import-to=pydantic.mypy',
            '--nofollow-import-to=pydantic.v1.mypy',
            '--nofollow-import-to=pytest',
            '--nofollow-import-to=_pytest',
            '--nofollow-import-to=pyright',
            '--nofollow-import-to=ruff',
            '--nofollow-import-to=setuptools',
            "--report=$OutputDir/nuitka-report.xml",
            '--company-name=Market Monitor',
            '--product-name=Market Monitor',
            '--file-description=Market Monitor desktop client',
            "--file-version=$fileVersion",
            "--product-version=$fileVersion",
            '--remove-output',
            'src/market_monitor_gui/main.py'
        )
        uv run --frozen --exact --no-default-groups --group packaging nuitka @nuitkaArgs
        if ($LASTEXITCODE -ne 0) {
            throw "Nuitka build failed with exit code $LASTEXITCODE"
        }

        $distDir = Join-Path $OutputDir 'main.dist'
        if (-not (Test-Path -LiteralPath $distDir)) {
            throw "Nuitka output not found: $distDir"
        }
        Move-Item -LiteralPath $distDir -Destination (Join-Path $OutputDir 'MarketMonitor')
    }
    else {
        $pyInstallerArgs = @(
            '--noconfirm',
            '--clean',
            '--onedir',
            '--windowed',
            '--name', 'MarketMonitor',
            '--icon', $iconPath,
            '--paths', 'src',
            '--add-data', 'src/market_monitor_gui/assets;market_monitor_gui/assets',
            '--collect-all', 'customtkinter',
            '--collect-all', 'certifi',
            '--distpath', (Join-Path $OutputDir 'pyinstaller-dist'),
            '--workpath', (Join-Path $OutputDir 'pyinstaller-work'),
            '--specpath', $OutputDir,
            'src/market_monitor_gui/main.py'
        )
        uv run --frozen --exact --no-default-groups --with 'pyinstaller>=6.15,<7' pyinstaller @pyInstallerArgs
        if ($LASTEXITCODE -ne 0) {
            throw "PyInstaller build failed with exit code $LASTEXITCODE"
        }

        $distDir = Join-Path $OutputDir 'pyinstaller-dist/MarketMonitor'
        if (-not (Test-Path -LiteralPath $distDir)) {
            throw "PyInstaller output not found: $distDir"
        }
        Move-Item -LiteralPath $distDir -Destination (Join-Path $OutputDir 'MarketMonitor')
    }

    if (-not (Test-Path -LiteralPath $exePath)) {
        throw "Expected executable not found: $exePath"
    }

    Write-Host "Built $exePath"

    if (-not $NoZip) {
        $zipPath = Join-Path $repoRoot 'MarketMonitor-windows-x64.zip'
        if (Test-Path -LiteralPath $zipPath) {
            Remove-Item -LiteralPath $zipPath -Force
        }
        Compress-Archive -Path (Join-Path $OutputDir 'MarketMonitor') -DestinationPath $zipPath
        $sizeMb = [math]::Round((Get-Item -LiteralPath $zipPath).Length / 1MB, 1)
        Write-Host "Wrote $zipPath ($sizeMb MB)"
    }
}
finally {
    Pop-Location
}
