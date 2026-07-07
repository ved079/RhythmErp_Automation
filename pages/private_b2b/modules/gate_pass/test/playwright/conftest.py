import os
import sys
import pytest
from playwright.sync_api import sync_playwright
from pages.private_b2b.modules.gate_pass.gp_playwright_page import GPPlaywrightPage

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

RHYTHMERP_LOGIN_URL = os.environ.get("RHYTHMERP_LOGIN_URL", "https://rhythmerp.algorhythms.in")
RHYTHMERP_EMAIL     = os.environ.get("RHYTHMERP_EMAIL", "")
RHYTHMERP_PASSWORD  = os.environ.get("RHYTHMERP_PASSWORD", "")


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: Critical happy-path tests")
    config.addinivalue_line("markers", "validation: Form validation and error handling")
    config.addinivalue_line("markers", "workflow: Gate pass workflow tests")
    config.addinivalue_line("markers", "regression: Negative and regression tests")


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
def logged_in_page(browser):
    page = browser.new_page()
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


@pytest.fixture(scope="function")
def gp_page(logged_in_page):
    p = GPPlaywrightPage(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass
