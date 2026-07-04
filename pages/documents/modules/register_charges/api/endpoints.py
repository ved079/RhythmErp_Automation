"""
endpoints.py
------------
Centralized API URL constants for the Register Charges screen.

All Register Charges API utilities MUST use these constants --
no hardcoded URL paths anywhere else.
"""

DYNAMIC_SCREEN_WRAPPER = "/core/dynamic-screen-wrapper/"
SCREEN_SCHEMA = "/core/dynamic-screen/{screen_name}/"

SCREEN_NAME = "Register Charges"

REGISTER_CHARGES_CREATE = DYNAMIC_SCREEN_WRAPPER
REGISTER_CHARGES_LIST = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/"
REGISTER_CHARGES_GET = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"
REGISTER_CHARGES_UPDATE = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"
REGISTER_CHARGES_SCHEMA = SCREEN_SCHEMA.format(screen_name="Register%20Charges")


def build_create_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{REGISTER_CHARGES_CREATE}"

def build_list_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{REGISTER_CHARGES_LIST}"

def build_get_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{REGISTER_CHARGES_GET.format(entry_id=entry_id)}"

def build_update_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{REGISTER_CHARGES_UPDATE.format(entry_id=entry_id)}"

def build_schema_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{REGISTER_CHARGES_SCHEMA}"
