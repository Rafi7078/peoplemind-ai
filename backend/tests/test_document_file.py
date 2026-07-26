from fastapi.testclient import TestClient
from backend.app.main import app
client = TestClient(app)
def test_document_file_requires_authentication() -> None:
    response = client.get(
        "/api/documents/1/file"
    )
    assert response.status_code == 401
