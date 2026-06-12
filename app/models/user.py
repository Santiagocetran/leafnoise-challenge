from datetime import datetime, timezone
from beanie import Document
from pydantic import EmailStr, Field
import pymongo


class User(Document):
    email: EmailStr
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = [
            pymongo.IndexModel([("email", pymongo.ASCENDING)], unique=True),
        ]
