"""
RhythmERP Automation — FastAPI Backend
=======================================
Serves test modules, test cases, and test run execution via SSE.

Run with:  python -m api.server
Default:   http://127.0.0.1:8000
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

# ─── Config ───────────────────────────────────────────────────────────────────

API_KEY = os.getenv("PROXY_API_KEY", "rhythmerp-proxy-key-change-in-production")
TESTS_DIR = Path(os.getenv("TESTS_DIR", "tests"))
HOST = os.getenv("API_HOST", "127.0.0.1")
PORT = int(os.getenv("API_PORT", "8000"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-5s  %(message)s")
logger = logging.getLogger("api")

# ─── Models ───────────────────────────────────────────────────────────────────


class ApiTest(BaseModel):
    name: str
    display_name: str
    docstring: Optional[str] = None


class ApiSubModule(BaseModel):
    name: str
    display: str
    test_files: list[str] = []
    tests: list[ApiTest] = []


class ApiModule(BaseModel):
    name: str
    display: str
    sub_modules: list[ApiSubModule] = []


class StartRunRequest(BaseModel):
    module: str
    sub_module: Optional[str] = None
    tests: Optional[list[str]] = None


class SSEEvent(BaseModel):
    type: str  # "log" | "test_end" | "run_end" | "error"
    message: str
    test_name: Optional[str] = None
    status: Optional[str] = None
    duration: Optional[float] = None
    timestamp: str = ""


class TestResult(BaseModel):
    name: str
    status: str  # "passed" | "failed" | "skipped" | "error"
    duration: float
    message: Optional[str] = None
    traceback: Optional[str] = None
    screenshot: Optional[str] = None


class RunListItem(BaseModel):
    id: str
    module: str
    sub_module: Optional[str] = None
    status: str  # "pending" | "running" | "completed" | "failed" | "stopped"
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    started_at: Optional[str] = None
    duration: Optional[float] = None


class RunDetail(RunListItem):
    skipped: int = 0
    completed_at: Optional[str] = None
    results: list[TestResult] = []
    report_path: Optional[str] = None


class TestCaseItem(BaseModel):
    id: str = ""
    screenName: str = ""
    description: str = ""
    steps: str = ""
    expected: str = ""
    actual: str = ""
    status: str = "Not Run"
    date: str = ""


class TestCaseModule(BaseModel):
    label: str
    tests: list[TestCaseItem] = []


# ─── In-memory store ──────────────────────────────────────────────────────────

runs: dict[str, RunDetail] = {}
active_runs: dict[str, bool] = {}  # run_id -> stop flag

# ─── Demo data ────────────────────────────────────────────────────────────────

DEMO_MODULES: list[ApiModule] = [
    ApiModule(
        name="login",
        display="Login",
        sub_modules=[
            ApiSubModule(
                name="login_valid",
                display="Valid Login",
                tests=[
                    ApiTest(name="test_valid_login", display_name="Test Valid Login", docstring="Verify login with valid credentials"),
                    ApiTest(name="test_invalid_password", display_name="Test Invalid Password", docstring="Verify error on invalid password"),
                ],
            ),
            ApiSubModule(
                name="login_logout",
                display="Logout",
                tests=[
                    ApiTest(name="test_logout", display_name="Test Logout", docstring="Verify user can log out"),
                ],
            ),
        ],
    ),
    ApiModule(
        name="dashboard",
        display="Dashboard",
        sub_modules=[
            ApiSubModule(
                name="dashboard_widgets",
                display="Widgets",
                tests=[
                    ApiTest(name="test_widget_load", display_name="Test Widget Load", docstring="Verify dashboard widgets load"),
                    ApiTest(name="test_refresh_data", display_name="Test Refresh Data", docstring="Verify dashboard data refreshes"),
                ],
            ),
        ],
    ),
    ApiModule(
        name="masters",
        display="Masters",
        sub_modules=[
            ApiSubModule(
                name="masters_item",
                display="Item Master",
                tests=[
                    ApiTest(name="test_create_item", display_name="Test Create Item", docstring="Verify creating a new item"),
                    ApiTest(name="test_edit_item", display_name="Test Edit Item", docstring="Verify editing an item"),
                    ApiTest(name="test_delete_item", display_name="Test Delete Item", docstring="Verify deleting an item"),
                ],
            ),
            ApiSubModule(
                name="masters_supplier",
                display="Supplier Master",
                tests=[
                    ApiTest(name="test_create_supplier", display_name="Test Create Supplier", docstring="Verify creating a supplier"),
                    ApiTest(name="test_search_supplier", display_name="Test Search Supplier", docstring="Verify supplier search"),
                ],
            ),
        ],
    ),
    ApiModule(
        name="transactions",
        display="Transactions",
        sub_modules=[
            ApiSubModule(
                name="transactions_po",
                display="Purchase Order",
                tests=[
                    ApiTest(name="test_create_po", display_name="Test Create PO", docstring="Verify creating a purchase order"),
                    ApiTest(name="test_approve_po", display_name="Test Approve PO", docstring="Verify PO approval workflow"),
                    ApiTest(name="test_cancel_po", display_name="Test Cancel PO", docstring="Verify PO cancellation"),
                ],
            ),
            ApiSubModule(
                name="transactions_grn",
                display="GRN",
                tests=[
                    ApiTest(name="test_create_grn", display_name="Test Create GRN", docstring="Verify goods receipt note"),
                ],
            ),
        ],
    ),
    ApiModule(
        name="reports",
        display="Reports",
        sub_modules=[
            ApiSubModule(
                name="reports_stock",
                display="Stock Report",
                tests=[
                    ApiTest(name="test_stock_summary", display_name="Test Stock Summary", docstring="Verify stock summary report"),
                    ApiTest(name="test_stock_detail", display_name="Test Stock Detail", docstring="Verify stock detail report"),
                ],
            ),
        ],
    ),
]

# ─── Helper: validate API key ────────────────────────────────────────────────


def verify_api_key(x_proxy_api_key: Optional[str] = Header(None)):
    if x_proxy_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(title="RhythmERP Automation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    """Health check — no auth required."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/modules")
