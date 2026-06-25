"""
conftest.py — Register of Loan Screen (RhythmERP)
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from common.browser_utils import get_driver
from pages.login_screens.Login_Screens_.login_page import LoginPage
from common.screenshot_broadcast import (
    start as start_screenshot_broadcast,
    stop as stop_screenshot_broadcast,
)
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD


@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Register of Loan Tests)...")
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
    log.separator()
    log.info("LOGGING INTO RHYTHMERP...")
    log.separator()

    login_page = LoginPage(driver)
    driver.get(RHYTHMERP_LOGIN_URL)
    login_page.wait_seconds(2)
    login_page.enter_email(RHYTHMERP_EMAIL)
    login_page.enter_password(RHYTHMERP_PASSWORD)
    login_page._dismiss_tenant_dropdown()
    login_page.click_login()
    login_page.wait_seconds(3)
    login_page.wait_for_login_complete()

    log.info("RhythmERP login successful!")
    start_screenshot_broadcast(driver)

    yield driver

    stop_screenshot_broadcast()


@pytest.fixture(scope="function")
def loan_page(logged_in_driver):
    from pages.registration.modules.register_of_loan.register_of_loan_page import (
        RegisterOfLoanPage,
    )

    page = RegisterOfLoanPage(logged_in_driver)
    page.navigate_to_page()
    yield page
    try:
        page.force_close_form_popup()
    except Exception:
        pass


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: Critical happy-path tests")
    config.addinivalue_line("markers", "sanity: Core feature validation tests")
    config.addinivalue_line("markers", "regression: Full coverage tests")
    config.addinivalue_line("markers", "ui: Popup, dialog, form UI behavior checks")
