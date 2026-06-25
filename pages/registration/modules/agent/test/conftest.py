"""
conftest.py - Agent Registration (RhythmERP)
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
    config.addinivalue_line(
        "markers", "hybrid: API creates data + UI verifies display/behavior"
    )
    config.addinivalue_line(
        "markers", "api: API-only tests — no browser, headless validation"
    )


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Agent Tests)...")
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
def agt_page(logged_in_driver):
    """Agent page object - fresh navigation for each test."""
    from pages.registration.modules.agent.agent_page import AgentPage
    page = AgentPage(logged_in_driver)
    page.navigate_to_page()
    yield page
    try:
        page.force_close_form_popup()
    except Exception:
        pass


@pytest.fixture(scope="session")
def agt_api():
    """Authenticated Agent API utility - session scoped.
    
    Logs in once, shares the API client across all API/hybrid tests.
    Generates cleanup report at session end.
    """
    from pages.registration.modules.agent.utils.api_agent_utils import AgentAPIUtils
    from common.erp_api_client import RhythmERPAPIClient

    client = RhythmERPAPIClient()
    client.login()

    api = AgentAPIUtils(api_client=client)

    yield api

    # Session cleanup — generate cleanup report
    try:
        api.tracker.generate_reports()
    except Exception as e:
        log.warning(f"Failed to generate cleanup report: {e}")


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_agt_store = CSReportStore()


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
    _agt_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_agt_store)
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
        _agt_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _agt_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _agt_store.results, output_dir, issues=_agt_store.known_issues
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
