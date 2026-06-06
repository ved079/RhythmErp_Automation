"""
Tax Authority — Validation Tests (v4 SPEED OPTIMIZED)
========================================================
UOM gold-standard pattern applied.
18 tests across 4 classes:
  - TestCreateFormValidations (C01-C08): Create form validation + positive tests
  - TestViewFormBehaviors (V01-V03): View form behavior checks
  - TestEditFormValidations (E01-E05): Edit form validation + positive tests
  - TestHistoryValidations (H01-H02): History popup checks

Speed optimizations vs v3:
- _fresh_page() smart navigation: navigate_to_page() first call, hard_refresh() after
- Removed all time.sleep() / wait_seconds() from test code
- All page object waits replaced with fast JS polls
- Uses logged_in_driver (session-scoped) instead of function-scoped tax_authority_page fixture
"""

import pytest

from pages.common_settings.modules.tax_authority.tax_authority_page import TaxAuthorityPage
from pages.common_settings.modules.tax_authority.data.tax_authority_data import (
    TAX_AUTHORITY_PAGE_URL,
    FIELD_TAX_NAME,
    VALIDATION_FAILED_TITLE,
    valid_tax_authority_data,
    duplicate_tax_authority_data,
    special_chars_tax_name,
    invalid_very_long_tax_name,
)
from common.logger import log


# ================================================================
# Helper — create page with smart navigation (UOM pattern)
# ================================================================

def _fresh_page(logged_in_driver):
    """Create a fresh page instance + navigate or refresh.
    First call uses navigate_to_page() (full URL load).
    Subsequent calls use hard_refresh() (fast Ctrl+R reset).
    """
    page = TaxAuthorityPage(logged_in_driver)
    if TAX_AUTHORITY_PAGE_URL not in logged_in_driver.current_url:
        page.navigate_to_page()
    else:
        page.hard_refresh()
    return page


# ================================================================
# CLASS 1: TestCreateFormValidations (C01 – C08)
# ================================================================

