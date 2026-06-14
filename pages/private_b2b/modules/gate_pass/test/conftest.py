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
    config.addinivalue_line("markers", "smoke: Critical happy-path tests")
    config.addinivalue_line("markers", "hybrid: API creates data + UI verifies display")
    config.addinivalue_line("markers", "ui: Popup/toggle/behavior checks")
    config.addinivalue_line("markers", "performance: Speed and benchmark tests")
    config.addinivalue_line("markers", "update: GP update/edit tests")


@pytest.fixture(scope="session")
def driver():
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - Gate Pass Tests)...")
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
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    log.separator()
    log.info("LOGGING INTO RHYTHMERP (Gate Pass)...")
    log.separator()

    login_page = LoginPage(driver)
    driver.get(RHYTHMERP_LOGIN_URL)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[formcontrolname='email']"))
    )

    login_page.enter_email(RHYTHMERP_EMAIL)
    login_page.enter_password(RHYTHMERP_PASSWORD)
    login_page._dismiss_tenant_dropdown()

    try:
        login_page.click_login()
    except Exception:
        pass
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "app-root, .main-content, .dashboard"))
    )
    yield driver


@pytest.fixture
def gp_page(logged_in_driver):
    from pages.private_b2b.modules.gate_pass.gate_pass_page import GatePassPage
    page = GatePassPage(logged_in_driver)
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
    client = RhythmERPAPIClient(tenant_id=tenant_id)
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
def gp_api(erp_api):
    from pages.private_b2b.modules.gate_pass.utils.api_gate_pass_utils import GPAPIUtils
    return GPAPIUtils(api_client=erp_api)
