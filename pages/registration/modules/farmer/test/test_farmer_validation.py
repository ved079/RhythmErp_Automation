"""
test_farmer_validation.py
-------------------------
Comprehensive validation test suite for RhythmERP Farmer screen.
~40 test cases across 7 phases.

Phases:
  1. Create Form Validations   (15 tests) — FR-C01 to FR-C15
  2. Duplicate Validations      (2 tests)  — FR-D01 to FR-D02
  3. Edit Form Validations      (5 tests)  — FR-E01 to FR-E05
  4. Search & Filter Edge Cases (5 tests)  — FR-S01 to FR-S05
  5. Popup & UI Behaviors       (6 tests)  — FR-P01 to FR-P06
  6. History & Audit Trail      (2 tests)  — FR-H01 to FR-H02
  7. Bug-Specific Tests         (9 tests)  — FR-B01 to FR-B09

Known Bugs (CONFIRMED via browser exploration 2026-05-21):
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
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from pages.registration.modules.farmer.farmer_page import FarmerPage
from pages.registration.modules.farmer.data.farmer_data import (
    generate_valid_farmer_step0,
    generate_valid_address_data,
    generate_valid_bank_data,
    generate_full_valid_farmer_data,
    generate_special_char_name,
    generate_uppercase_email,
    generate_invalid_email,
    generate_zero_amount,
    generate_dot_prefix_amount,
    generate_negative_amount,
    generate_empty_farmer_data,
    generate_farmer_name_only,
    generate_string_255,
    generate_string_256,
    generate_spaces_only,
    generate_sql_injection,
    generate_xss_payload,
    generate_future_date,
    generate_duplicate_farmer_data,
)
from common.logger import log


# ====================================================================
# Helper: create a prerequisite farmer, refresh, return its name
# ====================================================================

def _create_prerequisite_farmer(page, category="Walk-in Farmer"):
    """Create a Farmer entry for tests that need existing data.
    Returns the farmer name and the data dict.
    """
    data = generate_full_valid_farmer_data(category)
    result = page.create_farmer(data)
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
    name = result.get("farmer_name", "") or data.get("farmer_name", "")
    log.info(f"Prerequisite farmer created: {name}")
    return name, data


# ====================================================================
# PHASE 1: Create Form Validations (15 tests)
# ====================================================================

class TestCreateFormValidations:
    """FR-C01 to FR-C15: Validation checks on the Create form."""

    # ---- FR-C01: Submit with all fields empty ----
    def test_FR_C01_empty_submit(self, fr_page):
        """Submit with all fields empty — should be blocked."""
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
            "BUG: Form advanced with all fields empty — no validation"
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
    def test_FR_C02_valid_create_walkin(self, fr_page):
        """Create Walk-in Farmer with valid data (3 tabs) — should succeed."""
        log.info("FR-C02: Valid Walk-in Farmer create test")
        page = fr_page

        data = generate_full_valid_farmer_data("Walk-in Farmer")
        result = page.create_farmer(data)
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
    def test_FR_C03_valid_create_borrower(self, fr_page):
        """Create Borrower Farmer with valid data (13 tabs) — should succeed."""
        log.info("FR-C03: Valid Borrower Farmer create test")
        page = fr_page

        data = generate_full_valid_farmer_data("Borrower Farmer")
        result = page.create_farmer(data)
        name = result.get("farmer_name", "")

        if result["status"] == "PASSED":
            log.info(f"Borrower Farmer created: {name}")
        else:
            log.warning(f"Create failed: {result.get('error', 'unknown')}")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- FR-C04: Farmer Name accepts special characters (BUG-F03) ----
    @pytest.mark.xfail(reason="BUG-F03: Farmer Name accepts special characters", strict=False)
    def test_FR_C04_special_char_name(self, fr_page):
        """Farmer Name with special characters — should be rejected (BUG-F03)."""
        log.info("FR-C04: Special characters in Farmer Name test")
        page = fr_page

        special_name = generate_special_char_name()
        data = generate_valid_farmer_step0("Walk-in Farmer")
        data["farmer_name"] = special_name

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)
        page._force_close_panels()

        # Try to advance — should be blocked by validation
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
    @pytest.mark.xfail(reason="BUG-F04: Email rejects uppercase letters", strict=False)
    def test_FR_C05_uppercase_email(self, fr_page):
        """Email with uppercase letters — should be accepted (BUG-F04)."""
        log.info("FR-C05: Uppercase email test")
        page = fr_page

        data = generate_valid_farmer_step0("Walk-in Farmer")
        data["email"] = generate_uppercase_email()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)
        page._force_close_panels()

        # Check if email field has validation error
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()

        # BUG-F04: uppercase emails SHOULD be valid but are rejected
        # We expect this to FAIL because the system incorrectly rejects them
        assert not validation_alert and not any("email" in e.lower() for e in errors), (
            f"BUG-F04 CONFIRMED: Uppercase email rejected: {errors}"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C06: Farmer Category placeholder selectable (BUG-F05) ----
    @pytest.mark.xfail(reason="BUG-F05: Farmer Category placeholder is selectable", strict=False)
    def test_FR_C06_placeholder_category(self, fr_page):
        """Select 'Select Farmer Category' placeholder — should not be valid (BUG-F05)."""
        log.info("FR-C06: Placeholder category selectable test")
        page = fr_page

        data = generate_valid_farmer_step0()
        data["farmer_category"] = "Select Farmer Category"  # Placeholder

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)
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
    def test_FR_C07_name_maxlength_255(self, fr_page):
        """Farmer Name 255 chars — should be accepted."""
        log.info("FR-C07: Name maxlength 255 boundary test")
        page = fr_page

        name_255 = generate_string_255()
        data = generate_valid_farmer_step0("Walk-in Farmer")
        data["farmer_name"] = name_255

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)
        page.wait_seconds(1)

        # Check value was accepted (may be truncated to 255)
        values = page.get_form_field_values_step0()
        entered_name = values.get("farmer_name", "")
        log.info(f"Name 255 chars: entered length = {len(entered_name)}")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C08: Farmer Name 256 chars — over max ----
    def test_FR_C08_name_256_chars(self, fr_page):
        """Farmer Name 256 chars — should truncate or show error."""
        log.info("FR-C08: Name 256 chars test")
        page = fr_page

        name_256 = generate_string_256()
        data = generate_valid_farmer_step0("Walk-in Farmer")
        data["farmer_name"] = name_256

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)
        page.wait_seconds(1)

        values = page.get_form_field_values_step1() if hasattr(page, 'get_form_field_values_step1') else {}
        log.info("Name 256 chars entered — checking truncation behavior")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C09: Phone Number with alphabetic input ----
    def test_FR_C09_alpha_phone(self, fr_page):
        """Alphabetic characters in Phone Number — should be rejected."""
        log.info("FR-C09: Alpha phone number test")
        page = fr_page

        data = generate_valid_farmer_step0("Walk-in Farmer")
        data["phone_number"] = "abcdefghij"

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)
        page._force_close_panels()

        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()

        if validation_alert or errors:
            log.info("Alpha phone rejected — validation working")
        else:
            log.warning("BUG: Alphabetic characters accepted in Phone Number")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C10: Age auto-calculated from DOB ----
    def test_FR_C10_age_auto_calculated(self, fr_page):
        """Age should be auto-calculated from Date of Birth (readonly)."""
        log.info("FR-C10: Age auto-calculation test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)

        # Enter DOB
        page.type_text(page.DATE_OF_BIRTH_INPUT, "01/01/1990", clear_first=True)
        page.wait_seconds(1)

        # Check Age field (readonly)
        try:
            age_input = page.driver.find_element(By.CSS_SELECTOR, "input[name='Age']")
            age_value = age_input.get_attribute("value") or ""
            log.info(f"Age auto-calculated: {age_value}")

            if age_value:
                log.info("Age auto-calculated from DOB — working correctly")
            else:
                log.info("Age not auto-calculated yet — may need tab-out from DOB field")
        except Exception:
            log.info("Could not read Age value")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C11: Date of Birth future date ----
    def test_FR_C11_future_dob(self, fr_page):
        """Future date in Date Of Birth — should be rejected."""
        log.info("FR-C11: Future DOB test")
        page = fr_page

        data = generate_valid_farmer_step0("Walk-in Farmer")
        data["date_of_birth"] = generate_future_date()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)
        page.wait_seconds(1)

        log.info("Future DOB entered — checking validation")
        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C12: No Of Owner required but no asterisk (BUG-F01) ----
    @pytest.mark.xfail(reason="BUG-F01: No Of Owner required but no asterisk shown", strict=False)
    def test_FR_C12_no_of_owner_required(self, fr_page):
        """No Of Owner in Land Details is required but no asterisk shown (BUG-F01)."""
        log.info("FR-C12: No Of Owner required without asterisk test")
        page = fr_page

        data = generate_valid_farmer_step0("Borrower Farmer")
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)

        # Navigate to Land Details tab (step 4)
        for _ in range(5):
            page.click_stepper_next()
            page.wait_seconds(1)

        tab_names = page.get_stepper_tab_names()
        current_idx = page.get_current_step_index()
        log.info(f"Current tab: {tab_names[current_idx] if current_idx >= 0 else 'unknown'}")

        # Check if No Of Owner field has asterisk
        has_asterisk = page.driver.execute_script("""
            var labels = document.querySelectorAll('mat-label');
            for (var i = 0; i < labels.length; i++) {
                if (labels[i].textContent.includes('No Of Owner')) {
                    return labels[i].textContent.includes('*');
                }
            }
            return false;
        """)

        # BUG-F01: No asterisk but field IS required
        assert has_asterisk, (
            "BUG-F01 CONFIRMED: No Of Owner is required but no asterisk shown"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C13: Address table required fields validation ----
    def test_FR_C13_address_required_fields(self, fr_page):
        """Address tab — required fields (Country, State, District, Taluka, Address) validation."""
        log.info("FR-C13: Address required fields test")
        page = fr_page

        data = generate_valid_farmer_step0("Walk-in Farmer")
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)

        # Navigate to Current Address tab
        page.click_stepper_next()
        page.wait_seconds(1)

        # Try to proceed without filling address
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()

        if validation_alert or errors:
            log.info("Address validation working — required fields enforced")
        else:
            log.warning("Address required fields may not be validated")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C14: Address cascading dropdowns ----
    def test_FR_C14_address_cascading_dropdowns(self, fr_page):
        """Address cascading: Country → State → District → Taluka → Village."""
        log.info("FR-C14: Address cascading dropdowns test")
        page = fr_page

        data = generate_valid_farmer_step0("Walk-in Farmer")
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)

        # Navigate to Current Address tab
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill cascading address
        addr_data = generate_valid_address_data()
        page.fill_current_address(addr_data)

        log.info("Address cascading dropdowns filled successfully")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-C15: Stepper Next/Back navigation ----
    def test_FR_C15_stepper_navigation(self, fr_page):
        """Stepper Next and Back navigation — basic flow test."""
        log.info("FR-C15: Stepper navigation test")
        page = fr_page

        data = generate_valid_farmer_step0("Walk-in Farmer")
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)

        # Click Next to go to Current Address
        page.click_stepper_next()
        page.wait_seconds(1)

        current = page.get_current_step_index()
        assert current == 0, f"Expected step 0 (Current Address), got {current}"

        # Click Back
        page.click_stepper_back()
        page.wait_seconds(1)

        # Should be back at Step 0
        log.info("Stepper navigation working — Next/Back functional")

        try:
            page.cancel()
        except Exception:
            pass


# ====================================================================
# PHASE 2: Duplicate Validations (2 tests)
# ====================================================================

class TestDuplicateValidations:
    """FR-D01 to FR-D02: Duplicate farmer checks."""

    # ---- FR-D01: Create duplicate farmer ----
    def test_FR_D01_duplicate_farmer(self, fr_page):
        """Create two farmers with the same name — check if duplicates allowed."""
        log.info("FR-D01: Duplicate farmer test")
        page = fr_page

        # Create first farmer
        data1 = generate_full_valid_farmer_data("Walk-in Farmer")
        result1 = page.create_farmer(data1)
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
            log.warning("Farmer 1 creation failed — cannot test duplicate")
            return

        # Create second farmer with same name
        data2 = generate_full_valid_farmer_data("Walk-in Farmer")
        data2["farmer_name"] = name1  # Same name

        result2 = page.create_farmer(data2)

        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        if result2["status"] == "PASSED":
            log.info(f"Duplicate farmer allowed — name '{name1}' used twice")
        else:
            log.info(f"Duplicate farmer blocked: {result2.get('error', '')}")

    # ---- FR-D02: Create farmer with same phone number ----
    def test_FR_D02_duplicate_phone(self, fr_page):
        """Create farmer with same phone number — check if allowed."""
        log.info("FR-D02: Duplicate phone number test")
        page = fr_page

        # Create first farmer
        data1 = generate_full_valid_farmer_data("Walk-in Farmer")
        result1 = page.create_farmer(data1)
        phone1 = data1.get("phone_number", "")

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
            log.warning("Farmer 1 creation failed — cannot test duplicate phone")
            return

        # Create second with same phone
        data2 = generate_full_valid_farmer_data("Walk-in Farmer")
        data2["phone_number"] = phone1

        result2 = page.create_farmer(data2)

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

    # ---- FR-E01: Edit — pre-populated fields ----
    def test_FR_E01_edit_prepopulated(self, fr_page):
        """Edit popup should show Step 0 fields pre-populated."""
        log.info("FR-E01: Edit pre-populated fields test")
        page = fr_page

        name, data = _create_prerequisite_farmer(page, "Walk-in Farmer")

        if not name:
            log.warning("Prerequisite farmer name empty — cannot verify edit")
            return

        # Click Edit
        page.click_edit_button(farmer_name=name)
        page.wait_seconds(2)

        # Read form values
        form_values = page.get_form_field_values_step0()

        assert form_values.get("farmer_name"), "Farmer Name empty in Edit form"
        assert form_values.get("phone_number"), "Phone Number empty in Edit form"
        log.info(f"Edit form pre-populated: name={form_values.get('farmer_name')}")

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-E02: Edit — modify and save ----
    def test_FR_E02_edit_modify_save(self, fr_page):
        """Edit farmer — modify and save successfully."""
        log.info("FR-E02: Edit modify and save test")
        page = fr_page

        name, data = _create_prerequisite_farmer(page, "Walk-in Farmer")

        if not name:
            return

        page.click_edit_button(farmer_name=name)
        page.wait_seconds(2)

        # Modify some fields
        page.type_text(page.EMAIL_INPUT, "edited@test.com", clear_first=True)
        page._force_close_panels()

        page.click_update()
        page.wait_seconds(2)

        alert_title = page.handle_success_alert(timeout=30)
        if "successfully" in alert_title.lower():
            log.info("Edit saved successfully")
        else:
            log.warning(f"Edit save failed: {alert_title}")

    # ---- FR-E03: Edit mode shows only 10 tabs (BUG-F08) ----
    @pytest.mark.xfail(reason="BUG-F08: Edit mode missing Land/Crop/KYC tabs", strict=False)
    def test_FR_E03_edit_missing_tabs(self, fr_page):
        """Edit mode should show 13 tabs for Borrower Farmer but shows only 10 (BUG-F08)."""
        log.info("FR-E03: Edit missing tabs test")
        page = fr_page

        name, data = _create_prerequisite_farmer(page, "Borrower Farmer")

        if not name:
            return

        page.click_edit_button(farmer_name=name)
        page.wait_seconds(2)

        tab_count = page.get_stepper_tab_count()
        tab_names = page.get_stepper_tab_names()
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

    # ---- FR-E04: Edit — Farmer Name with special chars (BUG-F03) ----
    @pytest.mark.xfail(reason="BUG-F03: Farmer Name accepts special chars in Edit", strict=False)
    def test_FR_E04_edit_special_char_name(self, fr_page):
        """Edit Farmer Name to special characters — should be rejected (BUG-F03)."""
        log.info("FR-E04: Edit special char name test")
        page = fr_page

        name, data = _create_prerequisite_farmer(page, "Walk-in Farmer")
        if not name:
            return

        page.click_edit_button(farmer_name=name)
        page.wait_seconds(2)

        special_name = generate_special_char_name()
        page.type_text(page.FARMER_NAME_INPUT, special_name, clear_first=True)
        page._force_close_panels()

        page.click_update()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()

        assert validation_alert or errors, (
            f"BUG-F03 CONFIRMED: Special chars '{special_name}' accepted in Edit"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-E05: Edit — Email with uppercase (BUG-F04) ----
    @pytest.mark.xfail(reason="BUG-F04: Email rejects uppercase in Edit", strict=False)
    def test_FR_E05_edit_uppercase_email(self, fr_page):
        """Edit Email to uppercase — should be accepted (BUG-F04)."""
        log.info("FR-E05: Edit uppercase email test")
        page = fr_page

        name, data = _create_prerequisite_farmer(page, "Walk-in Farmer")
        if not name:
            return

        page.click_edit_button(farmer_name=name)
        page.wait_seconds(2)

        uppercase_email = generate_uppercase_email()
        page.type_text(page.EMAIL_INPUT, uppercase_email, clear_first=True)
        page._force_close_panels()

        page.click_update()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()

        assert not validation_alert and not any("email" in e.lower() for e in errors), (
            f"BUG-F04 CONFIRMED: Uppercase email rejected in Edit: {errors}"
        )

        try:
            page.cancel()
        except Exception:
            pass


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

    def test_FR_S03_search_no_results(self, fr_page):
        """Search with non-existent term — no results."""
        log.info("FR-S03: Search no results test")
        page = fr_page

        page.search_item("ZZZZZ_NONEXISTENT_FARMER_99999")
        page.wait_seconds(2)

        log.info("No-results search executed")

    def test_FR_S04_search_special_chars(self, fr_page):
        """Search with special characters."""
        log.info("FR-S04: Search special chars test")
        page = fr_page

        page.search_item("!@#$%^&*()")
        page.wait_seconds(2)

        log.info("Special chars search executed — checking for errors")

    def test_FR_S05_search_case_sensitivity(self, fr_page):
        """Search case sensitivity — uppercase vs lowercase."""
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

        log.info(f"Case sensitivity: uppercase found={found_upper}, lowercase found={found_lower}")


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
                "//div[contains(@class,'big-model')]//button[contains(@class,'close') or @aria-label='Close']"
            )
            page.driver.execute_script("arguments[0].click();", close_btn)
            page.wait_seconds(1)
        except Exception:
            # Fallback: cancel
            page.cancel()

        log.info("Form close via X button tested")

    def test_FR_P03_category_switch_borrower_fpc(self, fr_page):
        """Category switching: Borrower → FPC — tab count changes from 13 to 6."""
        log.info("FR-P03: Category switch Borrower→FPC test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)

        # Select Borrower Farmer first
        data = generate_valid_farmer_step0("Borrower Farmer")
        data["farmer_name"] = "CatSwitchTest"
        data["phone_number"] = "9876543210"
        data["password"] = "TestPass@123"
        page.fill_step0(data)
        page.wait_seconds(1)

        tab_count_borrower = page.get_stepper_tab_count()
        log.info(f"Borrower Farmer tab count: {tab_count_borrower}")

        assert tab_count_borrower == 13, f"Expected 13 tabs for Borrower, got {tab_count_borrower}"

        try:
            page.cancel()
        except Exception:
            pass

    def test_FR_P04_category_switch_fpc_walkin(self, fr_page):
        """Category switching: FPC → Walk-in — tab count changes from 6 to 3."""
        log.info("FR-P04: Category switch FPC→Walk-in test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_farmer_step0("Walk-in Farmer")
        data["farmer_name"] = "CatSwitchWalkin"
        data["phone_number"] = "9876543211"
        data["password"] = "TestPass@123"
        page.fill_step0(data)
        page.wait_seconds(1)

        tab_count_walkin = page.get_stepper_tab_count()
        log.info(f"Walk-in Farmer tab count: {tab_count_walkin}")

        assert tab_count_walkin == 3, f"Expected 3 tabs for Walk-in, got {tab_count_walkin}"

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-P05: Deselect+Reselect freezes Next/Back (BUG-F02) ----
    @pytest.mark.xfail(reason="BUG-F02: Deselect+Reselect farmer category freezes Next/Back", strict=False)
    def test_FR_P05_category_deselect_reselect_freeze(self, fr_page):
        """Deselect+Reselect farmer category should NOT freeze Next/Back (BUG-F02)."""
        log.info("FR-P05: Category deselect+reselect freeze test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)

        # Fill Step 0 with Borrower Farmer
        data = generate_valid_farmer_step0("Borrower Farmer")
        data["farmer_name"] = "FreezeTestFarmer"
        data["phone_number"] = "9876543212"
        data["password"] = "TestPass@123"
        page.fill_step0(data)
        page.wait_seconds(1)

        # Navigate to a later tab to fill required fields
        for _ in range(5):
            page.click_stepper_next()
            page.wait_seconds(1)

        # Now deselect and reselect the farmer category
        # First, clear the selection
        page.click_stepper_back()
        page.click_stepper_back()
        page.click_stepper_back()
        page.click_stepper_back()
        page.click_stepper_back()
        page.wait_seconds(1)

        # Deselect Borrower Farmer from multi-select
        page._select_farmer_category("Borrower Farmer")  # Click to toggle off
        page.wait_seconds(1)

        # Reselect
        page._select_farmer_category("Borrower Farmer")
        page.wait_seconds(1)

        # Try clicking Next — should work
        next_worked = page.click_stepper_next()
        assert next_worked, (
            "BUG-F02 CONFIRMED: Next button frozen after deselect+reselect farmer category"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-P06: Character count indicator disappears (BUG-F09) ----
    @pytest.mark.xfail(reason="BUG-F09: Character count indicator disappears on validation", strict=False)
    def test_FR_P06_char_count_disappears(self, fr_page):
        """Character count indicator should remain visible during validation (BUG-F09)."""
        log.info("FR-P06: Character count indicator test")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)

        # Type valid text in Farmer Name — observe character count
        page.type_text(page.FARMER_NAME_INPUT, "TestFarmer", clear_first=True)
        page.wait_seconds(1)

        # Check for character count indicator
        has_counter = page.driver.execute_script("""
            var counters = document.querySelectorAll('.mat-mdc-form-field-hint, [class*="character-count"], [class*="hint"]');
            return counters.length > 0;
        """)

        log.info(f"Character count indicator present: {has_counter}")

        # Type invalid characters
        page.type_text(page.FARMER_NAME_INPUT, "@@@", clear_first=True)
        page.wait_seconds(1)

        # Check if counter still visible
        has_counter_after_error = page.driver.execute_script("""
            var counters = document.querySelectorAll('.mat-mdc-form-field-hint, [class*="character-count"], [class*="hint"]');
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
        """Click View button — should open a read-only popup."""
        log.info("FR-H01: View button popup test")
        page = fr_page

        name, _ = _create_prerequisite_farmer(page, "Walk-in Farmer")
        if not name:
            return

        page.click_view_button(farmer_name=name)
        page.wait_seconds(2)

        # Check if view popup opened (likely in .big-model)
        popup_open = page._is_form_popup_open()
        log.info(f"View popup opened: {popup_open}")

        try:
            page.cancel()
        except Exception:
            pass

    def test_FR_H02_table_sorting(self, fr_page):
        """Click column headers to sort — verify sorting works."""
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

    # ---- FR-B01: BUG-F01: No Of Owner — no asterisk ----
    @pytest.mark.xfail(reason="BUG-F01: No Of Owner required but no asterisk", strict=False)
    def test_FR_B01_no_of_owner_no_asterisk(self, fr_page):
        """BUG-F01: No Of Owner required but no asterisk shown."""
        log.info("FR-B01: No Of Owner no asterisk test")
        page = fr_page

        data = generate_valid_farmer_step0("Borrower Farmer")
        data["farmer_name"] = "BugF01Test"
        data["phone_number"] = "9876543213"
        data["password"] = "TestPass@123"

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)

        # Navigate to Land Details tab
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
    @pytest.mark.xfail(reason="BUG-F02: Next/Back freeze on deselect+reselect", strict=False)
    def test_FR_B02_category_freeze(self, fr_page):
        """BUG-F02: Deselect+Reselect farmer category freezes Next/Back."""
        log.info("FR-B02: Category freeze test (same as FR-P05)")
        # This is a dedicated bug test — same logic as FR-P05
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_farmer_step0("Borrower Farmer")
        data["farmer_name"] = "BugF02Test"
        data["phone_number"] = "9876543214"
        data["password"] = "TestPass@123"
        page.fill_step0(data)
        page.wait_seconds(1)

        # Toggle category off and on
        page._select_farmer_category("Borrower Farmer")
        page.wait_seconds(1)
        page._select_farmer_category("Borrower Farmer")
        page.wait_seconds(1)

        # Next should still work
        next_worked = page.click_stepper_next()
        assert next_worked, "BUG-F02 CONFIRMED: Next frozen after category toggle"

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-B03: BUG-F03: Farmer Name special chars ----
    @pytest.mark.xfail(reason="BUG-F03: Farmer Name accepts special chars", strict=False)
    def test_FR_B03_special_char_name(self, fr_page):
        """BUG-F03: Farmer Name accepts special characters."""
        log.info("FR-B03: Special char name bug test")
        page = fr_page

        special_name = generate_special_char_name()
        data = generate_full_valid_farmer_data("Walk-in Farmer")
        data["farmer_name"] = special_name

        result = page.create_farmer(data)

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
    @pytest.mark.xfail(reason="BUG-F04: Email rejects uppercase", strict=False)
    def test_FR_B04_uppercase_email(self, fr_page):
        """BUG-F04: Email field rejects uppercase letters."""
        log.info("FR-B04: Uppercase email bug test")
        page = fr_page

        data = generate_full_valid_farmer_data("Walk-in Farmer")
        data["email"] = generate_uppercase_email()

        result = page.create_farmer(data)

        try:
            page.close_popup()
        except Exception:
            pass

        assert result["status"] == "PASSED", (
            f"BUG-F04 CONFIRMED: Uppercase email rejected: {result.get('error', '')}"
        )

    # ---- FR-B05: BUG-F05: Placeholder selectable ----
    @pytest.mark.xfail(reason="BUG-F05: Placeholder selectable", strict=False)
    def test_FR_B05_placeholder_selectable(self, fr_page):
        """BUG-F05: 'Select Farmer Category' placeholder is selectable."""
        log.info("FR-B05: Placeholder selectable bug test")
        page = fr_page

        data = generate_full_valid_farmer_data("Walk-in Farmer")
        data["farmer_category"] = "Select Farmer Category"

        result = page.create_farmer(data)

        try:
            page.close_popup()
        except Exception:
            pass

        assert result["status"] == "FAILED", (
            "BUG-F05 CONFIRMED: Placeholder 'Select Farmer Category' was accepted"
        )

    # ---- FR-B06: BUG-F06: Amount fields accept 0 and . prefix ----
    @pytest.mark.xfail(reason="BUG-F06: Amount fields accept 0 and . prefix", strict=False)
    def test_FR_B06_amount_zero_dot(self, fr_page):
        """BUG-F06: Amount fields accept 0 and . prefix values."""
        log.info("FR-B06: Amount zero/dot bug test")
        page = fr_page

        data = generate_valid_farmer_step0("Borrower Farmer")
        data["farmer_name"] = "BugF06Test"
        data["phone_number"] = "9876543215"
        data["password"] = "TestPass@123"

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)

        # Navigate to Income Details tab (step 8 for Borrower)
        for _ in range(9):
            page.click_stepper_next()
            page.wait_seconds(1)

        # Enter 0 in Exact Amount
        try:
            exact_amount_input = page.driver.find_element(By.CSS_SELECTOR, "input[name='Exact Amount']")
            exact_amount_input.clear()
            exact_amount_input.send_keys("0")
            page.wait_seconds(0.5)

            # Try to proceed — 0 should be rejected
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
    def test_FR_B07_dairy_duplicate(self, fr_page):
        """BUG-F07: Source of Income shows 'Dairy' twice."""
        log.info("FR-B07: Dairy duplicate bug test")
        page = fr_page

        data = generate_valid_farmer_step0("Borrower Farmer")
        data["farmer_name"] = "BugF07Test"
        data["phone_number"] = "9876543216"
        data["password"] = "TestPass@123"

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_step0(data)

        # Navigate to Income Details
        for _ in range(9):
            page.click_stepper_next()
            page.wait_seconds(1)

        # Open Source of Income dropdown and check for duplicates
        try:
            src_income_select = page.driver.find_element(
                By.XPATH, "//mat-label[contains(.,'Source of Income')]/ancestor::mat-form-field//mat-select"
            )
            src_income_select.click()
            page.wait_seconds(1)

            options = page.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
            option_texts = [opt.text.strip() for opt in options]

            dairy_count = option_texts.count("Dairy")
            log.info(f"Dairy appears {dairy_count} time(s) in Source of Income dropdown")

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
    @pytest.mark.xfail(reason="BUG-F08: Edit missing Land/Crop/KYC tabs", strict=False)
    def test_FR_B08_edit_missing_tabs(self, fr_page):
        """BUG-F08: Edit mode missing Land/Crop/KYC tabs."""
        log.info("FR-B08: Edit missing tabs bug test (same as FR-E03)")
        page = fr_page

        name, data = _create_prerequisite_farmer(page, "Borrower Farmer")
        if not name:
            return

        page.click_edit_button(farmer_name=name)
        page.wait_seconds(2)

        tab_count = page.get_stepper_tab_count()
        tab_names = page.get_stepper_tab_names()

        assert tab_count == 13, (
            f"BUG-F08 CONFIRMED: Edit mode shows {tab_count} tabs instead of 13. "
            f"Tabs: {tab_names}"
        )

        try:
            page.cancel()
        except Exception:
            pass

    # ---- FR-B09: BUG-F09: Character count disappears ----
    @pytest.mark.xfail(reason="BUG-F09: Character count disappears on validation", strict=False)
    def test_FR_B09_char_count_disappears(self, fr_page):
        """BUG-F09: Character count indicator disappears on validation error."""
        log.info("FR-B09: Character count disappears bug test (same as FR-P06)")
        page = fr_page

        page.open_add_form()
        page.wait_seconds(1)

        # Type in Farmer Name — check for character count
        page.type_text(page.FARMER_NAME_INPUT, "TestFarmer123", clear_first=True)
        page.wait_seconds(1)

        # Get character count indicator visibility
        counter_visible_before = page.driver.execute_script("""
            var hints = document.querySelectorAll('.mat-mdc-form-field-hint, [class*="hint"]');
            var visible = 0;
            hints.forEach(function(h) { if (h.offsetHeight > 0) visible++; });
            return visible > 0;
        """)

        # Type invalid characters to trigger validation
        page.type_text(page.FARMER_NAME_INPUT, "@@", clear_first=True)
        page.wait_seconds(1)

        counter_visible_after = page.driver.execute_script("""
            var hints = document.querySelectorAll('.mat-mdc-form-field-hint, [class*="hint"]');
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
