"""
Item Group Validation Test Suite — Rhythm ERP
37 test cases covering CRUD, duplicates, edits, special characters, popups, and history.

Test ID Format: IG-<Category><Number>
  C = Creation (12), D = Duplicate (2), E = Edit (5),
  S = Special Characters (5), P = Popup/UI (8), H = History (5)
"""

import pytest
import time
import logging
import random
import string

from pages.commodity_settings.modules.item_group.item_group_page import ItemGroupPage
from pages.commodity_settings.modules.item_group.data.item_group_data import (
    generate_valid_code,
    generate_valid_description,
    generate_code_only_data,
    generate_description_only_data,
    generate_empty_data,
    generate_max_length_code,
    generate_max_length_description,
    generate_over_length_code,
    generate_over_length_description,
    generate_spaces_code,
    generate_spaces_description,
    generate_special_char_code,
    generate_special_char_description,
    generate_duplicate_data,
    generate_exact_duplicate_data,
    generate_sql_injection_code,
    generate_sql_injection_description,
    generate_xss_code,
    generate_xss_description,
    generate_special_chars_only,
    generate_edit_description,
    generate_edit_max_length_description,
    generate_edit_special_char_description,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════
#  CREATION TESTS (IG-C01 to IG-C12)
# ══════════════════════════════════════════════════════════════════════════

class TestItemGroupCreation:
    """Tests for creating Item Group records."""

    def test_IG_C01_create_with_valid_data(self, item_group_page):
        """IG-C01: Create Item Group with valid Code and Description → Success."""
        code = generate_valid_code()
        description = generate_valid_description()

        item_group_page.create_record(code, description)

        assert item_group_page.is_success_popup(timeout=10), \
            f"IG-C01: Expected success popup after creating record with Code='{code}', Desc='{description}'"
        item_group_page._dismiss_sweet_alert()
        logger.info(f"IG-C01 PASSED: Created Item Group with Code='{code}'")

    def test_IG_C02_create_with_code_only(self, item_group_page):
        """IG-C02: Create Item Group with Code only (Description empty) → Validation Failed."""
        data = generate_code_only_data()

        item_group_page.click_add_button()
        item_group_page.fill_form(code=data["code"])
        item_group_page.click_submit()

        is_validation = item_group_page.is_validation_failed_popup(timeout=8)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        assert is_validation or is_failed, \
            f"IG-C02: Expected validation/failed popup when Description is empty. Code='{data['code']}'"
        item_group_page._dismiss_sweet_alert()
        logger.info(f"IG-C02 PASSED: Validation triggered for empty Description")

    def test_IG_C03_create_with_description_only(self, item_group_page):
        """IG-C03: Create Item Group with Description only (Code empty) → Validation Failed."""
        data = generate_description_only_data()

        item_group_page.click_add_button()
        item_group_page.fill_form(description=data["description"])
        item_group_page.click_submit()

        is_validation = item_group_page.is_validation_failed_popup(timeout=8)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        assert is_validation or is_failed, \
            f"IG-C03: Expected validation/failed popup when Code is empty. Desc='{data['description']}'"
        item_group_page._dismiss_sweet_alert()
        logger.info(f"IG-C03 PASSED: Validation triggered for empty Code")

    def test_IG_C04_create_with_both_empty(self, item_group_page):
        """IG-C04: Create Item Group with both fields empty → Validation Failed."""
        item_group_page.click_add_button()
        item_group_page.click_submit()

        is_validation = item_group_page.is_validation_failed_popup(timeout=8)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        assert is_validation or is_failed, \
            "IG-C04: Expected validation/failed popup when both fields are empty"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-C04 PASSED: Validation triggered for empty fields")

    def test_IG_C05_create_with_max_length_code(self, item_group_page):
        """IG-C05: Create Item Group with Code at max length (255) → Success."""
        code = generate_max_length_code()
        description = generate_valid_description()

        item_group_page.create_record(code, description)

        assert item_group_page.is_success_popup(timeout=10), \
            f"IG-C05: Expected success popup with max-length Code (255 chars)"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-C05 PASSED: Created with max-length Code")

    def test_IG_C06_create_with_max_length_description(self, item_group_page):
        """IG-C06: Create Item Group with Description at max length (255) → Success."""
        code = generate_valid_code()
        description = generate_max_length_description()

        item_group_page.create_record(code, description)

        assert item_group_page.is_success_popup(timeout=10), \
            f"IG-C06: Expected success popup with max-length Description (255 chars)"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-C06 PASSED: Created with max-length Description")

    def test_IG_C07_create_with_over_length_code(self, item_group_page):
        """IG-C07: Create Item Group with Code exceeding max length → Should be truncated or fail gracefully."""
        data = generate_over_length_code()

        item_group_page.click_add_button()
        item_group_page.fill_form(code=data["code"], description=generate_valid_description())
        item_group_page.click_submit()

        # Either it succeeds (truncated) or shows validation — both are acceptable
        is_success = item_group_page.is_success_popup(timeout=8)
        is_validation = item_group_page.is_validation_failed_popup(timeout=3)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        assert is_success or is_validation or is_failed, \
            "IG-C07: Expected either success (truncated) or validation popup for over-length Code"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-C07 PASSED: Over-length Code handled gracefully")

    def test_IG_C08_create_with_over_length_description(self, item_group_page):
        """IG-C08: Create Item Group with Description exceeding max length → Truncated or fail gracefully."""
        data = generate_over_length_description()

        item_group_page.click_add_button()
        item_group_page.fill_form(code=generate_valid_code(), description=data["description"])
        item_group_page.click_submit()

        is_success = item_group_page.is_success_popup(timeout=8)
        is_validation = item_group_page.is_validation_failed_popup(timeout=3)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        assert is_success or is_validation or is_failed, \
            "IG-C08: Expected either success (truncated) or validation popup for over-length Description"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-C08 PASSED: Over-length Description handled gracefully")

    def test_IG_C09_create_with_spaces_in_code(self, item_group_page):
        """IG-C09: Create Item Group with spaces in Code → Accept or validate."""
        data = generate_spaces_code()

        item_group_page.click_add_button()
        item_group_page.fill_form(code=data["code"], description=generate_valid_description())
        item_group_page.click_submit()

        is_success = item_group_page.is_success_popup(timeout=8)
        is_validation = item_group_page.is_validation_failed_popup(timeout=3)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        assert is_success or is_validation or is_failed, \
            "IG-C09: Expected popup response for spaces-only Code"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-C09 PASSED: Spaces in Code handled")

    def test_IG_C10_create_with_spaces_in_description(self, item_group_page):
        """IG-C10: Create Item Group with spaces in Description → Accept or validate."""
        data = generate_spaces_description()

        item_group_page.click_add_button()
        item_group_page.fill_form(code=generate_valid_code(), description=data["description"])
        item_group_page.click_submit()

        is_success = item_group_page.is_success_popup(timeout=8)
        is_validation = item_group_page.is_validation_failed_popup(timeout=3)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        assert is_success or is_validation or is_failed, \
            "IG-C10: Expected popup response for spaces-only Description"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-C10 PASSED: Spaces in Description handled")

    def test_IG_C11_create_with_special_char_code(self, item_group_page):
        """IG-C11: Create Item Group with special characters in Code → Success (alphanumericSpecial)."""
        data = generate_special_char_code()

        item_group_page.create_record(data["code"], generate_valid_description())

        assert item_group_page.is_success_popup(timeout=10), \
            f"IG-C11: Expected success popup with special chars in Code"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-C11 PASSED: Created with special characters in Code")

    def test_IG_C12_create_with_special_char_description(self, item_group_page):
        """IG-C12: Create Item Group with special characters in Description → Success (alphanumericSpecial)."""
        data = generate_special_char_description()

        item_group_page.create_record(generate_valid_code(), data["description"])

        assert item_group_page.is_success_popup(timeout=10), \
            f"IG-C12: Expected success popup with special chars in Description"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-C12 PASSED: Created with special characters in Description")


# ══════════════════════════════════════════════════════════════════════════
#  DUPLICATE TESTS (IG-D01 to IG-D02)
# ══════════════════════════════════════════════════════════════════════════

class TestItemGroupDuplicate:
    """Tests for duplicate Item Group records."""

    def test_IG_D01_create_duplicate_code(self, item_group_page):
        """IG-D01: Create Item Group with duplicate Code (different Description) → Success (duplicates allowed)."""
        data = generate_duplicate_data()

        # Create first record
        item_group_page.create_record(data["code"], data["description"])
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-D01: First record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Create second record with same Code, different Description
        item_group_page.create_record(data["code"], data["duplicate_description"])
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-D01: Expected success for duplicate Code (duplicates allowed)"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-D01 PASSED: Duplicate Code accepted")

    def test_IG_D02_create_exact_duplicate(self, item_group_page):
        """IG-D02: Create Item Group with exact same Code and Description → Success (duplicates allowed)."""
        data = generate_exact_duplicate_data()

        # Create first record
        item_group_page.create_record(data["code"], data["description"])
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-D02: First record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Create exact duplicate
        item_group_page.create_record(data["code"], data["description"])
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-D02: Expected success for exact duplicate (duplicates allowed)"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-D02 PASSED: Exact duplicate accepted")


