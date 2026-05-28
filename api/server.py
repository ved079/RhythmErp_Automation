"""
FastAPI backend for Rhythm ERP Test Runner UI.

Endpoints:
  - Auth:  POST /api/auth/login, POST /api/auth/logout, GET /api/auth/me,
           GET /api/auth/users (alias for /api/users)
  - Users: GET /api/users, POST /api/users, PUT /api/users/{id}, DELETE /api/users/{id},
           POST /api/users/{id}/reset-password
  - Environments: GET /api/environments, POST /api/environments, PUT /api/environments/{id},
                  DELETE /api/environments/{id}
  - Settings: GET /api/settings, PUT /api/settings/{id}, POST /api/settings/seed
  - Audit Log: GET /api/audit-log
  - Modules: GET /api/modules
  - Runs:  GET /api/runs, GET /api/runs/{id}, POST /api/runs/start,
           POST /api/runs/{id}/stop, POST /api/runs/{id}/rerun-failed
  - Test Cases: GET /api/test-cases
  - Screenshot: GET /api/screenshot
  - Health: GET /api/health
"""

import os
import re
import json
import secrets
import bcrypt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from api.models import (
    ModuleListResponse, RunResponse, RunListResponse,
    CreateRunRequest, StartRunRequest,
    LoginRequest, CreateUserRequest, UpdateUserRequest, ChangePasswordRequest,
    EnvironmentRequest, SettingRequest, AdminResetPasswordRequest,
    RunStatus,
)
from api.test_discovery import discover_all_modules
from api.test_runner import run_tests_stream, stop_run
from api.database import (
    init_db, get_run, list_runs, get_failed_tests, delete_run,
    list_environments, get_environment, create_environment, update_environment, delete_environment,
    list_settings, get_setting, upsert_setting, delete_setting, seed_default_settings,
    list_audit_log, add_audit_entry,
)
from api.screenshot_store import take_screenshot


PROJECT_ROOT = Path(__file__).parent.parent

app = FastAPI(title="Rhythm ERP Test API", version="2.0.0")

# --- Rate Limiting ---
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# --- CORS — restricted to frontend URL ---
_cors_origins = os.getenv("API_CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Setup ---
security = HTTPBearer(auto_error=False)
USERS_PATH = PROJECT_ROOT / "api" / "users.json"
SESSION_EXPIRY_HOURS = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "rhythmerp-proxy-key-change-in-production")

# In-memory sessions: token → {user_id, email, name, role, expires}
_sessions: dict[str, dict] = {}


# ================================================================
# AUTH HELPERS
# ================================================================

def _load_users() -> dict:
    """Load users from JSON file. Creates default if not exists."""
    if not USERS_PATH.exists():
        USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        USERS_PATH.write_text('{"next_id":1,"users":[]}', encoding="utf-8")
    with open(USERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_users(data: dict):
    """Save users to JSON file."""
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _get_user_by_token(token: str | None) -> dict | None:
    """Validate token and return user info. Checks expiry."""
    if not token:
        return None
    session = _sessions.get(token)
    if not session:
        return None

    # Check session expiry
    expires_str = session.get("expires")
    if expires_str:
        try:
            expires_dt = datetime.fromisoformat(expires_str)
            if datetime.now() > expires_dt:
                # Session expired — clean up
                _sessions.pop(token, None)
                return None
        except ValueError:
            pass

    return {
        "id": session["user_id"],
        "email": session["email"],
        "name": session["name"],
        "role": session["role"],
    }


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """FastAPI dependency — requires a valid Bearer token OR a trusted proxy API key."""
    # Check for proxy API key (trusted Next.js proxy)
    proxy_key = request.headers.get("X-Proxy-API-Key", "")
    if proxy_key and proxy_key == PROXY_API_KEY:
        # Build user info from proxy headers
        user_id = request.headers.get("X-User-Id", "proxy-user")
        user_email = request.headers.get("X-User-Email", "")
        user_role = request.headers.get("X-User-Role", "viewer")
        return {
            "id": user_id,
            "email": user_email,
            "name": "Proxy User",
            "role": user_role,
        }

    # Check for Bearer token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = _get_user_by_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict | None:
    """FastAPI dependency — optional auth (returns None if no token/key)."""
    # Check for proxy API key
    proxy_key = request.headers.get("X-Proxy-API-Key", "")
    if proxy_key and proxy_key == PROXY_API_KEY:
        user_id = request.headers.get("X-User-Id", "proxy-user")
        user_email = request.headers.get("X-User-Email", "")
        user_role = request.headers.get("X-User-Role", "viewer")
        return {
            "id": user_id,
            "email": user_email,
            "name": "Proxy User",
            "role": user_role,
        }

    if not credentials:
        return None
    return _get_user_by_token(credentials.credentials)


def require_role(*roles: str):
    """Factory for role-based access control dependency."""
    async def _check_role(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> dict:
        user = await get_current_user(request, credentials)
        if user["role"] not in roles and user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join(roles)}",
            )
        return user
    return _check_role


