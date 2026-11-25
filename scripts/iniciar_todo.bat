@echo off
cd /d "%~dp0.."
if not exist .venv\Scripts\activate.bat (
  echo Primero ejecuta scripts\instalar.bat
  pause
  exit /b 1
)
start "AgroRiego Gestion Django" cmd /k call scripts\iniciar_gestion.bat
timeout /t 2 /nobreak >nul
call scripts\iniciar.bat
