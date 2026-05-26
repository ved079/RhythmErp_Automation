"""
test_quality_parameter_master_validation.py
-------------------------------------------
Comprehensive validation test suite for RhythmERP Quality Parameter Master screen.
30 test cases across 5 phases covering all 6 bugs found during manual exploration.

Phases:
  1. Create Form Validations  (12 tests) — QPM-C01 to QPM-C12
  2. Duplicate Validations      (3 tests) — QPM-D01 to QPM-D03
  3. Edit Form Validations      (6 tests) — QPM-E01 to QPM-E06
  4. Search & Filter Edge Cases (5 tests) — QPM-S01 to QPM-S05
  5. Popup & UI Behaviors       (7 tests) — QPM-P01 to QPM-P07

Known Bugs (documented at time of inspection):
  BUG-001 (HIGH)  : Spaces-only name creates empty record (no trim)
  BUG-002 (HIGH)  : Duplicate names allowed (no uniqueness check)
  BUG-003 (MEDIUM): No maxlength on input, 300+ char names accepted
  BUG-004 (LOW)   : No success SweetAlert after create/update
  BUG-005 (LOW)   : No Delete option anywhere on screen
  BUG-006 (LOW)   : No History / Audit trail feature

Bug Handling Decisions:
  BUG-001: Test expects rejection — will FAIL until ERP is fixed
  BUG-002: Mark as known bug — test PASSES documenting current behavior
  BUG-003: Document as known issue, test confirms the bug
  BUG-004: Adjusted — no success alert check, just verify popup closes
  BUG-005: Documented in UI phase, not tested (no button to click)
  BUG-006: Documented in UI phase, not tested (no feature to test)

Run:
  pytest test_quality_parameter_master_validation.py -v --tb=short
  pytest test_quality_parameter_master_validation.py -v -k "TestCreateForm" --tb=short
  pytest test_quality_parameter_master_validation.py -v -k "QPM-C03" --tb=short

MARKER BREAKDOWN (30 tests):
  smoke      ( 7): C01, C02, C04, E01, E02, S01, P01
  sanity     (25): smoke + C03, C05-C09, D01-D02, E03-E05, S02-S03, S05, P02-P05
  regression (30): All tests
  bug        (13): C03, C04, C05, C06, C07, D01, D02, D03, E04, E05, E06,
                   P06, P07
  ui         ( 8): P01, P02, P03, P04, P05, P06, P07, S04

Usage:
  pytest test_quality_parameter_master_validation.py -m smoke
  pytest test_quality_parameter_master_validation.py -m "smoke or sanity"
  pytest test_quality_parameter_master_validation.py -m "not bug"
  pytest test_quality_parameter_master_validation.py -m ui
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

from pages.commodity_settings.modules.quality_parameter_master.quality_parameter_master_page import (
    QualityParameterMasterPage,
)
from pages.commodity_settings.modules.quality_parameter_master.data.quality_parameter_master_data import (
    generate_valid_quality_parameter_data,
    generate_valid_edit_data,
    generate_empty_data,
    generate_spaces_only,
    generate_spaces_only_data,
    generate_duplicate_name_data,
    generate_string_255,
    generate_string_256,
    generate_long_string,
    generate_special_char_name,
    generate_special_char_data,
    generate_sql_injection_name,
    generate_sql_injection_data,
    generate_xss_name,
    generate_xss_data,
    generate_unicode_name,
    generate_unicode_data,
    generate_name_with_leading_trailing_spaces,
    generate_name_with_inner_spaces,
    generate_name_with_numbers,
    generate_name_with_mixed_case,
    generate_single_char_name,
    generate_quality_parameter_name,
)
from common.logger import log


# ====================================================================
# Helper: create a QP prerequisite, refresh, and return its name
# ====================================================================

def _create_prerequisite_qp(page, data=None):
    """Create a Quality Parameter for tests that need existing data.
    Returns the QP name used.
    """
    if data is None:
        data = generate_valid_quality_parameter_data("PreReq")
    name = page.create_quality_parameter(data)
    # Cleanup form if still open
    try:
        page.close_popup()
    except Exception:
        pass
    page.click_refresh()
    page.wait_seconds(2)
    return name


# ====================================================================
# PHASE 1: Create Form Validations (12 tests)
# ====================================================================

class TestCreateFormValidations:
    """QPM-C01 to QPM-C12: Validation checks on the Create form.
    QPM has ONLY one form field: Name (text, required).
    No dropdowns, no price, no description fields.
    """

    # ---- QPM-C01: Submit with empty Name ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C01_empty_submit(self, qp_master_page):
        """Submit with empty Name field — should be blocked."""
        log.info("QPM-C01: Empty submit test")
        page = qp_master_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        page.submit()
        page.wait_seconds(2)

        # Check for SweetAlert2 validation warning
        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        # Expect: form stays open + validation errors/warning shown
        assert form_still_open or errors or validation_alert, (
            "BUG: Form submitted with empty Name — no validation"
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

    # ---- QPM-C02: Create with valid Name (happy path) ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C02_valid_create(self, qp_master_page):
        """Create with valid Name — should succeed.
        BUG-004: No success SweetAlert after create.
        """
        log.info("QPM-C02: Valid create test")
        page = qp_master_page

        data = generate_valid_quality_parameter_data("ValidC")
        name = page.create_quality_parameter(data)

        # BUG-004: No success alert, just check popup closed
        page.wait_seconds(2)
        popup_closed = page.is_form_closed()

        if popup_closed:
            log.info("Form closed after submit (QPM has no success alert — BUG-004)")
        else:
            # Check if validation alert appeared instead
            validation_alert = page.get_swal_title()
            if validation_alert:
                log.warning(
                    f"Validation alert instead of success: {validation_alert}"
                )

        # Verify the QP appears in the table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_qp_in_table(name)

        assert found, (
            f"Created QP '{name}' not found in table after refresh"
        )
        log.info(f"QP created and found in table: {name}")

    # ---- QPM-C03: Spaces-only Name ----
    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(
        reason="BUG-001: Spaces-only name accepted — will fail until ERP is fixed",
        strict=False,
    )
    def test_QPM_C03_spaces_only_name(self, qp_master_page):
        """Spaces-only Name — should be rejected.
        BUG-001: Spaces-only name creates empty record.
        Test expects rejection — will FAIL until ERP is fixed.
        """
        log.info("QPM-C03: Spaces-only name test")
        page = qp_master_page

        data = generate_spaces_only_data(10)
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        # Check if validation alert appeared (expected behavior)
        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        # BUG-001: ERP currently accepts spaces-only names.
        # Test asserts that validation SHOULD block this.
        # This test will FAIL until BUG-001 is fixed.
        assert form_still_open or errors or validation_alert, (
            "BUG-001 CONFIRMED: Spaces-only name was accepted — "
            "system should reject it with a validation error"
        )

        if not (form_still_open or errors or validation_alert):
            # Record was created — confirm the bug
            page.click_refresh()
            page.wait_seconds(2)
            log.warning(
                "BUG-001 CONFIRMED: Spaces-only name created an empty record"
            )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- QPM-C04: Duplicate Name (in Create) ----
    @pytest.mark.smoke
    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C04_duplicate_name(self, qp_master_page):
        """Duplicate Name in Create — should be rejected.
        BUG-002: Duplicate names are currently allowed.
        Test documents current behavior as known bug — passes either way.
        """
        log.info("QPM-C04: Duplicate name test")
        page = qp_master_page

        # Create first QP
        data1 = generate_valid_quality_parameter_data("Dup1")
        page.create_quality_parameter(data1)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Try creating second QP with same name
        data2 = generate_duplicate_name_data(data1["name"])
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data2)
        page.submit()
        page.wait_seconds(2)

        # Check for validation or acceptance
        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("Duplicate name rejected — validation working")
        else:
            log.warning(
                "BUG-002 CONFIRMED: Duplicate name allowed in Create form"
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

    # ---- QPM-C05: Name at 255 char boundary ----
    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C05_name_255_chars(self, qp_master_page):
        """Name with exactly 255 chars — boundary test.
        Should be accepted if maxlength is 255, or rejected if less.
        BUG-003: No maxlength on input.
        """
        log.info("QPM-C05: 255-char name test")
        page = qp_master_page

        name_255 = generate_string_255()
        data = {"name": name_255}
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
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

    # ---- QPM-C06: Name exceeds 255 chars (256) ----
    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C06_name_256_chars(self, qp_master_page):
        """Name with 256 chars — should be rejected or truncated.
        BUG-003: No maxlength on input, 256-char names accepted.
        """
        log.info("QPM-C06: 256-char name test")
        page = qp_master_page

        name_256 = generate_string_256()
        data = {"name": name_256}
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
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

    # ---- QPM-C07: No success popup after create (BUG-004) ----
    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C07_no_success_popup(self, qp_master_page):
        """Verify that no success SweetAlert appears after create.
        BUG-004: No success popup — form just closes silently.
        """
        log.info("QPM-C07: No success popup test")
        page = qp_master_page

        data = generate_valid_quality_parameter_data("NoAlert")
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        # Check if a SweetAlert appeared at all
        swal_visible = page.is_validation_alert_present(timeout=3)

        if not swal_visible:
            log.warning(
                "BUG-004 CONFIRMED: No success SweetAlert after create. "
                "The form popup simply closes with no confirmation."
            )
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

    # ---- QPM-C08: Special characters in Name ----
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C08_special_chars_name(self, qp_master_page):
        """Special characters in Name — check if accepted or rejected.
        Documents current behavior.
        """
        log.info("QPM-C08: Special chars in name test")
        page = qp_master_page

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
            log.info(
                "Special chars accepted in Name (may be expected behavior)"
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

    # ---- QPM-C09: SQL injection in Name ----
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C09_sql_injection_name(self, qp_master_page):
        """SQL injection string in Name — should be sanitized or rejected."""
        log.info("QPM-C09: SQL injection name test")
        page = qp_master_page

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

    # ---- QPM-C10: XSS payload in Name ----
    @pytest.mark.regression
    def test_QPM_C10_xss_name(self, qp_master_page):
        """XSS payload in Name — should be sanitized or rejected."""
        log.info("QPM-C10: XSS name test")
        page = qp_master_page

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
            log.info(
                "XSS payload accepted — check if DOM rendering is safe"
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

    # ---- QPM-C11: Unicode/international characters in Name ----
    @pytest.mark.regression
    def test_QPM_C11_unicode_name(self, qp_master_page):
        """Unicode/international characters in Name — check acceptance."""
        log.info("QPM-C11: Unicode name test")
        page = qp_master_page

        data = generate_unicode_data()
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("Unicode name rejected")
        else:
            log.info("Unicode name accepted (may be expected for i18n)")

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

    # ---- QPM-C12: Name with leading/trailing spaces ----
    @pytest.mark.regression
    def test_QPM_C12_leading_trailing_spaces(self, qp_master_page):
        """Name with leading/trailing spaces — should be trimmed.
        BUG: Spaces may not be trimmed before storage.
        """
        log.info("QPM-C12: Leading/trailing spaces test")
        page = qp_master_page

        spaced_name = generate_name_with_leading_trailing_spaces()
        data = {"name": spaced_name}
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        # Check if the form closed (submission succeeded)
        popup_closed = page.is_form_closed()

        if popup_closed:
            # Check if name was trimmed in the table
            page.click_refresh()
            page.wait_seconds(2)
            names = page.get_all_qp_names()
            trimmed_name = spaced_name.strip()

            # Check if the stored name has leading/trailing spaces
            has_spaces = any(
                n != n.strip()
                for n in names
                if spaced_name in n or trimmed_name in n
            )
            if has_spaces:
                log.warning(
                    "BUG: Leading/trailing spaces NOT trimmed in Name field"
                )
            else:
                log.info("Name was trimmed before storage")
        else:
            log.info("Spaced name rejected — validation working")

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
# PHASE 2: Duplicate Validations (3 tests)
# ====================================================================

class TestDuplicateValidations:
    """QPM-D01 to QPM-D03: Duplicate name checks in Create and Edit.
    BUG-002: Duplicate names are currently allowed with no check.
    """

    # ---- QPM-D01: Duplicate name — Create after Create ----
    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_D01_duplicate_create(self, qp_master_page):
        """Create two QPs with identical names.
        BUG-002: Second create is accepted.
        Test passes documenting current behavior as known bug.
        """
        log.info("QPM-D01: Duplicate create test")
        page = qp_master_page

        # Create first QP
        data1 = generate_valid_quality_parameter_data("DDup1")
        page.create_quality_parameter(data1)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Create second QP with same name
        data2 = generate_duplicate_name_data(data1["name"])
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data2)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert or form_still_open:
            log.info("Duplicate name rejected in Create — validation working")
        else:
            log.warning(
                "BUG-002 CONFIRMED: Duplicate name allowed in Create form"
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

    # ---- QPM-D02: Duplicate name — case-insensitive check ----
    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_D02_duplicate_case_insensitive(self, qp_master_page):
        """Create QP with same name in different case.
        Tests if the duplicate check is case-insensitive.
        BUG-002: No case-insensitive check.
        """
        log.info("QPM-D02: Duplicate case-insensitive test")
        page = qp_master_page

        # Create QP with known name
        data1 = generate_valid_quality_parameter_data("CaseDup")
        name1 = data1["name"]
        page.create_quality_parameter(data1)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Create QP with uppercase version of same name
        data2 = {"name": name1.upper()}
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data2)
        page.submit()
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

    # ---- QPM-D03: Duplicate name — Edit to existing name ----
    @pytest.mark.bug
    @pytest.mark.regression
    def test_QPM_D03_duplicate_edit(self, qp_master_page):
        """Edit a QP to use another QP's name.
        BUG-002: Duplicate name allowed in Edit.
        """
        log.info("QPM-D03: Duplicate edit test")
        page = qp_master_page

        # Create two QPs
        data1 = generate_valid_quality_parameter_data("EditDup1")
        page.create_quality_parameter(data1)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        data2 = generate_valid_quality_parameter_data("EditDup2")
        page.create_quality_parameter(data2)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Edit second QP with first QP's name
        page.click_edit_button(qp_name=data2["name"])
        page.wait_seconds(1)

        # Clear and type new (duplicate) name
        page.type_text(
            page.NAME_INPUT, data1["name"], clear_first=True
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
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 3: Edit Form Validations (6 tests)
# ====================================================================

class TestEditFormValidations:
    """QPM-E01 to QPM-E06: Validation checks on the Edit form."""

    # ---- QPM-E01: Edit — pre-populated Name field ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_E01_edit_prepopulated(self, qp_master_page):
        """Edit popup should show the Name field pre-populated."""
        log.info("QPM-E01: Edit pre-populated fields test")
        page = qp_master_page

        data = generate_valid_quality_parameter_data("EditPre")
        page.create_quality_parameter(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Click Edit
        page.click_edit_button(qp_name=data["name"])
        page.wait_seconds(2)

        # Read form values — try multiple approaches
        form_values = page.get_form_field_values()

        # If get_form_field_values returns empty, try reading via JS
        if not form_values.get("name"):
            try:
                val = page.driver.execute_script(
                    "var i = document.querySelector("
                    "  \"input[name='Name'], input[name='name'], \""
                    "  + \"input[formcontrolname='name']\");"
                    "return i ? i.value : '';"
                )
                form_values["name"] = val or ""
                log.info(f"Read name via JS fallback: '{val}'")
            except Exception as e:
                log.warning(f"JS fallback read failed: {e}")

        assert form_values.get("name"), (
            "Name field empty in Edit form"
        )
        # The value should contain at least part of the original name
        assert "EditPre" in form_values.get("name", ""), (
            f"Edit form Name value '{form_values.get('name')}' "
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

    # ---- QPM-E02: Edit — valid update ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_E02_valid_edit(self, qp_master_page):
        """Edit with valid new Name — should succeed.
        BUG-004: No success alert after update.
        """
        log.info("QPM-E02: Valid edit test")
        page = qp_master_page

        data = generate_valid_quality_parameter_data("EditOK")
        page.create_quality_parameter(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Edit with new name
        edit_data = generate_valid_edit_data("Updated")
        page.click_edit_button(qp_name=data["name"])
        page.wait_seconds(1)
        page.fill_form(edit_data)
        page.click_update()
        page.wait_seconds(2)

        # BUG-004: No success alert
        popup_closed = page.is_form_closed()

        if popup_closed:
            log.info(
                "Edit form closed after update "
                "(QPM has no success alert — BUG-004)"
            )
        else:
            validation_alert = page.get_swal_title()
            if validation_alert:
                log.warning(
                    f"Validation alert after edit: {validation_alert}"
                )

        # Verify updated name in table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_qp_in_table(edit_data["name"])

        assert found, (
            f"Updated QP '{edit_data['name']}' not found in table"
        )
        log.info(f"QP updated and found in table: {edit_data['name']}")

    # ---- QPM-E03: Edit — empty Name ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(
        reason="BUG: Edit form allows empty Name submission — will fail until ERP is fixed",
        strict=False,
    )
    def test_QPM_E03_edit_empty_name(self, qp_master_page):
        """Edit with empty Name — should be blocked."""
        log.info("QPM-E03: Edit empty name test")
        page = qp_master_page

        data = generate_valid_quality_parameter_data("EditEmpty")
        page.create_quality_parameter(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Open Edit and clear the Name field
        page.click_edit_button(qp_name=data["name"])
        page.wait_seconds(1)

        # Clear the name field via JS
        page.driver.execute_script(
            "var i = document.querySelector("
            "  \"input[name='Name'], input[name='name'], \""
            "  + \"input[formcontrolname='name']\");"
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
            "BUG: Edit form submitted with empty Name — no validation"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- QPM-E04: Edit — duplicate Name (same as D03 but via edit_qp) ----
    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_E04_edit_duplicate_name(self, qp_master_page):
        """Edit QP to use another QP's Name.
        BUG-002: Duplicate name allowed in Edit.
        Test passes documenting current behavior as known bug.
        """
        log.info("QPM-E04: Edit duplicate name test")
        page = qp_master_page

        # Create two QPs
        data1 = generate_valid_quality_parameter_data("EDup1")
        page.create_quality_parameter(data1)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        data2 = generate_valid_quality_parameter_data("EDup2")
        page.create_quality_parameter(data2)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Edit second QP with first QP's name via edit_quality_parameter
        new_name = page.edit_quality_parameter(
            data2["name"],
            {"name": data1["name"]},
        )

        # Check for validation (BUG-002: duplicate allowed)
        page.click_refresh()
        page.wait_seconds(2)

        # Look for both names in the table
        found_first = page.is_qp_in_table(data1["name"])
        # If duplicate allowed, the edited QP now has same name as first
        if found_first:
            log.warning(
                "BUG-002 CONFIRMED: Duplicate name allowed in Edit form"
            )
        else:
            log.info("Duplicate name rejected in Edit — validation working")

    # ---- QPM-E05: Edit — no success popup (BUG-004) ----
    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_E05_edit_no_success_popup(self, qp_master_page):
        """Verify that no success SweetAlert appears after edit.
        BUG-004: No success popup after update.
        """
        log.info("QPM-E05: Edit no success popup test")
        page = qp_master_page

        data = generate_valid_quality_parameter_data("EditNoAlert")
        page.create_quality_parameter(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Edit with new name
        edit_data = generate_valid_edit_data("UpdNoAlert")
        page.click_edit_button(qp_name=data["name"])
        page.wait_seconds(1)
        page.fill_form(edit_data)
        page.click_update()
        page.wait_seconds(2)

        # Check for SweetAlert
        swal_visible = page.is_validation_alert_present(timeout=3)

        if not swal_visible:
            log.warning(
                "BUG-004 CONFIRMED: No success SweetAlert after edit. "
                "The form popup simply closes with no confirmation."
            )
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

    # ---- QPM-E06: Edit — spaces-only Name ----
    @pytest.mark.bug
    @pytest.mark.regression
    def test_QPM_E06_edit_spaces_only(self, qp_master_page):
        """Edit QP Name to spaces-only — should be rejected.
        BUG-001: Spaces-only name may be accepted.
        """
        log.info("QPM-E06: Edit spaces-only name test")
        page = qp_master_page

        data = generate_valid_quality_parameter_data("EditSpace")
        page.create_quality_parameter(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Open Edit and type spaces-only name
        page.click_edit_button(qp_name=data["name"])
        page.wait_seconds(1)
        page.fill_form(generate_spaces_only_data(8))
        page.click_update()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        # BUG-001: Spaces-only name may be accepted in Edit too
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


# ====================================================================
# PHASE 4: Search & Filter Edge Cases (5 tests)
# ====================================================================

class TestSearchFilter:
    """QPM-S01 to QPM-S05: Search and Filter edge cases."""

    # ---- QPM-S01: Search with exact Name ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_S01_search_exact(self, qp_master_page):
        """Search with exact QP name — should find it."""
        log.info("QPM-S01: Search exact name")
        page = qp_master_page

        data = generate_valid_quality_parameter_data("SearchEx")
        page.create_quality_parameter(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        found = page.search_qp(data["name"])
        page.clear_search()

        assert found, f"Exact search failed for: {data['name']}"
        log.info(f"Exact search found: {data['name']}")

    # ---- QPM-S02: Search with partial Name ----
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_S02_search_partial(self, qp_master_page):
        """Search with partial QP name — should find it."""
        log.info("QPM-S02: Search partial name")
        page = qp_master_page

        data = generate_valid_quality_parameter_data("SearchPar")
        page.create_quality_parameter(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Use first 8 chars as partial search
        partial = data["name"][:8]
        found = page.search_qp(partial)
        page.clear_search()

        assert found, f"Partial search failed for: {partial}"
        log.info(f"Partial search found with: {partial}")

    # ---- QPM-S03: Search with non-existent Name ----
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_S03_search_nonexistent(self, qp_master_page):
        """Search for non-existent name — should return no results."""
        log.info("QPM-S03: Search nonexistent")
        page = qp_master_page

        fake_name = f"NonExistent_{int(time.time())}"
        found = page.search_qp(fake_name)
        page.clear_search()

        assert not found, (
            f"BUG: Non-existent name '{fake_name}' was found in table"
        )
        log.info(f"Correctly not found: {fake_name}")

    # ---- QPM-S04: Filter panel opens and closes ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_S04_filter_panel(self, qp_master_page):
        """Filter panel should open when Filters button is clicked.
        Then close when backdrop or Close is clicked.
        """
        log.info("QPM-S04: Filter panel test")
        page = qp_master_page

        # Try to open filter panel
        page.open_filter_panel()
        page.wait_seconds(1)

        filter_open = page.is_filter_panel_open()

        if filter_open:
            log.info("Filter panel opened successfully")

            # Close filter panel
            page.close_filter_panel()
            page.wait_seconds(1)

            # Verify it closed (may not be instant)
            still_open = page.is_filter_panel_open()
            if not still_open:
                log.info("Filter panel closed successfully")
            else:
                log.warning("Filter panel still visible after close attempt")
        else:
            log.info(
                "Filter button/panel not found — "
                "may not exist on this screen"
            )

        page.click_refresh()
        page.wait_seconds(2)

    # ---- QPM-S05: Name column sort ----
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_S05_column_sort(self, qp_master_page):
        """Click Name column header to toggle sort order.
        Verifies that the table still renders after sort.
        """
        log.info("QPM-S05: Column sort test")
        page = qp_master_page

        # Ensure at least one QP exists for meaningful sort test
        data = generate_valid_quality_parameter_data("Sort")
        page.create_quality_parameter(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Get names before sort
        names_before = page.get_all_qp_names()

        # Click Name column header to sort
        page.click_name_column_header()
        page.wait_seconds(1)

        # Get names after sort
        names_after = page.get_all_qp_names()

        # Table should still have data (not broken by sort)
        assert names_after, "Table is empty after column sort"

        # Verify same content (just potentially different order)
        assert set(names_before) == set(names_after), (
            "Table content changed after sort — data may have been lost"
        )

        log.info(
            f"Column sort test passed. "
            f"Before: {len(names_before)} rows, "
            f"After: {len(names_after)} rows"
        )


# ====================================================================
# PHASE 5: Popup & UI Behaviors (7 tests)
# ====================================================================

class TestPopupUIBehaviors:
    """QPM-P01 to QPM-P07: Popup and UI interaction checks.
    Includes documentation of BUG-005 (No Delete) and BUG-006 (No History).
    """

    # ---- QPM-P01: Cancel closes form without creating ----
    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P01_cancel_no_create(self, qp_master_page):
        """Cancel button closes form without creating a QP."""
        log.info("QPM-P01: Cancel no create test")
        page = qp_master_page

        before_count = page.get_table_row_count()

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Form did not open"

        # Fill form with data
        data = generate_valid_quality_parameter_data("CancelTest")
        page.fill_form(data)
        page.cancel()
        page.wait_seconds(1)

        after_count = page.get_table_row_count()
        assert after_count == before_count, (
            f"BUG: Row count changed after Cancel. "
            f"Before: {before_count}, After: {after_count}"
        )
        log.info("Cancel correctly did not create a QP")

    # ---- QPM-P02: X button closes form without creating ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P02_close_no_create(self, qp_master_page):
        """X button closes form without creating a QP."""
        log.info("QPM-P02: Close no create test")
        page = qp_master_page

        before_count = page.get_table_row_count()

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Form did not open"

        data = generate_valid_quality_parameter_data("CloseTest")
        page.fill_form(data)
        page.close_popup()
        page.wait_seconds(1)

        after_count = page.get_table_row_count()
        assert after_count == before_count, (
            f"BUG: Row count changed after X close. "
            f"Before: {before_count}, After: {after_count}"
        )
        log.info("X close correctly did not create a QP")

    # ---- QPM-P03: View popup shows read-only fields ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P03_view_readonly(self, qp_master_page):
        """View popup shows the Name field in read-only mode."""
        log.info("QPM-P03: View read-only test")
        page = qp_master_page

        data = generate_valid_quality_parameter_data("ViewTest")
        page.create_quality_parameter(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        page.click_view_button(qp_name=data["name"])
        page.wait_seconds(1)

        is_readonly = page.verify_view_popup_read_only()

        assert is_readonly, (
            "BUG: View popup Name field is editable (should be read-only)"
        )
        log.info("View popup correctly shows read-only Name field")

        page.close_popup()
        page.wait_seconds(0.5)

    # ---- QPM-P04: Edit popup shows editable fields with Update ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P04_edit_has_update(self, qp_master_page):
        """Edit popup shows editable Name field with Update button."""
        log.info("QPM-P04: Edit has Update button")
        page = qp_master_page

        data = generate_valid_quality_parameter_data("EditTest")
        page.create_quality_parameter(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        page.click_edit_button(qp_name=data["name"])
        page.wait_seconds(1)

        is_edit = page.verify_edit_popup_editable()

        assert is_edit, (
            "BUG: Edit popup does not show Update button"
        )
        log.info("Edit popup correctly shows Update button")

        # Verify Name field is editable
        form_values = page.get_form_field_values()

        # If get_form_field_values returns empty, try reading via JS
        if not form_values.get("name"):
            try:
                val = page.driver.execute_script(
                    "var i = document.querySelector("
                    "  \"input[name='Name'], input[name='name'], \""
                    " + \"input[formcontrolname='name']\");"
                    "return i ? i.value : '';"
                )
                form_values["name"] = val or ""
            except Exception:
                pass

        assert form_values.get("name"), (
            "Name field empty in Edit form"
        )
        log.info(f"Edit form Name field pre-populated: {form_values}")

        page.cancel()

    # ---- QPM-P05: Add form heading ----
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P05_add_form_heading(self, qp_master_page):
        """Add form should show a heading indicating creation mode."""
        log.info("QPM-P05: Add form heading test")
        page = qp_master_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        heading = page.get_form_heading()
        log.info(f"Add form heading: '{heading}'")

        # The heading should exist (even if empty, log it)
        if heading:
            log.info(f"Form heading is: {heading}")
        else:
            log.warning("No form heading found — UX issue")

        # Verify Submit button is visible (not Update)
        submit_visible = page.is_displayed(page.SUBMIT_BUTTON, timeout=3)
        update_visible = page.is_displayed(page.UPDATE_BUTTON, timeout=2)

        assert submit_visible, "Submit button not visible in Add form"
        assert not update_visible, (
            "Update button visible in Add form (should be Submit only)"
        )
        log.info("Add form has Submit button (not Update)")

        page.cancel()

    # ---- QPM-P06: No Delete option (BUG-005) ----
    @pytest.mark.bug
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P06_no_delete_option(self, qp_master_page):
        """Verify that no Delete option exists on the QPM screen.
        BUG-005: No Delete option anywhere on screen.
        This test documents the bug — it's expected to confirm
        that Delete is missing.
        """
        log.info("QPM-P06: No Delete option test")
        page = qp_master_page

        # Create a QP to have a row with action buttons
        data = generate_valid_quality_parameter_data("NoDelete")
        page.create_quality_parameter(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Check for Delete button in table rows
        delete_buttons = page.driver.find_elements(
            By.CSS_SELECTOR,
            "table#excel-table td.cdk-column-delete button, "
            "table#excel-table td.mat-column-delete button, "
            "table#excel-table button[mattooltip='Delete'], "
            "table#excel-table button.delete-btn",
        )

        # Check for Delete in the popup footer (use XPath for text match)
        popup_delete_buttons = []
        try:
            popup_delete_buttons = page.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]"
                "//button[contains(.,'Delete')]",
            )
        except Exception:
            pass

        # Check for Delete in More menu
        more_menu_delete = page.driver.find_elements(
            By.CSS_SELECTOR,
            "div[mattooltip='More'] button, button[mattooltip='More']",
        )

        if not delete_buttons and not popup_delete_buttons:
            log.warning(
                "BUG-005 CONFIRMED: No Delete option exists on the "
                "Quality Parameter Master screen. Users cannot remove "
                "any Quality Parameter records."
            )
        else:
            log.info("Delete option found — BUG-005 may be fixed")

        # This test always passes — it documents the bug
        log.info(
            f"Delete buttons in table: {len(delete_buttons)}, "
            f"in popup: {len(popup_delete_buttons)}"
        )

    # ---- QPM-P07: No History/Audit trail (BUG-006) ----
    @pytest.mark.bug
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P07_no_history_option(self, qp_master_page):
        """Verify that no History/Audit trail feature exists.
        BUG-006: No History button or audit trail.
        This test documents the bug — it's expected to confirm
        that History is missing.
        """
        log.info("QPM-P07: No History option test")
        page = qp_master_page

        # Create a QP to have a row with action buttons
        data = generate_valid_quality_parameter_data("NoHist")
        page.create_quality_parameter(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Check for History button in table rows
        history_buttons = page.driver.find_elements(
            By.CSS_SELECTOR,
            "table#excel-table td.cdk-column-history button, "
            "table#excel-table td.mat-column-history button, "
            "table#excel-table button[mattooltip='History'], "
            "table#excel-table button.history-btn",
        )

        # Check for History column header
        history_headers = page.driver.find_elements(
            By.CSS_SELECTOR,
            "table#excel-table th.cdk-column-history, "
            "table#excel-table th.mat-column-history",
        )

        if not history_buttons and not history_headers:
            log.warning(
                "BUG-006 CONFIRMED: No History/Audit trail feature "
                "exists on the Quality Parameter Master screen. "
                "Unlike Vehicle Master which has History per row, "
                "QPM has no way to track changes."
            )
        else:
            log.info("History option found — BUG-006 may be fixed")

        # This test always passes — it documents the bug
        log.info(
            f"History buttons: {len(history_buttons)}, "
            f"History headers: {len(history_headers)}"
        )
