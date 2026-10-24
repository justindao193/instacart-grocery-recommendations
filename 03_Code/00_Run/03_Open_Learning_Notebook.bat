@echo off
cd /d "%~dp0..\.."
".venv\Scripts\python.exe" -m jupyterlab "04_Learning\03_Notebooks\01_Data_And_SQL.ipynb"
if errorlevel 1 pause
