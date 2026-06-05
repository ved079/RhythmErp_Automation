"""
conftest.py - Designation Common Settings (RhythmERP)

UOM Gold Standard pattern:
- session-scoped driver + logged_in_driver (NO function-scoped fixture)
- Tests use logged_in_driver directly and create DesignationPage locally
- NO hard_refresh in fixture — saves 5-8s per test
"""

import os
import sys
import logging
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.browser_utils import get_driver
from common.logger import log
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD
from pages.login_screens.Login_Screens_.login_page import LoginPage
from common.screenshot_broadcast import start as start_screenshot_broadcast, stop as stop_screenshot_broadcast
from pages.common_settings.cs_report_generator import CSReportStore, generate_cs_report


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Designation Tests)...")
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

    login_page.wait_for_login_complete()

    if "login" in driver.current_url.lower():
        log.error("Login did not complete — still on login page. URL: " + driver.current_url)
        raise RuntimeError("RhythmERP login failed — still on login page after wait. Check credentials in .env")

    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


# ================================================================
# REPORT GENERATOR HOOKS (UOM pattern)
# ================================================================

_cs_store = CSReportStore()

# ---- Designation Known Issues ----
_cs_store.record_issue(
    severity="High",
    module="Designation",
    category="Data Integrity",
    description="Duplicate Designation Name allowed — no validation on Create or Edit.",
    expected="System should reject duplicate name with Pattern B alert.",
    actual="Duplicate name accepted without any warning or error.",
    test_ref="C08, E01",
    status="Open",
)
_cs_store.record_issue(
    severity="Medium",
    module="Designation",
    category="UI",
    description="type='character' rejects punctuation in Name field. "
                "Names like 'Jr. Manager', 'Vice-President', 'Quality (Agri)' "
                "are rejected with 'Invalid Name' mat-error.",
    expected="Common punctuation in job titles should be allowed.",
    actual="Only letters and spaces accepted. Dots, commas, hyphens, parens all rejected.",
    test_ref="C10",
    status="Open",
)
_cs_store.record_issue(
    severity="Critical",
    module="Designation",
    category="Filter",
    description="Apply Filters button completely non-functional.",
    expected="Apply Filters should filter table rows based on selected criteria.",
    actual="Apply Filters click has zero effect — no filtering occurs.",
    test_ref="F05",
    status="Open",
)
_cs_store.record_issue(
    severity="Medium",
    module="Designation",
    category="History",
    description="History shows no data after creation.",
    expected="History should record create/edit actions.",
    actual="History popup shows 'No data available'.",
    test_ref="H02",
    status="Open",
)
_cs_store.record_issue(
    severity="Medium",
    module="Designation",
    category="Backend",
    description="256-char Name submit silently fails — no SweetAlert2 response.",
    expected="Should show error or success message.",
    actual="No SweetAlert2 response — form stays open with no feedback.",
    test_ref="C09",
    status="Open",
)
_cs_store.record_issue(
    severity="Low",
    module="Designation",
    category="Backend",
    description="No max length validation on Name field.",
    expected="Should restrict or truncate at 255 chars.",
    actual="256+ char names accepted (submit may silently fail).",
    test_ref="C09",
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
