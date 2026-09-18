import os
import sys
import pytest
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.private_b2b.modules.Purchase_Flow_Tests.test.playwright.po_gp_grn_qc_pb.new_tests.pages.po_page import POPage
from pages.private_b2b.modules.Purchase_Flow_Tests.test.playwright.po_gp_grn_qc_pb.new_tests.pages.item_resolver import resolve_chain_config
from pages.private_b2b.modules.Purchase_Flow_Tests.test.playwright.po_gp_grn_qc_pb.new_tests.pages.gp_page import GPPage
from pages.private_b2b.modules.Purchase_Flow_Tests.test.playwright.po_gp_grn_qc_pb.new_tests.pages.grn_page import GRNPage
from pages.private_b2b.modules.Purchase_Flow_Tests.test.playwright.po_gp_grn_qc_pb.new_tests.pages.qc_page import QCPage
from pages.private_b2b.modules.Purchase_Flow_Tests.test.playwright.po_gp_grn_qc_pb.new_tests.pages.pb_page import PBPage

LOGIN_URL = "https://rhythmerp.algorhythms.in"
EMAIL     = "kedar@rhythmflows.com"
PASSWORD  = "Kedar@999999"
TENANT    = "Jay Kisan Ltd"


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: Critical happy-path tests")
    config.addinivalue_line("markers", "integration: Cross-module end-to-end flow tests")


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="class")
def browser(playwright_instance):
    b = playwright_instance.chromium.launch(headless=False, slow_mo=150)
    yield b
    b.close()


@pytest.fixture(scope="class")
def browser_context(browser):
    ctx = browser.new_context(viewport={"width": 1372, "height": 625})
    yield ctx
    ctx.close()


@pytest.fixture(scope="class")
def logged_in_page(browser_context):
    page = browser_context.new_page()
    page.goto(LOGIN_URL)
    page.wait_for_selector("input[name='Username']", timeout=15000)
    page.fill("input[name='Username']", EMAIL)
    page.fill("input[name='Password']", PASSWORD)
    page.locator("button[type='submit']").click()
    page.wait_for_timeout(2000)

    if TENANT:
        page.wait_for_selector("mat-select[aria-label], mat-select", timeout=15000)
        page.locator("mat-select").first.click(force=True)
        page.wait_for_selector(".dd-search-input", timeout=10000)
        page.locator(".dd-search-input").fill(TENANT)
        page.wait_for_timeout(800)
        for opt in page.locator(".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text").all():
            if opt.inner_text().strip() == TENANT:
                opt.click(force=True)
                break
        try:
            page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
        page.wait_for_timeout(300)

    page.locator("button[type='submit']").click(force=True)
    page.wait_for_url(
        lambda url: "signin" not in url.lower() and "authentication" not in url.lower(),
        timeout=20000,
    )
    page.wait_for_timeout(1500)
    yield page
    page.close()


@pytest.fixture(scope="class")
def flow_state():
    """Shared dict for threading ref_nos between steps in a class-scoped flow test."""
    return {}


@pytest.fixture(scope="session")
def _chain_config_future():
    """Kick off the API resolver in a background thread immediately at session start.

    Runs concurrently with browser launch + login so there's no visible delay
    before the first page appears. The future is resolved lazily when first accessed.
    """
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(resolve_chain_config, location_name="Pune")
    yield future
    executor.shutdown(wait=False)


@pytest.fixture(scope="class")
def chain_config(_chain_config_future):
    """Block until the background resolver completes and return its result."""
    return _chain_config_future.result()


@pytest.fixture(scope="function")
def po_page(logged_in_page):
    p = POPage(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass


@pytest.fixture(scope="function")
def gp_page(logged_in_page):
    p = GPPage(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass


@pytest.fixture(scope="function")
def grn_page(logged_in_page):
    p = GRNPage(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass


@pytest.fixture(scope="function")
def qc_page(logged_in_page):
    p = QCPage(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass


@pytest.fixture(scope="function")
def pb_page(logged_in_page):
    p = PBPage(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass
