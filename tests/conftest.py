import pytest
from testcontainers.mongodb import MongoDbContainer
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from httpx import AsyncClient, ASGITransport

MONGO_IMAGE = "mongo:7"


@pytest.fixture(scope="session")
def mongo_url():
    """Start MongoDB container once for the whole session."""
    with MongoDbContainer(MONGO_IMAGE) as mc:
        yield mc.get_connection_url()


@pytest.fixture(autouse=True)
async def db(mongo_url):
    """Per-test: fresh Motor client + Beanie init + clean collections."""
    from app.models.employee import Employee
    from app.models.user import User

    client = AsyncIOMotorClient(mongo_url)
    database = client["peopleflow_test"]
    await init_beanie(database=database, document_models=[Employee, User])
    await Employee.delete_all()
    await User.delete_all()
    yield database
    client.close()


@pytest.fixture
async def client(db):
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client):
    await client.post("/auth/register", json={"email": "test@example.com", "password": "secret123"})
    resp = await client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "secret123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
