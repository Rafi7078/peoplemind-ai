from fastapi.testclient import TestClient
from backend.app.core.security import hash_password, verify_password
from backend.app.main import app
client = TestClient(app)
def test_password_hashing() -> None:
    plain_password = "SecureAdmin123"
    hashed_password = hash_password(plain_password)
    assert hashed_password != plain_password
    assert verify_password(plain_password, hashed_password)
    assert not verify_password("IncorrectPassword123", hashed_password)
def test_me_endpoint_requires_authentication() -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401
