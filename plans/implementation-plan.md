# Plan de Implementación — PeopleFlow API

> Challenge Técnico Backend Developer Ssr. — Leafnoise
> Autor: Santiago Cetran

---

## 1. Contexto del challenge

PeopleFlow (startup) gestiona empleados en Excel y entró en caos. RRHH necesita una
**API interna** para registrar, consultar, actualizar y eliminar empleados. Además, el
CFO (Nacho) pide **cada lunes el promedio de salarios de toda la empresa**. Aunque el
promedio no aparece en la lista numerada de endpoints mínimos, sí forma parte de la
narrativa del problema, por lo que se implementa como endpoint adicional.

### Requerimientos mínimos (modelo Employee)
`id` · `nombre` · `apellido` · `email` · `puesto` · `salario` · `fecha_ingreso`

### Endpoints mínimos
1. Crear empleado
2. Listar empleados (filtro por puesto + paginación)
3. Obtener empleado por id
4. Actualizar empleado
5. Eliminar empleado

### Bonus (se implementan TODOS)
- Documentación Swagger/OpenAPI/Postman
- Docker
- Autenticación JWT
- Tests automatizados (pytest)

---

## 2. Decisiones técnicas

| Tema | Decisión | Justificación |
|------|----------|---------------|
| Python | **3.11** | Cumple Python 3.8+ del enunciado y evita fricción con dependencias modernas. |
| Framework | **FastAPI** | Async, validación con Pydantic, OpenAPI nativo. |
| Persistencia | **MongoDB + Beanie** | Mongo es la preferencia del enunciado. Beanie es un ODM async sobre Motor que integra con Pydantic v2 → modelos limpios. |
| Validación | **Pydantic v2** | Schemas de entrada/salida, validación de email y salario. |
| Auth | **JWT** (python-jose) + **bcrypt** (passlib) | Usuarios con register/login; protege todos los endpoints de empleados porque exponen datos internos y salarios. |
| Tests | **pytest + httpx + testcontainers** | **TDD** (test-first). MongoDB **real** efímero vía `testcontainers` (sin mocks) → fidelidad total en aggregations y `Decimal128`. Cobertura medida con `pytest-cov`, gate ≥ 85%. |
| Entorno | **Docker + docker-compose** | `docker compose up` levanta API + Mongo. |
| Config | **pydantic-settings** + `.env` | Sin secretos hardcodeados. |

---

## 3. Estructura del proyecto

```
peopleflow-api/
├── app/
│   ├── main.py                 # App FastAPI, lifespan, routers, metadata OpenAPI
│   ├── core/
│   │   ├── config.py           # Settings (pydantic-settings, env vars)
│   │   ├── security.py         # Hash de password, crear/validar JWT
│   │   └── database.py         # Init Beanie + cliente Motor
│   ├── models/
│   │   ├── employee.py         # Documento Beanie (colección employees)
│   │   └── user.py             # Documento Beanie (colección users)
│   ├── schemas/
│   │   ├── employee.py         # EmployeeCreate / Update / Out + paginación
│   │   ├── user.py             # UserCreate, UserOut
│   │   └── auth.py             # Token
│   ├── routers/
│   │   ├── employees.py        # CRUD + filtro + paginación + stats
│   │   └── auth.py             # register / login
│   └── deps.py                 # get_current_user (dependency JWT)
├── tests/
│   ├── conftest.py             # Fixtures (contenedor Mongo, cliente HTTP, token)
│   ├── test_employees.py
│   ├── test_auth.py
│   └── test_stats.py
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile                  # Multi-stage
├── docker-compose.yml          # api + mongo
├── requirements.txt            # Dependencias de runtime
├── requirements-dev.txt        # pytest, pytest-cov, testcontainers, etc.
├── LICENSE                     # Licencia de evaluación
├── postman_collection.json
└── README.md
```

---

## 4. Modelo de datos — Employee

| Campo | Tipo | Reglas |
|-------|------|--------|
| `id` | str (ObjectId) | Generado por Mongo. |
| `nombre` | str | Requerido, no vacío. |
| `apellido` | str | Requerido, no vacío. |
| `email` | EmailStr | Requerido, **único** (índice unique). |
| `puesto` | str | Requerido. |
| `salario` | Decimal | Requerido, ≥ 0. Se modela como decimal por tratarse de dinero; en Mongo se almacena como Decimal128 o formato compatible. |
| `fecha_ingreso` | date | Requerido. |
| `created_at` / `updated_at` | datetime | `created_at` con `default_factory`; `updated_at` se actualiza explícitamente en cada modificación. |

**Usuario (auth):** `id`, `email` (único), `hashed_password`, `created_at`.

---

## 5. Endpoints

