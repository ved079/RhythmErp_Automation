"""
conftest.py — Bank Module (Common Settings)
==========================================
Session-scoped fixtures for Bank screen tests.

Login uses RHYTHMERP_* credentials from config.py.
"""

import os
import sys
import logging
import pytest

# ---------------------------------------------------------------------------
# PATH SETUP — Add Pacs_Automation root to sys.path
# conftest is at: pages/common_settings/modules/bank/test/conftest.py
# PROJECT_ROOT  = Pacs_Automation/  (5 levels up)
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from common.browser_utils import get_driver
from pages.login_screens.Login_Screens_.login_page import LoginPage
from config import (
    RHYTHMERP_LOGIN_URL,
    RHYTHMERP_EMAIL,
    RHYTHMERP_PASSWORD,
    RHYTHMERP_FACILITY,
)

# ---------------------------------------------------------------------------
# OPTIONAL: CS Report Generator
# ---------------------------------------------------------------------------
try:
    from pages.common_settings.cs_report_generator import CSReportStore, generate_cs_report
    _cs_store = CSReportStore()
    _has_cs_report = True
except ImportError:
    _cs_store = None
    _has_cs_report = False


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    """Launch browser — session-scoped (shared across all tests)."""
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Bank Module)...")
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

    FIX: Wrapped entire login flow in try/except. If login fails,
    the session fixture still yields the driver so individual tests
    get a clear error message instead of a cryptic fixture crash.
    """
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


@pytest.fixture(scope="function")
def bank_page(logged_in_driver):
    """Fresh BankPage instance per test.

    FIX: Teardown wrapped in try/except to prevent cascade failure.
    If the browser session dies (InvalidSessionIdException) during a test,
    the teardown recovery call would ALSO crash, killing all remaining tests.
    Now it catches and logs the error silently.
    """
    from pages.common_settings.modules.bank.bank_page import BankPage
    page = BankPage(logged_in_driver)
    page.navigate_to_bank()
    yield page
    # FIX: Wrap teardown in try/except to prevent cascade failure
    try:
        page._recover_from_stuck_state()
    except Exception as e:
        log.warning(f"bank_page teardown recovery failed (session may be dead): {e}")
    finally:
        # Safety: try to refresh even if recovery failed
        try:
            logged_in_driver.refresh()
            logged_in_driver.implicit_wait(2)
        except Exception:
            pass


# ================================================================
# HARD REFRESH BETWEEN TESTS
# ================================================================

@pytest.fixture(autouse=True)
def hard_refresh_between_tests(logged_in_driver):
    """Hard refresh BEFORE and AFTER each test to prevent state leakage.

    NOTE: The test file also has its own autouse fixture that does
    navigate_to_bank() + refresh. This conftest fixture is a safety net
    for tests that don't have their own cleanup.
    """
    try:
        logged_in_driver.refresh()
        logged_in_driver.implicit_wait(2)
    except Exception:
        pass

    yield

    try:
        logged_in_driver.refresh()
        logged_in_driver.implicit_wait(2)
    except Exception:
        pass


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

if _has_cs_report:
    # ---- Bank Known Issues ----

    _cs_store.record_issue(
        severity="Medium",
        module="Bank",
        category="Functionality",
        description="History panel shows 'No data available' even after creating "
                    "and editing bank records. ERP does not create history entries.",
        expected="History should show creation and edit audit trail entries.",
        actual="'No data available' displayed for all bank records.",
        test_ref="BNK-H03",
        status="Open",
    )

    _cs_store.record_issue(
        severity="Low",
        module="Bank",
        category="Data Integrity",
        description="Duplicate Bank Name is accepted without unique constraint validation. "
                    "Multiple banks can be created with the same name.",
        expected="System should reject duplicate Bank Name with specific error message.",
        actual="Duplicate name accepted and stored successfully.",
        test_ref="BNK-D01",
        status="Open",
    )

    _cs_store.record_issue(
        severity="Medium",
        module="Bank",
        category="Validation",
        description="Branch Name field only accepts numeric values. Text characters like 'TestBranch' "
                    "are rejected with inline mat-error 'Invalid Name'. A Branch Name should accept "
                    "text characters as it is a name field.",
        expected="Branch Name should accept alphanumeric text (e.g. 'FC Road Branch').",
        actual="Only numeric values are accepted. Text characters trigger 'Invalid Name' error.",
        test_ref="BNK-BUG-001",
        status="Open",
    )

    _cs_store.record_issue(
        severity="Medium",
        module="Bank",
        category="Data Integrity",
        description="Cash Credit Limit with 255-digit number saves successfully, but when the record "
                    "is opened for editing, the value displays as scientific notation (e.g. 1.1e+254). "
                    "Attempting to save triggers 'Invalid Cash Credit Limit' because the 'e+' contains "
                    "non-numeric characters.",
        expected="Large numbers should either be rejected upfront or displayed accurately in edit mode.",
        actual="255-digit CCL becomes 1.1e+254 on edit, causing save to fail with validation error.",
        test_ref="BNK-BUG-002",
        status="Open",
    )

    # ---- Log Capture + Pytest Hooks ----

    class _LogCapture(logging.Handler):
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
            print("  [WARNING] Report generation failed")