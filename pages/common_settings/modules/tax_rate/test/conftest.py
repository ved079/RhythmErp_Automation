"""
conftest.py - Tax Rate Common Settings (RhythmERP)
"""

import os
import sys
import logging
import pytest
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from common.browser_utils import get_driver
from pages.login_screens.Login_Screens_.login_page import LoginPage
from common.screenshot_broadcast import start as start_screenshot_broadcast, stop as stop_screenshot_broadcast
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD
from pages.common_settings.cs_report_generator import CSReportStore, generate_cs_report


def pytest_configure(config):
    """Register custom pytest markers for Tax Rate tests."""
    config.addinivalue_line(
        "markers", "smoke: Critical path tests — must pass for build acceptance (7 tests)"
    )
    config.addinivalue_line(
        "markers", "sanity: Full functional validation of every test case (20 tests)"
    )
    config.addinivalue_line(
        "markers", "regression: Complete regression suite covering all 20 tests"
    )
    config.addinivalue_line(
        "markers", "bug: Tests verifying known open bugs (5 tests)"
    )
    config.addinivalue_line(
        "markers", "ui: UI/popup/form/table/visual behaviour tests (12 tests)"
    )


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Tax Rate Tests)...")
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
def tr_page(logged_in_driver):
    """Tax Rate page object — fresh navigation for each test.

    Setup:
      1. Hard-refresh the browser to clear leftover state.
      2. Navigate to the Tax Rate screen.
      3. If navigation fails, do one more hard-refresh + retry.

    Teardown:
      Hard-refresh after every test so the next test always starts
      from a clean browser state.
    """
    from pages.common_settings.modules.tax_rate.tax_rate_page import TaxRatePage

    # --- Pre-test hard refresh to wipe leftover state ---
    try:
        logged_in_driver.refresh()
        time.sleep(2)
    except Exception as e:
        log.warning(f"Pre-test refresh failed (non-fatal): {e}")

    page = TaxRatePage(logged_in_driver)

    # --- Navigate with one retry ---
    try:
        page.navigate_to_page()
    except Exception as first_err:
        log.warning(
            f"First navigation attempt failed: {first_err!r} — "
            "retrying after hard refresh..."
        )
        try:
            logged_in_driver.refresh()
            time.sleep(3)
            page.navigate_to_page()
        except Exception as second_err:
            log.error(f"Navigation failed after retry: {second_err!r}")
            raise

    yield page

    # --- Post-test teardown: hard refresh + settle ---
    try:
        logged_in_driver.refresh()
        time.sleep(2)
        log.info("Post-test hard refresh complete")
    except Exception as e:
        log.warning(f"Post-test refresh failed (non-fatal): {e}")


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_cs_store = CSReportStore()

# ---- Tax Rate Known Issues ----
_cs_store.record_issue(
    severity="High",
    module="Tax Rate",
    category="UX",
    description="No success SweetAlert after successful record creation. "
                "Form closes silently without any confirmation message.",
    expected="System should show 'Your record has been added successfully!' "
             "SweetAlert with OK button after successful create/update.",
    actual="Form closes silently after Submit/Update. No success toast or "
           "SweetAlert is displayed. User cannot confirm the save operation.",
    test_ref="T01-T03",
    status="Open",
)

_cs_store.record_issue(
    severity="High",
    module="Tax Rate",
    category="Bug",
    description="Edit button is disabled for all rows in the Tax Rate listing. "
                "Users can only use 'Version' to create a new version.",
    expected="Edit button should allow editing the existing record.",
    actual="Edit button is always disabled. Users must use 'Version' instead.",
    test_ref="T24",
    status="Open",
)

_cs_store.record_issue(
    severity="Medium",
    module="Tax Rate",
    category="Validation",
    description="Negative and zero tax rate values are accepted in sub-table "
                "without client-side validation.",
    expected="System should validate tax rate values are positive.",
    actual="Negative and zero values are accepted without warning.",
    test_ref="T13-T14",
    status="Open",
)

_cs_store.record_issue(
    severity="Low",
    module="Tax Rate",
    category="Validation",
    description="SQL injection strings are accepted in Tax Rate Name field.",
    expected="System should sanitize or reject SQL-like input.",
    actual="SQL injection strings like ' OR 1=1; --' are accepted.",
    test_ref="T11",
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
    """Capture test result (pass/fail) and finalise for report."""
    outcome = yield
    report  = outcome.get_result()
    if call.when == "call":
        if report.passed:
            status = "PASSED"
            error  = ""
        elif report.failed:
            status = "FAILED"
            error  = str(report.longrepr) if report.longrepr else ""
        else:
            status = "SKIPPED"
            error  = ""
        _cs_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _cs_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _cs_store.results, output_dir, issues=_cs_store.known_issues
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