# ================================================================
# STARTUP
# ================================================================

@app.on_event("startup")
def startup():
    init_db()
    seed_default_settings()


# ================================================================
# AUTH ENDPOINTS
# ================================================================

@app.post("/api/auth/login")
@limiter.limit("5/minute")
def auth_login(request: Request, req: LoginRequest):
    """Login with email + password. Returns a session token."""
    data = _load_users()
    user = None
    for u in data["users"]:
        if u["email"].lower() == req.email.lower():
            user = u
            break

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.get("status") != "active":
        raise HTTPException(status_code=403, detail="Account is deactivated")

    # Check password with bcrypt
    try:
        if not bcrypt.checkpw(req.password.encode(), user["password"].encode()):
            raise HTTPException(status_code=401, detail="Invalid email or password")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Update last login
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    user["lastLogin"] = now
    _save_users(data)

    # Create session
    token = secrets.token_hex(32)
    expires = datetime.now() + timedelta(hours=SESSION_EXPIRY_HOURS)
    _sessions[token] = {
        "user_id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "expires": expires.isoformat(),
    }

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "moduleAccess": user.get("moduleAccess", []),
        }
    }


@app.post("/api/auth/logout")
def auth_logout(user: dict = Depends(get_current_user), request: Request = None):
    """Logout — invalidate the current session token."""
    auth_header = request.headers.get("authorization", "") if request else ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        _sessions.pop(token, None)
    return {"message": "Logged out successfully"}


@app.get("/api/auth/me")
def auth_me(user: dict = Depends(get_current_user)):
    """Get current user info from token."""
    # Fetch fresh user data from file
    data = _load_users()
    full_user = None
    for u in data["users"]:
        if u["id"] == user["id"]:
            full_user = u
            break

    if not full_user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": full_user["id"],
        "email": full_user["email"],
        "name": full_user["name"],
        "role": full_user["role"],
        "status": full_user.get("status", "active"),
        "moduleAccess": full_user.get("moduleAccess", []),
        "lastLogin": full_user.get("lastLogin", ""),
        "createdAt": full_user.get("createdAt", ""),
    }


@app.post("/api/auth/change-password")
def change_password(
    req: ChangePasswordRequest,
    user: dict = Depends(get_current_user),
):
    """Change password for the current user."""
    data = _load_users()
    target = None
    for u in data["users"]:
        if u["id"] == user["id"]:
            target = u
            break

    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password
    try:
        if not bcrypt.checkpw(req.current_password.encode(), target["password"].encode()):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
    except Exception:
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Hash and save new password
    hashed = bcrypt.hashpw(req.new_password.encode(), bcrypt.gensalt()).decode()
    target["password"] = hashed
    _save_users(data)

    return {"message": "Password changed successfully"}


# ================================================================
# USER MANAGEMENT ENDPOINTS
# ================================================================

@app.get("/api/users")
def list_users(user: dict = Depends(require_role("admin"))):
    """List all users. Admin only."""
    data = _load_users()
    # Strip passwords from response
    safe_users = []
    for u in data["users"]:
        safe_users.append({
            "id": u["id"],
            "email": u["email"],
            "name": u["name"],
            "role": u["role"],
            "status": u.get("status", "active"),
            "moduleAccess": u.get("moduleAccess", []),
            "lastLogin": u.get("lastLogin", ""),
            "createdAt": u.get("createdAt", ""),
        })
    return {"users": safe_users, "total": len(safe_users)}


