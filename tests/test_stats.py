import pytest

EMPLOYEE_BASE = {
    "nombre": "Ana",
    "apellido": "Lopez",
    "email": "ana@example.com",
    "puesto": "Manager",
    "salario": 100000.0,
    "fecha_ingreso": "2021-06-15",
}


class TestSalaryStats:
    async def test_stats_no_employees(self, client, auth_headers):
        resp = await client.get("/employees/stats/salary-average", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_employees"] == 0
        assert data["average_salary"] is None

    async def test_stats_single_employee(self, client, auth_headers):
        await client.post("/employees", json=EMPLOYEE_BASE, headers=auth_headers)
        resp = await client.get("/employees/stats/salary-average", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_employees"] == 1
        assert data["average_salary"] == pytest.approx(100000.0)

    async def test_stats_multiple_employees(self, client, auth_headers):
        salaries = [60000.0, 80000.0, 100000.0]
        for i, salary in enumerate(salaries):
            payload = {**EMPLOYEE_BASE, "email": f"emp{i}@example.com", "salario": salary}
            await client.post("/employees", json=payload, headers=auth_headers)

        resp = await client.get("/employees/stats/salary-average", headers=auth_headers)
        data = resp.json()
        assert data["total_employees"] == 3
        assert data["average_salary"] == pytest.approx(80000.0)

    async def test_stats_requires_auth(self, client):
        resp = await client.get("/employees/stats/salary-average")
        assert resp.status_code == 401

    async def test_stats_route_not_captured_by_id_route(self, client, auth_headers):
        resp = await client.get("/employees/stats/salary-average", headers=auth_headers)
        assert resp.status_code == 200
