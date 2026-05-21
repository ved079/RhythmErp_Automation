"""
conftest.py - User Creation Screen (RhythmERP)
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
from config import RHYTHMERP_LOGIN_URL
from pages.common_settings.cs_report_generator import (
    CSReportStore,
    generate_cs_report,
)


# ================================================================
# LOGIN CREDENTIALS — User Creation Screen
# ================================================================
UC_LOGIN_EMAIL = "Rular@admin.com"
UC_LOGIN_PASSWORD = "Rular@12345678"
UC_LOGIN_FACILITY_INDEX = 0  # Agdi


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - User Creation Tests)...")
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
    log.info("LOGGING INTO RHYTHMERP (User Creation)...")
    log.separator()

    login_page = LoginPage(driver)

    log.info("Navigating to: " + str(RHYTHMERP_LOGIN_URL))
    driver.get(RHYTHMERP_LOGIN_URL)
    login_page.wait_seconds(2)

    log.step(1, "Entering email: " + UC_LOGIN_EMAIL)
    login_page.enter_email(UC_LOGIN_EMAIL)

    log.step(2, "Entering password")
    login_page.enter_password(UC_LOGIN_PASSWORD)

    log.step(3, f"Selecting facility (index {UC_LOGIN_FACILITY_INDEX} — Agdi)")
    login_page.select_facility_by_index(index=UC_LOGIN_FACILITY_INDEX)

    login_page.wait_seconds(1)

    log.step(4, "Clicking Login button")
    login_page.click_login()
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture
def uc_page(logged_in_driver):
    """User Creation page object — fresh navigation for each test."""
    from pages.access.modules.user_creation_screen.user_creation_page import (
        UserCreationPage,
    )
    page = UserCreationPage(logged_in_driver)
    page.navigate_to_page()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_uc_store = CSReportStore()

# ---- User Creation Known Issues ----

# BUG-001 (HIGH): Duplicate Username silently blocked — no error message
_uc_store.record_issue(
    severity="High",
    module="User Creation",
    category="Data Integrity",
    description="Duplicate Username is SILENTLY blocked during Create. "
                "Form stays open on Submit with no SweetAlert2, no mat-error, no toast. "
                "User gets zero feedback.",
    expected="System should show validation error 'Username already exists' "
             "and keep the form open for correction.",
    actual="CONFIRMED: Form stays open with no error message. Silent block.",
    test_ref="UC-D01",
    status="Confirmed",
)

# BUG-002 (MEDIUM): No maxlength on Username
_uc_store.record_issue(
    severity="Medium",
    module="User Creation",
    category="Validation",
    description="No maxlength attribute on Username input. 256+ character usernames "
                "accepted without error or truncation.",
    expected="System should restrict or truncate at a reasonable length (e.g., 255 chars).",
    actual="CONFIRMED: 256+ character usernames accepted.",
    test_ref="UC-C11",
    status="Confirmed",
)

# BUG-003 (HIGH): No email format validation
_uc_store.record_issue(
    severity="High",
    module="User Creation",
    category="Validation",
    description="No email format validation on blur or submit. Invalid emails like "
                "'notanemail' are accepted without any error.",
    expected="System should validate email format and show error for invalid emails.",
    actual="CONFIRMED: No email format validation anywhere in the form.",
    test_ref="UC-C12",
    status="Confirmed",
)

# BUG-004 (LOW): Misleading error for special chars in Username
_uc_store.record_issue(
    severity="Low",
    module="User Creation",
    category="UX",
    description="Typing special characters like !@#$%^&*() in Username shows "
                "'Username should not contain spaces' — misleading message.",
    expected="Error should say 'Username contains invalid characters'.",
    actual="Same 'no spaces' message shown for special characters.",
    test_ref="UC-C08",
    status="Confirmed",
)

# BUG-005 (MEDIUM): No input sanitization on First Name / Last Name
_uc_store.record_issue(
    severity="Medium",
    module="User Creation",
    category="Validation",
    description="No special character validation or sanitization on First Name and "
                "Last Name fields. Characters like !@#$%^&*() accepted without restriction.",
    expected="System should sanitize or reject special character input in name fields.",
    actual="Special chars stored and displayed as-is.",
    test_ref="UC-C09, UC-C10",
    status="Confirmed",
)

# BUG-006 (MEDIUM): Only 1 mat-error visible at a time
_uc_store.record_issue(
    severity="Medium",
    module="User Creation",
    category="UX",
    description="When submitting with all fields empty, only Username shows a visible "
                "mat-error text ('Username is required'). Other fields get ng-invalid CSS "
                "class but no inline error text is displayed.",
    expected="Each invalid field should show its own inline error message.",
    actual="Only 1 mat-error visible at a time. Others just get CSS highlight.",
    test_ref="UC-C01",
    status="Confirmed",
)

# BUG-007 (LOW): Duplicate 'Manager' in Designation dropdown
_uc_store.record_issue(
    severity="Low",
    module="User Creation",
    category="UI Bug",
    description="Designation dropdown shows 'Manager' twice in the options list.",
    expected="Dropdown should show unique options only.",
    actual="CONFIRMED: 'Manager' appears twice in the Designation dropdown.",
    test_ref="UC-P06",
    status="Confirmed",
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
    _uc_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_uc_store)
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
        _uc_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _uc_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _uc_store.results, output_dir, issues=_uc_store.known_issues
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
