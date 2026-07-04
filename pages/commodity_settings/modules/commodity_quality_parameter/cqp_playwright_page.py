import random
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


class CQPPlaywrightPage(BasePlaywrightPage):
    URL              = f"{BASE_URL}/#/dynamic-screens/Commodity%20Quality%20Parameter"
    ITEM_NAME        = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Name')]]//mat-select"
    TRANSACTION_TYPE = "xpath=//mat-form-field[.//mat-label[contains(.,'Transaction Type')]]//mat-select"
    QUALITY_PARAM    = "xpath=//mat-form-field[.//mat-label[contains(.,'Quality Parameter')]]//mat-select"
    MIN_QUALITY      = "xpath=//mat-form-field[.//mat-label[contains(.,'Min Quality Value')]]//input"
    MAX_QUALITY      = "xpath=//mat-form-field[.//mat-label[contains(.,'Max Quality Value')]]//input"
    MULTIPLIER       = "xpath=//mat-form-field[.//mat-label[contains(.,'Multiplier')]]//input"
    SUBMIT_BTN       = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN       = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    ADD_BTN          = "button.erp-add-btn"
    ADD_ROW_BTN      = "button.add-row-btn"

    def navigate_to_page(self):
        self.page.goto(self.URL)
        self.page.wait_for_selector("table#excel-table", timeout=15000)

    def open_add_form(self):
        self.page.locator(self.ADD_BTN).click()
        self.page.wait_for_selector(self.ITEM_NAME, timeout=8000)

    def submit(self):
        self.page.locator(self.SUBMIT_BTN).click()

    def close_popup(self):
        self.force_close_popup()
        self.page.wait_for_selector("table#excel-table", timeout=8000)

    def _select_random_mat_option(self, selector):
        trigger = self.page.locator(selector).first
        trigger.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(".mat-mdc-select-panel mat-option").all()
        if options:
            random.choice(options).click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            trigger.click(force=True)
        self.page.wait_for_timeout(300)

    def _add_row(self):
        for btn in self.page.locator(self.ADD_ROW_BTN).all():
            if btn.is_visible():
                btn.click()
                self.page.wait_for_timeout(500)
                return

    def fill_form(self, data: dict):
        self._select_random_mat_option(self.ITEM_NAME)
        self._select_random_mat_option(self.TRANSACTION_TYPE)
        # From Date / To Date are auto-populated — skip
        # Grid already has a pre-existing row — fill it directly, do NOT add row
        self._select_random_mat_option(self.QUALITY_PARAM)
        for selector, value in [
            (self.MIN_QUALITY, str(data["min_quality"])),
            (self.MAX_QUALITY, str(data["max_quality"])),
            (self.MULTIPLIER,  str(data["multiplier"])),
        ]:
            field = self.page.locator(selector).first
            field.click(force=True)
            field.fill(value)

    def create_record(self, data: dict):
        self.open_add_form()
        self.fill_form(data)
        self.submit()
        self.handle_success_alert()
        self.navigate_to_page()

    def search_cqp(self, value: str):
        search_input = self.page.locator("input#erpSearchInput")
        if not search_input.is_visible():
            self.page.locator("button[mattooltip='Search']").click()
            search_input.wait_for(state="visible", timeout=5000)
        search_input.fill(value)
        search_input.press("Enter")
        self.page.wait_for_timeout(1000)

    def verify_cqp_exists(self, value: str):
        self.page.wait_for_selector(
            f"//td[contains(@class,'cdk-column-item_ref_id') and contains(.,'{value}')]",
            timeout=5000,
        )

    def is_cqp_in_table(self, value: str) -> bool:
        return self.page.locator(
            f"//td[contains(@class,'cdk-column-item_ref_id') and contains(.,'{value}')]"
        ).count() > 0

    def get_first_item_name_in_table(self) -> str:
        cell = self.page.locator("td.cdk-column-item_ref_id").first
        return cell.inner_text().strip()

    def click_view_button(self):
        self.click_row_action(0, "View")

    def click_history_button(self):
        self.click_row_action(0, "History")

    def verify_view_popup_read_only(self):
        self.page.wait_for_selector(".popup-footer", timeout=5000)
        assert self.page.locator(self.SUBMIT_BTN).count() == 0
