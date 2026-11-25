# Evidencias Scrum del Entregable 2

## Sprint Planning 3

Objetivo acordado: construir el modelo de conocimiento y una cadena RAG demostrable. Se seleccionaron seis tareas con 29 puntos. El equipo priorizo primero el corpus y el pipeline para desbloquear la integracion del agente.

## Daily Sprint 3

- Dia 1: se definieron entidades y relaciones del dominio.
- Dia 3: se completo el corpus inicial y la coleccion Chroma.
- Dia 5: se verifico la ingesta y el recuperador.
- Dia 8: se integro el contexto RAG en `/chat`.
- Dia 10: se aprobaron pruebas y documentacion.

## Sprint Review 3

Se demostro una consulta sobre humedad y suelo. El agente recupero documentos relacionados y devolvio las fuentes en la respuesta JSON. Las seis tareas cumplieron sus criterios.

## Retrospectiva 3

Funciono bien mantener la base documental en archivos legibles. Como mejora, se acordo separar la logica de recuperacion del cliente LLM y agregar pruebas que no consumieran la API.

## Sprint Planning 4

Objetivo acordado: integrar reglas, Bayes y el microservicio de gestion. Se seleccionaron seis tareas con 28 puntos y se distribuyeron de manera equilibrada.

## Daily Sprint 4

- Dia 1: se definieron hechos, codigos de reglas y evidencias bayesianas.
- Dia 2: se implementaron modelos, migraciones y panel Django.
- Dia 3: se expusieron endpoints DRF y contrato `/api/exchanges/`.
- Dia 4: se integro el registro desde FastAPI y se probaron fallos controlados.
- Dia 5: se ejecutaron pruebas finales y se preparo la entrega.

## Sprint Review 4

Se demostro una consulta con humedad baja, temperatura alta y ausencia de lluvia. La salida mostro documentos recuperados, reglas activadas, probabilidad demostrativa y registro persistente en Django.

## Retrospectiva 4

La separacion de microservicios facilito probar cada componente. El sprint fue corto para respetar la fecha de entrega; como mejora futura se recomienda configurar autenticacion, usar un modelo de embeddings semantico y calibrar reglas con datos reales.

## Evidencia que debe adjuntarse en Jira

1. Captura del backlog con Sprint 3 y Sprint 4.
2. Captura de todas las incidencias en Done.
3. Captura de `/docs` de FastAPI.
4. Captura de `/api/` y `/admin/` de Django.
5. Salida de las pruebas automatizadas.
6. Ejemplo de respuesta con fuentes, reglas y probabilidad.
7. Enlace al repositorio o ZIP final.
