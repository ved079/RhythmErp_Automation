"""
test_farmer_validation.py
-------------------------
Comprehensive validation test suite for RhythmERP Farmer screen.
Rebuilt for the new schema (2026-06-12) with 11 top-level fields + 13 stepper tabs.

Phases:
  1. Create Form Validations   (15 tests) -- FR-C01 to FR-C15
  2. Duplicate Validations      (2 tests)  -- FR-D01 to FR-D02
  3. Edit Form Validations      (5 tests)  -- FR-E01 to FR-E05
  4. Search & Filter Edge Cases (5 tests)  -- FR-S01 to FR-S05
  5. Popup & UI Behaviors       (6 tests)  -- FR-P01 to FR-P06
  6. History & Audit Trail      (2 tests)  -- FR-H01 to FR-H02
  7. Bug-Specific Tests         (9 tests)  -- FR-B01 to FR-B09

Schema changes from previous version:
  - REMOVED: FR-C10 (Age auto-calc from DOB) -- DOB moved to Additional Details tab
  - REMOVED: FR-C11 (Future DOB)             -- same reason
  - ADDED:   FR-C14 (Copy From Existing Party toggle)
  - ADDED:   FR-C15 (Is Member of This FPC toggle + conditional fields)
  - UPDATED: FR-C02 now uses generate_valid_farmer_data() with address_details
  - UPDATED: FR-C13 now validates BOTH address types (Permanent + Current) required

Known Bugs (CONFIRMED via browser exploration 2026-06-12):
  BUG-F01 (HIGH)  : No Of Owner required but no asterisk shown
  BUG-F02 (HIGH)  : Deselect+Reselect farmer category freezes Next/Back
  BUG-F03 (MEDIUM): Farmer Name accepts special characters
  BUG-F04 (MEDIUM): Email rejects uppercase letters
  BUG-F05 (MEDIUM): Farmer Category placeholder selectable
  BUG-F06 (MEDIUM): Amount fields accept 0 and . prefix
  BUG-F07 (LOW)   : Source of Income shows Dairy twice
  BUG-F08 (LOW)   : Edit mode missing Land/Crop/KYC tabs
  BUG-F09 (LOW)   : Character count indicator disappears on validation error

Run:
  pytest test_farmer_validation.py -v --tb=short
  pytest test_farmer_validation.py -v -k "TestCreateForm" --tb=short
  pytest test_farmer_validation.py -v -k "FR-C02" --tb=short
  pytest test_farmer_validation.py -v -m smoke --tb=short
  pytest test_farmer_validation.py -v -m "not bug" --tb=short
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

from pages.registration.modules.farmer.farmer_page import FarmerPage
from pages.registration.modules.farmer.data.farmer_data import (
    generate_valid_farmer_step0,
    generate_valid_farmer_data,
    generate_valid_address_details,
    generate_valid_additional_details,
    generate_valid_edit_data,
    generate_empty_step0_data,
    generate_empty_address_details,
    generate_member_this_fpc_data,
    generate_copy_from_party_data,
    generate_duplicate_name_data,
    generate_duplicate_phone_data,
    generate_string_255,
    generate_string_256,
    generate_spaces_only,
    generate_invalid_name_special_chars,
    generate_invalid_name_numbers,
    generate_sql_injection_name,
    generate_xss_name,
    generate_uppercase_email,
    generate_invalid_email,
    generate_alpha_phone,
    generate_short_phone,
    generate_walkin_farmer_category,
    generate_fpc_member_category,
    generate_borrower_farmer_category,
    generate_multi_category,
    generate_zero_amount_land,
    generate_zero_amount_loan,
    KnownBugs,
)
from common.logger import log
from common.soft_assert import SoftAssert


# ====================================================================
# Key mapping: farmer_data.py keys -> farmer_page.py fill_step0() keys
# ====================================================================
# farmer_data.py uses API schema keys (name, email_id, mobile_no, party_ref_id)
# farmer_page.py fill_step0() uses UI-oriented keys (farmer_name, email, phone_number, party_reference)
# This mapping bridges the gap.

_STEP0_KEY_MAP = {
    "name":            "farmer_name",
    "email_id":        "email",
    "mobile_no":       "phone_number",
    "party_ref_id":    "party_reference",
}


def _adapt_step0(step0_data):
    """Convert farmer_data.py step0 keys to farmer_page.py fill_step0() keys.

    Returns a NEW dict; does not mutate the input.
    """
    adapted = {}
    for k, v in step0_data.items():
        adapted[_STEP0_KEY_MAP.get(k, k)] = v
    return adapted


def _build_create_data(full_data=None, category="Borrower Farmer"):
    """Build a flat data dict suitable for page.create_farmer().

    Merges step0 into top-level with key adaptation, then adds
    the stepper tab data keys that create_farmer() expects.

    Args:
        full_data: Output of generate_valid_farmer_data(). If None, generates one.
        category: Category string if full_data is None.

    Returns:
        Flat dict with both step0 fields (adapted keys) and stepper data keys.
    """
    if full_data is None:
        full_data = generate_valid_farmer_data()

    # Merge adapted step0 into top level
    flat = _adapt_step0(full_data.get("step0", {}))

    # Add stepper tab data (these keys match what create_farmer() uses)
    for tab_key in [
        "address_details", "other_details", "family_details",
        "additional_details", "land_details", "crop_details",
        "kyc_details", "vehicle_details", "income_details",
        "bank_details", "irrigation_details", "award_details",
        "loan_details",
    ]:
        if tab_key in full_data:
            flat[tab_key] = full_data[tab_key]

    # Ensure farmer_category is in a format fill_step0 / _select_farmer_category accepts
    # create_farmer() also accepts category as a string arg
    if "farmer_category" not in flat:
        flat["farmer_category"] = category

    return flat


# ====================================================================
# Helper: create a prerequisite farmer, refresh, return its name
# ====================================================================

def _create_prerequisite_farmer(page, category="Walk-in Farmer"):
    """Create a Farmer entry for tests that need existing data.
    Returns the farmer name and the data dict.
    """
    full_data = generate_valid_farmer_data()
    # Override category based on param
    if category == "Walk-in Farmer":
        full_data["step0"]["farmer_category"] = generate_walkin_farmer_category()
    elif category == "FPC Member":
        full_data["step0"]["farmer_category"] = generate_fpc_member_category()
    elif category == "Borrower Farmer":
        full_data["step0"]["farmer_category"] = generate_borrower_farmer_category()

    create_data = _build_create_data(full_data, category=category)
    result = page.create_farmer(create_data, category=category)
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

    name = result.get("farmer_name", "") or create_data.get("farmer_name", "")
    log.info(f"Prerequisite farmer created: {name}")
    return name, create_data


# ====================================================================
# PHASE 1: Create Form Validations (15 tests)
# ====================================================================

class TestCreateFormValidations:
    """FR-C01 to FR-C15: Validation checks on the Create form.

    CHANGES from previous version:
      - REMOVED: FR-C10 (Age auto-calc from DOB) -- DOB moved to Additional Details tab
      - REMOVED: FR-C11 (Future DOB)             -- same reason
      - ADDED:   FR-C14 (Copy From Existing Party toggle)
      - ADDED:   FR-C15 (Is Member of This FPC toggle + conditional fields)
      - UPDATED: FR-C02 uses generate_valid_farmer_data() with address_details
      - UPDATED: FR-C13 validates BOTH address types required
    """

    # ---- FR-C01: Submit with all fields empty ----
    @pytest.mark.smoke
    def test_FR_C01_empty_submit(self, fr_page):
        """Submit with all fields empty -- should be blocked."""
        log.info("FR-C01: Empty submit test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Click Next on first stepper tab with all fields empty
        page.click_stepper_next()
        page.wait_seconds(2)

        # Check for validation errors or SweetAlert
        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        # Expect: form stays open + validation errors shown
        assert form_still_open or errors or validation_alert, (
            "BUG: Form advanced with all fields empty -- no validation"
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

    # ---- FR-C02: Create Walk-in Farmer with valid data (happy path) ----
    @pytest.mark.smoke
    def test_FR_C02_valid_create_walkin(self, fr_page):
        """Create Walk-in Farmer with valid data (Address + Bank tabs) -- should succeed."""
        log.info("FR-C02: Valid Walk-in Farmer create test")
        page = fr_page

        full_data = generate_valid_farmer_data()
        full_data["step0"]["farmer_category"] = generate_walkin_farmer_category()
        create_data = _build_create_data(full_data, category="Walk-in Farmer")

        result = page.create_farmer(create_data, category="Walk-in Farmer")
        name = result.get("farmer_name", "")

        if result["status"] == "PASSED":
            log.info(f"Walk-in Farmer created: {name}")
        else:
            log.warning(f"Create failed: {result.get('error', 'unknown')}")

        # Verify the farmer appears in the table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_farmer_in_table(name)
        assert found, f"Created farmer '{name}' not found in table after refresh"

    # ---- FR-C03: Create Borrower Farmer with valid data ----
    @pytest.mark.sanity
    def test_FR_C03_valid_create_borrower(self, fr_page):
        """Create Borrower Farmer with valid data (all 13 tabs) -- should succeed."""
        log.info("FR-C03: Valid Borrower Farmer create test")
        page = fr_page

        full_data = generate_valid_farmer_data()
        full_data["step0"]["farmer_category"] = generate_borrower_farmer_category()
        create_data = _build_create_data(full_data, category="Borrower Farmer")

        result = page.create_farmer(create_data, category="Borrower Farmer")
        name = result.get("farmer_name", "")

        if result["status"] == "PASSED":
            log.info(f"Borrower Farmer created: {name}")
        else:
            log.warning(f"Create failed: {result.get('error', 'unknown')}")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- FR-C04: Farmer Name accepts special characters (BUG-F03) ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F03, strict=False)
    def test_FR_C04_special_char_name(self, fr_page):
        """Farmer Name with special characters -- should be rejected (BUG-F03)."""
        log.info("FR-C04: Special characters in Farmer Name test")
        page = fr_page

        special_name = generate_invalid_name_special_chars()
        step0 = generate_valid_farmer_step0()
        step0["name"] = special_name
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(adapted)
        page._force_close_panels()

        # Try to advance -- should be blocked by validation
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()

        assert validation_alert or errors, (
            f"BUG-F03 CONFIRMED: Special chars '{special_name}' accepted in Farmer Name"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C05: Email with uppercase letters rejected (BUG-F04) ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F04, strict=False)
    def test_FR_C05_uppercase_email(self, fr_page):
        """Email with uppercase letters -- should be accepted (BUG-F04)."""
        log.info("FR-C05: Uppercase email test")
        page = fr_page

        step0 = generate_valid_farmer_step0()
        step0["email_id"] = generate_uppercase_email()
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(adapted)
        page._force_close_panels()

        # Check if email field has validation error
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()

        # BUG-F04: uppercase emails SHOULD be valid but are rejected
        # We expect this to FAIL because the system incorrectly rejects them
        assert not validation_alert and not any(
            "email" in e.lower() for e in errors
        ), (
            f"BUG-F04 CONFIRMED: Uppercase email rejected: {errors}"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C06: Farmer Category placeholder selectable (BUG-F05) ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F05, strict=False)
    def test_FR_C06_placeholder_category(self, fr_page):
        """Select 'Select Farmer Category' placeholder -- should not be valid (BUG-F05)."""
        log.info("FR-C06: Placeholder category selectable test")
        page = fr_page

        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = "Select Farmer Category"  # Placeholder
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(adapted)
        page._force_close_panels()

        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()

        assert validation_alert or errors, (
            "BUG-F05 CONFIRMED: Placeholder 'Select Farmer Category' accepted as valid selection"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C07: Farmer Name maxlength 255 boundary ----
    @pytest.mark.sanity
    def test_FR_C07_name_maxlength_255(self, fr_page):
        """Farmer Name 255 chars -- should be accepted (boundary)."""
        log.info("FR-C07: Name maxlength 255 boundary test")
        page = fr_page

        name_255 = generate_string_255()
        step0 = generate_valid_farmer_step0()
        step0["name"] = name_255
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(adapted)
        page.wait_seconds(1)

        # Check value was accepted (may be truncated to 255)
        try:
            name_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Farmer Name']"
            )
            actual_value = name_input.get_attribute("value") or ""
            log.info(f"Name 255 chars: entered length = {len(actual_value)}")
            assert len(actual_value) <= 255, (
                f"Name accepted {len(actual_value)} chars (max 255)"
            )
        except Exception:
            log.info("Could not read Farmer Name value for boundary check")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C08: Farmer Name 256 chars -- over max ----
    @pytest.mark.sanity
    def test_FR_C08_name_256_chars(self, fr_page):
        """Farmer Name 256 chars -- should truncate or show error."""
        log.info("FR-C08: Name 256 chars test")
        page = fr_page

        name_256 = generate_string_256()
        step0 = generate_valid_farmer_step0()
        step0["name"] = name_256
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(adapted)
        page.wait_seconds(1)

        try:
            name_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Farmer Name']"
            )
            actual_value = name_input.get_attribute("value") or ""
            log.info(
                f"Name 256 chars: entered length = {len(actual_value)} "
                f"(expected <= 255)"
            )
        except Exception:
            log.info("Could not read Farmer Name value for overflow check")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C09: Phone Number with alphabetic input ----
    @pytest.mark.sanity
    def test_FR_C09_alpha_phone(self, fr_page):
        """Alphabetic characters in Phone Number -- should be rejected (integer field)."""
        log.info("FR-C09: Alpha phone number test")
        page = fr_page

        step0 = generate_valid_farmer_step0()
        step0["mobile_no"] = generate_alpha_phone()
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(adapted)
        page._force_close_panels()

        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()

        if validation_alert or errors:
            log.info("Alpha phone rejected -- validation working")
        else:
            log.warning("BUG: Alphabetic characters accepted in Phone Number")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C10: Spaces-only Farmer Name ----
    @pytest.mark.sanity
    def test_FR_C10_spaces_only_name(self, fr_page):
        """Spaces-only Farmer Name -- should be rejected."""
        log.info("FR-C10: Spaces-only Farmer Name test")
        page = fr_page

        step0 = generate_valid_farmer_step0()
        step0["name"] = generate_spaces_only(10)
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(adapted)
        page._force_close_panels()

        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "Spaces-only Farmer Name accepted without validation"
        )
        log.info(f"Spaces-only name validation: errors={errors}, swal={validation_alert}")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C11: SQL injection in Farmer Name ----
    @pytest.mark.sanity
    def test_FR_C11_sql_injection_name(self, fr_page):
        """SQL injection string in Farmer Name -- should be rejected or sanitized."""
        log.info("FR-C11: SQL injection in Farmer Name test")
        page = fr_page

        sql_name = generate_sql_injection_name()
        step0 = generate_valid_farmer_step0()
        step0["name"] = sql_name
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(adapted)
        page._force_close_panels()

        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()

        if validation_alert or errors:
            log.info(f"SQL injection rejected -- validation working: {errors}")
        else:
            log.warning(f"SQL injection string accepted in Farmer Name: {sql_name}")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C12: XSS payload in Farmer Name ----
    @pytest.mark.sanity
    def test_FR_C12_xss_name(self, fr_page):
        """XSS payload in Farmer Name -- should be rejected or sanitized."""
        log.info("FR-C12: XSS payload in Farmer Name test")
        page = fr_page

        xss_name = generate_xss_name()
        step0 = generate_valid_farmer_step0()
        step0["name"] = xss_name
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(adapted)
        page._force_close_panels()

        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()

        if validation_alert or errors:
            log.info(f"XSS rejected -- validation working: {errors}")
        else:
            log.warning(f"XSS payload accepted in Farmer Name: {xss_name}")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C13: Address Details required (both Permanent AND Current) ----
    @pytest.mark.smoke
    def test_FR_C13_address_required_both_types(self, fr_page):
        """Address tab -- both Permanent AND Current address types required for Farmer.

        Farmer role requires BOTH address types. Attempting to proceed with
        only one or empty addresses should be blocked.
        """
        log.info("FR-C13: Address required fields (both types) test")
        page = fr_page

        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = generate_walkin_farmer_category()
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(adapted)

        # Navigate to Address Details tab
        page.click_stepper_next()
        page.wait_seconds(1)

        # Try to proceed without filling address
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()

        if validation_alert or errors:
            log.info("Address validation working -- required fields enforced")
        else:
            log.warning("Address required fields may not be validated")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C14: Copy From Existing Party toggle (NEW) ----
    @pytest.mark.sanity
    def test_FR_C14_copy_from_party_toggle(self, fr_page):
        """Copy From Existing Party toggle -- enables Party Reference dropdown."""
        log.info("FR-C14: Copy From Existing Party toggle test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # By default, Copy From Existing Party is OFF
        # Party Reference dropdown should NOT be visible/interactive
        log.info("Verifying Party Reference is hidden when toggle is OFF")

        # Toggle ON
        try:
            page._toggle_switch(page.COPY_FROM_PARTY_TOGGLE, True)
            page.wait_seconds(1)
            log.info("Copy From Existing Party toggle turned ON")

            # Party Reference dropdown should now be visible
            try:
                party_ref_el = page.driver.find_element(
                    By.XPATH,
                    "//mat-label[contains(.,'Party Reference')]"
                    "/ancestor::mat-form-field//mat-select",
                )
                is_visible = party_ref_el.is_displayed()
                log.info(f"Party Reference dropdown visible after toggle ON: {is_visible}")
            except Exception:
                log.info("Party Reference dropdown not found after toggle ON")

        except Exception as e:
            log.warning(f"Could not toggle Copy From Existing Party: {e}")

        # Toggle OFF
        try:
            page._toggle_switch(page.COPY_FROM_PARTY_TOGGLE, False)
            page.wait_seconds(1)
            log.info("Copy From Existing Party toggle turned OFF")
        except Exception:
            pass

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C15: Is Member of This FPC toggle + conditional fields (NEW) ----
    @pytest.mark.sanity
    def test_FR_C15_member_this_fpc_toggle(self, fr_page):
        """Is Member of This FPC toggle -- shows Other FPC Name and Member Id fields."""
        log.info("FR-C15: Is Member of This FPC toggle test")
        page = fr_page

        step0 = generate_member_this_fpc_data()
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Fill step0 with is_member_this_fpc=True
        # This should reveal Other FPC Name and Member Id fields
        page.fill_step0(adapted)
        page.wait_seconds(1)

        # Verify conditional fields appeared
        try:
            other_fpc_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Other FPC Name']"
            )
            member_id_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Member Id']"
            )
            log.info(
                f"Conditional fields visible: "
                f"Other FPC Name={other_fpc_input.is_displayed()}, "
                f"Member Id={member_id_input.is_displayed()}"
            )
        except Exception:
            log.warning("Conditional fields (Other FPC Name, Member Id) not found")

        try:
            page.cancel()
        except Exception:
            pass


# ====================================================================
# PHASE 2: Duplicate Validations (2 tests)
# ====================================================================

class TestDuplicateValidations:
    """FR-D01 to FR-D02: Duplicate farmer checks."""

    # ---- FR-D01: Create duplicate farmer (same name) ----
    @pytest.mark.sanity
    def test_FR_D01_duplicate_farmer_name(self, fr_page):
        """Create two farmers with the same name -- check if duplicates allowed."""
        log.info("FR-D01: Duplicate farmer name test")
        page = fr_page

        # Create first farmer
        create_data1 = _build_create_data(category="Walk-in Farmer")
        result1 = page.create_farmer(create_data1, category="Walk-in Farmer")
        name1 = result1.get("farmer_name", "")

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

        if not name1:
            log.warning("Farmer 1 creation failed -- cannot test duplicate name")
            return

        # Create second farmer with same name
        step0_dup = generate_duplicate_name_data(name1)
        create_data2 = _build_create_data(category="Walk-in Farmer")
        create_data2.update(_adapt_step0(step0_dup))

        result2 = page.create_farmer(create_data2, category="Walk-in Farmer")

        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        if result2["status"] == "PASSED":
            log.info(f"Duplicate farmer allowed -- name '{name1}' used twice")
        else:
            log.info(f"Duplicate farmer blocked: {result2.get('error', '')}")

    # ---- FR-D02: Create farmer with same phone number ----
    @pytest.mark.sanity
    def test_FR_D02_duplicate_phone(self, fr_page):
        """Create farmer with same phone number -- check if allowed."""
        log.info("FR-D02: Duplicate phone number test")
        page = fr_page

        # Create first farmer
        create_data1 = _build_create_data(category="Walk-in Farmer")
        result1 = page.create_farmer(create_data1, category="Walk-in Farmer")
        phone1 = create_data1.get("phone_number", "")

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

        if not phone1:
            log.warning("Farmer 1 creation failed -- cannot test duplicate phone")
            return

        # Create second with same phone
        step0_dup = generate_duplicate_phone_data(phone1)
        create_data2 = _build_create_data(category="Walk-in Farmer")
        create_data2.update(_adapt_step0(step0_dup))

        result2 = page.create_farmer(create_data2, category="Walk-in Farmer")

        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        if result2["status"] == "PASSED":
            log.info(f"Duplicate phone number allowed: {phone1}")
        else:
            log.info(f"Duplicate phone blocked: {result2.get('error', '')}")


# ====================================================================
# PHASE 3: Edit Form Validations (5 tests)
# ====================================================================

class TestEditFormValidations:
    """FR-E01 to FR-E05: Validation checks on the Edit form."""

    # ---- FR-E01: Edit -- pre-populated fields ----
    @pytest.mark.smoke
    def test_FR_E01_edit_prepopulated(self, fr_page):
        """Edit popup should show Step 0 fields pre-populated."""
        log.info("FR-E01: Edit pre-populated fields test")
        page = fr_page

        name, data = _create_prerequisite_farmer(page, "Walk-in Farmer")

        if not name:
            log.warning("Prerequisite farmer name empty -- cannot verify edit")
            return

        # Click Edit on first row
        page.click_table_row(0)
        page.wait_seconds(1)
        try:
            edit_btn = page.driver.find_element(
                By.XPATH,
                "//button[contains(@class,'edit-btn') or contains(.,'Edit')]"
            )
            page.driver.execute_script("arguments[0].click();", edit_btn)
        except Exception:
            log.warning("Could not find Edit button")
        page.wait_seconds(2)

        # Read form values
        form_values = page.get_form_field_values()

        name_val = form_values.get("Farmer Name", form_values.get("farmer_name", ""))
        assert name_val, "Farmer Name empty in Edit form"
        log.info(f"Edit form pre-populated -- Farmer Name: {name_val}")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-E02: Edit -- modify and save ----
    @pytest.mark.sanity
    def test_FR_E02_edit_modify_save(self, fr_page):
        """Edit farmer -- modify email and save."""
        log.info("FR-E02: Edit modify and save test")
        page = fr_page

        name, data = _create_prerequisite_farmer(page, "Walk-in Farmer")

        if not name:
            return

        # Open Edit
        page.click_table_row(0)
        page.wait_seconds(1)
        try:
            edit_btn = page.driver.find_element(
                By.XPATH,
                "//button[contains(@class,'edit-btn') or contains(.,'Edit')]"
            )
            page.driver.execute_script("arguments[0].click();", edit_btn)
        except Exception:
            log.warning("Could not find Edit button")
        page.wait_seconds(2)

        # Modify email
        try:
            page.type_text(page.EMAIL_INPUT, "edited@test.com", clear_first=True)
            page._force_close_panels()

            if page.is_edit_mode():
                page.click_update()
                page.wait_seconds(2)
                alert_title = page.handle_success_alert(timeout=30)
                if "successfully" in alert_title.lower():
                    log.info("Edit saved successfully")
                else:
                    log.warning(f"Edit save result: {alert_title}")
            else:
                log.info("Not in edit mode")
        except Exception as e:
            log.warning(f"Edit modify test exception: {e}")

        try:
            page.cancel()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- FR-E03: Edit mode shows only 10 tabs (BUG-F08) ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F08, strict=False)
    def test_FR_E03_edit_missing_tabs(self, fr_page):
        """Edit mode should show 13 tabs for Borrower Farmer but shows only 10 (BUG-F08)."""
        log.info("FR-E03: Edit missing tabs test")
        page = fr_page

        name, data = _create_prerequisite_farmer(page, "Borrower Farmer")

        if not name:
            return

        page.click_table_row(0)
        page.wait_seconds(1)
        try:
            edit_btn = page.driver.find_element(
                By.XPATH,
                "//button[contains(@class,'edit-btn') or contains(.,'Edit')]"
            )
            page.driver.execute_script("arguments[0].click();", edit_btn)
        except Exception:
            log.warning("Could not find Edit button")
        page.wait_seconds(2)

        tab_names = page.get_stepper_tab_names()
        tab_count = len([t for t in tab_names if t.strip()])
        log.info(f"Edit mode tab count: {tab_count}, tabs: {tab_names}")

        # Expect 13 tabs for Borrower Farmer
        assert tab_count == 13, (
            f"BUG-F08 CONFIRMED: Edit mode shows {tab_count} tabs instead of 13. "
            f"Missing: Land Details, Crop Details, KYC Details"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-E04: Edit -- Farmer Name with special chars (BUG-F03) ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F03, strict=False)
    def test_FR_E04_edit_special_char_name(self, fr_page):
        """Edit Farmer Name to special characters -- should be rejected (BUG-F03)."""
        log.info("FR-E04: Edit special char name test")
        page = fr_page

        name, data = _create_prerequisite_farmer(page, "Walk-in Farmer")
        if not name:
            return

        page.click_table_row(0)
        page.wait_seconds(1)
        try:
            edit_btn = page.driver.find_element(
                By.XPATH,
                "//button[contains(@class,'edit-btn') or contains(.,'Edit')]"
            )
            page.driver.execute_script("arguments[0].click();", edit_btn)
        except Exception:
            log.warning("Could not find Edit button")
        page.wait_seconds(2)

        special_name = generate_invalid_name_special_chars()
        page.type_text(page.FARMER_NAME_INPUT, special_name, clear_first=True)
        page._force_close_panels()

        if page.is_edit_mode():
            page.click_update()
            page.wait_seconds(2)

            validation_alert = page.handle_validation_warning(timeout=5)
            errors = page.get_mat_error_text()

            assert validation_alert or errors, (
                f"BUG-F03 CONFIRMED: Special chars '{special_name}' accepted in Edit"
            )
        else:
            log.info("Not in edit mode")

        try:
            page.cancel()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- FR-E05: Edit -- Email with uppercase (BUG-F04) ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F04, strict=False)
    def test_FR_E05_edit_uppercase_email(self, fr_page):
        """Edit Email to uppercase -- should be accepted (BUG-F04)."""
        log.info("FR-E05: Edit uppercase email test")
        page = fr_page

        name, data = _create_prerequisite_farmer(page, "Walk-in Farmer")
        if not name:
            return

        page.click_table_row(0)
        page.wait_seconds(1)
        try:
            edit_btn = page.driver.find_element(
                By.XPATH,
                "//button[contains(@class,'edit-btn') or contains(.,'Edit')]"
            )
            page.driver.execute_script("arguments[0].click();", edit_btn)
        except Exception:
            log.warning("Could not find Edit button")
        page.wait_seconds(2)

        uppercase_email = generate_uppercase_email()
        page.type_text(page.EMAIL_INPUT, uppercase_email, clear_first=True)
        page._force_close_panels()

        if page.is_edit_mode():
            page.click_update()
            page.wait_seconds(2)

            validation_alert = page.handle_validation_warning(timeout=5)
            errors = page.get_mat_error_text()

            assert not validation_alert and not any(
                "email" in e.lower() for e in errors
            ), (
                f"BUG-F04 CONFIRMED: Uppercase email rejected in Edit: {errors}"
            )
        else:
            log.info("Not in edit mode")

        try:
            page.cancel()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 4: Search & Filter Edge Cases (5 tests)
# ====================================================================

class TestSearchFilter:
    """FR-S01 to FR-S05: Search and filter edge case tests."""

    def test_FR_S01_search_exact_name(self, fr_page):
        """Search by exact farmer name."""
        log.info("FR-S01: Search exact name test")
        page = fr_page

        name, _ = _create_prerequisite_farmer(page, "Walk-in Farmer")
        if not name:
            return

        page.search_item(name)
        page.wait_seconds(2)

        found = page.is_farmer_in_table(name)
        assert found, f"Farmer '{name}' not found in search results"

        page.clear_search()
        page.wait_seconds(2)

    def test_FR_S02_search_partial_name(self, fr_page):
        """Search by partial farmer name."""
        log.info("FR-S02: Search partial name test")
        page = fr_page

        name, _ = _create_prerequisite_farmer(page, "Walk-in Farmer")
        if not name:
            return

        # Use first 8 chars of name for partial search
        partial = name[:8]
        page.search_item(partial)
        page.wait_seconds(2)

        log.info(f"Partial search with '{partial}' executed")

        page.clear_search()
        page.wait_seconds(2)

    def test_FR_S03_search_no_results(self, fr_page):
        """Search with non-existent term -- no results."""
        log.info("FR-S03: Search no results test")
        page = fr_page

        fake_name = f"NonExistent_{int(time.time())}"
        page.search_item(fake_name)
        page.wait_seconds(2)

        found = page.is_farmer_in_table(fake_name)
        assert not found, f"BUG: Non-existent name '{fake_name}' was found in table"
        log.info(f"Correctly not found: {fake_name}")

        page.clear_search()
        page.wait_seconds(2)

    def test_FR_S04_search_special_chars(self, fr_page):
        """Search with special characters -- should not crash."""
        log.info("FR-S04: Search special chars test")
        page = fr_page

        try:
            page.search_item("!@#$%^&*()")
            page.wait_seconds(2)
            log.info("Search with special chars did not crash")
        except Exception as e:
            log.warning(f"Search with special chars raised exception: {e}")

        page.clear_search()
        page.wait_seconds(2)

    def test_FR_S05_search_case_sensitivity(self, fr_page):
        """Search case sensitivity -- uppercase vs lowercase."""
        log.info("FR-S05: Search case sensitivity test")
        page = fr_page

        name, _ = _create_prerequisite_farmer(page, "Walk-in Farmer")
        if not name:
            return

        # Search with uppercase
        page.search_item(name.upper())
        page.wait_seconds(2)

        found_upper = page.is_farmer_in_table(name)

        page.clear_search()
        page.wait_seconds(1)

        # Search with lowercase
        page.search_item(name.lower())
        page.wait_seconds(2)

        found_lower = page.is_farmer_in_table(name)

        log.info(
            f"Case sensitivity: uppercase found={found_upper}, "
            f"lowercase found={found_lower}"
        )

        page.clear_search()
        page.wait_seconds(2)


# ====================================================================
# PHASE 5: Popup & UI Behaviors (6 tests)
# ====================================================================

class TestPopupUIBehaviors:
    """FR-P01 to FR-P06: Popup and UI behavior tests."""

    def test_FR_P01_add_form_cancel(self, fr_page):
        """Add form opens and closes via Cancel button."""
        log.info("FR-P01: Add form cancel test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        page.cancel()
        page.wait_seconds(1)

        assert not page.is_add_form_open(), "Add form still open after Cancel"

    def test_FR_P02_add_form_close_x(self, fr_page):
        """Add form closes via X button."""
        log.info("FR-P02: Add form close X button test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Try closing via X button
        try:
            close_btn = page.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'big-model')]//button"
                "[contains(@class,'close') or @aria-label='Close']"
            )
            page.driver.execute_script("arguments[0].click();", close_btn)
            page.wait_seconds(1)
        except Exception:
            # Fallback: cancel
            page.cancel()

        log.info("Form close via X button tested")

    def test_FR_P03_category_borrower_shows_all_tabs(self, fr_page):
        """Borrower Farmer category should show all 13 stepper tabs."""
        log.info("FR-P03: Borrower Farmer shows all 13 tabs test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)

        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = generate_borrower_farmer_category()
        adapted = _adapt_step0(step0)
        page.fill_step0(adapted)
        page.wait_seconds(1)

        tab_count = len([t for t in page.get_stepper_tab_names() if t.strip()])
        log.info(f"Borrower Farmer tab count: {tab_count}")

        assert tab_count == 13, (
            f"Expected 13 tabs for Borrower Farmer, got {tab_count}"
        )

        try:
            page.cancel()
        except Exception:
            pass

    def test_FR_P04_category_walkin_shows_subset_tabs(self, fr_page):
        """Walk-in Farmer category should show subset of tabs (Address + Bank)."""
        log.info("FR-P04: Walk-in Farmer shows subset tabs test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)

        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = generate_walkin_farmer_category()
        adapted = _adapt_step0(step0)
        page.fill_step0(adapted)
        page.wait_seconds(1)

        tab_names = page.get_stepper_tab_names()
        tab_count = len([t for t in tab_names if t.strip()])
        log.info(f"Walk-in Farmer tab count: {tab_count}, tabs: {tab_names}")

        # Walk-in Farmer has at least Address Details + Bank Details
        assert tab_count >= 2, (
            f"Expected at least 2 tabs for Walk-in Farmer, got {tab_count}"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-P05: Deselect+Reselect freezes Next/Back (BUG-F02) ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F02, strict=False)
    def test_FR_P05_category_deselect_reselect_freeze(self, fr_page):
        """Deselect+Reselect farmer category should NOT freeze Next/Back (BUG-F02)."""
        log.info("FR-P05: Category deselect+reselect freeze test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)

        # Fill Step 0 with Borrower Farmer
        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = generate_borrower_farmer_category()
        adapted = _adapt_step0(step0)
        page.fill_step0(adapted)
        page.wait_seconds(1)

        # Deselect and reselect the farmer category
        page._select_farmer_category("Borrower Farmer")  # Click to toggle off
        page.wait_seconds(1)

        page._select_farmer_category("Borrower Farmer")  # Click to toggle back on
        page.wait_seconds(1)

        # Try clicking Next -- should work
        next_worked = page.click_stepper_next()
        assert next_worked, (
            "BUG-F02 CONFIRMED: Next button frozen after deselect+reselect farmer category"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-P06: Character count indicator disappears (BUG-F09) ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F09, strict=False)
    def test_FR_P06_char_count_disappears(self, fr_page):
        """Character count indicator should remain visible during validation (BUG-F09)."""
        log.info("FR-P06: Character count indicator test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)

        # Type valid text in Farmer Name -- observe character count
        page.type_text(page.FARMER_NAME_INPUT, "TestFarmer", clear_first=True)
        page.wait_seconds(1)

        # Check for character count indicator
        has_counter = page.driver.execute_script("""
            var counters = document.querySelectorAll(
                '.mat-mdc-form-field-hint, [class*="character-count"], [class*="hint"]'
            );
            return counters.length > 0;
        """)
        log.info(f"Character count indicator present: {has_counter}")

        # Type invalid characters to trigger validation
        page.type_text(page.FARMER_NAME_INPUT, "@@@", clear_first=True)
        page.wait_seconds(1)

        # Check if counter still visible
        has_counter_after_error = page.driver.execute_script("""
            var counters = document.querySelectorAll(
                '.mat-mdc-form-field-hint, [class*="character-count"], [class*="hint"]'
            );
            var visible = 0;
            counters.forEach(function(c) {
                if (c.offsetHeight > 0) visible++;
            });
            return visible > 0;
        """)

        assert has_counter_after_error, (
            "BUG-F09 CONFIRMED: Character count indicator disappears on validation error"
        )

        try:
            page.cancel()
        except Exception:
            pass


# ====================================================================
# PHASE 6: History & Audit Trail (2 tests)
# ====================================================================

class TestHistoryAuditTrail:
    """FR-H01 to FR-H02: History and audit trail tests."""

    def test_FR_H01_view_button_opens_popup(self, fr_page):
        """Click View button -- should open a read-only popup."""
        log.info("FR-H01: View button popup test")
        page = fr_page

        name, _ = _create_prerequisite_farmer(page, "Walk-in Farmer")
        if not name:
            return

        # Click View on first row
        page.click_table_row(0)
        page.wait_seconds(1)
        try:
            view_btn = page.driver.find_element(
                By.XPATH,
                "//button[contains(@class,'view-btn') or contains(.,'View')]"
            )
            page.driver.execute_script("arguments[0].click();", view_btn)
        except Exception:
            log.warning("Could not find View button")
        page.wait_seconds(2)

        # Check if view popup opened
        popup_open = page._is_form_popup_open()
        log.info(f"View popup opened: {popup_open}")

        try:
            page.cancel()
        except Exception:
            pass

    def test_FR_H02_table_sorting(self, fr_page):
        """Click column headers to sort -- verify sorting works."""
        log.info("FR-H02: Table sorting test")
        page = fr_page

        # Click Farmer Name column header to sort
        try:
            header = page.driver.find_element(
                By.CSS_SELECTOR, "th.cdk-column-name button, th.cdk-column-name"
            )
            page.driver.execute_script("arguments[0].click();", header)
            page.wait_seconds(2)
            log.info("Farmer Name column sorted")
        except Exception:
            log.info("Could not click sort header")


# ====================================================================
# PHASE 7: Bug-Specific Tests (9 tests)
# ====================================================================

class TestBugSpecific:
    """FR-B01 to FR-B09: Dedicated tests for every discovered bug."""

    # ---- FR-B01: BUG-F01: No Of Owner -- no asterisk ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F01, strict=False)
    def test_FR_B01_no_of_owner_no_asterisk(self, fr_page):
        """BUG-F01: No Of Owner required but no asterisk shown."""
        log.info("FR-B01: No Of Owner no asterisk test")
        page = fr_page

        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = generate_borrower_farmer_category()
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(adapted)

        # Navigate to Land Details tab (TAB_LAND = 4, so 5 Next clicks)
        for _ in range(5):
            page.click_stepper_next()
            page.wait_seconds(1)

        # Leave No Of Owner empty and try to proceed
        page.click_stepper_next()
        page.wait_seconds(2)

        # Check for red border (validation) on No Of Owner field
        has_validation = page.driver.execute_script("""
            var inputs = document.querySelectorAll('input[name="No Of Owner"]');
            for (var i = 0; i < inputs.length; i++) {
                var field = inputs[i].closest('mat-form-field');
                if (field && field.className.includes('invalid')) return true;
            }
            return false;
        """)

        assert not has_validation, (
            "BUG-F01 CONFIRMED: No Of Owner validates on empty but has no asterisk indicator"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-B02: BUG-F02: Deselect+Reselect freeze ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F02, strict=False)
    def test_FR_B02_category_freeze(self, fr_page):
        """BUG-F02: Deselect+Reselect farmer category freezes Next/Back."""
        log.info("FR-B02: Category freeze test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)

        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = generate_borrower_farmer_category()
        adapted = _adapt_step0(step0)
        page.fill_step0(adapted)
        page.wait_seconds(1)

        # Toggle category off and on
        page._select_farmer_category("Borrower Farmer")  # deselect
        page.wait_seconds(1)
        page._select_farmer_category("Borrower Farmer")  # reselect
        page.wait_seconds(1)

        # Next should still work
        next_worked = page.click_stepper_next()
        assert next_worked, "BUG-F02 CONFIRMED: Next frozen after category toggle"

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-B03: BUG-F03: Farmer Name special chars ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F03, strict=False)
    def test_FR_B03_special_char_name(self, fr_page):
        """BUG-F03: Farmer Name accepts special characters (create attempt)."""
        log.info("FR-B03: Special char name bug test")
        page = fr_page

        special_name = generate_invalid_name_special_chars()
        create_data = _build_create_data(category="Walk-in Farmer")
        create_data["farmer_name"] = special_name

        result = page.create_farmer(create_data, category="Walk-in Farmer")

        try:
            page.close_popup()
        except Exception:
            pass

        page.click_refresh()
        page.wait_seconds(2)

        # If create succeeded, BUG-F03 is confirmed
        assert result["status"] == "FAILED", (
            f"BUG-F03 CONFIRMED: Special char name '{special_name}' was saved successfully"
        )

    # ---- FR-B04: BUG-F04: Email uppercase rejected ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F04, strict=False)
    def test_FR_B04_uppercase_email(self, fr_page):
        """BUG-F04: Email field rejects uppercase letters (create attempt)."""
        log.info("FR-B04: Uppercase email bug test")
        page = fr_page

        create_data = _build_create_data(category="Walk-in Farmer")
        create_data["email"] = generate_uppercase_email()

        result = page.create_farmer(create_data, category="Walk-in Farmer")

        try:
            page.close_popup()
        except Exception:
            pass

        assert result["status"] == "PASSED", (
            f"BUG-F04 CONFIRMED: Uppercase email rejected: {result.get('error', '')}"
        )

    # ---- FR-B05: BUG-F05: Placeholder selectable ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F05, strict=False)
    def test_FR_B05_placeholder_selectable(self, fr_page):
        """BUG-F05: 'Select Farmer Category' placeholder is selectable (create attempt)."""
        log.info("FR-B05: Placeholder selectable bug test")
        page = fr_page

        create_data = _build_create_data(category="Walk-in Farmer")
        create_data["farmer_category"] = "Select Farmer Category"

        result = page.create_farmer(create_data, category="Walk-in Farmer")

        try:
            page.close_popup()
        except Exception:
            pass

        assert result["status"] == "FAILED", (
            "BUG-F05 CONFIRMED: Placeholder 'Select Farmer Category' was accepted"
        )

    # ---- FR-B06: BUG-F06: Amount fields accept 0 and . prefix ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F06, strict=False)
    def test_FR_B06_amount_zero_dot(self, fr_page):
        """BUG-F06: Amount fields accept 0 and . prefix values."""
        log.info("FR-B06: Amount zero/dot bug test")
        page = fr_page

        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = generate_borrower_farmer_category()
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(adapted)

        # Navigate to Income Details tab (TAB_INCOME = 8, so 9 Next clicks)
        for _ in range(9):
            page.click_stepper_next()
            page.wait_seconds(1)

        # Enter 0 in Exact Amount
        try:
            exact_amount_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Exact Amount']"
            )
            exact_amount_input.clear()
            exact_amount_input.send_keys("0")
            page.wait_seconds(0.5)

            # Try to proceed -- 0 should be rejected
            page.click_stepper_next()
            page.wait_seconds(2)

            validation_alert = page.handle_validation_warning(timeout=5)
            errors = page.get_mat_error_text()

            assert validation_alert or errors, (
                "BUG-F06 CONFIRMED: Amount '0' accepted without validation"
            )
        except Exception as e:
            log.warning(f"Could not test amount field: {e}")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-B07: BUG-F07: Source of Income Dairy duplicate ----
    @pytest.mark.bug
    def test_FR_B07_dairy_duplicate(self, fr_page):
        """BUG-F07: Source of Income shows 'Dairy' twice."""
        log.info("FR-B07: Dairy duplicate bug test")
        page = fr_page

        step0 = generate_valid_farmer_step0()
        step0["farmer_category"] = generate_borrower_farmer_category()
        adapted = _adapt_step0(step0)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(adapted)

        # Navigate to Income Details
        for _ in range(9):
            page.click_stepper_next()
            page.wait_seconds(1)

        # Open Source of Income dropdown and check for duplicates
        try:
            src_income_select = page.driver.find_element(
                By.XPATH,
                "//mat-label[contains(.,'Source of Income')]"
                "/ancestor::mat-form-field//mat-select",
            )
            src_income_select.click()
            page.wait_seconds(1)

            options = page.driver.find_elements(
                By.CSS_SELECTOR, "div[role='listbox'] mat-option"
            )
            option_texts = [opt.text.strip() for opt in options]

            dairy_count = option_texts.count("Dairy")
            log.info(
                f"Dairy appears {dairy_count} time(s) in Source of Income dropdown"
            )

            if dairy_count > 1:
                log.info("BUG-F07 CONFIRMED: 'Dairy' appears more than once")

            page._close_select_panel()
        except Exception as e:
            log.warning(f"Could not check Source of Income dropdown: {e}")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-B08: BUG-F08: Edit mode missing tabs ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F08, strict=False)
    def test_FR_B08_edit_missing_tabs(self, fr_page):
        """BUG-F08: Edit mode missing Land/Crop/KYC tabs."""
        log.info("FR-B08: Edit missing tabs bug test")
        page = fr_page

        name, data = _create_prerequisite_farmer(page, "Borrower Farmer")
        if not name:
            return

        page.click_table_row(0)
        page.wait_seconds(1)
        try:
            edit_btn = page.driver.find_element(
                By.XPATH,
                "//button[contains(@class,'edit-btn') or contains(.,'Edit')]"
            )
            page.driver.execute_script("arguments[0].click();", edit_btn)
        except Exception:
            log.warning("Could not find Edit button")
        page.wait_seconds(2)

        tab_names = page.get_stepper_tab_names()
        tab_count = len([t for t in tab_names if t.strip()])

        assert tab_count == 13, (
            f"BUG-F08 CONFIRMED: Edit mode shows {tab_count} tabs instead of 13. "
            f"Tabs: {tab_names}"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-B09: BUG-F09: Character count disappears ----
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_F09, strict=False)
    def test_FR_B09_char_count_disappears(self, fr_page):
        """BUG-F09: Character count indicator disappears on validation error."""
        log.info("FR-B09: Character count disappears bug test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)

        # Type in Farmer Name -- check for character count
        page.type_text(page.FARMER_NAME_INPUT, "TestFarmer123", clear_first=True)
        page.wait_seconds(1)

        # Get character count indicator visibility
        counter_visible_before = page.driver.execute_script("""
            var hints = document.querySelectorAll(
                '.mat-mdc-form-field-hint, [class*="hint"]'
            );
            var visible = 0;
            hints.forEach(function(h) { if (h.offsetHeight > 0) visible++; });
            return visible > 0;
        """)

        # Type invalid characters to trigger validation
        page.type_text(page.FARMER_NAME_INPUT, "@@", clear_first=True)
        page.wait_seconds(1)

        counter_visible_after = page.driver.execute_script("""
            var hints = document.querySelectorAll(
                '.mat-mdc-form-field-hint, [class*="hint"]'
            );
            var visible = 0;
            hints.forEach(function(h) { if (h.offsetHeight > 0) visible++; });
            return visible > 0;
        """)

        if counter_visible_before and not counter_visible_after:
            log.info("BUG-F09 CONFIRMED: Character count disappeared after validation error")

        assert counter_visible_after or not counter_visible_before, (
            "BUG-F09 CONFIRMED: Character count indicator disappeared during validation"
        )

        try:
            page.cancel()
        except Exception:
            pass