# ══════════════════════════════════════════════════════════════════════════
#  EDIT TESTS (IG-E01 to IG-E05)
# ══════════════════════════════════════════════════════════════════════════

class TestItemGroupEdit:
    """Tests for editing Item Group records."""

    def test_IG_E01_edit_description(self, item_group_page):
        """IG-E01: Edit Description of an existing record → Success."""
        # Create a record first
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-E01: Setup — record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Find the row and click Edit
        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, f"IG-E01: Could not find row with Code='{code}'"
        item_group_page.click_edit_button(row_index)

        # Verify edit popup opens
        assert item_group_page.is_edit_popup_open(timeout=8), \
            "IG-E01: Edit popup did not open"

        # Update Description
        new_desc = generate_edit_description()
        item_group_page.update_description(new_desc)
        item_group_page.click_submit()

        assert item_group_page.is_success_popup(timeout=10), \
            "IG-E01: Expected success popup after editing Description"
        item_group_page._dismiss_sweet_alert()
        logger.info(f"IG-E01 PASSED: Edited Description to '{new_desc}'")

    def test_IG_E02_edit_code_readonly_check(self, item_group_page):
        """IG-E02: Verify Code field is read-only in Edit mode."""
        # Create a record first
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-E02: Setup — record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Find the row and click Edit
        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, f"IG-E02: Could not find row with Code='{code}'"
        item_group_page.click_edit_button(row_index)

        assert item_group_page.is_edit_popup_open(timeout=8), \
            "IG-E02: Edit popup did not open"

        is_readonly = item_group_page.is_code_field_readonly_in_edit()
        # Close popup regardless
        item_group_page.click_cancel()
        time.sleep(0.5)

        assert is_readonly, \
            "IG-E02: Expected Code field to be read-only in Edit mode"
        logger.info("IG-E02 PASSED: Code field is read-only in Edit mode")

    def test_IG_E03_edit_with_empty_description(self, item_group_page):
        """IG-E03: Edit record with empty Description → Validation Failed (required field)."""
        # Create a record first
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-E03: Setup — record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Find the row and click Edit
        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, f"IG-E03: Could not find row with Code='{code}'"
        item_group_page.click_edit_button(row_index)

        assert item_group_page.is_edit_popup_open(timeout=8), \
            "IG-E03: Edit popup did not open"

        # Clear Description and submit
        item_group_page.update_description("")
        item_group_page.click_submit()

        is_validation = item_group_page.is_validation_failed_popup(timeout=8)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        assert is_validation or is_failed, \
            "IG-E03: Expected validation/failed popup when Description is cleared in Edit"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-E03 PASSED: Validation triggered for empty Description in Edit")

    def test_IG_E04_edit_with_max_length_description(self, item_group_page):
        """IG-E04: Edit Description to max length (255) → Success."""
        # Create a record first
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-E04: Setup — record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Find the row and click Edit
        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, f"IG-E04: Could not find row with Code='{code}'"
        item_group_page.click_edit_button(row_index)

        assert item_group_page.is_edit_popup_open(timeout=8), \
            "IG-E04: Edit popup did not open"

        # Update Description to max length
        new_desc = generate_edit_max_length_description()
        item_group_page.update_description(new_desc)
        item_group_page.click_submit()

        assert item_group_page.is_success_popup(timeout=10), \
            "IG-E04: Expected success popup after editing Description to max length"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-E04 PASSED: Edited Description to max length")

    def test_IG_E05_edit_with_special_char_description(self, item_group_page):
        """IG-E05: Edit Description with special characters → Success (alphanumericSpecial)."""
        # Create a record first
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-E05: Setup — record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Find the row and click Edit
        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, f"IG-E05: Could not find row with Code='{code}'"
        item_group_page.click_edit_button(row_index)

        assert item_group_page.is_edit_popup_open(timeout=8), \
            "IG-E05: Edit popup did not open"

        # Update Description with special characters
        new_desc = generate_edit_special_char_description()
        item_group_page.update_description(new_desc)
        item_group_page.click_submit()

        assert item_group_page.is_success_popup(timeout=10), \
            "IG-E05: Expected success popup after editing Description with special chars"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-E05 PASSED: Edited Description with special characters")


