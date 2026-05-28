"""
conftest.py (root)
------------------
Shared fixtures available to ALL test sections.
Each section has its own conftest for reporting, screenshots, etc.

Fixtures:
  driver            - Launches browser (session-scoped)
  login_page        - LoginPage object
  auth_section      - AuthSection helper
  logged_in_driver  - Driver with completed login session
"""

import os
import sys
import pytest

# Ensure project root is in Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.logger import log
from common.browser_utils import get_driver
from common.auth_helper import AuthSection
from pages.login_screens.Login_Screens_.login_page import LoginPage


# ================================================================
# BROWSER FIXTURE
# ================================================================

@pytest.fixture(scope="session")
def driver():
    """Launch browser ONCE for the entire test session."""
    log.separator()
    log.info("LAUNCHING BROWSER...")
    log.separator()

    drv = get_driver()

    yield drv

    log.separator()
    log.info("CLOSING BROWSER...")
    log.separator()
    try:
        drv.quit()
        log.info("Browser closed successfully")
    except Exception as e:
        log.error(f"Error closing browser: {e}")


# ================================================================
# PAGE OBJECT FIXTURES
# ================================================================

@pytest.fixture
def login_page(driver):
    """Provide a LoginPage object (not logged in)."""
    return LoginPage(driver)


@pytest.fixture
def auth_section(driver):
    """Provide an AuthSection helper object."""
    return AuthSection(driver)


# ================================================================
# AUTHENTICATED SESSION FIXTURE
# ================================================================

@pytest.fixture(scope="session")
def logged_in_driver(driver):
    """Driver with completed login session. Shared across all tests."""
    log.separator()
    log.info("PERFORMING SESSION LOGIN...")
    log.separator()

    auth = AuthSection(driver)
    try:
        auth.login_default()
        log.info("Session login successful!")
    except Exception as e:
        log.error(f"Session login failed: {e}")
        raise

    yield driver
