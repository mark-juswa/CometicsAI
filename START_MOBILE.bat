@echo off
setlocal
cd /d "%~dp0"
python scripts\mobile_launch.py
set "MOBILE_EXIT=%ERRORLEVEL%"
if not "%MOBILE_EXIT%"=="0" pause
exit /b %MOBILE_EXIT%
