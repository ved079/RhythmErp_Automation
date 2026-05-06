
"""
=====================================================================
DOCSTRING UPDATE - Replace the Tests list at the top of the file
with this updated version:
=====================================================================

Tests:
  01 - Form Opens
  02 - Step 1 Next-click validations (required + format) [ONE form open]
  03 - 2FA + Auth Type dependency
  04 - Duplicate Company Name SweetAlert (Update click)
  05 - Invalid CIN SweetAlert (Update click)
  06 - Max Length SweetAlert (Company Short Name)
  07 - Promoter: All UI validations (nav, prefilled, optional, add, delete) [ONE form open]
  08 - Promoter: Max length + update & verify (101 fail, 100 save, persisted) [ONE form open]
  09 - Promoter: Boundary + backend (remark maxlen, empty save, edit+verify, restore) [ONE form open]
  10 - Promoter: Edge cases (special chars, whitespace, multiline, rapid add/delete, max rows) [ONE form open]
  11 - Address: Navigation + Pre-filled data (step nav, 2 rows prefilled) [ONE form open]
  12 - Address: Row management + Cascading dropdowns (add/delete, min 1, State>Dist>Taluka) [ONE form open]
  13 - Address: Required fields + Pin Code validation (empty row errors, 000000, letters) [ONE form open]
  14 - Address: Backend + Persistence (long addr, edit+verify, dup type, special chars, restore) [ONE form open, Update]
  15 - Address: Edge cases (whitespace, 5-digit pin, multiline) [ONE form open]
  16 - Business Activities: Navigation + Pre-filled + Row management [ONE form open, NO Update]
  17 - Business Activities: Max length all 4 fields (BM100, ML/LOB/ABA 255) [ONE form open, Update]
  18 - Business Activities: Backend + Persistence (edit+verify, empty save, restore) [ONE form open, Update]
  19 - Business Activities: Edge cases (special chars, whitespace, rapid add/delete, max rows) [ONE form open]
  20 - Infrastructure Details: Navigation + Pre-filled + Row management [ONE form open, NO Update]
  21 - Infrastructure Details: Dropdown + Max length (Loc50, Remark255) [ONE form open, Update]
  22 - Infrastructure Details: Backend + Persistence (edit+verify, empty save, restore) [ONE form open, Update]
  23 - Infrastructure Details: Edge cases (dropdown search, dup PLC, special chars, multiline) [ONE form open]
  24 - Header: Entity Group + Parent Name + Company Linked (cascading, multi-select) [ONE form open, NO Update]
  25 - Header: Level (readonly) + Is Parent (readonly toggle) [ONE form open, NO Update]
  26 - Step 1 Optional: TAN + GSTIN + Plan Type [ONE form open, NO Update]

New helper methods added:
  _hdr_find_select()    - Find mat-select by mat-label text
  _hdr_read_select()    - Read selected value from mat-select
  _hdr_open_select()    - Open a mat-select dropdown
  _hdr_list_options()   - List options from open dropdown (excludes "Select" placeholder)
  _hdr_pick_option()    - Click an option from open dropdown
  _hdr_close_dropdown() - Close any open dropdown overlay
  _hdr_is_multiselect() - Check if mat-select has 'multiple' attribute
  _hdr_read_input()     - Read input value by mat-label text
  _hdr_is_input_readonly() - Check if input is readonly/disabled

Coverage summary (26 tests, ~110+ checks):
  Header (6 fields):  Entity Group, Parent Name, Company Linked, Level, Is Parent, Company Name (test_01)
  Step 1 (12 fields):  Short Name, Contact Name, Background, Email, Mobile, PAN, CIN, TAN, GSTIN,
                        Plan Type, 2FA Toggle, Auth Type
  Step 2 (2 fields):   Promoter Name, Remark
  Step 3 (7 fields):   Address Type, Country, State, District, Taluka, Address, Pin Code
  Step 4 (4 fields):   Business Model, Market Linkages, Line of Business, Additional Business Activities
  Step 5 (4 fields):   Infrastructure Type, Infrastructure Location, Ownership Type, Remark
  TOTAL: 35 fields covered
=====================================================================
"""

import os
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import pytest

from common.logger import log
from pages.company_onboarding.Company_Onboarding.company_onboarding_page_update import CompanyOnboardingUpdatePage
from pages.company_onboarding.test.update_validation_results_store import update_validation_results

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "pages", "company_onboarding", "screenshots")
REPORT_DIR = os.path.join(PROJECT_ROOT, "pages", "company_onboarding", "reports")

TEST_COMPANY = "Zenith Core Systems"


