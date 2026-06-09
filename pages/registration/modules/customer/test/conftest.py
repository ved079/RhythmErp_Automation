"""
conftest.py - Customer Screen (RhythmERP Registration)
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
# PYTEST MARKERS REGISTRATION
# ================================================================

def pytest_configure(config):
    """Register custom markers for test categorization."""
    config.addinivalue_line(
        "markers", "smoke: Critical happy-path tests — must pass for build acceptance"
    )
    config.addinivalue_line(
        "markers", "sanity: Core feature validation tests — key functionality checks"
    )
    config.addinivalue_line(
        "markers", "regression: Full suite — all tests for regression coverage"
    )
    config.addinivalue_line(
        "markers", "bug: Tests targeting known/confirmed bugs (often xfail)"
    )
    config.addinivalue_line(
        "markers", "ui: Popup, dialog, form UI behavior and visual checks"
    )


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Customer Tests)...")
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

    # log.step(3, "Selecting facility (blank - first option)")
    # login_page.select_facility_by_index(index=0)

    login_page.wait_seconds(5)

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
def cu_page(logged_in_driver):
    """Customer page object — fresh navigation for each test."""
    from pages.registration.modules.customer.customer_page import (
        CustomerPage,
    )
    page = CustomerPage(logged_in_driver)
    page.navigate_to_page()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_cu_store = CSReportStore()

# ---- Customer Known Issues ----

# BUG-001 (CRITICAL): Browser-clicked mat-select does NOT update Angular form model
_cu_store.record_issue(
    severity="Critical",
    module="Customer",
    category="Automation",
    description="Browser-clicked mat-select options do NOT update Angular reactive form model. "
                "Submit still fires 'Validation Failed' even with all fields filled via UI clicks. "
                "Must use JS value-setter + dispatchEvent pattern for all dropdown selections.",
    expected="Selenium clicks on mat-select options should update form state.",
    actual="CONFIRMED: Angular form model not synced. Need JS workaround.",
    test_ref="ALL",
    status="Confirmed",
)

# BUG-002 (MEDIUM): Stepper allows advancing with empty required fields
_cu_store.record_issue(
    severity="Medium",
    module="Customer",
    category="Validation",
    description="The horizontal stepper allows clicking Next to advance to the next step "
                "even when required fields on the current step are empty. No per-step "
                "validation is performed — validation only triggers on Submit.",
    expected="Stepper should block advancement when required fields are empty.",
    actual="CONFIRMED: Next button always works regardless of field state.",
    test_ref="CU-C15",
    status="Confirmed",
)

# BUG-003 (MEDIUM): Pin Code header shows asterisk but field is NOT required
_cu_store.record_issue(
    severity="Medium",
    module="Customer",
    category="UI Bug",
    description="The Address grid column header shows 'Pin Code *' with an asterisk "
                "suggesting the field is required, but the HTML input element has "
                "required=false and the form does not validate it as required on submit.",
    expected="Column header and field required attribute should match.",
    actual="CONFIRMED: Header says required, but field is optional.",
    test_ref="CU-C12",
    status="Confirmed",
)

# BUG-004 (RESOLVED): Bank Name/Branch/Holder/Number headers show asterisk — NOW REQUIRED
# NOTE: As of the latest ERP update, Account Type and Bank Proof dropdowns are
# also required=True in the UI. The header asterisks for Bank Name, Branch,
# Account Holder Name, Account Number are still mismatched (header says required,
# input attribute says optional), but Account Type and Bank Proof are now
# genuinely required.
_cu_store.record_issue(
    severity="Low",
    module="Customer",
    category="UI Bug",
    description="Bank Details grid column headers show asterisks for Bank Name, Branch, "
                "Account Holder Name, and Account Number. The HTML input elements still "
                "have required=false, but Account Type and Bank Proof dropdowns are now "
                "required=True in the ERP UI. The text input header/input mismatch remains "
                "but is a low-priority cosmetic issue.",
    expected="Column headers and field required attributes should match.",
    actual="PARTIALLY RESOLVED: Account Type & Bank Proof now required. "
           "Text inputs (Bank Name, Branch, etc.) header/input mismatch remains.",
    test_ref="CU-C13",
    status="Partially Resolved",
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
    _cu_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_cu_store)
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
        _cu_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _cu_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _cu_store.results, output_dir, issues=_cu_store.known_issues
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
