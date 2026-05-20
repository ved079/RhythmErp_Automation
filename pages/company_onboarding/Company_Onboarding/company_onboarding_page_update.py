"""
company_onboarding_page_update.py
----------------------------------
Update page object for Company Onboarding.
Inherits from CompanyOnboardingPage.

Step order (matches actual app):
  Step 1 = Company Details  (including Company Code)
  Step 2 = Promoters
  Step 3 = Address
  Step 4 = Business Details
  Step 5 = Infrastructure
  Step 6 = Configuration   (Base Currency)
"""

from selenium.webdriver.common.by import By
from pages.company_onboarding.Company_Onboarding.company_onboarding_page import CompanyOnboardingPage
from common.logger import log


class CompanyOnboardingUpdatePage(CompanyOnboardingPage):

    # ================================================================
    # READ helpers
    # ================================================================

    def _read_text_field(self, locator):
        """Read input value using pure JS document.querySelector."""
        try:
            if locator[0] == "css":
                val = self.driver.execute_script(
                    "return document.querySelector(arguments[0]).value", locator[1])
                return (val or "").strip()
            elif locator[0] == "xpath":
                el = self.driver.find_element(*locator)
                val = self.driver.execute_script("return arguments[0].value", el)
                return (val or "").strip()
        except Exception:
            return ""

    def _read_select_value(self, locator):
        """Read the currently displayed text from a mat-select dropdown."""
        try:
            trigger = ("xpath", f"{locator[1]}//div[contains(@class,'mat-mdc-select-trigger')]")
            el = self.driver.find_element(*trigger)
            return (el.text or "").strip()
        except Exception:
            return ""

    def read_all_step_values(self):
        """Walk through all 6 steps reading ALL field values."""
        values = {}
        try:
            values["step1"] = {"1": {
                "company_name":       self._read_text_field(self.COMPANY_NAME_INPUT),
                "company_code":       self._read_text_field(self.COMPANY_CODE_INPUT),
                "company_short_name": self._read_text_field(self.COMPANY_SHORT_NAME_INPUT),
                "contact_name":       self._read_text_field(self.CONTACT_NAME_INPUT),
                "company_background": self._read_text_field(self.COMPANY_BACKGROUND_INPUT),
                "email":              self._read_text_field(self.EMAIL_INPUT),
                "mobile_number":      self._read_text_field(self.MOBILE_NUMBER_INPUT),
                "pan":                self._read_text_field(self.PAN_INPUT),
                "gstin":              self._read_text_field(self.GSTIN_INPUT),
                "cin":                self._read_text_field(self.CIN_INPUT),
                "entity_group":       self._read_select_value(self.ENTITY_GROUP_SELECT),
                "parent_name":        self._read_select_value(self.PARENT_NAME_SELECT),
                "plan_type":          self._read_select_value(self.PLAN_TYPE_SELECT),
            }}
            log.info(f"  Read Step 1: {values['step1']}")
        except Exception as e:
            log.warning(f"Could not read Step 1: {e}")

        self._click_next()
        self.wait_seconds(1)
        try:
            values["step2"] = {"1": {
                "promoter_name":   self._read_text_field(("xpath", "(//app-dynamic-details//input[@name='Name'])[1]")),
                "promoter_remark": self._read_text_field(("xpath", "(//app-dynamic-details//textarea[@name='Remark'])[1]")),
            }}
            log.info(f"  Read Step 2 (Promoters): {values['step2']}")
        except Exception as e:
            log.warning(f"Could not read Step 2: {e}")

        self._click_next()
        self.wait_seconds(1)
        try:
            values["step3"] = {"1": {
                "address_type": self._read_select_value(self._idx(self.ADDRESS_TYPE_SELECT, 1)),
                "country":      self._read_select_value(self._idx(self.COUNTRY_SELECT, 1)),
                "state":        self._read_select_value(self._idx(self.STATE_SELECT, 1)),
                "district":     self._read_select_value(self._idx(self.DISTRICT_SELECT, 1)),
                "taluka":       self._read_select_value(self._idx(self.TALUKA_SELECT, 1)),
                "address":      self._read_text_field(("xpath", "(//app-dynamic-details//input[@name='Address'])[1]")),
                "pin_code":     self._read_text_field(("xpath", "(//app-dynamic-details//input[@name='Pin Code'])[1]")),
            }}
            log.info(f"  Read Step 3 (Address): {values['step3']}")
        except Exception as e:
            log.warning(f"Could not read Step 3 (Address): {e}")

        self._click_next()
        self.wait_seconds(1)
        try:
            values["step4"] = {"1": {
                "business_model":                self._read_text_field(self._idx(self.BUSINESS_MODEL_INPUT, 1)),
                "market_linkages":               self._read_text_field(self._idx(self.MARKET_LINKAGES_INPUT, 1)),
                "line_of_business":              self._read_text_field(self._idx(self.LINE_OF_BUSINESS_INPUT, 1)),
                "additional_business_activities": self._read_text_field(self._idx(self.ADDITIONAL_BUSINESS_INPUT, 1)),
            }}
            log.info(f"  Read Step 4 (Business): {values['step4']}")
        except Exception as e:
            log.warning(f"Could not read Step 4 (Business): {e}")

        self._click_next()
        self.wait_seconds(1)
        try:
            values["step5"] = {"1": {
                "infra_type":     self._read_select_value(self._idx(self.INFRA_TYPE_SELECT, 1)),
                "infra_location": self._read_text_field(self._idx(self.INFRA_LOCATION_INPUT, 1)),
                "ownership_type": self._read_select_value(self._idx(self.INFRA_OWNERSHIP_SELECT, 1)),
            }}
            log.info(f"  Read Step 5 (Infrastructure): {values['step5']}")
        except Exception as e:
            log.warning(f"Could not read Step 5 (Infrastructure): {e}")

        self._click_next()
        self.wait_seconds(1)
        try:
            values["step6"] = {"1": {
                "base_currency": self._read_select_value(self.BASE_CURRENCY_SELECT),
            }}
            log.info(f"  Read Step 6 (Configuration): {values['step6']}")
        except Exception as e:
            log.warning(f"Could not read Step 6 (Configuration): {e}")

        return values

    def _navigate_back_to_step1(self):
        """Click the back/previous button 5 times to reach Step 1."""
        log.info("Navigating back to Step 1...")
        back_selectors = [
            ("css", "form.step-form button[matstepperprevious]"),
            ("css", "button[matstepperprevious]"),
            ("xpath", "//button[@matstepperprevious or @matStepperPrevious]"),
        ]
        for i in range(5):
            clicked = False
            for strategy, path in back_selectors:
                try:
                    btns = self.driver.find_elements(strategy, path)
                    for btn in btns:
                        try:
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
                                btn,
                            )
                            log.info(f"  Clicked back button ({i + 1}/5)")
                            self.wait_seconds(1)
                            clicked = True
                            break
                        except Exception:
                            continue
                    if clicked:
                        break
                except Exception:
                    continue
            if not clicked:
                log.info(f"  No back button found at {i + 1}, stopping")
                break
        self.wait_seconds(1)
        log.info("Navigation back complete")

    # ================================================================
    # APPLY step updates
    # ================================================================

    def _apply_step1_updates(self, updates):
        """Step 1 = Company Details."""
        field_map = {
            "contact_name":  self.CONTACT_NAME_INPUT,
            "email":         self.EMAIL_INPUT,
            "mobile_number": self.MOBILE_NUMBER_INPUT,
            "company_code":  self.COMPANY_CODE_INPUT,
        }
        log.info(f"Applying Step 1 updates: {list(updates.keys())}")
        for key, value in updates.items():
            if key in field_map and value:
                self.type_text(field_map[key], str(value), clear_first=True)
                log.info(f"  Updated '{key}' = '{value}'")

    def _apply_step2_updates(self, updates):
        """Step 2 = Promoters."""
        for row_idx, row_data in updates.items():
            log.info(f"Applying Step 2 row {row_idx} updates: {list(row_data.keys())}")
            if row_data.get("promoter_name"):
                loc = ("xpath", f"(//app-dynamic-details//input[@name='Name'])[{row_idx}]")
                self.type_text(loc, str(row_data["promoter_name"]), clear_first=True)
            if row_data.get("promoter_remark"):
                loc = ("xpath", f"(//app-dynamic-details//textarea[@name='Remark'])[{row_idx}]")
                self.type_text(loc, str(row_data["promoter_remark"]), clear_first=True)

    def _apply_step3_updates(self, updates):
        """Step 3 = Address."""
        for row_idx, row_data in updates.items():
            log.info(f"Applying Step 3 row {row_idx} updates (Address): {list(row_data.keys())}")
            if row_data.get("address"):
                loc = ("xpath", f"(//app-dynamic-details//input[@name='Address'])[{row_idx}]")
                self.type_text(loc, str(row_data["address"]), clear_first=True)
            if row_data.get("pin_code"):
                loc = ("xpath", f"(//app-dynamic-details//input[@name='Pin Code'])[{row_idx}]")
                self.type_text(loc, str(row_data["pin_code"]), clear_first=True)

    def _apply_step4_updates(self, updates):
        """Step 4 = Business Details."""
        for row_idx, row_data in updates.items():
            log.info(f"Applying Step 4 row {row_idx} updates (Business): {list(row_data.keys())}")
            if row_data.get("business_model"):
                loc = self._idx(self.BUSINESS_MODEL_INPUT, row_idx)
                self.type_text(loc, str(row_data["business_model"]), clear_first=True)
            if row_data.get("market_linkages"):
                loc = self._idx(self.MARKET_LINKAGES_INPUT, row_idx)
                self.type_text(loc, str(row_data["market_linkages"]), clear_first=True)

    def _apply_step5_updates(self, updates):
        """Step 5 = Infrastructure."""
        for row_idx, row_data in updates.items():
            log.info(f"Applying Step 5 row {row_idx} updates (Infrastructure): {list(row_data.keys())}")
            if row_data.get("infra_location"):
                loc = self._idx(self.INFRA_LOCATION_INPUT, row_idx)
                self.type_text(loc, str(row_data["infra_location"]), clear_first=True)

    def _apply_step6_updates(self, updates):
        """Step 6 = Configuration (Base Currency)."""
        log.info(f"Applying Step 6 updates (Configuration): {list(updates.keys())}")
        base_currency = updates.get("1", updates)
        if isinstance(base_currency, dict):
            base_currency = base_currency.get("base_currency", "")
        if base_currency:
            self._select_mat_option(self.BASE_CURRENCY_SELECT, str(base_currency))
            log.info(f"  Updated base_currency = '{base_currency}'")

    # ================================================================
    # Click Edit button for a company row
    # ================================================================

    def _click_edit_button(self, company_name):
        """Click the Edit button for the matching company row."""
        edit_selectors = [
            "button[mattooltip='EDIT']",
            "button[mattooltip='Edit']",
            "div[mattooltip='EDIT'] button",
            "div[mattooltip='Edit'] button",
        ]
        row_selectors = [
            "tr.mat-mdc-row",
            "tr.mat-row",
            "table tbody tr",
        ]
        found_row = None
        for row_sel in row_selectors:
            rows = self.driver.find_elements(By.CSS_SELECTOR, row_sel)
            for row in rows:
                try:
                    cells = row.find_elements(By.CSS_SELECTOR, "td")
                    for cell in cells:
                        cell_text = (cell.text or "").strip()
                        if company_name.strip().lower() in cell_text.lower():
                            found_row = row
                            break
                    if found_row:
                        break
                except Exception:
                    continue
            if found_row:
                break

        if not found_row:
            raise Exception(f"Company row not found: {company_name}")

        for sel in edit_selectors:
            try:
                edit_btn = found_row.find_element(By.CSS_SELECTOR, sel)
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
                    edit_btn,
                )
                log.info(f"Clicked Edit ({sel}) for: {company_name}")
                self.wait_seconds(2)
                return
            except Exception:
                continue

        buttons = found_row.find_elements(By.CSS_SELECTOR, "button")
        for btn in buttons:
            try:
                if btn.is_displayed() and btn.is_enabled():
                    tooltip = btn.get_attribute("mattooltip") or btn.get_attribute("aria-label") or ""
                    icon_text = (btn.text or "").strip().lower()
                    if "edit" in tooltip.lower() or "edit" in icon_text:
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
                            btn,
                        )
                        log.info(f"Clicked Edit (fallback) for: {company_name}")
                        self.wait_seconds(2)
                        return
            except Exception:
                continue

        raise Exception(f"Edit button not found for: {company_name}")

    # ================================================================
    # Main: update_company
    # ================================================================

    def update_company(self, company_name, all_updates):
        """Open edit, read before, apply updates, submit, read after."""
        before_values = {}
        after_values = {}
        try:
            self.navigate_to_page()
            self.wait_seconds(2)
            if not self.search_company(company_name):
                return {"success": False, "error": f"Company not found: {company_name}"}
            self._click_edit_button(company_name)
            self.wait_seconds(2)

            log.info("Reading before-update values...")
            before_values = self.read_all_step_values()

            self._navigate_back_to_step1()

            apply_map = {
                1: self._apply_step1_updates, 2: self._apply_step2_updates,
                3: self._apply_step3_updates, 4: self._apply_step4_updates,
                5: self._apply_step5_updates, 6: self._apply_step6_updates,
            }
            for step_num in range(1, 7):
                step_data = all_updates.get(step_num)
                if not step_data:
                    if step_num < 6:
                        self._click_next()
                    continue
                apply_map[step_num](step_data)
                if step_num < 6:
                    self._click_next()

            self.wait_seconds(1)
            self._force_close_panels()
            self.click(('xpath', "//div[@class='popup-footer']//button[contains(.,'Update')]"))
            msg = self.get_success_message(timeout=60)
            self.wait_seconds(3)

            log.info("Re-opening edit to read after-update values...")
            self.navigate_to_page()
            self.wait_seconds(2)
            if self.search_company(company_name):
                self._click_edit_button(company_name)
                self.wait_seconds(2)
                after_values = self.read_all_step_values()
                log.info("After-update values read")
                try:
                    self.click_cancel_or_dismiss_dialog()
                except Exception:
                    pass
            else:
                log.warning("Could not re-find company for after-read")

            if msg and "Validation Failed" in str(msg):
                log.warning(f"Server validation failed: {msg}")
                return {"success": False, "error": f"Server validation failed: {msg}",
                        "before": before_values, "after": {},
                        "company_name": company_name, "message": msg}

            return {"success": True, "before": before_values, "after": after_values,
                    "company_name": company_name, "message": msg}

        except Exception as e:
            log.error(f"Company update failed: {company_name} - {e}")
            try:
                self.click_cancel_or_dismiss_dialog()
            except Exception:
                pass
            return {"success": False, "error": str(e), "company_name": company_name,
                    "before": before_values, "after": after_values}
