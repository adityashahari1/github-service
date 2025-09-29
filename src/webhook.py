import os
import hmac
import hashlib
from fastapi import APIRouter, Request, Header, HTTPException, status
from starlette.responses import Response
from hmac import compare_digest
import sqlite3
import logging

router = APIRouter()

# Setup logging
logger = logging.getLogger("webhook")
logging.basicConfig(level=logging.INFO)

DATABASE = "webhook_events.db"


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        delivery_id TEXT PRIMARY KEY,
        event_type TEXT,
        action TEXT,
        issue_number INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


def save_event(delivery_id, event_type, action, issue_number):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO events (delivery_id, event_type, action, issue_number)
        VALUES (?, ?, ?, ?)
        """, (delivery_id, event_type, action, issue_number))
        conn.commit()
        logger.info(f"Webhook event saved: {delivery_id} {event_type} {action} issue#{issue_number}")
    except sqlite3.IntegrityError:
        # Duplicate event, already processed
        logger.info(f"Duplicate webhook event ignored: {delivery_id}")
    finally:
        conn.close()


@router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None),
    x_github_delivery: str = Header(None),
):
    # Verify secret is configured
    secret = os.getenv("WEBHOOK_SECRET")
    if secret is None:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    # Read raw body bytes for signature
    body = await request.body()

    # Compute expected signature
    expected_signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    # Constant time compare signatures
    if not compare_digest(expected_signature, x_hub_signature_256):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Validate event type
    valid_events = {"issues", "issue_comment", "ping"}
    if x_github_event not in valid_events:
        logger.warning(f"Unknown webhook event: {x_github_event}")
        raise HTTPException(status_code=400, detail="Unknown event")

    # Parse JSON body for relevant info
    payload = await request.json()
    action = payload.get("action")
    issue = payload.get("issue")
    issue_number = issue.get("number") if issue else None

    # Idempotency and persistence
    save_event(x_github_delivery, x_github_event, action, issue_number)

    # Respond quickly with 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Call init_db on startup (you can trigger this from main or FastAPI events)
init_db()
