import math
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from app.deps import get_current_user
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeOut,
    EmployeeUpdate,
    PaginatedEmployees,
    SalaryStats,
)

router = APIRouter()


def _to_out(emp: Employee) -> EmployeeOut:
    data = emp.model_dump(mode="json")
    data["id"] = str(emp.id)
    return EmployeeOut(**data)


@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: EmployeeCreate,
    _: User = Depends(get_current_user),
):
    existing = await Employee.find_one(Employee.email == payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    emp = Employee(**payload.model_dump())
    await emp.insert()
    return _to_out(emp)


@router.get("/stats/salary-average", response_model=SalaryStats)
async def salary_stats(_: User = Depends(get_current_user)):
    total = await Employee.count()
    if total == 0:
        return SalaryStats(average_salary=None, total_employees=0)
    pipeline = [{"$group": {"_id": None, "avg": {"$avg": "$salario"}}}]
    result = await Employee.get_motor_collection().aggregate(pipeline).to_list(1)
    avg = float(result[0]["avg"]) if result else None
    return SalaryStats(average_salary=avg, total_employees=total)


@router.get("", response_model=PaginatedEmployees)
async def list_employees(
    puesto: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _: User = Depends(get_current_user),
):
    query = Employee.puesto == puesto if puesto else {}
    total = await Employee.find(query).count()
    skip = (page - 1) * page_size
    employees = await Employee.find(query).skip(skip).limit(page_size).to_list()
    items = [_to_out(e) for e in employees]
    return PaginatedEmployees.build(items, total, page, page_size)


@router.get("/{employee_id}", response_model=EmployeeOut)
async def get_employee(employee_id: str, _: User = Depends(get_current_user)):
    try:
        emp = await Employee.get(employee_id)
    except (ValueError, ValidationError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return _to_out(emp)


@router.patch("/{employee_id}", response_model=EmployeeOut)
async def update_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    _: User = Depends(get_current_user),
):
    try:
        emp = await Employee.get(employee_id)
    except (ValueError, ValidationError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        return _to_out(emp)
    if "email" in update_data:
        conflict = await Employee.find_one(Employee.email == update_data["email"])
        if conflict and str(conflict.id) != employee_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    update_data["updated_at"] = datetime.now(timezone.utc)
    await emp.set(update_data)
    return _to_out(emp)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: str, _: User = Depends(get_current_user)):
    try:
        emp = await Employee.get(employee_id)
    except (ValueError, ValidationError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    await emp.delete()