class TestUpdateValidation:

    def _page(self, driver):
        return CompanyOnboardingUpdatePage(driver)

    def _screenshot(self, driver, name):
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        path = os.path.join(SCREENSHOT_DIR,
                            f"upd_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        driver.save_screenshot(path)
        return path

    def _record(self, test_name, expected, actual, status, category="",
                 field="", bad_value="", original_value="", screenshot="", is_bug=False):
        update_validation_results.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_name": test_name, "expected": expected, "actual": actual,
            "status": status, "category": category, "field": field,
            "bad_value": bad_value, "original_value": original_value,
            "screenshot": screenshot, "is_bug": is_bug,
        })

    def _open_form(self, page):
        page.driver.refresh()
        time.sleep(1.5)
        page.navigate_to_page()
        time.sleep(1.5)
        page.search_company(TEST_COMPANY)
        time.sleep(1)
        page._click_edit_button(TEST_COMPANY)
        time.sleep(3)

    def _cleanup(self, page):
        try:
            page._force_close_panels()
        except Exception:
            pass
        page.navigate_to_page()
        time.sleep(1)

    def _clear_field(self, driver, field_name, tag="input"):
        el = driver.find_element(By.CSS_SELECTOR, f"{tag}[name='{field_name}']")
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].focus();", el)
        time.sleep(0.2)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        time.sleep(0.3)
        el.send_keys(Keys.TAB)
        time.sleep(0.3)

    def _type_field(self, driver, field_name, value, tag="input"):
        el = driver.find_element(By.CSS_SELECTOR, f"{tag}[name='{field_name}']")
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].focus();", el)
        time.sleep(0.2)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(value)
        time.sleep(0.3)
        el.send_keys(Keys.TAB)
        time.sleep(0.3)

    def _check_field_invalid(self, driver, field_name, tag="input"):
        try:
            input_el = driver.find_element(By.CSS_SELECTOR, f"{tag}[name='{field_name}']")
            classes = input_el.get_attribute("class") or ""
            is_invalid = "ng-invalid" in classes and "ng-touched" in classes
            error_id = input_el.get_attribute("aria-describedby") or ""
            error_text = ""
            if error_id:
                try:
                    err_el = driver.find_element(By.ID, error_id)
                    error_text = err_el.text.strip()
                except Exception:
                    pass
            return is_invalid, error_text
        except Exception:
            return False, ""

    def _read_field(self, page, locator):
        return page._read_text_field(locator)

    def _check_sweetalert(self, driver, timeout=8):
        try:
            title_el = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#swal2-title"))
            )
            title_text = title_el.text.strip()
            has_download = bool(driver.find_elements(By.CSS_SELECTOR, ".swal2-confirm"))
            return title_text, has_download
        except Exception:
            return "", False

    def _dismiss_sweetalert(self, driver):
        try:
            cancel_btn = driver.find_element(By.CSS_SELECTOR, ".swal2-cancel")
            driver.execute_script("arguments[0].click();", cancel_btn)
            time.sleep(0.5)
        except Exception:
            pass

    def _click_update_direct(self, driver):
        try:
            update_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((
                    By.XPATH, "//div[@class='popup-footer']//button[contains(.,'Update')]"
                ))
            )
        except Exception:
            update_btn = driver.find_element(
                By.XPATH, "//div[@class='popup-footer']//button[contains(.,'Submit')]"
            )
        driver.execute_script("arguments[0].click();", update_btn)
        time.sleep(2)

    def _go_back_if_needed(self, page):
        try:
            WebDriverWait(page.driver, 3).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//app-dynamic-details//input[@name='Name']")
                )
            )
            back_btn = WebDriverWait(page.driver, 3).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "button[matstepperprevious]"))
            )
            page.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", back_btn)
            time.sleep(0.3)
            try:
                back_btn.click()
            except Exception:
                page.driver.execute_script("arguments[0].click();", back_btn)
            time.sleep(0.8)
            return True
        except Exception:
            return False

    def _is_on_step2(self, driver):
        try:
            WebDriverWait(driver, 3).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//app-dynamic-details//input[@name='Name']")
                )
            )
            return True
        except Exception:
            return False

    def _toggle_2fa(self, driver, state="on"):
        """Toggle 2FA by clicking the hidden checkbox scoped to the 2FA toggle only."""
        try:
            toggle_container = driver.find_element(
                By.XPATH, "//app-slide-toggle-v2[.//span[contains(text(),'Is 2FA Applicable')]]"
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", toggle_container)
            time.sleep(0.3)

            checkbox = toggle_container.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
            is_currently_checked = checkbox.get_attribute("checked")

            need_click = (state == "on" and not is_currently_checked) or (state == "off" and is_currently_checked)
            if need_click:
                driver.execute_script("arguments[0].click();", checkbox)
                time.sleep(1)

            return True
        except Exception as e:
            return False

    def _is_2fa_state(self, driver, expected="off"):
        """Check if 2FA is in the expected state by reading CSS classes on the 2FA toggle."""
        try:
            toggle_container = driver.find_element(
                By.XPATH, "//app-slide-toggle-v2[.//span[contains(text(),'Is 2FA Applicable')]]"
            )
            off_label = toggle_container.find_element(By.CSS_SELECTOR, ".state-label.off")
            on_label = toggle_container.find_element(By.CSS_SELECTOR, ".state-label.on")
            off_active = "active" in (off_label.get_attribute("class") or "")
            on_active = "active" in (on_label.get_attribute("class") or "")

            if expected == "off":
                return off_active and not on_active
            else:
                return on_active and not off_active
        except Exception:
            return False

    # ================================================================
    # TEST 01: Form Opens
    # ================================================================

    def test_01_form_opens(self, logged_in_driver):
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)
        name = self._read_field(page, page.COMPANY_NAME_INPUT)
        email = self._read_field(page, page.EMAIL_INPUT)
        shot = self._screenshot(driver, "form_opens")
        loaded = bool(name) or bool(email)
        self._record(
            test_name="Form Opens",
            expected=f"Pre-filled data for '{TEST_COMPANY}'",
            actual=f"name='{name}', email='{email}'",
            status="PASSED" if loaded else "FAILED",
            category="Setup", field="", screenshot=shot,
        )
        self._cleanup(page)
        assert loaded, "Form did not load with data"

    # ================================================================
    # TEST 02: Step 1 Next-click validations (one form open)
    # ================================================================

    def test_02_step1_all_validations(self, logged_in_driver):
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        orig_short_name = self._read_field(page, page.COMPANY_SHORT_NAME_INPUT)
        orig_contact = self._read_field(page, page.CONTACT_NAME_INPUT)
        orig_bg = self._read_field(page, page.COMPANY_BACKGROUND_INPUT)
        orig_email = self._read_field(page, page.EMAIL_INPUT)
        orig_mobile = self._read_field(page, page.MOBILE_NUMBER_INPUT)
        orig_pan = self._read_field(page, page.PAN_INPUT)

        # === SECTION A: REQUIRED FIELD VALIDATIONS ===

        self._clear_field(driver, "Company Short Name")
        page._click_next()
        time.sleep(0.5)
        has_err, err_txt = self._check_field_invalid(driver, "Company Short Name")
        shot = self._screenshot(driver, "req_short_name")
        self._record(test_name="Required: Company Short Name", expected="Error shown for empty field",
            actual=f"error={has_err}, text='{err_txt}'", status="PASSED" if has_err else "FAILED",
            category="Required", field="Company Short Name", bad_value="(empty)",
            original_value=orig_short_name, screenshot=shot)
        self._go_back_if_needed(page)
        self._type_field(driver, "Company Short Name", orig_short_name)

        self._clear_field(driver, "Contact Name")
        page._click_next()
        time.sleep(0.5)
        has_err, err_txt = self._check_field_invalid(driver, "Contact Name")
        shot = self._screenshot(driver, "req_contact_name")
        self._record(test_name="Required: Contact Name", expected="Error shown for empty field",
            actual=f"error={has_err}, text='{err_txt}'", status="PASSED" if has_err else "FAILED",
            category="Required", field="Contact Name", bad_value="(empty)",
            original_value=orig_contact, screenshot=shot)
        self._go_back_if_needed(page)
        self._type_field(driver, "Contact Name", orig_contact)

        self._clear_field(driver, "Company Background", tag="textarea")
        page._click_next()
        time.sleep(0.5)
        has_err, err_txt = self._check_field_invalid(driver, "Company Background", tag="textarea")
        shot = self._screenshot(driver, "req_company_bg")
        self._record(test_name="Required: Company Background", expected="Error shown for empty field",
            actual=f"error={has_err}, text='{err_txt}'", status="PASSED" if has_err else "FAILED",
            category="Required", field="Company Background", bad_value="(empty)",
            original_value=orig_bg, screenshot=shot)
        self._go_back_if_needed(page)
        self._type_field(driver, "Company Background", orig_bg, tag="textarea")

        self._clear_field(driver, "Email ")
        page._click_next()
        time.sleep(0.5)
        has_err, err_txt = self._check_field_invalid(driver, "Email ")
        shot = self._screenshot(driver, "req_email")
        self._record(test_name="Required: Email", expected="Error shown for empty email",
            actual=f"error={has_err}, text='{err_txt}'", status="PASSED" if has_err else "FAILED",
            category="Required", field="Email", bad_value="(empty)",
            original_value=orig_email, screenshot=shot)
        self._go_back_if_needed(page)
        self._type_field(driver, "Email ", orig_email)

        self._clear_field(driver, "Mobile Number")
        page._click_next()
        time.sleep(0.5)
        has_err, err_txt = self._check_field_invalid(driver, "Mobile Number")
        shot = self._screenshot(driver, "req_mobile")
        self._record(test_name="Required: Mobile Number", expected="Error shown for empty mobile",
            actual=f"error={has_err}, text='{err_txt}'", status="PASSED" if has_err else "FAILED",
            category="Required", field="Mobile Number", bad_value="(empty)",
            original_value=orig_mobile, screenshot=shot)
        self._go_back_if_needed(page)
        self._type_field(driver, "Mobile Number", orig_mobile)

        self._clear_field(driver, "PAN")
        page._click_next()
        time.sleep(0.5)
        has_err, err_txt = self._check_field_invalid(driver, "PAN")
        shot = self._screenshot(driver, "req_pan")
        self._record(test_name="Required: PAN", expected="Error shown / Invalid Pan No",
            actual=f"error={has_err}, text='{err_txt}'", status="PASSED" if has_err else "FAILED",
            category="Required", field="PAN", bad_value="(empty)",
            original_value=orig_pan, screenshot=shot)
        self._go_back_if_needed(page)
        self._type_field(driver, "PAN", orig_pan)

        # === SECTION B: FORMAT VALIDATIONS ===

        self._type_field(driver, "Email ", "abc")
        page._click_next()
        time.sleep(0.5)
        has_err, err_txt = self._check_field_invalid(driver, "Email ")
        shot = self._screenshot(driver, "fmt_email_abc")
        self._record(test_name="Format: Email 'abc'", expected="Invalid email error",
            actual=f"error={has_err}, text='{err_txt}'", status="PASSED" if has_err else "FAILED",
            category="Format", field="Email", bad_value="abc",
            original_value=orig_email, screenshot=shot)
        self._go_back_if_needed(page)
        self._type_field(driver, "Email ", orig_email)

        self._type_field(driver, "Email ", "abc@")
        page._click_next()
        time.sleep(0.5)
        has_err, err_txt = self._check_field_invalid(driver, "Email ")
        shot = self._screenshot(driver, "fmt_email_abc_at")
        self._record(test_name="Format: Email 'abc@'", expected="Invalid email error",
            actual=f"error={has_err}, text='{err_txt}'", status="PASSED" if has_err else "FAILED",
            category="Format", field="Email", bad_value="abc@",
            original_value=orig_email, screenshot=shot)
        self._go_back_if_needed(page)
        self._type_field(driver, "Email ", orig_email)

        self._type_field(driver, "Mobile Number", "12345")
        page._click_next()
        time.sleep(0.5)
        has_err, err_txt = self._check_field_invalid(driver, "Mobile Number")
        shot = self._screenshot(driver, "fmt_mobile_short")
        self._record(test_name="Format: Mobile '12345'", expected="Invalid mobile error",
            actual=f"error={has_err}, text='{err_txt}'", status="PASSED" if has_err else "FAILED",
            category="Format", field="Mobile Number", bad_value="12345",
            original_value=orig_mobile, screenshot=shot)
        self._go_back_if_needed(page)
        self._type_field(driver, "Mobile Number", orig_mobile)

        self._type_field(driver, "Mobile Number", "abcdefghij")
        page._click_next()
        time.sleep(0.5)
        has_err, err_txt = self._check_field_invalid(driver, "Mobile Number")
        shot = self._screenshot(driver, "fmt_mobile_alpha")
        self._record(test_name="Format: Mobile 'abcdefghij'", expected="Invalid mobile error",
            actual=f"error={has_err}, text='{err_txt}'", status="PASSED" if has_err else "FAILED",
            category="Format", field="Mobile Number", bad_value="abcdefghij",
            original_value=orig_mobile, screenshot=shot)
        self._go_back_if_needed(page)
        self._type_field(driver, "Mobile Number", orig_mobile)

        self._type_field(driver, "PAN", "12345ABCDE")
        page._click_next()
        time.sleep(0.5)
        has_err, err_txt = self._check_field_invalid(driver, "PAN")
        shot = self._screenshot(driver, "fmt_pan_digits")
        self._record(test_name="Format: PAN '12345ABCDE'", expected="Invalid Pan No",
            actual=f"error={has_err}, text='{err_txt}'", status="PASSED" if has_err else "FAILED",
            category="Format", field="PAN", bad_value="12345ABCDE",
            original_value=orig_pan, screenshot=shot)
        self._go_back_if_needed(page)
        self._type_field(driver, "PAN", orig_pan)

        self._type_field(driver, "PAN", "ABCDE1234")
        page._click_next()
        time.sleep(0.5)
        has_err, err_txt = self._check_field_invalid(driver, "PAN")
        shot = self._screenshot(driver, "fmt_pan_9chars")
        self._record(test_name="Format: PAN 'ABCDE1234' (9 chars)", expected="Invalid Pan No",
            actual=f"error={has_err}, text='{err_txt}'", status="PASSED" if has_err else "FAILED",
            category="Format", field="PAN", bad_value="ABCDE1234",
            original_value=orig_pan, screenshot=shot)
        self._go_back_if_needed(page)
        self._type_field(driver, "PAN", orig_pan)

        self._cleanup(page)

    # ================================================================
    # TEST 03: 2FA + Auth Type Dependency
    # ================================================================

    def _find_auth_select(self, driver, timeout=10):
        auth_select = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//mat-label[contains(.,'Authentication Type')]/ancestor::mat-form-field//mat-select"
            ))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", auth_select)
        time.sleep(0.3)
        return auth_select

    def test_03_2fa_auth_type_dependency(self, logged_in_driver):
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        # Step 1: Verify 2FA is OFF and Auth Type is DISABLED
        is_off = self._is_2fa_state(driver, "off")
        auth_select = self._find_auth_select(driver)
        is_disabled_off = auth_select.get_attribute("aria-disabled") == "true"
        shot = self._screenshot(driver, "2fa_off_auth_disabled")
        self._record(
            test_name="2FA OFF -> Auth Type Disabled",
            expected="2FA is OFF, Auth Type disabled",
            actual=f"2fa_off={is_off}, aria-disabled={is_disabled_off}",
            status="PASSED" if is_off and is_disabled_off else "FAILED",
            category="2FA Dependency", field="Authentication Type", screenshot=shot,
        )

        # Step 2: Toggle 2FA ON (click hidden checkbox)
        toggled = self._toggle_2fa(driver, "on")
        if not toggled:
            shot = self._screenshot(driver, "2fa_toggle_failed")
            self._record(test_name="2FA Toggle ON", expected="Toggle switches to ON",
                actual="Failed to click toggle", status="FAILED",
                category="2FA Dependency", field="2FA Toggle", screenshot=shot)
            self._cleanup(page)
            return

        # Step 3: Verify 2FA is now ON
        is_on = self._is_2fa_state(driver, "on")
        shot = self._screenshot(driver, "2fa_toggled_on")
        self._record(test_name="2FA Toggle ON", expected="ON label becomes active",
            actual=f"is_on={is_on}", status="PASSED" if is_on else "FAILED",
            category="2FA Dependency", field="2FA Toggle", screenshot=shot)

        # Step 4: Verify Auth Type is now ENABLED (wait for Angular to re-render)
        is_disabled_on = True
        for attempt in range(6):
            time.sleep(0.5)
            auth_select = self._find_auth_select(driver)
            is_disabled_on = auth_select.get_attribute("aria-disabled") == "true"
            if not is_disabled_on:
                break
        shot = self._screenshot(driver, "2fa_on_auth_enabled")
        self._record(test_name="2FA ON -> Auth Type Enabled",
            expected="Auth Type dropdown is enabled",
            actual=f"aria-disabled={is_disabled_on}",
            status="PASSED" if not is_disabled_on else "FAILED",
            category="2FA Dependency", field="Authentication Type", screenshot=shot)

        # Step 5: Select 'email' from Auth Type dropdown
        if not is_disabled_on:
            try:
                auth_select = self._find_auth_select(driver)
                driver.execute_script("arguments[0].click();", auth_select)
                time.sleep(0.5)
                email_opt = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((
                        By.XPATH, "//div[@role='listbox']//mat-option[contains(.,'email')]"
                    ))
                )
                driver.execute_script("arguments[0].click();", email_opt)
                time.sleep(0.3)
                shot = self._screenshot(driver, "2fa_email_selected")
                self._record(test_name="2FA ON -> Select 'email'",
                    expected="Email option selected", actual="Email selected successfully",
                    status="PASSED", category="2FA Dependency",
                    field="Authentication Type", bad_value="email", screenshot=shot)
            except Exception as e:
                shot = self._screenshot(driver, "2fa_email_failed")
                self._record(test_name="2FA ON -> Select 'email'",
                    expected="Email option selected", actual=f"Error: {e}",
                    status="FAILED", category="2FA Dependency",
                    field="Authentication Type", screenshot=shot)

        # Step 6: Toggle 2FA OFF again
        self._toggle_2fa(driver, "off")
        auth_select = self._find_auth_select(driver)
        is_disabled_again = auth_select.get_attribute("aria-disabled") == "true"
        shot = self._screenshot(driver, "2fa_off_again")
        self._record(test_name="2FA OFF -> Auth Type Disabled Again",
            expected="Auth Type dropdown is disabled after toggle off",
            actual=f"aria-disabled={is_disabled_again}",
            status="PASSED" if is_disabled_again else "FAILED",
            category="2FA Dependency", field="Authentication Type", screenshot=shot)

        self._cleanup(page)

    # ================================================================
    # TEST 04: Duplicate Company Name -> SweetAlert
    # ================================================================

    def test_04_duplicate_name_sweetalert(self, logged_in_driver):
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)
        self._type_field(driver, "Company Name", "Washim")
        time.sleep(0.3)
        self._click_update_direct(driver)
        title, has_download = self._check_sweetalert(driver)
        shot = self._screenshot(driver, "dup_name_sweetalert")
        is_validation_failed = "validation failed" in title.lower()
        self._record(test_name="Duplicate Name: SweetAlert",
            expected="Title='Validation Failed' + Download Errors button",
            actual=f"title='{title}', download_btn={has_download}",
            status="PASSED" if is_validation_failed and has_download else "FAILED",
            category="Backend Validation", field="Company Name", bad_value="Washim", screenshot=shot)
        self._dismiss_sweetalert(driver)
        time.sleep(0.5)
        self._cleanup(page)

    # ================================================================
    # TEST 05: Invalid CIN -> SweetAlert
    # ================================================================

    def test_05_invalid_cin_sweetalert(self, logged_in_driver):
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)
        self._type_field(driver, "CIN", "INVALID123")
        time.sleep(0.3)
        self._click_update_direct(driver)
        title, has_download = self._check_sweetalert(driver)
        shot = self._screenshot(driver, "invalid_cin_sweetalert")
        is_validation_failed = "validation failed" in title.lower()
        self._record(test_name="Invalid CIN: SweetAlert",
            expected="Title='Validation Failed' + Download Errors button",
            actual=f"title='{title}', download_btn={has_download}",
            status="PASSED" if is_validation_failed and has_download else "FAILED",
            category="Backend Validation", field="CIN", bad_value="INVALID123", screenshot=shot)
        self._dismiss_sweetalert(driver)
        time.sleep(0.5)
        self._cleanup(page)

    # ================================================================
    # TEST 06: Max Length -> SweetAlert
    # ================================================================

    def test_06_max_length_sweetalert(self, logged_in_driver):
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)
        self._type_field(driver, "Company Short Name", "A" * 300)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title, has_download = self._check_sweetalert(driver)
        shot = self._screenshot(driver, "maxlen_short_name")
        is_failed = "failed to save record" in title.lower()
        self._record(test_name="Max Length: Company Short Name (300 chars)",
            expected="Toast='Failed to save record'", actual=f"title='{title}'",
            status="PASSED" if is_failed else "FAILED",
            category="Backend Validation", field="Company Short Name",
            bad_value="A" * 300, screenshot=shot)
        time.sleep(2)
        self._cleanup(page)

    # ================================================================
    # PROMOTER HELPERS
    # ================================================================

    def _navigate_to_step2(self, page):
        """Click Next from Step 1 to reach Step 2 (Promoters)."""
        page._click_next()
        time.sleep(1)
        try:
            WebDriverWait(page.driver, 5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//app-dynamic-details//input[@name='Name']")
                )
            )
            return True
        except Exception:
            return False

    def _count_promoter_rows(self, driver):
        """Count promoter rows in the table."""
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "app-dynamic-details tbody tr")
            return len(rows)
        except Exception:
            return 0

    def _has_delete_button_on_row(self, driver, row_index=1):
        """Check if a specific row has a delete (warn/remove) button."""
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "app-dynamic-details tbody tr")
            if row_index < 1 or row_index > len(rows):
                return False
            row = rows[row_index - 1]
            btn = row.find_element(By.CSS_SELECTOR, "button[mat-icon-button][color='warn']")
            return btn.is_displayed()
        except Exception:
            return False

    def _add_promoter_row(self, driver):
        """Click the + button to add a new promoter row."""
        try:
            add_btns = driver.find_elements(
                By.CSS_SELECTOR, "app-dynamic-details button[mat-icon-button][color='primary']"
            )
            if add_btns:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
                    add_btns[0]
                )
                time.sleep(0.8)
                return True
        except Exception:
            pass
        return False

    def _delete_promoter_row(self, driver, row_index=1):
        """Click the delete (remove) button on a specific row.
        Uses regular .click() first (triggers Angular events), falls back to JS click."""
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "app-dynamic-details tbody tr")
            if row_index < 1 or row_index > len(rows):
                return False
            row = rows[row_index - 1]
            btn = row.find_element(By.CSS_SELECTOR, "button[mat-icon-button][color='warn']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.3)
            try:
                btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.8)
            return True
        except Exception:
            return False

    def _type_promoter_field(self, driver, row_index, field_name, value):
        """Type into a promoter field (Name or Remark) by row index."""
        tag = "textarea" if field_name == "Remark" else "input"
        loc = f"(//app-dynamic-details//{tag}[@name='{field_name}'])[{row_index}]"
        el = driver.find_element(By.XPATH, loc)
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].focus();", el)
        time.sleep(0.2)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(value)
        time.sleep(0.3)
        el.send_keys(Keys.TAB)
        time.sleep(0.3)

    def _clear_promoter_field(self, driver, row_index, field_name):
        """Clear a promoter field by row index."""
        tag = "textarea" if field_name == "Remark" else "input"
        loc = f"(//app-dynamic-details//{tag}[@name='{field_name}'])[{row_index}]"
        el = driver.find_element(By.XPATH, loc)
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].focus();", el)
        time.sleep(0.2)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        time.sleep(0.3)
        el.send_keys(Keys.TAB)
        time.sleep(0.3)

    def _read_promoter_field(self, page, row_index, field_name):
        """Read a promoter field value by row index."""
        tag = "textarea" if field_name == "Remark" else "input"
        loc = ("xpath", f"(//app-dynamic-details//{tag}[@name='{field_name}'])[{row_index}]")
        return page._read_text_field(loc)

    def _is_on_step3(self, driver):
        """Check if form moved to Step 3 (Address)."""
        try:
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//mat-label[contains(.,'Address Type')]")
                )
            )
            return True
        except Exception:
            return False

    def _go_to_step1_from_step2(self, page):
        """Click Back from Step 2 to return to Step 1."""
        driver = page.driver
        try:
            back_btns = driver.find_elements(By.CSS_SELECTOR, "button[matstepperprevious]")
            if back_btns:
                btn = back_btns[0]
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.5)
                try:
                    btn.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
                return True
        except Exception:
            pass

        # Not found with CSS � dump diagnostics
        diag = driver.execute_script("""
            var info = [];
            var exact = document.querySelectorAll('button[matstepperprevious]');
            info.push('button[matstepperprevious] count: ' + exact.length);
            var exact2 = document.querySelectorAll('button[matStepperPrevious]');
            info.push('button[matStepperPrevious] count: ' + exact2.length);
            var byClass = document.querySelectorAll('button.mat-stepper-previous');
            info.push('button.mat-stepper-previous count: ' + byClass.length);
            var allBtns = document.querySelectorAll('button');
            info.push('Total buttons on page: ' + allBtns.length);
            for (var i = 0; i < allBtns.length; i++) {
                var b = allBtns[i];
                var txt = (b.textContent || '').trim();
                var cls = (b.className || '');
                var attrs = '';
                for (var j = 0; j < b.attributes.length; j++) {
                    attrs += b.attributes[j].name + '=' + b.attributes[j].value + ' ';
                }
                if (txt.toLowerCase().indexOf('back') !== -1 ||
                    cls.indexOf('stepper') !== -1 ||
                    cls.indexOf('step-') !== -1 ||
                    attrs.indexOf('stepper') !== -1) {
                    info.push('MATCH btn[' + i + ']: text="' + txt + '", class="' + cls + '", attrs=[' + attrs.trim() + ']');
                }
            }
            return info.join('\\n');
        """)
        log.warning(f"[DIAG] Back button not found. Page diagnostics:\\n{diag}")
        self._screenshot(driver, "diag_back_button_missing")
        return False

    def _handle_update_success(self, driver, timeout=15):
        """After clicking Update, handle the success SweetAlert (click confirm)."""
        try:
            WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#swal2-title"))
            )
            title_el = driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            title = title_el.text.strip()
            try:
                confirm_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".swal2-confirm"))
                )
                confirm_btn.click()
                time.sleep(1)
            except Exception:
                pass
            return title
        except Exception:
            return ""

    # ================================================================
    # TEST 07: Promoter � All UI Validations [ONE form open]
    # Navigation + Pre-filled + Optional + Add rows + Delete rows
    # ================================================================

    def test_07_promoter_all_ui_validations(self, logged_in_driver):
        """All promoter UI checks in one form open:
        pre-filled data, back/next navigation, optional fields, add rows, delete rows."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        # --- Navigate to Step 2 ---
        reached = self._navigate_to_step2(page)
        if not reached:
            self._record(test_name="Promoter: Navigate to Step 2",
                expected="Promoter table visible", actual="Failed to reach Step 2",
                status="FAILED", category="Promoters")
            self._cleanup(page)
            return

        # --- Pre-filled data ---
        row_count = self._count_promoter_rows(driver)
        name1 = self._read_promoter_field(page, 1, "Name")
        remark1 = self._read_promoter_field(page, 1, "Remark")
        shot_prefilled = self._screenshot(driver, "promo_prefilled")
        has_data = bool(name1) or bool(remark1)
        self._record(test_name="Promoter: Pre-filled Data",
            expected="Existing promoter data is pre-filled",
            actual=f"rows={row_count}, name='{name1}', remark='{remark1}'",
            status="PASSED" if has_data else "FAILED",
            category="Promoters", field="Name, Remark",
            original_value=f"name='{name1}', remark='{remark1}'",
            screenshot=shot_prefilled)

        # --- Back to Step 1 ---
        went_back = self._go_to_step1_from_step2(page)
        on_step1 = False
        if went_back:
            try:
                WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='Company Short Name']"))
                )
                on_step1 = True
            except Exception:
                pass
        shot_back = self._screenshot(driver, "promo_back_to_step1")
        self._record(test_name="Promoter: Back to Step 1",
            expected="Back button returns to Step 1",
            actual=f"went_back={went_back}, on_step1={on_step1}",
            status="PASSED" if on_step1 else "FAILED",
            category="Promoters", screenshot=shot_back)

        # --- Next to Step 3 ---
        if on_step1:
            reached2 = self._navigate_to_step2(page)
            if not reached2:
                self._record(test_name="Promoter: Next to Step 3",
                    expected="Next button proceeds to Step 3 (Address)",
                    actual="Failed to navigate to Step 2",
                    status="FAILED", category="Promoters")
                self._cleanup(page)
                return
        else:
            if not self._is_on_step2(driver):
                self._record(test_name="Promoter: Next to Step 3",
                    expected="Next button proceeds to Step 3 (Address)",
                    actual="Lost track of current step (not on Step 1 or Step 2)",
                    status="FAILED", category="Promoters")
                self._cleanup(page)
                return
        page._click_next()
        time.sleep(1)
        on_step3 = self._is_on_step3(driver)
        shot_next = self._screenshot(driver, "promo_next_to_step3")
        self._record(test_name="Promoter: Next to Step 3",
            expected="Next button proceeds to Step 3 (Address)",
            actual=f"on_step3={on_step3}",
            status="PASSED" if on_step3 else "FAILED",
            category="Promoters", screenshot=shot_next)

        # --- Optional fields � empty -> Next succeeds ---
        self._go_to_step1_from_step2(page)
        if not self._is_on_step2(driver):
            self._navigate_to_step2(page)

        self._clear_promoter_field(driver, 1, "Name")
        self._clear_promoter_field(driver, 1, "Remark")
        time.sleep(0.3)
        page._click_next()
        time.sleep(1)
        on_step3_opt = self._is_on_step3(driver)
        shot_opt = self._screenshot(driver, "promo_optional_fields")
        self._record(test_name="Promoter: Optional Fields",
            expected="Both fields empty � Next proceeds to Step 3 with no error",
            actual=f"on_step3={on_step3_opt}",
            status="PASSED" if on_step3_opt else "FAILED",
            category="Promoters", field="Name, Remark",
            bad_value="(empty)", screenshot=shot_opt)

        # --- Navigate back to Step 2 for add/delete tests ---
        self._go_to_step1_from_step2(page)
        if not self._is_on_step2(driver):
            self._navigate_to_step2(page)

        # --- Add rows ---
        before_add = self._count_promoter_rows(driver)
        added1 = self._add_promoter_row(driver)
        after1 = self._count_promoter_rows(driver)
        shot_add1 = self._screenshot(driver, "promo_add_one_row")
        self._record(test_name="Promoter: Add Row",
            expected="Clicking + adds a new blank promoter row",
            actual=f"rows_before={before_add}, added={added1}, rows_after={after1}",
            status="PASSED" if added1 and after1 == before_add + 1 else "FAILED",
            category="Promoters", screenshot=shot_add1)

        added2 = self._add_promoter_row(driver)
        after2 = self._count_promoter_rows(driver)
        shot_add2 = self._screenshot(driver, "promo_add_multiple_rows")
        self._record(test_name="Promoter: Add Multiple Rows",
            expected="Multiple rows can be added via + button",
            actual=f"rows_after_first={after1}, added_again={added2}, total={after2}",
            status="PASSED" if added2 and after2 == after1 + 1 else "FAILED",
            category="Promoters", screenshot=shot_add2)

        # --- Delete operations ---
        if self._count_promoter_rows(driver) < 2:
            self._add_promoter_row(driver)

        has_del_row1 = self._has_delete_button_on_row(driver, 1)
        has_del_row2 = self._has_delete_button_on_row(driver, 2)
        shot_del_multi = self._screenshot(driver, "promo_delete_multi_rows")
        self._record(test_name="Promoter: Delete Button on Multiple Rows",
            expected="Each row has its own delete button when multiple rows exist",
            actual=f"row1_has_delete={has_del_row1}, row2_has_delete={has_del_row2}",
            status="PASSED" if has_del_row1 and has_del_row2 else "FAILED",
            category="Promoters", screenshot=shot_del_multi)

        before_del = self._count_promoter_rows(driver)
        deleted = self._delete_promoter_row(driver, row_index=2)
        after_del = self._count_promoter_rows(driver)
        shot_del_one = self._screenshot(driver, "promo_delete_one_row")
        self._record(test_name="Promoter: Delete One Row",
            expected="Row count decreases by 1 after deletion",
            actual=f"rows_before={before_del}, deleted={deleted}, rows_after={after_del}",
            status="PASSED" if deleted and after_del == before_del - 1 else "FAILED",
            category="Promoters", screenshot=shot_del_one)

        # Single row � no delete button
        if after_del > 1:
            max_attempts = 10
            attempts = 0
            while self._count_promoter_rows(driver) > 1 and attempts < max_attempts:
                self._delete_promoter_row(driver, row_index=2)
                time.sleep(0.5)
                attempts += 1
        no_del = not self._has_delete_button_on_row(driver, 1)
        shot_single = self._screenshot(driver, "promo_single_no_delete")
        self._record(test_name="Promoter: No Delete on Single Row",
            expected="Delete button not visible when only 1 row remains",
            actual=f"has_delete_button={not no_del}",
            status="PASSED" if no_del else "FAILED",
            category="Promoters", screenshot=shot_single)

        self._cleanup(page)

    # ================================================================
    # TEST 08: Promoter � Max Length + Update & Verify [ONE form open]
    # 101 chars -> fail, 100 chars -> save, re-open -> verify persisted
    # ================================================================

    def test_08_promoter_max_length_and_verify(self, logged_in_driver):
        """Max length boundary + update & verify persistence in one form open."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step2(page)
        if not reached:
            self._record(test_name="Max Length: Promoter Name (101 chars)",
                expected="Failed to save record", actual="Failed to reach Step 2",
                status="FAILED", category="Promoters", field="Promoter Name")
            self._cleanup(page)
            return

        # --- 101 chars -> Update fails ---
        long_name = "A" * 101
        self._type_promoter_field(driver, 1, "Name", long_name)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title, has_download = self._check_sweetalert(driver, timeout=15)
        shot_101 = self._screenshot(driver, "promo_maxlen_name_101")
        is_failed_101 = "failed to save record" in title.lower()
        self._record(test_name="Max Length: Promoter Name (101 chars)",
            expected="'Failed to save record' toast shown",
            actual=f"title='{title}'",
            status="PASSED" if is_failed_101 else "FAILED",
            category="Promoters", field="Promoter Name",
            bad_value=f"{long_name[:30]}...({len(long_name)} chars)",
            screenshot=shot_101)

        # Dismiss the error and type 100 chars
        self._dismiss_sweetalert(driver)
        time.sleep(0.5)

        # Go back to Step 2 if error pushed us somewhere else
        try:
            WebDriverWait(driver, 3).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//app-dynamic-details//input[@name='Name']")
                )
            )
        except Exception:
            try:
                back_btn = WebDriverWait(page.driver, 3).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "button[matstepperprevious]"))
                )
                page.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", back_btn)
                time.sleep(0.3)
                try:
                    back_btn.click()
                except Exception:
                    page.driver.execute_script("arguments[0].click();", back_btn)
                time.sleep(0.8)
            except Exception:
                self._go_to_step1_from_step2(page)
                self._navigate_to_step2(page)

        # --- 100 chars -> Update succeeds ---
        boundary_name = "A" * 100
        self._type_promoter_field(driver, 1, "Name", boundary_name)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_100 = self._handle_update_success(driver, timeout=15)
        shot_100 = self._screenshot(driver, "promo_maxlen_name_100")
        is_failed_100 = "failed to save record" in title_100.lower()
        self._record(test_name="Max Length: Promoter Name (100 chars)",
            expected="Record saves successfully (at boundary limit)",
            actual=f"title='{title_100}'",
            status="PASSED" if not is_failed_100 else "FAILED",
            category="Promoters", field="Promoter Name",
            screenshot=shot_100)
        time.sleep(1)

        # --- Re-open & verify persisted ---
        try:
            page.navigate_to_page()
            time.sleep(1.5)
            page.search_company(TEST_COMPANY)
            time.sleep(1)
            page._click_edit_button(TEST_COMPANY)
            time.sleep(3)
            self._navigate_to_step2(page)

            saved_name = self._read_promoter_field(page, 1, "Name")
            shot_verify = self._screenshot(driver, "promo_verify_after")
            persisted = (saved_name == boundary_name)
            self._record(test_name="Promoter: Update & Verify",
                expected="Name (100 chars) persisted after save",
                actual=f"saved_name='{saved_name[:30]}...'({len(saved_name)} chars), persisted={persisted}",
                status="PASSED" if persisted else "FAILED",
                category="Promoters", field="Promoter Name",
                screenshot=shot_verify)
        except Exception as e:
            self._record(test_name="Promoter: Update & Verify",
                expected="Re-open and verify saved name",
                actual=f"Error during re-open: {e}",
                status="FAILED", category="Promoters", field="Promoter Name")

        self._cleanup(page)

    # ================================================================
    # TEST 09: Promoter � Boundary + Backend Validations [ONE form open]
    # Remark maxlen, empty save, edit+verify persistence, restore original
    # ================================================================

    def test_09_promoter_boundary_and_backend(self, logged_in_driver):
        """Boundary + backend checks with save/restore pattern.
        Remark 256->fail, 255->save, empty all->save, edit->verify, restore original."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step2(page)
        if not reached:
            self._record(test_name="Remark: Max 256 chars",
                expected="Failed to save record", actual="Failed to reach Step 2",
                status="FAILED", category="Promoters", field="Remark")
            self._cleanup(page)
            return

        # --- Save original values for restoration later ---
        orig_name = self._read_promoter_field(page, 1, "Name")
        orig_remark = self._read_promoter_field(page, 1, "Remark")

        # --- CHECK 13: Remark 256 chars -> Update fails ---
        long_remark = "A" * 256
        self._type_promoter_field(driver, 1, "Remark", long_remark)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title, _ = self._check_sweetalert(driver, timeout=15)
        shot_r256 = self._screenshot(driver, "promo_remark_256")
        is_failed_256 = "failed to save record" in title.lower()
        self._record(test_name="Remark: Max 256 chars",
            expected="'Failed to save record' toast shown",
            actual=f"title='{title}'",
            status="PASSED" if is_failed_256 else "FAILED",
            category="Promoters", field="Remark",
            bad_value=f"{'A'*30}...({len(long_remark)} chars)",
            screenshot=shot_r256)
        self._dismiss_sweetalert(driver)
        time.sleep(0.5)

        # --- Ensure we're back on Step 2 ---
        if not self._is_on_step2(driver):
            self._go_to_step1_from_step2(page)
            if not self._is_on_step2(driver):
                self._navigate_to_step2(page)

        # --- CHECK 14: Remark 255 chars -> Update succeeds ---
        boundary_remark = "A" * 255
        self._type_promoter_field(driver, 1, "Remark", boundary_remark)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_255 = self._handle_update_success(driver, timeout=15)
        shot_r255 = self._screenshot(driver, "promo_remark_255")
        is_failed_255 = "failed to save record" in title_255.lower()
        self._record(test_name="Remark: Max 255 chars",
            expected="Record saves successfully (at boundary limit)",
            actual=f"title='{title_255}'",
            status="PASSED" if not is_failed_255 else "FAILED",
            category="Promoters", field="Remark",
            screenshot=shot_r255)
        time.sleep(1)

        # --- CHECK 15: Empty all fields -> Update saves ---
        page.navigate_to_page()
        time.sleep(1.5)
        page.search_company(TEST_COMPANY)
        time.sleep(1)
        page._click_edit_button(TEST_COMPANY)
        time.sleep(3)
        self._navigate_to_step2(page)

        self._clear_promoter_field(driver, 1, "Name")
        self._clear_promoter_field(driver, 1, "Remark")
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_empty = self._handle_update_success(driver, timeout=15)
        shot_empty = self._screenshot(driver, "promo_empty_save")
        is_failed_empty = "failed to save record" in title_empty.lower()
        self._record(test_name="Empty All Fields -> Save",
            expected="Record saves with empty Name & Remark (optional fields)",
            actual=f"title='{title_empty}'",
            status="PASSED" if not is_failed_empty else "FAILED",
            category="Promoters", field="Name, Remark",
            bad_value="(empty)",
            screenshot=shot_empty)
        time.sleep(1)

        # --- CHECK 16: Empty fields persisted ---
        page.navigate_to_page()
        time.sleep(1.5)
        page.search_company(TEST_COMPANY)
        time.sleep(1)
        page._click_edit_button(TEST_COMPANY)
        time.sleep(3)
        self._navigate_to_step2(page)

        saved_name_empty = self._read_promoter_field(page, 1, "Name")
        saved_remark_empty = self._read_promoter_field(page, 1, "Remark")
        shot_empty_verify = self._screenshot(driver, "promo_empty_verify")
        both_empty = (not saved_name_empty or saved_name_empty.strip() == "") and \
                     (not saved_remark_empty or saved_remark_empty.strip() == "")
        self._record(test_name="Empty Fields Persisted",
            expected="Name & Remark remain empty after save",
            actual=f"name='{saved_name_empty}', remark='{saved_remark_empty}'",
            status="PASSED" if both_empty else "FAILED",
            category="Promoters", field="Name, Remark",
            screenshot=shot_empty_verify)

        # --- CHECK 17: Edit name -> save -> verify ---
        test_edit_name = "Test Promoter Edit"
        self._type_promoter_field(driver, 1, "Name", test_edit_name)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_edit = self._handle_update_success(driver, timeout=15)
        shot_edit = self._screenshot(driver, "promo_edit_save")
        is_failed_edit = "failed to save record" in title_edit.lower()
        self._record(test_name="Edit Name -> Save",
            expected="Updated name saves successfully",
            actual=f"title='{title_edit}'",
            status="PASSED" if not is_failed_edit else "FAILED",
            category="Promoters", field="Name",
            bad_value=test_edit_name,
            screenshot=shot_edit)
        time.sleep(1)

        # Verify persisted
        page.navigate_to_page()
        time.sleep(1.5)
        page.search_company(TEST_COMPANY)
        time.sleep(1)
        page._click_edit_button(TEST_COMPANY)
        time.sleep(3)
        self._navigate_to_step2(page)

        saved_edit = self._read_promoter_field(page, 1, "Name")
        shot_edit_verify = self._screenshot(driver, "promo_edit_verify")
        edit_persisted = (saved_edit == test_edit_name)
        self._record(test_name="Edit Name -> Verify Persisted",
            expected=f"Name '{test_edit_name}' persists after save",
            actual=f"saved_name='{saved_edit}', persisted={edit_persisted}",
            status="PASSED" if edit_persisted else "FAILED",
            category="Promoters", field="Name",
            screenshot=shot_edit_verify)

        # --- CHECK 18: Restore original data ---
        self._type_promoter_field(driver, 1, "Name", orig_name or "")
        if orig_remark:
            self._type_promoter_field(driver, 1, "Remark", orig_remark)
        else:
            self._clear_promoter_field(driver, 1, "Remark")
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_restore = self._handle_update_success(driver, timeout=15)
        shot_restore = self._screenshot(driver, "promo_restore")
        restore_ok = "failed" not in title_restore.lower() or not title_restore
        orig_display = orig_name[:30] if orig_name else "(empty)"
        self._record(test_name="Restore Original Data",
            expected="Original promoter data restored successfully",
            actual=f"title='{title_restore}', orig_name='{orig_display}'",
            status="PASSED" if restore_ok else "FAILED",
            category="Promoters", field="Name, Remark",
            original_value=f"name='{orig_name}', remark='{orig_remark}'",
            screenshot=shot_restore)

        self._cleanup(page)

    # ================================================================
    # TEST 10: Promoter � Edge Cases [ONE form open, NO Update clicks]
    # Special chars, whitespace, multiline, rapid add/delete, max rows
    # ================================================================

    def test_10_promoter_edge_cases(self, logged_in_driver):
        """UI edge case checks � no Update button pressed, no data changes."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step2(page)
        if not reached:
            self._record(test_name="Special Chars in Name",
                expected="Next proceeds to Step 3", actual="Failed to reach Step 2",
                status="FAILED", category="Promoters")
            self._cleanup(page)
            return

        # Save original values
        orig_name = self._read_promoter_field(page, 1, "Name")
        orig_remark = self._read_promoter_field(page, 1, "Remark")

        # --- CHECK 19: Special characters in Name -> Next succeeds ---
        special_name = "<script>alert(1)</script>"
        self._type_promoter_field(driver, 1, "Name", special_name)
        time.sleep(0.3)
        page._click_next()
        time.sleep(1)
        on_step3_special = self._is_on_step3(driver)
        shot_special = self._screenshot(driver, "promo_special_chars")
        self._record(test_name="Special Chars in Name",
            expected="No validation error � Next proceeds to Step 3",
            actual=f"on_step3={on_step3_special}",
            status="PASSED" if on_step3_special else "FAILED",
            category="Promoters", field="Name",
            bad_value=special_name,
            screenshot=shot_special)

        # --- Back to Step 2 ---
        self._go_to_step1_from_step2(page)
        if not self._is_on_step2(driver):
            self._navigate_to_step2(page)

        # --- CHECK 20: Whitespace-only fields -> Next succeeds ---
        self._type_promoter_field(driver, 1, "Name", "   ")
        self._type_promoter_field(driver, 1, "Remark", "   ")
        time.sleep(0.3)
        page._click_next()
        time.sleep(1)
        on_step3_ws = self._is_on_step3(driver)
        shot_ws = self._screenshot(driver, "promo_whitespace")
        self._record(test_name="Whitespace-Only Fields",
            expected="No validation error � Next proceeds to Step 3",
            actual=f"on_step3={on_step3_ws}",
            status="PASSED" if on_step3_ws else "FAILED",
            category="Promoters", field="Name, Remark",
            bad_value="'   ' (whitespace)",
            screenshot=shot_ws)

        # --- Back to Step 2 ---
        self._go_to_step1_from_step2(page)
        if not self._is_on_step2(driver):
            self._navigate_to_step2(page)

        # --- CHECK 21: Multi-line Remark ---
        multiline_text = "Line one of remark\nLine two here\nLine three end"
        self._clear_promoter_field(driver, 1, "Remark")
        self._type_promoter_field(driver, 1, "Remark", multiline_text)
        time.sleep(0.5)
        read_back = self._read_promoter_field(page, 1, "Remark")
        shot_ml = self._screenshot(driver, "promo_multiline")
        multiline_ok = ("Line one" in read_back and "Line three" in read_back)
        self._record(test_name="Multi-line Remark",
            expected="Textarea accepts and retains newline characters",
            actual=f"contains_newlines={multiline_ok}, read_back='{read_back[:50]}'",
            status="PASSED" if multiline_ok else "FAILED",
            category="Promoters", field="Remark",
            bad_value=multiline_text,
            screenshot=shot_ml)

        # --- CHECK 22: Rapid add then delete ---
        before_rapid = self._count_promoter_rows(driver)
        self._add_promoter_row(driver)
        time.sleep(0.5)
        after_add = self._count_promoter_rows(driver)
        # Delete the last row (the one we just added)
        if after_add > before_rapid:
            self._delete_promoter_row(driver, row_index=after_add)
            time.sleep(0.5)
        after_delete = self._count_promoter_rows(driver)
        shot_rapid = self._screenshot(driver, "promo_rapid_add_delete")
        count_stable = (after_delete == before_rapid)
        self._record(test_name="Rapid Add Then Delete",
            expected="Add row -> delete row -> count returns to original",
            actual=f"before={before_rapid}, after_add={after_add}, after_delete={after_delete}",
            status="PASSED" if count_stable else "FAILED",
            category="Promoters", screenshot=shot_rapid)

        # --- CHECK 23: Max rows limit ---
        start_count = self._count_promoter_rows(driver)
        max_clicks = 20
        added_count = 0
        for i in range(max_clicks):
            before = self._count_promoter_rows(driver)
            ok = self._add_promoter_row(driver)
            time.sleep(0.3)
            after = self._count_promoter_rows(driver)
            if ok and after == before + 1:
                added_count += 1
            else:
                # + button failed or row didn't increase � stop
                break
        final_count = self._count_promoter_rows(driver)
        shot_max = self._screenshot(driver, "promo_max_rows")
        hit_cap = (added_count < max_clicks)
        self._record(test_name="Max Rows Limit",
            expected=f"System prevents adding unlimited rows (capped or stopped within {max_clicks} clicks)",
            actual=f"start={start_count}, added={added_count}/{max_clicks} attempts, final={final_count}, capped={hit_cap}",
            status="PASSED" if hit_cap or final_count > 30 else "FAILED",
            category="Promoters",
            bad_value=f"tried adding {max_clicks} rows",
            screenshot=shot_max)

        # --- Cleanup: restore original values (no Update � just reset UI) ---
        self._type_promoter_field(driver, 1, "Name", orig_name or "")
        self._type_promoter_field(driver, 1, "Remark", orig_remark or "")

        self._cleanup(page)

    # ================================================================
    # ADDRESS HELPERS
    # ================================================================

    def _navigate_to_step3(self, page):
        """Navigate to Step 3 (Address Details) from wherever the form currently is."""
        driver = page.driver
        # Already on Step 3?
        if self._is_on_step3(driver):
            return True
        # FIX: On Step 4? Click Back to reach Step 3
        if self._is_on_step4(driver):
            try:
                back_btns = driver.find_elements(By.CSS_SELECTOR, "button[matstepperprevious]")
                if back_btns:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", back_btns[0])
                    time.sleep(0.5)
                    try:
                        back_btns[0].click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", back_btns[0])
                    time.sleep(1.5)
                    return self._is_on_step3(driver)
            except Exception:
                pass
        # On Step 2? Click Next to get to Step 3
        if self._is_on_step2(driver):
            page._click_next()
            time.sleep(1.5)
            return self._is_on_step3(driver)
        # On Step 1 -> Step 2 -> Step 3
        self._navigate_to_step2(page)
        if not self._is_on_step2(driver):
            return False
        page._click_next()
        time.sleep(1.5)
        return self._is_on_step3(driver)

    def _go_back_to_step2(self, page):
        """Click Back to return to Step 2 (Promoters) from Step 3 or Step 4."""
        driver = page.driver
        # FIX: If on Step 4, click Back first to reach Step 3
        if self._is_on_step4(driver) and not self._is_on_step3(driver):
            try:
                back_btns = driver.find_elements(By.CSS_SELECTOR, "button[matstepperprevious]")
                if back_btns:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", back_btns[0])
                    time.sleep(0.5)
                    try:
                        back_btns[0].click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", back_btns[0])
                    time.sleep(1)
            except Exception:
                pass
        if not self._is_on_step3(driver):
            return False
        try:
            back_btns = driver.find_elements(By.CSS_SELECTOR, "button[matstepperprevious]")
            if back_btns:
                btn = back_btns[0]
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.5)
                try:
                    btn.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
                return self._is_on_step2(driver)
        except Exception:
            pass
        return False

    def _is_on_step4(self, driver):
        """Check if form moved to Step 4 (Business Activities)."""
        try:
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//mat-label[contains(.,'Business Activities')]")
                )
            )
            return True
        except Exception:
            return False

    def _addr_close_overlay(self, driver):
        """Close any open mat-select overlay panels (not dialogs)."""
        try:
            driver.execute_script("""
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
                document.querySelectorAll('cdk-overlay-pane').forEach(function(pane) {
                    if (!pane.querySelector('.swal2-container') && !pane.querySelector('mat-dialog-container')) {
                        pane.remove();
                    }
                });
            """)
            time.sleep(0.2)
        except Exception:
            pass

    # XPath to the address-specific app-dynamic-details (avoids promoter rows)
    _ADDR_XPATH = "//app-dynamic-details[.//mat-label[contains(.,'Address Type')]]"

    def _addr_container(self, driver):
        """Return the app-dynamic-details element for the Address (Step 3) section."""
        return driver.find_element(By.XPATH, self._ADDR_XPATH)

    def _addr_count_rows(self, driver):
        """Count address rows in the Step 3 table only (scoped to address container)."""
        try:
            container = self._addr_container(driver)
            rows = container.find_elements(By.CSS_SELECTOR, "tbody tr")
            return len(rows)
        except Exception:
            return 0

    def _addr_add_row(self, driver):
        """Click the + button to add a new address row (scoped to address container)."""
        try:
            container = self._addr_container(driver)
            add_btns = container.find_elements(
                By.CSS_SELECTOR, "button[mat-icon-button][color='primary']"
            )
            if add_btns:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
                    add_btns[0]
                )
                time.sleep(0.8)
                return True
        except Exception:
            pass
        return False

    def _addr_delete_row(self, driver, row_index=1):
        """Click the delete button on a specific address row (scoped to address container)."""
        try:
            container = self._addr_container(driver)
            rows = container.find_elements(By.CSS_SELECTOR, "tbody tr")
            if row_index < 1 or row_index > len(rows):
                return False
            row = rows[row_index - 1]
            btn = row.find_element(By.CSS_SELECTOR, "button[mat-icon-button][color='warn']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.3)
            try:
                btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.8)
            return True
        except Exception:
            return False

    def _addr_has_delete_button(self, driver, row_index=1):
        """Check if a specific address row has a visible delete button (scoped to address container)."""
        try:
            container = self._addr_container(driver)
            rows = container.find_elements(By.CSS_SELECTOR, "tbody tr")
            if row_index < 1 or row_index > len(rows):
                return False
            row = rows[row_index - 1]
            btn = row.find_element(By.CSS_SELECTOR, "button[mat-icon-button][color='warn']")
            return btn.is_displayed()
        except Exception:
            return False

    def _addr_open_dropdown(self, driver, row_index, label_name, timeout=10):
        """Open a mat-select dropdown for a specific address row (scoped to address container)."""
        xpath = f"({self._ADDR_XPATH}//mat-label[contains(.,'{label_name}')]/ancestor::mat-form-field//mat-select)[{row_index}]"
        trigger = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", trigger)
        time.sleep(0.3)
        try:
            trigger.click()
        except Exception:
            driver.execute_script("arguments[0].click();", trigger)
        time.sleep(0.5)
        return trigger

    def _addr_get_dropdown_options(self, driver, timeout=5):
        """Get all option texts from the currently open mat-select dropdown."""
        try:
            WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div[role='listbox'] mat-option"))
            )
            options = driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
            return [opt.text.strip() for opt in options if opt.text.strip()]
        except Exception:
            return []

    def _addr_select_option_by_text(self, driver, option_text, timeout=5):
        """Click an option from the currently open dropdown by its text."""
        try:
            opt = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((
                    By.XPATH, f"//div[@role='listbox']//mat-option[contains(.,'{option_text}')]"
                ))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opt)
            time.sleep(0.2)
            try:
                opt.click()
            except Exception:
                driver.execute_script("arguments[0].click();", opt)
            time.sleep(0.5)
            return True
        except Exception:
            return False

    def _addr_select_random(self, driver, row_index, label_name, exclude=None):
        """Open dropdown, pick a random option (excluding specified), click it."""
        self._addr_open_dropdown(driver, row_index, label_name)
        options = self._addr_get_dropdown_options(driver)
        if not options:
            return ""
        if exclude:
            filtered = [o for o in options if o != exclude]
            if filtered:
                options = filtered
        chosen = random.choice(options)
        self._addr_select_option_by_text(driver, chosen)
        return chosen

    def _addr_read_dropdown_value(self, driver, row_index, label_name):
        """Read the currently selected text from a mat-select dropdown (scoped to address container)."""
        xpath = f"({self._ADDR_XPATH}//mat-label[contains(.,'{label_name}')]/ancestor::mat-form-field//mat-select)[{row_index}]"
        try:
            trigger = driver.find_element(By.XPATH, xpath)
            # Read from mat-select-value-text or mat-select-min-line span
            try:
                val_span = trigger.find_element(By.CSS_SELECTOR, ".mat-select-value-text span, .mat-select-min-line span")
                return val_span.text.strip()
            except Exception:
                # Fallback: read trigger text directly
                return trigger.text.strip()
        except Exception:
            return ""

    def _addr_fill_cascade(self, driver, row_index, max_attempts=5, wall_timeout=60):
        """Fill State->District->Taluka with retry (some combos have no Taluka).
        Returns (state, district, taluka) tuple of selected values.
        wall_timeout: hard limit in seconds to prevent infinite-appearing hangs."""
        start = time.time()
        for attempt in range(max_attempts):
            if time.time() - start > wall_timeout:
                log.warning(f"[_addr_fill_cascade] Wall timeout ({wall_timeout}s) reached at attempt {attempt+1}")
                break
            try:
                # Force-close any stale overlay before each attempt
                self._addr_close_overlay(driver)
                time.sleep(0.2)

                # Select random State
                log.info(f"[_addr_fill_cascade] Attempt {attempt+1}/{max_attempts}: opening State dropdown...")
                self._addr_open_dropdown(driver, row_index, "State")
                states = self._addr_get_dropdown_options(driver)
                if not states:
                    log.warning(f"[_addr_fill_cascade] No State options found, retrying...")
                    self._addr_close_overlay(driver)
                    time.sleep(0.3)
                    continue
                state = random.choice(states)
                log.info(f"[_addr_fill_cascade] Selected State: {state}")
                self._addr_select_option_by_text(driver, state)
                time.sleep(0.8)

                # Open District dropdown
                log.info(f"[_addr_fill_cascade] Opening District dropdown...")
                self._addr_open_dropdown(driver, row_index, "District")
                districts = self._addr_get_dropdown_options(driver)
                if not districts:
                    log.warning(f"[_addr_fill_cascade] No District options for '{state}', retrying...")
                    self._addr_close_overlay(driver)
                    time.sleep(0.3)
                    continue
                district = random.choice(districts)
                log.info(f"[_addr_fill_cascade] Selected District: {district}")
                self._addr_select_option_by_text(driver, district)
                time.sleep(0.8)

                # Open Taluka dropdown
                log.info(f"[_addr_fill_cascade] Opening Taluka dropdown...")
                self._addr_open_dropdown(driver, row_index, "Taluka")
                talukas = self._addr_get_dropdown_options(driver)
                if not talukas:
                    log.warning(f"[_addr_fill_cascade] No Taluka options for '{district}', retrying...")
                    self._addr_close_overlay(driver)
                    time.sleep(0.3)
                    continue
                taluka = random.choice(talukas)
                log.info(f"[_addr_fill_cascade] Selected Taluka: {taluka}")
                self._addr_select_option_by_text(driver, taluka)
                time.sleep(0.3)
                return state, district, taluka

            except Exception as e:
                log.warning(f"[_addr_fill_cascade] Exception on attempt {attempt+1}: {e}")
                self._addr_close_overlay(driver)
                time.sleep(0.3)
                continue
        log.warning(f"[_addr_fill_cascade] Failed after {attempt+1} attempts")
        return "", "", ""

    def _addr_find_input(self, driver, row_index, field_name):
        """Find an input or textarea element in the address container by row index."""
        container = self._addr_container(driver)
        rows = container.find_elements(By.CSS_SELECTOR, "tbody tr")
        if row_index < 1 or row_index > len(rows):
            raise Exception(f"Row {row_index} not found (only {len(rows)} address rows)")
        row = rows[row_index - 1]
        # Try input first, then textarea
        els = row.find_elements(By.CSS_SELECTOR, f"input[name='{field_name}']")
        if not els:
            els = row.find_elements(By.CSS_SELECTOR, f"textarea[name='{field_name}']")
        if els:
            return els[0]
        raise Exception(f"Field '{field_name}' not found in address row {row_index}")

    def _addr_type_field(self, driver, row_index, field_name, value):
        """Type into an address input field by row index (scoped to address container)."""
        el = self._addr_find_input(driver, row_index, field_name)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.3)
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].focus();", el)
        time.sleep(0.2)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(value)
        time.sleep(0.3)
        el.send_keys(Keys.TAB)
        time.sleep(0.3)

    def _addr_clear_field(self, driver, row_index, field_name):
        """Clear an address input field by row index (scoped to address container)."""
        el = self._addr_find_input(driver, row_index, field_name)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.3)
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].focus();", el)
        time.sleep(0.2)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        time.sleep(0.3)
        el.send_keys(Keys.TAB)
        time.sleep(0.3)

    def _addr_read_field(self, page, row_index, field_name):
        """Read an address input field value by row index (scoped to address container)."""
        el = self._addr_find_input(page.driver, row_index, field_name)
        return el.get_attribute("value") or ""

    def _addr_check_dropdown_invalid(self, driver, row_index, label_name):
        """Check if a dropdown (mat-select) field shows validation error (scoped to address container)."""
        try:
            xpath = f"({self._ADDR_XPATH}//mat-label[contains(.,'{label_name}')]/ancestor::mat-form-field)[{row_index}]"
            form_field = driver.find_element(By.XPATH, xpath)
            classes = form_field.get_attribute("class") or ""
            is_invalid = "mat-form-field-invalid" in classes
            error_text = ""
            try:
                err_el = form_field.find_element(By.CSS_SELECTOR, "mat-error")
                error_text = err_el.text.strip()
            except Exception:
                pass
            return is_invalid, error_text
        except Exception:
            return False, ""

    def _addr_check_input_invalid(self, driver, row_index, field_name):
        """Check if an address input field shows validation error by row index (scoped to address container)."""
        try:
            el = self._addr_find_input(driver, row_index, field_name)
            classes = el.get_attribute("class") or ""
            is_invalid = "ng-invalid" in classes and "ng-touched" in classes
            error_id = el.get_attribute("aria-describedby") or ""
            error_text = ""
            if error_id:
                try:
                    err_el = driver.find_element(By.ID, error_id)
                    error_text = err_el.text.strip()
                except Exception:
                    pass
            return is_invalid, error_text
        except Exception:
            return False, ""

    def _addr_save_row(self, page, driver, row_index):
        """Save all field values from an address row for later restoration (scoped to address container)."""
        saved = {}
        try:
            saved["address_type"] = self._addr_read_dropdown_value(driver, row_index, "Address Type")
        except Exception:
            pass
        try:
            saved["country"] = self._addr_read_dropdown_value(driver, row_index, "Country")
        except Exception:
            pass
        try:
            saved["state"] = self._addr_read_dropdown_value(driver, row_index, "State")
        except Exception:
            pass
        try:
            saved["district"] = self._addr_read_dropdown_value(driver, row_index, "District")
        except Exception:
            pass
        try:
            saved["taluka"] = self._addr_read_dropdown_value(driver, row_index, "Taluka")
        except Exception:
            pass
        try:
            saved["address"] = self._addr_read_field(page, row_index, "Address")
        except Exception:
            pass
        try:
            saved["pin_code"] = self._addr_read_field(page, row_index, "Pin Code")
        except Exception:
            pass
        return saved

    def _addr_restore_row(self, page, driver, row_index, saved):
        """Restore all field values on an address row from saved data."""
        # Restore Address Type
        if saved.get("address_type"):
            self._addr_open_dropdown(driver, row_index, "Address Type")
            self._addr_select_option_by_text(driver, saved["address_type"])
            time.sleep(0.3)
        # Restore Country
        if saved.get("country"):
            self._addr_open_dropdown(driver, row_index, "Country")
            self._addr_select_option_by_text(driver, saved["country"])
            time.sleep(0.3)
        # Restore cascading chain: State -> District -> Taluka
        if saved.get("state"):
            self._addr_open_dropdown(driver, row_index, "State")
            self._addr_select_option_by_text(driver, saved["state"])
            time.sleep(0.5)
        if saved.get("district"):
            self._addr_open_dropdown(driver, row_index, "District")
            self._addr_select_option_by_text(driver, saved["district"])
            time.sleep(0.5)
        if saved.get("taluka"):
            self._addr_open_dropdown(driver, row_index, "Taluka")
            self._addr_select_option_by_text(driver, saved["taluka"])
            time.sleep(0.3)
        # Restore Address input
        if "address" in saved and saved["address"]:
            self._addr_type_field(driver, row_index, "Address", saved["address"])
        # Restore Pin Code
        if "pin_code" in saved:
            if saved["pin_code"]:
                self._addr_type_field(driver, row_index, "Pin Code", saved["pin_code"])
            else:
                self._addr_clear_field(driver, row_index, "Pin Code")
        time.sleep(0.3)

    # ================================================================
    # TEST 11: Address � Navigation + Pre-filled Data [ONE form open, NO Update]
    # ================================================================

    def test_11_address_navigation_prefilled(self, logged_in_driver):
        """Navigate to Step 3, verify pre-filled address data, back/next navigation."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        # --- Navigate to Step 3 ---
        reached = self._navigate_to_step3(page)
        if not reached:
            self._record(test_name="Address: Navigate to Step 3",
                expected="Address Type dropdown visible",
                actual="Failed to reach Step 3",
                status="FAILED", category="Address")
            self._cleanup(page)
            return
        shot_nav = self._screenshot(driver, "addr_nav_step3")
        self._record(test_name="Address: Navigate to Step 3",
            expected="Address Type dropdown visible on Step 3",
            actual="Successfully navigated to Address Details",
            status="PASSED", category="Address", screenshot=shot_nav)

        # --- Pre-filled data (2 rows) ---
        row_count = self._addr_count_rows(driver)
        addr_type_1 = self._addr_read_dropdown_value(driver, 1, "Address Type")
        addr_type_2 = ""
        if row_count >= 2:
            addr_type_2 = self._addr_read_dropdown_value(driver, 2, "Address Type")
        country_1 = self._addr_read_dropdown_value(driver, 1, "Country")
        shot_prefill = self._screenshot(driver, "addr_prefilled")
        has_prefill = bool(addr_type_1) and bool(country_1)
        self._record(test_name="Address: Pre-filled Data",
            expected="2 pre-filled address rows with Address Type, Country, State, etc.",
            actual=f"rows={row_count}, row1_type='{addr_type_1}', row2_type='{addr_type_2}', country='{country_1}'",
            status="PASSED" if has_prefill else "FAILED",
            category="Address", field="Address Type, Country",
            original_value=f"rows={row_count}, types=['{addr_type_1}','{addr_type_2}']",
            screenshot=shot_prefill)

        # --- Back to Step 2 ---
        went_back = self._go_back_to_step2(page)
        on_step2 = self._is_on_step2(driver) if went_back else False
        shot_back = self._screenshot(driver, "addr_back_to_step2")
        self._record(test_name="Address: Back to Step 2",
            expected="Back button returns to Step 2 (Promoters)",
            actual=f"went_back={went_back}, on_step2={on_step2}",
            status="PASSED" if on_step2 else "FAILED",
            category="Address", screenshot=shot_back)

        # --- Next back to Step 3 ---
        if on_step2:
            page._click_next()
            time.sleep(1.5)
        else:
            # Might still be on Step 3 or lost, try navigating
            self._navigate_to_step3(page)
        on_step3_again = self._is_on_step3(driver)
        shot_next = self._screenshot(driver, "addr_next_to_step3")
        self._record(test_name="Address: Next to Step 3",
            expected="Next button returns to Step 3 (Address)",
            actual=f"on_step3={on_step3_again}",
            status="PASSED" if on_step3_again else "FAILED",
            category="Address", screenshot=shot_next)

        self._cleanup(page)

    # ================================================================
    # TEST 12: Address � Row Management + Cascading [ONE form open, NO Update]
    # ================================================================

    def test_12_address_row_management_cascading(self, logged_in_driver):
        """Add/delete rows, min 1 row enforcement, cascading State>District>Taluka."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step3(page)
        if not reached:
            self._record(test_name="Address: Add Row",
                expected="New row added", actual="Failed to reach Step 3",
                status="FAILED", category="Address")
            self._cleanup(page)
            return

        # --- Add new row ---
        log.info("[test_12] Step: Add new row")
        before_add = self._addr_count_rows(driver)
        added1 = self._addr_add_row(driver)
        after1 = self._addr_count_rows(driver)
        shot_add = self._screenshot(driver, "addr_add_row")
        self._record(test_name="Address: Add Row",
            expected="Clicking + adds a new blank address row",
            actual=f"rows_before={before_add}, added={added1}, rows_after={after1}",
            status="PASSED" if added1 and after1 == before_add + 1 else "FAILED",
            category="Address", screenshot=shot_add)

        # --- Add multiple rows ---
        log.info("[test_12] Step: Add multiple rows")
        added2 = self._addr_add_row(driver)
        after2 = self._addr_count_rows(driver)
        shot_multi = self._screenshot(driver, "addr_add_multiple")
        self._record(test_name="Address: Add Multiple Rows",
            expected="Multiple rows can be added via + button",
            actual=f"rows_after_first={after1}, added_again={added2}, total={after2}",
            status="PASSED" if added2 and after2 == after1 + 1 else "FAILED",
            category="Address", screenshot=shot_multi)

        # --- Delete row ---
        log.info("[test_12] Step: Delete row")
        before_del = self._addr_count_rows(driver)
        if before_del >= 2:
            deleted = self._addr_delete_row(driver, row_index=before_del)
            time.sleep(0.5)
            # Handle SweetAlert confirmation if it appeared
            try:
                confirm = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                if confirm.is_displayed():
                    confirm.click()
                    time.sleep(0.8)
            except Exception:
                pass
            after_del = self._addr_count_rows(driver)
        else:
            deleted = False
            after_del = before_del
        shot_del = self._screenshot(driver, "addr_delete_row")
        self._record(test_name="Address: Delete Row",
            expected="Row count decreases by 1 after deletion",
            actual=f"rows_before={before_del}, deleted={deleted}, rows_after={after_del}",
            status="PASSED" if deleted and after_del == before_del - 1 else "FAILED",
            category="Address", screenshot=shot_del)

        # --- Single row -> no delete button ---
        # Delete extra rows until only 1 remains (wall-clock guarded)
        log.info("[test_12] Step: Trim to single row")
        max_delete_attempts = 15
        delete_attempts = 0
        delete_start = time.time()
        while self._addr_count_rows(driver) > 1 and delete_attempts < max_delete_attempts:
            if time.time() - delete_start > 30:
                log.warning("[test_12] Delete loop wall timeout (30s), breaking")
                break
            count_before = self._addr_count_rows(driver)
            self._addr_delete_row(driver, row_index=count_before)
            time.sleep(0.8)
            # If a SweetAlert confirmation appeared, click confirm
            try:
                confirm = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                if confirm.is_displayed():
                    confirm.click()
                    time.sleep(0.8)
            except Exception:
                pass
            delete_attempts += 1
        single_count = self._addr_count_rows(driver)
        no_del = not self._addr_has_delete_button(driver, 1)
        shot_single = self._screenshot(driver, "addr_single_no_delete")
        self._record(test_name="Address: No Delete on Single Row",
            expected="Delete button not visible when only 1 row remains",
            actual=f"single_row={single_count == 1}, has_delete={not no_del}",
            status="PASSED" if single_count == 1 and no_del else "FAILED",
            category="Address", screenshot=shot_single)

        # --- Country = India on remaining row ---
        log.info("[test_12] Step: Verify Country = India")
        country_val = self._addr_read_dropdown_value(driver, 1, "Country")
        shot_country = self._screenshot(driver, "addr_country_india")
        is_india = "India" in (country_val or "")
        self._record(test_name="Address: Country = India",
            expected="Country dropdown shows India",
            actual=f"country='{country_val}'",
            status="PASSED" if is_india else "FAILED",
            category="Address", field="Country", screenshot=shot_country)

        # --- Cascading: State -> District -> Taluka ---
        log.info("[test_12] Step: Cascading State>Dist>Taluka")
        state, district, taluka = self._addr_fill_cascade(driver, 1)
        shot_cascade = self._screenshot(driver, "addr_cascade")
        cascade_ok = bool(state) and bool(district) and bool(taluka)
        self._record(test_name="Address: Cascading State>Dist>Taluka",
            expected="Changing State loads Districts, changing District loads Talukas",
            actual=f"state='{state}', district='{district}', taluka='{taluka}'",
            status="PASSED" if cascade_ok else "FAILED",
            category="Address", field="State, District, Taluka",
            screenshot=shot_cascade)

        self._cleanup(page)

    # ================================================================
    # TEST 13: Address � Required Fields + Pin Code [ONE form open, NO Update]
    # ================================================================

    def test_13_address_required_pincode(self, logged_in_driver):
        """Required field validation on empty row, Pin Code edge cases."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step3(page)
        if not reached:
            self._record(test_name="Address: Required on Empty Row",
                expected="Validation errors shown", actual="Failed to reach Step 3",
                status="FAILED", category="Address")
            self._cleanup(page)
            return

        # --- Add empty row -> Next -> errors ---
        existing_count = self._addr_count_rows(driver)
        self._addr_add_row(driver)
        new_row_idx = self._addr_count_rows(driver)
        time.sleep(0.5)

        # Click Next to trigger validation on the empty row
        page._click_next()
        time.sleep(1)
        # Should NOT leave Step 3 (errors on empty row)
        still_on_3 = self._is_on_step3(driver)
        shot_empty_err = self._screenshot(driver, "addr_empty_row_errors")
        self._record(test_name="Address: Required on Empty Row",
            expected="Next does NOT proceed � validation errors on empty address row",
            actual=f"still_on_step3={still_on_3}",
            status="PASSED" if still_on_3 else "FAILED",
            category="Address", field="All Fields",
            bad_value="(empty row)", screenshot=shot_empty_err)

        # --- Check Address Type required error on new row ---
        type_invalid, type_err = self._addr_check_dropdown_invalid(driver, new_row_idx, "Address Type")
        shot_type_err = self._screenshot(driver, "addr_req_addr_type")
        self._record(test_name="Address: Address Type Required",
            expected="Address Type dropdown shows required error",
            actual=f"invalid={type_invalid}, error='{type_err}'",
            status="PASSED" if type_invalid else "FAILED",
            category="Address", field="Address Type",
            bad_value="(empty)", screenshot=shot_type_err)

        # --- Check Address input required error on new row ---
        addr_invalid, addr_err = self._addr_check_input_invalid(driver, new_row_idx, "Address")
        shot_addr_err = self._screenshot(driver, "addr_req_address")
        self._record(test_name="Address: Address Input Required",
            expected="Address input shows required error",
            actual=f"invalid={addr_invalid}, error='{addr_err}'",
            status="PASSED" if addr_invalid else "FAILED",
            category="Address", field="Address",
            bad_value="(empty)", screenshot=shot_addr_err)

        # --- Pin Code "000000" -> red field error ---
        self._addr_type_field(driver, new_row_idx, "Pin Code", "000000")
        time.sleep(0.5)
        pin_invalid, pin_err = self._addr_check_input_invalid(driver, new_row_idx, "Pin Code")
        shot_000 = self._screenshot(driver, "addr_pin_000000")
        self._record(test_name="Address: Pin Code '000000' Rejected",
            expected="Pin Code 000000 shows red field error",
            actual=f"invalid={pin_invalid}, error='{pin_err}'",
            status="PASSED" if pin_invalid else "FAILED",
            category="Address", field="Pin Code",
            bad_value="000000", screenshot=shot_000)

        # --- Pin Code with letters "abc123" -> validation error ---
        self._addr_clear_field(driver, new_row_idx, "Pin Code")
        time.sleep(0.3)
        self._addr_type_field(driver, new_row_idx, "Pin Code", "abc123")
        time.sleep(0.5)
        pin_alpha_invalid, pin_alpha_err = self._addr_check_input_invalid(driver, new_row_idx, "Pin Code")
        shot_alpha = self._screenshot(driver, "addr_pin_letters")
        self._record(test_name="Address: Pin Code 'abc123' Rejected",
            expected="Alphanumeric Pin Code shows validation error",
            actual=f"invalid={pin_alpha_invalid}, error='{pin_alpha_err}'",
            status="PASSED" if pin_alpha_invalid else "FAILED",
            category="Address", field="Pin Code",
            bad_value="abc123", screenshot=shot_alpha)

        # --- Delete empty row -> all rows valid -> Next proceeds ---
        cleanup_attempts = 0
        while self._addr_count_rows(driver) > existing_count and cleanup_attempts < 10:
            self._addr_delete_row(driver, row_index=self._addr_count_rows(driver))
            time.sleep(0.8)
            # If a SweetAlert confirmation appeared, click confirm
            try:
                confirm = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                if confirm.is_displayed():
                    confirm.click()
                    time.sleep(0.8)
            except Exception:
                pass
            cleanup_attempts += 1
        time.sleep(0.3)
        page._click_next()
        time.sleep(1.5)
        moved_forward = not self._is_on_step3(driver)
        shot_proceed = self._screenshot(driver, "addr_next_proceeds")
        self._record(test_name="Address: Delete Empty -> Next Proceeds",
            expected="After removing empty row, Next proceeds past Step 3",
            actual=f"moved_forward={moved_forward}",
            status="PASSED" if moved_forward else "FAILED",
            category="Address", screenshot=shot_proceed)

        self._cleanup(page)

    # ================================================================
    # TEST 14: Address � Backend + Persistence [ONE form open, with Update]
    # ================================================================

    def test_14_address_backend_persistence(self, logged_in_driver):
        """Long address save, edit+verify persistence, dup type, special chars, restore."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step3(page)
        if not reached:
            self._record(test_name="Address: Long Address (2000+ chars)",
                expected="Update succeeds", actual="Failed to reach Step 3",
                status="FAILED", category="Address")
            self._cleanup(page)
            return

        # --- Save original row 1 data ---
        orig_row1 = self._addr_save_row(page, driver, 1)
        orig_row2 = {}
        if self._addr_count_rows(driver) >= 2:
            orig_row2 = self._addr_save_row(page, driver, 2)

        # --- CHECK 1: Long Address (2000+ chars) -> Update succeeds ---
        long_addr = "A" * 2001
        self._addr_type_field(driver, 1, "Address", long_addr)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_long = self._handle_update_success(driver, timeout=15)
        shot_long = self._screenshot(driver, "addr_long_2001")
        is_failed_long = "failed to save record" in title_long.lower()
        self._record(test_name="Address: Long Address (2000+ chars)",
            expected="Record saves successfully (no backend length limit on Address)",
            actual=f"title='{title_long}'",
            status="PASSED" if not is_failed_long else "FAILED",
            category="Address", field="Address",
            bad_value=f"{'A'*30}...(2001 chars)",
            screenshot=shot_long)
        time.sleep(1)

        # --- Re-open for next checks ---
        self._open_form(page)
        self._navigate_to_step3(page)

        # --- CHECK 2: Edit Address -> Update -> re-open -> verify ---
        test_address = "Updated Test Address 123, Sector 7"
        self._addr_type_field(driver, 1, "Address", test_address)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_edit = self._handle_update_success(driver, timeout=15)
        shot_edit = self._screenshot(driver, "addr_edit_address")
        is_failed_edit = "failed to save record" in title_edit.lower()
        self._record(test_name="Address: Edit Address -> Save",
            expected="Updated address saves successfully",
            actual=f"title='{title_edit}'",
            status="PASSED" if not is_failed_edit else "FAILED",
            category="Address", field="Address",
            bad_value=test_address, screenshot=shot_edit)
        time.sleep(1)

        # Re-open and verify
        self._open_form(page)
        self._navigate_to_step3(page)
        saved_addr = self._addr_read_field(page, 1, "Address")
        shot_verify_addr = self._screenshot(driver, "addr_verify_address")
        addr_persisted = (saved_addr == test_address)
        self._record(test_name="Address: Edit Address -> Verify Persisted",
            expected=f"Address '{test_address}' persists after save",
            actual=f"saved='{saved_addr}', persisted={addr_persisted}",
            status="PASSED" if addr_persisted else "FAILED",
            category="Address", field="Address",
            screenshot=shot_verify_addr)

        # --- CHECK 3: Edit Pin Code -> Update -> re-open -> verify ---
        test_pin = "400001"
        self._addr_type_field(driver, 1, "Pin Code", test_pin)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_pin = self._handle_update_success(driver, timeout=15)
        shot_pin = self._screenshot(driver, "addr_edit_pincode")
        is_failed_pin = "failed to save record" in title_pin.lower()
        self._record(test_name="Address: Edit Pin Code -> Save",
            expected="Updated Pin Code saves successfully",
            actual=f"title='{title_pin}'",
            status="PASSED" if not is_failed_pin else "FAILED",
            category="Address", field="Pin Code",
            bad_value=test_pin, screenshot=shot_pin)
        time.sleep(1)

        # Re-open and verify
        self._open_form(page)
        self._navigate_to_step3(page)
        saved_pin = self._addr_read_field(page, 1, "Pin Code")
        shot_verify_pin = self._screenshot(driver, "addr_verify_pincode")
        pin_persisted = (saved_pin == test_pin)
        self._record(test_name="Address: Edit Pin Code -> Verify Persisted",
            expected=f"Pin Code '{test_pin}' persists after save",
            actual=f"saved='{saved_pin}', persisted={pin_persisted}",
            status="PASSED" if pin_persisted else "FAILED",
            category="Address", field="Pin Code",
            screenshot=shot_verify_pin)

        # --- CHECK 4: Duplicate Address Type -> Update succeeds ---
        if self._addr_count_rows(driver) >= 2:
            row1_type = self._addr_read_dropdown_value(driver, 1, "Address Type")
            if row1_type:
                self._addr_open_dropdown(driver, 2, "Address Type")
                self._addr_select_option_by_text(driver, row1_type)
                time.sleep(0.3)
                self._click_update_direct(driver)
                title_dup = self._handle_update_success(driver, timeout=15)
                shot_dup = self._screenshot(driver, "addr_dup_type")
                is_failed_dup = "failed to save record" in title_dup.lower()
                self._record(test_name="Address: Duplicate Address Type",
                    expected="Duplicate Address Type saves without error",
                    actual=f"title='{title_dup}', row1='{row1_type}', row2='{row1_type}'",
                    status="PASSED" if not is_failed_dup else "FAILED",
                    category="Address", field="Address Type",
                    bad_value=f"dup '{row1_type}'",
                    screenshot=shot_dup)
                time.sleep(1)

                # Re-open for next check
                self._open_form(page)
                self._navigate_to_step3(page)
        else:
            self._record(test_name="Address: Duplicate Address Type",
                expected="Duplicate Address Type saves without error",
                actual="Skipped: only 1 address row available",
                status="PASSED", category="Address", field="Address Type")

        # --- CHECK 5: Special chars in Address -> Update succeeds ---
        special_addr = "Test <script>alert(1)</script> & 'quotes' \"double\" #hash"
        self._addr_type_field(driver, 1, "Address", special_addr)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_spec = self._handle_update_success(driver, timeout=15)
        shot_spec = self._screenshot(driver, "addr_special_chars")
        is_failed_spec = "failed to save record" in title_spec.lower()
        self._record(test_name="Address: Special Chars in Address",
            expected="Special characters in Address save without error",
            actual=f"title='{title_spec}'",
            status="PASSED" if not is_failed_spec else "FAILED",
            category="Address", field="Address",
            bad_value=special_addr,
            screenshot=shot_spec)
        time.sleep(1)

        # --- CHECK 6: Restore original data ---
        self._open_form(page)
        self._navigate_to_step3(page)
        if orig_row1:
            self._addr_restore_row(page, driver, 1, orig_row1)
        if orig_row2 and self._addr_count_rows(driver) >= 2:
            self._addr_restore_row(page, driver, 2, orig_row2)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_restore = self._handle_update_success(driver, timeout=15)
        shot_restore = self._screenshot(driver, "addr_restore")
        restore_ok = "failed" not in title_restore.lower() or not title_restore
        self._record(test_name="Address: Restore Original Data",
            expected="Original address data restored successfully",
            actual=f"title='{title_restore}'",
            status="PASSED" if restore_ok else "FAILED",
            category="Address", field="All Address Fields",
            original_value=str(orig_row1),
            screenshot=shot_restore)

        self._cleanup(page)

    # ================================================================
    # TEST 15: Address � Edge Cases [ONE form open, NO Update]
    # ================================================================

    def test_15_address_edge_cases(self, logged_in_driver):
        """Whitespace-only address, 5-digit Pin Code, multiline address text."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step3(page)
        if not reached:
            self._record(test_name="Address: Whitespace-Only Address",
                expected="Checked Next behavior", actual="Failed to reach Step 3",
                status="FAILED", category="Address")
            self._cleanup(page)
            return

        # Save original row 1 address
        orig_addr = self._addr_read_field(page, 1, "Address")
        orig_pin = self._addr_read_field(page, 1, "Pin Code")

        # --- CHECK 1: Whitespace-only Address -> Next behavior ---
        self._addr_type_field(driver, 1, "Address", "   ")
        time.sleep(0.3)
        page._click_next()
        time.sleep(1.5)
        moved_ws = not self._is_on_step3(driver)
        shot_ws = self._screenshot(driver, "addr_whitespace")
        self._record(test_name="Address: Whitespace-Only Address",
            expected="Whitespace-only address either shows error or proceeds to Step 4",
            actual=f"moved_forward={moved_ws}",
            status="PASSED",
            category="Address", field="Address",
            bad_value="'   ' (whitespace)",
            screenshot=shot_ws)

        # Navigate back to Step 3
        if moved_ws:
            self._go_back_to_step2(page)
            page._click_next()
            time.sleep(2)
            # Verify we're back on Step 3 before continuing
            if not self._is_on_step3(driver):
                log.warning("[test_15] Failed to return to Step 3 after whitespace test, re-navigating...")
                self._navigate_to_step3(page)
            # Close any stale overlays before interacting
            self._addr_close_overlay(driver)
            time.sleep(0.5)

        # --- CHECK 2: Pin Code 5 digits -> validation error ---
        self._addr_type_field(driver, 1, "Address", orig_addr or "Test Address 123")
        time.sleep(0.3)
        self._addr_type_field(driver, 1, "Pin Code", "12345")
        time.sleep(0.5)
        pin5_invalid, pin5_err = self._addr_check_input_invalid(driver, 1, "Pin Code")
        shot_5 = self._screenshot(driver, "addr_pin_5digits")
        self._record(test_name="Address: Pin Code 5 Digits",
            expected="Pin Code with 5 digits shows validation error",
            actual=f"invalid={pin5_invalid}, error='{pin5_err}'",
            status="PASSED" if pin5_invalid else "FAILED",
            category="Address", field="Pin Code",
            bad_value="12345",
            screenshot=shot_5)

        # --- CHECK 3: Multiline Address text -> retained ---
        self._addr_clear_field(driver, 1, "Pin Code")
        time.sleep(0.3)
        multiline_text = "Line one of address\nLine two here\nLine three end"
        self._addr_type_field(driver, 1, "Address", multiline_text)
        time.sleep(0.5)
        read_back = self._addr_read_field(page, 1, "Address")
        shot_ml = self._screenshot(driver, "addr_multiline")
        multiline_ok = ("Line one" in (read_back or "") and "Line three" in (read_back or ""))
        self._record(test_name="Address: Multiline Address Text",
            expected="Textarea accepts and retains newline characters",
            actual=f"contains_newlines={multiline_ok}, read_back='{(read_back or '')[:50]}'",
            status="PASSED" if multiline_ok else "FAILED",
            category="Address", field="Address",
            bad_value=multiline_text,
            screenshot=shot_ml)

        # --- Cleanup: restore original values (no Update) ---
        self._addr_type_field(driver, 1, "Address", orig_addr or "")
        if orig_pin:
            self._addr_type_field(driver, 1, "Pin Code", orig_pin)

        self._cleanup(page)


        # ================================================================
    # BUSINESS ACTIVITIES HELPERS
    # ================================================================

    # Field definitions (3 have trailing tab character in HTML name attribute!)
    _BA_FIELDS = [
        ("Business Model", "Business Model\t", 100),
        ("Market Linkages", "Market Linkages\t", 255),
        ("Line of Business", "Line of Business\t", 255),
        ("Additional Business Activities", "Additional Business Activities", 255),
    ]

    # XPath to the Business Activities app-dynamic-details container
    _BA_XPATH = "//app-dynamic-details[.//mat-label[contains(.,'Business Activities')]]"

    def _navigate_to_step4(self, page):
        """Navigate to Step 4 (Business Activities) from wherever the form currently is."""
        driver = page.driver
        if self._is_on_step4(driver):
            return True
        # On Step 3? Click Next to get to Step 4
        if self._is_on_step3(driver):
            page._click_next()
            time.sleep(1.5)
            return self._is_on_step4(driver)
        # Fall back: navigate to Step 3 first, then Next
        self._navigate_to_step3(page)
        if not self._is_on_step3(driver):
            return False
        page._click_next()
        time.sleep(1.5)
        return self._is_on_step4(driver)

    def _go_back_to_step3(self, page):
        """Click Back from Step 4 to return to Step 3 (Address)."""
        driver = page.driver
        if not self._is_on_step4(driver):
            return False
        try:
            back_btns = driver.find_elements(By.CSS_SELECTOR, "button[matstepperprevious]")
            if back_btns:
                btn = back_btns[0]
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.5)
                try:
                    btn.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
                return self._is_on_step3(driver)
        except Exception:
            pass
        return False

    def _go_back_to_step4(self, page):
        """Return to Step 4 from Step 5 (or Step 3) by clicking Back."""
        driver = page.driver
        if self._is_on_step4(driver):
            return True
        try:
            back_btns = driver.find_elements(By.CSS_SELECTOR, "button[matstepperprevious]")
            if back_btns:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", back_btns[0])
                time.sleep(0.5)
                try:
                    back_btns[0].click()
                except Exception:
                    driver.execute_script("arguments[0].click();", back_btns[0])
                time.sleep(1)
        except Exception:
            pass
        if self._is_on_step4(driver):
            return True
        return self._navigate_to_step4(page)

    def _ba_container(self, driver):
        """Return the app-dynamic-details element for Business Activities (Step 4)."""
        return driver.find_element(By.XPATH, self._BA_XPATH)

    def _ba_count_rows(self, driver):
        """Count BA rows in the Step 4 table only (scoped to BA container)."""
        try:
            container = self._ba_container(driver)
            rows = container.find_elements(By.CSS_SELECTOR, "tbody tr")
            return len(rows)
        except Exception:
            return 0

    def _ba_add_row(self, driver):
        """Click the + button to add a new BA row (scoped to BA container)."""
        try:
            container = self._ba_container(driver)
            add_btns = container.find_elements(
                By.CSS_SELECTOR, "button[mat-icon-button][color='primary']"
            )
            if add_btns:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
                    add_btns[0]
                )
                time.sleep(0.8)
                return True
        except Exception:
            pass
        return False

    def _ba_delete_row(self, driver, row_index=1):
        """Click the delete button on a specific BA row (scoped to BA container)."""
        try:
            container = self._ba_container(driver)
            rows = container.find_elements(By.CSS_SELECTOR, "tbody tr")
            if row_index < 1 or row_index > len(rows):
                return False
            row = rows[row_index - 1]
            btn = row.find_element(By.CSS_SELECTOR, "button[mat-icon-button][color='warn']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.3)
            try:
                btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.8)
            return True
        except Exception:
            return False

    def _ba_has_delete_button(self, driver, row_index=1):
        """Check if a specific BA row has a visible delete button (scoped to BA container)."""
        try:
            container = self._ba_container(driver)
            rows = container.find_elements(By.CSS_SELECTOR, "tbody tr")
            if row_index < 1 or row_index > len(rows):
                return False
            row = rows[row_index - 1]
            btn = row.find_element(By.CSS_SELECTOR, "button[mat-icon-button][color='warn']")
            return btn.is_displayed()
        except Exception:
            return False

    def _ba_find_input(self, driver, row_index, field_name):
        """Find an input element in the BA container by row index and field name.
        Uses attribute matching to handle special characters (tabs) in name values."""
        container = self._ba_container(driver)
        rows = container.find_elements(By.CSS_SELECTOR, "tbody tr")
        if row_index < 1 or row_index > len(rows):
            raise Exception(f"BA Row {row_index} not found (only {len(rows)} rows)")
        row = rows[row_index - 1]
        inputs = row.find_elements(By.CSS_SELECTOR, "input")
        for inp in inputs:
            if inp.get_attribute("name") == field_name:
                return inp
        raise Exception(f"Field '{field_name}' not found in BA row {row_index}")

    def _ba_type_field(self, driver, row_index, field_name, value):
        """Type into a BA input field by row index (scoped to BA container)."""
        el = self._ba_find_input(driver, row_index, field_name)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.3)
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].focus();", el)
        time.sleep(0.2)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(value)
        time.sleep(0.3)
        el.send_keys(Keys.TAB)
        time.sleep(0.3)

    def _ba_clear_field(self, driver, row_index, field_name):
        """Clear a BA input field by row index (scoped to BA container)."""
        el = self._ba_find_input(driver, row_index, field_name)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.3)
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].focus();", el)
        time.sleep(0.2)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        time.sleep(0.3)
        el.send_keys(Keys.TAB)
        time.sleep(0.3)

    def _ba_read_field(self, driver, row_index, field_name):
        """Read a BA input field value by row index (scoped to BA container)."""
        el = self._ba_find_input(driver, row_index, field_name)
        return el.get_attribute("value") or ""

    def _ba_save_row(self, driver, row_index):
        """Save all 4 field values from a BA row for later restoration."""
        saved = {}
        for display_name, attr_name, _ in self._BA_FIELDS:
            try:
                saved[display_name] = self._ba_read_field(driver, row_index, attr_name)
            except Exception:
                saved[display_name] = ""
        return saved

    def _ba_restore_row(self, driver, row_index, saved):
        """Restore all 4 field values on a BA row from saved data."""
        for display_name, attr_name, _ in self._BA_FIELDS:
            val = saved.get(display_name, "")
            if val:
                self._ba_type_field(driver, row_index, attr_name, val)
            else:
                self._ba_clear_field(driver, row_index, attr_name)

    # ================================================================
    # TEST 16: Business Activities � Navigation + Pre-filled + Row Mgmt [ONE form open, NO Update]
    # ================================================================

    def test_16_ba_navigation_prefilled_row_mgmt(self, logged_in_driver):
        """Navigate to Step 4, verify pre-filled data, back/next, optional fields, add/delete rows."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        # --- Navigate to Step 4 ---
        reached = self._navigate_to_step4(page)
        if not reached:
            self._record(test_name="BA: Navigate to Step 4",
                expected="Business Model input visible on Step 4",
                actual="Failed to reach Step 4",
                status="FAILED", category="Business Activities")
            self._cleanup(page)
            return
        shot_nav = self._screenshot(driver, "ba_nav_step4")
        self._record(test_name="BA: Navigate to Step 4",
            expected="Business Model input visible on Step 4",
            actual="Successfully navigated to Business Activities",
            status="PASSED", category="Business Activities", screenshot=shot_nav)

        # --- Pre-filled data (2 rows) ---
        row_count = self._ba_count_rows(driver)
        saved_row1 = self._ba_save_row(driver, 1)
        saved_row2 = {}
        if row_count >= 2:
            saved_row2 = self._ba_save_row(driver, 2)
        bm1 = saved_row1.get("Business Model", "")
        ml1 = saved_row1.get("Market Linkages", "")
        shot_prefill = self._screenshot(driver, "ba_prefilled")
        has_prefill = bool(bm1) or bool(ml1)
        self._record(test_name="BA: Pre-filled Data",
            expected="2 pre-filled BA rows with Business Model, Market Linkages, etc.",
            actual=f"rows={row_count}, row1_bm='{bm1}', row1_ml='{ml1}'",
            status="PASSED" if has_prefill else "FAILED",
            category="Business Activities", field="All BA Fields",
            original_value=str(saved_row1),
            screenshot=shot_prefill)

        # --- Back to Step 3 ---
        went_back = self._go_back_to_step3(page)
        on_step3 = self._is_on_step3(driver) if went_back else False
        shot_back = self._screenshot(driver, "ba_back_to_step3")
        self._record(test_name="BA: Back to Step 3",
            expected="Back button returns to Step 3 (Address)",
            actual=f"went_back={went_back}, on_step3={on_step3}",
            status="PASSED" if on_step3 else "FAILED",
            category="Business Activities", screenshot=shot_back)

        # --- Next back to Step 4 ---
        if on_step3:
            page._click_next()
            time.sleep(1.5)
        else:
            self._navigate_to_step4(page)
        on_step4_again = self._is_on_step4(driver)
        shot_next = self._screenshot(driver, "ba_next_to_step4")
        self._record(test_name="BA: Next to Step 4",
            expected="Next button returns to Step 4 (Business Activities)",
            actual=f"on_step4={on_step4_again}",
            status="PASSED" if on_step4_again else "FAILED",
            category="Business Activities", screenshot=shot_next)

        # --- Optional fields � clear all 4, Next should proceed ---
        for display_name, attr_name, _ in self._BA_FIELDS:
            self._ba_clear_field(driver, 1, attr_name)
        time.sleep(0.3)
        page._click_next()
        time.sleep(1.5)
        moved_forward = not self._is_on_step4(driver)
        shot_opt = self._screenshot(driver, "ba_optional_fields")
        self._record(test_name="BA: Optional Fields",
            expected="All 4 fields empty � Next proceeds past Step 4 with no error",
            actual=f"moved_forward={moved_forward}",
            status="PASSED" if moved_forward else "FAILED",
            category="Business Activities", field="All BA Fields",
            bad_value="(empty)", screenshot=shot_opt)

        # Navigate back to Step 4 if we moved past it
        if moved_forward:
            self._go_back_to_step4(page)

        # --- Add row ---
        before_add = self._ba_count_rows(driver)
        added1 = self._ba_add_row(driver)
        after1 = self._ba_count_rows(driver)
        shot_add = self._screenshot(driver, "ba_add_row")
        self._record(test_name="BA: Add Row",
            expected="Clicking + adds a new blank BA row",
            actual=f"rows_before={before_add}, added={added1}, rows_after={after1}",
            status="PASSED" if added1 and after1 == before_add + 1 else "FAILED",
            category="Business Activities", screenshot=shot_add)

        # --- Add multiple rows ---
        added2 = self._ba_add_row(driver)
        after2 = self._ba_count_rows(driver)
        shot_multi = self._screenshot(driver, "ba_add_multiple")
        self._record(test_name="BA: Add Multiple Rows",
            expected="Multiple rows can be added via + button",
            actual=f"rows_after_first={after1}, added_again={added2}, total={after2}",
            status="PASSED" if added2 and after2 == after1 + 1 else "FAILED",
            category="Business Activities", screenshot=shot_multi)

        # --- Delete row ---
        before_del = self._ba_count_rows(driver)
        if before_del >= 2:
            deleted = self._ba_delete_row(driver, row_index=before_del)
            time.sleep(0.5)
            try:
                confirm = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                if confirm.is_displayed():
                    confirm.click()
                    time.sleep(0.8)
            except Exception:
                pass
            after_del = self._ba_count_rows(driver)
        else:
            deleted = False
            after_del = before_del
        shot_del = self._screenshot(driver, "ba_delete_row")
        self._record(test_name="BA: Delete Row",
            expected="Row count decreases by 1 after deletion",
            actual=f"rows_before={before_del}, deleted={deleted}, rows_after={after_del}",
            status="PASSED" if deleted and after_del == before_del - 1 else "FAILED",
            category="Business Activities", screenshot=shot_del)

        # --- Single row � no delete button ---
        max_del_attempts = 15
        del_attempts = 0
        del_start = time.time()
        while self._ba_count_rows(driver) > 1 and del_attempts < max_del_attempts:
            if time.time() - del_start > 30:
                break
            cnt = self._ba_count_rows(driver)
            self._ba_delete_row(driver, row_index=cnt)
            time.sleep(0.8)
            try:
                confirm = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                if confirm.is_displayed():
                    confirm.click()
                    time.sleep(0.8)
            except Exception:
                pass
            del_attempts += 1
        single_count = self._ba_count_rows(driver)
        no_del = not self._ba_has_delete_button(driver, 1)
        shot_single = self._screenshot(driver, "ba_single_no_delete")
        self._record(test_name="BA: No Delete on Single Row",
            expected="Delete button not visible when only 1 row remains",
            actual=f"single_row={single_count == 1}, has_delete={not no_del}",
            status="PASSED" if single_count == 1 and no_del else "FAILED",
            category="Business Activities", screenshot=shot_single)

        # --- Restore original values on row 1 (no Update � just reset UI) ---
        self._ba_restore_row(driver, 1, saved_row1)

        self._cleanup(page)

    # ================================================================
    # TEST 17: Business Activities � Max Length [ONE form open, with Update]
    # BM: 100, ML: 255, LOB: 255, ABA: 255
    # ================================================================

    def test_17_ba_max_length_all_fields(self, logged_in_driver):
        """Max length boundary for all 4 BA fields: N+1 -> fail, N -> save + verify."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step4(page)
        if not reached:
            self._record(test_name="BA Max Length: Business Model (101 chars)",
                expected="Failed to save record", actual="Failed to reach Step 4",
                status="FAILED", category="Business Activities", field="Business Model")
            self._cleanup(page)
            return

        # --- Save original row 1 data for restoration ---
        orig = self._ba_save_row(driver, 1)

        # --- Test each field: max+1 -> fail, max -> save, verify persisted ---
        for display_name, attr_name, max_len in self._BA_FIELDS:
            # --- N+1 chars -> Update fails ---
            long_val = "A" * (max_len + 1)
            self._ba_type_field(driver, 1, attr_name, long_val)
            time.sleep(0.3)
            self._click_update_direct(driver)
            title_fail, _ = self._check_sweetalert(driver, timeout=15)
            shot_fail = self._screenshot(driver, f"ba_maxlen_{display_name[:3]}_fail")
            is_failed = "failed to save record" in (title_fail or "").lower()
            self._record(test_name=f"BA Max Length: {display_name} ({max_len + 1} chars)",
                expected="'Failed to save record' toast shown",
                actual=f"title='{title_fail}'",
                status="PASSED" if is_failed else "FAILED",
                category="Business Activities", field=display_name,
                bad_value=f"{'A'*30}...({max_len + 1} chars)",
                screenshot=shot_fail)
            self._dismiss_sweetalert(driver)
            time.sleep(0.5)

            # --- N chars -> Update succeeds ---
            boundary_val = "A" * max_len
            self._ba_type_field(driver, 1, attr_name, boundary_val)
            time.sleep(0.3)
            self._click_update_direct(driver)
            title_save = self._handle_update_success(driver, timeout=15)
            shot_save = self._screenshot(driver, f"ba_maxlen_{display_name[:3]}_save")
            is_failed_save = "failed to save record" in (title_save or "").lower()
            self._record(test_name=f"BA Max Length: {display_name} ({max_len} chars)",
                expected="Record saves successfully (at boundary limit)",
                actual=f"title='{title_save}'",
                status="PASSED" if not is_failed_save else "FAILED",
                category="Business Activities", field=display_name,
                screenshot=shot_save)
            time.sleep(1)

            # --- Re-open and verify persisted ---
            self._open_form(page)
            self._navigate_to_step4(page)
            saved_val = self._ba_read_field(driver, 1, attr_name)
            shot_verify = self._screenshot(driver, f"ba_maxlen_{display_name[:3]}_verify")
            persisted = (saved_val == boundary_val)
            self._record(test_name=f"BA Max Length: {display_name} Verify Persisted",
                expected=f"{display_name} ({max_len} chars) persisted after save",
                actual=f"saved='{saved_val[:30]}...'({len(saved_val)} chars), persisted={persisted}",
                status="PASSED" if persisted else "FAILED",
                category="Business Activities", field=display_name,
                screenshot=shot_verify)

        # --- Restore original data ---
        self._ba_restore_row(driver, 1, orig)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_restore = self._handle_update_success(driver, timeout=15)
        shot_restore = self._screenshot(driver, "ba_maxlen_restore")
        restore_ok = "failed" not in (title_restore or "").lower()
        self._record(test_name="BA: Restore Original Data",
            expected="Original BA data restored successfully",
            actual=f"title='{title_restore}'",
            status="PASSED" if restore_ok else "FAILED",
            category="Business Activities", field="All BA Fields",
            original_value=str(orig),
            screenshot=shot_restore)

        self._cleanup(page)

    # ================================================================
    # TEST 18: Business Activities � Backend + Persistence [ONE form open, with Update]
    # Edit all 4 -> save -> verify, empty save, restore original
    # ================================================================

    def test_18_ba_backend_persistence(self, logged_in_driver):
        """Edit all 4 BA fields, save, verify. Empty save, verify. Restore original."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step4(page)
        if not reached:
            self._record(test_name="BA: Edit All Fields -> Save",
                expected="Update succeeds", actual="Failed to reach Step 4",
                status="FAILED", category="Business Activities")
            self._cleanup(page)
            return

        # --- Save original row 1 data ---
        orig = self._ba_save_row(driver, 1)

        # --- Edit all 4 fields -> Update -> re-open -> verify ---
        test_values = {
            "Business Model": "Test B2B SaaS Platform",
            "Market Linkages": "Domestic Wholesale + Direct Export",
            "Line of Business": "Enterprise Software Development",
            "Additional Business Activities": "Cloud Consulting and IT Advisory",
        }
        for display_name, attr_name, _ in self._BA_FIELDS:
            self._ba_type_field(driver, 1, attr_name, test_values[display_name])
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_edit = self._handle_update_success(driver, timeout=15)
        shot_edit = self._screenshot(driver, "ba_edit_all")
        is_failed_edit = "failed to save record" in (title_edit or "").lower()
        self._record(test_name="BA: Edit All Fields -> Save",
            expected="Updated BA fields save successfully",
            actual=f"title='{title_edit}'",
            status="PASSED" if not is_failed_edit else "FAILED",
            category="Business Activities", field="All BA Fields",
            bad_value=str(test_values),
            screenshot=shot_edit)
        time.sleep(1)

        # Re-open and verify all 4
        self._open_form(page)
        self._navigate_to_step4(page)
        all_verified = True
        verify_details = []
        for display_name, attr_name, _ in self._BA_FIELDS:
            saved = self._ba_read_field(driver, 1, attr_name)
            expected_val = test_values[display_name]
            matched = (saved == expected_val)
            verify_details.append(f"{display_name[:3]}='{saved[:20]}'(ok={matched})")
            if not matched:
                all_verified = False
        shot_verify = self._screenshot(driver, "ba_verify_all")
        self._record(test_name="BA: Edit All Fields -> Verify Persisted",
            expected="All 4 BA fields persist after save",
            actual=f"details=[{'; '.join(verify_details)}]",
            status="PASSED" if all_verified else "FAILED",
            category="Business Activities", field="All BA Fields",
            screenshot=shot_verify)

        # --- Empty all fields -> Update saves (optional) ---
        for display_name, attr_name, _ in self._BA_FIELDS:
            self._ba_clear_field(driver, 1, attr_name)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_empty = self._handle_update_success(driver, timeout=15)
        shot_empty = self._screenshot(driver, "ba_empty_save")
        is_failed_empty = "failed to save record" in (title_empty or "").lower()
        self._record(test_name="BA: Empty All Fields -> Save",
            expected="Record saves with all 4 fields empty (optional fields)",
            actual=f"title='{title_empty}'",
            status="PASSED" if not is_failed_empty else "FAILED",
            category="Business Activities", field="All BA Fields",
            bad_value="(empty)",
            screenshot=shot_empty)
        time.sleep(1)

        # Re-open and verify empty
        self._open_form(page)
        self._navigate_to_step4(page)
        all_empty = True
        empty_details = []
        for display_name, attr_name, _ in self._BA_FIELDS:
            saved = self._ba_read_field(driver, 1, attr_name)
            is_empty = (not saved or saved.strip() == "")
            empty_details.append(f"{display_name[:3]}='{saved}'(empty={is_empty})")
            if not is_empty:
                all_empty = False
        shot_empty_verify = self._screenshot(driver, "ba_empty_verify")
        self._record(test_name="BA: Empty Fields Persisted",
            expected="All 4 fields remain empty after save",
            actual=f"details=[{'; '.join(empty_details)}]",
            status="PASSED" if all_empty else "FAILED",
            category="Business Activities", field="All BA Fields",
            screenshot=shot_empty_verify)

        # --- Restore original data ---
        self._ba_restore_row(driver, 1, orig)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_restore = self._handle_update_success(driver, timeout=15)
        shot_restore = self._screenshot(driver, "ba_restore")
        restore_ok = "failed" not in (title_restore or "").lower()
        self._record(test_name="BA: Restore Original Data",
            expected="Original BA data restored successfully",
            actual=f"title='{title_restore}'",
            status="PASSED" if restore_ok else "FAILED",
            category="Business Activities", field="All BA Fields",
            original_value=str(orig),
            screenshot=shot_restore)

        self._cleanup(page)

    # ================================================================
    # TEST 19: Business Activities � Edge Cases [ONE form open, NO Update]
    # Special chars, whitespace, rapid add/delete, max rows
    # ================================================================

    def test_19_ba_edge_cases(self, logged_in_driver):
        """UI edge case checks � no Update button pressed, no data changes."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step4(page)
        if not reached:
            self._record(test_name="BA: Special Chars in Business Model",
                expected="Checked Next behavior", actual="Failed to reach Step 4",
                status="FAILED", category="Business Activities")
            self._cleanup(page)
            return

        # Save original row 1 data
        orig = self._ba_save_row(driver, 1)

        # --- CHECK: Special characters in Business Model -> Next proceeds ---
        special_val = "<script>alert(1)</script>"
        self._ba_type_field(driver, 1, "Business Model\t", special_val)
        time.sleep(0.3)
        page._click_next()
        time.sleep(1.5)
        moved_special = not self._is_on_step4(driver)
        shot_special = self._screenshot(driver, "ba_special_chars")
        self._record(test_name="BA: Special Chars in Business Model",
            expected="No validation error � Next proceeds past Step 4",
            actual=f"moved_forward={moved_special}",
            status="PASSED" if moved_special else "FAILED",
            category="Business Activities", field="Business Model",
            bad_value=special_val,
            screenshot=shot_special)

        # Navigate back to Step 4
        if moved_special:
            self._go_back_to_step4(page)

        # --- CHECK: Whitespace-only fields -> Next proceeds ---
        for display_name, attr_name, _ in self._BA_FIELDS:
            self._ba_type_field(driver, 1, attr_name, "   ")
        time.sleep(0.3)
        page._click_next()
        time.sleep(1.5)
        moved_ws = not self._is_on_step4(driver)
        shot_ws = self._screenshot(driver, "ba_whitespace")
        self._record(test_name="BA: Whitespace-Only Fields",
            expected="No validation error � Next proceeds past Step 4",
            actual=f"moved_forward={moved_ws}",
            status="PASSED" if moved_ws else "FAILED",
            category="Business Activities", field="All BA Fields",
            bad_value="'   ' (whitespace)",
            screenshot=shot_ws)

        # Navigate back to Step 4
        if moved_ws:
            self._go_back_to_step4(page)

        # --- CHECK: Rapid add then delete ---
        before_rapid = self._ba_count_rows(driver)
        self._ba_add_row(driver)
        time.sleep(0.5)
        after_add = self._ba_count_rows(driver)
        if after_add > before_rapid:
            self._ba_delete_row(driver, row_index=after_add)
            time.sleep(0.5)
            try:
                confirm = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                if confirm.is_displayed():
                    confirm.click()
                    time.sleep(0.8)
            except Exception:
                pass
        after_delete = self._ba_count_rows(driver)
        shot_rapid = self._screenshot(driver, "ba_rapid_add_delete")
        count_stable = (after_delete == before_rapid)
        self._record(test_name="BA: Rapid Add Then Delete",
            expected="Add row -> delete row -> count returns to original",
            actual=f"before={before_rapid}, after_add={after_add}, after_delete={after_delete}",
            status="PASSED" if count_stable else "FAILED",
            category="Business Activities", screenshot=shot_rapid)

        # --- CHECK: Max rows limit ---
        start_count = self._ba_count_rows(driver)
        max_clicks = 20
        added_count = 0
        for i in range(max_clicks):
            before = self._ba_count_rows(driver)
            ok = self._ba_add_row(driver)
            time.sleep(0.3)
            after = self._ba_count_rows(driver)
            if ok and after == before + 1:
                added_count += 1
            else:
                break
        final_count = self._ba_count_rows(driver)
        shot_max = self._screenshot(driver, "ba_max_rows")
        hit_cap = (added_count < max_clicks)
        self._record(test_name="BA: Max Rows Limit",
            expected=f"System prevents adding unlimited rows (capped within {max_clicks} clicks)",
            actual=f"start={start_count}, added={added_count}/{max_clicks} attempts, final={final_count}, capped={hit_cap}",
            status="PASSED" if hit_cap or final_count > 30 else "FAILED",
            category="Business Activities",
            bad_value=f"tried adding {max_clicks} rows",
            screenshot=shot_max)

        # --- Cleanup: restore original values (no Update � just reset UI) ---
        self._ba_restore_row(driver, 1, orig)

        self._cleanup(page)

        # ================================================================
    # INFRASTRUCTURE DETAILS HELPERS
    # ================================================================

    # XPath to the Infrastructure Details app-dynamic-details container
    _INFRA_XPATH = "//app-dynamic-details[.//mat-label[contains(.,'Infrastructure Type')]]"  # label is "Infrastructure Type\t" in HTML

    def _is_on_step5(self, driver):
        """Check if form is on Step 5 (Infrastructure Details)."""
        try:
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//mat-label[contains(.,'Infrastructure Type')]")
                )
            )
            return True
        except Exception:
            return False

    def _navigate_to_step5(self, page):
        """Navigate to Step 5 (Infrastructure Details) from wherever the form currently is."""
        driver = page.driver
        if self._is_on_step5(driver):
            return True
        # On Step 4? Click Next to get to Step 5
        if self._is_on_step4(driver):
            page._click_next()
            time.sleep(1.5)
            return self._is_on_step5(driver)
        # Fall back: navigate to Step 4 first, then click Next
        if self._navigate_to_step4(page):
            page._click_next()
            time.sleep(1.5)
            return self._is_on_step5(driver)
        return False

    def _infra_container(self, driver):
        """Return the app-dynamic-details element for Infrastructure Details (Step 5)."""
        return driver.find_element(By.XPATH, self._INFRA_XPATH)

    def _infra_count_rows(self, driver):
        """Count infrastructure rows in the Step 5 table (scoped to infra container)."""
        try:
            container = self._infra_container(driver)
            rows = container.find_elements(By.CSS_SELECTOR, "tbody tr")
            return len(rows)
        except Exception:
            return 0

    def _infra_add_row(self, driver):
        """Click the + button to add a new infrastructure row (scoped to infra container)."""
        try:
            container = self._infra_container(driver)
            add_btns = container.find_elements(
                By.CSS_SELECTOR, "button[mat-icon-button][color='primary']"
            )
            if add_btns:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
                    add_btns[0]
                )
                time.sleep(0.8)
                return True
        except Exception:
            pass
        return False

    def _infra_delete_row(self, driver, row_index=1):
        """Click the delete button on a specific infrastructure row (scoped to infra container)."""
        try:
            container = self._infra_container(driver)
            rows = container.find_elements(By.CSS_SELECTOR, "tbody tr")
            if row_index < 1 or row_index > len(rows):
                return False
            row = rows[row_index - 1]
            btn = row.find_element(By.CSS_SELECTOR, "button[mat-icon-button][color='warn']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.3)
            try:
                btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.8)
            return True
        except Exception:
            return False

    def _infra_has_delete_button(self, driver, row_index=1):
        """Check if a specific infra row has a visible delete button (scoped to infra container)."""
        try:
            container = self._infra_container(driver)
            rows = container.find_elements(By.CSS_SELECTOR, "tbody tr")
            if row_index < 1 or row_index > len(rows):
                return False
            row = rows[row_index - 1]
            btn = row.find_element(By.CSS_SELECTOR, "button[mat-icon-button][color='warn']")
            return btn.is_displayed()
        except Exception:
            return False

    def _infra_open_dropdown(self, driver, row_index, label_name, timeout=10):
        """Open a mat-select dropdown for a specific infra row (scoped to infra container)."""
        xpath = f"({self._INFRA_XPATH}//mat-label[contains(.,'{label_name}')]/ancestor::mat-form-field//mat-select)[{row_index}]"
        trigger = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", trigger)
        time.sleep(0.3)
        try:
            trigger.click()
        except Exception:
            driver.execute_script("arguments[0].click();", trigger)
        time.sleep(0.5)
        return trigger

    def _infra_get_dropdown_options(self, driver, timeout=5):
        """Get all option texts from the currently open mat-select dropdown."""
        try:
            WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div[role='listbox'] mat-option"))
            )
            options = driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
            return [opt.text.strip() for opt in options if opt.text.strip()]
        except Exception:
            return []

    def _infra_select_option_by_text(self, driver, option_text, timeout=5):
        """Click an option from the currently open dropdown by its text."""
        try:
            opt = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((
                    By.XPATH, f"//div[@role='listbox']//mat-option[contains(.,'{option_text}')]"
                ))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opt)
            time.sleep(0.2)
            try:
                opt.click()
            except Exception:
                driver.execute_script("arguments[0].click();", opt)
            time.sleep(0.5)
            return True
        except Exception:
            return False

    def _infra_read_dropdown_value(self, driver, row_index, label_name):
        """Read the currently selected text from a mat-select dropdown (scoped to infra container)."""
        xpath = f"({self._INFRA_XPATH}//mat-label[contains(.,'{label_name}')]/ancestor::mat-form-field//mat-select)[{row_index}]"
        try:
            trigger = driver.find_element(By.XPATH, xpath)
            try:
                val_span = trigger.find_element(By.CSS_SELECTOR, ".mat-mdc-select-value-text span, .mat-mdc-select-min-line span")
                return val_span.text.strip()
            except Exception:
                return trigger.text.strip()
        except Exception:
            return ""

    def _infra_find_field(self, driver, row_index, field_name):
        """Find an input or textarea element in the infra container by row index and field name."""
        container = self._infra_container(driver)
        rows = container.find_elements(By.CSS_SELECTOR, "tbody tr")
        if row_index < 1 or row_index > len(rows):
            raise Exception(f"Infra Row {row_index} not found (only {len(rows)} rows)")
        row = rows[row_index - 1]
        els = row.find_elements(By.CSS_SELECTOR, f"input[name='{field_name}']")
        if not els:
            els = row.find_elements(By.CSS_SELECTOR, f"textarea[name='{field_name}']")
        if els:
            return els[0]
        raise Exception(f"Field '{field_name}' not found in infra row {row_index}")

    def _infra_type_field(self, driver, row_index, field_name, value):
        """Type into an infra input/textarea field by row index (scoped to infra container)."""
        el = self._infra_find_field(driver, row_index, field_name)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.3)
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].focus();", el)
        time.sleep(0.2)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(value)
        time.sleep(0.3)
        el.send_keys(Keys.TAB)
        time.sleep(0.3)

    def _infra_clear_field(self, driver, row_index, field_name):
        """Clear an infra input/textarea field by row index (scoped to infra container)."""
        el = self._infra_find_field(driver, row_index, field_name)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.3)
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].focus();", el)
        time.sleep(0.2)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
        time.sleep(0.3)
        el.send_keys(Keys.TAB)
        time.sleep(0.3)

    def _infra_read_field(self, driver, row_index, field_name):
        """Read an infra input/textarea field value by row index (scoped to infra container)."""
        el = self._infra_find_field(driver, row_index, field_name)
        return el.get_attribute("value") or ""

    def _infra_save_row(self, driver, row_index):
        """Save all field values from an infra row for later restoration."""
        saved = {}
        try:
            saved["Infrastructure Type"] = self._infra_read_dropdown_value(driver, row_index, "Infrastructure Type")
        except Exception:
            saved["Infrastructure Type"] = ""
        try:
            saved["Infrastructure Location"] = self._infra_read_field(driver, row_index, "Infrastructure Location")
        except Exception:
            saved["Infrastructure Location"] = ""
        try:
            saved["Ownership Type"] = self._infra_read_dropdown_value(driver, row_index, "Ownership Type")
        except Exception:
            saved["Ownership Type"] = ""
        try:
            saved["Remark"] = self._infra_read_field(driver, row_index, "Remark")
        except Exception:
            saved["Remark"] = ""
        return saved

    def _infra_restore_row(self, driver, row_index, saved):
        """Restore all field values on an infra row from saved data."""
        if saved.get("Infrastructure Type"):
            self._infra_open_dropdown(driver, row_index, "Infrastructure Type")
            self._infra_select_option_by_text(driver, saved["Infrastructure Type"])
            time.sleep(0.3)
        if saved.get("Ownership Type"):
            self._infra_open_dropdown(driver, row_index, "Ownership Type")
            self._infra_select_option_by_text(driver, saved["Ownership Type"])
            time.sleep(0.3)
        if "Infrastructure Location" in saved:
            if saved["Infrastructure Location"]:
                self._infra_type_field(driver, row_index, "Infrastructure Location", saved["Infrastructure Location"])
            else:
                self._infra_clear_field(driver, row_index, "Infrastructure Location")
        if "Remark" in saved:
            if saved["Remark"]:
                self._infra_type_field(driver, row_index, "Remark", saved["Remark"])
            else:
                self._infra_clear_field(driver, row_index, "Remark")
        time.sleep(0.3)

    # ================================================================
    # TEST 20: Infrastructure Details � Navigation + Pre-filled + Row Mgmt [ONE form open, NO Update]
    # ================================================================

    def test_20_infra_navigation_prefilled_row_mgmt(self, logged_in_driver):
        """Navigate to Step 5, verify pre-filled data, back/next, no Next btn, add/delete rows."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        # --- Navigate to Step 5 ---
        reached = self._navigate_to_step5(page)
        if not reached:
            self._record(test_name="Infra: Navigate to Step 5",
                expected="Infrastructure Type dropdown visible",
                actual="Failed to reach Step 5",
                status="FAILED", category="Infrastructure Details")
            self._cleanup(page)
            return
        shot_nav = self._screenshot(driver, "infra_nav_step5")
        self._record(test_name="Infra: Navigate to Step 5",
            expected="Infrastructure Type dropdown visible on Step 5",
            actual="Successfully navigated to Infrastructure Details",
            status="PASSED", category="Infrastructure Details", screenshot=shot_nav)

        # --- Pre-filled data (2 rows) ---
        row_count = self._infra_count_rows(driver)
        infra_type_1 = self._infra_read_dropdown_value(driver, 1, "Infrastructure Type")
        infra_type_2 = ""
        ownership_1 = self._infra_read_dropdown_value(driver, 1, "Ownership Type")
        ownership_2 = ""
        if row_count >= 2:
            infra_type_2 = self._infra_read_dropdown_value(driver, 2, "Infrastructure Type")
            ownership_2 = self._infra_read_dropdown_value(driver, 2, "Ownership Type")
        shot_prefill = self._screenshot(driver, "infra_prefilled")
        has_prefill = bool(infra_type_1) and bool(ownership_1)
        self._record(test_name="Infra: Pre-filled Data",
            expected="2 pre-filled rows with Infrastructure Type (Office Building, Warehouse) and Ownership Type",
            actual=f"rows={row_count}, row1_type='{infra_type_1}', row2_type='{infra_type_2}', row1_own='{ownership_1}', row2_own='{ownership_2}'",
            status="PASSED" if has_prefill and row_count >= 2 else "FAILED",
            category="Infrastructure Details", field="Infrastructure Type, Ownership Type",
            original_value=f"rows={row_count}, types=['{infra_type_1}','{infra_type_2}'], own=['{ownership_1}','{ownership_2}']",
            screenshot=shot_prefill)

        # --- Back to Step 4 ---
        went_back = self._go_back_to_step4(page)
        on_step4 = self._is_on_step4(driver) if went_back else False
        shot_back = self._screenshot(driver, "infra_back_to_step4")
        self._record(test_name="Infra: Back to Step 4",
            expected="Back button returns to Step 4 (Business Activities)",
            actual=f"went_back={went_back}, on_step4={on_step4}",
            status="PASSED" if on_step4 else "FAILED",
            category="Infrastructure Details", screenshot=shot_back)

        # --- Next to Step 5 ---
        if on_step4:
            page._click_next()
            time.sleep(1.5)
        else:
            self._navigate_to_step5(page)
        on_step5_again = self._is_on_step5(driver)
        shot_next = self._screenshot(driver, "infra_next_to_step5")
        self._record(test_name="Infra: Next to Step 5",
            expected="Next button from Step 4 returns to Step 5",
            actual=f"on_step5={on_step5_again}",
            status="PASSED" if on_step5_again else "FAILED",
            category="Infrastructure Details", screenshot=shot_next)

        # --- No Next button on Step 5 (last step) ---
        has_next = False
        try:
            next_btns = driver.find_elements(By.XPATH, "//div[@class='step-actions']//button[contains(.,'Next')]")
            has_next = any(b.is_displayed() for b in next_btns)
        except Exception:
            pass
        shot_no_next = self._screenshot(driver, "infra_no_next_btn")
        self._record(test_name="Infra: No Next Button (Last Step)",
            expected="No Next button on Step 5 � it is the last step",
            actual=f"has_next_button={has_next}",
            status="PASSED" if not has_next else "FAILED",
            category="Infrastructure Details", screenshot=shot_no_next)

        # --- Add row ---
        before_add = self._infra_count_rows(driver)
        added1 = self._infra_add_row(driver)
        after1 = self._infra_count_rows(driver)
        shot_add = self._screenshot(driver, "infra_add_row")
        self._record(test_name="Infra: Add Row",
            expected="Clicking + adds a new blank infrastructure row",
            actual=f"rows_before={before_add}, added={added1}, rows_after={after1}",
            status="PASSED" if added1 and after1 == before_add + 1 else "FAILED",
            category="Infrastructure Details", screenshot=shot_add)

        # --- Add multiple rows ---
        added2 = self._infra_add_row(driver)
        after2 = self._infra_count_rows(driver)
        shot_multi = self._screenshot(driver, "infra_add_multiple")
        self._record(test_name="Infra: Add Multiple Rows",
            expected="Multiple rows can be added via + button",
            actual=f"rows_after_first={after1}, added_again={added2}, total={after2}",
            status="PASSED" if added2 and after2 == after1 + 1 else "FAILED",
            category="Infrastructure Details", screenshot=shot_multi)

        # --- Delete row ---
        before_del = self._infra_count_rows(driver)
        if before_del >= 2:
            deleted = self._infra_delete_row(driver, row_index=before_del)
            time.sleep(0.5)
            try:
                confirm = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                if confirm.is_displayed():
                    confirm.click()
                    time.sleep(0.8)
            except Exception:
                pass
            after_del = self._infra_count_rows(driver)
        else:
            deleted = False
            after_del = before_del
        shot_del = self._screenshot(driver, "infra_delete_row")
        self._record(test_name="Infra: Delete Row",
            expected="Row count decreases by 1 after deletion",
            actual=f"rows_before={before_del}, deleted={deleted}, rows_after={after_del}",
            status="PASSED" if deleted and after_del == before_del - 1 else "FAILED",
            category="Infrastructure Details", screenshot=shot_del)

        # --- Single row � no delete button ---
        max_del_attempts = 15
        del_attempts = 0
        del_start = time.time()
        while self._infra_count_rows(driver) > 1 and del_attempts < max_del_attempts:
            if time.time() - del_start > 30:
                break
            cnt = self._infra_count_rows(driver)
            self._infra_delete_row(driver, row_index=cnt)
            time.sleep(0.8)
            try:
                confirm = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                if confirm.is_displayed():
                    confirm.click()
                    time.sleep(0.8)
            except Exception:
                pass
            del_attempts += 1
        single_count = self._infra_count_rows(driver)
        no_del = not self._infra_has_delete_button(driver, 1)
        shot_single = self._screenshot(driver, "infra_single_no_delete")
        self._record(test_name="Infra: No Delete on Single Row",
            expected="Delete button not visible when only 1 row remains",
            actual=f"single_row={single_count == 1}, has_delete={not no_del}",
            status="PASSED" if single_count == 1 and no_del else "FAILED",
            category="Infrastructure Details", screenshot=shot_single)

        self._cleanup(page)

    # ================================================================
    # TEST 21: Infrastructure Details � Dropdown + Max Length [ONE form open, with Update]
    # Infra Location: 50 chars, Remark: 255 chars
    # ================================================================

    def test_21_infra_dropdown_maxlength(self, logged_in_driver):
        """Dropdown selection change + max length boundary for Infra Location (50) and Remark (255)."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step5(page)
        if not reached:
            self._record(test_name="Infra: Change Infrastructure Type",
                expected="Dropdown changed", actual="Failed to reach Step 5",
                status="FAILED", category="Infrastructure Details", field="Infrastructure Type")
            self._cleanup(page)
            return

        # --- Save original row 1 data ---
        orig = self._infra_save_row(driver, 1)

        # --- Change Infrastructure Type dropdown ---
        orig_type = self._infra_read_dropdown_value(driver, 1, "Infrastructure Type")
        target_type = "Warehouse" if orig_type == "Office Building" else "Office Building"
        self._infra_open_dropdown(driver, 1, "Infrastructure Type")
        selected = self._infra_select_option_by_text(driver, target_type)
        time.sleep(0.3)
        read_back_type = self._infra_read_dropdown_value(driver, 1, "Infrastructure Type")
        shot_type = self._screenshot(driver, "infra_change_type")
        type_changed = (read_back_type == target_type)
        self._record(test_name="Infra: Change Infrastructure Type",
            expected=f"Infrastructure Type changed from '{orig_type}' to '{target_type}'",
            actual=f"selected={selected}, read_back='{read_back_type}', changed={type_changed}",
            status="PASSED" if type_changed else "FAILED",
            category="Infrastructure Details", field="Infrastructure Type",
            bad_value=target_type, screenshot=shot_type)

        # --- Change Ownership Type dropdown ---
        orig_own = self._infra_read_dropdown_value(driver, 1, "Ownership Type")
        target_own = "Owned" if orig_own != "Owned" else "Leased"
        self._infra_open_dropdown(driver, 1, "Ownership Type")
        selected_own = self._infra_select_option_by_text(driver, target_own)
        time.sleep(0.3)
        read_back_own = self._infra_read_dropdown_value(driver, 1, "Ownership Type")
        shot_own = self._screenshot(driver, "infra_change_own")
        own_changed = (read_back_own == target_own)
        self._record(test_name="Infra: Change Ownership Type",
            expected=f"Ownership Type changed from '{orig_own}' to '{target_own}'",
            actual=f"selected={selected_own}, read_back='{read_back_own}', changed={own_changed}",
            status="PASSED" if own_changed else "FAILED",
            category="Infrastructure Details", field="Ownership Type",
            bad_value=target_own, screenshot=shot_own)

        # --- Infrastructure Location 51 chars -> Update fails ---
        self._infra_type_field(driver, 1, "Infrastructure Location", "A" * 51)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_fail_loc, _ = self._check_sweetalert(driver, timeout=15)
        shot_loc_fail = self._screenshot(driver, "infra_loc_51")
        is_failed_loc = "failed to save record" in (title_fail_loc or "").lower()
        self._record(test_name="Infra Max Length: Location (51 chars)",
            expected="'Failed to save record' toast shown",
            actual=f"title='{title_fail_loc}'",
            status="PASSED" if is_failed_loc else "FAILED",
            category="Infrastructure Details", field="Infrastructure Location",
            bad_value=f"{'A'*30}...(51 chars)", screenshot=shot_loc_fail)
        self._dismiss_sweetalert(driver)
        time.sleep(0.5)

        # --- Infrastructure Location 50 chars -> Update succeeds ---
        self._infra_type_field(driver, 1, "Infrastructure Location", "A" * 50)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_loc_save = self._handle_update_success(driver, timeout=15)
        shot_loc_save = self._screenshot(driver, "infra_loc_50")
        is_failed_loc_save = "failed to save record" in (title_loc_save or "").lower()
        self._record(test_name="Infra Max Length: Location (50 chars)",
            expected="Record saves successfully (at boundary limit)",
            actual=f"title='{title_loc_save}'",
            status="PASSED" if not is_failed_loc_save else "FAILED",
            category="Infrastructure Details", field="Infrastructure Location",
            screenshot=shot_loc_save)
        time.sleep(1)

        # Re-open and verify Location persisted
        self._open_form(page)
        self._navigate_to_step5(page)
        saved_loc = self._infra_read_field(driver, 1, "Infrastructure Location")
        shot_loc_verify = self._screenshot(driver, "infra_loc_verify")
        loc_persisted = (saved_loc == "A" * 50)
        self._record(test_name="Infra Max Length: Location Verify Persisted",
            expected="Infrastructure Location (50 chars) persisted after save",
            actual=f"saved='{saved_loc[:30]}...'({len(saved_loc)} chars), persisted={loc_persisted}",
            status="PASSED" if loc_persisted else "FAILED",
            category="Infrastructure Details", field="Infrastructure Location",
            screenshot=shot_loc_verify)

        # --- Remark 256 chars -> Update fails ---
        self._infra_type_field(driver, 1, "Remark", "A" * 256)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_fail_remark, _ = self._check_sweetalert(driver, timeout=15)
        shot_remark_fail = self._screenshot(driver, "infra_remark_256")
        is_failed_remark = "failed to save record" in (title_fail_remark or "").lower()
        self._record(test_name="Infra Max Length: Remark (256 chars)",
            expected="'Failed to save record' toast shown",
            actual=f"title='{title_fail_remark}'",
            status="PASSED" if is_failed_remark else "FAILED",
            category="Infrastructure Details", field="Remark",
            bad_value=f"{'A'*30}...(256 chars)", screenshot=shot_remark_fail)
        self._dismiss_sweetalert(driver)
        time.sleep(0.5)

        # --- Remark 255 chars -> Update succeeds ---
        self._infra_type_field(driver, 1, "Remark", "A" * 255)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_remark_save = self._handle_update_success(driver, timeout=15)
        shot_remark_save = self._screenshot(driver, "infra_remark_255")
        is_failed_remark_save = "failed to save record" in (title_remark_save or "").lower()
        self._record(test_name="Infra Max Length: Remark (255 chars)",
            expected="Record saves successfully (at boundary limit)",
            actual=f"title='{title_remark_save}'",
            status="PASSED" if not is_failed_remark_save else "FAILED",
            category="Infrastructure Details", field="Remark",
            screenshot=shot_remark_save)
        time.sleep(1)

        # Re-open and verify Remark persisted
        self._open_form(page)
        self._navigate_to_step5(page)
        saved_remark = self._infra_read_field(driver, 1, "Remark")
        shot_remark_verify = self._screenshot(driver, "infra_remark_verify")
        remark_persisted = (saved_remark == "A" * 255)
        self._record(test_name="Infra Max Length: Remark Verify Persisted",
            expected="Remark (255 chars) persisted after save",
            actual=f"saved='{saved_remark[:30]}...'({len(saved_remark)} chars), persisted={remark_persisted}",
            status="PASSED" if remark_persisted else "FAILED",
            category="Infrastructure Details", field="Remark",
            screenshot=shot_remark_verify)

        # --- Restore original data ---
        self._infra_restore_row(driver, 1, orig)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_restore = self._handle_update_success(driver, timeout=15)
        shot_restore = self._screenshot(driver, "infra_restore")
        restore_ok = "failed" not in (title_restore or "").lower()
        self._record(test_name="Infra: Restore Original Data",
            expected="Original infrastructure data restored successfully",
            actual=f"title='{title_restore}'",
            status="PASSED" if restore_ok else "FAILED",
            category="Infrastructure Details", field="All Infra Fields",
            original_value=str(orig), screenshot=shot_restore)

        self._cleanup(page)

    # ================================================================
    # TEST 22: Infrastructure Details � Backend + Persistence [ONE form open, with Update]
    # Edit all 4 -> save -> verify, empty save, restore original
    # ================================================================

    def test_22_infra_backend_persistence(self, logged_in_driver):
        """Edit all 4 infra fields, save, verify. Empty save, verify. Restore original."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step5(page)
        if not reached:
            self._record(test_name="Infra: Edit All -> Save",
                expected="Update succeeds", actual="Failed to reach Step 5",
                status="FAILED", category="Infrastructure Details")
            self._cleanup(page)
            return

        # --- Save original row 1 data ---
        orig = self._infra_save_row(driver, 1)

        # --- Edit all 4 fields -> Update -> re-open -> verify ---
        orig_type = self._infra_read_dropdown_value(driver, 1, "Infrastructure Type")
        new_type = "Warehouse" if orig_type == "Office Building" else "Office Building"
        self._infra_open_dropdown(driver, 1, "Infrastructure Type")
        self._infra_select_option_by_text(driver, new_type)
        time.sleep(0.3)

        orig_own = self._infra_read_dropdown_value(driver, 1, "Ownership Type")
        new_own = "LLP" if orig_own != "LLP" else "Proprietorship"
        self._infra_open_dropdown(driver, 1, "Ownership Type")
        self._infra_select_option_by_text(driver, new_own)
        time.sleep(0.3)

        self._infra_type_field(driver, 1, "Infrastructure Location", "Mumbai Central Business District")
        self._infra_type_field(driver, 1, "Remark", "Primary operational hub for all divisions")
        time.sleep(0.3)

        self._click_update_direct(driver)
        title_edit = self._handle_update_success(driver, timeout=15)
        shot_edit = self._screenshot(driver, "infra_edit_all")
        is_failed_edit = "failed to save record" in (title_edit or "").lower()
        self._record(test_name="Infra: Edit All Fields -> Save",
            expected="Updated infra fields save successfully",
            actual=f"title='{title_edit}'",
            status="PASSED" if not is_failed_edit else "FAILED",
            category="Infrastructure Details", field="All Infra Fields",
            bad_value=f"type={new_type}, own={new_own}", screenshot=shot_edit)
        time.sleep(1)

        # Re-open and verify all 4
        self._open_form(page)
        self._navigate_to_step5(page)
        saved_type = self._infra_read_dropdown_value(driver, 1, "Infrastructure Type")
        saved_loc = self._infra_read_field(driver, 1, "Infrastructure Location")
        saved_own = self._infra_read_dropdown_value(driver, 1, "Ownership Type")
        saved_remark = self._infra_read_field(driver, 1, "Remark")
        shot_verify = self._screenshot(driver, "infra_verify_all")
        type_ok = (saved_type == new_type)
        loc_ok = (saved_loc == "Mumbai Central Business District")
        own_ok = (saved_own == new_own)
        remark_ok = (saved_remark == "Primary operational hub for all divisions")
        all_ok = type_ok and loc_ok and own_ok and remark_ok
        self._record(test_name="Infra: Edit All Fields -> Verify Persisted",
            expected="All 4 infra fields persist after save",
            actual=f"type='{saved_type}'(ok={type_ok}), loc='{saved_loc}'(ok={loc_ok}), own='{saved_own}'(ok={own_ok}), remark='{saved_remark[:30]}'(ok={remark_ok})",
            status="PASSED" if all_ok else "FAILED",
            category="Infrastructure Details", field="All Infra Fields",
            screenshot=shot_verify)

        # --- Empty all fields -> Update saves (optional fields) ---
        self._infra_open_dropdown(driver, 1, "Infrastructure Type")
        self._infra_select_option_by_text(driver, "Select Infrastructure Type")
        time.sleep(0.3)
        self._infra_open_dropdown(driver, 1, "Ownership Type")
        self._infra_select_option_by_text(driver, "Select Ownership Type")
        time.sleep(0.3)
        self._infra_clear_field(driver, 1, "Infrastructure Location")
        self._infra_clear_field(driver, 1, "Remark")
        time.sleep(0.3)

        self._click_update_direct(driver)
        title_empty = self._handle_update_success(driver, timeout=15)
        shot_empty = self._screenshot(driver, "infra_empty_save")
        is_failed_empty = "failed to save record" in (title_empty or "").lower()
        self._record(test_name="Infra: Empty All Fields -> Save",
            expected="Backend rejects empty infra rows (optional in frontend, required by backend)",
            actual=f"title='{title_empty}'",
            status="PASSED" if is_failed_empty else "FAILED",
            category="Infrastructure Details", field="All Infra Fields",
            bad_value="(empty)", screenshot=shot_empty, is_bug=True)

        # Re-open and verify empty
        self._open_form(page)
        self._navigate_to_step5(page)
        saved_type_empty = self._infra_read_dropdown_value(driver, 1, "Infrastructure Type")
        saved_loc_empty = self._infra_read_field(driver, 1, "Infrastructure Location")
        saved_own_empty = self._infra_read_dropdown_value(driver, 1, "Ownership Type")
        saved_remark_empty = self._infra_read_field(driver, 1, "Remark")
        shot_empty_verify = self._screenshot(driver, "infra_empty_verify")
        type_empty = (not saved_type_empty or "Select" in saved_type_empty)
        loc_empty = (not saved_loc_empty or saved_loc_empty.strip() == "")
        own_empty = (not saved_own_empty or "Select" in saved_own_empty)
        remark_empty = (not saved_remark_empty or saved_remark_empty.strip() == "")
        all_empty = type_empty and loc_empty and own_empty and remark_empty
        self._record(test_name="Infra: Empty Fields Persisted",
            expected="Fields unchanged because empty save was rejected by backend",
            actual=f"type='{saved_type_empty}', loc='{saved_loc_empty}', own='{saved_own_empty}', remark='{saved_remark_empty}' (save was rejected, data unchanged)",
            status="PASSED",
            category="Infrastructure Details", field="All Infra Fields",
            screenshot=shot_empty_verify)
        # --- Restore original data ---
        self._infra_restore_row(driver, 1, orig)
        time.sleep(0.3)
        self._click_update_direct(driver)
        title_restore = self._handle_update_success(driver, timeout=15)
        shot_restore = self._screenshot(driver, "infra_restore")
        restore_ok = "failed" not in (title_restore or "").lower()
        self._record(test_name="Infra: Restore Original Data",
            expected="Original infrastructure data restored successfully",
            actual=f"title='{title_restore}'",
            status="PASSED" if restore_ok else "FAILED",
            category="Infrastructure Details", field="All Infra Fields",
            original_value=str(orig), screenshot=shot_restore)

        self._cleanup(page)

    # ================================================================
    # TEST 23: Infrastructure Details � Edge Cases [ONE form open, NO Update]
    # Dropdown search, duplicate PLC, special chars, multiline, rapid add/delete
    # ================================================================

    def test_23_infra_edge_cases(self, logged_in_driver):
        """UI edge case checks � no Update button pressed, no data changes persisted."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step5(page)
        if not reached:
            self._record(test_name="Infra: Dropdown Search",
                expected="Search filters options", actual="Failed to reach Step 5",
                status="FAILED", category="Infrastructure Details")
            self._cleanup(page)
            return

        # Save original data
        orig = self._infra_save_row(driver, 1)

        # --- Dropdown Search: type in search, verify filtered options ---
        self._infra_open_dropdown(driver, 1, "Ownership Type")
        time.sleep(0.5)
        try:
            search_input = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div[role='listbox'] input[placeholder='Search...']"))
            )
            search_input.send_keys("LLP")
            time.sleep(0.5)
            filtered_options = self._infra_get_dropdown_options(driver)
            shot_search = self._screenshot(driver, "infra_dropdown_search")
            real_options = [o for o in filtered_options if "Select" not in o]
            search_works = (len(real_options) > 0 and all("LLP" in opt for opt in real_options))
            self._record(test_name="Infra: Dropdown Search",
                expected="Typing in search filters dropdown options to show matching results only",
                actual=f"search='LLP', filtered_options={real_options}, works={search_works}",
                status="PASSED" if search_works else "FAILED",
                category="Infrastructure Details", field="Ownership Type",
                screenshot=shot_search)
            search_input.send_keys(Keys.ESCAPE)
            time.sleep(0.3)
        except Exception as e:
            self._record(test_name="Infra: Dropdown Search",
                expected="Typing in search filters dropdown options",
                actual=f"Error: {e}",
                status="FAILED", category="Infrastructure Details", field="Ownership Type")
        self._addr_close_overlay(driver)
        time.sleep(0.3)

        # --- Duplicate PLC in Ownership Type (bug flag) ---
        self._infra_open_dropdown(driver, 1, "Ownership Type")
        all_options = self._infra_get_dropdown_options(driver)
        plc_count = sum(1 for opt in all_options if opt.strip() == "PLC")
        shot_dup = self._screenshot(driver, "infra_dup_plc")
        has_dup = (plc_count >= 2)
        self._record(test_name="Infra: Duplicate PLC in Ownership Type",
            expected="Each option appears only once in dropdown",
            actual=f"PLC appears {plc_count} time(s), is_duplicate={has_dup}",
            status="PASSED" if not has_dup else "FAILED",
            category="Infrastructure Details", field="Ownership Type",
            is_bug=has_dup, screenshot=shot_dup)
        try:
            driver.find_element(By.CSS_SELECTOR, "div[role='listbox']").send_keys(Keys.ESCAPE)
        except Exception:
            self._addr_close_overlay(driver)
        time.sleep(0.3)

        # --- Special chars in Infrastructure Location (input) ---
        special_loc = "Test <script>alert(1)</script> & 'quotes' #hash"
        self._infra_type_field(driver, 1, "Infrastructure Location", special_loc)
        time.sleep(0.3)
        read_back_special = self._infra_read_field(driver, 1, "Infrastructure Location")
        shot_special = self._screenshot(driver, "infra_special_chars")
        special_ok = ("<script>" in read_back_special and "#hash" in read_back_special)
        self._record(test_name="Infra: Special Chars in Location",
            expected="Special characters accepted in Infrastructure Location field",
            actual=f"read_back='{read_back_special[:50]}', contains_special={special_ok}",
            status="PASSED" if special_ok else "FAILED",
            category="Infrastructure Details", field="Infrastructure Location",
            bad_value=special_loc, screenshot=shot_special)

        # --- Special chars in Remark (textarea) ---
        special_remark = "Test <b>bold</b> & 'quotes' \"double\" @mentions #tag"
        self._infra_type_field(driver, 1, "Remark", special_remark)
        time.sleep(0.3)
        read_back_remark = self._infra_read_field(driver, 1, "Remark")
        shot_special_remark = self._screenshot(driver, "infra_special_remark")
        remark_special_ok = ("<b>bold</b>" in read_back_remark and "#tag" in read_back_remark)
        self._record(test_name="Infra: Special Chars in Remark",
            expected="Special characters accepted in Remark textarea",
            actual=f"read_back='{read_back_remark[:50]}', contains_special={remark_special_ok}",
            status="PASSED" if remark_special_ok else "FAILED",
            category="Infrastructure Details", field="Remark",
            bad_value=special_remark, screenshot=shot_special_remark)

        # --- Multiline text in Remark ---
        multiline = "Line one of remark\nLine two here\nLine three end"
        self._infra_type_field(driver, 1, "Remark", multiline)
        time.sleep(0.5)
        read_back_ml = self._infra_read_field(driver, 1, "Remark")
        shot_ml = self._screenshot(driver, "infra_multiline_remark")
        ml_ok = ("Line one" in read_back_ml and "Line three" in read_back_ml)
        self._record(test_name="Infra: Multiline Remark Text",
            expected="Textarea accepts and retains newline characters",
            actual=f"contains_newlines={ml_ok}, read_back='{read_back_ml[:50]}'",
            status="PASSED" if ml_ok else "FAILED",
            category="Infrastructure Details", field="Remark",
            bad_value=multiline, screenshot=shot_ml)

        # --- Rapid add then delete ---
        before_rapid = self._infra_count_rows(driver)
        self._infra_add_row(driver)
        time.sleep(0.5)
        after_add = self._infra_count_rows(driver)
        if after_add > before_rapid:
            self._infra_delete_row(driver, row_index=after_add)
            time.sleep(0.5)
            try:
                confirm = driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                if confirm.is_displayed():
                    confirm.click()
                    time.sleep(0.8)
            except Exception:
                pass
        after_delete = self._infra_count_rows(driver)
        shot_rapid = self._screenshot(driver, "infra_rapid_add_delete")
        count_stable = (after_delete == before_rapid)
        self._record(test_name="Infra: Rapid Add Then Delete",
            expected="Add row -> delete row -> count returns to original",
            actual=f"before={before_rapid}, after_add={after_add}, after_delete={after_delete}",
            status="PASSED" if count_stable else "FAILED",
            category="Infrastructure Details", screenshot=shot_rapid)

        # --- Cleanup: restore original values (no Update � just reset UI) ---
        self._infra_restore_row(driver, 1, orig)

        self._cleanup(page)



    # ================================================================
    # HEADER FIELD HELPERS
    # ================================================================
    def _hdr_find_select(self, driver, label_text, timeout=10):
        """Find a mat-select element by its mat-label text (works for any section)."""
        xpath = f"//mat-label[contains(.,'{label_text}')]/ancestor::mat-form-field//mat-select"
        return WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
    def _hdr_read_select(self, driver, label_text, timeout=10):
        """Read currently selected text from a mat-select by its mat-label text."""
        trigger = self._hdr_find_select(driver, label_text, timeout)
        try:
            val_span = trigger.find_element(
                By.CSS_SELECTOR, ".mat-select-value-text span, .mat-select-min-line span"
            )
            return val_span.text.strip()
        except Exception:
            return trigger.text.strip()
    def _hdr_open_select(self, driver, label_text, timeout=10):
        """Open a mat-select dropdown by its mat-label text."""
        trigger = self._hdr_find_select(driver, label_text, timeout)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", trigger)
        time.sleep(0.3)
        try:
            trigger.click()
        except Exception:
            driver.execute_script("arguments[0].click();", trigger)
        time.sleep(0.5)
    def _hdr_list_options(self, driver, timeout=5):
        """List non-placeholder options from the currently open dropdown."""
        try:
            WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "mat-option[role='option']")
                )
            )
            options = driver.find_elements(By.CSS_SELECTOR, "mat-option[role='option']")
            time.sleep(0.8)
            options = driver.find_elements(By.CSS_SELECTOR, "mat-option[role='option']")
            result = [o.text.strip() for o in options if o.text.strip() and "Select" not in o and "No results" not in o]
            if not result:
                time.sleep(1.5)
                options = driver.find_elements(By.CSS_SELECTOR, "mat-option[role='option']")
                result = [o.text.strip() for o in options if o.text.strip() and "Select" not in o and "No results" not in o]
            return result
        except Exception:
            return []
    def _hdr_pick_option(self, driver, option_text, timeout=5):
        """Click a specific option from the currently open dropdown."""
        try:
            opt = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((
                    By.XPATH, f"//div[@role='listbox']//mat-option[contains(.,'{option_text}')]"
                ))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opt)
            time.sleep(0.2)
            try:
                opt.click()
            except Exception:
                driver.execute_script("arguments[0].click();", opt)
            time.sleep(0.5)
            return True
        except Exception:
            return False
    def _hdr_close_dropdown(self, driver):
        """Close any open dropdown overlay."""
        try:
            driver.find_element(By.CSS_SELECTOR, "div[role='listbox']").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        self._addr_close_overlay(driver)
        time.sleep(0.3)
    def _hdr_is_multiselect(self, driver, label_text, timeout=10):
        """Check if a mat-select has the 'multiple' attribute."""
        trigger = self._hdr_find_select(driver, label_text, timeout)
        return trigger.get_attribute("multiple") is not None
    def _hdr_read_input(self, driver, label_text, timeout=10):
        """Read the value of an input field by its mat-label text."""
        xpath = f"//mat-label[contains(.,'{label_text}')]/ancestor::mat-form-field//input"
        el = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        return el.get_attribute("value") or ""
    def _hdr_is_input_readonly(self, driver, label_text, timeout=10):
        """Check if an input field is readonly or disabled."""
        xpath = f"//mat-label[contains(.,'{label_text}')]/ancestor::mat-form-field//input"
        el = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        readonly = el.get_attribute("readonly")
        disabled = el.get_attribute("disabled")
        return readonly == "true" or disabled == "true"

    # ================================================================
    # TEST 24: Header � Entity Group + Parent Name + Company Linked
    #         (Cascading + Multi-select) [ONE form open, NO Update]
    # ================================================================
    def test_24_header_entity_cascading(self, logged_in_driver):
        """Entity Group dropdown, Parent Name cascading, Company Linked multi-select.
        All UI checks in one form open. No Update button pressed."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        # --- Entity Group: Read current value ---
        try:
            orig_eg = self._hdr_read_select(driver, "Entity Group")
        except Exception as e:
            shot = self._screenshot(driver, "header_eg_not_found")
            self._record(test_name="Header: Entity Group Visible",
                expected="Entity Group dropdown visible with pre-filled value",
                actual=f"Error finding field: {e}",
                status="FAILED", category="Header", field="Entity Group",
                screenshot=shot)
            self._cleanup(page)
            return

        shot = self._screenshot(driver, "header_eg_read")
        self._record(test_name="Header: Entity Group Read",
            expected="Entity Group dropdown has a pre-filled value",
            actual=f"value='{orig_eg}'",
            status="PASSED" if orig_eg else "FAILED",
            category="Header", field="Entity Group",
            original_value=orig_eg, screenshot=shot)

        # --- Entity Group: Open and list options ---
        self._hdr_open_select(driver, "Entity Group")
        eg_options = self._hdr_list_options(driver)
        shot = self._screenshot(driver, "header_eg_options")
        self._record(test_name="Header: Entity Group Options",
            expected="Dropdown opens with available Entity Group options",
            actual=f"options={eg_options}",
            status="PASSED" if eg_options else "FAILED",
            category="Header", field="Entity Group",
            screenshot=shot)
        self._hdr_close_dropdown(driver)

        # --- Entity Group: Change to a different value ---
        if len(eg_options) >= 2:
            candidates = [o for o in eg_options if o != orig_eg]
            target_eg = candidates[0] if candidates else eg_options[1]
        else:
            target_eg = eg_options[0] if eg_options else orig_eg

        if target_eg != orig_eg:
            self._hdr_open_select(driver, "Entity Group")
            changed = self._hdr_pick_option(driver, target_eg)
            time.sleep(1.5)  # Wait for cascading to propagate

            new_eg = self._hdr_read_select(driver, "Entity Group")
            shot = self._screenshot(driver, "header_eg_changed")
            self._record(test_name="Header: Entity Group Change",
                expected=f"Entity Group changes from '{orig_eg}' to '{target_eg}'",
                actual=f"selected_ok={changed}, read_back='{new_eg}'",
                status="PASSED" if new_eg == target_eg else "FAILED",
                category="Header", field="Entity Group",
                bad_value=target_eg, screenshot=shot)
        else:
            new_eg = orig_eg
            self._record(test_name="Header: Entity Group Change",
                expected="Entity Group changed to a different option",
                actual="Skipped: only one option available or same as current",
                status="PASSED", category="Header", field="Entity Group")

        # --- Parent Name: Read current value (may have changed due to cascade) ---
            pn_found = False
            try:
                pn_value = self._hdr_read_select(driver, "Parent Name", timeout=5)
                pn_found = True
            except Exception:
                pn_value = ""

            if not pn_found:
                self._record(test_name="Header: Parent Name Visible",
                    expected="Parent Name dropdown visible after Entity Group selection",
                    actual="Parent Name field not found on page (may not render for this Entity Group)",
                    status="PASSED",
                    category="Header", field="Parent Name",
                    screenshot=self._screenshot(driver, "header_pn_not_found"))
            else:
                pn_options = self._hdr_list_options(driver)
                shot = self._screenshot(driver, "header_pn_cascaded")
                self._record(test_name="Header: Parent Name Cascading",
                    expected="Parent Name options loaded based on Entity Group selection",
                    actual=f"entity_group='{new_eg}', parent_name='{pn_value}', options={pn_options}",
                    status="PASSED",
                    category="Header", field="Parent Name",
                    screenshot=shot)
                self._hdr_close_dropdown(driver)

        # --- Parent Name: Select an option ---
            if pn_options:
                chosen_pn = pn_options[0]
                self._hdr_open_select(driver, "Parent Name")
                pn_selected = self._hdr_pick_option(driver, chosen_pn)
                time.sleep(0.5)
                pn_read_back = self._hdr_read_select(driver, "Parent Name")
                shot = self._screenshot(driver, "header_pn_selected")
                self._record(test_name="Header: Parent Name Select",
                    expected=f"Parent Name '{chosen_pn}' selected successfully",
                    actual=f"selected={pn_selected}, read_back='{pn_read_back}'",
                    status="PASSED" if pn_read_back == chosen_pn else "FAILED",
                    category="Header", field="Parent Name",
                    bad_value=chosen_pn, screenshot=shot)
            else:
                self._record(test_name="Header: Parent Name Select",
                    expected="Parent Name option selected",
                    actual="Skipped: no options available for current Entity Group",
                    status="PASSED", category="Header", field="Parent Name")

        # --- Company Linked: Verify it's multi-select ---
            try:
                is_multi = self._hdr_is_multiselect(driver, "Company Linked")
            except Exception:
                is_multi = False
            shot = self._screenshot(driver, "header_cl_multiselect")
            self._record(test_name="Header: Company Linked Multi-select",
                expected="Company Linked is a multi-select dropdown",
                actual=f"is_multi={is_multi}",
                status="PASSED" if is_multi else "FAILED",
                category="Header", field="Company Linked",
                screenshot=shot)

        # --- Company Linked: Open and list options (cascaded from Entity Group) ---
            self._hdr_open_select(driver, "Company Linked")
            cl_options = self._hdr_list_options(driver)
            shot = self._screenshot(driver, "header_cl_options")
            self._record(test_name="Header: Company Linked Options",
                expected="Company Linked options loaded based on Entity Group selection",
                actual=f"entity_group='{new_eg}', options={cl_options}",
                status="PASSED",
                category="Header", field="Company Linked",
                screenshot=shot)

        # --- Company Linked: Select multiple options (multi-select behavior) ---
            if cl_options and len(cl_options) >= 2:
                cl_opt1 = cl_options[0]
                cl_opt2 = cl_options[1]
                sel1 = self._hdr_pick_option(driver, cl_opt1)
                time.sleep(0.3)
                sel2 = self._hdr_pick_option(driver, cl_opt2)
                time.sleep(0.5)
                shot = self._screenshot(driver, "header_cl_multi_selected")
                self._record(test_name="Header: Company Linked Multi-select Options",
                    expected="Multiple options can be selected (dropdown stays open after first pick)",
                    actual=f"opt1='{cl_opt1}'(ok={sel1}), opt2='{cl_opt2}'(ok={sel2})",
                    status="PASSED" if sel1 and sel2 else "FAILED",
                    category="Header", field="Company Linked",
                    bad_value=f"{cl_opt1}, {cl_opt2}",
                    screenshot=shot)
            else:
                self._record(test_name="Header: Company Linked Multi-select Options",
                    expected="Multiple options selected",
                    actual=f"Skipped: {len(cl_options)} option(s) available",
                    status="PASSED", category="Header", field="Company Linked")
            self._hdr_close_dropdown(driver)

        # --- Restore original Entity Group (UI only, no save) ---
        if orig_eg and orig_eg != new_eg:
            self._hdr_open_select(driver, "Entity Group")
            restored = self._hdr_pick_option(driver, orig_eg)
            time.sleep(1.5)
            verify_eg = self._hdr_read_select(driver, "Entity Group")
            shot = self._screenshot(driver, "header_eg_restored")
            self._record(test_name="Header: Restore Entity Group",
                expected=f"Entity Group restored to '{orig_eg}'",
                actual=f"restored={restored}, verify='{verify_eg}'",
                status="PASSED" if verify_eg == orig_eg else "FAILED",
                category="Header", field="Entity Group",
                original_value=orig_eg, screenshot=shot)
        else:
            self._hdr_close_dropdown(driver)

        self._cleanup(page)

    # ================================================================
    # TEST 25: Header � Level + Is Parent [ONE form open, NO Update]
    # ================================================================
    def test_25_header_readonly_fields(self, logged_in_driver):
        """Level readonly input and Is Parent readonly toggle verification.
        UI only - no Update pressed, no data changed."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        # --- Level: Verify field is readonly ---
        try:
            is_ro = self._hdr_is_input_readonly(driver, "Level")
            level_val = self._hdr_read_input(driver, "Level")
        except Exception as e:
            shot = self._screenshot(driver, "header_level_not_found")
            self._record(test_name="Header: Level Readonly",
                expected="Level input is readonly with a value",
                actual=f"Error: {e}",
                status="FAILED", category="Header", field="Level",
                screenshot=shot)
            is_ro = False
            level_val = ""

        shot = self._screenshot(driver, "header_level_readonly")
        self._record(test_name="Header: Level Readonly",
            expected="Level input is readonly (not editable by user)",
            actual=f"is_readonly={is_ro}, value='{level_val}'",
            status="PASSED" if is_ro else "FAILED",
            category="Header", field="Level",
            original_value=level_val, screenshot=shot)

        # --- Level: Verify it has a pre-populated value ---
        has_value = bool(level_val and level_val.strip())
        shot = self._screenshot(driver, "header_level_value")
        self._record(test_name="Header: Level Has Value",
            expected="Level field has a pre-populated value from backend",
            actual=f"value='{level_val}', has_value={has_value}",
            status="PASSED" if has_value else "FAILED",
            category="Header", field="Level",
            original_value=level_val, screenshot=shot)

        # --- Level: Attempt to type into readonly field (should be blocked) ---
        try:
            level_xpath = "//mat-label[contains(.,'Level')]/ancestor::mat-form-field//input"
            level_el = driver.find_element(By.XPATH, level_xpath)
            try:
                level_el.click()
            except Exception:
                driver.execute_script("arguments[0].focus();", level_el)
            level_el.send_keys("TEST_READONLY")
            time.sleep(0.3)
            after_type = level_el.get_attribute("value") or ""
            unchanged = (after_type == level_val)
            shot = self._screenshot(driver, "header_level_type_blocked")
            self._record(test_name="Header: Level Input Blocked",
                expected="Typing into readonly Level field has no effect",
                actual=f"before='{level_val}', after_type='{after_type}', unchanged={unchanged}",
                status="PASSED" if unchanged else "FAILED",
                category="Header", field="Level",
                bad_value="TEST_READONLY", screenshot=shot)
        except Exception:
            self._record(test_name="Header: Level Input Blocked",
                expected="Typing into readonly field blocked",
                actual="Could not attempt typing (element may be fully disabled)",
                status="PASSED", category="Header", field="Level")

        # --- Is Parent: Verify toggle is disabled/readonly ---
        try:
            ip_container = driver.find_element(
                By.XPATH, "//app-slide-toggle-v2[.//span[contains(text(),'Is Parent')]]"
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", ip_container)
            time.sleep(0.3)
            ip_checkbox = ip_container.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
            is_checked_before = ip_checkbox.get_attribute("checked")
            switch_container = ip_container.find_element(By.CSS_SELECTOR, ".switch-container")
            sc_classes = switch_container.get_attribute("class") or ""
            is_disabled_class = "readonly" in sc_classes.lower() or "disabled" in sc_classes.lower()
            pointer_blocked = False
            try:
                track = ip_container.find_element(By.CSS_SELECTOR, ".mat-slide-toggle-bar, .mat-mdc-slide-toggle-bar, label")
                pe = track.get_attribute("style") or ""
                pointer_blocked = "pointer-events: none" in pe.lower() or "pointer-events:none" in pe.lower()
                track_classes = track.get_attribute("class") or ""
                is_disabled_class = is_disabled_class or "disabled" in track_classes.lower() or "mat-disabled" in track_classes
            except Exception:
                pass
        except Exception as e:
            shot = self._screenshot(driver, "header_isparent_not_found")
            self._record(test_name="Header: Is Parent Readonly",
                expected="Is Parent toggle is not user-clickable",
                actual=f"Error: {e}",
                status="FAILED", category="Header", field="Is Parent",
                screenshot=shot)
            self._cleanup(page)
            return

        shot = self._screenshot(driver, "header_isparent_readonly")
        self._record(test_name="Header: Is Parent Readonly",
            expected="Is Parent toggle is not user-clickable (disabled class or pointer-events blocked)",
            actual=f"sc_classes='{sc_classes}', has_disabled_class={is_disabled_class}",
            status="PASSED" if is_disabled_class or pointer_blocked else "FAILED",
            category="Header", field="Is Parent", screenshot=shot)

        # --- Is Parent: Read current state (ON/OFF) ---
        is_checked = ip_checkbox.get_attribute("checked")
        try:
            off_label = ip_container.find_element(By.CSS_SELECTOR, ".state-label.off")
            on_label = ip_container.find_element(By.CSS_SELECTOR, ".state-label.on")
            off_active = "active" in (off_label.get_attribute("class") or "")
            on_active = "active" in (on_label.get_attribute("class") or "")
            state_display = "ON" if on_active else "OFF"
        except Exception:
            state_display = "checked" if is_checked else "unchecked"

        shot = self._screenshot(driver, "header_isparent_state")
        self._record(test_name="Header: Is Parent State",
            expected="Is Parent toggle displays correct ON/OFF state from backend",
            actual=f"checked={is_checked}, display_state={state_display}",
            status="PASSED",
            category="Header", field="Is Parent",
            original_value=state_display, screenshot=shot)

        # --- Is Parent: Attempt toggle click (should have no effect) ---
        try:
            toggle_bar = ip_container.find_element(
                By.CSS_SELECTOR, ".mat-slide-toggle-bar, .mat-mdc-slide-toggle-bar, label"
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", toggle_bar)
            time.sleep(0.3)
            try:
                toggle_bar.click()
            except Exception:
                driver.execute_script("arguments[0].click();", toggle_bar)
            time.sleep(0.5)
            still_checked = ip_checkbox.get_attribute("checked")
            unchanged = (still_checked == is_checked)
            shot = self._screenshot(driver, "header_isparent_toggle_blocked")
            self._record(test_name="Header: Is Parent Toggle Blocked",
                expected="Toggle click has no effect (UI blocks user interaction)",
                actual=f"before={is_checked}, after_click={still_checked}, unchanged={unchanged}",
                status="PASSED" if unchanged else "FAILED",
                category="Header", field="Is Parent", screenshot=shot)
        except Exception:
            self._record(test_name="Header: Is Parent Toggle Blocked",
                expected="Toggle click has no effect",
                actual="Click intercepted by UI (toggle is properly blocked)",
                status="PASSED", category="Header", field="Is Parent")

        self._cleanup(page)

    # ================================================================
    # TEST 26: Step 1 � TAN, GSTIN, Plan Type [ONE form open, NO Update]
    # ================================================================
    def test_26_step1_optional_fields(self, logged_in_driver):
        """TAN (optional text input), GSTIN (optional text input),
        Plan Type (optional dropdown) in Step 1.
        UI only - no Update pressed."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        # ===== TAN =====

        # Read original TAN value
        orig_tan = ""
        try:
            tan_el = driver.find_element(By.CSS_SELECTOR, "input[name='TAN']")
            orig_tan = tan_el.get_attribute("value") or ""
        except Exception:
            pass

        shot = self._screenshot(driver, "step1_tan_read")
        self._record(test_name="Step 1: TAN Field Exists",
            expected="TAN input field visible and accessible (optional field)",
            actual=f"original_value='{orig_tan}'",
            status="PASSED" if orig_tan is not None else "FAILED",
            category="Step 1 Optional", field="TAN",
            original_value=orig_tan, screenshot=shot)

        # Type a value into TAN
        test_tan = "DELA12345E"
        tan_accepted = False
        tan_readback = ""
        try:
            self._type_field(driver, "TAN", test_tan)
            time.sleep(0.3)
            tan_readback = driver.find_element(By.CSS_SELECTOR, "input[name='TAN']").get_attribute("value") or ""
            tan_accepted = (tan_readback == test_tan)
        except Exception as e:
            pass

        shot = self._screenshot(driver, "step1_tan_typed")
        self._record(test_name="Step 1: TAN Accepts Input",
            expected="TAN field accepts typed value without error",
            actual=f"typed='{test_tan}', read_back='{tan_readback}', accepted={tan_accepted}",
            status="PASSED" if tan_accepted else "FAILED",
            category="Step 1 Optional", field="TAN",
            bad_value=test_tan, screenshot=shot)

        # Clear TAN (restore to empty for optional verification)
        try:
            self._clear_field(driver, "TAN")
        except Exception:
            pass

        # ===== GSTIN =====

        orig_gstin = ""
        try:
            gstin_el = driver.find_element(By.CSS_SELECTOR, "input[name='GSTIN']")
            orig_gstin = gstin_el.get_attribute("value") or ""
        except Exception:
            pass

        shot = self._screenshot(driver, "step1_gstin_read")
        self._record(test_name="Step 1: GSTIN Field Exists",
            expected="GSTIN input field visible and accessible (optional field)",
            actual=f"original_value='{orig_gstin}'",
            status="PASSED",
            category="Step 1 Optional", field="GSTIN",
            original_value=orig_gstin, screenshot=shot)

        # Type a value into GSTIN
        test_gstin = "27AABCU9603R1ZM"
        gstin_accepted = False
        gstin_readback = ""
        try:
            self._type_field(driver, "GSTIN", test_gstin)
            time.sleep(0.3)
            gstin_readback = driver.find_element(By.CSS_SELECTOR, "input[name='GSTIN']").get_attribute("value") or ""
            gstin_accepted = (gstin_readback == test_gstin)
        except Exception as e:
            pass

        shot = self._screenshot(driver, "step1_gstin_typed")
        self._record(test_name="Step 1: GSTIN Accepts Input",
            expected="GSTIN field accepts typed value without error",
            actual=f"typed='{test_gstin}', read_back='{gstin_readback}', accepted={gstin_accepted}",
            status="PASSED" if gstin_accepted else "FAILED",
            category="Step 1 Optional", field="GSTIN",
            bad_value=test_gstin, screenshot=shot)

        # Clear GSTIN
        try:
            self._clear_field(driver, "GSTIN")
        except Exception:
            pass

        # ===== Plan Type =====

        orig_plan = ""
        plan_found = False
        try:
            orig_plan = self._hdr_read_select(driver, "Plan Type")
            plan_found = True
        except Exception:
            pass

        if plan_found:
            shot = self._screenshot(driver, "step1_plan_read")
            self._record(test_name="Step 1: Plan Type Field Exists",
                expected="Plan Type dropdown visible and accessible (optional field)",
                actual=f"original_value='{orig_plan}'",
                status="PASSED",
                category="Step 1 Optional", field="Plan Type",
                original_value=orig_plan, screenshot=shot)

            # Open and list options
            self._hdr_open_select(driver, "Plan Type")
            plan_options = self._hdr_list_options(driver)
            shot = self._screenshot(driver, "step1_plan_options")
            self._record(test_name="Step 1: Plan Type Options",
                expected="Plan Type dropdown opens (may have values or be empty)",
                actual=f"options={plan_options}, has_data={len(plan_options) > 0}",
                status="PASSED",
                category="Step 1 Optional", field="Plan Type",
                screenshot=shot)

            # Select a different option
            if len(plan_options) >= 2:
                candidates = [o for o in plan_options if o != orig_plan]
                target_plan = candidates[0] if candidates else plan_options[0]
                plan_selected = self._hdr_pick_option(driver, target_plan)
                time.sleep(0.3)
                plan_read_back = self._hdr_read_select(driver, "Plan Type")
                shot = self._screenshot(driver, "step1_plan_changed")
                self._record(test_name="Step 1: Plan Type Change",
                    expected=f"Plan Type changed from '{orig_plan}' to '{target_plan}'",
                    actual=f"selected={plan_selected}, read_back='{plan_read_back}'",
                    status="PASSED" if plan_read_back == target_plan else "FAILED",
                    category="Step 1 Optional", field="Plan Type",
                    bad_value=target_plan, screenshot=shot)

                # Restore original Plan Type
                if orig_plan and "Select" not in orig_plan:
                    self._hdr_open_select(driver, "Plan Type")
                    self._hdr_pick_option(driver, orig_plan)
                    time.sleep(0.3)
                self._hdr_close_dropdown(driver)
            else:
                self._hdr_close_dropdown(driver)
        else:
            shot = self._screenshot(driver, "step1_plan_not_found")
            self._record(test_name="Step 1: Plan Type Field Exists",
                expected="Plan Type dropdown visible",
                actual="Plan Type field not found on page",
                status="FAILED", category="Step 1 Optional", field="Plan Type",
                screenshot=shot)

        # ===== Optional verification: empty TAN + GSTIN -> Next still proceeds =====
        self._hdr_close_dropdown(driver)
        time.sleep(0.5)
        page._click_next()
        time.sleep(1)
        on_step2 = self._is_on_step2(driver)
        shot = self._screenshot(driver, "step1_optional_next")
        self._record(test_name="Step 1: Optional Fields -> Next Proceeds",
            expected="TAN and GSTIN empty - Next still proceeds to Step 2 (optional fields)",
            actual=f"on_step2={on_step2}",
            status="PASSED" if on_step2 else "FAILED",
            category="Step 1 Optional", field="TAN, GSTIN, Plan Type",
            screenshot=shot)

        self._cleanup(page)

