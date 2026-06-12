import pytest

EMPLOYEE_PAYLOAD = {
    "nombre": "Juan",
    "apellido": "García",
    "email": "juan@example.com",
    "puesto": "Engineer",
    "salario": 75000.0,
    "fecha_ingreso": "2022-03-01",
}


class TestCreateEmployee:
    async def test_create_success(self, client, auth_headers):
        resp = await client.post("/employees", json=EMPLOYEE_PAYLOAD, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre"] == "Juan"
        assert data["email"] == "juan@example.com"
        assert data["salario"] == 75000.0
        assert "id" in data

    async def test_create_duplicate_email(self, client, auth_headers):
        await client.post("/employees", json=EMPLOYEE_PAYLOAD, headers=auth_headers)
        resp = await client.post("/employees", json=EMPLOYEE_PAYLOAD, headers=auth_headers)
        assert resp.status_code == 409

    async def test_create_negative_salary_fails(self, client, auth_headers):
        payload = {**EMPLOYEE_PAYLOAD, "salario": -100.0}
        resp = await client.post("/employees", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    async def test_create_invalid_email_fails(self, client, auth_headers):
        payload = {**EMPLOYEE_PAYLOAD, "email": "not-an-email"}
        resp = await client.post("/employees", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    async def test_create_requires_auth(self, client):
        resp = await client.post("/employees", json=EMPLOYEE_PAYLOAD)
        assert resp.status_code == 401


class TestListEmployees:
    async def test_list_empty(self, client, auth_headers):
        resp = await client.get("/employees", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["pages"] == 0

    async def test_list_returns_created(self, client, auth_headers):
        await client.post("/employees", json=EMPLOYEE_PAYLOAD, headers=auth_headers)
        resp = await client.get("/employees", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    async def test_filter_by_puesto(self, client, auth_headers):
        await client.post("/employees", json=EMPLOYEE_PAYLOAD, headers=auth_headers)
        other = {**EMPLOYEE_PAYLOAD, "email": "other@example.com", "puesto": "Designer"}
        await client.post("/employees", json=other, headers=auth_headers)

        resp = await client.get("/employees?puesto=Engineer", headers=auth_headers)
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["puesto"] == "Engineer"

    async def test_pagination(self, client, auth_headers):
        for i in range(5):
            payload = {**EMPLOYEE_PAYLOAD, "email": f"emp{i}@example.com"}
            await client.post("/employees", json=payload, headers=auth_headers)

        resp = await client.get("/employees?page=1&page_size=2", headers=auth_headers)
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["pages"] == 3

    async def test_pagination_page_2(self, client, auth_headers):
        for i in range(5):
            payload = {**EMPLOYEE_PAYLOAD, "email": f"pg{i}@example.com"}
            await client.post("/employees", json=payload, headers=auth_headers)

        resp = await client.get("/employees?page=2&page_size=3", headers=auth_headers)
        data = resp.json()
        assert len(data["items"]) == 2


class TestGetEmployee:
    async def test_get_existing(self, client, auth_headers):
        create = await client.post("/employees", json=EMPLOYEE_PAYLOAD, headers=auth_headers)
        emp_id = create.json()["id"]

        resp = await client.get(f"/employees/{emp_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == emp_id

    async def test_get_not_found(self, client, auth_headers):
        resp = await client.get("/employees/000000000000000000000000", headers=auth_headers)
        assert resp.status_code == 404

    async def test_get_invalid_id(self, client, auth_headers):
        resp = await client.get("/employees/not-a-valid-id", headers=auth_headers)
        assert resp.status_code in (404, 422)


class TestUpdateEmployee:
    async def test_patch_name(self, client, auth_headers):
        create = await client.post("/employees", json=EMPLOYEE_PAYLOAD, headers=auth_headers)
        emp_id = create.json()["id"]

        resp = await client.patch(
            f"/employees/{emp_id}", json={"nombre": "Pedro"}, headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Pedro"

    async def test_patch_salary(self, client, auth_headers):
        create = await client.post("/employees", json=EMPLOYEE_PAYLOAD, headers=auth_headers)
        emp_id = create.json()["id"]

        resp = await client.patch(
            f"/employees/{emp_id}", json={"salario": 90000.0}, headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["salario"] == 90000.0

    async def test_patch_email_conflict(self, client, auth_headers):
        await client.post("/employees", json=EMPLOYEE_PAYLOAD, headers=auth_headers)
        other = {**EMPLOYEE_PAYLOAD, "email": "other@example.com"}
        create2 = await client.post("/employees", json=other, headers=auth_headers)
        emp2_id = create2.json()["id"]

        resp = await client.patch(
            f"/employees/{emp2_id}",
            json={"email": "juan@example.com"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_patch_not_found(self, client, auth_headers):
        resp = await client.patch(
            "/employees/000000000000000000000000", json={"nombre": "X"}, headers=auth_headers
        )
        assert resp.status_code == 404

    async def test_patch_invalid_id(self, client, auth_headers):
        resp = await client.patch(
            "/employees/not-a-valid-id", json={"nombre": "X"}, headers=auth_headers
        )
        assert resp.status_code in (404, 422)

    async def test_patch_empty_body_returns_unchanged(self, client, auth_headers):
        create = await client.post("/employees", json=EMPLOYEE_PAYLOAD, headers=auth_headers)
        emp_id = create.json()["id"]
        resp = await client.patch(f"/employees/{emp_id}", json={}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Juan"

    async def test_patch_negative_salary_fails(self, client, auth_headers):
        create = await client.post("/employees", json=EMPLOYEE_PAYLOAD, headers=auth_headers)
        emp_id = create.json()["id"]
        resp = await client.patch(
            f"/employees/{emp_id}", json={"salario": -1.0}, headers=auth_headers
        )
        assert resp.status_code == 422


class TestDeleteEmployee:
    async def test_delete_success(self, client, auth_headers):
        create = await client.post("/employees", json=EMPLOYEE_PAYLOAD, headers=auth_headers)
        emp_id = create.json()["id"]

        resp = await client.delete(f"/employees/{emp_id}", headers=auth_headers)
        assert resp.status_code == 204

        get_resp = await client.get(f"/employees/{emp_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    async def test_delete_not_found(self, client, auth_headers):
        resp = await client.delete("/employees/000000000000000000000000", headers=auth_headers)
        assert resp.status_code == 404

    async def test_delete_invalid_id(self, client, auth_headers):
        resp = await client.delete("/employees/not-a-valid-id", headers=auth_headers)
        assert resp.status_code in (404, 422)


class TestHealth:
    async def test_health_endpoint(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
