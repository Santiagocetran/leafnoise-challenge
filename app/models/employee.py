from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated
from beanie import Document
from bson import Decimal128
from pydantic import BeforeValidator, EmailStr, Field
import pymongo


def _decimal128_to_decimal(value: object) -> object:
    # Beanie persiste Decimal como Decimal128 en Mongo; al leer hay que reconvertir.
    if isinstance(value, Decimal128):
        return value.to_decimal()
    return value


SalaryDecimal = Annotated[Decimal, BeforeValidator(_decimal128_to_decimal)]


class Employee(Document):
    nombre: str = Field(..., min_length=1)
    apellido: str = Field(..., min_length=1)
    email: EmailStr
    puesto: str = Field(..., min_length=1)
    salario: SalaryDecimal = Field(..., ge=0)
    fecha_ingreso: date
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "employees"
        indexes = [
            pymongo.IndexModel([("email", pymongo.ASCENDING)], unique=True),
        ]
