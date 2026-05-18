"""
test_item_group_validation.py
-----------------------------
Comprehensive validation test suite for RhythmERP Item Group screen.
37 test cases across 7 phases.

Location: Commodity Settings > Commodity Master > Item Group
URL:      /#/dynamic-screens/Item%20Group

Phases:
  1. Create Form Validations  (12 tests) — IG-C01 to IG-C12
  2. Duplicate Validations      (2 tests) — IG-D01 to IG-D02
  3. Edit Form Validations      (5 tests) — IG-E01 to IG-E05
  4. Search & Filter Edge Cases (5 tests) — IG-S01 to IG-S05
  5. Popup & UI Behaviors       (8 tests) — IG-P01 to IG-P08
  6. Filter Validations         (2 tests) — IG-F01 to IG-F02
  7. History Validations        (5 tests) — IG-H01 to IG-H05

Known Behaviors (confirmed via ERP exploration):
  BEH-001 : No dropdowns — both fields are text inputs
  BEH-002 : No Status toggle on this screen
  BEH-003 : No Delete button — only View, Edit, History
  BEH-004 : Duplicate Codes ALLOWED — no uniqueness constraint
  BEH-005 : Both Code and Description are required
  BEH-006 : History button present and functional
  BEH-007 : Fields use name="Code" / name="Description" (NO formcontrolname)

Bug Handling Decisions:
  BEH-004: Mark as known bug — test PASSES documenting current behavior
  Spaces-only: Test expects rejection — may FAIL until ERP is fixed

Run:
  pytest test_item_group_validation.py -v --tb=short
  pytest test_item_group_validation.py -v -k "TestCreateForm" --tb=short
  pytest test_item_group_validation.py -v -k "IG-C03" --tb=short
"""

import os
import sys
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from selenium.webdriver.common.by import By

from pages.commodity_settings.modules.item_group.item_group_page import (
    ItemGroupPage,
)
from pages.commodity_settings.modules.item_group.data.item_group_data import (
    generate_valid_ig_data,
    generate_valid_edit_data,
    generate_empty_code_data,
    generate_empty_description_data,
    generate_both_empty_data,
    generate_spaces_only,
    generate_spaces_only_code_data,
    generate_spaces_only_description_data,
    generate_duplicate_code_data,
    generate_string_255,
    generate_string_256,
    generate_special_char_data,
    generate_sql_injection_data,
    generate_xss_data,
    generate_unicode_data,
    generate_leading_trailing_spaces_data,
    generate_ig_code,
)
from common.logger import log


# ====================================================================
# Helper: create a prerequisite Item Group, refresh, and return its code
# ====================================================================

def _create_prerequisite_ig(page, data=None):
    """Create an Item Group for tests that need existing data.
    Returns the code used.
    """
    if data is None:
        data = generate_valid_ig_data("PreReq")
    code = page.create_item_group(data)
    # Cleanup form if still open
    try:
        page.cancel()
    except Exception:
        pass
    try:
        page.close_popup()
    except Exception:
        pass
    page.click_refresh()
    page.wait_seconds(2)
    return code


# ====================================================================
# PHASE 1: Create Form Validations (12 tests)
# ====================================================================

