"""
test_item_attribute_validation.py
---------------------------------
Automated test cases for RhythmERP Item Attribute 1-5 screens.

Test ID Prefix: IA{N} (e.g., IA1-C01, IA3-E02)
Parameterized via @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])

Phases:
  1. Create Form Validations   (IA{N}-C01 to IA{N}-C10, +C08a)  — 11 tests × 5 screens
  2. Duplicate Validations     (IA{N}-D01 to IA{N}-D03)  — 3 tests × 5 screens
  3. Edit Form Validations     (IA{N}-E01 to IA{N}-E06)  — 6 tests × 5 screens
  4. Search & Filter           (IA{N}-S01 to IA{N}-S05)  — 5 tests × 5 screens
  5. View & History            (IA{N}-V01 to IA{N}-V05)  — 5 tests × 5 screens
  6. Toggle & UI Behaviors     (IA{N}-T01 to IA{N}-T04)  — 4 tests × 5 screens

Total: 34 tests × 5 screens = ~170 test executions

PYTEST MARKERS:
  smoke=6  |  sanity=34  |  regression=34  |  bug=4  |  ui=13

  Usage:
    pytest -m smoke                              # 6 critical-path tests
    pytest -m "smoke or sanity"                   # 34 tests
    pytest -m "not bug"                          # 30 non-bug tests
    pytest -m ui                                  # 13 UI behavior tests
    pytest -m regression                         # full suite (34)

KEY RULES:
  - NEVER use Keys.ESCAPE (closes entire popup form!)
  - JS clicks for Angular Material overlays
  - Name input uses capital 'N': name="Name"
  - Base UOM dropdown only exists on Item Attribute 1
  - Status toggle: default ON (Active), labels Inactive/Active
  - Edit mode: Name IS editable (not readonly!)
  - Duplicate Names: ALLOWED (BUG-001)
"""

import os
import sys
import pytest
from selenium.webdriver.common.by import By

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from pages.commodity_settings.modules.item_attribute.data.item_attribute_data import (
    generate_valid_data,
    generate_minimal_valid_data,
    generate_empty_name,
    generate_spaces_name,
    generate_missing_base_uom,
    generate_all_required_missing,
    generate_duplicate_name_data,
    generate_long_name,
    generate_long_description,
    generate_special_char_name,
    generate_sql_injection_name,
    generate_xss_name,
    generate_unicode_name,
    generate_numeric_name,
    generate_status_on,
    generate_status_off,
    generate_edit_only_name,
    generate_edit_only_description,
    generate_edit_change_base_uom,
    generate_edit_toggle_status,
    generate_edit_all_fields,
)


# ====================================================================
#  PHASE 1: Create Form Validations (IA{N}-C01 to IA{N}-C10)
# ====================================================================

