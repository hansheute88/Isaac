@echo off
setlocal
cd /d "%~dp0"
title Isaac Master-Install
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_isaac_master_windows.ps1" %*
exit /b %ERRORLEVEL%