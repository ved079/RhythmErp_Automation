"""
conftest.py - Supplier Screen (RhythmERP)
==========================================
Session-scoped driver + login fixtures for Supplier Screen tests.

IMPORTANT: Uses DIFFERENT login credentials than other screens!
  Email:    Rular@admin.com
  Password: Rular@12345678
  Facility: RuralLife Producer Company (index 0)
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
# LOGIN CREDENTIALS — Supplier Screen (DIFFERENT from other screens!)
# ================================================================
SP_LOGIN_EMAIL = "Rular@admin.com"
SP_LOGIN_PASSWORD = "Rular@12345678"
SP_LOGIN_FACILITY_INDEX = 0  # RuralLife Producer Company


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Supplier Tests)...")
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
    """Driver with completed RhythmERP login session.
    Uses Rular@admin.com / Rular@12345678 / RuralLife Producer Company.
    """
    log.separator()
    log.info("LOGGING INTO RHYTHMERP (Supplier Screen)...")
    log.separator()

    login_page = LoginPage(driver)

    log.info("Navigating to: " + str(RHYTHMERP_LOGIN_URL))
    driver.get(RHYTHMERP_LOGIN_URL)
    login_page.wait_seconds(2)

    log.step(1, "Entering email: " + SP_LOGIN_EMAIL)
    login_page.enter_email(SP_LOGIN_EMAIL)

    log.step(2, "Entering password")
    login_page.enter_password(SP_LOGIN_PASSWORD)

    log.step(3, f"Selecting facility (index {SP_LOGIN_FACILITY_INDEX} — RuralLife Producer Company)")
    login_page.select_facility_by_index(index=SP_LOGIN_FACILITY_INDEX)

    login_page.wait_seconds(1)

    log.step(4, "Clicking Login button")
    login_page.click_login()
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful (Rular@admin)!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture
def sp_page(logged_in_driver):
    """Supplier page object — fresh navigation for each test."""
    from pages.dynamic_screens.modules.supplier.supplier_page import (
        SupplierPage,
    )
    page = SupplierPage(logged_in_driver)
    page.navigate_to_page()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_sp_store = CSReportStore()

# ---- Supplier Known Issues ----

# BUG-001 (HIGH): Company Name accepts special characters
_sp_store.record_issue(
    severity="High",
    module="Supplier",
    category="Validation",
    description="Company Name accepts special characters and numbers without any validation. "
                "Characters like @#$%^&* are accepted and saved successfully.",
    expected="Should restrict special characters and show validation error.",
    actual="CONFIRMED: 'ABC@@ Traders', 'ds&^%##%' saved successfully.",
    test_ref="SP-C04, SP-C05, SP-C06",
    status="Confirmed",
)

# BUG-002 (MEDIUM): No email format validation
_sp_store.record_issue(
    severity="Medium",
    module="Supplier",
    category="Validation",
    description="No email format validation. Invalid emails like 'notanemail' are accepted "
                "without any error on blur or submit.",
    expected="Should validate email format and show inline error.",
    actual="Any text accepted without validation.",
    test_ref="SP-C09",
    status="Confirmed",
)

# BUG-003 (LOW): Phone Number spinner controls
_sp_store.record_issue(
    severity="Low",
    module="Supplier",
    category="UI Bug",
    description="Phone Number field shows increase/decrease spinner controls (up/down arrows) "
                "because the input type is 'number' instead of 'tel' or 'text'.",
    expected="Should be type=tel or type=text with no spinner controls.",
    actual="Spinner controls visible — type=number on input.",
    test_ref="SP-P06",
    status="Confirmed",
)

# BUG-004 (MEDIUM): No PAN format validation
_sp_store.record_issue(
    severity="Medium",
    module="Supplier",
    category="Validation",
    description="No PAN format validation. PAN should follow Indian format: "
                "5 letters + 4 digits + 1 letter (e.g., ABCDE1234F). Any text is accepted.",
    expected="Should validate PAN format with regex pattern.",
    actual="Any text accepted in PAN field.",
    test_ref="SP-C10",
    status="Confirmed",
)

# BUG-005 (HIGH): No Update button in Edit mode
_sp_store.record_issue(
    severity="High",
    module="Supplier",
    category="Functionality",
    description="No Update button in Edit mode. Only Cancel button is visible in popup-footer. "
                "User cannot save edits — Edit mode is non-functional for saving changes.",
    expected="Update button should appear in edit mode popup-footer right div.",
    actual="Only Cancel button present. Edit mode is non-functional for saving changes.",
    test_ref="SP-E01",
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
    _sp_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_sp_store)
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
        _sp_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _sp_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _sp_store.results, output_dir, issues=_sp_store.known_issues
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
