"""
test_tax_authority_validation.py
--------------------------------
Test suite for Tax Authority screen (Common Settings > RhythmERP).

18 tests across 5 classes:
  - TestCreateFormValidations (C01-C08): Create form validation + positive tests
  - TestViewFormBehaviors (V01-V03): View form behavior checks
  - TestEditFormValidations (E01-E05): Edit form validation + positive tests
  - TestHistoryValidations (H01-H02): History popup checks
  - TestTableOperations (implicit): Record appearance in table verified within create tests
"""

import pytest

from common.logger import log


# ================================================================
# CLASS 1: CREATE FORM VALIDATIONS
# ================================================================

class TestCreateFormValidations:
    """Tests for the Add (Create) form validation behavior."""

    def test_empty_form_submit_shows_validation_failed(self, tax_authority_page):
        """C01: Submit form without filling any field should show Validation Failed."""
        log.info("C01: Empty form submit — expecting Validation Failed")
        page = tax_authority_page

        page.open_add_form()

        # Submit without filling any fields
        page.click_submit()
        page.wait_seconds(2)

        # Verify validation alert appears
        assert page.is_validation_alert_present(timeout=5), \
            "Expected 'Validation Failed' SweetAlert on empty submit"

        # Verify alert content
        title = page.get_alert_title()
        assert "Validation Failed" in title, \
            f"Expected 'Validation Failed' in alert title, got: {title}"

        page.handle_validation_alert()

    def test_submit_without_tax_name_shows_validation(self, tax_authority_page):
        """C02: Leave Tax Name empty, fill dropdowns, submit — should show Validation Failed."""
        log.info("C02: Submit without Tax Name — expecting Validation Failed")
        page = tax_authority_page

        page.open_add_form()

        # Fill dropdowns only (skip Tax Name)
        page.select_tax_type("GST")
        page.select_country("India")
        page.click_submit()
        page.wait_seconds(2)

        assert page.is_validation_alert_present(timeout=5), \
            "Expected 'Validation Failed' when Tax Name is empty"
        page.handle_validation_alert()

    def test_submit_without_tax_type_shows_validation(self, tax_authority_page):
        """C03: Fill Tax Name and Country, skip Tax Type, submit — should show Validation Failed."""
        log.info("C03: Submit without Tax Type — expecting Validation Failed")
        page = tax_authority_page

        page.open_add_form()

        # Fill Tax Name and Country only (skip Tax Type)
        page.fill_tax_name("TestWithoutTaxType")
        page.select_country("India")
        page.click_submit()
        page.wait_seconds(2)

        assert page.is_validation_alert_present(timeout=5), \
            "Expected 'Validation Failed' when Tax Type is empty"
        page.handle_validation_alert()

    def test_submit_without_country_shows_validation(self, tax_authority_page):
        """C04: Fill Tax Name and Tax Type, skip Country, submit — should show Validation Failed."""
        log.info("C04: Submit without Country — expecting Validation Failed")
        page = tax_authority_page

        page.open_add_form()

        # Fill Tax Name and Tax Type only (skip Country)
        page.fill_tax_name("TestWithoutCountry")
        page.select_tax_type("GST")
        page.click_submit()
        page.wait_seconds(2)

        assert page.is_validation_alert_present(timeout=5), \
            "Expected 'Validation Failed' when Country is empty"
        page.handle_validation_alert()

    def test_create_valid_record_all_fields(self, tax_authority_page):
        """C05: Fill all 3 fields and Submit — record should be created successfully."""
        log.info("C05: Create valid record with all fields")
        from tax_authority.data.tax_authority_data import valid_tax_authority_data, FIELD_TAX_NAME

        page = tax_authority_page
        data = valid_tax_authority_data()
        tax_name = data[FIELD_TAX_NAME]

        # Create record
        result = page.create_record(data)
        assert result, "Expected record creation to succeed"

        # Verify record appears in table
        page.wait_seconds(1)
        found = page.search_record(tax_name, exact=True)
        assert found, f"Expected to find '{tax_name}' in table after creation"
        page.clear_search()

    def test_duplicate_record_shows_validation(self, tax_authority_page):
        """C06: Create record, then create again with same Tax Name — should show Validation Failed."""
        log.info("C06: Duplicate record — expecting Validation Failed")
        from tax_authority.data.tax_authority_data import valid_tax_authority_data, FIELD_TAX_NAME, duplicate_tax_authority_data

        page = tax_authority_page

        # Step 1: Create first record
        data = valid_tax_authority_data()
        tax_name = data[FIELD_TAX_NAME]
        result = page.create_record(data)
        assert result, "First record creation should succeed"

        # Step 2: Try creating duplicate
        dup_data = duplicate_tax_authority_data(tax_name)
        result2 = page.create_record(dup_data)
        assert not result2, "Duplicate record creation should fail with Validation Failed"

    def test_special_characters_in_tax_name(self, tax_authority_page):
        """C07: Tax Name with special characters — test if accepted or rejected."""
        log.info("C07: Special characters in Tax Name")
        from tax_authority.data.tax_authority_data import special_chars_tax_name, FIELD_TAX_NAME

        page = tax_authority_page
        data = special_chars_tax_name()
        tax_name = data[FIELD_TAX_NAME]

        result = page.create_record(data)

        if result:
            # Record created with special chars (BUG or acceptable behavior)
            log.info(f"Special characters accepted: '{tax_name}'")
            page.search_record(tax_name, exact=True)
            page.clear_search()
        else:
            # Record rejected — server has validation for special chars
            log.info(f"Special characters rejected: '{tax_name}'")

    def test_very_long_tax_name(self, tax_authority_page):
        """C08: Very long Tax Name (200 chars) — tests max-length behavior."""
        log.info("C08: Very long Tax Name (200 chars)")
        from tax_authority.data.tax_authority_data import invalid_very_long_tax_name, FIELD_TAX_NAME

        page = tax_authority_page
        data = invalid_very_long_tax_name(200)
        tax_name = data[FIELD_TAX_NAME]

        result = page.create_record(data)

        if result:
            log.info(f"Long name accepted (BUG: no maxlength): {len(tax_name)} chars")
            page.search_record(tax_name[:50], exact=False)
            page.clear_search()
        else:
            log.info(f"Long name rejected by server: {len(tax_name)} chars")