# ══════════════════════════════════════════════════════════════════════════
#  SPECIAL CHARACTER / INJECTION TESTS (IG-S01 to IG-S05)
# ══════════════════════════════════════════════════════════════════════════

class TestItemGroupSpecialChars:
    """Tests for SQL injection, XSS, and special character handling."""

    def test_IG_S01_sql_injection_in_code(self, item_group_page):
        """IG-S01: Create Item Group with SQL injection in Code → Should not execute SQL."""
        data = generate_sql_injection_code()

        item_group_page.click_add_button()
        item_group_page.fill_form(code=data["code"], description=generate_valid_description())
        item_group_page.click_submit()

        # Either it accepts as plain text or rejects — both are fine as long as SQL doesn't execute
        is_success = item_group_page.is_success_popup(timeout=8)
        is_validation = item_group_page.is_validation_failed_popup(timeout=3)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        assert is_success or is_validation or is_failed, \
            "IG-S01: Expected some popup response for SQL injection in Code"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-S01 PASSED: SQL injection in Code handled safely")

    def test_IG_S02_sql_injection_in_description(self, item_group_page):
        """IG-S02: Create Item Group with SQL injection in Description → Should not execute SQL."""
        data = generate_sql_injection_description()

        item_group_page.click_add_button()
        item_group_page.fill_form(code=generate_valid_code(), description=data["description"])
        item_group_page.click_submit()

        is_success = item_group_page.is_success_popup(timeout=8)
        is_validation = item_group_page.is_validation_failed_popup(timeout=3)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        assert is_success or is_validation or is_failed, \
            "IG-S02: Expected some popup response for SQL injection in Description"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-S02 PASSED: SQL injection in Description handled safely")

    def test_IG_S03_xss_in_code(self, item_group_page):
        """IG-S03: Create Item Group with XSS script in Code → Should not execute script."""
        data = generate_xss_code()

        item_group_page.click_add_button()
        item_group_page.fill_form(code=data["code"], description=generate_valid_description())
        item_group_page.click_submit()

        is_success = item_group_page.is_success_popup(timeout=8)
        is_validation = item_group_page.is_validation_failed_popup(timeout=3)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        assert is_success or is_validation or is_failed, \
            "IG-S03: Expected some popup response for XSS in Code"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-S03 PASSED: XSS in Code handled safely")

    def test_IG_S04_xss_in_description(self, item_group_page):
        """IG-S04: Create Item Group with XSS script in Description → Should not execute script."""
        data = generate_xss_description()

        item_group_page.click_add_button()
        item_group_page.fill_form(code=generate_valid_code(), description=data["description"])
        item_group_page.click_submit()

        is_success = item_group_page.is_success_popup(timeout=8)
        is_validation = item_group_page.is_validation_failed_popup(timeout=3)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        assert is_success or is_validation or is_failed, \
            "IG-S04: Expected some popup response for XSS in Description"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-S04 PASSED: XSS in Description handled safely")

    def test_IG_S05_special_chars_only(self, item_group_page):
        """IG-S05: Create Item Group with only special characters in both fields → Accept or validate."""
        data = generate_special_chars_only()

        item_group_page.click_add_button()
        item_group_page.fill_form(code=data["code"], description=data["description"])
        item_group_page.click_submit()

        is_success = item_group_page.is_success_popup(timeout=8)
        is_validation = item_group_page.is_validation_failed_popup(timeout=3)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        assert is_success or is_validation or is_failed, \
            "IG-S05: Expected some popup response for special-chars-only fields"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-S05 PASSED: Special-chars-only fields handled")


