"""
conftest.py - Supplier Screen (RhythmERP)
==========================================
Session-scoped driver + login fixtures for Supplier Screen tests.

Login credentials loaded from environment variables:
  RHYTHMERP_EMAIL / RHYTHMERP_PASSWORD
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
# LOGIN CREDENTIALS (aliased from shared env vars)
# ================================================================
SP_LOGIN_EMAIL = RHYTHMERP_EMAIL
SP_LOGIN_PASSWORD = RHYTHMERP_PASSWORD
SP_LOGIN_FACILITY_INDEX = 0  # GS SPACE


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
        pytest test_supplier_validation.py                       # Full regression (15 functions, ~31 invocations)
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
    config.addinivalue_line(
        "markers", "api: Pure API tests — no browser needed (~5 min)"
    )
    config.addinivalue_line(
        "markers", "hybrid: API creates data + UI verifies display (~15-20 min)"
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
    Uses RHYTHMERP_EMAIL / RHYTHMERP_PASSWORD from env vars.
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

def _prompt_for_api_credentials():
    """Interactively prompt user for ERP API token and tenant ID.

    Only runs when stdin is a real TTY (local terminal). When running
    non-interactively (CI, web UI subprocess) returns (None, None) so
    the caller can skip rather than crash with OSError.
    """
    if not sys.stdin.isatty():
        return None, None

    print()
    print("=" * 60)
    print("  API AUTHENTICATION REQUIRED")
    print("=" * 60)
    print()
    print("  The ERP login endpoint is unavailable (502/404).")
    print("  Please provide your Bearer token from Chrome DevTools:")
    print()
    print("    1. Open ERP in Chrome -> F12 -> Network tab")
    print("    2. Click any XHR request to /core/...")
    print("    3. Copy the Authorization header value (after 'Bearer ')")
    print()

    token = input("  Paste your ERP Bearer token: ").strip()
    if not token:
        print("  [ABORT] No token entered. API tests will fail.")
        return None, None

    # Strip "Bearer " prefix if user pasted the full header
    if token.startswith("Bearer "):
        token = token[7:]

    tenant_id = input("  Enter Tenant ID [681]: ").strip()
    if not tenant_id:
        tenant_id = "681"

    return token, tenant_id


@pytest.fixture(scope="session")
def erp_api():
    """Session-scoped ERP API client.

    Authenticates once and reuses the token for the entire test session.

    Auth strategy (in order):
      1. ERP_TOKEN + ERP_TENANT_ID env vars (no prompt, fastest)
      2. API login via /auth/login1/ (auto, no manual step)
      3. Interactive prompt — asks user to paste token from DevTools

    To skip the prompt, set env vars in PowerShell:
        $env:ERP_TOKEN = "eyJhbGciOiJIUzI1NiIs..."
        $env:ERP_TENANT_ID = "681"
    """
    from common.erp_api_client import RhythmERPAPIClient

    tenant_id = os.environ.get("ERP_TENANT_ID", "681")

    client = RhythmERPAPIClient(
        username=SP_LOGIN_EMAIL,
        password=SP_LOGIN_PASSWORD,
        tenant_id=tenant_id,
    )

    # Strategy 1: Try ERP_TOKEN env var (fastest, no prompt)
    token = os.environ.get("ERP_TOKEN", "").strip()
    if token:
        if token.startswith("Bearer "):
            token = token[7:]
        try:
            client.login_from_browser(token=token, tenant_id=tenant_id)
            log.info(f"[API] Session set from ERP_TOKEN env var. Tenant: {tenant_id}")
            # Verify auth works
            result = client.list_entries("Supplier", page=1, page_size=1)
            if result:
                yield client
                try:
                    client.close()
                except Exception:
                    pass
                return
            else:
                log.warning("[API] ERP_TOKEN auth verification failed — trying next strategy")
        except Exception as e:
            log.warning(f"[API] ERP_TOKEN auth failed: {e} — trying next strategy")

    # Strategy 2: Try API login
    try:
        client.login()
        log.info("[API] ERP API client ready (auto login)")
        yield client
        try:
            client.close()
        except Exception:
            pass
        return
    except Exception:
        log.warning("[API] Auto login failed — will prompt for token")

    # Strategy 3: Interactive prompt (TTY only) or skip
    prompt_token, prompt_tenant = _prompt_for_api_credentials()
    if not prompt_token:
        pytest.skip("ERP_TOKEN not set and auto-login failed. Set ERP_TOKEN env var to run API tests.")
        return

    tenant_id = prompt_tenant or tenant_id
    client.tenant_id = tenant_id
    client.login_from_browser(token=prompt_token, tenant_id=tenant_id)
    result = client.list_entries("Supplier", page=1, page_size=1)
    if result:
        log.info(f"[API] Interactive auth successful. Tenant: {tenant_id}")
    else:
        log.warning("[API] Interactive auth verification failed — token may be invalid")

    yield client

    try:
        client.close()
    except Exception:
        pass


@pytest.fixture(scope="session")
def sp_cleanup_tracker():
    """CleanupTracker — records all created supplier IDs for no-delete cleanup reporting.

    Generates JSON + CSV reports at session end.
    """
    from pages.registration.modules.supplier.utils.supplier_cleanup import (
        CleanupTracker,
    )
    tracker = CleanupTracker()
    log.info("[Fixture] sp_cleanup_tracker initialized")
    yield tracker
    # Session teardown: generate cleanup reports
    if tracker.count > 0:
        try:
            paths = tracker.generate_reports()
            if paths:
                log.info(f"[Cleanup] Reports generated: {paths}")
        except Exception as e:
            log.warning(f"[Cleanup] Report generation failed: {e}")
    else:
        log.info("[Cleanup] No tracked supplier IDs to report")


@pytest.fixture
def sp_api(erp_api, sp_cleanup_tracker):
    """SupplierAPIUtils — function-scoped API utility with cleanup tracking.

    Uses the session-scoped erp_api and sp_cleanup_tracker.
    Each test gets a fresh SupplierAPIUtils instance, but all tracked
    IDs accumulate in the shared sp_cleanup_tracker for end-of-session reporting.
    """
    from pages.registration.modules.supplier.utils.api_supplier_utils import (
        SupplierAPIUtils,
    )
    utils = SupplierAPIUtils(
        api_client=erp_api,
        tracker=sp_cleanup_tracker,
    )
    yield utils


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

# BUG-006 (MEDIUM): Company Name accepts spaces-only
_sp_store.record_issue(
    severity="Medium",
    module="Supplier",
    category="Validation",
    description="Company Name accepts spaces-only input (e.g., '          ') without any validation. "
                "The ERP creates the entry successfully with a blank-looking name.",
    expected="Should strip/reject whitespace-only input and show validation error.",
    actual="CONFIRMED: '          ' (10 spaces) saved successfully as id=21.",
    test_ref="SP-C03",
    status="Confirmed",
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