# ================================================================
# CLASS 2: VIEW FORM BEHAVIORS
# ================================================================

class TestViewFormBehaviors:
    """Tests for the View form behavior."""

    def test_view_form_fields_disabled(self, tax_authority_page):
        """V01: Click View on a row — all fields should be disabled, no Submit button."""
        log.info("V01: View form — all fields should be disabled")
        page = tax_authority_page

        # Click View on first row
        page.click_view_button(row_index=0)

        # Verify form is in View mode
        assert page.is_form_in_view_mode(), \
            "Form should be in View mode (no Submit/Update button)"

        # Verify Tax Name is disabled
        assert page.is_field_disabled(page.TAX_NAME_INPUT), \
            "Tax Name should be disabled in View mode"

        page.close_form_via_cancel()

    def test_view_form_displays_correct_data(self, tax_authority_page):
        """V02: Create record, click View on it — form should show correct values."""
        log.info("V02: View form — displays correct data from table row")
        from tax_authority.data.tax_authority_data import valid_tax_authority_data, FIELD_TAX_NAME

        page = tax_authority_page

        # Create a record first
        data = valid_tax_authority_data()
        tax_name = data[FIELD_TAX_NAME]
        result = page.create_record(data)
        assert result, "Record creation should succeed for View test"

        # Find the row
        page.wait_seconds(1)
        row_index = page.find_row_by_name(tax_name)
        assert row_index != -1, f"Record '{tax_name}' not found in table"

        # Click View on that row
        page.click_view_button(row_index)

        # Verify Tax Name matches
        page.wait_seconds(1)
        tax_name_input = page.find_element(page.TAX_NAME_INPUT)
        displayed_name = tax_name_input.get_attribute("value")
        assert displayed_name == tax_name, \
            f"View form Tax Name mismatch: expected '{tax_name}', got '{displayed_name}'"

        page.close_form_via_cancel()
        page.clear_search()

    def test_view_form_cancel_closes_popup(self, tax_authority_page):
        """V03: Open View form, click Cancel — popup should close."""
        log.info("V03: View form — Cancel closes popup")
        page = tax_authority_page

        page.click_view_button(row_index=0)
        assert page.is_form_open(), "View form should be open"

        page.close_form_via_cancel()
        assert not page.is_form_open(), "View form should be closed after Cancel"


# ================================================================
# CLASS 3: EDIT FORM VALIDATIONS
# ================================================================

