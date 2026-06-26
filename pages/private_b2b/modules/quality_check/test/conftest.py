import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

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
    from common.browser_utils import get_driver
    from common.logger import log
    log.separator()
    log.info("LAUNCHING BROWSER (RhythmERP - QC Tests)...")
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
    from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD
    from common.logger import log

    log.separator()
    log.info("LOGGING INTO RHYTHMERP (Quality Check)...")
    log.separator()

    login_page = LoginPage(driver)
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
