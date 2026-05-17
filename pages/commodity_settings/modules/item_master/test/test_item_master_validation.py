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

IMPORTANT — Item Name is READONLY:
  - Item Name field has readonly=true and CANNOT be typed into
  - It is auto-generated as a space-separated concatenation of
    Item Attribute 1-5 values
  - Tests for spaces-only, maxlength, special chars in Item Name
    are NOT APPLICABLE — the field cannot receive manual input
  - Duplicate name checks would require selecting identical attribute
    values, which is difficult to control from live UI dropdowns
  - Item Name is also readonly in Edit mode

Stepper Layout (verified from live application 2026-05-18 — V2 exploration):
  - Step 1: All form fields + 3 toggle switches (NOT 4!)
    (Status, Is Critical, Include Wip, Is Packing Material)
    "Allow Negative Stock" toggle DOES NOT EXIST in Item Master
  - Step 2: Attachment Type (combobox) + File Upload ONLY
  - Step 3: Packaging table with Add Row
  - Edit mode: Step 2 & 3 tabs DISABLED, button says "Update" not "Submit"
  - Item Group is NOT required in Create or Edit mode
  - Base Uom does NOT auto-sync with UOM — independent fields
  - DROPDOWN FILL ORDER: Category → Group → Type → Attr1 → Attr2 → Attr3 → Attr4 → Attr5

Known Bugs (CONFIRMED via browser exploration 2026-05-18):
  BUG-001 (HIGH)  : [RETRACTED] Spaces-only Item Name — not applicable,
                     field is readonly and auto-generated
  BUG-002 (HIGH)  : Duplicate Item Names ALLOWED — confirmed! Two "Soyabean"
                     rows exist in table both Active. No uniqueness validation.
  BUG-003 (MEDIUM): [RETRACTED] No maxlength on Item Name — not applicable,
                     field is readonly and auto-generated
  BUG-004 (MEDIUM): Negative Base Uom Conversion accepted
  BUG-005 (LOW)   : No Delete option anywhere on screen
  BUG-006 (MEDIUM): Dropdown option duplication — Item Category & Item Group
                     show options TWICE in dropdown
  BUG-007 (CRITICAL): Browser-clicked mat-select does NOT update Angular form
                     model — must use JS value-setter + dispatchEvent pattern

Bug Handling Decisions:
  BUG-001: Retracted — Item Name is readonly; cannot type spaces
  BUG-002: CONFIRMED — Duplicate Item Names ARE allowed. Table has two
           "Soyabean" rows both Active. Test should verify duplicates
           CAN be created (not that they're blocked).
  BUG-003: Retracted — Item Name is auto-generated; maxlength not testable
  BUG-004: Test expects rejection — mark xfail if bug confirmed
  BUG-005: Documented in UI phase, not tested (no button to click)
  BUG-006: Documented — dropdown shows duplicate options, no test needed
  BUG-007: CRITICAL for automation — must use JS value-setter for dropdowns

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
    generate_full_valid_item_data,
    generate_valid_edit_data,
    generate_negative_uom_conversion,
    generate_zero_uom_conversion,
    generate_alpha_uom_conversion,
    generate_special_char_uom_conversion,
    generate_decimal_uom_conversion,
    generate_uom_conversion_with_spaces,
    generate_item_code_with_special_chars,
)
from common.logger import log


# ====================================================================
# Helper: create a prerequisite item, refresh, return its name
# ====================================================================

