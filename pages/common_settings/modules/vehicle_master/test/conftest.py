"""
conftest.py - Vehicle Master Common Settings (RhythmERP)
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


def pytest_configure(config):
    """Register custom pytest markers for Vehicle Master tests."""
    config.addinivalue_line(
        "markers", "smoke: Critical path tests — must pass for build acceptance (11 tests)"
    )
    config.addinivalue_line(
        "markers", "sanity: Full functional validation of every test case (43 tests)"
    )
    config.addinivalue_line(
        "markers", "regression: Complete regression suite covering all 43 tests"
    )
    config.addinivalue_line(
        "markers", "bug: Tests verifying known open bugs (16 tests)"
    )
    config.addinivalue_line(
        "markers", "ui: UI/popup/dropdown/visual behaviour tests (17 tests)"
    )


# ================================================================
# LOGIN HELPERS
# ================================================================

def _dismiss_tenant_dropdown(driver, login_page):
    """Dismiss the tenant/facility dropdown that auto-opens after entering email.
    This dropdown intercepts the Login button click, causing login to fail.
    Strategy: press Escape to close it, then wait briefly.
    """
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    try:
        # Check if a mat-option or cdk-overlay is open
        overlays = driver.find_elements(
            By.CSS_SELECTOR,
            "div.cdk-overlay-pane mat-option, "
            "div.cdk-overlay-pane .mat-mdc-option"
        )
        if overlays:
            log.info("Tenant dropdown detected, dismissing...")
            # Press Escape to close it
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            login_page.wait_seconds(0.5)
            # Also remove lingering overlays via JS
            driver.execute_script("""
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(
                    function(el) { el.remove(); }
                );
                document.querySelectorAll('.cdk-overlay-pane').forEach(
                    function(el) {
                        if (!el.querySelector('mat-dialog-container')) el.remove();
                    }
                );
            """)
            login_page.wait_seconds(0.3)
            log.info("Tenant dropdown dismissed")
    except Exception as e:
        log.info(f"No tenant dropdown to dismiss: {e}")


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Vehicle Master Tests)...")
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

    # Dismiss tenant dropdown that auto-opens after entering email
    _dismiss_tenant_dropdown(driver, login_page)
    login_page.wait_seconds(1)

    log.step(4, "Clicking Login button")
    login_page.click_login()
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()

    # Verify login actually succeeded
    if "login" in driver.current_url.lower():
        log.error("Login did not complete — still on login page. Retrying...")
        # Retry: dismiss dropdown and click login again
        _dismiss_tenant_dropdown(driver, login_page)
        login_page.click_login()
        login_page.wait_seconds(3)
        login_page.wait_for_login_complete()

    if "login" in driver.current_url.lower():
        raise RuntimeError("RhythmERP login failed — still on login page after retry. Check credentials in .env")

    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture
def vehicle_master_page(logged_in_driver):
    """Vehicle Master page object — hard refresh for speed.
    First test uses full navigate, subsequent tests use hard_refresh.
    Teardown does hard_refresh after each test for clean state."""
    from pages.common_settings.modules.vehicle_master.vehicle_master_page import VehicleMasterPage
    page = VehicleMasterPage(logged_in_driver)
    # Check if already on the Vehicle Master page
    current_url = logged_in_driver.current_url
    if "Vehicle%20Master" in current_url or "Vehicle Master" in current_url:
        page.hard_refresh()
    else:
        page.navigate_to_page()
    yield page
    # Hard refresh after each test for clean state
    try:
        page.hard_refresh()
    except Exception:
        pass


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_vm_store = CSReportStore()

# ---- Vehicle Master Known Issues ----
_vm_store.record_issue(
    severity="High",
    module="Vehicle Master",
    category="Data Integrity",
    description="Duplicate Vehicle Name is allowed in Create form. "
                "Two vehicles with identical Name can exist in the system.",
    expected="System should show a validation error like 'Vehicle Name already exists' "
             "and keep the form open for correction.",
    actual="Duplicate name is accepted and saved without any warning.",
    test_ref="VM-C09",
    status="Open",
)

_vm_store.record_issue(
    severity="High",
    module="Vehicle Master",
    category="Data Integrity",
    description="Duplicate Vehicle Name is allowed in Edit form. "
                "Editing a vehicle to use another vehicle's Name is accepted.",
    expected="System should reject duplicate name during edit.",
    actual="Duplicate name accepted in Edit with no error.",
    test_ref="VM-E01",
    status="Open",
)

_vm_store.record_issue(
    severity="High",
    module="Vehicle Master",
    category="Validation",
    description="Negative Vehicle Price is accepted in both Create and Edit forms.",
    expected="System should reject negative price values.",
    actual="Negative prices like -500 are saved without error.",
    test_ref="VM-C06, VM-E03",
    status="Open",
)

_vm_store.record_issue(
    severity="High",
    module="Vehicle Master",
    category="Validation",
    description="Alphabetic characters are accepted in Vehicle Price field "
                "during Create.",
    expected="Price field should only accept numeric values.",
    actual="Alphabets like 'abcDEF' are accepted and saved.",
    test_ref="VM-C07",
    status="Open",
)

_vm_store.record_issue(
    severity="Critical",
    module="Vehicle Master",
    category="Functionality",
    description="Apply Filters button is completely non-functional. "
                "Clicking Apply Filters after selecting any filter category "
                "(Vehicle Type, Fuel Type, etc.) does nothing. "
                "No request is sent, no loading, no error.",
    expected="Apply Filters should filter the table rows based on selected criteria.",
    actual="Apply Filters button click has zero effect regardless of filter selection.",
    test_ref="VM-S04, VM-S05",
    status="Open",
)

_vm_store.record_issue(
    severity="Medium",
    module="Vehicle Master",
    category="Validation",
    description="Zero (0) price is accepted in both Create and Edit forms. "
                "A vehicle price of 0 is nonsensical.",
    expected="System should reject zero price with a validation error.",
    actual="Price = 0 is saved without error.",
    test_ref="VM-C05, VM-E02",
    status="Open",
)

_vm_store.record_issue(
    severity="Medium",
    module="Vehicle Master",
    category="Validation",
    description="Leading/trailing spaces in Name field are NOT trimmed. "
                "Names are saved with spaces intact, causing potential "
                "duplicates and search issues.",
    expected="System should trim leading/trailing spaces before saving.",
    actual="Spaces are preserved as-is in the Name field.",
    test_ref="VM-C04",
    status="Open",
)

_vm_store.record_issue(
    severity="Low-Medium",
    module="Vehicle Master",
    category="Validation",
    description="Special characters (e.g., !@#$%^&*) are accepted in the "
                "Name field without any sanitization or rejection.",
    expected="System should reject or sanitize special character input in Name.",
    actual="Special characters are stored and displayed as-is.",
    test_ref="VM-C10",
    status="Open",
)

_vm_store.record_issue(
    severity="Low-Medium",
    module="Vehicle Master",
    category="UX",
    description="No per-field inline error messages on the form. "
                "When validation fails, there are no mat-error elements "
                "under individual fields to guide the user.",
    expected="Each invalid field should show an inline error message below it.",
    actual="No inline error messages appear. User gets no field-specific feedback.",
    test_ref="VM-C15",
    status="Open",
)

_vm_store.record_issue(
    severity="Medium",
    module="Vehicle Master",
    category="Functionality",
    description="Clicking a column header in the History popup does not "
                "reorder the rows. Sort icon may change but data stays the same.",
    expected="Clicking a sortable column should reorder rows ascending/descending.",
    actual="Rows remain in original order regardless of sort click.",
    test_ref="VM-H08",
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
    _vm_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_vm_store)
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
        _vm_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _vm_store.has_results():
        return
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
    try:
        filepath = generate_cs_report(_vm_store.results, output_dir,
                                       issues=_vm_store.known_issues)
        print("")
        print("=" * 60)
        print("  REPORT GENERATED: " + filepath)
        print("=" * 60)
    except Exception:
        import traceback as tb
        tb.print_exc()
        print("")
        print("  [WARNING] Report generation failed (see traceback above)")
