# Isaac - Master-Install (Windows): Wrapper um scripts\install_isaac_master_windows.ps1
# PowerShell-Fassung; ersetzt install_isaac_master_windows.cmd
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Rest
)

$RepoRoot = if ($PSScriptRoot) { $PSScriptRoot } elseif ($MyInvocation.MyCommand.Path) { Split-Path -Parent $MyInvocation.MyCommand.Path } else { (Get-Location).Path }
Set-Location $RepoRoot

$target = Join-Path $RepoRoot "scripts\install_isaac_master_windows.ps1"
if (-not (Test-Path $target)) {
    Write-Host "[FEHLER] Nicht gefunden: $target"
    exit 1
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $target @Rest
exit $LASTEXITCODE