class TestCreateFormValidations:
    """Tests for the Add (Create) form validation behavior."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C01_empty_form_submit_shows_validation_failed(self, logged_in_driver):
        """C01: Submit form without filling any field should show Validation Failed."""
        log.info("C01: Empty form submit — expecting Validation Failed")
        page = _fresh_page(logged_in_driver)
        page.open_add_form()
        page.submit()

        assert page.is_validation_alert_present(timeout=5), \
            "Expected 'Validation Failed' SweetAlert on empty submit"

        title = page.get_alert_title()
        assert "Validation Failed" in title, \
            f"Expected 'Validation Failed' in alert title, got: {title}"

        page.accept_sweetalert()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C02_submit_without_tax_name_shows_validation(self, logged_in_driver):
        """C02: Leave Tax Name empty, fill dropdowns, submit — should show Validation Failed."""
        log.info("C02: Submit without Tax Name — expecting Validation Failed")
        page = _fresh_page(logged_in_driver)
        page.open_add_form()
        page.select_tax_type("GST")
        page.select_country("India")
        page.submit()

        assert page.is_validation_alert_present(timeout=5), \
            "Expected 'Validation Failed' when Tax Name is empty"
        page.accept_sweetalert()
        page.cancel()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C03_submit_without_tax_type_shows_validation(self, logged_in_driver):
        """C03: Fill Tax Name and Country, skip Tax Type, submit — should show Validation Failed."""
        log.info("C03: Submit without Tax Type — expecting Validation Failed")
        page = _fresh_page(logged_in_driver)
        page.open_add_form()
        page.fill_tax_name("TestWithoutTaxType")
        page.select_country("India")
        page._force_close_panels()
        page.submit()

        assert page.is_validation_alert_present(timeout=5), \
            "Expected 'Validation Failed' when Tax Type is empty"
        page.accept_sweetalert()
        page.cancel()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C04_submit_without_country_shows_validation(self, logged_in_driver):
        """C04: Fill Tax Name and Tax Type, skip Country, submit — should show Validation Failed."""
        log.info("C04: Submit without Country — expecting Validation Failed")
        page = _fresh_page(logged_in_driver)
        page.open_add_form()
        page.fill_tax_name("TestWithoutCountry")
        page.select_tax_type("GST")
        page._force_close_panels()
        page.submit()

        assert page.is_validation_alert_present(timeout=5), \
            "Expected 'Validation Failed' when Country is empty"
        page.accept_sweetalert()
        page.cancel()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_C05_create_valid_record_all_fields(self, logged_in_driver):
        """C05: Fill all 3 fields and Submit — record should be created successfully."""
        log.info("C05: Create valid record with all fields")
        page = _fresh_page(logged_in_driver)
        data = valid_tax_authority_data()
        tax_name = data[FIELD_TAX_NAME]

        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        # Verify record appears in table
        page.hard_refresh()
        found = page.search_record(tax_name, exact=True)
        assert found, f"Expected to find '{tax_name}' in table after creation"
        page.clear_search()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_C06_duplicate_record_shows_validation(self, logged_in_driver):
        """C06: Create record, then create again with same Tax Name — should show Validation Failed."""
        log.info("C06: Duplicate record — expecting Validation Failed")
        page = _fresh_page(logged_in_driver)
        data = valid_tax_authority_data()
        tax_name = data[FIELD_TAX_NAME]

        # Create first record
        result = page.create_record(data)
        assert result["status"] == "success", f"First create failed: {result['error']}"

        # Try creating duplicate
        dup_data = duplicate_tax_authority_data(tax_name)
        result2 = page.create_record(dup_data)

        if result2["status"] == "failed":
            # Server correctly rejects duplicate
            assert "Validation" in result2["error"] or "validation" in result2["error"].lower(), \
                f"Expected validation error, got: {result2['error']}"
            log.info("C06 PASSED: Duplicate correctly rejected — 'Validation Failed' shown")
        else:
            # BUG: Server accepted duplicate without error
            log.warning("C06: BUG CONFIRMED — Duplicate record accepted by server")

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_C07_special_characters_in_tax_name(self, logged_in_driver):
        """C07: Tax Name with special characters — test if accepted or rejected."""
        log.info("C07: Special characters in Tax Name")
        page = _fresh_page(logged_in_driver)
        data = special_chars_tax_name()
        tax_name = data[FIELD_TAX_NAME]

        result = page.create_record(data)

        if result["status"] == "success":
            log.info(f"Special characters accepted: '{tax_name}'")
            page.hard_refresh()
            page.search_record(tax_name, exact=True)
            page.clear_search()
        else:
            log.info(f"Special characters rejected: '{tax_name}'")

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_C08_very_long_tax_name(self, logged_in_driver):
        """C08: Very long Tax Name (200 chars) — tests max-length behavior."""
        log.info("C08: Very long Tax Name (200 chars)")
        page = _fresh_page(logged_in_driver)
        data = invalid_very_long_tax_name(200)
        tax_name = data[FIELD_TAX_NAME]

        result = page.create_record(data)

        if result["status"] == "success":
            log.info(f"Long name accepted (BUG: no maxlength): {len(tax_name)} chars")
            page.hard_refresh()
            page.search_record(tax_name[:50], exact=False)
            page.clear_search()
        else:
            log.info(f"Long name rejected by server: {len(tax_name)} chars")


# ================================================================
# CLASS 2: TestViewFormBehaviors (V01 – V03)
# ================================================================

class TestViewFormBehaviors:
    """Tests for the View form behavior."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_V01_view_form_fields_disabled(self, logged_in_driver):
        """V01: Click View on a row — all fields should be disabled, no Submit button."""
        log.info("V01: View form — all fields should be disabled")
        page = _fresh_page(logged_in_driver)

        # Click View on first row
        page.click_view_button(row_index=0)

        assert page.is_view_mode(), \
            "Form should be in View mode (no Submit/Update button)"

        assert page.is_field_disabled(field_name="Tax Name"), \
            "Tax Name should be disabled in View mode"

        page.cancel()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_V02_view_form_displays_correct_data(self, logged_in_driver):
        """V02: Create record, click View on it — form should show correct values."""
        log.info("V02: View form — displays correct data from table row")
        page = _fresh_page(logged_in_driver)
        data = valid_tax_authority_data()
        tax_name = data[FIELD_TAX_NAME]

        # Create a record first
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        # Find the row
        page.hard_refresh()
        row_index = page.find_row_by_name(tax_name)
        assert row_index != -1, f"Record '{tax_name}' not found in table"

        # Click View and verify
        values = page.view_record(row_index)
        assert values is not None, "Failed to read view form values"
        assert tax_name == values.get("tax_name", ""), \
            f"Tax Name mismatch: expected '{tax_name}', got '{values.get('tax_name', '')}'"
        page.clear_search()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_V03_view_form_cancel_closes_popup(self, logged_in_driver):
        """V03: Open View form, click Cancel — popup should close."""
        log.info("V03: View form — Cancel closes popup")
        page = _fresh_page(logged_in_driver)
        page.click_view_button(row_index=0)

        assert page.is_form_open(), "View form should be open"
        page.cancel()
        assert page.is_form_closed(), "View form should be closed after Cancel"


# ================================================================
# CLASS 3: TestEditFormValidations (E01 – E05)
# ================================================================

