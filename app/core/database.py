from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings


async def init_db(uri: str | None = None) -> AsyncIOMotorClient:
    url = uri or settings.MONGODB_URL
    client = AsyncIOMotorClient(url)
    from app.models.employee import Employee
    from app.models.user import User
    db = client.get_database(settings.MONGODB_DB_NAME)
    await init_beanie(database=db, document_models=[Employee, User])
    return client
