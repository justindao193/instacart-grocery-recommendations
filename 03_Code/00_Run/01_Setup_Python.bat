@echo off
cd /d "%~dp0..\.."
rem Reuse an existing environment; create a new one with the tested Python minor version.
if exist ".venv\Scripts\python.exe" goto check_python
py -3.13 -m venv .venv
if errorlevel 1 goto failed
:check_python
".venv\Scripts\python.exe" -c "import sys; assert sys.version_info[:2] == (3, 13), 'Use Python 3.13 for this project environment.'"
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r 03_Code\00_Run\requirements-lock.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m ipykernel install --prefix .venv --name python3 --display-name "Instacart Project (Python)"
if errorlevel 1 goto failed
echo Setup complete. Source files and saved analysis outputs are separate from this environment.
pause
exit /b 0
:failed
echo Setup failed. Check that Python 3.13 is installed and read the error above.
echo No source data or saved model outputs were rebuilt.
pause
exit /b 1
