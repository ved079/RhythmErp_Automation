"""
conftest.py - Designation (RhythmERP Common Settings)

Pytest fixtures for Designation test suite.
Handles browser setup, login, page object creation,
and report generation with known-issues tracking.
"""

import os
import sys
import time
import pytest

# Resolve project root
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.browser_utils import get_driver
from common.logger import log
from config import (
    RHYTHMERP_LOGIN_URL,
    RHYTHMERP_EMAIL,
    RHYTHMERP_PASSWORD,
)
from pages.login_screens.Login_Screens_.login_page import LoginPage
from pages.common_settings.modules.designation.designation_page import DesignationPage
from pages.common_settings.modules.designation.des_report_generator import des_report


# ═══════════════════════════════════════════
#  Known Issues for Designation
# ═══════════════════════════════════════════

DESIGNATION_KNOWN_ISSUES = [
    {
        'id': 'DES-01',
        'phase': 'Create/Edit',
        'description': 'Duplicate Designation Name allowed',
        'expected': 'System should reject duplicate name',
        'actual': 'Duplicate name accepted without warning',
        'severity': 'High',
    },
    {
        'id': 'DES-02',
        'phase': 'Create',
        'description': 'No max length validation on Name',
        'expected': 'Should restrict or truncate at 255 chars',
        'actual': '256+ char names accepted (submit may silently fail)',
        'severity': 'Low',
    },
    {
        'id': 'DES-02b',
        'phase': 'Create',
        'description': 'type="character" rejects punctuation in Name',
        'expected': 'Names like "Jr. Manager", "Vice-President" should be valid',
        'actual': 'type="character" only allows letters and spaces — dots, commas, hyphens, parens all rejected as "Invalid Name"',
        'severity': 'Medium',
    },
    {
        'id': 'DES-03',
        'phase': 'Filter',
        'description': 'Apply Filters button completely non-functional',
        'expected': 'Apply Filters should filter table rows',
        'actual': 'Apply Filters click has zero effect',
        'severity': 'Critical',
    },
    {
        'id': 'DES-04',
        'phase': 'History',
        'description': 'History shows no data after creation',
        'expected': 'History should record create/edit actions',
        'actual': 'History popup shows "No data available"',
        'severity': 'Medium',
    },
    {
        'id': 'DES-05',
        'phase': 'Create',
        'description': '256-char Name submit silently fails',
        'expected': 'Should show error or success message',
        'actual': 'No SweetAlert2 response — form stays open with no feedback',
        'severity': 'Medium',
    },
]


# ═══════════════════════════════════════════
#  Session-Scoped Fixtures
# ═══════════════════════════════════════════

@pytest.fixture(scope='session')
def driver():
    """Session-scoped browser driver — one instance for all tests."""
    log.info("Starting Designation Test Session")
    driver = get_driver()
    driver.maximize_window()
    yield driver
    log.info("Ending Designation Test Session")
    driver.quit()


@pytest.fixture(scope='session')
def logged_in_driver(driver):
    """Login once for the entire test test session."""
    log.info("Logging into RhythmERP")
    driver.get(RHYTHMERP_LOGIN_URL)
    time.sleep(2)

    login_page = LoginPage(driver)

    # Enter email
    login_page.enter_email(RHYTHMERP_EMAIL)
    time.sleep(0.5)

    # Enter password
    login_page.enter_password(RHYTHMERP_PASSWORD)
    time.sleep(0.5)

    # Select facility by index 0
    login_page.select_facility_by_index(0)
    time.sleep(1)

    # Click Login (JS click required)
    login_page.click_login()
    time.sleep(3)

    # Wait for login complete
    login_page.wait_for_login_complete()
    log.info("Login successful — dashboard loaded")

    return driver


# ═══════════════════════════════════════════
#  Function-Scoped Fixtures
# ═══════════════════════════════════════════

@pytest.fixture(scope='function')
def designation_page(logged_in_driver):
    """Function-scoped page fixture — fresh navigate_to_page() per test."""
    page = DesignationPage(logged_in_driver)
    page.navigate_to_page()
    yield page
    # Cleanup: force close any leftover popups/overlays
    try:
        page._force_close_panels()
        page.force_close_form_popup()
    except Exception:
        pass


# ═══════════════════════════════════════════
#  Report Generator Fixture
# ═══════════════════════════════════════════

@pytest.fixture(scope='session', autouse=True)
def _des_report_generator():
    """
    Session-scoped report generator.
    Starts timer, registers known issues, yields, then
    generates Excel report at session end.
    """
    des_report.start()

    # Register known issues into the report store
    for issue in DESIGNATION_KNOWN_ISSUES:
        des_report.add_known_issue(
            issue_id=issue['id'],
            phase=issue['phase'],
            description=issue['description'],
            expected=issue['expected'],
            actual=issue['actual'],
            severity=issue['severity'],
        )

    yield

    # Generate report at session end
    des_report.finish()
    try:
        report_dir = os.path.join(
            os.path.dirname(__file__), '..', 'reports'
        )
        report_path = des_report.generate_excel(report_dir)
        log.info(f"Report generated: {report_path}")
    except Exception as e:
        log.warning(f"Report generation failed: {e}")


# ═══════════════════════════════════════════
#  Pytest Hooks
# ═══════════════════════════════════════════

def pytest_collection_modifyitems(items):
    """Sort tests by class order for consistent execution."""
    class_order = [
        'TestCreateFormValidations',
        'TestStatusToggleValidations',
        'TestEditFormValidations',
        'TestSearchFilter',
        'TestPopupUIBehaviors',
        'TestHistoryValidations',
    ]
    items.sort(key=lambda item: class_order.index(item.cls.__name__)
               if item.cls and item.cls.__name__ in class_order else 999)
