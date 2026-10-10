param(
    [Parameter(Mandatory = $true)]
    [string]$BackupDirectory,
    [string]$SourceRevision = "",
    [string]$RunDirectory = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Runner = Join-Path $PSScriptRoot "isaac_30day_run.py"

if (-not (Test-Path $Python)) {
    throw "Lokales Python fehlt: $Python. Bitte zuerst Isaac mit install_windows11.ps1 einrichten."
}

# An official run must use the canonical masterplan branch and a clean checkout.
$GitDir = Join-Path $RepoRoot ".git"
if (Test-Path $GitDir) {
    $Branch = (& git -C $RepoRoot branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or $Branch -ne "isaac-2.0/masterplan") {
        throw "Offizieller Lauf verweigert: Branch muss isaac-2.0/masterplan sein (aktuell: $Branch)."
    }
    $Dirty = (& git -C $RepoRoot status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $Dirty) {
        throw "Offizieller Lauf verweigert: Working Tree ist nicht sauber."
    }
    $DetectedRevision = (& git -C $RepoRoot rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Git-Revision konnte nicht ermittelt werden." }
    if ($SourceRevision -and $SourceRevision.ToLowerInvariant() -ne $DetectedRevision.ToLowerInvariant()) {
        throw "SourceRevision stimmt nicht mit HEAD überein."
    }
    $SourceRevision = $DetectedRevision
} elseif (-not $SourceRevision) {
    throw "Kein .git-Verzeichnis vorhanden. Bitte -SourceRevision mit dem exakten 40-stelligen Build-Commit angeben."
}

if ($SourceRevision -notmatch '^[0-9a-fA-F]{40}$') {
    throw "SourceRevision muss ein exakter 40-stelliger Git-Commit-SHA sein."
}

$LocalBase = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME "AppData\Local" }
if (-not $RunDirectory) {
    $RunDirectory = Join-Path $LocalBase ("Isaac\autonomy-30day\run-" + (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ"))
}
$RunDirectory = [System.IO.Path]::GetFullPath($RunDirectory)
$BackupDirectory = [System.IO.Path]::GetFullPath($BackupDirectory)
if ($RunDirectory.StartsWith($BackupDirectory, [System.StringComparison]::OrdinalIgnoreCase) -or
    $BackupDirectory.StartsWith($RunDirectory, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Run- und Backup-Verzeichnis dürfen sich nicht überlappen."
}
if ([System.IO.Path]::GetPathRoot($RunDirectory) -eq [System.IO.Path]::GetPathRoot($BackupDirectory)) {
    throw "Für den offiziellen Lauf muss das Backup auf einem anderen Laufwerk liegen (z. B. D:\IsaacEvidenceBackup)."
}

# Compile before creating the run. This is a setup check, not proof of autonomy.
Push-Location $RepoRoot
try {
    & $Python -m py_compile decision_trace.py isaac_autonomy_cycle.py isaac_autonomy_reconstruction.py isaac_autonomy_verification.py scripts\isaac_30day_run.py
    if ($LASTEXITCODE -ne 0) { throw "Python-Kompilierung fehlgeschlagen." }
    $TestStamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    $TestStdout = Join-Path $env:TEMP ("isaac-30day-tests-" + $TestStamp + ".stdout.log")
    $TestStderr = Join-Path $env:TEMP ("isaac-30day-tests-" + $TestStamp + ".stderr.log")
    $TestProcess = Start-Process -FilePath $Python -ArgumentList @("-m", "unittest", "tests_isaac_autonomy_cycle", "tests_isaac_autonomy_reconstruction", "tests_isaac_autonomy_verification", "tests_isaac_governance_gate", "tests_isaac_30day_run") -WorkingDirectory $RepoRoot -Wait -PassThru -RedirectStandardOutput $TestStdout -RedirectStandardError $TestStderr
    if ($TestProcess.ExitCode -ne 0) { throw "Autonomie-/Governance-Tests fehlgeschlagen. Preflight wurde nicht gestartet. Logs: $TestStdout ; $TestStderr" }

    & $Python $Runner --run-dir $RunDirectory init --source-revision $SourceRevision --backup-dir $BackupDirectory
    if ($LASTEXITCODE -ne 0) { throw "Run-Initialisierung fehlgeschlagen." }
    Copy-Item $TestStdout (Join-Path $RunDirectory "preflight-tests.stdout.log")
    Copy-Item $TestStderr (Join-Path $RunDirectory "preflight-tests.stderr.log")
    $TestReport = @{
        schema = "isaac.30day.preflight-tests.v1"
        source_revision = $SourceRevision.ToLowerInvariant()
        exit_code = $TestProcess.ExitCode
        test_command = "python -m unittest tests_isaac_autonomy_cycle tests_isaac_autonomy_reconstruction tests_isaac_autonomy_verification tests_isaac_governance_gate tests_isaac_30day_run"
        finished_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        stdout_sha256 = (Get-FileHash (Join-Path $RunDirectory "preflight-tests.stdout.log") -Algorithm SHA256).Hash.ToLowerInvariant()
        stderr_sha256 = (Get-FileHash (Join-Path $RunDirectory "preflight-tests.stderr.log") -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $TestReportPath = Join-Path $RunDirectory "preflight-tests.json"
    $TestReportJson = ($TestReport | ConvertTo-Json -Depth 5) + [Environment]::NewLine
    [System.IO.File]::WriteAllText($TestReportPath, $TestReportJson, [System.Text.UTF8Encoding]::new($false))
    & $Python $Runner --run-dir $RunDirectory backup-now
    if ($LASTEXITCODE -ne 0) { throw "Initiales Evidence-Backup fehlgeschlagen." }

    $env:ISAAC_AUTONOMY_TRACE_PATH = Join-Path $RunDirectory "runtime-trace.jsonl"
    $Stdout = Join-Path $RunDirectory "isaac-stdout.log"
    $Stderr = Join-Path $RunDirectory "isaac-stderr.log"
    $Isaac = Start-Process -FilePath $Python -ArgumentList @("isaac_core.py") -WorkingDirectory $RepoRoot -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru
    Write-Host "Isaac PID: $($Isaac.Id)"
    Write-Host "Preflight läuft. Der offizielle 30-Tage-Zähler ist NOCH NICHT gestartet."
    Write-Host "Evidenz: $RunDirectory"
    Write-Host "Backup:  $BackupDirectory"
    & $Python $Runner --run-dir $RunDirectory monitor --pid $Isaac.Id --interval 60 --backup-interval 900
    if ($LASTEXITCODE -ne 0) { throw "Evidence-Monitor meldete einen Fehler." }
} finally {
    Pop-Location
}
