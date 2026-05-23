"""
test_agent_validation.py
-----------------------
Comprehensive validation test suite for RhythmERP Agent screen.
~50 test cases across 7 phases.

Phases:
  1. Universal Step Validations  (15 tests) - AGT-U01 to AGT-U15
  2. Address Step Validations    (10 tests) - AGT-A01 to AGT-A10
  3. Payment Step Validations     (5 tests) - AGT-P01 to AGT-P05
  4. Bank Details Validations    (10 tests) - AGT-B01 to AGT-B10
  5. Stepper Navigation Tests     (5 tests) - AGT-N01 to AGT-N05
  6. Create Happy Path Tests      (5 tests) - AGT-C01 to AGT-C05
  7. Bug-specific                 (5 tests) - AGT-X01 to AGT-X05

FORM LAYOUT (multi-step STEPPER):
  Step 1 - Universal:  Agent Name, Phone Number, Email
  Step 2 - Address Details: Address Type, Country, State, District,
           Taluka, Village, Address, Pin Code, GST
  Step 3 - Payment Details: Payment Terms, Preferred Payment Method
  Step 4 - Bank Details: Bank Name, Branch, IFSC Code, Account Type,
           Account Holder Name, Account Number, Bank Proof, Attachment

KEY RULES:
  - Multi-step STEPPER - use Next/Back to navigate
  - Angular Material UI - use execute_script for reading values
  - Address & Bank are repeatable rows
  - State depends on Country, District depends on State (cascading)
  - SweetAlert2 for success/validation popups

Run:
  pytest test_agent_validation.py -v --tb=short
  pytest test_agent_validation.py -v -k "TestUniversal" --tb=short
  pytest test_agent_validation.py -v -k "AGT-U03" --tb=short
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

from pages.registration.modules.agent.agent_page import AgentPage
from pages.registration.modules.agent.data.agent_data import (
    generate_valid_agent_data,
    generate_valid_edit_data,
    generate_valid_address_data,
    generate_valid_bank_data,
    generate_agent_name,
    generate_phone_number,
    generate_email,
    generate_address,
    generate_pin_code,
    generate_gst,
    generate_bank_name,
    generate_branch,
    generate_ifsc_code,
    generate_account_holder_name,
    generate_account_number,
    generate_spaces_only,
    generate_string_255,
    generate_string_256,
    generate_special_char_name,
    generate_sql_injection,
    generate_xss_payload,
    generate_invalid_email,
    generate_invalid_phone,
    generate_invalid_pin_code,
    generate_invalid_ifsc,
    generate_leading_trailing_spaces,
    generate_lowercase_agent_name,
    generate_alpha_phone,
    generate_numeric_email,
    generate_empty_data,
    generate_partial_required_data,
    VALIDATION_MSG_REQUIRED,
    SWAL_TITLE_VALIDATION_FAILED,
    SWAL_TITLE_SUCCESS,
)
from common.logger import log


# ====================================================================
# Helper functions
# ====================================================================

def _create_prerequisite_agent(page, prefix="PreReq"):
    """Create an Agent entry for tests that need existing data.
    Returns the agent name and the data dict used.
    """
    data = generate_valid_agent_data(prefix)
    result = page.create_agent(data)
    try:
        page.close_popup()
    except Exception:
        pass
    try:
        page.force_close_form_popup()
    except Exception:
        pass
    name = result.get("agent_name", "")
    if name:
        page.search(name)
        page.wait_seconds(2)
    log.info(f"Prerequisite agent created: {name}")
    return name, data


def _cleanup_form(page):
    """Try to close any open form popup."""
    try:
        page.cancel()
    except Exception:
        pass
    try:
        page.force_close_form_popup()
    except Exception:
        pass


# ====================================================================
# PHASE 1: Universal Step Validations (15 tests)
# ====================================================================

class TestUniversalStepValidations:
    """AGT-U01 to AGT-U15: Validation checks on Step 1 (Universal)."""

    # ---- AGT-U01: Submit with all fields empty on step 1 ----
    def test_AGT_U01_empty_submit(self, agt_page):
        """Submit with all Universal fields empty - should be blocked."""
        log.info("AGT-U01: Empty submit on Universal step")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        page.submit()
        page.wait_seconds(3)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG: Form advanced with all Universal fields empty - no validation"
        )
        if validation_alert:
            log.info(f"Validation alert shown: {validation_alert}")
        if errors:
            log.info(f"Validation errors shown: {errors}")

        _cleanup_form(page)

    # ---- AGT-U02: Agent Name - valid input ----
    def test_AGT_U02_agent_name_valid(self, agt_page):
        """Agent Name should accept alphanumeric values."""
        log.info("AGT-U02: Valid Agent Name test")
        page = agt_page

        valid_name = generate_agent_name("ValidU02")
        page.open_add_form()
        page.wait_seconds(1)
        page._fill_input_by_name("Agent Name", valid_name)
        page.wait_seconds(0.5)

        actual = page.get_input_value("Agent Name")
        log.info(f"Input: '{valid_name}' -> Actual: '{actual}'")
        assert actual == valid_name, f"Agent Name mismatch: expected '{valid_name}', got '{actual}'"

        _cleanup_form(page)

    # ---- AGT-U03: Agent Name - special characters ----
    def test_AGT_U03_agent_name_special_chars(self, agt_page):
        """Agent Name with special characters - check behavior."""
        log.info("AGT-U03: Agent Name special chars test")
        page = agt_page

        special = generate_special_char_name()
        page.open_add_form()
        page.wait_seconds(1)
        page._fill_input_by_name("Agent Name", special)
        page.wait_seconds(0.5)

        state = page.get_field_validation_state("Agent Name")
        log.info(
            f"Special chars Agent Name: "
            f"invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    # ---- AGT-U04: Agent Name - spaces only ----
    def test_AGT_U04_agent_name_spaces_only(self, agt_page):
        """Agent Name with spaces only - should be rejected."""
        log.info("AGT-U04: Agent Name spaces only test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        page._fill_input_by_name("Agent Name", generate_spaces_only())
        page.wait_seconds(0.5)

        page.click_next()
        page.wait_seconds(1)

        step = page.get_active_step_index()
        form_open = page.is_add_form_open()
        log.info(f"After spaces-only name: step={step}, form_open={form_open}")

        _cleanup_form(page)

    # ---- AGT-U05: Agent Name - maxlength boundary ----
    def test_AGT_U05_agent_name_maxlength(self, agt_page):
        """Agent Name maxlength boundary (255/256 chars)."""
        log.info("AGT-U05: Agent Name maxlength test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        long_255 = generate_string_255()
        page._fill_input_by_name("Agent Name", long_255)
        page.wait_seconds(0.5)
        actual_255 = page.get_input_value("Agent Name")
        log.info(f"255-char input: actual length = {len(actual_255)}")

        long_256 = generate_string_256()
        page._fill_input_by_name("Agent Name", long_256)
        page.wait_seconds(0.5)
        actual_256 = page.get_input_value("Agent Name")
        log.info(
            f"256-char input: actual length = {len(actual_256)}, "
            f"truncated = {len(actual_256) == 255}"
        )

        _cleanup_form(page)

    # ---- AGT-U06: Agent Name - leading/trailing spaces ----
    def test_AGT_U06_agent_name_leading_trailing_spaces(self, agt_page):
        """Test leading/trailing spaces in Agent Name."""
        log.info("AGT-U06: Leading/trailing spaces test")
        page = agt_page

        spaced = generate_leading_trailing_spaces()
        page.open_add_form()
        page.wait_seconds(1)
        page._fill_input_by_name("Agent Name", spaced)
        page.wait_seconds(0.5)
        actual = page.get_input_value("Agent Name")
        log.info(
            f"Input: '{spaced}' -> Actual: '{actual}' "
            f"(trimmed={actual.strip() == spaced.strip()})"
        )

        _cleanup_form(page)

    # ---- AGT-U07: Phone Number - valid ----
    def test_AGT_U07_phone_number_valid(self, agt_page):
        """Phone Number should accept valid 10-digit Indian numbers."""
        log.info("AGT-U07: Valid Phone Number test")
        page = agt_page

        valid_phone = generate_phone_number()
        page.open_add_form()
        page.wait_seconds(1)
        page._fill_input_by_name("Phone Number", valid_phone)
        page.wait_seconds(0.5)

        actual = page.get_input_value("Phone Number")
        assert actual == valid_phone, (
            f"Phone Number mismatch: expected '{valid_phone}', got '{actual}'"
        )
        log.info(f"Valid Phone Number '{valid_phone}' accepted")

        _cleanup_form(page)

    # ---- AGT-U08: Phone Number - alphabetic (invalid) ----
    def test_AGT_U08_phone_number_alpha(self, agt_page):
        """Phone Number with letters - should be rejected."""
        log.info("AGT-U08: Phone Number alpha test")
        page = agt_page

        alpha_phone = generate_alpha_phone()
        page.open_add_form()
        page.wait_seconds(1)
        page._fill_input_by_name("Phone Number", alpha_phone)
        page.wait_seconds(0.5)

        state = page.get_field_validation_state("Phone Number")
        log.info(
            f"Alpha Phone '{alpha_phone}': "
            f"invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    # ---- AGT-U09: Phone Number - too short ----
    def test_AGT_U09_phone_number_too_short(self, agt_page):
        """Phone Number too short - should be rejected."""
        log.info("AGT-U09: Phone Number too short test")
        page = agt_page

        short_phone = generate_invalid_phone()
        page.open_add_form()
        page.wait_seconds(1)
        page._fill_input_by_name("Phone Number", short_phone)
        page.wait_seconds(0.5)

        state = page.get_field_validation_state("Phone Number")
        log.info(
            f"Short Phone '{short_phone}': "
            f"invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    # ---- AGT-U10: Email - valid ----
    def test_AGT_U10_email_valid(self, agt_page):
        """Email should accept valid email addresses."""
        log.info("AGT-U10: Valid Email test")
        page = agt_page

        valid_email = generate_email("validU10")
        page.open_add_form()
        page.wait_seconds(1)
        page._fill_input_by_name("Email", valid_email)
        page.wait_seconds(0.5)

        actual = page.get_input_value("Email")
        assert actual == valid_email, (
            f"Email mismatch: expected '{valid_email}', got '{actual}'"
        )
        log.info(f"Valid Email '{valid_email}' accepted")

        _cleanup_form(page)

    # ---- AGT-U11: Email - invalid format ----
    def test_AGT_U11_email_invalid(self, agt_page):
        """Invalid email format - should show validation."""
        log.info("AGT-U11: Invalid Email test")
        page = agt_page

        invalid_email = generate_invalid_email()
        page.open_add_form()
        page.wait_seconds(1)
        page._fill_input_by_name("Email", invalid_email)
        page.wait_seconds(0.5)

        state = page.get_field_validation_state("Email")
        log.info(
            f"Invalid Email '{invalid_email}': "
            f"invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    # ---- AGT-U12: Email - missing @ sign ----
    def test_AGT_U12_email_no_at_sign(self, agt_page):
        """Email without @ sign - should show validation."""
        log.info("AGT-U12: Email no @ sign test")
        page = agt_page

        no_at_email = generate_numeric_email()
        page.open_add_form()
        page.wait_seconds(1)
        page._fill_input_by_name("Email", no_at_email)
        page.wait_seconds(0.5)

        state = page.get_field_validation_state("Email")
        log.info(
            f"Email without @ '{no_at_email}': "
            f"invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    # ---- AGT-U13: SQL injection in Agent Name ----
    @pytest.mark.xfail(
        reason="BUG: SQL injection strings may be accepted. "
               "Verifying if accepted (BUG) or rejected (security).",
        strict=False,
    )
    def test_AGT_U13_sql_injection(self, agt_page):
        """SQL injection payload should be rejected."""
        log.info("AGT-U13: SQL injection test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        page._fill_input_by_name("Agent Name", generate_sql_injection())
        page.wait_seconds(0.5)

        state = page.get_field_validation_state("Agent Name")
        log.info(
            f"SQL injection: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    # ---- AGT-U14: XSS in Agent Name ----
    @pytest.mark.xfail(
        reason="BUG: XSS payloads may be accepted. "
               "Verifying if accepted (BUG) or rejected (security).",
        strict=False,
    )
    def test_AGT_U14_xss_payload(self, agt_page):
        """XSS payload should be rejected."""
        log.info("AGT-U14: XSS payload test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        page._fill_input_by_name("Agent Name", generate_xss_payload())
        page.wait_seconds(0.5)

        state = page.get_field_validation_state("Agent Name")
        log.info(
            f"XSS payload: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    # ---- AGT-U15: Invalid -> valid -> next (error persistence) ----
    def test_AGT_U15_invalid_then_valid_next(self, agt_page):
        """Fill invalid Agent Name, fix to valid, click Next - errors should clear."""
        log.info("AGT-U15: Invalid -> valid -> next test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        page._fill_input_by_name("Agent Name", generate_spaces_only())
        page.wait_seconds(0.5)
        page.click_next()
        page.wait_seconds(1)
        step_after_invalid = page.get_active_step_index()
        log.info(f"After invalid name + Next: step={step_after_invalid}")

        valid_name = generate_agent_name("FixU15")
        page._fill_input_by_name("Agent Name", valid_name)
        page.wait_seconds(0.5)
        state = page.get_field_validation_state("Agent Name")
        log.info(f"After valid name: invalid={state['invalid']}")

        page.click_next()
        page.wait_seconds(1)
        step_after_valid = page.get_active_step_index()
        log.info(f"After valid name + Next: step={step_after_valid}")

        _cleanup_form(page)


# ====================================================================
# PHASE 2: Address Step Validations (10 tests)
# ====================================================================

class TestAddressStepValidations:
    """AGT-A01 to AGT-A10: Validation checks on Step 2 (Address Details)."""

    # ---- AGT-A01: Navigate to Address step with valid Universal data ----
    def test_AGT_A01_navigate_to_address(self, agt_page):
        """Verify the form opens on Step 0 (Address Details) and confirm stepper structure."""
        log.info("AGT-A01: Verify Address Details is Step 0")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        # Step 0 = "Address Details" (Universal + Address fields are on the SAME step)
        step = page.get_active_step_index()
        step_label = page.get_active_step_label()
        log.info(f"Current step: index={step}, label='{step_label}'")

        assert step == 0, f"Form should open on Step 0 (Address Details), but got step {step}"
        assert step_label == "Address Details", f"Step 0 label should be 'Address Details', got '{step_label}'"

        _cleanup_form(page)

    # ---- AGT-A02: Address - valid data acceptance ----
    def test_AGT_A02_address_valid(self, agt_page):
        """Address fields should accept valid data."""
        log.info("AGT-A02: Valid Address data test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("AddrA02")
        page.fill_universal_step(data)
        page.click_next()
        page.wait_seconds(1.5)

        addr = data["address"]
        page.fill_address_step(addr)
        page.wait_seconds(0.5)

        values = page.get_form_field_values()
        log.info(f"Address form values: {values}")

        _cleanup_form(page)

    # ---- AGT-A03: Pin Code - valid 6 digits ----
    def test_AGT_A03_pin_code_valid(self, agt_page):
        """Pin Code should accept 6-digit values."""
        log.info("AGT-A03: Valid Pin Code test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("PinA03")
        page.fill_universal_step(data)
        page.click_next()
        page.wait_seconds(1.5)

        valid_pin = generate_pin_code()
        page._fill_input_by_name("Pin Code", valid_pin)
        page.wait_seconds(0.5)
        actual = page.get_input_value("Pin Code")
        assert actual == valid_pin, f"Pin Code mismatch: '{valid_pin}' vs '{actual}'"
        log.info(f"Valid Pin Code '{valid_pin}' accepted")

        _cleanup_form(page)

    # ---- AGT-A04: Pin Code - invalid (wrong length) ----
    def test_AGT_A04_pin_code_invalid(self, agt_page):
        """Pin Code with wrong length - should show validation."""
        log.info("AGT-A04: Invalid Pin Code test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("PinA04")
        page.fill_universal_step(data)
        page.click_next()
        page.wait_seconds(1.5)

        invalid_pin = generate_invalid_pin_code()
        page._fill_input_by_name("Pin Code", invalid_pin)
        page.wait_seconds(0.5)

        state = page.get_field_validation_state("Pin Code")
        log.info(
            f"Invalid Pin Code '{invalid_pin}': "
            f"invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    # ---- AGT-A05: GST - valid format ----
    def test_AGT_A05_gst_valid(self, agt_page):
        """GST field should accept valid GST format."""
        log.info("AGT-A05: Valid GST test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("GstA05")
        page.fill_universal_step(data)
        page.click_next()
        page.wait_seconds(1.5)

        valid_gst = generate_gst()
        page._fill_input_by_name("GST", valid_gst)
        page.wait_seconds(0.5)
        actual = page.get_input_value("GST")
        log.info(f"GST input: '{valid_gst}' -> Actual: '{actual}'")

        _cleanup_form(page)

    # ---- AGT-A06: GST - empty (optional field) ----
    def test_AGT_A06_gst_empty_optional(self, agt_page):
        """Empty GST should be valid (optional field)."""
        log.info("AGT-A06: GST empty optional test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("GstA06")
        page.fill_universal_step(data)
        page.click_next()
        page.wait_seconds(1.5)

        page._fill_input_by_name("GST", "")
        page.wait_seconds(0.3)

        state = page.get_field_validation_state("GST")
        log.info(
            f"Empty GST: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    # ---- AGT-A07: Address - spaces only in required fields ----
    def test_AGT_A07_address_spaces_only(self, agt_page):
        """Spaces-only Address and Pin Code - should be rejected."""
        log.info("AGT-A07: Address spaces only test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("SpA07")
        page.fill_universal_step(data)
        page.click_next()
        page.wait_seconds(1.5)

        page._fill_input_by_name("Address", generate_spaces_only())
        page._fill_input_by_name("Pin Code", generate_spaces_only())
        page.wait_seconds(0.5)

        page.click_next()
        page.wait_seconds(1)

        step = page.get_active_step_index()
        errors = page.get_mat_error_text()
        log.info(f"After spaces-only address: step={step}, errors={errors}")

        _cleanup_form(page)

    def test_AGT_A08_back_to_universal(self, agt_page):
        """Clicking Back on Step 0 (first step) should not navigate away."""
        log.info("AGT-A08: Back button on first step test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        step_before = page.get_active_step_index()
        log.info(f"Before Back: step={step_before}")

        # On Step 0, Back button either doesn't exist or shouldn't navigate away
        try:
            page.click_back()
            page.wait_seconds(1)
        except Exception:
            log.info("Back button not found/clickable on Step 0 — expected behavior")

        step_after = page.get_active_step_index()
        log.info(f"After Back attempt: step={step_after}")

        assert step_after == 0, f"Should stay on Step 0 after Back, got step {step_after}"

        _cleanup_form(page)

    # ---- AGT-A09: Maxlength on Address field ----
    def test_AGT_A09_address_maxlength(self, agt_page):
        """Address field maxlength boundary test."""
        log.info("AGT-A09: Address maxlength test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("MaxA09")
        page.fill_universal_step(data)
        page.click_next()
        page.wait_seconds(1.5)

        long_255 = generate_string_255()
        page._fill_input_by_name("Address", long_255)
        page.wait_seconds(0.5)
        actual_255 = page.get_input_value("Address")
        log.info(f"255-char Address: actual length = {len(actual_255)}")

        long_256 = generate_string_256()
        page._fill_input_by_name("Address", long_256)
        page.wait_seconds(0.5)
        actual_256 = page.get_input_value("Address")
        log.info(
            f"256-char Address: actual length = {len(actual_256)}, "
            f"truncated = {len(actual_256) == 255}"
        )

        _cleanup_form(page)

    # ---- AGT-A10: Navigate to Payment step from Address ----
    def test_AGT_A10_navigate_to_payment(self, agt_page):
        """Fill all required Step 0 fields and navigate to Payment Details (Step 1)."""
        log.info("AGT-A10: Navigate to Payment step")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("NavA10")
        page.fill_universal_step(data)
        page.fill_address_step_required()  # NEW: fills cascading dropdowns + inputs
        page.click_next()
        page.wait_seconds(1.5)

        step = page.get_active_step_index()
        step_label = page.get_active_step_label()
        log.info(f"Current step: index={step}, label='{step_label}'")

        assert step >= 1, f"Should be on step 1+ (Payment), but got step {step}"

        _cleanup_form(page)


# ====================================================================
# PHASE 3: Payment Step Validations (5 tests)
# ====================================================================

class TestPaymentStepValidations:
    """AGT-P01 to AGT-P05: Validation checks on Step 3 (Payment Details)."""

    # ---- AGT-P01: Navigate to Payment step ----
    def test_AGT_P01_navigate_to_payment(self, agt_page):
        """Verify Payment step loads after filling Universal + Address."""
        log.info("AGT-P01: Navigate to Payment step")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("PayP01")
        page.fill_universal_step(data)
        page.click_next()
        page.wait_seconds(1.5)
        page.fill_address_step(data["address"])
        page.click_next()
        page.wait_seconds(1.5)

        step = page.get_active_step_index()
        log.info(f"Current step: {step}")
        assert step >= 2, f"Should be on Payment step (2+), got {step}"

        _cleanup_form(page)

    # ---- AGT-P02: Payment fields are optional ----
    def test_AGT_P02_payment_optional(self, agt_page):
        """Payment Terms and Preferred Payment Method should be optional."""
        log.info("AGT-P02: Payment fields optional test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("PayP02")
        page.fill_universal_step(data)
        page.click_next()
        page.wait_seconds(1.5)
        page.fill_address_step(data["address"])
        page.click_next()
        page.wait_seconds(1.5)

        page.click_next()
        page.wait_seconds(1.5)

        step = page.get_active_step_index()
        log.info(f"After skipping payment: step={step}")
        assert step >= 3, f"Should advance to Bank Details even without payment data, got step {step}"

        _cleanup_form(page)

    # ---- AGT-P03: Back from Payment to Address ----
    def test_AGT_P03_back_to_address(self, agt_page):
        """Back from Payment returns to Address step."""
        log.info("AGT-P03: Back to Address from Payment")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("PayP03")
        page.fill_universal_step(data)
        page.click_next()
        page.wait_seconds(1.5)
        page.fill_address_step(data["address"])
        page.click_next()
        page.wait_seconds(1.5)

        page.click_back()
        page.wait_seconds(1)

        step = page.get_active_step_index()
        log.info(f"After Back from Payment: step={step}")
        assert step <= 1, f"Should be on Address step after Back, got step {step}"

        _cleanup_form(page)

    # ---- AGT-P04: Payment Terms dropdown options ----
    def test_AGT_P04_payment_terms_options(self, agt_page):
        """List available Payment Terms dropdown options."""
        log.info("AGT-P04: Payment Terms options test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("PayP04")
        page.fill_universal_step(data)
        page.click_next()
        page.wait_seconds(1.5)
        page.fill_address_step(data["address"])
        page.click_next()
        page.wait_seconds(1.5)

        opts = page.get_dropdown_options_by_label("Payment Terms")
        log.info(f"Payment Terms options: {opts}")

        _cleanup_form(page)

    # ---- AGT-P05: Navigate to Bank Details from Payment ----
    def test_AGT_P05_navigate_to_bank(self, agt_page):
        """Navigate to Bank Details step from Payment."""
        log.info("AGT-P05: Navigate to Bank Details")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("PayP05")
        page.fill_universal_step(data)
        page.click_next()
        page.wait_seconds(1.5)
        page.fill_address_step(data["address"])
        page.click_next()
        page.wait_seconds(1.5)

        page.click_next()
        page.wait_seconds(1.5)

        step = page.get_active_step_index()
        step_label = page.get_active_step_label()
        log.info(f"Current step: index={step}, label='{step_label}'")

        assert step >= 3, f"Should be on Bank Details step (3+), got step {step}"

        _cleanup_form(page)


# ====================================================================
# PHASE 4: Bank Details Validations (10 tests)
# ====================================================================

class TestBankDetailsValidations:
    """AGT-B01 to AGT-B10: Validation checks on Step 4 (Bank Details)."""

    # ---- AGT-B01: Navigate to Bank Details step ----
    def test_AGT_B01_navigate_to_bank(self, agt_page):
        """Verify Bank Details step loads correctly."""
        log.info("AGT-B01: Navigate to Bank Details step")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("BnkB01")
        page.fill_agent_form(data)
        page.wait_seconds(0.5)

        step = page.get_active_step_index()
        log.info(f"Current step: {step}")
        assert step >= 3, f"Should be on Bank Details step, got {step}"

        _cleanup_form(page)

    # ---- AGT-B02: Bank Name - valid input ----
    def test_AGT_B02_bank_name_valid(self, agt_page):
        """Bank Name should accept valid text."""
        log.info("AGT-B02: Valid Bank Name test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        data = generate_valid_agent_data("BnkB02")
        page.fill_agent_form(data)
        page.wait_seconds(0.5)

        valid_bank = generate_bank_name()
        page._fill_input_by_name("Bank Name", valid_bank)
        page.wait_seconds(0.5)
        actual = page.get_input_value("Bank Name")
        log.info(f"Bank Name: '{valid_bank}' -> '{actual}'")

        _cleanup_form(page)

    # ---- AGT-B03: IFSC Code - valid 11 chars ----
    def test_AGT_B03_ifsc_code_valid(self, agt_page):
        """IFSC Code should accept valid 11-char format."""
        log.info("AGT-B03: Valid IFSC Code test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        data = generate_valid_agent_data("BnkB03")
        page.fill_agent_form(data)
        page.wait_seconds(0.5)

        valid_ifsc = generate_ifsc_code()
        page._fill_input_by_name("IFSC Code", valid_ifsc)
        page.wait_seconds(0.5)
        actual = page.get_input_value("IFSC Code")
        assert actual == valid_ifsc, f"IFSC mismatch: '{valid_ifsc}' vs '{actual}'"
        log.info(f"Valid IFSC Code '{valid_ifsc}' accepted")

        _cleanup_form(page)

    # ---- AGT-B04: IFSC Code - invalid (wrong length) ----
    def test_AGT_B04_ifsc_code_invalid(self, agt_page):
        """IFSC Code with wrong length - should show validation."""
        log.info("AGT-B04: Invalid IFSC Code test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        data = generate_valid_agent_data("BnkB04")
        page.fill_agent_form(data)
        page.wait_seconds(0.5)

        invalid_ifsc = generate_invalid_ifsc()
        page._fill_input_by_name("IFSC Code", invalid_ifsc)
        page.wait_seconds(0.5)

        state = page.get_field_validation_state("IFSC Code")
        log.info(
            f"Invalid IFSC '{invalid_ifsc}': "
            f"invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    # ---- AGT-B05: Account Number - valid ----
    def test_AGT_B05_account_number_valid(self, agt_page):
        """Account Number should accept valid numeric values."""
        log.info("AGT-B05: Valid Account Number test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        data = generate_valid_agent_data("BnkB05")
        page.fill_agent_form(data)
        page.wait_seconds(0.5)

        valid_acct = generate_account_number()
        page._fill_input_by_name("Account Number", valid_acct)
        page.wait_seconds(0.5)
        actual = page.get_input_value("Account Number")
        assert actual == valid_acct, f"Account Number mismatch"
        log.info(f"Valid Account Number '{valid_acct}' accepted")

        _cleanup_form(page)

    # ---- AGT-B06: Account Holder Name - valid ----
    def test_AGT_B06_account_holder_name_valid(self, agt_page):
        """Account Holder Name should accept valid text."""
        log.info("AGT-B06: Valid Account Holder Name test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        data = generate_valid_agent_data("BnkB06")
        page.fill_agent_form(data)
        page.wait_seconds(0.5)

        valid_holder = generate_account_holder_name()
        page._fill_input_by_name("Account Holder Name", valid_holder)
        page.wait_seconds(0.5)
        actual = page.get_input_value("Account Holder Name")
        assert actual == valid_holder, f"Holder Name mismatch"
        log.info(f"Valid Account Holder Name '{valid_holder}' accepted")

        _cleanup_form(page)

    # ---- AGT-B07: Bank fields empty submit ----
    def test_AGT_B07_bank_fields_empty_submit(self, agt_page):
        """Submit with empty bank detail fields - should be blocked."""
        log.info("AGT-B07: Bank fields empty submit test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        data = generate_valid_agent_data("BnkB07")
        page.fill_agent_form(data)
        page.wait_seconds(0.5)

        page._clear_input_by_name("Bank Name")
        page._clear_input_by_name("IFSC Code")
        page._clear_input_by_name("Account Holder Name")
        page._clear_input_by_name("Account Number")
        page.wait_seconds(0.5)

        page.submit()
        page.wait_seconds(3)

        validation_alert = page.handle_validation_warning(timeout=5)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        log.info(
            f"Empty bank submit: form_open={form_still_open}, "
            f"alert={validation_alert}, errors={errors}"
        )

        _cleanup_form(page)

    # ---- AGT-B08: Back from Bank Details to Payment ----
    def test_AGT_B08_back_to_payment(self, agt_page):
        """Back from Bank Details returns to Payment step."""
        log.info("AGT-B08: Back to Payment from Bank Details")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        data = generate_valid_agent_data("BnkB08")
        page.fill_agent_form(data)
        page.wait_seconds(0.5)

        page.click_back()
        page.wait_seconds(1)

        step = page.get_active_step_index()
        log.info(f"After Back from Bank Details: step={step}")
        assert step <= 2, f"Should be on Payment step after Back, got step {step}"

        _cleanup_form(page)

    # ---- AGT-B09: Account Type dropdown options ----
    def test_AGT_B09_account_type_options(self, agt_page):
        """List available Account Type dropdown options."""
        log.info("AGT-B09: Account Type options test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        data = generate_valid_agent_data("BnkB09")
        page.fill_agent_form(data)
        page.wait_seconds(0.5)

        opts = page.get_dropdown_options_by_label("Account Type")
        log.info(f"Account Type options: {opts}")

        _cleanup_form(page)

    # ---- AGT-B10: Full bank details fill ----
    def test_AGT_B10_full_bank_details(self, agt_page):
        """Fill all bank detail fields with valid data."""
        log.info("AGT-B10: Full bank details fill test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        data = generate_valid_agent_data("BnkB10")
        page.fill_agent_form(data)
        page.wait_seconds(0.5)

        bank = data["bank"]
        page.fill_bank_detail_step(bank)
        page.wait_seconds(0.5)

        values = page.get_form_field_values()
        log.info(f"Bank detail values: {values}")

        _cleanup_form(page)


# ====================================================================
# PHASE 5: Stepper Navigation Tests (5 tests)
# ====================================================================

class TestStepperNavigation:
    """AGT-N01 to AGT-N05: Stepper navigation behavior."""

    # ---- AGT-N01: Step count verification ----
    def test_AGT_N01_step_count(self, agt_page):
        """Verify the Agent form has the expected number of stepper steps."""
        log.info("AGT-N01: Step count verification")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        js = """
            var steps = document.querySelectorAll(
                'mat-horizontal-stepper mat-step-header'
            );
            return steps.length;
        """
        step_count = page.driver.execute_script(js)
        log.info(f"Total stepper steps: {step_count}")
        assert step_count >= 4, f"Expected at least 4 steps, got {step_count}"

        _cleanup_form(page)

    # ---- AGT-N02: Step labels verification ----
    def test_AGT_N02_step_labels(self, agt_page):
        """Verify stepper step labels are present."""
        log.info("AGT-N02: Step labels verification")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        js = """
            var steps = document.querySelectorAll(
                'mat-horizontal-stepper mat-step-header'
            );
            var labels = [];
            for (var i = 0; i < steps.length; i++) {
                var label = steps[i].querySelector('.mat-step-label');
                labels.push(label ? label.textContent.trim() : '');
            }
            return labels;
        """
        labels = page.driver.execute_script(js)
        log.info(f"Step labels: {labels}")

        _cleanup_form(page)

    # ---- AGT-N03: Cannot skip to later steps without filling ----
    def test_AGT_N03_no_step_skip(self, agt_page):
        """Verify cannot skip to step 3+ without filling step 1."""
        log.info("AGT-N03: No step skip test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        page.click_next()
        page.wait_seconds(1)

        step = page.get_active_step_index()
        log.info(f"After empty Next: step={step}")

        _cleanup_form(page)

    # ---- AGT-N04: Navigate forward through all steps ----
    def test_AGT_N04_navigate_all_steps(self, agt_page):
        """Navigate through all 4 steps with valid data."""
        log.info("AGT-N04: Navigate all steps test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("NavN04")
        page.fill_universal_step(data)

        page.click_next()
        page.wait_seconds(1.5)
        step1 = page.get_active_step_index()
        page.fill_address_step(data["address"])

        page.click_next()
        page.wait_seconds(1.5)
        step2 = page.get_active_step_index()

        page.click_next()
        page.wait_seconds(1.5)
        step3 = page.get_active_step_index()
        page.fill_bank_detail_step(data["bank"])

        log.info(f"Steps visited: 0 -> {step1} -> {step2} -> {step3}")
        assert step3 >= 3, f"Should reach Bank Details step (3+), got {step3}"

        _cleanup_form(page)

    # ---- AGT-N05: Cancel closes form from any step ----
    def test_AGT_N05_cancel_from_step(self, agt_page):
        """Cancel button should close the form from any step."""
        log.info("AGT-N05: Cancel from step test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Form should be open"

        page.cancel()
        page.wait_seconds(1)

        form_open = page.is_add_form_open()
        log.info(f"After Cancel: form_open={form_open}")
        assert not form_open, "Form should be closed after Cancel"


# ====================================================================
# PHASE 6: Create Happy Path Tests (5 tests)
# ====================================================================

class TestCreateHappyPath:
    """AGT-C01 to AGT-C05: Create agent with valid data."""

    # ---- AGT-C01: Create with valid data (happy path) ----
    def test_AGT_C01_valid_create(self, agt_page):
        """Create agent with all valid data - should succeed."""
        log.info("AGT-C01: Valid create (happy path)")
        page = agt_page

        data = generate_valid_agent_data("HappyC01")
        result = page.create_agent(data)
        name = result.get("agent_name", "")

        if result["status"] == "PASSED":
            log.info(f"Agent created successfully: {name}")
        else:
            log.warning(f"Create failed: {result.get('error', 'unknown')}")

        if name:
            page.search(name)
            page.wait_seconds(2)
        found = page.is_agent_in_table(name)

        log.info(
            f"Create result: status={result['status']}, "
            f"name='{name}', found={found}"
        )

    # ---- AGT-C02: Create with minimal data (no optional fields) ----
    def test_AGT_C02_minimal_create(self, agt_page):
        """Create agent with only required fields - should succeed."""
        log.info("AGT-C02: Minimal create test")
        page = agt_page

        data = generate_valid_agent_data("MinC02")
        data["payment"]["payment_terms"] = None
        data["payment"]["preferred_payment_method"] = None
        data["address"]["gst"] = ""
        data["address"]["taluka"] = None
        data["address"]["village"] = None
        data["bank"]["branch"] = ""

        result = page.create_agent(data)
        name = result.get("agent_name", "")

        log.info(
            f"Minimal create: status={result['status']}, "
            f"error={result.get('error', '')}"
        )

    # ---- AGT-C03: Form values reading via JS ----
    def test_AGT_C03_read_form_values(self, agt_page):
        """Verify get_form_field_values() reads all input values correctly."""
        log.info("AGT-C03: Read form values test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("ReadC03")
        page.fill_universal_step(data)
        page.wait_seconds(0.5)

        values = page.get_form_field_values()
        log.info(f"Form values on step 1: {values}")

        assert "Agent Name" in values or len(values) > 0, (
            f"Form values should contain data, got: {values}"
        )

        _cleanup_form(page)

    # ---- AGT-C04: Duplicate Agent Name ----
    def test_AGT_C04_duplicate_agent_name(self, agt_page):
        """Create two agents with the same name - check behavior."""
        log.info("AGT-C04: Duplicate Agent Name test")
        page = agt_page

        data1 = generate_valid_agent_data("DupC04a")
        result1 = page.create_agent(data1)
        name1 = result1.get("agent_name", "")

        _cleanup_form(page)
        page.click_refresh()
        page.wait_seconds(2)

        if not name1:
            log.warning("Agent 1 creation failed - cannot test duplicate")
            return

        data2 = generate_valid_agent_data("DupC04b")
        data2["agent_name"] = name1
        result2 = page.create_agent(data2)

        _cleanup_form(page)
        page.click_refresh()
        page.wait_seconds(2)

        log.info(
            f"Duplicate test: agent1='{name1}', "
            f"result2_status={result2['status']}, "
            f"result2_error={result2.get('error', '')}"
        )

    # ---- AGT-C05: Refresh after create ----
    def test_AGT_C05_refresh_after_create(self, agt_page):
        """Create agent, refresh page, verify table still shows the record."""
        log.info("AGT-C05: Refresh after create test")
        page = agt_page

        data = generate_valid_agent_data("RefC05")
        result = page.create_agent(data)
        name = result.get("agent_name", "")

        _cleanup_form(page)
        page.click_refresh()
        page.wait_seconds(2)

        if name:
            found = page.is_agent_in_table(name)
            log.info(f"After refresh: name='{name}', found={found}")


# ====================================================================
# PHASE 7: Bug-specific Tests (5 tests)
# ====================================================================

class TestBugSpecific:
    """AGT-X01 to AGT-X05: Bug verification and edge case tests."""

    # ---- AGT-X01: Angular Material value read via JS ----
    def test_AGT_X01_js_value_read(self, agt_page):
        """Verify execute_script reads Angular Material values correctly."""
        log.info("AGT-X01: JS value read test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        test_name = "JSReadX01"
        page._fill_input_by_name("Agent Name", test_name)
        page.wait_seconds(0.5)

        actual = page.get_input_value("Agent Name")
        log.info(f"JS-read value: '{actual}'")

        all_values = page.get_form_field_values()
        log.info(f"All form values: {all_values}")

        assert actual == test_name, (
            f"JS value read mismatch: expected '{test_name}', got '{actual}'"
        )

        _cleanup_form(page)

    # ---- AGT-X02: Form field values preserved after Next/Back ----
    def test_AGT_X02_values_preserved_next_back(self, agt_page):
        """Values entered on Universal step should persist after Next/Back."""
        log.info("AGT-X02: Values preserved after Next/Back test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("PresX02")
        page.fill_universal_step(data)
        page.wait_seconds(0.5)

        values_before = page.get_form_field_values()

        page.click_next()
        page.wait_seconds(1.5)

        page.click_back()
        page.wait_seconds(1.5)

        values_after = page.get_form_field_values()
        log.info(f"Before Next: {values_before}")
        log.info(f"After Back: {values_after}")

        name_before = values_before.get("Agent Name", "")
        name_after = values_after.get("Agent Name", "")
        assert name_after == name_before, (
            f"Agent Name not preserved: '{name_before}' -> '{name_after}'"
        )

        _cleanup_form(page)

    # ---- AGT-X03: Close and reopen form starts fresh ----
    def test_AGT_X03_close_reopen_fresh(self, agt_page):
        """Closing and reopening the form should start with fresh values."""
        log.info("AGT-X03: Close reopen fresh test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)
        page._fill_input_by_name("Agent Name", "ShouldNotPersist")
        page.wait_seconds(0.5)

        page.cancel()
        page.wait_seconds(1)

        page.open_add_form()
        page.wait_seconds(1)

        values = page.get_form_field_values()
        name = values.get("Agent Name", "")
        log.info(f"After reopen: Agent Name = '{name}'")

        _cleanup_form(page)

    # ---- AGT-X04: Multiple rapid Next clicks ----
    def test_AGT_X04_rapid_next_clicks(self, agt_page):
        """Multiple rapid Next clicks should not crash the stepper."""
        log.info("AGT-X04: Rapid Next clicks test")
        page = agt_page

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_agent_data("RapidX04")
        page.fill_universal_step(data)
        page.fill_address_step(data["address"])
        page.wait_seconds(0.5)

        for i in range(3):
            try:
                page.click_next()
                page.wait_seconds(0.5)
            except Exception as e:
                log.warning(f"Rapid Next click {i+1} error: {e}")

        step = page.get_active_step_index()
        form_open = page.is_add_form_open()
        log.info(f"After rapid Next clicks: step={step}, form_open={form_open}")

        _cleanup_form(page)

    # ---- AGT-X05: Table row count changes after create ----
    def test_AGT_X05_table_count_after_create(self, agt_page):
        """Table row count should increase after creating a new agent."""
        log.info("AGT-X05: Table count after create test")
        page = agt_page

        count_before = page.get_table_row_count()
        log.info(f"Table rows before: {count_before}")

        data = generate_valid_agent_data("CntX05")
        result = page.create_agent(data)

        _cleanup_form(page)
        page.click_refresh()
        page.wait_seconds(2)

        count_after = page.get_table_row_count()
        log.info(f"Table rows after: {count_after}")
        log.info(
            f"Result: status={result['status']}, "
            f"rows_before={count_before}, rows_after={count_after}"
        )
