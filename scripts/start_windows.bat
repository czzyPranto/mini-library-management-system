@echo off
REM From the project root: scripts\start_windows.bat
cd /d "%~dp0.."
if not exist .venv (python -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
python manage.py migrate
if errorlevel 1 exit /b 1
python manage.py seed_demo
if errorlevel 1 exit /b 1
python manage.py check
if errorlevel 1 exit /b 1
python manage.py runserver
