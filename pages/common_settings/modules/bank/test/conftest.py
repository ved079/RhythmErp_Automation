"""
conftest.py - Bank Common Settings (RhythmERP)
"""
import sys
import os
import logging  # <-- ADD THIS LINE
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from selenium import webdriver
# ... rest of your existing conftest code

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from common.browser_utils import get_driver
from pages.login_screens.Login_Screens_.login_page import LoginPage
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD
from pages.common_settings.cs_report_generator import CSReportStore, generate_cs_report


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Bank Tests)...")
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
def bank_page(logged_in_driver):
    """Bank page object — fresh navigation for each test."""
    from bank.bank_page import BankPage
    page = BankPage(logged_in_driver)
    page.navigate_to_bank()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_cs_store = CSReportStore()

# ---- Bank Known Issues ----
_cs_store.record_issue(
    severity="High",
    module="Bank",
    category="Validation",
    description="Inconsistent Required Validation — only 4 of 12 required fields show "
                "'This field is required' error on empty submit. Bank Name, Account Number, "
                "IFSC Code, and Cash Credit Limit show inline error. The other 8 required fields "
                "(Bank Code, Branch Name, Branch Code, Account Type, Bank Address, GL Account) "
                "fail silently without any visual feedback.",
    expected="All 12 required fields should display 'This field is required' error text.",
    actual="Only 4 fields show mat-error. The remaining 8 required fields have no inline error, "
           "making it confusing for users to identify missing fields.",
    test_ref="Test T3",
    status="Open",
)

_cs_store.record_issue(
    severity="High",
    module="Bank",
    category="Data Integrity",
    description="No Duplicate Bank Name Check — multiple banks with identical names can be "
                "created without any warning or validation error.",
    expected="System should block duplicate Bank Name with an error like 'Bank Name already exists'.",
    actual="Duplicate names are accepted. No unique constraint on Bank Name field.",
    test_ref="Test T9",
    status="Open",
)

_cs_store.record_issue(
    severity="Medium",
    module="Bank",
    category="Validation",
    description="Special characters accepted in Bank Code and Branch Code fields. Input like "
                "'BC@#$%' and 'BR@#' are stored without any alphanumeric validation.",
    expected="System should restrict Bank Code and Branch Code to alphanumeric characters only.",
    actual="Special characters are accepted and stored in the database.",
    test_ref="Test T18",
    status="Open",
)

_cs_store.record_issue(
    severity="Medium",
    module="Bank",
    category="Validation",
    description="Cash Credit Limit field uses type=text instead of type=number. Browser allows "
                "typing non-numeric characters like 'abc' into the field. Server catches some "
                "invalid values but not all.",
    expected="Field should be type=number to prevent non-numeric browser input.",
    actual="Field is type=text. Server rejects negative numbers but not all invalid input.",
    test_ref="Test T11",
    status="Open",
)

_cs_store.record_issue(
    severity="Low",
    module="Bank",
    category="Validation",
    description="No maxlength on any of the 10 text input fields. All have maxlength=-1 "
                "(unlimited). Extremely long strings (500+ chars) are accepted.",
    expected="Fields should have reasonable maxlength limits to prevent display/storage issues.",
    actual="All text inputs accept unlimited length with no character count indicator.",
    test_ref="—",
    status="Open",
)

_cs_store.record_issue(
    severity="Medium",
    module="Bank",
    category="Security",
    description="SQL injection pattern stored in database. String like '; DROP TABLE Bank-- "
                "is saved as-is. Angular prevents execution but application does not sanitize input.",
    expected="System should sanitize SQL injection patterns before storage.",
    actual="SQL injection payload stored in database. Angular escaping prevents execution but raw string persists.",
    test_ref="—",
    status="Open",
)

_cs_store.record_issue(
    severity="Low",
    module="Bank",
    category="Security",
    description="XSS script tag stored in database. String like <script>alert(1)</script> is "
                "saved as-is. Angular auto-escaping prevents execution but raw HTML stored in DB.",
    expected="System should sanitize HTML/script tags before storage.",
    actual="Script tags stored in DB and displayed as escaped text. Angular prevents XSS execution.",
    test_ref="—",
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