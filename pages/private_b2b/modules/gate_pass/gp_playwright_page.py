import os
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
    ADD_BTN        = "button.erp-add-btn"
    ADD_ROW_BTN    = "button.add-row-btn"
    DELETE_ROW_BTN = "button.apply-button"  # fa-minus; only visible when 2+ rows exist
    SUBMIT_BTN     = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN     = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    UPDATE_BTN     = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"

    # Table columns
    REF_NO_COL     = "td.cdk-column-transaction_ref_no"
    STATUS_COL     = "td.cdk-column-booking_status"

    # ── Navigation ───────────────────────────────────────────────────────

    # Default folder for validation error Excel downloads — always used when validation fails
    _DOWNLOADS_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "test_downloads", "gate_pass")
    )

    def handle_success_alert(self, downloads_dir=None):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=8000)
        except Exception:
            return

        title = self.page.locator("#swal2-title").inner_text().strip()

        if "Validation" in title or "Failed" in title:
            save_dir = downloads_dir or self._DOWNLOADS_DIR
            os.makedirs(save_dir, exist_ok=True)
            try:
                with self.page.expect_download(timeout=10000) as dl_info:
                    self.page.locator("button.swal2-confirm").click()
                download = dl_info.value
                save_path = os.path.join(save_dir, download.suggested_filename)
                download.save_as(save_path)
                print(f"\n[GP] Validation errors saved → {save_path}")
            except Exception as e:
                print(f"\n[GP] Download failed: {e}")
                self.page.locator("button.swal2-cancel").click()

            try:
                self.page.wait_for_selector(".swal2-container", state="hidden", timeout=5000)
            except Exception:
                pass
            raise RuntimeError(f"GP creation failed — validation error: {title}")

        # Success popup — click confirm
        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        try:
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=10000)
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

    def _select_random_mat_option_with_text(self, selector):
        """Same as _select_random_mat_option but returns the selected option's text."""
        self.page.locator(selector).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text").all()
        chosen_text = ""
        if options:
            chosen = random.choice(options)
            chosen_text = chosen.inner_text().strip()
            chosen.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)
        return chosen_text

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

    def _select_random_mat_option_nth(self, selector, row_index, exclude_texts=None, exclude_keywords=None):
        self.page.locator(selector).nth(row_index).click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(".mat-mdc-select-panel mat-option").all()
        if exclude_texts:
            options = [o for o in options if o.inner_text().strip() not in exclude_texts]
        if exclude_keywords:
            options = [o for o in options if not any(kw in o.inner_text() for kw in exclude_keywords)]
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
        self._select_mat_by_text(self.DELIVERY_TERMS, "Spot")
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

    def _add_item_row(self, row_index, bags, qty, used_items=None, exclude_keywords=None):
        all_exclude = set(used_items or [])
        item_name = self._select_random_mat_option_nth(
            self.ITEM_NAME, row_index,
            exclude_texts=all_exclude,
            exclude_keywords=exclude_keywords,
        )
        self.page.wait_for_timeout(800)
        self._fill_number_nth(self.NO_OF_BAGS, row_index, bags)
        self._fill_number_nth(self.QUANTITY, row_index, qty)
        self.page.wait_for_timeout(400)
        return {"item_name": item_name, "bags": bags, "qty": qty}

    # ── Create ───────────────────────────────────────────────────────────

    def create_record(self, item_configs=None, all_items=False, exclude_keywords=None):
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

    # ── Edit helpers ─────────────────────────────────────────────────────

    def open_edit_form(self, row_index=0):
        """Click Edit on listing row row_index and wait for the form to load."""
        self.click_row_action(row_index, "Edit")
        self.page.wait_for_selector(self.SUPPLIER_NAME, timeout=15000)
        self.page.wait_for_timeout(1000)

    def read_item_names_from_form(self):
        """Return a list of selected item names from all Item Name mat-selects in the form.
        Works in both edit and view modes. Skips blank/placeholder rows."""
        spans = self.page.locator(
            "xpath=//mat-form-field[.//mat-label[contains(.,'Item Name')]]"
            "//span[contains(@class,'mat-mdc-select-min-line')]"
        ).all()
        return [
            s.inner_text().strip()
            for s in spans
            if s.inner_text().strip() and "select" not in s.inner_text().lower()
        ]

    def count_form_rows(self):
        """Count item rows currently in the form (by counting Item Name mat-selects)."""
        return self.page.locator(self.ITEM_NAME).count()

    def delete_row_nth(self, row_index):
        """Click the minus (delete) button for the item row at row_index.
        Minus buttons only appear when the form has 2+ rows."""
        self.page.locator(self.DELETE_ROW_BTN).nth(row_index).click(force=True)
        self.page.wait_for_timeout(500)

    def submit_update(self):
        """Click Update, dismiss success alert, navigate back to listing."""
        self.page.locator(self.UPDATE_BTN).click(force=True)
        self.page.wait_for_timeout(500)
        self.handle_success_alert()
        self.navigate_to_page()

    # ── Integration helpers ──────────────────────────────────────────────

    def fill_header_with_supplier(self, supplier_name, location=None, type_of_sale="B2B"):
        """Fill header with a specific supplier, matching location and type_of_sale to the PO.

        Pass the same location and type_of_sale as the PO so the GRN can correctly
        link the GP to the PO (mismatched fields prevent the linkage from resolving).
        """
        self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
        self.page.wait_for_timeout(500)
        self._select_mat_by_text(self.ITEM_TYPE, "Farm")
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

    def _select_item_by_name_nth(self, row_index, item_name):
        """Open the nth Item Name mat-select and click the option matching item_name exactly."""
        self.page.locator(self.ITEM_NAME).nth(row_index).click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).all()
        for opt in options:
            if opt.inner_text().strip() == item_name:
                opt.click(force=True)
                break
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)

    def fill_items_form(self, supplier_name, items, location=None, type_of_sale="B2B"):
        """Open GP add form and fill header + all item rows without submitting.

        items: list of (item_name, bags, qty) tuples — one entry per row.
        Call submit_items_form() when ready to submit. The fill/submit split lets
        parallel tests fill simultaneously and only sequence the actual submit clicks.
        """
        self.open_add_form()
        self.fill_header_with_supplier(supplier_name, location=location, type_of_sale=type_of_sale)

        # Add extra rows if more than one item
        for _ in range(len(items) - 1):
            self.page.locator(self.ADD_ROW_BTN).click()
            self.page.wait_for_timeout(600)

        for i, (item_name, bags, qty) in enumerate(items):
            self._select_item_by_name_nth(i, item_name)
            self.page.wait_for_timeout(800)
            self._fill_number_nth(self.NO_OF_BAGS, i, bags)
            self._fill_number_nth(self.QUANTITY, i, qty)
            self.page.wait_for_timeout(400)

    def submit_items_form(self, items):
        """Submit the already-filled GP form and return (ref_no, [row_dicts])."""
        self.page.locator(self.SUBMIT_BTN).click()
        self.page.wait_for_timeout(5000)
        self.handle_success_alert()
        self.navigate_to_page()
        ref_no = self.get_ref_no_of_first_row()
        row_dicts = [{"item_name": n, "bags": b, "qty": q} for n, b, q in items]
        return ref_no, row_dicts

    def create_record_with_specific_item(self, supplier_name, item_name, bags, qty,
                                         location=None, type_of_sale="B2B"):
        """Convenience wrapper for a single-item GP. Returns (ref_no, [row_dict])."""
        items = [(item_name, bags, qty)]
        self.fill_items_form(supplier_name, items, location=location, type_of_sale=type_of_sale)
        return self.submit_items_form(items)

    def create_record_with_supplier(self, supplier_name, item_configs=None, location=None,
                                    type_of_sale="B2B", exclude_keywords=None):
        """Create a GP using a specific supplier, location, and type_of_sale.

        item_configs: list of (bags, qty). Defaults to one random row.
        Returns (ref_no, row_dicts) — same shape as create_record.
        """
        if item_configs is None:
            item_configs = [(random.randint(1, 5), random.randint(50, 200))]

        self.open_add_form()
        self.fill_header_with_supplier(supplier_name, location=location, type_of_sale=type_of_sale)

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
