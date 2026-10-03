@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Isaac ist noch nicht installiert.
 echo Bitte IsaacSetup.exe erneut ausfuehren.
 exit /b 1
)
call ".venv\Scripts\activate.bat"
set "ISAAC_BIND_HOST=127.0.0.1"
if "%MONITOR_HTTP_PORT%"=="" set "MONITOR_HTTP_PORT=8766"
echo ==============================================
echo  Isaac - Windows 11
echo  Monitor: http://127.0.0.1:%MONITOR_HTTP_PORT%
echo ==============================================
".venv\Scripts\python.exe" "isaac_core.py"
