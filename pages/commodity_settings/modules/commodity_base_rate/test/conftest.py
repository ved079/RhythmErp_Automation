"""
conftest.py - Commodity Base Rate (RhythmERP)
Fixtures, hooks, and bug registry for CBR automation tests.
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
from common.screenshot_broadcast import start as start_screenshot_broadcast, stop as stop_screenshot_broadcast
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD


# ================================================================
# PYTEST MARKERS
# ================================================================

def pytest_configure(config):
    """Register custom pytest markers for test categorization."""
    config.addinivalue_line("markers", "smoke: Critical path tests (create, search, view, version)")
    config.addinivalue_line("markers", "sanity: Core validation tests — must pass for build acceptance")
    config.addinivalue_line("markers", "regression: Full regression suite — all tests")
    config.addinivalue_line("markers", "bug: Tests documenting known open bugs (BUG-001 to BUG-006)")
    config.addinivalue_line("markers", "ui: UI-specific behavior tests (popups, sort, view, history)")


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Commodity Base Rate Tests)...")
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

    log.step(1, "Entering email: " + str(RHYTHMERP_EMAIL))
    login_page.enter_email(RHYTHMERP_EMAIL)

    log.step(2, "Entering password")
    login_page.enter_password(RHYTHMERP_PASSWORD)

    log.step(3, "Selecting facility (Agdi - index 0)")
    login_page.select_facility_by_index(index=0)

    login_page.wait_seconds(1)

    log.step(4, "Clicking Login button")
    login_page.click_login()
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)
    log.info("RhythmERP login successful!")

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture
def cbr_page(logged_in_driver):
    """Commodity Base Rate page object - fresh navigation for each test."""
    from pages.commodity_settings.modules.commodity_base_rate.commodity_base_rate_page import (
        CommodityBaseRatePage,
    )
    page = CommodityBaseRatePage(logged_in_driver)
    page.navigate_to_page()
    yield page
