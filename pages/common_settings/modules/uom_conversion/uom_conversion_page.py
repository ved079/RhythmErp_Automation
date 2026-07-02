import os
from pages.base_playwright_page import BasePlaywrightPage


class UOMConversionPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/UOM%20Conversion"
    ADD_BTN = "button:has-text('Add UOM Conversion')"
    SUBMIT = ".popup-footer button:has-text('Submit')"
    UPDATE = ".popup-footer button:has-text('Update')"
    CANCEL = ".popup-footer button:has-text('Cancel')"
    CONVERSION_FACTOR = "input[name='Conversion Factor']"
    CHANGE_LOG = "app-dynamic-history table#excel-table tbody tr"

    def handle_success_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=3000)
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        except Exception:
            pass
        try:
            if self.page.locator(self.CANCEL).is_visible():
                self._force_close_panels()
                self.page.click(self.CANCEL)
                self.page.wait_for_timeout(500)
        except Exception:
            pass
        self.page.wait_for_selector("table#excel-table", timeout=5000)

    def navigate_to_page(self):
        try:
            if "UOM%20Conversion" in self.page.url or "UOM Conversion" in self.page.url:
                self.page.reload()
            else:
                self.page.goto(self.URL)
        except Exception:
            self.page.goto(self.URL)
        try:
            self.page.wait_for_selector("table#excel-table", timeout=10000)
        except Exception:
            self.page.reload()
            self.page.wait_for_selector("table#excel-table", timeout=15000)

    def open_add_form(self):
        self.page.evaluate("""
            var btn = document.querySelector('button.erp-add-btn');
            if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
        """)
        self.page.wait_for_selector(".popup-footer", timeout=5000)

    def _force_close_panels(self):
        self.page.evaluate("""
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) { el.remove(); });
            var sw = document.querySelector('.swal2-container');
            if (sw) sw.remove();
        """)

    _fallback_counter = 0

    def _select_from_panel(self, label_text, preferred_code):
        """Click trigger, search for preferred_code, fall back to next available real option."""
        self.page.evaluate(f"""
            var labels = document.querySelectorAll('mat-label');
            for (var i = 0; i < labels.length; i++) {{
                if (labels[i].textContent.trim() === '{label_text}') {{
                    var ff = labels[i].closest('mat-form-field');
                    if (ff) {{
                        var t = ff.querySelector('.mat-mdc-select-trigger');
                        if (t) t.click();
                    }}
                    break;
                }}
            }}
        """)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        search = self.page.locator(".mat-mdc-select-panel .dd-search-input")
        try:
            search.wait_for(state="visible", timeout=3000)
            search.clear()
            search.fill(preferred_code)
            self.page.wait_for_timeout(500)
        except Exception:
            pass
        # Try exact text match first
        all_opts = self.page.locator(".mat-mdc-select-panel mat-option")
        count = all_opts.count()
        for i in range(count):
            text = all_opts.nth(i).text_content().strip()
            if text == preferred_code:
                all_opts.nth(i).click(force=True)
                return text
        # Clear search, pick rotating real option to avoid duplicate pairs
        try:
            search.clear()
            self.page.wait_for_timeout(500)
        except Exception:
            pass
        all_opts = self.page.locator(".mat-mdc-select-panel mat-option")
        count = all_opts.count()
        real_opts = []
        for i in range(count):
            text = all_opts.nth(i).text_content().strip()
            if text and "No results" not in text and "no records" not in text.lower():
                real_opts.append(text)
        if not real_opts:
            raise AssertionError(f"No real options available in {label_text} dropdown")
        UOMConversionPage._fallback_counter += 1
        idx = UOMConversionPage._fallback_counter % len(real_opts)
        chosen = real_opts[idx]
        all_opts.nth(idx).click(force=True)
        return chosen

    def select_uom(self, label_text, uom_code):
        try:
            self.page.evaluate("document.querySelector('.swal2-container')?.remove()")
        except Exception:
            pass
        self._force_close_panels()
        try:
            actual = self._select_from_panel(label_text, uom_code)
            self.page.wait_for_timeout(1000)
            self._force_close_panels()
            return actual
        except Exception as e:
            self._force_close_panels()
            raise

    def select_source_uom(self, uom_code):
        return self.select_uom("Source UOM", uom_code)

    def select_target_uom(self, uom_code):
        return self.select_uom("Target UOM", uom_code)

    def fill_conversion_factor(self, value):
        self.page.fill(self.CONVERSION_FACTOR, str(value))

    def submit(self):
        self._force_close_panels()
        self.page.click(self.SUBMIT)

    def click_update(self):
        self._force_close_panels()
        self.page.click(self.UPDATE)

    def close_popup(self):
        self._force_close_panels()
        self.page.click(self.CANCEL)

    def is_record_in_table(self, source_uom, target_uom):
        src_cells = self.page.locator("td.cdk-column-source_uom_code")
        for i in range(src_cells.count()):
            if src_cells.nth(i).inner_text().strip() == source_uom:
                row = src_cells.nth(i).locator("xpath=ancestor::tr")
                tgt = row.locator("td.cdk-column-target_uom_code").inner_text().strip()
                if tgt == target_uom:
                    return True
        return False

    def verify_record_exists(self, source_uom, target_uom):
        assert self.is_record_in_table(source_uom, target_uom), \
            f"Record {source_uom} \u2192 {target_uom} not found in table"

    def _find_row_index(self, source_uom, target_uom):
        src_cells = self.page.locator("td.cdk-column-source_uom_code")
        for i in range(src_cells.count()):
            if src_cells.nth(i).inner_text().strip() == source_uom:
                row = src_cells.nth(i).locator("xpath=ancestor::tr")
                tgt = row.locator("td.cdk-column-target_uom_code").inner_text().strip()
                if tgt == target_uom:
                    return i
        raise AssertionError(f"Record {source_uom} \u2192 {target_uom} not found in table")

    def click_view_button(self, source_uom, target_uom):
        self._force_close_panels()
        self.click_row_action(self._find_row_index(source_uom, target_uom), "View")

    def click_edit_button(self, source_uom, target_uom):
        self._force_close_panels()
        self.click_row_action(self._find_row_index(source_uom, target_uom), "Edit")

    def click_history_button(self, source_uom, target_uom):
        self._force_close_panels()
        self.click_row_action(self._find_row_index(source_uom, target_uom), "History")
        self.page.wait_for_selector("app-dynamic-history", timeout=5000)

    def search_conversion(self, text):
        self.page.evaluate("""
            var btn = document.querySelector('button[mattooltip="Search"]');
            if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
        """)
        self.page.wait_for_timeout(1500)
        self.page.evaluate(f"""
            var inp = document.getElementById('erpSearchInput');
            if (inp) {{
                inp.value = '{text}';
                inp.dispatchEvent(new Event('input', {{bubbles: true}}));
            }}
        """)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1000)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts, "View popup should not have Submit"
        assert "Update" not in texts, "View popup should not have Update"
        assert self.page.locator(self.CONVERSION_FACTOR).count() > 0, "Conversion Factor present"
