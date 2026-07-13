import os
import random
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"

DOWNLOADS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "test_downloads", "purchase_booking")
)


class PBPlaywrightPage(BasePlaywrightPage):
    URL = f"{BASE_URL}/#/purchase/purchase-booking"

    # Header fields
    SUPPLIER_NAME        = "xpath=//mat-form-field[.//mat-label[contains(.,'Supplier Name')]]//mat-select"
    QC_SELECT            = "xpath=//mat-form-field[.//mat-label[contains(.,'QC')]]//mat-select"
    PO_SELECT            = "xpath=//mat-form-field[.//mat-label[contains(.,'PO') or contains(.,'Purchase Order')]]//mat-select"
    TRANSACTION_CURRENCY = "xpath=//mat-form-field[.//mat-label[contains(.,'Transaction Currency')]]//mat-select"
    CONVERSION_RATE      = "xpath=//mat-form-field[.//mat-label[contains(.,'Conversion Rate')]]//input"

    # Auto-patched readonly header fields (read after QC selection)
    AMOUNT       = "xpath=//mat-form-field[.//mat-label[normalize-space()='Amount']]//input"
    TOTAL_AMOUNT = "xpath=//mat-form-field[.//mat-label[normalize-space()='Total Amount']]//input"

    # Per-row item grid (auto-patched from QC — read only)
    ITEM_NAME        = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Name')]]//mat-select"
    RATE             = "xpath=//mat-form-field[.//mat-label[normalize-space()='Rate']]//input"
    NET_QUANTITY     = "xpath=//mat-form-field[.//mat-label[contains(.,'Net Quantity')]]//input"
    TXN_AMOUNT_ROW   = "xpath=//mat-form-field[.//mat-label[contains(.,'Transaction Amount')]]//input"

    # Quantity Details popup trigger (same col_input pattern as QC parameter popup)
    QTY_DETAILS_BTN = "xpath=//td[contains(@class,'col_input')]//button[.//mat-icon[text()='add']]"

    # Per-row item grid calc fields (filled BEFORE opening popup)
    EMPTY_BAG_WEIGHT = "xpath=//mat-form-field[.//mat-label[contains(.,'Empty Bag Weight (KG)')]]//input"
    LABOUR_CHARGES   = "xpath=//mat-form-field[.//mat-label[contains(.,'Labour Charges')]]//input"
    DISC_PERCENTAGE  = "xpath=//mat-form-field[.//mat-label[contains(.,'Discount Percentage')]]//input"

    # Round off fields — editable inputs use uppercase 'Off'; max value = 1
    ROUND_OFF_CREDIT = "xpath=//mat-form-field[.//mat-label[normalize-space()='Round Off Credit Amount(-)']]//input"
    ROUND_OFF_DEBIT  = "xpath=//mat-form-field[.//mat-label[normalize-space()='Round Off Debit Amount(+)']]//input"

    # Other charges section
    TRANSPORTATION_AMOUNT = "xpath=//mat-form-field[.//mat-label[contains(.,'Transportation Amount')]]//input"
    AGENT_COMMISSION_AMT  = "xpath=//mat-form-field[.//mat-label[contains(.,'Agent Commision Amount')]]//input"

    # Buttons
    ADD_BTN    = "button.erp-add-btn"
    SUBMIT_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    DONE_BTN   = "xpath=//button[contains(.,'Done')]"

    # Table
    REF_NO_COL = "td.cdk-column-transaction_ref_no"

    # ── Navigation ───────────────────────────────────────────────────────

    def navigate_to_page(self):
        self.page.goto(self.URL)
        try:
            self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=15000)
        except Exception:
            self.page.reload()
            self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=20000)
        try:
            self.page.wait_for_selector("div.edit_pop_up", state="hidden", timeout=8000)
        except Exception:
            pass
        self.page.wait_for_timeout(500)

    def handle_success_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=8000)
        except Exception:
            return

        title = self.page.locator("#swal2-title").inner_text().strip()

        if "Validation" in title or "Failed" in title:
            os.makedirs(DOWNLOADS_DIR, exist_ok=True)
            try:
                with self.page.expect_download(timeout=10000) as dl_info:
                    self.page.locator("button.swal2-confirm").click()
                download = dl_info.value
                save_path = os.path.join(DOWNLOADS_DIR, download.suggested_filename)
                download.save_as(save_path)
                print(f"\n[PB] Validation errors saved → {save_path}")
            except Exception as e:
                print(f"\n[PB] Download failed: {e}")
                self.page.locator("button.swal2-cancel").click()
            try:
                self.page.wait_for_selector(".swal2-container", state="hidden", timeout=5000)
            except Exception:
                pass
            raise RuntimeError(f"PB creation failed — validation error: {title}")

        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        try:
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=10000)
        except Exception:
            pass
        try:
            self.page.wait_for_selector("table.mat-mdc-table", timeout=8000)
        except Exception:
            pass

    # ── Open Add Form ────────────────────────────────────────────────────

    def open_add_form(self):
        self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=15000)
        self.page.wait_for_timeout(500)
        add_btn = self.page.locator(self.ADD_BTN)
        add_btn.wait_for(state="visible", timeout=10000)
        add_btn.click(force=True)
        self.page.wait_for_timeout(2000)
        if self.page.locator(self.SUPPLIER_NAME).count() == 0:
            add_btn.click(force=True)
            self.page.wait_for_timeout(2000)
        self.page.wait_for_selector(self.SUPPLIER_NAME, timeout=25000)
        self.page.wait_for_timeout(500)

    # ── Mat-select helpers ───────────────────────────────────────────────

    def _select_mat_by_text(self, selector, text):
        self.page.locator(selector).first.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
        except Exception:
            # Panel didn't open — field is likely already set (e.g. auto-patched from QC)
            return
        for opt in self.page.locator(".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text").all():
            if opt.inner_text().strip() == text:
                opt.click(force=True)
                break
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)

    def _select_last_mat_option(self, selector):
        loc = self.page.locator(selector).first
        loc.wait_for(state="visible", timeout=10000)
        loc.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=12000)

        if self.page.locator(".dd-empty-state").count() > 0:
            self.page.keyboard.press("Escape")
            try:
                self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
            except Exception:
                pass
            return False

        self.page.locator(".mat-mdc-select-panel mat-option").last.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)
        return True

    # ── JS helpers ───────────────────────────────────────────────────────

    def _read_nth(self, selector, index):
        """Read the nth VISIBLE input — skips hidden stale Angular popup relics."""
        xpath = selector.replace("xpath=", "")
        val = self.page.evaluate("""
            ([xpath, idx]) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const visible = [];
                for (let i = 0; i < result.snapshotLength; i++) {
                    const el = result.snapshotItem(i);
                    if (el.offsetParent !== null) visible.push(el);
                }
                const el = visible[idx];
                return el ? el.value : '';
            }
        """, [xpath, index])
        return val.strip() if val else ""

    def _fill_number_nth(self, selector, index, value):
        self.page.evaluate("""
            ([xpath, idx, val]) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const visible = [];
                for (let i = 0; i < result.snapshotLength; i++) {
                    const el = result.snapshotItem(i);
                    if (el.offsetParent !== null) visible.push(el);
                }
                const el = visible[idx];
                if (!el) return;
                const setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, val);
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
                el.blur();
            }
        """, [selector.replace("xpath=", ""), index, str(value)])
        self.page.wait_for_timeout(400)

    def _fill_single(self, selector, value):
        """Fill a single (non-indexed) header-level number input."""
        loc = self.page.locator(selector).first
        loc.wait_for(state="visible", timeout=8000)
        loc.click(force=True)
        loc.fill(str(value))
        loc.press("Tab")
        self.page.wait_for_timeout(400)

    # ── Header fill ──────────────────────────────────────────────────────

    def select_supplier_and_qc(self, supplier_name):
        """Select supplier → select last QC → wait for auto-patch → set currency."""
        self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
        self.page.wait_for_timeout(1000)

        selected = self._select_last_mat_option(self.QC_SELECT)
        if not selected:
            # Wake up: pick random supplier, re-select ours, retry
            self.page.locator(self.SUPPLIER_NAME).first.click(force=True)
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
            options = self.page.locator(".mat-mdc-select-panel mat-option").all()
            if options:
                random.choice(options).click(force=True)
            try:
                self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
            except Exception:
                pass
            self.page.wait_for_timeout(2000)
            self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
            self.page.wait_for_timeout(3000)
            self._select_last_mat_option(self.QC_SELECT)

        # Wait for GRN / Payment Terms / Location / Department / Division / Type of Sale to auto-patch
        self.page.wait_for_timeout(6000)

        # Transaction Currency must be set explicitly — base currency is pre-filled but txn is not
        self._select_mat_by_text(self.TRANSACTION_CURRENCY, "INR")
        self.page.wait_for_timeout(300)

        # Conversion Rate
        conv = self.page.locator(self.CONVERSION_RATE)
        if conv.count() > 0:
            conv.first.click(force=True)
            conv.first.fill("1")
            conv.first.press("Tab")
            self.page.wait_for_timeout(300)

    def select_supplier_and_po(self, supplier_name):
        """Select supplier → select last PO → wait for auto-patch → set currency."""
        self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
        self.page.wait_for_timeout(1000)

        self._select_last_mat_option(self.PO_SELECT)

        # Wait for items / Payment Terms / Location to auto-patch from PO
        self.page.wait_for_timeout(6000)

        self._select_mat_by_text(self.TRANSACTION_CURRENCY, "INR")
        self.page.wait_for_timeout(300)

        conv = self.page.locator(self.CONVERSION_RATE)
        if conv.count() > 0:
            conv.first.click(force=True)
            conv.first.fill("1")
            conv.first.press("Tab")
            self.page.wait_for_timeout(300)

    def create_record_from_po(self, supplier_name, row_configs=None):
        """PB create flow starting from PO (no QC chain).

        supplier_name: supplier to select — must match the PO's supplier.
        row_configs:   list of (no_of_bags, qty) per item row.
                       None = default (1 bag, full net_qty per row).

        Returns (total_amount, [row_dicts]).
        """
        self.open_add_form()
        self.select_supplier_and_po(supplier_name)

        row_count = self.count_item_rows()
        assert row_count > 0, "No item rows auto-patched after PO selection"

        if row_configs is None:
            row_configs = []
            for i in range(row_count):
                net_qty = self.read_net_qty(i) or 1
                row_configs.append((1, int(net_qty)))

        row_dicts = []
        for i, (bags, qty) in enumerate(row_configs[:row_count]):
            self.open_qty_details_popup(i)
            self.fill_qty_details(bags, qty)
            self.click_done()
            self.page.wait_for_timeout(500)

            rate       = self.read_rate(i)
            net_qty    = self.read_net_qty(i)
            txn_amount = self.read_txn_amount(i)
            row_dicts.append({
                "rate":       rate,
                "net_qty":    net_qty,
                "txn_amount": txn_amount,
                "no_of_bags": bags,
                "qty":        qty,
            })

        self.page.wait_for_timeout(500)
        total_amount = self.read_total_amount() or sum(r["txn_amount"] or 0 for r in row_dicts)

        self.page.locator(self.SUBMIT_BTN).click()
        self.handle_success_alert()
        self.navigate_to_page()

        return total_amount, row_dicts

    # ── Quantity Details popup ────────────────────────────────────────────

    def open_qty_details_popup(self, row_index=0):
        """Click the + button on item row to open Quantity Details popup."""
        self.page.locator(self.QTY_DETAILS_BTN).nth(row_index).click(force=True)
        # Wait for the Done button to confirm popup is open
        self.page.wait_for_selector(self.DONE_BTN, timeout=10000)
        self.page.wait_for_timeout(500)

    def fill_qty_details(self, no_of_bags, qty):
        """Fill the Quantity Details popup inputs directly by placeholder.

        Popup fields: placeholder='No of Bags' and placeholder='Quantity' (both editable).
        Main grid has placeholder='No Of Bags' (capital O) which is readonly — excluded via :not([readonly]).
        """
        bags_inp = self.page.locator("input[placeholder='No of Bags']:not([readonly])")
        bags_inp.last.wait_for(state="visible", timeout=8000)
        bags_inp.last.fill(str(no_of_bags))
        self.page.wait_for_timeout(300)

        qty_inp = self.page.locator("input[placeholder='Quantity']:not([readonly])")
        qty_inp.last.wait_for(state="visible", timeout=8000)
        qty_inp.last.fill(str(qty))
        self.page.wait_for_timeout(300)

    def click_done(self):
        self.page.locator(self.DONE_BTN).click(force=True)
        try:
            self.page.wait_for_selector(self.DONE_BTN, state="hidden", timeout=5000)
        except Exception:
            pass
        self.page.wait_for_timeout(800)

    def count_item_rows(self):
        return self.page.locator(self.QTY_DETAILS_BTN).count()

    # ── Read calculated fields ────────────────────────────────────────────

    def read_rate(self, row_index=0):
        val = self._read_nth(self.RATE, row_index)
        return float(val) if val else None

    def read_net_qty(self, row_index=0):
        val = self._read_nth(self.NET_QUANTITY, row_index)
        return float(val) if val else None

    def read_txn_amount(self, row_index=0):
        val = self._read_nth(self.TXN_AMOUNT_ROW, row_index)
        return float(val) if val else None

    def read_total_amount(self):
        val = self._read_nth(self.TOTAL_AMOUNT, 0)
        return float(val) if val else None

    # ── Create record ─────────────────────────────────────────────────────

    def fill_other_charges(self, transportation=None, agent_commission=None):
        """Fill the Other Charges section (transportation / agent commission)."""
        if transportation is not None:
            loc = self.page.locator(self.TRANSPORTATION_AMOUNT).first
            if loc.count() > 0:
                loc.click(force=True)
                loc.fill(str(transportation))
                loc.press("Tab")
                self.page.wait_for_timeout(300)
        if agent_commission is not None:
            loc = self.page.locator(self.AGENT_COMMISSION_AMT).first
            if loc.count() > 0:
                loc.click(force=True)
                loc.fill(str(agent_commission))
                loc.press("Tab")
                self.page.wait_for_timeout(300)

    def create_record(self, supplier_name, row_configs=None,
                      row_ebw=None, row_labour=None, row_discount=None,
                      row_round_debit=None, row_round_credit=None,
                      transportation=None, agent_commission=None):
        """Full PB create flow.

        row_configs:     list of (no_of_bags, qty) per item row. None = vanilla (grn_qty, bags=1).
        row_ebw:         list of empty bag weight per row (fills BEFORE popup).
        row_labour:      list of labour charges per row (fills BEFORE popup).
        row_discount:    list of discount percentage per row (fills BEFORE popup).
        row_round_debit: list of per-row Round Off Debit Amount(+) — max 1.0 each.
        row_round_credit:list of per-row Round Off Credit Amount(-) — max 1.0 each.

        All list params are per-row; None entries are skipped.

        Returns (total_amount, [row_dicts]) where row_dict has:
            {rate, net_qty, txn_amount, no_of_bags, qty, ebw, labour, discount, debit, credit}
        total_amount is read from the master TOTAL_AMOUNT field = SUM(per-row finals).

        Per-row final formula:
            gross  = rate × net_qty                          (= txn_amount in row_dict)
            disc   = gross × discount / 100
            final  = gross - disc - labour + debit - credit  (= what master Total sums)
        """
        self.open_add_form()
        self.select_supplier_and_qc(supplier_name)

        row_count = self.count_item_rows()
        assert row_count > 0, "No item rows auto-patched after QC selection"

        if row_configs is None:
            row_configs = []
            for i in range(row_count):
                net_qty = self.read_net_qty(i) or 1
                row_configs.append((1, int(net_qty)))

        row_dicts = []
        for i, (bags, qty) in enumerate(row_configs[:row_count]):
            ebw      = row_ebw[i]          if row_ebw          and i < len(row_ebw)          else None
            labour   = row_labour[i]       if row_labour       and i < len(row_labour)       else None
            discount = row_discount[i]     if row_discount     and i < len(row_discount)     else None
            debit    = row_round_debit[i]  if row_round_debit  and i < len(row_round_debit)  else None
            credit   = row_round_credit[i] if row_round_credit and i < len(row_round_credit) else None

            # Fill all calc modifiers in item grid BEFORE opening popup
            if ebw is not None:
                self._fill_number_nth(self.EMPTY_BAG_WEIGHT, i, ebw)
            if labour is not None:
                self._fill_number_nth(self.LABOUR_CHARGES, i, labour)
            if discount is not None:
                self._fill_number_nth(self.DISC_PERCENTAGE, i, discount)
            if debit is not None:
                self._fill_number_nth(self.ROUND_OFF_DEBIT, i, debit)
            if credit is not None:
                self._fill_number_nth(self.ROUND_OFF_CREDIT, i, credit)

            self.open_qty_details_popup(i)
            self.fill_qty_details(bags, qty)
            self.click_done()
            self.page.wait_for_timeout(500)

            rate       = self.read_rate(i)
            net_qty    = self.read_net_qty(i)
            txn_amount = self.read_txn_amount(i)
            row_dicts.append({
                "rate":       rate,
                "net_qty":    net_qty,
                "txn_amount": txn_amount,   # gross = rate × net_qty
                "no_of_bags": bags,
                "qty":        qty,
                "ebw":        ebw or 0,
                "labour":     labour or 0,
                "discount":   discount or 0,
                "debit":      debit or 0,
                "credit":     credit or 0,
            })

        # Other charges (stored separately, don't affect master Total Amount)
        if transportation is not None or agent_commission is not None:
            self.fill_other_charges(transportation=transportation, agent_commission=agent_commission)

        # Read master total from form before submit
        self.page.wait_for_timeout(500)
        total_amount = self.read_total_amount() or sum(r["txn_amount"] or 0 for r in row_dicts)

        self.page.locator(self.SUBMIT_BTN).click()
        self.handle_success_alert()
        self.navigate_to_page()

        return total_amount, row_dicts

    # ── Table helpers ─────────────────────────────────────────────────────

    def get_ref_no_of_first_row(self):
        return self.page.locator(self.REF_NO_COL).first.inner_text().strip()

    def is_pb_in_table(self, ref_no):
        return self.page.locator(self.REF_NO_COL).filter(has_text=ref_no).count() > 0

    def search_by_ref_no(self, ref_no):
        self.search_entry(ref_no)

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

    def click_row_action(self, row_index, action):
        self.page.locator("button.erp-row-trigger").nth(row_index).click()
        self.page.wait_for_timeout(400)
        label_map = {
            "View":    "Open record details",
            "Edit":    "Modify this record",
            "History": "View change log",
        }
        label = label_map.get(action, action)
        self.page.locator(
            f"//button[contains(@class,'erp-menu-item')][.//span[contains(.,'{label}')]]"
        ).click()
        self.page.wait_for_timeout(500)
