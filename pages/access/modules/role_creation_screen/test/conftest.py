"""
conftest.py - Role Creation Screen (RhythmERP - Access)
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

    yield driver


@pytest.fixture
def rc_page(logged_in_driver):
    """Role Creation Screen page object — fresh navigation for each test."""
    from pages.access.modules.role_creation_screen.role_creation_screen_page import (
        RoleCreationScreenPage,
    )
    page = RoleCreationScreenPage(logged_in_driver)
    page.navigate_to_page()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_rc_store = CSReportStore()

# ---- Role Creation Screen Known Issues ----

# BUG-001 (HIGH): Duplicate Role Name accepted silently
_rc_store.record_issue(
    severity="High",
    module="Role Creation Screen",
    category="Data Integrity",
    description="Duplicate Role Names are accepted silently. When a user enters a "
                "Role Name that already exists and submits, the form closes without "
                "any error or success message. The duplicate is NOT created, but the "
                "user has no feedback about why the submission was rejected.",
    expected="System should show a validation error like 'Role Name already exists' "
             "and keep the form open for correction.",
    actual="Form closes silently with no error message. Duplicate is not created, "
           "but user receives no feedback.",
    test_ref="RC-D01, RC-D02, RC-D03",
    status="Confirmed",
)

# BUG-002 (HIGH): Spaces-only Role Name accepted without validation
_rc_store.record_issue(
    severity="High",
    module="Role Creation Screen",
    category="Validation",
    description="Spaces-only Role Name is accepted without showing any validation "
                "error text. When a user enters only spaces in the Role Name field "
                "and submits, the form stays open but shows no mat-error message. "
                "The .mat-form-field-invalid CSS class is applied but no text error "
                "is visible to the user.",
    expected="System should reject spaces-only input with a visible validation error "
             "like 'Role Name cannot be empty or spaces only'.",
    actual="No mat-error text is shown. The field is highlighted as invalid via CSS "
           "class but the user cannot tell what is wrong.",
    test_ref="RC-C04",
    status="Confirmed",
)

# BUG-003 (MEDIUM): Inconsistent SweetAlert after successful create
_rc_store.record_issue(
    severity="Medium",
    module="Role Creation Screen",
    category="UX",
    description="SweetAlert confirmation after successful creation is inconsistent. "
                "The first role creation in a session typically shows 'Role created' "
                "SweetAlert, but subsequent creations may not show any confirmation.",
    expected="System should consistently show a success SweetAlert after every "
             "successful role creation.",
    actual="Success SweetAlert is shown inconsistently — sometimes yes, sometimes no.",
    test_ref="RC-P01",
    status="Confirmed",
)

# BUG-004 (MEDIUM): No maxlength on Role Name
_rc_store.record_issue(
    severity="Medium",
    module="Role Creation Screen",
    category="Validation",
    description="No maxlength attribute on the Role Name input field. Names of 256+ "
                "characters may be accepted and stored without any truncation or "
                "validation error.",
    expected="System should enforce a reasonable maxlength (e.g., 255 chars) "
             "and show inline validation if exceeded.",
    actual="No maxlength attribute found. Very long names are accepted.",
    test_ref="RC-C06",
    status="Confirmed",
)

# BUG-005 (LOW): Special characters / SQL injection / XSS not sanitized
_rc_store.record_issue(
    severity="Low",
    module="Role Creation Screen",
    category="Security",
    description="Special characters, SQL injection strings, and XSS payloads are "
                "accepted in the Role Name field without any sanitization. Examples "
                "include '!@#$%^&*()', '1; DROP TABLE; --', and "
                "'<script>alert(xss)</script>'. While these may be stored safely "
                "by the backend, the lack of input sanitization is a security concern.",
    expected="System should sanitize or reject potentially dangerous input strings.",
    actual="All special characters, SQL injection, and XSS strings are accepted "
           "and stored as-is.",
    test_ref="RC-C07, RC-C08, RC-C09",
    status="Confirmed",
)

# BUG-006 (LOW): No Delete option
_rc_store.record_issue(
    severity="Low",
    module="Role Creation Screen",
    category="Functionality",
    description="No Delete option exists anywhere on the Role Creation Screen — "
                "no Delete button per row, no Delete in More menu, no Delete in "
                "the edit popup.",
    expected="Users should be able to delete a Role record via a Delete button.",
    actual="No Delete functionality available. Records cannot be removed.",
    test_ref="RC-P04",
    status="Confirmed",
)

# BUG-007 (MEDIUM): Empty submit shows no mat-error text
_rc_store.record_issue(
    severity="Medium",
    module="Role Creation Screen",
    category="Validation",
    description="When submitting the form with all required fields empty, the "
                "fields are marked with .mat-form-field-invalid CSS class but "
                "no mat-error text is displayed. The user cannot tell what is "
                "wrong with their submission.",
    expected="System should show clear validation error messages for each "
             "required field, e.g., 'Role Name is required'.",
    actual="Fields are highlighted as invalid (red border) but no error text appears.",
    test_ref="RC-C01",
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