async def get_modules(x_proxy_api_key: str = Header(None)):
    """List all test modules, sub-modules, and tests."""
    verify_api_key(x_proxy_api_key)

    # Try to discover real test modules from the tests/ directory
    modules = _discover_modules()
    if modules:
        return {"modules": [m.model_dump() for m in modules]}

    # Fallback to demo data
    return {"modules": [m.model_dump() for m in DEMO_MODULES]}


@app.get("/api/runs")
async def get_runs(x_proxy_api_key: str = Header(None)):
    """List all runs."""
    verify_api_key(x_proxy_api_key)
    run_list = [RunListItem(**r.model_dump()) for r in runs.values()]
    return {"runs": [r.model_dump() for r in run_list]}


@app.get("/api/runs/{run_id}")
async def get_run_detail(run_id: str, x_proxy_api_key: str = Header(None)):
    """Get detailed run information."""
    verify_api_key(x_proxy_api_key)
    if run_id not in runs:
        raise HTTPException(status_code=404, detail="Run not found")
    return runs[run_id].model_dump()


@app.post("/api/runs/{run_id}/stop")
async def stop_run(run_id: str, x_proxy_api_key: str = Header(None)):
    """Stop a running test."""
    verify_api_key(x_proxy_api_key)
    if run_id not in runs:
        raise HTTPException(status_code=404, detail="Run not found")
    active_runs[run_id] = False
    return {"message": "Stop signal sent"}


@app.delete("/api/runs/{run_id}")
async def delete_run(run_id: str, x_proxy_api_key: str = Header(None)):
    """Delete a run record."""
    verify_api_key(x_proxy_api_key)
    if run_id in runs:
        del runs[run_id]
        active_runs.pop(run_id, None)
    return {"message": "Run deleted"}


