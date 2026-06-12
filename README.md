# PeopleFlow API

API interna de gestión de empleados para PeopleFlow.

---

## Levantar con Docker (recomendado)

Requiere Docker y Docker Compose instalados.

```bash
cp .env.example .env
# Editar .env y cambiar SECRET_KEY por un valor aleatorio seguro
docker compose up --build
```

La API queda disponible en `http://localhost:8000`.  
Documentación interactiva: `http://localhost:8000/docs`

---

## Levantar en local (sin Docker)

Requiere Python 3.11+ y un MongoDB corriendo.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Ajustar MONGODB_URL y SECRET_KEY en .env

uvicorn app.main:app --reload
```

---

## Correr los tests

Requiere Docker activo (testcontainers levanta un MongoDB efímero).

```bash
pip install -r requirements-dev.txt
pytest
```

Los tests usan un contenedor MongoDB descartable, no afectan ninguna base de datos real.  
El gate de cobertura es ≥ 85%; la suite actual supera el 95%.

---

## Endpoints

### Auth
| Método | Ruta             | Descripción                     |
|--------|------------------|---------------------------------|
| POST   | `/auth/register` | Registrar usuario               |
| POST   | `/auth/login`    | Login (form data) → JWT         |

### Empleados (requieren JWT)
| Método | Ruta                              | Descripción                        |
|--------|-----------------------------------|------------------------------------|
| POST   | `/employees`                      | Crear empleado                     |
| GET    | `/employees`                      | Listar con filtro y paginación     |
| GET    | `/employees/stats/salary-average` | Promedio de salarios (CFO)         |
| GET    | `/employees/{id}`                 | Obtener por ID                     |
| PATCH  | `/employees/{id}`                 | Actualización parcial              |
| DELETE | `/employees/{id}`                 | Eliminar (204)                     |

---

## Ejemplos rápidos (curl)

```bash
# Registrar usuario
curl -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"mypassword"}'

# Obtener token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d 'username=user@example.com&password=mypassword' | jq -r .access_token)

# Crear empleado
curl -X POST http://localhost:8000/employees \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"nombre":"Ana","apellido":"García","email":"ana@example.com","puesto":"Engineer","salario":85000,"fecha_ingreso":"2022-01-15"}'

# Listar con filtro y paginación
curl "http://localhost:8000/employees?puesto=Engineer&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"

# Promedio de salarios
curl http://localhost:8000/employees/stats/salary-average \
  -H "Authorization: Bearer $TOKEN"
```

---

## Parámetros de listado

| Parámetro   | Tipo   | Default | Descripción                      |
|-------------|--------|---------|----------------------------------|
| `puesto`    | string | —       | Filtrar por puesto               |
| `page`      | int    | 1       | Número de página (≥ 1)           |
| `page_size` | int    | 10      | Resultados por página (1–100)    |

Respuesta paginada: `{ items, total, page, pages }`.

---

## Decisiones técnicas destacadas

- **Beanie + Motor**: ODM async sobre MongoDB; modelos con Pydantic v2 → validación y serialización integradas.
- **JWT**: `python-jose` para encode/decode; bcrypt directo para hashing de passwords (passlib no es compatible con bcrypt ≥ 4).
- **Stats**: el endpoint `/stats/salary-average` usa un aggregation pipeline de MongoDB (`$avg`) en lugar de calcular en memoria, y se declara antes de `/{id}` para evitar conflictos de routing.
- **Tests**: TDD con `testcontainers` (MongoDB real efímero); Motor re-inicializado por test para compatibilidad con el event loop de pytest-asyncio; cobertura ≥ 85%.
- **Salario**: almacenado como `float` (Double en MongoDB). En un sistema productivo se usaría `Decimal128` para evitar errores de punto flotante.

---

## Colección Postman

Importar `postman_collection.json`. Ejecutar "Login" primero para que la variable `{{token}}` se auto-complete en los demás requests.

---

## Licencia

Este código se entrega exclusivamente para evaluación técnica por parte de Leafnoise.  
Cualquier otro uso requiere autorización escrita del autor.