@app.post("/api/users")
def create_user(req: CreateUserRequest, user: dict = Depends(require_role("admin"))):
    """Create a new user. Admin only."""
    data = _load_users()

    # Check for duplicate email
    for u in data["users"]:
        if u["email"].lower() == req.email.lower():
            raise HTTPException(status_code=400, detail="Email already exists")

    # Generate user ID
    user_id = f"usr-{data['next_id']}"
    data["next_id"] += 1

    # Hash password with bcrypt
    hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()

    new_user = {
        "id": user_id,
        "email": req.email,
        "name": req.name,
        "password": hashed,
        "role": req.role,
        "status": "active",
        "moduleAccess": req.moduleAccess,
        "lastLogin": "",
        "createdAt": datetime.now().strftime("%Y-%m-%d"),
    }
    data["users"].append(new_user)
    _save_users(data)

    # Audit log
    add_audit_entry(
        user_id=user["id"], user_name=user.get("name", ""), action="create_user",
        target_type="user", target_id=user_id, target_label=req.name,
        details=f"Created user {req.email} with role {req.role}"
    )

    return {
        "id": user_id,
        "email": req.email,
        "name": req.name,
        "role": req.role,
        "message": "User created successfully",
    }


@app.put("/api/users/{user_id}")
def update_user(
    user_id: str,
    req: UpdateUserRequest,
    current_user: dict = Depends(require_role("admin")),
):
    """Update a user. Admin only."""
    data = _load_users()
    target = None
    for u in data["users"]:
        if u["id"] == user_id:
            target = u
            break

    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Apply updates
    if req.name is not None:
        target["name"] = req.name
    if req.email is not None:
        # Check for duplicate email (excluding current user)
        for u in data["users"]:
            if u["id"] != user_id and u["email"].lower() == req.email.lower():
                raise HTTPException(status_code=400, detail="Email already exists")
        target["email"] = req.email
    if req.role is not None:
        target["role"] = req.role
    if req.status is not None:
        target["status"] = req.status
    if req.moduleAccess is not None:
        target["moduleAccess"] = req.moduleAccess

    _save_users(data)

    # Audit log
    updated_fields = [k for k, v in {"name": req.name, "email": req.email, "role": req.role, "status": req.status}.items() if v is not None]
    add_audit_entry(
        user_id=current_user["id"], user_name=current_user.get("name", ""), action="update_user",
        target_type="user", target_id=user_id, target_label=target.get("name", ""),
        details=f"Updated fields: {', '.join(updated_fields)}"
    )

    return {
        "id": target["id"],
        "email": target["email"],
        "name": target["name"],
        "role": target["role"],
        "status": target.get("status", "active"),
        "message": "User updated successfully",
    }


@app.delete("/api/users/{user_id}")
def delete_user(user_id: str, current_user: dict = Depends(require_role("admin"))):
    """Delete a user. Admin only. Cannot delete self."""
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    data = _load_users()
    original_count = len(data["users"])
    # Find user name before deleting for audit log
    deleted_user = next((u for u in data["users"] if u["id"] == user_id), None)
    deleted_user_name = deleted_user.get("name", "") if deleted_user else ""
    deleted_user_email = deleted_user.get("email", "") if deleted_user else ""
    data["users"] = [u for u in data["users"] if u["id"] != user_id]

    if len(data["users"]) == original_count:
        raise HTTPException(status_code=404, detail="User not found")

    _save_users(data)

    # Audit log
    add_audit_entry(
        user_id=current_user["id"], user_name=current_user.get("name", ""), action="delete_user",
        target_type="user", target_id=user_id, target_label=deleted_user_name,
        details=f"Deleted user {deleted_user_email}"
    )

    return {"message": "User deleted successfully"}


# ================================================================
# AUTH USERS ALIAS (for admin frontend compatibility)
# ================================================================

@app.get("/api/auth/users")
def auth_list_users(user: dict = Depends(require_role("admin"))):
    """Alias for GET /api/users — admin frontend fetches /api/auth/users."""
    return list_users(user)


# ================================================================
# TEST DISCOVERY ENDPOINT
# ================================================================

