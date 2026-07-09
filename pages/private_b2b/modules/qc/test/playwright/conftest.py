import os
import sys
import random
import pytest
from playwright.sync_api import sync_playwright
from pages.private_b2b.modules.qc.qc_playwright_page import QCPlaywrightPage
from pages.private_b2b.modules.qc.cqp_playwright_page import CQPPlaywrightPage
from pages.private_b2b.modules.grn.grn_playwright_page import GRNPlaywrightPage
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
    config.addinivalue_line("markers", "calc: Calculation verification tests")
    config.addinivalue_line("markers", "regression: Negative and regression tests")


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
    ctx = browser.new_context(accept_downloads=True)
    yield ctx
    ctx.close()


@pytest.fixture(scope="session")
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


# ── Single-item GP + GRN (for smoke, calc, validation, regression) ────────

@pytest.fixture(scope="session")
def session_gp_single(logged_in_page):
    gp = GPPlaywrightPage(logged_in_page)
    gp.navigate_to_page()
    ref_no, row_dicts = gp.create_record([(random.randint(1, 5), random.randint(10, 50))])
    supplier_name = logged_in_page.locator("td.cdk-column-supplier_ref_id").first.inner_text().strip()
    item_names = [rd["item_name"] for rd in row_dicts if rd.get("item_name")]
    return supplier_name, ref_no, item_names


@pytest.fixture(scope="session")
def session_grn_single(logged_in_page, session_gp_single):
    supplier_name, _, item_names = session_gp_single
    grn = GRNPlaywrightPage(logged_in_page)
    grn.navigate_to_page()
    grn.open_add_form()
    grn.fill_form(supplier_name, accepted_qty=0)
    gp_qty = grn.read_gp_qty(0)
    accepted = max(1, int(gp_qty) - 1)
    grn._fill_number_nth(grn.ACCEPTED_QTY, 0, accepted)
    grn.page.wait_for_timeout(600)
    grn.page.locator(grn.SUBMIT_BTN).click()
    grn.handle_success_alert()
    grn.navigate_to_page()
    grn_ref_no = grn.get_ref_no_of_first_row()
    return supplier_name, grn_ref_no, item_names


# ── Multi-item GP + GRN (for multi-row calc test) ─────────────────────────

@pytest.fixture(scope="session")
def session_gp_multi(logged_in_page):
    gp = GPPlaywrightPage(logged_in_page)
    gp.navigate_to_page()
    ref_no, row_dicts = gp.create_record(all_items=True)
    supplier_name = logged_in_page.locator("td.cdk-column-supplier_ref_id").first.inner_text().strip()
    item_names = [rd["item_name"] for rd in row_dicts if rd.get("item_name")]
    return supplier_name, ref_no, item_names


@pytest.fixture(scope="session")
def session_grn_multi(logged_in_page, session_gp_multi):
    supplier_name, _, item_names = session_gp_multi
    grn = GRNPlaywrightPage(logged_in_page)
    grn.navigate_to_page()
    grn.open_add_form()
    row_count = grn.select_supplier_and_gp(supplier_name, expected_rows=2)
    for i in range(row_count):
        gp_qty = grn.read_gp_qty(i)
        accepted = max(1, int(gp_qty) - 1)
        grn._fill_number_nth(grn.ACCEPTED_QTY, i, accepted)
        grn.page.wait_for_timeout(500)
    grn.page.locator(grn.SUBMIT_BTN).click()
    grn.handle_success_alert()
    grn.navigate_to_page()
    grn_ref_no = grn.get_ref_no_of_first_row()
    return supplier_name, grn_ref_no, item_names


# ── CQP config (session-scoped, runs once after GRN) ─────────────────────

@pytest.fixture(scope="session")
def session_cqp_config_single(logged_in_page, session_grn_single):
    _, _, item_names = session_grn_single
    cqp = CQPPlaywrightPage(logged_in_page)
    return cqp.read_configs_for_items(item_names)


@pytest.fixture(scope="session")
def session_cqp_config_multi(logged_in_page, session_grn_multi):
    _, _, item_names = session_grn_multi
    cqp = CQPPlaywrightPage(logged_in_page)
    return cqp.read_configs_for_items(item_names)


# ── Function-scoped page fixtures ─────────────────────────────────────────

@pytest.fixture(scope="function")
def qc_page(logged_in_page, session_grn_single, session_cqp_config_single):
    supplier_name, grn_ref_no, item_names = session_grn_single
    p = QCPlaywrightPage(logged_in_page)
    p.cqp_config = session_cqp_config_single
    p.item_names = item_names
    p.navigate_to_page()
    yield p, (supplier_name, grn_ref_no)
    try:
        p.close_popup()
    except Exception:
        pass


@pytest.fixture(scope="function")
def qc_page_multi(logged_in_page, session_grn_multi, session_cqp_config_multi):
    supplier_name, grn_ref_no, item_names = session_grn_multi
    p = QCPlaywrightPage(logged_in_page)
    p.cqp_config = session_cqp_config_multi
    p.item_names = item_names
    p.navigate_to_page()
    yield p, (supplier_name, grn_ref_no)
    try:
        p.close_popup()
    except Exception:
        pass
