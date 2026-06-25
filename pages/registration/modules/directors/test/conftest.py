"""
conftest.py — Directors Screen (RhythmERP)
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from common.browser_utils import get_driver
from common.erp_api_client import RhythmERPAPIClient
from pages.login_screens.Login_Screens_.login_page import LoginPage
from common.screenshot_broadcast import (
    start as start_screenshot_broadcast,
    stop as stop_screenshot_broadcast,
)
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD


DIR_LOGIN_EMAIL = RHYTHMERP_EMAIL
DIR_LOGIN_PASSWORD = RHYTHMERP_PASSWORD


@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Directors Tests)...")
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
    log.separator()
    log.info("LOGGING INTO RHYTHMERP...")
    log.separator()

    login_page = LoginPage(driver)

    log.info("Navigating to: " + str(RHYTHMERP_LOGIN_URL))
    driver.get(RHYTHMERP_LOGIN_URL)
    login_page.wait_seconds(2)

    login_page.enter_email(DIR_LOGIN_EMAIL)
    login_page.enter_password(DIR_LOGIN_PASSWORD)
    login_page._dismiss_tenant_dropdown()
    login_page.click_login()
    login_page.wait_seconds(3)
    login_page.wait_for_login_complete()

    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture(scope="function")
def dir_page(logged_in_driver):
    from pages.registration.modules.directors.directors_page import DirectorsPage

    page = DirectorsPage(logged_in_driver)
    page.navigate_to_page()
    yield page
    try:
        page.force_close_form_popup()
    except Exception:
        pass


@pytest.fixture(scope="session")
def api_client(logged_in_driver):
    """Extract auth token from the already-logged-in browser session.
    No separate API login needed — reuses .env credentials via the browser."""
    from config import RHYTHMERP_FP_TENANT
    token = logged_in_driver.execute_script(
        "return localStorage.getItem('access_token') "
        "|| localStorage.getItem('token') "
        "|| localStorage.getItem('authToken') "
        "|| localStorage.getItem('rhythmerp_token');"
    )
    if not token:
        cookies = {c["name"]: c["value"] for c in logged_in_driver.get_cookies()}
        token = cookies.get("access_token") or cookies.get("refresh_token")
    tenant = RHYTHMERP_FP_TENANT or "681"
    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=tenant)
    yield client


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: Critical happy-path tests")
    config.addinivalue_line("markers", "sanity: Core feature validation tests")
    config.addinivalue_line("markers", "regression: Full coverage tests")
    config.addinivalue_line("markers", "bug: Known bug tests")
    config.addinivalue_line("markers", "ui: Popup, dialog, form UI behavior checks")
    config.addinivalue_line("markers", "hybrid: API creates data + UI verifies")
    config.addinivalue_line("markers", "api: API-only tests, no browser")
