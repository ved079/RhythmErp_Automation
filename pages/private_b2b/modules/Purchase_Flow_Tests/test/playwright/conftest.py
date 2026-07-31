import os
import sys
import pytest
from playwright.sync_api import sync_playwright
from pages.private_b2b.modules.purchase_order.po_playwright_page import POPlaywrightPage
from pages.private_b2b.modules.gate_pass.gp_playwright_page import GPPlaywrightPage
from pages.private_b2b.modules.goods_receipt_note.grn_playwright_page import GRNPlaywrightPage
from pages.private_b2b.modules.quality_check.qc_playwright_page import QCPlaywrightPage
from pages.private_b2b.modules.purchase_booking.pb_playwright_page import PBPlaywrightPage

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

RHYTHMERP_LOGIN_URL = os.environ.get("RHYTHMERP_LOGIN_URL", "https://rhythmerp.algorhythms.in")
RHYTHMERP_EMAIL     = os.environ.get("RHYTHMERP_EMAIL", "")
RHYTHMERP_PASSWORD  = os.environ.get("RHYTHMERP_PASSWORD", "")


def pytest_configure(config):
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
    """Explicit browser context — required so multiple tabs can share the same session."""
    ctx = browser.new_context(viewport={"width": 1366, "height": 768})
    yield ctx
    ctx.close()


@pytest.fixture(scope="class")
def logged_in_page(browser_context):
    page = browser_context.new_page()
    page.goto(RHYTHMERP_LOGIN_URL)
    page.wait_for_selector("input[name='Username']", timeout=15000)
    page.fill("input[name='Username']", RHYTHMERP_EMAIL)
    page.fill("input[name='Password']", RHYTHMERP_PASSWORD)
    page.locator("button[type='submit']").click()
    page.wait_for_timeout(1000)
    try:
        page.locator("button[type='submit']").click()
    except Exception:
        pass
    page.wait_for_url(
        lambda url: "signin" not in url.lower() and "authentication" not in url.lower(),
        timeout=20000,
    )
    yield page
    page.close()


@pytest.fixture(scope="class")
def integration_state():
    """Shared dict for passing state between sequential test steps in a class."""
    return {}


@pytest.fixture(scope="function")
def po_page(logged_in_page):
    p = POPlaywrightPage(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass


@pytest.fixture(scope="function")
def gp_page(logged_in_page):
    p = GPPlaywrightPage(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass


@pytest.fixture(scope="function")
def grn_page(logged_in_page):
    p = GRNPlaywrightPage(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass


# ── Tab 2 fixtures (same session, second browser tab) ───────────────────────
# Used in full-cycle tests to run GP2+GRN2 in a separate tab while Tab 1 stays
# on its current page — mirrors real-world multi-tab usage and saves navigation time.

@pytest.fixture(scope="class")
def tab2_page(browser_context):
    """Second browser tab — same context as Tab 1, so session/cookies are shared."""
    new_tab = browser_context.new_page()
    yield new_tab
    try:
        new_tab.close()
    except Exception:
        pass


@pytest.fixture(scope="function")
def gp_page_tab2(tab2_page):
    p = GPPlaywrightPage(tab2_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass


@pytest.fixture(scope="function")
def qc_page(logged_in_page):
    p = QCPlaywrightPage(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass


@pytest.fixture(scope="function")
def pb_page(logged_in_page):
    p = PBPlaywrightPage(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass


@pytest.fixture(scope="function")
def grn_page_tab2(tab2_page):
    p = GRNPlaywrightPage(tab2_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass
