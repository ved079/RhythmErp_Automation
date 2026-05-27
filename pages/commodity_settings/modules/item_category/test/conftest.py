"""
conftest.py - Item Attribute 1-5 (RhythmERP)
Fixtures, hooks, and bug registry for Item Attribute automation tests.
Uses parameterized fixture for all 5 screens.
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
    log.info("LAUNCHING BROWSER (RhythmERP - Item Attribute Tests)...")
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

    log.step(3, "Selecting facility (Agdi - index 0)")
#     login_page.select_facility_by_index(index=0)

    login_page.wait_seconds(1)

    log.step(4, "Clicking Login button")
    login_page.click_login()
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)
    log.info("RhythmERP login successful!")

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture
def ia_page(logged_in_driver, attr_num):
    """Item Attribute page object - fresh navigation for each test.
    Parameterized by attr_num (1-5) from @pytest.mark.parametrize.
    """
    from pages.commodity_settings.modules.item_attribute.item_attribute_page import (
        ItemAttributePage,
    )
    page = ItemAttributePage(logged_in_driver, attr_num=attr_num)
    page.navigate_to_page()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_ia_store = CSReportStore()

# ---- Item Attribute Known Issues ----

# BUG-001 (HIGH): Duplicate Names allowed
_ia_store.record_issue(
    severity="High",
    module="Item Attribute",
    category="Data Integrity",
    description="Duplicate attribute Names are allowed in the system. "
                "Two or more attributes with identical Names can exist "
                "with no warning or rejection.",
    expected="System should show a validation error like 'Name already exists' "
             "and keep the form open for correction.",
    actual="Duplicate Name is accepted and saved without any warning.",
    test_ref="IA-D01",
    status="Open",
)

# BUG-002 (HIGH): Browser-clicked mat-select values don't register in Angular
_ia_store.record_issue(
    severity="High",
    module="Item Attribute",
    category="Automation / Framework",
    description="When browser-clicking mat-select dropdown options, the value "
                "does not register in Angular's reactive form model. This causes "
                "'Validation Failed' errors on Submit even though the UI appears "
                "to show the selected value. Fix: Must use JS value-setter + "
                "dispatchEvent pattern for all dropdown selections.",
    expected="Standard Selenium .click() on mat-select options should update "
             "Angular's reactive form model.",
    actual="Browser-clicked options display correctly in UI but Angular form "
           "model does not recognize the selection, causing validation failures.",
    test_ref="All IA1 tests with Base UOM dropdown",
    status="Open",
)

# BUG-003 (MEDIUM): History popup shows "No data available"
_ia_store.record_issue(
    severity="Medium",
    module="Item Attribute",
    category="Functionality",
    description="History popup shows 'No data available' even for records "
                "that were just created. The history tracking may not be "
                "functional for Item Attribute screens.",
    expected="History popup should show at least the creation record.",
    actual="History popup shows 'No data available'.",
    test_ref="IA-H01",
    status="Open",
)

# BUG-004 (HIGH): No maxlength on Name and Description fields
_ia_store.record_issue(
    severity="High",
    module="Item Attribute",
    category="Validation",
    description="No maxlength attribute on Name or Description input fields. "
                "Names of 256+ characters are accepted by the UI with no "
                "client-side validation or warning. The server then rejects "
                "the record with a generic 'Failed to save record' message. "
                "Name limit is 255 chars; Description limit is also 255 chars.",
    expected="System should enforce maxlength=255 on Name and Description inputs, "
             "or show inline validation like 'Name must be 255 characters or less' "
             "before the user submits the form.",
    actual="No maxlength constraint. 256+ char names are accepted by UI, "
           "rejected by server with no specific error message.",
    test_ref="IA-C08",
    status="Open",
)

# BUG-005 (MEDIUM): Generic 'Failed to save record' message on length violation
_ia_store.record_issue(
    severity="Medium",
    module="Item Attribute",
    category="UX / Validation",
    description="When Name or Description exceeds 255 characters, the server "
                "returns a generic 'Failed to save record' popup instead of a "
                "specific message like 'Name exceeds maximum length of 255 "
                "characters'. The user has no indication which field caused "
                "the failure or what the limit is.",
    expected="System should show a specific error message indicating which "
             "field exceeded the length limit and what the maximum is, e.g. "
             "'Name must be 255 characters or less'.",
    actual="Generic 'Failed to save record' popup with no field-specific "
           "information. User cannot determine the cause of the failure.",
    test_ref="IA-C08",
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
    _ia_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_ia_store)
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
        _ia_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _ia_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _ia_store.results, output_dir, issues=_ia_store.known_issues
        )
        print("")
        print("=" * 60)
        print("  ITEM ATTRIBUTE REPORT GENERATED: " + filepath)
        print("=" * 60)
    except Exception:
        import traceback as tb
        tb.print_exc()
        print("")
        print("  [WARNING] Report generation failed (see traceback above)")

