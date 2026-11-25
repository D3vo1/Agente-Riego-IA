@echo off
echo Creando entorno virtual...
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
echo Preparando base de datos Django...
python management_service\manage.py migrate
echo Indexando documentos en Chroma...
python -m app.ingest
echo.
echo Instalacion terminada. Abre .env, agrega GROQ_API_KEY y ejecuta iniciar_todo.bat.
pause

