@echo off
if not exist .venv\Scripts\activate.bat (
  echo Primero ejecuta instalar.bat
  pause
  exit /b 1
)
start "AgroRiego Gestion Django" cmd /k call iniciar_gestion.bat
timeout /t 2 /nobreak >nul
call iniciar.bat
