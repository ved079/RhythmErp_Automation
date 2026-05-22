"""
test_customer_validation.py
------------------------------
Comprehensive validation test suite for RhythmERP Customer screen.
~46 test cases across 6 phases.

Phases:
  1. Create Form Validations  (20 tests) — CU-C01 to CU-C20
  2. Duplicate Validations      (4 tests) — CU-D01 to CU-D04
  3. Edit Form Validations      (5 tests) — CU-E01 to CU-E05
  4. Search & Filter Edge Cases (5 tests) — CU-S01 to CU-S05
  5. Popup & UI Behaviors       (8 tests) — CU-P01 to CU-P08
  6. Bug-specific               (4 tests) — CU-B01 to CU-B04

Known Bugs (suspected — to be confirmed during test execution):
  BUG-001 (CRITICAL): Browser-clicked mat-select does NOT update Angular form model
  BUG-002 (MEDIUM)  : Stepper allows advancing with empty required fields
  BUG-003 (MEDIUM)  : Pin Code header shows asterisk but field is NOT required
  BUG-004 (MEDIUM)  : Bank Name/Branch headers show asterisk but fields are NOT required

Bug Handling Decisions:
  BUG-001: Test expects Validation Failed — mark xfail, will XPASS when ERP is fixed
  BUG-002: Document as confirmed bug — test confirms the stepper is non-linear
  BUG-003: Document as known issue — test confirms the mismatch
  BUG-004: Document as known issue — test confirms the mismatch

Run:
  pytest test_customer_validation.py -v --tb=short
  pytest test_customer_validation.py -v -k "TestCreateForm" --tb=short
  pytest test_customer_validation.py -v -k "CU-C03" --tb=short
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

from pages.registration.modules.customer.customer_page import CustomerPage
from pages.registration.modules.customer.data.customer_data import (
    generate_valid_customer_data,
    generate_valid_address_row,
    generate_valid_bank_row,
    generate_full_valid_customer_data,
    generate_valid_edit_data,
    generate_invalid_email,
    generate_email_no_domain,
    generate_email_no_at,
    generate_special_char_name,
    generate_sql_injection,
    generate_xss_payload,
    generate_spaces_only,
    generate_string_255,
    generate_string_256,
    generate_negative_deposite,
    generate_zero_deposite,
    generate_alpha_deposite,
    generate_negative_phone,
    generate_alpha_phone,
    generate_duplicate_pan_data,
    generate_empty_data,
    generate_company_name_only_data,
    generate_invalid_pan,
    generate_pan_with_spaces,
    generate_pan_with_special_chars,
    generate_long_phone,
    generate_emoji_name,
    generate_unicode_name,
)
from common.logger import log


# ====================================================================
# Helper: create a prerequisite customer, refresh, return its name
# ====================================================================

def _create_prerequisite_customer(page, name_prefix="PreReq"):
    """Create a Customer entry for tests that need existing data.
    Returns the company name used and the data dict.
    """
    data = generate_full_valid_customer_data(name_prefix)
    result = page.create_customer(data)
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
    company_name = result.get("company_name", "") or data.get("company_name", "")
    log.info(f"Prerequisite customer created: {company_name}")
    return company_name, data


# ====================================================================
# PHASE 1: Create Form Validations (20 tests)
# ====================================================================

class TestCreateFormValidations:
    """CU-C01 to CU-C20: Validation checks on the Create form.
    Customer has universal fields + 3-step stepper
    (Step 0: Additional Details, Step 1: Customer Details/Address,
     Step 2: Customer Bank Details).
    """

    # ---- CU-C01: Submit with all fields empty ----
    def test_CU_C01_empty_submit(self, cu_page):
        """Submit with all fields empty — should be blocked.
        Expect: SweetAlert2 'Validation Failed' + mat-error
        'This field is required' for required fields.
        """
        log.info("CU-C01: Empty submit test")
        page = cu_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Go through all stepper steps with empty fields and click Submit
        # Step 0 (Additional Details) is active by default
        page.click_stepper_next()
        page.wait_seconds(1)

        # Step 1 (Customer Details / Address)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Step 2 (Customer Bank Details) — click Submit
        page.click_submit()
        page.wait_seconds(2)

        # Check for validation errors or SweetAlert
        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        # Expect: form stays open + validation errors shown
        assert form_still_open or errors or validation_alert, (
            "BUG: Form submitted with all fields empty — no validation"
        )
        if validation_alert:
            log.info(f"Validation alert shown: {validation_alert}")
        if errors:
            log.info(f"Validation errors shown: {errors}")
        if form_still_open:
            log.info("Form stayed open — validation blocked submission")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        try:
            page.force_close_form_popup()
        except Exception:
            pass

    # ---- CU-C02: Valid create (happy path) ----
    def test_CU_C02_valid_create(self, cu_page):
        """Create with valid data across all 3 steps — should succeed.
        Fill universal fields -> step0 -> next -> step1 address -> next
        -> step2 bank -> submit.
        """
        log.info("CU-C02: Valid create test (happy path)")
        page = cu_page

        data = generate_full_valid_customer_data("ValidC")
        result = page.create_customer(data)
        company_name = data.get("company_name", "")

        if result["status"] == "PASSED":
            log.info(f"Customer created successfully: {company_name}")
        else:
            log.warning(f"Create failed: {result.get('error', 'unknown')}")

        # Verify the customer appears in the table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_customer_in_table(company_name)

        assert found, (
            f"Created customer '{company_name}' not found in table after refresh"
        )
        log.info(f"Customer created and found in table: {company_name}")

    # ---- CU-C03: Company Name with spaces only ----
    @pytest.mark.xfail(
        reason="Spaces-only Company Name may be accepted — "
               "will fail until ERP rejects it",
        strict=False,
    )
    def test_CU_C03_spaces_only_company_name(self, cu_page):
        """Company Name with spaces only — should be rejected."""
        log.info("CU-C03: Spaces-only Company Name test")
        page = cu_page

        data = generate_valid_customer_data("SpaceIt")
        data["company_name"] = generate_spaces_only(10)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        assert form_still_open or errors or validation_alert, (
            "Spaces-only Company Name was accepted — "
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

    # ---- CU-C04: Company Name 256 chars (over maxlength) ----
    def test_CU_C04_company_name_256_chars(self, cu_page):
        """Company Name with 256 chars — should be truncated to 255
        or rejected with validation error.
        """
        log.info("CU-C04: 256-char Company Name test")
        page = cu_page

        name_256 = generate_string_256()
        data = generate_valid_customer_data("Bnd256")
        data["company_name"] = name_256

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)

        # Read back the actual value to see if it was truncated
        actual_value = page.get_input_value(page.COMPANY_NAME_INPUT)
        if len(actual_value) <= 255:
            log.info(
                f"Company Name truncated to {len(actual_value)} chars — "
                "maxlength enforced by HTML"
            )
        else:
            log.warning(
                f"Company Name accepted with {len(actual_value)} chars — "
                "no maxlength enforced"
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

    # ---- CU-C05: Invalid email format ----
    def test_CU_C05_invalid_email(self, cu_page):
        """Fill email with 'invalid-email' — expect mat-error 'Invalid Email'."""
        log.info("CU-C05: Invalid email format test")
        page = cu_page

        data = generate_valid_customer_data("InvEmail")
        data["email"] = generate_invalid_email()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)

        # Check for email validation error
        page.wait_seconds(1)
        errors = page.get_mat_error_text()

        # Also try submitting to trigger server-side validation
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info("Invalid email rejected — validation working")
            if "Invalid Email" in str(errors):
                log.info("'Invalid Email' mat-error confirmed")
        else:
            log.warning(
                "BUG: Invalid email format was accepted without validation error"
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

    # ---- CU-C06: Email with no @ sign ----
    def test_CU_C06_email_no_at(self, cu_page):
        """Fill email with 'testexample.com' — expect validation error."""
        log.info("CU-C06: Email with no @ sign test")
        page = cu_page

        data = generate_valid_customer_data("NoAt")
        data["email"] = generate_email_no_at()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.wait_seconds(1)

        # Check for email validation error after filling
        errors = page.get_mat_error_text()

        # Submit to trigger full validation
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info("Email without @ sign rejected — validation working")
        else:
            log.warning(
                "BUG: Email without @ sign was accepted"
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

    # ---- CU-C07: Email with no domain ----
    def test_CU_C07_email_no_domain(self, cu_page):
        """Fill email with 'test@' — expect validation error."""
        log.info("CU-C07: Email with no domain test")
        page = cu_page

        data = generate_valid_customer_data("NoDom")
        data["email"] = generate_email_no_domain()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.wait_seconds(1)

        # Check for email validation error
        errors = page.get_mat_error_text()

        # Submit to trigger full validation
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info("Email without domain rejected — validation working")
        else:
            log.warning(
                "BUG: Email without domain was accepted"
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

    # ---- CU-C08: Special characters in Company Name ----
    def test_CU_C08_special_chars_company_name(self, cu_page):
        """Fill Company Name with special characters — document behaviour:
        either accepted or validation error.
        """
        log.info("CU-C08: Special chars in Company Name test")
        page = cu_page

        data = generate_valid_customer_data("SpecCh")
        data["company_name"] = generate_special_char_name()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)

        # Try submitting through all steps
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info("Special chars in Company Name rejected — validation working")
        else:
            log.info(
                "Special chars in Company Name accepted "
                "(may be expected behavior for company names)"
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

    # ---- CU-C09: SQL injection in Company Name ----
    def test_CU_C09_sql_injection_company_name(self, cu_page):
        """Fill Company Name with SQL injection string — document:
        accepted or rejected.
        """
        log.info("CU-C09: SQL injection in Company Name test")
        page = cu_page

        data = generate_valid_customer_data("SqlInj")
        data["company_name"] = generate_sql_injection()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)

        # Submit through all steps
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info(
                "SQL injection in Company Name rejected — validation working"
            )
        else:
            log.info(
                "SQL injection in Company Name accepted — "
                "system should sanitize input (but may store it safely)"
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

    # ---- CU-C10: XSS payload in Company Name ----
    def test_CU_C10_xss_payload_company_name(self, cu_page):
        """Fill Company Name with XSS payload — document:
        accepted or rejected, does it execute?
        """
        log.info("CU-C10: XSS payload in Company Name test")
        page = cu_page

        data = generate_valid_customer_data("XssPay")
        data["company_name"] = generate_xss_payload()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)

        # Submit through all steps
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        # Check if an alert was triggered (XSS execution)
        try:
            alert_text = page.driver.switch_to.alert.text
            log.warning(
                f"XSS EXECUTED! Alert text: {alert_text} — "
                "CRITICAL SECURITY VULNERABILITY"
            )
            page.driver.switch_to.alert.dismiss()
        except Exception:
            log.info("No XSS alert triggered — script tag may be sanitized")

        if form_still_open or errors or validation_alert:
            log.info("XSS payload in Company Name rejected — validation working")
        else:
            log.info(
                "XSS payload in Company Name accepted but not executed — "
                "Angular sanitization likely prevents execution"
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

    # ---- CU-C11: Negative deposit value ----
    def test_CU_C11_negative_deposite(self, cu_page):
        """Fill Deposite with negative number — should be rejected
        (deposit must be positive).
        """
        log.info("CU-C11: Negative Deposite test")
        page = cu_page

        data = generate_valid_customer_data("NegDep")
        data["deposite"] = generate_negative_deposite()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.wait_seconds(1)

        # Check if the negative value was accepted in the input
        actual_value = page.get_input_value(page.DEPOSITE_INPUT)
        if actual_value and float(actual_value) < 0:
            log.warning(
                f"Negative deposit value accepted in input: {actual_value}"
            )
        else:
            log.info(
                f"Negative deposit value rejected or blocked: actual={actual_value}"
            )

        # Submit through remaining steps
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info("Negative deposit rejected — validation working")
        else:
            log.warning(
                "BUG: Negative deposit value was accepted"
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

    # ---- CU-C12: Pin Code — header says required but HTML says optional (BUG-003) ----
    def test_CU_C12_pin_code_required_mismatch(self, cu_page):
        """Fill all fields except Pin Code — submit.
        BUG-003: Header says 'Pin Code *' but HTML says optional.
        Document: Does it require Pin Code or not?
        """
        log.info("CU-C12: Pin Code required mismatch test (BUG-003)")
        page = cu_page

        data = generate_full_valid_customer_data("PinBug")
        # Ensure pin_code is empty
        if "address_rows" in data and data["address_rows"]:
            data["address_rows"][0]["pin_code"] = ""

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill address row but leave Pin Code empty
        page.fill_address_row(0, data["address_rows"][0])
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill bank row
        page.fill_bank_row(0, data["bank_rows"][0])
        page.click_submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info(
                "BUG-003: Pin Code IS required on submit — "
                "header asterisk is correct, HTML attribute is wrong"
            )
        else:
            log.info(
                "BUG-003 CONFIRMED: Pin Code is NOT required on submit — "
                "header asterisk is misleading"
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

    # ---- CU-C13: Bank Name/Branch header says required but HTML says optional (BUG-004) ----
    def test_CU_C13_bank_fields_required_mismatch(self, cu_page):
        """Fill all required fields but leave Bank Name/Branch empty — submit.
        BUG-004: Headers show asterisks but HTML says optional.
        Document: Does it require these fields or not?
        """
        log.info("CU-C13: Bank fields required mismatch test (BUG-004)")
        page = cu_page

        data = generate_full_valid_customer_data("BankBug")
        # Ensure bank name and branch are empty
        if "bank_rows" in data and data["bank_rows"]:
            data["bank_rows"][0]["bank_name"] = ""
            data["bank_rows"][0]["branch"] = ""

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill address row
        page.fill_address_row(0, data["address_rows"][0])
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill bank row but leave Bank Name/Branch empty
        page.fill_bank_row(0, data["bank_rows"][0])
        page.click_submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info(
                "BUG-004: Bank Name/Branch IS required on submit — "
                "header asterisks are correct, HTML attributes are wrong"
            )
        else:
            log.info(
                "BUG-004 CONFIRMED: Bank Name/Branch are NOT required on submit — "
                "header asterisks are misleading"
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

    # ---- CU-C14: PAN Number with spaces ----
    def test_CU_C14_pan_with_spaces(self, cu_page):
        """Fill PAN with leading/trailing spaces — document:
        accepted, trimmed, or error.
        """
        log.info("CU-C14: PAN Number with spaces test")
        page = cu_page

        data = generate_valid_customer_data("PanSp")
        data["pan_number"] = generate_pan_with_spaces()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.wait_seconds(1)

        # Read back the PAN value to see if it was trimmed
        actual_value = page.get_input_value(page.PAN_NUMBER_INPUT)
        if actual_value != data["pan_number"]:
            log.info(
                f"PAN was trimmed: input='{data['pan_number']}', "
                f"actual='{actual_value}'"
            )
        else:
            log.info(
                f"PAN with spaces accepted as-is: '{actual_value}'"
            )

        # Try submitting through all steps
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info("PAN with spaces rejected — validation working")
        else:
            log.info(
                "PAN with spaces accepted — system may auto-trim"
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

    # ---- CU-C15: Stepper advances with empty required fields (BUG-002) ----
    @pytest.mark.xfail(
        reason="BUG-002: Stepper allows advancing with empty required fields",
        strict=False,
    )
    def test_CU_C15_stepper_advances_empty(self, cu_page):
        """Open add form with no fields filled, click Next.
        BUG-002: Stepper ALLOWS advancement — confirmed.
        """
        log.info("CU-C15: Stepper advances with empty required fields (BUG-002)")
        page = cu_page

        page.open_add_form()
        page.wait_seconds(1)

        # Confirm we start on Step 0
        assert page.is_step0_active(), "Should start on Step 0"

        # Click Next with all fields empty
        page.click_stepper_next()
        page.wait_seconds(1)

        # BUG-002: Stepper should NOT advance but it does
        stepped_to_1 = page.is_step1_active()
        log.info(f"After Next with empty fields: step1_active={stepped_to_1}")

        # Click Next again to reach Step 2
        if stepped_to_1:
            page.click_stepper_next()
            page.wait_seconds(1)
            stepped_to_2 = page.is_step2_active()
            log.info(f"After second Next with empty fields: step2_active={stepped_to_2}")

        # Go back to Step 0
        page.click_stepper_back()
        page.wait_seconds(1)

        # Verify still able to navigate back
        back_to_0 = page.is_step0_active() or page.get_current_step_index() < 2
        log.info(f"After Back: current_step={page.get_current_step_index()}")

        # The assertion that SHOULD pass if stepper validates:
        # With empty fields, we should NOT have been able to advance
        assert not stepped_to_1, (
            "BUG-002 CONFIRMED: Stepper allowed advancing with empty required fields"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- CU-C16: Partial required fields — only Company Name filled ----
    def test_CU_C16_partial_company_name_only(self, cu_page):
        """Fill only Company Name, leave all other required fields empty —
        submit. Expect: Validation errors for remaining required fields.
        """
        log.info("CU-C16: Partial required fields — Company Name only")
        page = cu_page

        data = generate_company_name_only_data("NameOnly")

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)

        # Submit through all steps
        page.fill_step0({})
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        # Required fields (Ownership Status, Sale Type, Supply Type,
        # Transaction Currency, Email, Phone, PAN) should block
        assert form_still_open or errors or validation_alert, (
            "BUG: Form submitted with only Company Name — "
            "other required fields not validated"
        )
        if errors:
            log.info(f"Partial fill validation errors: {errors}")
        if validation_alert:
            log.info(f"Validation alert: {validation_alert}")

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

    # ---- CU-C17: Stepper Back button ----
    def test_CU_C17_stepper_back_button(self, cu_page):
        """Fill Step 0, click Next to go to Step 1, click Back.
        Expect: Return to Step 0, data preserved.
        """
        log.info("CU-C17: Stepper Back button test")
        page = cu_page

        data = generate_valid_customer_data("StepNav")

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_step0_active(), "Step 0 should be active initially"

        # Fill Step 0 and go to Step 1
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Verify we're on Step 1
        step1_active = page.is_step1_active()
        if step1_active:
            log.info("Successfully navigated to Step 1")

            # Click Back
            page.click_stepper_back()
            page.wait_seconds(1)

            # Verify we're back on Step 0
            assert page.is_step0_active(), (
                "Did not return to Step 0 after clicking Back"
            )
            log.info("Back button correctly returned to Step 0")

            # Verify Step 0 data is preserved
            company_name_value = page.get_input_value(page.COMPANY_NAME_INPUT)
            if company_name_value:
                log.info(
                    f"Step 0 data preserved after Back: "
                    f"company_name={company_name_value}"
                )
            else:
                log.warning(
                    "Step 0 data may have been lost after Back navigation"
                )
        else:
            log.warning(
                "Could not navigate to Step 1 — "
                "may need all universal fields filled first"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- CU-C18: PAN Number with invalid format ----
    def test_CU_C18_invalid_pan_format(self, cu_page):
        """Fill PAN with '1234567890' (numbers only) — document:
        accepted or rejected.
        """
        log.info("CU-C18: PAN Number with invalid format test")
        page = cu_page

        data = generate_valid_customer_data("InvPan")
        data["pan_number"] = generate_invalid_pan()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)

        # Submit through all steps
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info("Invalid PAN format rejected — validation working")
        else:
            log.info(
                "Invalid PAN format accepted — "
                "system may not validate PAN format on frontend"
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

    # ---- CU-C19: Phone Number with alphabetic characters ----
    def test_CU_C19_alpha_phone_number(self, cu_page):
        """Try typing letters in Phone Number (number input) — document:
        accepted or blocked by HTML5 number validation.
        """
        log.info("CU-C19: Phone Number with alphabetic characters test")
        page = cu_page

        data = generate_valid_customer_data("AlphaPh")
        data["phone_number"] = generate_alpha_phone()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.wait_seconds(1)

        # Read back the phone value — HTML5 number input should block letters
        actual_value = page.get_input_value(page.PHONE_NUMBER_INPUT)
        if actual_value == "" or actual_value != data["phone_number"]:
            log.info(
                f"Alphabetic characters blocked by HTML5 number input: "
                f"attempted='{data['phone_number']}', actual='{actual_value}'"
            )
        else:
            log.warning(
                f"Alphabetic characters accepted in Phone Number: "
                f"actual='{actual_value}' — input type may not be 'number'"
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

    # ---- CU-C20: Unicode/Emoji in Company Name ----
    def test_CU_C20_unicode_emoji_company_name(self, cu_page):
        """Fill Company Name with emoji/unicode — document:
        accepted or rejected.
        """
        log.info("CU-C20: Unicode/Emoji in Company Name test")
        page = cu_page

        # Test with emoji
        data = generate_valid_customer_data("EmojiN")
        data["company_name"] = generate_emoji_name()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.wait_seconds(1)

        # Read back the company name value
        actual_value = page.get_input_value(page.COMPANY_NAME_INPUT)
        log.info(f"Emoji Company Name: input='{data['company_name']}', actual='{actual_value}'")

        # Also test with unicode characters
        page.cancel()
        try:
            page.close_popup()
        except Exception:
            pass
        try:
            page.force_close_form_popup()
        except Exception:
            pass

        page.wait_seconds(1)

        # Second test with unicode
        data2 = generate_valid_customer_data("UniN")
        data2["company_name"] = generate_unicode_name()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data2)
        page.wait_seconds(1)

        actual_value2 = page.get_input_value(page.COMPANY_NAME_INPUT)
        log.info(
            f"Unicode Company Name: input='{data2['company_name']}', "
            f"actual='{actual_value2}'"
        )

        # Submit through all steps with the unicode name
        page.fill_step0(data2)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info("Unicode/Emoji in Company Name rejected — validation working")
        else:
            log.info(
                "Unicode/Emoji in Company Name accepted — "
                "system allows international characters"
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
# PHASE 2: Duplicate Validations (4 tests)
# ====================================================================

class TestDuplicateValidations:
    """CU-D01 to CU-D04: Duplicate field checks in Create and Edit.
    PAN Number is unique (server-side). Other fields may not be.
    """

    # ---- CU-D01: Duplicate PAN Number — Create after Create ----
    def test_CU_D01_duplicate_pan_create(self, cu_page):
        """Create customer 1 with valid PAN, then create customer 2
        with SAME PAN. Expect: Second create should be BLOCKED
        (unique PAN validation, server-side).
        """
        log.info("CU-D01: Duplicate PAN Number — Create after Create")
        page = cu_page

        # Create first customer and get its PAN
        company1, data1 = _create_prerequisite_customer(page, "DupPan1")
        pan1 = data1.get("pan_number", "")
        log.info(f"First customer PAN: {pan1}")

        # Try creating second customer with same PAN
        data2 = generate_duplicate_pan_data(pan1)
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data2)
        page.fill_step0(data2)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill address row
        if "address_rows" in data2 and data2["address_rows"]:
            page.fill_address_row(0, data2["address_rows"][0])
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill bank row
        if "bank_rows" in data2 and data2["bank_rows"]:
            page.fill_bank_row(0, data2["bank_rows"][0])

        page.click_submit()
        page.wait_seconds(3)

        # Check for duplicate PAN validation error
        validation_alert = page.handle_validation_warning(timeout=5)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info(
                "Duplicate PAN rejected in Create — "
                "unique PAN validation working (server-side)"
            )
        else:
            log.warning(
                "BUG: Duplicate PAN Number was accepted — "
                "unique PAN validation NOT enforced"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
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

    # ---- CU-D02: Duplicate Company Name — Create after Create ----
    def test_CU_D02_duplicate_company_name_create(self, cu_page):
        """Create customer 1, then create customer 2 with SAME Company Name
        but different PAN. Document: Allowed or blocked?
        """
        log.info("CU-D02: Duplicate Company Name — Create after Create")
        page = cu_page

        # Create first customer
        company1, data1 = _create_prerequisite_customer(page, "DupComp1")
        log.info(f"First customer Company Name: {company1}")

        # Create second customer with same Company Name but different PAN
        data2 = generate_full_valid_customer_data("DupComp2")
        data2["company_name"] = company1  # Same company name
        # PAN is already different from data2 generator

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data2)
        page.fill_step0(data2)
        page.click_stepper_next()
        page.wait_seconds(1)

        if "address_rows" in data2 and data2["address_rows"]:
            page.fill_address_row(0, data2["address_rows"][0])
        page.click_stepper_next()
        page.wait_seconds(1)

        if "bank_rows" in data2 and data2["bank_rows"]:
            page.fill_bank_row(0, data2["bank_rows"][0])

        page.click_submit()
        page.wait_seconds(3)

        validation_alert = page.handle_validation_warning(timeout=5)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info(
                "Duplicate Company Name rejected — validation working"
            )
        else:
            log.info(
                "Duplicate Company Name allowed — "
                "system does not enforce uniqueness on Company Name"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
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

    # ---- CU-D03: Duplicate email — Create after Create ----
    def test_CU_D03_duplicate_email_create(self, cu_page):
        """Create customer with same email as existing customer.
        Document: Allowed or blocked?
        """
        log.info("CU-D03: Duplicate email — Create after Create")
        page = cu_page

        # Create first customer
        company1, data1 = _create_prerequisite_customer(page, "DupEmail1")
        email1 = data1.get("email", "")
        log.info(f"First customer email: {email1}")

        # Create second customer with same email but different Company Name & PAN
        data2 = generate_full_valid_customer_data("DupEmail2")
        data2["email"] = email1  # Same email

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data2)
        page.fill_step0(data2)
        page.click_stepper_next()
        page.wait_seconds(1)

        if "address_rows" in data2 and data2["address_rows"]:
            page.fill_address_row(0, data2["address_rows"][0])
        page.click_stepper_next()
        page.wait_seconds(1)

        if "bank_rows" in data2 and data2["bank_rows"]:
            page.fill_bank_row(0, data2["bank_rows"][0])

        page.click_submit()
        page.wait_seconds(3)

        validation_alert = page.handle_validation_warning(timeout=5)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        if form_still_open or errors or validation_alert:
            log.info(
                "Duplicate email rejected — validation working"
            )
        else:
            log.info(
                "Duplicate email allowed — "
                "system does not enforce uniqueness on email"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
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

    # ---- CU-D04: Duplicate PAN in Edit ----
    def test_CU_D04_duplicate_pan_edit(self, cu_page):
        """Edit existing customer, change PAN to another customer's PAN.
        Expect: Should be blocked (unique PAN validation).
        """
        log.info("CU-D04: Duplicate PAN in Edit")
        page = cu_page

        # Create two customers
        company1, data1 = _create_prerequisite_customer(page, "EditDupP1")
        company2, data2 = _create_prerequisite_customer(page, "EditDupP2")
        pan1 = data1.get("pan_number", "")
        log.info(f"Customer 1 PAN: {pan1}, Customer 2 PAN: {data2.get('pan_number', '')}")

        # Edit second customer to use first customer's PAN
        page.click_edit_button(company_name=company2)
        page.wait_seconds(2)

        if page.is_edit_mode():
            # Clear and type duplicate PAN
            page.type_text(
                page.PAN_NUMBER_INPUT, pan1, clear_first=True
            )
            page.click_update()
            page.wait_seconds(3)

            validation_alert = page.handle_validation_warning(timeout=5)
            form_still_open = page.is_add_form_open()
            errors = page.get_mat_error_text()

            if form_still_open or errors or validation_alert:
                log.info(
                    "Duplicate PAN rejected in Edit — "
                    "unique PAN validation working"
                )
            else:
                log.warning(
                    "BUG: Duplicate PAN allowed in Edit form — "
                    "unique PAN validation NOT enforced on update"
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
            log.warning("Could not open Edit form for second customer")

        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 3: Edit Form Validations (5 tests)
# ====================================================================

class TestEditFormValidations:
    """CU-E01 to CU-E05: Validation checks on the Edit form."""

    # ---- CU-E01: Edit — pre-populated fields ----
    def test_CU_E01_edit_prepopulated(self, cu_page):
        """Edit popup should show fields pre-populated with original data."""
        log.info("CU-E01: Edit pre-populated fields test")
        page = cu_page

        company_name, data = _create_prerequisite_customer(page, "EditPre")

        # Click Edit
        page.click_edit_button(company_name=company_name)
        page.wait_seconds(2)

        # Read form values
        form_values = page.get_form_field_values()

        assert form_values.get("company_name"), (
            "Company Name field empty in Edit form"
        )
        # The value should contain at least part of the original name
        assert "EditPre" in form_values.get("company_name", ""), (
            f"Edit form Company Name value '{form_values.get('company_name')}' "
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

    # ---- CU-E02: Edit — modify Company Name and save ----
    def test_CU_E02_edit_modify_company_name(self, cu_page):
        """Edit customer, change Company Name, Update.
        Verify change reflected in table.
        """
        log.info("CU-E02: Edit modify Company Name test")
        page = cu_page

        company_name, data = _create_prerequisite_customer(page, "EditMod")

        # Edit with new Company Name
        edit_data = generate_valid_edit_data("Updated")
        result = page.edit_customer(company_name, edit_data)

        if result["status"] == "PASSED":
            log.info("Customer updated successfully")
        else:
            log.warning(f"Edit failed: {result.get('error', 'unknown')}")

        # Verify updated name in table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_customer_in_table(edit_data["company_name"])

        assert found, (
            f"Updated customer '{edit_data['company_name']}' not found in table"
        )
        log.info(f"Customer updated and found in table: {edit_data['company_name']}")

    # ---- CU-E03: Edit — clear required field and try to save ----
    def test_CU_E03_edit_clear_required_field(self, cu_page):
        """Edit customer, clear Company Name, Update.
        Expect: Validation error.
        """
        log.info("CU-E03: Edit clear required field test")
        page = cu_page

        company_name, data = _create_prerequisite_customer(page, "EditClr")

        # Open Edit and clear the Company Name field
        page.click_edit_button(company_name=company_name)
        page.wait_seconds(1)

        # Clear the Company Name field via JS (Angular reactive form)
        page.driver.execute_script(
            "var i = document.querySelector("
            "  \"input[name='Company Name']\");"
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
            "BUG: Edit form submitted with empty Company Name — no validation"
        )
        if errors:
            log.info(f"Validation errors after clearing Company Name: {errors}")

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

    # ---- CU-E04: Edit — invalid email ----
    def test_CU_E04_edit_invalid_email(self, cu_page):
        """Edit customer, change email to invalid format.
        Expect: 'Invalid Email' error.
        """
        log.info("CU-E04: Edit invalid email test")
        page = cu_page

        company_name, data = _create_prerequisite_customer(page, "EditInvE")

        # Open Edit and change email to invalid format
        page.click_edit_button(company_name=company_name)
        page.wait_seconds(1)

        page.type_text(
            page.EMAIL_INPUT, generate_invalid_email(), clear_first=True
        )
        page.wait_seconds(1)

        # Check for 'Invalid Email' mat-error
        errors = page.get_mat_error_text()
        if errors and "Invalid Email" in str(errors):
            log.info("'Invalid Email' mat-error displayed correctly")
        else:
            log.info(
                f"No 'Invalid Email' error yet. Errors: {errors}. "
                "Attempting Update to trigger validation..."
            )
            page.click_update()
            page.wait_seconds(2)

            validation_alert = page.handle_validation_warning(timeout=3)
            form_still_open = page.is_add_form_open()
            errors = page.get_mat_error_text()

            if form_still_open or errors or validation_alert:
                log.info("Invalid email rejected in Edit — validation working")
            else:
                log.warning(
                    "BUG: Invalid email was accepted in Edit form"
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

    # ---- CU-E05: Edit — verify Update button instead of Submit ----
    def test_CU_E05_edit_update_button(self, cu_page):
        """Edit customer — verify button says 'Update' not 'Submit'."""
        log.info("CU-E05: Edit Update button verification")
        page = cu_page

        company_name, data = _create_prerequisite_customer(page, "EditBtn")

        page.click_edit_button(company_name=company_name)
        page.wait_seconds(2)

        if page.is_edit_mode():
            # Look for Update button in popup footer
            try:
                update_buttons = page.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class,'popup-footer')]//button"
                    "[contains(.,'Update') or @type='submit']"
                )
                if update_buttons:
                    btn_text = update_buttons[0].text.strip()
                    log.info(f"Footer button text: '{btn_text}'")

                    assert "Update" in btn_text, (
                        f"Expected 'Update' button text but got: '{btn_text}'"
                    )
                    log.info("Update button confirmed in Edit mode")
                else:
                    log.warning("No submit/update button found in popup footer")
            except Exception as e:
                log.warning(f"Could not verify Update button: {e}")
        else:
            log.warning("Could not open Edit form")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass


# ====================================================================
# PHASE 4: Search & Filter Edge Cases (5 tests)
# ====================================================================

class TestSearchFilter:
    """CU-S01 to CU-S05: Search and Filter edge cases."""

    # ---- CU-S01: Search by Company Name ----
    def test_CU_S01_search_exact_company_name(self, cu_page):
        """Create customer, search by company name — verify result found."""
        log.info("CU-S01: Search by Company Name")
        page = cu_page

        company_name, data = _create_prerequisite_customer(page, "SearchEx")

        found = page.search_item(company_name)
        page.wait_seconds(3)

        # Verify the customer appears in search results
        in_table = page.is_customer_in_table(company_name)

        assert found or in_table, (
            f"Exact search failed for: {company_name}"
        )
        log.info(f"Exact search found: {company_name}")

        # Clear search
        page.clear_search()
        page.wait_seconds(2)

    # ---- CU-S02: Search with partial match ----
    def test_CU_S02_search_partial_match(self, cu_page):
        """Search with partial company name — document:
        Does it find partial matches?
        """
        log.info("CU-S02: Search with partial match")
        page = cu_page

        company_name, data = _create_prerequisite_customer(page, "SearchPar")

        # Use first 8 chars as partial search term
        partial_name = company_name[:8]
        log.info(f"Searching with partial name: {partial_name}")

        found = page.search_item(partial_name)
        page.wait_seconds(3)

        # Check if customer appears in search results
        in_table = page.is_customer_in_table(company_name)

        if in_table:
            log.info(
                f"Partial search found customer: {partial_name} -> {company_name}"
            )
        else:
            log.info(
                f"Partial search did NOT find customer: "
                f"{partial_name} -> {company_name}. "
                "Search may require exact match only."
            )

        # Clear search
        page.clear_search()
        page.wait_seconds(2)

    # ---- CU-S03: Search with no results ----
    def test_CU_S03_search_no_results(self, cu_page):
        """Search for non-existent string — expect
        'No results found' or 'No data to display'.
        """
        log.info("CU-S03: Search with no results")
        page = cu_page

        nonexistent = "ZZZ_NONEXISTENT_CUSTOMER_99999"
        found = page.search_item(nonexistent)
        page.wait_seconds(3)

        # Check for "no data" or "empty state" message
        no_data_visible = False
        try:
            no_data_elements = page.driver.find_elements(
                By.CSS_SELECTOR,
                ".empty-state__title, .no-data, .no-data-message, "
                "td.no-data, .mat-mdc-table .empty-row"
            )
            for el in no_data_elements:
                try:
                    if el.is_displayed():
                        no_data_visible = True
                        log.info(f"No data message: {el.text.strip()}")
                        break
                except Exception:
                    continue
        except Exception:
            pass

        # Check if table has no rows
        try:
            rows = page.driver.find_elements(
                By.CSS_SELECTOR,
                "app-dynamic-table table tbody tr, table tbody tr"
            )
            visible_rows = [
                r for r in rows
                if r.is_displayed() and r.text.strip()
            ]
            if not visible_rows:
                no_data_visible = True
                log.info("Table is empty — no results found")
        except Exception:
            pass

        if no_data_visible:
            log.info("Search returned no results — expected behavior")
        else:
            log.info(
                "Search may have returned results for non-existent string, "
                "or no-data indicator not found"
            )

        # Clear search
        page.clear_search()
        page.wait_seconds(2)

    # ---- CU-S04: Search with special characters ----
    def test_CU_S04_search_special_chars(self, cu_page):
        """Search for '!@#$%' — document: handled gracefully or error."""
        log.info("CU-S04: Search with special characters")
        page = cu_page

        special_query = "!@#$%"
        found = page.search_item(special_query)
        page.wait_seconds(3)

        # Check if the search was handled gracefully (no JS errors, page still works)
        try:
            # Check for JS errors in console
            logs = page.driver.get_log("browser")
            error_logs = [
                l for l in logs
                if "SEVERE" in l.get("level", "")
            ]
            if error_logs:
                log.warning(
                    f"JS errors during special char search: "
                    f"{[l.get('message', '') for l in error_logs[:3]]}"
                )
            else:
                log.info("Search with special chars handled gracefully — no JS errors")
        except Exception:
            log.info("Could not check browser logs")

        # Verify page is still functional
        page_is_ok = page.is_page_loaded()
        if page_is_ok:
            log.info("Page still functional after special char search")
        else:
            log.warning("Page may be broken after special char search")

        # Clear search
        page.clear_search()
        page.wait_seconds(2)

    # ---- CU-S05: Search then clear ----
    def test_CU_S05_search_then_clear(self, cu_page):
        """Search, get results, clear search, refresh —
        expect: All results return.
        """
        log.info("CU-S05: Search then clear test")
        page = cu_page

        company_name, data = _create_prerequisite_customer(page, "SearchClr")

        # Search for the specific customer
        page.search_item(company_name)
        page.wait_seconds(3)

        # Count results after search
        try:
            rows_after_search = page.driver.find_elements(
                By.CSS_SELECTOR,
                "app-dynamic-table table tbody tr, table tbody tr"
            )
            search_count = len([
                r for r in rows_after_search
                if r.is_displayed() and r.text.strip()
            ])
            log.info(f"Rows after search: {search_count}")
        except Exception:
            search_count = 0

        # Clear search
        page.clear_search()
        page.wait_seconds(2)

        # Click refresh
        page.click_refresh()
        page.wait_seconds(3)

        # Count results after clear
        try:
            rows_after_clear = page.driver.find_elements(
                By.CSS_SELECTOR,
                "app-dynamic-table table tbody tr, table tbody tr"
            )
            clear_count = len([
                r for r in rows_after_clear
                if r.is_displayed() and r.text.strip()
            ])
            log.info(f"Rows after clear+refresh: {clear_count}")
        except Exception:
            clear_count = 0

        # After clearing, we should have at least as many rows as the search
        assert clear_count >= search_count, (
            f"After clearing search, row count ({clear_count}) "
            f"should be >= search count ({search_count})"
        )
        log.info(
            f"Search then clear working: {search_count} -> {clear_count} rows"
        )


# ====================================================================
# PHASE 5: Popup & UI Behaviors (8 tests)
# ====================================================================

class TestPopupUIBehaviors:
    """CU-P01 to CU-P08: Popup and UI behavior tests."""

    # ---- CU-P01: Open and close Add form ----
    def test_CU_P01_open_close_add_form(self, cu_page):
        """Click Add, verify form opens. Click Cancel, verify form closes."""
        log.info("CU-P01: Open and close Add form")
        page = cu_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        log.info("Add form opened successfully")

        # Click Cancel
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

        page.wait_seconds(1)

        # Verify form closed
        form_open = page.is_add_form_open()
        assert not form_open, "Form still open after Cancel"
        log.info("Add form closed successfully after Cancel")

    # ---- CU-P02: Close via X button ----
    def test_CU_P02_close_via_x_button(self, cu_page):
        """Open form, click X close button — verify form closes."""
        log.info("CU-P02: Close via X button")
        page = cu_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Click X close button
        try:
            close_btn = page.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-actions')]//button"
                "[.//mat-icon[text()='close']]"
            )
            page.driver.execute_script("arguments[0].click();", close_btn)
            page.wait_seconds(1)
        except Exception:
            log.warning("X button not found, trying close_popup fallback")
            try:
                page.close_popup()
            except Exception:
                pass

        page.wait_seconds(1)

        # Verify form closed
        form_open = page.is_add_form_open()
        assert not form_open, "Form still open after clicking X"
        log.info("Form closed via X button")

    # ---- CU-P03: Fullscreen toggle ----
    def test_CU_P03_fullscreen_toggle(self, cu_page):
        """Open form, click fullscreen, verify popup expands.
        Click again, verify popup shrinks.
        """
        log.info("CU-P03: Fullscreen toggle")
        page = cu_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Get initial popup dimensions
        try:
            popup = page.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up, .big-model, "
                "mat-dialog-container"
            )
            initial_width = popup.size["width"]
            initial_height = popup.size["height"]
            log.info(
                f"Initial popup size: {initial_width}x{initial_height}"
            )
        except Exception:
            initial_width = 0
            initial_height = 0
            log.warning("Could not get initial popup dimensions")

        # Click fullscreen button
        try:
            fullscreen_btn = page.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-actions')]//button"
                "[.//mat-icon[text()='fullscreen']]"
            )
            page.driver.execute_script("arguments[0].click();", fullscreen_btn)
            page.wait_seconds(1)
        except Exception:
            log.warning("Fullscreen button not found")

        # Get expanded popup dimensions
        try:
            popup = page.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up, .big-model, "
                "mat-dialog-container"
            )
            expanded_width = popup.size["width"]
            expanded_height = popup.size["height"]
            log.info(
                f"Expanded popup size: {expanded_width}x{expanded_height}"
            )

            if expanded_width >= initial_width and expanded_height >= initial_height:
                log.info("Popup expanded on fullscreen click")
            else:
                log.info("Popup size did not increase — fullscreen may not work")
        except Exception:
            log.warning("Could not get expanded popup dimensions")

        # Click fullscreen again to shrink
        try:
            fullscreen_btn = page.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-actions')]//button"
                "[.//mat-icon[text()='fullscreen']]"
            )
            page.driver.execute_script("arguments[0].click();", fullscreen_btn)
            page.wait_seconds(1)
            log.info("Fullscreen toggle clicked again")
        except Exception:
            log.warning("Could not click fullscreen toggle again")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- CU-P04: No Delete option ----
    def test_CU_P04_no_delete_option(self, cu_page):
        """Check listing page for Delete button per row.
        Document: No delete option exists (if confirmed).
        """
        log.info("CU-P04: No Delete option check")
        page = cu_page

        # Create a prerequisite customer to ensure at least one row exists
        company_name, data = _create_prerequisite_customer(page, "NoDel")

        # Look for delete button in table rows
        delete_buttons = []
        try:
            # Common delete button selectors
            delete_buttons = page.driver.find_elements(
                By.CSS_SELECTOR,
                "td .cdk-column-delete button, "
                "td .delete button, "
                "button[mattooltip='Delete'], "
                "td button[color='warn']"
            )
        except Exception:
            pass

        # Also check for delete icon in action columns
        try:
            delete_icons = page.driver.find_elements(
                By.XPATH,
                "//td[contains(@class,'cdk-column-delete') or "
                "contains(@class,'cdk-column-actions')]//button"
                "[.//mat-icon[text()='delete' or text()='delete_outline']]"
            )
            delete_buttons.extend(delete_icons)
        except Exception:
            pass

        if not delete_buttons:
            log.info(
                "No Delete button found in table rows — "
                "Customer screen has no delete option (confirmed)"
            )
        else:
            log.info(
                f"Delete buttons found: {len(delete_buttons)} — "
                "Customer screen has delete option"
            )

    # ---- CU-P05: Cancel mid-form ----
    def test_CU_P05_cancel_mid_form(self, cu_page):
        """Fill some fields, click Cancel.
        Reopen form, verify fields are empty (no state leakage).
        """
        log.info("CU-P05: Cancel mid-form test")
        page = cu_page

        page.open_add_form()
        page.wait_seconds(1)

        # Fill some fields
        data = generate_valid_customer_data("MidFill")
        page.fill_universal_fields(data)
        page.wait_seconds(1)

        # Verify fields have values
        company_name_value = page.get_input_value(page.COMPANY_NAME_INPUT)
        log.info(f"Company Name filled: {company_name_value}")
        assert company_name_value, "Company Name should have been filled"

        # Cancel the form
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        page.wait_seconds(1)

        # Reopen the form
        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not reopen"

        # Verify fields are empty (no state leakage)
        company_name_after = page.get_input_value(page.COMPANY_NAME_INPUT)
        if company_name_after == "" or company_name_after is None:
            log.info("No state leakage — fields are empty after reopening form")
        else:
            log.warning(
                f"STATE LEAKAGE: Company Name still has value "
                f"'{company_name_after}' after cancel and reopen"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- CU-P06: Double-click Submit ----
    def test_CU_P06_double_click_submit(self, cu_page):
        """Fill valid data, click Submit twice rapidly.
        Document: Does it create duplicate or handle gracefully?
        """
        log.info("CU-P06: Double-click Submit test")
        page = cu_page

        data = generate_full_valid_customer_data("DblSub")

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill address row
        if "address_rows" in data and data["address_rows"]:
            page.fill_address_row(0, data["address_rows"][0])
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill bank row
        if "bank_rows" in data and data["bank_rows"]:
            page.fill_bank_row(0, data["bank_rows"][0])

        # Double-click Submit rapidly
        try:
            submit_btn = page.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[@type='submit']"
            )
            # Click twice rapidly via JS
            page.driver.execute_script("arguments[0].click();", submit_btn)
            page.driver.execute_script("arguments[0].click();", submit_btn)
        except Exception:
            log.warning("Could not find Submit button for double-click")
            try:
                page.click_submit()
            except Exception:
                pass

        page.wait_seconds(3)

        # Handle any validation alerts
        try:
            page.handle_validation_warning(timeout=3)
        except Exception:
            pass

        # Close popup
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

        # Check for duplicates in the table
        company_name = data.get("company_name", "")
        try:
            all_rows = page.driver.find_elements(
                By.CSS_SELECTOR,
                "app-dynamic-table table tbody tr, table tbody tr"
            )
            matching_rows = [
                r for r in all_rows
                if company_name in r.text
            ]
            match_count = len(matching_rows)

            if match_count <= 1:
                log.info(
                    f"No duplicate created from double-click "
                    f"(found {match_count} row(s) for '{company_name}')"
                )
            else:
                log.warning(
                    f"BUG: Double-click created {match_count} rows "
                    f"for '{company_name}' — no debounce on Submit"
                )
        except Exception:
            log.info("Could not verify duplicate count after double-click")

    # ---- CU-P07: Stepper step headers clickable ----
    def test_CU_P07_stepper_step_headers_clickable(self, cu_page):
        """After filling Step 0 and clicking Next, click on Step 0 header.
        Verify: Can navigate back via header click.
        """
        log.info("CU-P07: Stepper step headers clickable test")
        page = cu_page

        data = generate_valid_customer_data("StepHead")

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_step0_active(), "Step 0 should be active initially"

        # Fill Step 0 and go to Step 1
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Verify we're on Step 1
        step1_active = page.is_step1_active()
        if step1_active:
            log.info("Navigated to Step 1")

            # Click on Step 0 header to go back
            page.go_to_step(0)
            page.wait_seconds(1)

            # Verify we're back on Step 0
            step0_active = page.is_step0_active()
            if step0_active:
                log.info(
                    "Step 0 header is clickable — "
                    "can navigate back via header click"
                )
            else:
                log.info(
                    "Step 0 header is NOT clickable — "
                    "stepper may be in linear mode"
                )
        else:
            log.warning(
                "Could not navigate to Step 1 — "
                "cannot test header navigation"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- CU-P08: Address grid — add row ----
    def test_CU_P08_address_grid_add_row(self, cu_page):
        """On Step 1, click Add Row (+) button.
        Verify: Second empty row appears.
        """
        log.info("CU-P08: Address grid — add row test")
        page = cu_page

        data = generate_valid_customer_data("AddRow")

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Count initial rows in address grid
        try:
            initial_rows = page.driver.find_elements(
                By.CSS_SELECTOR,
                ".grid-container .grid-table tbody tr"
            )
            initial_count = len([
                r for r in initial_rows
                if r.is_displayed()
            ])
            log.info(f"Initial address grid rows: {initial_count}")
        except Exception:
            initial_count = 0
            log.warning("Could not count initial address grid rows")

        # Click Add Row (+) button for address grid
        try:
            add_row_btn = page.driver.find_element(
                By.XPATH,
                "(//button[contains(@class,'mat-mdc-icon-button mat-primary')]"
                "[.//mat-icon[text()='add']])[1]"
            )
            page.driver.execute_script("arguments[0].click();", add_row_btn)
            page.wait_seconds(1)
        except Exception:
            log.warning("Address grid Add Row button not found")

        # Count rows after adding
        try:
            after_rows = page.driver.find_elements(
                By.CSS_SELECTOR,
                ".grid-container .grid-table tbody tr"
            )
            after_count = len([
                r for r in after_rows
                if r.is_displayed()
            ])
            log.info(f"Address grid rows after Add: {after_count}")

            if after_count > initial_count:
                log.info(
                    f"Second address row added successfully "
                    f"({initial_count} -> {after_count})"
                )
            else:
                log.warning(
                    f"Row count did not increase after clicking Add "
                    f"({initial_count} -> {after_count})"
                )
        except Exception:
            log.warning("Could not count address grid rows after Add")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass


# ====================================================================
# PHASE 6: Bug-specific (4 tests)
# ====================================================================

class TestBugSpecific:
    """CU-B01 to CU-B04: Tests targeting specific known bugs."""

    # ---- CU-B01: BUG-001 — mat-select form model not synced ----
    @pytest.mark.xfail(
        reason="BUG-001: Browser-clicked mat-select does NOT update "
               "Angular reactive form model — Submit fires 'Validation Failed'",
        strict=False,
    )
    def test_CU_B01_mat_select_form_model_not_synced(self, cu_page):
        """Open form, fill ALL fields including dropdowns via normal
        Selenium clicks. Submit. Expect: Validation Failed (because
        Angular form doesn't recognize dropdown selections).

        This test uses @pytest.mark.xfail since we know the bug exists.
        """
        log.info("CU-B01: BUG-001 — mat-select form model not synced")
        page = cu_page

        data = generate_full_valid_customer_data("Bug001")

        page.open_add_form()
        page.wait_seconds(1)

        # Fill ALL fields using normal Selenium/browser clicks
        # (NOT the JS value-setter workaround)
        page.fill_universal_fields_browser_click(data)
        page.fill_step0_browser_click(data)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill address row
        if "address_rows" in data and data["address_rows"]:
            page.fill_address_row_browser_click(0, data["address_rows"][0])
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill bank row
        if "bank_rows" in data and data["bank_rows"]:
            page.fill_bank_row_browser_click(0, data["bank_rows"][0])

        # Click Submit
        page.click_submit()
        page.wait_seconds(3)

        # BUG-001: Despite all fields being filled via browser clicks,
        # Angular form model doesn't recognize mat-select selections
        # so Submit will fail with "Validation Failed"
        validation_alert = page.handle_validation_warning(timeout=5)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        # If BUG-001 is present, validation fails even with all fields filled
        if validation_alert and "Validation Failed" in str(validation_alert):
            log.info(
                "BUG-001 CONFIRMED: 'Validation Failed' despite all fields "
                "filled via browser clicks — mat-select form model not synced"
            )
        elif form_still_open or errors:
            log.info(
                "Form blocked after browser-click submit — "
                "may be BUG-001 or other validation"
            )
        else:
            # This means the bug was fixed — test will XPASS
            log.info(
                "BUG-001 may be FIXED: Form submitted successfully "
                "with browser-clicked dropdowns"
            )

        # The assertion that should pass when BUG-001 is fixed:
        # Form should NOT show validation error when all fields are filled
        assert not (validation_alert and "Validation Failed" in str(validation_alert)), (
            "BUG-001: mat-select browser clicks don't sync with Angular form model"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass
        try:
            page.force_close_form_popup()
        except Exception:
            pass

    # ---- CU-B02: BUG-002 — Stepper non-linear validation ----
    @pytest.mark.xfail(
        reason="BUG-002: Stepper allows advancing with empty required fields — "
               "non-linear validation",
        strict=False,
    )
    def test_CU_B02_stepper_nonlinear_validation(self, cu_page):
        """Open form with all fields empty. Click Next twice.
        Verify: Reached Step 2 without any validation.
        """
        log.info("CU-B02: BUG-002 — Stepper non-linear validation")
        page = cu_page

        page.open_add_form()
        page.wait_seconds(1)

        # Confirm we start on Step 0
        assert page.is_step0_active(), "Should start on Step 0"

        # Click Next with all fields empty — should be blocked but BUG-002
        page.click_stepper_next()
        page.wait_seconds(1)

        # Check if we advanced to Step 1 without validation
        on_step1 = page.is_step1_active()
        log.info(f"After first Next (empty): on Step 1 = {on_step1}")

        if on_step1:
            # Click Next again to try Step 2
            page.click_stepper_next()
            page.wait_seconds(1)
            on_step2 = page.is_step2_active()
            log.info(f"After second Next (empty): on Step 2 = {on_step2}")

        # The assertion that should pass when BUG-002 is fixed:
        # We should NOT have been able to advance past Step 0 with empty fields
        assert not on_step1, (
            "BUG-002 CONFIRMED: Stepper allowed advancing to Step 1 "
            "with all fields empty — no per-step validation"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- CU-B03: BUG-003 — Pin Code required mismatch ----
    def test_CU_B03_pin_code_required_mismatch(self, cu_page):
        """Fill all fields including Pin Code = empty. Submit.
        Document: Does it require Pin Code or not?
        """
        log.info("CU-B03: BUG-003 — Pin Code required mismatch")
        page = cu_page

        data = generate_full_valid_customer_data("Bug003")
        # Explicitly set pin_code to empty
        if "address_rows" in data and data["address_rows"]:
            data["address_rows"][0]["pin_code"] = ""

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill address row without Pin Code
        if "address_rows" in data and data["address_rows"]:
            page.fill_address_row(0, data["address_rows"][0])
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill bank row
        if "bank_rows" in data and data["bank_rows"]:
            page.fill_bank_row(0, data["bank_rows"][0])

        page.click_submit()
        page.wait_seconds(3)

        validation_alert = page.handle_validation_warning(timeout=5)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        # Check the Pin Code input's HTML required attribute
        pin_code_required = False
        try:
            pin_code_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Pin Code']"
            )
            required_attr = pin_code_input.get_attribute("required")
            aria_required = pin_code_input.get_attribute("aria-required")
            pin_code_required = (
                required_attr == "true" or aria_required == "true"
            )
            log.info(
                f"Pin Code HTML required={required_attr}, "
                f"aria-required={aria_required}"
            )
        except Exception:
            log.info("Could not check Pin Code HTML required attribute")

        # Check the column header for asterisk
        header_has_asterisk = False
        try:
            headers = page.driver.find_elements(
                By.CSS_SELECTOR,
                ".grid-container .grid-table th, "
                ".grid-container .grid-table thead td"
            )
            for h in headers:
                if "Pin Code" in h.text:
                    header_has_asterisk = "*" in h.text
                    log.info(
                        f"Pin Code header text: '{h.text}', "
                        f"has asterisk: {header_has_asterisk}"
                    )
                    break
        except Exception:
            log.info("Could not check Pin Code column header")

        if form_still_open or errors or validation_alert:
            log.info(
                "BUG-003: Submit was BLOCKED without Pin Code — "
                "Pin Code IS required despite HTML attribute saying optional"
            )
        else:
            log.info(
                "BUG-003 CONFIRMED: Submit was ALLOWED without Pin Code — "
                "Pin Code is NOT required despite header asterisk"
            )

        if header_has_asterisk and not pin_code_required:
            log.warning(
                "BUG-003 CONFIRMED: Header shows 'Pin Code *' "
                "but HTML input has required=false — mismatch"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
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

    # ---- CU-B04: BUG-004 — Bank fields required mismatch ----
    def test_CU_B04_bank_fields_required_mismatch(self, cu_page):
        """Fill all fields but leave Bank Name empty. Submit.
        Document: Does it require Bank Name or not?
        """
        log.info("CU-B04: BUG-004 — Bank fields required mismatch")
        page = cu_page

        data = generate_full_valid_customer_data("Bug004")
        # Explicitly set bank fields to empty
        if "bank_rows" in data and data["bank_rows"]:
            data["bank_rows"][0]["bank_name"] = ""
            data["bank_rows"][0]["branch"] = ""

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill address row
        if "address_rows" in data and data["address_rows"]:
            page.fill_address_row(0, data["address_rows"][0])
        page.click_stepper_next()
        page.wait_seconds(1)

        # Fill bank row without Bank Name/Branch
        if "bank_rows" in data and data["bank_rows"]:
            page.fill_bank_row(0, data["bank_rows"][0])

        page.click_submit()
        page.wait_seconds(3)

        validation_alert = page.handle_validation_warning(timeout=5)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        # Check the Bank Name input's HTML required attribute
        bank_name_required = False
        try:
            bank_name_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Bank Name']"
            )
            required_attr = bank_name_input.get_attribute("required")
            aria_required = bank_name_input.get_attribute("aria-required")
            bank_name_required = (
                required_attr == "true" or aria_required == "true"
            )
            log.info(
                f"Bank Name HTML required={required_attr}, "
                f"aria-required={aria_required}"
            )
        except Exception:
            log.info("Could not check Bank Name HTML required attribute")

        # Check the bank grid column headers for asterisks
        header_has_asterisk = False
        try:
            headers = page.driver.find_elements(
                By.CSS_SELECTOR,
                "(.grid-container)[2] .grid-table th, "
                ".grid-container:nth-of-type(2) .grid-table thead td"
            )
            for h in headers:
                if "Bank Name" in h.text or "Branch" in h.text:
                    has_star = "*" in h.text
                    log.info(
                        f"Bank header text: '{h.text}', "
                        f"has asterisk: {has_star}"
                    )
                    if has_star:
                        header_has_asterisk = True
        except Exception:
            log.info("Could not check Bank grid column headers")

        if form_still_open or errors or validation_alert:
            log.info(
                "BUG-004: Submit was BLOCKED without Bank Name/Branch — "
                "Bank Name/Branch IS required despite HTML attribute"
            )
        else:
            log.info(
                "BUG-004 CONFIRMED: Submit was ALLOWED without "
                "Bank Name/Branch — Bank fields are NOT required "
                "despite header asterisks"
            )

        if header_has_asterisk and not bank_name_required:
            log.warning(
                "BUG-004 CONFIRMED: Bank Name/Branch headers show asterisks "
                "but HTML inputs have required=false — mismatch"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
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
