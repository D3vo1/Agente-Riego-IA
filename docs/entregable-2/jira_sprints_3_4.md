# Planeacion Scrum del Entregable 2

## Equipo

- Luis Gabriel Lopez Vega
- Alexis Chavez Mendoza
- Daniel Orlando Ceja Olloqui
- David Melgoza Martinez

## Sprint 3 Conocimiento y RAG

Fechas propuestas: 21 de septiembre de 2026 al 2 de octubre de 2026.

Objetivo: modelar el conocimiento del dominio e integrar una cadena RAG funcional con Chroma.

| Ref | Historia o tarea | Responsable | Puntos | Criterio de aceptacion |
|---|---|---|---:|---|
| AIR-13 | Crear mapa conceptual y red semantica | Luis Gabriel Lopez Vega | 5 | El documento identifica entidades, relaciones y jerarquias del dominio. |
| AIR-14 | Preparar la base documental de riego | Alexis Chavez Mendoza | 3 | Existen documentos sobre riego, suelo, cultivos, sensores y seguridad. |
| AIR-15 | Configurar la base vectorial Chroma | Daniel Orlando Ceja Olloqui | 5 | La coleccion persiste localmente y puede reconstruirse. |
| AIR-16 | Implementar el pipeline de ingesta | David Melgoza Martinez | 5 | Carga, chunking, embeddings y almacenamiento funcionan con un comando. |
| AIR-17 | Integrar el retriever RAG al agente | Luis Gabriel Lopez Vega | 8 | `/chat` recupera contexto y devuelve fuentes. |
| AIR-18 | Crear pruebas del pipeline RAG | Alexis Chavez Mendoza | 3 | Las pruebas validan embeddings, fragmentacion, ingesta y busqueda. |

Total: 29 puntos.

## Sprint 4 Reglas Bayes y gestion

Fechas propuestas: 5 al 9 de octubre de 2026. Sprint comprimido para respetar la fecha oficial del entregable.

Objetivo: agregar razonamiento determinista y probabilistico, persistencia administrativa y evidencias completas.

| Ref | Historia o tarea | Responsable | Puntos | Criterio de aceptacion |
|---|---|---|---:|---|
| AIR-19 | Implementar el sistema basado en reglas | Daniel Orlando Ceja Olloqui | 5 | Extrae hechos, activa reglas y explica recomendaciones. |
| AIR-20 | Implementar el modulo del Teorema de Bayes | David Melgoza Martinez | 5 | Calcula una probabilidad simple y muestra evidencias y limitaciones. |
| AIR-21 | Crear modelos y panel Django | Luis Gabriel Lopez Vega | 5 | Administra conversaciones, mensajes, reglas, documentos y auditoria. |
| AIR-22 | Exponer la API con Django REST Framework | Alexis Chavez Mendoza | 5 | Los endpoints de gestion responden y validan datos. |
| AIR-23 | Integrar FastAPI con Django | Daniel Orlando Ceja Olloqui | 5 | Cada consulta puede registrarse sin bloquear al agente si Django falla. |
| AIR-24 | Ejecutar pruebas y actualizar documentacion | David Melgoza Martinez | 3 | Las pruebas pasan y existen README, arquitectura y evidencias. |

Total: 28 puntos.

## Definition of Done

- Codigo versionado y sin claves privadas.
- Pruebas automatizadas aprobadas.
- Criterios de aceptacion comprobados.
- Documentacion actualizada.
- Evidencia de revision y retrospectiva agregada en Jira.
- Incidencia movida a Done.

## Nota de uso en Jira

El archivo `jira_import_sprints_3_4.csv` contiene las doce incidencias para importacion. Jira genera sus propias claves; la referencia AIR se conserva en el resumen para relacionarla con la documentacion.
