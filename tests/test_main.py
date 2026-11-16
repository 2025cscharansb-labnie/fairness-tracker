from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_page_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "Team Fairness Tracker" in response.text


def test_invalid_url_shows_error():
    response = client.get("/", params={"repo_url": "not-a-url"})
    assert "Not a valid GitHub URL" in response.text