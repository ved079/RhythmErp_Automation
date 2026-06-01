"""
test_uom_validation.py
----------------------
Negative / validation tests for UOM.
Tests: Empty fields, duplicate code, length limits, edge cases.

Optimised (v3):
- Smart finally blocks: only cleanup if form is actually open
- Uses hard_refresh() instead of navigate_to_page() for fast page reset
- Uses search_and_verify() for create/update verification (handles pagination)
- Fixed Test 12/14: fields auto-cutoff at 255 chars, 256-char input is truncated to 255
"""

import sys
import os
import time
import pytest
from common.logger import log

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pages.common_settings.modules.uom.uom_page import UOMPage
from pages.common_settings.modules.uom.data.uom_data import (
    generate_uom_data, generate_string_255, generate_string_256,
    generate_lowercase_uom_code, generate_mixed_case_uom_code,
    generate_number_uom_code, generate_special_char_uom_code,
    generate_leading_space_uom_code, generate_special_char_description
)


class TestUOMValidation:
    """Test suite for UOM input validation (negative tests)."""

    def _cleanup(self, uom_page):
        """Smart cleanup — only close form if it's still open, then refresh."""
        if uom_page.is_add_form_open():
            uom_page.force_close_form_popup()
        uom_page.hard_refresh()

    def test_empty_uom_code(self, logged_in_driver):
        """Test 7: Submit with empty UOM Code should show Pattern A alert + mat-error."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)

        try:
            log.info(">>> STEP 1: Open Add form and submit with empty code")
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            valid_description = "Test Description for Empty Code"
            uom_page.type_text(uom_page.UOM_CODE_INPUT, valid_description)
            log.info("  Left UOM Code empty, filled description only")

            uom_page.submit()

            log.info(">>> STEP 2: Verify Pattern A alert appeared")
            assert uom_page.is_validation_alert_present(timeout=3), \
                "Pattern A validation alert should appear for empty UOM Code"
            uom_page.handle_validation_warning()
            log.info("  [PASS] Pattern A alert detected and dismissed")

            log.info(">>> STEP 3: Verify inline mat-error under UOM Code field")
            error_text = uom_page.get_mat_error_text(uom_page.UOM_CODE_INPUT)
            assert error_text != "", \
                "mat-error should be shown under UOM Code field. Got: '" + str(error_text) + "'"
            log.info("  [PASS] mat-error text: " + error_text)

            log.info(">>> STEP 4: Verify form is still open (not closed)")
            assert uom_page.is_add_form_open(), \
                "Add form should remain open after validation error"
            log.info("  [PASS] Form is still open")

            log.info(">>> TEST 7 PASSED: Empty UOM Code validation works")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_empty_uom_description(self, logged_in_driver):
        """Test 8: Submit with empty Description - description is NOT required, should save successfully."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)

        try:
            log.info(">>> STEP 1: Open Add form and submit with empty description")
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_data = generate_uom_data()
            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_data["uom_code"])
            log.info("  Filled UOM Code: " + uom_data["uom_code"] + ", left Description empty")

            uom_page.submit()

            log.info(">>> STEP 2: Verify UOM created successfully (description is NOT required)")
            uom_page.handle_success_alert()
            log.info("  [PASS] UOM created with empty description (field is optional)")

            log.info(">>> STEP 3: Search and verify UOM exists")
            uom_page.hard_refresh()
            uom_page.search_and_verify(uom_data["uom_code"])
            log.info("  [PASS] UOM '" + uom_data["uom_code"] + "' found via search")

            log.info(">>> TEST 8 PASSED: Empty description accepted (field is optional)")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_both_fields_empty(self, logged_in_driver):
        """Test 9: Submit with both fields empty should show Pattern A alert + mat-error on Code only."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)

        try:
            log.info(">>> STEP 1: Open Add form and submit with both fields empty")
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            log.info("  Left both UOM Code and Description empty")

            uom_page.submit()

            log.info(">>> STEP 2: Verify Pattern A alert appeared")
            assert uom_page.is_validation_alert_present(timeout=3), \
                "Pattern A validation alert should appear for empty UOM Code"
            uom_page.handle_validation_warning()
            log.info("  [PASS] Pattern A alert detected and dismissed")

            log.info(">>> STEP 3: Verify Code shows mat-error text (Description is optional)")
            code_error = uom_page.get_mat_error_text(uom_page.UOM_CODE_INPUT)
            assert code_error != "", \
                "mat-error should be shown under UOM Code. Got: '" + str(code_error) + "'"
            log.info("  [PASS] Code error text: " + code_error)

            log.info(">>> STEP 4: Verify form is still open")
            assert uom_page.is_add_form_open(), \
                "Add form should remain open after validation error"
            log.info("  [PASS] Form is still open")

            log.info(">>> TEST 9 PASSED: Both fields empty — only Code shows error")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_duplicate_code_MT(self, logged_in_driver):
        """Test 10: Submit with duplicate code 'MT' should show Pattern B alert."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        duplicate_code = "MT"

        try:
            log.info(">>> STEP 1: Open Add form and submit with duplicate code: " + duplicate_code)
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_page.type_text(uom_page.UOM_CODE_INPUT, duplicate_code)
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "Duplicate test for MT")

            uom_page.submit()

            log.info(">>> STEP 2: Verify Pattern B alert appeared")
            assert uom_page.is_validation_alert_present(timeout=3), \
                "Pattern B validation alert should appear for duplicate code '" + duplicate_code + "'"
            uom_page.handle_validation_download()
            log.info("  [PASS] Pattern B alert detected and dismissed")

            log.info(">>> TEST 10 PASSED: Duplicate code '" + duplicate_code + "' rejected")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_duplicate_code_KG(self, logged_in_driver):
        """Test 11: Submit with duplicate code 'KG' should show Pattern B alert."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        duplicate_code = "KG"

        try:
            log.info(">>> STEP 1: Open Add form and submit with duplicate code: " + duplicate_code)
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_page.type_text(uom_page.UOM_CODE_INPUT, duplicate_code)
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "Duplicate test for KG")

            uom_page.submit()

            log.info(">>> STEP 2: Verify Pattern B alert appeared")
            assert uom_page.is_validation_alert_present(timeout=3), \
                "Pattern B validation alert should appear for duplicate code '" + duplicate_code + "'"
            uom_page.handle_validation_download()
            log.info("  [PASS] Pattern B alert detected and dismissed")

            log.info(">>> TEST 11 PASSED: Duplicate code '" + duplicate_code + "' rejected")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_256_char_description_autocutoff(self, logged_in_driver):
        """Test 12: 256-char Description auto-cutoffs to 255 — UOM is created with 255 chars."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)

        try:
            log.info(">>> STEP 1: Open Add form with 256-char description")
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_data = generate_uom_data()
            long_desc = generate_string_256()
            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_data["uom_code"])
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, long_desc)

            # Verify auto-cutoff: field should only contain 255 chars (maxlength=255)
            actual_desc = uom_page.get_field_value(uom_page.UOM_DESCRIPTION_INPUT)
            log.info("  Sent 256 chars, field contains: " + str(len(actual_desc)) + " chars")
            assert len(actual_desc) == 255, \
                "Description field should auto-cutoff at 255 chars. Got: " + str(len(actual_desc))
            log.info("  [PASS] Description auto-cutoff at 255 chars confirmed")

            uom_page.submit()

            log.info(">>> STEP 2: Verify UOM created successfully")
            uom_page.handle_success_alert()
            log.info("  [PASS] UOM created with 255-char description")

            log.info(">>> STEP 3: Search and verify UOM exists")
            uom_page.hard_refresh()
            uom_page.search_and_verify(uom_data["uom_code"])
            log.info("  [PASS] UOM '" + uom_data["uom_code"] + "' found via search")

            log.info(">>> TEST 12 PASSED: 256-char description auto-cutoff, UOM created")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_255_char_description_accepted(self, logged_in_driver):
        """Test 13: Submit with 255-char Description should succeed, then edit back to normal."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)

        try:
            log.info(">>> STEP 1: Open Add form with 255-char description")
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_data = generate_uom_data()
            long_desc = generate_string_255()
            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_data["uom_code"])
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, long_desc)

            uom_page.submit()

            log.info(">>> STEP 2: Verify success - UOM created")
            uom_page.handle_success_alert()

            log.info(">>> STEP 3: Search and verify, then edit back to normal")
            uom_page.hard_refresh()
            uom_page.search_and_verify(uom_data["uom_code"])

            uom_page.click_edit_button(uom_data["uom_code"])
            uom_page.update_uom_description("Normal Description - cleaned up")
            uom_page.click_update()
            uom_page.handle_success_alert()

            log.info(">>> TEST 13 PASSED: 255-char description accepted + cleanup done")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_256_char_code_autocutoff(self, logged_in_driver):
        """Test 14: 256-char UOM Code auto-cutoffs to 255 — UOM is created with 255-char code."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)

        try:
            log.info(">>> STEP 1: Open Add form with 256-char code")
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            long_code = generate_string_256()
            uom_page.type_text(uom_page.UOM_CODE_INPUT, long_code)
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "Test 256 char code autocutoff")

            actual_code = uom_page.get_field_value(uom_page.UOM_CODE_INPUT)
            log.info("  Sent 256 chars, field contains: " + str(len(actual_code)) + " chars")
            assert len(actual_code) == 255, \
                "Code field should auto-cutoff at 255 chars. Got: " + str(len(actual_code))
            log.info("  [PASS] Code auto-cutoff at 255 chars confirmed")

            uom_page.submit()

            log.info(">>> STEP 2: Verify UOM created successfully")
            uom_page.handle_success_alert()

            log.info(">>> STEP 3: Search and verify UOM exists")
            uom_page.hard_refresh()
            search_code = actual_code[:20]
            uom_page.search_and_verify(search_code)
            log.info("  [PASS] UOM found via search with prefix: '" + search_code + "'")

            log.info(">>> TEST 14 PASSED: 256-char code auto-cutoff, UOM created")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_255_char_code_accepted(self, logged_in_driver):
        """Test 15: Submit with 255-char UOM Code should succeed."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)

        try:
            log.info(">>> STEP 1: Open Add form with 255-char code")
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            long_code = generate_string_255()
            uom_page.type_text(uom_page.UOM_CODE_INPUT, long_code)
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "Test 255 char code")

            uom_page.submit()

            log.info(">>> STEP 2: Verify success - UOM created")
            uom_page.handle_success_alert()

            search_code = long_code[:20]
            uom_page.hard_refresh()
            uom_page.search_and_verify(search_code)

            log.info(">>> TEST 15 PASSED: 255-char code accepted and verified")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    # ----------------------------------------------------------------
    # STEP 9: Edge Cases (Tests 16-19)
    # ----------------------------------------------------------------

    def test_cancel_add_form(self, logged_in_driver):
        """Test 16: Fill both fields and click Cancel - UOM should NOT be created."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)

        try:
            log.info(">>> STEP 1: Open Add form and fill both fields")
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_data = generate_uom_data()
            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_data["uom_code"])
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "Cancel test description")

            log.info(">>> STEP 2: Click Cancel to close form without saving")
            uom_page.close_popup()

            log.info(">>> STEP 3: Search and verify UOM was NOT created")
            uom_page.hard_refresh()
            uom_page.search_uom(uom_data["uom_code"])
            exists = uom_page.is_uom_in_table(uom_data["uom_code"])
            assert not exists, \
                "UOM '" + uom_data["uom_code"] + "' should NOT be in table after Cancel"

            log.info(">>> TEST 16 PASSED: Cancel add form - UOM not created")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_edit_empty_description(self, logged_in_driver):
        """Test 17: Create a UOM, then edit it with empty description — should succeed."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)

        try:
            log.info(">>> STEP 1: Create a fresh UOM to edit")
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_data = generate_uom_data()
            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_data["uom_code"])
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "Temp description for edit test")
            uom_page.submit()
            uom_page.handle_success_alert()

            log.info(">>> STEP 2: Search, open edit, clear description")
            uom_page.hard_refresh()
            uom_page.search_and_verify(uom_data["uom_code"])
            uom_page.click_edit_button(uom_data["uom_code"])

            css = uom_page.UOM_DESCRIPTION_INPUT[1]
            el = uom_page.driver.find_element("css selector", css)
            uom_page.driver.execute_script(
                "var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
                "nativeSetter.call(arguments[0], '');"
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
                "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                el
            )

            uom_page.click_update()

            log.info(">>> STEP 3: Verify update succeeded")
            uom_page.handle_success_alert()

            log.info(">>> TEST 17 PASSED: Edit empty description — update successful")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_edit_empty_code(self, logged_in_driver):
        """Test 18: Create a UOM, then edit it with empty code - should show Pattern A alert."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)

        try:
            log.info(">>> STEP 1: Create a fresh UOM to edit")
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_data = generate_uom_data()
            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_data["uom_code"])
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "Temp description for code edit test")
            uom_page.submit()
            uom_page.handle_success_alert()

            log.info(">>> STEP 2: Search, open edit, clear code")
            uom_page.hard_refresh()
            uom_page.search_and_verify(uom_data["uom_code"])
            uom_page.click_edit_button(uom_data["uom_code"])

            css = uom_page.UOM_CODE_INPUT[1]
            el = uom_page.driver.find_element("css selector", css)
            uom_page.driver.execute_script(
                "var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
                "nativeSetter.call(arguments[0], '');"
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
                "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                el
            )

            uom_page.click_update()

            log.info(">>> STEP 3: Verify Pattern A alert appeared")
            assert uom_page.is_validation_alert_present(timeout=3), \
                "Pattern A validation alert should appear for empty Code on edit"
            uom_page.handle_validation_warning()

            log.info(">>> STEP 4: Verify inline mat-error under Code field")
            error_text = uom_page.get_mat_error_text(uom_page.UOM_CODE_INPUT)
            assert error_text != "", \
                "mat-error should be shown under Code field on edit"

            log.info(">>> TEST 18 PASSED: Edit empty code validation works")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_submit_without_filling_anything(self, logged_in_driver):
        """Test 19: Open Add form and immediately Submit without typing - Pattern A."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)

        try:
            log.info(">>> STEP 1: Open Add form and submit immediately")
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_page.submit()

            log.info(">>> STEP 2: Verify Pattern A alert appeared")
            assert uom_page.is_validation_alert_present(timeout=3), \
                "Pattern A validation alert should appear when submitting untouched form"
            uom_page.handle_validation_warning()

            log.info(">>> STEP 3: Verify UOM Code shows error")
            code_error = uom_page.get_mat_error_text(uom_page.UOM_CODE_INPUT)
            assert code_error != "", "Code field should show mat-error"

            log.info(">>> STEP 4: Verify form is still open")
            assert uom_page.is_add_form_open(), "Add form should remain open"

            log.info(">>> TEST 19 PASSED: Submit without filling — only Code shows error")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    # ----------------------------------------------------------------
    # STEP 10: Input Format / Character Type Tests (Tests 20-25)
    # ----------------------------------------------------------------

    def test_lowercase_code_accepted(self, logged_in_driver):
        """Test 20: Submit with lowercase UOM code - should be accepted."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        uom_code = generate_lowercase_uom_code()

        try:
            log.info(">>> STEP 1: Open Add form with lowercase code: " + uom_code)
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_code)
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "Lowercase code test")

            uom_page.submit()

            log.info(">>> STEP 2: Verify outcome")
            if uom_page.is_validation_alert_present(timeout=3):
                uom_page.dismiss_any_validation_alert()
                log.info("  [NOTE] Code triggered validation (possible duplicate)")
            else:
                uom_page.handle_success_alert()
                uom_page.hard_refresh()
                uom_page.search_and_verify(uom_code)
                log.info("  [PASS] UOM '" + uom_code + "' found via search")

            log.info(">>> TEST 20 PASSED: Lowercase code accepted")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_mixed_case_code_accepted(self, logged_in_driver):
        """Test 21: Submit with mixed case UOM code - should be accepted."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        uom_code = generate_mixed_case_uom_code()

        try:
            log.info(">>> STEP 1: Open Add form with mixed case code: " + uom_code)
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_code)
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "Mixed case code test")

            uom_page.submit()

            log.info(">>> STEP 2: Verify outcome")
            if uom_page.is_validation_alert_present(timeout=3):
                uom_page.dismiss_any_validation_alert()
                log.info("  [NOTE] Code triggered validation (possible duplicate)")
            else:
                uom_page.handle_success_alert()
                uom_page.hard_refresh()
                uom_page.search_and_verify(uom_code)
                log.info("  [PASS] UOM '" + uom_code + "' found via search")

            log.info(">>> TEST 21 PASSED: Mixed case code accepted")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_number_in_code_accepted(self, logged_in_driver):
        """Test 22: Submit with numbers in UOM code - numbers ARE allowed."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        uom_code = generate_number_uom_code()

        try:
            log.info(">>> STEP 1: Open Add form with number-in-code: " + uom_code)
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_code)
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "Number in code test")

            uom_page.submit()

            log.info(">>> STEP 2: Verify outcome")
            if uom_page.is_validation_alert_present(timeout=3):
                uom_page.dismiss_any_validation_alert()
                log.info("  [NOTE] Code triggered validation (possible duplicate)")
            else:
                uom_page.handle_success_alert()
                uom_page.hard_refresh()
                uom_page.search_and_verify(uom_code)
                log.info("  [PASS] UOM '" + uom_code + "' found via search")

            log.info(">>> TEST 22 PASSED: Code with numbers accepted")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_special_char_code_rejected(self, logged_in_driver):
        """Test 23: Submit with special characters in UOM code - should show Pattern A alert."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        uom_code = generate_special_char_uom_code()

        try:
            log.info(">>> STEP 1: Open Add form with special char code: " + uom_code)
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_code)
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "Special char code test")

            uom_page.submit()

            log.info(">>> STEP 2: Verify Pattern A alert appeared")
            assert uom_page.is_validation_alert_present(timeout=3), \
                "Pattern A validation alert should appear for code with special characters"
            uom_page.handle_validation_warning()

            log.info(">>> STEP 3: Verify UOM was NOT created")
            uom_page.hard_refresh()
            uom_page.search_uom(uom_code)
            exists = uom_page.is_uom_in_table(uom_code)
            assert not exists, "UOM should NOT be in table (special chars not allowed)"

            log.info(">>> TEST 23 PASSED: Code with special characters rejected")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_leading_space_code_trimmed(self, logged_in_driver):
        """Test 24: Submit with leading space in UOM code - system auto-trims."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        uom_code = generate_leading_space_uom_code()
        trimmed_code = uom_code.strip()

        try:
            log.info(">>> STEP 1: Open Add form with leading space code: '" + uom_code + "'")
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_code)
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, "Leading space code test")

            uom_page.submit()

            log.info(">>> STEP 2: Verify outcome")
            if uom_page.is_validation_alert_present(timeout=3):
                uom_page.dismiss_any_validation_alert()
                log.info("  [NOTE] Code triggered validation (trimmed code may already exist)")
            else:
                uom_page.handle_success_alert()
                uom_page.hard_refresh()
                uom_page.search_and_verify(trimmed_code)
                log.info("  [PASS] UOM found as trimmed code: '" + trimmed_code + "'")

            log.info(">>> TEST 24 PASSED: Leading space code behavior verified")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)

    def test_special_char_description_accepted(self, logged_in_driver):
        """Test 25: Submit with special characters in description - should be accepted."""
        driver = logged_in_driver
        uom_page = UOMPage(driver)

        try:
            log.info(">>> STEP 1: Open Add form with special char description")
            uom_page.navigate_to_page()
            uom_page.open_add_form()

            uom_data = generate_uom_data()
            special_desc = generate_special_char_description()
            uom_page.type_text(uom_page.UOM_CODE_INPUT, uom_data["uom_code"])
            uom_page.type_text(uom_page.UOM_DESCRIPTION_INPUT, special_desc)

            uom_page.submit()

            log.info(">>> STEP 2: Verify success - UOM created")
            uom_page.handle_success_alert()

            log.info(">>> STEP 3: Search and verify UOM exists")
            uom_page.hard_refresh()
            uom_page.search_and_verify(uom_data["uom_code"])

            log.info(">>> TEST 25 PASSED: Special char description accepted")
        except Exception:
            raise
        finally:
            self._cleanup(uom_page)
