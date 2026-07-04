"""
endpoints.py
------------
Centralized API URL constants for the Register of Loan screen.
"""

DYNAMIC_SCREEN_WRAPPER = "/core/dynamic-screen-wrapper/"
SCREEN_SCHEMA = "/core/dynamic-screen/{screen_name}/"

SCREEN_NAME = "Register of Loan"

REGISTER_LOAN_CREATE = DYNAMIC_SCREEN_WRAPPER
REGISTER_LOAN_LIST = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/"
REGISTER_LOAN_GET = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"
REGISTER_LOAN_UPDATE = f"{DYNAMIC_SCREEN_WRAPPER}{SCREEN_NAME}/{{entry_id}}/"
REGISTER_LOAN_SCHEMA = SCREEN_SCHEMA.format(screen_name="Register%20of%20Loan")


def build_create_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{REGISTER_LOAN_CREATE}"

def build_list_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{REGISTER_LOAN_LIST}"

def build_get_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{REGISTER_LOAN_GET.format(entry_id=entry_id)}"

def build_update_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{REGISTER_LOAN_UPDATE.format(entry_id=entry_id)}"

def build_schema_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{REGISTER_LOAN_SCHEMA}"
