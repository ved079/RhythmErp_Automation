import os
import random
import sys
import pytest
from playwright.sync_api import sync_playwright
from pages.private_b2b.modules.purchase_order.po_playwright_page import POPlaywrightPage
from pages.private_b2b.modules.gate_pass.gp_playwright_page import GPPlaywrightPage
from pages.private_b2b.modules.goods_receipt_note.grn_playwright_page import GRNPlaywrightPage

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

LOGIN_URL = "https://rhythmerp.algorhythms.in"
EMAIL     = "kedar@rhythmflows.com"
PASSWORD  = "Kedar@999999"
TENANT    = "Agristack Company ltd"

_ITEM_CATEGORY = "Raw Materia"


class GPPlaywrightPageItemCategory(GPPlaywrightPage):
    ITEM_TYPE      = "xpath=//mat-form-field[.//mat-label[contains(.,'Item category')]]//mat-select"
    PURCHASE_ORDER = "xpath=//mat-form-field[.//mat-label[contains(.,'Purchase Order')]]//mat-select"

    def fill_header_with_supplier(self, supplier_name, location=None, type_of_sale=None, po_ref_no=None):
        self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
        self.page.wait_for_timeout(500)
        if po_ref_no:
            self._select_mat_by_text(self.PURCHASE_ORDER, po_ref_no)
        self._select_mat_by_text(self.ITEM_TYPE, "Raw Materia")
        self._select_mat_by_text(self.DELIVERY_TERMS, "Spot")
        self.fill_in_time(10, 0)
        if location:
            self._select_mat_by_text(self.LOCATION, location)
        else:
            self._select_random_mat_option(self.LOCATION)
        self._select_random_mat_option(self.DEPARTMENT)
        self._select_random_mat_option(self.DIVISION)
        if type_of_sale:
            self._select_mat_by_text(self.TYPE_OF_SALE, type_of_sale)
        else:
            self._select_random_mat_option(self.TYPE_OF_SALE)
        self._fill_text_field(self.DISTANCE, "1")
        self._fill_text_field(self.VEHICLE_NUMBER, "MH14KK2354")
        self._fill_text_field(self.DRIVER_NAME, "TestDriver")
        self._fill_number_nth(self.DRIVER_NUMBER, 0, 9999988888)

    def fill_items_form(self, supplier_name, items, location=None, type_of_sale="B2B", po_ref_no=None):
        self.open_add_form()
        self.fill_header_with_supplier(supplier_name, location=location, type_of_sale=type_of_sale, po_ref_no=po_ref_no)

        row0_item = items[0][0] if items else None
        for i, (item_name, bags, qty) in enumerate(items):
            if i > 0:
                self.page.locator(self.ADD_ROW_BTN).click()
                self.page.wait_for_timeout(1000)
            self._select_item_by_name_nth(i, item_name)
            self.page.wait_for_timeout(800)
            # Fallback: if HSN SAC No is still empty Angular didn't register the selection.
            # Nudge with row 0's item (triggers duplicate warning → wakes change detection)
            # then re-select the correct item.
            if i > 0 and row0_item and row0_item != item_name:
                hsn_text = self.page.locator(self.HSN_SAC_NO).nth(i).inner_text().strip()
                if not hsn_text:
                    self._select_item_by_name_nth(i, row0_item)
                    self.page.wait_for_timeout(600)
                    self._select_item_by_name_nth(i, item_name)
                    self.page.wait_for_timeout(600)
            self._fill_number_nth(self.NO_OF_BAGS, i, bags)
            self._fill_number_nth(self.QUANTITY, i, qty)
            self.page.wait_for_timeout(400)

    def create_record_with_specific_item(self, supplier_name, item_name, bags, qty,
                                         location=None, type_of_sale="B2B", po_ref_no=None):
        items = [(item_name, bags, qty)]
        self.fill_items_form(supplier_name, items, location=location, type_of_sale=type_of_sale, po_ref_no=po_ref_no)
        return self.submit_items_form(items)

    def create_record_with_supplier(self, supplier_name, item_configs=None, location=None,
                                    type_of_sale="B2B", exclude_keywords=None, po_ref_no=None):
        if item_configs is None:
            item_configs = [(random.randint(1, 5), random.randint(50, 200))]

        self.open_add_form()
        self.fill_header_with_supplier(supplier_name, location=location, type_of_sale=type_of_sale, po_ref_no=po_ref_no)

        total_rows = len(item_configs)
        for _ in range(total_rows - 1):
            self.page.locator(self.ADD_ROW_BTN).click()
            self.page.wait_for_timeout(600)

        row_dicts = []
        used_items = set()
        for i, (bags, qty) in enumerate(item_configs):
            rd = self._add_item_row(i, bags, qty, used_items, exclude_keywords=exclude_keywords)
            if not rd["item_name"]:
                break
            used_items.add(rd["item_name"])
            row_dicts.append(rd)

        self.page.locator(self.SUBMIT_BTN).click()
        self.page.wait_for_timeout(5000)
        self.handle_success_alert()
        self.navigate_to_page()

        ref_no = self.get_ref_no_of_first_row()
        return ref_no, row_dicts


