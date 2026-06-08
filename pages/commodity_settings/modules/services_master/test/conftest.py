"""
conftest.py - Services Master Commodity Settings (RhythmERP)
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
# PYTEST MARKERS
# ================================================================

def pytest_configure(config):
    """Register custom pytest markers for Services Master tests.

    Usage examples:
        pytest test_services_master_validation.py -m smoke
        pytest test_services_master_validation.py -m "smoke or sanity"
        pytest test_services_master_validation.py -m "not bug"
        pytest test_services_master_validation.py -m ui
    """
    config.addinivalue_line("markers", "smoke: Critical path â€” core create/view/edit/search")
    config.addinivalue_line("markers", "sanity: Broad functional coverage for quick feedback")
    config.addinivalue_line("markers", "regression: Full test suite â€” all 50 tests")
    config.addinivalue_line("markers", "bug: Tests validating known open bugs (BUG-001 to BUG-007)")
    config.addinivalue_line("markers", "ui: UI element visibility, layout, and interaction checks")


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Services Master Tests)...")
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

#     log.step(3, "Selecting facility (blank - first option)")
#     login_page.select_facility_by_index(index=0)

    login_page.wait_seconds(1)

    log.step(4, "Clicking Login button")
    login_page.click_login()
    login_page.wait_seconds(3)

    login_page.wait_for_login_complete()

    # Verify login actually succeeded (don't falsely report success)
    if "login" in driver.current_url.lower():
        log.error("Login did not complete — still on login page. URL: " + driver.current_url)
        raise RuntimeError("RhythmERP login failed — still on login page after wait. Check credentials in .env")

    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture
def sm_page(logged_in_driver):
    """Services Master page object — fresh navigation for each test.
    Optimised (v3): eliminates double hard_refresh between tests.
    _cleanup() in each test's finally block already does hard_refresh,
    so the fixture only refreshes if the page is NOT in a clean state.
    This saves ~3-4s per test x 49 tests = ~150-200s total."""
    from pages.commodity_settings.modules.services_master.services_master_page import (
        ServicesMasterPage,
    )
    page = ServicesMasterPage(logged_in_driver)
    current_url = logged_in_driver.current_url
    if "Services%20Master" not in current_url and "Services Master" not in current_url:
        # Not on SM page at all — full navigation needed
        page.navigate_to_page()
    else:
        # Already on SM page — _cleanup() from previous test already
        # did a hard_refresh. Just verify the page is in a clean state
        # with a fast JS check. Only refresh if the table is missing.
        try:
            table_present = logged_in_driver.execute_script(
                "return !!document.querySelector('table#excel-table');"
            )
            if not table_present:
                page.hard_refresh()
        except Exception:
            page.hard_refresh()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_sm_store = CSReportStore()

# ---- Services Master Known Issues ----

# BUG-001 (HIGH): No maxlength on Name input
_sm_store.record_issue(
    severity="High",
    module="Services Master",
    category="Validation",
    description="No maxlength attribute on the Name input field. Names of 256+ "
                "characters are accepted by the client. The server rejects at 255 "
                "with a generic 'Failed to save record' error instead of a specific "
                "field-level message. No client-side length validation exists.",
    expected="System should enforce maxlength=255 on the Name input and show "
             "inline validation if the limit is exceeded.",
    actual="No maxlength constraint. 256+ char names accepted by client, "
           "accepted by both client and server without any error.",
    test_ref="SM-C08",
    status="Open",
)

# BUG-002 (HIGH): No maxlength on Base Uom Conversion
_sm_store.record_issue(
    severity="High",
    module="Services Master",
    category="Validation",
    description="No maxlength attribute on the Base Uom Conversion input field. "
                "Values of 11+ characters are accepted by the client. Server max "
                "is 10 characters. No client-side length validation exists.",
    expected="System should enforce maxlength=10 on the Base Uom Conversion input.",
    actual="No maxlength constraint. 11+ char values accepted by both client and server without any error.",
    test_ref="SM-C09",
    status="Open",
)

# BUG-003 (HIGH): Name accepts all characters without restriction
_sm_store.record_issue(
    severity="High",
    module="Services Master",
    category="Data Integrity",
    description="The Name field accepts all types of input without any restrictions â€” "
                "special characters (!@#$%^&*), spaces-only, and any Unicode. No "
                "input sanitization or format validation exists.",
    expected="System should restrict or sanitize special characters and reject "
             "spaces-only input.",
    actual="All characters accepted freely. Spaces-only name creates blank record.",
    test_ref="SM-C05, SM-C06",
    status="Open",
)

# BUG-004 (HIGH): Base Uom Conversion accepts all input types
_sm_store.record_issue(
    severity="High",
    module="Services Master",
    category="Validation",
    description="The Base Uom Conversion field accepts all input types â€” alphabetic "
                "characters (abcDEF), special characters (!@#$%), negative numbers (-5), "
                "zero (0), and spaces-only (   ). No type, range, or format validation "
                "exists on this field despite it being a numeric/quantity field.",
    expected="Field should only accept positive numeric values. Should reject "
             "alphabetic input, special characters, negative numbers, zero, and spaces.",
    actual="All input types accepted without any validation.",
    test_ref="SM-C10, SM-C11, SM-C12, SM-C13",
    status="Open",
)

# BUG-005 (MEDIUM): Duplicate Names allowed
_sm_store.record_issue(
    severity="Medium",
    module="Services Master",
    category="Data Integrity",
    description="Duplicate Service Names are allowed in the Create form. "
                "Two or more services with identical Name can exist in the system "
                "with no warning or rejection.",
    expected="System should show a validation error like 'Name already exists' "
             "and keep the form open for correction.",
    actual="Duplicate name is accepted and saved without any warning.",
    test_ref="SM-C07",
    status="Open",
)

# BUG-006 (MEDIUM): Generic server error instead of specific message
_sm_store.record_issue(
    severity="Medium",
    module="Services Master",
    category="UX",
    description="When server-side validation rejects data (e.g., Name exceeds 255 "
                "chars or Base Uom Conversion exceeds 10 chars), the error message "
                "is a generic 'Failed to save record' instead of indicating which "
                "field caused the error and why.",
    expected="Error message should indicate the specific field and reason, e.g., "
             "'Name must not exceed 255 characters'.",
    actual="Generic 'Failed to save record' message with no field-level detail.",
    test_ref="SM-C08, SM-C09",
    status="Open",
)

# BUG-007 (LOW): History popup shows "No data available"
_sm_store.record_issue(
    severity="Low",
    module="Services Master",
    category="Functionality",
    description="History popup shows 'No data available' even for records that "
                "have been created or modified. No audit trail is available.",
    expected="History should show creation and modification timestamps.",
    actual="History popup is always empty.",
    test_ref="SM-H01",
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
    _sm_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_sm_store)
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
        _sm_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _sm_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _sm_store.results, output_dir, issues=_sm_store.known_issues
        )
        print("")
        print("=" * 60)
        print("  SERVICES MASTER REPORT GENERATED: " + filepath)
        print("=" * 60)
    except Exception:
        import traceback as tb
        tb.print_exc()
        print("")
        print("  [WARNING] Report generation failed (see traceback above)")

