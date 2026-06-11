"""
endpoints.py
------------
Centralized API URL constants for the Agent screen.

All Agent API utilities MUST use these constants —
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
# Agent-Specific Constants
# ──────────────────────────────────────────────

SCREEN_NAME = "Agent"

# Full endpoint paths for Agent CRUD
AGENT_CREATE = DYNAMIC_SCREEN_WRAPPER                       # POST
AGENT_LIST = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/"      # GET  (list/search)
AGENT_GET = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"   # GET  (detail)
AGENT_UPDATE = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"  # POST (PUT returns 405)
AGENT_SCHEMA = SCREEN_SCHEMA.format(screen_name=SCREEN_NAME)  # GET

# ──────────────────────────────────────────────
# URL Builder Helpers
# ──────────────────────────────────────────────

def build_create_url(base_url: str) -> str:
    """Build full Agent Create URL."""
    return f"{base_url.rstrip('/')}{AGENT_CREATE}"


def build_list_url(base_url: str) -> str:
    """Build full Agent List/Search URL."""
    return f"{base_url.rstrip('/')}{AGENT_LIST}"


def build_get_url(base_url: str, entry_id) -> str:
    """Build full Agent Get Detail URL."""
    return f"{base_url.rstrip('/')}{AGENT_GET.format(entry_id=entry_id)}"


def build_update_url(base_url: str, entry_id) -> str:
    """Build full Agent Update URL."""
    return f"{base_url.rstrip('/')}{AGENT_UPDATE.format(entry_id=entry_id)}"


def build_schema_url(base_url: str) -> str:
    """Build full Agent Schema URL."""
    return f"{base_url.rstrip('/')}{AGENT_SCHEMA}"
