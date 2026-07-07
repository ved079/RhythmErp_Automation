import random
from datetime import date, timedelta
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


class GPPlaywrightPage(BasePlaywrightPage):
    URL = f"{BASE_URL}/#/purchase/gate-pass"

    # Header fields
    SUPPLIER_NAME   = "xpath=//mat-form-field[.//mat-label[contains(.,'Supplier Name')]]//mat-select"
    ITEM_TYPE       = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Type')]]//mat-select"
    DELIVERY_TERMS  = "xpath=//mat-form-field[.//mat-label[contains(.,'Delivery Terms')]]//mat-select"
    IN_TIME         = "xpath=//mat-form-field[.//mat-label[contains(.,'IN Time')]]//input"
    LOCATION        = "xpath=//mat-form-field[.//mat-label[contains(.,'Location')]]//mat-select"
    DEPARTMENT      = "xpath=//mat-form-field[.//mat-label[contains(.,'Department')]]//mat-select"
    DIVISION        = "xpath=//mat-form-field[.//mat-label[contains(.,'Division')]]//mat-select"
    TYPE_OF_SALE    = "xpath=//mat-form-field[.//mat-label[contains(.,'Type of Sale')]]//mat-select"
    DISTANCE        = "xpath=//mat-form-field[.//mat-label[contains(.,'Distance')]]//input"
    VEHICLE_NUMBER  = "xpath=//mat-form-field[.//mat-label[contains(.,'Vehicle Number')]]//input"
    DRIVER_NAME     = "xpath=//mat-form-field[.//mat-label[contains(.,'Driver Name')]]//input"
    DRIVER_NUMBER   = "xpath=//mat-form-field[.//mat-label[contains(.,'Driver Number')]]//input"

    # Item grid fields
    ITEM_NAME  = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Name')]]//mat-select"
    NO_OF_BAGS = "xpath=//mat-form-field[.//mat-label[contains(.,'NO. of Bags')]]//input"
    QUANTITY   = "xpath=//mat-form-field[.//mat-label[contains(.,'Quantity')]]//input"

    # Buttons
    ADD_BTN     = "button.erp-add-btn"
    ADD_ROW_BTN = "button.add-row-btn"
    SUBMIT_BTN  = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN  = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    UPDATE_BTN  = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"

    # Table columns
    REF_NO_COL     = "td.cdk-column-transaction_ref_no"
    STATUS_COL     = "td.cdk-column-booking_status"

    # ── Navigation ───────────────────────────────────────────────────────

    def handle_success_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=8000)
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            try:
                self.page.wait_for_selector(".swal2-container", state="hidden", timeout=10000)
            except Exception:
                pass
        except Exception:
            pass
        try:
            self.page.wait_for_selector("table.mat-mdc-table", timeout=8000)
        except Exception:
            pass

    def navigate_to_page(self):
        self.page.goto(self.URL)
        try:
            self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=15000)
        except Exception:
            self.page.reload()
            self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=20000)

    # ── Mat-select helpers ───────────────────────────────────────────────

    def _select_random_mat_option(self, selector):
        self.page.locator(selector).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(".mat-mdc-select-panel mat-option").all()
        if options:
            random.choice(options).click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)

    def _select_mat_by_text(self, selector, text):
        self.page.locator(selector).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        option = self.page.locator(".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text")
        for opt in option.all():
            if opt.inner_text().strip() == text:
                opt.click(force=True)
                break
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)

    def _select_random_mat_option_nth(self, selector, row_index, exclude_texts=None):
        self.page.locator(selector).nth(row_index).click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(".mat-mdc-select-panel mat-option").all()
        if exclude_texts:
            options = [o for o in options if o.inner_text().strip() not in exclude_texts]
        if not options:
            self.page.locator(".cdk-overlay-backdrop").last.click(force=True)
            try:
                self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
            except Exception:
                pass
            return ""
        chosen = random.choice(options)
        text = chosen.inner_text().strip()
        chosen.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)
        return text

    # ── Number field helper ──────────────────────────────────────────────

    def _fill_number_nth(self, selector, row_index, value):
        self.page.evaluate("""
            ([xpath, idx, val]) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const el = result.snapshotItem(idx);
                if (!el) return;
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(el, val);
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
                el.blur();
            }
        """, [selector.replace("xpath=", ""), row_index, str(value)])
        self.page.wait_for_timeout(400)

    def _fill_text_field(self, selector, value):
        field = self.page.locator(selector).first
        field.click()
        field.fill(value)
        field.press("Tab")
        self.page.wait_for_timeout(300)

    # ── IN Time picker ───────────────────────────────────────────────────

    def fill_in_time(self, hour=10, minute=0):
        self.page.locator(self.IN_TIME).click()
        self.page.wait_for_selector(".owl-dt-timer-input", timeout=5000)
        self.page.evaluate("""
            ([h, m]) => {
                const inputs = document.querySelectorAll('.owl-dt-timer-input');
                if (inputs[0]) {
                    inputs[0].value = String(h).padStart(2, '0');
                    inputs[0].dispatchEvent(new Event('input', {bubbles: true}));
                    inputs[0].dispatchEvent(new Event('change', {bubbles: true}));
                }
                if (inputs[1]) {
                    inputs[1].value = String(m).padStart(2, '0');
                    inputs[1].dispatchEvent(new Event('input', {bubbles: true}));
                    inputs[1].dispatchEvent(new Event('change', {bubbles: true}));
                }
            }
        """, [hour, minute])
        self.page.wait_for_timeout(300)
        self.page.evaluate("""
            () => {
                const btns = document.querySelectorAll('button.owl-dt-control-button');
                for (const btn of btns) {
                    if (btn.textContent.trim() === 'Set') { btn.click(); return; }
                }
            }
        """)
        self.page.wait_for_timeout(300)

    # ── Open Add Form ────────────────────────────────────────────────────

    def open_add_form(self):
        self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=15000)
        self.page.wait_for_timeout(800)
        add_btn = self.page.locator(self.ADD_BTN)
        add_btn.wait_for(state="visible", timeout=10000)
        add_btn.scroll_into_view_if_needed()
        add_btn.click(force=True)
        self.page.wait_for_timeout(2000)
        if self.page.locator(self.SUPPLIER_NAME).count() == 0:
            add_btn.click(force=True)
            self.page.wait_for_timeout(2000)
        self.page.wait_for_selector(self.SUPPLIER_NAME, timeout=25000)
        self.page.wait_for_timeout(500)

    # ── Header fill ──────────────────────────────────────────────────────

    def fill_header(self):
        self._select_random_mat_option(self.SUPPLIER_NAME)
        self.page.wait_for_timeout(500)
        self._select_mat_by_text(self.ITEM_TYPE, "Farm")
        self._select_random_mat_option(self.DELIVERY_TERMS)
        self.fill_in_time(10, 0)
        self._select_random_mat_option(self.LOCATION)
        self._select_random_mat_option(self.DEPARTMENT)
        self._select_random_mat_option(self.DIVISION)
        self._select_random_mat_option(self.TYPE_OF_SALE)
        self._fill_text_field(self.DISTANCE, "1")
        self._fill_text_field(self.VEHICLE_NUMBER, "MH14KK2354")
        self._fill_text_field(self.DRIVER_NAME, "TestDriver")
        self._fill_number_nth(self.DRIVER_NUMBER, 0, 9999988888)

    # ── Item row fill ────────────────────────────────────────────────────

    def count_available_items(self):
        self.page.locator(self.ITEM_NAME).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        count = self.page.locator(".mat-mdc-select-panel mat-option").count()
        self.page.locator(".cdk-overlay-backdrop").last.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)
        return count

    def _add_item_row(self, row_index, bags, qty, used_items=None):
        item_name = self._select_random_mat_option_nth(
            self.ITEM_NAME, row_index, exclude_texts=used_items
        )
        self.page.wait_for_timeout(800)
        self._fill_number_nth(self.NO_OF_BAGS, row_index, bags)
        self._fill_number_nth(self.QUANTITY, row_index, qty)
        self.page.wait_for_timeout(400)
        return {"item_name": item_name, "bags": bags, "qty": qty}

    # ── Create ───────────────────────────────────────────────────────────

    def create_record(self, item_configs=None, all_items=False):
        """Open form, fill header, add item rows, submit.

        item_configs: list of (bags, qty).
        all_items: if True, add one row per available item.
        Returns (ref_no, [row_dicts]).
        """
        if item_configs is None:
            item_configs = [(random.randint(1, 10), random.randint(1, 100))]

        self.open_add_form()
        self.fill_header()

        if all_items:
            available = self.count_available_items()
            item_configs = [(random.randint(1, 10), random.randint(1, 100)) for _ in range(available)]

        total_rows = len(item_configs)

        for _ in range(total_rows - 1):
            self.page.locator(self.ADD_ROW_BTN).click()
            self.page.wait_for_timeout(600)

        row_dicts = []
        used_items = set()
        for i, (bags, qty) in enumerate(item_configs):
            rd = self._add_item_row(i, bags, qty, used_items)
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

    # ── Table reads ──────────────────────────────────────────────────────

    def get_ref_no_of_first_row(self):
        return self.page.locator(self.REF_NO_COL).first.inner_text().strip()

    def get_table_row_count(self):
        return self.page.locator("table.mat-mdc-table tbody tr").count()

    def is_gp_in_table(self, ref_no):
        return self.page.locator(self.REF_NO_COL).filter(has_text=ref_no).count() > 0

    # ── Search ───────────────────────────────────────────────────────────

    def search_by_ref_no(self, ref_no):
        self.search_entry(ref_no)

    # ── Close popup ──────────────────────────────────────────────────────

    def close_popup(self):
        try:
            cancel = self.page.locator(self.CANCEL_BTN)
            cancel.wait_for(state="visible", timeout=3000)
            cancel.click()
            self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=10000)
        except Exception:
            try:
                self.page.locator("//mat-icon[text()='close']/ancestor::button").first.click()
            except Exception:
                pass
