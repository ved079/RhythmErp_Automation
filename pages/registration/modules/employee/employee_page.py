from pages.base_playwright_page import BasePlaywrightPage


class EmployeePage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Employee/Employee"

    EMPLOYEE_NAME = "xpath=//mat-form-field[.//mat-label[contains(.,'Employee Name')]]//input"
    EMAIL         = "xpath=//mat-form-field[.//mat-label[contains(.,'Email')]]//input"
    PHONE_NUMBER  = "xpath=//mat-form-field[.//mat-label[contains(.,'Phone Number')]]//input"
    DESIGNATION   = "xpath=//mat-form-field[.//mat-label[contains(.,'Designation')]]//mat-select"
    DEPARTMENT    = "xpath=//mat-form-field[.//mat-label[contains(.,'Department')]]//mat-select"
    SUBMIT_BTN    = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN    = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    SEARCH_INPUT  = "#erpSearchInput"

    def _clear_overlays(self):
        self.page.evaluate(
            "document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove())"
        )

    def _select_mat_option(self, selector):
        sel = self.page.locator(selector)
        sel.wait_for(state="visible", timeout=5000)
        sel.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        self.page.locator(".mat-mdc-select-panel mat-option").first.wait_for(state="visible", timeout=3000)
        self.page.evaluate("document.querySelector('.mat-mdc-select-panel mat-option')?.click()")
        self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=5000)
        self.page.wait_for_timeout(300)

    def navigate_to_page(self):
        try:
            if "Employee" in self.page.url:
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
        try:
            self.page.click("button.erp-add-btn")
        except Exception:
            self.page.evaluate("""
                var btn = document.querySelector('button.erp-add-btn');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
        self.page.wait_for_selector(self.EMPLOYEE_NAME, timeout=5000)

    def fill_form(self, data):
        if data.get("employee_name"):
            self.page.locator(self.EMPLOYEE_NAME).first.click(force=True)
            self.page.locator(self.EMPLOYEE_NAME).first.fill(data["employee_name"])
            self.page.locator(self.EMPLOYEE_NAME).first.press("Tab")

        if data.get("email"):
            self.page.locator(self.EMAIL).first.click(force=True)
            self.page.locator(self.EMAIL).first.fill(data["email"])
            self.page.locator(self.EMAIL).first.press("Tab")

        if data.get("phone_number"):
            self.page.locator(self.PHONE_NUMBER).first.click(force=True)
            self.page.locator(self.PHONE_NUMBER).first.fill(data["phone_number"])
            self.page.locator(self.PHONE_NUMBER).first.press("Tab")

        self._select_mat_option(self.DESIGNATION)
        self.page.wait_for_timeout(300)

        self._select_mat_option(self.DEPARTMENT)
        self.page.wait_for_timeout(300)

        self._clear_overlays()

    def submit(self):
        self._clear_overlays()
        self.page.click(self.SUBMIT_BTN)

    def close_popup(self):
        self._clear_overlays()
        self.page.click(self.CANCEL_BTN)

    def handle_success_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=5000)
            title = (self.page.locator("#swal2-title").text_content() or "").strip().lower()
            body = (self.page.locator("#swal2-html-container").text_content() or "").strip()
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
            if "validation" in title or "failed" in title or "error" in title:
                labels = self.page.locator("mat-form-field.ng-invalid mat-label").all_text_contents()
                raise AssertionError(f"Validation failed — invalid fields: {labels} — body: '{body}'")
        except AssertionError:
            raise
        except Exception:
            pass
        try:
            if self.page.locator(self.CANCEL_BTN).is_visible():
                self._clear_overlays()
                self.page.locator(self.CANCEL_BTN).click()
                self.page.wait_for_timeout(500)
        except Exception:
            pass
        self.page.wait_for_selector("table#excel-table", timeout=8000)

    def handle_validation_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=5000)
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_selector("table#excel-table", timeout=5000)

    def create_record(self, data):
        self.open_add_form()
        self.fill_form(data)
        self.submit()
        self.handle_success_alert()
        self.navigate_to_page()

    def search_employee(self, employee_name):
        inp = self.page.locator(self.SEARCH_INPUT)
        if not inp.is_visible():
            self.page.evaluate("""
                var btn = document.querySelector('button[mattooltip="Search"]');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
            self.page.wait_for_timeout(800)
        inp.wait_for(state="visible", timeout=5000)
        inp.fill(employee_name)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1500)

    def is_employee_in_table(self, employee_name):
        for _ in range(10):
            rows = self.page.locator("table#excel-table tbody tr")
            for i in range(rows.count()):
                if employee_name in rows.nth(i).inner_text():
                    return True
            self.page.wait_for_timeout(300)
        return False

    def verify_employee_exists(self, employee_name):
        assert self.is_employee_in_table(employee_name), f"Employee '{employee_name}' not found in table"

    def _find_row_index(self, employee_name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if employee_name in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Employee '{employee_name}' not found in table")

    def click_view_button(self, employee_name):
        self.click_row_action(self._find_row_index(employee_name), "View")

    def click_history_button(self, employee_name):
        self.click_row_action(self._find_row_index(employee_name), "History")
        self.page.wait_for_timeout(1000)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
