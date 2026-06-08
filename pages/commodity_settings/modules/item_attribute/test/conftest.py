"""
conftest.py - Item Attribute (RhythmERP)
Fixtures and hooks for Item Attribute automation tests.
Optimised (UOM gold standard v2):
- Session-scoped logged_in_driver (login ONCE, reuse browser)
- Per-test ia_page fixture parameterized by attr_num [1-5]
- _cleanup() (hard_refresh between tests) for speed
"""

import os
import sys
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
    config.addinivalue_line("markers", "smoke: Critical path tests (create, search, view, edit)")
    config.addinivalue_line("markers", "sanity: Core validation tests - must pass for build acceptance")
    config.addinivalue_line("markers", "regression: Full regression suite - all tests")
    config.addinivalue_line("markers", "bug: Tests documenting known open bugs (BUG-IA01 to BUG-IA08)")
    config.addinivalue_line("markers", "ui: UI-specific behavior tests (popups, filter panels, button visibility)")


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Item Attribute Tests)...")
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

    log.step(3, "Clicking Login button (click_login double-clicks internally)")
    login_page.click_login()
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()

    # Verify login actually succeeded
    if "login" in driver.current_url.lower():
        log.error("Login did not complete — still on login page. URL: " + driver.current_url)
        raise RuntimeError("RhythmERP login failed — still on login page after wait. Check credentials in .env")

    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture
def ia_page(logged_in_driver, attr_num):
    """Item Attribute page object - fresh navigation for each test.
    Uses _cleanup() (hard_refresh) between tests for speed.
    Parameterized by attr_num (1-5)."""
    from pages.commodity_settings.modules.item_attribute.item_attribute_page import (
        ItemAttributePage,
    )
    page = ItemAttributePage(logged_in_driver, attr_num=attr_num)
    page.navigate_to_page()
    yield page
    # Cleanup: hard refresh to clear any leftover state
    try:
        page._cleanup()
    except Exception:
        pass


def pytest_generate_tests(metafunc):
    """Parameterize tests that use attr_num fixture."""
    if "attr_num" in metafunc.fixturenames:
        metafunc.parametrize("attr_num", [1, 2, 3, 4, 5])
