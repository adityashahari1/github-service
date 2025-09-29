# Author: Aditya Shahari
# Contributors: Mohsen Minai (Non-functional requirements)

import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, Request
from typing import Optional
from pydantic import BaseModel
import httpx
# Import non-functional requirement modules
from .utils.rate_limiter import rate_limiter
from .utils.pagination import validate, pagination_headers
from .utils.logging_utils import logger
from .utils.security import verify_webhook_signature
from .utils.idempotency import idempotency

load_dotenv()

app = FastAPI(title="GitHub Issues Gateway", version="1.0.0")
from .webhook import router as webhook_router
app.include_router(webhook_router)
@app.on_event("startup")
def boot():
    logger.info("ENV_CHECK: %s", {
        "GITHUB_OWNER": os.getenv("GITHUB_OWNER"),
        "GITHUB_REPO": os.getenv("GITHUB_REPO"),
        "PORT": os.getenv("PORT"),
    })

@app.get("/healthz")
def healthz():
    logger.info("Health check called")
    return {"status": "ok"}


# 1) GET /issues, get list of issues
# Author: Aditya Shahari

@app.get("/issues")
def list_issues(
    response: Response,
    state: str = "open",
    page: int = 1,
    per_page: int = 30,
    labels: Optional[str] = None,
):
    logger.info("List issues called: state=%s, page=%s, per_page=%s, labels=%s",
                state, page, per_page, labels)
    if state not in ("open", "closed", "all"):
        raise HTTPException(status_code=400, detail="state must be one of: open, closed, all")
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if per_page < 1 or per_page > 100:
        raise HTTPException(status_code=400, detail="per_page must be between 1 and 100")

    url = f"https://api.github.com/repos/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}/issues"
    params = {"state": state, "page": page, "per_page": per_page}
    if labels:
        params["labels"] = labels

    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        with httpx.Client(timeout=10) as client:
            gh = client.get(url, headers=headers, params=params)
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"github unreachable: {e}")

    response.headers["Link"] = gh.headers.get("Link", "")

    if gh.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="github auth failed or insufficient permissions")
    if gh.status_code == 404:
        raise HTTPException(status_code=404, detail="owner/repo not found or not accessible")
    if gh.status_code >= 500:
        raise HTTPException(status_code=503, detail="github server error")

    return gh.json()


# 2) POST /issues, create new issues
# Author: Aditya Shahari

class CreateIssue(BaseModel):
    title: str
    body: Optional[str] = None
    labels: Optional[list[str]] = None

@app.post("/issues", status_code=201)
def create_issue(request: Request, issue: CreateIssue, response: Response):
    logger.info("Create issue called: title=%s, labels=%s", issue.title, issue.labels)

    if not issue.title:
        raise HTTPException(status_code=400, detail="Title is required")

    url = f"https://api.github.com/repos/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}/issues"

    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    payload = {
        "title": issue.title,
        "body": issue.body,
        "labels": issue.labels,
    }

    try:
        with httpx.Client(timeout=10) as client:
            gh = client.post(url, headers=headers, json=payload)
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"github unreachable: {e}")

    if gh.status_code == 401 or gh.status_code == 403:
        raise HTTPException(status_code=401, detail="GitHub auth failed or no access.")
    if gh.status_code == 422:
        raise HTTPException(status_code=400, detail="GitHub validation failed")
    if gh.status_code >= 500:
        raise HTTPException(status_code=503, detail="GitHub server error")

    data = gh.json()
    response.headers["Location"] = f"/issues/{data.get('number')}"
    logger.info("Issue created successfully: number=%s", data.get("number"))
    return {
        "number": data.get("number"),
        "html_url": data.get("html_url"),
        "state": data.get("state"),
        "title": data.get("title"),
        "body": data.get("body"),
        "labels": [label["name"] for label in data.get("labels", [])],
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }


# 3) GET /issues, get issue by id 
# Author: Aditya Shahari

