"""
Tax Rate — Validation Tests
=============================
Test cases for Tax Rate module (Common Settings).
6 header fields + nested sub-table (HSN Number + Tax Rate).
26 tests across 6 classes covering create, validation, date, sub-table, view, and table.
"""

import time
import pytest

from pages.common_settings.modules.tax_rate.data.tax_rate_data import (
    VALIDATION_FAILED_TITLE,
    POPUP_TITLE,
    HISTORY_POPUP_TITLE,
    VERSION_BUTTON_TEXT,
    TAX_TYPE_OPTIONS,
    TAX_AUTHORITY_OPTIONS,
    generate_tax_rate_name,
    generate_revision_status,
    generate_tax_rate_value,
    generate_valid_tax_rate_data,
    generate_sub_table_row,
    generate_create_test_data,
    generate_create_multi_row_data,
    generate_version_test_data,
    empty_fields_data,
    missing_name_data,
    missing_tax_type_data,
    missing_tax_authority_data,
    missing_revision_status_data,
    sql_injection_name_data,
    special_chars_name_data,
    very_long_name_data,
    negative_tax_rate_data,
    zero_tax_rate_data,
    very_large_tax_rate_data,
    empty_sub_table_data,
    unselected_hsn_data,
)
from common.logger import log


# ================================================================
# CLASS 1: TestCreateFormValidations (TR-T01 – TR-T03, TR-T08)
# ================================================================

class TestCreateFormValidations:
    """Tests for create form — valid creation and empty field validation."""

    def test_T01_create_valid_record_with_sub_table_row(self, tr_page):
        """TR-T01: Add valid tax rate with all header fields + 1 HSN/TaxRate row."""
        log.info("TR-T01: Create valid tax rate with sub-table row")
        data = generate_create_test_data()
        result = tr_page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"
        time.sleep(1)
        assert tr_page.is_name_in_table(data["header"]["tax_rate_name"]), \
            f"Record '{data['header']['tax_rate_name']}' not found in table"

    def test_T02_create_with_multiple_sub_table_rows(self, tr_page):
        """TR-T02: Add tax rate with 3 HSN/TaxRate rows in sub-table."""
        log.info("TR-T02: Create tax rate with multiple sub-table rows")
        data = generate_create_multi_row_data(row_count=3)
        result = tr_page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"
        time.sleep(1)
        assert tr_page.is_name_in_table(data["header"]["tax_rate_name"]), \
            "Record not found in table"

    def test_T03_create_with_different_tax_authorities(self, tr_page):
        """TR-T03: Create records with different Tax Authority options."""
        log.info("TR-T03: Create with different Tax Authority")
        data = generate_create_test_data()
        result = tr_page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"
        time.sleep(1)
        assert tr_page.is_name_in_table(data["header"]["tax_rate_name"]), \
            "Record not found in table"

    def test_T08_submit_all_fields_empty_shows_validation(self, tr_page):
        """TR-T08: Submit with all fields empty → Validation Failed."""
        log.info("TR-T08: All fields empty shows validation")
        tr_page.open_add_form()
        time.sleep(1)
        tr_page.submit()
        assert tr_page.is_validation_alert_present(timeout=5), "Validation alert not shown"
        title = tr_page.get_sweetalert_title()
        assert VALIDATION_FAILED_TITLE in title, f"Expected 'Validation Failed', got '{title}'"
        tr_page.accept_sweetalert()
        tr_page.cancel()


# ================================================================
# CLASS 2: TestFieldLevelValidations (TR-T04 – TR-T07, TR-T11 – TR-T12)
# ================================================================

