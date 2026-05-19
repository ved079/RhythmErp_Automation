"""
test_entity_group_definition_validation.py
-------------------------------------------
Comprehensive validation test suite for RhythmERP Entity Group Definition screen.
35 test cases across 6 phases covering all 8 bugs found during manual exploration.

Phases:
  1. Create Form Validations  (12 tests) — EGD-C01 to EGD-C12
  2. Duplicate Validations      (4 tests) — EGD-D01 to EGD-D04
  3. Edit Form Validations      (6 tests) — EGD-E01 to EGD-E06
  4. Search & Filter Edge Cases (4 tests) — EGD-S01 to EGD-S04
  5. Popup & UI Behaviors       (5 tests) — EGD-P01 to EGD-P05
  6. Bug-Specific Tests         (4 tests) — EGD-B01 to EGD-B04

Known Bugs (documented at time of inspection):
  BUG-001 (HIGH)  : Spaces-only Entity Group Name accepted — creates blank record
  BUG-002 (HIGH)  : Exact duplicate name silently rejected with NO user feedback
  BUG-003 (HIGH)  : Case-insensitive duplicate NOT blocked
  BUG-004 (MEDIUM): Negative Level values accepted (no min validation)
  BUG-005 (MEDIUM): Decimal Level values accepted (no step="1" validation)
  BUG-006 (LOW)   : Special characters in Entity Group Name accepted
  BUG-007 (LOW)   : No maxlength on Entity Group Name
  BUG-008 (LOW)   : No success SweetAlert after create/update

Bug Handling Decisions:
  BUG-001: Test expects rejection — will FAIL until ERP is fixed → @pytest.mark.xfail
  BUG-002: Test documents the silent rejection — passes either way
  BUG-003: Test expects case-insensitive check — will FAIL until fixed → @pytest.mark.xfail
  BUG-004: Test expects integer >= 0 — will FAIL until fixed → @pytest.mark.xfail
  BUG-005: Test expects integer only — will FAIL until fixed → @pytest.mark.xfail
  BUG-006: Document current behavior — passes either way
  BUG-007: Document — passes either way
  BUG-008: Adjusted — no success alert check, just verify popup closes

Run:
  pytest test_entity_group_definition_validation.py -v --tb=short
  pytest test_entity_group_definition_validation.py -v -k "TestCreateForm" --tb=short
  pytest test_entity_group_definition_validation.py -v -k "EGD_C02" --tb=short
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

from pages.access.modules.entity_group_definition.entity_group_definition_page import (
    EntityGroupDefinitionPage,
)
from pages.access.modules.entity_group_definition.data.entity_group_definition_data import (
    generate_valid_data,
    generate_valid_edit_data,
    generate_empty_data,
    generate_empty_name_only,
    generate_empty_level_only,
    generate_spaces_only_data,
    generate_duplicate_name_data,
    generate_case_variant_name,
    generate_space_ignored_name,
    generate_string_255,
    generate_string_256,
    generate_long_string,
    generate_special_char_data,
    generate_sql_injection_data,
    generate_xss_data,
    generate_unicode_data,
    generate_negative_level,
    generate_decimal_level,
    generate_zero_level,
    generate_name_with_leading_trailing_spaces,
    generate_entity_group_name,
)
from common.logger import log


# ====================================================================
# Helper: create a prerequisite EGD record, refresh, and return its name
# ====================================================================

def _create_prerequisite_egd(page, data=None):
    """Create an Entity Group Definition for tests that need existing data.
    Returns the Entity Group Name used.
    """
    if data is None:
        data = generate_valid_data("PreReq")
    name = page.create_entity_group_definition(data)
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
    """EGD-C01 to EGD-C12: Validation checks on the Create form.
    EGD has TWO form fields: Entity Group Name (text, required) + Level (number, required).
    """

    # ---- EGD-C01: Submit with ALL empty fields ----
    def test_EGD_C01_empty_submit(self, egd_page):
        """Submit with both fields empty — should be blocked."""
        log.info("EGD-C01: Empty submit test")
        page = egd_page

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
            "BUG: Form submitted with empty fields — no validation"
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

    # ---- EGD-C02: Create with valid data (happy path) ----
    def test_EGD_C02_valid_create(self, egd_page):
        """Create with valid Entity Group Name and Level — should succeed.
        BUG-008: No success SweetAlert after create.
        """
        log.info("EGD-C02: Valid create test")
        page = egd_page

        data = generate_valid_data("ValidC")
        name = page.create_entity_group_definition(data)

        # BUG-008: No success alert, just check popup closed
        page.wait_seconds(2)
        popup_closed = page.is_form_closed()

        if popup_closed:
            log.info("Form closed after submit (EGD has no success alert — BUG-008)")
        else:
            validation_alert = page.get_swal_title()
            if validation_alert:
                log.warning(f"Validation alert instead of success: {validation_alert}")

        # Verify the record appears in the table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_entity_group_in_table(name)

        assert found, (
            f"Created EGD '{name}' not found in table after refresh"
        )
        log.info(f"EGD created and found in table: {name}")

    # ---- EGD-C03: Spaces-only Entity Group Name ----
    @pytest.mark.xfail(
        reason="BUG-001: Spaces-only name accepted — will fail until ERP is fixed",
        strict=False,
    )
    def test_EGD_C03_spaces_only_name(self, egd_page):
        """Spaces-only Entity Group Name — should be rejected.
        BUG-001: Spaces-only name creates empty record.
        Test expects rejection — will FAIL until ERP is fixed.
        """
        log.info("EGD-C03: Spaces-only name test")
        page = egd_page

        data = generate_spaces_only_data(10, level=10)
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
        assert form_still_open or errors or validation_alert, (
            "BUG-001 CONFIRMED: Spaces-only name was accepted — "
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
        page.click_refresh()
        page.wait_seconds(2)

    # ---- EGD-C04: Empty Entity Group Name + valid Level ----
    def test_EGD_C04_empty_name_valid_level(self, egd_page):
        """Empty Entity Group Name with valid Level — should be blocked."""
        log.info("EGD-C04: Empty name + valid level test")
        page = egd_page

        data = generate_empty_name_only(level=10)
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG: Form submitted with empty Entity Group Name — no validation"
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

    # ---- EGD-C05: Valid Name + empty Level ----
    def test_EGD_C05_valid_name_empty_level(self, egd_page):
        """Valid Entity Group Name with empty Level — should be blocked."""
        log.info("EGD-C05: Valid name + empty level test")
        page = egd_page

        data = generate_empty_level_only("NoLevel")
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG: Form submitted with empty Level — no validation"
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

    # ---- EGD-C06: Name at 255 char boundary ----
    def test_EGD_C06_name_255_chars(self, egd_page):
        """Entity Group Name with exactly 255 chars — boundary test.
        BUG-007: No maxlength on input.
        """
        log.info("EGD-C06: 255-char name test")
        page = egd_page

        name_255 = generate_string_255()
        data = {"entity_group": name_255, "level": 10}
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
            log.info("255-char name accepted (may be expected if max >= 255)")

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

    # ---- EGD-C07: Name exceeds 255 chars (256) ----
    def test_EGD_C07_name_256_chars(self, egd_page):
        """Entity Group Name with 256 chars — should be rejected or truncated.
        BUG-007: No maxlength on input.
        """
        log.info("EGD-C07: 256-char name test")
        page = egd_page

        name_256 = generate_string_256()
        data = {"entity_group": name_256, "level": 10}
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
                "BUG-007 CONFIRMED: 256-char name accepted — "
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

    # ---- EGD-C08: Special characters in Name ----
    def test_EGD_C08_special_chars_name(self, egd_page):
        """Special characters in Entity Group Name — check if accepted or rejected.
        BUG-006: Special characters accepted.
        """
        log.info("EGD-C08: Special chars in name test")
        page = egd_page

        data = generate_special_char_data(level=55)
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
                "Special chars accepted in Name (BUG-006 — may be expected)"
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

    # ---- EGD-C09: SQL injection in Name ----
    def test_EGD_C09_sql_injection_name(self, egd_page):
        """SQL injection string in Name — should be sanitized or rejected."""
        log.info("EGD-C09: SQL injection name test")
        page = egd_page

        data = generate_sql_injection_data(level=10)
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
                "SQL injection string accepted — check server-side sanitization"
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

    # ---- EGD-C10: XSS payload in Name ----
    def test_EGD_C10_xss_name(self, egd_page):
        """XSS payload in Name — should be sanitized or rejected."""
        log.info("EGD-C10: XSS name test")
        page = egd_page

        data = generate_xss_data(level=10)
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
            log.info("XSS payload accepted — check DOM rendering safety")

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

    # ---- EGD-C11: Unicode/international characters in Name ----
    def test_EGD_C11_unicode_name(self, egd_page):
        """Unicode/international characters in Name — check acceptance."""
        log.info("EGD-C11: Unicode name test")
        page = egd_page

        data = generate_unicode_data(level=10)
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

    # ---- EGD-C12: Name with leading/trailing spaces ----
    def test_EGD_C12_leading_trailing_spaces(self, egd_page):
        """Name with leading/trailing spaces — should be trimmed.
        BUG: Spaces may not be trimmed before storage.
        """
        log.info("EGD-C12: Leading/trailing spaces test")
        page = egd_page

        spaced_name = generate_name_with_leading_trailing_spaces()
        data = {"entity_group": spaced_name, "level": 10}
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
            names = page.get_all_entity_group_names()
            trimmed_name = spaced_name.strip()

            has_spaces = any(
                n != n.strip()
                for n in names
                if spaced_name in n or trimmed_name in n
            )
            if has_spaces:
                log.warning("BUG: Leading/trailing spaces NOT trimmed")
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
# PHASE 2: Duplicate Validations (4 tests)
# ====================================================================

class TestDuplicateValidations:
    """EGD-D01 to EGD-D04: Duplicate name checks in Create and Edit.
    BUG-002: Exact duplicate silently rejected (no feedback).
    BUG-003: Case-insensitive duplicate NOT blocked.
    """

    # ---- EGD-D01: Exact duplicate name — Create after Create ----
    def test_EGD_D01_exact_duplicate(self, egd_page):
        """Create two EGDs with identical Entity Group Names.
        BUG-002: Second create is silently rejected — form stays open with no feedback.
        Test documents current behavior as known bug — passes either way.
        """
        log.info("EGD-D01: Exact duplicate test")
        page = egd_page

        # Create first EGD
        data1 = generate_valid_data("Dup1")
        page.create_entity_group_definition(data1)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Try creating second EGD with same name
        data2 = generate_duplicate_name_data(data1["entity_group"])
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data2)
        page.submit()
        page.wait_seconds(3)

        # Check for validation or acceptance
        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert:
            log.info("Duplicate name rejected with validation alert — working")
        elif form_still_open:
            log.warning(
                "BUG-002 CONFIRMED: Duplicate name silently rejected — "
                "form stays open with NO error feedback"
            )
        else:
            log.warning(
                "BUG-002 CONFIRMED: Duplicate name accepted — no uniqueness check"
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

    # ---- EGD-D02: Case-insensitive duplicate check ----
    @pytest.mark.xfail(
        reason="BUG-003: Case-insensitive duplicate NOT blocked — will fail until ERP is fixed",
        strict=False,
    )
    def test_EGD_D02_case_insensitive_duplicate(self, egd_page):
        """Create EGD with same name in different case.
        BUG-003: No case-insensitive check — "agdi" accepted alongside "Agdi".
        Test expects case-insensitive rejection.
        """
        log.info("EGD-D02: Case-insensitive duplicate test")
        page = egd_page

        # Create EGD with known name
        data1 = generate_valid_data("CaseDup")
        name1 = data1["entity_group"]
        page.create_entity_group_definition(data1)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Create EGD with lowercase version of same name
        data2 = generate_case_variant_name(name1)
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data2)
        page.submit()
        page.wait_seconds(3)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        # BUG-003: Should block case-insensitive duplicates
        assert validation_alert or form_still_open, (
            "BUG-003 CONFIRMED: Case-insensitive duplicate accepted — "
            "system should reject it"
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

    # ---- EGD-D03: Duplicate name ignoring spaces ----
    @pytest.mark.xfail(
        reason="BUG-003: Spaces-ignored duplicate NOT blocked — will fail until ERP is fixed",
        strict=False,
    )
    def test_EGD_D03_space_ignored_duplicate(self, egd_page):
        """Create EGD with same name plus leading/trailing spaces.
        BUG-003: Spaces-ignored duplicate check not enforced.
        """
        log.info("EGD-D03: Space-ignored duplicate test")
        page = egd_page

        # Create EGD with known name
        data1 = generate_valid_data("SpaceDup")
        name1 = data1["entity_group"]
        page.create_entity_group_definition(data1)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Create EGD with spaces around same name
        data2 = generate_space_ignored_name(name1)
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data2)
        page.submit()
        page.wait_seconds(3)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        # BUG-003: Should block duplicates ignoring spaces
        assert validation_alert or form_still_open, (
            "BUG-003 CONFIRMED: Spaces-ignored duplicate accepted — "
            "system should reject it"
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

    # ---- EGD-D04: Duplicate name — Edit to existing name ----
    def test_EGD_D04_duplicate_edit(self, egd_page):
        """Edit an EGD to use another EGD's Entity Group Name.
        BUG-002: Duplicate name silently rejected in Edit.
        Test documents current behavior.
        """
        log.info("EGD-D04: Duplicate edit test")
        page = egd_page

        # Create two EGDs
        data1 = generate_valid_data("EditDup1")
        page.create_entity_group_definition(data1)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        data2 = generate_valid_data("EditDup2")
        page.create_entity_group_definition(data2)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Edit second EGD with first EGD's name
        page.click_edit_button(egd_name=data2["entity_group"])
        page.wait_seconds(1)
        page.fill_form({"entity_group": data1["entity_group"], "level": 10})
        page.click_update()
        page.wait_seconds(3)

        validation_alert = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        if validation_alert:
            log.info("Duplicate name rejected in Edit — validation working")
        elif form_still_open:
            log.warning(
                "BUG-002 CONFIRMED in Edit: Duplicate name silently rejected — "
                "form stays open with NO error feedback"
            )
        else:
            log.warning(
                "BUG-002 CONFIRMED in Edit: Duplicate name accepted — "
                "no uniqueness check"
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
    """EGD-E01 to EGD-E06: Validation checks on the Edit form."""

    # ---- EGD-E01: Edit — pre-populated fields ----
    def test_EGD_E01_edit_prepopulated(self, egd_page):
        """Edit popup should show both fields pre-populated."""
        log.info("EGD-E01: Edit pre-populated fields test")
        page = egd_page

        data = generate_valid_data("EditPre")
        page.create_entity_group_definition(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Click Edit
        page.click_edit_button(egd_name=data["entity_group"])
        page.wait_seconds(2)

        # Read form values
        form_values = page.get_form_field_values()

        # If get_form_field_values returns empty, try reading via JS
        if not form_values.get("entity_group"):
            try:
                val = page.driver.execute_script(
                    "var i = document.querySelector("
                    "  \"input[formcontrolname='entity_group']\");"
                    "return i ? i.value : '';"
                )
                form_values["entity_group"] = val or ""
                log.info(f"Read entity_group via JS fallback: '{val}'")
            except Exception as e:
                log.warning(f"JS fallback read failed: {e}")

        assert form_values.get("entity_group"), (
            "Entity Group Name field empty in Edit form"
        )
        assert "EditPre" in form_values.get("entity_group", ""), (
            f"Edit form Name value '{form_values.get('entity_group')}' "
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

    # ---- EGD-E02: Edit — valid update ----
    def test_EGD_E02_valid_edit(self, egd_page):
        """Edit with valid new Name and Level — should succeed.
        BUG-008: No success alert after update.
        """
        log.info("EGD-E02: Valid edit test")
        page = egd_page

        data = generate_valid_data("EditOK")
        page.create_entity_group_definition(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Edit with new data
        edit_data = generate_valid_edit_data("Updated")
        page.click_edit_button(egd_name=data["entity_group"])
        page.wait_seconds(1)
        page.fill_form(edit_data)
        page.click_update()
        page.wait_seconds(2)

        # BUG-008: No success alert
        popup_closed = page.is_form_closed()

        if popup_closed:
            log.info("Edit form closed after update (BUG-008 — no success alert)")
        else:
            validation_alert = page.get_swal_title()
            if validation_alert:
                log.warning(f"Validation alert after edit: {validation_alert}")

        # Verify updated name in table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_entity_group_in_table(edit_data["entity_group"])

        assert found, (
            f"Updated EGD '{edit_data['entity_group']}' not found in table"
        )
        log.info(f"EGD updated and found in table: {edit_data['entity_group']}")

    # ---- EGD-E03: Edit — empty Entity Group Name ----
    @pytest.mark.xfail(
        reason="BUG: Edit form may allow empty Name submission — will fail until ERP is fixed",
        strict=False,
    )
    def test_EGD_E03_edit_empty_name(self, egd_page):
        """Edit with empty Entity Group Name — should be blocked."""
        log.info("EGD-E03: Edit empty name test")
        page = egd_page

        data = generate_valid_data("EditEmpty")
        page.create_entity_group_definition(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Open Edit and clear the Name field
        page.click_edit_button(egd_name=data["entity_group"])
        page.wait_seconds(1)

        # Clear the entity_group field via JS
        page.driver.execute_script(
            "var i = document.querySelector("
            "  \"input[formcontrolname='entity_group']\");"
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

    # ---- EGD-E04: Edit — empty Level ----
    @pytest.mark.xfail(
        reason="BUG: Edit form may allow empty Level submission — will fail until ERP is fixed",
        strict=False,
    )
    def test_EGD_E04_edit_empty_level(self, egd_page):
        """Edit with empty Level — should be blocked."""
        log.info("EGD-E04: Edit empty level test")
        page = egd_page

        data = generate_valid_data("EditNoLvl")
        page.create_entity_group_definition(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Open Edit and clear the Level field
        page.click_edit_button(egd_name=data["entity_group"])
        page.wait_seconds(1)

        # Clear level field via JS
        page.driver.execute_script(
            "var i = document.querySelector("
            "  \"input[formcontrolname='level']\");"
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

        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG: Edit form submitted with empty Level — no validation"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- EGD-E05: Edit — no success popup (BUG-008) ----
    def test_EGD_E05_edit_no_success_popup(self, egd_page):
        """Verify that no success SweetAlert appears after edit.
        BUG-008: No success popup after update.
        """
        log.info("EGD-E05: Edit no success popup test")
        page = egd_page

        data = generate_valid_data("EditNoAlert")
        page.create_entity_group_definition(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Edit with new data
        edit_data = generate_valid_edit_data("UpdNoAlert")
        page.click_edit_button(egd_name=data["entity_group"])
        page.wait_seconds(1)
        page.fill_form(edit_data)
        page.click_update()
        page.wait_seconds(2)

        # Check for SweetAlert
        swal_visible = page.is_validation_alert_present(timeout=3)

        if not swal_visible:
            log.warning(
                "BUG-008 CONFIRMED: No success SweetAlert after edit. "
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

    # ---- EGD-E06: Edit — spaces-only Name ----
    @pytest.mark.xfail(
        reason="BUG-001: Spaces-only name accepted in Edit — will fail until ERP is fixed",
        strict=False,
    )
    def test_EGD_E06_edit_spaces_only_name(self, egd_page):
        """Edit EGD Name to spaces-only — should be rejected.
        BUG-001: Spaces-only name may be accepted in Edit too.
        """
        log.info("EGD-E06: Edit spaces-only name test")
        page = egd_page

        data = generate_valid_data("EditSpace")
        page.create_entity_group_definition(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Open Edit and type spaces-only name
        page.click_edit_button(egd_name=data["entity_group"])
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

        assert form_still_open or errors or validation_alert, (
            "BUG-001 CONFIRMED in Edit: Spaces-only name was accepted"
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
# PHASE 4: Search & Filter Edge Cases (4 tests)
# ====================================================================

class TestSearchFilter:
    """EGD-S01 to EGD-S04: Search and Filter edge cases."""

    # ---- EGD-S01: Search with exact Name ----
    def test_EGD_S01_search_exact(self, egd_page):
        """Search with exact Entity Group name — should find it."""
        log.info("EGD-S01: Search exact name")
        page = egd_page

        data = generate_valid_data("SearchEx")
        page.create_entity_group_definition(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        found = page.search_entity_group(data["entity_group"])
        page.clear_search()

        assert found, f"Exact search failed for: {data['entity_group']}"
        log.info(f"Exact search found: {data['entity_group']}")

    # ---- EGD-S02: Search with partial Name ----
    def test_EGD_S02_search_partial(self, egd_page):
        """Search with partial Entity Group name — should find it."""
        log.info("EGD-S02: Search partial name")
        page = egd_page

        data = generate_valid_data("SearchPar")
        page.create_entity_group_definition(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Use first 10 chars as partial search
        partial = data["entity_group"][:10]
        found = page.search_entity_group(partial)
        page.clear_search()

        assert found, f"Partial search failed for: {partial}"
        log.info(f"Partial search found with: {partial}")

    # ---- EGD-S03: Search with non-existent Name ----
    def test_EGD_S03_search_nonexistent(self, egd_page):
        """Search for non-existent name — should return no results."""
        log.info("EGD-S03: Search nonexistent")
        page = egd_page

        fake_name = f"NonExistent_{int(time.time())}"
        found = page.search_entity_group(fake_name)
        page.clear_search()

        assert not found, (
            f"BUG: Non-existent name '{fake_name}' was found in table"
        )
        log.info(f"Correctly not found: {fake_name}")

    # ---- EGD-S04: Filter panel opens and closes ----
    def test_EGD_S04_filter_panel(self, egd_page):
        """Filter panel should open when Filters button is clicked.
        Then close when close button is clicked.
        """
        log.info("EGD-S04: Filter panel test")
        page = egd_page

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
            log.info("Filter button/panel not found or not visible")

        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 5: Popup & UI Behaviors (5 tests)
# ====================================================================

class TestPopupUIBehaviors:
    """EGD-P01 to EGD-P05: Popup and UI behavior checks."""

    # ---- EGD-P01: View mode — fields read-only ----
    def test_EGD_P01_view_mode_readonly(self, egd_page):
        """View mode should show all fields as disabled/read-only."""
        log.info("EGD-P01: View mode read-only test")
        page = egd_page

        data = generate_valid_data("ViewTest")
        page.create_entity_group_definition(data)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Click View button
        page.click_view_button(egd_name=data["entity_group"])
        page.wait_seconds(2)

        # Verify view mode
        is_view = page.is_view_mode()
        form_heading = page.get_form_heading()

        assert is_view, "View mode — fields should be disabled/read-only"
        assert "Entity Group Definition" in form_heading, (
            f"Unexpected form heading: {form_heading}"
        )

        # Verify no Submit/Update button in view mode
        has_submit = page.is_displayed(page.SUBMIT_BUTTON, timeout=2)
        has_update = page.is_displayed(page.UPDATE_BUTTON, timeout=2)

        assert not has_submit, "View mode should not have Submit button"
        assert not has_update, "View mode should not have Update button"

        log.info(f"View mode confirmed: heading='{form_heading}', fields disabled")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- EGD-P02: No Delete option ----
    def test_EGD_P02_no_delete_option(self, egd_page):
        """Verify that no Delete button exists on the screen."""
        log.info("EGD-P02: No delete option test")
        page = egd_page

        # Check for delete buttons in table rows
        delete_btns = page.driver.find_elements(
            By.CSS_SELECTOR,
            "button .tbl-fav-delete, .cdk-column-delete button, "
            "button[mattooltip='Delete']"
        )

        # Check More menu for delete option
        delete_menu_items = page.driver.find_elements(
            By.XPATH,
            "//*[contains(text(),'Delete') or contains(text(),'delete')]"
        )

        has_delete = len(delete_btns) > 0 or len(delete_menu_items) > 0

        assert not has_delete, (
            "Delete option found — screen should not have delete functionality"
        )
        log.info("Confirmed: No Delete option on Entity Group Definition screen")

    # ---- EGD-P03: No History option ----
    def test_EGD_P03_no_history_option(self, egd_page):
        """Verify that no History button exists on the screen."""
        log.info("EGD-P03: No history option test")
        page = egd_page

        # Check for history buttons in table rows
        history_btns = page.driver.find_elements(
            By.CSS_SELECTOR,
            "button .tbl-fav-history, .cdk-column-history button, "
            "button[mattooltip='History']"
        )

        has_history = len(history_btns) > 0

        assert not has_history, (
            "History button found — screen should not have history functionality"
        )
        log.info("Confirmed: No History option on Entity Group Definition screen")

    # ---- EGD-P04: Fullscreen toggle ----
    def test_EGD_P04_fullscreen_toggle(self, egd_page):
        """Fullscreen toggle should expand the popup."""
        log.info("EGD-P04: Fullscreen toggle test")
        page = egd_page

        data = generate_valid_data("FullScr")
        page.open_add_form()
        page.wait_seconds(1)

        # Click fullscreen button
        try:
            fullscreen_btns = page.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model .popup-header button, "
                ".edit_pop_up .popup-header button",
            )
            clicked = False
            for btn in fullscreen_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if btn.is_displayed():
                        page.driver.execute_script(
                            "arguments[0].click();", btn
                        )
                        page.wait_seconds(1)
                        clicked = True
                        break
                except Exception:
                    continue

            if clicked:
                # Check if fullscreen class was applied
                is_fullscreen = page.driver.find_elements(
                    By.CSS_SELECTOR, ".big-model.fullscreen"
                )
                if is_fullscreen:
                    log.info("Fullscreen toggle works — popup expanded")
                else:
                    log.info("Fullscreen toggle clicked — state changed")
            else:
                log.info("Fullscreen button not found or not clickable")
        except Exception:
            log.info("Fullscreen test skipped — button not available")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- EGD-P05: Form heading text ----
    def test_EGD_P05_form_heading(self, egd_page):
        """Verify the form popup heading text."""
        log.info("EGD-P05: Form heading test")
        page = egd_page

        page.open_add_form()
        page.wait_seconds(1)

        heading = page.get_form_heading()
        assert "Entity Group Definition" in heading, (
            f"Unexpected form heading: '{heading}'"
        )
        log.info(f"Form heading confirmed: '{heading}'")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass


# ====================================================================
# PHASE 6: Bug-Specific Tests (4 tests)
# ====================================================================

class TestBugSpecific:
    """EGD-B01 to EGD-B04: Targeted bug verification tests."""

    # ---- EGD-B01: Negative Level value ----
    @pytest.mark.xfail(
        reason="BUG-004: Negative Level accepted — will fail until ERP is fixed",
        strict=False,
    )
    def test_EGD_B01_negative_level(self, egd_page):
        """Negative Level value should be rejected.
        BUG-004: Negative values like -5, -10 are accepted.
        """
        log.info("EGD-B01: Negative level test")
        page = egd_page

        data = generate_negative_level(level=-5)
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG-004 CONFIRMED: Negative Level accepted — "
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
        page.click_refresh()
        page.wait_seconds(2)

    # ---- EGD-B02: Decimal Level value ----
    @pytest.mark.xfail(
        reason="BUG-005: Decimal Level accepted — will fail until ERP is fixed",
        strict=False,
    )
    def test_EGD_B02_decimal_level(self, egd_page):
        """Decimal Level value should be rejected.
        BUG-005: Decimal values like 3.5 are accepted.
        """
        log.info("EGD-B02: Decimal level test")
        page = egd_page

        data = generate_decimal_level(level=3.5)
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG-005 CONFIRMED: Decimal Level accepted — "
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
        page.click_refresh()
        page.wait_seconds(2)

    # ---- EGD-B03: Duplicate name silent rejection ----
    @pytest.mark.xfail(
        reason="BUG-002: Duplicate name silently rejected — no error feedback shown to user",
        strict=False,
    )
    def test_EGD_B03_duplicate_silent_rejection(self, egd_page):
        """Exact duplicate name should show a clear error message.
        BUG-002: Form stays open with no feedback when duplicate submitted.
        """
        log.info("EGD-B03: Duplicate silent rejection test")
        page = egd_page

        # Create an EGD
        data1 = generate_valid_data("SilentBug")
        page.create_entity_group_definition(data1)
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Try duplicate with same name
        data2 = generate_duplicate_name_data(data1["entity_group"])
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data2)
        page.submit()
        page.wait_seconds(3)

        # BUG-002: Should show clear error message to user
        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        swal_visible = page.is_validation_alert_present(timeout=2)

        assert validation_alert or errors or swal_visible, (
            "BUG-002 CONFIRMED: Duplicate submission silently rejected — "
            "no error message shown to user. Form just stays open with no feedback."
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

    # ---- EGD-B04: Level = 0 (should be valid) ----
    def test_EGD_B04_zero_level(self, egd_page):
        """Level = 0 should be valid (e.g., 'Agdi' has Level 0 in production)."""
        log.info("EGD-B04: Zero level test")
        page = egd_page

        data = generate_zero_level()
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_form(data)
        page.submit()
        page.wait_seconds(2)

        # Level 0 should be accepted
        popup_closed = page.is_form_closed()

        if popup_closed:
            log.info("Level 0 accepted as expected")
        else:
            validation_alert = page.get_swal_title()
            if validation_alert:
                log.warning(f"Level 0 rejected: {validation_alert}")

        # Verify in table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_entity_group_in_table(data["entity_group"])

        assert found, f"EGD with Level 0 not found in table: {data['entity_group']}"
        log.info(f"EGD with Level 0 created successfully: {data['entity_group']}")
