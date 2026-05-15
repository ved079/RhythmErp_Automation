"""
conftest.py - Crop Master (RhythmERP Commodity Settings)

Pytest fixtures for Crop Master test suite.
Handles browser setup, login, page object creation,
and report generation with known-issues tracking.

44 test cases across 6 classes:
  - TestCreateFormValidations (15)
  - TestFileUpload (5)
  - TestEditFormValidations (5)
  - TestSearchFilter (5)
  - TestPopupUIBehaviors (6)
  - TestHistoryValidations (8)
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
from pages.commodity_settings.modules.crop_master.crop_master_page import CropMasterPage
from pages.commodity_settings.modules.crop_master.cm_report_generator import cm_report


# ═══════════════════════════════════════════
#  Known Issues for Crop Master (9 Bugs)
# ═══════════════════════════════════════════

CROP_MASTER_KNOWN_ISSUES = [
    {
        'id': 'BUG-CM01',
        'phase': 'Create',
        'description': 'Blank (spaces-only) Name accepted on Create',
        'expected': 'System should reject spaces-only input with validation error',
        'actual': "Spaces-only name '   ' accepted and saved without any warning",
        'severity': 'High',
    },
    {
        'id': 'BUG-CM02',
        'phase': 'Create/Edit',
        'description': 'Duplicate Crop Name allowed in Create and Edit',
        'expected': "System should show validation error 'Crop Name already exists'",
        'actual': 'Duplicate name accepted and saved without any warning',
        'severity': 'High',
    },
    {
        'id': 'BUG-CM03',
        'phase': 'Create',
        'description': 'Leading/trailing spaces NOT trimmed in Name',
        'expected': 'System should trim leading/trailing spaces before saving',
        'actual': 'Spaces preserved as-is in the Name field, causing duplicates',
        'severity': 'Medium',
    },
    {
        'id': 'BUG-CM04',
        'phase': 'Create/Edit',
        'description': 'No per-field inline error messages',
        'expected': 'Each invalid field should show inline error message below it',
        'actual': 'No inline error messages appear — only generic SweetAlert2 popup',
        'severity': 'Low-Medium',
    },
    {
        'id': 'BUG-CM05',
        'phase': 'Create',
        'description': 'No max length validation on Name',
        'expected': 'System should restrict or truncate names at 255 chars',
        'actual': 'Names with 256+ chars accepted without error',
        'severity': 'Low',
    },
    {
        'id': 'BUG-CM06',
        'phase': 'Create',
        'description': 'Special characters accepted in Name without sanitization',
        'expected': 'System should reject or sanitize special character input',
        'actual': 'Special chars like !@#$%^&*() stored and displayed as-is',
        'severity': 'Low-Medium',
    },
    {
        'id': 'BUG-CM07',
        'phase': 'History',
        'description': 'RhythmERP does not create history entries on creation',
        'expected': 'History should show at least 1 row after creating a crop',
        'actual': 'After creating a crop, History popup shows 0 rows',
        'severity': 'Medium',
    },
    {
        'id': 'BUG-CM08',
        'phase': 'History',
        'description': "Column sort doesn't reorder rows",
        'expected': 'Clicking sortable column should reorder rows ascending/descending',
        'actual': 'Sort indicators toggle but rows stay in same order',
        'severity': 'Medium',
    },
    {
        'id': 'BUG-CM09',
        'phase': 'Edit',
        'description': 'Blank (spaces-only) Name accepted on Edit/Update',
        'expected': 'System should reject spaces-only input during edit',
        'actual': 'Spaces-only name accepted and updated without any warning',
        'severity': 'High',
    },
]


# ═══════════════════════════════════════════
#  Session-Scoped Fixtures
# ═══════════════════════════════════════════

@pytest.fixture(scope='session')
def driver():
    """Session-scoped browser driver — one instance for all tests."""
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Crop Master Tests)...")
    log.separator()
    driver = get_driver()
    driver.maximize_window()
    yield driver
    log.separator()
    log.info("CLOSING BROWSER...")
    log.separator()
    driver.quit()


@pytest.fixture(scope='session')
def logged_in_driver(driver):
    """Login once for the entire test session."""
    log.separator()
    log.info("LOGGING INTO RHYTHMERP...")
    log.separator()
    driver.get(RHYTHMERP_LOGIN_URL)
    time.sleep(2)

    login_page = LoginPage(driver)

    # Step 1: Enter email
    log.step(1, "Entering email: " + RHYTHMERP_EMAIL)
    login_page.enter_email(RHYTHMERP_EMAIL)
    time.sleep(0.5)

    # Step 2: Enter password
    log.step(2, "Entering password")
    login_page.enter_password(RHYTHMERP_PASSWORD)
    time.sleep(0.5)

    # Step 3: Select facility by index 0
    log.step(3, "Selecting facility (Agdi — first option)")
    login_page.select_facility_by_index(0)
    time.sleep(1)

    # Step 4: Click Login (JS click required)
    log.step(4, "Clicking Login button")
    login_page.click_login()
    time.sleep(3)

    # Wait for login complete
    login_page.wait_for_login_complete()
    log.info("RhythmERP login successful!")

    return driver


# ═══════════════════════════════════════════
#  Function-Scoped Fixtures
# ═══════════════════════════════════════════

@pytest.fixture(scope='function')
def crop_master_page(logged_in_driver):
    """Function-scoped page fixture — fresh navigate_to_page() per test.
    Includes driver.refresh() to clear SPA state.
    """
    page = CropMasterPage(logged_in_driver)
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
def _cm_report_generator():
    """Session-scoped report generator.
    Starts timer, registers known issues, yields, then
    generates Excel report at session end.
    """
    cm_report.start()

    # Register known issues
    for issue in CROP_MASTER_KNOWN_ISSUES:
        cm_report.add_known_issue(
            issue_id=issue['id'],
            phase=issue['phase'],
            description=issue['description'],
            expected=issue['expected'],
            actual=issue['actual'],
            severity=issue['severity'],
        )

    yield

    cm_report.finish()
    try:
        report_dir = os.path.join(
            os.path.dirname(__file__), '..', 'reports'
        )
        report_path = cm_report.generate_excel(report_dir)
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
        'TestFileUpload',
        'TestEditFormValidations',
        'TestSearchFilter',
        'TestPopupUIBehaviors',
        'TestHistoryValidations',
    ]
    items.sort(key=lambda item: class_order.index(item.cls.__name__)
               if item.cls and item.cls.__name__ in class_order else 999)