@app.get("/api/modules", response_model=ModuleListResponse)
def get_modules(user: dict = Depends(get_current_user)):
    """Discover all test modules from the pages/ directory."""
    return discover_all_modules(str(PROJECT_ROOT))


# ================================================================
# TEST RUNS ENDPOINTS
# ================================================================

@app.get("/api/runs", response_model=RunListResponse)
def get_runs(user: dict = Depends(get_current_user)):
    """List all past test runs (most recent first)."""
    runs = list_runs()
    return RunListResponse(runs=runs)


@app.get("/api/runs/{run_id}")
def get_run_detail(run_id: str, user: dict = Depends(get_current_user)):
    """Get full details of a single run including test results."""
    data = get_run(run_id)
    if not data:
        raise HTTPException(status_code=404, detail="Run not found")
    return data


@app.post("/api/runs")
def create_run(request: CreateRunRequest, user: dict = Depends(get_current_user)):
    """Create a new run record (does NOT start execution). Returns the run ID."""
    from api.database import create_run as db_create_run
    run_id = db_create_run(request.module, request.sub_module)
    return {"id": run_id, "message": "Run created. Use POST /api/runs/start to execute."}


@app.post("/api/runs/start")
def start_run(request: StartRunRequest, user: dict = Depends(get_current_user)):
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


@app.post("/api/runs/{run_id}/stop")
def stop_run_endpoint(run_id: str, user: dict = Depends(get_current_user)):
    """Stop a running test by killing the subprocess."""
    # Verify run exists
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


@app.post("/api/runs/{run_id}/rerun-failed")
def rerun_failed(run_id: str, user: dict = Depends(get_current_user)):
    """Re-run only the failed tests from a previous run."""
    failed = get_failed_tests(run_id)
    if not failed:
        return {"error": "No failed tests found", "failed_tests": []}

    # Get original run details to know which module
    data = get_run(run_id)
    if not data:
        raise HTTPException(status_code=404, detail="Original run not found")

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


@app.delete("/api/runs/{run_id}")
def delete_run_endpoint(run_id: str, user: dict = Depends(require_role("admin"))):
    """Delete a run record. Admin only."""
    success = delete_run(run_id)
    if not success:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"message": "Run deleted successfully"}


# ================================================================
# ENVIRONMENTS ENDPOINTS
# ================================================================

@app.get("/api/environments")
def get_environments(user: dict = Depends(get_current_user)):
    """List all environments. Auth required."""
    return {"environments": list_environments()}


@app.post("/api/environments")
def create_env_endpoint(req: EnvironmentRequest, user: dict = Depends(require_role("admin"))):
    """Create a new environment. Admin only."""
    env_id = create_environment(
        name=req.name, base_url=req.base_url, browser=req.browser,
        status=req.status, color=req.color
    )
    # Audit log
    add_audit_entry(
        user_id=user["id"], user_name=user.get("name", ""), action="create_environment",
        target_type="environment", target_id=env_id, target_label=req.name,
        details=f"Created environment {req.name} at {req.base_url}"
    )
    return {"id": env_id, "message": "Environment created successfully"}


