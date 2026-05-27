"""Pydantic models for the Rhythm ERP Test API."""

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


class StartRunRequest(BaseModel):
    module: str
    sub_module: Optional[str] = None
    tests: Optional[list[str]] = None
    env_url: Optional[str] = None


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


# --- Auth Models ---

class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        return v.strip().lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v:
            raise ValueError('Password cannot be empty')
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class CreateUserRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str = "tester"
    moduleAccess: list[str] = []

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.strip().lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v:
            raise ValueError('Password cannot be empty')
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v) > 100:
            raise ValueError('Name too long (max 100 characters)')
        # Sanitize name to prevent XSS
        sanitized = v.strip()
        if any(char in sanitized for char in ['<', '>', '"', "'", '&']):
            raise ValueError('Name contains invalid characters')
        return sanitized

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        allowed_roles = ['admin', 'tester', 'viewer', 'manager', 'qa_lead', 'client']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    moduleAccess: Optional[list[str]] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Email cannot be empty')
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
            return v.strip().lower()
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Name cannot be empty')
            if len(v) > 100:
                raise ValueError('Name too long (max 100 characters)')
            sanitized = v.strip()
            if any(char in sanitized for char in ['<', '>', '"', "'", '&']):
                raise ValueError('Name contains invalid characters')
            return sanitized
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v is not None:
            allowed_roles = ['admin', 'tester', 'viewer', 'manager', 'qa_lead', 'client']
            if v not in allowed_roles:
                raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['active', 'inactive']
            if v not in allowed_statuses:
                raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v
