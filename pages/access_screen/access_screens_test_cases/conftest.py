"""
conftest.py
-----------
pytest configuration for Access Screen tests.
Provides fixtures for browser, login, and navigation.

Overrides REPORT_DIR and SCREENSHOT_DIR so reports/screenshots
save inside pages/access_screen/ (not login_screens).
"""

import os
import sys
import time

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from datetime import datetime
from selenium.webdriver.common.by import By

import config
from common.logger import log
from common.browser_utils import get_driver
from common.auth_helper import AuthSection
from common.nav_section import navigate_to

from pages.access_screen.report_config import (
    REPORT_TITLE, FILENAME_PREFIX,
    UC_DESCRIPTIONS, UC_CATEGORIES
)


# ================================================================
# OVERRIDE PATHS — save to access_screen dirs, not login_screens
# ================================================================
config.SCREENSHOT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "screenshots"
)
config.REPORT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reports"
)
os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
os.makedirs(config.REPORT_DIR, exist_ok=True)

from config import SCREENSHOT_DIR, REPORT_DIR


# ================================================================
# TEST RESULT STORAGE (for Excel report)
# ================================================================
test_results = []


# ================================================================
# BROWSER FIXTURE
# ================================================================

@pytest.fixture(scope="session")
def driver():
    """Launch browser ONCE for the entire test session."""
    log.separator()
    log.info("LAUNCHING BROWSER...")
    log.separator()

    driver = get_driver()

    yield driver

    log.separator()
    log.info("CLOSING BROWSER...")
    log.separator()
    try:
        driver.quit()
        log.info("Browser closed successfully")
    except Exception as e:
        log.error(f"Error closing browser: {e}")


# ================================================================
# AUTHENTICATED SESSION FIXTURE (RHYTHMERP VERSION – SAME AS COMPANY ONBOARDING)
# ================================================================

@pytest.fixture(scope="session")
def logged_in_driver(driver):
    """Driver with completed RhythmERP login session."""
    log.separator()
    log.info("LOGGING INTO RHYTHMERP...")
    log.separator()

    from pages.login_screens.Login_Screens_.login_page import LoginPage
    from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD, RHYTHMERP_FACILITY

    login_page = LoginPage(driver)

    log.info(f"Navigating to: {RHYTHMERP_LOGIN_URL}")
    driver.get(RHYTHMERP_LOGIN_URL)
    login_page.wait_seconds(2)

    log.step(1, f"Entering email: {RHYTHMERP_EMAIL}")
    login_page.enter_email(RHYTHMERP_EMAIL)

    log.step(2, "Entering password")
    login_page.enter_password(RHYTHMERP_PASSWORD)

    if RHYTHMERP_FACILITY:
        log.step(3, f"Selecting facility: {RHYTHMERP_FACILITY}")
        login_page.select_facility(RHYTHMERP_FACILITY)
    else:
        log.step(3, "Selecting facility (blank - first option)")
        login_page.select_facility(" ")

    login_page.wait_seconds(1)

    log.step(4, "Clicking Login button")
    login_button = ("xpath", "//button[contains(.,'Login')]")
    login_page.click(login_button)
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful!")

    # Override BASE_URL so navigation to Access screens uses RhythmERP
    import config as cfg
    original_base = cfg.BASE_URL
    cfg.BASE_URL = "https://rhythmerp.algorhythms.in"

    yield driver

    cfg.BASE_URL = original_base


# ================================================================
# PAGE NAVIGATION FIXTURES
# ================================================================

@pytest.fixture
def on_user_creation(logged_in_driver):
    """Navigate to User Creation screen. Fresh navigation per test."""
    from selenium.webdriver.support.ui import WebDriverWait
    driver = logged_in_driver
    wait = WebDriverWait(driver, 15)

    # Cleanup: dismiss leftover form/modal from previous test
    try:
        close_btns = driver.find_elements(By.CSS_SELECTOR,
            "button[aria-label='Close dialog'], button[mattooltip='CLOSE'], "
            "button[mattooltip='Close']"
        )
        for btn in close_btns:
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
    except Exception:
        pass

    # Cleanup: dismiss leftover SweetAlert
    try:
        confirm = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
        driver.execute_script("arguments[0].click();", confirm)
        time.sleep(0.5)
    except Exception:
        pass

    # Cleanup: dismiss any open dropdown overlay
    try:
        driver.find_element(By.TAG_NAME, "body").click()
        time.sleep(0.5)
    except Exception:
        pass

    log.info("Navigating to User Creation screen...")
    navigate_to(driver, wait, "Access", "User Creation Screen")
    time.sleep(2)

    yield driver, wait


# ================================================================
# CLASS-SCOPED NAVIGATION (positive tests – navigate ONCE per class)
# ================================================================
@pytest.fixture(scope="class")
def user_creation_screen(logged_in_driver):
    """Navigate to User Creation list once for the whole test class."""
    from selenium.webdriver.support.ui import WebDriverWait
    driver = logged_in_driver
    wait = WebDriverWait(driver, 30)

    # One-time cleanup (dismiss any stray overlays before first test)
    try:
        driver.find_element(By.TAG_NAME, "body").click()
        time.sleep(0.3)
    except Exception:
        pass

    log.info("Navigating to User Creation screen...")
    navigate_to(driver, wait, "Access", "User Creation Screen")
    time.sleep(2)

    yield driver, wait
    # No teardown – the next class or session end will handle cleanup


# ================================================================
# PYTEST HOOKS
# ================================================================

def pytest_configure(config):
    """Runs before test session starts."""
    log.separator("=")
    log.info(" ACCESS SCREEN TEST SUITE")
    log.info(f" Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.separator("=")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results for Excel report + screenshot on failure."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        result = {
            "nodeid": item.nodeid,
            "status": "PASSED" if report.passed else "FAILED",
            "message": str(report.longrepr) if report.failed else "",
            "duration": report.duration,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "screenshot": "",
        }

        if report.failed:
            driver = None
            for fixture_name in ["driver", "logged_in_driver", "on_user_creation"]:
                if fixture_name in item.funcargs:
                    val = item.funcargs[fixture_name]
                    if isinstance(val, tuple):
                        driver = val[0]
                    else:
                        driver = val
                    break

            if driver:
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    shot_name = f"FAILED_{item.name}_{timestamp}"
                    shot_path = os.path.join(SCREENSHOT_DIR, f"{shot_name}.png")
                    driver.save_screenshot(shot_path)
                    result["screenshot"] = shot_path
                    log.error(f"Failure screenshot saved: {shot_path}")
                except Exception as e:
                    log.error(f"Could not take failure screenshot: {e}")

        test_results.append(result)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report after all tests complete."""
    if test_results:
        try:
            from common.report_generator import generate_report
            filepath = generate_report(
                test_results,
                config.REPORT_DIR,
                title=REPORT_TITLE,
                filename_prefix=FILENAME_PREFIX,
                descriptions=UC_DESCRIPTIONS,
                categories=UC_CATEGORIES,
            )
            log.separator()
            log.info(f" EXCEL REPORT GENERATED: {filepath}")
            log.separator()
        except Exception as e:
            log.error(f"Failed to generate Excel report: {e}")