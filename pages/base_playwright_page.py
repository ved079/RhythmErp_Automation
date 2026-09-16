class BasePlaywrightPage:
    MENU_SELECTORS = {
        "View":    "//button[contains(@class,'erp-menu-item')][.//span[contains(.,'Open record details')]]",
        "Edit":    "//button[contains(@class,'erp-menu-item')][.//span[contains(.,'Modify this record')]]",
        "History": "//button[contains(@class,'erp-menu-item')][.//span[contains(.,'View change log')]]",
    }

    def __init__(self, page):
        self.page = page

    def navigate(self, url):
        self.page.goto(url)

    def handle_success_alert(self):
        self.page.wait_for_selector(".swal2-container", timeout=5000)
        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        self.page.wait_for_selector("table#excel-table", timeout=5000)

    def handle_submit_result(self, timeout=8000):
        """Wait for swal2 after submit. Returns True on success, False on error.

        Either way dismisses the alert. Caller should cancel + retry on False.
        """
        try:
            self.page.wait_for_selector(".swal2-container", timeout=timeout)
        except Exception:
            return False  # no alert at all — likely inline validation error

        # Detect error vs success by icon class
        is_error = self.page.locator(".swal2-icon.swal2-error, .swal2-icon.swal2-warning").count() > 0
        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        try:
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        except Exception:
            pass

        if is_error:
            return False

        try:
            self.page.wait_for_selector("table#excel-table", timeout=5000)
        except Exception:
            pass
        return True

    def handle_validation_alert(self):
        self.page.wait_for_selector(".swal2-container", timeout=5000)
        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        self.page.wait_for_selector("table#excel-table", timeout=5000)

    def force_close_popup(self):
        cancel = self.page.locator(".popup-footer button:has-text('Cancel')")
        try:
            cancel.wait_for(state="visible", timeout=2000)
            cancel.click()
            return
        except Exception:
            pass
        try:
            close = self.page.locator("//mat-icon[text()='close']/ancestor::button")
            close.wait_for(state="visible", timeout=2000)
            close.click()
        except Exception:
            pass

    def get_table_row_count(self):
        return self.page.locator("table#excel-table tbody tr").count()

    def set_page_size(self, size: str):
        """Set the paginator page-size dropdown so all records are visible."""
        self.page.locator("mat-paginator mat-select").click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        )
        matched = None
        for opt in options.all():
            if opt.inner_text().strip() == size:
                matched = opt
                break
        if matched:
            matched.click(force=True)
        else:
            options.filter(has_text=size).first.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(1000)

    def read_table_data(self, col_indices: list) -> list:
        """Return list of tuples — one per tbody row — for the given column indices."""
        rows = self.page.locator("table#excel-table tbody tr")
        result = []
        for i in range(rows.count()):
            cells = rows.nth(i).locator("td")
            result.append(tuple(cells.nth(c).text_content().strip() for c in col_indices))
        return result

    def search_entry(self, value):
        search_input = self.page.locator("input#erpSearchInput")
        if not search_input.is_visible():
            self.page.evaluate("""
                var btn = document.querySelector('button[mattooltip="Search"]')
                       || document.querySelector('button[matTooltip="Search"]');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
            self.page.wait_for_timeout(300)
            if not search_input.is_visible():
                try:
                    self.page.locator("button").filter(has_text="search").first.click(force=True)
                except Exception:
                    pass
            search_input.wait_for(state="visible", timeout=8000)
        search_input.fill(value)
        search_input.press("Enter")
        self.page.wait_for_timeout(1000)

    def _find_row_index(self, search_text):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if search_text in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Row containing '{search_text}' not found in table")

    def get_history_entry_count(self, record_name):
        """Open History for record_name, return row count (0 if empty), then close.

        History opens in-place (replaces the main table), so after a fixed wait
        whatever is in table#excel-table is the history content.
        """
        self.click_row_action(self._find_row_index(record_name), "History")
        self.page.wait_for_timeout(2500)
        if self.page.locator(".empty-state").is_visible():
            count = 0
        else:
            # History opens as an overlay — nth(1) is the dialog table, nth(0) is the main page table
            count = self.page.locator("table#excel-table").nth(1).locator("tbody tr").count()
        self.force_close_popup()
        self.page.wait_for_timeout(500)
        return count

    def get_row_field_value(self, row_index, field_label):
        """Open View on row_index, read a field value, close popup."""
        self.click_row_action(row_index, "View")
        selector = f"xpath=//mat-label[contains(.,'{field_label}')]/ancestor::mat-form-field//input"
        self.page.wait_for_selector(selector, timeout=8000)
        value = self.page.locator(selector).first.input_value()
        self.force_close_popup()
        self.page.wait_for_timeout(500)
        return value

    def bulk_edit_field(self, record_name, field_label, values):
        """Apply each value in sequence via edit → update, without reading history in between.

        Searches before each edit because navigate_to_page() clears the search filter.
        """
        for v in values:
            self.search_entry(record_name)
            self.edit_field_and_update(record_name, field_label, v)

    def click_row_action(self, row_index, action):
        self.page.evaluate(f"""
            var btns = document.querySelectorAll('button.erp-row-trigger');
            if (btns[{row_index}]) {{ btns[{row_index}].scrollIntoView({{block:'center'}}); btns[{row_index}].click(); }}
        """)
        self.page.wait_for_selector("div.mat-mdc-menu-panel", timeout=3000)
        selector = self.MENU_SELECTORS.get(action)
        if selector:
            self.page.locator(selector).first.click()
        else:
            self.page.locator(f"button:has-text('{action}')").first.click()
        self.page.wait_for_timeout(500)
