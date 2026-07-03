import os

os.environ.setdefault("JIRA_BASE_URL", "https://example.atlassian.net")
os.environ.setdefault("JIRA_EMAIL", "test@example.com")
os.environ.setdefault("JIRA_API_TOKEN", "test-token")
os.environ.setdefault("JIRA_PROJECT_KEY", "NISS")
os.environ.setdefault("APP_BASIC_AUTH_USER", "oncall")
os.environ.setdefault("APP_BASIC_AUTH_PASSWORD", "test-password")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_index_requires_auth():
    assert client.get("/").status_code == 401


def test_index_rejects_wrong_password():
    assert client.get("/", auth=("oncall", "wrong")).status_code == 401


def test_index_accepts_correct_credentials():
    assert client.get("/", auth=("oncall", "test-password")).status_code == 200
