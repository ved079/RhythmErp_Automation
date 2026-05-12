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
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD
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
def season_page(logged_in_driver):
    """Season page object — fresh navigation for each test."""
    from pages.common_settings.modules.season.season_page import SeasonPage
    page = SeasonPage(logged_in_driver)
    page.navigate_to_season()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_cs_store = CSReportStore()

# ---- Season Known Issues ----
_cs_store.record_issue(
    severity="High",
    module="Season",
    category="Data Integrity",
    description="Duplicate Season Name causes system to hang indefinitely with no "
                "error message or alert. The submit button appears to do nothing, "
                "no loading spinner appears, and the form stays open forever. "
                "The only way to recover is to close the popup.",
    expected="System should show a validation error like 'Season Name already exists' "
             "and keep the form open for correction.",
    actual="System hangs indefinitely. No error, no alert, no response. "
           "User must close the popup to recover.",
    test_ref="Test T5",
    status="Open",
)

_cs_store.record_issue(
    severity="High",
    module="Season",
    category="Security",
    description="SQL injection accepted and stored in Season Name field. "
                "Input like '; DROP TABLE Season-- is saved as-is and displayed "
                "in the list table without any sanitization.",
    expected="System should reject or sanitize SQL injection input.",
    actual="SQL injection payload is accepted, stored in DB, and rendered in the list view.",
    test_ref="Test T3",
    status="Open",
)

_cs_store.record_issue(
    severity="High",
    module="Season",
    category="Security",
    description="XSS script tag accepted in Name field — stored as raw HTML and "
                "visible in the list page. If any part of the UI renders HTML "
                "content, this could execute arbitrary JavaScript.",
    expected="System should reject or sanitize script tags and HTML input.",
    actual="<script>alert('xss')</script> is stored as-is and visible in the list table.",
    test_ref="Test T4",
    status="Open",
)

_cs_store.record_issue(
    severity="Low",
    module="Season",
    category="Validation",
    description="No max length restriction on Name or Description fields. "
                "Very long strings (200+ characters) are accepted without warning "
                "or character count indicator.",
    expected="System should enforce a reasonable max length with visual character count.",
    actual="Fields accept any length input with no validation or feedback.",
    test_ref="Test T10",
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

