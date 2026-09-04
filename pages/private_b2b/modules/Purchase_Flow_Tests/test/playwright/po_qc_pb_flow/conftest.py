"""
Conftest for PO → QC → PB flow tests.

Uses a dedicated login: kedar@rhythmflows.com / Kedar@999999 → tenant: Ganesh Agrotech Pvt Ltd.
Completely isolated from the main session fixtures — does not share browser or login
with any other test module.
"""

import os
import sys
import pytest
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.private_b2b.modules.purchase_order.po_playwright_page import POPlaywrightPage
from pages.private_b2b.modules.qc.qc_playwright_page import QCPlaywrightPage
from pages.private_b2b.modules.purchase_booking.pb_playwright_page import PBPlaywrightPage

LOGIN_URL = os.environ.get("RHYTHMERP_LOGIN_URL", "https://rhythmerp.algorhythms.in")
EMAIL     = os.environ.get("RHYTHMERP_PO_QC_PB_EMAIL",    "Bhagyesh123@admin.com")
PASSWORD  = os.environ.get("RHYTHMERP_PO_QC_PB_PASSWORD", "Saii@123456abc")
TENANT    = os.environ.get("RHYTHMERP_PO_QC_PB_TENANT",   "Janardhan FPC")


def pytest_configure(config):
    config.addinivalue_line("markers", "po_qc_pb: PO to QC to PB flow tests")


@pytest.fixture(scope="class")
def integration_state():
    """Shared dict for passing state between sequential test steps in a class."""
    return {}


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance):
    b = playwright_instance.chromium.launch(headless=False, slow_mo=150)
    yield b
    b.close()


@pytest.fixture(scope="session")
def browser_context(browser):
    ctx = browser.new_context()
    yield ctx
    ctx.close()


@pytest.fixture(scope="session")
def logged_in_page(browser_context):
    """Login as kedar@rhythmflows.com and select tenant 'Ganesh Agrotech Pvt Ltd.'."""
    page = browser_context.new_page()
    page.goto(LOGIN_URL)

    page.wait_for_selector("input[name='Username']", timeout=15000)
    page.fill("input[name='Username']", EMAIL)
    page.fill("input[name='Password']", PASSWORD)
    page.locator("button[type='submit']").click()
    page.wait_for_timeout(2000)

    # Tenant selector — search and pick exact match
    page.wait_for_selector("mat-select", timeout=15000)
    page.locator("mat-select").first.click(force=True)
    page.wait_for_selector(".dd-search-input", timeout=10000)
    page.locator(".dd-search-input").fill(TENANT)
    page.wait_for_timeout(800)
    for opt in page.locator(".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text").all():
        if opt.inner_text().strip() == TENANT:
            opt.click(force=True)
            break
    page.wait_for_timeout(500)

    page.locator("button[type='submit']").click()
    page.wait_for_url(
        lambda url: "signin" not in url.lower() and "authentication" not in url.lower(),
        timeout=20000,
    )
    page.wait_for_timeout(1500)

    yield page
    page.close()


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
