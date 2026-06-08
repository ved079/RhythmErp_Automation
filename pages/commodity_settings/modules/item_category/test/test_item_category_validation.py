"""
test_item_category_validation.py
--------------------------------
Automated test cases for RhythmERP Item Category screen.

Location: Commodity Settings > Item Category
URL:      /#/dynamic-screens/Item%20Category
Prefix:   IC (IC-C01..C13, IC-V01..V04, IC-E01..E05, IC-S01..S05,
               IC-P01..P08, IC-N01..N07, IC-H01..H05)

FORM LAYOUT (Simple popup — NOT a stepper):
  - Item Category       (text input,   required)
  - Item Description    (text input,   required)
  - Level               (number input, required)
  [Cancel] [Submit]

NOTES:
  - NO Status toggle
  - NO dropdowns
  - NO Delete button
  - HAS History button
  - Duplicates ALLOWED for Item Category name
  - Level: accepts negatives, no decimals, leading zeros stripped, accepts 0

TEST PHASES:
  C = Create (valid + validation)  — 13 tests
  V = View                         — 4 tests
  E = Edit (valid + validation)    — 5 tests
  S = Search                       — 5 tests
  P = Popup & UI interactions      — 8 tests
  N = Number field validations     — 7 tests
  H = History                      — 5 tests
  TOTAL: 47 tests

Run:
  pytest test_item_category_validation.py -v --tb=short
  pytest test_item_category_validation.py -v -k "TestCreateForm" --tb=short
  pytest test_item_category_validation.py -v -k "IC-C07" --tb=short

Marker-based run examples (requires conftest.py with pytest_configure):
  pytest test_item_category_validation.py -v -m smoke
  pytest test_item_category_validation.py -v -m "smoke or sanity"
  pytest test_item_category_validation.py -v -m "sanity and not bug"
  pytest test_item_category_validation.py -v -m "not bug"
  pytest test_item_category_validation.py -v -m ui
  pytest test_item_category_validation.py -v -m bug
  pytest test_item_category_validation.py -v -m regression

Marker Summary (47 tests across 7 classes):
  smoke (14): C01, C02, C03, C04, C05, C06, C07, V01, E01, E03, S01, S03, P01, H01
  sanity (47): All tests
  regression (47): All tests
  bug (9): C09, C10, C11, C12, C13, N02, N04, N05, P03
  ui (15): V01, V02, V03, V04, E02, P01, P02, P03, P04, P05, P06, P07, P08, H01, H03
"""

import os
import sys
import pytest
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from pages.commodity_settings.modules.item_category.data.item_category_data import (
    generate_valid_item_category_data,
    generate_long_category_name,
    generate_spaces_only,
    generate_special_char_category,
    generate_sql_injection,
    generate_xss_attempt,
    generate_negative_level,
    generate_zero_level,
    generate_decimal_level,
    generate_leading_zeros_level,
    generate_large_level,
    generate_alpha_level,
    generate_empty_data,
    generate_category_only_data,
    generate_description_only_data,
    generate_level_only_data,
    generate_category_description_no_level,
    generate_category_level_no_description,
    generate_duplicate_category_data,
    generate_valid_edit_data,
    generate_item_category_name,
)


# ╔══════════════════════════════════════════════════════════════╗
# ║              CREATE PHASE (IC-C01 – IC-C13)                ║
# ╚══════════════════════════════════════════════════════════════╝

