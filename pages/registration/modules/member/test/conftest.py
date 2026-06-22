"""
conftest.py — Member Screen (RhythmERP)
"""

import os
import sys
import logging
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from common.browser_utils import get_driver
from pages.login_screens.Login_Screens_.login_page import LoginPage
from common.screenshot_broadcast import (
    start as start_screenshot_broadcast,
    stop as stop_screenshot_broadcast,
)
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD


# ================================================================
# LOGIN CREDENTIALS — Member Screen (from config.py / .env)
# ================================================================
MB_LOGIN_EMAIL = RHYTHMERP_EMAIL
MB_LOGIN_PASSWORD = RHYTHMERP_PASSWORD


# ================================================================
# FIXTURES
# ================================================================


@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Member Tests)...")
    log.separator()
    drv = get_driver()
    drv.maximize_window()
    yield drv
    log.separator()
    log.info("CLOSING BROWSER...")
    log.separator()
    try:
        drv.quit()
    except Exception:
        pass


@pytest.fixture(scope="session")
def logged_in_driver(driver):
    """Driver with completed RhythmERP login session."""
    log.separator()
    log.info("LOGGING INTO RHYTHMERP...")
    log.separator()

    login_page = LoginPage(driver)

    log.info("Navigating to: " + str(RHYTHMERP_LOGIN_URL))
    driver.get(RHYTHMERP_LOGIN_URL)
    login_page.wait_seconds(2)

    log.step(1, "Entering email: " + str(MB_LOGIN_EMAIL))
    login_page.enter_email(MB_LOGIN_EMAIL)

    log.step(2, "Entering password")
    login_page.enter_password(MB_LOGIN_PASSWORD)

    login_page._dismiss_tenant_dropdown()

    log.step(3, "Clicking Login button")
    login_page.click_login()
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture(scope="function")
def mb_page(logged_in_driver):
    """Member page object — fresh navigation for each test."""
    from pages.registration.modules.member.member_page import MemberPage

    page = MemberPage(logged_in_driver)
    page.navigate_to_page()
    yield page
    try:
        page.force_close_form_popup()
    except Exception:
        pass


# ================================================================
# MARKER REGISTRATION
# ================================================================


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: smoke tests")
    config.addinivalue_line("markers", "bug: known bug tests")