@app.post("/api/runs/start")
async def start_run(request: Request, body: StartRunRequest, x_proxy_api_key: str = Header(None)):
    """Start a test run — returns SSE stream."""
    verify_api_key(x_proxy_api_key)

    run_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()

    # Find the module and tests to run
    all_modules = _discover_modules() or DEMO_MODULES
    target_module = next((m for m in all_modules if m.name == body.module), None)
    if not target_module:
        target_module = all_modules[0] if all_modules else None

    # Collect tests to run
    tests_to_run: list[ApiTest] = []
    if target_module:
        for sub in target_module.sub_modules:
            if body.sub_module and sub.name != body.sub_module:
                continue
            for t in sub.tests:
                if body.tests and t.name not in body.tests:
                    continue
                tests_to_run.append(t)

    if not tests_to_run:
        tests_to_run = [ApiTest(name="demo_test", display_name="Demo Test", docstring="Demo test run")]

    # Create run record
    runs[run_id] = RunDetail(
        id=run_id,
        module=body.module,
        sub_module=body.sub_module,
        status="running",
        total_tests=len(tests_to_run),
        passed=0,
        failed=0,
        started_at=now,
    )
    active_runs[run_id] = True

    async def event_stream():
        try:
            for test in tests_to_run:
                if not active_runs.get(run_id, False):
                    yield f"data: {json.dumps(SSEEvent(type='error', message='Run stopped by user', timestamp=datetime.now(timezone.utc).isoformat()).model_dump())}\n\n"
                    break

                # Log start
                yield f"data: {json.dumps(SSEEvent(type='log', message=f'Running: {test.display_name}...', test_name=test.name, timestamp=datetime.now(timezone.utc).isoformat()).model_dump())}\n\n"
                await asyncio.sleep(0.3)

                # Simulate test execution
                start_time = time.time()
                await asyncio.sleep(0.5 + len(test.display_name) * 0.05)
                duration = round(time.time() - start_time, 2)

                # Determine result (80% pass, 15% fail, 5% error for demo)
                import random
                roll = random.random()
                if roll < 0.80:
                    status = "passed"
                    message = None
                elif roll < 0.95:
                    status = "failed"
                    message = f"Assertion failed in {test.display_name}"
                else:
                    status = "error"
                    message = f"Unexpected error in {test.display_name}"

                # Update run record
                if run_id in runs:
                    runs[run_id].results.append(TestResult(
                        name=test.name,
                        status=status,
                        duration=duration,
                        message=message,
                    ))
                    if status == "passed":
                        runs[run_id].passed += 1
                    elif status == "failed":
                        runs[run_id].failed += 1

                # Emit test_end event
                yield f"data: {json.dumps(SSEEvent(type='test_end', message=f'{test.display_name}: {status}', test_name=test.name, status=status, duration=duration, timestamp=datetime.now(timezone.utc).isoformat()).model_dump())}\n\n"

            # Finalize
            if run_id in runs:
                runs[run_id].status = "completed"
                runs[run_id].completed_at = datetime.now(timezone.utc).isoformat()
                runs[run_id].duration = sum(r.duration for r in runs[run_id].results)

            yield f"data: {json.dumps(SSEEvent(type='run_end', message=f'Run completed. {runs[run_id].passed} passed, {runs[run_id].failed} failed.', timestamp=datetime.now(timezone.utc).isoformat()).model_dump())}\n\n"

        except Exception as e:
            logger.error(f"Run {run_id} error: {e}")
            if run_id in runs:
                runs[run_id].status = "failed"
            yield f"data: {json.dumps(SSEEvent(type='error', message=str(e), timestamp=datetime.now(timezone.utc).isoformat()).model_dump())}\n\n"
        finally:
            active_runs.pop(run_id, None)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/screenshot")
async def get_screenshot(x_proxy_api_key: str = Header(None)):
    """Get current browser screenshot (placeholder)."""
    verify_api_key(x_proxy_api_key)
    return {"screenshot": None, "active": False}


@app.get("/api/test-cases")
async def get_test_cases(x_proxy_api_key: str = Header(None)):
    """Get test case data for the Results tab."""
    verify_api_key(x_proxy_api_key)

    all_modules = _discover_modules() or DEMO_MODULES
    data: dict[str, dict] = {}

    for mod in all_modules:
        tests = []
        for sub in mod.sub_modules:
            for t in sub.tests:
                tests.append(TestCaseItem(
                    id=t.name,
                    screenName=sub.display,
                    description=t.docstring or t.display_name,
                    steps=f"1. Navigate to {mod.display} > {sub.display}\n2. Execute {t.display_name}",
                    expected=f"{t.display_name} should complete successfully",
                    actual="Not Run",
                    status="Not Run",
                    date="",
                ).model_dump())
        if tests:
            data[mod.name] = TestCaseModule(label=mod.display, tests=tests).model_dump()

    return data


# ─── Module discovery from tests/ directory ───────────────────────────────────


