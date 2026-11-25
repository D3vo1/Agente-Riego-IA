@echo off
if not exist .venv\Scripts\activate.bat (
  echo Primero ejecuta instalar.bat
  pause
  exit /b 1
)
call .venv\Scripts\activate
python -m app.ingest
pause
