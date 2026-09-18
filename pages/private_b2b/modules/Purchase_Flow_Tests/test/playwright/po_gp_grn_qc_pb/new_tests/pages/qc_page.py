from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


def compute_actual_values(cqp_params: list) -> list:
    """Compute safe actual_values from CQP param dicts (same logic as QCPlaywrightPage.safe_actual_values).

    - Pattern A (slab1 mult=0, slab2 exists): keep all at slab1.max_q, push one into slab2 for small deduction.
    - Pattern B (single slab, mult≠0): use min_q + 1.
    - Pattern C (slab1 mult=0, no slab2): stay at slab1.max_q (0% deduction).
    Falls back to [1] * n if params is empty.
    """
    if not cqp_params:
        return [1]

    n = len(cqp_params)
    result = [None] * n
    pattern_a_idx = []
    pattern_b_idx = []

    for i, p in enumerate(cqp_params):
        slabs = p.get("slabs", [])
        slab1 = slabs[0] if slabs else p
        if len(slabs) >= 2 and slab1["multiplier"] == 0:
            pattern_a_idx.append(i)
        elif slab1["multiplier"] != 0:
            pattern_b_idx.append(i)
        else:
            # slab1 mult=0, no slab2 — stay at slab1.max_q but cap at 99 to avoid % overflow
            result[i] = min(round(slab1["max_q"], 2), 99.0)

    for i in pattern_b_idx:
        slabs = cqp_params[i].get("slabs", [])
        slab1 = slabs[0] if slabs else cqp_params[i]
        result[i] = round(slab1["min_q"] + 1, 2)

    for i in pattern_a_idx:
        result[i] = round(cqp_params[i]["max_q"], 2)

    if pattern_a_idx:
        best_i = min(
            pattern_a_idx,
            key=lambda i: (int(cqp_params[i]["slabs"][1]["max_q"]) - cqp_params[i]["slabs"][0]["max_q"])
                          * cqp_params[i]["slabs"][1]["multiplier"]
        )
        result[best_i] = int(cqp_params[best_i]["slabs"][1]["max_q"])

    return [v if v is not None else 1 for v in result]


