# Isaac - Windows 11 (PowerShell-Fassung; ersetzt start_isaac_windows.cmd)
[CmdletBinding()]
param()

$RepoRoot = if ($PSScriptRoot) { $PSScriptRoot } elseif ($MyInvocation.MyCommand.Path) { Split-Path -Parent $MyInvocation.MyCommand.Path } else { (Get-Location).Path }
Set-Location $RepoRoot

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

Write-Host ""
Write-Host "=============================================="
Write-Host " Isaac - Windows 11"
Write-Host "=============================================="
Write-Host " Arbeitsverzeichnis: $RepoRoot"
Write-Host ""

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$failed = $false
$exitCode = 0

$needsSetup = $false
if (-not (Test-Path $VenvPython)) {
    $needsSetup = $true
} else {
    try {
        & $VenvPython -c "import sys; print(sys.executable)" *> $null
        if ($LASTEXITCODE -ne 0) { $needsSetup = $true }
    } catch {
        $needsSetup = $true
    }
}

if ($needsSetup) {
    Write-Host "[HINWEIS] Isaac richtet seine lokale Python-Umgebung ein..."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "install_windows11.ps1") -NoStart
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FEHLER] Einrichtung fehlgeschlagen."
        Write-Host ""
        $failed = $true
    }
}

if (-not $failed -and -not (Test-Path $VenvPython)) {
    Write-Host "[FEHLER] Lokales Python wurde nicht erstellt."
    Write-Host ""
    $failed = $true
}

if (-not $failed) {
    try {
        & $VenvPython -c "import sys; print(sys.executable)" *> $null
        if ($LASTEXITCODE -ne 0) { $failed = $true }
    } catch {
        $failed = $true
    }
    if ($failed) {
        Write-Host "[FEHLER] Lokales Python ist weiterhin nicht lauffaehig."
        Write-Host ""
    }
}

if (-not $failed) {
    $env:ISAAC_BIND_HOST = "127.0.0.1"
    if (-not $env:MONITOR_HTTP_PORT) { $env:MONITOR_HTTP_PORT = "8766" }

    Write-Host " Dashboard: http://127.0.0.1:$($env:MONITOR_HTTP_PORT)"
    Write-Host " WebSocket: ws://127.0.0.1:8765"
    Write-Host ""
    Write-Host " Isaac wird jetzt gestartet."
    Write-Host " Dieses Fenster bleibt geoeffnet, solange Isaac laeuft."
    Write-Host " Bei einem Fehler bleibt das Fenster ebenfalls offen."
    Write-Host "=============================================="
    Write-Host ""

    & $VenvPython (Join-Path $RepoRoot "isaac_core.py")
    $exitCode = $LASTEXITCODE

    Write-Host ""
    Write-Host "=============================================="
    if ($exitCode -eq 0) {
        Write-Host " Isaac wurde beendet."
    } else {
        Write-Host " [FEHLER] Isaac wurde mit Fehlercode $exitCode beendet."
        Write-Host ""
        Write-Host " Die Fehlermeldung oben ist fuer die Diagnose wichtig."
    }
    Write-Host "=============================================="
    Write-Host ""
}

# Fenster offen halten (wie das fruehere "pause" der .cmd-Fassung)
try {
    if ($Host.Name -eq 'ConsoleHost' -and -not [Console]::IsInputRedirected) {
        Read-Host "Enter druecken zum Schliessen" | Out-Null
    }
} catch {}

if ($failed) { exit 1 } else { exit $exitCode }
