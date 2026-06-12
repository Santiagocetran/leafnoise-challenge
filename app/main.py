from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.database import init_db
from app.routers import auth, employees


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = await init_db()
    app.state.db_client = client
    yield
    client.close()


app = FastAPI(
    title="PeopleFlow API",
    description=(
        "API interna de gestión de empleados para PeopleFlow.\n\n"
        "Autenticación: usar el botón **Authorize** con las credenciales obtenidas en `/auth/login`."
    ),
    version="1.0.0",
    lifespan=lifespan,
    contact={"name": "Santiago Cetran"},
    license_info={"name": "Proprietary — evaluation only"},
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(employees.router, prefix="/employees", tags=["Employees"])


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["Health"], summary="Health check")
async def health():
    return {"status": "ok"}
