# Isaac 24/7 — startet isaac_core.py und startet nach Absturz neu (Backoff max 60s).
$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$venvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Write-Error "Kein .venv — zuerst install_windows11.ps1 oder setup_laptop_24_7_autonomy.ps1 ausführen."
    exit 1
}

$logDir = Join-Path $RepoRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "watchdog_24_7.log"

function Write-Log([string]$msg) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $logFile -Value $line
    Write-Host $line
}

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
if (Test-Path (Join-Path $RepoRoot ".env")) {
    Get-Content (Join-Path $RepoRoot ".env") | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
        $p = $_.Split('=', 2)
        if ($p.Count -eq 2) { Set-Item -Path "Env:$($p[0].Trim())" -Value $p[1].Trim() }
    }
}

$backoff = 5
while ($true) {
    Write-Log "Starte isaac_core.py (PID wird neu vergeben)..."
    $proc = Start-Process -FilePath $venvPy -ArgumentList "isaac_core.py" -WorkingDirectory $RepoRoot -PassThru -NoNewWindow
    Wait-Process -Id $proc.Id
    $code = $proc.ExitCode
    Write-Log "Isaac beendet mit ExitCode $code — Neustart in ${backoff}s"
    Start-Sleep -Seconds $backoff
    if ($backoff -lt 60) { $backoff = [Math]::Min(60, $backoff + 5) }
}