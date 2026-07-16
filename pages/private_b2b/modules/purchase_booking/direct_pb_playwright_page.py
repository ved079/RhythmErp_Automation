import random
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"

# All active items for Eco Green Pvt Ltd tenant
ITEMS = [
    "Soybean Yellow FAQ Grade 5 KG",
    "Tur (Arhar) White FAQ Grade 5 KG",
    "Chana White FAQ Grade 10 KG",
    "Maize Yellow FAQ Grade 5 KG",
    "Soybean Red Grade A 10 KG",
    "Masoor Yellow Grade A 20 KG",
    "Chana White Grade A 25 KG",
    "Maize Green Grade B 20 KG",
    "Sesame (Til) Green Grade A 10 KG",
    "Ragi White 5 KG",
    "Chana Red Grade A 500 KG",
    "Bajra Yellow Grade A 20 KG",
    "Barley Red Grade A 30 KG",
    "Maize White Grade B 100 KG",
    "Chana Yellow Premium Grade 1000 KG (1 MT)",
    "Sesame (Til) Sona Masuri Grade B 20 KG",
    "Sunflower Ooty Super Grade 20 KG",
    "Bajra Sharbati Super Grade 75 KG",
    "Safflower Black Super Grade 20 KG",
    "Mustard Medium Milling Grade 25 KG",
]


