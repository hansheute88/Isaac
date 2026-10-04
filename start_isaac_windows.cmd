@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Isaac - Windows 11

chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

echo.
echo ==============================================
echo  Isaac - Windows 11
echo ==============================================
echo  Arbeitsverzeichnis: %CD%
echo.

if not exist ".venv\Scripts\python.exe" (
  echo [HINWEIS] Isaac ist noch nicht eingerichtet. Starte Setup-Skript...
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "install_windows11.ps1" -NoStart
  if not exist ".venv\Scripts\python.exe" (
    echo [FEHLER] Einrichtung fehlgeschlagen. Bitte install_windows11.ps1 manuell pruefen.
    echo.
    pause
    goto :end
  )
)

call ".venv\Scripts\activate.bat"
set "ISAAC_BIND_HOST=127.0.0.1"
if "%MONITOR_HTTP_PORT%"=="" set "MONITOR_HTTP_PORT=8766"

echo  Dashboard: http://127.0.0.1:%MONITOR_HTTP_PORT%
echo  WebSocket: ws://127.0.0.1:8765
echo.
echo  Isaac wird jetzt gestartet.
echo  Dieses Fenster bleibt geoeffnet, solange Isaac laeuft.
echo  Bei einem Fehler bleibt das Fenster ebenfalls offen.
echo ==============================================
echo.

".venv\Scripts\python.exe" "isaac_core.py"
set "ISAAC_EXIT_CODE=%ERRORLEVEL%"

echo.
echo ==============================================
if "%ISAAC_EXIT_CODE%"=="0" (
  echo  Isaac wurde beendet.
) else (
  echo  [FEHLER] Isaac wurde mit Fehlercode %ISAAC_EXIT_CODE% beendet.
  echo.
  echo  Die Fehlermeldung oben ist fuer die Diagnose wichtig.
)
echo ==============================================
echo.
pause
:end
