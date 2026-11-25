# Agente Inteligente de Riego

Proyecto academico del Entregable 2 de IA Agentica. AgroRiego combina un modelo alojado en Groq con recuperacion de conocimiento, reglas explicables y un modulo probabilistico. FastAPI atiende las consultas del agente y Django REST Framework conserva conversaciones, reglas y auditoria.

## Funciones implementadas

- Agente LangChain conectado con Groq.
- Endpoint `POST /chat` y pagina web de demostracion.
- Memoria conversacional temporal por `session_id`.
- RAG con documentos locales y base vectorial Chroma.
- Pipeline de ingesta, division en fragmentos y embeddings reproducibles.
- Sistema basado en reglas para humedad, temperatura, lluvia, suelo y seguridad.
- Estimacion bayesiana simple de necesidad de riego.
- Fuentes, reglas y probabilidad incluidas en la respuesta JSON.
- Microservicio Django/DRF con conversaciones, mensajes, reglas, documentos y auditoria.
- Panel administrativo de Django.
- Registro tolerante a fallos desde FastAPI hacia Django.
- Pruebas automatizadas de API, RAG, reglas, Bayes y Django.

## Arquitectura

```text
Navegador
   |
   v
FastAPI :8000 ---- LangChain ---- Groq
   |  |                 |
   |  +---- Reglas -----+
   |  +---- Bayes ------+
   |  +---- Chroma/RAG -+---- knowledge/*.md
   |
   +---- HTTP JSON ---- Django/DRF :8001 ---- SQLite
```

FastAPI puede responder aunque Django no este disponible. En ese caso, `management_logged` sera `false`, pero la conversacion no falla.

## Instalacion en Windows

1. Extrae completamente el ZIP.
2. Abre PowerShell dentro de `agente-riego-ia`.
3. Ejecuta:

```powershell
.\instalar.bat
```

El instalador crea `.venv`, instala dependencias, prepara SQLite, ejecuta las migraciones e indexa la carpeta `knowledge` en Chroma.

4. Abre `.env` y reemplaza `GROQ_API_KEY` por una clave personal.
5. Confirma que `GROQ_MODEL` exista en tu cuenta de Groq.
6. Inicia ambos microservicios:

```powershell
.\iniciar_todo.bat
```

Se abre Django en una segunda terminal y FastAPI permanece en la terminal principal.

## Direcciones

| Servicio | Direccion |
|---|---|
| Chatbot | http://127.0.0.1:8000 |
| Swagger FastAPI | http://127.0.0.1:8000/docs |
| Salud FastAPI | http://127.0.0.1:8000/health |
| API Django | http://127.0.0.1:8001/api/ |
| Administracion Django | http://127.0.0.1:8001/admin/ |

## Crear un administrador

Con el entorno virtual activado:

```powershell
.\.venv\Scripts\python.exe management_service\manage.py createsuperuser
```

## Actualizar la base de conocimiento

Agrega o edita archivos `.md` o `.txt` en `knowledge` y ejecuta:

```powershell
.\ingerir_conocimiento.bat
```

El proceso reconstruye la coleccion local. No subas `data/chroma` al repositorio; se genera nuevamente a partir de los documentos.

## Ejemplo de consulta

```json
{
  "message": "Tengo jitomate en suelo arenoso, humedad 18 %, temperatura 34 y no se espera lluvia. ¿Debo regar?",
  "session_id": "demo-01"
}
```

La respuesta contiene:

```json
{
  "answer": "Respuesta fundamentada del agente",
  "session_id": "demo-01",
  "model": "openai/gpt-oss-20b",
  "sources": ["02_suelos_sustratos.md"],
  "rules_fired": ["R-HUM-01", "R-TEMP-01", "R-CLIMA-02", "R-SUELO-01"],
  "bayes_probability": 0.9,
  "reasoning": ["Explicaciones del motor"],
  "management_logged": true
}
```

## Contrato entre microservicios

FastAPI envia a `POST http://127.0.0.1:8001/api/exchanges/`:

```json
{
  "session_id": "demo-01",
  "question": "Pregunta del usuario",
  "answer": "Respuesta del agente",
  "sources": ["archivo.md"],
  "rules": ["R-HUM-01"],
  "bayes_probability": 0.8
}
```

Django crea o recupera la conversacion, almacena dos mensajes y registra un evento de auditoria.

## API de gestion

| Metodo | Ruta | Funcion |
|---|---|---|
| GET/POST | `/api/conversations/` | Gestionar conversaciones |
| GET | `/api/messages/` | Consultar mensajes |
| GET | `/api/audit-logs/` | Consultar auditoria |
| GET/POST | `/api/rules/` | Gestionar configuracion de reglas |
| GET/POST | `/api/knowledge-documents/` | Registrar documentos |
| POST | `/api/exchanges/` | Recibir una interaccion de FastAPI |

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe management_service\manage.py test core
```

Las pruebas del agente no consumen la API de Groq. Para una demostracion completa si se requiere una clave valida y conexion a internet.

## Estructura principal

```text
agente-riego-ia/
├── app/                         FastAPI, agente, RAG, reglas y Bayes
├── knowledge/                   Base documental indexable
├── management_service/         Django y Django REST Framework
├── docs/                        Arquitectura, modelo y Scrum
├── tests/                       Pruebas del agente
├── instalar.bat
├── iniciar.bat
├── iniciar_gestion.bat
├── iniciar_todo.bat
├── ingerir_conocimiento.bat
├── .env.example
└── requirements.txt
```

## Limitaciones

- Los embeddings por hashing priorizan ejecucion local y reproducible; no sustituyen un modelo semantico entrenado para produccion.
- Los umbrales de reglas y razones de verosimilitud de Bayes son demostrativos.
- SQLite es apropiado para la entrega academica, no para alta concurrencia.
- La API de demostracion no implementa autenticacion completa.
- El agente no controla sensores, bombas o valvulas reales ni consulta clima en tiempo real.
