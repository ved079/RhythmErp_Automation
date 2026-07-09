import os
import sys
import random
import pytest
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.private_b2b.modules.gate_pass.gp_playwright_page import GPPlaywrightPage
from pages.private_b2b.modules.grn.grn_playwright_page import GRNPlaywrightPage
from pages.private_b2b.modules.qc.cqp_playwright_page import CQPPlaywrightPage
from pages.private_b2b.modules.qc.qc_playwright_page import QCPlaywrightPage
from pages.private_b2b.modules.purchase_booking.pb_playwright_page import PBPlaywrightPage

RHYTHMERP_LOGIN_URL = os.environ.get("RHYTHMERP_LOGIN_URL", "https://rhythmerp.algorhythms.in")
RHYTHMERP_EMAIL     = os.environ.get("RHYTHMERP_EMAIL", "")
RHYTHMERP_PASSWORD  = os.environ.get("RHYTHMERP_PASSWORD", "")


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: Critical happy-path tests")
    config.addinivalue_line("markers", "calc: Calculation verification tests")
    config.addinivalue_line("markers", "validation: Form validation and error handling")
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


@pytest.fixture(scope="session")
def session_qc_for_pb(logged_in_page):
    """Full chain GP → GRN → CQP → QC.

    Returns (supplier_name, grn_qtys) where grn_qtys is a list of accepted_qty
    per item row — used by pb_page to fill the Quantity Details popup.
    grn_qty == QC's grn_qty == GRN's accepted_qty.
    """
    # ── Step 1: GP ───────────────────────────────────────────────────────
    gp = GPPlaywrightPage(logged_in_page)
    gp.navigate_to_page()
    _, row_dicts = gp.create_record([(random.randint(1, 5), random.randint(10, 50))])
    supplier_name = logged_in_page.locator("td.cdk-column-supplier_ref_id").first.inner_text().strip()
    item_names = [rd["item_name"] for rd in row_dicts if rd.get("item_name")]

    # ── Step 2: GRN ──────────────────────────────────────────────────────
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

    # ── Step 3: CQP config ───────────────────────────────────────────────
    cqp = CQPPlaywrightPage(logged_in_page)
    cqp_config = cqp.read_configs_for_items(item_names)

    # ── Step 4: QC — create + capture grn_qty for PB ────────────────────
    qc = QCPlaywrightPage(logged_in_page)
    qc.cqp_config = cqp_config
    qc.item_names = item_names
    qc.navigate_to_page()
    qc.open_add_form()
    qc.select_supplier_and_gp(supplier_name)

    # Read the accepted_qty the QC form auto-patched from GRN — this is what PB needs
    grn_qty = qc.read_accepted_qty(0)
    grn_qtys = [int(grn_qty) if grn_qty else accepted]

    actual_values = qc.safe_actual_values(0, max_pct=15)
    qc.open_qc_param_popup(0)
    qc.fill_actual_values(actual_values)
    qc.click_done()
    qc.page.locator(qc.SUBMIT_BTN).click()
    qc.handle_success_alert()
    qc.navigate_to_page()

    print(f"\n[PB SETUP] supplier={supplier_name} grn_qtys={grn_qtys}")
    return supplier_name, grn_qtys


@pytest.fixture(scope="session")
def session_qc_for_pb_multi(logged_in_page):
    """Full chain GP(all items) → GRN(multi) → CQP → QC(multi).

    Returns (supplier_name, grn_qtys) where grn_qtys is a list of accepted_qty
    per item row — one entry per item in the GP.
    """
    # ── Step 1: GP all items ─────────────────────────────────────────────
    gp = GPPlaywrightPage(logged_in_page)
    gp.navigate_to_page()
    _, row_dicts = gp.create_record(all_items=True)
    supplier_name = logged_in_page.locator("td.cdk-column-supplier_ref_id").first.inner_text().strip()
    item_names = [rd["item_name"] for rd in row_dicts if rd.get("item_name")]

    # ── Step 2: GRN multi-row ────────────────────────────────────────────
    grn = GRNPlaywrightPage(logged_in_page)
    grn.navigate_to_page()
    grn.open_add_form()
    row_count = grn.select_supplier_and_gp(supplier_name, expected_rows=len(item_names))
    accepted_per_row = []
    for i in range(row_count):
        gp_qty = grn.read_gp_qty(i)
        accepted = max(1, int(gp_qty) - 1)
        grn._fill_number_nth(grn.ACCEPTED_QTY, i, accepted)
        grn.page.wait_for_timeout(500)
        accepted_per_row.append(accepted)
    grn.page.locator(grn.SUBMIT_BTN).click()
    grn.handle_success_alert()
    grn.navigate_to_page()

    # ── Step 3: CQP config ───────────────────────────────────────────────
    cqp = CQPPlaywrightPage(logged_in_page)
    cqp_config = cqp.read_configs_for_items(item_names)

    # ── Step 4: QC multi-row — create + capture grn_qty per row ─────────
    qc = QCPlaywrightPage(logged_in_page)
    qc.cqp_config = cqp_config
    qc.item_names = item_names
    qc.navigate_to_page()
    qc.open_add_form()
    qc.select_supplier_and_gp(supplier_name)

    qc_row_count = qc.count_item_rows()
    grn_qtys = []
    for i in range(qc_row_count):
        qty = qc.read_accepted_qty(i)
        grn_qtys.append(int(qty) if qty else accepted_per_row[i] if i < len(accepted_per_row) else 1)
        actual_values = qc.safe_actual_values(i, max_pct=15)
        qc.open_qc_param_popup(i)
        qc.fill_actual_values(actual_values)
        qc.click_done()
        qc.page.wait_for_timeout(800)

    qc.page.locator(qc.SUBMIT_BTN).click()
    qc.handle_success_alert()
    qc.navigate_to_page()

    print(f"\n[PB MULTI SETUP] supplier={supplier_name} grn_qtys={grn_qtys}")
    return supplier_name, grn_qtys


@pytest.fixture(scope="function")
def pb_page(logged_in_page, session_qc_for_pb):
    supplier_name, grn_qtys = session_qc_for_pb
    p = PBPlaywrightPage(logged_in_page)
    p.navigate_to_page()
    yield p, (supplier_name, grn_qtys)
    try:
        p.close_popup()
    except Exception:
        pass


@pytest.fixture(scope="function")
def pb_page_multi(logged_in_page, session_qc_for_pb_multi):
    supplier_name, grn_qtys = session_qc_for_pb_multi
    p = PBPlaywrightPage(logged_in_page)
    p.navigate_to_page()
    yield p, (supplier_name, grn_qtys)
    try:
        p.close_popup()
    except Exception:
        pass
