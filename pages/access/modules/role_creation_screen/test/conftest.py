"""
conftest.py - Role Creation Screen (RhythmERP)
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
    log.info("LAUNCHING BROWSER (RhythmERP - Role Creation Screen Tests)...")
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
def rc_page(logged_in_driver):
    """Role Creation page object — fresh navigation for each test."""
    from pages.access.modules.role_creation_screen.role_creation_page import (
        RoleCreationPage,
    )
    page = RoleCreationPage(logged_in_driver)
    page.navigate_to_page()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_rc_store = CSReportStore()

# ---- Role Creation Known Issues ----
# These are populated from the Role Creation Master Spec exploration.

# BUG-001 (HIGH): Spaces-only Role Name accepted as valid (ng-valid)
_rc_store.record_issue(
    severity="High",
    module="Role Creation Screen",
    category="Validation",
    description="Spaces-only Role Name is accepted as valid (ng-valid class set). "
                "The system does not validate against whitespace-only input in the "
                "Role Name field. A name consisting entirely of spaces passes client-side "
                "validation and can be submitted.",
    expected="System should trigger a validation error like 'This field is required' "
             "or 'Spaces-only input is not allowed' and keep the form open.",
    actual="CONFIRMED: Spaces-only input accepted as ng-valid. Form can be submitted.",
    test_ref="RC-C03",
    status="Confirmed",
)

# BUG-002 (HIGH): Special characters accepted in Role Name
_rc_store.record_issue(
    severity="High",
    module="Role Creation Screen",
    category="Input Validation",
    description="Special characters such as !@#$%^&*() are accepted in the Role Name "
                "field and saved to the database. No input sanitization or validation "
                "is performed on the Role Name field.",
    expected="System should reject special characters with a validation error.",
    actual="CONFIRMED: Special characters accepted and saved.",
    test_ref="RC-C05",
    status="Confirmed",
)

# BUG-003 (CRITICAL): SQL injection strings accepted
_rc_store.record_issue(
    severity="Critical",
    module="Role Creation Screen",
    category="Security",
    description="SQL injection strings such as '; DROP TABLE roles; -- are accepted "
                "in the Role Name field and saved to the database. This is a critical "
                "security vulnerability that could allow data exfiltration or destruction.",
    expected="System should reject or sanitize SQL injection input.",
    actual="CONFIRMED: SQL injection strings accepted and saved.",
    test_ref="RC-C06",
    status="Confirmed",
)

# BUG-004 (CRITICAL): XSS payloads accepted
_rc_store.record_issue(
    severity="Critical",
    module="Role Creation Screen",
    category="Security",
    description="XSS payloads such as <script>alert('xss')</script> are accepted "
                "in the Role Name field and saved to the database. This is a critical "
                "security vulnerability that could allow cross-site scripting attacks.",
    expected="System should reject or sanitize XSS payloads.",
    actual="CONFIRMED: XSS payloads accepted and saved.",
    test_ref="RC-C07",
    status="Confirmed",
)

# BUG-005 (HIGH): Duplicate Role Names allowed
_rc_store.record_issue(
    severity="High",
    module="Role Creation Screen",
    category="Data Integrity",
    description="Duplicate Role Names are ALLOWED in the system. Two or more roles "
                "with identical Role Name can coexist with no warning. Case-insensitive "
                "duplicates are also allowed.",
    expected="System should show a validation error like 'Role Name already exists' "
             "and keep the form open for correction.",
    actual="CONFIRMED: No uniqueness validation. Duplicate names accepted.",
    test_ref="RC-D01, RC-D02",
    status="Confirmed",
)

# BUG-006 (MEDIUM): No client maxlength — 500-char name silently fails
_rc_store.record_issue(
    severity="Medium",
    module="Role Creation Screen",
    category="Validation",
    description="No maxlength attribute on Role Name input. 500-character names pass "
                "client-side validation (ng-valid) but are silently rejected server-side "
                "with no error message shown to the user. The form just stays open with "
                "no feedback.",
    expected="Client should enforce maxlength or show a clear server-side error.",
    actual="CONFIRMED: No maxlength. Server silently rejects with no error shown.",
    test_ref="RC-C08",
    status="Confirmed",
)

# BUG-007 (LOW): No visible mat-error text on required field validation
_rc_store.record_issue(
    severity="Low",
    module="Role Creation Screen",
    category="Validation UX",
    description="When required field validation triggers, only a red outline appears "
                "on the invalid field. No visible mat-error text is displayed to guide "
                "the user on what needs to be corrected.",
    expected="Should display 'This field is required' inline error text.",
    actual="CONFIRMED: Only red outline, no error text visible.",
    test_ref="RC-C01",
    status="Confirmed",
)

# BUG-008 (LOW): No Delete option anywhere on screen
_rc_store.record_issue(
    severity="Low",
    module="Role Creation Screen",
    category="Functionality",
    description="No Delete option exists anywhere on the Role Creation Screen — "
                "no Delete button per row, no Delete in More menu, no Delete in the "
                "edit popup. Records cannot be removed once created.",
    expected="Users should be able to delete a Role Creation record via a Delete "
             "button on the row or in the edit popup.",
    actual="No Delete functionality available. Records cannot be removed.",
    test_ref="RC-P02",
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
    _rc_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_rc_store)
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
        _rc_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _rc_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _rc_store.results, output_dir, issues=_rc_store.known_issues
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