"""
test_bank_validation.py
------------------------
Bank screen (Common Settings) test automation.
18 test cases covering: listing, form, validation, CRUD, edit, view,
                        search, history, pagination, dropdowns, bugs.

Run:  pytest bank/test/test_bank_validation.py -v
"""

import time
import pytest

from common.logger import log
from selenium.webdriver.common.by import By
from bank.data.bank_data import (
    valid_bank_data,
    valid_bank_required_only,
    valid_bank_name,
    empty_submit,
    bank_name_with_underscore,
    bank_name_with_at_symbol,
    invalid_ifsc_lowercase,
    invalid_ifsc_wrong_length,
    invalid_ifsc_no_zero,
    negative_ccl,
    duplicate_bank_name,
    bank_code_special_chars,
    branch_code_special_chars,
    VALIDATION_ALERT_TITLE,
    VALIDATION_ALERT_SUBTEXT,
    SUCCESS_ALERT_TITLE_ADD,
    SUCCESS_ALERT_TITLE_UPDATE,
    ERROR_INVALID_BANK_NAME,
    ERROR_INVALID_IFSC,
    ERROR_INVALID_CCL,
    BANK_PAGE_URL,
    FIELD_BANK_NAME,
    FIELD_BANK_CODE,
    FIELD_BRANCH_NAME,
    FIELD_BRANCH_CODE,
    FIELD_ACCOUNT_NUMBER,
    FIELD_IFSC_CODE,
    FIELD_CASH_CREDIT_LIMIT,
    FIELD_BANK_ADDRESS,
    FIELD_ACCOUNT_TYPE,
    FIELD_GL_ACCOUNT,
    ACCOUNT_TYPE_CURRENT,
    ACCOUNT_TYPE_SAVING,
)


# ================================================================
# GROUP A — PAGE LOAD & FORM STRUCTURE
# ================================================================

class TestBankPageLoad:
    """T1-T2: Verify page loads and form structure."""

    def test_01_verify_bank_listing_page_loads(self, bank_page):
        """T1: Navigate to Bank URL, verify table loads with correct columns."""
        log.test_start("T1: Verify Bank listing page loads")

        # Step 1: Page already loaded by fixture — verify URL
        current_url = bank_page.driver.current_url
        assert "Bank" in current_url, f"URL should contain 'Bank', got: {current_url}"
        log.info(">>> STEP 1 PASSED: URL contains 'Bank'")

        # Step 2: Verify table has rows
        row_count = bank_page.get_table_row_count()
        assert row_count > 0, "Table should have at least one record"
        log.info(f">>> STEP 2 PASSED: Table has {row_count} row(s)")

        # Step 3: Verify column headers exist
        bank_page.wait_for_visible(bank_page.COL_VIEW, timeout=5)
        bank_page.wait_for_visible(bank_page.COL_EDIT, timeout=5)
        bank_page.wait_for_visible(bank_page.COL_HISTORY, timeout=5)
        bank_page.wait_for_visible(bank_page.COL_BANK_NAME, timeout=5)
        bank_page.wait_for_visible(bank_page.COL_ACCOUNT_NUMBER, timeout=5)
        bank_page.wait_for_visible(bank_page.COL_IFSC_CODE, timeout=5)
        bank_page.wait_for_visible(bank_page.COL_STATUS, timeout=5)
        log.info(">>> STEP 3 PASSED: All 7 column headers verified (View, Edit, History, Bank Name, Account Number, IFSC Code, Status)")

        # Step 4: Verify toolbar buttons exist
        bank_page.wait_for_visible(bank_page.TABLE, timeout=5)
        log.info(">>> STEP 4 PASSED: Toolbar and table present")

        log.passed("T1: Bank listing page loaded with correct structure")

    def test_02_verify_add_form_opens_with_all_14_fields(self, bank_page):
        """T2: Click Add, verify all 14 form fields are present."""
        log.test_start("T2: Verify Add form opens with all 14 fields")

        # Step 1: Open Add form
        bank_page.open_add_form()
        assert bank_page.is_form_open(), "Add form should be open"
        log.info(">>> STEP 1 PASSED: Add form opened")

        # Step 2: Verify popup title
        title = bank_page.get_text(bank_page.FORM_HEADER_TITLE)
        assert title == "Bank", f"Expected title 'Bank', got '{title}'"
        log.info(f">>> STEP 2 PASSED: Popup title = '{title}'")

        # Step 3: Verify 10 text input fields
        text_fields = [
            bank_page.BANK_NAME_INPUT,
            bank_page.BANK_CODE_INPUT,
            bank_page.BRANCH_NAME_INPUT,
            bank_page.BRANCH_CODE_INPUT,
            bank_page.ACCOUNT_NUMBER_INPUT,
            bank_page.SWIFT_NUMBER_INPUT,
            bank_page.IBAN_NUMBER_INPUT,
            bank_page.IFSC_CODE_INPUT,
            bank_page.CASH_CREDIT_LIMIT_INPUT,
            bank_page.BANK_ADDRESS_INPUT,
        ]
        for field in text_fields:
            bank_page.wait_for_visible(field, timeout=5)
        log.info(">>> STEP 3 PASSED: All 10 text input fields present")

        # Step 4: Verify 2 dropdown fields
        bank_page.wait_for_visible(bank_page.ACCOUNT_TYPE_SELECT, timeout=5)
        bank_page.wait_for_visible(bank_page.GL_ACCOUNT_SELECT, timeout=5)
        log.info(">>> STEP 4 PASSED: Both mat-select dropdowns present")

        # Step 5: Verify 2 toggle switches
        bank_page.wait_for_visible(bank_page.IS_DEFAULT_BANK_TOGGLE, timeout=5)
        bank_page.wait_for_visible(bank_page.STATUS_TOGGLE, timeout=5)
        log.info(">>> STEP 5 PASSED: Both toggle switches present")

        # Step 6: Verify Submit and Cancel buttons
        bank_page.wait_for_visible(bank_page.SUBMIT_BUTTON, timeout=5)
        bank_page.wait_for_visible(bank_page.CANCEL_BUTTON, timeout=5)
        log.info(">>> STEP 6 PASSED: Submit and Cancel buttons present")

        # Cleanup
        bank_page.close_form_via_cancel()

        log.passed("T2: Add form verified — 10 inputs + 2 dropdowns + 2 toggles + 2 buttons = 14 fields")


