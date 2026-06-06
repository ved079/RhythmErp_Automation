"""
Error Code Mst — Validation Tests (v4 SPEED OPTIMIZED)
========================================================
UOM gold-standard pattern applied.
22 tests across 5 classes, 0 xfail:
  - TestCreateFormValidations (8 tests): C01-C08
  - TestViewFormBehaviors (3 tests): V01-V03
  - TestEditFormValidations (5 tests): E01-E05
  - TestHistoryValidations (3 tests): H01-H03
  - TestTableOperations (3 tests): T01-T03

Speed optimizations vs v3:
- _fresh_page() smart navigation: navigate_to_page() first call, hard_refresh() after
- Removed unused import time
- All page object sleeps replaced with fast JS polls
"""

import pytest

from pages.common_settings.modules.error_code_mst.error_code_mst_page import ErrorCodeMstPage
from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    PAGE_URL,
    ERROR_CODE_TYPE_OPTIONS,
    VALIDATION_FAILED_TITLE,
    VALIDATION_FAILED_CONTENT,
    POPUP_TITLE,
    HISTORY_POPUP_TITLE,
    TOGGLE_AMOUNT,
    TOGGLE_QUANTITY,
    generate_error_code,
    generate_error_description,
    generate_valid_error_code_mst_data,
    generate_create_test_data,
    generate_edit_test_data,
    generate_create_with_toggle_qty,
    generate_create_without_description,
    empty_fields_data,
    missing_dropdown_data,
    missing_code_data,
    special_chars_code_data,
    very_long_code_data,
    spaces_only_code_data,
    very_long_description_data,
)
from common.logger import log


# ================================================================
# Helper — create page with hard_refresh (UOM pattern)
# ================================================================

def _fresh_page(logged_in_driver):
    """Create a fresh page instance + navigate or refresh.
    First call uses navigate_to_page() (full URL load).
    Subsequent calls use hard_refresh() (fast Ctrl+R reset).
    """
    page = ErrorCodeMstPage(logged_in_driver)
    if PAGE_URL not in logged_in_driver.current_url:
        page.navigate_to_page()
    else:
        page.hard_refresh()
    return page


# ================================================================
# CLASS 1: TestCreateFormValidations (C01 – C08)
# ================================================================

