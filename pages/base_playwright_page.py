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

    def search_entry(self, value):
        search_input = self.page.locator("input#erpSearchInput")
        if not search_input.is_visible():
            self.page.evaluate("""
                var btn = document.querySelector('button[mattooltip="Search"]');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
            search_input.wait_for(state="visible", timeout=5000)
        search_input.fill(value)
        search_input.press("Enter")
        self.page.wait_for_timeout(1000)

    def click_row_action(self, row_index, action):
        self.page.locator("button.erp-row-trigger").nth(row_index).click()
        selector = self.MENU_SELECTORS.get(action)
        if selector:
            self.page.locator(selector).click()
        else:
            self.page.locator(f"button:has-text('{action}')").click()