@app.get("/issues/{number}")
def get_issue(number: int):
    logger.info("Get issue called: number=%s", number)

    url = f"https://api.github.com/repos/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}/issues/{number}"

    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        with httpx.Client(timeout=10) as client:
            gh = client.get(url, headers=headers)
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"github unreachable: {e}")

    if gh.status_code == 404:
        raise HTTPException(status_code=404, detail="Issue not found")
    if gh.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="GitHub auth failed or insufficient permissions")
    if gh.status_code >= 500:
        raise HTTPException(status_code=503, detail="GitHub server error")

    logger.info("Get issue success: number=%s", number)

    return gh.json()


# 4) PATCH /issues, update issue by id 
# Author: Aditya Shahari

class UpdateIssue(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    state: Optional[str] = None

@app.patch("/issues/{number}")
def update_issue(number: int, update: UpdateIssue):
    logger.info("Update issue called: number=%s, title=%s, state=%s",
                number, update.title, update.state)
    url = f"https://api.github.com/repos/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}/issues/{number}"

    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    payload = {}
    if update.title is not None:
        payload["title"] = update.title
    if update.body is not None:
        payload["body"] = update.body
    if update.state is not None:
        if update.state not in ["open", "closed"]:
            raise HTTPException(status_code=400, detail="state must be 'open' or 'closed'")
        payload["state"] = update.state

    try:
        with httpx.Client(timeout=10) as client:
            gh = client.patch(url, headers=headers, json=payload)
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"github unreachable: {e}")

    if gh.status_code == 404:
        raise HTTPException(status_code=404, detail="Issue not found")
    if gh.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="GitHub auth failed or insufficient permissions")
    if gh.status_code == 422:
        raise HTTPException(status_code=400, detail="GitHub validation failed")
    if gh.status_code >= 500:
        raise HTTPException(status_code=503, detail="GitHub server error")
    logger.info("Update issue success: number=%s", number)

    return gh.json()


# 5) POST /issues/{number}/comments - Add comment to issue
# Author: Mohsen Minai

class CreateComment(BaseModel):
    body: str

@app.post("/issues/{number}/comments", status_code=201)
def create_comment(number: int, comment: CreateComment):
    logger.info("Create comment called: number=%s", number)
    
    if not comment.body or not comment.body.strip():
        raise HTTPException(status_code=400, detail="Comment body is required")
    
    url = f"https://api.github.com/repos/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}/issues/{number}/comments"
    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"body": comment.body.strip()}
    
    try:
        with httpx.Client(timeout=10) as client:
            gh = client.post(url, headers=headers, json=payload)
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"GitHub unreachable: {e}")
    
    if gh.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Issue #{number} not found")
    if gh.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="GitHub auth failed")
    
    data = gh.json()
    logger.info("Comment created successfully: id=%s", data.get("id"))
    return {
        "id": data["id"],
        "body": data["body"],
        "user": {"login": data["user"]["login"]},
        "created_at": data["created_at"],
        "html_url": data["html_url"]
    }


# 6) POST /webhook - Handle GitHub webhooks
# Author: Mohsen Minai

@app.post("/webhook", status_code=204)
async def handle_webhook(request: Request):
    delivery_id = request.headers.get("x-github-delivery", "")
    event_type = request.headers.get("x-github-event", "")
    signature = request.headers.get("x-hub-signature-256", "")
    
    payload_bytes = await request.body()
    
    # Verify signature
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")
    if not verify_webhook_signature(payload_bytes, signature, webhook_secret):
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse JSON
    try:
        payload = json.loads(payload_bytes)
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    action = payload.get("action", "")
    
    # Check supported events
    if event_type not in ("ping", "issues", "issue_comment"):
        raise HTTPException(status_code=400, detail=f"Unsupported event: {event_type}")
    
    # Handle ping
    if event_type == "ping":
        logger.info("Webhook ping received")
        return
    
    # Check if already processed
    if idempotency.already_processed(delivery_id, event_type, action):
        logger.info("Duplicate webhook, skipping")
        return
    
    # Mark as processed
    idempotency.mark_processed(delivery_id, event_type, action, payload)
    logger.info("Webhook processed: %s %s", event_type, action)


# 7) GET /events - Get recent webhook events
# Author: Mohsen Minai

@app.get("/events")
def get_events(limit: int = 50):
    if limit > 100:
        limit = 100
    return idempotency.get_recent_events(limit)
@app.get("/")
def read_root():
    return {"message": "GitHub Issues Gateway API running. See /docs for API docs."}