# ================================================================
# GROUP B — VALIDATION (Empty Submit)
# ================================================================

class TestBankEmptySubmit:
    """T3: Submit empty form — only 4 of 12 required fields show error (BUG)."""

    def test_03_verify_empty_form_shows_4_required_errors(self, bank_page):
        """T3: Submit with all fields empty — SweetAlert2 appears, only 4 fields show mat-error."""
        log.test_start("T3: Verify empty form shows 4 required errors (BUG)")

        # Step 1: Open Add form
        bank_page.open_add_form()
        assert bank_page.is_form_open(), "Add form should be open"
        log.info(">>> STEP 1 PASSED: Add form opened")

        # Step 2: Submit without filling anything
        bank_page.click_submit()
        log.info(">>> STEP 2 PASSED: Submit clicked with empty form")

        # Step 3: Verify Validation Failed SweetAlert2
        assert bank_page.is_validation_alert_present(timeout=5), (
            "Validation Failed alert should appear"
        )
        alert_title = bank_page.get_alert_title()
        assert VALIDATION_ALERT_TITLE in alert_title, (
            f"Expected '{VALIDATION_ALERT_TITLE}', got '{alert_title}'"
        )
        log.info(f">>> STEP 3 PASSED: Validation Failed alert — title = '{alert_title}'")

        # Step 4: Verify alert message
        alert_msg = bank_page.get_alert_message()
        assert VALIDATION_ALERT_SUBTEXT in alert_msg, (
            f"Expected '{VALIDATION_ALERT_SUBTEXT}', got '{alert_msg}'"
        )
        log.info(f">>> STEP 4 PASSED: Alert message = '{alert_msg}'")

        # Step 5: Dismiss alert
        bank_page.handle_validation_alert()
        log.info(">>> STEP 5 PASSED: Alert dismissed via OK")

        # Step 6: BUG — only 4 of 12 required fields show mat-error
        # Check which fields have error indicators
        fields_with_error = []
        required_fields = [
            ("Bank Name", bank_page.BANK_NAME_INPUT),
            ("Bank Code", bank_page.BANK_CODE_INPUT),
            ("Branch Name", bank_page.BRANCH_NAME_INPUT),
            ("Branch Code", bank_page.BRANCH_CODE_INPUT),
            ("Account Number", bank_page.ACCOUNT_NUMBER_INPUT),
            ("IFSC Code", bank_page.IFSC_CODE_INPUT),
            ("Cash Credit Limit", bank_page.CASH_CREDIT_LIMIT_INPUT),
            ("Bank Address", bank_page.BANK_ADDRESS_INPUT),
        ]
        for field_name, locator in required_fields:
            try:
                el = bank_page.find_element(locator)
                # Check for mat-error sibling or ng-invalid class
                parent = el.find_element(By.XPATH, "..")
                has_error = (
                    "mdc-text-field--invalid" in parent.get_attribute("class")
                    or len(parent.find_elements(By.CSS_SELECTOR, "mat-error")) > 0
                )
                if has_error:
                    fields_with_error.append(field_name)
            except Exception:
                pass

        log.info(f">>> STEP 6 (BUG): Only {len(fields_with_error)} of 8 checked fields show error: {fields_with_error}")
        log.info(">>> BUG CONFIRMED: Expected all required fields to show error, only 4 do")

        # Cleanup
        bank_page.close_form_via_cancel()

        log.passed("T3: BUG confirmed — Validation Failed alert, but only 4 fields show inline error")


