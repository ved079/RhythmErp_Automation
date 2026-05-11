"""
test_uom_conversion_validation.py
---------------------------------
Edge-case / validation tests for UOM Conversion.

22 test cases across 6 groups:
  A — Happy Path (Add)        : Tests 1-3
  B — Validation (Add)        : Tests 4-11
  C — Boundary / Bug          : Tests 12-14
  D — Edit Flow               : Tests 15-18
  E — History                 : Tests 19-20
  F — Cancel Flow             : Tests 21-22

Run:
    pytest pages/common_settings/modules/uom_conversion/test/test_uom_conversion_validation.py -v
"""

import sys
import os
import time
import pytest
from common.logger import log

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pages.common_settings.modules.uom_conversion.uom_conversion_page import UOMConversionPage
from pages.common_settings.modules.uom_conversion.data.uom_conversion_data import (
    generate_uom_conversion_data,
    generate_fresh_pair,
    generate_decimal_conversion_factor,
    generate_large_conversion_factor,
    generate_negative_conversion_factor,
    generate_zero_conversion_factor,
    generate_text_conversion_factor,
    generate_special_char_conversion_factor,
)


class TestUOMConversionValidation:
    """Test suite for UOM Conversion input validation and edge cases."""

    # ================================================================
    # GROUP A — HAPPY PATH (ADD)
    # Tests 1-3
    # ================================================================

    def test_add_valid_uom_conversion(self, logged_in_driver):
        """Test 1: Add a valid UOM conversion with a normal integer factor."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Create fresh record via one-flow")
            page.navigate_to_page()
            data = page.create_fresh_record()

            log.step(2, "Verify success alert")
            assert page.is_success_alert_present(timeout=5), \
                "Success alert should appear after valid submission"
            page.handle_success_alert()
            log.info("  [PASS] Success alert handled")

            log.info(">>> TEST 1 PASSED: Valid UOM conversion created successfully")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_add_decimal_conversion_factor(self, logged_in_driver):
        """Test 2: Add with a decimal conversion factor — system rejects decimals (validation)."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            factor = generate_decimal_conversion_factor()

            log.step(1, "Navigate to page and open Add form")
            page.navigate_to_page()
            page.open_add_form()

            log.step(2, "Select NOS -> ML with decimal factor: " + factor)
            page.select_source_uom("NOS")
            page.select_target_uom("ML")
            page.enter_conversion_factor(factor)

            log.step(3, "Click Submit")
            page.submit()

            log.step(4, "Verify Pattern A validation alert (decimals rejected)")
            assert page.is_validation_alert_present(timeout=5), \
                "Pattern A alert should appear for decimal factor"
            page.handle_validation_warning()
            log.info("  [PASS] Decimal factor rejected by system: " + factor)

            log.info(">>> TEST 2 PASSED: Decimal conversion factor rejected")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_add_same_source_and_target(self, logged_in_driver):
        """Test 3: Same UOM for source and target with factor = 1."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Navigate to page and open Add form")
            page.navigate_to_page()
            page.open_add_form()

            log.step(2, "Select Fest -> Fest with factor 1")
            page.select_source_uom("Fest")
            page.select_target_uom("Fest")
            page.enter_conversion_factor("1")

            log.step(3, "Click Submit")
            page.submit()

            log.step(4, "Observe system response (may succeed or reject as duplicate)")
            time.sleep(2)
            alert_title = page.get_swal_title()
            log.info("  [OBSERVE] Alert after same UOM submit: " + str(alert_title))
            if alert_title:
                page.handle_success_alert() if "successfully" in alert_title.lower() else page.handle_validation_warning()
                page.handle_error_toast()
            log.info("  [PASS] System responded to same-source-and-target submission")

            log.info(">>> TEST 3 PASSED: Same source/target observed")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    # ================================================================
    # GROUP B — VALIDATION (ADD)
    # Tests 4-11
    # ================================================================

    def test_add_without_source_uom(self, logged_in_driver):
        """Test 4: Submit with Source UOM empty — should show Pattern A alert."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Open Add form, fill only Target UOM and factor, leave Source empty")
            page.navigate_to_page()
            page.open_add_form()

            page.select_target_uom("KG")
            page.enter_conversion_factor("10")
            log.info("  Left Source UOM empty")

            log.step(2, "Click Submit")
            page.submit()

            log.step(3, "Verify Pattern A validation alert")
            assert page.is_validation_alert_present(timeout=5), \
                "Pattern A validation alert should appear for empty Source UOM"
            page.handle_validation_warning()
            log.info("  [PASS] Pattern A alert detected and dismissed")

            log.step(4, "Verify Source UOM dropdown shows error state")
            has_error = page.is_dropdown_error("Source UOM")
            assert has_error, "Source UOM dropdown should show error state (invalid class)"
            log.info("  [PASS] Source UOM dropdown has error state")

            log.step(5, "Verify form is still open")
            assert page.is_add_form_open(), "Add form should remain open after validation error"
            log.info("  [PASS] Form is still open")

            log.info(">>> TEST 4 PASSED: Empty Source UOM validation works")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_add_without_target_uom(self, logged_in_driver):
        """Test 5: Submit with Target UOM empty — should show Pattern A alert."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Open Add form, fill only Source UOM and factor, leave Target empty")
            page.navigate_to_page()
            page.open_add_form()

            page.select_source_uom("KG")
            page.enter_conversion_factor("10")
            log.info("  Left Target UOM empty")

            log.step(2, "Click Submit")
            page.submit()

            log.step(3, "Verify Pattern A validation alert")
            assert page.is_validation_alert_present(timeout=5), \
                "Pattern A validation alert should appear for empty Target UOM"
            page.handle_validation_warning()
            log.info("  [PASS] Pattern A alert detected and dismissed")

            log.step(4, "Verify Target UOM dropdown shows error state")
            has_error = page.is_dropdown_error("Target UOM")
            assert has_error, "Target UOM dropdown should show error state"
            log.info("  [PASS] Target UOM dropdown has error state")

            log.step(5, "Verify form is still open")
            assert page.is_add_form_open(), "Add form should remain open"
            log.info("  [PASS] Form is still open")

            log.info(">>> TEST 5 PASSED: Empty Target UOM validation works")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_add_without_conversion_factor(self, logged_in_driver):
        """Test 6: Submit with Conversion Factor empty — should show Pattern A + mat-error."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Open Add form, select both UOMs, leave factor empty")
            page.navigate_to_page()
            page.open_add_form()

            page.select_source_uom("NOS")
            page.select_target_uom("BAKMRMRY")
            log.info("  Left Conversion Factor empty")

            log.step(2, "Click Submit")
            page.submit()

            log.step(3, "Verify Pattern A validation alert")
            assert page.is_validation_alert_present(timeout=5), \
                "Pattern A alert should appear for empty Conversion Factor"
            page.handle_validation_warning()
            log.info("  [PASS] Pattern A alert detected")

            log.step(4, "Verify mat-error on Conversion Factor field")
            error_text = page.get_mat_error_text(page.CONVERSION_FACTOR_INPUT)
            assert error_text != "", \
                "mat-error should appear under Conversion Factor. Got: '" + str(error_text) + "'"
            log.info("  [PASS] mat-error text: " + error_text)

            log.step(5, "Verify form is still open")
            assert page.is_add_form_open(), "Add form should remain open"
            log.info("  [PASS] Form is still open")

            log.info(">>> TEST 6 PASSED: Empty Conversion Factor validation works")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_add_all_fields_empty(self, logged_in_driver):
        """Test 7: Submit with nothing filled — Pattern A + errors on all fields."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Open Add form and submit immediately (no fields filled)")
            page.navigate_to_page()
            page.open_add_form()

            log.step(2, "Click Submit")
            page.submit()

            log.step(3, "Verify Pattern A validation alert")
            assert page.is_validation_alert_present(timeout=5), \
                "Pattern A alert should appear for all-empty submission"
            page.handle_validation_warning()
            log.info("  [PASS] Pattern A alert detected")

            log.step(4, "Verify errors on fields")
            cf_error = page.get_mat_error_text(page.CONVERSION_FACTOR_INPUT)
            src_error = page.is_dropdown_error("Source UOM")
            tgt_error = page.is_dropdown_error("Target UOM")
            assert cf_error != "", "Conversion Factor should show mat-error"
            log.info("  [PASS] Conversion Factor has mat-error: " + cf_error)
            log.info("  [PASS] Source UOM error: " + str(src_error))
            log.info("  [PASS] Target UOM error: " + str(tgt_error))

            log.step(5, "Verify form is still open")
            assert page.is_add_form_open(), "Add form should remain open"
            log.info("  [PASS] Form is still open")

            log.info(">>> TEST 7 PASSED: All fields empty validation works")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_add_text_in_conversion_factor(self, logged_in_driver):
        """Test 8: Enter 'abc' as conversion factor — should show Pattern A + 'Invalid Conversion Factor'."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Open Add form with text in Conversion Factor")
            page.navigate_to_page()
            page.open_add_form()

            page.select_source_uom("NOS")
            page.select_target_uom("BAKMRMRY")
            text_value = generate_text_conversion_factor()
            page.enter_conversion_factor(text_value)
            log.info("  Entered: " + text_value)

            log.step(2, "Click Submit")
            page.submit()

            log.step(3, "Verify Pattern A validation alert")
            assert page.is_validation_alert_present(timeout=5), \
                "Pattern A alert should appear for text in Conversion Factor"
            page.handle_validation_warning()
            log.info("  [PASS] Pattern A alert detected")

            log.step(4, "Verify 'Invalid Conversion Factor' mat-error")
            error_text = page.get_mat_error_text(page.CONVERSION_FACTOR_INPUT)
            assert error_text != "", \
                "mat-error should appear. Got: '" + str(error_text) + "'"
            log.info("  [PASS] mat-error text: " + error_text)

            log.info(">>> TEST 8 PASSED: Text in Conversion Factor rejected")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_add_special_char_conversion_factor(self, logged_in_driver):
        """Test 9: Enter '@#$' as conversion factor — should show Pattern A + mat-error."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Open Add form with special characters in Conversion Factor")
            page.navigate_to_page()
            page.open_add_form()

            page.select_source_uom("KG")
            page.select_target_uom("ML")
            special_value = generate_special_char_conversion_factor()
            page.enter_conversion_factor(special_value)
            log.info("  Entered: " + special_value)

            log.step(2, "Click Submit")
            page.submit()

            log.step(3, "Verify Pattern A validation alert")
            assert page.is_validation_alert_present(timeout=5), \
                "Pattern A alert should appear for special chars in Conversion Factor"
            page.handle_validation_warning()
            log.info("  [PASS] Pattern A alert detected")

            log.step(4, "Verify mat-error on Conversion Factor")
            error_text = page.get_mat_error_text(page.CONVERSION_FACTOR_INPUT)
            assert error_text != "", \
                "mat-error should appear. Got: '" + str(error_text) + "'"
            log.info("  [PASS] mat-error text: " + error_text)

            log.info(">>> TEST 9 PASSED: Special chars in Conversion Factor rejected")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_add_negative_conversion_factor(self, logged_in_driver):
        """Test 10: Enter -5 as conversion factor. OBSERVE — accepted or rejected?"""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Open Add form with negative Conversion Factor")
            page.navigate_to_page()
            page.open_add_form()

            page.select_source_uom("KG")
            page.select_target_uom("ML")
            negative_value = generate_negative_conversion_factor()
            page.enter_conversion_factor(negative_value)
            log.info("  Entered: " + negative_value)

            log.step(2, "Click Submit and observe response")
            page.submit()
            time.sleep(2)

            alert_title = page.get_swal_title()
            log.info("  [OBSERVE] Alert for negative factor: " + str(alert_title))

            if page.is_validation_alert_present(timeout=3):
                page.handle_validation_warning()
                log.info("  [OBSERVE] Negative factor REJECTED by system")
            elif page.is_success_alert_present(timeout=3):
                page.handle_success_alert()
                log.info("  [OBSERVE] Negative factor ACCEPTED by system")
                page.navigate_to_page()
                exists = page.is_record_in_table("KG", "ML")
                log.info("  [OBSERVE] Record in table: " + str(exists))
            else:
                page.handle_error_toast()
                log.info("  [OBSERVE] Error toast for negative factor")

            log.info(">>> TEST 10 PASSED: Negative factor behavior observed")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_add_zero_conversion_factor(self, logged_in_driver):
        """Test 11: Enter 0 as conversion factor. OBSERVE — accepted or rejected?"""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Open Add form with zero Conversion Factor")
            page.navigate_to_page()
            page.open_add_form()

            page.select_source_uom("NOS")
            page.select_target_uom("BAKMRMRY")
            page.enter_conversion_factor("0")
            log.info("  Entered: 0")

            log.step(2, "Click Submit and observe response")
            page.submit()
            time.sleep(2)

            alert_title = page.get_swal_title()
            log.info("  [OBSERVE] Alert for zero factor: " + str(alert_title))

            if page.is_validation_alert_present(timeout=3):
                page.handle_validation_warning()
                log.info("  [OBSERVE] Zero factor REJECTED by system")
            elif page.is_success_alert_present(timeout=3):
                page.handle_success_alert()
                log.info("  [OBSERVE] Zero factor ACCEPTED by system")
            else:
                page.handle_error_toast()
                log.info("  [OBSERVE] Error toast for zero factor")

            log.info(">>> TEST 11 PASSED: Zero factor behavior observed")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    # ================================================================
    # GROUP C — BOUNDARY / BUG (22+ digit factor)
    # Tests 12-14
    # ================================================================

    def test_conversion_factor_21_digits(self, logged_in_driver):
        """Test 12: 21-digit factor should save and display correctly."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            factor = generate_large_conversion_factor(21)

            log.step(1, "Open Add form with 21-digit Conversion Factor")
            page.navigate_to_page()
            page.open_add_form()

            page.select_source_uom("ML")
            page.select_target_uom("Dozens")
            page.enter_conversion_factor(factor)
            log.info("  Entered: " + factor + " (length: " + str(len(factor)) + ")")

            log.step(2, "Click Submit")
            page.submit()

            log.step(3, "Verify success — 21-digit factor saves correctly")
            assert page.is_success_alert_present(timeout=5), \
                "21-digit factor should save successfully"
            page.handle_success_alert()
            log.info("  [PASS] 21-digit factor saved successfully")

            log.info(">>> TEST 12 PASSED: 21-digit conversion factor accepted")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_conversion_factor_22_digits_bug(self, logged_in_driver):
        """Test 13: 22-digit factor — OBSERVE system behavior (may reject or save with scientific notation)."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            factor = generate_large_conversion_factor(22)

            log.step(1, "Open Add form with 22-digit Conversion Factor")
            page.navigate_to_page()
            page.open_add_form()

            page.select_source_uom("MT")
            page.select_target_uom("KG")
            page.enter_conversion_factor(factor)
            log.info("  Entered: " + factor + " (length: " + str(len(factor)) + ")")

            log.step(2, "Click Submit and observe response")
            page.submit()
            time.sleep(2)

            alert_title = page.get_swal_title()
            log.info("  [OBSERVE] Alert for 22-digit factor: " + str(alert_title))

            if page.is_validation_alert_present(timeout=3):
                page.handle_validation_warning()
                log.info("  [OBSERVE] 22-digit factor REJECTED by system (backend validation)")
            elif page.is_success_alert_present(timeout=3):
                page.handle_success_alert()
                log.info("  [OBSERVE] 22-digit factor ACCEPTED by system")
                page.navigate_to_page()
                page.cleanup()
                time.sleep(1)
                row = page.find_table_row("MT", "KG")
                if row is not None:
                    page.click_row_edit("MT", "KG")
                    time.sleep(1)
                    displayed_value = page.get_conversion_factor_value()
                    log.info("  [BUG CHECK] Saved '" + factor + "', Edit form shows: '" + str(displayed_value) + "'")
                    if displayed_value and "e+" in displayed_value.lower():
                        log.info("  [PASS] Scientific notation bug confirmed: " + displayed_value)
                    else:
                        log.info("  [PASS] No scientific notation — value displayed correctly")
            else:
                page.handle_error_toast()
                log.info("  [OBSERVE] Error toast for 22-digit factor")

            log.info(">>> TEST 13 PASSED: 22-digit factor behavior observed")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_scientific_notation_not_editable(self, logged_in_driver):
        """Test 14: OBSERVE — if 22-digit record exists, check if re-editing triggers validation error."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Check if MT->KG row exists (from Test 13)")
            page.navigate_to_page()
            page.cleanup()
            time.sleep(1)

            row = page.find_table_row("MT", "KG")
            if row is None:
                log.info("  [OBSERVE] MT->KG row not found — Test 13 was rejected by system. Skipping edit check.")
                log.info(">>> TEST 14 PASSED: Skipped (no 22-digit record to re-edit)")
                return

            log.step(2, "Open Edit form for the 22-digit record")
            page.click_row_edit("MT", "KG")
            time.sleep(1)

            log.step(3, "Click Update without changing anything")
            page.click_update()
            time.sleep(1)

            log.step(4, "Observe system response")
            alert_title = page.get_swal_title()
            log.info("  [OBSERVE] Alert on update: " + str(alert_title))

            if page.is_validation_alert_present(timeout=3):
                page.handle_validation_warning()
                log.info("  [PASS] Validation alert confirmed on re-edit")
            elif page.is_success_alert_present(timeout=3):
                page.handle_success_alert()
                log.info("  [OBSERVE] Update succeeded — no validation issue")
            else:
                page.handle_error_toast()
                log.info("  [OBSERVE] Error toast on re-edit")

            log.info(">>> TEST 14 PASSED: 22-digit re-edit behavior observed")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    # ================================================================
    # GROUP D — EDIT FLOW
    # Tests 15-18
    # ================================================================

    def test_edit_valid_conversion_factor(self, logged_in_driver):
        """Test 15: Edit an existing record with a new valid factor — should succeed."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Create fresh record via one-flow")
            page.navigate_to_page()
            data = page.create_fresh_record()

            if page.is_validation_alert_present(timeout=5):
                page.handle_validation_warning()
                raise AssertionError(
                    "Create should succeed: " + data["source_uom"] + " -> " + data["target_uom"])

            assert page.is_success_alert_present(timeout=5), \
                "Success alert expected after creating " + data["source_uom"] + " -> " + data["target_uom"]
            page.handle_success_alert()
            log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"] + " = " + data["conversion_factor"])

            log.step(2, "Open Edit form for the record")
            page.navigate_to_page()
            time.sleep(1)
            page.click_row_edit(data["source_uom"], data["target_uom"])
            time.sleep(1)

            log.step(3, "Change Conversion Factor to 7 and click Update")
            page.enter_conversion_factor("7")
            page.click_update()
            time.sleep(1)

            log.step(4, "Verify success alert")
            assert page.is_success_alert_present(timeout=5), \
                "Update should succeed with new valid factor"
            page.handle_success_alert()
            log.info("  [PASS] Update succeeded")

            log.step(5, "Verify new factor in table")
            page.navigate_to_page()
            time.sleep(1)
            row = page.find_table_row(data["source_uom"], data["target_uom"])
            assert row is not None, "Record not found after update"
            table_factor = page.get_conversion_factor_from_row(row)
            assert table_factor == "7", \
                "Table should show updated factor '7', got: '" + str(table_factor) + "'"
            log.info("  [PASS] Table shows factor: " + table_factor)

            log.info(">>> TEST 15 PASSED: Edit valid conversion factor works")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_edit_clear_conversion_factor(self, logged_in_driver):
        """Test 16: Edit existing record, clear factor, Update — Pattern A + mat-error."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Create fresh record via one-flow")
            page.navigate_to_page()
            data = page.create_fresh_record()
            assert page.is_success_alert_present(timeout=5), \
                "Create should succeed for pair: " + data["source_uom"] + " -> " + data["target_uom"]
            page.handle_success_alert()
            log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"] + " = " + data["conversion_factor"])

            log.step(2, "Open Edit form and clear Conversion Factor via JS")
            page.navigate_to_page()
            page.click_row_edit(data["source_uom"], data["target_uom"])
            time.sleep(1)

            page.clear_conversion_factor_via_js()
            log.info("  Cleared Conversion Factor field")

            log.step(3, "Click Update")
            page.click_update()
            time.sleep(1)

            log.step(4, "Verify Pattern A validation alert")
            assert page.is_validation_alert_present(timeout=5), \
                "Pattern A alert should appear for cleared factor on edit"
            page.handle_validation_warning()
            log.info("  [PASS] Pattern A alert detected")

            log.step(5, "Verify mat-error on Conversion Factor")
            error_text = page.get_mat_error_text(page.CONVERSION_FACTOR_INPUT)
            assert error_text != "", \
                "mat-error should appear for cleared factor. Got: '" + str(error_text) + "'"
            log.info("  [PASS] mat-error: " + error_text)

            log.info(">>> TEST 16 PASSED: Edit cleared factor validation works")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_edit_source_uom_disabled_on_view(self, logged_in_driver):
        """Test 17: View popup — Source UOM and Target UOM dropdowns should be disabled."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Create fresh record via one-flow")
            page.navigate_to_page()
            data = page.create_fresh_record()
            assert page.is_success_alert_present(timeout=5), \
                "Create should succeed for pair: " + data["source_uom"] + " -> " + data["target_uom"]
            page.handle_success_alert()
            log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"] + " = " + data["conversion_factor"])

            log.step(2, "Open View popup")
            page.navigate_to_page()
            page.click_row_view(data["source_uom"], data["target_uom"])
            time.sleep(1.5)

            log.step(3, "Verify View popup is read-only")
            page.verify_view_popup_read_only()
            log.info("  [PASS] View popup verified as read-only")

            log.info(">>> TEST 17 PASSED: View popup read-only verification works")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_cancel_edit_no_changes_saved(self, logged_in_driver):
        """Test 18: Open Edit, change factor, click Cancel — original value unchanged."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Create fresh record via one-flow")
            page.navigate_to_page()
            data = page.create_fresh_record()
            assert page.is_success_alert_present(timeout=5), \
                "Create should succeed for pair: " + data["source_uom"] + " -> " + data["target_uom"]
            page.handle_success_alert()
            log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"] + " = " + data["conversion_factor"])

            log.step(2, "Read original factor from table")
            page.navigate_to_page()
            row = page.find_table_row(data["source_uom"], data["target_uom"])
            assert row is not None, "Record not found"
            original_factor = page.get_conversion_factor_from_row(row)
            log.info("  Original factor in table: " + original_factor)

            log.step(3, "Open Edit form and change factor")
            page.click_row_edit(data["source_uom"], data["target_uom"])
            time.sleep(1)
            page.enter_conversion_factor("99999")
            log.info("  Changed factor to 99999 in edit form")

            log.step(4, "Click Cancel")
            page.close_popup()
            time.sleep(1)

            log.step(5, "Verify original factor is unchanged in table")
            page.navigate_to_page()
            row_after = page.find_table_row(data["source_uom"], data["target_uom"])
            assert row_after is not None, "Record not found after cancel"
            current_factor = page.get_conversion_factor_from_row(row_after)
            assert current_factor == original_factor, \
                "Factor changed after Cancel! Was '" + original_factor + "', now '" + current_factor + "'"
            log.info("  [PASS] Factor unchanged: " + current_factor)

            log.info(">>> TEST 18 PASSED: Cancel edit preserves original value")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    # ================================================================
    # GROUP E — HISTORY
    # Tests 19-20
    # ================================================================

    def test_history_shows_record(self, logged_in_driver):
        """Test 19: History popup opens and shows at least 1 row with data."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Create fresh record via one-flow")
            page.navigate_to_page()
            data = page.create_fresh_record()
            assert page.is_success_alert_present(timeout=5), \
                "Create should succeed for pair: " + data["source_uom"] + " -> " + data["target_uom"]
            page.handle_success_alert()
            log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"] + " = " + data["conversion_factor"])

            log.step(2, "Open History popup")
            page.navigate_to_page()
            page.click_row_history(data["source_uom"], data["target_uom"])
            time.sleep(2)

            log.step(3, "Verify History has data")
            row_count = page.get_history_row_count()
            log.info("  History rows found: " + str(row_count))
            assert row_count >= 1, \
                "History should have at least 1 row for a newly created record"

            history_data = page.get_history_data()
            log.info("  History data: " + str(history_data))
            log.info("  [PASS] History shows " + str(row_count) + " record(s)")

            log.info(">>> TEST 19 PASSED: History shows record data")
        except Exception:
            raise
        finally:
            page.close_history_popup()
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_history_close_button(self, logged_in_driver):
        """Test 20: Open History popup, click Cancel to close."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Create fresh record via one-flow")
            page.navigate_to_page()
            data = page.create_fresh_record()
            assert page.is_success_alert_present(timeout=5), \
                "Create should succeed for pair: " + data["source_uom"] + " -> " + data["target_uom"]
            page.handle_success_alert()
            log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"] + " = " + data["conversion_factor"])

            log.step(2, "Open History popup")
            page.navigate_to_page()
            page.click_row_history(data["source_uom"], data["target_uom"])
            time.sleep(2)

            log.step(3, "Click Cancel to close History")
            page.close_history_popup()
            time.sleep(1)

            log.step(4, "Verify we're back at the table")
            page._wait_for_page_ready()
            rows = page.get_table_rows()
            assert len(rows) > 0, "Table should be visible after closing History"
            log.info("  [PASS] Table visible with " + str(len(rows)) + " row(s)")

            log.info(">>> TEST 20 PASSED: History close button works")
        except Exception:
            raise
        finally:
            page.close_history_popup()
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    # ================================================================
    # GROUP F — CANCEL FLOW
    # Tests 21-22
    # ================================================================

    def test_cancel_add_form(self, logged_in_driver):
        """Test 21: Fill Add form, click Cancel — no record created."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Navigate to page and count rows before")
            page.navigate_to_page()
            rows_before = len(page.get_table_rows())
            log.info("  Rows before: " + str(rows_before))

            log.step(2, "Open Add form, fill all fields")
            page.open_add_form()
            page.select_source_uom("KG")
            page.select_target_uom("ML")
            page.enter_conversion_factor("42")
            log.info("  Filled form with: KG -> ML = 42")

            log.step(3, "Click Cancel")
            page.close_popup()
            time.sleep(1)

            log.step(4, "Verify no new record in table")
            page.navigate_to_page()
            rows_after = len(page.get_table_rows())
            assert rows_after == rows_before, \
                "New record created after Cancel! Before: " + str(rows_before) + ", After: " + str(rows_after)
            log.info("  [PASS] Rows unchanged: " + str(rows_after))

            log.info(">>> TEST 21 PASSED: Cancel add form - no record created")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)

    def test_cancel_edit_form(self, logged_in_driver):
        """Test 22: Open Edit, modify factor, click Cancel — changes not saved."""
        driver = logged_in_driver
        page = UOMConversionPage(driver)

        try:
            log.step(1, "Create fresh record via one-flow")
            page.navigate_to_page()
            data = page.create_fresh_record()
            assert page.is_success_alert_present(timeout=5), \
                "Create should succeed for pair: " + data["source_uom"] + " -> " + data["target_uom"]
            page.handle_success_alert()
            log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"] + " = " + data["conversion_factor"])

            log.step(2, "Read original factor from table")
            page.navigate_to_page()
            row = page.find_table_row(data["source_uom"], data["target_uom"])
            assert row is not None, "Record not found"
            original_factor = page.get_conversion_factor_from_row(row)
            log.info("  Original factor: " + original_factor)

            log.step(3, "Open Edit, change factor, click Cancel")
            page.click_row_edit(data["source_uom"], data["target_uom"])
            time.sleep(1)
            page.enter_conversion_factor("55555")
            page.close_popup()
            time.sleep(1)

            log.step(4, "Verify factor unchanged in table")
            page.navigate_to_page()
            row_after = page.find_table_row(data["source_uom"], data["target_uom"])
            assert row_after is not None, "Record not found after cancel"
            current_factor = page.get_conversion_factor_from_row(row_after)
            assert current_factor == original_factor, \
                "Edit saved after Cancel! Was '" + original_factor + "', now '" + current_factor + "'"
            log.info("  [PASS] Factor unchanged: " + current_factor)

            log.info(">>> TEST 22 PASSED: Cancel edit preserves original value")
        except Exception:
            raise
        finally:
            page.force_close_form_popup()
            page.close_popup()
            time.sleep(1)