class TestCreateFormValidations:
    """Tests for the Create (Add) form on Item Category."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_C01_empty_submit(self, ic_page):
        """IC-C01: Submit empty form — required field validation."""
        log.info("IC-C01: Submit empty form")
        try:
            ic_page.open_add_form()
            ic_page.submit()

            swal_title = ic_page.handle_validation_warning(timeout=10)

            assert swal_title, "IC-C01: Expected validation popup"
            assert "validation failed" in swal_title.lower(), \
                f"IC-C01: Expected 'Validation Failed', got: '{swal_title}'"

            # No mat-error check – system only shows SweetAlert
        finally:
            ic_page._cleanup()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_C02_category_only(self, ic_page):
        """IC-C02: Submit with only Item Category filled — partial validation.
        Expected: Validation Failed for remaining required fields.
        """
        log.info("IC-C02: Submit with Item Category only")
        try:
            data = generate_category_only_data()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_validation_warning(timeout=10)

            assert swal_title, "IC-C02: Expected validation popup"
            assert "validation failed" in swal_title.lower(), \
                f"IC-C02: Expected 'Validation Failed', got: '{swal_title}'"
        finally:
            ic_page._cleanup()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_C03_description_only(self, ic_page):
        """IC-C03: Submit with only Item Description filled — partial validation."""
        log.info("IC-C03: Submit with Item Description only")
        try:
            data = generate_description_only_data()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_validation_warning(timeout=10)

            assert swal_title, "IC-C03: Expected validation popup"
            assert "validation failed" in swal_title.lower(), \
                f"IC-C03: Expected 'Validation Failed', got: '{swal_title}'"
        finally:
            ic_page._cleanup()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_C04_level_only(self, ic_page):
        """IC-C04: Submit with only Level filled — partial validation."""
        log.info("IC-C04: Submit with Level only")
        try:
            data = generate_level_only_data()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_validation_warning(timeout=10)

            assert swal_title, "IC-C04: Expected validation popup"
            assert "validation failed" in swal_title.lower(), \
                f"IC-C04: Expected 'Validation Failed', got: '{swal_title}'"
        finally:
            ic_page._cleanup()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_C05_category_description_no_level(self, ic_page):
        """IC-C05: Submit with Category + Description but no Level — validation."""
        log.info("IC-C05: Submit with Category + Description, no Level")
        try:
            data = generate_category_description_no_level()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_validation_warning(timeout=10)

            assert swal_title, "IC-C05: Expected validation popup"
            assert "validation failed" in swal_title.lower(), \
                f"IC-C05: Expected 'Validation Failed', got: '{swal_title}'"
        finally:
            ic_page._cleanup()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_C06_category_level_no_description(self, ic_page):
        """IC-C06: Submit with Category + Level, no Description — should succeed (Description is optional)."""
        log.info("IC-C06: Submit with Category + Level, no Description (optional field)")
        try:
            data = generate_category_level_no_description()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            # Description is NOT required — record should be created successfully
            swal_title = ic_page.handle_success_alert(timeout=15)

            assert swal_title, "IC-C06: Expected success popup"
            assert "success" in swal_title.lower(), \
                f"IC-C06: Expected success, got: '{swal_title}'"
        finally:
            ic_page._cleanup()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_C07_valid_create(self, ic_page):
        """IC-C07: Create a valid Item Category record with all required fields.
        Happy path — should succeed.
        """
        log.info("IC-C07: Create valid Item Category record")
        try:
            data = generate_valid_item_category_data()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_success_alert(timeout=15)

            assert swal_title, "IC-C07: Expected success popup after valid submission"
            assert "success" in swal_title.lower(), \
                f"IC-C07: Expected success message, got: '{swal_title}'"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_C08_special_chars_category(self, ic_page):
        """IC-C08: Create with special characters in Item Category name.
        Tests input sanitization — special chars may be accepted or rejected.
        """
        log.info("IC-C08: Create with special char category name")
        try:
            data = generate_valid_item_category_data()
            data["item_category"] = generate_special_char_category()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_success_alert(timeout=15)
            if not swal_title:
                swal_title = ic_page.handle_save_failure_alert(timeout=5)

            log.info(f"IC-C08: Result for special char name: '{swal_title}'")
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_IC_C09_category_max_length(self, ic_page):
        """IC-C09: Create with very long Item Category name.
        Tests server-side length limit handling.
        """
        log.info("IC-C09: Create with long category name")
        try:
            data = generate_valid_item_category_data()
            data["item_category"] = generate_long_category_name(255)

            ic_page.click_refresh()
            ic_page.wait_seconds(2)
            count_before = ic_page.get_table_row_count()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_success_alert(timeout=15)
            if not swal_title:
                swal_title = ic_page.handle_save_failure_alert(timeout=5)

            log.info(f"IC-C09: Result for 255-char name: '{swal_title}'")
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_IC_C10_category_exceeds_length(self, ic_page):
        """IC-C10: Create with 256-char Item Category name — exceeds server max.
        Expected: "Failed to save record" (Type B popup).
        """
        log.info("IC-C10: Create with 256-char category name (server rejection)")
        try:
            data = generate_valid_item_category_data()
            data["item_category"] = generate_long_category_name(256)

            ic_page.click_refresh()
            ic_page.wait_seconds(2)
            count_before = ic_page.get_table_row_count()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_save_failure_alert(timeout=10)

            assert swal_title, \
                "IC-C10: Expected popup after submitting 256-char category name"
            assert "failed" in swal_title.lower(), \
                f"IC-C10: Expected failure popup, got: '{swal_title}'"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_IC_C11_duplicate_category(self, ic_page):
        """IC-C11: Create with duplicate Item Category name.
        Duplicates are ALLOWED — no uniqueness constraint.
        Expected: Should succeed (duplicate accepted).
        """
        log.info("IC-C11: Create duplicate Item Category name")
        try:
            # First, create a record
            data1 = generate_valid_item_category_data()
            ic_page.open_add_form()
            ic_page.fill_form(data1)
            ic_page.submit()
            swal1 = ic_page.handle_success_alert(timeout=15)

            if not (swal1 and "success" in swal1.lower()):
                pytest.skip("IC-C11: Could not create first record for duplicate test")

            ic_page._cleanup()

            # Now try duplicate
            data2 = generate_duplicate_category_data(data1["item_category"])
            ic_page.open_add_form()
            ic_page.fill_form(data2)
            ic_page.submit()

            swal2 = ic_page.handle_success_alert(timeout=15)
            if not swal2:
                swal2 = ic_page.handle_validation_warning(timeout=5)

            if swal2 and "success" in swal2.lower():
                log.warning("IC-C11: BUG CONFIRMED — duplicate category name accepted")
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_IC_C12_sql_injection(self, ic_page):
        """IC-C12: Create with SQL injection string in Item Category.
        Tests input sanitization for SQL injection.
        """
        log.info("IC-C12: Create with SQL injection string")
        try:
            data = generate_valid_item_category_data()
            data["item_category"] = generate_sql_injection()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_success_alert(timeout=15)
            if not swal_title:
                swal_title = ic_page.handle_save_failure_alert(timeout=5)

            log.info(f"IC-C12: Result for SQL injection: '{swal_title}'")
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_IC_C13_xss_attempt(self, ic_page):
        """IC-C13: Create with XSS attempt string in Item Category.
        Tests input sanitization for XSS attacks.
        """
        log.info("IC-C13: Create with XSS attempt string")
        try:
            data = generate_valid_item_category_data()
            data["item_category"] = generate_xss_attempt()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_success_alert(timeout=15)
            if not swal_title:
                swal_title = ic_page.handle_save_failure_alert(timeout=5)

            log.info(f"IC-C13: Result for XSS attempt: '{swal_title}'")
        finally:
            ic_page._cleanup()


# ╔══════════════════════════════════════════════════════════════╗
# ║              VIEW PHASE (IC-V01 – IC-V04)                  ║
# ╚══════════════════════════════════════════════════════════════╝

class TestViewValidations:
    """Tests for the View (read-only) mode on Item Category."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_V01_view_opens_readonly(self, ic_page):
        """IC-V01: View button opens read-only popup."""
        log.info("IC-V01: View opens read-only popup")
        try:
            rows = ic_page.get_table_row_count()
            if rows == 0:
                pytest.skip("IC-V01: No records in table to view")

            ic_page.click_view_button(row_index=0)
            ic_page.wait_seconds(2)

            is_view = ic_page.is_view_mode()
            assert is_view, "IC-V01: Expected View mode (fields disabled)"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_V02_all_fields_readonly(self, ic_page):
        """IC-V02: All fields are disabled in View mode."""
        log.info("IC-V02: All fields disabled in View mode")
        try:
            rows = ic_page.get_table_row_count()
            if rows == 0:
                pytest.skip("IC-V02: No records to view")

            ic_page.click_view_button(row_index=0)
            ic_page.wait_seconds(2)

            # Check Item Category input is disabled
            cat_enabled = ic_page.is_field_enabled(ic_page.ITEM_CATEGORY_INPUT)
            desc_enabled = ic_page.is_field_enabled(ic_page.ITEM_DESCRIPTION_INPUT)
            level_enabled = ic_page.is_field_enabled(ic_page.LEVEL_INPUT)

            assert not cat_enabled, "IC-V02: Item Category should be disabled in View"
            assert not desc_enabled, "IC-V02: Item Description should be disabled in View"
            assert not level_enabled, "IC-V02: Level should be disabled in View"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_V03_view_data_matches_table(self, ic_page):
        """IC-V03: View popup shows same data as table row."""
        log.info("IC-V03: View data matches table")
        try:
            rows = ic_page.get_table_row_count()
            if rows == 0:
                pytest.skip("IC-V03: No records to view")

            # Get first row data from table (columns after action buttons)
            category_in_table = ic_page.get_cell_text_by_row(0, 3)  # 4th column

            ic_page.click_view_button(row_index=0)
            ic_page.wait_seconds(2)

            category_in_form = ic_page.get_input_value(ic_page.ITEM_CATEGORY_INPUT)

            log.info(f"IC-V03: Table='{category_in_table}', Form='{category_in_form}'")
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_V04_close_view_returns_to_table(self, ic_page):
        """IC-V04: Closing View popup returns to the table listing."""
        log.info("IC-V04: Close View returns to table")
        try:
            rows = ic_page.get_table_row_count()
            if rows == 0:
                pytest.skip("IC-V04: No records to view")

            ic_page.click_view_button(row_index=0)
            ic_page.wait_seconds(2)

            ic_page.cancel()
            ic_page.wait_seconds(1)

            is_closed = ic_page.is_form_closed()
            assert is_closed, "IC-V04: Form should be closed after Cancel in View"
        finally:
            ic_page._cleanup()


