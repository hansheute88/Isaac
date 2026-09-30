@echo off
setlocal

REM ======================================================
REM  Isaac - start on Windows 10/11 (native Python)
REM  Local-first: ACTIVE_PROVIDER=ollama preferred; if Ollama
REM  is not reachable Isaac falls back to API models
REM  (groq/gemini/openrouter) automatically via relay fallback.
REM ======================================================

if not exist .venv\Scripts\python.exe (
  echo [ERROR] No venv found. Run install_windows.bat first.
  pause
  exit /b 1
)

if not exist .env (
  copy .env.example .env >nul
  echo [OK] .env created from .env.example - edit it and set GROQ_API_KEY.
)

echo.
echo [Isaac] Dashboard:  http://localhost:8766
echo [Isaac] WebSocket:  ws://localhost:8765
echo [Isaac] Stop with Ctrl+C
echo.

.venv\Scripts\python.exe isaac_core.py
pause
