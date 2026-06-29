from pages.base_playwright_page import BasePlaywrightPage


class UOMPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/UOM"
    ADD_BTN = "button:has-text('Add UOM')"
    UOM_CODE = "input[name='UOM Code']"
    UOM_DESC = "input[name='UOM Description']"
    SUBMIT = ".popup-footer button:has-text('Submit')"
    UPDATE = ".popup-footer button:has-text('Update')"
    CANCEL = ".popup-footer button:has-text('Cancel')"
    CHANGE_LOG = "app-dynamic-history table#excel-table tbody tr"

    def navigate_to_page(self):
        self.page.goto(self.URL)
        try:
            self.page.wait_for_selector("table#excel-table", timeout=10000)
        except Exception:
            self.page.reload()
            self.page.wait_for_selector("table#excel-table", timeout=15000)

    def open_add_form(self):
        self.page.click(self.ADD_BTN)
        self.page.wait_for_selector(self.UOM_CODE, timeout=5000)

    def fill_uom_form(self, data):
        self.page.fill(self.UOM_CODE, data["uom_code"])
        if data.get("uom_description"):
            self.page.fill(self.UOM_DESC, data["uom_description"])

    def submit(self):
        self.page.click(self.SUBMIT)

    def search_uom(self, code):
        self.search_entry(code)

    def verify_uom_exists(self, code):
        assert self.page.locator(f"table#excel-table td:has-text('{code}')").count() > 0

    def is_uom_in_table(self, code):
        return self.page.locator(f"table#excel-table td:has-text('{code}')").count() > 0

    def _find_row_index(self, code):
        cells = self.page.locator("td.cdk-column-uom_code")
        count = cells.count()
        for i in range(count):
            if cells.nth(i).inner_text().strip() == code:
                return i
        raise AssertionError(f"UOM code '{code}' not found in table")

    def click_view_button(self, code):
        idx = self._find_row_index(code)
        self.click_row_action(idx, "View")

    def click_edit_button(self, code):
        idx = self._find_row_index(code)
        self.click_row_action(idx, "Edit")

    def click_history_button(self, code):
        idx = self._find_row_index(code)
        self.click_row_action(idx, "History")
        self.page.wait_for_selector("app-dynamic-history", timeout=5000)

    def update_uom_description(self, desc):
        self.page.fill(self.UOM_DESC, desc)

    def click_update(self):
        self.page.click(self.UPDATE)

    def close_popup(self):
        self.page.click(self.CANCEL)