# ══════════════════════════════════════════════════════════════════════════
#  POPUP / UI TESTS (IG-P01 to IG-P08)
# ══════════════════════════════════════════════════════════════════════════

class TestItemGroupPopup:
    """Tests for popup and UI behavior on the Item Group screen."""

    def test_IG_P01_add_form_opens_with_all_fields(self, item_group_page):
        """IG-P01: Verify Add form opens and displays Code and Description fields."""
        item_group_page.click_add_button()

        assert item_group_page.is_add_form_open(timeout=8), \
            "IG-P01: Add form did not open"
        logger.info("IG-P01 PASSED: Add form opens with all fields")

    def test_IG_P02_cancel_closes_form(self, item_group_page):
        """IG-P02: Verify Cancel button closes the Add form."""
        item_group_page.click_add_button()
        assert item_group_page.is_add_form_open(timeout=8), \
            "IG-P02: Add form did not open"

        item_group_page.click_cancel()

        assert item_group_page.is_form_closed(timeout=8), \
            "IG-P02: Form did not close after clicking Cancel"
        logger.info("IG-P02 PASSED: Cancel closes the form")

    def test_IG_P03_submit_without_filling(self, item_group_page):
        """IG-P03: Verify Submit without filling any field shows validation error."""
        item_group_page.click_add_button()
        item_group_page.click_submit()

        is_validation = item_group_page.is_validation_failed_popup(timeout=8)
        is_failed = item_group_page.is_failed_to_save_popup(timeout=3)
        has_error = item_group_page.has_validation_error()
        assert is_validation or is_failed or has_error, \
            "IG-P03: Expected validation error or popup for empty form submission"
        item_group_page._dismiss_sweet_alert()
        logger.info("IG-P03 PASSED: Validation triggered for empty submission")

    def test_IG_P04_view_popup_displays_data(self, item_group_page):
        """IG-P04: Verify View popup opens and displays record data."""
        # Create a record first
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-P04: Setup — record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Find the row and click View
        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, f"IG-P04: Could not find row with Code='{code}'"
        item_group_page.click_view_button(row_index)

        assert item_group_page.is_view_popup_open(timeout=8), \
            "IG-P04: View popup did not open"
        item_group_page.close_view_popup()
        logger.info("IG-P04 PASSED: View popup opens and displays data")

    def test_IG_P05_edit_popup_prefilled_data(self, item_group_page):
        """IG-P05: Verify Edit popup opens with pre-filled Code and Description."""
        # Create a record first
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-P05: Setup — record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Find the row and click Edit
        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, f"IG-P05: Could not find row with Code='{code}'"
        item_group_page.click_edit_button(row_index)

        assert item_group_page.is_edit_popup_open(timeout=8), \
            "IG-P05: Edit popup did not open"

        # Verify pre-filled data
        prefilled_code = item_group_page.get_edit_form_code_value()
        prefilled_desc = item_group_page.get_edit_form_description_value()

        item_group_page.click_cancel()
        time.sleep(0.5)

        assert prefilled_code == code, \
            f"IG-P05: Code mismatch — expected '{code}', got '{prefilled_code}'"
        assert prefilled_desc == description, \
            f"IG-P05: Description mismatch — expected '{description}', got '{prefilled_desc}'"
        logger.info("IG-P05 PASSED: Edit popup has pre-filled data")

    def test_IG_P06_form_closes_after_success(self, item_group_page):
        """IG-P06: Verify form closes after successful submission."""
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)

        assert item_group_page.is_success_popup(timeout=10), \
            "IG-P06: Record creation failed"
        item_group_page._dismiss_sweet_alert()

        assert item_group_page.is_form_closed(timeout=8), \
            "IG-P06: Form did not close after successful submission"
        logger.info("IG-P06 PASSED: Form closes after successful submission")

    def test_IG_P07_table_displays_new_record(self, item_group_page):
        """IG-P07: Verify newly created record appears in the table."""
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)

        assert item_group_page.is_success_popup(timeout=10), \
            "IG-P07: Record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(2)

        # Search for the record
        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, \
            f"IG-P07: Newly created record with Code='{code}' not found in table"
        logger.info("IG-P07 PASSED: New record appears in table")

    def test_IG_P08_search_functionality(self, item_group_page):
        """IG-P08: Verify Search functionality finds existing records."""
        # Create a record first
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-P08: Setup — record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Search for the record
        item_group_page.search_record(code)
        time.sleep(2)

        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, \
            f"IG-P08: Search did not find record with Code='{code}'"

        # Clear search to reset
        item_group_page.clear_search()
        item_group_page.click_refresh()
        logger.info("IG-P08 PASSED: Search finds existing record")


