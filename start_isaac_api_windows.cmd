@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Isaac ist noch nicht installiert.
 exit /b 1
)
call ".venv\Scripts\activate.bat"
echo Isaac Flask API: http://127.0.0.1:5000
".venv\Scripts\python.exe" -m flask --app app:app run --host 127.0.0.1 --port 5000
