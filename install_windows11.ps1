# Isaac – Windows 11 Setup
# Creates an isolated Python 3.12+ environment, installs Isaac dependencies,
# installs Playwright Chromium, creates a local .env when missing, and verifies startup.
# Run from the Isaac repository root in PowerShell:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\install_windows11.ps1

[CmdletBinding()]
param(
    [switch]$SkipPlaywright,
    [switch]$SkipOptionalMemory,
    [switch]$NoStart
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Fail([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

function Test-Command([string]$Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

Write-Host "==============================================" -ForegroundColor Green
Write-Host " Isaac – Windows 11 Setup" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green

Write-Step "Prüfe Windows / Architektur"
if ([Environment]::OSVersion.Platform -ne "Win32NT") {
    Fail "Dieses Setup ist für Windows vorgesehen."
}
if (-not [Environment]::Is64BitOperatingSystem) {
    Fail "Isaac benötigt ein 64-Bit-Windows-System."
}

Write-Step "Prüfe Git"
if (-not (Test-Command "git")) {
    Fail "Git wurde nicht gefunden. Installiere Git für Windows und starte PowerShell danach neu."
}
Write-Host "Git: $((git --version).Trim())"

Write-Step "Suche Python 3.12+"
$python = $null
$pythonCandidates = @("py", "python")
foreach ($candidate in $pythonCandidates) {
    if (Test-Command $candidate) {
        try {
            $candidateVersion = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
            $major, $minor, $patch = $candidateVersion.Trim().Split(".")
            if ([int]$major -gt 3 -or ([int]$major -eq 3 -and [int]$minor -ge 12)) {
                $python = $candidate
                break
            }
        } catch {
            continue
        }
    }
}
if ($null -eq $python) {
    Fail "Python 3.12 oder neuer wurde nicht gefunden. Installiere Python 3.12+ (64-bit) und aktiviere 'Add python.exe to PATH'."
}
$pythonVersion = & $python --version
Write-Host "Python: $($pythonVersion.Trim())"

Write-Step "Erstelle virtuelle Umgebung"
$VenvPath = Join-Path $RepoRoot ".venv"
if (-not (Test-Path $VenvPath)) {
    & $python -m venv $VenvPath
}
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$VenvPip = Join-Path $VenvPath "Scripts\pip.exe"
if (-not (Test-Path $VenvPython)) {
    Fail "Die virtuelle Umgebung konnte nicht erstellt werden."
}

Write-Step "Aktualisiere pip / Build-Werkzeuge"
& $VenvPython -m pip install --upgrade pip setuptools wheel

Write-Step "Installiere Isaac-Abhängigkeiten"
if (-not (Test-Path (Join-Path $RepoRoot "requirements.txt"))) {
    Fail "requirements.txt fehlt."
}
& $VenvPython -m pip install -r (Join-Path $RepoRoot "requirements.txt")

if (-not $SkipOptionalMemory -and (Test-Path (Join-Path $RepoRoot "requirements-memory-extra.txt"))) {
    Write-Step "Installiere optionale Memory-Adapter"
    & $VenvPython -m pip install -r (Join-Path $RepoRoot "requirements-memory-extra.txt")
} else {
    Write-Host "Optionale Memory-Adapter übersprungen."
}

if (-not $SkipPlaywright) {
    Write-Step "Installiere Playwright Chromium"
    & $VenvPython -m playwright install chromium
} else {
    Write-Host "Playwright-Browserinstallation übersprungen."
}

Write-Step "Erzeuge lokale Verzeichnisse"
foreach ($dir in @("data", "logs", "runtime", "workspace", "traces")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot $dir) | Out-Null
}

Write-Step "Erzeuge .env bei Bedarf"
$EnvPath = Join-Path $RepoRoot ".env"
if (-not (Test-Path $EnvPath)) {
    $envContent = @"
# Isaac – lokale Windows-Konfiguration
# Keine Geheimnisse ins Git-Repository committen.
ISAAC_BIND_HOST=127.0.0.1
PORT=5000
MONITOR_PORT=8765
MONITOR_HTTP_PORT=8766
ISAAC_DISABLE_VECTOR_MEMORY=1
# Optional:
# ISAAC_OWNER=DeinName
# ACTIVE_PROVIDER=ollama
# OLLAMA_HOST=http://127.0.0.1:11434
# OPENROUTER_API_KEY=
# GROQ_API_KEY=
# GOOGLE_API_KEY=
"@
    Set-Content -Path $EnvPath -Value $envContent -Encoding UTF8
    Write-Host ".env wurde angelegt."
} else {
    Write-Host ".env existiert bereits – unverändert."
}

Write-Step "Prüfe Python-Module"
& $VenvPython -c "import flask, aiohttp, websockets, dotenv; import app; print('Isaac Python-Import: OK')"

Write-Step "Kompiliere Kernmodule"
$coreModules = @(
    "isaac_core.py","executor.py","low_complexity.py","memory.py",
    "relay.py","logic.py","watchdog.py","task_checkpoint.py"
)
& $VenvPython -m py_compile @coreModules

Write-Step "Führe Stabilitätstests aus"
$env:ISAAC_DISABLE_VECTOR_MEMORY = "1"
& $VenvPython -m unittest tests_phase_a_stabilization tests_state_io tests_provider_configuration -q

Write-Step "Erstelle Windows-Startskripte"
$StartCmd = Join-Path $RepoRoot "start_isaac_windows.cmd"
@"
@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Isaac ist noch nicht installiert.
  echo Bitte install_windows11.ps1 zuerst ausfuehren.
  exit /b 1
)
call ".venv\Scripts\activate.bat"
set "ISAAC_BIND_HOST=127.0.0.1"
if "%MONITOR_HTTP_PORT%"=="" set "MONITOR_HTTP_PORT=8766"
echo Isaac startet auf http://127.0.0.1:%MONITOR_HTTP_PORT%
".venv\Scripts\python.exe" "isaac_core.py"
"@ | Set-Content -Path $StartCmd -Encoding ASCII

$ApiCmd = Join-Path $RepoRoot "start_isaac_api_windows.cmd"
@"
@echo off
setlocal
cd /d "%~dp0"
call ".venv\Scripts\activate.bat"
".venv\Scripts\python.exe" -m flask --app app:app run --host 127.0.0.1 --port 5000
"@ | Set-Content -Path $ApiCmd -Encoding ASCII

Write-Step "Setup erfolgreich"
Write-Host "Web/API:          http://127.0.0.1:5000"
Write-Host "Isaac Monitor:    http://127.0.0.1:8766"
Write-Host "Virtuelle Env:    $VenvPath"
Write-Host ""
Write-Host "Start:            .\start_isaac_windows.cmd" -ForegroundColor Green
Write-Host "Nur Flask API:    .\start_isaac_api_windows.cmd" -ForegroundColor Green

if (-not $NoStart) {
    Write-Step "Starte Isaac"
    & (Join-Path $RepoRoot "start_isaac_windows.cmd")
}
