"""
conftest.py - Item Group (RhythmERP)
------------------------------------
Pytest fixtures and report generation hooks for Item Group automation.

Location: Commodity Settings > Commodity Master > Item Group
URL:      /#/dynamic-screens/Item%20Group

Known Issues recorded in CSReportStore:
  BEH-004 : Duplicate Codes allowed (no uniqueness check)
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
    log.info("LAUNCHING BROWSER (RhythmERP - Item Group Tests)...")
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
def ig_page(logged_in_driver):
    """Item Group page object — fresh navigation for each test."""
    from pages.commodity_settings.modules.item_group.item_group_page import (
        ItemGroupPage,
    )
    page = ItemGroupPage(logged_in_driver)
    page.navigate_to_page()
    yield page


# ================================================================
# REPORT GENERATOR HOOKS
# ================================================================

_ig_store = CSReportStore()

# ---- Item Group Known Issues ----

# BEH-004: Duplicate Codes allowed
_ig_store.record_issue(
    severity="High",
    module="Item Group",
    category="Data Integrity",
    description="Duplicate Item Group Codes are allowed in the Create form. "
                "Two or more Item Groups with identical Code can exist in the "
                "system with no warning or rejection.",
    expected="System should show a validation error like 'Code already exists' "
             "and keep the form open for correction.",
    actual="Duplicate Code is accepted and saved without any warning.",
    test_ref="IG-C04, IG-D01",
    status="Open",
)

# BEH-004: Duplicate Codes allowed in Edit
_ig_store.record_issue(
    severity="High",
    module="Item Group",
    category="Data Integrity",
    description="Duplicate Item Group Codes are allowed in the Edit form. "
                "Editing an Item Group to use another Item Group's Code is accepted.",
    expected="System should reject duplicate Code during edit.",
    actual="Duplicate Code accepted in Edit with no error.",
    test_ref="IG-D02, IG-E04",
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
    _ig_store.start_test(item.name, item.nodeid)

    _capture_handler = _LogCapture(_ig_store)
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
        _ig_store.finish_test(status, error)


def pytest_sessionfinish(session, exitstatus):
    """Generate Excel report at end of test session."""
    if not _ig_store.has_results():
        return
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports"
    )
    try:
        filepath = generate_cs_report(
            _ig_store.results, output_dir, issues=_ig_store.known_issues
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
