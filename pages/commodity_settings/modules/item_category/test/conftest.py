"""
conftest.py - Item Category Commodity Settings (RhythmERP)
Fixtures, hooks, and bug registry for Item Category automation tests.
Golden standard pattern — matches UOM and Services Master.
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
    """Register custom pytest markers for Item Category tests.

    Usage examples:
        pytest test_item_category_validation.py -m smoke
        pytest test_item_category_validation.py -m "smoke or sanity"
        pytest test_item_category_validation.py -m "not bug"
        pytest test_item_category_validation.py -m ui
    """
    config.addinivalue_line("markers", "smoke: Critical path — core create/view/edit/search")
    config.addinivalue_line("markers", "sanity: Broad functional coverage for quick feedback")
    config.addinivalue_line("markers", "regression: Full test suite — all 47 tests")
    config.addinivalue_line("markers", "bug: Tests validating known open bugs (BUG-001 to BUG-007)")
    config.addinivalue_line("markers", "ui: UI element visibility, layout, and interaction checks")


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Item Category Tests)...")
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

    # Verify login actually succeeded (don't falsely report success)
    if "login" in driver.current_url.lower():
        log.error("Login did not complete — still on login page. URL: " + driver.current_url)
        raise RuntimeError("RhythmERP login failed — still on login page after wait. Check credentials in .env")

    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture
def ic_page(logged_in_driver):
    """Item Category page object — fresh navigation for each test."""
    from pages.commodity_settings.modules.item_category.item_category_page import (
        ItemCategoryPage,
    )
    page = ItemCategoryPage(logged_in_driver)
    # Optimised: full navigation only if not already on IC page
    current_url = logged_in_driver.current_url
    if "Item%20Category" not in current_url and "Item Category" not in current_url:
        page.navigate_to_page()
    else:
        page.hard_refresh()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_ic_store = CSReportStore()

# ---- Item Category Known Issues ----

# BUG-001 (HIGH): No maxlength on Item Category input — 256+ char names ACCEPTED
_ic_store.record_issue(
    severity="High",
    module="Item Category",
    category="Validation",
    description="No maxlength attribute on the Item Category input field. Names of 256+ "
                "characters are accepted by BOTH the client AND the server. There is "
                "no client-side or server-side length validation. The 256-char name "
                "(all 'C' chars) is saved successfully with 'Your record has been added "
                "successfully!' message.",
    expected="System should enforce maxlength=255 on the Item Category input and show "
             "inline validation if the limit is exceeded.",
    actual="No maxlength constraint. 256+ char names accepted and saved successfully. "
           "No warning, no error, no truncation.",
    test_ref="IC-C10, IC-P08",
    status="Open",
)

# BUG-001b (INFO): Item Category field only accepts chars, nums, hyphen (-), and slash (/)
_ic_store.record_issue(
    severity="Info",
    module="Item Category",
    category="Validation",
    description="Item Category field rejects underscores (_) and other special characters "
                "with a generic 'Validation Failed' popup. Only letters, numbers, "
                "hyphen (-) and slash (/) are accepted. This is by design but the "
                "error message is not specific — it says 'Validation Failed' without "
                "indicating which character is invalid.",
    expected="System should show a specific message like 'Item Category can only contain "
             "letters, numbers, hyphens and slashes'.",
    actual="Generic 'Validation Failed' popup with no indication of the character restriction.",
    test_ref="IC-C06, IC-C07, IC-N01, IC-P04",
    status="Open",
)

# BUG-002 (HIGH): No maxlength on Item Description input
_ic_store.record_issue(
    severity="High",
    module="Item Category",
    category="Validation",
    description="No maxlength attribute on the Item Description input field. "
                "Descriptions of 256+ characters are accepted by the client. "
                "Server rejects at 255 with a generic error. No client-side "
                "length validation exists.",
    expected="System should enforce maxlength=255 on the Item Description input.",
    actual="No maxlength constraint. 256+ char descriptions accepted by client, "
           "rejected by server with generic error message.",
    test_ref="IC-C09, IC-C10",
    status="Open",
)

# BUG-003 (HIGH): Duplicate Item Category names allowed
_ic_store.record_issue(
    severity="High",
    module="Item Category",
    category="Data Integrity",
    description="Duplicate Item Category names are allowed in the system. "
                "Two or more categories with identical names can exist "
                "with no warning or rejection.",
    expected="System should show a validation error like 'Item Category already exists' "
             "and keep the form open for correction.",
    actual="Duplicate name is accepted and saved without any warning.",
    test_ref="IC-C11",
    status="Open",
)

# BUG-004 (MEDIUM): Level field accepts negative integers
_ic_store.record_issue(
    severity="Medium",
    module="Item Category",
    category="Validation",
    description="The Level field accepts negative integer values (e.g., -5). "
                "Negative levels have no meaningful interpretation in a category "
                "hierarchy (levels should be 1, 2, 3 etc.). No minimum value "
                "validation exists.",
    expected="System should reject negative Level values and show an inline error "
             "like 'Level must be a positive integer'.",
    actual="Negative Level values are accepted and saved without any validation.",
    test_ref="IC-N02",
    status="Open",
)

# BUG-005 (MEDIUM): Level field accepts zero
_ic_store.record_issue(
    severity="Medium",
    module="Item Category",
    category="Validation",
    description="The Level field accepts zero (0). A level of zero has no meaningful "
                "interpretation in a category hierarchy. No minimum value validation exists.",
    expected="System should reject zero Level and show an inline error.",
    actual="Zero Level is accepted and saved without any validation.",
    test_ref="IC-N03",
    status="Open",
)

# BUG-006 (MEDIUM): Generic 'Failed to save record' message on length violation
_ic_store.record_issue(
    severity="Medium",
    module="Item Category",
    category="UX / Validation",
    description="When Item Category or Item Description exceeds 255 characters, the server "
                "returns a generic 'Failed to save record' popup instead of a "
                "specific message like 'Item Category exceeds maximum length of 255 "
                "characters'. The user has no indication which field caused "
                "the failure or what the limit is.",
    expected="System should show a specific error message indicating which "
             "field exceeded the length limit and what the maximum is.",
    actual="Generic 'Failed to save record' popup with no field-specific "
           "information.",
    test_ref="IC-C10",
    status="Open",
)

# BUG-007 (LOW): History popup shows "No data available"
_ic_store.record_issue(
    severity="Low",
    module="Item Category",
    category="Functionality",
    description="History popup shows 'No data available' even for records "
                "that were just created or modified. The history tracking "
                "may not be functional for Item Category.",
    expected="History popup should show at least the creation record.",
    actual="History popup shows 'No data available'.",
    test_ref="IC-H01, IC-H03",
    status="Open",
)

# ---- Item Category UI Changes (live system vs. original automation) ----
_ic_store.record_issue(
    severity="Info",
    module="Item Category",
    category="UI Change",
    description="Action buttons changed from separate columns (View/Edit/History) "
                "to a single 3-dot menu dropdown in cdk-column-actions. "
                "Automation code updated to use _click_action_menu_item() instead of "
                "separate column button locators.",
    expected="Separate action columns (cdk-column-view/edit/archive).",
    actual="Single Actions column with 3-dot menu dropdown.",
    test_ref="All tests using click_view/edit/history_button",
    status="Fixed",
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
    _ic_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_ic_store)
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
        _ic_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _ic_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _ic_store.results, output_dir, issues=_ic_store.known_issues
        )
        print("")
        print("=" * 60)
        print("  ITEM CATEGORY REPORT GENERATED: " + filepath)
        print("=" * 60)
    except Exception:
        import traceback as tb
        tb.print_exc()
        print("")
        print("  [WARNING] Report generation failed (see traceback above)")
