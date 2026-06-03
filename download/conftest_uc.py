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
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD
from pages.common_settings.cs_report_generator import (
    CSReportStore,
    generate_cs_report,
)


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - User Creation Screen Tests)...")
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

    log.step(3, "Selecting facility (blank - first option)")
    login_page.select_facility_by_index(index=0)

    login_page.wait_seconds(1)

    log.step(4, "Clicking Login button")
    login_page.click_login()
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)
    start_screenshot_broadcast(driver)
    log.info("RhythmERP login successful!")

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

# BUG-001 (HIGH): Duplicate username/email: Submit silently fails, NO error message
_uc_store.record_issue(
    severity="High",
    module="User Creation Screen",
    category="Validation",
    description="When creating a user with a username or email that already exists, "
                "the Submit button appears to succeed but the form stays open "
                "with no error message. The user receives no feedback about "
                "why the creation failed. The popup remains visible and the "
                "record is not saved to the database. This applies to BOTH "
                "duplicate username AND duplicate email scenarios.",
    expected="System should show a validation error like 'Username/Email already exists' "
             "and keep the form open for correction, or show a SweetAlert2 warning.",
    actual="CONFIRMED: Submit silently fails — no error message, no record created. "
           "Both duplicate username and duplicate email exhibit this behavior.",
    test_ref="UC-D01, UC-D02",
    status="Confirmed",
)

# BUG-002 (MEDIUM): No maxlength on Username — 256+ chars accepted
_uc_store.record_issue(
    severity="Medium",
    module="User Creation Screen",
    category="Validation",
    description="No maxlength attribute on the Username input field. Names with "
                "256+ characters pass client-side validation but may be silently "
                "rejected server-side with no error message.",
    expected="Client should enforce maxlength or show a clear server-side error.",
    actual="CONFIRMED: No maxlength. Very long names may silently fail.",
    test_ref="UC-C08",
    status="Confirmed",
)

# BUG-003 (MEDIUM): No email format validation on blur
_uc_store.record_issue(
    severity="Medium",
    module="User Creation Screen",
    category="Validation",
    description="The Email field does not validate format on blur. Invalid email "
                "formats like 'not-an-email' are accepted without immediate feedback.",
    expected="Email field should validate format on blur and show inline error.",
    actual="CONFIRMED: No format validation on blur.",
    test_ref="UC-C10",
    status="Confirmed",
)

# BUG-004 (LOW): Spaces in Username show generic SweetAlert2
_uc_store.record_issue(
    severity="Low",
    module="User Creation Screen",
    category="Validation UX",
    description="When a username contains spaces or special characters, a generic "
                "SweetAlert2 popup appears with the message 'Username must not contain "
                "spaces or special characters (# $ % & * etc.)'. Per-field inline "
                "mat-error would be more user-friendly.",
    expected="Per-field inline mat-error message below the Username field.",
    actual="CONFIRMED: Generic SweetAlert2 popup instead of inline mat-error.",
    test_ref="UC-C04",
    status="Confirmed",
)

# BUG-005 (LOW): Designation dropdown has duplicate "Manager" option
_uc_store.record_issue(
    severity="Low",
    module="User Creation Screen",
    category="Data Quality",
    description="The Designation dropdown shows duplicate 'Manager' option. "
                "Both options appear identically in the list, which is confusing.",
    expected="Dropdown should show unique options only.",
    actual="CONFIRMED: 'Manager' appears twice in Designation dropdown.",
    test_ref="UC-C14",
    status="Confirmed",
)

# BUG-006 (LOW): Only 1 mat-error visible at a time
_uc_store.record_issue(
    severity="Low",
    module="User Creation Screen",
    category="Validation UX",
    description="When multiple fields are invalid, only one mat-error is visible "
                "at a time. The user has to fix one error to see the next.",
    expected="All invalid fields should show their errors simultaneously.",
    actual="CONFIRMED: Only 1 mat-error visible at a time.",
    test_ref="UC-C01",
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
