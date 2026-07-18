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
