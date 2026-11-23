# Isaac — Master-Install (Windows): Python, pip, Playwright, optional Memory, MCP-Grundcheck, Validierung
[CmdletBinding()]
param(
    [switch]$SkipPlaywright,
    [switch]$WithMemoryExtras,
    [switch]$WithVectorMemory,
    [switch]$NoStart
)

$ErrorActionPreference = "Stop"

if ($PSScriptRoot) {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
} elseif ($MyInvocation.MyCommand.Path) {
    $RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
} else {
    $RepoRoot = (Get-Location).Path
}
Set-Location $RepoRoot

function Step([string]$m) { Write-Host "`n==> $m" -ForegroundColor Cyan }

Step "Basis-Setup (venv, requirements, Verzeichnisse)"
$installArgs = @("-NoStart")
if ($SkipPlaywright) { $installArgs += "-SkipPlaywright" }
& (Join-Path $RepoRoot "install_windows11.ps1") @installArgs
if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "install_windows11.ps1 fehlgeschlagen (exit $LASTEXITCODE)" }

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not $SkipPlaywright) {
    Step "Playwright-Paket + Chromium (Browser)"
    & $VenvPython -m pip install "playwright>=1.40.0"
    & $VenvPython -m playwright install chromium
    & $VenvPython -c "from playwright.sync_api import sync_playwright; print('Playwright: OK')"
}

if ($WithMemoryExtras) {
    Step "Optionale Memory-Backends (mem0, cognee — kann Minuten dauern)"
    & $VenvPython -m pip install -r (Join-Path $RepoRoot "requirements-memory-extra.txt")
}

if ($WithVectorMemory) {
    Step "ChromaDB fuer Vector-Memory"
    & $VenvPython -m pip install "chromadb>=0.4.0"
    Write-Host "  Hinweis: ISAAC_DISABLE_VECTOR_MEMORY in .env entfernen oder auf 0 setzen, um Vektorspeicher zu nutzen."
}

Step "MCP / Kernel-Module kompilieren"
$mcpModules = @(
    "mcp_registry.py", "mcp_jsonrpc.py", "mcp_client.py", "mcp_server.py",
    "isaac_mcp.py", "mcp_integration.py", "tool_bridge.py"
)
& $VenvPython -m py_compile @mcpModules

$mcpExample = Join-Path $RepoRoot "mcp_config.json.example"
$mcpLive = Join-Path $RepoRoot "mcp_config.json"
if ((Test-Path $mcpExample) -and -not (Test-Path $mcpLive)) {
    Copy-Item $mcpExample $mcpLive
    Write-Host "  mcp_config.json aus Beispiel angelegt (anpassen nach docs/ISAAC_MCP.md)."
}

Step "sanity_check.py"
$env:ISAAC_DISABLE_VECTOR_MEMORY = if ($WithVectorMemory) { "0" } else { "1" }
& $VenvPython sanity_check.py

Step "Regression (Phase A — unittest, ohne Vector)"
& $VenvPython -m unittest tests_phase_a_stabilization tests_state_io tests_provider_configuration -q

Write-Host @"

============================================================
 Isaac Master-Install abgeschlossen
============================================================
 Start:     powershell -ExecutionPolicy Bypass -File .\start_isaac_windows.ps1
 24/7:      powershell -ExecutionPolicy Bypass -File .\scripts\run_isaac_24_7_watchdog.ps1
 Laptop:    powershell -ExecutionPolicy Bypass -File .\scripts\setup_laptop_24_7_autonomy.ps1

 Dashboard: http://127.0.0.1:8766  (DASHBOARD_PORT in .env)
 WebSocket: ws://127.0.0.1:8765

 Optional:
   Ollama: https://ollama.ai  →  ollama pull qwen2.5:1.5b
   Keys:   .env.local (gitignored) — GROQ, OPENROUTER, GOOGLE_API_KEY
   MCP:    docs/ISAAC_MCP.md — ISAAC_MCP_API_KEY fuer Remote-HTTP

============================================================
"@ -ForegroundColor Green

if (-not $NoStart) {
    $start = Read-Host "Isaac jetzt starten? [j/N]"
    if ($start -match '^[jyJy]') {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "start_isaac_windows.ps1")
    }
}