# Isaac API - Windows 11 (PowerShell-Fassung; ersetzt start_isaac_api_windows.cmd)
[CmdletBinding()]
param()

$RepoRoot = if ($PSScriptRoot) { $PSScriptRoot } elseif ($MyInvocation.MyCommand.Path) { Split-Path -Parent $MyInvocation.MyCommand.Path } else { (Get-Location).Path }
Set-Location $RepoRoot

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "[HINWEIS] Isaac ist noch nicht eingerichtet. Starte Setup-Skript..."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "install_windows11.ps1") -NoStart
    if (-not (Test-Path $VenvPython)) {
        Write-Host "[FEHLER] Einrichtung fehlgeschlagen. Bitte install_windows11.ps1 manuell pruefen."
        try {
            if ($Host.Name -eq 'ConsoleHost' -and -not [Console]::IsInputRedirected) {
                Read-Host "Enter druecken zum Schliessen" | Out-Null
            }
        } catch {}
        exit 1
    }
}

Write-Host "Isaac Flask API: http://127.0.0.1:5000"
& $VenvPython -m flask --app app:app run --host 127.0.0.1 --port 5000
exit $LASTEXITCODE