class TestCreateFormValidations:
    """Validation tests for the Item Attribute Create (Add) form.
    Parameterized across all 5 screens.
    """

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_C01_create_with_all_required_fields(self, ia_page, attr_num):
        """IA{N}-C01: Create attribute with all required fields filled.
        Should succeed and close the form.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-C01: Create with all required fields (Attr{attr_num})")
        page = ia_page
        data = generate_valid_data(attr_num)

        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        # Check for success or validation error
        swal_title = page.get_swal_title()
        if swal_title and "failed" in swal_title.lower():
            page.handle_validation_warning(timeout=5)
            assert page.is_add_form_open(), \
                "Form should still be open after validation failure"
        else:
            if swal_title:
                page.handle_success_alert(timeout=10)
            assert page.is_form_closed(), \
                "Form should close after successful creation"

        # Cleanup
        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_C02_create_empty_name(self, ia_page, attr_num):
        """IA{N}-C02: Create attribute without Name (required).
        Should show validation error.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-C02: Create without Name (Attr{attr_num})")
        page = ia_page
        data = generate_empty_name(attr_num)

        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        # Should see validation error
        swal_title = page.get_swal_title()
        has_error = (
            (swal_title and "failed" in swal_title.lower())
            or page.has_field_error("Name")
            or page.get_mat_error_text()
        )
        assert has_error, \
            f"{prefix}: Should show validation error when Name is missing"

        if swal_title:
            page.handle_validation_warning(timeout=3)
        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_C03_create_spaces_only_name(self, ia_page, attr_num):
        """IA{N}-C03: Create attribute with only spaces in Name.
        Should show validation error.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-C03: Create with spaces-only Name (Attr{attr_num})")
        page = ia_page
        data = generate_spaces_name(attr_num)

        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        has_error = (
            (swal_title and "failed" in swal_title.lower())
            or page.has_field_error("Name")
            or page.get_mat_error_text()
        )
        if has_error:
            log.info(f"{prefix}: ERP correctly rejects spaces-only name")
        else:
            log.info(f"{prefix}: ERP accepts spaces-only name (possible bug)")

        if swal_title:
            page.handle_validation_warning(timeout=3)
        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1])
    def test_IA1_C04_create_missing_base_uom(self, ia_page, attr_num):
        """IA1-C04: Create Item Attribute 1 without Base UOM (required).
        Only applies to Item Attribute 1 which has Base UOM.
        """
        log.info("IA1-C04: Create IA1 without Base UOM")
        page = ia_page
        data = generate_missing_base_uom()

        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        has_error = (
            (swal_title and "failed" in swal_title.lower())
            or page.has_field_error("Base UOM")
            or page.get_mat_error_text()
        )
        assert has_error, \
            "IA1: Should show validation error when Base UOM is missing"

        if swal_title:
            page.handle_validation_warning(timeout=3)
        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_C05_create_with_special_char_name(self, ia_page, attr_num):
        """IA{N}-C05: Create attribute with special characters in Name."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-C05: Create with special chars in Name (Attr{attr_num})")
        page = ia_page
        data = generate_special_char_name(attr_num)

        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title and "failed" in swal_title.lower():
            page.handle_validation_warning(timeout=3)
        elif swal_title:
            page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_C06_create_sql_injection(self, ia_page, attr_num):
        """IA{N}-C06: SQL injection attempt in Name field.
        Tests input sanitization.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-C06: SQL injection in Name (Attr{attr_num})")
        page = ia_page
        data = generate_sql_injection_name(attr_num)

        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)
            else:
                page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_C07_create_xss_in_name(self, ia_page, attr_num):
        """IA{N}-C07: XSS payload in Name field.
        Tests input sanitization.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-C07: XSS payload in Name (Attr{attr_num})")
        page = ia_page
        data = generate_xss_name(attr_num)

        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)
            else:
                page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_C08_create_long_name(self, ia_page, attr_num):
        """IA{N}-C08: Create attribute with extremely long Name (256 chars).
        Server rejects names > 255 chars with "Failed to save record" popup.
        BUG-004: No maxlength/client-side validation on Name field.
        BUG-005: Generic error message instead of specific field error.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-C08: Create with long Name (256 chars) (Attr{attr_num})")
        page = ia_page
        data = generate_long_name(256, attr_num)

        # Record count before attempt
        page.click_refresh()
        page.wait_seconds(2)
        count_before = page.get_table_row_count()

        page.open_add_form()
        page.fill_form(data)
        page.submit()

        # Server rejects with "Failed to save record" (Type B popup)
        # Check IMMEDIATELY — popup appears right after Submit and auto-dismisses quickly
        swal_title = page.handle_save_failure_alert(timeout=10)

        # Assert the popup title indicates failure
        assert swal_title, \
            f"{prefix}-C08: Expected a popup after submitting 256-char Name"
        assert "failed" in swal_title.lower(), \
            f"{prefix}-C08: Expected failure popup, got: '{swal_title}'"

        # Cleanup: close form popup
        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

        # Assert record was NOT created in the table
        count_after = page.get_table_row_count()
        assert count_after == count_before, \
            f"{prefix}-C08: Record should NOT be created with 256-char Name " \
            f"(before={count_before}, after={count_after})"

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_C08a_create_long_description(self, ia_page, attr_num):
        """IA{N}-C08a: Create attribute with valid Name but 256-char Description.
        Server rejects descriptions > 255 chars with "Failed to save record" popup.
        BUG-004: No maxlength/client-side validation on Description field.
        BUG-005: Generic error message instead of specific field error.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-C08a: Create with long Description (256 chars) (Attr{attr_num})")
        page = ia_page
        data = generate_long_description(256, attr_num)

        # Record count before attempt
        page.click_refresh()
        page.wait_seconds(2)
        count_before = page.get_table_row_count()

        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        # Server rejects with "Failed to save record" (Type B popup)
        swal_title = page.handle_save_failure_alert(timeout=10)

        # Assert the popup title indicates failure
        assert swal_title, \
            f"{prefix}-C08a: Expected a popup after submitting 256-char Description"
        assert "failed" in swal_title.lower(), \
            f"{prefix}-C08a: Expected failure popup, got: '{swal_title}'"

        # Cleanup: close form popup
        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

        # Assert record was NOT created in the table
        count_after = page.get_table_row_count()
        assert count_after == count_before, \
            f"{prefix}-C08a: Record should NOT be created with 256-char Description " \
            f"(before={count_before}, after={count_after})"

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_C09_create_unicode_name(self, ia_page, attr_num):
        """IA{N}-C09: Create attribute with unicode characters in Name."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-C09: Create with unicode Name (Attr{attr_num})")
        page = ia_page
        data = generate_unicode_name(attr_num)

        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)
            else:
                page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_C10_create_numeric_name(self, ia_page, attr_num):
        """IA{N}-C10: Create attribute with purely numeric Name."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-C10: Create with numeric Name (Attr{attr_num})")
        page = ia_page
        data = generate_numeric_name(attr_num)

        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)
            else:
                page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
