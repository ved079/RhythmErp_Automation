"""
conftest.py - Designation (RhythmERP Common Settings) v2 OPTIMISED

Key change: NO navigate_to_page() per test — just hard_refresh if already on page.
Saves ~5-10s per test (full page navigation vs simple refresh).
"""

import os
import sys
import time
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.browser_utils import get_driver
from common.logger import log
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD
from pages.login_screens.Login_Screens_.login_page import LoginPage
from common.screenshot_broadcast import start as start_screenshot_broadcast, stop as stop_screenshot_broadcast
from pages.common_settings.modules.designation.designation_page import DesignationPage
from pages.common_settings.modules.designation.des_report_generator import des_report

DESIGNATION_KNOWN_ISSUES = [
    {'id': 'DES-01', 'phase': 'Create/Edit', 'description': 'Duplicate Designation Name allowed',
     'expected': 'System should reject duplicate name', 'actual': 'Duplicate name accepted without warning', 'severity': 'High'},
    {'id': 'DES-02', 'phase': 'Create', 'description': 'No max length validation on Name',
     'expected': 'Should restrict or truncate at 255 chars', 'actual': '256+ char names accepted (submit may silently fail)', 'severity': 'Low'},
    {'id': 'DES-02b', 'phase': 'Create', 'description': 'type="character" rejects punctuation in Name',
     'expected': 'Names like "Jr. Manager", "Vice-President" should be valid',
     'actual': 'type="character" only allows letters and spaces — dots, commas, hyphens, parens all rejected as "Invalid Name"', 'severity': 'Medium'},
    {'id': 'DES-03', 'phase': 'Filter', 'description': 'Apply Filters button completely non-functional',
     'expected': 'Apply Filters should filter table rows', 'actual': 'Apply Filters click has zero effect', 'severity': 'Critical'},
    {'id': 'DES-04', 'phase': 'History', 'description': 'History shows no data after creation',
     'expected': 'History should record create/edit actions', 'actual': 'History popup shows "No data available"', 'severity': 'Medium'},
    {'id': 'DES-05', 'phase': 'Create', 'description': '256-char Name submit silently fails',
     'expected': 'Should show error or success message', 'actual': 'No SweetAlert2 response — form stays open with no feedback', 'severity': 'Medium'},
]


@pytest.fixture(scope='session')
def driver():
    log.info("Starting Designation Test Session")
    driver = get_driver()
    driver.maximize_window()
    yield driver
    stop_screenshot_broadcast()
    driver.quit()


@pytest.fixture(scope='session')
def logged_in_driver(driver):
    log.info("Logging into RhythmERP")
    driver.get(RHYTHMERP_LOGIN_URL)
    time.sleep(2)
    login_page = LoginPage(driver)
    login_page.enter_email(RHYTHMERP_EMAIL)
    time.sleep(0.5)
    login_page.enter_password(RHYTHMERP_PASSWORD)
    time.sleep(1)
    login_page.click_login()
    time.sleep(3)
    login_page.wait_for_login_complete()
    if "login" in driver.current_url.lower():
        raise RuntimeError("Login failed — still on login page")
    log.info("Login successful!")
    start_screenshot_broadcast(driver)
    return driver


@pytest.fixture(scope='function')
def designation_page(logged_in_driver):
    """Smart fixture: navigate only if not already on Designation page, else hard_refresh."""
    page = DesignationPage(logged_in_driver)
    if 'Designation' not in logged_in_driver.current_url:
        page.navigate_to_page()
    else:
        page.hard_refresh()
    yield page
    # NO cleanup here — test _cleanup() handles it


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: Core CRUD + critical path tests (8 tests)")
    config.addinivalue_line("markers", "sanity: All 44 tests — full module sanity check")
    config.addinivalue_line("markers", "regression: All 44 tests — full regression suite")
    config.addinivalue_line("markers", "bug: Known bugs (7 tests)")
    config.addinivalue_line("markers", "ui: UI interaction tests (32 tests)")


@pytest.fixture(scope='session', autouse=True)
def _des_report_generator():
    des_report.start()
    for issue in DESIGNATION_KNOWN_ISSUES:
        des_report.add_known_issue(**issue)
    yield
    des_report.finish()
    try:
        report_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
        report_path = des_report.generate_excel(report_dir)
        log.info(f"Report generated: {report_path}")
    except Exception as e:
        log.warning(f"Report generation failed: {e}")


def pytest_collection_modifyitems(items):
    class_order = ['TestCreateFormValidations', 'TestStatusToggleValidations',
                   'TestEditFormValidations', 'TestSearchFilter',
                   'TestPopupUIBehaviors', 'TestHistoryValidations']
    items.sort(key=lambda item: class_order.index(item.cls.__name__)
               if item.cls and item.cls.__name__ in class_order else 999)
