"""
conftest.py - Role Creation Screen Access Settings (RhythmERP)
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


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Role Creation Screen Tests)...")
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
def role_page(logged_in_driver):
    """Role Creation Screen page object — fresh navigation for each test."""
    from pages.access.modules.role_creation_screen.role_creation_screen_page import (
        RoleCreationScreenPage,
    )
    page = RoleCreationScreenPage(logged_in_driver)
    page.navigate_to_role_creation_screen()
    yield page


@pytest.fixture(scope="session")
def seed_role(logged_in_driver):
    """Create a seed role that other phases can reference.
    Returns the payload dict used for creation."""
    from pages.access.modules.role_creation_screen.role_creation_screen_page import (
        RoleCreationScreenPage,
    )
    from pages.access.modules.role_creation_screen.data.role_creation_screen_data import (
        create_payload,
    )
    page = RoleCreationScreenPage(logged_in_driver)
    page.navigate_to_role_creation_screen()

    payload = create_payload()
    page.create_role(
        name=payload["name"],
        description=payload["description"],
        code=payload["code"],
    )
    try:
        page.wait_for_success_and_dismiss()
    except Exception:
        page._force_close_panels()

    page.navigate_to_role_creation_screen()
    page.wait_for_table_to_load()

    return payload


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_rcs_store = CSReportStore()

# ---- Role Creation Screen Known Issues ----

# BUG-301 (HIGH): Duplicate role with case-flipped name accepted
_rcs_store.record_issue(
    severity="High",
    module="Role Creation Screen",
    category="Data Integrity",
    description="Case-insensitive duplicate Role Names are NOT blocked. "
                "If 'AdminRole' exists, creating 'adminrole' or 'ADMINROLE' is "
                "accepted as a new record. This leads to data duplication and "
                "confusion in role-based access control.",
    expected="System should perform a case-insensitive comparison and reject "
             "duplicate role names regardless of casing.",
    actual="Case-variant duplicates are accepted as separate records.",
    test_ref="RCS-D02",
    status="Open",
)

# BUG-302 (HIGH): Duplicate role with extra spaces accepted
_rcs_store.record_issue(
    severity="High",
    module="Role Creation Screen",
    category="Data Integrity",
    description="Duplicate Role Names with extra leading/trailing or internal "
                "spaces are accepted. If 'AdminRole' exists, creating '  AdminRole  ' "
                "or 'Admin  Role' is accepted as a new record. Space-normalised "
                "uniqueness check is missing.",
    expected="System should normalise spaces and reject duplicate names after "
             "trimming and collapsing internal spaces.",
    actual="Space-variant duplicates are accepted as separate records.",
    test_ref="RCS-D03",
    status="Open",
)

# BUG-303 (MEDIUM): SQL injection strings accepted in Role Name
_rcs_store.record_issue(
    severity="Medium",
    module="Role Creation Screen",
    category="Security",
    description="SQL injection strings like \"' OR 1=1--\" are accepted in the "
                "Role Name field without any sanitisation or validation. This could "
                "pose a security risk if the input is used in dynamic queries.",
    expected="System should sanitise or reject input containing SQL injection patterns.",
    actual="SQL injection strings are accepted and stored as-is.",
    test_ref="RCS-C07",
    status="Open",
)

# BUG-304 (MEDIUM): XSS script tags accepted in Role Name
_rcs_store.record_issue(
    severity="Medium",
    module="Role Creation Screen",
    category="Security",
    description="XSS script tags like '<script>alert()</script>' are accepted in "
                "the Role Name field without any sanitisation. This could pose a "
                "cross-site scripting risk if the name is rendered without encoding.",
    expected="System should sanitise or reject input containing HTML/script tags.",
    actual="XSS script tags are accepted and stored as-is.",
    test_ref="RCS-C08",
    status="Open",
)

# BUG-305 (HIGH): Edit allows saving with empty Role Name
_rcs_store.record_issue(
    severity="High",
    module="Role Creation Screen",
    category="Validation",
    description="When editing an existing role, clearing the Role Name field and "
                "clicking Update does not trigger a required-field validation error. "
                "The role can be saved with an empty name.",
    expected="System should enforce required-field validation on update, same as create.",
    actual="Empty role name is accepted on edit without any validation error.",
    test_ref="RCS-E05",
    status="Open",
)

# BUG-306 (HIGH): History dialog shows no records after creation
_rcs_store.record_issue(
    severity="High",
    module="Role Creation Screen",
    category="Audit",
    description="The History dialog for a role shows no records even after the "
                "role has been created or edited. The audit trail is not being "
                "populated for the Role Creation Screen module.",
    expected="History should show at least one record (creation) and additional "
             "records after each edit.",
    actual="History dialog shows zero records regardless of create/edit actions.",
    test_ref="RCS-H01, RCS-H03",
    status="Open",
)

# BUG-307 (MEDIUM): Sort on Role Name column does not reorder rows
_rcs_store.record_issue(
    severity="Medium",
    module="Role Creation Screen",
    category="UI",
    description="Clicking the sort header on the Role Name column does not reorder "
                "the table rows. The sort handler appears to be broken or not wired "
                "to the data source.",
    expected="Clicking the sort header should toggle between ascending and "
             "descending order by Role Name.",
    actual="Clicking sort header has no effect — rows remain in original order.",
    test_ref="RCS-S05",
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
    _rcs_store.start_test(item.name, item.nodeid)
    _capture_handler = _LogCapture(_rcs_store)
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
        _rcs_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _rcs_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _rcs_store.results, output_dir, issues=_rcs_store.known_issues
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