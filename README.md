# 🌱 AgroRiego — Agente Inteligente de Riego

![Pruebas](https://github.com/D3vo1/IA-2026/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white)

Agente conversacional que orienta a agricultores sobre **riego inteligente y uso responsable del agua**. El agente se expone como microservicio REST con **FastAPI**, y razona con un LLM (Llama 3.3 70B) a través de **LangChain** y **Groq**. Incluye una interfaz web de chat, memoria de conversación por sesión y pruebas automatizadas.

> Proyecto de la materia de Inteligencia Artificial (2026). El repositorio contiene el código del agente y la documentación de diseño de cada actividad del curso.

---

## ✨ Qué hace

- **Recomendaciones de riego explicadas.** El agente justifica cada sugerencia y pide los datos que faltan (cultivo, etapa, suelo, humedad, clima, sistema de riego) antes de dar una respuesta específica.
- **Comportamiento seguro por diseño.** El *prompt* del sistema le prohíbe inventar mediciones o afirmar que accionó válvulas, y ante fugas, riesgo eléctrico o inundación indica detener el sistema y pedir revisión técnica.
- **Memoria por sesión.** Cada `session_id` conserva su propio historial, limitado a una ventana configurable de mensajes.
- **API documentada.** Swagger se genera automáticamente en `/docs`.
- **Pruebas sin costo.** Los tests sustituyen la llamada al modelo, así que no consumen la API ni necesitan una clave real.

## 🏗️ Arquitectura

```text
Navegador (index.html) ──► FastAPI (app/main.py) ──► IrrigationAgent (app/agent.py) ──► LangChain ──► Groq (Llama 3.3 70B)
                                  │                              │
                           Validación con Pydantic        Historial en memoria
                             (app/schemas.py)               por session_id
```

| Componente | Archivo | Responsabilidad |
|---|---|---|
| API | `app/main.py` | Endpoints, manejo de errores (503 sin clave, 502 si falla el modelo) |
| Agente | `app/agent.py` | *Prompt* del sistema, ventana de historial, llamada asíncrona al LLM |
| Configuración | `app/config.py` | Variables de entorno (`.env`) |
| Esquemas | `app/schemas.py` | Modelos Pydantic de petición y respuesta |
| Interfaz | `app/static/index.html` | Chat web mínimo |
| Pruebas | `tests/test_api.py` | Pruebas de la API con el modelo simulado |

## 🔌 Endpoints

| Método | Ruta | Función |
|---|---|---|
| `GET` | `/` | Interfaz web del chatbot |
| `GET` | `/health` | Estado del servicio y del modelo configurado |
| `POST` | `/chat` | Enviar un mensaje al agente |
| `DELETE` | `/chat/{session_id}` | Borrar la memoria de una sesión |
| `GET` | `/docs` | Documentación Swagger |

Ejemplo de petición a `/chat`:

```json
{
  "message": "¿Debo regar el tomate si la humedad del suelo es 18 %?",
  "session_id": "demo-01"
}
```

Respuesta:

```json
{
  "answer": "Respuesta generada por el agente...",
  "session_id": "demo-01",
  "model": "llama-3.3-70b-versatile"
}
```

## 🚀 Cómo ejecutarlo

Requisitos: Python 3.11 o 3.12 y una clave gratuita de [Groq](https://console.groq.com/keys).

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # luego coloca tu GROQ_API_KEY en .env
python -m uvicorn app.main:app --reload
```

**Windows:** ejecuta `instalar.bat`, coloca tu clave en `.env` y luego ejecuta `iniciar.bat`.

Abre <http://127.0.0.1:8000> para usar el chat, o <http://127.0.0.1:8000/docs> para probar la API.

### Pruebas

```bash
pytest -q
```

## 📚 Documentación del curso

El proyecto se desarrolló por actividades. Los entregables de diseño están en [`docs/`](docs):

| # | Documento | Tema |
|---|---|---|
| 1 | [Fundamentos de IA](docs/01-fundamentos-ia.docx) | Historia de la IA y modelo lógico del agente (axiomas y teoremas en lógica de predicados) |
| 2 | [Diseño del agente](docs/02-diseno-del-agente.docx) | Especificación PEAS, agente híbrido BDI y arquitectura inicial |
| 3 | [Heurística A\*](docs/03-heuristica-a-estrella.docx) | Planificación del riego entre varias zonas con búsqueda A\* |
| 4 | [Scrum y JIRA](docs/04-scrum-jira.docx) | Backlog, épicas, criterios de aceptación y sprints |
| — | [Guía de instalación](docs/guia-instalacion.docx) | Instalación paso a paso |

## 🧭 Limitaciones y siguientes pasos

Esta versión corresponde al primer entregable. El historial vive en memoria y se pierde al reiniciar el servidor, y el agente no lee sensores ni controla válvulas reales. Las siguientes etapas contemplan:

- RAG con una base de conocimiento agronómica.
- Integración con sensores de humedad y datos climáticos.
- Persistencia del historial en una base de datos.

## 🛠️ Tecnologías

Python · FastAPI · LangChain · Groq (Llama 3.3 70B) · Pydantic · Uvicorn · Pytest · GitHub Actions

---

Desarrollado por **David Melgoza** ([@D3vo1](https://github.com/D3vo1)).