class DirectPBPlaywrightPage(BasePlaywrightPage):
    URL = f"{BASE_URL}/#/purchase/purchase-booking"

    # ── Header selectors ──────────────────────────────────────────────────
    SUPPLIER_NAME   = "xpath=//mat-form-field[.//mat-label[contains(.,'Supplier Name')]]//mat-select"
    LOCATION        = "xpath=//mat-form-field[.//mat-label[contains(.,'Location')]]//mat-select"
    DEPARTMENT      = "xpath=//mat-form-field[.//mat-label[contains(.,'Department')]]//mat-select"
    DIVISION        = "xpath=//mat-form-field[.//mat-label[contains(.,'Division')]]//mat-select"
    TYPE_OF_SALE    = "xpath=//mat-form-field[.//mat-label[contains(.,'Type of Sale')]]//mat-select"
    CONVERSION_RATE = "input[placeholder='Conversion Rate']"

    # ── Item grid selectors (use .nth(row_index)) ─────────────────────────
    ITEM_NAME          = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Name')]]//mat-select"
    HSN_SAC_NO         = "xpath=//mat-form-field[.//mat-label[contains(.,'HSN SAC No')]]//mat-select"
    NO_OF_BAGS         = "xpath=//mat-form-field[.//mat-label[contains(.,'No Of Bags')]]//input"
    QUANTITY           = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Quantity']]//input"
    EMPTY_BAG_WEIGHT   = "xpath=//mat-form-field[.//mat-label[contains(.,'Empty Bag Weight (KG)')]]//input"
    NET_QUANTITY       = "xpath=//mat-form-field[.//mat-label[contains(.,'Net Quantity')]]//input"
    RATE               = "xpath=//mat-form-field[.//mat-label[contains(.,'Rate')]]//input"
    TRANSACTION_AMOUNT = "xpath=//mat-form-field[.//mat-label[contains(.,'Transaction Amount')]]//input"
    LABOUR_CHARGES     = "xpath=//mat-form-field[.//mat-label[contains(.,'Labour Charges')]]//input"
    DISC_PERCENTAGE    = "xpath=//mat-form-field[.//mat-label[contains(.,'Discount Percentage')]]//input"

    # ── Per-row computed readonly fields (use .nth(row_index)) ────────────
    # Exact-match labels to avoid collisions (Amount ≠ Total Amount, IGST Amount, etc.)
    AMOUNT          = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Amount']]//input"
    TOTAL_AMOUNT    = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Total Amount']]//input"
    DISCOUNT_AMOUNT = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Discount Amount']]//input"
    TAX_AMOUNT_FIELD = "xpath=//mat-form-field[.//mat-label[contains(.,'Tax amount') or contains(.,'Tax Amount')]]//input"
    IGST_AMOUNT     = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='IGST Amount']]//input"
    IGST_RATE_FIELD = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='IGST Rate']]//input"
    CGST_AMOUNT     = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='CGST Amount']]//input"
    CGST_RATE_FIELD = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='CGST Rate']]//input"
    SGST_AMOUNT     = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='SGST Amount']]//input"
    SGST_RATE_FIELD = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='SGST Rate']]//input"

    # ── Per-row GST controls ──────────────────────────────────────────────
    # IS GST Off toggle: click .slider to enable, app-slide-toggle-v2 indexed per row
    IS_GST_OFF_SLIDER = "app-slide-toggle-v2 .slider"
    GST_TYPE_SELECT   = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='GST Type']]//mat-select"
    TAX_RATE_SELECT   = "xpath=//mat-form-field[.//mat-label[contains(.,'Tax') and contains(.,'ate') and not(contains(.,'Amount'))]]//mat-select"

    # ── Qty Details popup (same pattern as PO-linked PB) ─────────────────
    QTY_DETAILS_BTN = "xpath=//td[contains(@class,'col_input')]//button[.//mat-icon[text()='add']]"
    DONE_BTN        = "xpath=//button[contains(.,'Done')]"

    # ── Buttons ───────────────────────────────────────────────────────────
    ADD_BTN        = "button.erp-add-btn"
    # Both row action buttons share .apply-button; distinguished by icon class.
    # fa-plus (add) is always visible; fa-minus (delete) only appears when rows >= 2.
    ADD_ROW_BTN    = "xpath=(//button[contains(@class,'add-row-btn') and contains(.,'Add Row')])[1]"
    DELETE_ROW_BTN = "button.apply-button:has(i.fa-minus)"
    SUBMIT_BTN     = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN     = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"

    # ── Navigation ────────────────────────────────────────────────────────

    def navigate_to_page(self):
        self.page.goto(self.URL)
        self.page.evaluate("location.reload(true)")  # hard refresh — clears any lingering overlays
        self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=20000)
        self.page.wait_for_timeout(1000)

    # ── Form open / close ─────────────────────────────────────────────────

    def open_add_form(self):
        self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=15000)
        self.page.wait_for_timeout(500)
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

    def close_popup(self):
        cancel = self.page.locator(self.CANCEL_BTN)
        if cancel.count() > 0:
            try:
                cancel.first.click(force=True)
                self.page.wait_for_timeout(500)
            except Exception:
                pass
        self.navigate_to_page()

    # ── Mat-select helpers ────────────────────────────────────────────────

    def _select_random_mat_option(self, selector):
        """Open a mat-select and pick a random option. Returns the chosen text."""
        self.page.locator(selector).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(".mat-mdc-select-panel mat-option").all()
        text = ""
        if options:
            chosen = random.choice(options)
            text = chosen.inner_text().strip()
            chosen.scroll_into_view_if_needed()
            chosen.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)
        return text

    def _select_mat_by_text_nth(self, selector, row_index, text):
        """Open the nth mat-select in the grid and select the option matching text."""
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)
        el = self.page.locator(selector).nth(row_index)
        el.scroll_into_view_if_needed()
        self.page.wait_for_timeout(200)
        el.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=10000)
        search = self.page.locator(".mat-mdc-select-panel input.dd-search-input")
        if search.count():
            search.fill(text)
            self.page.wait_for_timeout(500)
        opt = self.page.locator(
            ".mat-mdc-select-panel mat-option:not(.dd-state-option)"
        ).filter(has_text=text).first
        if opt.count():
            opt.scroll_into_view_if_needed()
            opt.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(400)

    # ── Number field fill (JS native setter so Angular picks up the value) ─

    def _fill_number_nth(self, selector, row_index, value):
        self.page.evaluate("""
            ([xpath, idx, val]) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const el = result.snapshotItem(idx);
                if (!el) return;
                const setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, val);
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
                el.blur();
            }
        """, [selector.replace("xpath=", ""), row_index, str(value)])
        self.page.wait_for_timeout(400)

    # ── Header fill ───────────────────────────────────────────────────────

    SUPPLIERS = [
        "Omkar Agencies | 9389399233",
        "Vedant Company | 9494949494",
        "Jagdamba Krishna Oil Mills Group | 9978228598",
        "Jai Vindhya Exports & Sons | 9581809469",
        "Maa Agro Traders Group | 6915553555",
        "Supreme Godavari Oil Mills & Sons | 8761823111",
        "Venkatesh Amul Enterprises & Bros | 6997018367",
        "Falcon enterprises | 9388239912",
    ]

    def fill_header(self):
        """Fill all mandatory header fields with random valid values.
        Returns the selected supplier name."""
        supplier_name = random.choice(self.SUPPLIERS)
        self.page.locator(self.SUPPLIER_NAME).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        for opt in self.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).all():
            opt_text = opt.inner_text().strip()
            if supplier_name in opt_text or opt_text in supplier_name:
                opt.scroll_into_view_if_needed()
                opt.click(force=True)
                break
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(600)
        supplier = supplier_name
        self.page.wait_for_timeout(600)
        self._select_random_mat_option(self.LOCATION)
        self.page.wait_for_timeout(400)
        self._select_random_mat_option(self.DEPARTMENT)
        self.page.wait_for_timeout(400)
        if self.page.locator(self.DIVISION).count() > 0:
            self._select_random_mat_option(self.DIVISION)
            self.page.wait_for_timeout(300)
        self._select_random_mat_option(self.TYPE_OF_SALE)
        self.page.wait_for_timeout(400)
        conv = self.page.locator(self.CONVERSION_RATE)
        if conv.count() > 0 and not conv.first.input_value():
            conv.first.fill("1")
            self.page.wait_for_timeout(200)
        return supplier

    # ── Item row ──────────────────────────────────────────────────────────

    def _pick_nudge_item(self, target_item):
        """Return an item name different from target_item to use as nudge."""
        for item in ITEMS:
            if item != target_item:
                return item
        return ITEMS[0]

    def open_qty_details_popup(self, row_index):
        """Open the Quantity Details popup for the given row."""
        self.page.locator(self.QTY_DETAILS_BTN).nth(row_index).click(force=True)
        self.page.wait_for_selector(self.DONE_BTN, timeout=10000)
        self.page.wait_for_timeout(400)

    def fill_qty_details(self, no_of_bags, qty):
        """Fill No of Bags and Quantity inside the open Quantity Details popup."""
        bags_inp = self.page.locator("input[placeholder='No of Bags']:not([readonly])")
        bags_inp.last.wait_for(state="visible", timeout=8000)
        bags_inp.last.fill(str(no_of_bags))
        qty_inp = self.page.locator("input[placeholder='Quantity']:not([readonly])")
        qty_inp.last.wait_for(state="visible", timeout=8000)
        qty_inp.last.fill(str(qty))
        self.page.wait_for_timeout(300)

    def click_done(self):
        """Close the Quantity Details popup."""
        self.page.locator(self.DONE_BTN).click(force=True)
        try:
            self.page.wait_for_selector(self.DONE_BTN, state="hidden", timeout=5000)
        except Exception:
            pass
        self.page.wait_for_timeout(500)

    def add_item_row(self, row_index, item_name, qty, rate,
                     no_of_bags=1, empty_bag_weight=0, labour_charges=0, disc_pct=0):
        """Add one item row to the direct PB grid.

        Double-select nudge: select a different item first (activates Angular's
        selectionChange so HSN/UOM auto-fetch), then select the real item.
        Quantity is filled via the Quantity Details popup (grid fields are readonly).
        """
        if row_index > 0:
            self.page.locator(self.ADD_ROW_BTN).click()
            self.page.wait_for_timeout(600)

        nudge = self._pick_nudge_item(item_name)
        self._select_mat_by_text_nth(self.ITEM_NAME, row_index, nudge)
        self.page.wait_for_timeout(500)
        self._select_mat_by_text_nth(self.ITEM_NAME, row_index, item_name)
        self.page.wait_for_timeout(1000)

        self.open_qty_details_popup(row_index)
        self.fill_qty_details(no_of_bags, qty)
        self.click_done()
        self.page.wait_for_timeout(400)

        if empty_bag_weight:
            self._fill_number_nth(self.EMPTY_BAG_WEIGHT, row_index, empty_bag_weight)
        self._fill_number_nth(self.RATE, row_index, rate)
        if labour_charges:
            self._fill_number_nth(self.LABOUR_CHARGES, row_index, labour_charges)
        if disc_pct:
            self._fill_number_nth(self.DISC_PERCENTAGE, row_index, disc_pct)
        self.page.wait_for_timeout(500)

    def delete_row(self, row_index):
        """Delete item row at row_index (DELETE_ROW_BTN only appears when 2+ rows exist)."""
        self.page.locator(self.DELETE_ROW_BTN).nth(row_index).click(force=True)
        self.page.wait_for_timeout(600)

    def count_item_rows(self):
        return self.page.locator(self.ITEM_NAME).count()

    # ── Error helpers ─────────────────────────────────────────────────────

    def visible_errors(self):
        """Return list of visible mat-error texts (offsetParent JS filter)."""
        return self.page.evaluate("""
            () => Array.from(document.querySelectorAll('mat-error'))
                       .filter(el => el.offsetParent !== null)
                       .map(el => el.innerText.trim())
        """)

    def submit_and_wait(self):
        self.page.locator(self.SUBMIT_BTN).click(force=True)
        self.page.wait_for_timeout(1000)

    # ── Supplier dropdown helpers ─────────────────────────────────────────

    def search_supplier_in_dropdown(self, search_text):
        """Open supplier dropdown, type search_text, return all visible option texts."""
        self.page.locator(self.SUPPLIER_NAME).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        search = self.page.locator(".mat-mdc-select-panel input, .dd-search-input")
        if search.count() > 0:
            search.first.fill(search_text)
            self.page.wait_for_timeout(800)
        options = [
            o.inner_text().strip()
            for o in self.page.locator(
                ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
            ).all()
        ]
        self.page.locator(".cdk-overlay-backdrop").last.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        return options

    def _read_number_nth(self, selector, row_index):
        """Read numeric value from nth readonly input via JS. Returns float."""
        val = self.page.evaluate("""
            ([xpath, idx]) => {
                const r = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const el = r.snapshotItem(idx);
                return el ? el.value : '';
            }
        """, [selector.replace("xpath=", ""), row_index])
        return float(val) if val and val.strip() else 0.0

    def enable_gst_off(self, row_index):
        """Toggle IS GST Off to Yes for the given row."""
        # JS click on the hidden checkbox to properly fire Angular's change detection
        self.page.evaluate(
            """(idx) => {
                const inputs = document.querySelectorAll('app-slide-toggle-v2 input[type="checkbox"]');
                if (inputs[idx]) inputs[idx].click();
            }""",
            row_index,
        )
        self.page.wait_for_timeout(500)

    def select_tax_rate(self, row_index, rate):
        """Select tax rate for the given row.
        Opens dropdown, reads available options, picks the one matching `rate`
        (by number), then searches for its exact label text."""
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)
        el = self.page.locator(self.TAX_RATE_SELECT).nth(row_index)
        el.scroll_into_view_if_needed()
        self.page.wait_for_timeout(200)
        el.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=10000)
        self.page.wait_for_timeout(500)
        opts = self.page.locator(
            ".mat-mdc-select-panel mat-option:not(.dd-state-option)"
        ).all()
        chosen_text = None
        for o in opts:
            t = o.inner_text().strip()
            if t and rate is not None and str(rate) in t:
                chosen_text = t
                break
        if chosen_text is None and opts:
            chosen_text = opts[0].inner_text().strip()
        search = self.page.locator(".mat-mdc-select-panel input.dd-search-input")
        if search.count() and chosen_text:
            search.fill(chosen_text)
            self.page.wait_for_timeout(500)
        opt = self.page.locator(
            ".mat-mdc-select-panel mat-option:not(.dd-state-option)"
        ).filter(has_text=chosen_text).first if chosen_text else None
        if opt and opt.count():
            opt.scroll_into_view_if_needed()
            opt.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(400)

    def select_gst_type(self, row_index, gst_type):
        """Select GST Type for the given row. gst_type: 'IGST' or 'CGST + SGST'."""
        self._select_mat_by_text_nth(self.GST_TYPE_SELECT, row_index, gst_type)
        self.page.wait_for_timeout(600)

    def read_transaction_amount(self, row_index=0):
        """Read the Transaction Amount field for a given row via JS."""
        val = self.page.evaluate("""
            ([xpath, idx]) => {
                const r = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const el = r.snapshotItem(idx);
                return el ? el.value : '';
            }
        """, [self.TRANSACTION_AMOUNT.replace("xpath=", ""), row_index])
        return float(val) if val and val.strip() else 0.0
