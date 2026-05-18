"""
conftest.py - Item Master Commodity Settings (RhythmERP)
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
    log.info("LAUNCHING BROWSER (RhythmERP - Item Master Tests)...")
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
def im_page(logged_in_driver):
    """Item Master page object — fresh navigation for each test."""
    from pages.commodity_settings.modules.item_master.item_master_page import (
        ItemMasterPage,
    )
    page = ItemMasterPage(logged_in_driver)
    page.navigate_to_page()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_im_store = CSReportStore()

# ---- Item Master Known Issues ----
# These will be populated/updated after running tests and observing
# actual ERP behavior. Placeholder entries below:

# BUG-001 (HIGH): [RETRACTED] Spaces-only Item Name — not applicable
# Item Name is READONLY and auto-generated from attributes.
# Cannot type spaces into it. This bug is not applicable.
# _im_store.record_issue(...) — REMOVED, not applicable per V2 exploration

# BUG-002 (HIGH): Duplicate Item Names ALLOWED — CONFIRMED 2026-05-18
# Table has two "Soyabean" rows both Active. No uniqueness validation on Item Name.
_im_store.record_issue(
    severity="High",
    module="Item Master",
    category="Data Integrity",
    description="Duplicate Item Names are ALLOWED in the system. "
                "Two or more items with identical Item Name can exist with no warning. "
                "Confirmed via browser exploration: two 'Soyabean' rows both Active.",
    expected="System should show a validation error like 'Item Name already exists' "
             "and keep the form open for correction.",
    actual="CONFIRMED: No uniqueness validation. Duplicate names are accepted.",
    test_ref="IM-C04",
    status="Confirmed",
)

# BUG-003 (MEDIUM): [RETRACTED] No maxlength on Item Name — not applicable
# Item Name is READONLY and auto-generated. Maxlength testing not possible.
# _im_store.record_issue(...) — REMOVED, not applicable per V2 exploration

# BUG-004 (MEDIUM): Negative Base Uom Conversion accepted — needs verification
_im_store.record_issue(
    severity="Medium",
    module="Item Master",
    category="Validation",
    description="Negative values may be accepted in the Base Uom Conversion field. "
                "A conversion factor should logically be a positive number.",
    expected="System should reject negative values with a validation error.",
    actual="To be confirmed during test execution.",
    test_ref="IM-C08",
    status="Suspected",
)

# BUG-006 (MEDIUM): Dropdown option duplication — CONFIRMED 2026-05-18
_im_store.record_issue(
    severity="Medium",
    module="Item Master",
    category="UI Bug",
    description="Item Category and Item Group dropdowns show options TWICE. "
                "e.g., Pulses, Oilseeds, Grains appear twice each in Category. "
                "Raw Material, Finished Goods, Semi Finished appear twice in Group.",
    expected="Dropdowns should show unique options only.",
    actual="CONFIRMED: Options duplicated in Category and Group dropdowns.",
    test_ref="IM-C11",
    status="Confirmed",
)

# BUG-007 (CRITICAL): Angular form model not synced with browser clicks
_im_store.record_issue(
    severity="Critical",
    module="Item Master",
    category="Automation",
    description="Browser-clicked mat-select options do NOT update Angular reactive form model. "
                "Submit still fires 'Validation Failed' even with all fields filled via UI clicks. "
                "Must use JS value-setter + dispatchEvent pattern for all dropdown selections.",
    expected="Selenium/Playwright clicks on mat-select options should update form state.",
    actual="CONFIRMED: Angular form model not synced. Need JS workaround.",
    test_ref="ALL",
    status="Confirmed",
)

# BUG-005 (LOW): No Delete option
_im_store.record_issue(
    severity="Low",
    module="Item Master",
    category="Functionality",
    description="No Delete option exists anywhere on the Item Master "
                "screen — no Delete button per row, no Delete in More menu, "
                "no Delete in the edit popup.",
    expected="Users should be able to delete an Item Master record via a Delete "
             "button on the row or in the edit popup.",
    actual="No Delete functionality available. Records cannot be removed.",
    test_ref="IM-P02",
    status="Suspected",
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
    _im_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_im_store)
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
        _im_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _im_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _im_store.results, output_dir, issues=_im_store.known_issues
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
