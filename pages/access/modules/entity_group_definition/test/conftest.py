"""
conftest.py - Entity Group Definition Access Settings (RhythmERP)
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
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD
from pages.common_settings.cs_report_generator import (
    CSReportStore,
    generate_cs_report,
)


def pytest_configure(config):
    """Register custom pytest markers for Entity Group Definition tests."""
    config.addinivalue_line("markers", "smoke: Core critical-path tests (create happy path, required field validation, edit pre-populated, search)")
    config.addinivalue_line("markers", "sanity: Full suite -- all 35 Entity Group Definition tests")
    config.addinivalue_line("markers", "regression: Full suite -- all 35 Entity Group Definition tests")
    config.addinivalue_line("markers", "bug: Tests targeting confirmed bugs (BUG-001 through BUG-008)")
    config.addinivalue_line("markers", "ui: Popup behavior, view/edit form, cancel/close, SweetAlert2, refresh, pagination, sort, filter panel, mat-error")


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Entity Group Definition Tests)...")
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
def egd_page(logged_in_driver):
    """Entity Group Definition page object — fresh navigation for each test."""
    from pages.access.modules.entity_group_definition.entity_group_definition_page import (
        EntityGroupDefinitionPage,
    )
    page = EntityGroupDefinitionPage(logged_in_driver)
    page.navigate_to_page()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_egd_store = CSReportStore()

# ---- Entity Group Definition Known Issues ----

# BUG-001 (HIGH): Spaces-only Entity Group Name accepted
_egd_store.record_issue(
    severity="High",
    module="Entity Group Definition",
    category="Data Integrity",
    description="Spaces-only Entity Group Name is accepted and creates a blank/empty "
                "record in the table. When a user enters only spaces in the Entity "
                "Group Name field and submits, the ERP trims the spaces but stores "
                "an empty string, resulting in a row with no visible name text.",
    expected="System should reject spaces-only input with a validation error "
             "like 'Entity Group Name cannot be empty or spaces only'.",
    actual="Spaces-only name is accepted and creates a blank record in the table.",
    test_ref="EGD-C03, EGD-E06",
    status="Open",
)

# BUG-002 (HIGH): Exact duplicate name silently rejected with no feedback
_egd_store.record_issue(
    severity="High",
    module="Entity Group Definition",
    category="UX",
    description="When creating an Entity Group Definition with a name that exactly "
                "matches an existing record, the form stays open with no error message, "
                "no SweetAlert2 popup, no toast notification, and no mat-error. The "
                "submission simply does nothing — the user gets zero feedback about "
                "why their submission failed.",
    expected="System should show a clear error message like 'Entity Group Name "
             "already exists' and keep the form open for correction.",
    actual="Form stays open with values intact but no feedback. Submission silently fails.",
    test_ref="EGD-D01, EGD-D04, EGD-B03",
    status="Open",
)

# BUG-003 (HIGH): Case-insensitive duplicate NOT blocked
_egd_store.record_issue(
    severity="High",
    module="Entity Group Definition",
    category="Data Integrity",
    description="Case-insensitive duplicate Entity Group Names are NOT blocked. "
                "If 'Agdi' exists, creating 'agdi' (lowercase) is accepted as a "
                "new record. Similarly, spaces around names are not checked for "
                "uniqueness. This leads to data duplication and confusion.",
    expected="System should perform a case-insensitive comparison (ignoring "
             "leading/trailing spaces) and reject duplicate names.",
    actual="Case-variant duplicates are accepted as separate records.",
    test_ref="EGD-D02, EGD-D03",
    status="Open",
)

# BUG-004 (MEDIUM): Negative Level values accepted
_egd_store.record_issue(
    severity="Medium",
    module="Entity Group Definition",
    category="Validation",
    description="Negative Level values (e.g., -5, -10) are accepted without any "
                "validation error. The Level field has no min attribute, allowing "
                "any negative integer. This is likely unintended as entity group "
                "levels should represent hierarchical depth (0, 1, 2, ...).",
    expected="System should enforce min=0 on the Level field and reject negative values.",
    actual="Negative levels are accepted and stored as-is.",
    test_ref="EGD-B01",
    status="Open",
)

# BUG-005 (MEDIUM): Decimal Level values accepted
_egd_store.record_issue(
    severity="Medium",
    module="Entity Group Definition",
    category="Validation",
    description="Decimal Level values (e.g., 3.5) are accepted without validation. "
                "The Level field has no step='1' attribute, allowing fractional values. "
                "Entity group hierarchy levels should be integers.",
    expected="System should enforce step='1' on the Level field and reject decimal values.",
    actual="Decimal levels are accepted and stored as-is.",
    test_ref="EGD-B02",
    status="Open",
)

# BUG-006 (LOW): Special characters in Entity Group Name accepted
_egd_store.record_issue(
    severity="Low",
    module="Entity Group Definition",
    category="Validation",
    description="Special characters like !@#$%^&*() are accepted in Entity Group Name "
                "without any sanitization or validation. While some special characters "
                "may be acceptable, characters like <, >, or script tags could pose "
                "security risks.",
    expected="System should sanitize or restrict special characters in names.",
    actual="All special characters are accepted without validation.",
    test_ref="EGD-C08",
    status="Open",
)

# BUG-007 (LOW): No maxlength on Entity Group Name
_egd_store.record_issue(
    severity="Low",
    module="Entity Group Definition",
    category="Validation",
    description="No maxlength attribute on the Entity Group Name input field. Names "
                "of 255+ characters are accepted and stored without truncation or "
                "validation error.",
    expected="System should enforce a reasonable maxlength (e.g., 255 chars) "
             "and show inline validation if exceeded.",
    actual="No maxlength constraint. Extremely long names are stored as-is.",
    test_ref="EGD-C06, EGD-C07",
    status="Open",
)

# BUG-008 (LOW): No success SweetAlert after create/update
_egd_store.record_issue(
    severity="Low",
    module="Entity Group Definition",
    category="UX",
    description="No success SweetAlert2 popup appears after creating or updating "
                "an Entity Group Definition. The form popup simply closes with no "
                "confirmation to the user that the action succeeded.",
    expected="A success alert like 'Entity Group Definition created successfully' "
             "should appear after create/update.",
    actual="Popup closes silently. No success confirmation shown to user.",
    test_ref="EGD-C02, EGD-E02, EGD-E05",
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
    _egd_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_egd_store)
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
        _egd_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _egd_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _egd_store.results, output_dir, issues=_egd_store.known_issues
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
