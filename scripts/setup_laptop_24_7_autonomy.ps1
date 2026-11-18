# Isaac — Laptop-Setup für dauerhaften Betrieb (24/7) mit maximaler Owner-Freigabe
# Hinweis: Constitution, Privilege-Gates und Audit bleiben aktiv (kein „Governance-Aus").
[CmdletBinding()]
param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [switch]$RegisterWatchdogTask,
    [switch]$ApplyPowerPlanHint
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

function Step([string]$m) { Write-Host "`n==> $m" -ForegroundColor Cyan }

Step "Virtuelle Umgebung prüfen"
$venvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    & (Join-Path $RepoRoot "install_windows11.ps1") -NoStart -SkipPlaywright
}

Step "Runtime-Verzeichnisse"
foreach ($d in @("data", "logs", "runtime", "workspace", "traces")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot $d) | Out-Null
}

Step ".env — Owner-Admin, Autonomie, lokale Ports"
$envPath = Join-Path $RepoRoot ".env"
$envBlock = @'
# Isaac — Laptop 24/7 (Owner-Admin, lokale Bindung)
ISAAC_BIND_HOST=127.0.0.1
MONITOR_PORT=8765
DASHBOARD_PORT=8766
PORT=5000
ISAAC_DISABLE_VECTOR_MEMORY=1
ISAAC_OWNER=Steffen
ISAAC_PRIVILEGE_MODE=admin
ISAAC_OWNER_AUTONOMY=1
ISAAC_BROWSER_AUTOMATION=1
ISAAC_BROWSER_EXTERNAL_SITES=1
ISAAC_COMPUTER_USE_ENABLED=1
ISAAC_COMPUTER_USE_LIVE=1
ISAAC_FREE_ONLY_PROVIDERS=0
# Provider-Keys in .env.local eintragen (gitignored):
# OPENROUTER_API_KEY=
# GROQ_API_KEY=
# GOOGLE_API_KEY=
# OLLAMA_HOST=http://127.0.0.1:11434
'@
if (-not (Test-Path $envPath)) {
    Set-Content -Path $envPath -Value $envBlock.TrimEnd() -Encoding UTF8
    Write-Host "  .env angelegt."
} else {
    Write-Host "  .env existiert bereits — prüfe manuell: ISAAC_PRIVILEGE_MODE=admin, ISAAC_OWNER_AUTONOMY=1"
}

Step "runtime_settings.json — volle lokale Fähigkeiten"
$settingsPath = Join-Path $RepoRoot "data\runtime_settings.json"
$settings = @{
    settings = @{
        filesystem_full_access     = $true
        filesystem_access_tier     = "full"
        browser_automation         = $true
        browser_external_sites     = $true
        auto_provision_providers   = $true
        auto_provision_all_providers = $true
        computer_use_enabled       = $true
        computer_use_live          = $true
        free_only_providers        = $false
        multi_tool_mode            = $true
        style_mode                 = "professional"
    }
    owner_autonomy = @{
        enabled = $true
    }
}
$settings | ConvertTo-Json -Depth 5 | Set-Content -Path $settingsPath -Encoding UTF8

Step "Kurzvalidierung"
& $venvPy -m py_compile isaac_core.py executor.py low_complexity.py memory.py
$env:ISAAC_DISABLE_VECTOR_MEMORY = "1"
& $venvPy sanity_check.py

Step "Start-Optionen"
Write-Host @"

  Interaktiv (Fenster offen):
    .\start_isaac_windows.cmd

  24/7 mit Auto-Neustart bei Absturz:
    powershell -ExecutionPolicy Bypass -File .\scripts\run_isaac_24_7_watchdog.ps1

  Health: http://127.0.0.1:8766/  (DASHBOARD_PORT; API oft :5000)

  Wichtig — Windows Energie (manuell, als Admin):
    powercfg /change standby-timeout-ac 0
    powercfg /change monitor-timeout-ac 30
    powercfg /change hibernate-timeout-ac 0

  Offizieller 30-Tage-Proof (evidenzbasiert, Branch isaac-2.0/masterplan):
    docs\ISAAC_30DAY_PROOF_RUNBOOK.md

"@ -ForegroundColor Green

if ($ApplyPowerPlanHint) {
    Write-Host "Führe powercfg nur aus, wenn du die Konsole als Administrator geöffnet hast." -ForegroundColor Yellow
}

if ($RegisterWatchdogTask) {
    $watchdog = Join-Path $RepoRoot "scripts\run_isaac_24_7_watchdog.ps1"
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$watchdog`""
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)
    Register-ScheduledTask -TaskName "Isaac24x7Watchdog" -Action $action -Trigger $trigger -Settings $settings -Description "Isaac Kernel mit Watchdog-Neustart" -Force
    Write-Host "Geplante Aufgabe Isaac24x7Watchdog registriert (bei Anmeldung)." -ForegroundColor Green
}