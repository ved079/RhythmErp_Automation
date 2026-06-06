"""
conftest.py - Error Code Mst Common Settings (RhythmERP)
UOM Gold Standard pattern:
  - Session-scoped driver + logged_in_driver
  - NO function-scoped page fixture — each test creates ErrorCodeMstPage(logged_in_driver) locally
  - This saves 5-8s per test (no full navigate_to_page + force_cleanup_all per test)
"""

import os
import sys
import logging
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from common.browser_utils import get_driver
from pages.login_screens.Login_Screens_.login_page import LoginPage
from common.screenshot_broadcast import start as start_screenshot_broadcast, stop as stop_screenshot_broadcast
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD, RHYTHMERP_FACILITY
from pages.common_settings.cs_report_generator import CSReportStore, generate_cs_report


# ================================================================
# FIXTURES — UOM Gold Standard Pattern
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Error Code Mst Tests)...")
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

    log.step(4, "Clicking Login button (double-click)")
    login_page.click_login()
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()

    # Verify login actually succeeded
    if "login" in driver.current_url.lower():
        log.error("Login did not complete — still on login page. URL: " + driver.current_url)
        raise RuntimeError("RhythmERP login failed — still on login page after wait. Check credentials in .env")

    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


# ================================================================
# PYTEST MARKERS
# ================================================================

def pytest_configure(config):
    """Register custom pytest markers for Error Code Mst module."""
    config.addinivalue_line("markers", "smoke: Core CRUD + critical path tests (4 tests)")
    config.addinivalue_line("markers", "sanity: All 22 tests — full module sanity check")
    config.addinivalue_line("markers", "regression: All 22 tests — full regression suite")
    config.addinivalue_line("markers", "bug: Known bugs — duplicate create/edit accepted, no max-length on Code (3 tests)")
    config.addinivalue_line("markers", "ui: UI interaction tests — alerts, view mode, edit mode, history popup, table columns (18 tests)")


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_cs_store = CSReportStore()

# ---- Error Code Mst Known Issues ----
_cs_store.record_issue(
    severity="Low",
    module="Error Code Mst",
    category="UX",
    description="Dropdown selection sometimes does not register on first click. "
                "The mat-select panel opens but clicking an option may not update "
                "the displayed value. Built-in retry logic (3 attempts) handles this.",
    expected="Option should be selected and displayed on first click.",
    actual="Sometimes requires clicking the option twice for it to register.",
    test_ref="C01, C04, C05",
    status="Open",
)

_cs_store.record_issue(
    severity="Medium",
    module="Error Code Mst",
    category="Validation",
    description="Duplicate record shows generic 'Validation Failed - Please correct "
                "the highlighted fields' instead of a specific 'Duplicate record' message. "
                "Same message appears for empty form submit, making it unclear to the user "
                "what went wrong.",
    expected="System should show specific message like 'Error Code Type + Code "
             "combination already exists'.",
    actual="Generic 'Validation Failed' shown for both empty submit and duplicate.",
    test_ref="C06",
    status="Open",
)

_cs_store.record_issue(
    severity="Low",
    module="Error Code Mst",
    category="Validation",
    description="No field-specific error messages shown below invalid fields on empty "
                "submit. mat-form-field elements get 'ng-invalid' class but no mat-error "
                "text elements are rendered inside them.",
    expected="mat-error elements should show 'Field is required' below each required field.",
    actual="Fields show ng-invalid class but no visible error text.",
    test_ref="C01, C02, C03",
    status="Open",
)

_cs_store.record_issue(
    severity="Low",
    module="Error Code Mst",
    category="Data",
    description="No max-length restriction on Code or Description text fields. "
                "Both inputs have maxLength=-1 (unlimited), allowing extremely long values "
                "that could cause display or storage issues.",
    expected="Backend should enforce reasonable character limits (e.g., 50 for Code, 255 for Description).",
    actual="maxLength=-1 (no limit) on both text inputs.",
    test_ref="C08",
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
