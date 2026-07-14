"""
Conftest for Direct PB creation tests.

Login: kedar@rhythmflows.com / Kedar@999999 -> tenant: Eco Green Pvt Ltd.
Isolated from all other test modules — separate browser and session.
"""

import os
import sys
import pytest
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.private_b2b.modules.purchase_booking.direct_pb_playwright_page import DirectPBPlaywrightPage

LOGIN_URL = os.environ.get("RHYTHMERP_LOGIN_URL", "https://rhythmerp.algorhythms.in")
EMAIL     = os.environ.get("RHYTHMERP_DIRECT_PB_EMAIL",    "kedar@rhythmflows.com")
PASSWORD  = os.environ.get("RHYTHMERP_DIRECT_PB_PASSWORD", "Kedar@999999")
TENANT    = os.environ.get("RHYTHMERP_DIRECT_PB_TENANT",   "Eco Green Pvt Ltd")


def pytest_configure(config):
    config.addinivalue_line("markers", "direct_pb: Direct PB creation tests")


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
    """Login as kedar@rhythmflows.com and select tenant 'Eco Green Pvt Ltd'."""
    page = browser_context.new_page()
    page.goto(LOGIN_URL)

    page.wait_for_selector("input[name='Username']", timeout=15000)
    page.fill("input[name='Username']", EMAIL)
    page.fill("input[name='Password']", PASSWORD)
    page.locator("button[type='submit']").click()
    page.wait_for_timeout(2000)

    page.wait_for_selector("mat-select[aria-label], mat-select", timeout=15000)
    page.locator("mat-select").first.click(force=True)
    page.wait_for_selector(".dd-search-input", timeout=10000)
    page.locator(".dd-search-input").fill(TENANT)
    page.wait_for_timeout(800)
    for opt in page.locator(".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text").all():
        if opt.inner_text().strip() == TENANT:
            opt.click(force=True)
            break
    # Wait for the dropdown overlay to close before clicking submit
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


@pytest.fixture(scope="function")
def pb_page(logged_in_page):
    p = DirectPBPlaywrightPage(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass
