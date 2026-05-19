"""
conftest.py - Commodity Quality Parameter (RhythmERP)
-----------------------------------------------------
Pytest fixtures and report generation hooks for CQP automation.

Location: Commodity Settings > Commodity Master > Commodity Quality Parameter
URL:      /#/dynamic-screens/Commodity%20Quality%20Parameter

Known Issues recorded in CSReportStore:
  BUG-001 : Version & History buttons mis-classed (both use tbl-fav-edit)
  BUG-002 : Duplicate Item Names in dropdown (no dedup)
  BUG-003 : Dates displayed as raw ISO strings
  BUG-004 : History popup always shows "No data available"
  BUG-005 : To Date auto-populates sentinel 30/12/2099
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
    log.info("LAUNCHING BROWSER (RhythmERP - CQP Tests)...")
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
def cqp_page(logged_in_driver):
    """CQP page object — fresh navigation for each test."""
    from pages.commodity_settings.modules.commodity_quality_parameter.commodity_quality_parameter_page import (
        CommodityQualityParameterPage,
    )
    page = CommodityQualityParameterPage(logged_in_driver)
    page.navigate_to_page()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_cqp_store = CSReportStore()

# ---- CQP Known Issues ----

# BUG-001: Version & History buttons mis-classed
_cqp_store.record_issue(
    severity="Medium",
    module="Commodity Quality Parameter",
    category="CSS Class",
    description="Version (folder-plus) and History (clock) icons both use "
                "CSS class 'tbl-fav-edit' instead of distinct classes. "
                "Only the View button has a unique class (tbl-fav-eye).",
    expected="Each action button type should have its own distinct CSS class.",
    actual="Version and History share 'tbl-fav-edit' with Edit button.",
    test_ref="CQP-C10, CQP-H01",
    status="Open",
)

# BUG-002: Duplicate Item Names in dropdown
_cqp_store.record_issue(
    severity="High",
    module="Commodity Quality Parameter",
    category="Data Integrity",
    description="The Item Name dropdown contains duplicate entries "
                "(e.g., 'Soyabean' appears 4+ times). No deduplication is performed.",
    expected="Dropdown should show unique Item Names only.",
    actual="Multiple identical Item Name entries visible in dropdown.",
    test_ref="CQP-D01",
    status="Open",
)

# BUG-003: Dates displayed as raw ISO strings
_cqp_store.record_issue(
    severity="Medium",
    module="Commodity Quality Parameter",
    category="UI/UX",
    description="From Date and To Date columns show raw ISO timestamps "
                "(e.g., '2026-05-18T17:57:17.975438Z') instead of "
                "human-readable formatted dates (e.g., '18/05/2026').",
    expected="Dates should be displayed in DD/MM/YYYY or similar readable format.",
    actual="Dates displayed as raw ISO 8601 timestamp strings.",
    test_ref="CQP-P02, CQP-P04, CQP-P05",
    status="Open",
)

# BUG-004: History always empty
_cqp_store.record_issue(
    severity="High",
    module="Commodity Quality Parameter",
    category="Data Integrity",
    description="The History popup always shows 'No data available' even for "
                "Effective records. History tracking may not be properly "
                "implemented for this screen.",
    expected="History popup should show version history for records with changes.",
    actual="History popup is always empty regardless of record status.",
    test_ref="CQP-H02",
    status="Open",
)

# BUG-005: To Date auto-populates sentinel
_cqp_store.record_issue(
    severity="Low",
    module="Commodity Quality Parameter",
    category="UI/UX",
    description="After selecting an Item Name, the To Date field auto-fills "
                "to 30/12/2099 which is a sentinel value for 'indefinite'. "
                "This is not clearly communicated to the user.",
    expected="Either leave To Date empty for user input, or show a tooltip/label "
             "explaining the sentinel value.",
    actual="To Date auto-populates to 30/12/2099 without explanation.",
    test_ref="CQP-F01",
    status="Open",
)

# BUG-008: Detail grid input name attrs have trailing tab characters
_cqp_store.record_issue(
    severity="High",
    module="Commodity Quality Parameter",
    category="Data Integrity",
    description="Detail grid text inputs (Min Quality Value, Max Quality Value, "
                "Multiplier) have trailing tab characters in their name attribute. "
                "E.g. name=\"Min Quality Value\\t\" instead of name=\"Min Quality Value\". "
                "This causes CSS attribute selectors like input[name='Min Quality Value'] "
                "to FAIL — the selector requires an exact match but the actual name "
                "has an invisible tab character appended.",
    expected="Input name attributes should not have trailing whitespace/tabs.",
    actual="name attr includes trailing tab character (e.g., \"Min Quality Value\\t\").",
    test_ref="CQP-C02, CQP-C06, CQP-C07",
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
    _cqp_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_cqp_store)
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
        _cqp_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _cqp_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _cqp_store.results, output_dir, issues=_cqp_store.known_issues
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

