"""Pydantic models for the Rhythm ERP Test Execution Engine."""

import re
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


# --- Enums ---

class FetchFkRequest(BaseModel):
    erp_token: str
    erp_tenant_id: Optional[str] = ""
    screen: str


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
    erp_email: Optional[str] = None      # ERP login email for UI Selenium tests
    erp_password: Optional[str] = None   # ERP login password for UI Selenium tests


class StartRunRequest(BaseModel):
    module: str
    sub_module: Optional[str] = None
    tests: Optional[list[str]] = None
    env_url: Optional[str] = None
    erp_token: Optional[str] = None
    erp_tenant_id: Optional[str] = None
    erp_email: Optional[str] = None
    erp_password: Optional[str] = None


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
    created: Optional[int] = None        # run_end: successful chains
    failed: Optional[int] = None         # run_end: failed chains
    total: Optional[int] = None          # run_end: total chains


# --- Batch Data Creation ---

class BatchCreateRequest(BaseModel):
    module: str                        # e.g. "registration"
    sub_module: str                    # e.g. "supplier"
    count: int = 10                    # number of records to create (1-500)
    erp_token: str                     # Bearer token for ERP API
    erp_tenant_id: str = "681"         # ERP tenant ID
    config: Optional[dict] = None      # Module-specific config (e.g. farmer_type, attr_number)
    fixed_payloads: Optional[list[dict]] = None  # pre-generated payloads (conflict mode); skips generation


class CbrTokenRequest(BaseModel):
    erp_token: str
    erp_tenant_id: str = "681"


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


# --- Purchase Chain ---

class PurchaseChainRequest(BaseModel):
    count: int = 1                       # number of chains to create
    supplier_ref_id: int = 1             # supplier ref ID
    num_items: int = 2                   # items per document
    item_ref_id: int = 5                 # item ref ID (fallback if item_ref_ids not set)
    item_ref_ids: Optional[list[int]] = None  # per-row item IDs (overrides item_ref_id)
    item_category_id: Optional[int] = None   # restrict items to this category (None = auto-pick biggest)
    require_tax_rate: bool = True        # True = only items whose HSN has a tax rate; False = all items (rate 0.0 when none)
    delay: float = 0.3                   # delay between API calls
    erp_token: str                       # Bearer token for ERP API
    erp_tenant_id: str = "681"           # ERP tenant ID
    documents: list[str] = ["PO", "GP", "GRN", "QC"]  # which documents to create
    multi_gate_pass: bool = False        # split one PO across multiple GPs (each GP -> its own GRN and QC)
    gp_count: int = 2                    # number of gate passes when multi_gate_pass is True
    supplier_ref_ids: Optional[list[int]] = None  # per-chain suppliers (chain i uses supplier_ref_ids[i]); falls back to supplier_ref_id
    qc_discount: bool = True             # False = skip discount in QC (discount_rate=0)
    customer_ref_id: Optional[int] = None  # Sales Order customer FK (None = auto-pick first customer)


# --- Concurrency Testing ---

class ConcurrencyDispatchRequest(BaseModel):
    payload: CreateRunRequest
    agents: Optional[list[str]] = None  # override PC_AGENT_URLS


class AgentStatusResponse(BaseModel):
    url: str
    pc: str
    status: str  # "ok" | "unreachable"
    latency_ms: float
