"""
conftest.py - Tax Authority Common Settings (RhythmERP)
UOM Gold Standard pattern:
  - Session-scoped driver + logged_in_driver
  - NO function-scoped page fixture — each test creates TaxAuthorityPage(logged_in_driver) locally
  - This saves 5-8s per test (no full navigate_to_page + force_cleanup_all per test)
"""

import os
import sys
import logging
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from common.browser_utils import get_driver
from pages.login_screens.Login_Screens_.login_page import LoginPage
from common.screenshot_broadcast import start as start_screenshot_broadcast, stop as stop_screenshot_broadcast
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD
from pages.common_settings.cs_report_generator import CSReportStore, generate_cs_report


# ================================================================
# FIXTURES — UOM Gold Standard Pattern
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Tax Authority Tests)...")
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


@pytest.fixture(scope="session")
def shared_tax_authority(logged_in_driver):
    """Creates one Tax Authority record via UI once for the session."""
    from pages.common_settings.modules.tax_authority.tax_authority_page import TaxAuthorityPage
    from pages.common_settings.modules.tax_authority.data.tax_authority_data import valid_tax_authority_data
    page = TaxAuthorityPage(logged_in_driver)
    data = valid_tax_authority_data()
    page.navigate_to_page()
    result = page.create_record(data)
    assert result.get("status") == "success", f"shared_tax_authority fixture failed: {result.get('error')}"
    yield data


# ================================================================
# PYTEST MARKERS
# ================================================================

def pytest_configure(config):
    """Register custom pytest markers for Tax Authority tests."""
    config.addinivalue_line("markers", "smoke: Critical path tests (7 tests)")
    config.addinivalue_line("markers", "sanity: Full functional validation (18 tests)")
    config.addinivalue_line("markers", "regression: Complete regression suite (18 tests)")
    config.addinivalue_line("markers", "bug: Tests verifying known open bugs (6 tests)")
    config.addinivalue_line("markers", "ui: UI/popup/form/table behaviour tests (12 tests)")


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_cs_store = CSReportStore()

# ---- Tax Authority Known Issues ----
_cs_store.record_issue(
    severity="High",
    module="Tax Authority",
    category="UX",
    description="No success SweetAlert after successful record creation. "
                "Form closes silently without any confirmation message.",
    expected="System should show 'Your record has been added successfully!' "
             "SweetAlert with OK button after successful create/update.",
    actual="Form closes silently after Submit/Update. No success toast or "
           "SweetAlert is displayed. User cannot confirm the save operation.",
    test_ref="C05, E04",
    status="Open",
)

_cs_store.record_issue(
    severity="Medium",
    module="Tax Authority",
    category="Validation",
    description="Missing mat-error messages for Tax Type and Country dropdowns "
                "on empty form submit. Only Tax Name shows 'This field is required'.",
    expected="All 3 required fields should show 'This field is required' "
             "mat-error below the field on empty submit.",
    actual="Only Tax Name shows mat-error. Tax Type and Country have ng-invalid "
           "class but no visible error message text is rendered.",
    test_ref="C01",
    status="Open",
)

_cs_store.record_issue(
    severity="Low",
    module="Tax Authority",
    category="Validation",
    description="No maxlength restriction on Tax Name field.",
    expected="Tax Name should have a reasonable max-length limit.",
    actual="maxlength=-1 (unlimited). Extremely long strings (200+ characters) "
           "may be accepted without warning.",
    test_ref="C08",
    status="Open",
)

_cs_store.record_issue(
    severity="Low",
    module="Tax Authority",
    category="Consistency",
    description="ADD button has no mattooltip attribute, unlike other Common Settings "
                "modules (Bank, Error Code Mst) which have mattooltip='ADD'.",
    expected="ADD button should have mattooltip='ADD' for consistency.",
    actual="ADD button has no mattooltip. Requires different locator strategy "
           "(//button[mat-icon[text()='add']] instead of //button[contains(@class,'erp-add-btn')]).",
    test_ref="---",
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