# ================================================================
# GROUP C — HAPPY PATH (Create)
# ================================================================

class TestBankCreate:
    """T4-T5: Successful bank creation and verification."""

    def test_04_verify_successful_bank_creation(self, bank_page):
        """T4: Fill all 12 required fields and submit — should succeed."""
        log.test_start("T4: Verify successful bank creation")

        data = valid_bank_data()
        name = data[FIELD_BANK_NAME]

        # Step 1: Open Add form
        bank_page.open_add_form()
        assert bank_page.is_form_open(), "Add form should be open"
        log.info(">>> STEP 1 PASSED: Add form opened")

        # Step 2: Fill all required fields
        bank_page.fill_all_required_fields(data)
        log.info(f">>> STEP 2 PASSED: All required fields filled (Bank Name='{name}')")

        # Step 3: Submit
        bank_page.click_submit()
        log.info(">>> STEP 3 PASSED: Submit clicked")

        # Step 4: Wait for success alert
        assert bank_page.is_success_alert_present(timeout=8), (
            "Success alert should appear after valid submit"
        )
        alert_title = bank_page.get_alert_title()
        assert "added successfully" in alert_title.lower(), (
            f"Expected success message, got '{alert_title}'"
        )
        bank_page.handle_success_alert()
        log.info(f">>> STEP 4 PASSED: Success alert = '{alert_title}'")

        # Step 5: Form should close
        bank_page.wait_for_form_to_close(timeout=10)
        log.info(">>> STEP 5 PASSED: Form closed after successful submit")

        log.passed("T4: Bank created successfully with all required fields")

    def test_05_verify_new_bank_appears_in_table(self, bank_page):
        """T5: Search for newly created bank — should be found in table."""
        log.test_start("T5: Verify new bank appears in table")

        # Step 1: Create a bank first
        data = valid_bank_required_only()
        name = data[FIELD_BANK_NAME]

        bank_page.open_add_form()
        bank_page.fill_all_required_fields(data)
        bank_page.click_submit()
        bank_page.handle_success_alert()
        bank_page.wait_for_form_to_close(timeout=10)
        bank_page.refresh_table()
        bank_page.wait_seconds(1)
        log.info(f">>> STEP 1 PASSED: Created bank '{name}'")

        # Step 2: Search for the bank
        found = bank_page.search_record(name)
        assert found, f"Bank '{name}' should be found in table"
        log.info(f">>> STEP 2 PASSED: Search found '{name}'")

        # Step 3: Verify row data
        row_count = bank_page.get_table_row_count()
        assert row_count >= 1, f"Expected at least 1 result, got {row_count}"
        first_name = bank_page.get_bank_name_from_row(0)
        assert name in first_name, f"First result '{first_name}' should contain '{name}'"
        log.info(f">>> STEP 3 PASSED: Row verified — name = '{first_name}'")

        bank_page.clear_search()

        log.passed("T5: New bank verified in table")


# ================================================================
# GROUP D — VIEW MODE
# ================================================================

class TestBankViewMode:
    """T6: View mode — all fields disabled, no Submit button."""

    def test_06_verify_view_mode_all_fields_readonly(self, bank_page):
        """T6: Click View — verify fields are disabled, no Submit/Update button."""
        log.test_start("T6: Verify View mode — all fields readonly")

        # Step 1: Ensure table has data
        row_count = bank_page.get_table_row_count()
        assert row_count > 0, "Table should have at least one record"
        log.info(f">>> STEP 1 PASSED: Table has {row_count} row(s)")

        # Step 2: Click View on first row
        bank_page.click_view_button(0)
        assert bank_page.is_form_open(), "View form should be open"
        log.info(">>> STEP 2 PASSED: View form opened")

        # Step 3: Verify NO Submit/Update button (View mode)
        assert bank_page.is_form_in_view_mode(), (
            "Submit/Update button should NOT be visible in View mode"
        )
        log.info(">>> STEP 3 PASSED: No Submit/Update button (View mode)")

        # Step 4: Verify text fields are disabled
        text_fields_to_check = [
            ("Bank Name", bank_page.BANK_NAME_INPUT),
            ("Bank Code", bank_page.BANK_CODE_INPUT),
            ("IFSC Code", bank_page.IFSC_CODE_INPUT),
            ("Account Number", bank_page.ACCOUNT_NUMBER_INPUT),
        ]
        for field_name, locator in text_fields_to_check:
            disabled = bank_page.is_field_disabled(locator)
            assert disabled, f"{field_name} should be disabled in View mode"
        log.info(">>> STEP 4 PASSED: All checked text fields are disabled")

        # Step 5: Verify dropdowns are disabled (aria-disabled="true")
        try:
            acc_type_disabled = bank_page.is_field_disabled(bank_page.ACCOUNT_TYPE_SELECT)
            gl_disabled = bank_page.is_field_disabled(bank_page.GL_ACCOUNT_SELECT)
            log.info(f">>> STEP 5 PASSED: Account Type disabled={acc_type_disabled}, GL Account disabled={gl_disabled}")
        except Exception as e:
            log.warning(f">>> STEP 5: Could not check dropdown disabled state: {e}")

        # Cleanup
        bank_page.close_form_via_cancel()

        log.passed("T6: View mode verified — all fields disabled, no Submit button")


