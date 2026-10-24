@echo off
cd /d "%~dp0..\.."
".venv\Scripts\python.exe" "03_Code\06_Guide\refresh_guide.py"
if errorlevel 1 goto failed
exit /b 0
:failed
echo Guide refresh failed. Read the message above.
pause
exit /b 1
