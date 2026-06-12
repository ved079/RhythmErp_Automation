"""
endpoints.py
------------
Centralized API URL constants for the Farmer screen.

All Farmer API utilities MUST use these constants —
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
# Farmer-Specific Constants
# ──────────────────────────────────────────────

SCREEN_NAME = "Farmer"
SCREEN_ID = 49

# Full endpoint paths for Farmer CRUD
FARMER_CREATE = DYNAMIC_SCREEN_WRAPPER                       # POST
FARMER_LIST = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/"      # GET  (list/search)
FARMER_GET = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"   # GET  (detail)
FARMER_UPDATE = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"  # POST (PUT returns 405)
FARMER_SCHEMA = SCREEN_SCHEMA.format(screen_name=SCREEN_NAME)  # GET

# ──────────────────────────────────────────────
# URL Builder Helpers
# ──────────────────────────────────────────────

def build_create_url(base_url: str) -> str:
    """Build full Farmer Create URL."""
    return f"{base_url.rstrip('/')}{FARMER_CREATE}"


def build_list_url(base_url: str) -> str:
    """Build full Farmer List/Search URL."""
    return f"{base_url.rstrip('/')}{FARMER_LIST}"


def build_get_url(base_url: str, entry_id) -> str:
    """Build full Farmer Get Detail URL."""
    return f"{base_url.rstrip('/')}{FARMER_GET.format(entry_id=entry_id)}"


def build_update_url(base_url: str, entry_id) -> str:
    """Build full Farmer Update URL."""
    return f"{base_url.rstrip('/')}{FARMER_UPDATE.format(entry_id=entry_id)}"


def build_schema_url(base_url: str) -> str:
    """Build full Farmer Schema URL."""
    return f"{base_url.rstrip('/')}{FARMER_SCHEMA}"
