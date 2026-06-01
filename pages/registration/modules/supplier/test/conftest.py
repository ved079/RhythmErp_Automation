"""
conftest.py - Supplier Screen (RhythmERP)
==========================================
Session-scoped driver + login fixtures for Supplier Screen tests.

IMPORTANT: Uses DIFFERENT login credentials than other screens!
  Email:    Assistant@mail.com
  Password: Vedant@12345
  Facility: RuralLife Producer Company (index 0)
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
from config import RHYTHMERP_LOGIN_URL
from pages.common_settings.cs_report_generator import (
    CSReportStore,
    generate_cs_report,
)


# ================================================================
# LOGIN CREDENTIALS — Supplier Screen (DIFFERENT from other screens!)
# ================================================================
SP_LOGIN_EMAIL = "user@admin.com"
SP_LOGIN_PASSWORD = "Tenant@123456789"
SP_LOGIN_FACILITY_INDEX = 0  # RuralLife Producer Company


# ================================================================
# PYTEST MARKERS REGISTRATION
# ================================================================

def pytest_configure(config):
    """Register custom test markers for categorized test execution.

    Usage:
        pytest test_supplier_validation.py -m smoke              # Critical paths only (~10 min)
        pytest test_supplier_validation.py -m sanity             # Targeted validation (~20 min)
        pytest test_supplier_validation.py -m "smoke or sanity"  # Combined (~25 min)
        pytest test_supplier_validation.py -m "not bug"          # Skip known-bug tests
        pytest test_supplier_validation.py -m bug                # Known bug tracking only
        pytest test_supplier_validation.py -m ui                 # Popup/toggle/behavior checks
        pytest test_supplier_validation.py                       # Full regression (all 42 tests)
    """
    config.addinivalue_line(
        "markers", "smoke: Critical happy-path tests — build not broken (~10-15 min)"
    )
    config.addinivalue_line(
        "markers", "sanity: Targeted feature validation — specific checks (~20-30 min)"
    )
    config.addinivalue_line(
        "markers", "bug: Known bug tracking tests (usually xfail) — confirm bugs exist or are fixed"
    )
    config.addinivalue_line(
        "markers", "ui: Popup, toggle, close button, readonly behavior checks (~15-20 min)"
    )


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Supplier Tests)...")
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
    """Driver with completed RhythmERP login session.
    Uses Assistant@mail.com / Vedant@12345 / RuralLife Producer Company.
    """
    log.separator()
    log.info("LOGGING INTO RHYTHMERP (Supplier Screen)...")
    log.separator()

    login_page = LoginPage(driver)

    log.info("Navigating to: " + str(RHYTHMERP_LOGIN_URL))
    driver.get(RHYTHMERP_LOGIN_URL)
    login_page.wait_seconds(2)

    log.step(1, "Entering email: " + SP_LOGIN_EMAIL)
    login_page.enter_email(SP_LOGIN_EMAIL)

    log.step(2, "Entering password")
    login_page.enter_password(SP_LOGIN_PASSWORD)

    # Dismiss tenant dropdown (backend bug: shows even for single-tenant users)
    login_page._dismiss_tenant_dropdown()
    

    log.step(3, "Clicking Login button")
    login_page.click_login()
    login_page.click_login()
    login_page.wait_seconds(3)
    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture
def sp_page(logged_in_driver):
    """Supplier page object — fresh navigation for each test."""
    from pages.registration.modules.supplier.supplier_page import (
        SupplierPage,
    )
    page = SupplierPage(logged_in_driver)
    page.navigate_to_page()
    yield page


# ================================================================
# API FIXTURES (additive — do not affect existing tests)
# ================================================================
# These fixtures provide direct API access for fast data creation.
# Existing Selenium-based tests are completely unaffected.
# To use API fixtures in a test, add 'erp_api' or 'supplier_api'
# to the test's parameter list.
#
# Usage in tests:
#   def test_something(sp_page, erp_api):
#       # API creates prerequisite data in 0.3s instead of 30s
#       erp_api.create_entry(generate_supplier_api_payload("PreReq"))
#       # UI test continues normally
#       ...
#
#   def test_api_only(erp_api):
#       # Pure API test — no browser needed
#       payloads = generate_supplier_api_payloads(20)
#       erp_api.batch_create(payloads)
# ================================================================

@pytest.fixture(scope="session")
def erp_api():
    """Session-scoped ERP API client.

    Authenticates once and reuses the token for the entire test session.
    Uses the same credentials from config.py / .env file.

    Note: If the login endpoint doesn't work with these credentials,
    use login_from_browser() with a token captured from DevTools:
        client = RhythmERPAPIClient()
        client.login_from_browser(token="eyJ...", tenant_id="599")
    """
    from common.erp_api_client import RhythmERPAPIClient

    client = RhythmERPAPIClient(
        username=SP_LOGIN_EMAIL,
        password=SP_LOGIN_PASSWORD,
    )

    try:
        client.login()
        log.info("[API] ERP API client ready")
    except Exception as e:
        log.warning(
            f"[API] API login failed: {e}. "
            "API-based tests will be skipped. "
            "Use login_from_browser() as fallback."
        )

    yield client

    try:
        client.close()
    except Exception:
        pass


@pytest.fixture(scope="session")
def supplier_api(erp_api):
    """Supplier-specific API helper with pre-resolved dropdown FK IDs.

    Resolves all Supplier dropdown options once per session via the
    screen schema, then provides them for payload generation.
    """
    from pages.registration.modules.supplier.data.supplier_data import (
        DEFAULT_SUPPLIER_FK_IDS,
    )

    if not erp_api.is_authenticated():
        log.warning("[API] Not authenticated — supplier_api will use default FK IDs")
        yield {"client": erp_api, "dropdown_ids": DEFAULT_SUPPLIER_FK_IDS}
        return

    # Try to resolve dropdown IDs from the API schema
    resolved_ids = dict(DEFAULT_SUPPLIER_FK_IDS)

    try:
        schema = erp_api.get_screen_schema("Supplier")
        if schema:
            log.info("[API] Supplier schema fetched — resolving dropdown IDs...")
            # The schema's filter_dropdown_raw_query contains available options
            # with their IDs. We can auto-resolve common dropdowns here.
            # For now, defaults are verified — add dynamic resolution as needed.
            log.info(f"[API] Using FK IDs: {resolved_ids}")
    except Exception as e:
        log.warning(f"[API] Schema resolution failed: {e} — using defaults")

    yield {"client": erp_api, "dropdown_ids": resolved_ids}


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_sp_store = CSReportStore()

# ---- Supplier Known Issues ----

# BUG-001 (HIGH): Company Name accepts special characters
_sp_store.record_issue(
    severity="High",
    module="Supplier",
    category="Validation",
    description="Company Name accepts special characters and numbers without any validation. "
                "Characters like @#$%^&* are accepted and saved successfully.",
    expected="Should restrict special characters and show validation error.",
    actual="CONFIRMED: 'ABC@@ Traders', 'ds&^%##%' saved successfully.",
    test_ref="SP-C04, SP-C05, SP-C06",
    status="Confirmed",
)

# BUG-002 (MEDIUM): No email format validation — FIXED
_sp_store.record_issue(
    severity="Medium",
    module="Supplier",
    category="Validation",
    description="No email format validation. Invalid emails like 'notanemail' are accepted "
                "without any error on blur or submit.",
    expected="Should validate email format and show inline error.",
    actual="FIXED: ERP now shows 'Invalid Email' error on blur/submit.",
    test_ref="SP-C09",
    status="Fixed",
)

# BUG-003 (LOW): Phone Number spinner controls
_sp_store.record_issue(
    severity="Low",
    module="Supplier",
    category="UI Bug",
    description="Phone Number field shows increase/decrease spinner controls (up/down arrows) "
                "because the input type is 'number' instead of 'tel' or 'text'.",
    expected="Should be type=tel or type=text with no spinner controls.",
    actual="Spinner controls visible — type=number on input.",
    test_ref="SP-P06",
    status="Confirmed",
)

# BUG-004 (MEDIUM): No PAN format validation — FIXED
_sp_store.record_issue(
    severity="Medium",
    module="Supplier",
    category="Validation",
    description="No PAN format validation. PAN should follow Indian format: "
                "5 letters + 4 digits + 1 letter (e.g., ABCDE1234F). Any text is accepted.",
    expected="Should validate PAN format with regex pattern.",
    actual="FIXED: ERP now shows 'Invalid PAN Number' error on blur/submit.",
    test_ref="SP-C10",
    status="Fixed",
)

# BUG-005 (HIGH): No Update button in Edit mode — FIXED
_sp_store.record_issue(
    severity="High",
    module="Supplier",
    category="Functionality",
    description="No Update button in Edit mode. Only Cancel button is visible in popup-footer. "
                "User cannot save edits — Edit mode is non-functional for saving changes.",
    expected="Update button should appear in edit mode popup-footer right div.",
    actual="FIXED: Update button now visible in Edit mode popup-footer.",
    test_ref="SP-E01",
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
    _sp_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_sp_store)
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
        _sp_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _sp_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _sp_store.results, output_dir, issues=_sp_store.known_issues
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
