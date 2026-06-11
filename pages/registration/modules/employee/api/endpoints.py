"""
endpoints.py
------------
Centralized API URL constants for the Employee screen.

All Employee API utilities MUST use these constants —
no hardcoded URL paths anywhere else.

ERP Base URL is read from config.RHYTHMERP_BASE_URL at runtime.
The base URL is managed by RhythmERPAPIClient — this file only
provides the path components that are appended to it.

EMPLOYEE SCREEN (flat form — no steppers, no children[]):
  Schema:  GET  /core/dynamic-screen/Employee/
  List:    GET  /core/dynamic-screen-wrapper/Employee/
  Detail:  GET  /core/dynamic-screen-wrapper/Employee/{id}/
  Create:  POST /core/dynamic-screen-wrapper/Employee/
  Update:  PUT  /core/dynamic-screen-wrapper/Employee/{id}/

NOTE: Unlike Agent (where PUT returns 405 and POST is used for updates),
Employee uses PUT for updates — this is the standard REST pattern.
"""

# ──────────────────────────────────────────────
# Core Endpoint Paths
# ──────────────────────────────────────────────

# The dynamic-screen-wrapper endpoint handles CRUD for all screens
DYNAMIC_SCREEN_WRAPPER = "/core/dynamic-screen-wrapper/"

# Screen schema endpoint — returns field definitions for a screen
SCREEN_SCHEMA = "/core/dynamic-screen/{screen_name}/"

# ──────────────────────────────────────────────
# Employee-Specific Constants
# ──────────────────────────────────────────────

SCREEN_NAME = "Employee"

# Full endpoint paths for Employee CRUD
EMPLOYEE_CREATE = DYNAMIC_SCREEN_WRAPPER                         # POST
EMPLOYEE_LIST = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/"        # GET  (list/search)
EMPLOYEE_GET = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"   # GET  (detail)
EMPLOYEE_UPDATE = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"  # PUT
EMPLOYEE_SCHEMA = SCREEN_SCHEMA.format(screen_name=SCREEN_NAME)  # GET

# ──────────────────────────────────────────────
# URL Builder Helpers
# ──────────────────────────────────────────────

def build_create_url(base_url: str) -> str:
    """Build full Employee Create URL."""
    return f"{base_url.rstrip('/')}{EMPLOYEE_CREATE}"


def build_list_url(base_url: str) -> str:
    """Build full Employee List/Search URL."""
    return f"{base_url.rstrip('/')}{EMPLOYEE_LIST}"


def build_get_url(base_url: str, entry_id) -> str:
    """Build full Employee Get Detail URL."""
    return f"{base_url.rstrip('/')}{EMPLOYEE_GET.format(entry_id=entry_id)}"


def build_update_url(base_url: str, entry_id) -> str:
    """Build full Employee Update URL."""
    return f"{base_url.rstrip('/')}{EMPLOYEE_UPDATE.format(entry_id=entry_id)}"


def build_schema_url(base_url: str) -> str:
    """Build full Employee Schema URL."""
    return f"{base_url.rstrip('/')}{EMPLOYEE_SCHEMA}"
