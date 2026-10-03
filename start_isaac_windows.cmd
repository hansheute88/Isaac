@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Isaac - Windows 11

echo.
echo ==============================================
echo  Isaac - Windows 11
echo ==============================================
echo  Arbeitsverzeichnis: %CD%
echo.

if not exist ".venv\Scripts\python.exe" (
  echo [FEHLER] Isaac ist noch nicht eingerichtet.
  echo Bitte IsaacSetup.exe erneut ausfuehren.
  echo.
  pause
  exit /b 1
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
exit /b %ISAAC_EXIT_CODE%
