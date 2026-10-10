[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$EvidenceDir,
    [Parameter(Mandatory = $true)]
    [string]$BackupDir,
    [string]$HealthUrl = "http://127.0.0.1:8766/",
    [int]$StartupTimeoutMinutes = 10
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"

function Stop-Setup([string]$Reason) {
    Write-Error $Reason
    exit 2
}

if (-not (Test-Path $Python)) {
    Stop-Setup "Lokale Python-Umgebung fehlt. Bitte zuerst install_windows11.ps1 erfolgreich ausführen."
}

$branchName = (& git -C $RepoRoot branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $branchName -ne "isaac-2.0/masterplan") {
    Stop-Setup "Sicherheitsstopp: erwartet wird Branch isaac-2.0/masterplan, gefunden: $branchName"
}
$dirty = (& git -C $RepoRoot status --porcelain)
if ($LASTEXITCODE -ne 0 -or $dirty) {
    Stop-Setup "Sicherheitsstopp: Git-Arbeitsverzeichnis muss sauber sein. Keine Beweise mit uncommitted Code starten."
}
$revision = (& git -C $RepoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or -not $revision) {
    Stop-Setup "Git-Revision konnte nicht ermittelt werden."
}

$EvidenceDir = [IO.Path]::GetFullPath($EvidenceDir)
$BackupDir = [IO.Path]::GetFullPath($BackupDir)
if ($EvidenceDir -eq $BackupDir) {
    Stop-Setup "Evidenz- und Backup-Verzeichnis müssen verschieden sein."
}
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$evidenceDrive = [IO.Path]::GetPathRoot($EvidenceDir)
$backupDrive = [IO.Path]::GetPathRoot($BackupDir)
if ($evidenceDrive -eq $backupDrive) {
    Stop-Setup "Backup muss auf einem anderen Laufwerk oder einem separaten Netzlaufwerk liegen. Evidenz: $evidenceDrive; Backup: $backupDrive"
}
if (Test-Path (Join-Path $EvidenceDir "run_state.json")) {
    Stop-Setup "Dieses Evidenzverzeichnis enthält bereits einen Lauf. Nichts wird überschrieben; verwende einen neuen Ordner."
}

Write-Host "Prüfe Supervisor-Tests ..."
& $Python -m unittest tests_isaac_30day_evidence
if ($LASTEXITCODE -ne 0) {
    Stop-Setup "Evidence-Supervisor-Tests fehlgeschlagen; Isaac wird nicht gestartet."
}
& $Python -m py_compile isaac_30day_evidence.py isaac_autonomy_cycle.py isaac_learning_causality.py isaac_interest_derivation.py motivation.py goal_store.py
if ($LASTEXITCODE -ne 0) {
    Stop-Setup "Kompilierungsprüfung fehlgeschlagen; Isaac wird nicht gestartet."
}

$env:ISAAC_30DAY_EVIDENCE_DIR = $EvidenceDir
$env:ISAAC_30DAY_OFFICIAL = "1"

Write-Host "Initialisiere Evidenzlauf für Revision $revision ..."
& $Python -m isaac_30day_evidence init --evidence-dir $EvidenceDir --source-revision $revision --health-url $HealthUrl --interval-seconds 60 --backup-dir $BackupDir
if ($LASTEXITCODE -ne 0) {
    Stop-Setup "Evidenzlauf konnte nicht initialisiert werden."
}

Write-Host "Starte Isaac. Der offizielle 30-Tage-Zähler läuft NOCH NICHT."
$isaac = Start-Process -FilePath $Python -ArgumentList "isaac_core.py" -WorkingDirectory $RepoRoot -PassThru
$deadline = (Get-Date).AddMinutes($StartupTimeoutMinutes)
$healthy = $false
while ((Get-Date) -lt $deadline) {
    if ($isaac.HasExited) { break }
    try {
        $response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
            $healthy = $true
            break
        }
    } catch { }
    Start-Sleep -Seconds 5
}
if (-not $healthy) {
    & $Python -m isaac_30day_evidence fail --evidence-dir $EvidenceDir --reason "startup_health_timeout_or_process_exit"
    Stop-Setup "Isaac wurde innerhalb des Zeitlimits nicht gesund. Der Lauf ist als FAILED markiert; Evidenz wurde nicht gelöscht."
}

$stdout = Join-Path $EvidenceDir "supervisor.stdout.log"
$stderr = Join-Path $EvidenceDir "supervisor.stderr.log"
$watchArgs = '-m isaac_30day_evidence watch --evidence-dir "' + $EvidenceDir + '"'
$watcher = Start-Process -FilePath $Python -ArgumentList $watchArgs -WorkingDirectory $RepoRoot -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
Write-Host ""
Write-Host "Isaac-Prozess-ID: $($isaac.Id)"
Write-Host "Supervisor-Prozess-ID: $($watcher.Id)"
Write-Host "Evidenz: $EvidenceDir"
Write-Host "Backups: $BackupDir"
Write-Host "Revision: $revision"
Write-Host "Status prüfen: & '$Python' -m isaac_30day_evidence verify --evidence-dir '$EvidenceDir'"
Write-Host "WICHTIG: PC am Strom lassen und Ruhezustand vermeiden. Eine Überwachungslücke invalidiert den Lauf."
Write-Host "Der offizielle 30-Tage-Zähler startet automatisch erst nach bestandenen 24h-, 48h- und 72h-Gates."
