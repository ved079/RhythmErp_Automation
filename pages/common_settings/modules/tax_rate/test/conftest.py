"""
conftest.py - Tax Rate Common Settings (RhythmERP)

Optimised (v2) — following UOM gold standard:
- Session-scoped driver + logged_in_driver
- Per-test: PageClass(driver) + navigate_to_page()
- Single hard_refresh() in _cleanup() for fast reset
- No time.sleep in fixture setup
"""

import os
import sys
import logging
import pytest
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from common.browser_utils import get_driver
from pages.login_screens.Login_Screens_.login_page import LoginPage
from common.screenshot_broadcast import start as start_screenshot_broadcast, stop as stop_screenshot_broadcast
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD
from pages.common_settings.cs_report_generator import CSReportStore, generate_cs_report


def pytest_configure(config):
    """Register custom pytest markers for Tax Rate tests."""
    config.addinivalue_line("markers", "smoke: Critical path tests (7 tests)")
    config.addinivalue_line("markers", "sanity: Full functional validation of every test case (20 tests)")
    config.addinivalue_line("markers", "regression: Complete regression suite covering all 20 tests")
    config.addinivalue_line("markers", "bug: Tests verifying known open bugs (5 tests)")
    config.addinivalue_line("markers", "ui: UI/popup/form/table/visual behaviour tests (12 tests)")


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Tax Rate Tests)...")
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

    login_page.wait_seconds(1)

    log.step(4, "Clicking Login button (double-click)")
    login_page.click_login()
    login_page.wait_seconds(3)

    # Double-click login to get tenant dropdown autofilled
    try:
        login_page.click_login()
        login_page.wait_seconds(3)
    except Exception:
        pass

    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture
def tr_page(logged_in_driver):
    """
    Tax Rate page object — fresh navigation for each test.

    Setup:
      1. Create TaxRatePage instance
      2. Navigate to the Tax Rate screen

    Teardown:
      1. Force cleanup any open popups
      2. Hard-refresh for clean state
    """
    from pages.common_settings.modules.tax_rate.tax_rate_page import TaxRatePage

    page = TaxRatePage(logged_in_driver)

    # Navigate to page
    try:
        page.navigate_to_page()
    except Exception as first_err:
        log.warning("First navigation attempt failed, retrying...")
        try:
            page.hard_refresh()
            page.navigate_to_page()
        except Exception as second_err:
            log.error("Navigation failed after retry: " + str(second_err))
            raise

    yield page

    # Post-test teardown
    try:
        page._cleanup()
    except Exception:
        pass
    try:
        page.hard_refresh()
        log.info("Post-test hard refresh complete")
    except Exception:
        pass


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_cs_store = CSReportStore()


# ================================================================
# LOG CAPTURE + PYTEST HOOKS
# ================================================================

class _LogCapture(logging.Handler):
    """Captures log messages during each test for step-level reporting."""

    def __init__(self, store):
        super().__init__()
        self.store = store

    def emit(self, record):
        try:
            msg = record.getMessage()
        except Exception:
            msg = str(record.msg)
        self.store.add_log_message(msg)


_capture_handler = None


def pytest_runtest_setup(item):
    """Start log capture before each test."""
    global _capture_handler
    _cs_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_cs_store)
    _capture_handler.setLevel(logging.INFO)
    try:
        if hasattr(log, "logger") and log.logger:
            log.logger.addHandler(_capture_handler)
        elif hasattr(log, "handlers"):
            log.handlers.append(_capture_handler)
    except Exception:
        logging.getLogger().addHandler(_capture_handler)


def pytest_runtest_teardown(item, nextitem):
    """Detach log handler after each test."""
    global _capture_handler
    if _capture_handler is None:
        return
    try:
        if hasattr(log, "logger") and log.logger:
            log.logger.removeHandler(_capture_handler)
        elif hasattr(log, "handlers") and _capture_handler in log.handlers:
            log.handlers.remove(_capture_handler)
    except Exception:
        pass
    _capture_handler = None


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_makereport(item, call):
    """Capture test result (pass/fail) and finalise for report."""
    outcome = yield
    report = outcome.get_result()
    if call.when == "call":
        if report.passed:
            status = "PASSED"
            error = ""
        elif report.failed:
            status = "FAILED"
            error = str(report.longrepr) if report.longrepr else ""
        else:
            status = "SKIPPED"
            error = ""
        _cs_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _cs_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _cs_store.results, output_dir, issues=_cs_store.known_issues
        )
        print("")
        print("=" * 60)
        print("  REPORT GENERATED: " + filepath)
        print("=" * 60)
    except Exception:
        import traceback as tb
        tb.print_exc()
        print("")
        print("  [WARNING] Report generation failed (see traceback above)")
