# Isaac – Windows 11 Setup
[CmdletBinding()]
param([switch]$SkipPlaywright,[switch]$SkipOptionalMemory,[switch]$NoStart)
$ErrorActionPreference="Stop"; Set-StrictMode -Version Latest
$RepoRoot=Split-Path -Parent $MyInvocation.MyCommand.Path; Set-Location $RepoRoot
function Step([string]$m){Write-Host "";Write-Host "==> $m" -ForegroundColor Cyan}
function Fail([string]$m){Write-Host "ERROR: $m" -ForegroundColor Red;exit 1}
function Has([string]$n){$null -ne (Get-Command $n -ErrorAction SilentlyContinue)}
if([Environment]::OSVersion.Platform -ne "Win32NT"){Fail "Dieses Setup ist für Windows vorgesehen."}
if(-not [Environment]::Is64BitOperatingSystem){Fail "Isaac benötigt 64-Bit-Windows."}
Step "Prüfe Python 3.12+"
$python=$null
foreach($candidate in @("py","python")){
 if(Has $candidate){try{$v=& $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')";$p=$v.Trim().Split(".");if([int]$p[0]-gt 3 -or ([int]$p[0]-eq 3 -and [int]$p[1]-ge 12)){$python=$candidate;break}}catch{}}
}
if($null -eq $python -and (Has "winget")){
 Step "Python fehlt – Installation über winget"
 & winget install --id Python.Python.3.12 --exact --accept-package-agreements --accept-source-agreements --silent
 foreach($candidate in @("py","python")){if(Has $candidate){try{$v=& $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')";$p=$v.Trim().Split(".");if([int]$p[0]-gt 3 -or ([int]$p[0]-eq 3 -and [int]$p[1]-ge 12)){$python=$candidate;break}}catch{}}}
}
if($null -eq $python){Fail "Python 3.12+ wurde nicht gefunden."}
Write-Host "Python: $((& $python --version).Trim())"
$VenvPath=Join-Path $RepoRoot ".venv";$VenvPython=Join-Path $VenvPath "Scripts\python.exe"
if(-not(Test-Path $VenvPath)){& $python -m venv $VenvPath}
if(-not(Test-Path $VenvPython)){Fail "Virtuelle Umgebung konnte nicht erstellt werden."}
Step "Installiere Isaac-Abhängigkeiten"
& $VenvPython -m pip install --upgrade pip setuptools wheel
& $VenvPython -m pip install -r (Join-Path $RepoRoot "requirements.txt")
if(-not $SkipOptionalMemory){Write-Host "Optionale Memory-Adapter bleiben deaktiviert; Isaac Core benötigt sie nicht."}
if(-not $SkipPlaywright){Step "Installiere Playwright Chromium";& $VenvPython -m playwright install chromium}
Step "Erzeuge Runtime-Verzeichnisse"
foreach($d in @("data","logs","runtime","workspace","traces")){New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot $d)|Out-Null}
$EnvPath=Join-Path $RepoRoot ".env"
if(-not(Test-Path $EnvPath)){@"
# Isaac – lokale Windows-Konfiguration
ISAAC_BIND_HOST=127.0.0.1
PORT=5000
MONITOR_PORT=8765
MONITOR_HTTP_PORT=8766
ISAAC_DISABLE_VECTOR_MEMORY=1
ISAAC_COMPUTER_USE_ENABLED=1
ISAAC_COMPUTER_USE_LIVE=1
ISAAC_BROWSER_AUTOMATION=1
ISAAC_BROWSER_EXTERNAL_SITES=1
ISAAC_PRIVILEGE_MODE=user
# ACTIVE_PROVIDER=ollama
# OLLAMA_HOST=http://127.0.0.1:11434
# OPENROUTER_API_KEY=
# GROQ_API_KEY=
# GOOGLE_API_KEY=
"@|Set-Content $EnvPath -Encoding UTF8}
Step "Validiere Isaac"
& $VenvPython -c "import flask, aiohttp, websockets, dotenv; import app; print('Isaac Python-Import: OK')"
& $VenvPython -m py_compile isaac_core.py executor.py low_complexity.py memory.py relay.py logic.py watchdog.py task_checkpoint.py
$env:ISAAC_DISABLE_VECTOR_MEMORY="1"
& $VenvPython -m unittest tests_provider_configuration -q
Write-Host "Windows-spezifische Basisvalidierung erfolgreich." -ForegroundColor Green
Write-Host "Hinweis: plattformgebundene Unix-Permission-Tests laufen weiterhin in der Linux-CI."
Write-Host "Start: .\start_isaac_windows.cmd"
Write-Host "API:   http://127.0.0.1:5000"
Write-Host "UI:    http://127.0.0.1:8766"
if(-not $NoStart){& (Join-Path $RepoRoot "start_isaac_windows.cmd")}
