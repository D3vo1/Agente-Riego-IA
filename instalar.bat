@echo off
echo Creando entorno virtual...
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
echo.
echo Instalacion terminada. Abre el archivo .env y agrega tu GROQ_API_KEY.
pause

