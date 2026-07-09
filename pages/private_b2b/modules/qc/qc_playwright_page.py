import math
import os
import random
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"

DOWNLOADS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "test_downloads", "qc")
)


class QCPlaywrightPage(BasePlaywrightPage):
    URL = f"{BASE_URL}/#/purchase/qc"

    # Header selectors
    SUPPLIER_NAME   = "xpath=//mat-form-field[.//mat-label[contains(.,'Supplier Name')]]//mat-select"
    ITEM_TYPE       = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Type')]]//mat-select"
    GATE_PASS       = "xpath=//mat-form-field[.//mat-label[contains(.,'Gate Pass')]]//mat-select"
    CONVERSION_RATE = "xpath=//mat-form-field[.//mat-label[contains(.,'Conversion Rate')]]//input"

    # Per-row calculated fields (use _read_nth with these)
    BASE_RATE       = "xpath=//mat-form-field[.//mat-label[contains(.,'Base Rate')]]//input"
    ACCEPTED_QTY    = "xpath=//mat-form-field[.//mat-label[contains(.,'Accepted Quantity')]]//input"
    DEDUCTION_PCT   = "xpath=//mat-form-field[.//mat-label[contains(.,'Deduction(%)')]]//input"
    DEDUCTION_RATE  = "xpath=//mat-form-field[.//mat-label[contains(.,'Deduction Rate')]]//input"
    QC_RATE         = "xpath=//mat-form-field[.//mat-label[contains(.,'QC Rate')]]//input"
    TXN_AMOUNT      = "xpath=//mat-form-field[.//mat-label[contains(.,'Transaction Amount') and not(contains(.,'Total'))]]//input"

    # QC Parameter popup
    QC_PARAM_BTN  = "xpath=//td[contains(@class,'col_input')]//button[.//mat-icon[text()='add']]"
    ACTUAL_VALUE  = "xpath=//mat-form-field[.//mat-label[contains(.,'Actual Value')]]//input"
    DONE_BTN      = "xpath=//button[contains(.,'Done')]"

    # Buttons
    ADD_BTN    = "button.erp-add-btn"
    SUBMIT_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"

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
        # Wait for any popup overlay to fully disappear
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
                print(f"\n[QC] Validation errors saved → {save_path}")
            except Exception as e:
                print(f"\n[QC] Download failed: {e}")
                self.page.locator("button.swal2-cancel").click()
            try:
                self.page.wait_for_selector(".swal2-container", state="hidden", timeout=5000)
            except Exception:
                pass
            raise RuntimeError(f"QC creation failed — validation error: {title}")

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
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
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

    # ── JS read/write helpers ────────────────────────────────────────────

    def _read_nth(self, selector, index):
        """Read the nth input matching selector — visible elements only (skips hidden popup relics)."""
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

    def _fill_nth(self, selector, index, value):
        """Fill the nth visible input matching selector (skips hidden popup relics)."""
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

    # ── Header fill ──────────────────────────────────────────────────────

    def select_supplier_and_gp(self, supplier_name):
        self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
        self.page.wait_for_timeout(2000)
        self._select_mat_by_text(self.ITEM_TYPE, "Farm")
        self.page.wait_for_timeout(3000)
        gp_selected = self._select_last_mat_option(self.GATE_PASS)
        if not gp_selected:
            # wake up: select random supplier then reselect ours
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
            self.page.wait_for_timeout(5000)
            self._select_last_mat_option(self.GATE_PASS)
        self.page.wait_for_timeout(5000)  # GRN auto-patches
        self._fill_nth(self.CONVERSION_RATE, 0, "1")

    # ── QC Parameter popup ───────────────────────────────────────────────

    def open_qc_param_popup(self, row_index=0):
        """Click the + button on item row to open QC Parameter popup."""
        self.page.locator(self.QC_PARAM_BTN).nth(row_index).click(force=True)
        self.page.wait_for_selector(self.ACTUAL_VALUE, timeout=10000)
        self.page.wait_for_timeout(500)

    def fill_actual_values(self, actual_values):
        """Fill each Actual Value input scoped to the currently active popup."""
        scope = (
            "xpath=//button[contains(.,'Done')]"
            "/ancestor::div[.//input[@placeholder='Actual Value']][1]"
            "//input[@placeholder='Actual Value']"
        )
        visible_count = self.page.locator(scope).count()
        for i, val in enumerate(actual_values[:visible_count]):
            inp = self.page.locator(scope).nth(i)
            inp.wait_for(state="visible", timeout=8000)
            inp.fill(str(val))
            self.page.wait_for_timeout(300)
        self.page.wait_for_timeout(300)

    def click_done(self):
        self.page.locator(self.DONE_BTN).click(force=True)
        try:
            self.page.wait_for_selector(self.DONE_BTN, state="hidden", timeout=5000)
        except Exception:
            pass
        self.page.wait_for_timeout(800)

    def count_item_rows(self):
        return self.page.locator(self.QC_PARAM_BTN).count()

    # ── Read calculated fields ───────────────────────────────────────────

    def read_base_rate(self, row_index=0):
        val = self._read_nth(self.BASE_RATE, row_index)
        return float(val) if val else None

    def read_accepted_qty(self, row_index=0):
        val = self._read_nth(self.ACCEPTED_QTY, row_index)
        return float(val) if val else None

    def read_deduction_pct(self, row_index=0):
        val = self._read_nth(self.DEDUCTION_PCT, row_index)
        return float(val) if val else None

    def read_deduction_rate(self, row_index=0):
        val = self._read_nth(self.DEDUCTION_RATE, row_index)
        return float(val) if val else None

    def read_qc_rate(self, row_index=0):
        val = self._read_nth(self.QC_RATE, row_index)
        return float(val) if val else None

    def safe_actual_values(self, row_index=0, max_pct=20):
        """Return actual values so total deduction_pct <= max_pct.

        Formula: deduction_pct = sum(actual_value_i * multiplier_i)
        Each v_i must satisfy: v_i * mult_i <= max_pct / n_params
        and be within [min_q_i, max_q_i].
        """
        params = []
        item_names = getattr(self, "item_names", [])
        cqp_config = getattr(self, "cqp_config", {})
        if item_names and cqp_config and row_index < len(item_names):
            params = cqp_config.get(item_names[row_index], [])

        if not params:
            per = max(1, max_pct // 3)
            return [random.randint(1, per) for _ in range(3)]

        n = len(params)
        result = []
        for p in params:
            mult   = p["multiplier"] or 1.0
            min_v  = max(1, int(p["min_q"]))
            max_v  = max(min_v, int(p["max_q"]))
            cap    = max(min_v, int(max_pct / (n * mult)))
            max_v  = min(max_v, cap)
            result.append(random.randint(min_v, max_v))
        return result

    def read_txn_amount(self, row_index=0):
        val = self._read_nth(self.TXN_AMOUNT, row_index)
        return float(val) if val else None

    # ── Table helpers ────────────────────────────────────────────────────

    def get_ref_no_of_first_row(self):
        return self.page.locator(self.REF_NO_COL).first.inner_text().strip()

    def is_qc_in_table(self, ref_no):
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
            "View": "Open record details",
            "Edit": "Modify this record",
        }
        label = label_map.get(action, action)
        self.page.locator(
            f"//button[contains(@class,'erp-menu-item')][.//span[contains(.,'{label}')]]"
        ).click()
        self.page.wait_for_timeout(500)
