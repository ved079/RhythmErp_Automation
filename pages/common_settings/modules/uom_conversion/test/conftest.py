"""
conftest.py - UOM Conversion Common Settings (RhythmERP)
"""

import os
import sys
import logging
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from common.browser_utils import get_driver
from pages.login_screens.Login_Screens_.login_page import LoginPage
from common.screenshot_broadcast import start as start_screenshot_broadcast, stop as stop_screenshot_broadcast
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD, RHYTHMERP_FACILITY
from pages.common_settings.cs_report_generator import CSReportStore, generate_cs_report


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - UOM Conversion Tests)...")
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


@pytest.fixture(scope="function", autouse=True)
def reset_between_tests(logged_in_driver):
    """Hard refresh page after each test to clear stale overlays/state."""
    yield
    try:
        logged_in_driver.execute_script("location.reload(true)")
        import time as _t
        _t.sleep(2)
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

    if RHYTHMERP_FACILITY:
        log.step(3, "Selecting facility: " + str(RHYTHMERP_FACILITY))
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
    start_screenshot_broadcast(driver)
    start_screenshot_broadcast(driver)
    log.info("RhythmERP login successful!")

    yield driver

    stop_screenshot_broadcast()


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_cs_store = CSReportStore()

# ---- UOM Conversion Known Issues ----
_cs_store.record_issue(
    severity="High",
    module="UOM Conversion",
    category="Data Integrity",
    description="Conversion factor with 22+ digits saves successfully but displays "
                "as scientific notation (e.g. 1e+22) when the edit form is reopened. "
                "Clicking Update with the scientific notation value triggers 'Invalid "
                "Conversion Factor' validation — making the record permanently uneditable.",
    expected="System should either reject values that cannot be displayed accurately, "
             "or preserve the full numeric value so the record remains editable.",
    actual="Value saves and displays as 1e+22 on reopen. Update fails with "
           "'Invalid Conversion Factor'. Record becomes permanently uneditable.",
    test_ref="Test 13, Test 14",
    status="Open",
)

_cs_store.record_issue(
    severity="Low",
    module="UOM Conversion",
    category="UI",
    description="The Conversion Factor input has type='character' instead of type='number'. "
                "This means the browser does not provide native number validation or a "
                "numeric keyboard on mobile devices. All validation is done by the backend.",
    expected="Input should use type='number' for better UX and native browser validation.",
    actual="Input uses type='character'. All numeric validation is backend-only.",
    test_ref="Test 8, Test 9",
    status="Open",
)


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
    """Capture test result (pass/fail) and finalize for report."""
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
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
    try:
        filepath = generate_cs_report(_cs_store.results, output_dir,
                                       issues=_cs_store.known_issues)
        print("")
        print("=" * 60)
        print("  REPORT GENERATED: " + filepath)
        print("=" * 60)
    except Exception:
        import traceback as tb
        tb.print_exc()
        print("")
        print("  [WARNING] Report generation failed (see traceback above)")