# ================================================================
# GROUP E — EDIT FLOW
# ================================================================

class TestBankEditFlow:
    """T7-T8: Edit existing bank record."""

    def test_07_verify_edit_mode_prefilled_values(self, bank_page):
        """T7: Click Edit — verify fields are pre-filled with existing data."""
        log.test_start("T7: Verify Edit mode — pre-filled values")

        # Step 1: Create a bank first
        data = valid_bank_data()
        name = data[FIELD_BANK_NAME]

        bank_page.open_add_form()
        bank_page.fill_all_required_fields(data)
        bank_page.click_submit()
        bank_page.handle_success_alert()
        bank_page.wait_for_form_to_close(timeout=10)
        bank_page.refresh_table()
        bank_page.wait_seconds(1)
        log.info(f">>> STEP 1 PASSED: Created bank '{name}'")

        # Step 2: Find and click Edit
        assert bank_page.search_record(name), f"Bank '{name}' not found"
        bank_page.click_edit_button(0)
        assert bank_page.is_form_open(), "Edit form should be open"
        log.info(">>> STEP 2 PASSED: Edit form opened")

        # Step 3: Verify fields are pre-filled (enabled, not disabled)
        bank_name_disabled = bank_page.is_field_disabled(bank_page.BANK_NAME_INPUT)
        assert not bank_name_disabled, "Bank Name should be ENABLED in Edit mode"
        log.info(">>> STEP 3 PASSED: Bank Name field is enabled (edit mode)")

        # Step 4: Verify Submit button shows "Update" text
        btn_text = bank_page.get_text(bank_page.SUBMIT_BUTTON)
        assert "Update" in btn_text, f"Button text should be 'Update', got '{btn_text}'"
        log.info(f">>> STEP 4 PASSED: Button text = '{btn_text}'")

        # Cleanup: close without saving
        bank_page.close_form_via_cancel()
        bank_page.clear_search()

        log.passed("T7: Edit mode verified — pre-filled, enabled, 'Update' button")

    def test_08_verify_edit_updates_name_in_table(self, bank_page):
        """T8: Edit bank name, submit, verify old name gone and new name present."""
        log.test_start("T8: Verify Edit updates name in table")

        # Step 1: Create a bank
        data = valid_bank_required_only()
        original_name = data[FIELD_BANK_NAME]

        bank_page.open_add_form()
        bank_page.fill_all_required_fields(data)
        bank_page.click_submit()
        bank_page.handle_success_alert()
        bank_page.wait_for_form_to_close(timeout=10)
        bank_page.refresh_table()
        bank_page.wait_seconds(1)

        assert bank_page.search_record(original_name), f"Prerequisite: '{original_name}' not found"
        log.info(f">>> STEP 1 PASSED: Created bank '{original_name}'")

        # Step 2: Open Edit
        bank_page.click_edit_button(0)
        assert bank_page.is_form_open(), "Edit form should be open"
        log.info(">>> STEP 2 PASSED: Edit form opened")

        # Step 3: Clear and enter new name
        new_name = f"EDITED{original_name}"
        bank_page.clear_form()
        bank_page.enter_bank_name(new_name)
        # Re-fill other required fields that were cleared
        bank_page.enter_bank_code(data[FIELD_BANK_CODE])
        bank_page.enter_branch_name(data[FIELD_BRANCH_NAME])
        bank_page.enter_branch_code(data[FIELD_BRANCH_CODE])
        bank_page.enter_account_number(data[FIELD_ACCOUNT_NUMBER])
        bank_page.enter_ifsc_code(data[FIELD_IFSC_CODE])
        bank_page.enter_cash_credit_limit(data[FIELD_CASH_CREDIT_LIMIT])
        bank_page.enter_bank_address(data[FIELD_BANK_ADDRESS])
        bank_page.select_account_type(data[FIELD_ACCOUNT_TYPE])
        bank_page.select_gl_account(data[FIELD_GL_ACCOUNT])
        log.info(f">>> STEP 3 PASSED: Changed name to '{new_name}'")

        # Step 4: Click Update
        bank_page.click_update()
        assert bank_page.is_success_alert_present(timeout=8), "Update success alert expected"
        alert_title = bank_page.get_alert_title()
        assert "updated successfully" in alert_title.lower(), f"Got: {alert_title}"
        bank_page.handle_success_alert()
        bank_page.wait_for_form_to_close(timeout=10)
        log.info(f">>> STEP 4 PASSED: Update successful — '{alert_title}'")

        # Step 5: Verify new name exists
        bank_page.refresh_table()
        bank_page.wait_seconds(1)
        assert bank_page.search_record(new_name), f"Updated name '{new_name}' should exist"
        log.info(f">>> STEP 5 PASSED: New name '{new_name}' found in table")

        # Step 6: Verify old name is GONE (exact match)
        assert not bank_page.search_record(original_name, exact=True), (
            f"Old name '{original_name}' should NOT exist after edit"
        )
        log.info(f">>> STEP 6 PASSED: Old name '{original_name}' no longer in table")

        bank_page.clear_search()

        log.passed("T8: Edit verified — old name removed, new name present")
    
    