class POPlaywrightPageRawMateria(POPlaywrightPage):
    """Subclass that uses 'Raw Materia' as PO Item Category instead of 'Beverages'."""

    def get_all_item_names(self, supplier_name=None):
        self.open_add_form()
        if supplier_name:
            self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
            chosen_supplier = supplier_name
        else:
            chosen_supplier = self._select_random_mat_option_text(self.SUPPLIER_NAME)
        self._try_select_mat_by_text(self.PO_ITEM_TYPE, _ITEM_CATEGORY)
        self.page.wait_for_timeout(600)

        self.page.locator(self.ITEM_NAME).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).all()
        names = [o.inner_text().strip() for o in options if o.inner_text().strip()]
        self.page.locator(".cdk-overlay-backdrop").last.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass

        import random
        cap = random.randint(4, 6)
        names = names[:cap]

        self._try_select_random_mat_option(self.PO_TYPE)
        self.page.wait_for_timeout(400)
        conv_rate_field = self.page.locator(self.CONVERSION_RATE)
        if conv_rate_field.count() > 0:
            conv_rate_field.first.click(force=True)
            conv_rate_field.first.fill("1")
            conv_rate_field.first.press("Tab")
            self.page.wait_for_timeout(300)
        location = self._select_random_mat_option_text(self.LOCATION)
        self.page.wait_for_timeout(500)
        self._select_random_mat_option(self.DEPARTMENT)
        self._select_random_mat_option(self.DIVISION)
        self._select_mat_by_text(self.TYPE_OF_SALE, "B2B")
        if self.page.locator(self.PACKAGING_FORWARDING).count() > 0:
            self._select_mat_by_text(self.PACKAGING_FORWARDING, "Nil")
        return names, chosen_supplier, location

    def fill_header_returning_supplier(self, forced_location=None, forced_supplier=None):
        supplier_name = "Sri Lakshmi Traders Associates"
        self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
        self._try_select_mat_by_text(self.PO_ITEM_TYPE, _ITEM_CATEGORY)
        self._try_select_random_mat_option(self.PO_TYPE)
        self.page.wait_for_timeout(400)
        conv_rate_field = self.page.locator(self.CONVERSION_RATE)
        if conv_rate_field.count() > 0:
            conv_rate_field.first.click(force=True)
            conv_rate_field.first.fill("1")
            conv_rate_field.first.press("Tab")
            self.page.wait_for_timeout(300)
        if forced_location:
            self._select_mat_by_text(self.LOCATION, forced_location)
            location = forced_location
        else:
            location = self._select_random_mat_option_text(self.LOCATION)
        self.page.wait_for_timeout(500)
        self._select_random_mat_option(self.DEPARTMENT)
        self._select_random_mat_option(self.DIVISION)
        self._select_mat_by_text(self.TYPE_OF_SALE, "B2B")
        if self.page.locator(self.PACKAGING_FORWARDING).count() > 0:
            self._select_mat_by_text(self.PACKAGING_FORWARDING, "Nil")
        return supplier_name, location


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
def integration_state():
    return {}


@pytest.fixture(scope="function")
def po_page(logged_in_page):
    p = POPlaywrightPageRawMateria(logged_in_page)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass


@pytest.fixture(scope="function")
def gp_page(logged_in_page):
    p = GPPlaywrightPageItemCategory(logged_in_page)
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


@pytest.fixture(scope="class")
def tab2_page(browser_context):
    new_tab = browser_context.new_page()
    yield new_tab
    try:
        new_tab.close()
    except Exception:
        pass


@pytest.fixture(scope="function")
def gp_page_tab2(tab2_page):
    p = GPPlaywrightPageItemCategory(tab2_page)
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
