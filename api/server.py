"""
FastAPI backend for Rhythm ERP Test Runner UI.

Pure execution engine — only handles test running and discovery.
All auth, user management, environments, settings, and audit logging
are handled by the Next.js application.

Endpoints:
  - POST /api/runs/start    — Start a test run (returns SSE stream)
  - POST /api/runs/{id}/stop — Stop a running test
  - GET  /api/modules       — Discover test modules
  - GET  /api/screenshot    — Get browser screenshot
  - GET  /api/test-cases    — Read test case definitions
  - GET  /api/health        — Health check
"""

import os
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from api.models import (
    ModuleListResponse, CreateRunRequest, StartRunRequest,
)
from api.test_discovery import discover_all_modules
from api.test_runner import run_tests_stream, stop_run
from api.database import init_db
from api.screenshot_store import take_screenshot


PROJECT_ROOT = Path(__file__).parent.parent

app = FastAPI(title="Rhythm ERP Test API", version="3.0.0")

# --- CORS — restricted to frontend URL ---
_cors_origins = os.getenv("API_CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
# STARTUP
# ================================================================

@app.on_event("startup")
def startup():
    init_db()


# ================================================================
# TEST DISCOVERY ENDPOINT
# ================================================================

@app.get("/api/modules", response_model=ModuleListResponse)
def get_modules():
    """Discover all test modules from the pages/ directory."""
    return discover_all_modules(str(PROJECT_ROOT))


# ================================================================
# TEST RUNS ENDPOINTS
# ================================================================

@app.post("/api/runs/start")
def start_run(request: StartRunRequest):
    """Start a test run and return SSE stream with live output."""
    run_request = CreateRunRequest(
        module=request.module,
        sub_module=request.sub_module,
        tests=request.tests,
        env_url=request.env_url,
        erp_token=request.erp_token,
        erp_tenant_id=request.erp_tenant_id,
    )

    return StreamingResponse(
        run_tests_stream(run_request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/api/runs/{run_id}/stop")
def stop_run_endpoint(run_id: str):
    """Stop a running test by killing the subprocess."""
    from api.database import get_run
    run_data = get_run(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")

    if run_data.get("status") not in ("running", "pending"):
        raise HTTPException(status_code=400, detail="Run is not currently running")

    success = stop_run(run_id)
    if success:
        return {"message": f"Run {run_id} stopped successfully", "status": "stopped"}
    else:
        raise HTTPException(status_code=400, detail="Could not stop run — process may have already finished")


# ================================================================
# SCREENSHOT ENDPOINT
# ================================================================

@app.get("/api/screenshot")
def get_screenshot_endpoint():
    """Returns the current browser screenshot as base64 PNG."""
    img = take_screenshot()
    if img is None:
        return JSONResponse({"screenshot": None, "active": False})
    return JSONResponse({"screenshot": img, "active": True})


# ================================================================
# TEST CASES ENDPOINT
# ================================================================

TEST_CASES_PATH = PROJECT_ROOT / "api" / "test_cases.json"


@app.get("/api/test-cases")
async def get_test_cases(module: str = None):
    """Return all test cases, optionally filtered by module key."""
    if not TEST_CASES_PATH.exists():
        return JSONResponse({"error": "test_cases.json not found"}, status_code=404)

    try:
        with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON in test_cases.json"}, status_code=500)

    if module:
        key = module.lower().replace(" ", "_").replace("-", "_")
        if key in data:
            return {key: data[key]}
        return {"error": f"Module '{module}' not found", "available_modules": list(data.keys())}

    return data


# ================================================================
# HEALTH ENDPOINT
# ================================================================

@app.get("/api/health")
def health():
    """Health check — no auth required."""
    return {
        "status": "ok",
        "version": "3.0.0",
        "engine": "pure-execution",
        "project_root": str(PROJECT_ROOT),
    }


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
