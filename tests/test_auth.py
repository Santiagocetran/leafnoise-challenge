import pytest
from datetime import timedelta
from jose import JWTError


class TestPasswordHashing:
    def test_hash_and_verify(self):
        from app.core.security import hash_password, verify_password

        hashed = hash_password("mysecret")
        assert hashed != "mysecret"
        assert verify_password("mysecret", hashed)

    def test_wrong_password_fails(self):
        from app.core.security import hash_password, verify_password

        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)


class TestJWT:
    def test_create_and_decode(self):
        from app.core.security import create_access_token, decode_access_token

        token = create_access_token({"sub": "user@example.com"})
        payload = decode_access_token(token)
        assert payload["sub"] == "user@example.com"

    def test_expired_token_raises(self):
        from app.core.security import create_access_token, decode_access_token

        token = create_access_token({"sub": "u@e.com"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(JWTError):
            decode_access_token(token)

    def test_tampered_token_raises(self):
        from app.core.security import decode_access_token

        with pytest.raises(JWTError):
            decode_access_token("not.a.valid.token")


class TestAuthEndpoints:
    async def test_register_success(self, client):
        resp = await client.post(
            "/auth/register", json={"email": "alice@example.com", "password": "pass123"}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "alice@example.com"
        assert "id" in data

    async def test_register_duplicate_email(self, client):
        payload = {"email": "dup@example.com", "password": "pass"}
        await client.post("/auth/register", json=payload)
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 409

    async def test_login_success(self, client):
        await client.post("/auth/register", json={"email": "bob@example.com", "password": "pass123"})
        resp = await client.post(
            "/auth/login",
            data={"username": "bob@example.com", "password": "pass123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client):
        await client.post("/auth/register", json={"email": "carol@example.com", "password": "correct"})
        resp = await client.post(
            "/auth/login",
            data={"username": "carol@example.com", "password": "wrong"},
        )
        assert resp.status_code == 401

    async def test_login_unknown_user(self, client):
        resp = await client.post(
            "/auth/login",
            data={"username": "nobody@example.com", "password": "x"},
        )
        assert resp.status_code == 401

    async def test_protected_endpoint_requires_token(self, client):
        resp = await client.get("/employees")
        assert resp.status_code == 401

    async def test_protected_endpoint_invalid_token(self, client):
        resp = await client.get("/employees", headers={"Authorization": "Bearer bad.token.here"})
        assert resp.status_code == 401

    async def test_token_without_sub_claim(self, client):
        from app.core.security import create_access_token

        token = create_access_token({"user": "alice"})  # No "sub" key
        resp = await client.get("/employees", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    async def test_token_user_deleted(self, client):
        from app.core.security import create_access_token
        from app.models.user import User

        await client.post("/auth/register", json={"email": "ghost@example.com", "password": "x"})
        token = create_access_token({"sub": "ghost@example.com"})
        user = await User.find_one(User.email == "ghost@example.com")
        if user:
            await user.delete()
        resp = await client.get("/employees", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
