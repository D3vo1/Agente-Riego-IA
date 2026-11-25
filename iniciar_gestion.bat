@echo off
if not exist .venv\Scripts\activate.bat (
  echo Primero ejecuta instalar.bat
  pause
  exit /b 1
)
call .venv\Scripts\activate
python management_service\manage.py migrate
python management_service\manage.py runserver 127.0.0.1:8001
