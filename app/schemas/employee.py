import math
from datetime import date
from typing import List
from pydantic import BaseModel, EmailStr, Field


class EmployeeCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    apellido: str = Field(..., min_length=1)
    email: EmailStr
    puesto: str = Field(..., min_length=1)
    salario: float = Field(..., ge=0.0)
    fecha_ingreso: date


class EmployeeUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1)
    apellido: str | None = Field(default=None, min_length=1)
    email: EmailStr | None = None
    puesto: str | None = Field(default=None, min_length=1)
    salario: float | None = Field(default=None, ge=0.0)
    fecha_ingreso: date | None = None


class EmployeeOut(BaseModel):
    id: str
    nombre: str
    apellido: str
    email: str
    puesto: str
    salario: float
    fecha_ingreso: date

    model_config = {"from_attributes": True}


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
    average_salary: float | None
    total_employees: int