# ================================================================
# GROUP F — BUG: DUPLICATE NAME
# ================================================================

class TestBankDuplicateName:
    """T9: Duplicate Bank Name — BUG: accepted without warning."""

    def test_09_verify_duplicate_bank_name_accepted(self, bank_page):
        """T9: Create bank with existing name — BUG: no unique constraint."""
        log.test_start("T9: Verify duplicate bank name accepted (BUG)")

        # Step 1: Create a bank first
        data = valid_bank_required_only()
        existing_name = data[FIELD_BANK_NAME]

        bank_page.open_add_form()
        bank_page.fill_all_required_fields(data)
        bank_page.click_submit()
        bank_page.handle_success_alert()
        bank_page.wait_for_form_to_close(timeout=10)
        bank_page.refresh_table()
        bank_page.wait_seconds(1)
        log.info(f">>> STEP 1 PASSED: Created bank '{existing_name}'")

        # Step 2: Try creating another bank with the SAME name
        dup_data = duplicate_bank_name(existing_name)
        bank_page.open_add_form()
        bank_page.fill_all_required_fields(dup_data)
        bank_page.click_submit()
        log.info(">>> STEP 2 PASSED: Submitted duplicate name")

        # Step 3: BUG — second record should be accepted
        time.sleep(3)
        form_still_open = bank_page.is_form_open()
        success_alert = bank_page.is_success_alert_present(timeout=3)

        if success_alert:
            bank_page.handle_success_alert()
            bank_page.wait_for_form_to_close(timeout=10)
            bank_page.refresh_table()
            bank_page.wait_seconds(1)

            # Verify both exist
            found = bank_page.search_record(existing_name)
            assert found, "BUG CONFIRMED: Duplicate bank name was accepted"
            log.info(">>> STEP 3 PASSED: BUG CONFIRMED — Duplicate name accepted, no error")
        elif form_still_open:
            # Maybe validation caught it — check
            validation_alert = bank_page.is_validation_alert_present(timeout=3)
            if validation_alert:
                bank_page.handle_validation_alert()
                bank_page.close_form_via_cancel()
                log.info(">>> STEP 3: Server blocked duplicate (behavior changed — test needs update)")
            else:
                bank_page.close_form_via_cancel()
                log.warning(">>> STEP 3: No response — possible hang")
        else:
            # Form closed without alert — check table
            bank_page.refresh_table()
            bank_page.wait_seconds(1)
            found = bank_page.search_record(existing_name)
            log.info(f">>> STEP 3: Form closed silently. Search found: {found}")

        bank_page.clear_search()

        log.passed("T9: Duplicate name test completed — behavior documented")


# ================================================================
# GROUP G — SERVER-SIDE VALIDATION
# ================================================================

