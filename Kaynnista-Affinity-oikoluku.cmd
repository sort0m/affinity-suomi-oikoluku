@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0voikko\launch.ps1" -Action start
if errorlevel 1 pause