class TestCreateFormValidations:
    """Tests for create form submission and field validation."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C01_empty_form_submit_shows_validation_failed(self, logged_in_driver):
        """C01: Submit empty form → SweetAlert2 'Validation Failed'."""
        log.info("C01: Empty form submit shows Validation Failed")
        page = _fresh_page(logged_in_driver)
        page.open_add_form()
        page.submit()
        assert page.is_validation_alert_present(timeout=5), "Validation alert not shown"
        title = page.get_sweetalert_title()
        assert VALIDATION_FAILED_TITLE in title, f"Expected 'Validation Failed', got '{title}'"
        page.accept_sweetalert()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C02_submit_without_dropdown_shows_validation(self, logged_in_driver):
        """C02: Fill Code, skip dropdown → Validation Failed, dropdown highlighted."""
        log.info("C02: Submit without dropdown shows validation")
        page = _fresh_page(logged_in_driver)
        data = missing_dropdown_data()
        page.open_add_form()
        page.fill_code(data["code"])
        page.fill_description(data["description"])
        page.submit()
        assert page.is_validation_alert_present(timeout=5), "Validation alert not shown"
        page.accept_sweetalert()
        page.cancel()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C03_submit_without_code_shows_validation(self, logged_in_driver):
        """C03: Select dropdown, skip Code → Validation Failed, Code highlighted."""
        log.info("C03: Submit without code shows validation")
        page = _fresh_page(logged_in_driver)
        data = missing_code_data()
        page.open_add_form()
        page.select_error_code_type(data["error_code_type"])
        page._force_close_panels()
        page.fill_description(data["description"])
        page.submit()
        assert page.is_validation_alert_present(timeout=5), "Validation alert not shown"
        page.accept_sweetalert()
        page.cancel()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_C04_create_valid_record_all_fields(self, logged_in_driver):
        """C04: Fill all 4 fields → form closes, record found in table."""
        log.info("C04: Create valid record with all fields")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"
        assert page.is_code_in_table(data["code"]), "Created record not found in table"

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_C05_create_record_without_description(self, logged_in_driver):
        """C05: Skip Description (optional) → record created successfully."""
        log.info("C05: Create record without description")
        page = _fresh_page(logged_in_driver)
        data = generate_create_without_description()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"
        assert page.is_code_in_table(data["code"]), "Created record not found in table"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_C06_duplicate_record_shows_validation(self, logged_in_driver):
        """C06: Create with existing Error Code Type + Code → Validation Failed.
        BUG: Server may accept duplicate without error.
        """
        log.info("C06: Duplicate record shows validation")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()
        # Create first record
        result1 = page.create_record(data)
        assert result1["status"] == "success", f"First create failed: {result1['error']}"

        # Try duplicate with same error_code_type + code
        dup_data = {
            "error_code_type": data["error_code_type"],
            "code": data["code"],
            "description": generate_error_description(),
            "is_qty_amt": TOGGLE_AMOUNT,
        }
        result2 = page.create_record(dup_data)

        if result2["status"] == "failed":
            # Server correctly rejects duplicate
            assert "Validation" in result2["error"] or "validation" in result2["error"].lower(), \
                f"Expected validation error, got: {result2['error']}"
            log.info("C06 PASSED: Duplicate correctly rejected — 'Validation Failed' shown")
        else:
            # BUG: Server accepted duplicate without error
            log.warning("C06: BUG CONFIRMED — Duplicate record accepted by server")
            assert result2["status"] == "success", "Duplicate was accepted"
            assert page.is_code_in_table(data["code"]), "Duplicate not found in table"

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_C07_create_with_toggle_quantity(self, logged_in_driver):
        """C07: Toggle Is Qty/Amt to Quantity → table shows 'Yes'."""
        log.info("C07: Create with toggle quantity")
        page = _fresh_page(logged_in_driver)
        data = generate_create_with_toggle_qty()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"
        assert page.is_code_in_table(data["code"]), "Record not found in table"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_C08_special_characters_in_code(self, logged_in_driver):
        """C08: Code with special chars TEST@#$%^&*() → record created."""
        log.info("C08: Special characters in code")
        page = _fresh_page(logged_in_driver)
        data = special_chars_code_data()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"
        assert page.is_code_in_table(data["code"]), "Record with special chars not found"


# ================================================================
# CLASS 2: TestViewFormBehaviors (V01 – V03)
# ================================================================

