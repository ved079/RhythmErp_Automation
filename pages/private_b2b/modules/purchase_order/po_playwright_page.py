import random
from datetime import date, timedelta
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


class POPlaywrightPage(BasePlaywrightPage):
    URL = f"{BASE_URL}/#/purchase/purchase-order"

    # Header fields
    SUPPLIER_NAME        = "xpath=//mat-form-field[.//mat-label[contains(.,'Supplier Name')]]//mat-select"
    PO_ITEM_TYPE         = "xpath=//mat-form-field[.//mat-label[contains(.,'PO Item Type')]]//mat-select"
    PO_TYPE              = "xpath=//mat-form-field[.//mat-label[contains(.,'PO Type')]]//mat-select"
    TRANSACTION_CURRENCY = "xpath=//mat-form-field[.//mat-label[contains(.,'Transaction Currency')]]//mat-select"
    LOCATION             = "xpath=//mat-form-field[.//mat-label[contains(.,'Location')]]//mat-select"
    DEPARTMENT           = "xpath=//mat-form-field[.//mat-label[contains(.,'Department')]]//mat-select"
    DIVISION             = "xpath=//mat-form-field[.//mat-label[contains(.,'Division')]]//mat-select"
    TYPE_OF_SALE         = "xpath=//mat-form-field[.//mat-label[contains(.,'Type of Sale')]]//mat-select"
    PACKAGING_FORWARDING = "xpath=//mat-form-field[.//mat-label[contains(.,'Packaging Forwarding')]]//mat-select"
    CONVERSION_RATE      = "xpath=//mat-form-field[.//input[@placeholder='Conversion Rate']]//input"

    # Item grid fields — multiple rows; use .nth(row_index) to target each row
    ITEM_NAME          = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Name')]]//mat-select"
    QUANTITY           = "xpath=//mat-form-field[.//mat-label[contains(.,'Quantity')]]//input"
    RATE               = "xpath=//mat-form-field[.//mat-label[contains(.,'Rate')]]//input"
    EXPECTED_DELIVERY  = "xpath=//mat-form-field[.//mat-label[contains(.,'Expected Delivery Date')]]//input[@placeholder='DD/MM/YYYY']"
    DISCOUNT           = "xpath=//mat-form-field[.//mat-label[contains(.,'Discount %')]]//input"
    INTEREST           = "xpath=//mat-form-field[.//mat-label[contains(.,'Interest%')]]//input"
    TRANSACTION_AMOUNT = "xpath=//mat-form-field[.//mat-label[contains(.,'Transaction Amount')]]//input"
    TOTAL_AMOUNT       = "xpath=//mat-form-field[.//mat-label[contains(.,'Total Amount')]]//input"

    # Buttons
    ADD_BTN      = "button.erp-add-btn"
    ADD_ROW_BTN  = "button.add-row-btn"
    SUBMIT_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(@class,'mat-mdc-unelevated-button') or contains(@class,'mat-mdc-raised-button')][.//span[contains(.,'Submit')]]"
    UPDATE_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
    CANCEL_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    APPROVE_BTN  = "xpath=//button[contains(@class,'mat-mdc-raised-button')][.//span[contains(.,'Approve')]]"

    # Table columns
    REF_NO_COL          = "td.cdk-column-transaction_ref_no"
    TOTAL_PO_AMOUNT_COL = "td.cdk-column-txn_currency_total_amount"
    WORKFLOW_STATUS_COL = "td.cdk-column-workflow_status"

    # PO listing table is mat-mdc-table, not #excel-table — override base
    def handle_success_alert(self):
        self.page.wait_for_selector(".swal2-container", timeout=8000)
        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        self.page.wait_for_selector(".swal2-container", state="hidden", timeout=5000)
        self.page.wait_for_selector("table.mat-mdc-table", timeout=8000)

    # ── Navigation ──────────────────────────────────────────────────────

    def navigate_to_page(self):
        self.page.goto(self.URL)
        self.page.wait_for_selector("table.mat-mdc-table", timeout=20000)
        self.page.wait_for_timeout(1000)

    # ── Form open ───────────────────────────────────────────────────────

    def open_add_form(self):
        add_btn = self.page.locator(self.ADD_BTN)
        add_btn.wait_for(state="visible", timeout=10000)
        add_btn.scroll_into_view_if_needed()
        add_btn.click()
        self.page.wait_for_timeout(1000)
        self.page.wait_for_selector(self.SUPPLIER_NAME, timeout=20000)
        self.page.wait_for_timeout(500)

    # ── Mat-select helpers ──────────────────────────────────────────────

    def _select_mat_by_text(self, selector, text):
        """Open dropdown and click the option whose visible text exactly matches."""
        self.page.locator(selector).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        # Use XPath exact-text match to avoid "Farm" also matching "Non Farm"
        option = self.page.locator(
            f".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).filter(has_text=text)
        # Find the one whose stripped text is exactly `text`
        matched = None
        for opt in option.all():
            if opt.inner_text().strip() == text:
                matched = opt
                break
        if matched:
            matched.click(force=True)
        else:
            # fallback: first filter match
            self.page.locator(".mat-mdc-select-panel mat-option").filter(has_text=text).first.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)

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

    def count_available_items(self):
        """Open the Item Name dropdown on row 0 and count available options."""
        self.page.locator(self.ITEM_NAME).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        count = self.page.locator(".mat-mdc-select-panel mat-option").count()
        # Close without pressing Escape — click the overlay backdrop instead
        self.page.locator(".cdk-overlay-backdrop").last.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)
        return count

    def _select_random_mat_option_nth(self, selector, row_index, exclude_texts=None):
        """Open the nth dropdown in the grid and pick a random option, skipping excluded ones.
        Returns the text of the chosen option, or '' if none available."""
        self.page.locator(selector).nth(row_index).click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(".mat-mdc-select-panel mat-option").all()
        if exclude_texts:
            options = [o for o in options if o.inner_text().strip() not in exclude_texts]
        if not options:
            # No options left — close safely via backdrop, not Escape (Escape can dismiss the whole form)
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

    def _select_mat_by_text_nth(self, selector, row_index, text):
        """Open the nth dropdown and click the option matching text."""
        self.page.locator(selector).nth(row_index).click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        self.page.locator(".mat-mdc-select-panel mat-option").filter(has_text=text).first.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)

    # ── Header fill ─────────────────────────────────────────────────────

    def fill_header(self):
        self._select_random_mat_option(self.SUPPLIER_NAME)
        self._select_mat_by_text(self.PO_ITEM_TYPE, "Farm")
        self._select_random_mat_option(self.PO_TYPE)
        self._select_mat_by_text(self.TRANSACTION_CURRENCY, "INR")
        self.page.wait_for_timeout(400)
        # Conversion Rate is required when currency is not the base currency
        conv_rate_field = self.page.locator(self.CONVERSION_RATE)
        if conv_rate_field.count() > 0:
            conv_rate_field.first.click(force=True)
            conv_rate_field.first.fill("1")
            conv_rate_field.first.press("Tab")
            self.page.wait_for_timeout(300)
        self._select_random_mat_option(self.LOCATION)
        self.page.wait_for_timeout(500)
        self._select_random_mat_option(self.DEPARTMENT)
        self._select_random_mat_option(self.DIVISION)
        self._select_mat_by_text(self.TYPE_OF_SALE, "B2B")
        self._select_mat_by_text(self.PACKAGING_FORWARDING, "Nil")

    # ── Item row fill ───────────────────────────────────────────────────

    @staticmethod
    def _delivery_date():
        return (date.today() + timedelta(days=5)).strftime("%d/%m/%Y")

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

    def _add_item_row(self, row_index, qty, disc_pct, int_pct, used_items=None):
        """Add one detail row to the PO grid.

        Returns dict:
            item_name, rate, qty, disc_pct, int_pct, txn_amount, total_amount
        """
        # Rows are pre-created before filling starts — no ADD_ROW_BTN click needed here

        # Select item — avoid picking duplicates across rows
        item_name = self._select_random_mat_option_nth(
            self.ITEM_NAME, row_index, exclude_texts=used_items
        )
        # Wait for Rate to be auto-fetched from Commodity Base Rate
        self.page.wait_for_timeout(1500)

        # Read auto-populated rate via JS (field may be off-screen)
        rate_str = self.page.evaluate("""
            ([xpath, idx]) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const el = result.snapshotItem(idx);
                return el ? el.value : '';
            }
        """, [self.RATE.replace("xpath=", ""), row_index])
        rate = float(rate_str) if rate_str and rate_str.strip() else 0.0

        # Fill quantity → triggers Transaction Amount calculation
        self._fill_number_nth(self.QUANTITY, row_index, qty)
        self.page.wait_for_timeout(800)

        # Fill discount % and interest % → trigger total row update
        self._fill_number_nth(self.DISCOUNT, row_index, disc_pct)
        self._fill_number_nth(self.INTEREST, row_index, int_pct)
        self.page.wait_for_timeout(600)

        # Read back ERP-calculated amounts via JS
        def _read_nth(xpath, idx):
            return self.page.evaluate("""
                ([xpath, idx]) => {
                    const result = document.evaluate(xpath, document, null,
                        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    const el = result.snapshotItem(idx);
                    return el ? el.value : '';
                }
            """, [xpath.replace("xpath=", ""), idx])

        txn_str   = _read_nth(self.TRANSACTION_AMOUNT, row_index)
        total_str = _read_nth(self.TOTAL_AMOUNT, row_index)
        txn_amount   = float(txn_str)   if txn_str   and txn_str.strip()   else rate * qty
        total_amount = float(total_str) if total_str and total_str.strip() else txn_amount

        return {
            "item_name":   item_name,
            "rate":        rate,
            "qty":         qty,
            "disc_pct":    disc_pct,
            "int_pct":     int_pct,
            "txn_amount":  txn_amount,
            "total_amount": total_amount,
        }

    # ── Create ──────────────────────────────────────────────────────────

    TOTAL_PO_AMOUNT_FORM = "input[placeholder='Total PO Amount']"

    def _read_form_total_po_amount(self):
        """Read the disabled Total PO Amount summary field in the open form."""
        field = self.page.locator(self.TOTAL_PO_AMOUNT_FORM)
        if field.count() > 0:
            val = field.first.input_value()
            if val and val.strip():
                return float(val.strip())
        return None

    def _read_all_row_totals(self):
        """Read each row's Total Amount from DOM via JS and return sum."""
        xpath = self.TOTAL_AMOUNT.replace("xpath=", "")
        values = self.page.evaluate("""
            (xpath) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const vals = [];
                for (let i = 0; i < result.snapshotLength; i++) {
                    vals.push(result.snapshotItem(i).value || '0');
                }
                return vals;
            }
        """, xpath)
        return sum(float(v) for v in values if v and v.strip())

    def create_record(self, item_configs=None, all_items=False):
        """Open form, fill header, add item rows, submit.

        item_configs: list of (qty, disc_pct, int_pct).
        all_items: if True, ignore item_configs and add one row per available item.
        Returns (total_po_amount, [row_dicts]).
        """
        if item_configs is None:
            item_configs = [(10, 5, 2)]

        self.open_add_form()
        self.fill_header()

        if all_items:
            available = self.count_available_items()
            item_configs = [(10, 0, 0)] * available

        total_rows = len(item_configs)

        # Pre-create all rows upfront so every row's fields exist in DOM before filling
        for _ in range(total_rows - 1):
            self.page.locator(self.ADD_ROW_BTN).click()
            self.page.wait_for_timeout(600)

        row_dicts = []
        used_items = set()
        for i, (qty, disc_pct, int_pct) in enumerate(item_configs):
            rd = self._add_item_row(i, qty, disc_pct, int_pct, used_items)
            if not rd["item_name"]:
                break
            used_items.add(rd["item_name"])
            row_dicts.append(rd)

        # Wait for Angular to finish recalculating all row totals
        self.page.wait_for_timeout(800)
        total_po_amount = self._read_form_total_po_amount()
        row_totals_sum = self._read_all_row_totals()
        # Attach the live row-sum to each row_dict so tests can compare
        for rd in row_dicts:
            rd["live_row_sum"] = row_totals_sum
        if total_po_amount is None:
            total_po_amount = row_totals_sum

        self.page.locator(self.SUBMIT_BTN).click()
        self.handle_success_alert()
        self.navigate_to_page()

        return total_po_amount, row_dicts

    # ── Table reads ─────────────────────────────────────────────────────

    def get_first_ref_no(self):
        return self.page.locator(self.REF_NO_COL).first.inner_text().strip()

    def get_workflow_status_of_first_row(self):
        return self.page.locator(f"{self.WORKFLOW_STATUS_COL} span").first.inner_text().strip()

    def get_total_po_amount_of_first_row(self):
        text = self.page.locator(self.TOTAL_PO_AMOUNT_COL).first.inner_text().strip()
        return float(text) if text else 0.0

    def get_table_row_count(self):
        return self.page.locator("table.mat-mdc-table tbody tr").count()

    def is_po_in_table(self, ref_no):
        return self.page.locator(f"td.cdk-column-transaction_ref_no").filter(has_text=ref_no).count() > 0

    # ── Search ───────────────────────────────────────────────────────────

    def search_po(self, ref_no):
        self.search_entry(ref_no)

    def search_by_total_amount(self, total_amount):
        """Search the listing table by Total PO Amount value."""
        self.search_entry(str(total_amount))

    def is_po_amount_in_table(self, total_amount):
        """Check if a row with the given Total PO Amount exists in the listing."""
        return self.page.locator(self.TOTAL_PO_AMOUNT_COL).filter(
            has_text=str(total_amount)
        ).count() > 0

    def get_ref_no_for_amount(self, total_amount):
        """Return the ref_no of the first row matching the given Total PO Amount."""
        rows = self.page.locator("table.mat-mdc-table tbody tr").all()
        for row in rows:
            amt_cell = row.locator(f"td.cdk-column-txn_currency_total_amount")
            if amt_cell.count() > 0 and str(total_amount) in amt_cell.inner_text():
                ref_cell = row.locator("td.cdk-column-transaction_ref_no")
                if ref_cell.count() > 0:
                    return ref_cell.inner_text().strip()
        return None

    # ── Row actions ──────────────────────────────────────────────────────

    def click_view_button(self):
        self.page.evaluate("var btn = document.querySelectorAll('button.erp-row-trigger')[0]; if(btn){btn.scrollIntoView({block:'center'});btn.click();}")
        self.page.wait_for_selector("div.mat-mdc-menu-panel", timeout=3000)
        self.page.locator("xpath=//button[contains(@class,'erp-menu-item')][.//span[contains(.,'Open record details')]]").first.click(force=True)
        self.page.wait_for_timeout(500)

    def click_edit_button(self):
        self.click_row_action(0, "Edit")

    def is_edit_disabled(self):
        """Open the action menu for the first row and check if Edit is disabled."""
        self.page.evaluate("var btn = document.querySelectorAll('button.erp-row-trigger')[0]; if(btn){btn.scrollIntoView({block:'center'});btn.click();}")
        self.page.wait_for_selector("div.mat-mdc-menu-panel", timeout=3000)
        edit_btn = self.page.locator("xpath=//button[contains(@class,'erp-menu-item')][.//span[contains(.,'Modify this record')]]")
        disabled = edit_btn.get_attribute("aria-disabled") == "true" or edit_btn.get_attribute("disabled") is not None
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)
        return disabled

    def click_history_button(self):
        self.click_row_action(0, "History")

    def click_approve(self):
        self.page.locator(self.APPROVE_BTN).click()
        self.page.wait_for_timeout(300)

    def approve_po(self):
        """Edit the top row, click Approve, confirm success."""
        self.click_edit_button()
        self.page.wait_for_selector(self.APPROVE_BTN, timeout=8000)
        self.click_approve()
        self.handle_success_alert()
        self.navigate_to_page()

    # ── Popup close ──────────────────────────────────────────────────────

    def close_popup(self):
        try:
            self.page.locator(self.CANCEL_BTN).click()
        except Exception:
            pass
        try:
            self.page.wait_for_selector("table.mat-mdc-table", timeout=5000)
        except Exception:
            pass

    def verify_view_popup_read_only(self):
        self.page.wait_for_selector("xpath=//mat-label[contains(.,'Supplier Name')]", timeout=10000)
        self.page.wait_for_timeout(500)
        assert self.page.locator(self.SUBMIT_BTN).count() == 0, \
            "Submit must not appear in View mode"
        assert self.page.locator(self.APPROVE_BTN).count() == 0, \
            "Approve must not appear in View mode"
