import random
from pages.base_playwright_page import BasePlaywrightPage


class EmployeePage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Employee/Employee"

    # ── Selectors ─────────────────────────────────────────────────────────
    SUBMIT_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    UPDATE_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
    CANCEL_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    SEARCH_INPUT = "#erpSearchInput"

    EMPLOYEE_NAME = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Employee Name']]//input"
    EMAIL         = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Email']]//input"
    PHONE_NUMBER  = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Phone Number']]//input"
    DESIGNATION   = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Designation']]//mat-select"
    DEPARTMENT    = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Department']]//mat-select"

    # ── mat-select helpers ────────────────────────────────────────────────
    def _select_mat_option_by_text(self, selector, text, nth=0):
        self.page.locator(selector).nth(nth).click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).filter(has_text=text)
        matched = None
        for opt in options.all():
            if opt.inner_text().strip() == text:
                matched = opt
                break
        if matched:
            matched.click(force=True)
        else:
            self.page.locator(".mat-mdc-select-panel mat-option").filter(has_text=text).first.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(100)

    def _select_random_mat_option(self, selector, nth=0):
        self.page.locator(selector).nth(nth).click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(".mat-mdc-select-panel mat-option:not(.dd-clear-option)").all()
        if options:
            random.choice(options).click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(200)

    def _fill_text(self, selector, value, nth=0):
        loc = self.page.locator(selector).nth(nth)
        loc.click(force=True)
        loc.fill(str(value))
        loc.press("Tab")

    def _clear_overlays(self):
        self.page.evaluate("document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove())")

    # ── Navigation ────────────────────────────────────────────────────────
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
        self.page.locator("button.erp-add-btn").click()
        self.page.wait_for_selector(self.EMPLOYEE_NAME, timeout=8000)

    # ── Form fill ─────────────────────────────────────────────────────────
    def fill_form(self, data):
        self._fill_text(self.EMPLOYEE_NAME, data["employee_name"])
        self._fill_text(self.EMAIL, data.get("email", "employee@testmail.com"))
        self._fill_text(self.PHONE_NUMBER, data["phone_number"])
        self._select_random_mat_option(self.DESIGNATION)
        self.page.locator(self.DEPARTMENT).wait_for(state="visible", timeout=10000)
        self._select_random_mat_option(self.DEPARTMENT)
        self._clear_overlays()

    def submit(self):
        self._clear_overlays()
        self.page.click(self.SUBMIT_BTN)

    def close_popup(self):
        self._clear_overlays()
        try:
            self.page.locator(self.CANCEL_BTN).click(timeout=3000)
        except Exception:
            try:
                self.page.get_by_role("button", name="close").click(timeout=3000)
            except Exception:
                pass

    def handle_success_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=5000)
            title = (self.page.locator("#swal2-title").text_content() or "").strip().lower()
            body = (self.page.locator("#swal2-html-container").text_content() or "").strip()
            if "validation" in title or "failed" in title or "error" in title:
                try:
                    import tempfile, openpyxl
                    self.page.wait_for_selector(".swal2-container", timeout=3000)
                    with self.page.expect_download() as _dl:
                        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
                    _d = _dl.value
                    _p = tempfile.mktemp(suffix="." + _d.suggested_filename.rsplit(".", 1)[-1])
                    _d.save_as(_p)
                    _ws = openpyxl.load_workbook(_p).active
                    _rows = [r for r in _ws.iter_rows(values_only=True) if any(c for c in r)]
                    print("\n=== VALIDATION ERROR EXCEL ===")
                    for _r in _rows:
                        print(_r)
                    print("==============================\n")
                except Exception as _e:
                    print(f"[could not read error excel: {_e}]")
                    self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
                labels = self.page.locator("mat-form-field.ng-invalid mat-label").all_text_contents()
                raise AssertionError(f"Validation failed — invalid fields: {labels} — body: '{body}'")
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        except AssertionError:
            raise
        except Exception:
            pass

    def download_validation_error_excel(self):
        import tempfile
        self.page.wait_for_selector(".swal2-container", timeout=10000)
        with self.page.expect_download() as dl:
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        download = dl.value
        path = tempfile.mktemp(suffix="." + download.suggested_filename.rsplit(".", 1)[-1])
        download.save_as(path)
        try:
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=5000)
        except Exception:
            pass
        return path

    def create_record(self, data):
        self.open_add_form()
        self.fill_form(data)
        self.submit()
        self.handle_success_alert()

    # ── Search / table helpers ────────────────────────────────────────────
    def search_employee(self, name):
        inp = self.page.locator(self.SEARCH_INPUT)
        if not inp.is_visible():
            self.page.evaluate("""
                var btn = document.querySelector('button[mattooltip="Search"]');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
            self.page.wait_for_timeout(500)
        inp.wait_for(state="visible", timeout=5000)
        inp.fill(name)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1000)

    def verify_employee_exists(self, name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if name in rows.nth(i).inner_text():
                return
        raise AssertionError(f"Employee '{name}' not found in table")

    def _find_row_index(self, name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if name in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Employee '{name}' not found in table")

    def click_view_button(self, name):
        self.search_employee(name)
        self.click_row_action(self._find_row_index(name), "View")

    def click_edit_button(self, name):
        self.search_employee(name)
        self.click_row_action(self._find_row_index(name), "Edit")
        self.page.wait_for_selector(self.EMPLOYEE_NAME, timeout=5000)

    def click_update(self):
        self.page.locator(self.UPDATE_BTN).click()
        self.handle_success_alert()

    def get_first_employee_name(self):
        self.click_row_action(0, "View")
        self.page.wait_for_selector(self.EMPLOYEE_NAME, timeout=8000)
        name = self.page.locator(self.EMPLOYEE_NAME).input_value()
        self.force_close_popup()
        self.page.wait_for_timeout(300)
        return name

    def get_view_field_value(self, name, field_label):
        self.click_view_button(name)
        self.page.wait_for_selector(
            f"xpath=//mat-label[contains(.,'{field_label}')]/ancestor::mat-form-field//input",
            timeout=8000,
        )
        value = self.page.locator(
            f"xpath=//mat-label[contains(.,'{field_label}')]/ancestor::mat-form-field//input"
        ).input_value()
        self.force_close_popup()
        self.page.wait_for_timeout(300)
        return value

    def export_master(self):
        self.page.locator("button.mat-mdc-menu-trigger.erp-outline-btn").click()
        self.page.wait_for_selector(".mat-mdc-menu-panel", timeout=5000)
        with self.page.expect_download() as dl:
            self.page.locator(
                ".mat-mdc-menu-panel button.mat-mdc-menu-item:has(.erp-menu-title:text-is('Export Master'))"
            ).click()
        return dl.value