def _discover_modules() -> list[ApiModule]:
    """
    Scan the tests/ directory for Python test files and build module structure.
    Expected layout:
        tests/
          login/
            test_valid_login.py
            test_invalid_password.py
          dashboard/
            test_widgets.py
          masters/
            item/
              test_create_item.py
            supplier/
              test_create_supplier.py
    """
    if not TESTS_DIR.exists():
        return []

    modules: list[ApiModule] = []

    for module_dir in sorted(TESTS_DIR.iterdir()):
        if not module_dir.is_dir() or module_dir.name.startswith("_") or module_dir.name.startswith("."):
            continue

        sub_modules: list[ApiSubModule] = []

        # Check for direct test files (flat structure)
        direct_tests = _scan_test_files(module_dir)
        if direct_tests:
            sub_modules.append(ApiSubModule(
                name=module_dir.name,
                display=_title_case(module_dir.name),
                tests=direct_tests,
            ))

        # Check for sub-directory structure
        for sub_dir in sorted(module_dir.iterdir()):
            if not sub_dir.is_dir() or sub_dir.name.startswith("_") or sub_dir.name.startswith("."):
                continue
            sub_tests = _scan_test_files(sub_dir)
            if sub_tests:
                sub_modules.append(ApiSubModule(
                    name=sub_dir.name,
                    display=_title_case(sub_dir.name),
                    tests=sub_tests,
                ))

        if sub_modules:
            modules.append(ApiModule(
                name=module_dir.name,
                display=_title_case(module_dir.name),
                sub_modules=sub_modules,
            ))

    return modules


def _scan_test_files(directory: Path) -> list[ApiTest]:
    """Find test files in a directory and extract test functions."""
    tests: list[ApiTest] = []

    for f in sorted(directory.iterdir()):
        if not f.is_file() or not f.name.startswith("test_") or not f.name.endswith(".py"):
            continue

        test_name = f.stem  # e.g., "test_valid_login"
        display_name = _test_name_to_display(test_name)

        # Try to extract docstring
        docstring = _extract_docstring(f)

        tests.append(ApiTest(
            name=test_name,
            display_name=display_name,
            docstring=docstring,
        ))

        # Also look for test functions inside the file
        inner_tests = _extract_test_functions(f)
        if len(inner_tests) > 1:
            # Replace the file-level test with individual test functions
            tests.pop()
            tests.extend(inner_tests)

    return tests


def _extract_docstring(filepath: Path) -> Optional[str]:
    """Extract the module-level docstring from a Python file."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        lines = content.strip().split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                # Single-line docstring
                end = stripped[3:]
                if end.endswith('"""') or end.endswith("'''"):
                    return end[:-3].strip()
                # Multi-line — grab until closing
                doc_lines = [stripped[3:]]
                for l in lines[lines.index(line) + 1:]:
                    if '"""' in l or "'''" in l:
                        doc_lines.append(l.split('"""')[0].split("'''")[0])
                        break
                    doc_lines.append(l)
                return " ".join(doc_lines).strip()
            if stripped.startswith("#") or stripped == "":
                continue
            break
    except Exception:
        pass
    return None


def _extract_test_functions(filepath: Path) -> list[ApiTest]:
    """Extract test function names from a Python test file."""
    tests: list[ApiTest] = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("def test_") or stripped.startswith("async def test_"):
                fn_name = stripped.split("(")[0].replace("def ", "").replace("async ", "").strip()
                display = _test_name_to_display(fn_name)
                tests.append(ApiTest(name=fn_name, display_name=display))
    except Exception:
        pass
    return tests


def _title_case(name: str) -> str:
    """Convert snake_case or kebab-case to Title Case."""
    return name.replace("_", " ").replace("-", " ").title()


def _test_name_to_display(name: str) -> str:
    """Convert test_name to 'Test Name' display format."""
    # Remove test_ prefix
    clean = name
    if clean.startswith("test_"):
        clean = clean[5:]
    return "Test " + clean.replace("_", " ").title()


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 RhythmERP Automation API starting on http://{HOST}:{PORT}")
    logger.info(f"   Tests directory: {TESTS_DIR.resolve()}")
    logger.info(f"   Modules discovered: {len(_discover_modules())}")

    uvicorn.run(
        "api.server:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info",
    )
