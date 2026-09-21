import os
import sys
import pytest
from concurrent.futures import ThreadPoolExecutor, Future
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

_executor = ThreadPoolExecutor(max_workers=1)
_resolve_future: Future = None


def pytest_collection_finish(session):
    """After collection: start the resolver only if chain_config is actually needed."""
    global _resolve_future
    needs_resolver = any(
        "chain_config" in getattr(item, "fixturenames", [])
        for item in session.items
    )
    if needs_resolver:
        _resolve_future = _executor.submit(resolve_chain_config, location_name="Pune")

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


@pytest.fixture(scope="class")
def chain_config():
    """Block until the background resolver (started at pytest_sessionstart) completes."""
    return _resolve_future.result()


@pytest.fixture(scope="class")
def wago_config():
    """Resolve rate/qty for CONNECTOR WAGO from CBR; actual_values are hardcoded."""
    cfg = resolve_chain_config(location_name="Pune", item_name="CONNECTOR WAGO")
    cfg["actual_values"] = [1]
    return cfg


@pytest.fixture(scope="session")
def flow_configs():
    """Pre-generated N configs from FLOW_CONFIGS env var (set by FastAPI). Falls back via FLOW_COUNT."""
    import json as _json
    raw = os.environ.get("FLOW_CONFIGS")
    if raw:
        return _json.loads(raw)
    import random
    cfg = resolve_chain_config(location_name="Pune")
    cfg.setdefault("actual_values", [1])
    count = int(os.environ.get("FLOW_COUNT", "1"))
    if count <= 1:
        return [cfg]
    configs = [cfg]
    for _ in range(count - 1):
        qty = random.randint(10, 50)
        rate_min, rate_max = cfg.get("rate_min"), cfg.get("rate_max")
        rate = round(random.uniform(rate_min, rate_max), 2) if rate_min and rate_max else cfg["rate"]
        configs.append({**cfg, "quantity": qty, "rate": rate, "per_bag_weight": round(qty * 0.04, 2)})
    return configs


@pytest.fixture(scope="session")
def wago_configs():
    """Pre-generated N configs from WAGO_CONFIGS env var (set by the FastAPI backend).

    Falls back to a single resolved config when run standalone.
    """
    import json
    raw = os.environ.get("WAGO_CONFIGS")
    if raw:
        return json.loads(raw)
    import random
    cfg = resolve_chain_config(location_name="Pune", item_name="CONNECTOR WAGO")
    cfg["actual_values"] = [1]
    count = int(os.environ.get("WAGO_COUNT", "1"))
    if count <= 1:
        return [cfg]
    configs = [cfg]
    for _ in range(count - 1):
        qty = random.randint(10, 50)
        rate_min, rate_max = cfg.get("rate_min"), cfg.get("rate_max")
        rate = round(random.uniform(rate_min, rate_max), 2) if rate_min and rate_max else cfg["rate"]
        configs.append({**cfg, "quantity": qty, "rate": rate, "per_bag_weight": round(qty * 0.04, 2)})
    return configs


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