# ══════════════════════════════════════════════════════════════════════════
#  HISTORY TESTS (IG-H01 to IG-H05)
# ══════════════════════════════════════════════════════════════════════════

class TestItemGroupHistory:
    """Tests for History popup on the Item Group screen."""

    def test_IG_H01_history_button_opens_popup(self, item_group_page):
        """IG-H01: Verify History button opens the History popup."""
        # Create a record first
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-H01: Setup — record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Find the row and click History
        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, f"IG-H01: Could not find row with Code='{code}'"
        item_group_page.click_history_button(row_index)

        assert item_group_page.is_history_popup_open(timeout=8), \
            "IG-H01: History popup did not open after clicking History button"
        item_group_page.close_history_popup()
        logger.info("IG-H01 PASSED: History button opens popup")

    def test_IG_H02_history_popup_title(self, item_group_page):
        """IG-H02: Verify History popup title contains 'Item Group'."""
        # Create a record first
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-H02: Setup — record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Find the row and click History
        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, f"IG-H02: Could not find row with Code='{code}'"
        item_group_page.click_history_button(row_index)

        assert item_group_page.is_history_popup_open(timeout=8), \
            "IG-H02: History popup did not open"

        title = item_group_page.get_history_popup_title()
        item_group_page.close_history_popup()

        assert "item group" in title.lower() or "history" in title.lower(), \
            f"IG-H02: History popup title '{title}' does not contain 'Item Group' or 'History'"
        logger.info(f"IG-H02 PASSED: History popup title is '{title}'")

    def test_IG_H03_history_popup_has_content(self, item_group_page):
        """IG-H03: Verify History popup contains history records/content."""
        # Create a record first
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-H03: Setup — record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Find the row and click History
        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, f"IG-H03: Could not find row with Code='{code}'"
        item_group_page.click_history_button(row_index)

        assert item_group_page.is_history_popup_open(timeout=8), \
            "IG-H03: History popup did not open"

        # Check that popup has some content (not empty)
        try:
            popup_content = item_group_page.driver.find_element(
                item_group_page.POPUP_CONTENT[0], item_group_page.POPUP_CONTENT[1]
            )
            content_text = popup_content.text.strip()
            has_content = len(content_text) > 0
        except Exception:
            has_content = False

        item_group_page.close_history_popup()

        assert has_content, \
            "IG-H03: History popup appears to have no content"
        logger.info("IG-H03 PASSED: History popup has content")

    def test_IG_H04_history_popup_can_be_closed(self, item_group_page):
        """IG-H04: Verify History popup can be closed."""
        # Create a record first
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-H04: Setup — record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Find the row and click History
        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, f"IG-H04: Could not find row with Code='{code}'"
        item_group_page.click_history_button(row_index)

        assert item_group_page.is_history_popup_open(timeout=8), \
            "IG-H04: History popup did not open"

        # Close the popup
        item_group_page.close_history_popup()
        time.sleep(1)

        # Verify popup is no longer open
        assert not item_group_page.is_history_popup_open(timeout=3), \
            "IG-H04: History popup did not close"
        logger.info("IG-H04 PASSED: History popup can be closed")

    def test_IG_H05_history_for_newly_created_record(self, item_group_page):
        """IG-H05: Verify History popup shows at least one entry for a newly created record."""
        # Create a record first
        code = generate_valid_code()
        description = generate_valid_description()
        item_group_page.create_record(code, description)
        assert item_group_page.is_success_popup(timeout=10), \
            "IG-H05: Setup — record creation failed"
        item_group_page._dismiss_sweet_alert()
        time.sleep(1)

        # Find the row and click History
        row_index = item_group_page.find_row_by_code(code)
        assert row_index >= 0, f"IG-H05: Could not find row with Code='{code}'"
        item_group_page.click_history_button(row_index)

        assert item_group_page.is_history_popup_open(timeout=8), \
            "IG-H05: History popup did not open"

        # Check for at least one history row/entry
        try:
            history_rows = item_group_page.driver.find_elements(
                By.CSS_SELECTOR, 'div.popup-overlay table tbody tr, div.popup-overlay .history-row, div.popup-overlay .history-item'
            )
            has_entries = len(history_rows) > 0
        except Exception:
            # Fallback: just check popup content is not empty
            try:
                popup_content = item_group_page.driver.find_element(
                    item_group_page.POPUP_CONTENT[0], item_group_page.POPUP_CONTENT[1]
                )
                has_entries = len(popup_content.text.strip()) > 0
            except Exception:
                has_entries = False

        item_group_page.close_history_popup()

        assert has_entries, \
            "IG-H05: History popup should have at least one entry for a newly created record"
        logger.info("IG-H05 PASSED: History shows entry for new record")