### Auth
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/auth/register` | Crea usuario (password hasheado con bcrypt). *Nota: en un sistema real este endpoint sería solo-admin; abierto aquí para facilitar la evaluación.* |
| POST | `/auth/login` | OAuth2 password flow con `OAuth2PasswordRequestForm` (`application/x-www-form-urlencoded`) → devuelve JWT e integra con "Authorize" de Swagger. |

### Empleados (todos protegidos con JWT)
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/employees` | Crear. Valida email único → `409` si duplicado. |
| GET | `/employees` | Listar con `?puesto=&page=&page_size=`. Respuesta paginada: `items`, `total`, `page`, `pages`. |
| GET | `/employees/stats/salary-average` | **Pedido del CFO**: promedio de salarios de toda la empresa (vía aggregation pipeline de Mongo, no en memoria). Se declara antes de `/{id}` para evitar conflictos de routing. |
| GET | `/employees/{id}` | Obtener por id. `404` si no existe. |
| PATCH | `/employees/{id}` | Actualización parcial. |
| DELETE | `/employees/{id}` | Eliminar. `204` sin contenido. |

---

## 6. Cumplimiento de bonus

- **Swagger/OpenAPI**: nativo de FastAPI en `/docs` y `/redoc`, con metadata, tags,
  descripciones y ejemplos. Más colección Postman exportada.
- **Docker**: `Dockerfile` multi-stage + `docker-compose.yml` (API + MongoDB).
- **JWT**: register/login, bcrypt, dependency de protección para todos los endpoints de
  empleados, botón Authorize en Swagger.
- **Tests (pytest)**: desarrollados con **TDD**. Cubren CRUD, validaciones (email
  duplicado, 404, salario negativo), auth (token inválido/ausente), paginación y cálculo
  del promedio. Corren contra **MongoDB real** (testcontainers), cobertura ≥ 85%.

---

## 6.1 Estrategia de testing (TDD)

**Metodología:** ciclo TDD red → green → refactor. Para cada feature se escribe primero
el test (falla), luego el mínimo código que lo hace pasar, después se refactoriza.

**Tipos de test (mezcla pragmática):**
- **Unit (puros, sin I/O):** lógica aislable y rápida → `core/security.py` (hash y
  verificación de password, encode/decode de JWT, expiración/firma inválida),
  helpers de paginación. Acá el ciclo TDD es ágil (sin contenedor).
- **Integración / API:** endpoints completos vía `httpx.AsyncClient` contra la app y
  **MongoDB real** levantado con `testcontainers` → CRUD, filtros, paginación, auth y el
  promedio del CFO (aggregation `$avg` real sobre `Decimal128`).

**Infraestructura de tests:**
- Contenedor de Mongo **scope sesión** (arranca una vez); limpieza de colecciones
  **por test** (función) para aislamiento → rápido y determinista.
- `pytest-asyncio` para los tests async.
- `pytest-cov` con `--cov-fail-under=85` (el build falla si baja del umbral).
- Fixtures en `conftest.py`: contenedor Mongo, init de Beanie, cliente HTTP, usuario +
  token de prueba.
- **Requisito:** correr los tests necesita un **daemon de Docker** activo (testcontainers
  levanta el Mongo). Se documenta en el README.

---

## 7. Calidad y detalles que suman

- Manejo de errores consistente (exception handlers → JSON limpio).
- Type hints completos; código limpio y comentado al nivel justo.
- Variables de entorno (`.env.example`, sin secretos en el repo).
- README claro: levantar con Docker y en local, ejemplos `curl`, decisiones técnicas y
  nota de licencia.

---

## 8. Protección de propiedad intelectual

El código se entrega **solo para evaluación técnica**:

- Archivo `LICENSE` propietario: uso exclusivo para evaluación técnica de Leafnoise;
  cualquier otro uso (incl. producción) requiere autorización escrita del autor.
- Nota breve en el README, sin sobredimensionar este punto para no distraer de la
  evaluación técnica.
- **Sin kill switch** (removible y poco profesional; la protección legal vía copyright
  es la vía correcta y defendible).

---

## 9. Git

- Repo objetivo: `git@github.com:Santiagocetran/leafnoise-challenge.git`
- Identidad a usar: `Santiago Cetran <santiagorcetran236@gmail.com>` (único autor).
- Los commits no llevarán firma ni co-autoría de herramientas de IA.
- Commits incrementales con mensajes claros.

---

## 10. Orden de trabajo

> Cada feature funcional (pasos 3 a 5) se desarrolla en **TDD**: test primero, luego
> implementación, luego refactor.

1. Scaffold + config + Docker + Mongo levantando + infra de tests (conftest, contenedor).
2. Modelos + schemas + conexión DB.
3. Auth JWT + dependency de usuario actual *(TDD)*.
4. CRUD empleados protegido + filtro + paginación *(TDD)*.
5. Endpoint stats (CFO), declarado antes de `/{id}` *(TDD)*.
6. Cierre de cobertura (≥ 85%) y casos borde.
7. Docs (README, metadata OpenAPI, Postman) + LICENSE.
8. Revisión de commits limpios y push.
