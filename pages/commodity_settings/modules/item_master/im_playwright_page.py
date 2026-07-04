import random
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


class IMPlaywrightPage(BasePlaywrightPage):
    URL          = f"{BASE_URL}/#/dynamic-screens/Item%20Master"
    ITEM_CATEGORY = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Category')]]//mat-select"
    ITEM_GROUP    = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Group')]]//mat-select"
    ITEM_TYPE     = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Type')]]//mat-select"
    ITEM_ATTR1    = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Attribute1')]]//mat-select"
    ITEM_ATTR2    = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Attribute2')]]//mat-select"
    ITEM_ATTR3    = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Attribute3')]]//mat-select"
    ITEM_ATTR4    = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Attribute4')]]//mat-select"
    ITEM_ATTR5    = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Attribute5')]]//mat-select"
    ITEM_NAME     = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Name')]]//input"
    DESCRIPTION   = "xpath=//mat-form-field[.//mat-label[contains(.,'Description')]]//input"
    UOM           = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='UOM']]//mat-select"
    SUBMIT_BTN    = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN    = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    ADD_BTN       = "button.erp-add-btn"

    def navigate_to_page(self):
        self.page.goto(self.URL)
        self.page.wait_for_selector("table#excel-table", timeout=15000)

    def open_add_form(self):
        self.page.locator(self.ADD_BTN).click()
        self.page.wait_for_selector(self.ITEM_CATEGORY, timeout=8000)

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

    def _select_mat_option_by_text(self, selector, text):
        trigger = self.page.locator(selector).first
        trigger.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        self.page.locator(f".mat-mdc-select-panel mat-option:has-text('{text}')").first.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            trigger.click(force=True)
        self.page.wait_for_timeout(300)

    def _select_uom_until_conversion_filled(self, uom_attempts: int = 10):
        BASE_UOM_CONV = "xpath=//mat-form-field[.//mat-label[contains(.,'Base Uom Conversion')]]//input"

        # collect all IA1 options once
        trigger_ia1 = self.page.locator(self.ITEM_ATTR1).first
        trigger_ia1.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        ia1_options = self.page.locator(".mat-mdc-select-panel mat-option").all()
        # close panel before iterating
        trigger_ia1.click(force=True)
        self.page.wait_for_timeout(200)

        for ia1_opt in ia1_options:
            # select this IA1 option
            trigger_ia1.click(force=True)
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
            try:
                ia1_opt.click(force=True)
            except Exception:
                pass
            try:
                self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
            except Exception:
                trigger_ia1.click(force=True)
            self.page.wait_for_timeout(300)

            # try up to uom_attempts different UOM values
            for _ in range(uom_attempts):
                self._select_random_mat_option(self.UOM)
                self.page.wait_for_timeout(400)
                val = self.page.locator(BASE_UOM_CONV).first.input_value()
                if val and val.strip():
                    return

        # exhausted all IA1 options — leave whatever state we're in

    def fill_form(self, data: dict):
        self._select_random_mat_option(self.ITEM_CATEGORY)
        self._select_random_mat_option(self.ITEM_GROUP)
        self._select_mat_option_by_text(self.ITEM_TYPE, "Farm")
        self._select_random_mat_option(self.ITEM_ATTR2)
        self._select_random_mat_option(self.ITEM_ATTR3)
        self._select_random_mat_option(self.ITEM_ATTR4)
        self._select_random_mat_option(self.ITEM_ATTR5)
        # IA1 + UOM retried together until Base UOM Conversion is auto-populated
        self._select_uom_until_conversion_filled()
        # Item Name is auto-populated from selections above — wait for it
        self.page.wait_for_timeout(500)
        if data.get("description"):
            self.page.locator(self.DESCRIPTION).first.click(force=True)
            self.page.locator(self.DESCRIPTION).first.fill(data["description"])
        self._select_random_mat_option(
            "xpath=//mat-form-field[.//mat-label[contains(.,'HSN SAC Code')]]//mat-select"
        )

    def get_auto_item_name(self) -> str:
        return self.page.locator(self.ITEM_NAME).first.input_value()

    def create_record(self, data: dict) -> str:
        self.open_add_form()
        self.fill_form(data)
        name = self.get_auto_item_name()
        self.submit()
        self.handle_success_alert()
        self.navigate_to_page()
        return name

    def search_item(self, name: str):
        self.search_entry(name)

    def verify_item_exists(self, name: str):
        self.page.wait_for_selector(
            f"//td[contains(@class,'cdk-column-name') and contains(.,'{name}')]",
            timeout=5000,
        )

    def is_item_in_table(self, name: str) -> bool:
        return self.page.locator(
            f"//td[contains(@class,'cdk-column-name') and contains(.,'{name}')]"
        ).count() > 0

    def click_view_button(self, name: str):
        self.click_row_action(0, "View")

    def click_history_button(self, name: str):
        self.click_row_action(0, "History")

    def verify_view_popup_read_only(self):
        self.page.wait_for_selector(".popup-footer", timeout=5000)
        assert self.page.locator(self.SUBMIT_BTN).count() == 0
