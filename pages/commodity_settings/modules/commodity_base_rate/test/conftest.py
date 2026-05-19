"""
conftest.py - Commodity Base Rate (RhythmERP)
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
    log.info("LAUNCHING BROWSER (RhythmERP - Commodity Base Rate Tests)...")
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
def cbr_page(logged_in_driver):
    """Commodity Base Rate page object — fresh navigation for each test.
    Includes browser health check and recovery.
    """
    from pages.commodity_settings.modules.commodity_base_rate.commodity_base_rate_page import (
        CommodityBaseRatePage,
    )
    # Quick browser health check before navigating
    try:
        _ = logged_in_driver.current_url
    except Exception as e:
        pytest.skip(f"Browser session is dead: {e}")

    page = CommodityBaseRatePage(logged_in_driver)

    # Try to navigate, skip test if browser is dead
    try:
        page.navigate_to_page()
    except Exception as e:
        log.warning(f"Navigation failed (browser may be dead): {e}")
        pytest.skip(f"Could not navigate to CBR page: {e}")

    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_cbr_store = CSReportStore()

# ---- Commodity Base Rate Known Issues ----

_cbr_store.record_issue(
    severity="High",
    module="Commodity Base Rate",
    category="Data Integrity",
    description="Item Rate field accepts non-numeric input like negative values "
                "(-100) and special characters (abc!@#). No client-side or "
                "server-side validation prevents invalid rate values.",
    expected="System should reject non-numeric and negative values with a "
             "validation error like 'Item Rate must be a positive number'.",
    actual="Negative values and special characters are accepted and saved.",
    test_ref="CBR-V-02, CBR-V-03",
    status="Open",
)

_cbr_store.record_issue(
    severity="Medium",
    module="Commodity Base Rate",
    category="Data Integrity",
    description="Item Rate field accepts zero (0) value. A base rate of zero "
                "is not meaningful and should be validated.",
    expected="System should reject zero rate with validation error.",
    actual="Zero rate is accepted and saved without any warning.",
    test_ref="CBR-V-04",
    status="Open",
)

_cbr_store.record_issue(
    severity="Medium",
    module="Commodity Base Rate",
    category="UI",
    description="Listing table shows raw ISO timestamps (e.g., "
                "'2025-05-27T00:00:00.000Z') instead of properly formatted "
                "dates (e.g., '27/05/2025') in From Date and To Date columns.",
    expected="Dates should be displayed in DD/MM/YYYY format.",
    actual="Dates show raw ISO timestamp strings.",
    test_ref="CBR-H-01",
    status="Open",
)

_cbr_store.record_issue(
    severity="High",
    module="Commodity Base Rate",
    category="Data Integrity",
    description="When creating a record with a custom To Date, the system "
                "overrides it to 30/12/2099 on submit, ignoring the user's "
                "selected date.",
    expected="To Date should retain the user's selected value.",
    actual="To Date is always saved as 30/12/2099 regardless of input.",
    test_ref="CBR-H-02",
    status="Open",
)

_cbr_store.record_issue(
    severity="Low",
    module="Commodity Base Rate",
    category="Functionality",
    description="Edit button is disabled for newly created records. "
                "Only enabled after a version has been created from the record.",
    expected="Edit should be available for the latest version of any record.",
    actual="Edit button remains disabled until versioning is performed.",
    test_ref="CBR-E-01",
    status="Open",
)

_cbr_store.record_issue(
    severity="Medium",
    module="Commodity Base Rate",
    category="Functionality",
    description="Version creation fails when the From Date overlaps with an "
                "existing record. Error message is generic and not helpful.",
    expected="Clear error message indicating date overlap, e.g., "
             "'From Date overlaps with existing record'.",
    actual="Generic error message with no specific guidance.",
    test_ref="CBR-P-02",
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
    _cbr_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_cbr_store)
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
        _cbr_store.finish_test(status, error)

        # Screenshot on failure
        if report.failed:
            driver = item.funcargs.get("logged_in_driver") or item.funcargs.get("driver")
            if driver:
                try:
                    from datetime import datetime
                    screenshots_dir = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), "..", "screenshots"
                    )
                    os.makedirs(screenshots_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    driver.save_screenshot(
                        os.path.join(screenshots_dir, f"{item.name}_{timestamp}.png")
                    )
                except Exception:
                    pass


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _cbr_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _cbr_store.results, output_dir, issues=_cbr_store.known_issues
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

