import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from common.erp_api_client import RhythmERPAPIClient
from pages.login_screens.Login_Screens_.login_page import LoginPage
from pages.private_b2b.modules.quality_check.utils.api_quality_check_utils import QCAPIUtils


def pytest_configure(config):
    config.addinivalue_line("markers", "api: API-level tests")
    config.addinivalue_line("markers", "schema: Schema validation tests")
    config.addinivalue_line("markers", "smoke: Critical path smoke tests")
    config.addinivalue_line("markers", "hybrid: API + UI hybrid tests")
    config.addinivalue_line("markers", "ui: UI-only tests")
    config.addinivalue_line("markers", "performance: Performance benchmark tests")
    config.addinivalue_line("markers", "update: Update operation tests")


@pytest.fixture(scope="session")
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


@pytest.fixture(scope="session")
def logged_in_driver(driver):
    login_page = LoginPage(driver)
    login_page.login_default()
    return driver


@pytest.fixture
def qc_page(logged_in_driver):
    from pages.private_b2b.modules.quality_check.quality_check_page import (
        QualityCheckPage,
    )
    page = QualityCheckPage(logged_in_driver)
    page.navigate_to_page()
    return page


@pytest.fixture(scope="session")
def erp_api():
    token = os.environ.get("ERP_TOKEN", "")
    tenant_id = os.environ.get("ERP_TENANT_ID", "711")
    client = RhythmERPAPIClient(tenant_id=tenant_id)
    if token:
        client.login_from_browser(token=token, tenant_id=tenant_id)
    else:
        client.login()
    return client


@pytest.fixture
def qc_api(erp_api):
    return QCAPIUtils(api_client=erp_api)
