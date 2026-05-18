"""
conftest.py - Tax Authority Common Settings (RhythmERP)
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
def tax_authority_page(logged_in_driver):
    """
    Tax Authority page object — fresh navigation for each test.

    Setup:
      1. Hard-refresh the browser to clear any leftover state from the
         previous test (overlays, open popups, stale Angular state).
      2. Navigate to the Tax Authority screen.
      3. If navigation fails, do one more hard-refresh + retry before
         raising — this handles the case where a previous test left the
         browser in a partially broken state.

    Teardown:
      Hard-refresh after every test so the next test always starts
      from a clean browser state.  Wait long enough for Angular to
      fully settle before the next fixture setup runs.
    """
    from tax_authority.tax_authority_page import TaxAuthorityPage

    # --- Pre-test hard refresh to wipe leftover state ---
    try:
        logged_in_driver.refresh()
        import time
        time.sleep(2)
    except Exception as e:
        log.warning(f"Pre-test refresh failed (non-fatal): {e}")

    page = TaxAuthorityPage(logged_in_driver)

    # --- Navigate with one retry ---
    try:
        page.navigate_to_tax_authority()
    except Exception as first_err:
        log.warning(
            f"First navigation attempt failed: {first_err!r} — "
            "retrying after hard refresh..."
        )
        try:
            logged_in_driver.refresh()
            page.wait_seconds(3)
            page.navigate_to_tax_authority()
        except Exception as second_err:
            log.error(f"Navigation failed after retry: {second_err!r}")
            raise

    yield page

    # --- Post-test teardown: hard refresh + settle ---
    try:
        logged_in_driver.refresh()
        page.wait_seconds(2)
        log.info("Post-test hard refresh complete")
    except Exception as e:
        log.warning(f"Post-test refresh failed (non-fatal): {e}")


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
    test_ref="—",
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
    test_ref="—",
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
    """Capture test result (pass/fail) and finalise for report."""
    outcome = yield
    report  = outcome.get_result()
    if call.when == "call":
        if report.passed:
            status = "PASSED"
            error  = ""
        elif report.failed:
            status = "FAILED"
            error  = str(report.longrepr) if report.longrepr else ""
        else:
            status = "SKIPPED"
            error  = ""
        _cs_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
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
        print("  [WARNING] Report generation failed (see traceback above)")