# 🌱 AgroRiego — Agente Inteligente de Riego

![Pruebas](https://github.com/D3vo1/Agente-Riego-IA/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Django](https://img.shields.io/badge/Django%20REST-092E20?logo=django&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white)

Proyecto académico del Entregable 2 de IA Agéntica (2026). AgroRiego combina un modelo alojado en Groq con recuperación de conocimiento, reglas explicables y un módulo probabilístico. FastAPI atiende las consultas del agente y Django REST Framework conserva conversaciones, reglas y auditoría.

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

### Mejoras posteriores a la entrega

- **Extracción de datos más robusta.** Reconoce negaciones ("no hay lluvia esperada"), separa la humedad relativa o ambiental de la del suelo, no confunde "temporada 2026" con una temperatura, acepta plurales y acentos, y entiende "probabilidad de lluvia 80 %" o "34 °C".
- **Regla de seguridad R-SEG-01 más amplia.** Detecta cualquier orden de abrir, encender o activar válvulas, bombas o riego, en singular o plural. No se puede desactivar.
- **Cultivos no reconocidos.** La regla R-DAT-02 avisa cuando el cultivo no está en la base de conocimiento en lugar de ignorarlo.
- **Datos acumulados por conversación.** El usuario puede dar cultivo, suelo y humedad en mensajes distintos; la respuesta incluye `facts` y `missing_data`.
- **Reglas configurables desde Django.** FastAPI lee `/api/rules/` (cada `RULES_REFRESH_SECONDS`) y deja de aplicar las reglas con `enabled = false`.
- **RAG más preciso.** Los embeddings ignoran palabras vacías y acentos, y `RAG_MAX_DISTANCE` descarta fragmentos sin relación con la pregunta.
- **API de gestión protegida.** Con `MANAGEMENT_API_KEY` definida, Django exige la cabecera `X-API-Key`; `DJANGO_DEBUG` y `DJANGO_ALLOWED_HOSTS` se leen de `.env`.
- **Operación.** Los fallos de arranque e integración quedan en el log, la memoria se limita a `MAX_SESSIONS` conversaciones y las dependencias tienen versiones fijas.

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

1. Clona el repositorio o extrae el ZIP.
2. Abre PowerShell dentro de la carpeta del proyecto.
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
  "facts": {"cultivo": "tomate", "suelo": "arenoso", "humedad_suelo": 18.0, "temperatura": 34.0, "lluvia_esperada": false},
  "missing_data": [],
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
├── docs/                        Documentación de cada entregable
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
- La API de gestión solo se protege con una clave compartida; no hay usuarios por agricultor.
- La extracción de datos usa expresiones regulares; frases muy distintas a los ejemplos pueden no reconocerse.
- El agente no controla sensores, bombas o valvulas reales ni consulta clima en tiempo real.

## Documentación del curso

| # | Documento | Tema |
|---|---|---|
| 1 | [Fundamentos de IA](docs/01-fundamentos-ia.docx) | Historia de la IA y modelo lógico del agente |
| 2 | [Diseño del agente](docs/02-diseno-del-agente.docx) | Especificación PEAS, agente híbrido BDI y arquitectura inicial |
| 3 | [Heurística A\*](docs/03-heuristica-a-estrella.docx) | Planificación del riego entre zonas con búsqueda A\* |
| 4 | [Scrum y JIRA](docs/04-scrum-jira.docx) | Backlog, épicas, criterios de aceptación y sprints |
| — | [Guía de instalación (v1)](docs/guia-instalacion.docx) | Instalación del primer entregable |
| E2 | [Documentación del Entregable 2](docs/entregable-2/Documentacion_Entregable2_AgroRiego_IA.docx) | RAG, reglas, Bayes y microservicios |
| E2 | [Guía de instalación del Entregable 2](docs/entregable-2/Guia_Instalacion_Entregable2_AgroRiego_IA.docx) | Instalación de ambos servicios |
| E2 | [Arquitectura](docs/entregable-2/arquitectura_entregable2.md) · [Modelo de conocimiento](docs/entregable-2/modelo_conocimiento.md) · [Sprints 3 y 4](docs/entregable-2/jira_sprints_3_4.md) | Material de apoyo |

---

Desarrollado por **David Melgoza** ([@D3vo1](https://github.com/D3vo1)).
