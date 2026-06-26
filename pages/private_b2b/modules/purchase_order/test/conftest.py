import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log


def pytest_configure(config):
    config.addinivalue_line("markers", "api: Pure API tests — no browser needed")
    config.addinivalue_line("markers", "schema: Schema and structure verification")
    config.addinivalue_line("markers", "calculation: Computed field verification")
    config.addinivalue_line("markers", "smoke: Critical happy-path tests")
    config.addinivalue_line("markers", "hybrid: API creates data + UI verifies display")
    config.addinivalue_line("markers", "ui: Popup/toggle/behavior checks")
    config.addinivalue_line("markers", "performance: Speed and benchmark tests")
    config.addinivalue_line("markers", "update: PO update/edit tests")


@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Purchase Order Tests)...")
    log.separator()
    from common.browser_utils import get_driver
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
    from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD
    from pages.login_screens.Login_Screens_.login_page import LoginPage

    log.separator()
    log.info("LOGGING INTO RHYTHMERP (Purchase Order)...")
    log.separator()

    login_page = LoginPage(driver)
    log.info("Navigating to: " + str(RHYTHMERP_LOGIN_URL))
    driver.get(RHYTHMERP_LOGIN_URL)
    login_page.wait_seconds(2)
    login_page.enter_email(RHYTHMERP_EMAIL)
    login_page.enter_password(RHYTHMERP_PASSWORD)
    login_page.wait_seconds(1)
    login_page.click_login()
    login_page.wait_seconds(3)
    login_page.wait_for_login_complete()
    if "login" in driver.current_url.lower():
        raise RuntimeError("RhythmERP login failed — still on login page after wait.")
    log.info("RhythmERP login successful!")
    yield driver


@pytest.fixture
def po_page(logged_in_driver):
    from pages.private_b2b.modules.purchase_order.purchase_order_page import (
        PurchaseOrderPage,
    )
    page = PurchaseOrderPage(logged_in_driver)
    try:
        page.navigate_to_page()
    except Exception:
        log.warning("Page navigation failed — test may skip")
    yield page


@pytest.fixture(scope="session")
def erp_api():
    from common.erp_api_client import RhythmERPAPIClient
    token = os.environ.get("ERP_TOKEN", "").strip()
    tenant_id = os.environ.get("ERP_TENANT_ID", "711")
    client = RhythmERPAPIClient()
    if token:
        client.login_from_browser(token=token, tenant_id=tenant_id)
    else:
        try:
            client.login()
        except Exception:
            pytest.skip("No ERP token available. Set ERP_TOKEN env var.")
    yield client
    try:
        client.close()
    except Exception:
        pass


@pytest.fixture
def po_api(erp_api):
    from pages.private_b2b.modules.purchase_order.utils.api_purchase_order_utils import (
        POAPIUtils,
    )
    return POAPIUtils(api_client=erp_api)
