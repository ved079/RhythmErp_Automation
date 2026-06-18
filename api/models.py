"""Pydantic models for the Rhythm ERP Test Execution Engine."""

import re
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


# --- Enums ---

class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


# --- Test Discovery ---

class TestFunction(BaseModel):
    name: str                    # e.g. "test_bank_add"
    display_name: str            # e.g. "test_bank_add" (parsed to readable later)
    docstring: Optional[str] = None  # from the test function's docstring
    type: str = "ui"             # "ui" or "api" — determined by which directory the test lives in


class SubModule(BaseModel):
    name: str                    # e.g. "bank"
    display: str                 # e.g. "Bank"
    test_files: list[str]        # e.g. ["test_bank_validation.py"]
    tests: list[TestFunction]    # discovered test functions


class Module(BaseModel):
    name: str                    # e.g. "common_settings"
    display: str                 # e.g. "Common Settings"
    sub_modules: list[SubModule]


class ModuleListResponse(BaseModel):
    modules: list[Module]


# --- Test Runs ---

class CreateRunRequest(BaseModel):
    module: str                          # e.g. "common_settings"
    sub_module: Optional[str] = None     # e.g. "bank" (optional, runs whole module if blank)
    tests: Optional[list[str]] = None    # specific test names (optional, runs all if blank)
    env_url: Optional[str] = None        # override base URL (optional)
    erp_token: Optional[str] = None      # ERP JWT token for API tests
    erp_tenant_id: Optional[str] = None  # ERP tenant ID (default "681")


class StartRunRequest(BaseModel):
    module: str
    sub_module: Optional[str] = None
    tests: Optional[list[str]] = None
    env_url: Optional[str] = None
    erp_token: Optional[str] = None
    erp_tenant_id: Optional[str] = None


class TestResult(BaseModel):
    name: str                            # test function name
    status: TestStatus
    duration: float                      # seconds
    message: Optional[str] = None        # failure message / skip reason
    traceback: Optional[str] = None      # full traceback on failure
    screenshot: Optional[str] = None     # path to failure screenshot


class RunResponse(BaseModel):
    id: str                              # unique run ID (UUID)
    module: str
    sub_module: Optional[str] = None
    status: RunStatus
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration: Optional[float] = None     # total seconds
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: list[TestResult] = []
    report_path: Optional[str] = None    # path to generated Excel report


class RunListItem(BaseModel):
    id: str
    module: str
    sub_module: Optional[str] = None
    status: RunStatus
    total_tests: int
    passed: int
    failed: int
    started_at: Optional[datetime] = None
    duration: Optional[float] = None


class RunListResponse(BaseModel):
    runs: list[RunListItem]


# --- SSE Log Event ---

class LogEvent(BaseModel):
    type: str                            # "log", "test_start", "test_end", "run_end", "error"
    message: str
    test_name: Optional[str] = None
    status: Optional[str] = None         # passed/failed/skipped
    duration: Optional[float] = None
    timestamp: datetime
    run_id: Optional[str] = None         # batch run ID for Excel export


# --- Batch Data Creation ---

class BatchCreateRequest(BaseModel):
    module: str                        # e.g. "registration"
    sub_module: str                    # e.g. "supplier"
    count: int = 10                    # number of records to create (1-500)
    erp_token: str                     # Bearer token for ERP API
    erp_tenant_id: str = "681"         # ERP tenant ID


# --- Run Completion Callback Payload ---
# Sent from FastAPI to Next.js when a test run finishes.

class RunCompletionPayload(BaseModel):
    """Payload sent to Next.js callback endpoint when a run completes."""
    run_id: str
    module: str
    sub_module: Optional[str] = None
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total: int = 0
    duration_seconds: float = 0
    status: str = "completed"  # completed, failed, stopped
    results: list[dict] = []
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
