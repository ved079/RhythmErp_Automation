"""
conftest.py - Quality Parameter Master Commodity Settings (RhythmERP)
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
    log.info("LAUNCHING BROWSER (RhythmERP - Quality Parameter Master Tests)...")
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
def qp_master_page(logged_in_driver):
    """Quality Parameter Master page object — fresh navigation for each test."""
    from pages.commodity_settings.modules.quality_parameter_master.quality_parameter_master_page import (
        QualityParameterMasterPage,
    )
    page = QualityParameterMasterPage(logged_in_driver)
    page.navigate_to_page()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_qpm_store = CSReportStore()

# ---- Quality Parameter Master Known Issues ----

# BUG-001 (HIGH): Spaces-only name creates empty record
_qpm_store.record_issue(
    severity="High",
    module="Quality Parameter Master",
    category="Data Integrity",
    description="Spaces-only name creates an empty/blank record in the table. "
                "When a user enters only spaces in the Name field and submits, "
                "the ERP trims the spaces but stores an empty string, resulting "
                "in a row with no visible name text.",
    expected="System should reject spaces-only input with a validation error "
             "like 'Name cannot be empty or spaces only'.",
    actual="Spaces-only name is accepted and creates a blank record in the table.",
    test_ref="QPM-C03",
    status="Open",
)

# BUG-002 (HIGH): Duplicate names allowed
_qpm_store.record_issue(
    severity="High",
    module="Quality Parameter Master",
    category="Data Integrity",
    description="Duplicate Quality Parameter names are allowed in the Create form. "
                "Two or more parameters with identical Name can exist in the system "
                "with no warning or rejection.",
    expected="System should show a validation error like 'Name already exists' "
             "and keep the form open for correction.",
    actual="Duplicate name is accepted and saved without any warning.",
    test_ref="QPM-C04",
    status="Open",
)

# BUG-002 (HIGH): Duplicate names allowed in Edit
_qpm_store.record_issue(
    severity="High",
    module="Quality Parameter Master",
    category="Data Integrity",
    description="Duplicate Quality Parameter names are allowed in the Edit form. "
                "Editing a parameter to use another parameter's Name is accepted.",
    expected="System should reject duplicate name during edit.",
    actual="Duplicate name accepted in Edit with no error.",
    test_ref="QPM-E04",
    status="Open",
)

# BUG-003 (MEDIUM): No maxlength on input
_qpm_store.record_issue(
    severity="Medium",
    module="Quality Parameter Master",
    category="Validation",
    description="No maxlength attribute on the Name input field. Names of 300+ "
                "characters are accepted and stored without any truncation or "
                "validation error.",
    expected="System should enforce a reasonable maxlength (e.g., 255 chars) "
             "and show inline validation if exceeded.",
    actual="No maxlength constraint. Extremely long names are stored as-is.",
    test_ref="QPM-C05, QPM-C06",
    status="Open",
)

# BUG-004 (LOW): No success popup
_qpm_store.record_issue(
    severity="Low",
    module="Quality Parameter Master",
    category="UX",
    description="No success SweetAlert2 popup appears after creating or updating "
                "a Quality Parameter. The form popup simply closes with no "
                "confirmation to the user that the action succeeded.",
    expected="A success alert like 'Quality Parameter created successfully' "
             "should appear after create/update.",
    actual="Popup closes silently. No success confirmation shown to user.",
    test_ref="QPM-C07, QPM-E05",
    status="Open",
)

# BUG-005 (LOW): No Delete option
_qpm_store.record_issue(
    severity="Low",
    module="Quality Parameter Master",
    category="Functionality",
    description="No Delete option exists anywhere on the Quality Parameter Master "
                "screen — no Delete button per row, no Delete in More menu, "
                "no Delete in the edit popup.",
    expected="Users should be able to delete a Quality Parameter via a Delete "
             "button on the row or in the edit popup.",
    actual="No Delete functionality available. Records cannot be removed.",
    test_ref="QPM-P02",
    status="Open",
)

# BUG-006 (LOW): No History / Audit trail
_qpm_store.record_issue(
    severity="Low",
    module="Quality Parameter Master",
    category="Functionality",
    description="No History / Audit trail feature exists for Quality Parameter "
                "Master. Unlike Vehicle Master which has a History button per row, "
                "QPM has no way to track when a parameter was created or modified.",
    expected="A History button should be available per row to view change audit trail.",
    actual="No History button or audit trail feature available.",
    test_ref="QPM-P03",
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
    _qpm_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_qpm_store)
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
        _qpm_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _qpm_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _qpm_store.results, output_dir, issues=_qpm_store.known_issues
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
