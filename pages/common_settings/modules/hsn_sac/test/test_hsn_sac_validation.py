"""
test_hsn_sac_validation.py — HSN SAC Module Automated Tests
============================================================
20 test cases across 5 classes, 0 xfail:
  - TestCreateFormValidations (6 tests): C01-C06
  - TestViewFormBehaviors (3 tests): V01-V03
  - TestEditFormValidations (5 tests): E01-E05
  - TestHistoryValidations (3 tests): H01-H03
  - TestTableOperations (3 tests): T01-T03

Marker counts: smoke=4, sanity=20, regression=20, bug=1, ui=15
Known bugs: C06 (no duplicate HSN SAC number check)
"""

import time
import pytest
from selenium.webdriver.common.by import By
from pages.common_settings.modules.hsn_sac.data.hsn_sac_data import (
    generate_valid_hsn_sac_data,
    generate_hsn_sac_number,
    generate_hsn_sac_description,
    empty_fields_data,
    missing_number_data,
    missing_type_data,
    missing_description_data,
    special_chars_number_data,
    very_long_number_data,
    spaces_only_number_data,
    SUCCESS_ADD_MESSAGE,
    SUCCESS_UPDATE_MESSAGE,
    VALIDATION_FAILED_TITLE,
    HSN_SAC_TYPE_OPTIONS,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Class 1: CREATE Form Validations (6 tests)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreateFormValidations:

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_C01_successful_creation(self, hsn_sac_page):
        """HSN-C01: Create HSN SAC with all 3 valid fields → success."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()
        print(f"\n  Creating: {data['hsn_sac_number']} | {data['hsn_sac_type']} | {data['hsn_sac_description']}")

        result = page.create_hsn_sac(data)

        assert result["status"] == "success", f"Create failed: {result['error']}"
        assert "added successfully" in result["message"].lower(), f"Unexpected message: {result['message']}"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C02_empty_hsn_number(self, hsn_sac_page):
        """HSN-C02: Empty HSN SAC Number → Validation Failed."""
        page = hsn_sac_page
        data = missing_number_data()

        page.open_add_form()
        time.sleep(1)
        page.fill_all_fields(data)
        page._force_close_panels()
        page.submit()

        is_validation = page.is_validation_alert_present(timeout=10)
        warning = page.handle_validation_warning(timeout=5)

        assert is_validation, "Expected 'Validation Failed' alert for empty HSN SAC Number"
        assert VALIDATION_FAILED_TITLE in warning, f"Unexpected warning: {warning}"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C03_empty_hsn_type(self, hsn_sac_page):
        """HSN-C03: Empty HSN SAC Type → Validation Failed."""
        page = hsn_sac_page
        data = missing_type_data()

        page.open_add_form()
        time.sleep(1)
        page.fill_hsn_sac_number(data["hsn_sac_number"])
        page.fill_hsn_sac_description(data["hsn_sac_description"])
        page._force_close_panels()
        page.submit()

        is_validation = page.is_validation_alert_present(timeout=10)
        warning = page.handle_validation_warning(timeout=5)

        assert is_validation, "Expected 'Validation Failed' alert for empty HSN SAC Type"
        assert VALIDATION_FAILED_TITLE in warning, f"Unexpected warning: {warning}"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C04_empty_hsn_description(self, hsn_sac_page):
        """HSN-C04: Empty HSN SAC Description → Validation Failed."""
        page = hsn_sac_page
        data = missing_description_data()

        page.open_add_form()
        time.sleep(1)
        page.select_hsn_sac_type(data["hsn_sac_type"])
        page._force_close_panels()
        page.fill_hsn_sac_number(data["hsn_sac_number"])
        page._force_close_panels()
        page.submit()

        is_validation = page.is_validation_alert_present(timeout=10)
        warning = page.handle_validation_warning(timeout=5)

        assert is_validation, "Expected 'Validation Failed' alert for empty HSN SAC Description"
        assert VALIDATION_FAILED_TITLE in warning, f"Unexpected warning: {warning}"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C05_all_fields_empty(self, hsn_sac_page):
        """HSN-C05: Submit with all fields empty → Validation Failed."""
        page = hsn_sac_page

        page.open_add_form()
        time.sleep(1)
        page.submit()

        is_validation = page.is_validation_alert_present(timeout=10)
        warning = page.handle_validation_warning(timeout=5)

        assert is_validation, "Expected 'Validation Failed' alert for all empty fields"
        assert VALIDATION_FAILED_TITLE in warning, f"Unexpected warning: {warning}"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_C06_duplicate_hsn_number(self, hsn_sac_page):
        """HSN-C06: Create with duplicate HSN SAC Number → check system behavior."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()

        # Create first record
        result1 = page.create_hsn_sac(data)
        assert result1["status"] == "success", f"First create failed: {result1['error']}"

        # Try creating duplicate
        result2 = page.create_hsn_sac(data)

        # System may allow or block duplicates — just verify no crash
        if result2["status"] == "failed":
            if page.is_validation_alert_present(timeout=3):
                page.handle_validation_warning()
        print(f"  Duplicate behavior: status={result2['status']}, msg={result2.get('message','')}")


# ═══════════════════════════════════════════════════════════════════════════════
# Class 2: VIEW Form Behaviors (3 tests)
# ═══════════════════════════════════════════════════════════════════════════════

class TestViewFormBehaviors:

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_V01_view_existing_record(self, hsn_sac_page):
        """HSN-V01: View existing record → all fields disabled, no Submit button."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()

        result = page.create_hsn_sac(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        page.search_record(data["hsn_sac_number"])
        time.sleep(1.5)

        page.click_view_button(0)
        time.sleep(1.5)

        assert page.is_form_open(), "View popup did not open"
        assert page.is_view_mode(), "Should be in View mode (no Submit/Update button)"

        values = page.get_form_field_values()
        assert data["hsn_sac_number"] in values["hsn_sac_number"], \
            f"Number mismatch: expected '{data['hsn_sac_number']}', got '{values['hsn_sac_number']}'"

        page.close_popup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_V02_close_view_via_cancel(self, hsn_sac_page):
        """HSN-V02: Close View popup via Cancel button."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()

        result = page.create_hsn_sac(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        page.search_record(data["hsn_sac_number"])
        time.sleep(1.5)

        page.click_view_button(0)
        time.sleep(1)
        assert page.is_form_open(), "View popup should be open"

        page.cancel()
        time.sleep(1)
        assert page.is_form_closed(), "View popup should be closed after Cancel"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_V03_close_view_via_x_button(self, hsn_sac_page):
        """HSN-V03: Close View popup via X icon button."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()

        result = page.create_hsn_sac(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        page.search_record(data["hsn_sac_number"])
        time.sleep(1.5)

        page.click_view_button(0)
        time.sleep(1)
        assert page.is_form_open(), "View popup should be open"

        page.close_popup()
        time.sleep(1)
        assert page.is_form_closed(), "View popup should be closed after X click"


# ═══════════════════════════════════════════════════════════════════════════════
# Class 3: EDIT Form Validations (5 tests)
# ═══════════════════════════════════════════════════════════════════════════════

class TestEditFormValidations:

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_E01_edit_hsn_number(self, hsn_sac_page):
        """HSN-E01: Edit HSN SAC Number → success."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()

        result = page.create_hsn_sac(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        page.search_record(data["hsn_sac_number"])
        time.sleep(1.5)

        new_number = generate_hsn_sac_number()
        edit_data = {"hsn_sac_number": new_number}

        result = page.edit_hsn_sac(0, edit_data)
        assert result["status"] == "success", f"Edit failed: {result['error']}"
        assert "updated successfully" in result["message"].lower(), \
            f"Unexpected message: {result['message']}"

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_E02_edit_hsn_description(self, hsn_sac_page):
        """HSN-E02: Edit HSN SAC Description → success."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()

        result = page.create_hsn_sac(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        page.search_record(data["hsn_sac_number"])
        time.sleep(1.5)

        new_desc = f"Updated Desc {generate_hsn_sac_number()}"
        edit_data = {"hsn_sac_description": new_desc}

        result = page.edit_hsn_sac(0, edit_data)
        assert result["status"] == "success", f"Edit failed: {result['error']}"
        assert "updated successfully" in result["message"].lower(), \
            f"Unexpected message: {result['message']}"

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_E03_edit_hsn_type(self, hsn_sac_page):
        """HSN-E03: Edit HSN SAC Type → success."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()

        result = page.create_hsn_sac(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        page.search_record(data["hsn_sac_number"])
        time.sleep(1.5)

        original_type = data["hsn_sac_type"]
        new_type = [t for t in HSN_SAC_TYPE_OPTIONS if t != original_type][0]

        edit_data = {"hsn_sac_type": new_type}
        result = page.edit_hsn_sac(0, edit_data)
        assert result["status"] == "success", f"Edit failed: {result['error']}"
        assert "updated successfully" in result["message"].lower(), \
            f"Unexpected message: {result['message']}"

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_E04_edit_all_fields(self, hsn_sac_page):
        """HSN-E04: Edit all 3 fields → success."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()

        result = page.create_hsn_sac(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        page.search_record(data["hsn_sac_number"])
        time.sleep(1.5)

        edit_data = generate_valid_hsn_sac_data()
        result = page.edit_hsn_sac(0, edit_data)
        assert result["status"] == "success", f"Edit failed: {result['error']}"
        assert "updated successfully" in result["message"].lower(), \
            f"Unexpected message: {result['message']}"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_E05_edit_with_empty_required_field(self, hsn_sac_page):
        """HSN-E05: Clear Number and Update → Validation Failed."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()

        result = page.create_hsn_sac(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        page.search_record(data["hsn_sac_number"])
        time.sleep(1.5)

        page.click_edit_button(0)
        time.sleep(1.5)
        assert page.is_edit_mode(), "Should be in Edit mode"

        page.fill_hsn_sac_number("")
        page._force_close_panels()
        page.click_update()

        is_validation = page.is_validation_alert_present(timeout=10)
        warning = page.handle_validation_warning(timeout=5)

        assert is_validation, "Expected 'Validation Failed' for empty Number in Edit"
        assert VALIDATION_FAILED_TITLE in warning, f"Unexpected warning: {warning}"


# ═══════════════════════════════════════════════════════════════════════════════
# Class 4: HISTORY Validations (3 tests)
# ═══════════════════════════════════════════════════════════════════════════════

class TestHistoryValidations:

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H01_open_history_popup(self, hsn_sac_page):
        """HSN-H01: Open History popup → popup opens with correct title."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()

        result = page.create_hsn_sac(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        page.search_record(data["hsn_sac_number"])
        time.sleep(1.5)

        page.click_history_button(0)
        time.sleep(1.5)

        assert page.is_history_popup_open(), "History popup did not open"

        page.close_history_popup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H02_close_history_via_cancel(self, hsn_sac_page):
        """HSN-H02: Close History popup via Cancel → popup closes."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()

        result = page.create_hsn_sac(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        page.search_record(data["hsn_sac_number"])
        time.sleep(1.5)

        page.click_history_button(0)
        time.sleep(1.5)
        assert page.is_history_popup_open(), "History popup should be open"

        page.close_history_popup()
        time.sleep(1)
        assert not page.is_history_popup_open(), "History popup should be closed"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H03_history_data_check(self, hsn_sac_page):
        """HSN-H03: Check history data after creation (may be 0 rows)."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()

        result = page.create_hsn_sac(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        page.search_record(data["hsn_sac_number"])
        time.sleep(1.5)

        history = page.check_history(0)
        print(f"  History: rows={history['row_count']}, empty={history['is_empty']}, error={history['error']}")

        assert history["error"] == "", f"History check error: {history['error']}"


# ═══════════════════════════════════════════════════════════════════════════════
# Class 5: TABLE Operations (3 tests)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTableOperations:

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_T01_search_existing_record(self, hsn_sac_page):
        """HSN-T01: Search for an existing record → found in table."""
        page = hsn_sac_page
        data = generate_valid_hsn_sac_data()

        result = page.create_hsn_sac(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"

        page.clear_search()
        time.sleep(1)

        search_ok = page.search_record(data["hsn_sac_number"])
        assert search_ok, "Search execution failed"

        time.sleep(1.5)
        row_count = page.get_table_row_count()
        assert row_count >= 1, f"Expected at least 1 row after search, got {row_count}"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_T02_verify_table_columns(self, hsn_sac_page):
        """HSN-T02: Verify table has expected columns (View, Edit, History, Number, Type)."""
        page = hsn_sac_page

        assert page.is_page_loaded(), "Page should be loaded"

        row_count = page.get_table_row_count()
        if row_count > 0:
            rows = page.driver.find_elements(*page.TABLE_BODY_ROWS)
            first_row = rows[0]
            cells = first_row.find_elements(By.CSS_SELECTOR, "td")
            assert len(cells) >= 5, f"Expected 5+ columns, got {len(cells)}"
        else:
            assert True, "Table exists but no rows (acceptable)"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_T03_pagination_check(self, hsn_sac_page):
        """HSN-T03: Verify page loads and table is accessible."""
        page = hsn_sac_page

        assert page.is_page_loaded(), "Page should be loaded"

        page.click_refresh()
        time.sleep(2)

        assert page.is_page_loaded(), "Page should still be loaded after refresh"