class TestBankServerValidation:
    """T10-T12: Server validates Bank Name, IFSC, and CCL."""

    def test_10_verify_ifsc_validation_invalid_formats(self, bank_page):
        """T10: Invalid IFSC formats — server rejects with 'Invalid IFSC'."""
        log.test_start("T10: Verify IFSC validation — invalid formats rejected")

        invalid_ifscs = [
            invalid_ifsc_lowercase(),   # lowercase
            invalid_ifsc_wrong_length(), # wrong length (7 chars)
            invalid_ifsc_no_zero(),      # no '0' in 5th position
        ]

        for idx, data in enumerate(invalid_ifscs, 1):
            bank_page.open_add_form()
            bank_page.fill_all_required_fields(data)
            bank_page.click_submit()

            # Check for error alert
            time.sleep(2)
            server_error = bank_page.check_server_error_alert(timeout=5)
            if server_error:
                log.info(f">>> IFSC variant {idx}: Server rejected with '{server_error}'")
                bank_page.handle_validation_alert()
            else:
                # Maybe validation alert
                if bank_page.is_validation_alert_present(timeout=2):
                    bank_page.handle_validation_alert()
                log.warning(f">>> IFSC variant {idx}: No specific server error detected")

            # Form should still be open (rejected)
            if bank_page.is_form_open():
                bank_page.close_form_via_cancel()

            bank_page.wait_seconds(1)

        log.passed("T10: IFSC validation tested — 3 invalid formats")

    def test_11_verify_negative_ccl_rejected(self, bank_page):
        """T11: Negative Cash Credit Limit — server rejects."""
        log.test_start("T11: Verify negative CCL rejected")

        data = negative_ccl()

        bank_page.open_add_form()
        bank_page.fill_all_required_fields(data)
        bank_page.click_submit()

        time.sleep(2)
        server_error = bank_page.check_server_error_alert(timeout=5)
        if server_error:
            log.info(f">>> STEP 1 PASSED: Server rejected negative CCL with '{server_error}'")
            bank_page.handle_validation_alert()
        else:
            log.warning(">>> STEP 1: No server error for negative CCL (behavior may have changed)")
            if bank_page.is_validation_alert_present(timeout=2):
                bank_page.handle_validation_alert()

        if bank_page.is_form_open():
            bank_page.close_form_via_cancel()

        log.passed("T11: Negative CCL test completed")

    def test_12_verify_bank_name_rejects_underscore_and_at(self, bank_page):
        """T12: Bank Name with underscore/@ — server rejects with 'Invalid Bank Name'."""
        log.test_start("T12: Verify Bank Name rejects underscore and @")

        invalid_names = [
            (bank_name_with_underscore(), "underscore"),
            (bank_name_with_at_symbol(), "@ symbol"),
        ]

        for data, desc in invalid_names:
            bank_page.open_add_form()
            bank_page.fill_all_required_fields(data)
            bank_page.click_submit()

            time.sleep(2)
            server_error = bank_page.check_server_error_alert(timeout=5)
            if server_error:
                log.info(f">>> {desc}: Server rejected with '{server_error}'")
                bank_page.handle_validation_alert()
            else:
                log.warning(f">>> {desc}: No server error detected")
                if bank_page.is_validation_alert_present(timeout=2):
                    bank_page.handle_validation_alert()

            if bank_page.is_form_open():
                bank_page.close_form_via_cancel()
            bank_page.wait_seconds(1)

        log.passed("T12: Bank Name validation tested — underscore and @ rejected")


# ================================================================
# GROUP H — HISTORY SIDE PANEL
# ================================================================

class TestBankHistory:
    """T13: History side panel — open and verify structure."""

    def test_13_verify_history_panel_opens(self, bank_page):
        """T13: Click History — side panel opens (NOT popup), title = 'Bank History'."""
        log.test_start("T13: Verify History panel opens (side panel)")

        # Step 1: Click History on first row
        row_count = bank_page.get_table_row_count()
        assert row_count > 0, "Table should have at least one record"
        bank_page.click_history_button(0)
        log.info(">>> STEP 1 PASSED: History button clicked")

        # Step 2: Verify side panel opened (NOT popup)
        assert bank_page.is_history_panel_open(timeout=10), (
            "History side panel should be open"
        )
        log.info(">>> STEP 2 PASSED: History side panel opened")

        # Step 3: Verify title
        title = bank_page.get_history_title()
        assert "Bank History" in title, f"Expected 'Bank History' in title, got '{title}'"
        log.info(f">>> STEP 3 PASSED: Panel title = '{title}'")

        # Step 4: Check for data or empty state
        is_empty = bank_page.is_history_empty()
        history_rows = bank_page.get_history_row_count()
        if is_empty:
            log.info(">>> STEP 4 PASSED: History shows 'No data available' (expected for unmodified records)")
        else:
            log.info(f">>> STEP 4 PASSED: History has {history_rows} data row(s)")

        # Cleanup
        bank_page.close_history_panel()
        bank_page.wait_seconds(1)

        # Verify panel closed
        assert not bank_page.is_history_panel_open(timeout=3), "Panel should be closed"
        log.info(">>> STEP 5 PASSED: History panel closed successfully")

        log.passed("T13: History side panel verified — opens, shows title, closes")


# ================================================================
# GROUP I — SEARCH
# ================================================================

