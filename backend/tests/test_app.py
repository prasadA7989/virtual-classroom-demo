import os

os.environ["DB_HOST"] = ""
os.environ["DB_USER"] = ""
os.environ["DB_PASSWORD"] = ""

from app import app


def test_health():

    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"