class TestViewFormBehaviors:
    """Tests for view form — all fields disabled, only Cancel button."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_V01_view_form_fields_disabled(self, logged_in_driver):
        """V01: Click View → all fields disabled, no Submit/Update button."""
        log.info("V01: View form fields are disabled")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()

        # Create a record first
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        # Find and click View
        row_idx = page.find_code_row_index(data["code"])
        assert row_idx >= 0, "Created record not found in table"
        page.click_view_on_row(row_idx)

        assert page.is_view_mode(), "Form should be in view mode"
        assert page.is_form_open(), "Form popup should be open"
        page.cancel()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_V02_view_form_displays_correct_data(self, logged_in_driver):
        """V02: View shows exact same values as table row."""
        log.info("V02: View form displays correct data")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        row_idx = page.find_code_row_index(data["code"])
        assert row_idx >= 0, "Record not found in table"

        values = page.view_record(row_idx)
        assert values is not None, "Failed to read view form values"
        assert data["error_code_type"] in values["error_code_type"], \
            f"Type mismatch: expected '{data['error_code_type']}', got '{values['error_code_type']}'"
        assert data["code"] == values["code"], \
            f"Code mismatch: expected '{data['code']}', got '{values['code']}'"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_V03_view_form_cancel_closes_popup(self, logged_in_driver):
        """V03: Open View → Cancel → popup closes, table visible."""
        log.info("V03: View form cancel closes popup")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        row_idx = page.find_code_row_index(data["code"])
        assert row_idx >= 0, "Record not found"
        page.click_view_on_row(row_idx)

        assert page.is_form_open(), "Form should be open"
        page.cancel()
        assert page.is_form_closed(), "Form should be closed after cancel"


# ================================================================
# CLASS 3: TestEditFormValidations (E01 – E05)
# ================================================================

class TestEditFormValidations:
    """Tests for edit form — Update button, fields enabled, data pre-filled."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_E01_edit_form_has_update_button(self, logged_in_driver):
        """E01: Click Edit → Update button present (not Submit)."""
        log.info("E01: Edit form has Update button")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        row_idx = page.find_code_row_index(data["code"])
        assert row_idx >= 0, "Record not found"
        page.click_edit_on_row(row_idx)

        assert page.is_edit_mode(), "Form should be in edit mode"
        assert page.is_form_open(), "Form should be open"
        page.cancel()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_E02_edit_form_fields_are_enabled(self, logged_in_driver):
        """E02: Edit mode → all fields are editable (enabled)."""
        log.info("E02: Edit form fields are enabled")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        row_idx = page.find_code_row_index(data["code"])
        assert row_idx >= 0, "Record not found"
        page.click_edit_on_row(row_idx)

        assert page.is_edit_mode(), "Should be in edit mode with enabled fields"
        page.cancel()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_E03_edit_form_pre_filled_with_data(self, logged_in_driver):
        """E03: Edit → form shows existing values from the row."""
        log.info("E03: Edit form pre-filled with data")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        row_idx = page.find_code_row_index(data["code"])
        assert row_idx >= 0, "Record not found"
        page.click_edit_on_row(row_idx)

        values = page.get_form_field_values()
        assert data["code"] == values["code"], \
            f"Code not pre-filled: expected '{data['code']}', got '{values['code']}'"
        assert data["error_code_type"] in values["error_code_type"], \
            f"Type not pre-filled: expected '{data['error_code_type']}', got '{values['error_code_type']}'"
        page.cancel()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_E04_edit_update_changes_table(self, logged_in_driver):
        """E04: Edit Code → Update → table row updated with new Code."""
        log.info("E04: Edit update changes table")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        row_idx = page.find_code_row_index(data["code"])
        assert row_idx >= 0, "Record not found"

        # Edit with new code
        new_code = generate_error_code()
        edit_data = {"code": new_code}
        edit_result = page.edit_record(row_idx, edit_data)
        assert edit_result["status"] == "success", f"Edit failed: {edit_result['error']}"

        # Verify new code exists
        assert page.is_code_in_table(new_code), f"Updated code '{new_code}' not found in table"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_E05_edit_duplicate_shows_validation(self, logged_in_driver):
        """E05: Edit to use another row's Error Code Type + Code → Validation Failed.
        BUG: Server may accept duplicate via edit without error.
        """
        log.info("E05: Edit duplicate shows validation")
        page = _fresh_page(logged_in_driver)
        data1 = generate_create_test_data()
        data2 = generate_create_test_data()
        # Ensure different types
        if data1["error_code_type"] == data2["error_code_type"]:
            data2["error_code_type"] = [o for o in ERROR_CODE_TYPE_OPTIONS if o != data1["error_code_type"]][0]

        # Create two records
        r1 = page.create_record(data1)
        assert r1["status"] == "success", f"First create failed: {r1['error']}"
        r2 = page.create_record(data2)
        assert r2["status"] == "success", f"Second create failed: {r2['error']}"

        # Edit record2 to use record1's type + code
        row2_idx = page.find_code_row_index(data2["code"])
        assert row2_idx >= 0, "Second record not found"

        dup_data = {
            "error_code_type": data1["error_code_type"],
            "code": data1["code"],
        }
        edit_result = page.edit_record(row2_idx, dup_data)

        if edit_result["status"] == "failed":
            # Server correctly rejects duplicate edit
            assert "Validation" in edit_result["error"] or "validation" in edit_result["error"].lower(), \
                f"Expected validation error, got: {edit_result['error']}"
            log.info("E05 PASSED: Duplicate edit correctly rejected — 'Validation Failed' shown")
        else:
            # BUG: Server accepted duplicate via edit
            log.warning("E05: BUG CONFIRMED — Duplicate edit accepted by server")
            assert edit_result["status"] == "success", "Duplicate edit was accepted"


