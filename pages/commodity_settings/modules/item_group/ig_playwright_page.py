from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


class IGPlaywrightPage(BasePlaywrightPage):
    URL        = f"{BASE_URL}/#/dynamic-screens/Item%20Group"
    ITEM_GROUP = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Group')]]//input"
    DESCRIPTION = "xpath=//mat-form-field[.//mat-label[contains(.,'Description')]]//input"
    SUBMIT_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    ADD_BTN    = "button.erp-add-btn"

    def navigate_to_page(self):
        self.page.goto(self.URL)
        self.page.wait_for_selector("table#excel-table", timeout=15000)

    def open_add_form(self):
        self.page.locator(self.ADD_BTN).click()
        self.page.wait_for_selector(self.ITEM_GROUP, timeout=8000)

    def submit(self):
        self.page.locator(self.SUBMIT_BTN).click()

    def close_popup(self):
        self.force_close_popup()
        self.page.wait_for_selector("table#excel-table", timeout=8000)

    def fill_form(self, data: dict):
        self.page.locator(self.ITEM_GROUP).first.click(force=True)
        self.page.locator(self.ITEM_GROUP).first.fill(data["item_group"])
        self.page.locator(self.DESCRIPTION).first.click(force=True)
        self.page.locator(self.DESCRIPTION).first.fill(data["description"])

    def create_record(self, data: dict):
        self.open_add_form()
        self.fill_form(data)
        self.submit()
        self.handle_success_alert()
        self.navigate_to_page()

    def search_group(self, name: str):
        self.search_entry(name)

    def verify_group_exists(self, name: str):
        self.page.wait_for_selector(
            f"//td[contains(@class,'cdk-column-code') and contains(.,'{name}')]",
            timeout=5000,
        )

    def is_group_in_table(self, name: str) -> bool:
        return self.page.locator(
            f"//td[contains(@class,'cdk-column-code') and contains(.,'{name}')]"
        ).count() > 0

    def click_view_button(self, name: str):
        self.click_row_action(0, "View")

    def click_history_button(self, name: str):
        self.click_row_action(0, "History")

    def verify_view_popup_read_only(self):
        self.page.wait_for_selector(".popup-footer", timeout=5000)
        assert self.page.locator(self.SUBMIT_BTN).count() == 0
