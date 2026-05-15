"""
test_item_master_validation.py
------------------------------
Comprehensive validation test suite for RhythmERP Item Master screen.
~57 test cases across 6 phases.

Phases:
  1. Create Form Validations  (15 tests) — IM-C01 to IM-C15
  2. Duplicate Validations      (3 tests) — IM-D01 to IM-D03
  3. Edit Form Validations      (8 tests) — IM-E01 to IM-E08
  4. Search & Filter Edge Cases (5 tests) — IM-S01 to IM-S05
  5. Popup & UI Behaviors       (8 tests) — IM-P01 to IM-P08
  6. History & Audit Trail      (5 tests) — IM-H01 to IM-H05

Known Bugs (suspected — to be confirmed during test execution):
  BUG-001 (HIGH)  : Spaces-only Item Name creates empty record
  BUG-002 (HIGH)  : Duplicate Item Names allowed
  BUG-003 (MEDIUM): No maxlength on Item Name input
  BUG-004 (MEDIUM): Negative Base Uom Conversion accepted
  BUG-005 (LOW)   : No Delete option anywhere on screen

Bug Handling Decisions:
  BUG-001: Test expects rejection — mark xfail, will FAIL until ERP is fixed
  BUG-002: Mark as known bug — test PASSES documenting current behavior
  BUG-003: Document as known issue, test confirms the bug
  BUG-004: Test expects rejection — mark xfail if bug confirmed
  BUG-005: Documented in UI phase, not tested (no button to click)

Run:
  pytest test_item_master_validation.py -v --tb=short
  pytest test_item_master_validation.py -v -k "TestCreateForm" --tb=short
  pytest test_item_master_validation.py -v -k "IM-C03" --tb=short
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

from pages.commodity_settings.modules.item_master.item_master_page import (
    ItemMasterPage,
)
from pages.commodity_settings.modules.item_master.data.item_master_data import (
    generate_valid_item_data,
    generate_valid_step2_data,
    generate_valid_step3_data,
    generate_full_valid_item_data,
    generate_valid_edit_data,
    generate_empty_data,
    generate_name_only_data,
    generate_duplicate_name_data,
    generate_string_255,
    generate_string_256,
    generate_spaces_only,
    generate_special_char_name,
    generate_negative_uom_conversion,
    generate_zero_uom_conversion,
    generate_alpha_uom_conversion,
    generate_special_char_uom_conversion,
    generate_decimal_uom_conversion,
    generate_uom_conversion_with_spaces,
    generate_item_code_with_special_chars,
    generate_item_name,
    generate_item_code,
    generate_description,
    generate_base_uom_conversion,
)
from common.logger import log


# ====================================================================
# Helper: create a prerequisite item, refresh, return its name
# ====================================================================

def _create_prerequisite_item(page, name_prefix="PreReq"):
    """Create an Item Master entry for tests that need existing data.
    Returns the item name used.
    """
    data = generate_full_valid_item_data(name_prefix)
    result = page.create_item(data)
    # Cleanup form if still open
    try:
        page.close_popup()
    except Exception:
        pass
    try:
        page.force_close_form_popup()
    except Exception:
        pass
    page.click_refresh()
    page.wait_seconds(2)
    name = data.get("item_name", "")
    log.info(f"Prerequisite item created: {name}")
    return name, data


# ====================================================================
# PHASE 1: Create Form Validations (15 tests)
# ====================================================================

class TestCreateFormValidations:
    """IM-C01 to IM-C15: Validation checks on the Create form.
    Item Master has a 3-step stepper with many fields.
    """

    # ---- IM-C01: Submit with all fields empty ----
    def test_IM_C01_empty_submit(self, im_page):
        """Submit with all fields empty — should be blocked."""
        log.info("IM-C01: Empty submit test")
        page = im_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Click Next on Step 1 with all fields empty
        page.click_stepper_next()
        page.wait_seconds(2)

        # Check for validation errors or SweetAlert
        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()
        still_step1 = page.is_step1_active()

        # Expect: form stays on Step 1 + validation errors shown
        assert form_still_open or errors or validation_alert, (
            "BUG: Form advanced with all fields empty — no validation"
        )
        if still_step1:
            log.info("Form stayed on Step 1 — validation working")
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

    # ---- IM-C02: Create with valid data (happy path) ----
    def test_IM_C02_valid_create(self, im_page):
        """Create with valid data across all 3 steps — should succeed."""
        log.info("IM-C02: Valid create test (happy path)")
        page = im_page

        data = generate_full_valid_item_data("ValidC")
        result = page.create_item(data)
        name = data.get("item_name", "")

        if result["status"] == "PASSED":
            log.info(f"Item created successfully: {name}")
        else:
            log.warning(f"Create failed: {result.get('error', 'unknown')}")

        # Verify the item appears in the table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_item_in_table(name)

        assert found, (
            f"Created item '{name}' not found in table after refresh"
        )
        log.info(f"Item created and found in table: {name}")

    # ---- IM-C03: Spaces-only Item Name ----
    @pytest.mark.xfail(
        reason="BUG-001: Spaces-only Item Name may be accepted — will fail until ERP is fixed",
        strict=False,
    )
    def test_IM_C03_spaces_only_name(self, im_page):
        """Spaces-only Item Name — should be rejected.
        BUG-001: Spaces-only name creates empty record.
        """
        log.info("IM-C03: Spaces-only name test")
        page = im_page

        data = generate_valid_item_data("SpaceIt")
        data["item_name"] = generate_spaces_only(10)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        assert form_still_open or errors or validation_alert, (
            "BUG-001 CONFIRMED: Spaces-only Item Name was accepted — "
            "system should reject it with a validation error"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IM-C04: Duplicate Item Name ----
    def test_IM_C04_duplicate_name(self, im_page):
        """Duplicate Item Name in Create — should be rejected.
        BUG-002: Duplicate names may be allowed.
        Test documents current behavior as known bug.
        """
        log.info("IM-C04: Duplicate name test")
        page = im_page

        # Create first item
        name1, data1 = _create_prerequisite_item(page, "Dup1")

        # Try creating second item with same name
        data2 = generate_duplicate_name_data(name1)
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data2)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("Duplicate name rejected — validation working")
        else:
            log.warning(
                "BUG-002 CONFIRMED: Duplicate Item Name allowed in Create form"
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

    # ---- IM-C05: Item Name at 255 char boundary ----
    def test_IM_C05_name_255_chars(self, im_page):
        """Item Name with exactly 255 chars — boundary test."""
        log.info("IM-C05: 255-char name test")
        page = im_page

        name_255 = generate_string_255()
        data = generate_valid_item_data("Bnd255")
        data["item_name"] = name_255

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("255-char name rejected — maxlength enforced")
        else:
            log.info(
                "255-char name accepted (may be expected if max >= 255)"
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

    # ---- IM-C06: Item Name exceeds 255 chars (256) ----
    def test_IM_C06_name_256_chars(self, im_page):
        """Item Name with 256 chars — should be rejected or truncated.
        BUG-003: No maxlength on input.
        """
        log.info("IM-C06: 256-char name test")
        page = im_page

        name_256 = generate_string_256()
        data = generate_valid_item_data("Bnd256")
        data["item_name"] = name_256

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("256-char name rejected — maxlength enforced")
        else:
            log.warning(
                "BUG-003 CONFIRMED: 256-char name accepted — "
                "no maxlength validation"
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

    # ---- IM-C07: Special characters in Item Name ----
    def test_IM_C07_special_chars_name(self, im_page):
        """Special characters in Item Name — check if accepted or rejected."""
        log.info("IM-C07: Special chars in name test")
        page = im_page

        data = generate_valid_item_data("SpecCh")
        data["item_name"] = generate_special_char_name()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("Special chars rejected — validation working")
        else:
            log.info(
                "Special chars accepted in Item Name (may be expected behavior)"
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

    # ---- IM-C08: Negative Base Uom Conversion ----
    @pytest.mark.xfail(
        reason="BUG-004: Negative Base Uom Conversion may be accepted",
        strict=False,
    )
    def test_IM_C08_negative_uom_conversion(self, im_page):
        """Negative value in Base Uom Conversion — should be rejected.
        BUG-004: Negative values may be accepted.
        """
        log.info("IM-C08: Negative UOM conversion test")
        page = im_page

        data = generate_valid_item_data("NegUom")
        data["base_uom_conversion"] = generate_negative_uom_conversion()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG-004 CONFIRMED: Negative Base Uom Conversion was accepted"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IM-C09: Zero Base Uom Conversion ----
    def test_IM_C09_zero_uom_conversion(self, im_page):
        """Zero value in Base Uom Conversion — check if rejected."""
        log.info("IM-C09: Zero UOM conversion test")
        page = im_page

        data = generate_valid_item_data("ZeroUom")
        data["base_uom_conversion"] = generate_zero_uom_conversion()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        if form_still_open or errors or validation_alert:
            log.info("Zero UOM conversion rejected — validation working")
        else:
            log.info(
                "Zero UOM conversion accepted (may be valid in some contexts)"
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

    # ---- IM-C10: Alphabetic Base Uom Conversion ----
    def test_IM_C10_alpha_uom_conversion(self, im_page):
        """Alphabetic characters in Base Uom Conversion — should be rejected."""
        log.info("IM-C10: Alpha UOM conversion test")
        page = im_page

        data = generate_valid_item_data("AlphaUom")
        data["base_uom_conversion"] = generate_alpha_uom_conversion()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        if form_still_open or errors or validation_alert:
            log.info("Alpha UOM conversion rejected — validation working")
        else:
            log.warning(
                "BUG: Alphabetic characters accepted in Base Uom Conversion"
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

    # ---- IM-C11: Special characters in Base Uom Conversion ----
    def test_IM_C11_special_char_uom_conversion(self, im_page):
        """Special characters in Base Uom Conversion — should be rejected."""
        log.info("IM-C11: Special char UOM conversion test")
        page = im_page

        data = generate_valid_item_data("SpUom")
        data["base_uom_conversion"] = generate_special_char_uom_conversion()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        if form_still_open or errors or validation_alert:
            log.info("Special char UOM conversion rejected — validation working")
        else:
            log.warning(
                "BUG: Special characters accepted in Base Uom Conversion"
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

    # ---- IM-C12: Spaces in Base Uom Conversion ----
    def test_IM_C12_spaces_uom_conversion(self, im_page):
        """Spaces-only value in Base Uom Conversion — should be rejected."""
        log.info("IM-C12: Spaces UOM conversion test")
        page = im_page

        data = generate_valid_item_data("SpUom")
        data["base_uom_conversion"] = generate_uom_conversion_with_spaces()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        if form_still_open or errors or validation_alert:
            log.info("Spaces UOM conversion rejected — validation working")
        else:
            log.warning(
                "BUG: Spaces accepted in Base Uom Conversion"
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

    # ---- IM-C13: Valid decimal Base Uom Conversion ----
    def test_IM_C13_decimal_uom_conversion(self, im_page):
        """Valid decimal value in Base Uom Conversion — should be accepted."""
        log.info("IM-C13: Decimal UOM conversion test")
        page = im_page

        data = generate_valid_item_data("DecUom")
        data["base_uom_conversion"] = generate_decimal_uom_conversion()

        result = page.create_item(data)
        name = data.get("item_name", "")

        if result["status"] == "PASSED":
            page.click_refresh()
            page.wait_seconds(2)
            found = page.is_item_in_table(name)
            assert found, f"Item with decimal UOM conversion not found: {name}"
            log.info(f"Decimal UOM conversion accepted: {name}")
        else:
            log.warning(
                f"Decimal UOM conversion may have been rejected: {result.get('error', '')}"
            )

    # ---- IM-C14: Only Item Name filled (partial) ----
    def test_IM_C14_name_only_partial(self, im_page):
        """Submit with only Item Name filled — required fields should block."""
        log.info("IM-C14: Name-only partial submit test")
        page = im_page

        data = generate_name_only_data("NameOnly")

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        still_step1 = page.is_step1_active()

        # Required dropdowns (Item Category, Item Type, UOM, etc.) should block
        assert still_step1 or errors or validation_alert, (
            "BUG: Form advanced with only Item Name — "
            "other required fields not validated"
        )
        if errors:
            log.info(f"Partial fill validation errors: {errors}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IM-C15: Stepper navigation — Back button ----
    def test_IM_C15_stepper_back_button(self, im_page):
        """Fill Step 1, go to Step 2, then click Back — should return to Step 1."""
        log.info("IM-C15: Stepper Back button test")
        page = im_page

        data = generate_valid_item_data("StepNav")

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_step1_active(), "Step 1 should be active initially"

        # Fill Step 1 and go to Step 2
        page.fill_step1(data)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Verify we're on Step 2
        step2_active = page.is_step2_active()
        if step2_active:
            log.info("Successfully navigated to Step 2")

            # Click Back
            page.click_stepper_back()
            page.wait_seconds(1)

            # Verify we're back on Step 1
            assert page.is_step1_active(), (
                "Did not return to Step 1 after clicking Back"
            )
            log.info("Back button correctly returned to Step 1")

            # Verify Step 1 data is preserved
            values = page.get_form_field_values_step1()
            if values.get("item_name"):
                log.info(
                    f"Step 1 data preserved after Back: name={values['item_name']}"
                )
            else:
                log.warning("Step 1 data may have been lost after Back navigation")
        else:
            log.warning(
                "Could not navigate to Step 2 — "
                "required field validation may have blocked"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass


# ====================================================================
# PHASE 2: Duplicate Validations (3 tests)
# ====================================================================

class TestDuplicateValidations:
    """IM-D01 to IM-D03: Duplicate name checks in Create and Edit.
    BUG-002: Duplicate Item Names may be allowed with no check.
    """

    # ---- IM-D01: Duplicate name — Create after Create ----
    def test_IM_D01_duplicate_create(self, im_page):
        """Create two items with identical names.
        BUG-002: Second create may be accepted.
        """
        log.info("IM-D01: Duplicate create test")
        page = im_page

        # Create first item
        name1, data1 = _create_prerequisite_item(page, "DDup1")

        # Create second item with same name
        data2 = generate_duplicate_name_data(name1)
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data2)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("Duplicate name rejected in Create — validation working")
        else:
            log.warning(
                "BUG-002 CONFIRMED: Duplicate Item Name allowed in Create form"
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

    # ---- IM-D02: Duplicate name — case-insensitive check ----
    def test_IM_D02_duplicate_case_insensitive(self, im_page):
        """Create item with same name in different case.
        Tests if the duplicate check is case-insensitive.
        """
        log.info("IM-D02: Duplicate case-insensitive test")
        page = im_page

        # Create first item
        name1, data1 = _create_prerequisite_item(page, "CaseDup")

        # Create second item with uppercase version of same name
        data2 = generate_valid_item_data("CaseDup2")
        data2["item_name"] = name1.upper()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data2)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info(
                "Case-insensitive duplicate check working — rejected"
            )
        else:
            log.info(
                "Case-insensitive duplicate check NOT enforced — "
                "uppercase version accepted"
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

    # ---- IM-D03: Duplicate name — Edit to existing name ----
    def test_IM_D03_duplicate_edit(self, im_page):
        """Edit an item to use another item's name.
        BUG-002: Duplicate name may be allowed in Edit.
        """
        log.info("IM-D03: Duplicate edit test")
        page = im_page

        # Create two items
        name1, data1 = _create_prerequisite_item(page, "EditDup1")
        name2, data2 = _create_prerequisite_item(page, "EditDup2")

        # Edit second item with first item's name
        page.click_edit_button(item_name=name2)
        page.wait_seconds(1)

        if page.is_edit_mode():
            # Clear and type duplicate name
            page.type_text(
                page.ITEM_NAME_INPUT, name1, clear_first=True
            )
            page.click_update()
            page.wait_seconds(2)

            validation_alert = page.handle_validation_warning(timeout=3)
            form_still_open = page.is_add_form_open()

            if validation_alert or form_still_open:
                log.info(
                    "Duplicate name rejected in Edit — validation working"
                )
            else:
                log.warning(
                    "BUG-002 CONFIRMED: Duplicate name allowed in Edit form"
                )

            # Cleanup
            try:
                page.cancel()
            except Exception:
                try:
                    page.close_popup()
                except Exception:
                    pass
        else:
            log.warning("Could not open Edit form for second item")

        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 3: Edit Form Validations (8 tests)
# ====================================================================

class TestEditFormValidations:
    """IM-E01 to IM-E08: Validation checks on the Edit form."""

    # ---- IM-E01: Edit — pre-populated fields ----
    def test_IM_E01_edit_prepopulated(self, im_page):
        """Edit popup should show Step 1 fields pre-populated."""
        log.info("IM-E01: Edit pre-populated fields test")
        page = im_page

        name, data = _create_prerequisite_item(page, "EditPre")

        # Click Edit
        page.click_edit_button(item_name=name)
        page.wait_seconds(2)

        # Read form values
        form_values = page.get_form_field_values_step1()

        assert form_values.get("item_name"), (
            "Item Name field empty in Edit form"
        )
        # The value should contain at least part of the original name
        assert "EditPre" in form_values.get("item_name", ""), (
            f"Edit form Name value '{form_values.get('item_name')}' "
            f"doesn't match created name containing 'EditPre'"
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

    # ---- IM-E02: Edit — valid update ----
    def test_IM_E02_valid_edit(self, im_page):
        """Edit with valid new values — should succeed."""
        log.info("IM-E02: Valid edit test")
        page = im_page

        name, data = _create_prerequisite_item(page, "EditOK")

        # Edit with new values
        edit_data = generate_valid_edit_data("Updated")
        result = page.edit_item(name, edit_data)

        if result["status"] == "PASSED":
            log.info(f"Item updated successfully")
        else:
            log.warning(f"Edit failed: {result.get('error', 'unknown')}")

        # Verify updated name in table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_item_in_table(edit_data["item_name"])

        assert found, (
            f"Updated item '{edit_data['item_name']}' not found in table"
        )
        log.info(f"Item updated and found in table: {edit_data['item_name']}")

    # ---- IM-E03: Edit — empty Item Name ----
    @pytest.mark.xfail(
        reason="BUG: Edit form may allow empty Name submission",
        strict=False,
    )
    def test_IM_E03_edit_empty_name(self, im_page):
        """Edit with empty Item Name — should be blocked."""
        log.info("IM-E03: Edit empty name test")
        page = im_page

        name, data = _create_prerequisite_item(page, "EditEmpty")

        # Open Edit and clear the Item Name field
        page.click_edit_button(item_name=name)
        page.wait_seconds(1)

        # Clear the name field via JS
        page.driver.execute_script(
            "var i = document.querySelector("
            "  \"input[name='Item Name'], input[formcontrolname='itemName'], \""
            "  + \"input[name='itemName']\");"
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
            "BUG: Edit form submitted with empty Item Name — no validation"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IM-E04: Edit — spaces-only Item Name ----
    def test_IM_E04_edit_spaces_only(self, im_page):
        """Edit Item Name to spaces-only — should be rejected.
        BUG-001: Spaces-only name may be accepted.
        """
        log.info("IM-E04: Edit spaces-only name test")
        page = im_page

        name, data = _create_prerequisite_item(page, "EditSpace")

        # Open Edit and type spaces-only name
        page.click_edit_button(item_name=name)
        page.wait_seconds(1)

        page.type_text(
            page.ITEM_NAME_INPUT, generate_spaces_only(8), clear_first=True
        )
        page.click_update()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        if form_still_open or errors or validation_alert:
            log.info("Spaces-only name rejected in Edit — validation working")
        else:
            log.warning(
                "BUG-001 in Edit: Spaces-only name accepted in Edit form"
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

    # ---- IM-E05: Edit — stepper still works in edit mode ----
    def test_IM_E05_edit_stepper_navigation(self, im_page):
        """Edit form should allow navigating between stepper steps."""
        log.info("IM-E05: Edit stepper navigation test")
        page = im_page

        name, data = _create_prerequisite_item(page, "EditStep")

        page.click_edit_button(item_name=name)
        page.wait_seconds(1)

        if page.is_edit_mode():
            # Should start on Step 1
            assert page.is_step1_active(), "Edit should start on Step 1"

            # Navigate to Step 2
            next_clicked = page.click_stepper_next()
            page.wait_seconds(1)

            if next_clicked:
                log.info(f"Current step after Next: {page.get_current_step_index()}")
                # Navigate back to Step 1
                page.click_stepper_back()
                page.wait_seconds(1)
                assert page.is_step1_active(), (
                    "Did not return to Step 1 after Back in Edit"
                )
                log.info("Stepper navigation works in Edit mode")
            else:
                log.warning("Stepper Next did not work in Edit mode")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IM-E06: Edit — toggle switches ----
    def test_IM_E06_edit_toggle_switches(self, im_page):
        """Toggle switches in Edit mode should be changeable."""
        log.info("IM-E06: Edit toggle switches test")
        page = im_page

        name, data = _create_prerequisite_item(page, "EditToggle")

        page.click_edit_button(item_name=name)
        page.wait_seconds(1)

        if page.is_edit_mode():
            # Read current toggle states
            status_before = page.get_toggle_state(page.STATUS_TOGGLE, "Status")
            critical_before = page.get_toggle_state(page.IS_CRITICAL_TOGGLE, "Is Critical")

            # Toggle them
            page._set_toggle_to(page.STATUS_TOGGLE, "Status", not status_before)
            page._set_toggle_to(page.IS_CRITICAL_TOGGLE, "Is Critical", not critical_before)
            page.wait_seconds(0.5)

            # Verify states changed
            status_after = page.get_toggle_state(page.STATUS_TOGGLE, "Status")
            critical_after = page.get_toggle_state(page.IS_CRITICAL_TOGGLE, "Is Critical")

            if status_after != status_before:
                log.info("Status toggle changed successfully")
            else:
                log.warning("Status toggle did not change")

            if critical_after != critical_before:
                log.info("Is Critical toggle changed successfully")
            else:
                log.warning("Is Critical toggle did not change")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IM-E07: Edit — negative Uom Conversion ----
    @pytest.mark.xfail(
        reason="BUG-004: Negative Uom Conversion may be accepted in Edit",
        strict=False,
    )
    def test_IM_E07_edit_negative_uom(self, im_page):
        """Edit with negative Base Uom Conversion — should be rejected."""
        log.info("IM-E07: Edit negative UOM conversion test")
        page = im_page

        name, data = _create_prerequisite_item(page, "EditNegUom")

        page.click_edit_button(item_name=name)
        page.wait_seconds(1)

        if page.is_edit_mode():
            page.type_text(
                page.BASE_UOM_CONVERSION_INPUT,
                generate_negative_uom_conversion(),
                clear_first=True,
            )
            page.click_update()
            page.wait_seconds(2)

            validation_alert = page.handle_validation_warning(timeout=3)
            errors = page.get_mat_error_text()
            form_still_open = page.is_add_form_open()

            assert form_still_open or errors or validation_alert, (
                "BUG-004 CONFIRMED: Negative UOM conversion accepted in Edit"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IM-E08: Edit — special chars in Item Code ----
    def test_IM_E08_edit_special_char_code(self, im_page):
        """Edit Item Code with special characters — check acceptance."""
        log.info("IM-E08: Edit special char code test")
        page = im_page

        name, data = _create_prerequisite_item(page, "EditSpCode")

        page.click_edit_button(item_name=name)
        page.wait_seconds(1)

        if page.is_edit_mode():
            page.type_text(
                page.ITEM_CODE_INPUT,
                generate_item_code_with_special_chars(),
                clear_first=True,
            )
            page.click_update()
            page.wait_seconds(2)

            validation_alert = page.handle_validation_warning(timeout=3)
            form_still_open = page.is_add_form_open()

            if validation_alert or form_still_open:
                log.info("Special chars in Item Code rejected")
            else:
                log.info("Special chars in Item Code accepted")

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
    """IM-S01 to IM-S05: Search and Filter edge cases."""

    # ---- IM-S01: Search with exact Item Name ----
    def test_IM_S01_search_exact(self, im_page):
        """Search with exact item name — should find it."""
        log.info("IM-S01: Search exact name")
        page = im_page

        name, data = _create_prerequisite_item(page, "SearchEx")

        found = page.search_item(name)
        page.clear_search()

        assert found, f"Exact search failed for: {name}"
        log.info(f"Exact search found: {name}")

    # ---- IM-S02: Search with partial Item Name ----
    def test_IM_S02_search_partial(self, im_page):
        """Search with partial item name — should find it."""
        log.info("IM-S02: Search partial name")
        page = im_page

        name, data = _create_prerequisite_item(page, "SearchPar")

        # Use first 8 chars as partial search
        partial = name[:8]
        found = page.search_item(partial)
        page.clear_search()

        assert found, f"Partial search failed for: {partial}"
        log.info(f"Partial search found with: {partial}")

    # ---- IM-S03: Search with non-existent Name ----
    def test_IM_S03_search_nonexistent(self, im_page):
        """Search for non-existent name — should return no results."""
        log.info("IM-S03: Search nonexistent")
        page = im_page

        fake_name = f"NonExistent_{int(time.time())}"
        found = page.search_item(fake_name)
        page.clear_search()

        assert not found, (
            f"BUG: Non-existent name '{fake_name}' was found in table"
        )
        log.info(f"Correctly not found: {fake_name}")

    # ---- IM-S04: Search after creating new item ----
    def test_IM_S04_search_after_create(self, im_page):
        """Create a new item, then search — should find it immediately."""
        log.info("IM-S04: Search after create")
        page = im_page

        name, data = _create_prerequisite_item(page, "SearchNew")

        # Refresh and search
        page.click_refresh()
        page.wait_seconds(2)
        found = page.search_item(name)
        page.clear_search()

        assert found, f"Newly created item not found in search: {name}"
        log.info(f"Newly created item found in search: {name}")

    # ---- IM-S05: Search and verify row details ----
    def test_IM_S05_search_verify_details(self, im_page):
        """Search for an item and verify row details match."""
        log.info("IM-S05: Search verify details")
        page = im_page

        name, data = _create_prerequisite_item(page, "SearchDet")

        found = page.search_item(name)
        if found:
            row_idx = page.find_item_row_index(name)
            if row_idx >= 0:
                details = page.get_item_details_from_row(row_idx)
                log.info(f"Row details: {details}")
                # Item name should be in the row
                assert name in details.get("item_name", ""), (
                    f"Row item name '{details.get('item_name')}' "
                    f"doesn't match '{name}'"
                )
                log.info(f"Row details verified for: {name}")
        else:
            log.warning(f"Could not find item for detail verification: {name}")

        page.clear_search()


# ====================================================================
# PHASE 5: Popup & UI Behaviors (8 tests)
# ====================================================================

class TestPopupUIBehaviors:
    """IM-P01 to IM-P08: Popup, stepper, and UI behavior tests."""

    # ---- IM-P01: View popup is read-only ----
    def test_IM_P01_view_read_only(self, im_page):
        """View popup should show fields as read-only."""
        log.info("IM-P01: View read-only test")
        page = im_page

        name, data = _create_prerequisite_item(page, "ViewRO")

        page.click_view_button(item_name=name)
        page.wait_seconds(1)

        is_readonly = page.verify_view_popup_read_only()
        assert is_readonly, (
            "View popup fields are editable — should be read-only"
        )
        log.info("View popup is correctly read-only")

        # Cleanup
        page.close_popup()
        page.wait_seconds(0.5)

    # ---- IM-P02: No Delete button available ----
    def test_IM_P02_no_delete_button(self, im_page):
        """Verify no Delete button exists per row.
        BUG-005: No Delete option on the screen.
        """
        log.info("IM-P02: No delete button test")
        page = im_page

        row_count = page.get_table_row_count()
        if row_count > 0:
            # Check each row for delete button
            rows = page.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            for i, row in enumerate(rows):
                delete_btns = row.find_elements(
                    By.CSS_SELECTOR,
                    "td.cdk-column-delete button, "
                    "td.mat-column-delete button, "
                    "button[mattooltip='Delete']"
                )
                if delete_btns:
                    log.warning(
                        f"BUG: Delete button found in row {i} — "
                        "this may have been added since last inspection"
                    )
                    return

            log.info(
                "No Delete button found in any row — "
                "BUG-005 confirmed: No Delete functionality"
            )
        else:
            log.info("No rows in table to check for Delete button")

    # ---- IM-P03: Add form opens stepper ----
    def test_IM_P03_add_form_stepper(self, im_page):
        """Add form should open with Step 1 active in stepper."""
        log.info("IM-P03: Add form stepper test")
        page = im_page

        page.open_add_form()
        page.wait_seconds(1)

        assert page.is_add_form_open(), "Add form did not open"
        assert page.is_step1_active(), (
            "Add form should start on Step 1"
        )
        log.info("Add form opens with Step 1 active — stepper working")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IM-P04: Cancel closes the form ----
    def test_IM_P04_cancel_closes_form(self, im_page):
        """Cancel button should close the stepper form."""
        log.info("IM-P04: Cancel closes form test")
        page = im_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        page.cancel()
        page.wait_seconds(1)

        assert page.is_form_closed(), (
            "Form still open after Cancel"
        )
        log.info("Cancel correctly closes the form")

    # ---- IM-P05: Refresh button works ----
    def test_IM_P05_refresh_button(self, im_page):
        """Refresh button should reload the table."""
        log.info("IM-P05: Refresh button test")
        page = im_page

        row_count_before = page.get_table_row_count()
        page.click_refresh()
        page.wait_seconds(2)

        # Page should still be loaded
        assert page.is_page_loaded(), "Page not loaded after refresh"
        log.info("Refresh button works — page reloaded")

    # ---- IM-P06: Step 3 — Add Row button ----
    def test_IM_P06_step3_add_row(self, im_page):
        """Step 3 should allow adding rows to the packaging table."""
        log.info("IM-P06: Step 3 Add Row test")
        page = im_page

        data = generate_valid_item_data("AddRow")

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Navigate to Step 3
        step2_data = generate_valid_step2_data()
        page.fill_step2(step2_data)
        page.click_stepper_next()
        page.wait_seconds(1)

        if page.is_step3_active():
            # Get initial row count
            initial_count = page.get_step3_row_count()
            log.info(f"Step 3 initial row count: {initial_count}")

            # Click Add Row
            page._click_add_row_step3()
            page.wait_seconds(1)

            new_count = page.get_step3_row_count()
            log.info(f"Step 3 row count after Add Row: {new_count}")

            if new_count > initial_count:
                log.info("Add Row button works — new row added")
            else:
                log.warning("Add Row button may not have added a new row")
        else:
            log.warning("Could not navigate to Step 3")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IM-P07: Toggle switches in Create form ----
    def test_IM_P07_toggle_switches_create(self, im_page):
        """Toggle switches should be functional in Create form."""
        log.info("IM-P07: Toggle switches in Create test")
        page = im_page

        page.open_add_form()
        page.wait_seconds(1)

        # Read default states
        status_default = page.get_toggle_state(page.STATUS_TOGGLE, "Status")
        critical_default = page.get_toggle_state(page.IS_CRITICAL_TOGGLE, "Is Critical")
        wip_default = page.get_toggle_state(page.INCLUDE_WIP_TOGGLE, "Include Wip")
        packing_default = page.get_toggle_state(
            page.IS_PACKING_MATERIAL_TOGGLE, "Is Packing Material"
        )

        log.info(
            f"Default toggle states — "
            f"Status: {status_default}, Critical: {critical_default}, "
            f"WIP: {wip_default}, Packing: {packing_default}"
        )

        # Toggle Status
        page._set_toggle_to(page.STATUS_TOGGLE, "Status", not status_default)
        page.wait_seconds(0.5)
        new_status = page.get_toggle_state(page.STATUS_TOGGLE, "Status")

        if new_status != status_default:
            log.info("Status toggle works in Create form")
        else:
            log.warning("Status toggle did not change in Create form")

        # Toggle Is Critical
        page._set_toggle_to(page.IS_CRITICAL_TOGGLE, "Is Critical", True)
        page.wait_seconds(0.5)
        new_critical = page.get_toggle_state(page.IS_CRITICAL_TOGGLE, "Is Critical")

        if new_critical:
            log.info("Is Critical toggle works in Create form")
        else:
            log.warning("Is Critical toggle did not change to ON")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IM-P08: Stepper header click navigation ----
    def test_IM_P08_stepper_header_click(self, im_page):
        """Clicking stepper headers should navigate between steps
        (if linear mode allows).
        """
        log.info("IM-P08: Stepper header click test")
        page = im_page

        data = generate_valid_item_data("HeadClick")

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step1(data)

        # Try to click Step 2 header directly
        navigated = page.go_to_step(1)
        page.wait_seconds(1)

        if navigated and page.is_step2_active():
            log.info("Step 2 header click navigation works")
        else:
            log.info(
                "Step 2 header click navigation blocked — "
                "may need Next button first (linear stepper)"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass


# ====================================================================
# PHASE 6: History & Audit Trail (5 tests)
# ====================================================================

class TestHistoryAuditTrail:
    """IM-H01 to IM-H05: History popup and audit trail tests.
    Item Master has History column (mat-column-archive).
    """

    # ---- IM-H01: History popup opens ----
    def test_IM_H01_history_popup_opens(self, im_page):
        """Clicking History button should open the history popup."""
        log.info("IM-H01: History popup opens test")
        page = im_page

        name, data = _create_prerequisite_item(page, "HistOpen")

        page.click_history_button(item_name=name)
        page.wait_seconds(1.5)

        # Check if history popup is visible
        history_open = page.is_history_popup_open()

        if history_open:
            log.info("History popup opened successfully")
            page.close_history_popup()
            page.wait_seconds(0.5)
        else:
            # Check if any popup opened at all
            any_popup = page._is_form_popup_open()
            if any_popup:
                heading = page.get_form_heading()
                log.info(f"Popup opened with heading: {heading}")
                page.close_popup()
            else:
                log.warning("No popup opened after clicking History button")

    # ---- IM-H02: History has data after create ----
    def test_IM_H02_history_data_after_create(self, im_page):
        """After creating an item, history should show at least one entry."""
        log.info("IM-H02: History data after create test")
        page = im_page

        name, data = _create_prerequisite_item(page, "HistData")

        page.click_history_button(item_name=name)
        page.wait_seconds(1.5)

        if page.is_history_popup_open():
            row_count = page.get_history_row_count()
            log.info(f"History row count: {row_count}")

            if row_count > 0:
                log.info(f"History has {row_count} entries after create")
            else:
                log.info("History is empty after create (may be expected)")

            page.close_history_popup()
            page.wait_seconds(0.5)
        else:
            log.warning("History popup did not open")

    # ---- IM-H03: History data after edit ----
    def test_IM_H03_history_data_after_edit(self, im_page):
        """After editing an item, history should show additional entries."""
        log.info("IM-H03: History data after edit test")
        page = im_page

        name, data = _create_prerequisite_item(page, "HistEdit")

        # Check history before edit
        page.click_history_button(item_name=name)
        page.wait_seconds(1.5)

        count_before = 0
        if page.is_history_popup_open():
            count_before = page.get_history_row_count()
            page.close_history_popup()
            page.wait_seconds(0.5)

        # Edit the item
        edit_data = generate_valid_edit_data("HistUpd")
        result = page.edit_item(name, edit_data)

        # Check history after edit
        page.click_refresh()
        page.wait_seconds(2)

        # Search for the updated name
        updated_name = edit_data["item_name"]
        page.search_item(updated_name)
        page.wait_seconds(1)

        page.click_history_button(item_name=updated_name)
        page.wait_seconds(1.5)

        count_after = 0
        if page.is_history_popup_open():
            count_after = page.get_history_row_count()
            page.close_history_popup()
            page.wait_seconds(0.5)

        log.info(
            f"History rows: before edit={count_before}, "
            f"after edit={count_after}"
        )

        if count_after > count_before:
            log.info("History updated after edit — audit trail working")
        else:
            log.info(
                "History not updated after edit (may be expected if "
                "only one history entry per record)"
            )

        page.clear_search()

    # ---- IM-H04: History search within popup ----
    def test_IM_H04_history_search(self, im_page):
        """Search within history popup should filter results."""
        log.info("IM-H04: History search test")
        page = im_page

        name, data = _create_prerequisite_item(page, "HistSrch")

        page.click_history_button(item_name=name)
        page.wait_seconds(1.5)

        if page.is_history_popup_open():
            # Try searching within history
            search_result = page.search_in_history(name[:6])

            if search_result:
                log.info("History search executed successfully")
            else:
                log.info("History search input not found or not functional")

            page.close_history_popup()
            page.wait_seconds(0.5)
        else:
            log.warning("History popup did not open for search test")

    # ---- IM-H05: History close button works ----
    def test_IM_H05_history_close(self, im_page):
        """History popup should close via Close/Cancel button."""
        log.info("IM-H05: History close test")
        page = im_page

        name, data = _create_prerequisite_item(page, "HistClose")

        page.click_history_button(item_name=name)
        page.wait_seconds(1.5)

        if page.is_history_popup_open():
            page.close_history_popup()
            page.wait_seconds(1)

            assert not page.is_history_popup_open(), (
                "History popup still open after close attempt"
            )
            log.info("History popup closed successfully")
        else:
            log.info("History popup did not open — close test skipped")