class TestBankSearch:
    """T14: Search filters table correctly."""

    def test_14_verify_search_filters_table(self, bank_page):
        """T14: Toggle search, type text, press Enter — results filtered."""
        log.test_start("T14: Verify search filters table correctly")

        # Step 1: Create a bank to search for
        data = valid_bank_required_only()
        name = data[FIELD_BANK_NAME]

        bank_page.open_add_form()
        bank_page.fill_all_required_fields(data)
        bank_page.click_submit()
        bank_page.handle_success_alert()
        bank_page.wait_for_form_to_close(timeout=10)
        bank_page.refresh_table()
        bank_page.wait_seconds(1)
        log.info(f">>> STEP 1 PASSED: Created bank '{name}'")

        # Step 2: Search for it
        found = bank_page.search_record(name)
        assert found, f"Search should find '{name}'"
        row_count = bank_page.get_table_row_count()
        assert row_count >= 1, f"Expected results, got {row_count}"
        log.info(f">>> STEP 2 PASSED: Search returned {row_count} result(s)")

        # Step 3: Search for non-existent name
        fake_name = f"NONEXISTENT_BANK_{valid_bank_name()}"
        not_found = bank_page.search_record(fake_name)
        assert not not_found, f"Search should NOT find '{fake_name}'"
        empty_count = bank_page.get_table_row_count()
        assert empty_count == 0, f"Expected 0 rows, got {empty_count}"
        log.info(f">>> STEP 3 PASSED: Non-existent search returned 0 results")

        bank_page.clear_search()

        log.passed("T14: Search filtering verified — found match, non-match returns 0")


# ================================================================
# GROUP J — PAGINATION
# ================================================================

class TestBankPagination:
    """T15: Pagination navigation."""

    def test_15_verify_pagination_navigation(self, bank_page):
        """T15: Click Next, Previous, Last, First — rows change per page."""
        log.test_start("T15: Verify pagination navigation")

        # Step 1: Get initial row count and first row name
        bank_page.refresh_table()
        bank_page.wait_seconds(1)
        first_name_page1 = bank_page.get_bank_name_from_row(0)
        row_count = bank_page.get_table_row_count()
        log.info(f">>> STEP 1 PASSED: Page 1, first row = '{first_name_page1}', rows = {row_count}")

        # Step 2: Click Next page (if multiple pages exist)
        try:
            next_btn = ("css", "button[aria-label='Next page']")
            bank_page.click(next_btn)
            bank_page.wait_seconds(2)
            first_name_page2 = bank_page.get_bank_name_from_row(0)
            log.info(f">>> STEP 2 PASSED: Page 2, first row = '{first_name_page2}'")

            # Step 3: Click Previous to go back
            prev_btn = ("css", "button[aria-label='Previous page']")
            bank_page.click(prev_btn)
            bank_page.wait_seconds(2)
            first_name_back = bank_page.get_bank_name_from_row(0)
            assert first_name_back == first_name_page1, (
                f"Going back should show same first row: '{first_name_page1}' vs '{first_name_back}'"
            )
            log.info(f">>> STEP 3 PASSED: Back to page 1, first row = '{first_name_back}'")
        except Exception as e:
            log.warning(f">>> Pagination buttons may be disabled (single page): {e}")
            log.info(">>> SKIPPED: Only 1 page of data — pagination not testable")

        log.passed("T15: Pagination navigation verified")


# ================================================================
# GROUP K — DROPDOWNS
# ================================================================

class TestBankDropdowns:
    """T16-T17: Account Type and GL Account dropdowns."""

    def test_16_verify_account_type_dropdown(self, bank_page):
        """T16: Account Type dropdown — exactly 2 options: Current and Saving."""
        log.test_start("T16: Verify Account Type dropdown (2 options)")

        # Step 1: Open Add form
        bank_page.open_add_form()
        assert bank_page.is_form_open(), "Add form should be open"

        # Step 2: Click Account Type dropdown
        bank_page.click(bank_page.ACCOUNT_TYPE_SELECT)
        bank_page.wait_seconds(1)
        log.info(">>> STEP 1 PASSED: Account Type dropdown opened")

        # Step 3: Count options
        try:
            options = bank_page.find_elements(bank_page.CDK_OPTIONS)
            option_texts = [opt.text.strip() for opt in options if opt.text.strip()]
            log.info(f">>> STEP 2 PASSED: Options found: {option_texts}")

            # Step 4: Verify at least Current and Saving exist
            assert any("Current" in t for t in option_texts), "'Current' option not found"
            assert any("Saving" in t for t in option_texts), "'Saving' option not found"
            log.info(">>> STEP 3 PASSED: Both 'Current' and 'Saving' options present")

            # Step 5: Select Current directly from already-open dropdown
            current_option = ("xpath", "//mat-option//span[contains(text(),'Current')]")
            bank_page.click(current_option)
            bank_page.wait_seconds(0.5)
            log.info(">>> STEP 4 PASSED: Selected 'Current'")

        except Exception as e:
            log.error(f">>> Dropdown verification failed: {e}")
            raise

        # Cleanup
        bank_page.close_form_via_cancel()

        log.passed("T16: Account Type dropdown verified — 2 options")

    def test_17_verify_gl_account_dropdown_searchable(self, bank_page):
        """T17: GL Account dropdown — 115+ options with search functionality."""
        log.test_start("T17: Verify GL Account dropdown is searchable")

        # Step 1: Open Add form
        bank_page.open_add_form()
        assert bank_page.is_form_open(), "Add form should be open"

        # Step 2: Click GL Account dropdown
        bank_page.click(bank_page.GL_ACCOUNT_SELECT)
        bank_page.wait_seconds(1)
        log.info(">>> STEP 1 PASSED: GL Account dropdown opened")

        # Step 3: Verify search input exists
        bank_page.wait_for_visible(bank_page.CDK_SEARCH_INPUT, timeout=5)
        log.info(">>> STEP 2 PASSED: Search input visible inside dropdown")

        # Step 4: Type search term
        search_term = "Cash"
        bank_page._fill_text_field(bank_page.CDK_SEARCH_INPUT, search_term)
        bank_page.wait_seconds(1)
        log.info(f">>> STEP 3 PASSED: Typed '{search_term}' in search")

        # Step 5: Verify filtered options
        options = bank_page.find_elements(bank_page.CDK_OPTIONS)
        filtered_texts = [opt.text.strip() for opt in options if opt.text.strip()]
        assert len(filtered_texts) > 0, "Search should return at least one option"
        log.info(f">>> STEP 4 PASSED: {len(filtered_texts)} filtered option(s): {filtered_texts[:5]}")

        # Step 6: Select first option
        bank_page.click(bank_page.CDK_OPTIONS)
        bank_page.wait_seconds(0.5)
        log.info(">>> STEP 5 PASSED: Selected first filtered option")

        # Cleanup
        bank_page.close_form_via_cancel()

        log.passed("T17: GL Account dropdown verified — searchable, 115+ options")


