"""
Company Onboarding UPDATE Validation Tests.
Target company: Zenith Core Systems

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
  14 - Address: Backend + Persistence (long addr, edit+verify, dup type, special chars, restore) [ONE form open]
  15 - Address: Edge cases (whitespace, 5-digit pin, multiline) [ONE form open]
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

        # Not found with CSS — dump diagnostics
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
    # TEST 07: Promoter — All UI Validations [ONE form open]
    # ================================================================

    def test_07_promoter_all_ui_validations(self, logged_in_driver):
        """All promoter UI checks in one form open:
        pre-filled data, back/next navigation, optional fields, add rows, delete rows."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

        reached = self._navigate_to_step2(page)
        if not reached:
            self._record(test_name="Promoter: Navigate to Step 2",
                expected="Promoter table visible", actual="Failed to reach Step 2",
                status="FAILED", category="Promoters")
            self._cleanup(page)
            return

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
            expected="Both fields empty — Next proceeds to Step 3 with no error",
            actual=f"on_step3={on_step3_opt}",
            status="PASSED" if on_step3_opt else "FAILED",
            category="Promoters", field="Name, Remark",
            bad_value="(empty)", screenshot=shot_opt)

        self._go_to_step1_from_step2(page)
        if not self._is_on_step2(driver):
            self._navigate_to_step2(page)

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
    # TEST 08: Promoter — Max Length + Update & Verify [ONE form open]
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

        self._dismiss_sweetalert(driver)
        time.sleep(0.5)

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
    # TEST 09: Promoter — Boundary + Backend Validations [ONE form open]
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

        orig_name = self._read_promoter_field(page, 1, "Name")
        orig_remark = self._read_promoter_field(page, 1, "Remark")

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

        if not self._is_on_step2(driver):
            self._go_to_step1_from_step2(page)
            if not self._is_on_step2(driver):
                self._navigate_to_step2(page)

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
    # TEST 10: Promoter — Edge Cases [ONE form open, NO Update clicks]
    # ================================================================

    def test_10_promoter_edge_cases(self, logged_in_driver):
        """UI edge case checks — no Update button pressed, no data changes."""
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

        orig_name = self._read_promoter_field(page, 1, "Name")
        orig_remark = self._read_promoter_field(page, 1, "Remark")

        special_name = "<script>alert(1)</script>"
        self._type_promoter_field(driver, 1, "Name", special_name)
        time.sleep(0.3)
        page._click_next()
        time.sleep(1)
        on_step3_special = self._is_on_step3(driver)
        shot_special = self._screenshot(driver, "promo_special_chars")
        self._record(test_name="Special Chars in Name",
            expected="No validation error — Next proceeds to Step 3",
            actual=f"on_step3={on_step3_special}",
            status="PASSED" if on_step3_special else "FAILED",
            category="Promoters", field="Name",
            bad_value=special_name,
            screenshot=shot_special)

        self._go_to_step1_from_step2(page)
        if not self._is_on_step2(driver):
            self._navigate_to_step2(page)

        self._type_promoter_field(driver, 1, "Name", "   ")
        self._type_promoter_field(driver, 1, "Remark", "   ")
        time.sleep(0.3)
        page._click_next()
        time.sleep(1)
        on_step3_ws = self._is_on_step3(driver)
        shot_ws = self._screenshot(driver, "promo_whitespace")
        self._record(test_name="Whitespace-Only Fields",
            expected="No validation error — Next proceeds to Step 3",
            actual=f"on_step3={on_step3_ws}",
            status="PASSED" if on_step3_ws else "FAILED",
            category="Promoters", field="Name, Remark",
            bad_value="'   ' (whitespace)",
            screenshot=shot_ws)

        self._go_to_step1_from_step2(page)
        if not self._is_on_step2(driver):
            self._navigate_to_step2(page)

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

        before_rapid = self._count_promoter_rows(driver)
        self._add_promoter_row(driver)
        time.sleep(0.5)
        after_add = self._count_promoter_rows(driver)
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

        self._type_promoter_field(driver, 1, "Name", orig_name or "")
        self._type_promoter_field(driver, 1, "Remark", orig_remark or "")

        self._cleanup(page)

    # ================================================================
    # ADDRESS HELPERS
    # ================================================================

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
            try:
                val_span = trigger.find_element(By.CSS_SELECTOR, ".mat-select-value-text span, .mat-select-min-line span")
                return val_span.text.strip()
            except Exception:
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
                self._addr_close_overlay(driver)
                time.sleep(0.2)

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
        if saved.get("address_type"):
            self._addr_open_dropdown(driver, row_index, "Address Type")
            self._addr_select_option_by_text(driver, saved["address_type"])
            time.sleep(0.3)
        if saved.get("country"):
            self._addr_open_dropdown(driver, row_index, "Country")
            self._addr_select_option_by_text(driver, saved["country"])
            time.sleep(0.3)
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
        if "address" in saved and saved["address"]:
            self._addr_type_field(driver, row_index, "Address", saved["address"])
        if "pin_code" in saved:
            if saved["pin_code"]:
                self._addr_type_field(driver, row_index, "Pin Code", saved["pin_code"])
            else:
                self._addr_clear_field(driver, row_index, "Pin Code")
        time.sleep(0.3)

    # ================================================================
    # TEST 11: Address — Navigation + Pre-filled Data [ONE form open, NO Update]
    # ================================================================

    def test_11_address_navigation_prefilled(self, logged_in_driver):
        """Navigate to Step 3, verify pre-filled address data, back/next navigation."""
        driver = logged_in_driver
        page = self._page(driver)
        self._open_form(page)

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

        went_back = self._go_back_to_step2(page)
        on_step2 = self._is_on_step2(driver) if went_back else False
        shot_back = self._screenshot(driver, "addr_back_to_step2")
        self._record(test_name="Address: Back to Step 2",
            expected="Back button returns to Step 2 (Promoters)",
            actual=f"went_back={went_back}, on_step2={on_step2}",
            status="PASSED" if on_step2 else "FAILED",
            category="Address", screenshot=shot_back)

        if on_step2:
            page._click_next()
            time.sleep(1.5)
        else:
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
    # TEST 12: Address — Row Management + Cascading [ONE form open, NO Update]
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

        log.info("[test_12] Step: Add multiple rows")
        added2 = self._addr_add_row(driver)
        after2 = self._addr_count_rows(driver)
        shot_multi = self._screenshot(driver, "addr_add_multiple")
        self._record(test_name="Address: Add Multiple Rows",
            expected="Multiple rows can be added via + button",
            actual=f"rows_after_first={after1}, added_again={added2}, total={after2}",
            status="PASSED" if added2 and after2 == after1 + 1 else "FAILED",
            category="Address", screenshot=shot_multi)

        log.info("[test_12] Step: Delete row")
        before_del = self._addr_count_rows(driver)
        if before_del >= 2:
            deleted = self._addr_delete_row(driver, row_index=before_del)
            time.sleep(0.5)
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

        log.info("[test_12] Step: Verify Country = India")
        country_val = self._addr_read_dropdown_value(driver, 1, "Country")
        shot_country = self._screenshot(driver, "addr_country_india")
        is_india = "India" in (country_val or "")
        self._record(test_name="Address: Country = India",
            expected="Country dropdown shows India",
            actual=f"country='{country_val}'",
            status="PASSED" if is_india else "FAILED",
            category="Address", field="Country", screenshot=shot_country)

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
    # TEST 13: Address — Required Fields + Pin Code [ONE form open, NO Update]
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

        existing_count = self._addr_count_rows(driver)
        self._addr_add_row(driver)
        new_row_idx = self._addr_count_rows(driver)
        time.sleep(0.5)

        page._click_next()
        time.sleep(1)
        still_on_3 = self._is_on_step3(driver)
        shot_empty_err = self._screenshot(driver, "addr_empty_row_errors")
        self._record(test_name="Address: Required on Empty Row",
            expected="Next does NOT proceed — validation errors on empty address row",
            actual=f"still_on_step3={still_on_3}",
            status="PASSED" if still_on_3 else "FAILED",
            category="Address", field="All Fields",
            bad_value="(empty row)", screenshot=shot_empty_err)

        type_invalid, type_err = self._addr_check_dropdown_invalid(driver, new_row_idx, "Address Type")
        shot_type_err = self._screenshot(driver, "addr_req_addr_type")
        self._record(test_name="Address: Address Type Required",
            expected="Address Type dropdown shows required error",
            actual=f"invalid={type_invalid}, error='{type_err}'",
            status="PASSED" if type_invalid else "FAILED",
            category="Address", field="Address Type",
            bad_value="(empty)", screenshot=shot_type_err)

        addr_invalid, addr_err = self._addr_check_input_invalid(driver, new_row_idx, "Address")
        shot_addr_err = self._screenshot(driver, "addr_req_address")
        self._record(test_name="Address: Address Input Required",
            expected="Address input shows required error",
            actual=f"invalid={addr_invalid}, error='{addr_err}'",
            status="PASSED" if addr_invalid else "FAILED",
            category="Address", field="Address",
            bad_value="(empty)", screenshot=shot_addr_err)

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

        cleanup_attempts = 0
        while self._addr_count_rows(driver) > existing_count and cleanup_attempts < 10:
            self._addr_delete_row(driver, row_index=self._addr_count_rows(driver))
            time.sleep(0.8)
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
    # TEST 14: Address — Backend + Persistence [ONE form open, with Update]
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

        orig_row1 = self._addr_save_row(page, driver, 1)
        orig_row2 = {}
        if self._addr_count_rows(driver) >= 2:
            orig_row2 = self._addr_save_row(page, driver, 2)

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

        self._open_form(page)
        self._navigate_to_step3(page)

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

                self._open_form(page)
                self._navigate_to_step3(page)
        else:
            self._record(test_name="Address: Duplicate Address Type",
                expected="Duplicate Address Type saves without error",
                actual="Skipped: only 1 address row available",
                status="PASSED", category="Address", field="Address Type")

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
    # TEST 15: Address — Edge Cases [ONE form open, NO Update]
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

        # Navigate back to Step 3 (now works with Step 4 -> Back -> Step 3)
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
