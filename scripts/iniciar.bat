@echo off
cd /d "%~dp0.."
if not exist .venv\Scripts\activate.bat (
  echo Primero ejecuta scripts\instalar.bat
  pause
  exit /b 1
)
call .venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