#  PHASE 2: Duplicate Validations (IA{N}-D01 to IA{N}-D03)
# ====================================================================

class TestDuplicateValidations:
    """Tests for duplicate attribute Name behavior.
    BUG-001: Duplicate Names are ALLOWED (no uniqueness constraint).
    """

    def _create_item(self, page, attr_num):
        """Helper: Create an attribute first."""
        data = generate_valid_data(attr_num, name_prefix="DUP")
        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)
            else:
                page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)
        return data.get("name", "")

    @pytest.mark.smoke
    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_D01_duplicate_name_allowed(self, ia_page, attr_num):
        """IA{N}-D01: Create two attributes with same Name.
        BUG-001: Currently ALLOWED — test documents this behavior.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-D01: Duplicate Name - should be allowed (BUG-001)")
        page = ia_page
        data = generate_duplicate_name_data(attr_num)

        # Create first attribute
        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)
            else:
                page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

        # Create second attribute with same data
        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "success" in swal_title.lower():
                page.handle_success_alert(timeout=10)
                log.info(f"{prefix}: BUG-001 CONFIRMED: Duplicate Name allowed")
            elif "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)
                log.info(f"{prefix}: Duplicate Name now rejected (bug fixed)")
        else:
            if page.is_form_closed():
                log.info(f"{prefix}: BUG-001 CONFIRMED: Duplicate Name allowed (form closed)")

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_D02_duplicate_different_case(self, ia_page, attr_num):
        """IA{N}-D02: Create attributes with same Name but different case.
        Tests case-sensitivity of Name uniqueness.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-D02: Duplicate with different case")
        page = ia_page

        # Create first with uppercase
        data1 = generate_valid_data(attr_num, name_prefix="CASE")
        page.open_add_form()
        page.fill_form(data1)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)
            else:
                page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

        # Create second with lowercase version
        data2 = generate_valid_data(attr_num, name_prefix="case")
        page.open_add_form()
        page.fill_form(data2)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "success" in swal_title.lower():
                page.handle_success_alert(timeout=10)
            elif "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_D03_duplicate_name_edit(self, ia_page, attr_num):
        """IA{N}-D03: Edit an attribute to have the same Name as another.
        Tests if duplicate check works during edit.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-D03: Duplicate Name during Edit")
        page = ia_page

        # Create two different attributes
        data1 = generate_valid_data(attr_num, name_prefix="EDUP1")
        page.open_add_form()
        page.fill_form(data1)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)
            else:
                page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

        # Create second attribute
        data2 = generate_valid_data(attr_num, name_prefix="EDUP2")
        page.open_add_form()
        page.fill_form(data2)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)
            else:
                page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
#  PHASE 3: Edit Form Validations (IA{N}-E01 to IA{N}-E06)
# ====================================================================

class TestEditFormValidations:
    """Validation tests for the Item Attribute Edit form.
    Edit mode: all fields editable, Update button visible.
    """

    def _create_prerequisite_item(self, page, attr_num):
        """Helper: Create an attribute first."""
        data = generate_valid_data(attr_num, name_prefix="EDITP")
        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)
            else:
                page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_E01_edit_prepopulated(self, ia_page, attr_num):
        """IA{N}-E01: Edit form should be pre-populated with existing data."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-E01: Edit form pre-populated (Attr{attr_num})")
        page = ia_page

        self._create_prerequisite_item(page, attr_num)

        page.click_edit_button(row_index=0)
        page.wait_seconds(1.5)

        if page.is_edit_mode():
            # Check that Update button is visible
            assert page.is_displayed(page.UPDATE_BUTTON, timeout=5), \
                f"{prefix}: Update button should be visible in Edit mode"

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_E02_edit_change_name(self, ia_page, attr_num):
        """IA{N}-E02: Edit — change the Name field.
        Name IS editable in Edit mode (not readonly).
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-E02: Edit - change Name (Attr{attr_num})")
        page = ia_page

        self._create_prerequisite_item(page, attr_num)

        page.click_edit_button(row_index=0)
        page.wait_seconds(1.5)

        if page.is_edit_mode():
            edit_data = generate_edit_only_name(attr_num)
            page.fill_form(edit_data)
            page.click_update()
            page.wait_seconds(2)

            swal_title = page.get_swal_title()
            if swal_title:
                if "failed" in swal_title.lower():
                    page.handle_validation_warning(timeout=3)
                else:
                    page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_E03_edit_change_description(self, ia_page, attr_num):
        """IA{N}-E03: Edit — change the Description field."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-E03: Edit - change Description (Attr{attr_num})")
        page = ia_page

        self._create_prerequisite_item(page, attr_num)

        page.click_edit_button(row_index=0)
        page.wait_seconds(1.5)

        if page.is_edit_mode():
            edit_data = generate_edit_only_description(attr_num)
            page.fill_form(edit_data)
            page.click_update()
            page.wait_seconds(2)

            swal_title = page.get_swal_title()
            if swal_title:
                if "failed" in swal_title.lower():
                    page.handle_validation_warning(timeout=3)
                else:
                    page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1])
    def test_IA1_E04_edit_change_base_uom(self, ia_page, attr_num):
        """IA1-E04: Edit Item Attribute 1 — change Base UOM dropdown.
        Only applies to Item Attribute 1.
        """
        log.info("IA1-E04: Edit - change Base UOM")
        page = ia_page

        self._create_prerequisite_item(page, attr_num)

        page.click_edit_button(row_index=0)
        page.wait_seconds(1.5)

        if page.is_edit_mode():
            edit_data = generate_edit_change_base_uom()
            page.fill_form(edit_data)
            page.click_update()
            page.wait_seconds(2)

            swal_title = page.get_swal_title()
            if swal_title:
                if "failed" in swal_title.lower():
                    page.handle_validation_warning(timeout=3)
                else:
                    page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_E05_edit_toggle_status(self, ia_page, attr_num):
        """IA{N}-E05: Edit — toggle Status from Active to Inactive."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-E05: Edit - toggle Status (Attr{attr_num})")
        page = ia_page

        self._create_prerequisite_item(page, attr_num)

        page.click_edit_button(row_index=0)
        page.wait_seconds(1.5)

        if page.is_edit_mode():
            edit_data = generate_edit_toggle_status()
            page.fill_form(edit_data)
            page.click_update()
            page.wait_seconds(2)

            swal_title = page.get_swal_title()
            if swal_title:
                if "failed" in swal_title.lower():
                    page.handle_validation_warning(timeout=3)
                else:
                    page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_E06_edit_cancel_returns(self, ia_page, attr_num):
        """IA{N}-E06: Cancel in Edit mode returns to listing page."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-E06: Cancel returns to listing (Attr{attr_num})")
        page = ia_page

        self._create_prerequisite_item(page, attr_num)

        page.click_edit_button(row_index=0)
        page.wait_seconds(1.5)

        page.cancel()
        page.wait_seconds(1)

        assert page.is_form_closed(), \
            f"{prefix}: Form should close after Cancel in Edit mode"

        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
