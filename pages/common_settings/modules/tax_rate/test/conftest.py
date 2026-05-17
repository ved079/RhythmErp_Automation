"""
conftest.py — Tax Rate Common Settings (RhythmERP)
====================================================
Overrides logged_in_driver to use RHYTHMERP credentials.
Inherits driver from root conftest.
"""

import os
import sys
import logging
import pytest

# ── PATH SETUP ── (5 ".." → Pacs_Automation/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD, RHYTHMERP_FACILITY
from pages.common_settings.cs_report_generator import CSReportStore, generate_cs_report
from pages.common_settings.modules.tax_rate.tax_rate_page import TaxRatePage
from pages.login_screens.Login_Screens_.login_page import LoginPage


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="function")
def tr_page(logged_in_driver):
    """
    Fresh TaxRatePage instance per test.
    Navigates to Tax Rate page and ensures clean state.
    """
    page = TaxRatePage(logged_in_driver)
    page.navigate_to_page()
    page.force_cleanup_all()
    yield page
    try:
        page.force_cleanup_all()
    except Exception:
        pass


# ================================================================
# OVERRIDE: logged_in_driver with RHYTHMERP credentials
# (root conftest uses PACS credentials — wrong for Tax Rate)
# ================================================================

@pytest.fixture(scope="session")
def logged_in_driver(driver):
    """Driver with completed RhythmERP login session."""
    log.separator()
    log.info("LOGGING INTO RHYTHMERP (Tax Rate tests)...")
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

    yield driver


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_cs_store = CSReportStore()

_cs_store.record_issue(
    severity="High",
    module="Tax Rate",
    category="Security",
    description="SQL injection accepted in Tax Rate Name field. Input like "
                "'DROP TABLE tax;--' is accepted and stored as-is without sanitization. "
                "The value appears in the list table.",
    expected="System should reject or sanitize SQL injection payloads.",
    actual="SQL injection payload accepted and stored in database.",
    test_ref="TR-T11",
    status="Open",
)

_cs_store.record_issue(
    severity="Medium",
    module="Tax Rate",
    category="Functionality",
    description="Edit button is permanently disabled for ALL records (disabled=true). "
                "Users must use the Version button (folder icon) to create a new version "
                "of the record instead of directly editing.",
    expected="Edit button should be enabled for records that can be modified.",
    actual="Edit button disabled=true on all rows. Version button provides alternative.",
    test_ref="TR-T24",
    status="Open",
)

_cs_store.record_issue(
    severity="Low",
    module="Tax Rate",
    category="UX",
    description="No visible success SweetAlert2 popup after record creation or versioning. "
                "The form closes silently with no user feedback.",
    expected="Success alert should appear confirming the operation.",
    actual="Form closes silently after success. No alert shown.",
    test_ref="TR-T01, TR-T02",
    status="Open",
)

_cs_store.record_issue(
    severity="Info",
    module="Tax Rate",
    category="Technical",
    description="From Date and To Date inputs have name=null (no name attribute). "
                "Fields must be located via mat-label traversal instead of input[name=...].",
    expected="Date inputs should have name attributes for reliable automation.",
    actual="name=null on both date inputs. Requires mat-label based selection.",
    test_ref="TR-T16, TR-T17, TR-T18",
    status="Open",
)

_cs_store.record_issue(
    severity="Info",
    module="Tax Rate",
    category="Data Integrity",
    description="HSN Number '7133100' appears twice in the dropdown options, "
                "inherited from HSN SAC master data duplication.",
    expected="Each HSN Number should appear exactly once.",
    actual="'7133100' appears twice in HSN Number dropdown options.",
    test_ref="TR-T21",
    status="Open",
)

_cs_store.record_issue(
    severity="Medium",
    module="Tax Rate",
    category="Validation",
    description="Duplicate Tax Rate record shows generic 'Validation Failed' message "
                "instead of a specific duplicate error.",
    expected="Specific message like 'Tax Rate Name already exists'.",
    actual="Generic 'Validation Failed' for all validation errors.",
    test_ref="N/A",
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
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "reports")
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