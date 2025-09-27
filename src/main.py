import os
from dotenv import load_dotenv
from fastapi import FastAPI

# Load environment variables from .env
load_dotenv()

app = FastAPI()

@app.on_event("startup")
def boot():
    print("ENV_CHECK:", {
        "GITHUB_OWNER": os.getenv("GITHUB_OWNER"),
        "GITHUB_REPO": os.getenv("GITHUB_REPO"),
        "PORT": os.getenv("PORT")
    })

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

