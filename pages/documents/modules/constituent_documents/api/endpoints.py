"""
endpoints.py
------------
Centralized API URL constants for the Constituent Documents screen.
"""

DYNAMIC_SCREEN_WRAPPER = "/core/dynamic-screen-wrapper/"
SCREEN_SCHEMA = "/core/dynamic-screen/{screen_name}/"

SCREEN_NAME = "Constituent Documents"

CONST_DOCS_CREATE = DYNAMIC_SCREEN_WRAPPER
CONST_DOCS_LIST = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/"
CONST_DOCS_GET = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"
CONST_DOCS_UPDATE = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"
CONST_DOCS_SCHEMA = SCREEN_SCHEMA.format(screen_name="Constituent%20Documents")


def build_create_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{CONST_DOCS_CREATE}"

def build_list_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{CONST_DOCS_LIST}"

def build_get_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{CONST_DOCS_GET.format(entry_id=entry_id)}"

def build_update_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{CONST_DOCS_UPDATE.format(entry_id=entry_id)}"

def build_schema_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{CONST_DOCS_SCHEMA}"
