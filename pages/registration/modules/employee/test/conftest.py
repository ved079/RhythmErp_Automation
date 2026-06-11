"""
conftest.py - Employee Screen (RhythmERP Registration)
======================================================
Session-scoped driver + login fixtures for Employee Screen tests.
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
# LOGIN CREDENTIALS — Employee Screen
# ================================================================
EMP_LOGIN_EMAIL = "user@admin.com"
EMP_LOGIN_PASSWORD = "Tenant@123456789"
EMP_LOGIN_FACILITY_INDEX = 0


# ================================================================
# PYTEST MARKERS REGISTRATION
# ================================================================

def pytest_configure(config):
    """Register custom test markers for categorized test execution."""
    config.addinivalue_line(
        "markers", "api: API creation and payload tests"
    )
    config.addinivalue_line(
        "markers", "validation: Field validation boundary tests"
    )
    config.addinivalue_line(
        "markers", "schema: Schema and structure verification tests"
    )
    config.addinivalue_line(
        "markers", "ui: Selenium browser UI tests"
    )
    config.addinivalue_line(
        "markers", "performance: Speed and benchmark tests"
    )
    config.addinivalue_line(
        "markers", "hybrid: API+UI cross-verification tests"
    )
    config.addinivalue_line(
        "markers", "regression: Regression test suite"
    )
    config.addinivalue_line(
        "markers", "bug: Test documenting a known bug"
    )


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Employee Tests)...")
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
    log.info("LOGGING INTO RHYTHMERP (Employee Screen)...")
    log.separator()

    login_page = LoginPage(driver)

    log.info("Navigating to: " + str(RHYTHMERP_LOGIN_URL))
    driver.get(RHYTHMERP_LOGIN_URL)
    login_page.wait_seconds(2)

    log.step(1, "Entering email: " + EMP_LOGIN_EMAIL)
    login_page.enter_email(EMP_LOGIN_EMAIL)

    log.step(2, "Entering password")
    login_page.enter_password(EMP_LOGIN_PASSWORD)

    login_page._dismiss_tenant_dropdown()

    log.step(3, "Clicking Login button")
    login_page.click_login()
    login_page.wait_seconds(3)
    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture
def emp_page(logged_in_driver):
    """Employee page object — fresh navigation for each test."""
    from pages.registration.modules.employee.employee_page import EmployeePage
    page = EmployeePage(logged_in_driver)
    page.navigate_to_page()
    yield page


@pytest.fixture(scope="session")
def emp_api():
    """EmployeeAPIUtils — authenticated API client + cleanup tracker.

    Session-scoped so the tracker accumulates all created IDs across
    the entire test session. Cleanup report is generated at session end.
    """
    from common.erp_api_client import RhythmERPAPIClient
    from pages.registration.modules.employee.utils.api_employee_utils import EmployeeAPIUtils
    from pages.registration.modules.employee.utils.employee_cleanup import CleanupTracker

    tracker = CleanupTracker()
    client = RhythmERPAPIClient()

    # Authenticate — try token first, then login
    token = os.environ.get("ERP_TOKEN", "").strip()
    tenant_id = os.environ.get("ERP_TENANT_ID", "681")

    if token:
        client.login_from_browser(token=token, tenant_id=tenant_id)
    else:
        try:
            client.login()
        except Exception:
            pytest.skip("No ERP token available. Set ERP_TOKEN env var.")

    # Verify auth works
    from pages.registration.modules.employee.api.endpoints import SCREEN_NAME
    result = client.list_entries(SCREEN_NAME, page=1, page_size=1)
    if not result:
        pytest.skip("ERP authentication failed. Check token/credentials.")

    api = EmployeeAPIUtils(api_client=client, tracker=tracker)

    yield api

    # Generate cleanup report at session end
    if tracker.count > 0:
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "reports", "cleanup"
        )
        try:
            paths = tracker.generate_reports(output_dir=output_dir)
            if paths:
                log.info(f"[EmployeeAPI] Cleanup report generated: {paths}")
        except Exception as e:
            log.warning(f"[EmployeeAPI] Cleanup report generation failed: {e}")

    client.close()


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_emp_store = CSReportStore()


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
    _emp_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_emp_store)
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
        _emp_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _emp_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _emp_store.results, output_dir, issues=_emp_store.known_issues
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