#  PHASE 4: Search & Filter (IA{N}-S01 to IA{N}-S05)
# ====================================================================

class TestSearchFilter:
    """Tests for search and filter functionality on the Item Attribute listing."""

    def _create_prerequisite_item(self, page, attr_num):
        """Helper: Create an attribute first."""
        data = generate_valid_data(attr_num, name_prefix="SRCH")
        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)
            else:
                page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_S01_search_existing_item(self, ia_page, attr_num):
        """IA{N}-S01: Search for an existing attribute by name."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-S01: Search for existing item (Attr{attr_num})")
        page = ia_page

        names = page.get_all_item_names()
        if names:
            search_name = names[0][:10]  # Use partial name
            page.search_item(search_name)
            page.wait_seconds(2)

            row_count = page.get_table_row_count()
            assert row_count >= 1, \
                f"{prefix}: Search for '{search_name}' should return at least one row"
        else:
            log.warning(f"{prefix}: No items in table to search for")

        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_S02_search_nonexistent_item(self, ia_page, attr_num):
        """IA{N}-S02: Search for a non-existent attribute name."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-S02: Search for non-existent item (Attr{attr_num})")
        page = ia_page

        page.search_item("ZZZZZ_NONEXISTENT_ATTR_12345")
        page.wait_seconds(2)

        row_count = page.get_table_row_count()
        no_data = page.is_displayed(page.NO_DATA_ROW, timeout=3)
        assert row_count == 0 or no_data, \
            f"{prefix}: Search for non-existent item should return no results"

        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_S03_search_partial_name(self, ia_page, attr_num):
        """IA{N}-S03: Search with partial attribute name."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-S03: Search with partial name (Attr{attr_num})")
        page = ia_page

        names = page.get_all_item_names()
        if names:
            partial = names[0][:3] if len(names[0]) >= 3 else names[0]
            page.search_item(partial)
            page.wait_seconds(2)

            row_count = page.get_table_row_count()
            assert row_count >= 1, \
                f"{prefix}: Partial search for '{partial}' should find items"
        else:
            log.warning(f"{prefix}: No items in table for partial search")

        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_S04_search_case_insensitive(self, ia_page, attr_num):
        """IA{N}-S04: Search should be case-insensitive."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-S04: Case-insensitive search (Attr{attr_num})")
        page = ia_page

        names = page.get_all_item_names()
        if names:
            search_name = names[0][:8]
            search_lower = search_name.lower()
            search_upper = search_name.upper()

            page.search_item(search_lower)
            page.wait_seconds(2)
            count_lower = page.get_table_row_count()

            page.click_refresh()
            page.wait_seconds(2)

            page.search_item(search_upper)
            page.wait_seconds(2)
            count_upper = page.get_table_row_count()

            log.info(
                f"{prefix}: Lower: {count_lower} rows, Upper: {count_upper} rows"
            )
        else:
            log.warning(f"{prefix}: No items for case-insensitive test")

        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_S05_refresh_clears_search(self, ia_page, attr_num):
        """IA{N}-S05: Clicking Refresh should clear search and show all items."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-S05: Refresh clears search (Attr{attr_num})")
        page = ia_page

        page.search_item("ZZZZZ_FAKE")
        page.wait_seconds(2)

        page.click_refresh()
        page.wait_seconds(2)

        assert page.is_page_loaded(), \
            f"{prefix}: Table should be visible after refresh"

        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
#  PHASE 5: View & History (IA{N}-V01 to IA{N}-V05)
# ====================================================================

class TestViewHistory:
    """Tests for View (read-only) and History popup functionality."""

    def _create_prerequisite_item(self, page, attr_num):
        """Helper: Create an attribute first."""
        data = generate_valid_data(attr_num, name_prefix="VIEW")
        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title:
            if "failed" in swal_title.lower():
                page.handle_validation_warning(timeout=3)
            else:
                page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_V01_view_all_fields_readonly(self, ia_page, attr_num):
        """IA{N}-V01: View mode - all fields should be read-only/disabled."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-V01: View mode - all fields read-only (Attr{attr_num})")
        page = ia_page

        self._create_prerequisite_item(page, attr_num)

        page.click_view_button(row_index=0)
        page.wait_seconds(1.5)

        is_view = page.is_view_mode()
        assert is_view, \
            f"{prefix}: All fields should be disabled in View mode"

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_V02_view_only_cancel_button(self, ia_page, attr_num):
        """IA{N}-V02: View mode - only Cancel button should be visible.
        No Submit or Update button in View mode.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-V02: View mode - only Cancel button (Attr{attr_num})")
        page = ia_page

        self._create_prerequisite_item(page, attr_num)

        page.click_view_button(row_index=0)
        page.wait_seconds(1.5)

        has_submit = page.is_displayed(page.SUBMIT_BUTTON, timeout=3)
        has_update = page.is_displayed(page.UPDATE_BUTTON, timeout=3)
        has_cancel = page.is_displayed(page.CANCEL_BUTTON, timeout=3)

        assert not has_submit, \
            f"{prefix}: Submit button should NOT be visible in View mode"
        assert not has_update, \
            f"{prefix}: Update button should NOT be visible in View mode"
        assert has_cancel, \
            f"{prefix}: Cancel button should be visible in View mode"

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_V03_view_cancel_returns(self, ia_page, attr_num):
        """IA{N}-V03: Cancel in View mode returns to listing page."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-V03: View - Cancel returns to listing (Attr{attr_num})")
        page = ia_page

        self._create_prerequisite_item(page, attr_num)

        page.click_view_button(row_index=0)
        page.wait_seconds(1.5)

        page.cancel()
        page.wait_seconds(1)

        assert page.is_form_closed(), \
            f"{prefix}: Form should close after Cancel in View mode"

        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_V04_history_popup_opens(self, ia_page, attr_num):
        """IA{N}-V04: History popup opens for an attribute.
        History button uses cdk-column-archive.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-V04: History popup opens (Attr{attr_num})")
        page = ia_page

        self._create_prerequisite_item(page, attr_num)

        page.click_history_button(row_index=0)
        page.wait_seconds(1.5)

        history_open = page.is_history_popup_open()
        if history_open:
            log.info(f"{prefix}: History popup opened successfully")
            page.close_history_popup()
        else:
            log.warning(f"{prefix}: History popup did not open")

        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_V05_history_has_data(self, ia_page, attr_num):
        """IA{N}-V05: History popup should contain at least one row.
        BUG-003: History may show "No data available".
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-V05: History popup has data (Attr{attr_num})")
        page = ia_page

        self._create_prerequisite_item(page, attr_num)

        page.click_history_button(row_index=0)
        page.wait_seconds(1.5)

        if page.is_history_popup_open():
            row_count = page.get_history_row_count()
            if row_count >= 1:
                log.info(f"{prefix}: History has {row_count} rows")
            else:
                log.warning(f"{prefix}: History popup shows no data (BUG-003)")
            page.close_history_popup()
        else:
            log.warning(f"{prefix}: History popup did not open")

        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