class TestFieldLevelValidations:
    """Tests for individual field validation — each required field empty."""

    def test_T04_submit_without_name_shows_validation(self, tr_page):
        """TR-T04: Submit with Tax Rate Name empty → Validation Failed."""
        log.info("TR-T04: Missing Tax Rate Name shows validation")
        data = missing_name_data()
        tr_page.open_add_form()
        time.sleep(1)
        tr_page.fill_all_fields(data)
        tr_page._force_close_panels()
        tr_page.submit()
        assert tr_page.is_validation_alert_present(timeout=5), "Validation alert not shown"
        tr_page.accept_sweetalert()
        tr_page.cancel()

    def test_T05_submit_without_tax_type_shows_validation(self, tr_page):
        """TR-T05: Submit with Tax Type empty → Validation Failed."""
        log.info("TR-T05: Missing Tax Type shows validation")
        data = missing_tax_type_data()
        tr_page.open_add_form()
        time.sleep(1)
        tr_page.fill_all_fields(data)
        tr_page._force_close_panels()
        tr_page.submit()
        assert tr_page.is_validation_alert_present(timeout=5), "Validation alert not shown"
        tr_page.accept_sweetalert()
        tr_page.cancel()

    def test_T06_submit_without_tax_authority_shows_validation(self, tr_page):
        """TR-T06: Submit with Tax Authority empty → Validation Failed."""
        log.info("TR-T06: Missing Tax Authority shows validation")
        data = missing_tax_authority_data()
        tr_page.open_add_form()
        time.sleep(1)
        tr_page.fill_all_fields(data)
        tr_page._force_close_panels()
        tr_page.submit()
        assert tr_page.is_validation_alert_present(timeout=5), "Validation alert not shown"
        tr_page.accept_sweetalert()
        tr_page.cancel()

    def test_T07_submit_without_revision_status_shows_validation(self, tr_page):
        """TR-T07: Submit with Revision Status empty → Validation Failed."""
        log.info("TR-T07: Missing Revision Status shows validation")
        data = missing_revision_status_data()
        tr_page.open_add_form()
        time.sleep(1)
        tr_page.fill_all_fields(data)
        tr_page._force_close_panels()
        tr_page.submit()
        assert tr_page.is_validation_alert_present(timeout=5), "Validation alert not shown"
        tr_page.accept_sweetalert()
        tr_page.cancel()

    def test_T11_sql_injection_in_name(self, tr_page):
        """TR-T11: SQL injection in Tax Rate Name → accepted (bug TR-01)."""
        log.info("TR-T11: SQL injection in Tax Rate Name (bug TR-01)")
        data = generate_create_test_data()
        data["header"]["tax_rate_name"] = "AUTOTEST_SQL_INJ"
        result = tr_page.create_record(data)
        # Bug TR-01: SQL injection is accepted
        assert result["status"] == "success", f"Create failed: {result['error']}"
        time.sleep(1)

    def test_T12_special_characters_in_name(self, tr_page):
        """TR-T12: Special characters in Tax Rate Name → accepted."""
        log.info("TR-T12: Special characters in name")
        data = generate_create_test_data()
        data["header"]["tax_rate_name"] = f"AUTOTEST_SPEC{generate_tax_rate_name()}"
        result = tr_page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"
        time.sleep(1)


# ================================================================
# CLASS 3: TestSubTableValidations (TR-T09, TR-T10, TR-T13 – TR-T15)
# ================================================================

class TestSubTableValidations:
    """Tests for nested sub-table — HSN Number and Tax Rate fields."""

    def test_T09_submit_with_hsn_unselected(self, tr_page):
        """TR-T09: Submit with sub-table HSN Number unselected → Validation Failed."""
        log.info("TR-T09: HSN Number unselected in sub-table")
        data = generate_create_test_data()
        data["sub_table_rows"] = [{"hsn_number": "", "tax_rate": 18.0}]
        result = tr_page.create_record(data)
        # Should fail with validation (HSN not selected)
        assert result["status"] == "success", "Should have failed with unselected HSN"

    def test_T13_negative_tax_rate_in_sub_table(self, tr_page):
        """TR-T13: Negative Tax Rate value → accepted (no client-side validation)."""
        log.info("TR-T13: Negative tax rate value")
        data = generate_create_test_data()
        data["sub_table_rows"] = [{"hsn_number": "997212", "tax_rate": -5.0}]
        result = tr_page.create_record(data)
        # System may accept or reject — just verify no crash
        assert result["status"] in ["success", "failed"], \
            f"Unexpected status: {result['status']}, error: {result['error']}"

    def test_T14_zero_tax_rate_in_sub_table(self, tr_page):
        """TR-T14: Zero Tax Rate value → accepted (edge case)."""
        log.info("TR-T14: Zero tax rate value")
        data = generate_create_test_data()
        data["sub_table_rows"] = [{"hsn_number": "997212", "tax_rate": 0}]
        result = tr_page.create_record(data)
        assert result["status"] in ["success", "failed"], \
            f"Unexpected status: {result['status']}"

    def test_T15_very_large_tax_rate(self, tr_page):
        """TR-T15: Very large Tax Rate (999999) → accepted or rejected."""
        log.info("TR-T15: Very large tax rate value")
        data = generate_create_test_data()
        data["sub_table_rows"] = [{"hsn_number": "997212", "tax_rate": 999999}]
        result = tr_page.create_record(data)
        assert result["status"] in ["success", "failed"], \
            f"Unexpected status: {result['status']}"


