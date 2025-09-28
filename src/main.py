# Author: Aditya Shahari
# Contributor(s):

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, Request
from typing import Optional
from pydantic import BaseModel
import httpx
from logger import logger

load_dotenv()

app = FastAPI()

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