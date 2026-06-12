from datetime import date, datetime, timezone
from beanie import Document
from pydantic import EmailStr, Field
import pymongo


class Employee(Document):
    nombre: str = Field(..., min_length=1)
    apellido: str = Field(..., min_length=1)
    email: EmailStr
    puesto: str = Field(..., min_length=1)
    salario: float = Field(..., ge=0.0)
    fecha_ingreso: date
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "employees"
        indexes = [
            pymongo.IndexModel([("email", pymongo.ASCENDING)], unique=True),
        ]
