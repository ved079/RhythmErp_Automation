from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


class ICPlaywrightPage(BasePlaywrightPage):
    URL             = f"{BASE_URL}/#/dynamic-screens/Item%20Category"
    ITEM_CATEGORY   = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Category')]]//input"
    ITEM_DESC       = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Description')]]//input"
    LEVEL           = "xpath=//mat-form-field[.//mat-label[contains(.,'Level')]]//input"
    SUBMIT_BTN      = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    UPDATE_BTN      = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
    CANCEL_BTN      = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    ADD_BTN         = "button.erp-add-btn"

    def navigate_to_page(self):
        self.page.goto(self.URL)
        self.page.wait_for_selector("table#excel-table", timeout=15000)

    def open_add_form(self):
        self.page.locator(self.ADD_BTN).click()
        self.page.wait_for_selector(self.ITEM_CATEGORY, timeout=8000)

    def submit(self):
        self.page.locator(self.SUBMIT_BTN).click()

    def close_popup(self):
        try:
            self.page.locator(self.CANCEL_BTN).click()
        except Exception:
            pass
        self.page.wait_for_selector("table#excel-table", timeout=8000)

    def fill_form(self, data: dict):
        self.page.locator(self.ITEM_CATEGORY).first.click(force=True)
        self.page.locator(self.ITEM_CATEGORY).first.fill(data["item_category"])
        self.page.locator(self.ITEM_DESC).first.click(force=True)
        self.page.locator(self.ITEM_DESC).first.fill(data["item_description"])
        self.page.locator(self.LEVEL).first.click(force=True)
        self.page.locator(self.LEVEL).first.fill(str(data["level"]))

    def create_record(self, data: dict):
        self.open_add_form()
        self.fill_form(data)
        self.submit()
        self.handle_success_alert()
        self.navigate_to_page()

    def search_category(self, name: str):
        self.search_entry(name)

    def verify_category_exists(self, name: str):
        self.page.wait_for_selector(
            f"//td[contains(@class,'cdk-column-item_code') and contains(.,'{name}')]",
            timeout=5000,
        )

    def is_category_in_table(self, name: str) -> bool:
        return self.page.locator(
            f"//td[contains(@class,'cdk-column-item_code') and contains(.,'{name}')]"
        ).count() > 0

    def click_edit_button(self, name: str):
        self.click_row_action(0, "Edit")

    def update_item_description(self, desc: str):
        self.page.locator(self.ITEM_DESC).first.click(force=True)
        self.page.locator(self.ITEM_DESC).first.fill(desc)

    def click_update(self):
        self.page.locator(self.UPDATE_BTN).click()

    def click_view_button(self, name: str):
        self.click_row_action(0, "View")

    def click_history_button(self, name: str):
        self.click_row_action(0, "History")

    def verify_view_popup_read_only(self):
        self.page.wait_for_selector(".popup-footer", timeout=5000)
        assert self.page.locator(self.SUBMIT_BTN).count() == 0
