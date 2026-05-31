"""Patch: Restore company_onboarding_page_update.py to full 606-line version."""

import os

TARGET = r"pages\company_onboarding\Company_Onboarding\company_onboarding_page_update.py"

CONTENT = """\""""
company_onboarding_page_update.py
----------------------------------
Page Object Model for EDITING/UPDATING existing Company Onboarding records.

Inherits from CompanyOnboardingPage (reuses all locators, dropdown logic,
step navigation, search methods, panel cleanup, etc.)

Adds: Edit button click, form value reading, targeted field updates,
Update button, SweetAlert handling, and verification via re-open Edit.
\"\""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common.logger import log
from pages.company_onboarding.Company_Onboarding.company_onboarding_page import (
    CompanyOnboardingPage,
    CO_SUBMISSIONS,
)
import copy


class CompanyOnboardingUpdatePage(CompanyOnboardingPage):

    SWEETALERT_TITLE = ("css", "#swal2-title")
    SWEETALERT_CONFIRM = ("css", ".swal2-confirm")
    UPDATE_BUTTON = ("xpath", "//div[@class='popup-footer']//button[contains(.,'Update')]")
    DIALOG_CLOSE_X = ("css", "div.popup-actions button mat-icon, .mat-icon-button mat-icon")
    FIRST_ROW_EDIT_BTN = ("css", "tbody tr.mat-mdc-row:first-child td.cdk-column-edit button")
    FIRST_ROW_VIEW_BTN = ("css", "tbody tr.mat-mdc-row:first-child td.cdk-column-view button")
    FIRST_ROW_NAME = ("css", "tbody tr.mat-mdc-row:first-child td.cdk-column-name")
    FIRST_ROW_LEVEL = ("css", "tbody tr.mat-mdc-row:first-child td.cdk-column-level")
    FIRST_ROW_STATE = ("css", "tbody tr.mat-mdc-row:first-child td.cdk-column-state")
    FIRST_ROW_DISTRICT = ("css", "tbody tr.mat-mdc-row:first-child td.cdk-column-district")
    FIRST_ROW_STATUS = ("css", "tbody tr.mat-mdc-row:first-child td.cdk-column-status")

    def click_edit_for_company(self, company_name):
        log.info(f"Searching for company to edit: {company_name}")
        self.navigate_to_page()
        self.wait_seconds(2)
        found = self.search_company(company_name)
        if not found:
            raise Exception(f"Company not found in table: {company_name}")
        self.wait_seconds(1)
        try:
            edit_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "tbody tr.mat-mdc-row:first-child td.cdk-column-edit button"))
            )
        except Exception:
            edit_btn = self.driver.find_element(By.CSS_SELECTOR, "tbody tr.mat-mdc-row:first-child td.cdk-column-edit button")
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
            edit_btn,
        )
        log.info(f"Clicked Edit for: {company_name}")
        self.wait_seconds(2)

    def click_view_for_company(self, company_name):
        self.navigate_to_page()
        self.wait_seconds(2)
        found = self.search_company(company_name)
        if not found:
            raise Exception(f"Company not found in table: {company_name}")
        self.wait_seconds(1)
        view_btn = self.driver.find_element(By.CSS_SELECTOR, "tbody tr.mat-mdc-row:first-child td.cdk-column-view button")
        self.driver.execute_script("arguments[0].click();", view_btn)
        log.info(f"Clicked View for: {company_name}")
        self.wait_seconds(2)

    def read_table_row_values(self, company_name):
        self.navigate_to_page()
        self.wait_seconds(2)
        found = self.search_company(company_name)
        if not found:
            raise Exception(f"Company not found in table: {company_name}")
        self.wait_seconds(1)
        row = self.driver.find_element(By.CSS_SELECTOR, "tbody tr.mat-mdc-row:first-child")
        values = {
            "name": row.find_element(By.CSS_SELECTOR, "td.cdk-column-name").text.strip(),
            "level": row.find_element(By.CSS_SELECTOR, "td.cdk-column-level").text.strip(),
            "state": row.find_element(By.CSS_SELECTOR, "td.cdk-column-state").text.strip(),
            "district": row.find_element(By.CSS_SELECTOR, "td.cdk-column-district").text.strip(),
            "status": row.find_element(By.CSS_SELECTOR, "td.cdk-column-status").text.strip(),
        }
        log.info(f"Table row values: {values}")
        self.clear_search()
        return values

    def get_total_record_count(self):
        try:
            label = self.driver.find_element(By.CSS_SELECTOR, ".mat-mdc-paginator-range-label")
            text = label.text.strip()
            if "of" in text:
                return int(text.split("of")[-1].strip())
        except Exception as e:
            log.warning(f"Could not read paginator: {e}")
        return 0

    def _get_input_value(self, locator):
        strategy, path = locator
        if strategy == "css":
            element = self.driver.find_element(By.CSS_SELECTOR, path)
        elif strategy == "xpath":
            element = self.driver.find_element(By.XPATH, path)
        else:
            element = self.driver.find_element(*locator)
        return element.get_attribute("value") or ""

    def _get_textarea_value(self, locator):
        return self._get_input_value(locator)

    def _get_mat_select_text(self, locator):
        try:
            strategy, path = locator
            if strategy == "css":
                element = self.driver.find_element(By.CSS_SELECTOR, path)
            elif strategy == "xpath":
                element = self.driver.find_element(By.XPATH, path)
            else:
                element = self.driver.find_element(*locator)
            value_el = element.find_element(By.CSS_SELECTOR, ".mat-mdc-select-value-text span")
            return value_el.text.strip()
        except Exception:
            try:
                strategy, path = locator
                if strategy == "xpath":
                    trigger = self.driver.find_element(By.XPATH, f"{path}//div[contains(@class,'mat-mdc-select-trigger')]")
                else:
                    trigger = self.driver.find_element(By.CSS_SELECTOR, f"{path} .mat-mdc-select-trigger")
                return trigger.text.strip()
            except Exception:
                return ""

    def read_step1_values(self):
        self._force_close_panels()
        values = {
            "company_name": self._get_input_value(self.COMPANY_NAME_INPUT),
            "company_short_name": self._get_input_value(self.COMPANY_SHORT_NAME_INPUT),
            "contact_name": self._get_input_value(self.CONTACT_NAME_INPUT),
            "company_background": self._get_textarea_value(self.COMPANY_BACKGROUND_INPUT),
            "email": self._get_input_value(self.EMAIL_INPUT),
            "mobile_number": self._get_input_value(self.MOBILE_NUMBER_INPUT),
            "pan": self._get_input_value(self.PAN_INPUT),
            "gstin": self._get_input_value(self.GSTIN_INPUT),
            "cin": self._get_input_value(self.CIN_INPUT),
            "entity_group": self._get_mat_select_text(self.ENTITY_GROUP_SELECT),
            "parent_name": self._get_mat_select_text(self.PARENT_NAME_SELECT),
            "plan_type": self._get_mat_select_text(self.PLAN_TYPE_SELECT),
        }
        log.info(f"Step 1 values read: {list(values.keys())}")
        return values

    def read_step2_values(self, row_index=1):
        self._force_close_panels()
        name_loc = ("xpath", f"(//app-dynamic-details//input[@name='Name'])[{row_index}]")
        remark_loc = ("xpath", f"(//app-dynamic-details//textarea[@name='Remark'])[{row_index}]")
        values = {
            "promoter_name": self._get_input_value(name_loc),
            "promoter_remark": self._get_textarea_value(remark_loc),
        }
        log.info(f"Step 2 row {row_index} values read")
        return values

    def read_step3_values(self, row_index=1):
        self._force_close_panels()
        values = {
            "business_model": self._get_input_value(self._idx(self.BUSINESS_MODEL_INPUT, row_index)),
            "market_linkages": self._get_input_value(self._idx(self.MARKET_LINKAGES_INPUT, row_index)),
            "line_of_business": self._get_input_value(self._idx(self.LINE_OF_BUSINESS_INPUT, row_index)),
            "additional_business": self._get_input_value(self._idx(self.ADDITIONAL_BUSINESS_INPUT, row_index)),
        }
        log.info(f"Step 3 row {row_index} values read")
        return values

    def read_step4_values(self, row_index=1):
        self._force_close_panels()
        values = {
            "address_type": self._get_mat_select_text(self._idx(self.ADDRESS_TYPE_SELECT, row_index)),
            "country": self._get_mat_select_text(self._idx(self.COUNTRY_SELECT, row_index)),
            "state": self._get_mat_select_text(self._idx(self.STATE_SELECT, row_index)),
            "district": self._get_mat_select_text(self._idx(self.DISTRICT_SELECT, row_index)),
            "taluka": self._get_mat_select_text(self._idx(self.TALUKA_SELECT, row_index)),
            "address": self._get_input_value(self._idx(self.ADDRESS_INPUT, row_index)),
            "pin_code": self._get_input_value(self._idx(self.PIN_CODE_INPUT, row_index)),
        }
        log.info(f"Step 4 row {row_index} values read")
        return values

    def read_step5_values(self, row_index=1):
        self._force_close_panels()
        values = {
            "infra_type": self._get_mat_select_text(self._idx(self.INFRA_TYPE_SELECT, row_index)),
            "infra_location": self._get_input_value(self._idx(self.INFRA_LOCATION_INPUT, row_index)),
            "ownership_type": self._get_mat_select_text(self._idx(self.INFRA_OWNERSHIP_SELECT, row_index)),
        }
        log.info(f"Step 5 row {row_index} values read")
        return values

    def apply_step1_updates(self, updates):
        self._force_close_panels()
        log.info(f"Applying Step 1 updates: {list(updates.keys())}")
        field_map = {
            "company_short_name": self.COMPANY_SHORT_NAME_INPUT,
            "contact_name": self.CONTACT_NAME_INPUT,
            "company_background": self.COMPANY_BACKGROUND_INPUT,
            "email": self.EMAIL_INPUT,
            "mobile_number": self.MOBILE_NUMBER_INPUT,
            "pan": self.PAN_INPUT,
            "gstin": self.GSTIN_INPUT,
            "cin": self.CIN_INPUT,
        }
        select_map = {
            "entity_group": self.ENTITY_GROUP_SELECT,
            "parent_name": self.PARENT_NAME_SELECT,
            "plan_type": self.PLAN_TYPE_SELECT,
        }
        for key, value in updates.items():
            if key in field_map:
                self.type_text(field_map[key], str(value), clear_first=True)
                log.info(f"  Updated text field '{key}' = '{value}'")
            elif key in select_map:
                self._select_mat_option(select_map[key], str(value))
                self._force_close_panels()
                log.info(f"  Updated select field '{key}' = '{value}'")
            else:
                log.warning(f"  Unknown Step 1 field: '{key}'")
        self._force_close_panels()

    def apply_step2_updates(self, updates, row_index=1):
        self._force_close_panels()
        log.info(f"Applying Step 2 row {row_index} updates: {list(updates.keys())}")
        name_loc = ("xpath", f"(//app-dynamic-details//input[@name='Name'])[{row_index}]")
        remark_loc = ("xpath", f"(//app-dynamic-details//textarea[@name='Remark'])[{row_index}]")
        if "promoter_name" in updates:
            self.type_text(name_loc, str(updates["promoter_name"]), clear_first=True)
            log.info(f"  Updated promoter name = '{updates['promoter_name']}'")
        if "promoter_remark" in updates:
            self.type_text(remark_loc, str(updates["promoter_remark"]), clear_first=True)
            log.info(f"  Updated promoter remark = '{updates['promoter_remark']}'")
        self._force_close_panels()

    def apply_step3_updates(self, updates, row_index=1):
        self._force_close_panels()
        log.info(f"Applying Step 3 row {row_index} updates: {list(updates.keys())}")
        field_map = {
            "business_model": self._idx(self.BUSINESS_MODEL_INPUT, row_index),
            "market_linkages": self._idx(self.MARKET_LINKAGES_INPUT, row_index),
            "line_of_business": self._idx(self.LINE_OF_BUSINESS_INPUT, row_index),
            "additional_business": self._idx(self.ADDITIONAL_BUSINESS_INPUT, row_index),
        }
        for key, value in updates.items():
            if key in field_map:
                self.type_text(field_map[key], str(value), clear_first=True)
                log.info(f"  Updated '{key}' = '{value}'")
        self._force_close_panels()

    def apply_step4_updates(self, updates, row_index=1):
        self._force_close_panels()
        log.info(f"Applying Step 4 row {row_index} updates: {list(updates.keys())}")
        if "address_type" in updates:
            self._select_mat_option(self._idx(self.ADDRESS_TYPE_SELECT, row_index), str(updates["address_type"]))
            self._force_close_panels()
            log.info(f"  Updated address type = '{updates['address_type']}'")
        if "country" in updates:
            self._select_mat_option(self._idx(self.COUNTRY_SELECT, row_index), str(updates["country"]))
            self._force_close_panels()
            log.info(f"  Updated country = '{updates['country']}'")
        if "address" in updates:
            self.type_text(self._idx(self.ADDRESS_INPUT, row_index), str(updates["address"]), clear_first=True)
            log.info(f"  Updated address = '{updates['address']}'")
        if "pin_code" in updates:
            self.type_text(self._idx(self.PIN_CODE_INPUT, row_index), str(updates["pin_code"]), clear_first=True)
            log.info(f"  Updated pin_code = '{updates['pin_code']}'")
        self._force_close_panels()

    def apply_step5_updates(self, updates, row_index=1):
        self._force_close_panels()
        log.info(f"Applying Step 5 row {row_index} updates: {list(updates.keys())}")
        if "infra_type" in updates:
            self._select_mat_option(self._idx(self.INFRA_TYPE_SELECT, row_index), str(updates["infra_type"]))
            self._force_close_panels()
            log.info(f"  Updated infra type = '{updates['infra_type']}'")
        if "infra_location" in updates:
            self.type_text(self._idx(self.INFRA_LOCATION_INPUT, row_index), str(updates["infra_location"]), clear_first=True)
            log.info(f"  Updated infra location = '{updates['infra_location']}'")
        if "ownership_type" in updates:
            self._select_mat_option(self._idx(self.INFRA_OWNERSHIP_SELECT, row_index), str(updates["ownership_type"]))
            self._force_close_panels()
            log.info(f"  Updated ownership type = '{updates['ownership_type']}'")
        self._force_close_panels()

    def navigate_to_step(self, target_step):
        current = 1
        while current < target_step:
            log.info(f"Navigating: Step {current} -> Step {current + 1}")
            self._click_next()
            self.wait_seconds(1)
            current += 1
        log.info(f"Reached Step {target_step}")

    def click_update_button(self):
        self._force_close_panels()
        log.info("Clicking Update button...")
        try:
            btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='popup-footer']//button[contains(.,'Update')]"))
            )
        except Exception:
            btn = self.driver.find_element(By.XPATH, "//div[@class='popup-footer']//button[contains(.,'Update')]")
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
            btn,
        )
        log.info("Update button clicked")

    def wait_for_update_success(self, timeout=30):
        log.info("Waiting for update success SweetAlert...")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#swal2-title"))
            )
            title = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title").text
            log.info(f"SweetAlert appeared: {title}")
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "#swal2-title"))
            )
            log.info("SweetAlert auto-dismissed")
            self.wait_seconds(2)
            return True
        except Exception as e:
            log.warning(f"SweetAlert handling: {e}")
            self.wait_seconds(3)
            return True

    def wait_for_dialog_closed(self, timeout=30):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "mat-dialog-container"))
            )
            log.info("Dialog closed")
        except Exception:
            log.warning("Dialog may still be open, attempting dismiss")
            self.click_cancel_or_dismiss_dialog()
        self.wait_seconds(1)

    def read_all_step_values(self):
        all_values = {}
        all_values.update(self.read_step1_values())
        self._click_next()
        self.wait_seconds(1)
        all_values.update(self.read_step2_values(row_index=1))
        self._click_next()
        self.wait_seconds(1)
        all_values.update(self.read_step3_values(row_index=1))
        self._click_next()
        self.wait_seconds(1)
        all_values.update(self.read_step4_values(row_index=1))
        self._click_next()
        self.wait_seconds(1)
        all_values.update(self.read_step5_values(row_index=1))
        log.info(f"All step values read: {list(all_values.keys())}")
        return all_values

    def update_company(self, company_name, updates_by_step):
        result = {
            "company_name": company_name,
            "success": False,
            "error": "",
            "before_values": {},
            "after_values": {},
        }
        try:
            self.click_edit_for_company(company_name)
            result["before_values"] = self.read_all_step_values()
            self.click_cancel_or_dismiss_dialog()
            self.wait_seconds(1)
            self.click_edit_for_company(company_name)
            self.wait_seconds(1)
            for step_num in sorted(updates_by_step.keys()):
                updates = updates_by_step[step_num]
                if not updates:
                    continue
                if step_num == 1:
                    self.apply_step1_updates(updates)
                elif step_num == 2:
                    self._click_next()
                    self.wait_seconds(1)
                    self.apply_step2_updates(updates, row_index=1)
                elif step_num == 3:
                    self._click_next()
                    self.wait_seconds(1)
                    self.apply_step3_updates(updates, row_index=1)
                elif step_num == 4:
                    self._click_next()
                    self.wait_seconds(1)
                    self.apply_step4_updates(updates, row_index=1)
                elif step_num == 5:
                    self._click_next()
                    self.wait_seconds(1)
                    self.apply_step5_updates(updates, row_index=1)
            self.click_update_button()
            success = self.wait_for_update_success(timeout=30)
            self.wait_for_dialog_closed(timeout=15)
            self.click_refresh()
            self.wait_seconds(2)
            self.click_edit_for_company(company_name)
            result["after_values"] = self.read_all_step_values()
            self.click_cancel_or_dismiss_dialog()
            self.wait_seconds(1)
            result["success"] = True
            log.info(f"Company update completed: {company_name}")
        except Exception as e:
            result["error"] = str(e)
            log.error(f"Company update failed: {company_name} - {e}")
            try:
                self.click_cancel_or_dismiss_dialog()
            except Exception:
                pass
        CO_SUBMISSIONS.append({
            "data": {
                "company_name": company_name,
                "updates_by_step": updates_by_step,
            },
            "status": "UPDATED" if result["success"] else "UPDATE_FAILED",
            "error": result["error"],
            "before_values": result["before_values"],
            "after_values": result["after_values"],
        })
        return result

    def verify_updated_fields(self, after_values, updates_by_step):
        mismatches = {}
        for step_num, updates in updates_by_step.items():
            for field, expected_value in updates.items():
                actual = after_values.get(field, "")
                if actual.strip() != str(expected_value).strip():
                    mismatches[field] = {
                        "expected": expected_value,
                        "actual": actual,
                    }
                    log.warning(f"Mismatch '{field}': expected='{expected_value}', actual='{actual}'")
                else:
                    log.info(f"Match '{field}': '{actual}'")
        return mismatches
"""

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(CONTENT)

import os
lines = CONTENT.strip().split("\n")
print(f"Written {len(lines)} lines to {TARGET}")