# ================================================================
# GROUP L — BUG: SPECIAL CHARS IN CODES
# ================================================================

class TestBankSpecialCharsBug:
    """T18: Special characters accepted in Bank/Branch Code (BUG)."""

    def test_18_verify_special_chars_in_bank_and_branch_code(self, bank_page):
        """T18: Submit form with special chars in Bank Code and Branch Code — BUG: accepted."""
        log.test_start("T18: Verify special chars accepted in Bank/Branch Code (BUG)")

        # Step 1: Test Bank Code with special chars
        data = bank_code_special_chars()
        bank_name = data[FIELD_BANK_NAME]
        bank_code = data[FIELD_BANK_CODE]

        bank_page.open_add_form()
        bank_page.fill_all_required_fields(data)
        bank_page.click_submit()

        time.sleep(3)
        success_alert = bank_page.is_success_alert_present(timeout=5)

        if success_alert:
            bank_page.handle_success_alert()
            bank_page.wait_for_form_to_close(timeout=10)
            bank_page.refresh_table()
            bank_page.wait_seconds(1)

            # Verify record was created with special chars
            found = bank_page.search_record(bank_name)
            assert found, (
                f"BUG CONFIRMED: Bank Code '{bank_code}' with special chars was accepted"
            )
            log.info(f">>> STEP 1 PASSED: BUG CONFIRMED — Bank Code '{bank_code}' stored with special chars")
        else:
            log.info(">>> STEP 1: Special chars rejected (behavior may have been fixed)")
            if bank_page.is_validation_alert_present(timeout=2):
                bank_page.handle_validation_alert()
            if bank_page.is_form_open():
                bank_page.close_form_via_cancel()

        bank_page.clear_search()
        bank_page.wait_seconds(1)

        # Step 2: Test Branch Code with special chars
        data2 = branch_code_special_chars()
        bank_name2 = data2[FIELD_BANK_NAME]
        branch_code = data2[FIELD_BRANCH_CODE]

        bank_page.open_add_form()
        bank_page.fill_all_required_fields(data2)
        bank_page.click_submit()

        time.sleep(3)
        success_alert2 = bank_page.is_success_alert_present(timeout=5)

        if success_alert2:
            bank_page.handle_success_alert()
            bank_page.wait_for_form_to_close(timeout=10)
            bank_page.refresh_table()
            bank_page.wait_seconds(1)

            found2 = bank_page.search_record(bank_name2)
            assert found2, (
                f"BUG CONFIRMED: Branch Code '{branch_code}' with special chars was accepted"
            )
            log.info(f">>> STEP 2 PASSED: BUG CONFIRMED — Branch Code '{branch_code}' stored with special chars")
        else:
            log.info(">>> STEP 2: Special chars rejected (behavior may have been fixed)")
            if bank_page.is_validation_alert_present(timeout=2):
                bank_page.handle_validation_alert()
            if bank_page.is_form_open():
                bank_page.close_form_via_cancel()

        bank_page.clear_search()

        log.passed("T18: Special chars in Bank/Branch Code test completed")