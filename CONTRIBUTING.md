# Guía para contribuir

Gracias por colaborar con AgroRiego. Esta guía explica cómo trabajamos en equipo.

## Ramas

| Rama | Para qué sirve | Quién escribe en ella |
|---|---|---|
| `main` | Versiones estables, listas para entregar | Solo recibe merges desde `development` |
| `development` | Integración del trabajo del equipo | Solo recibe Pull Requests desde ramas de trabajo |
| `feature/<descripcion>` | Nueva funcionalidad | Tú |
| `fix/<descripcion>` | Corrección de errores | Tú |
| `docs/<descripcion>` | Documentación | Tú |
| `chore/<descripcion>` | Mantenimiento (CI, dependencias, estructura) | Tú |

Usa nombres cortos, en minúsculas y con guiones. Por ejemplo `feature/memoria-persistente` o `fix/error-503`.

Nadie hace push directo a `main` ni a `development`: GitHub lo bloquea.

## Flujo de trabajo

1. Actualiza tu copia de `development`:
   ```bash
   git checkout development
   git pull
   ```
2. Crea tu rama de trabajo:
   ```bash
   git checkout -b feature/mi-cambio
   ```
3. Haz commits pequeños y con mensajes claros (ver abajo).
4. Corre las pruebas antes de subir:
   ```bash
   pytest -q
   ```
5. Sube tu rama y abre un Pull Request **hacia `development`**:
   ```bash
   git push -u origin feature/mi-cambio
   ```
6. Llena la plantilla del Pull Request, espera a que pasen las pruebas y a que alguien lo apruebe.
7. Cuando esté aprobado, se integra con **Squash and merge** y se borra la rama.

Para publicar una versión, se abre un Pull Request de `development` hacia `main`.

## Mensajes de commit

Usamos [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/):

```text
<tipo>: <descripción corta en presente>
```

| Tipo | Cuándo usarlo |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de un error |
| `docs` | Solo documentación |
| `test` | Agregar o corregir pruebas |
| `refactor` | Cambio de código que no altera el comportamiento |
| `chore` | Mantenimiento: CI, dependencias, estructura |

Ejemplos: `feat: guardar historial en SQLite`, `fix: responder 503 cuando falta la clave`.

## Pruebas

- Toda funcionalidad nueva debe venir con su prueba en `tests/`.
- Las pruebas no deben llamar al modelo real; usa el modelo simulado como en `tests/test_api.py`.
- GitHub Actions corre `pytest` en cada Pull Request; si falla, no se puede integrar.

## Issues

Antes de empezar algo, revisa que exista un issue (o créalo con las plantillas de **Reporte de error** o **Tarea**) y asígnatelo para que el equipo sepa quién trabaja en qué.

## Secretos

Nunca subas tu archivo `.env` ni claves de API. Usa `.env.example` como referencia.