class QCPage(BasePlaywrightPage):
    URL = f"{BASE_URL}/#/purchase/qc"

    # ── Header selectors ────────────────────────────────────────────────
    SUPPLIER_NAME   = "xpath=//mat-label[contains(.,'Supplier Name')]/ancestor::mat-form-field//mat-select"
    GATE_PASS       = "xpath=//mat-label[contains(.,'Gate Pass')]/ancestor::mat-form-field//mat-select"
    GRN             = "xpath=//mat-label[contains(.,'GRN')]/ancestor::mat-form-field//mat-select"

    # ── Bags detail dialog selectors ────────────────────────────────────
    # Note: label has double space — matches DOM text exactly
    TYPE_OF_BAG     = "xpath=//mat-label[contains(.,'Type of Bag')]/ancestor::mat-form-field//mat-select"
    NO_OF_BAGS      = "xpath=//mat-label[contains(.,'No of  Bags')]/ancestor::mat-form-field//input"
    PER_BAG_WEIGHT  = "xpath=//mat-label[contains(.,'Per Bag Weight (KG)')]/ancestor::mat-form-field//input"
    TOTAL_WEIGHT    = "xpath=//mat-label[contains(.,'Total Weight')]/ancestor::mat-form-field//input"
    RECEIVED_QTY    = "xpath=//mat-label[contains(.,'Received Qty.')]/ancestor::mat-form-field//input"
    NET_OF_EMPTY_BAG_QTY = "xpath=//mat-label[contains(.,'Net of Empty Bag Qty.')]/ancestor::mat-form-field//input"

    # ── Quality parameters dialog selectors ─────────────────────────────
    # actual_value inputs — select by nth(index)
    ACTUAL_VALUE    = "xpath=//mat-label[contains(.,'Actual Value')]/ancestor::mat-form-field//input"

    # ── Read-only computed fields ────────────────────────────────────────
    QC_DEDUCTION_PCT      = "xpath=//mat-label[contains(.,'QC Deduction %')]/ancestor::mat-form-field//input"
    NET_PURCHASE_RATE     = "xpath=//mat-label[contains(.,'Net Purchase Rate')]/ancestor::mat-form-field//input"
    NET_PURCHASE_AMOUNT   = "xpath=//mat-label[contains(.,'Net Purchase Amount')]/ancestor::mat-form-field//input"

    # ── Cancel / close popup ─────────────────────────────────────────────
    CANCEL_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"

    # ── Detail opener buttons ─────────────────────────────────────────────
    BAGS_OPENER       = "button[data-sd-details-opener='qc_details[0].qc_bags_details']"
    QC_PARAMS_OPENER  = "button[data-sd-details-opener='qc_details[0].qc_parameter_details']"

    # ── Buttons ──────────────────────────────────────────────────────────
    ADD_BTN      = "button.erp-add-btn"
    DONE_BTN     = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Done')]"
    SUBMIT_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    SEARCH_BTN   = "button[mattooltip='Search']"
    SEARCH_INPUT = "input#erpSearchInput"
    ROW_TRIGGER  = "button.erp-row-trigger"

    # ── Table ────────────────────────────────────────────────────────────
    REF_NO_COL = "td.cdk-column-transaction_ref_no"

    # ── Navigation ───────────────────────────────────────────────────────

    def navigate_to_page(self):
        self.page.goto(self.URL)
        self.page.wait_for_selector("mat-form-field, table.mat-mdc-table, .page-content", timeout=20000)

    def open_add_form(self):
        self.page.locator(self.ADD_BTN).click()
        self.page.wait_for_selector(self.SUPPLIER_NAME, timeout=15000)

    # ── Header actions ────────────────────────────────────────────────────

    def select_supplier(self, name):
        self._select_mat_by_text(self.SUPPLIER_NAME, name)

    def select_gate_pass(self, gp_ref_no):
        self._select_mat_by_text(self.GATE_PASS, gp_ref_no)
        # Gate pass selection auto-populates GRN and all item fields
        self.page.locator(self.GRN).wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Bags detail dialog ────────────────────────────────────────────────
    # Call in order: open_bags → select_type_of_bag → fill_no_of_bags → fill_per_bag_weight → done_bags

    def open_bags_detail(self):
        self.page.locator(self.BAGS_OPENER).wait_for(state="visible", timeout=10000)
        self.page.locator(self.BAGS_OPENER).click()
        self.page.locator(self.TYPE_OF_BAG).wait_for(state="visible", timeout=10000)

    def select_type_of_bag(self, value):
        self._select_mat_by_text(self.TYPE_OF_BAG, value)

    def fill_no_of_bags(self, value):
        self.page.locator(self.NO_OF_BAGS).first.fill(str(value))

    def fill_per_bag_weight(self, value):
        self.page.locator(self.PER_BAG_WEIGHT).first.fill(str(value))

    def done_bags(self):
        """Click Done in the Bags detail dialog."""
        self.page.locator(self.DONE_BTN).click()
        self.page.wait_for_timeout(500)

    # ── Quality parameters dialog ─────────────────────────────────────────

    def open_quality_params(self):
        self.page.locator(self.QC_PARAMS_OPENER).wait_for(state="visible", timeout=10000)
        self.page.locator(self.QC_PARAMS_OPENER).click()
        self.page.locator(self.ACTUAL_VALUE).first.wait_for(state="visible", timeout=10000)

    def count_actual_value_inputs(self):
        """Return number of visible Actual Value inputs currently in the form."""
        return self.page.locator(self.ACTUAL_VALUE).count()

    def fill_actual_value(self, row_index, value):
        """Fill actual_value for quality parameter at row_index (0-based)."""
        self.page.locator(self.ACTUAL_VALUE).nth(row_index).fill(str(value))

    def done_quality_params(self):
        """Click Done in the Quality Parameters dialog."""
        self.page.locator(self.DONE_BTN).click()
        self.page.wait_for_timeout(500)

    def close_quality_params_popup(self):
        """Close the quality parameters inner panel if still open after Done."""
        btn = self.page.get_by_role("button", name="close")
        try:
            btn.wait_for(state="visible", timeout=2000)
            btn.click()
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    # ── Submit & search ───────────────────────────────────────────────────

    def submit(self):
        self.page.locator(self.SUBMIT_BTN).click(force=True)
        self.handle_success_alert()
        self.navigate_to_page()

    def search(self, ref_no):
        if not self.page.locator(self.SEARCH_INPUT).is_visible():
            self.page.locator(self.SEARCH_BTN).click()
        self.page.locator(self.SEARCH_INPUT).fill(ref_no)
        self.page.locator(self.SEARCH_INPUT).press("Enter")
        self.page.wait_for_timeout(1000)

    def open_view(self, ref_no):
        self.page.locator(f"tr:has-text('{ref_no}')").first.locator(self.ROW_TRIGGER).click(force=True)
        self.page.wait_for_selector(".mat-mdc-menu-panel", timeout=8000)
        self.page.locator(".mat-mdc-menu-panel button.mat-mdc-menu-item:has(.erp-menu-title:text-is('View'))").click()
        self.page.wait_for_timeout(1000)

    def close_view(self):
        self.force_close_popup()

    # ── Read values ───────────────────────────────────────────────────────

    def get_ref_no_of_first_row(self):
        self.page.wait_for_selector(self.REF_NO_COL, timeout=15000)
        return self.page.locator(self.REF_NO_COL).first.inner_text().strip()

    def get_qc_deduction_pct(self):
        return self.page.locator(self.QC_DEDUCTION_PCT).input_value()

    def computed_fields_ready(self) -> bool:
        """Return True if Net Purchase Rate and Net Purchase Amount are both non-empty."""
        try:
            rate = self.page.locator(self.NET_PURCHASE_RATE).input_value()
            amount = self.page.locator(self.NET_PURCHASE_AMOUNT).input_value()
            return bool(rate and rate.strip() and amount and amount.strip())
        except Exception:
            return False

    def cancel_form(self):
        """Cancel / close the add form without saving."""
        try:
            self.page.locator(self.CANCEL_BTN).click()
            self.page.wait_for_timeout(500)
        except Exception:
            self.force_close_popup()

    def get_gate_pass(self):
        return self.page.locator(self.GATE_PASS).text_content().strip()

    def get_grn(self):
        return self.page.locator(self.GRN).text_content().strip()

    def handle_success_alert(self):
        self.page.wait_for_selector(".swal2-container", timeout=8000)
        title = self.page.locator("#swal2-title").inner_text().strip()
        message = self.page.locator("#swal2-html-container").inner_text().strip()
        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        try:
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=15000)
        except Exception:
            pass
        if any(k in title for k in ("Validation", "Failed", "Error")):
            raise RuntimeError(f"QC submit failed — {title}: {message}")

    def _select_mat_by_text(self, selector, text):
        self.page.locator(selector).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
        search = self.page.locator(".mat-mdc-select-panel input.dd-search-input")
        if search.count() > 0:
            search.fill(text)
            self.page.wait_for_timeout(800)
        for opt in self.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).all():
            if opt.inner_text().strip() == text:
                opt.click(force=True)
                break
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
