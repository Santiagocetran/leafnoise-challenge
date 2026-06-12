import math
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List
from pydantic import BaseModel, EmailStr, Field, field_serializer


class EmployeeCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    apellido: str = Field(..., min_length=1)
    email: EmailStr
    puesto: str = Field(..., min_length=1)
    salario: Decimal = Field(..., ge=0)
    fecha_ingreso: date


class EmployeeUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1)
    apellido: str | None = Field(default=None, min_length=1)
    email: EmailStr | None = None
    puesto: str | None = Field(default=None, min_length=1)
    salario: Decimal | None = Field(default=None, ge=0)
    fecha_ingreso: date | None = None


class EmployeeOut(BaseModel):
    id: str
    nombre: str
    apellido: str
    email: str
    puesto: str
    salario: Decimal
    fecha_ingreso: date

    model_config = {"from_attributes": True}

    @field_serializer("salario")
    def _serialize_salario(self, value: Decimal) -> float:
        # Almacenamos con precisión decimal (Decimal128); exponemos número en la API.
        return float(value)


class PaginatedEmployees(BaseModel):
    items: List[EmployeeOut]
    total: int
    page: int
    pages: int

    @classmethod
    def build(cls, items: List[EmployeeOut], total: int, page: int, page_size: int) -> "PaginatedEmployees":
        pages = math.ceil(total / page_size) if total > 0 else 0
        return cls(items=items, total=total, page=page, pages=pages)


class SalaryStats(BaseModel):
    average_salary: Decimal | None
    total_employees: int

    @field_serializer("average_salary")
    def _serialize_average(self, value: Decimal | None) -> float | None:
        if value is None:
            return None
        # Reporte de dinero: redondeo a 2 decimales (centavos) con ROUND_HALF_UP.
        return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
