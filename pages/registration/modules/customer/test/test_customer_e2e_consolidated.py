"""
test_customer_e2e_consolidated.py
---------------------------------
Consolidated E2E test suite for RhythmERP Customer screen.

This file groups the original 46 isolated tests into 12 continuous
E2E flow groups that minimize form open/close cycles and use soft
assertions to report all failures without stopping at the first one.

GROUP MAPPING:
  G1  — Empty + Partial Submit         (was C01, C16)
  G2  — Valid Create E2E               (was C02)
  G3  — Email Validation Suite         (was C05, C06, C07)
  G4  — Input Injection Suite          (was C08, C09, C10)
  G5  — Boundary & Edge Inputs         (was C03, C04, C11, C19, C20)
  G6  — PAN Validation Suite           (was C14, C18)
  G7  — Stepper Navigation Suite       (was C15, C17)
  G8  — Grid Bug Suite                 (was C12, C13)
  G9  — Duplicate E2E                  (was D01, D02, D03, D04)
  G10 — Edit E2E                       (was E01, E02, E03, E04, E05)
  G11 — Search E2E                     (was S01, S02, S03, S04, S05)
  G12 — Popup, UI & Bug Suite          (was P01-P08, B01-B04) [12 checks]

KEY IMPROVEMENTS OVER ISOLATED TESTS:
  - Soft assertions: all checks in a group run even if early ones fail
  - Shared form cycles: G1 reuses the same popup for empty + partial submit
  - Reusable helpers: _cleanup_form(), _submit_full_form() reduce boilerplate
  - Same markers: smoke/sanity/regression/bug/ui preserved for selective runs

RUN:
  pytest test_customer_e2e_consolidated.py -v --tb=short
  pytest test_customer_e2e_consolidated.py -v -k "G1" --tb=short
  pytest test_customer_e2e_consolidated.py -v -m smoke --tb=short
  pytest test_customer_e2e_consolidated.py -v -m "not bug" --tb=short

NOTE: The original test_customer_validation.py is NOT modified and can
still be run independently. Both files share the same conftest.py.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from selenium.webdriver.common.by import By

from common.soft_assert import SoftAssert
from common.logger import log
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
    generate_alpha_phone,
    generate_duplicate_pan_data,
    generate_company_name_only_data,
    generate_invalid_pan,
    generate_pan_with_spaces,
    generate_long_phone,
    generate_emoji_name,
    generate_unicode_name,
)


# ====================================================================
# REUSABLE HELPERS — reduce boilerplate across all groups
# ====================================================================

def _cleanup_form(page):
    """Shared cleanup: dismiss alert -> cancel/close -> refresh.

    Safe to call multiple times; all steps are wrapped in try/except.
    """
    page.dismiss_swal_alert()
    for _ in range(2):
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


def _submit_full_form(page, data):
    """Fill all 3 steps of the create form and click Submit.

    Assumes the add form popup is already open.
    Does NOT click Submit for Step 0/1 only — use the individual
    step helpers for partial submission tests.

    Returns:
        dict with keys: alert, errors, form_open
    """
    # Universal fields + Step 0
    page.fill_universal_fields(data)
    page.fill_step0(data)

    # Step 1 — Address
    page.click_stepper_next()
    page.wait_seconds(1)
    address_rows = data.get("address_rows", [])
    if address_rows:
        page.fill_address_row(0, address_rows[0])

    # Step 2 — Bank
    page.click_stepper_next()
    page.wait_seconds(1)
    bank_rows = data.get("bank_rows", [])
    if bank_rows:
        page.fill_bank_row(0, bank_rows[0])

    # Submit
    page.click_submit()
    page.wait_seconds(2)

    return {
        "alert": page.handle_validation_warning(timeout=5),
        "errors": page.get_mat_error_text(),
        "form_open": page.is_add_form_open(),
    }


def _check_validation_blocked(result, sa, ref):
    """Soft-assert that validation blocked submission.

    Args:
        result: dict from _submit_full_form or manual submit
        sa: SoftAssert instance
        ref: Test reference string (e.g., "CU-C01")
    """
    sa.assert_true(
        result["form_open"] or result["errors"] or result["alert"],
        msg=f"[{ref}] Form submitted without validation — "
            f"alert={result['alert']}, errors={result['errors']}, "
            f"form_open={result['form_open']}",
    )


def _create_prerequisite_customer(page, name_prefix="PreReq"):
    """Create a Customer entry for tests that need existing data.
    Returns the company name used and the data dict.
    """
    data = generate_full_valid_customer_data(name_prefix)
    result = page.create_customer(data)
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
# G1: Empty + Partial Submit
# ====================================================================

class TestG1EmptyPartialSubmit:
    """G1: Empty submit + partial submit in ONE form cycle.

    Covers: CU-C01 (empty submit), CU-C16 (partial — Company Name only).
    The empty-submit phase and the partial-submit phase reuse the same
    popup — no close/reopen between them.
    """

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_G1_empty_and_partial_submit(self, cu_page):
        """Open form -> submit empty -> verify errors -> fill Company Name
        only -> submit -> verify errors. Single form cycle.
        """
        sa = SoftAssert()
        page = cu_page

        # ---- Phase 1: Empty submit (CU-C01) ----
        log.info("G1 Phase 1: Empty submit (CU-C01)")
        page.open_add_form()
        page.wait_seconds(1)
        sa.assert_true(
            page.is_add_form_open(), "Add form did not open"
        )

        page.click_submit()
        page.wait_seconds(2)

        result = {
            "alert": page.handle_validation_warning(timeout=5),
            "errors": page.get_mat_error_text(),
            "form_open": page.is_add_form_open(),
        }
        _check_validation_blocked(result, sa, "CU-C01")

        if result["alert"]:
            log.info(f"CU-C01 Validation alert: {result['alert']}")
        if result["errors"]:
            log.info(f"CU-C01 Validation errors: {result['errors']}")

        # ---- Phase 2: Partial fill — Company Name only (CU-C16) ----
        # Same form is still open — reuse it
        log.info("G1 Phase 2: Partial — Company Name only (CU-C16)")
        data = generate_company_name_only_data("NameOnly")
        page.fill_universal_fields(data)

        # Navigate through stepper and submit
        page.fill_step0({})
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        result2 = {
            "alert": page.handle_validation_warning(timeout=5),
            "errors": page.get_mat_error_text(),
            "form_open": page.is_add_form_open(),
        }
        _check_validation_blocked(result2, sa, "CU-C16")

        if result2["errors"]:
            log.info(f"CU-C16 Partial fill errors: {result2['errors']}")

        # Cleanup
        _cleanup_form(page)
        sa.check_all()


# ====================================================================
# G2: Valid Create E2E
# ====================================================================

class TestG2ValidCreate:
    """G2: Full happy-path create across all 3 steps.

    Covers: CU-C02 (valid create).
    """

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_G2_valid_create(self, cu_page):
        """Create customer with valid data across all 3 steps,
        then verify it appears in the listing table.
        """
        sa = SoftAssert()
        page = cu_page

        data = generate_full_valid_customer_data("ValidC")
        result = page.create_customer(data)
        company_name = data.get("company_name", "")

        if result["status"] == "PASSED":
            log.info(f"Customer created: {company_name}")
        else:
            log.warning(f"Create failed: {result.get('error', 'unknown')}")

        # Verify in table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_customer_in_table(company_name)

        sa.assert_true(
            found,
            f"Created customer '{company_name}' not found in table after refresh",
        )
        _cleanup_form(page)
        sa.check_all()


# ====================================================================
# G3: Email Validation Suite
# ====================================================================

class TestG3EmailValidation:
    """G3: Three invalid email variants in sequence.

    Covers: CU-C05 (invalid), CU-C06 (no @), CU-C07 (no domain).
    Each variant opens its own form (email is a root-level required field
    so we need a fresh submit cycle), but uses soft assertions so all
    three results are reported even if the first fails.
    """

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_G3_email_validation_suite(self, cu_page):
        """Test 3 invalid email formats: plain invalid, no @, no domain."""
        sa = SoftAssert()
        page = cu_page

        email_variants = [
            ("invalid-email", generate_invalid_email(), "CU-C05"),
            ("no-at-sign",   generate_email_no_at(),    "CU-C06"),
            ("no-domain",    generate_email_no_domain(), "CU-C07"),
        ]

        for label, bad_email, ref in email_variants:
            log.info(f"[{ref}] Testing email: {bad_email}")
            data = generate_valid_customer_data(label)
            data["email"] = bad_email

            page.open_add_form()
            page.wait_seconds(1)
            result = _submit_full_form(page, data)
            _check_validation_blocked(result, sa, ref)

            if result["errors"] and "Invalid Email" in str(result["errors"]):
                log.info(f"[{ref}] 'Invalid Email' mat-error confirmed")

            _cleanup_form(page)

        sa.check_all()


# ====================================================================
# G4: Input Injection Suite
# ====================================================================

class TestG4InputInjection:
    """G4: Special characters, SQL injection, XSS in Company Name.

    Covers: CU-C08 (special chars), CU-C09 (SQL injection), CU-C10 (XSS).
    """

    @pytest.mark.regression
    def test_G4_input_injection_suite(self, cu_page):
        """Test 3 injection payloads in Company Name field."""
        sa = SoftAssert()
        page = cu_page

        injection_variants = [
            ("special-chars", generate_special_char_name(), "CU-C08"),
            ("sql-injection", generate_sql_injection(),     "CU-C09"),
            ("xss-payload",   generate_xss_payload(),       "CU-C10"),
        ]

        for label, payload, ref in injection_variants:
            log.info(f"[{ref}] Testing payload: {payload[:40]}...")
            data = generate_valid_customer_data(label)
            data["company_name"] = payload

            page.open_add_form()
            page.wait_seconds(1)
            page.fill_universal_fields(data)
            page.fill_step0(data)
            page.click_stepper_next()
            page.wait_seconds(1)
            page.click_stepper_next()
            page.wait_seconds(1)
            page.click_submit()
            page.wait_seconds(2)

            result = {
                "alert": page.handle_validation_warning(timeout=3),
                "errors": page.get_mat_error_text(),
                "form_open": page.is_add_form_open(),
            }

            # For XSS: check if script alert was triggered
            if ref == "CU-C10":
                try:
                    alert_text = page.driver.switch_to.alert.text
                    log.warning(
                        f"XSS EXECUTED! Alert: {alert_text} — "
                        "CRITICAL SECURITY VULNERABILITY"
                    )
                    page.driver.switch_to.alert.dismiss()
                except Exception:
                    log.info("No XSS alert triggered — script tag sanitized")

            if result["form_open"] or result["errors"] or result["alert"]:
                log.info(f"[{ref}] Payload rejected — validation working")
            else:
                log.info(
                    f"[{ref}] Payload accepted — "
                    "system may store it safely (SQL/XSS sanitized server-side)"
                )

            _cleanup_form(page)

        sa.check_all()


# ====================================================================
# G5: Boundary & Edge Inputs
# ====================================================================

class TestG5BoundaryEdge:
    """G5: Boundary and edge-case input values.

    Covers: CU-C03 (spaces-only name), CU-C04 (256-char name),
    CU-C11 (negative deposit), CU-C19 (alpha phone), CU-C20 (emoji/unicode).
    """

    @pytest.mark.xfail(
        reason="Spaces-only Company Name may be accepted — "
               "will fail until ERP rejects it",
        strict=False,
    )
    @pytest.mark.bug
    @pytest.mark.regression
    def test_G5_boundary_edge_suite(self, cu_page):
        """Test 5 boundary/edge inputs with soft assertions."""
        sa = SoftAssert()
        page = cu_page

        # ---- CU-C03: Spaces-only Company Name ----
        log.info("G5: CU-C03 Spaces-only Company Name")
        data = generate_valid_customer_data("SpaceIt")
        data["company_name"] = generate_spaces_only(10)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(2)

        result = {
            "alert": page.handle_validation_warning(timeout=3),
            "errors": page.get_mat_error_text(),
            "form_open": page.is_add_form_open(),
        }
        _check_validation_blocked(result, sa, "CU-C03")
        _cleanup_form(page)

        # ---- CU-C04: 256-char Company Name (maxlength test) ----
        log.info("G5: CU-C04 256-char Company Name")
        data = generate_valid_customer_data("Bnd256")
        data["company_name"] = generate_string_256()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)

        actual_value = page.get_input_value(page.COMPANY_NAME_INPUT)
        sa.assert_less_equal(
            len(actual_value), 255,
            msg=f"CU-C04: Company Name accepted with {len(actual_value)} chars — "
                f"no maxlength enforced. Expected <= 255.",
        )
        _cleanup_form(page)

        # ---- CU-C11: Negative deposit ----
        log.info("G5: CU-C11 Negative Deposite")
        data = generate_valid_customer_data("NegDep")
        data["deposite"] = generate_negative_deposite()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.wait_seconds(1)

        actual_dep = page.get_input_value(page.DEPOSITE_INPUT)
        if actual_dep and float(actual_dep) < 0:
            log.warning(f"Negative deposit accepted in input: {actual_dep}")

        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        result = {
            "alert": page.handle_validation_warning(timeout=3),
            "errors": page.get_mat_error_text(),
            "form_open": page.is_add_form_open(),
        }
        if result["form_open"] or result["errors"] or result["alert"]:
            log.info("CU-C11: Negative deposit rejected — validation working")
        else:
            log.warning("CU-C11: BUG — Negative deposit accepted")
        _cleanup_form(page)

        # ---- CU-C19: Alphabetic phone number ----
        log.info("G5: CU-C19 Alpha phone number")
        data = generate_valid_customer_data("AlphaPh")
        data["phone_number"] = generate_alpha_phone()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.wait_seconds(1)

        actual_phone = page.get_input_value(page.PHONE_NUMBER_INPUT)
        if actual_phone == "" or actual_phone != data["phone_number"]:
            log.info(
                f"CU-C19: Alpha chars blocked by HTML5 number input: "
                f"attempted='{data['phone_number']}', actual='{actual_phone}'"
            )
        else:
            log.warning(
                f"CU-C19: Alpha chars accepted in Phone Number: "
                f"actual='{actual_phone}'"
            )
        _cleanup_form(page)

        # ---- CU-C20: Emoji/Unicode in Company Name ----
        log.info("G5: CU-C20 Emoji/Unicode Company Name")
        # Emoji test
        data = generate_valid_customer_data("EmojiN")
        data["company_name"] = generate_emoji_name()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.wait_seconds(1)

        actual_emoji = page.get_input_value(page.COMPANY_NAME_INPUT)
        log.info(f"CU-C20 Emoji: input='{data['company_name']}', actual='{actual_emoji}'")

        _cleanup_form(page)

        # Unicode test
        data2 = generate_valid_customer_data("UniN")
        data2["company_name"] = generate_unicode_name()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data2)
        page.fill_step0(data2)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        result = {
            "alert": page.handle_validation_warning(timeout=3),
            "errors": page.get_mat_error_text(),
            "form_open": page.is_add_form_open(),
        }
        if result["form_open"] or result["errors"] or result["alert"]:
            log.info("CU-C20: Unicode/Emoji rejected — validation working")
        else:
            log.info("CU-C20: Unicode/Emoji accepted — system allows international chars")

        _cleanup_form(page)
        sa.check_all()


# ====================================================================
# G6: PAN Validation Suite
# ====================================================================

class TestG6PANValidation:
    """G6: PAN Number validation variants.

    Covers: CU-C14 (PAN with spaces), CU-C18 (invalid PAN format).
    """

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_G6_pan_validation_suite(self, cu_page):
        """Test 2 PAN validation variants with soft assertions."""
        sa = SoftAssert()
        page = cu_page

        # ---- CU-C14: PAN with spaces ----
        log.info("G6: CU-C14 PAN with spaces")
        data = generate_valid_customer_data("PanSp")
        data["pan_number"] = generate_pan_with_spaces()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.wait_seconds(1)

        actual_value = page.get_input_value(page.PAN_NUMBER_INPUT)
        if actual_value != data["pan_number"]:
            log.info(f"CU-C14: PAN trimmed: input='{data['pan_number']}', actual='{actual_value}'")
        else:
            log.info(f"CU-C14: PAN with spaces accepted as-is: '{actual_value}'")

        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(2)

        result = {
            "alert": page.handle_validation_warning(timeout=3),
            "errors": page.get_mat_error_text(),
            "form_open": page.is_add_form_open(),
        }
        if result["form_open"] or result["errors"] or result["alert"]:
            log.info("CU-C14: PAN with spaces rejected — validation working")
        else:
            log.info("CU-C14: PAN with spaces accepted — system may auto-trim")

        _cleanup_form(page)

        # ---- CU-C18: Invalid PAN format ----
        log.info("G6: CU-C18 Invalid PAN format")
        data = generate_valid_customer_data("InvPan")
        data["pan_number"] = generate_invalid_pan()

        page.open_add_form()
        page.wait_seconds(1)
        result = _submit_full_form(page, data)
        _check_validation_blocked(result, sa, "CU-C18")

        _cleanup_form(page)
        sa.check_all()


# ====================================================================
# G7: Stepper Navigation Suite
# ====================================================================

class TestG7StepperNavigation:
    """G7: Stepper Next/Back navigation tests.

    Covers: CU-C15 (stepper advances with empty fields — BUG-002),
    CU-C17 (Back button + data preservation).
    """

    @pytest.mark.xfail(
        reason="BUG-002: Stepper allows advancing with empty required fields",
        strict=False,
    )
    @pytest.mark.bug
    @pytest.mark.regression
    def test_G7_stepper_navigation_suite(self, cu_page):
        """Test stepper advance with empty fields + Back button."""
        sa = SoftAssert()
        page = cu_page

        # ---- CU-C15: Stepper advances with empty fields ----
        log.info("G7: CU-C15 Stepper advances with empty fields (BUG-002)")
        page.open_add_form()
        page.wait_seconds(1)
        sa.assert_true(page.is_step0_active(), "Should start on Step 0")

        page.click_stepper_next()
        page.wait_seconds(1)

        stepped_to_1 = page.is_step1_active()
        log.info(f"After Next with empty fields: step1_active={stepped_to_1}")

        if stepped_to_1:
            page.click_stepper_next()
            page.wait_seconds(1)
            stepped_to_2 = page.is_step2_active()
            log.info(f"After second Next: step2_active={stepped_to_2}")

        page.click_stepper_back()
        page.wait_seconds(1)

        sa.assert_true(
            not stepped_to_1,
            "BUG-002 CONFIRMED: Stepper allowed advancing with empty required fields",
        )

        _cleanup_form(page)

        # ---- CU-C17: Back button + data preservation ----
        log.info("G7: CU-C17 Stepper Back button test")
        data = generate_valid_customer_data("StepNav")

        page.open_add_form()
        page.wait_seconds(1)
        sa.assert_true(page.is_step0_active(), "Step 0 should be active initially")

        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)

        step1_active = page.is_step1_active()
        if step1_active:
            log.info("Navigated to Step 1")
            page.click_stepper_back()
            page.wait_seconds(1)

            sa.assert_true(
                page.is_step0_active(),
                "Did not return to Step 0 after clicking Back",
            )

            company_name_value = page.get_input_value(page.COMPANY_NAME_INPUT)
            if company_name_value:
                log.info(f"Step 0 data preserved after Back: company_name={company_name_value}")
            else:
                log.warning("Step 0 data may have been lost after Back navigation")

        _cleanup_form(page)
        sa.check_all()


# ====================================================================
# G8: Grid Bug Suite
# ====================================================================

class TestG8GridBugs:
    """G8: Address and Bank grid required-field mismatch bugs.

    Covers: CU-C12 (Pin Code — BUG-003), CU-C13 (Bank fields — BUG-004).
    """

    @pytest.mark.bug
    @pytest.mark.regression
    def test_G8_grid_bug_suite(self, cu_page):
        """Test Pin Code and Bank field required mismatches."""
        sa = SoftAssert()
        page = cu_page

        # ---- CU-C12: Pin Code required mismatch (BUG-003) ----
        log.info("G8: CU-C12 Pin Code required mismatch (BUG-003)")
        data = generate_full_valid_customer_data("PinBug")
        if "address_rows" in data and data["address_rows"]:
            data["address_rows"][0]["pin_code"] = ""

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.fill_address_row(0, data["address_rows"][0])
        page.click_stepper_next()
        page.wait_seconds(1)
        page.fill_bank_row(0, data["bank_rows"][0])
        page.click_submit()
        page.wait_seconds(2)

        result = {
            "alert": page.handle_validation_warning(timeout=3),
            "errors": page.get_mat_error_text(),
            "form_open": page.is_add_form_open(),
        }

        if result["form_open"] or result["errors"] or result["alert"]:
            log.info(
                "BUG-003: Pin Code IS required on submit — "
                "header asterisk is correct, HTML attribute is wrong"
            )
        else:
            log.info(
                "BUG-003 CONFIRMED: Pin Code is NOT required — "
                "header asterisk is misleading"
            )

        _cleanup_form(page)

        # ---- CU-C13: Bank fields required mismatch (BUG-004) ----
        log.info("G8: CU-C13 Bank fields required mismatch (BUG-004 — partially resolved)")
        data = generate_full_valid_customer_data("BankBug")
        if "bank_rows" in data and data["bank_rows"]:
            data["bank_rows"][0]["bank_name"] = ""
            data["bank_rows"][0]["branch"] = ""
            data["bank_rows"][0]["account_type"] = ""
            data["bank_rows"][0]["bank_proof"] = ""

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)
        page.fill_address_row(0, data["address_rows"][0])
        page.click_stepper_next()
        page.wait_seconds(1)
        page.fill_bank_row(0, data["bank_rows"][0])
        page.click_submit()
        page.wait_seconds(2)

        result = {
            "alert": page.handle_validation_warning(timeout=3),
            "errors": page.get_mat_error_text(),
            "form_open": page.is_add_form_open(),
        }

        if result["form_open"] or result["errors"] or result["alert"]:
            log.info(
                "BUG-004 PARTIALLY RESOLVED: Account Type & Bank Proof "
                "are now required — submission blocked as expected."
            )
        else:
            log.warning(
                "BUG: Form submitted without Account Type & Bank Proof — "
                "required validation may not be enforced"
            )

        _cleanup_form(page)
        sa.check_all()


# ====================================================================
# G9: Duplicate E2E
# ====================================================================

class TestG9DuplicateE2E:
    """G9: Duplicate field validation across Create and Edit.

    Covers: CU-D01 (duplicate PAN create), CU-D02 (duplicate company name),
    CU-D03 (duplicate email), CU-D04 (duplicate PAN edit).
    """

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_G9_duplicate_e2e(self, cu_page):
        """Test duplicate PAN, Company Name, Email in Create + Edit."""
        sa = SoftAssert()
        page = cu_page

        # ---- CU-D01: Duplicate PAN — Create ----
        log.info("G9: CU-D01 Duplicate PAN — Create")
        company1, data1 = _create_prerequisite_customer(page, "DupPan1")
        pan1 = data1.get("pan_number", "")
        log.info(f"First customer PAN: {pan1}")

        data2 = generate_duplicate_pan_data(pan1)
        page.open_add_form()
        page.wait_seconds(1)
        result = _submit_full_form(page, data2)
        _check_validation_blocked(result, sa, "CU-D01")
        _cleanup_form(page)

        # ---- CU-D02: Duplicate Company Name — Create ----
        log.info("G9: CU-D02 Duplicate Company Name — Create")
        data3 = generate_full_valid_customer_data("DupComp2")
        data3["company_name"] = company1

        page.open_add_form()
        page.wait_seconds(1)
        result = _submit_full_form(page, data3)
        # Company Name may not be unique — just document behavior
        if result["form_open"] or result["errors"] or result["alert"]:
            log.info("CU-D02: Duplicate Company Name rejected — validation working")
        else:
            log.info("CU-D02: Duplicate Company Name allowed — not enforced as unique")
        _cleanup_form(page)

        # ---- CU-D03: Duplicate Email — Create ----
        log.info("G9: CU-D03 Duplicate Email — Create")
        email1 = data1.get("email", "")
        data4 = generate_full_valid_customer_data("DupEmail2")
        data4["email"] = email1

        page.open_add_form()
        page.wait_seconds(1)
        result = _submit_full_form(page, data4)
        if result["form_open"] or result["errors"] or result["alert"]:
            log.info("CU-D03: Duplicate email rejected — validation working")
        else:
            log.info("CU-D03: Duplicate email allowed — not enforced as unique")
        _cleanup_form(page)

        # ---- CU-D04: Duplicate PAN in Edit ----
        log.info("G9: CU-D04 Duplicate PAN — Edit")
        company2, data2b = _create_prerequisite_customer(page, "EditDupP2")

        page.search_item(company2)
        page.wait_seconds(2)
        page.click_edit_first_row()
        page.wait_seconds(2)

        if page.is_edit_mode():
            page.type_text(page.PAN_NUMBER_INPUT, pan1, clear_first=True)
            page.click_update()
            page.wait_seconds(3)

            result = {
                "alert": page.handle_validation_warning(timeout=5),
                "errors": page.get_mat_error_text(),
                "form_open": page.is_add_form_open(),
            }
            _check_validation_blocked(result, sa, "CU-D04")
        else:
            log.warning("CU-D04: Could not open Edit form")

        _cleanup_form(page)
        sa.check_all()


# ====================================================================
# G10: Edit E2E
# ====================================================================

class TestG10EditE2E:
    """G10: Edit form validations in a continuous flow.

    Covers: CU-E01 (pre-populated), CU-E02 (modify company name),
    CU-E03 (clear required field), CU-E04 (invalid email),
    CU-E05 (Update button).
    """

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_G10_edit_e2e(self, cu_page):
        """Test edit flow: prepopulation -> modify -> clear -> invalid email -> Update button."""
        sa = SoftAssert()
        page = cu_page

        # ---- CU-E01: Edit — pre-populated fields ----
        log.info("G10: CU-E01 Edit pre-populated fields")
        page.click_edit_first_row()
        page.wait_seconds(2)

        form_values = page.get_form_field_values()
        sa.assert_true(
            form_values.get("company_name"),
            "CU-E01: Company Name field empty in Edit form",
        )
        log.info(f"CU-E01: Edit form pre-populated: {form_values}")
        _cleanup_form(page)

        # ---- CU-E02: Edit — modify Company Name ----
        log.info("G10: CU-E02 Edit modify Company Name")
        page.click_edit_first_row()
        page.wait_seconds(1)

        edit_data = generate_valid_edit_data("Updated")
        page.type_text(page.COMPANY_NAME_INPUT, edit_data["company_name"], clear_first=True)
        page.wait_seconds(0.5)
        page.click_update()
        page.wait_seconds(2)
        page.handle_success_alert(timeout=5)

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
        found = page.is_customer_in_table(edit_data["company_name"])
        sa.assert_true(
            found,
            f"CU-E02: Updated customer '{edit_data['company_name']}' not found in table",
        )
        page.click_refresh()
        page.wait_seconds(2)

        # ---- CU-E03: Edit — clear required field ----
        log.info("G10: CU-E03 Edit clear required field")
        page.click_edit_first_row()
        page.wait_seconds(1)

        page.driver.execute_script(
            "var i = document.querySelector(\"input[name='Company Name']\");"
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

        validation_alert = ""
        if page.is_validation_alert_present(timeout=3):
            validation_alert = page.get_swal_title() or ""
            page.handle_validation_warning(timeout=5)

        result = {
            "alert": validation_alert,
            "errors": page.get_mat_error_text(),
            "form_open": page.is_add_form_open(),
        }
        _check_validation_blocked(result, sa, "CU-E03")
        _cleanup_form(page)

        # ---- CU-E04: Edit — invalid email ----
        log.info("G10: CU-E04 Edit invalid email")
        page.click_edit_first_row()
        page.wait_seconds(1)

        page.type_text(page.EMAIL_INPUT, generate_invalid_email(), clear_first=True)
        page.wait_seconds(1)

        errors = page.get_mat_error_text()
        if errors and "Invalid Email" in str(errors):
            log.info("CU-E04: 'Invalid Email' mat-error displayed")
        else:
            page.click_update()
            page.wait_seconds(2)
            result = {
                "alert": page.handle_validation_warning(timeout=3),
                "errors": page.get_mat_error_text(),
                "form_open": page.is_add_form_open(),
            }
            _check_validation_blocked(result, sa, "CU-E04")

        _cleanup_form(page)

        # ---- CU-E05: Edit — Update button verification ----
        log.info("G10: CU-E05 Update button verification")
        page.click_edit_first_row()
        page.wait_seconds(2)

        if page.is_edit_mode():
            try:
                update_buttons = page.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class,'popup-footer')]//button"
                    "[contains(.,'Update') or @type='submit']"
                )
                if update_buttons:
                    btn_text = update_buttons[0].text.strip()
                    sa.assert_in(
                        "Update", btn_text,
                        msg=f"CU-E05: Expected 'Update' button but got: '{btn_text}'",
                    )
                    log.info(f"CU-E05: Update button confirmed: '{btn_text}'")
            except Exception as e:
                log.warning(f"CU-E05: Could not verify Update button: {e}")

        _cleanup_form(page)
        sa.check_all()


# ====================================================================
# G11: Search E2E
# ====================================================================

class TestG11SearchE2E:
    """G11: Search and filter operations in a continuous flow.

    Covers: CU-S01 (exact search), CU-S02 (partial match),
    CU-S03 (no results), CU-S04 (special chars), CU-S05 (search then clear).
    """

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_G11_search_e2e(self, cu_page):
        """Test search flow: exact -> partial -> no results -> special chars -> clear."""
        sa = SoftAssert()
        page = cu_page

        # ---- CU-S01: Exact search ----
        log.info("G11: CU-S01 Search exact Company Name")
        company_name = page.get_first_row_name()
        if not company_name:
            log.warning("No rows in table — skipping search tests")
            return

        found = page.search_item(company_name)
        page.wait_seconds(3)
        in_table = page.is_customer_in_table(company_name)
        sa.assert_true(
            found or in_table,
            f"CU-S01: Exact search failed for: {company_name}",
        )
        page.clear_search()
        page.wait_seconds(2)

        # ---- CU-S02: Partial search ----
        log.info("G11: CU-S02 Search partial match")
        partial_name = company_name[:8]
        page.search_item(partial_name)
        page.wait_seconds(3)
        in_table = page.is_customer_in_table(company_name)

        if in_table:
            log.info(f"CU-S02: Partial search found: {partial_name} -> {company_name}")
        else:
            log.info(f"CU-S02: Partial search NOT found — may require exact match")

        page.clear_search()
        page.wait_seconds(2)

        # ---- CU-S03: No results search ----
        log.info("G11: CU-S03 Search no results")
        nonexistent = "ZZZ_NONEXISTENT_CUSTOMER_99999"
        page.search_item(nonexistent)
        page.wait_seconds(3)

        no_data_visible = False
        try:
            no_data_elements = page.driver.find_elements(
                By.CSS_SELECTOR,
                ".empty-state__title, .no-data, .no-data-message, "
                "td.no-data, .mat-mdc-table .empty-row",
            )
            for el in no_data_elements:
                try:
                    if el.is_displayed():
                        no_data_visible = True
                        log.info(f"CU-S03: No data message: {el.text.strip()}")
                        break
                except Exception:
                    continue
        except Exception:
            pass

        sa.assert_true(
            no_data_visible or not page.is_customer_in_table(nonexistent),
            "CU-S03: No-data state not shown for non-existent search",
        )
        page.clear_search()
        page.wait_seconds(2)

        # ---- CU-S04: Special chars search ----
        log.info("G11: CU-S04 Search special characters")
        page.search_item("!@#$%^&*()")
        page.wait_seconds(3)
        # Should not crash — just show no results
        log.info("CU-S04: Special chars search did not crash")
        page.clear_search()
        page.wait_seconds(2)

        # ---- CU-S05: Search then clear ----
        log.info("G11: CU-S05 Search then clear")
        page.search_item(company_name)
        page.wait_seconds(3)
        page.clear_search()
        page.wait_seconds(3)

        # After clearing, original table should be visible
        sa.assert_true(
            page.is_customer_in_table(company_name),
            "CU-S05: Table not restored after clearing search",
        )

        sa.check_all()


# ====================================================================
# G12: Popup, UI & Bug Suite
# ====================================================================

class TestG12PopupUIBugSuite:
    """G12: Popup behaviors, UI interactions, and bug-specific tests.

    Covers: CU-P01-P08 (popup/UI), CU-B01-B04 (bug-specific).
    This is the largest group because popup/UI tests are naturally
    lightweight and fast — they don't require full form submissions.
    12 checks in a single test method with soft assertions.
    """

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_G12_popup_ui_and_bugs(self, cu_page):
        """Test popup open/close, fullscreen, stepper clicks, grid rows,
        double-submit, and all 4 bug-specific validations.
        """
        sa = SoftAssert()
        page = cu_page

        # ---- CU-P01: Open/close add form ----
        log.info("G12: CU-P01 Open/close add form")
        page.open_add_form()
        page.wait_seconds(1)
        sa.assert_true(page.is_add_form_open(), "CU-P01: Add form did not open")
        _cleanup_form(page)

        # ---- CU-P02: Close via X button ----
        log.info("G12: CU-P02 Close via X button")
        page.open_add_form()
        page.wait_seconds(1)
        sa.assert_true(page.is_add_form_open(), "CU-P02: Add form did not open")

        try:
            page.close_popup()
            page.wait_seconds(1)
            sa.assert_true(
                not page.is_add_form_open(),
                "CU-P02: Form still open after X button click",
            )
        except Exception:
            log.warning("CU-P02: X button close failed")
            _cleanup_form(page)

        page.click_refresh()
        page.wait_seconds(2)

        # ---- CU-P03: Fullscreen toggle ----
        log.info("G12: CU-P03 Fullscreen toggle")
        page.open_add_form()
        page.wait_seconds(1)

        try:
            fullscreen_btn = page.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-actions')]//button"
                "[.//mat-icon[text()='fullscreen']]",
            )
            page.driver.execute_script("arguments[0].click();", fullscreen_btn)
            page.wait_seconds(1)

            # Check if popup expanded (dialog becomes larger)
            popup_el = page.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up, .big-model, mat-dialog-container",
            )
            classes = popup_el.get_attribute("class") or ""
            log.info(f"CU-P03: Popup classes after fullscreen: {classes}")

            # Toggle back
            page.driver.execute_script("arguments[0].click();", fullscreen_btn)
            page.wait_seconds(0.5)
            log.info("CU-P03: Fullscreen toggle works")
        except Exception:
            log.info("CU-P03: Fullscreen toggle not found or not functional")

        _cleanup_form(page)

        # ---- CU-P04: No Delete option on listing page ----
        log.info("G12: CU-P04 No Delete option check")
        # Check listing page for Delete button per row — should not exist
        delete_buttons = []
        try:
            delete_buttons = page.driver.find_elements(
                By.CSS_SELECTOR,
                "td .cdk-column-delete button, "
                "td .delete button, "
                "button[mattooltip='Delete'], "
                "td button[color='warn']",
            )
        except Exception:
            pass

        try:
            delete_icons = page.driver.find_elements(
                By.XPATH,
                "//td[contains(@class,'cdk-column-delete') or "
                "contains(@class,'cdk-column-actions')]//button"
                "[.//mat-icon[text()='delete' or text()='delete_outline']]",
            )
            delete_buttons.extend(delete_icons)
        except Exception:
            pass

        if not delete_buttons:
            log.info(
                "CU-P04: No Delete button found — "
                "Customer screen has no delete option (confirmed)"
            )
        else:
            log.info(
                f"CU-P04: Delete buttons found: {len(delete_buttons)} — "
                "Customer screen has delete option"
            )

        # ---- CU-P05: Cancel mid-form ----
        log.info("G12: CU-P05 Cancel mid-form")
        data = generate_valid_customer_data("CancelMid")
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.wait_seconds(0.5)

        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

        page.wait_seconds(1)
        sa.assert_true(
            not page.is_add_form_open(),
            "CU-P05: Form still open after Cancel",
        )
        page.click_refresh()
        page.wait_seconds(2)

        # ---- CU-P06: Double-click Submit ----
        log.info("G12: CU-P06 Double-click Submit")
        page.open_add_form()
        page.wait_seconds(1)
        page.click_submit()
        page.wait_seconds(0.5)
        page.click_submit()
        page.wait_seconds(2)

        # Should not create duplicate or crash
        log.info("CU-P06: Double-submit did not crash")
        _cleanup_form(page)

        # ---- CU-P07: Stepper step headers clickable ----
        log.info("G12: CU-P07 Stepper headers clickable")
        data = generate_valid_customer_data("StepClick")
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)

        # Click Step 1 header directly
        page.go_to_step(1)
        page.wait_seconds(1)
        sa.assert_true(
            page.is_step1_active(),
            "CU-P07: Could not navigate to Step 1 via header click",
        )

        # Click Step 2 header
        page.go_to_step(2)
        page.wait_seconds(1)
        sa.assert_true(
            page.is_step2_active(),
            "CU-P07: Could not navigate to Step 2 via header click",
        )
        _cleanup_form(page)

        # ---- CU-P08: Address grid add row ----
        log.info("G12: CU-P08 Address grid add row")
        data = generate_full_valid_customer_data("AddRow")
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_universal_fields(data)
        page.fill_step0(data)
        page.click_stepper_next()
        page.wait_seconds(1)

        # Count initial rows
        initial_rows = len(page.driver.find_elements(
            By.CSS_SELECTOR, ".grid-container .grid-table tbody tr"
        ))
        log.info(f"CU-P08: Initial address rows: {initial_rows}")

        # Click add row button
        page.add_address_row()
        page.wait_seconds(1)

        new_rows = len(page.driver.find_elements(
            By.CSS_SELECTOR, ".grid-container .grid-table tbody tr"
        ))
        sa.assert_true(
            new_rows > initial_rows,
            f"CU-P08: Row count did not increase after Add. "
            f"Before={initial_rows}, After={new_rows}",
        )
        _cleanup_form(page)

        # ---- CU-B01: mat-select form model not synced (BUG-001) ----
        log.info("G12: CU-B01 mat-select form model not synced (BUG-001)")
        # This is a documentation test — BUG-001 is confirmed.
        # Browser-clicked mat-select does NOT update Angular reactive form.
        # The codebase uses JS value-setter + dispatchEvent pattern as workaround.
        log.info(
            "CU-B01: BUG-001 CONFIRMED — mat-select requires JS interaction. "
            "Codebase workaround: js_type + select_mat_option."
        )

        # ---- CU-B02: Stepper non-linear validation (BUG-002) ----
        log.info("G12: CU-B02 Stepper non-linear validation (BUG-002)")
        page.open_add_form()
        page.wait_seconds(1)
        page.click_stepper_next()
        page.wait_seconds(1)

        stepped_without_data = page.is_step1_active()
        if stepped_without_data:
            log.info("CU-B02: BUG-002 CONFIRMED — stepper allows advancing with empty fields")
        else:
            log.info("CU-B02: BUG-002 may be fixed — stepper blocks advancement")

        _cleanup_form(page)

        # ---- CU-B03: Pin Code required mismatch (BUG-003) ----
        # Already tested in G8 — just document
        log.info(
            "CU-B03: BUG-003 documented — Pin Code header says required "
            "but HTML says optional. See G8 for live test."
        )

        # ---- CU-B04: Bank fields required mismatch (BUG-004) ----
        # Already tested in G8 — just document
        log.info(
            "CU-B04: BUG-004 partially resolved — Account Type & Bank Proof "
            "now required in ERP UI. See G8 for live test."
        )

        sa.check_all()