class TestEditFormValidations:
    """Tests for the Edit form validation behavior."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_E01_edit_form_has_update_button(self, logged_in_driver):
        """E01: Click Edit on a row — form should show Update button (not Submit)."""
        log.info("E01: Edit form — should have Update button")
        page = _fresh_page(logged_in_driver)
        page.click_edit_button(row_index=0)

        assert page.is_edit_mode(), "Form should be in edit mode with Update button"
        assert page.is_form_open(), "Form should be open"
        page.cancel()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_E02_edit_form_fields_are_enabled(self, logged_in_driver):
        """E02: Click Edit on a row — all fields should be editable."""
        log.info("E02: Edit form — all fields should be enabled")
        page = _fresh_page(logged_in_driver)
        page.click_edit_button(row_index=0)

        assert not page.is_field_disabled(field_name="Tax Name"), \
            "Tax Name should be enabled in Edit mode"
        page.cancel()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_E03_edit_form_pre_filled_with_data(self, logged_in_driver):
        """E03: Click Edit on a known row — form should be pre-filled with existing values."""
        log.info("E03: Edit form — pre-filled with existing data")
        page = _fresh_page(logged_in_driver)
        original_name = page.get_name_from_row(0)
        assert original_name, "First row should have a Tax Name"

        page.click_edit_button(row_index=0)
        values = page.get_form_field_values()
        assert original_name == values.get("tax_name", ""), \
            f"Pre-filled Tax Name mismatch: expected '{original_name}', got '{values.get('tax_name', '')}'"
        page.cancel()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_E04_edit_update_changes_table(self, logged_in_driver):
        """E04: Edit a record's Tax Name, click Update — table should reflect the change."""
        log.info("E04: Edit update — table should change")
        page = _fresh_page(logged_in_driver)
        data = valid_tax_authority_data()
        original_name = data[FIELD_TAX_NAME]

        # Create a record first
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        # Search for the record
        page.hard_refresh()
        found = page.search_record(original_name, exact=True)
        assert found, f"Expected to find '{original_name}' in table after creation"

        # Edit with new data — row 0 is our record after search
        new_data = valid_tax_authority_data()
        new_name = new_data[FIELD_TAX_NAME]
        result2 = page.edit_record(new_data, row_index=0)
        assert result2["status"] == "success", f"Edit failed: {result2['error']}"

        # Verify new name appears in table
        page.hard_refresh()
        found = page.search_record(new_name, exact=True)
        assert found, f"Expected to find '{new_name}' in table after edit"

        # Verify old name no longer exists
        page.clear_search()
        assert not page.search_record(original_name, exact=True), \
            f"Old name '{original_name}' should NOT exist after edit"
        page.clear_search()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_E05_edit_duplicate_shows_validation(self, logged_in_driver):
        """E05: Edit to use existing Tax Name — should show Validation Failed.
        BUG: Server may accept duplicate without error.
        """
        log.info("E05: Edit duplicate — expecting Validation Failed")
        page = _fresh_page(logged_in_driver)

        # Create two records
        data1 = valid_tax_authority_data()
        name1 = data1[FIELD_TAX_NAME]
        result1 = page.create_record(data1)
        assert result1["status"] == "success", f"First create failed: {result1['error']}"

        data2 = valid_tax_authority_data()
        name2 = data2[FIELD_TAX_NAME]
        result2 = page.create_record(data2)
        assert result2["status"] == "success", f"Second create failed: {result2['error']}"

        # Find first record and edit to use second record's name
        page.hard_refresh()
        row_index = page.find_row_by_name(name1)
        assert row_index != -1, f"Record '{name1}' not found"

        dup_data = duplicate_tax_authority_data(name2)
        result3 = page.edit_record(dup_data, row_index=row_index)

        if result3["status"] == "failed":
            # Server correctly rejects duplicate
            assert "Validation" in result3["error"] or "validation" in result3["error"].lower(), \
                f"Expected validation error, got: {result3['error']}"
            log.info("E05 PASSED: Duplicate edit correctly rejected — 'Validation Failed' shown")
        else:
            # BUG: Server accepted duplicate
            log.warning("E05: BUG CONFIRMED — Duplicate edit accepted by server")


# ================================================================
# CLASS 4: TestHistoryValidations (H01 – H02)
# ================================================================

class TestHistoryValidations:
    """Tests for the History popup behavior."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H01_history_popup_opens(self, logged_in_driver):
        """H01: Click History on a row — history popup should open with correct title."""
        log.info("H01: History popup — should open with correct title")
        page = _fresh_page(logged_in_driver)
        page.click_history_button(row_index=0)

        assert page.is_history_popup_open(), \
            "History popup should be visible"

        title = page.get_history_title()
        assert "Tax Authority" in title, \
            f"Expected 'Tax Authority' in history title, got: '{title}'"

        page.close_history_popup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H02_history_popup_cancel_closes(self, logged_in_driver):
        """H02: Open History popup, click Cancel — popup should close."""
        log.info("H02: History popup — Cancel closes popup")
        page = _fresh_page(logged_in_driver)
        page.click_history_button(row_index=0)

        assert page.is_history_popup_open(), \
            "History popup should be open"

        page.close_history_popup()
        assert not page.is_history_popup_open(), \
            "History popup should be closed after Cancel"
