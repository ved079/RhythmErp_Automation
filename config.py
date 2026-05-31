"""
config.py
---------
Central configuration for RhythmERP Automation Project.
All URLs, timeouts, paths, and settings are defined here.
Other modules import from this file — change once, reflects everywhere.

IMPORTANT: Credentials are loaded from .env file.
Never hardcode credentials here — always use environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# RHYTHMERP APPLICATION
# ============================================================
RHYTHMERP_BASE_URL = os.getenv("RHYTHMERP_BASE_URL", "https://rhythmerp.algorhythms.in")
RHYTHMERP_LOGIN_URL = f"{RHYTHMERP_BASE_URL}/#/authentication/signin"
LOGIN_URL = RHYTHMERP_LOGIN_URL
COMPANY_ONBOARDING_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Company%20Onboarding"
RHYTHMERP_FORGOT_PASSWORD_URL = f"{RHYTHMERP_BASE_URL}/#/authentication/forgot-password"


# ============================================================
# RHYTHMERP LOGIN CREDENTIALS (loaded from .env)
# ============================================================
RHYTHMERP_EMAIL = os.getenv("RHYTHMERP_EMAIL", "")
RHYTHMERP_PASSWORD = os.getenv("RHYTHMERP_PASSWORD", "")
RHYTHMERP_FACILITY = os.getenv("RHYTHMERP_FACILITY", "")


# ============================================================
# FORGOT PASSWORD CREDENTIALS (loaded from .env)
# ============================================================
RHYTHMERP_FP_EMAIL = os.getenv("RHYTHMERP_FP_EMAIL", RHYTHMERP_EMAIL)
RHYTHMERP_FP_USERNAME = os.getenv("RHYTHMERP_FP_USERNAME", RHYTHMERP_EMAIL)
RHYTHMERP_FP_TENANT = os.getenv("RHYTHMERP_FP_TENANT", "")
RHYTHMERP_FP_CURRENT_PASSWORD = os.getenv("RHYTHMERP_FP_CURRENT_PASSWORD", RHYTHMERP_PASSWORD)
RHYTHMERP_FP_NEW_PASSWORD = os.getenv("RHYTHMERP_FP_NEW_PASSWORD", "")
RHYTHMERP_FP_ALT_PASSWORD = os.getenv("RHYTHMERP_FP_ALT_PASSWORD", "")
RHYTHMERP_FP_DEFAULT_PASSWORD = os.getenv("RHYTHMERP_FP_DEFAULT_PASSWORD", RHYTHMERP_PASSWORD)
RHYTHMERP_FP_OLD_PASSWORDS = [
    os.getenv("RHYTHMERP_FP_OLD_PASSWORD_1", ""),
    os.getenv("RHYTHMERP_FP_OLD_PASSWORD_2", ""),
    os.getenv("RHYTHMERP_FP_OLD_PASSWORD_3", ""),
]


# ============================================================
# BROWSER SETTINGS
# ============================================================
BROWSER = os.getenv("BROWSER", "chrome").lower()  # "chrome" or "edge"
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"


# ============================================================
# TIMEOUTS (in seconds)
# ============================================================
EXPLICIT_WAIT = int(os.getenv("EXPLICIT_WAIT", "15"))
PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "60"))
IMPLICIT_WAIT = 5


# ============================================================
# DIRECTORY PATHS (relative to project root)
# ============================================================
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "pages", "login_screens", "screenshots")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "pages", "login_screens", "reports")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Ensure directories exist
for directory in [SCREENSHOT_DIR, REPORT_DIR, DATA_DIR]:
    os.makedirs(directory, exist_ok=True)

# ============================================================
# ALIAS MAPPINGS (backward compatibility)
# ============================================================
FP_EMAIL = RHYTHMERP_FP_EMAIL
FP_CURRENT_PASSWORD = RHYTHMERP_FP_CURRENT_PASSWORD
FP_NEW_PASSWORD = RHYTHMERP_FP_NEW_PASSWORD
FP_ALT_PASSWORD = RHYTHMERP_FP_ALT_PASSWORD
FP_USERNAME = RHYTHMERP_FP_USERNAME
FP_TENANT = RHYTHMERP_FP_TENANT
FP_OLD_PASSWORDS = RHYTHMERP_FP_OLD_PASSWORDS
