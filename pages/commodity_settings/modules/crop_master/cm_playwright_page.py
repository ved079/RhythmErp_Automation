from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


class CMPlaywrightPage(BasePlaywrightPage):
    URL        = f"{BASE_URL}/#/dynamic-screens/Crop%20Master"
    NAME       = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Name']]//input"
    SUBMIT_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    UPDATE_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
    CANCEL_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    ADD_BTN    = "button.erp-add-btn"

    def navigate_to_page(self):
        self.page.goto(self.URL)
        self.page.wait_for_selector("table#excel-table", timeout=15000)

    def open_add_form(self):
        self.page.locator(self.ADD_BTN).click()
        self.page.wait_for_selector(self.NAME, timeout=8000)

    def submit(self):
        self.page.locator(self.SUBMIT_BTN).click()

    def close_popup(self):
        try:
            self.page.locator(self.CANCEL_BTN).click()
        except Exception:
            pass
        self.page.wait_for_selector("table#excel-table", timeout=8000)

    def fill_form(self, data: dict):
        self.page.locator(self.NAME).first.click(force=True)
        self.page.locator(self.NAME).first.fill(data["name"])

    def create_record(self, data: dict):
        self.open_add_form()
        self.fill_form(data)
        self.submit()
        self.handle_success_alert()
        self.navigate_to_page()

    def search_crop(self, name: str):
        self.search_entry(name)

    def verify_crop_exists(self, name: str):
        self.page.wait_for_selector(
            f"//td[contains(@class,'cdk-column-name') and contains(.,'{name}')]",
            timeout=5000,
        )

    def is_crop_in_table(self, name: str) -> bool:
        return self.page.locator(
            f"//td[contains(@class,'cdk-column-name') and contains(.,'{name}')]"
        ).count() > 0

    def click_edit_button(self, name: str):
        self.click_row_action(0, "Edit")

    def update_name(self, name: str):
        self.page.locator(self.NAME).first.click(force=True)
        self.page.locator(self.NAME).first.fill(name)

    def click_update(self):
        self.page.locator(self.UPDATE_BTN).click()

    def click_view_button(self, name: str):
        self.click_row_action(0, "View")

    def click_history_button(self, name: str):
        self.click_row_action(0, "History")

    def verify_view_popup_read_only(self):
        self.page.wait_for_selector(".popup-footer", timeout=5000)
        assert self.page.locator(self.SUBMIT_BTN).count() == 0