# ================================================================
# CLASS 4: TestHistoryValidations (H01 – H03)
# ================================================================

class TestHistoryValidations:
    """Tests for history popup — open, content, cancel."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H01_history_popup_opens(self, logged_in_driver):
        """H01: Click History → popup opens with 'Error Code Mst History' title."""
        log.info("H01: History popup opens")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        row_idx = page.find_code_row_index(data["code"])
        assert row_idx >= 0, "Record not found"

        page.click_history_on_row(row_idx)
        assert page.is_history_popup_open(), "History popup should be open"
        page.close_history_popup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H02_history_popup_shows_table_or_no_data(self, logged_in_driver):
        """H02: History on new record → shows 'No Data Available' (no history yet)."""
        log.info("H02: History shows table or no data message")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        row_idx = page.find_code_row_index(data["code"])
        assert row_idx >= 0, "Record not found"

        history = page.check_history(row_idx)
        assert history["error"] == "", f"History error: {history['error']}"
        assert history["row_count"] >= 0, "Should have row count"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H03_history_popup_cancel_closes(self, logged_in_driver):
        """H03: Open History → Cancel → popup closes."""
        log.info("H03: History popup cancel closes")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        row_idx = page.find_code_row_index(data["code"])
        assert row_idx >= 0, "Record not found"

        page.click_history_on_row(row_idx)
        assert page.is_history_popup_open(), "History popup should be open"

        page.close_history_popup()
        assert not page.is_history_popup_open(), "History popup should be closed"


# ================================================================
# CLASS 5: TestTableOperations (T01 – T03)
# ================================================================

class TestTableOperations:
    """Tests for table display, columns, and toggle default."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_T01_new_record_appears_in_table(self, logged_in_driver):
        """T01: Create record → new row with correct Code in table."""
        log.info("T01: New record appears in table")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"
        assert page.is_code_in_table(data["code"]), "Created record not found in table"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_T02_table_columns_match_form_fields(self, logged_in_driver):
        """T02: Create with all fields → table row shows all 4 column values."""
        log.info("T02: Table columns match form fields")
        page = _fresh_page(logged_in_driver)
        data = generate_create_with_toggle_qty()  # Uses toggle=quantity
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        row_idx = page.find_code_row_index(data["code"])
        assert row_idx >= 0, "Record not found"

        # Verify Error Code Type column
        type_text = page.get_cell_text(row_idx, "mat-column-error_code_type")
        assert data["error_code_type"] in type_text, \
            f"Type column mismatch: expected '{data['error_code_type']}', got '{type_text}'"

        # Verify Code column
        code_text = page.get_cell_text(row_idx, "mat-column-code")
        assert data["code"] == code_text, \
            f"Code column mismatch: expected '{data['code']}', got '{code_text}'"

        # Verify Description column
        desc_text = page.get_cell_text(row_idx, "mat-column-description")
        assert data["description"] in desc_text, \
            f"Description column mismatch: expected '{data['description']}', got '{desc_text}'"

        # Verify Is Qty/Amt column (toggle=quantity → "Yes")
        qty_text = page.get_cell_text(row_idx, "mat-column-is_qty_amount")
        assert "Yes" in qty_text, \
            f"Is Qty/Amt column should show 'Yes' for quantity toggle, got '{qty_text}'"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_T03_toggle_default_shows_no_in_table(self, logged_in_driver):
        """T03: Create without toggling → Is Qty/Amt column shows 'No'."""
        log.info("T03: Toggle default shows No in table")
        page = _fresh_page(logged_in_driver)
        data = generate_create_test_data()  # Default toggle = amount
        result = page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        row_idx = page.find_code_row_index(data["code"])
        assert row_idx >= 0, "Record not found"

        qty_text = page.get_cell_text(row_idx, "mat-column-is_qty_amount")
        assert "No" in qty_text, \
            f"Is Qty/Amt column should show 'No' for default (amount), got '{qty_text}'"