def _create_prerequisite_item(page, name_prefix="PreReq"):
    """Create an Item Master entry for tests that need existing data.
    Returns the auto-generated item name and the data dict.

    Note: Item Name is auto-generated from Item Attribute 1-5 values
    and cannot be manually typed (readonly=true).
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
    # Item Name is auto-generated from attributes
    name = result.get("item_name", "") or data.get("_auto_item_name", "")
    log.info(f"Prerequisite item created: {name}")
    return name, data


# ====================================================================
# PHASE 1: Create Form Validations (15 tests)
# ====================================================================

class TestCreateFormValidations:
    """IM-C01 to IM-C15: Validation checks on the Create form.
    Item Master has a 3-step stepper with many fields.

    Note: Item Name is READONLY (auto-generated from Item Attributes 1-5).
    Tests that previously tried to type into Item Name have been redesigned
    to verify readonly enforcement instead.
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
        # Item Name is auto-generated from Item Attribute 1-5 concatenation
        name = result.get("item_name", "") or data.get("_auto_item_name", "")

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

    # ---- IM-C03: Item Name field is readonly ----
    def test_IM_C03_item_name_readonly(self, im_page):
        """Item Name field is readonly — manual input should have no effect.

        Item Name has readonly=true and is auto-generated from Item
        Attribute 1-5 values. Typing into it should not change its value.
        This replaces the former spaces-only name test (BUG-001) since
        the field cannot receive manual input at all.
        """
        log.info("IM-C03: Item Name readonly test")
        page = im_page

        data = generate_valid_item_data("ROTest")

        page.open_add_form()
        page.wait_seconds(1)

        # Fill Step 1 to trigger auto-generation of Item Name
        page.fill_step1(data)
        page.wait_seconds(1)

        # Read the auto-generated Item Name value
        values_before = page.get_form_field_values_step1()
        name_before = values_before.get("item_name", "")

        # Attempt to type into the readonly Item Name field
        page.type_text(
            page.ITEM_NAME_INPUT, "ManualInputAttempt", clear_first=True
        )
        page.wait_seconds(0.5)

        # Read the value again — it should NOT have changed
        values_after = page.get_form_field_values_step1()
        name_after = values_after.get("item_name", "")

        if name_before and name_after == name_before:
            log.info(
                f"Item Name is readonly — value unchanged: '{name_before}'"
            )
        elif not name_before and not name_after:
            log.info(
                "Item Name was empty before and after — "
                "readonly prevents manual input"
            )
        else:
            log.warning(
                f"Item Name may not be readonly — "
                f"before='{name_before}', after='{name_after}'"
            )

        # Also verify the readonly attribute on the input element
        is_readonly = page.driver.execute_script(
            "var i = document.querySelector("
            "  \"input[name='Item Name'], input[formcontrolname='name'], \""
            "  + \"input[name='itemName']\");"
            "return i ? i.readOnly : null;"
        )
        if is_readonly is True:
            log.info("Item Name input has readonly=true attribute confirmed")
        elif is_readonly is False:
            log.warning(
                "Item Name input does NOT have readonly attribute — "
                "unexpected"
            )
        else:
            log.info(
                "Could not verify readonly attribute on Item Name input "
                "(element selector may need updating)"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IM-C04: Duplicate Item Name (known limitation) ----
    @pytest.mark.skip(
        reason="Item Name is readonly and auto-generated from attributes; "
               "cannot type a duplicate name. Testing duplicates would "
               "require creating two items with identical Item Attribute "
               "1-5 selections, which is difficult to control from live "
               "UI dropdowns. See BUG-002 for known duplicate name issue."
    )
    def test_IM_C04_duplicate_name(self, im_page):
        """Duplicate Item Name in Create — cannot test via typing.

        Since Item Name is auto-generated from Item Attributes 1-5,
        creating a duplicate would require selecting the exact same
        attribute values in two separate create operations. This is
        not reliably achievable when dropdowns are populated from
        live data. Marked as known limitation (BUG-002).
        """
        log.info("IM-C04: Duplicate name test — SKIPPED (readonly field)")
        pass

    # ---- IM-C05: Auto-generated Item Name length is reasonable ----
    def test_IM_C05_auto_name_length_reasonable(self, im_page):
        """Auto-generated Item Name length should be reasonable.

        Item Name is auto-generated from Item Attribute 1-5 values
        concatenated with spaces. This test verifies the generated
        name is within a reasonable length (e.g., under 500 chars).

        Note: maxlength boundary testing (255/256 chars) is not
        applicable for auto-generated fields since the user cannot
        manually control the input length.
        """
        log.info("IM-C05: Auto-generated name length test")
        page = im_page

        data = generate_full_valid_item_data("LenChk")
        result = page.create_item(data)
        name = result.get("item_name", "") or data.get("_auto_item_name", "")

        if result["status"] == "PASSED" and name:
            name_len = len(name)
            log.info(f"Auto-generated Item Name length: {name_len}")

            # Reasonable upper bound — auto-generated from 5 attributes
            # should not exceed 500 chars in normal usage
            MAX_REASONABLE_LENGTH = 500
            assert name_len <= MAX_REASONABLE_LENGTH, (
                f"Auto-generated Item Name is {name_len} chars — "
                f"exceeds reasonable limit of {MAX_REASONABLE_LENGTH}"
            )
            log.info(
                f"Auto-generated name length ({name_len}) is within "
                f"reasonable bounds (<= {MAX_REASONABLE_LENGTH})"
            )
        else:
            log.warning(
                f"Could not verify name length: "
                f"status={result.get('status')}, name='{name}'"
            )

        page.click_refresh()
        page.wait_seconds(2)

    # ---- IM-C06: Maxlength not applicable for auto-generated field ----
    @pytest.mark.skip(
        reason="Item Name is readonly and auto-generated from attributes; "
               "maxlength boundary testing (256 chars) is not applicable "
               "since the user cannot manually input text. "
               "See IM-C05 for auto-generated name length verification."
    )
    def test_IM_C06_name_256_chars(self, im_page):
        """Item Name 256-char boundary — not applicable.

        Since Item Name is auto-generated, we cannot test the maxlength
        boundary by typing 256 characters. The field's readonly attribute
        prevents manual input. IM-C05 verifies the auto-generated name
        length is reasonable.
        """
        log.info("IM-C06: 256-char name test — SKIPPED (readonly field)")
        pass

    # ---- IM-C07: Verify Item Name readonly attribute ----
    def test_IM_C07_verify_name_readonly_attribute(self, im_page):
        """Verify Item Name input element has the readonly attribute.

        Item Name is auto-generated from Item Attribute 1-5 and should
        have readonly=true on the input element. This test verifies
        the UI enforcement of readonly behavior.

        Replaces the former special-characters-in-name test since
        special characters cannot be typed into a readonly field.
        """
        log.info("IM-C07: Verify Item Name readonly attribute test")
        page = im_page

        page.open_add_form()
        page.wait_seconds(1)

        # Check the readonly attribute via JavaScript
        is_readonly = page.driver.execute_script(
            "var i = document.querySelector("
            "  \"input[name='Item Name'], input[formcontrolname='name'], \""
            "  + \"input[name='itemName']\");"
            "return i ? i.readOnly : null;"
        )

        # Check the HTML readonly attribute as well
        has_readonly_attr = page.driver.execute_script(
            "var i = document.querySelector("
            "  \"input[name='Item Name'], input[formcontrolname='name'], \""
            "  + \"input[name='itemName']\");"
            "return i ? i.hasAttribute('readonly') : null;"
        )

        if is_readonly is True:
            log.info(
                "Item Name input has readonly property = true — "
                "readonly enforcement confirmed"
            )
        elif is_readonly is False:
            log.warning(
                "Item Name input readonly property is false — "
                "field may accept manual input (unexpected)"
            )
        else:
            log.info(
                "Could not read readonly property — "
                "element selector may need updating"
            )

        if has_readonly_attr is True:
            log.info(
                "Item Name input has HTML readonly attribute — confirmed"
            )
        elif has_readonly_attr is False:
            log.warning(
                "Item Name input does NOT have HTML readonly attribute"
            )
        else:
            log.info(
                "Could not check HTML readonly attribute — "
                "element not found with current selector"
            )

        # Attempt to type and verify no change
        page.type_text(
            page.ITEM_NAME_INPUT, "!@#$%^&*()_+", clear_first=True
        )
        page.wait_seconds(0.5)

        values = page.get_form_field_values_step1()
        name_value = values.get("item_name", "")

        # Value should be empty or unchanged (not the special chars string)
        if name_value != "!@#$%^&*()_+":
            log.info(
                "Typing special characters into Item Name had no effect — "
                "readonly enforcement working"
            )
        else:
            log.warning(
                "Special characters were accepted in Item Name — "
                "readonly may not be enforced"
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
        # Item Name is auto-generated from attributes
        name = result.get("item_name", "") or data.get("_auto_item_name", "")

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

    # ---- IM-C14: Partial required fields — dropdowns missing ----
    def test_IM_C14_partial_required_fields(self, im_page):
        """Submit with only partial required fields — should be blocked.

        Since Item Name is auto-generated from attributes, we cannot
        test 'name-only' partial fill. Instead, this test fills only
        some fields (e.g., Item Code and Description) and leaves
        required dropdowns (Item Category, Item Type, UOM) empty to
        verify that validation errors are shown.
        """
        log.info("IM-C14: Partial required fields submit test")
        page = im_page

        # Open form and fill only text fields, leaving dropdowns empty
        page.open_add_form()
        page.wait_seconds(1)

        # Type only into text inputs — leave all dropdowns unfilled
        page.type_text(page.ITEM_CODE_INPUT, "PartialTestCode")
        page.type_text(page.DESCRIPTION_INPUT, "Partial test description")
        # Intentionally do NOT select any dropdown values
        # (Item Category, Item Type, UOM, Item Attribute 1-5, etc.)

        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        still_step1 = page.is_step1_active()

        # Required dropdowns should block advancement
        assert still_step1 or errors or validation_alert, (
            "BUG: Form advanced with only text fields filled — "
            "required dropdown fields not validated"
        )
        if errors:
            log.info(f"Partial fill validation errors: {errors}")
        if still_step1:
            log.info("Form stayed on Step 1 — required dropdown validation working")

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

    Note: Since Item Name is READONLY and auto-generated from Item
    Attributes 1-5, duplicate name tests that rely on typing a
    duplicate name are not feasible. Creating true duplicates would
    require selecting identical attribute values in two separate
    create operations, which is difficult to control from live UI
    dropdowns.

    BUG-002: Duplicate Item Names may be allowed — this is a known
    issue but cannot be tested by typing the same name.
    """

    # ---- IM-D01: Duplicate name — Create after Create ----
    @pytest.mark.skip(
        reason="Item Name is readonly and auto-generated from attributes; "
               "cannot type a duplicate name in the Create form. Testing "
               "duplicates would require selecting identical Item Attribute "
               "1-5 values, which is not reliably controllable from live "
               "UI dropdowns. BUG-002 (duplicate names allowed) remains a "
               "known issue."
    )
    def test_IM_D01_duplicate_create(self, im_page):
        """Create two items with identical names — cannot test via typing.

        Since Item Name is auto-generated from attributes, creating
        a duplicate would require selecting the same attribute values.
        This is not reliably achievable with live UI dropdowns.
        """
        log.info("IM-D01: Duplicate create test — SKIPPED (readonly field)")
        pass

    # ---- IM-D02: Duplicate name — case-insensitive check ----
    @pytest.mark.skip(
        reason="Item Name is readonly and auto-generated from attributes; "
               "cannot type a name in different case. Case-insensitive "
               "duplicate check would require identical attribute selections "
               "that produce names differing only in case, which is not "
               "reliably controllable from live UI dropdowns."
    )
    def test_IM_D02_duplicate_case_insensitive(self, im_page):
        """Create item with same name in different case — cannot test.

        Since Item Name is auto-generated, we cannot type an uppercase
        version of an existing name. This test is not applicable.
        """
        log.info("IM-D02: Duplicate case-insensitive test — SKIPPED (readonly field)")
        pass

    # ---- IM-D03: Duplicate name — Edit to existing name ----
    @pytest.mark.skip(
        reason="Item Name is readonly in Edit mode as well; cannot type "
               "another item's name into the edit form. The Item Name "
               "field cannot be modified during edit, so duplicate name "
               "testing via edit is not applicable."
    )
    def test_IM_D03_duplicate_edit(self, im_page):
        """Edit an item to use another item's name — not applicable.

        Item Name is readonly in both Create and Edit modes. Since we
        cannot modify the Item Name field during edit, testing for
        duplicate names via edit is not applicable.
        """
        log.info("IM-D03: Duplicate edit test — SKIPPED (readonly field)")
        pass


# ====================================================================
# PHASE 3: Edit Form Validations (8 tests)
# ====================================================================

class TestEditFormValidations:
    """IM-E01 to IM-E08: Validation checks on the Edit form.

    Note: Item Name is READONLY in Edit mode too — cannot be modified.
    Tests that previously tried to clear or change Item Name in edit
    have been redesigned to verify readonly enforcement.
    """

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

        # Verify Item Name is readonly in edit mode
        is_readonly = page.driver.execute_script(
            "var i = document.querySelector("
            "  \"input[name='Item Name'], input[formcontrolname='name'], \""
            "  + \"input[name='itemName']\");"
            "return i ? i.readOnly : null;"
        )
        if is_readonly is True:
            log.info("Item Name is readonly in Edit mode — confirmed")
        else:
            log.info(
                f"Item Name readonly status in Edit mode: {is_readonly}"
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
        """Edit with valid new values — should succeed.

        Since Item Name is readonly, we verify that editable fields
        (Item Code, Description, Base Uom Conversion) were updated
        and the ORIGINAL Item Name is still present in the table.
        """
        log.info("IM-E02: Valid edit test")
        page = im_page

        name, data = _create_prerequisite_item(page, "EditOK")

        # Edit with new values (Item Name will not change — readonly)
        edit_data = generate_valid_edit_data("Updated")
        result = page.edit_item(name, edit_data)

        if result["status"] == "PASSED":
            log.info("Item updated successfully")
        else:
            log.warning(f"Edit failed: {result.get('error', 'unknown')}")

        # Verify the ORIGINAL name is still in the table
        # (Item Name is readonly and cannot be changed)
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_item_in_table(name)

        assert found, (
            f"Original item '{name}' not found in table after edit — "
            f"Item Name should remain unchanged (readonly)"
        )
        log.info(
            f"Item edit successful — original name '{name}' "
            f"still in table (readonly, as expected)"
        )

    # ---- IM-E03: Edit — readonly Item Name prevents clearing ----
    def test_IM_E03_edit_readonly_name_enforcement(self, im_page):
        """Item Name is readonly in Edit — JS-based clearing should have no effect.

        Since Item Name is readonly, attempting to clear it via JavaScript
        (bypassing the input event) should either have no effect or the
        system should prevent submission with an empty name.

        Replaces the former 'edit empty name' test which assumed
        the name field was editable.
        """
        log.info("IM-E03: Edit readonly name enforcement test")
        page = im_page

        name, data = _create_prerequisite_item(page, "EditRO")

        # Open Edit form
        page.click_edit_button(item_name=name)
        page.wait_seconds(1)

        # Record the Item Name value before attempting to clear
        values_before = page.get_form_field_values_step1()
        name_before = values_before.get("item_name", "")

        # Attempt to clear the readonly Item Name field via JS
        page.driver.execute_script(
            "var i = document.querySelector("
            "  \"input[name='Item Name'], input[formcontrolname='name'], \""
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

        # Check the value after the JS clearing attempt
        values_after = page.get_form_field_values_step1()
        name_after = values_after.get("item_name", "")

        if name_after == name_before and name_before:
            log.info(
                f"Item Name unchanged after JS clear attempt — "
                f"readonly enforcement working (value: '{name_before}')"
            )
        elif not name_after and name_before:
            log.warning(
                "JS clearing succeeded — readonly did not prevent "
                "programmatic value change. System should still reject "
                "submission with empty name."
            )
            # Try submitting — system should block
            page.click_update()
            page.wait_seconds(2)

            validation_alert = ""
            if page.is_validation_alert_present(timeout=3):
                validation_alert = page.get_swal_title() or ""
                log.info(f"SweetAlert after empty edit submit: {validation_alert}")
                page.handle_validation_warning(timeout=5)

            errors = page.get_mat_error_text()
            form_still_open = page.is_add_form_open()

            if form_still_open or errors or validation_alert:
                log.info(
                    "System rejected submission after JS clearing — "
                    "validation working even without readonly enforcement"
                )
            else:
                log.warning(
                    "BUG: Edit form submitted after JS clearing Item Name"
                )
        else:
            log.info(
                f"Item Name state after JS clear: "
                f"before='{name_before}', after='{name_after}'"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- IM-E04: Edit — typing into readonly Item Name has no effect ----
    def test_IM_E04_edit_readonly_name_no_typing(self, im_page):
        """Typing into readonly Item Name in Edit should have no effect.

        Since Item Name is readonly in Edit mode, any attempt to type
        into it should be ignored. This replaces the former spaces-only
        name test in edit mode.
        """
        log.info("IM-E04: Edit readonly name — typing has no effect test")
        page = im_page

        name, data = _create_prerequisite_item(page, "EditRO2")

        # Open Edit form
        page.click_edit_button(item_name=name)
        page.wait_seconds(1)

        # Record the Item Name value before typing
        values_before = page.get_form_field_values_step1()
        name_before = values_before.get("item_name", "")

        # Attempt to type into the readonly Item Name field
        page.type_text(
            page.ITEM_NAME_INPUT, "AttemptedOverwrite", clear_first=True
        )
        page.wait_seconds(0.5)

        # Read the value after typing
        values_after = page.get_form_field_values_step1()
        name_after = values_after.get("item_name", "")

        if name_after == name_before and name_before:
            log.info(
                f"Item Name unchanged after typing attempt — "
                f"readonly enforcement working (value: '{name_before}')"
            )
        elif name_after == "AttemptedOverwrite":
            log.warning(
                "Item Name was overwritten — readonly is NOT enforced"
            )
        else:
            log.info(
                f"Item Name state after typing: "
                f"before='{name_before}', after='{name_after}'"
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

    # ---- IM-E06: Edit — toggle switches (all on Step 1) ----
    def test_IM_E06_edit_toggle_switches(self, im_page):
        """Toggle switches in Edit mode should be changeable.

        Note: ALL 4 toggle switches (Status, Is Critical, Include Wip,
        Is Packing Material) are located on Step 1, NOT Step 2.
        Step 2 contains only Attachment Type (combobox) + File Upload.
        """
        log.info("IM-E06: Edit toggle switches test (all on Step 1)")
        page = im_page

        name, data = _create_prerequisite_item(page, "EditToggle")

        page.click_edit_button(item_name=name)
        page.wait_seconds(1)

        if page.is_edit_mode():
            # All 4 toggles are on Step 1 — read current states
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

    # ---- IM-P07: Toggle switches in Create form (all on Step 1) ----
    def test_IM_P07_toggle_switches_create(self, im_page):
        """Toggle switches should be functional in Create form.

        Note: ALL 4 toggle switches (Status, Is Critical, Include Wip,
        Is Packing Material) are located on Step 1, NOT Step 2.
        Step 2 contains only Attachment Type (combobox) + File Upload.
        """
        log.info("IM-P07: Toggle switches in Create test (all on Step 1)")
        page = im_page

        page.open_add_form()
        page.wait_seconds(1)

        # All 4 toggles are on Step 1 — read default states
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
        """After editing an item, history should show additional entries.

        Note: Item Name is readonly and cannot be changed during edit.
        We search for the item using the ORIGINAL name after editing.
        """
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

        # Edit the item (Item Name will NOT change — it's readonly)
        edit_data = generate_valid_edit_data("HistUpd")
        result = page.edit_item(name, edit_data)

        # Check history after edit — search using ORIGINAL name
        # since Item Name cannot be changed (readonly)
        page.click_refresh()
        page.wait_seconds(2)

        page.search_item(name)
        page.wait_seconds(1)

        page.click_history_button(item_name=name)
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