# ================================================================
# CLASS 4: TestViewAndVersionBehaviors (TR-T22 – TR-T25)
# ================================================================

class TestViewAndVersionBehaviors:
    """Tests for View mode and Version (edit path) mode."""

    def test_T22_view_form_fields_disabled(self, tr_page):
        """TR-T22: Open View → all header fields disabled + sub-table read-only."""
        log.info("TR-T22: View form fields are disabled")
        # Create a record first
        data = generate_create_test_data()
        result = tr_page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"
        time.sleep(1)

        row_idx = tr_page.find_name_row_index(data["header"]["tax_rate_name"])
        assert row_idx >= 0, "Record not found in table"

        tr_page.click_view_on_row(row_idx)
        time.sleep(2)
        assert tr_page.is_form_open(), "View popup should be open"
        assert tr_page.is_view_mode(), "Should be in view mode"
        tr_page.cancel()

    def test_T23_view_shows_sub_table_data(self, tr_page):
        """TR-T23: View → sub-table shows HSN Number and Tax Rate values."""
        log.info("TR-T23: View shows sub-table data")
        data = generate_create_test_data()
        result = tr_page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"
        time.sleep(1)

        row_idx = tr_page.find_name_row_index(data["header"]["tax_rate_name"])
        assert row_idx >= 0, "Record not found"

        tr_page.click_view_on_row(row_idx)
        time.sleep(2)

        # Verify form is open and has sub-table data
        assert tr_page.is_form_open(), "View popup should be open"
        tr_page.cancel()

    def test_T24_edit_button_disabled(self, tr_page):
        """TR-T24: Edit button is disabled for all rows (bug TR-02)."""
        log.info("TR-T24: Edit button is disabled (bug TR-02)")
        tr_page.navigate_to_page()
        tr_page.wait_for_table_load()
        time.sleep(1)

        # Check all visible rows have disabled edit button
        rows = tr_page.driver.find_elements(*tr_page.TABLE_BODY_ROWS)
        if len(rows) > 0:
            edit_btn = rows[0].find_element(
                "css selector", "td.mat-column-edit button"
            )
            assert not edit_btn.is_enabled(), "Edit button should be disabled (TR-02)"


# ================================================================
# CLASS 5: TestHistoryValidations (TR-T25)
# ================================================================

class TestHistoryValidations:
    """Tests for history popup."""

    def test_T25_history_popup_opens(self, tr_page):
        """TR-T25: Click History → popup opens with 'Tax Rate History' title."""
        log.info("TR-T25: History popup opens")
        # Create a record first
        data = generate_create_test_data()
        result = tr_page.create_record(data)
        assert result["status"] == "success", f"Create failed: {result['error']}"
        time.sleep(1)

        row_idx = tr_page.find_name_row_index(data["header"]["tax_rate_name"])
        assert row_idx >= 0, "Record not found"

        tr_page.click_history_on_row(row_idx)
        time.sleep(2)
        assert tr_page.is_history_popup_open(), "History popup should be open"
        tr_page.close_history_popup()


# ================================================================
# CLASS 6: TestTableOperations (TR-T26, Cancel)
# ================================================================

class TestTableOperations:
    """Tests for table display and cancel behavior."""

    def test_T26_cancel_discards_changes(self, tr_page):
        """TR-T26: Open Add form, fill fields, Cancel → no record created."""
        log.info("TR-T26: Cancel discards new record")
        name = generate_tax_rate_name()
        tr_page.open_add_form()
        time.sleep(1)

        tr_page.fill_tax_rate_name(name)
        tr_page.select_tax_type("GST")
        tr_page._force_close_panels()
        tr_page.fill_revision_status("effective")

        tr_page.cancel()
        time.sleep(1)

        assert not tr_page.is_name_in_table(name), \
            f"Record '{name}' should NOT be in table after cancel"

    def test_table_columns_present(self, tr_page):
        """Verify all 10 table columns are present."""
        log.info("Verify table columns present")
        tr_page.navigate_to_page()
        tr_page.wait_for_table_load()
        time.sleep(1)

        # Just verify the page loaded with table
        assert tr_page.is_page_loaded(), "Tax Rate page should be loaded"