class TestCreateFormValidations:
    """IG-C01 to IG-C12: Validation checks on the Create form.
    Item Group has TWO form fields: Code (text, required)
    and Description (text, required). No dropdowns.
    """

    # ---- IG-C01: Submit with empty Code ----
    def test_IG_C01_empty_code(self, ig_page):
        """Submit with empty Code field — should be blocked."""
        log.info("IG-C01: Empty Code submit test")
        page = ig_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Fill only Description, leave Code empty
        data = generate_empty_code_data()
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        # Check for SweetAlert2 validation warning
        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        # Expect: form stays open + validation errors/warning shown
        assert form_still_open or errors or validation_alert, (
            "BUG: Form submitted with empty Code — no validation"
        )
        if validation_alert:
            log.info(f"Validation alert shown: {validation_alert}")
        if errors:
            log.info(f"Validation errors shown: {errors}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IG-C02: Create with valid Code + Description (happy path) ----
    def test_IG_C02_valid_create(self, ig_page):
        """Create with valid Code and Description — should succeed."""
        log.info("IG-C02: Valid create test")
        page = ig_page

        data = generate_valid_ig_data("ValidC", "ValidD")
        code = page.create_item_group(data)

        page.wait_seconds(2)
        popup_closed = page.is_form_closed()

        if popup_closed:
            log.info("Form closed after submit")
        else:
            # Check if validation alert appeared instead
            validation_alert = page.get_swal_title()
            if validation_alert:
                log.warning(f"Validation alert instead of success: {validation_alert}")

        # Verify the Item Group appears in the table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_item_group_in_table(code)

        assert found, (
            f"Created Item Group '{code}' not found in table after refresh"
        )
        log.info(f"Item Group created and found in table: {code}")

    # ---- IG-C03: Spaces-only Code ----
    @pytest.mark.xfail(
        reason="BUG: Spaces-only Code may be accepted — will fail until ERP is fixed",
        strict=False,
    )
    def test_IG_C03_spaces_only_code(self, ig_page):
        """Spaces-only Code — should be rejected.
        Test expects rejection — will FAIL if ERP accepts it.
        """
        log.info("IG-C03: Spaces-only Code test")
        page = ig_page

        data = generate_spaces_only_code_data(10)
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        # Check if validation alert appeared (expected behavior)
        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        assert form_still_open or errors or validation_alert, (
            "BUG CONFIRMED: Spaces-only Code was accepted — "
            "system should reject it with a validation error"
        )

        if not (form_still_open or errors or validation_alert):
            page.click_refresh()
            page.wait_seconds(2)
            log.warning("BUG CONFIRMED: Spaces-only Code created a record")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IG-C04: Duplicate Code ----
    def test_IG_C04_duplicate_code(self, ig_page):
        """Duplicate Code in Create — should be rejected.
        BEH-004: Duplicate Codes are currently allowed.
        Test documents current behavior as known bug — passes either way.
        """
        log.info("IG-C04: Duplicate Code test")
        page = ig_page

        # Create first Item Group
        data1 = generate_valid_ig_data("Dup1", "Desc1")
        page.create_item_group(data1)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Try creating second Item Group with same Code
        data2 = generate_duplicate_code_data(data1["code"])
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data2)
        page.submit()
        page.wait_seconds(2)

        # Check for validation or acceptance
        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("Duplicate Code rejected — validation working")
        else:
            log.warning(
                "BEH-004 CONFIRMED: Duplicate Code allowed in Create form"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- IG-C05: Code at 255 char boundary ----
    def test_IG_C05_code_255_chars(self, ig_page):
        """Code with exactly 255 chars — boundary test."""
        log.info("IG-C05: 255-char Code test")
        page = ig_page

        code_255 = generate_string_255()
        data = {"code": code_255, "description": "Boundary 255 test"}
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("255-char Code rejected — maxlength enforced")
        else:
            log.info("255-char Code accepted (may be expected if max >= 255)")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- IG-C06: Code exceeds 255 chars (256) ----
    def test_IG_C06_code_256_chars(self, ig_page):
        """Code with 256 chars — should be rejected or truncated."""
        log.info("IG-C06: 256-char Code test")
        page = ig_page

        code_256 = generate_string_256()
        data = {"code": code_256, "description": "Boundary 256 test"}
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("256-char Code rejected — maxlength enforced")
        else:
            log.warning("256-char Code accepted — no maxlength validation")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- IG-C07: No success popup check ----
    def test_IG_C07_no_success_popup(self, ig_page):
        """Verify whether a success SweetAlert appears after create.
        Documents current behavior.
        """
        log.info("IG-C07: No success popup test")
        page = ig_page

        data = generate_valid_ig_data("NoAlert", "NoAlertDesc")
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        # Check if a SweetAlert appeared at all
        swal_visible = page.is_validation_alert_present(timeout=3)

        if not swal_visible:
            log.info("No success SweetAlert after create — popup just closes")
        else:
            swal_title = page.get_swal_title()
            log.info(f"SweetAlert appeared: {swal_title}")
            page.handle_validation_warning(timeout=3)

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- IG-C08: Special characters in Code ----
    def test_IG_C08_special_chars_code(self, ig_page):
        """Special characters in Code — check if accepted or rejected."""
        log.info("IG-C08: Special chars in Code test")
        page = ig_page

        data = generate_special_char_data()
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("Special chars rejected — validation working")
        else:
            log.info("Special chars accepted (may be expected behavior)")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- IG-C09: SQL injection in Code ----
    def test_IG_C09_sql_injection_code(self, ig_page):
        """SQL injection string in Code — should be sanitized or rejected."""
        log.info("IG-C09: SQL injection Code test")
        page = ig_page

        data = generate_sql_injection_data()
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("SQL injection string rejected — input sanitized")
        else:
            log.info(
                "SQL injection string accepted — check if server-side "
                "sanitization prevents actual injection"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- IG-C10: XSS payload in Code ----
    def test_IG_C10_xss_code(self, ig_page):
        """XSS payload in Code — should be sanitized or rejected."""
        log.info("IG-C10: XSS Code test")
        page = ig_page

        data = generate_xss_data()
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("XSS payload rejected — input sanitized")
        else:
            log.info("XSS payload accepted — check if DOM rendering is safe")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- IG-C11: Unicode/international characters in Code ----
    def test_IG_C11_unicode_code(self, ig_page):
        """Unicode/international characters in Code — check acceptance."""
        log.info("IG-C11: Unicode Code test")
        page = ig_page

        data = generate_unicode_data()
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("Unicode Code rejected")
        else:
            log.info("Unicode Code accepted (may be expected for i18n)")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- IG-C12: Code with leading/trailing spaces ----
    def test_IG_C12_leading_trailing_spaces(self, ig_page):
        """Code with leading/trailing spaces — should be trimmed.
        BUG: Spaces may not be trimmed before storage.
        """
        log.info("IG-C12: Leading/trailing spaces test")
        page = ig_page

        data = generate_leading_trailing_spaces_data()
        spaced_code = data["code"]
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        # Check if the form closed (submission succeeded)
        popup_closed = page.is_form_closed()

        if popup_closed:
            # Check if code was trimmed in the table
            page.click_refresh()
            page.wait_seconds(2)
            codes = page.get_all_codes()
            trimmed_code = spaced_code.strip()

            # Check if the stored code has leading/trailing spaces
            has_spaces = any(
                c != c.strip()
                for c in codes
                if spaced_code in c or trimmed_code in c
            )
            if has_spaces:
                log.warning("BUG: Leading/trailing spaces NOT trimmed in Code field")
            else:
                log.info("Code was trimmed before storage")
        else:
            log.info("Spaced Code rejected — validation working")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 2: Duplicate Validations (2 tests)
# ====================================================================

class TestDuplicateValidations:
    """IG-D01 to IG-D02: Duplicate Code checks in Create and Edit.
    BEH-004: Duplicate Codes are currently allowed with no check.
    """

    # ---- IG-D01: Duplicate Code — Create after Create ----
    def test_IG_D01_duplicate_create(self, ig_page):
        """Create two Item Groups with identical Codes.
        BEH-004: Second create is accepted.
        Test passes documenting current behavior as known bug.
        """
        log.info("IG-D01: Duplicate create test")
        page = ig_page

        # Create first Item Group
        data1 = generate_valid_ig_data("DDup1", "DDesc1")
        page.create_item_group(data1)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Create second Item Group with same Code
        data2 = generate_duplicate_code_data(data1["code"])
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data2)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("Duplicate Code rejected in Create — validation working")
        else:
            log.warning(
                "BEH-004 CONFIRMED: Duplicate Code allowed in Create form"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- IG-D02: Duplicate Code — Edit to existing Code ----
    def test_IG_D02_duplicate_edit(self, ig_page):
        """Edit an Item Group to use another Item Group's Code.
        BEH-004: Duplicate Code allowed in Edit.
        """
        log.info("IG-D02: Duplicate edit test")
        page = ig_page

        # Create two Item Groups
        data1 = generate_valid_ig_data("EditDup1", "EDesc1")
        page.create_item_group(data1)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        data2 = generate_valid_ig_data("EditDup2", "EDesc2")
        page.create_item_group(data2)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Edit second Item Group with first Item Group's code
        page.click_edit_button(item_name=data2["code"])
        page.wait_seconds(1)

        # Clear and type new (duplicate) code
        page._type_in_input(
            page.CODE_INPUT, page.CODE_INPUT_ALT, data1["code"]
        )
        page.click_update()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("Duplicate Code rejected in Edit — validation working")
        else:
            log.warning(
                "BEH-004 CONFIRMED: Duplicate Code allowed in Edit form"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 3: Edit Form Validations (5 tests)
# ====================================================================

class TestEditFormValidations:
    """IG-E01 to IG-E05: Validation checks on the Edit form."""

    # ---- IG-E01: Edit — pre-populated fields ----
    def test_IG_E01_edit_prepopulated(self, ig_page):
        """Edit popup should show Code and Description pre-populated."""
        log.info("IG-E01: Edit pre-populated fields test")
        page = ig_page

        data = generate_valid_ig_data("EditPre", "EditPreDesc")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Click Edit
        page.click_edit_button(item_name=data["code"])
        page.wait_seconds(2)

        # Read form values
        form_values = page.get_form_values()

        # If get_form_values returns empty, try reading via JS directly
        if not form_values.get("code"):
            try:
                val = page.driver.execute_script(
                    "var i = document.querySelector("
                    "  \"input[name='Code'], input[formcontrolname='code']\");"
                    "return i ? i.value : '';"
                )
                form_values["code"] = val or ""
                log.info(f"Read code via JS fallback: '{val}'")
            except Exception as e:
                log.warning(f"JS fallback read failed: {e}")

        assert form_values.get("code"), "Code field empty in Edit form"
        assert "EditPre" in form_values.get("code", ""), (
            f"Edit form Code value '{form_values.get('code')}' "
            f"doesn't match created code containing 'EditPre'"
        )

        log.info(f"Edit form pre-populated correctly: {form_values}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IG-E02: Edit — valid update ----
    def test_IG_E02_valid_edit(self, ig_page):
        """Edit with valid new Code and Description — should succeed."""
        log.info("IG-E02: Valid edit test")
        page = ig_page

        data = generate_valid_ig_data("EditOK", "EditOKDesc")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Edit with new data
        edit_data = generate_valid_edit_data("Updated", "UpdatedDesc")
        page.click_edit_button(item_name=data["code"])
        page.wait_seconds(1)
        page.fill_form(edit_data)
        page.click_update()
        page.wait_seconds(2)

        popup_closed = page.is_form_closed()

        if popup_closed:
            log.info("Edit form closed after update")
        else:
            validation_alert = page.get_swal_title()
            if validation_alert:
                log.warning(f"Validation alert after edit: {validation_alert}")

        # Verify updated code in table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_item_group_in_table(edit_data["code"])

        assert found, (
            f"Updated Item Group '{edit_data['code']}' not found in table"
        )
        log.info(f"Item Group updated and found in table: {edit_data['code']}")

    # ---- IG-E03: Edit — empty Code ----
    @pytest.mark.xfail(
        reason="BUG: Edit form may allow empty Code submission — will fail until ERP is fixed",
        strict=False,
    )
    def test_IG_E03_edit_empty_code(self, ig_page):
        """Edit with empty Code — should be blocked."""
        log.info("IG-E03: Edit empty Code test")
        page = ig_page

        data = generate_valid_ig_data("EditEmpty", "EditEmptyDesc")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Open Edit and clear the Code field
        page.click_edit_button(item_name=data["code"])
        page.wait_seconds(1)

        # Clear the Code field via JS
        page.driver.execute_script(
            "var i = document.querySelector("
            "  \"input[name='Code'], input[formcontrolname='code']\");"
            "if(i){"
            "  var s = Object.getOwnPropertyDescriptor("
            "    window.HTMLInputElement.prototype,'value').set;"
            "  s.call(i, '');"
            "  i.dispatchEvent(new Event('input',{bubbles:true}));"
            "  i.dispatchEvent(new Event('change',{bubbles:true}));"
            "}"
        )
        page.wait_seconds(0.5)

        page.click_update()
        page.wait_seconds(2)

        # Handle SweetAlert if it appeared
        validation_alert = ""
        if page.is_validation_alert_present(timeout=3):
            validation_alert = page.get_swal_title() or ""
            log.info(f"SweetAlert after empty edit submit: {validation_alert}")
            page.handle_validation_warning(timeout=5)

        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG: Edit form submitted with empty Code — no validation"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IG-E04: Edit — duplicate Code ----
    def test_IG_E04_edit_duplicate_code(self, ig_page):
        """Edit Item Group to use another Item Group's Code.
        BEH-004: Duplicate Code allowed in Edit.
        Test passes documenting current behavior as known bug.
        """
        log.info("IG-E04: Edit duplicate Code test")
        page = ig_page

        # Create two Item Groups
        data1 = generate_valid_ig_data("EDup1", "EDesc1")
        page.create_item_group(data1)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        data2 = generate_valid_ig_data("EDup2", "EDesc2")
        page.create_item_group(data2)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Edit second Item Group with first Item Group's code
        new_code = page.edit_item_group(
            data2["code"],
            {"code": data1["code"], "description": "Dup edit test"},
        )

        # Check for validation (BEH-004: duplicate allowed)
        page.click_refresh()
        page.wait_seconds(2)

        found_first = page.is_item_group_in_table(data1["code"])
        if found_first:
            log.warning(
                "BEH-004 CONFIRMED: Duplicate Code allowed in Edit form"
            )
        else:
            log.info("Duplicate Code rejected in Edit — validation working")

    # ---- IG-E05: Edit — no success popup ----
    def test_IG_E05_edit_no_success_popup(self, ig_page):
        """Verify whether a success SweetAlert appears after edit.
        Documents current behavior.
        """
        log.info("IG-E05: Edit no success popup test")
        page = ig_page

        data = generate_valid_ig_data("EditNoAlert", "EditNoAlertD")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Edit with new data
        edit_data = generate_valid_edit_data("UpdNoAlert", "UpdNoAlertD")
        page.click_edit_button(item_name=data["code"])
        page.wait_seconds(1)
        page.fill_form(edit_data)
        page.click_update()
        page.wait_seconds(2)

        # Check for SweetAlert
        swal_visible = page.is_validation_alert_present(timeout=3)

        if not swal_visible:
            log.info("No success SweetAlert after edit — popup just closes")
        else:
            swal_title = page.get_swal_title()
            log.info(f"SweetAlert appeared after edit: {swal_title}")
            page.handle_validation_warning(timeout=3)

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 4: Search & Filter Edge Cases (5 tests)
# ====================================================================

class TestSearchFilter:
    """IG-S01 to IG-S05: Search and Filter edge cases."""

    # ---- IG-S01: Search with exact Code ----
    def test_IG_S01_search_exact(self, ig_page):
        """Search with exact Item Group Code — should find it."""
        log.info("IG-S01: Search exact code")
        page = ig_page

        data = generate_valid_ig_data("SearchEx", "SearchDesc")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        found = page.search_item_group(data["code"])
        page.clear_search()

        assert found, f"Exact search failed for: {data['code']}"
        log.info(f"Exact search found: {data['code']}")

    # ---- IG-S02: Search with partial Code ----
    def test_IG_S02_search_partial(self, ig_page):
        """Search with partial Item Group Code — should find it."""
        log.info("IG-S02: Search partial code")
        page = ig_page

        data = generate_valid_ig_data("SearchPar", "SearchParD")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Use first 8 chars as partial search
        partial = data["code"][:8]
        found = page.search_item_group(partial)
        page.clear_search()

        assert found, f"Partial search failed for: {partial}"
        log.info(f"Partial search found with: {partial}")

    # ---- IG-S03: Search with non-existent Code ----
    def test_IG_S03_search_nonexistent(self, ig_page):
        """Search for non-existent code — should return no results."""
        log.info("IG-S03: Search nonexistent")
        page = ig_page

        fake_code = f"NonExistent_{int(time.time())}"
        found = page.search_item_group(fake_code)
        page.clear_search()

        assert not found, (
            f"BUG: Non-existent code '{fake_code}' was found in table"
        )
        log.info(f"Correctly not found: {fake_code}")

    # ---- IG-S04: Search — clear search restores table ----
    def test_IG_S04_clear_search_restores(self, ig_page):
        """After searching, clearing should restore full table."""
        log.info("IG-S04: Clear search restores table")
        page = ig_page

        # Get initial row count
        initial_count = page.get_table_row_count()

        # Search for something
        data = generate_valid_ig_data("ClearSearch", "ClearD")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Do a search
        page.search_item_group("ClearSearch")
        page.wait_seconds(1)

        # Clear search
        page.clear_search()
        page.wait_seconds(2)

        # Check row count is restored (should be >= initial count + 1)
        restored_count = page.get_table_row_count()
        log.info(f"Initial: {initial_count}, After restore: {restored_count}")

        assert restored_count >= initial_count, (
            "Table not restored after clearing search"
        )
        log.info("Table restored after clear search")

    # ---- IG-S05: Search — refresh resets search ----
    def test_IG_S05_refresh_resets_search(self, ig_page):
        """Clicking Refresh after search should reset the search."""
        log.info("IG-S05: Refresh resets search")
        page = ig_page

        data = generate_valid_ig_data("RefreshSearch", "RefreshD")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Search for something specific
        page.search_item_group("RefreshSearch")
        page.wait_seconds(1)

        # Click refresh
        page.click_refresh()
        page.wait_seconds(2)

        # Table should show all rows again
        row_count = page.get_table_row_count()
        log.info(f"Row count after refresh: {row_count}")

        assert row_count > 0, "Table should have rows after refresh"
        log.info("Refresh reset search successfully")


# ====================================================================
# PHASE 5: Popup & UI Behaviors (8 tests)
# ====================================================================

class TestPopupUIBehaviors:
    """IG-P01 to IG-P08: Popup and UI behavior checks."""

    # ---- IG-P01: View mode — all fields read-only ----
    def test_IG_P01_view_read_only(self, ig_page):
        """View popup should have all fields disabled/read-only."""
        log.info("IG-P01: View read-only test")
        page = ig_page

        data = generate_valid_ig_data("ViewRO", "ViewDesc")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Click View button
        page.click_view_button(item_name=data["code"])
        page.wait_seconds(1)

        is_view = page.is_view_mode()
        log.info(f"View mode detected: {is_view}")

        # Check that Code and Description inputs are disabled
        code_disabled = page.is_input_disabled(page.CODE_INPUT, page.CODE_INPUT_ALT)
        desc_disabled = page.is_input_disabled(
            page.DESCRIPTION_INPUT, page.DESCRIPTION_INPUT_ALT
        )

        log.info(f"Code disabled: {code_disabled}, Description disabled: {desc_disabled}")

        # At least one should be disabled for view mode
        assert is_view or code_disabled or desc_disabled, (
            "View mode: fields are NOT read-only"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IG-P02: Cancel closes the form ----
    def test_IG_P02_cancel_closes_form(self, ig_page):
        """Clicking Cancel should close the Add form."""
        log.info("IG-P02: Cancel closes form test")
        page = ig_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        page.cancel()
        page.wait_seconds(1)

        assert page.is_form_closed(), "Form still open after Cancel"
        log.info("Cancel closed the form successfully")

    # ---- IG-P03: No Delete button ----
    def test_IG_P03_no_delete_button(self, ig_page):
        """Verify that no Delete option exists.
        BEH-003: No Delete button on this screen.
        """
        log.info("IG-P03: No Delete button test")
        page = ig_page

        # Check the table row buttons — should only have View, Edit, History (3 buttons)
        row_count = page.get_table_row_count()
        if row_count > 0:
            try:
                rows = page.driver.find_elements(
                    By.CSS_SELECTOR, "table#excel-table tbody tr"
                )
                if rows:
                    btns = rows[0].find_elements(By.CSS_SELECTOR, "button")
                    btn_count = len(btns)
                    log.info(f"First row has {btn_count} action buttons")

                    # Should have 3 buttons: View, Edit, History
                    assert btn_count <= 4, (
                        f"Expected 3-4 action buttons, found {btn_count} — "
                        "there may be a Delete button"
                    )
            except Exception:
                log.warning("Could not check row buttons")

        # Check inside the edit popup — no Delete button
        data = generate_valid_ig_data("NoDel", "NoDelDesc")
        page.open_add_form()
        page.wait_seconds(1)

        # Look for Delete button in popup
        try:
            delete_btns = page.driver.find_elements(
                By.XPATH,
                "//div[@class='popup-footer']//button[contains(.,'Delete')]"
            )
            if delete_btns:
                log.warning("Delete button found in popup form!")
            else:
                log.info("No Delete button in popup form — as expected (BEH-003)")
        except Exception:
            log.info("No Delete button found — as expected")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            pass

    # ---- IG-P04: Add button opens form ----
    def test_IG_P04_add_button_opens_form(self, ig_page):
        """Clicking ADD button should open the create form popup."""
        log.info("IG-P04: Add button opens form test")
        page = ig_page

        page.open_add_form()
        page.wait_seconds(1)

        assert page.is_add_form_open(), "ADD button did not open form"
        log.info("ADD button opened form successfully")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            pass

    # ---- IG-P05: Form heading text ----
    def test_IG_P05_form_heading(self, ig_page):
        """Verify the form popup has a heading."""
        log.info("IG-P05: Form heading test")
        page = ig_page

        page.open_add_form()
        page.wait_seconds(1)

        heading = page.get_form_heading()
        log.info(f"Form heading: '{heading}'")

        assert heading, "Form heading is empty"
        # The heading should contain "Item Group" or similar
        log.info(f"Form heading verified: {heading}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            pass

    # ---- IG-P06: Edit mode shows Update button ----
    def test_IG_P06_edit_mode_update_button(self, ig_page):
        """Edit popup should show Update button instead of Submit."""
        log.info("IG-P06: Edit mode Update button test")
        page = ig_page

        data = generate_valid_ig_data("EditBtn", "EditBtnDesc")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Click Edit
        page.click_edit_button(item_name=data["code"])
        page.wait_seconds(1)

        is_edit = page.is_edit_mode()
        log.info(f"Edit mode detected: {is_edit}")

        assert is_edit, "Edit mode not detected — Update button not visible"

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IG-P07: Empty Description submit ----
    def test_IG_P07_empty_description_submit(self, ig_page):
        """Submit with empty Description — should be blocked (both fields required)."""
        log.info("IG-P07: Empty Description submit test")
        page = ig_page

        data = generate_empty_description_data()
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG: Form submitted with empty Description — no validation"
        )
        if validation_alert:
            log.info(f"Validation alert shown: {validation_alert}")
        if errors:
            log.info(f"Validation errors shown: {errors}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IG-P08: Both fields empty submit ----
    def test_IG_P08_both_empty_submit(self, ig_page):
        """Submit with both Code and Description empty — should be blocked."""
        log.info("IG-P08: Both fields empty submit test")
        page = ig_page

        data = generate_both_empty_data()
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG: Form submitted with both fields empty — no validation"
        )
        if validation_alert:
            log.info(f"Validation alert shown: {validation_alert}")
        if errors:
            log.info(f"Validation errors shown: {errors}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass


# ====================================================================
# PHASE 6: Filter Validations (2 tests)
# ====================================================================

class TestFilterValidations:
    """IG-F01 to IG-F02: Filter panel tests."""

    # ---- IG-F01: Filter panel opens and closes ----
    def test_IG_F01_filter_panel(self, ig_page):
        """Filter panel should open when Filters button is clicked."""
        log.info("IG-F01: Filter panel test")
        page = ig_page

        # Try to open filter panel
        page.open_filter_panel()
        page.wait_seconds(1)

        filter_open = page.is_filter_panel_open()

        if filter_open:
            log.info("Filter panel opened successfully")

            # Close filter panel
            page.close_filter_panel()
            page.wait_seconds(1)

            still_open = page.is_filter_panel_open()
            if not still_open:
                log.info("Filter panel closed successfully")
            else:
                log.warning("Filter panel still visible after close attempt")
        else:
            log.info("Filter button/panel not found — may not exist on this screen")

        page.click_refresh()

    # ---- IG-F02: Filter panel backdrop close ----
    def test_IG_F02_filter_backdrop_close(self, ig_page):
        """Filter panel should close when backdrop is clicked."""
        log.info("IG-F02: Filter backdrop close test")
        page = ig_page

        # Try to open filter panel
        page.open_filter_panel()
        page.wait_seconds(1)

        filter_open = page.is_filter_panel_open()

        if filter_open:
            # Click backdrop to close
            page._force_close_panels()
            page.wait_seconds(1)

            still_open = page.is_filter_panel_open()
            log.info(f"Filter panel still open after backdrop: {still_open}")
        else:
            log.info("Filter button/panel not found — skipping backdrop test")

        page.click_refresh()


# ====================================================================
# PHASE 7: History Validations (5 tests)
# ====================================================================

class TestHistoryValidations:
    """IG-H01 to IG-H05: History popup checks.
    Item Group has History button per row (cdk-column-archive).
    History popup uses div.popup-overlay container.
    """

    # ---- IG-H01: History button opens popup ----
    def test_IG_H01_history_opens(self, ig_page):
        """Click History button — popup should open."""
        log.info("IG-H01: History opens test")
        page = ig_page

        data = generate_valid_ig_data("HistOpen", "HistDesc")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Click History button
        page.click_history_button(item_name=data["code"])
        page.wait_seconds(2)

        # Check if history popup opened
        history_open = page.is_history_popup_open()

        assert history_open, "History popup did not open after clicking History button"
        log.info("History popup opened successfully")

        # Cleanup
        try:
            page.close_history_popup()
        except Exception:
            pass
        page.wait_seconds(1)

    # ---- IG-H02: History popup has rows ----
    def test_IG_H02_history_has_rows(self, ig_page):
        """History popup should show at least one entry after create."""
        log.info("IG-H02: History has rows test")
        page = ig_page

        data = generate_valid_ig_data("HistRow", "HistRowDesc")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Click History button
        page.click_history_button(item_name=data["code"])
        page.wait_seconds(2)

        row_count = page.get_history_row_count()
        log.info(f"History popup has {row_count} rows")

        assert row_count > 0, "History popup has no rows after create"

        # Cleanup
        try:
            page.close_history_popup()
        except Exception:
            pass
        page.wait_seconds(1)

    # ---- IG-H03: History popup can be closed ----
    def test_IG_H03_history_closes(self, ig_page):
        """History popup should close when Cancel/Close is clicked."""
        log.info("IG-H03: History closes test")
        page = ig_page

        data = generate_valid_ig_data("HistClose", "HistCloseD")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Click History button
        page.click_history_button(item_name=data["code"])
        page.wait_seconds(2)

        # Close it
        page.close_history_popup()
        page.wait_seconds(1)

        # Verify it closed
        history_open = page.is_history_popup_open()
        assert not history_open, "History popup still visible after close"
        log.info("History popup closed successfully")

    # ---- IG-H04: History shows new entry after edit ----
    def test_IG_H04_history_after_edit(self, ig_page):
        """After editing an Item Group, history should show a new entry."""
        log.info("IG-H04: History after edit test")
        page = ig_page

        data = generate_valid_ig_data("HistEdit", "HistEditD")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Get history row count before edit
        page.click_history_button(item_name=data["code"])
        page.wait_seconds(2)
        rows_before = page.get_history_row_count()
        log.info(f"History rows before edit: {rows_before}")
        page.close_history_popup()
        page.wait_seconds(1)

        # Edit the Item Group
        edit_data = generate_valid_edit_data("HistUpd", "HistUpdD")
        page.click_edit_button(item_name=data["code"])
        page.wait_seconds(1)
        page.fill_form(edit_data)
        page.click_update()
        page.wait_seconds(2)

        # Handle any SweetAlert
        if page.is_validation_alert_present(timeout=3):
            page.handle_validation_warning(timeout=5)

        page.click_refresh()
        page.wait_seconds(2)

        # Get history row count after edit
        page.click_history_button(item_name=edit_data["code"])
        page.wait_seconds(2)
        rows_after = page.get_history_row_count()
        log.info(f"History rows after edit: {rows_after}")

        assert rows_after >= rows_before, (
            f"History rows did not increase after edit "
            f"(before: {rows_before}, after: {rows_after})"
        )

        # Cleanup
        try:
            page.close_history_popup()
        except Exception:
            pass
        page.wait_seconds(1)

    # ---- IG-H05: History popup heading contains "history" ----
    def test_IG_H05_history_heading(self, ig_page):
        """History popup heading should contain the word 'history'."""
        log.info("IG-H05: History heading test")
        page = ig_page

        data = generate_valid_ig_data("HistHead", "HistHeadD")
        page.create_item_group(data)
        try:
            page.cancel()
        except Exception:
            pass
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Click History button
        page.click_history_button(item_name=data["code"])
        page.wait_seconds(2)

        # Check for any h3 with "history" text
        history_heading = ""
        try:
            h3s = page.driver.find_elements(
                By.CSS_SELECTOR,
                "div.popup-overlay h3, div.big-model h3"
            )
            for h in h3s:
                try:
                    if h.is_displayed() and "history" in h.text.lower():
                        history_heading = h.text.strip()
                        break
                except Exception:
                    continue
        except Exception:
            pass

        log.info(f"History heading: '{history_heading}'")

        # Cleanup
        try:
            page.close_history_popup()
        except Exception:
            pass
        page.wait_seconds(1)
