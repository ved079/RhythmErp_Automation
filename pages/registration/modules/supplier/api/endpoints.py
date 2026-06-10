"""
endpoints.py
------------
Centralized API URL constants for the Supplier screen.

All Supplier API utilities MUST use these constants —
no hardcoded URL paths anywhere else.

ERP Base URL is read from config.RHYTHMERP_BASE_URL at runtime.
The base URL is managed by RhythmERPAPIClient — this file only
provides the path components that are appended to it.
"""

# ──────────────────────────────────────────────
# Core Endpoint Paths
# ──────────────────────────────────────────────

# The dynamic-screen-wrapper endpoint handles CRUD for all screens
DYNAMIC_SCREEN_WRAPPER = "/core/dynamic-screen-wrapper/"

# Screen schema endpoint — returns field definitions for a screen
SCREEN_SCHEMA = "/core/dynamic-screen/{screen_name}/"

# ──────────────────────────────────────────────
# Supplier-Specific Constants
# ──────────────────────────────────────────────

SCREEN_NAME = "Supplier"

# Full endpoint paths for Supplier CRUD
SUPPLIER_CREATE = DYNAMIC_SCREEN_WRAPPER                       # POST
SUPPLIER_LIST = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/"      # GET  (list/search)
SUPPLIER_GET = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"   # GET  (detail)
SUPPLIER_UPDATE = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"  # POST (PUT returns 405)
SUPPLIER_SCHEMA = SCREEN_SCHEMA.format(screen_name=SCREEN_NAME)  # GET

# ──────────────────────────────────────────────
# URL Builder Helpers
# ──────────────────────────────────────────────

def build_create_url(base_url: str) -> str:
    """Build full Supplier Create URL."""
    return f"{base_url.rstrip('/')}{SUPPLIER_CREATE}"


def build_list_url(base_url: str) -> str:
    """Build full Supplier List/Search URL."""
    return f"{base_url.rstrip('/')}{SUPPLIER_LIST}"


def build_get_url(base_url: str, entry_id) -> str:
    """Build full Supplier Get Detail URL."""
    return f"{base_url.rstrip('/')}{SUPPLIER_GET.format(entry_id=entry_id)}"


def build_update_url(base_url: str, entry_id) -> str:
    """Build full Supplier Update URL."""
    return f"{base_url.rstrip('/')}{SUPPLIER_UPDATE.format(entry_id=entry_id)}"


def build_schema_url(base_url: str) -> str:
    """Build full Supplier Schema URL."""
    return f"{base_url.rstrip('/')}{SUPPLIER_SCHEMA}"
