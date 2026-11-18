from fastapi.testclient import TestClient

from app.main import app, group_commits

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


def test_group_commits_groups_by_author():
    commits = [
        {"sha": "abcdef123", "author": "alice", "message": "Add login page", "date": "2026-11-01T10:00:00Z"},
        {"sha": "123456abc", "author": "alice", "message": "fix", "date": "2026-11-02T10:00:00Z"},
    ]
    grouped = group_commits(commits)
    assert len(grouped["alice"]) == 2
    assert grouped["alice"][0]["counted"] is True
    assert grouped["alice"][1]["counted"] is False