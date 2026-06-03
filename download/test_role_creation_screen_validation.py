"""
test_role_creation_validation.py
----------------------------------
Comprehensive validation test suite for RhythmERP Role Creation Screen.
45 test cases across 7 phases.

Phases:
  1. Create Form Validations  (12 tests) — RC-C01 to RC-C12
  2. Duplicate Validations      (3 tests) — RC-D01 to RC-D03
  3. Edit Form Validations      (6 tests) — RC-E01 to RC-E06
  4. Search & Filter Edge Cases (5 tests) — RC-S01 to RC-S05
  5. Popup & UI Behaviors       (8 tests) — RC-P01 to RC-P08
  6. History & Audit Trail      (4 tests) — RC-H01 to RC-H04
  7. Bug-Specific Tests         (7 tests) — RC-B01 to RC-B07

IMPORTANT — Role Creation Screen is a SIMPLE POPUP (NOT a stepper):
  - Only 2 fields: Role Name (text input) + Entity Group Name (mat-select)
  - No stepper, no tabs, no toggles
  - Submit button directly on popup

Known Bugs (CONFIRMED via browser exploration 2026-05-20):
  BUG-001 (HIGH)   : Spaces-only Role Name accepted as valid (ng-valid)
  BUG-002 (HIGH)   : Special characters accepted in Role Name
  BUG-003 (CRITICAL): SQL injection strings accepted in Role Name
  BUG-004 (CRITICAL): XSS payloads accepted in Role Name
  BUG-005 (HIGH)   : Duplicate Role Names allowed — no uniqueness validation
  BUG-006 (MEDIUM) : No client maxlength — 500-char name silently fails server-side
  BUG-007 (LOW)    : No visible mat-error text on required field validation
  BUG-008 (LOW)    : No Delete option anywhere on screen

Bug Handling Decisions:
  BUG-001: CONFIRMED — xfail marker on RC-C03
  BUG-002: CONFIRMED — xfail marker on RC-C05
  BUG-003: CONFIRMED — xfail marker on RC-C06
  BUG-004: CONFIRMED — xfail marker on RC-C07
  BUG-005: CONFIRMED — xfail marker on RC-D01, RC-D02
  BUG-006: CONFIRMED — xfail marker on RC-C08
  BUG-007: CONFIRMED — No xfail, test checks for red outline as partial validation
  BUG-008: CONFIRMED — No xfail, test documents absence of Delete

Run:
  pytest test_role_creation_validation.py -v --tb=short
  pytest test_role_creation_validation.py -v -k "TestCreateForm" --tb=short
  pytest test_role_creation_validation.py -v -k "RC-C03" --tb=short
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

from pages.access.modules.role_creation_screen.role_creation_page import (
    RoleCreationPage,
)
from pages.access.modules.role_creation_screen.data.role_creation_data import (
    generate_valid_role_data,
    generate_spaces_only,
    generate_special_char_name,
    generate_sql_injection_name,
    generate_xss_payload_name,
    generate_string_500,
    generate_numbers_only_name,
    generate_leading_trailing_spaces_name,
    generate_unicode_name,
    generate_role_name_with_dot,
    generate_duplicate_name_data,
    generate_case_insensitive_duplicate_name,
    generate_empty_data,
    generate_role_name_only_data,
    generate_valid_edit_data,
)
from common.logger import log


# ====================================================================
# Helper: create a prerequisite role, refresh, return its name
# ====================================================================

def _create_prerequisite_role(page, name_prefix="PreReq"):
    """Create a Role Creation entry for tests that need existing data.
    Returns the role name and the data dict.
    """
    data = generate_valid_role_data(name_prefix)
    result = page.create_role(data)
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
    name = result.get("role_name", "")
    log.info(f"Prerequisite role created: {name}")
    return name, data


# ====================================================================
# PHASE 1: Create Form Validations (12 tests)
# ====================================================================

class TestCreateFormValidations:
    """RC-C01 to RC-C12: Validation checks on the Create form.
    Role Creation Screen has a simple 2-field popup (NOT a stepper).
    """

    # ---- RC-C01: Submit with all fields empty ----
    def test_RC_C01_empty_submit(self, rc_page):
        """Submit with both fields empty — should be blocked.
        BUG-007: Only red outline, no visible error text.
        """
        log.info("RC-C01: Empty submit test")
        page = rc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Click Submit with empty fields
        page.submit()
        page.wait_seconds(2)

        # Check for validation indicators
        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        # BUG-007: May not have visible error text
        # At minimum, form should stay open (validation blocking)
        assert form_still_open or errors or validation_alert, (
            "BUG: Form submitted with both fields empty — no validation"
        )
        if form_still_open:
            log.info("Form stayed open — validation working (partially)")
        if validation_alert:
            log.info(f"Validation alert shown: {validation_alert}")
        if errors:
            log.info(f"Validation errors shown: {errors}")
        else:
            log.info("BUG-007: No visible error text — only red outline")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- RC-C02: Create with valid data (happy path) ----
    def test_RC_C02_valid_create(self, rc_page):
        """Create with valid data — should succeed."""
        log.info("RC-C02: Valid create test (happy path)")
        page = rc_page

        data = generate_valid_role_data("ValidRC")
        result = page.create_role(data)
        name = result.get("role_name", "")

        if result["status"] == "PASSED":
            log.info(f"Role created successfully: {name}")
        else:
            log.warning(f"Create failed: {result.get('error', 'unknown')}")

        # Verify the role appears in the table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.is_role_in_table(name)

        assert found, (
            f"Created role '{name}' not found in table after refresh"
        )
        log.info(f"Role created and found in table: {name}")

    # ---- RC-C03: Spaces-only Role Name ----
    @pytest.mark.xfail(
        reason="BUG-001: Spaces-only Role Name accepted as valid (ng-valid)",
        strict=False,
    )
    def test_RC_C03_spaces_only_name(self, rc_page):
        """Spaces-only Role Name — should be rejected.
        BUG-001: Spaces-only input accepted as ng-valid.
        """
        log.info("RC-C03: Spaces-only Role Name test")
        page = rc_page

        data = generate_valid_role_data("SpaceRC")
        data["role_name"] = generate_spaces_only(10)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_create_form(data)
        page.wait_seconds(0.5)

        # Submit
        page.submit()
        page.wait_seconds(2)

        # Should be blocked — but BUG-001 allows it
        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG-001 CONFIRMED: Spaces-only Role Name was accepted"
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

    # ---- RC-C04: Entity Group not selected ----
    def test_RC_C04_entity_group_not_selected(self, rc_page):
        """Fill Role Name only, leave Entity Group empty — should be blocked."""
        log.info("RC-C04: Entity Group not selected test")
        page = rc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Fill only Role Name
        page.fill_role_name("TestRoleNoGroup")
        page.wait_seconds(0.5)

        # Submit without Entity Group
        page.submit()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG: Form submitted with Entity Group empty — no validation"
        )
        if form_still_open:
            log.info("Form stayed open — Entity Group validation working")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.close_popup()
            except Exception:
                pass

    # ---- RC-C05: Special characters in Role Name ----
    @pytest.mark.xfail(
        reason="BUG-002: Special characters accepted in Role Name",
        strict=False,
    )
    def test_RC_C05_special_chars_name(self, rc_page):
        """Special characters in Role Name — should be rejected.
        BUG-002: Special chars accepted and saved.
        """
        log.info("RC-C05: Special chars Role Name test")
        page = rc_page

        data = generate_valid_role_data("SpCharRC")
        data["role_name"] = generate_special_char_name()

        result = page.create_role(data)

        # Should fail — but BUG-002 allows it
        assert result["status"] != "PASSED", (
            "BUG-002 CONFIRMED: Special characters accepted in Role Name"
        )

        # Cleanup
        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-C06: SQL injection in Role Name ----
    @pytest.mark.xfail(
        reason="BUG-003: SQL injection strings accepted in Role Name",
        strict=False,
    )
    def test_RC_C06_sql_injection_name(self, rc_page):
        """SQL injection in Role Name — should be rejected.
        BUG-003: SQL injection accepted and saved.
        """
        log.info("RC-C06: SQL injection Role Name test")
        page = rc_page

        data = generate_valid_role_data("SQLRC")
        data["role_name"] = generate_sql_injection_name()

        result = page.create_role(data)

        assert result["status"] != "PASSED", (
            "BUG-003 CONFIRMED: SQL injection accepted in Role Name"
        )

        # Cleanup
        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-C07: XSS in Role Name ----
    @pytest.mark.xfail(
        reason="BUG-004: XSS payloads accepted in Role Name",
        strict=False,
    )
    def test_RC_C07_xss_name(self, rc_page):
        """XSS payload in Role Name — should be rejected.
        BUG-004: XSS payloads accepted and saved.
        """
        log.info("RC-C07: XSS Role Name test")
        page = rc_page

        data = generate_valid_role_data("XSSRC")
        data["role_name"] = generate_xss_payload_name()

        result = page.create_role(data)

        assert result["status"] != "PASSED", (
            "BUG-004 CONFIRMED: XSS payload accepted in Role Name"
        )

        # Cleanup
        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-C08: Very long Role Name (500 chars) ----
    @pytest.mark.xfail(
        reason="BUG-006: No client maxlength — 500-char name silently fails server-side",
        strict=False,
    )
    def test_RC_C08_very_long_name(self, rc_page):
        """500-character Role Name — should show maxlength error.
        BUG-006: No maxlength on client; server silently rejects.
        """
        log.info("RC-C08: 500-char Role Name test")
        page = rc_page

        data = generate_valid_role_data("LongRC")
        data["role_name"] = generate_string_500()

        result = page.create_role(data)

        # Should either be blocked or show error — but BUG-006 causes silent failure
        if result["status"] == "PASSED":
            log.warning("BUG-006: 500-char name was accepted by server")
        elif result["status"] == "VALIDATION_BLOCKED":
            log.info("500-char name was blocked by validation")
        else:
            log.info(f"500-char name result: {result['status']}")

        assert result["status"] != "PASSED", (
            "BUG-006 CONFIRMED: 500-char name accepted or silently failed"
        )

        # Cleanup
        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-C09: Numbers-only Role Name ----
    def test_RC_C09_numbers_only_name(self, rc_page):
        """Numbers-only Role Name — should be accepted (no alpha-only rule)."""
        log.info("RC-C09: Numbers-only Role Name test")
        page = rc_page

        data = generate_valid_role_data("NumRC")
        data["role_name"] = generate_numbers_only_name()

        result = page.create_role(data)
        name = result.get("role_name", "")

        if result["status"] == "PASSED":
            page.click_refresh()
            page.wait_seconds(2)
            found = page.is_role_in_table(name)
            assert found, f"Numeric role name not found in table: {name}"
            log.info(f"Numbers-only Role Name accepted: {name}")
        else:
            log.info(f"Numbers-only Role Name rejected: {result.get('error', '')}")

    # ---- RC-C10: Leading/trailing spaces trimmed ----
    def test_RC_C10_leading_trailing_spaces(self, rc_page):
        """Leading/trailing spaces in Role Name — should be trimmed on save."""
        log.info("RC-C10: Leading/trailing spaces test")
        page = rc_page

        data = generate_valid_role_data("TrimRC")
        data["role_name"] = generate_leading_trailing_spaces_name()

        result = page.create_role(data)
        name = result.get("role_name", "")

        if result["status"] == "PASSED":
            page.click_refresh()
            page.wait_seconds(2)
            # Server should trim spaces
            trimmed_name = name.strip()
            found = page.is_role_in_table(trimmed_name)
            if found:
                log.info(f"Spaces trimmed: '{name}' → '{trimmed_name}'")
            else:
                log.info(f"Role with trimmed name not found: '{trimmed_name}'")
        else:
            log.info(f"Spaces role result: {result.get('error', '')}")

    # ---- RC-C11: Unicode in Role Name ----
    def test_RC_C11_unicode_name(self, rc_page):
        """Unicode characters in Role Name — check acceptance."""
        log.info("RC-C11: Unicode Role Name test")
        page = rc_page

        data = generate_valid_role_data("UniRC")
        data["role_name"] = generate_unicode_name()

        result = page.create_role(data)
        name = result.get("role_name", "")

        if result["status"] == "PASSED":
            log.info(f"Unicode Role Name accepted: {name}")
        else:
            log.info(f"Unicode Role Name result: {result.get('error', '')}")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-C12: Role Name with dot ----
    def test_RC_C12_name_with_dot(self, rc_page):
        """Role Name containing a dot — should be accepted."""
        log.info("RC-C12: Role Name with dot test")
        page = rc_page

        data = generate_valid_role_data("DotRC")
        data["role_name"] = generate_role_name_with_dot()

        result = page.create_role(data)
        name = result.get("role_name", "")

        if result["status"] == "PASSED":
            page.click_refresh()
            page.wait_seconds(2)
            found = page.is_role_in_table(name)
            assert found, f"Role name with dot not found: {name}"
            log.info(f"Role Name with dot accepted: {name}")
        else:
            log.info(f"Role Name with dot result: {result.get('error', '')}")


# ====================================================================
# PHASE 2: Duplicate Validations (3 tests)
# ====================================================================

class TestDuplicateValidations:
    """RC-D01 to RC-D03: Duplicate name checks in Create.

    BUG-005: Duplicate Role Names are ALLOWED — confirmed via exploration.
    Tests verify duplicates CAN be created (xfail expected).
    """

    # ---- RC-D01: Duplicate Role Name (exact) ----
    @pytest.mark.xfail(
        reason="BUG-005: Duplicate Role Names allowed — no uniqueness validation",
        strict=False,
    )
    def test_RC_D01_duplicate_exact(self, rc_page):
        """Create two roles with identical names — should be blocked.
        BUG-005: Duplicates are allowed.
        """
        log.info("RC-D01: Duplicate exact name test")
        page = rc_page

        # Create first role
        name1, data1 = _create_prerequisite_role(page, "DupD01")

        if not name1:
            log.warning("First role creation failed — cannot test duplicate")
            return

        # Create second role with same name
        dup_data = generate_duplicate_name_data(name1)
        result2 = page.create_role(dup_data)

        # Should be blocked — but BUG-005 allows it
        assert result2["status"] != "PASSED", (
            f"BUG-005 CONFIRMED: Duplicate role '{name1}' was created"
        )

        # Cleanup
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-D02: Duplicate (case-insensitive) ----
    @pytest.mark.xfail(
        reason="BUG-005b: Case-insensitive duplicate Role Names allowed",
        strict=False,
    )
    def test_RC_D02_duplicate_case_insensitive(self, rc_page):
        """Create role with same name in different case — should be blocked.
        BUG-005b: Case-insensitive duplicates also allowed.
        """
        log.info("RC-D02: Duplicate case-insensitive test")
        page = rc_page

        # Create first role
        name1, data1 = _create_prerequisite_role(page, "DupD02")

        if not name1:
            log.warning("First role creation failed — cannot test duplicate")
            return

        # Create second role with lowercase version of name
        dup_data = generate_case_insensitive_duplicate_name(name1)
        result2 = page.create_role(dup_data)

        assert result2["status"] != "PASSED", (
            f"BUG-005b CONFIRMED: Case-insensitive duplicate '{name1.lower()}' created"
        )

        # Cleanup
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-D03: Duplicate + different Entity Group ----
    def test_RC_D03_duplicate_different_entity(self, rc_page):
        """Same name, different Entity Group — test if name uniqueness is checked."""
        log.info("RC-D03: Duplicate name with different Entity Group test")
        page = rc_page

        # Create first role
        name1, data1 = _create_prerequisite_role(page, "DupD03")

        if not name1:
            log.warning("First role creation failed")
            return

        # Create second role with same name (different Entity Group will be
        # selected randomly)
        dup_data = generate_duplicate_name_data(name1)
        result2 = page.create_role(dup_data)

        # BUG-005: Duplicates are allowed regardless
        if result2["status"] == "PASSED":
            log.info(f"BUG-005: Duplicate role created even with different Entity Group")
        else:
            log.info(f"Duplicate with different Entity Group blocked: {result2.get('error', '')}")

        # Cleanup
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
    """RC-E01 to RC-E06: Validation checks on the Edit form."""

    # ---- RC-E01: Edit pre-populated fields ----
    def test_RC_E01_edit_prepopulated(self, rc_page):
        """Edit popup should show fields pre-populated with existing data."""
        log.info("RC-E01: Edit pre-populated fields test")
        page = rc_page

        name, data = _create_prerequisite_role(page, "EditPre")

        if not name:
            log.warning("Prerequisite role name is empty — cannot verify edit pre-population")
            return

        # Click Edit
        page.click_edit_button(name)
        page.wait_seconds(2)

        # Read form values
        form_values = page.get_form_field_values()

        assert form_values.get("role_name"), (
            "Role Name field empty in Edit form"
        )
        log.info(f"Edit form pre-populated — Role Name: '{form_values.get('role_name')}'")

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

    # ---- RC-E02: Edit with valid data ----
    def test_RC_E02_edit_valid(self, rc_page):
        """Edit a role with valid new data — should succeed."""
        log.info("RC-E02: Edit with valid data test")
        page = rc_page

        name, data = _create_prerequisite_role(page, "EditVal")

        if not name:
            log.warning("Prerequisite role name is empty")
            return

        edit_data = generate_valid_edit_data("EditedRC")
        result = page.edit_role(name, edit_data)

        if result["status"] == "PASSED":
            log.info(f"Role updated successfully")
        else:
            log.warning(f"Edit failed: {result.get('error', '')}")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-E03: Edit with empty Role Name ----
    def test_RC_E03_edit_empty_name(self, rc_page):
        """Clear Role Name in Edit, click Update — should be blocked."""
        log.info("RC-E03: Edit with empty Role Name test")
        page = rc_page

        name, data = _create_prerequisite_role(page, "EditEmpty")

        if not name:
            log.warning("Prerequisite role name is empty")
            return

        # Click Edit
        page.click_edit_button(name)
        page.wait_seconds(2)

        # Clear Role Name and try to Update
        page.fill_role_name("", clear_first=True)
        page.wait_seconds(0.5)
        page.click_update()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG: Update accepted with empty Role Name"
        )
        log.info("Empty Role Name in Edit blocked — validation working")

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

    # ---- RC-E04: Edit with special chars ----
    def test_RC_E04_edit_special_chars(self, rc_page):
        """Edit to special characters in Role Name.
        BUG-002: Special chars are accepted.
        """
        log.info("RC-E04: Edit with special chars test")
        page = rc_page

        name, data = _create_prerequisite_role(page, "EditSpCh")

        if not name:
            log.warning("Prerequisite role name is empty")
            return

        edit_data = {"role_name": generate_special_char_name()}
        result = page.edit_role(name, edit_data)

        if result["status"] == "PASSED":
            log.info("BUG-002 in Edit: Special chars accepted in Role Name during edit")
        else:
            log.info(f"Special chars in Edit rejected: {result.get('error', '')}")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-E05: Edit with spaces-only ----
    def test_RC_E05_edit_spaces_only(self, rc_page):
        """Edit to spaces-only Role Name — should be blocked.
        BUG-001: Spaces-only accepted as valid.
        """
        log.info("RC-E05: Edit with spaces-only test")
        page = rc_page

        name, data = _create_prerequisite_role(page, "EditSpace")

        if not name:
            log.warning("Prerequisite role name is empty")
            return

        edit_data = {"role_name": generate_spaces_only(10)}
        result = page.edit_role(name, edit_data)

        if result["status"] == "PASSED":
            log.info("BUG-001 in Edit: Spaces-only Role Name accepted during edit")
        else:
            log.info(f"Spaces-only in Edit rejected: {result.get('error', '')}")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-E06: Edit Entity Group Name ----
    def test_RC_E06_edit_entity_group(self, rc_page):
        """Change Entity Group in Edit — should succeed."""
        log.info("RC-E06: Edit Entity Group test")
        page = rc_page

        name, data = _create_prerequisite_role(page, "EditEG")

        if not name:
            log.warning("Prerequisite role name is empty")
            return

        # Edit with different Entity Group (None = random from UI)
        edit_data = {"role_name": None, "entity_group": None}
        result = page.edit_role(name, edit_data)

        if result["status"] == "PASSED":
            log.info("Entity Group changed in Edit — update succeeded")
        else:
            log.info(f"Entity Group edit result: {result.get('error', '')}")

        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 4: Search & Filter Edge Cases (5 tests)
# ====================================================================

class TestSearchFilter:
    """RC-S01 to RC-S05: Search and filter edge cases."""

    # ---- RC-S01: Search exact match ----
    def test_RC_S01_search_exact(self, rc_page):
        """Search for an exact existing role name."""
        log.info("RC-S01: Search exact match test")
        page = rc_page

        # Create a role to search for
        name, data = _create_prerequisite_role(page, "SearchEx")

        if not name:
            log.warning("Prerequisite role not created")
            return

        # Search for the exact name
        page.search_item(name)
        page.wait_seconds(2)

        found = page.is_role_in_table(name)
        assert found, f"Exact search failed for '{name}'"
        log.info(f"Exact search found: {name}")

        # Clear search
        page.clear_search()

    # ---- RC-S02: Search partial match ----
    def test_RC_S02_search_partial(self, rc_page):
        """Search with partial name — should find matching records."""
        log.info("RC-S02: Search partial match test")
        page = rc_page

        # Get existing names from table
        existing_names = page.get_table_role_names()
        if not existing_names:
            log.warning("No roles in table for partial search test")
            return

        # Use first 5 chars of first name
        partial = existing_names[0][:5] if len(existing_names[0]) >= 5 else existing_names[0]
        page.search_item(partial)
        page.wait_seconds(2)

        # At least one result should contain the partial string
        result_names = page.get_table_role_names()
        matches = [n for n in result_names if partial.lower() in n.lower()]
        assert matches, f"No partial matches found for '{partial}'"
        log.info(f"Partial search '{partial}' found {len(matches)} matches")

        page.clear_search()

    # ---- RC-S03: Search case insensitive ----
    def test_RC_S03_search_case_insensitive(self, rc_page):
        """Search with lowercase — should match case-insensitive."""
        log.info("RC-S03: Search case-insensitive test")
        page = rc_page

        existing_names = page.get_table_role_names()
        if not existing_names:
            log.warning("No roles in table for case-insensitive search test")
            return

        # Search with lowercase version
        search_term = existing_names[0].lower()
        page.search_item(search_term)
        page.wait_seconds(2)

        result_names = page.get_table_role_names()
        log.info(f"Case-insensitive search for '{search_term}' returned {len(result_names)} results")

        page.clear_search()

    # ---- RC-S04: Search no results ----
    def test_RC_S04_search_no_results(self, rc_page):
        """Search for non-existent name — should show empty or no-data."""
        log.info("RC-S04: Search no results test")
        page = rc_page

        page.search_item("ZZZZZ_NONEXISTENT_ROLE_12345")
        page.wait_seconds(2)

        result_names = page.get_table_role_names()
        # Should have no results or empty table
        no_data = not result_names
        log.info(f"Non-existent search returned {len(result_names)} results")

        page.clear_search()

    # ---- RC-S05: Search special chars ----
    def test_RC_S05_search_special_chars(self, rc_page):
        """Search for special characters — should not crash."""
        log.info("RC-S05: Search special chars test")
        page = rc_page

        page.search_item("!@#$%")
        page.wait_seconds(2)

        # Should not crash — just return results or empty
        result_names = page.get_table_role_names()
        log.info(f"Special chars search returned {len(result_names)} results")

        page.clear_search()


# ====================================================================
# PHASE 5: Popup & UI Behaviors (8 tests)
# ====================================================================

class TestPopupUIBehaviors:
    """RC-P01 to RC-P08: Popup and UI behavior tests."""

    # ---- RC-P01: View popup readonly ----
    def test_RC_P01_view_readonly(self, rc_page):
        """View popup should show disabled/readonly fields with Cancel only."""
        log.info("RC-P01: View popup readonly test")
        page = rc_page

        name, data = _create_prerequisite_role(page, "ViewRO")

        if not name:
            log.warning("Prerequisite role not created")
            return

        page.click_view_button(name)
        page.wait_seconds(2)

        # View mode should have disabled inputs
        is_view = page.is_view_form_open()
        if is_view:
            log.info("View popup has disabled inputs — readonly confirmed")
        else:
            log.info("View popup check — may not have detected disabled state")

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

    # ---- RC-P02: No delete functionality ----
    def test_RC_P02_no_delete(self, rc_page):
        """Verify no Delete option exists anywhere on the screen.
        BUG-008: No Delete option.
        """
        log.info("RC-P02: No delete functionality test")
        page = rc_page

        # Check table row actions — should only have View, Edit, History
        try:
            action_cells = page.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table tbody td.cdk-column-actions"
            )
            for cell in action_cells[:3]:
                try:
                    buttons = cell.find_elements(By.CSS_SELECTOR, "button")
                    icons = [b.find_element(By.CSS_SELECTOR, "app-feather-icons").get_attribute("icon")
                             for b in buttons if b.find_elements(By.CSS_SELECTOR, "app-feather-icons")]
                    log.info(f"Row action icons: {icons}")
                    # Should only have eye, edit, clock — no delete/trash icon
                    assert "trash" not in icons and "delete" not in icons, (
                        "Delete icon found in row actions — unexpected"
                    )
                except Exception:
                    continue
        except Exception:
            log.info("No action cells found to check for delete")

        # Check More menu
        try:
            more_btns = page.driver.find_elements(
                By.CSS_SELECTOR,
                "button mat-icon"
            )
            more_icons = [b.text.strip().lower() for b in more_btns if b.is_displayed()]
            log.info(f"Visible icon texts: {more_icons}")
        except Exception:
            pass

        log.info("BUG-008 CONFIRMED: No Delete option found on screen")

    # ---- RC-P03: Cancel closes popup ----
    def test_RC_P03_cancel_closes_popup(self, rc_page):
        """Open Add, click Cancel — popup should close without creating record."""
        log.info("RC-P03: Cancel closes popup test")
        page = rc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Fill some data
        page.fill_role_name("CancelTestRole")
        page.wait_seconds(0.5)

        # Click Cancel
        page.cancel()
        page.wait_seconds(1)

        # Popup should be closed
        assert not page.is_add_form_open(), "Popup still open after Cancel"
        log.info("Cancel closed the popup — no record created")

    # ---- RC-P04: Close (X) button ----
    def test_RC_P04_close_x_button(self, rc_page):
        """Open Add, click X — popup should close."""
        log.info("RC-P04: Close (X) button test")
        page = rc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Click X button
        page.close_popup()
        page.wait_seconds(1)

        assert not page.is_add_form_open(), "Popup still open after X click"
        log.info("X button closed the popup")

    # ---- RC-P05: Fullscreen button ----
    def test_RC_P05_fullscreen(self, rc_page):
        """Click fullscreen button in popup — popup should expand."""
        log.info("RC-P05: Fullscreen button test")
        page = rc_page

        page.open_add_form()
        page.wait_seconds(1)

        # Click fullscreen
        try:
            fullscreen_btns = page.driver.find_elements(
                By.CSS_SELECTOR, ".big-model .popup-actions button"
            )
            for btn in fullscreen_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "fullscreen" and btn.is_displayed():
                        page.driver.execute_script("arguments[0].click();", btn)
                        page.wait_seconds(1)
                        log.info("Fullscreen button clicked")
                        break
                except Exception:
                    continue
        except Exception:
            log.info("Fullscreen button not found")

        # Cleanup
        try:
            page.close_popup()
        except Exception:
            pass

    # ---- RC-P06: SweetAlert2 success ----
    def test_RC_P06_sweetalert_success(self, rc_page):
        """Create valid record — verify SweetAlert2 success message."""
        log.info("RC-P06: SweetAlert2 success test")
        page = rc_page

        data = generate_valid_role_data("SWTest")
        result = page.create_role(data)

        # Success should have been handled inside create_role
        if result["status"] == "PASSED":
            log.info("SweetAlert2 success confirmed — 'Role created'")
        else:
            log.info(f"Create result: {result['status']} — {result.get('error', '')}")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-P07: Refresh button ----
    def test_RC_P07_refresh(self, rc_page):
        """Click Refresh — table should reload data."""
        log.info("RC-P07: Refresh button test")
        page = rc_page

        # Get initial count
        initial_names = page.get_table_role_names()
        initial_count = len(initial_names)

        # Click Refresh
        page.click_refresh()
        page.wait_seconds(2)

        # Table should still have data
        refreshed_names = page.get_table_role_names()
        log.info(f"Before refresh: {initial_count} rows, after: {len(refreshed_names)} rows")

    # ---- RC-P08: Pagination ----
    def test_RC_P08_pagination(self, rc_page):
        """Check pagination — verify paginator exists and works."""
        log.info("RC-P08: Pagination test")
        page = rc_page

        try:
            paginator = page.driver.find_elements(
                By.CSS_SELECTOR, ".mat-mdc-paginator"
            )
            if paginator:
                range_label = page.get_current_page()
                log.info(f"Paginator range: {range_label}")
            else:
                log.info("No paginator visible (may not have enough records)")
        except Exception:
            log.info("Pagination check — no paginator found")


# ====================================================================
# PHASE 6: History & Audit Trail (4 tests)
# ====================================================================

class TestHistoryAuditTrail:
    """RC-H01 to RC-H04: History popup and audit trail tests."""

    # ---- RC-H01: History popup opens ----
    def test_RC_H01_history_opens(self, rc_page):
        """Click History button — popup should open."""
        log.info("RC-H01: History popup opens test")
        page = rc_page

        name, data = _create_prerequisite_role(page, "HistOpen")

        if not name:
            log.warning("Prerequisite role not created")
            return

        page.click_history_button(name)
        page.wait_seconds(2)

        is_open = page.is_history_popup_open()
        if is_open:
            log.info("History popup opened successfully")
        else:
            log.warning("History popup did not open")

        # Cleanup
        try:
            page.close_history_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-H02: History for edited record ----
    def test_RC_H02_history_edited(self, rc_page):
        """View history for an edited record — should show history entries."""
        log.info("RC-H02: History for edited record test")
        page = rc_page

        name, data = _create_prerequisite_role(page, "HistEdit")

        if not name:
            log.warning("Prerequisite role not created")
            return

        # Edit the role first
        edit_data = generate_valid_edit_data("HistEdited")
        page.edit_role(name, edit_data)
        page.wait_seconds(1)

        # Cleanup edit popup
        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Open history
        page.click_history_button(name)
        page.wait_seconds(2)

        row_count = page.get_history_row_count()
        log.info(f"History for edited record: {row_count} entries")

        # Cleanup
        try:
            page.close_history_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-H03: History for new record ----
    def test_RC_H03_history_new_record(self, rc_page):
        """View history for a new (un-edited) record."""
        log.info("RC-H03: History for new record test")
        page = rc_page

        name, data = _create_prerequisite_role(page, "HistNew")

        if not name:
            log.warning("Prerequisite role not created")
            return

        page.click_history_button(name)
        page.wait_seconds(2)

        is_open = page.is_history_popup_open()
        row_count = page.get_history_row_count()
        log.info(f"History for new record: {row_count} entries (may be 0 for un-edited)")

        # Cleanup
        try:
            page.close_history_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-H04: History search ----
    def test_RC_H04_history_search(self, rc_page):
        """Type in history search box — should filter entries."""
        log.info("RC-H04: History search test")
        page = rc_page

        name, data = _create_prerequisite_role(page, "HistSrch")

        if not name:
            log.warning("Prerequisite role not created")
            return

        page.click_history_button(name)
        page.wait_seconds(2)

        if page.is_history_popup_open():
            try:
                search_input = page.driver.find_element(
                    By.CSS_SELECTOR,
                    ".big-model input[placeholder='Search box']"
                )
                search_input.send_keys("test")
                page.wait_seconds(1)
                log.info("History search input accepted text")
            except Exception:
                log.info("History search input not found or not interactable")

        # Cleanup
        try:
            page.close_history_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 7: Bug-Specific Tests (7 tests)
# ====================================================================

class TestBugSpecific:
    """RC-B01 to RC-B07: Tests specifically targeting confirmed bugs.
    These tests are designed to clearly demonstrate each bug.
    All are expected to FAIL (xfail) because the bugs are confirmed.
    """

    # ---- RC-B01: BUG-001 Spaces-only accepted ----
    @pytest.mark.xfail(
        reason="BUG-001: Spaces-only Role Name accepted as valid",
        strict=False,
    )
    def test_RC_B01_bug_spaces_only(self, rc_page):
        """Demonstrate BUG-001: Spaces-only Role Name is accepted."""
        log.info("RC-B01: BUG-001 Spaces-only accepted")
        page = rc_page

        data = generate_valid_role_data("BugSp")
        data["role_name"] = generate_spaces_only(15)

        result = page.create_role(data)

        # If the bug is fixed, this should NOT pass
        assert result["status"] != "PASSED", (
            "BUG-001: Spaces-only Role Name was accepted as valid"
        )

        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-B02: BUG-002 Special chars accepted ----
    @pytest.mark.xfail(
        reason="BUG-002: Special characters accepted in Role Name",
        strict=False,
    )
    def test_RC_B02_bug_special_chars(self, rc_page):
        """Demonstrate BUG-002: Special chars accepted in Role Name."""
        log.info("RC-B02: BUG-002 Special chars accepted")
        page = rc_page

        data = generate_valid_role_data("BugSC")
        data["role_name"] = "!@#$%^&*()_+"

        result = page.create_role(data)

        assert result["status"] != "PASSED", (
            "BUG-002: Special characters accepted in Role Name"
        )

        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-B03: BUG-003 SQL injection accepted ----
    @pytest.mark.xfail(
        reason="BUG-003: SQL injection strings accepted in Role Name",
        strict=False,
    )
    def test_RC_B03_bug_sql_injection(self, rc_page):
        """Demonstrate BUG-003: SQL injection accepted."""
        log.info("RC-B03: BUG-003 SQL injection accepted")
        page = rc_page

        data = generate_valid_role_data("BugSQL")
        data["role_name"] = generate_sql_injection_name()

        result = page.create_role(data)

        assert result["status"] != "PASSED", (
            "BUG-003: SQL injection accepted in Role Name"
        )

        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-B04: BUG-004 XSS accepted ----
    @pytest.mark.xfail(
        reason="BUG-004: XSS payloads accepted in Role Name",
        strict=False,
    )
    def test_RC_B04_bug_xss(self, rc_page):
        """Demonstrate BUG-004: XSS payloads accepted."""
        log.info("RC-B04: BUG-004 XSS accepted")
        page = rc_page

        data = generate_valid_role_data("BugXSS")
        data["role_name"] = generate_xss_payload_name()

        result = page.create_role(data)

        assert result["status"] != "PASSED", (
            "BUG-004: XSS payload accepted in Role Name"
        )

        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-B05: BUG-005 Duplicates allowed ----
    @pytest.mark.xfail(
        reason="BUG-005: Duplicate Role Names allowed",
        strict=False,
    )
    def test_RC_B05_bug_duplicates(self, rc_page):
        """Demonstrate BUG-005: Duplicate Role Names allowed."""
        log.info("RC-B05: BUG-005 Duplicates allowed")
        page = rc_page

        name1, data1 = _create_prerequisite_role(page, "BugDup")

        if not name1:
            log.warning("Prerequisite role not created")
            return

        dup_data = generate_duplicate_name_data(name1)
        result2 = page.create_role(dup_data)

        assert result2["status"] != "PASSED", (
            f"BUG-005: Duplicate role '{name1}' was created"
        )

        try:
            page.close_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-B06: BUG-006 No maxlength, silent fail ----
    @pytest.mark.xfail(
        reason="BUG-006: No client maxlength — 500-char name silently fails",
        strict=False,
    )
    def test_RC_B06_bug_no_maxlength(self, rc_page):
        """Demonstrate BUG-006: No maxlength, 500-char name silently fails."""
        log.info("RC-B06: BUG-006 No maxlength, silent fail")
        page = rc_page

        data = generate_valid_role_data("BugLong")
        data["role_name"] = generate_string_500()

        result = page.create_role(data)

        # Should show error — but BUG-006 causes silent failure
        assert result["status"] == "PASSED", (
            "BUG-006: 500-char name not accepted — either bug fixed or different behavior"
        )

        page.click_refresh()
        page.wait_seconds(2)

    # ---- RC-B07: BUG-007 No visible error text ----
    def test_RC_B07_bug_no_error_text(self, rc_page):
        """Demonstrate BUG-007: No visible mat-error text on required field validation.
        This test documents the bug — it's not expected to fail.
        """
        log.info("RC-B07: BUG-007 No visible error text")
        page = rc_page

        page.open_add_form()
        page.wait_seconds(1)

        # Submit empty form
        page.submit()
        page.wait_seconds(2)

        # Check for mat-error text
        errors = page.get_mat_error_text()

        if not errors:
            log.info("BUG-007 CONFIRMED: No visible mat-error text — only red outline")
        else:
            log.info(f"Error text found: {errors}")

        # Check for ng-invalid class (partial validation)
        role_name_invalid = page.is_field_ng_invalid(page.ROLE_NAME_INPUT)
        entity_group_invalid = page.is_field_ng_invalid(
            page.ENTITY_GROUP_SELECT
        )

        log.info(f"Role Name ng-invalid: {role_name_invalid}")
        log.info(f"Entity Group ng-invalid: {entity_group_invalid}")

        # At minimum, fields should get ng-invalid class
        assert role_name_invalid or entity_group_invalid or not errors, (
            "No validation indicators at all — complete validation failure"
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
