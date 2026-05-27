"""FastAPI backend for Rhythm ERP Test Runner UI."""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.models import (
    ModuleListResponse, RunResponse, RunListResponse,
    CreateRunRequest, RunStatus
)
from api.test_discovery import discover_all_modules
from api.test_runner import run_tests_stream
from api.database import init_db, get_run, list_runs, get_failed_tests
from api.screenshot_store import take_screenshot

PROJECT_ROOT = Path(__file__).parent.parent

app = FastAPI(title="Rhythm ERP Test API", version="1.0.0")

# CORS — allow the Next.js UI to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# --- Test Discovery ---

@app.get("/api/modules", response_model=ModuleListResponse)
def get_modules():
    """Discover all test modules from the pages/ directory."""
    return discover_all_modules(str(PROJECT_ROOT))


# --- Test Runs ---

@app.get("/api/runs", response_model=RunListResponse)
def get_runs():
    """List all past test runs (most recent first)."""
    runs = list_runs()
    return RunListResponse(runs=runs)


@app.get("/api/runs/{run_id}", response_model=RunResponse)
def get_run_detail(run_id: str):
    """Get full details of a single run including test results."""
    data = get_run(run_id)
    if not data:
        return {"error": "Run not found"}
    return data


@app.post("/api/runs")
def create_run(request: CreateRunRequest):
    """Start a new test run. Returns the run ID immediately (execution is async via SSE)."""
    from api.database import create_run as db_create_run
    run_id = db_create_run(request.module, request.sub_module)
    return {"id": run_id, "message": "Run created. Connect to /api/runs/{id}/stream for live logs."}


@app.get("/api/runs/{run_id}/stream")
def stream_run(run_id: str):
    """SSE endpoint — streams live pytest output while a run is executing."""
    from api.database import update_run_started
    
    # We need the request details to start the run
    # For now, we'll use a simple approach — the client sends the run config via POST
    # and then connects to this SSE endpoint
    # The run_id is used to look up or the run is started fresh
    
    def event_generator():
        # Start the run and stream events
        # This will be triggered after POST /api/runs/start
        yield f"data: {{\"type\": \"log\", \"message\": \"Connect to POST /api/runs/start for execution\", \"timestamp\": \"\"}}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


from typing import Optional

class StartRunRequest(BaseModel):
    module: str
    sub_module: Optional[str] = None
    tests: Optional[list[str]] = None
    env_url: Optional[str] = None


@app.post("/api/runs/start")
def start_run(request: StartRunRequest):
    """Start a test run and return SSE stream with live output."""
    run_request = CreateRunRequest(
        module=request.module,
        sub_module=request.sub_module,
        tests=request.tests,
        env_url=request.env_url,
    )
    
    return StreamingResponse(
        run_tests_stream(run_request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/api/runs/{run_id}/rerun-failed")
def rerun_failed(run_id: str):
    """Re-run only the failed tests from a previous run."""
    failed = get_failed_tests(run_id)
    if not failed:
        return {"error": "No failed tests found", "failed_tests": []}
    
    # Get original run details to know which module
    data = get_run(run_id)
    if not data:
        return {"error": "Original run not found"}
    
    run_request = CreateRunRequest(
        module=data["module"],
        sub_module=data.get("sub_module"),
        tests=failed,
    )
    
    return StreamingResponse(
        run_tests_stream(run_request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/api/runs/{run_id}/stop")
def stop_run(run_id: str):
    """Stop a running test (placeholder — will kill subprocess)."""
    return {"message": f"Stop requested for run {run_id}", "status": "not_implemented"}


# --- Health ---

@app.get("/api/health")
def health():
    return {"status": "ok", "project_root": str(PROJECT_ROOT)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


@app.get("/api/screenshot")
def get_screenshot():
    """Returns the current browser screenshot as base64 PNG."""
    from fastapi.responses import JSONResponse
    img = take_screenshot()
    if img is None:
        return JSONResponse({"screenshot": None, "active": False})
    return JSONResponse({"screenshot": img, "active": True})

# ─── Test Cases Endpoint ────────────────────────────────
import json

TEST_CASES_PATH = PROJECT_ROOT / "api" / "test_cases.json"

@app.get("/api/test-cases")
async def get_test_cases(module: str = None):
    """Return all test cases, optionally filtered by module key."""
    if not TEST_CASES_PATH.exists():
        return {"error": "test_cases.json not found"}
    
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if module:
        key = module.lower().replace(" ", "_").replace("-", "_")
        if key in data:
            return {key: data[key]}
        return {"error": f"Module '{module}' not found"}
    
    return data

# ─── AUTH & USER MANAGEMENT ──────────────────────────────────
import hashlib
import secrets
from datetime import datetime
from fastapi import HTTPException, Header
from pydantic import BaseModel as _BM

USERS_PATH = PROJECT_ROOT / "api" / "users.json"
_sessions: dict[str, dict] = {}  # token → {user_id, email, name, role, expires}

def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def _load_users() -> dict:
    if not USERS_PATH.exists():
        USERS_PATH.write_text('{"next_id":1,"users":[]}', encoding="utf-8")
    with open(USERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_users(data: dict):
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _get_user_by_token(token: str | None) -> dict | None:
    if not token:
        return None
    session = _sessions.get(token)
    if not session:
        return None
    return {"id": session["user_id"], "email": session["email"], "name": session["name"], "role": session["role"]}

class LoginRequest(_BM):
    email: str
    password: str

class CreateUserRequest(_BM):
    email: str
    name: str
    password: str
    role: str = "tester"
    moduleAccess: list[str] = []

class UpdateUserRequest(_BM):
    name: str | None = None
    email: str | None = None
    role: str | None = None
    status: str | None = None
    moduleAccess: list[str] | None = None

@app.post("/api/auth/login")
def auth_login(req: LoginRequest):
    """Login with email + password. Returns a session token."""
    data = _load_users()
    user = None
    for u in data["users"]:
        if u["email"].lower() == req.email.lower():
            user = u
            break
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user["status"] != "active":
        raise HTTPException(status_code=403, detail="Account is deactivated")
    if user["password"] != _hash_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Update last login
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    user["lastLogin"] = now
    _save_users(data)

    # Create session
    token = secrets.token_hex(32)
    _sessions[token] = {
        "user_id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
    }
