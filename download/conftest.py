"""
conftest.py - Farmer Screen (RhythmERP)
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
    log.info("LAUNCHING BROWSER (RhythmERP - Farmer Tests)...")
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

    log.step(4, "Clicking Login button (JS click)")
    login_page.click_login()
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture
def fr_page(logged_in_driver):
    """Farmer page object — fresh navigation for each test."""
    from pages.registration.modules.farmer.farmer_page import FarmerPage
    page = FarmerPage(logged_in_driver)
    page.navigate_to_page()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_fr_store = CSReportStore()

# ---- Farmer Known Bugs ----

# BUG-F01 (HIGH): No Of Owner required but no asterisk shown
_fr_store.record_issue(
    severity="High",
    module="Farmer",
    category="Missing Validation Indicator",
    description="No Of Owner field in Land Details is required but shows no asterisk (*) "
                "indicator. The field appears optional, but clicking Next with it empty "
                "produces a red border validation error.",
    expected="Asterisk (*) should be displayed next to 'No Of Owner' label to indicate "
             "it is a required field.",
    actual="No asterisk shown. Red border appears only after clicking Next.",
    test_ref="FR-B01",
    status="Confirmed",
)

# BUG-F02 (HIGH): Deselect+Reselect farmer category freezes Next/Back
_fr_store.record_issue(
    severity="High",
    module="Farmer",
    category="UI Freeze",
    description="When a farmer category is selected, all required fields filled, and then "
                "the category is unselected and reselected, the Next and Back stepper buttons "
                "become completely unresponsive. Must click on stepper header tabs to unfreeze.",
    expected="Next and Back buttons should remain functional after category changes.",
    actual="Next/Back buttons freeze completely. Only workaround is clicking stepper headers.",
    test_ref="FR-B02",
    status="Confirmed",
)

# BUG-F03 (MEDIUM): Farmer Name accepts special characters
_fr_store.record_issue(
    severity="Medium",
    module="Farmer",
    category="Missing Validation",
    description="Farmer Name field accepts unsupported special characters (e.g., Rahul@@, "
                "Amit###). Names should be restricted to valid characters.",
    expected="System should restrict unsupported special characters in Farmer Name.",
    actual="Special characters are accepted without validation error.",
    test_ref="FR-B03",
    status="Confirmed",
)

# BUG-F04 (MEDIUM): Email rejects uppercase letters
_fr_store.record_issue(
    severity="Medium",
    module="Farmer",
    category="Incorrect Validation",
    description="Email field rejects email addresses containing uppercase letters. "
                "Uppercase letters are valid in email addresses per RFC 5321.",
    expected="System should accept uppercase letters in email or auto-convert to lowercase.",
    actual="Validation error shown for uppercase letters in email.",
    test_ref="FR-B04",
    status="Confirmed",
)

# BUG-F05 (MEDIUM): Farmer Category placeholder selectable
_fr_store.record_issue(
    severity="Medium",
    module="Farmer",
    category="Placeholder Selectable",
    description="The Farmer Category dropdown allows selecting the placeholder option "
                "'Select Farmer Category' as a valid selection. This allows saving a farmer "
                "without an actual category.",
    expected="Placeholder option should not be selectable.",
    actual="Placeholder is selectable and can be saved.",
    test_ref="FR-B05",
    status="Confirmed",
)

# BUG-F06 (MEDIUM): Amount fields accept 0 and . prefix
_fr_store.record_issue(
    severity="Medium",
    module="Farmer",
    category="Missing Validation",
    description="Amount input fields (Exact Amount, Sanctioned Amount, Present Outstanding "
                "Amount) accept values starting with 0 or decimal point (e.g., 0, .50, 000).",
    expected="Amount values should start with at least 1.",
    actual="Values starting with 0 or . are accepted and saved.",
    test_ref="FR-B06",
    status="Confirmed",
)

# BUG-F07 (LOW): Source of Income shows Dairy twice
_fr_store.record_issue(
    severity="Low",
    module="Farmer",
    category="Dropdown Duplication",
    description="Source of Income dropdown shows 'Dairy' option twice.",
    expected="Dropdown should show unique options only.",
    actual="'Dairy' appears twice in the dropdown.",
    test_ref="FR-B07",
    status="Confirmed",
)

# BUG-F08 (LOW): Edit mode missing Land/Crop/KYC tabs
_fr_store.record_issue(
    severity="Low",
    module="Farmer",
    category="Missing Functionality",
    description="In Edit mode, the stepper shows only 10 tabs instead of 13. "
                "Land Details, Crop Details, and KYC Details are missing in Edit mode "
                "even when Borrower Farmer is selected.",
    expected="All 13 tabs should be visible in Edit mode matching Create mode.",
    actual="Only 10 tabs shown. Land Details, Crop Details, KYC Details are missing.",
    test_ref="FR-B08",
    status="Suspected",
)

# BUG-F09 (LOW): Character count indicator disappears on validation
_fr_store.record_issue(
    severity="Low",
    module="Farmer",
    category="UI Bug",
    description="Character count indicator (e.g., 19 / 255) disappears when a validation "
                "error is triggered in input fields.",
    expected="Character count indicator should remain visible during validation errors.",
    actual="Character count indicator disappears during validation error state.",
    test_ref="FR-B09",
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
    _fr_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_fr_store)
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
        _fr_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _fr_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _fr_store.results, output_dir, issues=_fr_store.known_issues
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
