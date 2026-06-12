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

> **La forma más simple de probar todo** es la documentación interactiva en
> **`http://localhost:8000/docs`** (Swagger UI): registrás un usuario, hacés login,
> hacés click en **Authorize** (pegás el token) y ejecutás cualquier endpoint desde el
> navegador, sin armar comandos a mano.
>
> Nota: la raíz `/` no tiene endpoint (responde `404` a propósito); el punto de entrada
> es `/docs`.

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

## Guía de prueba completa (curl)

Esta secuencia ejercita **todas** las funcionalidades de la API de principio a fin.
Pegala paso a paso en una terminal con la API ya levantada. Usa
[`jq`](https://stedolan.github.io/jq/) para extraer datos de las respuestas (en Debian/
Ubuntu: `sudo apt install jq`); más abajo hay una alternativa sin `jq`.

```bash
BASE=http://localhost:8000

# 1) Registrar un usuario
curl -s -X POST $BASE/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@peopleflow.com","password":"secret123"}'

# 2) Login → guardar el JWT en una variable (el campo es "username", va el email)
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -d 'username=admin@peopleflow.com&password=secret123' | jq -r .access_token)
echo "TOKEN=$TOKEN"        # debe imprimir un string largo, no 'null'

# A partir de acá, todos los endpoints de empleados requieren el header Authorization.

# 3) Crear empleados (guardamos el id del primero para los pasos siguientes)
EMP_ID=$(curl -s -X POST $BASE/employees \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"nombre":"Ana","apellido":"García","email":"ana@example.com","puesto":"Engineer","salario":85000,"fecha_ingreso":"2022-01-15"}' \
  | jq -r .id)
echo "EMP_ID=$EMP_ID"

curl -s -X POST $BASE/employees \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"nombre":"Beto","apellido":"Pérez","email":"beto@example.com","puesto":"Engineer","salario":95000,"fecha_ingreso":"2023-03-10"}'

curl -s -X POST $BASE/employees \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"nombre":"Carla","apellido":"Díaz","email":"carla@example.com","puesto":"Manager","salario":120000,"fecha_ingreso":"2021-09-01"}'

# 4) Listar con filtro por puesto y paginación → { items, total, page, pages }
curl -s "$BASE/employees?puesto=Engineer&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"

# 5) Obtener un empleado por id
curl -s $BASE/employees/$EMP_ID -H "Authorization: Bearer $TOKEN"

# 6) Actualizar (parcial) — subimos el salario de Ana
curl -s -X PATCH $BASE/employees/$EMP_ID \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"salario":90000}'

# 7) Promedio de salarios de toda la empresa (el reporte del CFO)
curl -s $BASE/employees/stats/salary-average -H "Authorization: Bearer $TOKEN"

# 8) Eliminar un empleado (responde 204 sin cuerpo)
curl -s -o /dev/null -w "%{http_code}\n" -X DELETE $BASE/employees/$EMP_ID \
  -H "Authorization: Bearer $TOKEN"

# 9) Verificar que ya no existe (responde 404)
curl -s -o /dev/null -w "%{http_code}\n" $BASE/employees/$EMP_ID \
  -H "Authorization: Bearer $TOKEN"
```

**Sin `jq`** (paso 2 alternativo, usando Python):

```bash
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -d 'username=admin@peopleflow.com&password=secret123' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

> `Authorization` siempre lleva la palabra **`Bearer`** + espacio + el JWT. Sin un token
> válido, los endpoints de empleados responden `401`.

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
- **Salario**: modelado como `Decimal` y persistido como `Decimal128` en MongoDB para evitar errores de punto flotante en montos de dinero. El promedio del CFO se calcula con aritmética decimal exacta (`$avg` sobre `Decimal128`); en la API se expone como número JSON vía un `field_serializer`. Hay un test (`test_stats_preserves_decimal_precision`) que verifica que el promedio no sufre deriva de float.

---

## Colección Postman

Importar `postman_collection.json`. Ejecutar "Login" primero para que la variable `{{token}}` se auto-complete en los demás requests.

---

## Licencia

Este código se entrega exclusivamente para evaluación técnica por parte de Leafnoise.  
Cualquier otro uso requiere autorización escrita del autor.