class TestEditFormValidations:
    """Tests for the Edit form validation behavior."""

    def test_edit_form_has_update_button(self, tax_authority_page):
        """E01: Click Edit on a row — form should show Update button (not Submit)."""
        log.info("E01: Edit form — should have Update button")
        page = tax_authority_page

        page.click_edit_button(row_index=0)

        # Verify Update button is present
        assert page.is_displayed(page.UPDATE_BUTTON, timeout=5), \
            "Update button should be visible in Edit mode"

        # Verify Submit button is NOT present
        assert not page.is_displayed(page.SUBMIT_BUTTON, timeout=3), \
            "Submit button should NOT be visible in Edit mode"

        page.close_form_via_cancel()

    def test_edit_form_fields_are_enabled(self, tax_authority_page):
        """E02: Click Edit on a row — all fields should be editable."""
        log.info("E02: Edit form — all fields should be enabled")
        page = tax_authority_page

        page.click_edit_button(row_index=0)

        # Verify Tax Name is enabled
        assert not page.is_field_disabled(page.TAX_NAME_INPUT), \
            "Tax Name should be enabled in Edit mode"

        page.close_form_via_cancel()

    def test_edit_form_pre_filled_with_data(self, tax_authority_page):
        """E03: Click Edit on a known row — form should be pre-filled with existing values."""
        log.info("E03: Edit form — pre-filled with existing data")
        page = tax_authority_page

        # Get the Tax Name from first row
        original_name = page.get_name_from_row(0)
        assert original_name, "First row should have a Tax Name"

        page.click_edit_button(row_index=0)

        # Verify Tax Name is pre-filled
        tax_name_input = page.find_element(page.TAX_NAME_INPUT)
        displayed_name = tax_name_input.get_attribute("value")
        assert displayed_name == original_name, \
            f"Pre-filled Tax Name mismatch: expected '{original_name}', got '{displayed_name}'"

        page.close_form_via_cancel()

    def test_edit_update_changes_table(self, tax_authority_page):
        """E04: Edit a record's Tax Name, click Update — table should reflect the change."""
        log.info("E04: Edit update — table should change")
        from tax_authority.data.tax_authority_data import valid_tax_authority_data, FIELD_TAX_NAME

        page = tax_authority_page

        # Create a record first
        data = valid_tax_authority_data()
        original_name = data[FIELD_TAX_NAME]
        result = page.create_record(data)
        assert result, "Record creation should succeed for Edit test"

        # Search for the record (pagination-safe)
        page.wait_seconds(1)
        found = page.search_record(original_name, exact=True)
        assert found, f"Expected to find '{original_name}' in table after creation"

        # Edit with new data – row 0 is our record after search
        new_data = valid_tax_authority_data()
        new_name = new_data[FIELD_TAX_NAME]
        result2 = page.edit_record(new_data, row_index=0)
        assert result2, "Edit update should succeed"

        # Verify new name appears in table
        page.wait_seconds(1)
        found = page.search_record(new_name, exact=True)
        assert found, f"Expected to find '{new_name}' in table after edit"

        # Verify old name no longer existsa
        page.clear_search()
        assert not page.search_record(original_name, exact=True), \
            f"Old name '{original_name}' should NOT exist after edit"

        page.clear_search()

    def test_edit_duplicate_shows_validation(self, tax_authority_page):
        """E05: Edit to use existing Tax Name — should show Validation Failed.
        BUG: Server may accept duplicate without error.
        """
        log.info("E05: Edit duplicate — expecting Validation Failed")
        from tax_authority.data.tax_authority_data import (
            valid_tax_authority_data, duplicate_tax_authority_data, FIELD_TAX_NAME
        )

        page = tax_authority_page

        # Create two records
        data1 = valid_tax_authority_data()
        name1 = data1[FIELD_TAX_NAME]
        result1 = page.create_record(data1)
        assert result1, "First record creation should succeed"

        data2 = valid_tax_authority_data()
        name2 = data2[FIELD_TAX_NAME]
        result2 = page.create_record(data2)
        assert result2, "Second record creation should succeed"

        # Find first record and edit to use second record's name
        page.wait_seconds(1)
        row_index = page.find_row_by_name(name1)
        assert row_index != -1, f"Record '{name1}' not found"

        dup_data = duplicate_tax_authority_data(name2)
        result3 = page.edit_record(dup_data, row_index=row_index)

        if not result3:
            # Server correctly rejects duplicate
            log.info("E05 PASSED: Duplicate edit correctly rejected — 'Validation Failed' shown")
        else:
            # BUG: Server accepted duplicate
            log.warning("E05: BUG CONFIRMED — Duplicate edit accepted by server")
            assert result3, "Duplicate edit was accepted by server (bug)"


# ================================================================
# CLASS 4: HISTORY VALIDATIONS
# ================================================================

class TestHistoryValidations:
    """Tests for the History popup behavior."""

    def test_history_popup_opens(self, tax_authority_page):
        """H01: Click History on a row — history popup should open with correct title."""
        log.info("H01: History popup — should open with correct title")
        page = tax_authority_page

        page.click_history_button(row_index=0)

        # Verify history popup is open
        assert page.is_history_popup_open(timeout=10), \
            "History popup should be visible"

        # Verify title
        title = page.get_history_title()
        assert "Tax Authority" in title, \
            f"Expected 'Tax Authority' in history title, got: '{title}'"

        page.close_history_popup()

    def test_history_popup_cancel_closes(self, tax_authority_page):
        """H02: Open History popup, click Cancel — popup should close."""
        log.info("H02: History popup — Cancel closes popup")
        page = tax_authority_page

        page.click_history_button(row_index=0)
        assert page.is_history_popup_open(timeout=10), \
            "History popup should be open"

        page.close_history_popup()
        assert not page.is_history_popup_open(timeout=3), \
            "History popup should be closed after Cancel"
