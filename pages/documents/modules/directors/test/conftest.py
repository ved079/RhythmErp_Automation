import os
import pytest
from playwright.sync_api import sync_playwright
from pages.documents.modules.directors.directors_page import DirectorsPage

RHYTHMERP_LOGIN_URL = os.environ.get("RHYTHMERP_LOGIN_URL", "https://rhythmerp.algorhythms.in")
RHYTHMERP_EMAIL     = os.environ.get("RHYTHMERP_EMAIL", "")
RHYTHMERP_PASSWORD  = os.environ.get("RHYTHMERP_PASSWORD", "")


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="class")
def browser(playwright_instance):
    b = playwright_instance.chromium.launch(headless=True)
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
def dir_page(logged_in_page):
    p = DirectorsPage(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.force_close_popup()
    except Exception:
        pass
