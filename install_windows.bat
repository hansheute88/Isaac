@echo off
setlocal

REM ======================================================
REM  Isaac - one-time setup for Windows 10/11 (native Python)
REM  Installs slim deps (aiohttp/websockets/dotenv) - no
REM  Playwright, no ChromaDB, no admin rights needed.
REM ======================================================

echo ========================================
echo   Isaac - Windows Setup
echo ========================================

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found. Install Python 3.12 from python.org, check
  echo         "Add python.exe to PATH" during install, then re-run this file.
  pause
  exit /b 1
)

echo [1/3] Creating virtual environment ...
python -m venv .venv
if errorlevel 1 (
  echo [ERROR] Could not create .venv
  pause
  exit /b 1
)

echo [2/3] Installing dependencies ...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements-free.txt
if errorlevel 1 (
  echo [ERROR] pip install failed - check your internet connection.
  pause
  exit /b 1
)

echo [3/3] Preparing .env ...
if not exist .env (
  copy .env.example .env >nul
  powershell -NoProfile -Command "(Get-Content .env) -replace '^ACTIVE_PROVIDER=groq','ACTIVE_PROVIDER=ollama' | Set-Content .env"
  echo [OK]   .env created from .env.example with ACTIVE_PROVIDER=ollama.
  echo        Edit .env and set GROQ_API_KEY - it is the fallback when
  echo        Ollama is not running.
) else (
  echo [OK]   .env already exists - left untouched.
)

echo.
echo ========================================
echo   Setup done!
echo   Optional (local model): install Ollama
echo   from https://ollama.ai then run:
echo     ollama pull qwen2.5:1.5b
echo   Start Isaac: run_isaac_windows.bat
echo ========================================
pause
