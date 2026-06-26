"""
conftest.py - Season Common Settings (RhythmERP)
"""

import os
import sys
import logging
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from common.browser_utils import get_driver
from pages.login_screens.Login_Screens_.login_page import LoginPage
from common.screenshot_broadcast import start as start_screenshot_broadcast, stop as stop_screenshot_broadcast
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD, RHYTHMERP_FACILITY
from pages.common_settings.cs_report_generator import CSReportStore, generate_cs_report


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Season Tests)...")
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

    # Dismiss tenant dropdown before clicking Login (backend bug workaround)
    # The dropdown auto-appears after email entry and intercepts the Login button click
    login_page._dismiss_tenant_dropdown()
    login_page.wait_seconds(1)

    log.step(4, "Clicking Login button (double-click)")
    login_page.click_login()
    login_page.wait_seconds(3)

    # Verify login succeeded; retry once if still on login page
    if not login_page.wait_for_login_complete(timeout=15):
        log.warning("First login attempt may have failed — retrying...")
        login_page._dismiss_tenant_dropdown()
        login_page.click_login()
        login_page.wait_seconds(3)
        assert login_page.wait_for_login_complete(timeout=15), "Login failed after retry"

    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture(scope="session")
def shared_season(logged_in_driver):
    """Creates one Season record via UI once for the session.
    History appears immediately after create — no edit needed."""
    from pages.common_settings.modules.season.season_page import SeasonPage
    from pages.common_settings.modules.season.data.season_data import valid_season_name
    driver = logged_in_driver
    page = SeasonPage(driver)
    name = valid_season_name()
    page.navigate_to_season()
    page.open_add_form()
    page.enter_name(name)
    result = page.click_submit()
    assert result == "success", f"Shared season fixture create failed: {result}"
    yield name


# NOTE: No per-test season_page fixture — each test creates its own
# SeasonPage(logged_in_driver) and calls navigate_to_season() or
# hard_refresh() as needed. This matches the UOM pattern and avoids
# an unnecessary full page load for every test.


# ================================================================
# PYTEST MARKERS
# ================================================================

def pytest_configure(config):
    """Register custom pytest markers for Season module."""
    config.addinivalue_line("markers", "smoke: Core CRUD + critical path tests (4 tests)")
    config.addinivalue_line("markers", "sanity: All 18 tests — full module sanity check")
    config.addinivalue_line("markers", "regression: All 18 tests — full regression suite")
    config.addinivalue_line("markers", "bug: Known bugs — SQL injection, XSS, duplicate alert, special chars, no max length (5 tests)")
    config.addinivalue_line("markers", "ui: UI interaction tests — alerts, view mode, search, history, cancel, boundary (12 tests)")


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_cs_store = CSReportStore()


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
        _cs_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _cs_store.has_results():
        return
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
    try:
        os.makedirs(output_dir, exist_ok=True)
        filepath = generate_cs_report(_cs_store.results, output_dir,
                                       issues=_cs_store.known_issues)
        print("")
        print("=" * 60)
        print("  REPORT GENERATED: " + filepath)
        print("=" * 60)
    except Exception:
        import traceback as tb
        tb.print_exc()
        print("")
        print("  [WARNING] Report generation failed (see traceback above)")
