# tests/conftest.py
import os
import json
import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient

# Safe defaults for unit tests (real values can override via env)
os.environ.setdefault("GITHUB_OWNER", "owner")
os.environ.setdefault("GITHUB_REPO", "repo")
os.environ.setdefault("GITHUB_TOKEN", "ghp_dummy")
os.environ.setdefault("WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("PORT", "8000")

@pytest.fixture(scope="session")
def app_instance():
    # Import your FastAPI app from src/main.py
    from src.main import app
    return app

@pytest.fixture()
def client(app_instance):
    return TestClient(app_instance)

def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

@pytest.fixture()
def webhook_headers():
    secret = os.getenv("WEBHOOK_SECRET", "test-secret")
    def mk(event: str, delivery: str, payload: dict):
        raw = json.dumps(payload).encode()
        headers = {
            "X-GitHub-Event": event,
            "X-GitHub-Delivery": delivery,
            "X-Hub-Signature-256": _sign(secret, raw),
            "Content-Type": "application/json",
        }
        return headers, raw
    return mk
