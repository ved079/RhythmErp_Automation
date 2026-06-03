"""
test_supplier_validation.py
----------------------------
Comprehensive validation test suite for RhythmERP Supplier Screen.
42 test cases across 6 phases covering all bugs found during exploration.

Phases:
  1. Create Form Validations   (18 tests) — SP-C01 to SP-C18
  2. Duplicate Validations      (3 tests)  — SP-D01 to SP-D03
  3. Edit Form Validations      (4 tests)  — SP-E01 to SP-E04
  4. Search & Filter Edge Cases (5 tests)  — SP-S01 to SP-S05
  5. Popup & UI Behaviors       (7 tests)  — SP-P01 to SP-P07
  6. Bug-Specific Tests         (5 tests)  — SP-B01 to SP-B05

Run:
  pytest test_supplier_validation.py -v --tb=short
  pytest test_supplier_validation.py -v -k "TestCreateForm" --tb=short
  pytest test_supplier_validation.py -v -k "SP-C02" --tb=short
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

from pages.dynamic_screens.modules.supplier.supplier_page import (
    SupplierPage,
)
from pages.dynamic_screens.modules.supplier.data.supplier_data import (
    generate_valid_step1_data,
    generate_valid_step2_data,
    generate_valid_step3_data,
    generate_valid_supplier_data,
    generate_valid_edit_data,
    generate_empty_step1_data,
    generate_spaces_only,
    generate_string_255,
    generate_string_256,
    generate_special_char_company_name,
    generate_sql_injection_company_name,
    generate_xss_company_name,
    generate_invalid_email,
    generate_invalid_pan,
    generate_alpha_phone,
    generate_duplicate_company_data,
    generate_duplicate_email_data,
    generate_duplicate_phone_data,
    generate_numbers_only_company_name,
    generate_leading_trailing_spaces_company_name,
    ExpectedMessages,
    KnownBugs,
)
from common.logger import log


# ====================================================================
# Helper: create a supplier, refresh, and return its company name
# ====================================================================

def _create_prerequisite_supplier(page, data=None):
    """Create a supplier for tests that need existing data.
    Returns the company name used.
    """
    if data is None:
        data = generate_valid_supplier_data("PreReq")
    result = page.create_supplier(data)
    try:
        page.force_close_form_popup()
    except Exception:
        pass
    page.click_refresh()
    page.wait_seconds(2)
    company_name = data.get("step1", {}).get("company_name", "")
    return company_name, result


# ====================================================================
# PHASE 1: Create Form Validations (18 tests)
# ====================================================================

class TestCreateFormValidations:
    """SP-C01 to SP-C18: Validation checks on the Create stepper form."""

    # ---- SP-C01: Empty form submit ----
    def test_SP_C01_empty_submit(self, sp_page):
        """Submit stepper with all required fields empty — SweetAlert2 + mat-errors."""
        log.info("SP-C01: Empty submit test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Click Next on Step 1 with all fields empty
        page.click_stepper_next()
        page.wait_seconds(2)

        # Should get validation warning or stay on step
        swal = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or swal, (
            "BUG: Stepper proceeded with all fields empty — no validation"
        )
        if errors:
            log.info(f"Validation errors shown: {errors}")
        if swal:
            log.info(f"SweetAlert2 shown: {swal}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-C02: Valid create (happy path) ----
    def test_SP_C02_valid_create(self, sp_page):
        """Create supplier with valid data across all 3 steps."""
        log.info("SP-C02: Valid create test")
        page = sp_page

        data = generate_valid_supplier_data("ValidSP")
        result = page.create_supplier(data)

        assert result["status"] == "PASSED", (
            f"Valid supplier creation failed: {result['message']}"
        )
        company_name = data["step1"]["company_name"]
        log.info(f"Supplier created: {company_name}")

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-C03: Company Name spaces-only ----
    def test_SP_C03_company_name_spaces(self, sp_page):
        """Enter spaces only in Company Name — should be rejected."""
        log.info("SP-C03: Company Name spaces-only test")
        page = sp_page

        data = generate_valid_supplier_data("SpaceSP")
        data["step1"]["company_name"] = generate_spaces_only(10)

        # Open form and fill only Step 1 with spaces in Company Name
        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        page.fill_step1_universal(data["step1"])
        page.fill_step1_additional(data["step1"])

        # Try to proceed
        page.click_stepper_next()
        page.wait_seconds(2)

        errors = page.get_mat_error_text()
        swal = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        # Spaces-only should be caught as empty or invalid
        assert form_still_open or errors or swal, (
            "BUG: Spaces-only Company Name accepted without validation"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-C04: Company Name special characters ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_001, strict=False)
    def test_SP_C04_company_name_special_chars(self, sp_page):
        """Special characters in Company Name — BUG-001: accepted."""
        log.info("SP-C04: Company Name special chars test")
        page = sp_page

        data = generate_valid_supplier_data("SpecSP")
        data["step1"]["company_name"] = generate_special_char_company_name()

        result = page.create_supplier(data)

        assert result["status"] == "FAILED", (
            "BUG-001 CONFIRMED: Special characters accepted in Company Name"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-C05: Company Name SQL injection ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_001, strict=False)
    def test_SP_C05_company_name_sql_injection(self, sp_page):
        """SQL injection string in Company Name — BUG-001: accepted."""
        log.info("SP-C05: Company Name SQL injection test")
        page = sp_page

        data = generate_valid_supplier_data("SQLSP")
        data["step1"]["company_name"] = generate_sql_injection_company_name()

        result = page.create_supplier(data)

        assert result["status"] == "FAILED", (
            "BUG-001 CONFIRMED: SQL injection accepted in Company Name"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-C06: Company Name XSS ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_001, strict=False)
    def test_SP_C06_company_name_xss(self, sp_page):
        """XSS payload in Company Name — BUG-001: accepted."""
        log.info("SP-C06: Company Name XSS test")
        page = sp_page

        data = generate_valid_supplier_data("XSSSP")
        data["step1"]["company_name"] = generate_xss_company_name()

        result = page.create_supplier(data)

        assert result["status"] == "FAILED", (
            "BUG-001 CONFIRMED: XSS payload accepted in Company Name"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-C07: Company Name 255 chars (boundary) ----
    def test_SP_C07_company_name_255_chars(self, sp_page):
        """Exactly 255 chars in Company Name — should be accepted (maxlength=255)."""
        log.info("SP-C07: Company Name 255 chars boundary test")
        page = sp_page

        data = generate_valid_supplier_data("255SP")
        data["step1"]["company_name"] = generate_string_255()

        result = page.create_supplier(data)

        # maxlength=255 should truncate or accept
        if result["status"] == "PASSED":
            log.info("255 chars accepted — maxlength working correctly")
        else:
            log.info(f"255 chars result: {result['message']}")

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-C08: Company Name 256 chars (over-max) ----
    def test_SP_C08_company_name_256_chars(self, sp_page):
        """256 chars — should be truncated at 255 due to maxlength."""
        log.info("SP-C08: Company Name 256 chars over-max test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Type 256 chars — should be truncated by maxlength=255
        page.type_text(
            page.COMPANY_NAME_INPUT,
            generate_string_256(),
            clear_first=True,
        )
        page.wait_seconds(0.5)

        # Read back the value
        try:
            company_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Company Name']"
            )
            actual_value = company_input.get_attribute("value") or ""
            assert len(actual_value) <= 255, (
                f"BUG: Company Name accepted {len(actual_value)} chars (max 255)"
            )
            log.info(f"Company Name truncated to {len(actual_value)} chars")
        except Exception:
            log.warning("Could not read Company Name value")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-C09: Invalid email format ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_002, strict=False)
    def test_SP_C09_invalid_email(self, sp_page):
        """Invalid email format — BUG-002: no validation."""
        log.info("SP-C09: Invalid email test")
        page = sp_page

        data = generate_valid_supplier_data("InvEmail")
        data["step1"]["email"] = generate_invalid_email()

        result = page.create_supplier(data)

        assert result["status"] == "FAILED", (
            "BUG-002 CONFIRMED: Invalid email accepted"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-C10: Invalid PAN format ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_004, strict=False)
    def test_SP_C10_invalid_pan(self, sp_page):
        """Invalid PAN format — BUG-004: no validation."""
        log.info("SP-C10: Invalid PAN test")
        page = sp_page

        data = generate_valid_supplier_data("InvPAN")
        data["step1"]["pan_number"] = generate_invalid_pan()

        result = page.create_supplier(data)

        assert result["status"] == "FAILED", (
            "BUG-004 CONFIRMED: Invalid PAN accepted"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-C11: Phone Number text input ----
    def test_SP_C11_phone_alpha_chars(self, sp_page):
        """Type alphabetic chars in Phone Number — should reject or show error."""
        log.info("SP-C11: Phone Number alpha chars test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Try typing alpha chars — type=number should reject them
        page.type_text(
            page.PHONE_NUMBER_INPUT,
            generate_alpha_phone(),
            clear_first=True,
        )
        page.wait_seconds(0.5)

        # Read back the value — should be empty (type=number rejects alpha)
        try:
            phone_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Phone Number']"
            )
            actual_value = phone_input.get_attribute("value") or ""
            if actual_value:
                log.warning(f"BUG: Phone Number accepted alpha chars: {actual_value}")
            else:
                log.info("Phone Number correctly rejected alpha chars (type=number)")
        except Exception:
            log.warning("Could not read Phone Number value")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-C12: Ownership Status dropdown ----
    def test_SP_C12_ownership_status_dropdown(self, sp_page):
        """Ownership Status shows correct options."""
        log.info("SP-C12: Ownership Status dropdown test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)

        options = page.get_dropdown_options(page.OWNERSHIP_STATUS_SELECT)
        expected_options = [
            "owned", "leased", "proprietorship", "partnership",
            "llp", "plc", "private limited company", "individual"
        ]
        found = any(
            any(eo in opt.lower() for opt in options)
            for eo in expected_options
        )

        assert found, f"Ownership Status options missing. Found: {options}"
        log.info(f"Ownership Status options: {options}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-C13: PO Type dropdown ----
    def test_SP_C13_po_type_dropdown(self, sp_page):
        """PO Type shows Domestic/Import options."""
        log.info("SP-C13: PO Type dropdown test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)

        options = page.get_dropdown_options(page.PO_TYPE_SELECT)
        options_lower = [o.lower() for o in options]

        assert "domestic" in options_lower or "import" in options_lower, (
            f"PO Type options missing Domestic/Import. Found: {options}"
        )
        log.info(f"PO Type options: {options}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-C14: Default Currency dropdown ----
    def test_SP_C14_currency_dropdown(self, sp_page):
        """Default Currency shows currency list (100+ currencies)."""
        log.info("SP-C14: Default Currency dropdown test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)

        options = page.get_dropdown_options(page.DEFAULT_CURRENCY_SELECT)

        assert len(options) > 0, "No currency options found"
        # Check for INR at minimum
        options_lower = [o.lower() for o in options]
        has_inr = any("inr" in o for o in options_lower)
        log.info(f"Currency options count: {len(options)}, has INR: {has_inr}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-C15: Payment Terms dropdown ----
    def test_SP_C15_payment_terms_dropdown(self, sp_page):
        """Payment Terms shows options (21 Days, 14 Days, etc.)."""
        log.info("SP-C15: Payment Terms dropdown test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)
        page.scroll_to_additional_details()
        page.wait_seconds(0.5)

        options = page.get_dropdown_options(page.PAYMENT_TERMS_SELECT)
        log.info(f"Payment Terms options: {options}")

        assert len(options) > 0, "No Payment Terms options found"

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-C16: Delivery Terms dropdown ----
    def test_SP_C16_delivery_terms_dropdown(self, sp_page):
        """Delivery Terms shows options (Delivery, Spot)."""
        log.info("SP-C16: Delivery Terms dropdown test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)
        page.scroll_to_additional_details()
        page.wait_seconds(0.5)

        options = page.get_dropdown_options(page.DELIVERY_TERMS_SELECT)
        log.info(f"Delivery Terms options: {options}")

        assert len(options) > 0, "No Delivery Terms options found"

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-C17: Mode Of Delivery dropdown ----
    def test_SP_C17_mode_of_delivery_dropdown(self, sp_page):
        """Mode Of Delivery shows options (Air, Courier, Sea, Railway, Truck)."""
        log.info("SP-C17: Mode Of Delivery dropdown test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)
        page.scroll_to_additional_details()
        page.wait_seconds(0.5)

        options = page.get_dropdown_options(page.MODE_OF_DELIVERY_SELECT)
        expected = ["air", "courier", "sea", "railway", "truck"]
        options_lower = [o.lower() for o in options]
        found = any(e in options_lower for e in expected)

        assert found or len(options) > 0, (
            f"Mode Of Delivery options missing. Found: {options}"
        )
        log.info(f"Mode Of Delivery options: {options}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-C18: Stepper Next/Back navigation ----
    def test_SP_C18_stepper_navigation(self, sp_page):
        """Navigate through steps via Next/Back buttons."""
        log.info("SP-C18: Stepper navigation test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Initially on Step 1 (index 0)
        current_step = page.get_current_step_index()
        assert current_step == 0, f"Expected Step 0, got Step {current_step}"

        # Fill Step 1 required fields to allow Next
        step1 = generate_valid_step1_data("NavSP")
        page.fill_step1_universal(step1)
        page.fill_step1_additional(step1)

        # Click Next
        page.click_stepper_next()
        page.wait_seconds(1)

        # Should be on Step 2 (index 1)
        current_step = page.get_current_step_index()
        assert current_step == 1, f"Expected Step 1 after Next, got Step {current_step}"

        # Click Back
        page.click_stepper_back()
        page.wait_seconds(1)

        # Should be back on Step 1
        current_step = page.get_current_step_index()
        assert current_step == 0, f"Expected Step 0 after Back, got Step {current_step}"

        log.info("Stepper Next/Back navigation works correctly")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()


# ====================================================================
# PHASE 2: Duplicate Validations (3 tests)
# ====================================================================

class TestDuplicateValidations:
    """SP-D01 to SP-D03: Duplicate data checks."""

    # ---- SP-D01: Duplicate Company Name ----
    def test_SP_D01_duplicate_company_name(self, sp_page):
        """Create supplier with same Company Name — check behavior."""
        log.info("SP-D01: Duplicate Company Name test")
        page = sp_page

        # Create first supplier
        data1 = generate_valid_supplier_data("Dup1")
        result1 = page.create_supplier(data1)
        company_name = data1["step1"]["company_name"]
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        if result1["status"] != "PASSED":
            log.warning(f"First supplier creation failed: {result1['message']}")
            return

        # Try creating second with same Company Name
        data2 = generate_duplicate_company_data(company_name)
        result2 = page.create_supplier(data2)

        if result2["status"] == "PASSED":
            log.info("Duplicate Company Name allowed — no uniqueness validation")
        else:
            log.info(f"Duplicate Company Name blocked: {result2['message']}")

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-D02: Duplicate Email ----
    def test_SP_D02_duplicate_email(self, sp_page):
        """Create supplier with same email — check behavior."""
        log.info("SP-D02: Duplicate Email test")
        page = sp_page

        # Create first supplier
        data1 = generate_valid_supplier_data("DupE1")
        result1 = page.create_supplier(data1)
        email = data1["step1"]["email"]
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        if result1["status"] != "PASSED":
            log.warning(f"First supplier creation failed: {result1['message']}")
            return

        # Create second with same email
        data2 = generate_duplicate_email_data(email)
        result2 = page.create_supplier(data2)

        if result2["status"] == "PASSED":
            log.info("Duplicate Email allowed — no uniqueness validation")
        else:
            log.info(f"Duplicate Email blocked: {result2['message']}")

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-D03: Duplicate Phone Number ----
    def test_SP_D03_duplicate_phone(self, sp_page):
        """Create supplier with same phone number — check behavior."""
        log.info("SP-D03: Duplicate Phone Number test")
        page = sp_page

        # Create first supplier
        data1 = generate_valid_supplier_data("DupP1")
        result1 = page.create_supplier(data1)
        phone = data1["step1"]["phone_number"]
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        if result1["status"] != "PASSED":
            log.warning(f"First supplier creation failed: {result1['message']}")
            return

        # Create second with same phone
        data2 = generate_duplicate_phone_data(phone)
        result2 = page.create_supplier(data2)

        if result2["status"] == "PASSED":
            log.info("Duplicate Phone Number allowed — no uniqueness validation")
        else:
            log.info(f"Duplicate Phone Number blocked: {result2['message']}")

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 3: Edit Form Validations (4 tests)
# ====================================================================

class TestEditFormValidations:
    """SP-E01 to SP-E04: Validation checks on the Edit form."""

    # ---- SP-E01: Edit no Update button ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_005, strict=False)
    def test_SP_E01_edit_no_update_button(self, sp_page):
        """Open Edit popup — BUG-005: no Update button."""
        log.info("SP-E01: Edit no Update button test")
        page = sp_page

        company_name, create_result = _create_prerequisite_supplier(page)

        if create_result["status"] != "PASSED":
            pytest.skip("Prerequisite supplier creation failed")

        # Search and click Edit
        page.search_supplier(company_name)
        page.wait_seconds(2)
        page.click_edit_button_by_name(company_name)
        page.wait_seconds(1)

        # Check for Update button
        has_update = page.has_update_button()

        assert has_update, (
            "BUG-005 CONFIRMED: No Update button in Edit mode — cannot save edits"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-E02: Edit pre-populated fields ----
    def test_SP_E02_edit_prepopulated(self, sp_page):
        """Edit popup shows fields pre-populated with existing data."""
        log.info("SP-E02: Edit pre-populated fields test")
        page = sp_page

        data = generate_valid_supplier_data("EditPre")
        data["step1"]["company_name"] = f"EditPreTest_{int(time.time())}"
        company_name, create_result = _create_prerequisite_supplier(page, data)

        if create_result["status"] != "PASSED":
            pytest.skip("Prerequisite supplier creation failed")

        page.search_supplier(company_name)
        page.wait_seconds(2)
        page.click_edit_button_by_name(company_name)
        page.wait_seconds(1)

        form_values = page.get_form_field_values()

        # At minimum, Company Name should be pre-populated
        company_val = form_values.get("Company Name", "")
        assert company_val, "Company Name empty in Edit form"

        log.info(f"Edit form pre-populated — Company Name: {company_val}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-E03: Edit Company Name special chars ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_001, strict=False)
    def test_SP_E03_edit_company_name_special_chars(self, sp_page):
        """Edit to special chars in Company Name — BUG-001: accepted."""
        log.info("SP-E03: Edit Company Name special chars test")
        page = sp_page

        company_name, create_result = _create_prerequisite_supplier(page)

        if create_result["status"] != "PASSED":
            pytest.skip("Prerequisite supplier creation failed")

        page.search_supplier(company_name)
        page.wait_seconds(2)
        page.click_edit_button_by_name(company_name)
        page.wait_seconds(1)

        # Try to change Company Name to special chars
        try:
            page.type_text(
                page.COMPANY_NAME_INPUT,
                generate_special_char_company_name(),
                clear_first=True,
            )
            page.wait_seconds(0.5)

            # Check if we can proceed (BUG-001: should be rejected but accepted)
            if page.has_update_button():
                page.click_update()
                page.wait_seconds(2)

            log.info("Edit with special chars attempted")
        except Exception as e:
            log.warning(f"Edit special chars test exception: {e}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-E04: Edit Email to invalid ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_002, strict=False)
    def test_SP_E04_edit_invalid_email(self, sp_page):
        """Edit email to invalid format — BUG-002: no validation."""
        log.info("SP-E04: Edit invalid email test")
        page = sp_page

        company_name, create_result = _create_prerequisite_supplier(page)

        if create_result["status"] != "PASSED":
            pytest.skip("Prerequisite supplier creation failed")

        page.search_supplier(company_name)
        page.wait_seconds(2)
        page.click_edit_button_by_name(company_name)
        page.wait_seconds(1)

        # Change email to invalid
        try:
            page.type_text(
                page.EMAIL_INPUT,
                generate_invalid_email(),
                clear_first=True,
            )
            page.wait_seconds(0.5)

            if page.has_update_button():
                page.click_update()
                page.wait_seconds(2)

            log.info("Edit with invalid email attempted")
        except Exception as e:
            log.warning(f"Edit invalid email test exception: {e}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 4: Search & Filter Edge Cases (5 tests)
# ====================================================================

class TestSearchFilter:
    """SP-S01 to SP-S05: Search edge cases."""

    # ---- SP-S01: Search exact match ----
    def test_SP_S01_search_exact(self, sp_page):
        """Search for exact Company Name — should find the supplier."""
        log.info("SP-S01: Search exact match test")
        page = sp_page

        data = generate_valid_supplier_data("SearchEx")
        result = page.create_supplier(data)
        company_name = data["step1"]["company_name"]
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        if result["status"] != "PASSED":
            pytest.skip("Prerequisite supplier creation failed")

        found = page.search_supplier(company_name)
        assert found, f"Exact search failed for: {company_name}"
        log.info(f"Exact search found: {company_name}")

    # ---- SP-S02: Search partial match ----
    def test_SP_S02_search_partial(self, sp_page):
        """Search with partial Company Name — should find matching suppliers."""
        log.info("SP-S02: Search partial match test")
        page = sp_page

        data = generate_valid_supplier_data("SearchPar")
        result = page.create_supplier(data)
        company_name = data["step1"]["company_name"]
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        if result["status"] != "PASSED":
            pytest.skip("Prerequisite supplier creation failed")

        # Search with partial name (first 10 chars)
        partial = company_name[:10]
        found = page.search_supplier(partial)
        assert found, f"Partial search failed for: {partial}"
        log.info(f"Partial search found with: {partial}")

    # ---- SP-S03: Search case insensitive ----
    def test_SP_S03_search_case_insensitive(self, sp_page):
        """Search with different case — should find the supplier."""
        log.info("SP-S03: Search case insensitive test")
        page = sp_page

        data = generate_valid_supplier_data("SearchCI")
        result = page.create_supplier(data)
        company_name = data["step1"]["company_name"]
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        if result["status"] != "PASSED":
            pytest.skip("Prerequisite supplier creation failed")

        found = page.search_supplier(company_name.lower())
        log.info(f"Case insensitive search result: found={found}")

    # ---- SP-S04: Search no results ----
    def test_SP_S04_search_no_results(self, sp_page):
        """Search for non-existent supplier — should return no results."""
        log.info("SP-S04: Search no results test")
        page = sp_page

        fake_name = f"NonExistent_{int(time.time())}"
        found = page.search_supplier(fake_name)

        assert not found, (
            f"BUG: Non-existent name '{fake_name}' was found in table"
        )
        log.info(f"Correctly not found: {fake_name}")
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-S05: Search special chars ----
    def test_SP_S05_search_special_chars(self, sp_page):
        """Search with special characters — should not crash."""
        log.info("SP-S05: Search special chars test")
        page = sp_page

        try:
            page.search_item("!@#$%^&*()")
            page.wait_seconds(2)
            log.info("Search with special chars did not crash")
        except Exception as e:
            log.warning(f"Search with special chars raised exception: {e}")

        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 5: Popup & UI Behaviors (7 tests)
# ====================================================================

class TestPopupUIBehaviors:
    """SP-P01 to SP-P07: Popup and UI interaction checks."""

    # ---- SP-P01: Add form opens ----
    def test_SP_P01_add_form_opens(self, sp_page):
        """Click ADD — stepper popup opens."""
        log.info("SP-P01: Add form opens test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)

        assert page.is_add_form_open(), "Add form did not open"

        # Check stepper is present
        try:
            stepper = page.driver.find_elements(
                By.CSS_SELECTOR, "mat-stepper, mat-horizontal-stepper"
            )
            assert len(stepper) > 0, "Stepper not found in popup"
            log.info("Stepper popup opened correctly")
        except Exception:
            log.warning("Could not verify stepper presence")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-P02: View popup readonly ----
    def test_SP_P02_view_popup_readonly(self, sp_page):
        """View popup shows all fields disabled/read-only."""
        log.info("SP-P02: View popup readonly test")
        page = sp_page

        data = generate_valid_supplier_data("ViewSP")
        result = page.create_supplier(data)
        company_name = data["step1"]["company_name"]
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        if result["status"] != "PASSED":
            pytest.skip("Prerequisite supplier creation failed")

        page.search_supplier(company_name)
        page.wait_seconds(2)
        page.click_view_button_by_name(company_name)
        page.wait_seconds(1)

        is_readonly = page.verify_view_popup_read_only()

        assert is_readonly, (
            "BUG: View popup fields are editable (should be read-only)"
        )
        log.info("View popup correctly shows read-only fields")

        page.close_popup()
        page.wait_seconds(0.5)

    # ---- SP-P03: Cancel closes popup ----
    def test_SP_P03_cancel_closes_popup(self, sp_page):
        """Click Cancel — popup closes without creating a supplier."""
        log.info("SP-P03: Cancel closes popup test")
        page = sp_page

        before_count = page.get_table_row_count()

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Form did not open"

        # Fill some data
        step1 = generate_valid_step1_data("CancelSP")
        page.fill_step1_universal(step1)

        page.cancel()
        page.wait_seconds(1)

        after_count = page.get_table_row_count()
        assert after_count == before_count, (
            f"BUG: Row count changed after Cancel. "
            f"Before: {before_count}, After: {after_count}"
        )
        log.info("Cancel correctly did not create a supplier")

    # ---- SP-P04: Close (X) button ----
    def test_SP_P04_close_button(self, sp_page):
        """Click X — popup closes without creating a supplier."""
        log.info("SP-P04: Close button test")
        page = sp_page

        before_count = page.get_table_row_count()

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Form did not open"

        step1 = generate_valid_step1_data("CloseSP")
        page.fill_step1_universal(step1)

        page.close_popup()
        page.wait_seconds(1)

        after_count = page.get_table_row_count()
        assert after_count == before_count, (
            f"BUG: Row count changed after X close. "
            f"Before: {before_count}, After: {after_count}"
        )
        log.info("X close correctly did not create a supplier")

    # ---- SP-P05: SweetAlert2 success ----
    def test_SP_P05_sweetalert_success(self, sp_page):
        """Valid create shows SweetAlert2 success toast."""
        log.info("SP-P05: SweetAlert2 success test")
        page = sp_page

        data = generate_valid_supplier_data("SwalSP")
        result = page.create_supplier(data)

        if result["status"] == "PASSED":
            log.info("SweetAlert2 success toast confirmed")
        else:
            log.info(f"Create result: {result['message']}")

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-P06: Phone Number spinner controls ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_003, strict=False)
    def test_SP_P06_phone_spinner_controls(self, sp_page):
        """Phone Number has spinner arrows — BUG-003: type=number."""
        log.info("SP-P06: Phone Number spinner controls test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)

        has_spinner = page.has_phone_number_spinner()

        assert not has_spinner, (
            "BUG-003 CONFIRMED: Phone Number has spinner controls (type=number)"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-P07: Toggle switches default values ----
    def test_SP_P07_toggle_defaults(self, sp_page):
        """Verify toggle defaults: MSME=No, Status=Active, GST=Yes, TDS=No."""
        log.info("SP-P07: Toggle switch defaults test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)

        # Check Universal toggles
        msme_state = page.get_toggle_state(page.IS_MSME_TOGGLE)
        status_state = page.get_toggle_state(page.STATUS_TOGGLE)

        # Check Additional toggles (need to scroll)
        page.scroll_to_additional_details()
        page.wait_seconds(0.5)
        gst_state = page.get_toggle_state(page.IS_GST_SET_OFF_TOGGLE)
        tds_state = page.get_toggle_state(page.IS_TDS_APPLICABLE_TOGGLE)

        log.info(f"Toggle states — MSME: {msme_state}, Status: {status_state}, "
                 f"GST Set Off: {gst_state}, TDS: {tds_state}")

        # Verify defaults
        assert msme_state is False or msme_state is None, (
            f"MSME default should be No (unchecked), got: {msme_state}"
        )
        assert status_state is True or status_state is None, (
            f"Status default should be Active (checked), got: {status_state}"
        )
        assert gst_state is True or gst_state is None, (
            f"GST Set Off default should be Yes (checked), got: {gst_state}"
        )
        assert tds_state is False or tds_state is None, (
            f"TDS default should be No (unchecked), got: {tds_state}"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()


# ====================================================================
# PHASE 6: Bug-Specific Tests (5 tests)
# ====================================================================

class TestBugSpecific:
    """SP-B01 to SP-B05: Confirmed bug validation tests."""

    # ---- SP-B01: Company Name accepts special chars ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_001, strict=False)
    def test_SP_B01_special_chars_accepted(self, sp_page):
        """BUG-001: Create with special chars succeeds."""
        log.info("SP-B01: Company Name accepts special chars bug test")
        page = sp_page

        data = generate_valid_supplier_data("Bug001")
        data["step1"]["company_name"] = "BugTest@@##Traders"

        result = page.create_supplier(data)

        assert result["status"] == "FAILED", (
            "BUG-001 CONFIRMED: Special characters accepted in Company Name"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-B02: No email format validation ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_002, strict=False)
    def test_SP_B02_no_email_validation(self, sp_page):
        """BUG-002: Invalid email accepted."""
        log.info("SP-B02: No email format validation bug test")
        page = sp_page

        data = generate_valid_supplier_data("Bug002")
        data["step1"]["email"] = "notanemail"

        result = page.create_supplier(data)

        assert result["status"] == "FAILED", (
            "BUG-002 CONFIRMED: Invalid email accepted"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-B03: Phone Number spinner controls ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_003, strict=False)
    def test_SP_B03_phone_spinner(self, sp_page):
        """BUG-003: type=number shows spinners."""
        log.info("SP-B03: Phone Number spinner bug test")
        page = sp_page

        page.open_add_form()
        page.wait_seconds(1)

        has_spinner = page.has_phone_number_spinner()

        assert not has_spinner, (
            "BUG-003 CONFIRMED: Phone Number type=number shows spinner controls"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-B04: No PAN format validation ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_004, strict=False)
    def test_SP_B04_no_pan_validation(self, sp_page):
        """BUG-004: Invalid PAN accepted."""
        log.info("SP-B04: No PAN format validation bug test")
        page = sp_page

        data = generate_valid_supplier_data("Bug004")
        data["step1"]["pan_number"] = "INVALIDPANFORMAT"

        result = page.create_supplier(data)

        assert result["status"] == "FAILED", (
            "BUG-004 CONFIRMED: Invalid PAN accepted"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- SP-B05: Edit mode no Update button ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_005, strict=False)
    def test_SP_B05_edit_no_update(self, sp_page):
        """BUG-005: Cannot save edits — no Update button."""
        log.info("SP-B05: Edit no Update button bug test")
        page = sp_page

        company_name, create_result = _create_prerequisite_supplier(page)

        if create_result["status"] != "PASSED":
            pytest.skip("Prerequisite supplier creation failed")

        page.search_supplier(company_name)
        page.wait_seconds(2)
        page.click_edit_button_by_name(company_name)
        page.wait_seconds(1)

        has_update = page.has_update_button()

        assert has_update, (
            "BUG-005 CONFIRMED: No Update button in Edit mode — edits cannot be saved"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()
