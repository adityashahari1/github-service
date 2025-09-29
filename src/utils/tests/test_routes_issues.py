import re
import respx
from httpx import Response as HTTPXResponse

RE_ISSUES_CREATE = re.compile(r"^https://api\.github\.com/repos/.+?/.+?/issues$")

def test_list_issues_rejects_invalid_state(client):
    r = client.get("/issues?state=weird")
    assert r.status_code == 400
    assert "state must be one of" in r.json()["detail"]

def test_update_issue_rejects_invalid_state(client):
    r = client.patch("/issues/1", json={"state": "invalid"})
    assert r.status_code == 400
    assert "state must be 'open' or 'closed'" in r.json()["detail"]

def test_create_issue_requires_title(client):
    # If 'title' is missing entirely, FastAPI returns 422.
    # To exercise your 400 path, send an empty title string:
    r = client.post("/issues", json={"title": "", "body": "missing real title"})
    assert r.status_code == 400
    assert "Title is required" in r.json()["detail"]

@respx.mock
def test_create_issue_201(client):
    respx.post(RE_ISSUES_CREATE).mock(
        return_value=HTTPXResponse(
            201,
            json={
                "number": 42,
                "html_url": "https://github.com/owner/repo/issues/42",
                "state": "open",
                "title": "T",
                "body": "B",
                "labels": [{"name": "bug"}],
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            },
            headers={"Location": "https://api.github.com/repos/owner/repo/issues/42"},
        )
    )

    r = client.post("/issues", json={"title": "T", "body": "B", "labels": ["bug"]})
    assert r.status_code == 201
    assert r.headers["Location"].endswith("/issues/42")
    j = r.json()
    assert j["number"] == 42
    assert j["labels"] == ["bug"]