@app.put("/api/environments/{env_id}")
def update_env_endpoint(
    env_id: str,
    req: EnvironmentRequest,
    user: dict = Depends(require_role("admin")),
):
    """Update an environment. Admin only."""
    existing = get_environment(env_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Environment not found")
    success = update_environment(
        env_id, name=req.name, base_url=req.base_url, browser=req.browser,
        status=req.status, color=req.color
    )
    if not success:
        raise HTTPException(status_code=400, detail="No fields to update")
    # Audit log
    add_audit_entry(
        user_id=user["id"], user_name=user.get("name", ""), action="update_environment",
        target_type="environment", target_id=env_id, target_label=req.name,
        details=f"Updated environment {req.name}"
    )
    return {"message": "Environment updated successfully"}


@app.delete("/api/environments/{env_id}")
def delete_env_endpoint(env_id: str, user: dict = Depends(require_role("admin"))):
    """Delete an environment. Admin only."""
    existing = get_environment(env_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Environment not found")
    env_name = existing.get("name", "")
    success = delete_environment(env_id)
    if not success:
        raise HTTPException(status_code=404, detail="Environment not found")
    # Audit log
    add_audit_entry(
        user_id=user["id"], user_name=user.get("name", ""), action="delete_environment",
        target_type="environment", target_id=env_id, target_label=env_name,
        details=f"Deleted environment {env_name}"
    )
    return {"message": "Environment deleted successfully"}


# ================================================================
# SETTINGS ENDPOINTS
# ================================================================

@app.get("/api/settings")
def get_settings(user: dict = Depends(get_current_user)):
    """List all settings. Auth required."""
    return {"settings": list_settings()}


@app.put("/api/settings/{setting_id}")
def update_setting_endpoint(
    setting_id: str,
    req: SettingRequest,
    user: dict = Depends(require_role("admin")),
):
    """Update a setting value. Admin only."""
    # Verify setting exists by key or id
    existing = get_setting(req.key)
    if not existing:
        # Try by id
        all_settings = list_settings()
        existing = next((s for s in all_settings if s["id"] == setting_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="Setting not found")
    upsert_setting(
        key=req.key if req.key else existing["key"],
        label=req.label if req.label else existing["label"],
        value=req.value if req.value is not None else existing.get("value", ""),
        type=req.type if req.type else existing.get("type", "text"),
        description=req.description if req.description is not None else existing.get("description", ""),
        category=req.category if req.category else existing.get("category", "System"),
    )
    # Audit log
    add_audit_entry(
        user_id=user["id"], user_name=user.get("name", ""), action="update_setting",
        target_type="setting", target_id=setting_id, target_label=req.label,
        details=f"Updated setting {req.key} = {req.value}"
    )
    return {"message": "Setting updated successfully"}


@app.post("/api/settings/seed")
def seed_settings_endpoint(user: dict = Depends(require_role("admin"))):
    """Seed default settings. Admin only."""
    seed_default_settings()
    return {"message": "Default settings seeded successfully"}


# ================================================================
# AUDIT LOG ENDPOINT
# ================================================================

@app.get("/api/audit-log")
def get_audit_log(
    limit: int = 100,
    offset: int = 0,
    user: dict = Depends(require_role("admin")),
):
    """List audit log entries. Admin only."""
    return {"entries": list_audit_log(limit=limit, offset=offset)}


# ================================================================
# ADMIN PASSWORD RESET
# ================================================================

@app.post("/api/users/{user_id}/reset-password")
def admin_reset_password(
    user_id: str,
    req: AdminResetPasswordRequest,
    current_user: dict = Depends(require_role("admin")),
):
    """Admin resets another user's password. Admin only."""
    data = _load_users()
    target = None
    for u in data["users"]:
        if u["id"] == user_id:
            target = u
            break

    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Hash and save new password
    hashed = bcrypt.hashpw(req.new_password.encode(), bcrypt.gensalt()).decode()
    target["password"] = hashed
    _save_users(data)

    # Audit log
    add_audit_entry(
        user_id=current_user["id"], user_name=current_user.get("name", ""), action="reset_password",
        target_type="user", target_id=user_id, target_label=target.get("name", ""),
        details=f"Admin reset password for {target.get('email', '')}"
    )

    return {"message": "Password reset successfully"}


# ================================================================
# TEST CASES ENDPOINT
# ================================================================

TEST_CASES_PATH = PROJECT_ROOT / "api" / "test_cases.json"


@app.get("/api/test-cases")
async def get_test_cases(
    module: str = None,
    user: dict = Depends(get_current_user),
):
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
# SCREENSHOT ENDPOINT
# ================================================================

@app.get("/api/screenshot")
def get_screenshot_endpoint(user: dict = Depends(get_current_user_optional)):
    """Returns the current browser screenshot as base64 PNG."""
    img = take_screenshot()
    if img is None:
        return JSONResponse({"screenshot": None, "active": False})
    return JSONResponse({"screenshot": img, "active": True})


# ================================================================
# HEALTH ENDPOINT
# ================================================================

@app.get("/api/health")
def health():
    """Health check — no auth required."""
    return {
        "status": "ok",
        "version": "2.0.0",
        "project_root": str(PROJECT_ROOT),
        "active_sessions": len(_sessions),
    }


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
