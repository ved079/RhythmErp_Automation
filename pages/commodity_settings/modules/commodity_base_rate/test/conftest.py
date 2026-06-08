"""
conftest.py - Commodity Base Rate (RhythmERP)
Fixtures, hooks, and bug registry for CBR automation tests.

Optimised (v2) — UOM golden standard:
- Session-scoped browser and login
- Login verification (checks URL doesn't contain "login")
- CSReportStore for auto-generating Excel reports
- Known issues recorded for report
- Removed cbr_page fixture — tests create page object directly
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
from pages.common_settings.cs_report_generator import CSReportStore, generate_cs_report


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

    login_page.wait_seconds(1)

    log.step(3, "Clicking Login button")
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


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_cs_store = CSReportStore()

# ---- CBR Known Issues ----
_cs_store.record_issue(
    severity="High",
    module="Commodity Base Rate",
    category="Data Integrity",
    description="Item Rate field accepts non-numeric input (negative values, special characters). "
                "Should only accept positive decimal numbers.",
    expected="Item Rate should reject non-numeric and negative input.",
    actual="Negative values like -100 and special chars like 'abc!@#' are accepted and saved.",
    test_ref="CBR-V-02, CBR-V-03",
    status="Open",
)
_cs_store.record_issue(
    severity="Medium",
    module="Commodity Base Rate",
    category="Data Integrity",
    description="Item Rate field accepts zero value. Should require a positive number.",
    expected="Item Rate should reject zero value.",
    actual="Zero (0) is accepted as a valid rate.",
    test_ref="CBR-V-04",
    status="Open",
)
_cs_store.record_issue(
    severity="Medium",
    module="Commodity Base Rate",
    category="UI",
    description="Listing shows raw ISO timestamps instead of formatted dates (DD/MM/YYYY).",
    expected="Dates should be formatted as DD/MM/YYYY.",
    actual="Dates displayed as ISO timestamps (e.g. 2026-06-02T00:00:00Z).",
    test_ref="CBR-H-01",
    status="Open",
)
_cs_store.record_issue(
    severity="High",
    module="Commodity Base Rate",
    category="Data Integrity",
    description="To Date is overridden to 30/12/2099 on submit, ignoring user's selected value.",
    expected="To Date should retain the user's selected value.",
    actual="Regardless of what To Date the user selects, it is saved as 30/12/2099.",
    test_ref="CBR-H-02",
    status="Open",
)
_cs_store.record_issue(
    severity="Low",
    module="Commodity Base Rate",
    category="UI",
    description="Edit button disabled for newly created records. "
                "Need to create a version first to enable editing.",
    expected="Edit should be available for records the user created.",
    actual="Edit button is disabled for new records until a version is created.",
    test_ref="CBR-E-01",
    status="Open",
)
_cs_store.record_issue(
    severity="Medium",
    module="Commodity Base Rate",
    category="Functional",
    description="Version creation fails with same From Date — shows generic error instead of "
                "a clear message about date conflicts.",
    expected="Clear error message: 'From Date must be different from existing versions'.",
    actual="Generic error or validation failure when creating version with same From Date.",
    test_ref="CBR-P-02",
    status="Open",
)


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
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
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