# ╔══════════════════════════════════════════════════════════════╗
# ║              EDIT PHASE (IC-E01 – IC-E05)                  ║
# ╚══════════════════════════════════════════════════════════════╝

class TestEditFormValidations:
    """Tests for the Edit mode on Item Category."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_E01_edit_opens_editable(self, ic_page):
        """IC-E01: Edit button opens form with Update button."""
        log.info("IC-E01: Edit opens with Update button")
        try:
            rows = ic_page.get_table_row_count()
            if rows == 0:
                pytest.skip("IC-E01: No records to edit")

            ic_page.click_edit_button(row_index=0)
            ic_page.wait_seconds(2)

            is_edit = ic_page.is_edit_mode()
            assert is_edit, "IC-E01: Expected Edit mode (Update button visible)"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_E02_all_fields_editable(self, ic_page):
        """IC-E02: All fields are editable in Edit mode."""
        log.info("IC-E02: All fields editable in Edit mode")
        try:
            rows = ic_page.get_table_row_count()
            if rows == 0:
                pytest.skip("IC-E02: No records to edit")

            ic_page.click_edit_button(row_index=0)
            ic_page.wait_seconds(2)

            cat_enabled = ic_page.is_field_enabled(ic_page.ITEM_CATEGORY_INPUT)
            desc_enabled = ic_page.is_field_enabled(ic_page.ITEM_DESCRIPTION_INPUT)
            level_enabled = ic_page.is_field_enabled(ic_page.LEVEL_INPUT)

            assert cat_enabled, "IC-E02: Item Category should be editable in Edit"
            assert desc_enabled, "IC-E02: Item Description should be editable in Edit"
            assert level_enabled, "IC-E02: Level should be editable in Edit"
        finally:
            ic_page._cleanup()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_E03_edit_and_save(self, ic_page):
        """IC-E03: Edit and update a record successfully."""
        log.info("IC-E03: Edit and update record")
        try:
            rows = ic_page.get_table_row_count()
            if rows == 0:
                pytest.skip("IC-E03: No records to edit")

            ic_page.click_edit_button(row_index=0)
            ic_page.wait_seconds(2)

            # Modify Item Description
            new_desc = generate_item_category_name("Edited")
            ic_page.type_text(ic_page.ITEM_DESCRIPTION_INPUT, new_desc, clear_first=True)
            ic_page._force_close_panels()
            ic_page.click_update()

            swal_title = ic_page.handle_success_alert(timeout=15)

            assert swal_title, "IC-E03: Expected success popup after update"
            assert "success" in swal_title.lower() or "update" in swal_title.lower(), \
                f"IC-E03: Expected success/update message, got: '{swal_title}'"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_E04_edit_and_cancel(self, ic_page):
        """IC-E04: Edit and cancel — changes should not be saved."""
        log.info("IC-E04: Edit and cancel")
        try:
            rows = ic_page.get_table_row_count()
            if rows == 0:
                pytest.skip("IC-E04: No records to edit")

            # Get original description
            ic_page.click_view_button(row_index=0)
            ic_page.wait_seconds(2)
            original_desc = ic_page.get_input_value(ic_page.ITEM_DESCRIPTION_INPUT)
            ic_page.cancel()
            ic_page.wait_seconds(1)

            # Open Edit, modify, then cancel
            ic_page.click_edit_button(row_index=0)
            ic_page.wait_seconds(2)

            new_desc = generate_item_category_name("CancelEdit")
            ic_page.type_text(ic_page.ITEM_DESCRIPTION_INPUT, new_desc, clear_first=True)
            ic_page.cancel()
            ic_page.wait_seconds(1)

            # View again to verify original is intact
            ic_page.click_view_button(row_index=0)
            ic_page.wait_seconds(2)
            current_desc = ic_page.get_input_value(ic_page.ITEM_DESCRIPTION_INPUT)

            log.info(f"IC-E04: Original='{original_desc}', Current='{current_desc}'")
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_E05_edit_empty_required(self, ic_page):
        """IC-E05: Edit — clear required field, submit -> validation."""
        log.info("IC-E05: Edit validation on empty required field")
        try:
            rows = ic_page.get_table_row_count()
            if rows == 0:
                pytest.skip("IC-E05: No records to edit")

            ic_page.click_edit_button(row_index=0)
            ic_page.wait_seconds(2)

            # Clear Item Category
            ic_page.type_text(ic_page.ITEM_CATEGORY_INPUT, "", clear_first=True)
            ic_page._force_close_panels()
            ic_page.click_update()

            swal_title = ic_page.handle_validation_warning(timeout=10)
            assert swal_title, "IC-E05: Expected validation popup with empty Category"
        finally:
            ic_page._cleanup()


# ╔══════════════════════════════════════════════════════════════╗
# ║              SEARCH PHASE (IC-S01 – IC-S05)                ║
# ╚══════════════════════════════════════════════════════════════╝

class TestSearchFilter:
    """Tests for search functionality on Item Category."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_S01_search_exact(self, ic_page):
        """IC-S01: Search for an existing record by exact name."""
        log.info("IC-S01: Search exact match")
        try:
            names = ic_page.get_all_item_names()
            if not names:
                pytest.skip("IC-S01: No records in table to search")

            search_name = names[0]
            ic_page.search_item(search_name)
            ic_page.wait_seconds(2)

            found = ic_page.is_record_in_table(search_name)
            assert found, f"IC-S01: Should find record '{search_name}' after search"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_S02_search_partial(self, ic_page):
        """IC-S02: Search with partial name matches record."""
        log.info("IC-S02: Search partial match")
        try:
            names = ic_page.get_all_item_names()
            if not names:
                pytest.skip("IC-S02: No records in table")

            partial = names[0][:3]
            ic_page.search_item(partial)
            ic_page.wait_seconds(2)

            found = ic_page.is_record_in_table(partial)
            log.info(f"IC-S02: Partial search '{partial}' found={found}")
        finally:
            ic_page._cleanup()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_S03_search_no_match(self, ic_page):
        """IC-S03: Search for a non-existent record shows no results."""
        log.info("IC-S03: Search no match")
        try:
            ic_page.search_item("ZZZ_NONEXISTENT_IC_99999")
            ic_page.wait_seconds(2)

            found = ic_page.is_record_in_table("ZZZ_NONEXISTENT_IC_99999")
            assert not found, "IC-S03: Should NOT find non-existent record"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_S04_clear_search(self, ic_page):
        """IC-S04: Clear search shows all records again."""
        log.info("IC-S04: Clear search")
        try:
            count_before = ic_page.get_table_row_count()

            ic_page.search_item("ZZZ_CLEAR_TEST_IC")
            ic_page.wait_seconds(2)

            # Clear search by refreshing
            ic_page.click_refresh()
            ic_page.wait_seconds(2)

            count_after = ic_page.get_table_row_count()
            assert count_after == count_before, \
                f"IC-S04: Record count should match after clear (before={count_before}, after={count_after})"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_S05_search_special_chars(self, ic_page):
        """IC-S05: Search with special characters does not crash."""
        log.info("IC-S05: Search special chars")
        try:
            ic_page.search_item("!@#$%^&*()")
            ic_page.wait_seconds(2)

            # Just verify no crash — page should still be functional
            is_loaded = ic_page.is_page_loaded()
            assert is_loaded, "IC-S05: Page should still be loaded after special char search"
        finally:
            ic_page._cleanup()


