@echo off
cd /d "%~dp0..\.."
rem Historical DuckDB workflow: stop before preparation if its native import is blocked.
".venv\Scripts\python.exe" -c "import duckdb"
if errorlevel 1 goto duckdb_blocked
".venv\Scripts\python.exe" "03_Code\01_Data_Preparation\prepare_data.py"
if errorlevel 1 goto failed
echo Ready. Open 03_Open_Learning_Notebook.bat for the first lesson.
pause
exit /b 0
:failed
echo Preparation stopped. Keep this window open so I can read the message.
pause
exit /b 1

:duckdb_blocked
echo This shortcut uses the historical DuckDB preparation workflow.
echo DuckDB could not load. Keep Windows security enabled.
echo Open README.md for the current SQLite workflow and saved-results instructions.
echo No preparation was started.
pause
exit /b 1