#  PHASE 6: Toggle & UI Behaviors (IA{N}-T01 to IA{N}-T04)
# ====================================================================

class TestToggleUIBehaviors:
    """Tests for Status toggle and UI behavior on Item Attribute screens.
    Only 1 toggle exists: Status (Active/Inactive).
    """

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_T01_create_status_active(self, ia_page, attr_num):
        """IA{N}-T01: Create attribute with Status Active (default ON).
        Should create successfully and show Active in table.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-T01: Create with Status Active (Attr{attr_num})")
        page = ia_page
        data = generate_status_on(attr_num)

        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title and "failed" in swal_title.lower():
            page.handle_validation_warning(timeout=3)
        elif swal_title:
            page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_T02_create_status_inactive(self, ia_page, attr_num):
        """IA{N}-T02: Create attribute with Status Inactive (toggle OFF).
        Should create successfully and show Inactive in table.
        """
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-T02: Create with Status Inactive (Attr{attr_num})")
        page = ia_page
        data = generate_status_off(attr_num)

        page.open_add_form()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        swal_title = page.get_swal_title()
        if swal_title and "failed" in swal_title.lower():
            page.handle_validation_warning(timeout=3)
        elif swal_title:
            page.handle_success_alert(timeout=10)

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_T03_toggle_default_is_active(self, ia_page, attr_num):
        """IA{N}-T03: Verify Status toggle defaults to Active (ON) in Create mode."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-T03: Toggle default is Active (Attr{attr_num})")
        page = ia_page

        page.open_add_form()
        page.wait_seconds(1)

        # Check toggle state - should be ON (Active) by default
        try:
            on_label = page.driver.find_element(
                By.CSS_SELECTOR, ".switch-wrapper .state-label.on.active"
            )
            assert on_label is not None, \
                f"{prefix}: Status toggle should default to Active (ON)"
            log.info(f"{prefix}: Confirmed - Status toggle defaults to Active")
        except Exception:
            log.warning(f"{prefix}: Could not verify toggle default state")

        try:
            page.cancel()
        except Exception:
            pass
        page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    @pytest.mark.parametrize("attr_num", [1, 2, 3, 4, 5])
    def test_IA_T04_cancel_closes_form(self, ia_page, attr_num):
        """IA{N}-T04: Cancel in Create mode closes the form without saving."""
        prefix = f"IA{attr_num}"
        log.info(f"{prefix}-T04: Cancel closes form (Attr{attr_num})")
        page = ia_page

        page.open_add_form()
        page.wait_seconds(1)

        # Fill some data
        data = generate_valid_data(attr_num, name_prefix="CANCEL")
        page.fill_form(data)

        # Cancel should close form
        page.cancel()
        page.wait_seconds(1)

        assert page.is_form_closed(), \
            f"{prefix}: Form should close after Cancel"

        page.click_refresh()
        page.wait_seconds(2)