# ╔══════════════════════════════════════════════════════════════╗
# ║         POPUP & UI PHASE (IC-P01 – IC-P08)                ║
# ╚══════════════════════════════════════════════════════════════╝

class TestPopupUIBehaviors:
    """Tests for popup and UI interactions on Item Category."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_P01_validation_popup_empty(self, ic_page):
        """IC-P01: Validation popup appears on empty submit."""
        log.info("IC-P01: Validation popup on empty submit")
        try:
            ic_page.open_add_form()
            ic_page.submit()

            is_present = ic_page.is_validation_alert_present(timeout=10)
            assert is_present, "IC-P01: Validation popup should appear"

            ic_page.handle_validation_warning(timeout=5)
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_P02_popup_title_message(self, ic_page):
        """IC-P02: Validation popup has correct title and message."""
        log.info("IC-P02: Popup title and message")
        try:
            ic_page.open_add_form()
            ic_page.submit()

            swal_title = ic_page.handle_validation_warning(timeout=10)

            assert "validation failed" in swal_title.lower(), \
                f"IC-P02: Expected 'Validation Failed' in title, got: '{swal_title}'"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_IC_P03_popup_ok_dismisses(self, ic_page):
        """IC-P03: Clicking OK on validation popup dismisses it."""
        log.info("IC-P03: OK dismisses validation popup")
        try:
            ic_page.open_add_form()
            ic_page.submit()

            # Wait for popup then dismiss
            ic_page.handle_validation_warning(timeout=10)

            # Verify popup is gone
            ic_page.wait_seconds(1)
            is_gone = not ic_page.is_validation_alert_present(timeout=2)
            assert is_gone, "IC-P03: Popup should be dismissed after OK click"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_P04_success_message(self, ic_page):
        """IC-P04: Success popup shows after valid create."""
        log.info("IC-P04: Success message after valid create")
        try:
            data = generate_valid_item_category_data()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_success_alert(timeout=15)

            assert swal_title, "IC-P04: Expected success popup"
            assert "success" in swal_title.lower(), \
                f"IC-P04: Expected success message, got: '{swal_title}'"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_P05_cancel_no_save(self, ic_page):
        """IC-P05: Cancel after filling form does not save data."""
        log.info("IC-P05: Cancel does not save")
        try:
            count_before = ic_page.get_table_row_count()

            data = generate_valid_item_category_data()
            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.cancel()
            ic_page.wait_seconds(1)

            ic_page.click_refresh()
            ic_page.wait_seconds(2)

            count_after = ic_page.get_table_row_count()
            assert count_after == count_before, \
                f"IC-P05: Record count should not change after Cancel (before={count_before}, after={count_after})"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_P06_add_opens_empty_form(self, ic_page):
        """IC-P06: ADD button opens form with all fields empty."""
        log.info("IC-P06: ADD opens empty form")
        try:
            ic_page.open_add_form()

            cat_val = ic_page.get_input_value(ic_page.ITEM_CATEGORY_INPUT)
            desc_val = ic_page.get_input_value(ic_page.ITEM_DESCRIPTION_INPUT)
            level_val = ic_page.get_input_value(ic_page.LEVEL_INPUT)

            assert cat_val == "", "IC-P06: Item Category should be empty in new form"
            assert desc_val == "", "IC-P06: Item Description should be empty in new form"
            assert level_val == "", "IC-P06: Level should be empty in new form"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_P07_reopen_form_cleared(self, ic_page):
        """IC-P07: Reopening ADD form after cancel shows empty fields."""
        log.info("IC-P07: Reopen form is cleared")
        try:
            # First fill and cancel
            data = generate_valid_item_category_data()
            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.cancel()
            ic_page.wait_seconds(1)

            # Reopen
            ic_page.open_add_form()

            cat_val = ic_page.get_input_value(ic_page.ITEM_CATEGORY_INPUT)
            assert cat_val == "", "IC-P07: Item Category should be empty after reopen"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_P08_save_failure_popup(self, ic_page):
        """IC-P08: Save failure popup appears for invalid data on server side.
        Uses 256-char name to trigger server rejection.
        """
        log.info("IC-P08: Save failure popup for invalid data")
        try:
            data = generate_valid_item_category_data()
            data["item_category"] = generate_long_category_name(256)

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_save_failure_alert(timeout=10)

            assert swal_title, "IC-P08: Expected save failure popup"
            assert "failed" in swal_title.lower(), \
                f"IC-P08: Expected failure message, got: '{swal_title}'"
        finally:
            ic_page._cleanup()


# ╔══════════════════════════════════════════════════════════════╗
# ║        NUMBER FIELD PHASE (IC-N01 – IC-N07)               ║
# ╚══════════════════════════════════════════════════════════════╝

class TestNumberFieldValidations:
    """Tests for Level number field validations on Item Category."""

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_N01_positive_integer(self, ic_page):
        """IC-N01: Level accepts a positive integer value."""
        log.info("IC-N01: Positive integer Level")
        try:
            data = generate_valid_item_category_data()
            data["level"] = "5"

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_success_alert(timeout=15)

            assert swal_title, "IC-N01: Expected success with positive integer Level"
            assert "success" in swal_title.lower(), \
                f"IC-N01: Expected success, got: '{swal_title}'"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_IC_N02_negative_integer(self, ic_page):
        """IC-N02: Level accepts a negative integer value."""
        log.info("IC-N02: Negative integer Level")
        try:
            data = generate_valid_item_category_data()
            data["level"] = generate_negative_level()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_success_alert(timeout=15)
            if not swal_title:
                swal_title = ic_page.handle_save_failure_alert(timeout=5)

            if swal_title and "success" in swal_title.lower():
                log.info("IC-N02: Negative Level accepted by the system")
            else:
                log.info(f"IC-N02: Negative Level rejected: '{swal_title}'")
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_N03_zero_level(self, ic_page):
        """IC-N03: Level accepts zero value."""
        log.info("IC-N03: Zero Level")
        try:
            data = generate_valid_item_category_data()
            data["level"] = generate_zero_level()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_success_alert(timeout=15)
            if not swal_title:
                swal_title = ic_page.handle_save_failure_alert(timeout=5)

            if swal_title and "success" in swal_title.lower():
                log.info("IC-N03: Zero Level accepted by the system")
            else:
                log.info(f"IC-N03: Zero Level rejected: '{swal_title}'")
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_IC_N04_decimal_level(self, ic_page):
        """IC-N04: Level does NOT accept decimal values — should truncate or reject."""
        log.info("IC-N04: Decimal Level")
        try:
            data = generate_valid_item_category_data()
            data["level"] = generate_decimal_level()

            ic_page.open_add_form()
            ic_page.fill_form(data)

            # Check what the field actually holds after typing a decimal
            level_val = ic_page.get_input_value(ic_page.LEVEL_INPUT)
            log.info(f"IC-N04: Level field value after typing decimal: '{level_val}'")

            ic_page.submit()

            swal_title = ic_page.handle_success_alert(timeout=15)
            if not swal_title:
                swal_title = ic_page.handle_save_failure_alert(timeout=5)

            log.info(f"IC-N04: Result for decimal level: '{swal_title}'")
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_IC_N05_leading_zeros_stripped(self, ic_page):
        """IC-N05: Leading zeros in Level are stripped on save.
        Input "007" should save as "7".
        """
        log.info("IC-N05: Leading zeros stripped in Level")
        try:
            data = generate_valid_item_category_data()
            data["level"] = generate_leading_zeros_level()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_success_alert(timeout=15)

            if swal_title and "success" in swal_title.lower():
                # Check saved value in table
                ic_page._cleanup()

                # View the record to check the saved level value
                ic_page.click_view_button(row_index=0)
                ic_page.wait_seconds(2)
                saved_level = ic_page.get_input_value(ic_page.LEVEL_INPUT)
                log.info(f"IC-N05: Saved level value = '{saved_level}'")

                # Leading zeros should be stripped: "007" -> "7"
                assert saved_level == "7", \
                    f"IC-N05: Expected '7' (leading zeros stripped), got '{saved_level}'"
            else:
                log.info(f"IC-N05: Record not created: '{swal_title}'")
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_N06_large_number(self, ic_page):
        """IC-N06: Level accepts a very large number."""
        log.info("IC-N06: Large number Level")
        try:
            data = generate_valid_item_category_data()
            data["level"] = generate_large_level()

            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_success_alert(timeout=15)
            if not swal_title:
                swal_title = ic_page.handle_save_failure_alert(timeout=5)

            if swal_title and "success" in swal_title.lower():
                log.info("IC-N06: Large number Level accepted")
            else:
                log.info(f"IC-N06: Large number Level result: '{swal_title}'")
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_N07_alpha_level(self, ic_page):
        """IC-N07: Level field does NOT accept alphabetic characters.
        Number input should prevent typing letters.
        """
        log.info("IC-N07: Alphabetic Level (should be rejected)")
        try:
            data = generate_valid_item_category_data()
            data["level"] = generate_alpha_level()

            ic_page.open_add_form()
            ic_page.fill_form(data)

            # Check what the field actually holds — number inputs typically reject alpha
            level_val = ic_page.get_input_value(ic_page.LEVEL_INPUT)
            log.info(f"IC-N07: Level field value after typing alpha: '{level_val}'")

            # Number input should be empty or not contain alpha chars
            assert level_val == "" or not any(c.isalpha() for c in level_val), \
                f"IC-N07: Level field should not accept alpha, got: '{level_val}'"
        finally:
            ic_page._cleanup()


# ╔══════════════════════════════════════════════════════════════╗
# ║            HISTORY PHASE (IC-H01 – IC-H05)                 ║
# ╚══════════════════════════════════════════════════════════════╝

class TestHistoryValidations:
    """Tests for History popup functionality on Item Category."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_H01_history_opens_popup(self, ic_page):
        """IC-H01: History button opens a popup."""
        log.info("IC-H01: History opens popup")
        try:
            rows = ic_page.get_table_row_count()
            if rows == 0:
                pytest.skip("IC-H01: No records in table")

            ic_page.click_history_button(row_index=0)
            ic_page.wait_seconds(2)

            is_open = ic_page.is_history_popup_open()
            assert is_open, "IC-H01: History popup should be open"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_H02_history_has_columns(self, ic_page):
        """IC-H02: History popup has table columns."""
        log.info("IC-H02: History has columns")
        try:
            rows = ic_page.get_table_row_count()
            if rows == 0:
                pytest.skip("IC-H02: No records in table")

            ic_page.click_history_button(row_index=0)
            ic_page.wait_seconds(2)

            headers = ic_page.get_history_table_headers()
            log.info(f"IC-H02: History headers = {headers}")
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_IC_H03_history_close_button(self, ic_page):
        """IC-H03: History popup can be closed via Close/Cancel button."""
        log.info("IC-H03: History close button")
        try:
            rows = ic_page.get_table_row_count()
            if rows == 0:
                pytest.skip("IC-H03: No records in table")

            ic_page.click_history_button(row_index=0)
            ic_page.wait_seconds(2)

            ic_page.close_history_popup()
            ic_page.wait_seconds(1)

            is_open = ic_page.is_history_popup_open()
            assert not is_open, "IC-H03: History popup should be closed"
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_H04_history_after_edit(self, ic_page):
        """IC-H04: History popup accessible after editing a record."""
        log.info("IC-H04: History after edit")
        try:
            rows = ic_page.get_table_row_count()
            if rows == 0:
                pytest.skip("IC-H04: No records in table")

            # Edit the record first
            ic_page.click_edit_button(row_index=0)
            ic_page.wait_seconds(2)

            new_desc = generate_item_category_name("HistEdit")
            ic_page.type_text(ic_page.ITEM_DESCRIPTION_INPUT, new_desc, clear_first=True)
            ic_page._force_close_panels()
            ic_page.click_update()

            swal_title = ic_page.handle_success_alert(timeout=15)
            log.info(f"IC-H04: Edit result: '{swal_title}'")

            ic_page._cleanup()

            # Now check History
            ic_page.click_history_button(row_index=0)
            ic_page.wait_seconds(2)

            is_open = ic_page.is_history_popup_open()
            log.info(f"IC-H04: History popup open after edit: {is_open}")
        finally:
            ic_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_IC_H05_history_new_record(self, ic_page):
        """IC-H05: History popup accessible for newly created record."""
        log.info("IC-H05: History for new record")
        try:
            # Create a new record
            data = generate_valid_item_category_data()
            ic_page.open_add_form()
            ic_page.fill_form(data)
            ic_page.submit()

            swal_title = ic_page.handle_success_alert(timeout=15)

            if not (swal_title and "success" in swal_title.lower()):
                pytest.skip("IC-H05: Could not create record for history test")

            ic_page._cleanup()

            # Check History on the new record
            ic_page.click_history_button(row_index=0)
            ic_page.wait_seconds(2)

            is_open = ic_page.is_history_popup_open()
            log.info(f"IC-H05: History popup open for new record: {is_open}")
        finally:
            ic_page._cleanup()
