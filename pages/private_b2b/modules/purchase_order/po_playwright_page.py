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
    RATE               = "xpath=//mat-form-field[.//input[@placeholder='Rate']]//input"
    EXPECTED_DELIVERY  = "xpath=//mat-form-field[.//mat-label[contains(.,'Expected Delivery Date')]]//input[@placeholder='DD/MM/YYYY']"
    DISCOUNT           = "xpath=//mat-form-field[.//mat-label[contains(.,'Discount %')]]//input"
    INTEREST           = "xpath=//mat-form-field[.//mat-label[contains(.,'Interest%')]]//input"
    TRANSACTION_AMOUNT = "xpath=//mat-form-field[.//mat-label[contains(.,'Transaction Amount')]]//input"
    TOTAL_AMOUNT       = "xpath=//mat-form-field[.//mat-label[contains(.,'Total Amount')]]//input"

    # Buttons
    ADD_BTN        = "button.erp-add-btn"
    ADD_ROW_BTN    = "button.add-row-btn"
    DELETE_ROW_BTN = "button.apply-button"  # fa-minus; only visible when 2+ rows exist
    SUBMIT_BTN     = "xpath=//div[contains(@class,'popup-footer')]//button[contains(@class,'mat-mdc-unelevated-button') or contains(@class,'mat-mdc-raised-button')][.//span[contains(.,'Submit')]]"
    UPDATE_BTN     = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
    CANCEL_BTN     = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"

    # GST per-row fields (in item grid)
    GST_TOGGLE_SLIDER = "app-slide-toggle-v2 div.slider"
    TAX_RATE_SELECT   = "xpath=//mat-select[.//span[contains(@class,'mat-mdc-select-placeholder') and contains(.,'Select tax rate')]]"
    TAX_AMOUNT_INPUT  = "xpath=//mat-form-field[.//input[@placeholder='Tax Amount']]//input"

    # Table columns
    REF_NO_COL          = "td.cdk-column-transaction_ref_no"
    TOTAL_PO_AMOUNT_COL = "td.cdk-column-txn_currency_total_amount"
    WORKFLOW_STATUS_COL = "td.cdk-column-workflow_status"

    # PO listing table is mat-mdc-table, not #excel-table — override base
    def handle_success_alert(self):
        self.page.wait_for_selector(".swal2-container", timeout=8000)
        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        try:
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=15000)
        except Exception:
            pass
        # Wait for the form (popup) to close, then wait for listing table
        try:
            self.page.wait_for_selector(self.SUPPLIER_NAME, state="hidden", timeout=15000)
        except Exception:
            pass
        self.page.wait_for_selector("table.mat-mdc-table", timeout=15000)

    # ── Navigation ──────────────────────────────────────────────────────

    def navigate_to_page(self):
        self.page.goto(self.URL)
        self.page.wait_for_selector("table.mat-mdc-table", timeout=20000)
        self.page.wait_for_timeout(1000)

    # ── Form open ───────────────────────────────────────────────────────

    def open_add_form(self):
        self.page.wait_for_selector("table.mat-mdc-table", timeout=15000)
        self.page.wait_for_timeout(800)
        add_btn = self.page.locator(self.ADD_BTN)
        add_btn.wait_for(state="visible", timeout=10000)
        add_btn.scroll_into_view_if_needed()
        add_btn.click(force=True)
        self.page.wait_for_timeout(2000)
        # If form didn't open, click again once
        if self.page.locator(self.SUPPLIER_NAME).count() == 0:
            add_btn.click(force=True)
            self.page.wait_for_timeout(2000)
        self.page.wait_for_selector(self.SUPPLIER_NAME, timeout=25000)
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

    def _try_select_random_mat_option(self, selector):
        """Like _select_random_mat_option but silently skips if no panel appears (auto-fetched/disabled field)."""
        self.page.locator(selector).first.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=3000)
        except Exception:
            return  # field is auto-fetched / disabled — skip
        options = self.page.locator(".mat-mdc-select-panel mat-option").all()
        if options:
            random.choice(options).click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)

    def _try_select_mat_by_text(self, selector, text):
        """Like _select_mat_by_text but silently skips if no panel appears (auto-fetched/disabled field)."""
        self.page.locator(selector).first.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=3000)
        except Exception:
            return  # field is auto-fetched / disabled — skip
        try:
            self.page.locator(".dd-search-input").fill(text)
            self.page.wait_for_timeout(400)
        except Exception:
            pass
        option = self.page.locator(".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text")
        matched = None
        for opt in option.all():
            if opt.inner_text().strip() == text:
                matched = opt
                break
        if matched:
            matched.click(force=True)
        else:
            self.page.locator(".mat-mdc-select-panel mat-option").filter(has_text=text).first.click(force=True)
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

        Uses search-then-click: types the item name into the dropdown's search box
        (if present) before clicking, which triggers Angular's selectionChange on rows 2+
        where the component might not be fully initialised via a direct click alone.

        Returns the text of the chosen option, or '' if none available.
        """
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
        # Use a real (non-forced) click so the browser generates a trusted event
        # (isTrusted=true). Angular on freshly-added rows guards selectionChange
        # behind isTrusted; force=True bypasses actionability but marks the event
        # as untrusted, so the rate auto-fetch never fires for rows 2+.
        chosen.scroll_into_view_if_needed()
        chosen.click()
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
        self._try_select_random_mat_option(self.PO_TYPE)
        self._try_select_mat_by_text(self.TRANSACTION_CURRENCY, "INR")
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

    def _enable_gst_nth(self, row_index):
        """Toggle 'Is GST Set Off' ON for row_index and pick a random Tax Rate.

        Must be called AFTER all previous rows have already had GST enabled,
        so that row_index lines up with the nth visible Tax Rate dropdown.
        Returns (tax_rate_float, tax_amount_float).
        """
        toggle = self.page.locator(self.GST_TOGGLE_SLIDER).nth(row_index)
        toggle.scroll_into_view_if_needed()
        toggle.click(force=True)
        self.page.wait_for_timeout(1500)

        # Always use nth(0) — by the time this row's toggle fires, previous rows have
        # already had their tax rate selected, so their placeholder is gone. Only this
        # row's "Select tax rate" placeholder remains → it is always the first match.
        tax_rate_text = self._select_random_mat_option_nth(self.TAX_RATE_SELECT, 0)
        self.page.wait_for_timeout(600)

        tax_amount_str = self.page.evaluate("""
            ([xpath, idx]) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const el = result.snapshotItem(idx);
                return el ? el.value : '';
            }
        """, [self.TAX_AMOUNT_INPUT.replace("xpath=", ""), row_index])

        tax_rate   = float(tax_rate_text)   if tax_rate_text   and tax_rate_text.strip()   else 0.0
        tax_amount = float(tax_amount_str)  if tax_amount_str  and tax_amount_str.strip()  else 0.0
        return tax_rate, tax_amount

    def _add_item_row(self, row_index, qty, disc_pct, int_pct, used_items=None, enable_gst=False, nudge_item=None):
        """Add one detail row to the PO grid.

        Returns dict:
            item_name, rate, qty, disc_pct, int_pct, txn_amount, total_amount,
            gst_enabled, tax_rate, tax_amount
        """
        # Rows are pre-created before filling starts — no ADD_ROW_BTN click needed here

        # Select item — avoid picking duplicates across rows
        item_name = self._select_random_mat_option_nth(
            self.ITEM_NAME, row_index, exclude_texts=used_items
        )

        # Angular quirk: for rows 2+, selecting an item doesn't fire selectionChange
        # (rate stays 0). Workaround confirmed manually: on THIS row, first select
        # row 0's item (creates a duplicate-item validation warning but wakes Angular's
        # selectionChange), then re-select the correct item — rate auto-fetches.
        if row_index > 0 and nudge_item and item_name:
            self.page.wait_for_timeout(600)
            self._select_mat_by_text_nth(self.ITEM_NAME, row_index, nudge_item)
            self.page.wait_for_timeout(800)
            self._select_mat_by_text_nth(self.ITEM_NAME, row_index, item_name)

        def _read_rate():
            val = self.page.evaluate("""
                ([xpath, idx]) => {
                    const result = document.evaluate(xpath, document, null,
                        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    const el = result.snapshotItem(idx);
                    return el ? el.value : '';
                }
            """, [self.RATE.replace("xpath=", ""), row_index])
            return float(val) if val and val.strip() else 0.0

        # Wait up to 5s for rate to auto-fetch after initial selection
        self.page.wait_for_timeout(1500)
        rate = 0.0
        for _ in range(4):
            rate = _read_rate()
            if rate > 0:
                break
            self.page.wait_for_timeout(1000)

        # Rate still 0 — re-select the same item to re-trigger the API call
        if rate == 0.0 and item_name:
            self._select_mat_by_text_nth(self.ITEM_NAME, row_index, item_name)
            self.page.wait_for_timeout(1500)
            for _ in range(4):
                rate = _read_rate()
                if rate > 0:
                    break
                self.page.wait_for_timeout(1000)

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
        txn_amount = float(txn_str) if txn_str and txn_str.strip() else rate * qty

        # Optionally enable GST and read tax fields for this row
        gst_enabled = False
        tax_rate    = None
        tax_amount  = 0.0
        if enable_gst:
            tax_rate, tax_amount = self._enable_gst_nth(row_index)
            gst_enabled = True

        # Read total_amount after any GST changes
        total_str    = _read_nth(self.TOTAL_AMOUNT, row_index)
        total_amount = float(total_str) if total_str and total_str.strip() else txn_amount + tax_amount

        return {
            "item_name":    item_name,
            "rate":         rate,
            "qty":          qty,
            "disc_pct":     disc_pct,
            "int_pct":      int_pct,
            "txn_amount":   txn_amount,
            "total_amount": total_amount,
            "gst_enabled":  gst_enabled,
            "tax_rate":     tax_rate,
            "tax_amount":   tax_amount,
        }

    # ── Create ──────────────────────────────────────────────────────────

    TOTAL_PO_AMOUNT_FORM = "input[placeholder='Total PO Amount']"

    def _read_form_total_po_amount(self):
        """Read the disabled Total PO Amount summary field in the open form via JS."""
        val = self.page.evaluate("""
            () => {
                const el = document.querySelector("input[placeholder='Total PO Amount']");
                return el ? el.value : '';
            }
        """)
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

    def create_record(self, item_configs=None, all_items=False, enable_gst=False):
        """Open form, fill header, add item rows, submit.

        item_configs: list of (qty, disc_pct, int_pct).
        all_items: if True, ignore item_configs and add one row per available item.
        enable_gst: if True, toggle GST on for every row and select a random Tax Rate.
        Returns (total_po_amount, [row_dicts]).
        """
        if item_configs is None:
            item_configs = [(10, 5, 2)]

        self.open_add_form()
        self.fill_header()

        if all_items:
            available = self.count_available_items()
            item_configs = [(10, 0, 0)] * available

        # Pass 1 — add rows one-at-a-time so Angular fully initialises each row
        # before the next ADD_ROW_BTN click. Use nudge_item for rows 2+ so
        # selectionChange fires and rate auto-fetches correctly.
        row_dicts = []
        used_items = set()
        row0_item = None
        for i, (qty, disc_pct, int_pct) in enumerate(item_configs):
            if i > 0:
                self.page.locator(self.ADD_ROW_BTN).click()
                self.page.wait_for_timeout(1000)
            rd = self._add_item_row(i, qty, disc_pct, int_pct, used_items,
                                    enable_gst=False, nudge_item=row0_item)
            if not rd["item_name"]:
                break
            if i == 0:
                row0_item = rd["item_name"]
            used_items.add(rd["item_name"])
            row_dicts.append(rd)

        # Pass 2 — enable GST after all rows are filled so Angular is fully awake
        if enable_gst:
            self.page.wait_for_timeout(600)
            for i in range(len(row_dicts)):
                tax_rate, tax_amount = self._enable_gst_nth(i)
                row_dicts[i]["gst_enabled"] = True
                row_dicts[i]["tax_rate"]    = tax_rate
                row_dicts[i]["tax_amount"]  = tax_amount

        self.page.wait_for_timeout(800)
        total_po_amount = self._read_form_total_po_amount()
        row_totals_sum = self._read_all_row_totals()
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
        self.page.wait_for_selector("table.mat-mdc-table", timeout=15000)
        self.page.wait_for_timeout(500)
        self.page.evaluate("var btn = document.querySelectorAll('button.erp-row-trigger')[0]; if(btn){btn.scrollIntoView({block:'center'});btn.click();}")
        self.page.wait_for_selector("div.mat-mdc-menu-panel", timeout=5000)
        self.page.locator("xpath=//button[contains(@class,'erp-menu-item')][.//span[contains(.,'Open record details')]]").first.click(force=True)
        try:
            self.page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass

    def click_history_button(self):
        self.click_row_action(0, "History")

    def edit_first_record_qty(self, new_qty):
        """Open Edit on the first row, change qty, submit via Update, return (new_total, new_txn_amount)."""
        self.click_row_action(0, "Edit")
        self.page.wait_for_selector(self.SUPPLIER_NAME, timeout=15000)
        self.page.wait_for_timeout(1000)

        self._fill_number_nth(self.QUANTITY, 0, new_qty)
        self.page.wait_for_timeout(800)

        def _read_nth(xpath, idx):
            return self.page.evaluate("""
                ([xpath, idx]) => {
                    const result = document.evaluate(xpath, document, null,
                        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    const el = result.snapshotItem(idx);
                    return el ? el.value : '';
                }
            """, [xpath.replace("xpath=", ""), idx])

        txn_str = _read_nth(self.TRANSACTION_AMOUNT, 0)
        new_txn_amount = float(txn_str) if txn_str and txn_str.strip() else 0.0

        self.page.wait_for_timeout(500)
        new_total = self._read_form_total_po_amount() or new_txn_amount

        self.page.locator(self.UPDATE_BTN).click(force=True)
        # Dismiss success alert without waiting for listing table (navigate_to_page handles that)
        self.page.wait_for_selector(".swal2-container", timeout=8000)
        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        try:
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=15000)
        except Exception:
            pass
        self.page.wait_for_timeout(1000)
        self.navigate_to_page()

        return new_total, new_txn_amount

    # ── Popup close ──────────────────────────────────────────────────────

    # ── Integration helpers ──────────────────────────────────────────────

    def _select_random_mat_option_text(self, selector):
        """Same as _select_random_mat_option but returns the selected option's text."""
        self.page.locator(selector).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).all()
        chosen_text = ""
        if options:
            import random as _random
            chosen = _random.choice(options)
            chosen_text = chosen.inner_text().strip()
            chosen.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)
        return chosen_text

    def fill_header_returning_supplier(self, forced_location=None):
        """Like fill_header() but returns (supplier_name, location) for integration use.

        forced_location: if provided, selects that exact location instead of random.
        """
        supplier_name = self._select_random_mat_option_text(self.SUPPLIER_NAME)
        self._select_mat_by_text(self.PO_ITEM_TYPE, "Farm")
        self._try_select_random_mat_option(self.PO_TYPE)
        self._try_select_mat_by_text(self.TRANSACTION_CURRENCY, "INR")
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
        self._select_mat_by_text(self.PACKAGING_FORWARDING, "Nil")
        return supplier_name, location

    def create_record_for_integration(self, item_configs=None, all_items=False,
                                      default_qty=500, forced_location=None,
                                      enable_gst=True):
        """Like create_record but also returns supplier_name and po_ref_no.

        Returns (total_po_amount, row_dicts, supplier_name, location, po_ref_no).
        default_qty: qty used per row when all_items=True (keep large so GP qty fits).
        forced_location: pin the Location dropdown to a specific value (e.g. "Pune").
        enable_gst: toggle GST on for every row in a second pass after all rows filled.
        """
        if item_configs is None:
            item_configs = [(default_qty, 0, 0)]

        self.open_add_form()
        supplier_name, location = self.fill_header_returning_supplier(
            forced_location=forced_location,
        )

        if all_items:
            available = self.count_available_items()
            item_configs = [(default_qty, 0, 0)] * available

        # Pass 1 — add one row at a time so Angular fully initialises each row's
        # mat-select before the next ADD_ROW_BTN click. Use nudge_item for rows 2+
        # so selectionChange fires and rate auto-fetches correctly.
        row_dicts = []
        used_items = set()
        row0_item = None
        for i, (qty, disc_pct, int_pct) in enumerate(item_configs):
            if i > 0:
                self.page.locator(self.ADD_ROW_BTN).click()
                self.page.wait_for_timeout(1000)
            rd = self._add_item_row(i, qty, disc_pct, int_pct, used_items,
                                    enable_gst=False, nudge_item=row0_item)
            if not rd["item_name"]:
                break
            if i == 0:
                row0_item = rd["item_name"]
            used_items.add(rd["item_name"])
            row_dicts.append(rd)

        # Pass 2 — enable GST after all rows are filled so Angular is fully awake.
        if enable_gst:
            self.page.wait_for_timeout(600)
            for i in range(len(row_dicts)):
                tax_rate, tax_amount = self._enable_gst_nth(i)
                row_dicts[i]["gst_enabled"] = True
                row_dicts[i]["tax_rate"]    = tax_rate
                row_dicts[i]["tax_amount"]  = tax_amount

        self.page.wait_for_timeout(800)
        total_po_amount = self._read_form_total_po_amount()
        if total_po_amount is None:
            total_po_amount = self._read_all_row_totals()

        self.page.locator(self.SUBMIT_BTN).click()
        self.handle_success_alert()
        self.navigate_to_page()

        po_ref_no = self.get_first_ref_no()
        return total_po_amount, row_dicts, supplier_name, location, po_ref_no

    def is_po_closed(self, ref_no):
        """Return True if the given PO's status column shows 'Closed'.

        The ERP only recalculates PO status when the listing receives a new record.
        Caller must open and cancel the PO add form before calling this so the listing
        refreshes — see trigger_listing_refresh().
        """
        self.search_po(ref_no)
        self.page.wait_for_timeout(2000)
        return self.page.locator(
            "xpath=//td[contains(@class,'cdk-column-po_status')]"
            "[.//text()[contains(.,'Closed')]]"
        ).count() > 0

    def trigger_po_status_recalculation(self):
        """Create a minimal throwaway PO so the ERP recalculates statuses for all POs.

        The ERP only marks a PO as 'Closed' (balance=0) after a new PO is inserted —
        it does not update statuses on a simple listing refresh or form open/cancel.
        This creates the smallest valid PO (1 bag, qty=1) to fire that backend trigger.
        """
        self.create_record_for_integration(item_configs=[(1, 0, 0)])
        self.page.wait_for_timeout(1000)

    def close_popup(self):
        # If view form is open (full-page details-form), navigate back to listing
        if self.page.locator(".details-form").count() > 0:
            self.navigate_to_page()
            return
        try:
            self.page.locator(self.CANCEL_BTN).click()
        except Exception:
            pass
        try:
            self.page.wait_for_selector("table.mat-mdc-table", timeout=5000)
        except Exception:
            pass

    def verify_view_popup_read_only(self):
        # Wait for readonly inputs — only present when view form is fully rendered
        self.page.wait_for_selector("input[readonly]", timeout=30000)
        self.page.wait_for_timeout(500)
        assert self.page.locator(self.SUBMIT_BTN).count() == 0, \
            "Submit must not appear in View mode"

    # ── Edit helpers ─────────────────────────────────────────────────────

    def click_row_action(self, row_index, action):
        """Override base class with a longer menu panel timeout for PO's heavier DOM."""
        self.page.evaluate(f"""
            var btns = document.querySelectorAll('button.erp-row-trigger');
            if (btns[{row_index}]) {{
                btns[{row_index}].scrollIntoView({{block:'center'}});
                btns[{row_index}].click();
            }}
        """)
        self.page.wait_for_selector("div.mat-mdc-menu-panel", timeout=8000)
        selector = self.MENU_SELECTORS.get(action)
        if selector:
            self.page.locator(selector).first.click()
        else:
            self.page.locator(f"button:has-text('{action}')").first.click()
        self.page.wait_for_timeout(500)

    def open_edit_form(self, row_index=0):
        self.click_row_action(row_index, "Edit")
        # Flat wait: XPath wait_for races with Angular re-renders; 3s is reliable in practice
        self.page.wait_for_timeout(3000)

    def count_form_rows(self):
        return self.page.locator(self.ITEM_NAME).count()

    def delete_row_nth(self, row_index):
        self.page.locator(self.DELETE_ROW_BTN).nth(row_index).click(force=True)
        self.page.wait_for_timeout(500)

    def submit_update(self):
        self.page.locator(self.UPDATE_BTN).click(force=True)
        self.page.wait_for_timeout(500)
        self.handle_success_alert()
        self.navigate_to_page()

    def read_item_names_from_form(self):
        """Read selected item names from all rows in the current open form (edit or view)."""
        spans = self.page.locator(
            "xpath=//mat-form-field[.//mat-label[contains(.,'Item Name')]]"
            "//span[contains(@class,'mat-mdc-select-min-line')]"
        ).all()
        return [
            s.inner_text().strip()
            for s in spans
            if s.inner_text().strip() and "select" not in s.inner_text().lower()
        ]

    def read_rate_nth(self, row_index):
        """Read the Rate field of a specific row via JS (field may be off-screen)."""
        val = self.page.evaluate("""
            ([xpath, idx]) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const el = result.snapshotItem(idx);
                return el ? el.value : '';
            }
        """, [self.RATE.replace("xpath=", ""), row_index])
        return float(val) if val and val.strip() else 0.0

    def read_txn_amount_nth(self, row_index):
        """Read Transaction Amount of a specific row via JS."""
        val = self.page.evaluate("""
            ([xpath, idx]) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const el = result.snapshotItem(idx);
                return el ? el.value : '';
            }
        """, [self.TRANSACTION_AMOUNT.replace("xpath=", ""), row_index])
        return float(val) if val and val.strip() else 0.0
