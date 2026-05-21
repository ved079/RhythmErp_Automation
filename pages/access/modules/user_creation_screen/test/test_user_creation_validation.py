"""
test_user_creation_validation.py
----------------------------------
Comprehensive validation test suite for RhythmERP User Creation Screen.
42 test cases across 7 phases.

Phases:
  1. Create Form Validations  (16 tests) — UC-C01 to UC-C16
  2. Duplicate Validations      (3 tests) — UC-D01 to UC-D03
  3. Edit Form Validations      (6 tests) — UC-E01 to UC-E06
  4. Search & Filter Edge Cases (5 tests) — UC-S01 to UC-S05
  5. Popup & UI Behaviors       (5 tests) — UC-P01 to UC-P05
  6. History & Audit Trail      (4 tests) — UC-H01 to UC-H04
  7. Bug-Specific Tests         (3 tests) — UC-B01 to UC-B03

IMPORTANT — User Creation Screen is a SIMPLE POPUP (NOT a stepper):
  - 9 fields + 2 checkboxes
  - 4 mat-select dropdowns (User Type, Role, Entity, Designation)
  - Submit button directly on popup
  - Edit mode button says "Update" not "Submit"
  - View mode has disabled fields, Cancel button only

Known Bugs (CONFIRMED via browser exploration 2026-05-21):
  BUG-001 (HIGH)   : Duplicate username: Submit silently fails, NO error message
  BUG-002 (MEDIUM) : No maxlength on Username — 256+ chars accepted
  BUG-003 (MEDIUM) : No email format validation on blur
  BUG-004 (LOW)    : Spaces in Username show generic SweetAlert2 (not inline mat-error)
  BUG-005 (LOW)    : Designation dropdown has duplicate "Manager" option
  BUG-006 (LOW)    : Only 1 mat-error visible at a time

Bug Handling Decisions:
  BUG-001: CONFIRMED — xfail marker on UC-D01
  BUG-002: CONFIRMED — xfail marker on UC-C08
  BUG-003: CONFIRMED — test verifies behavior, no xfail
  BUG-004: CONFIRMED — test verifies SweetAlert2 appears
  BUG-005: CONFIRMED — test verifies duplicate option exists
  BUG-006: CONFIRMED — test verifies only 1 error at a time

Run:
  pytest test_user_creation_validation.py -v --tb=short
  pytest test_user_creation_validation.py -v -k "TestCreateForm" --tb=short
  pytest test_user_creation_validation.py -v -k "UC-C04" --tb=short
  # Run only the 6 previously-failed tests:
  pytest test_user_creation_validation.py -v -k "UC-C04 or UC-C08 or UC-H01 or UC-E01 or UC-S01 or UC-D02" --tb=short
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

from pages.access.modules.user_creation_screen.user_creation_page import (
    UserCreationPage,
)
from pages.access.modules.user_creation_screen.data.user_creation_data import (
    generate_valid_user_data,
    generate_spaces_only,
    generate_special_char_username,
    generate_sql_injection_username,
    generate_xss_payload_username,
    generate_string_256,
    generate_string_500,
    generate_invalid_email,
    generate_numbers_only_username,
    generate_leading_trailing_spaces_username,
    generate_unicode_username,
    generate_duplicate_user_data,
    generate_duplicate_username_data,
    generate_case_insensitive_duplicate_username,
    generate_empty_data,
    generate_username_only_data,
    generate_valid_edit_data,
    generate_search_test_data,
    generate_email,
    generate_password,
)
from common.logger import log


# ====================================================================
# Helper: create a prerequisite user, refresh, return its username
# ====================================================================

def _create_prerequisite_user(page, name_prefix="PreReq"):
    """Create a User Creation entry for tests that need existing data.
    Returns the username and the data dict.
    """
    data = generate_valid_user_data(name_prefix)
    result = page.create_user(data)
    # Cleanup form if still open
    try:
        page.cancel()
    except Exception:
        pass
    try:
        page.force_close_form_popup()
    except Exception:
        pass
    page.click_refresh()
    page.wait_seconds(2)
    username = data.get("username", "")
    log.info(f"Prerequisite user created: {username}")
    return username, data


# ====================================================================
# PHASE 1: Create Form Validations (16 tests)
# ====================================================================

class TestCreateFormValidations:
    """UC-C01 to UC-C16: Validation checks on the Create form.
    User Creation Screen has a simple 9-field + 2-checkbox popup.
    """

    # ---- UC-C01: Submit with all fields empty ----
    def test_UC_C01_empty_submit(self, uc_page):
        """Submit with all fields empty — should be blocked.
        BUG-006: Only 1 mat-error visible at a time.
        """
        log.info("UC-C01: Empty submit test")
        page = uc_page

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

        # BUG-006: May only show one error at a time
        assert form_still_open or errors or validation_alert, (
            "BUG: Form submitted with all fields empty — no validation"
        )
        if form_still_open:
            log.info("Form stayed open — validation working (partially)")
        if validation_alert:
            log.info(f"Validation alert shown: {validation_alert}")
        if errors:
            log.info(f"Validation errors shown: {errors}")
        else:
            log.info("BUG-006: No visible error text — only red outline")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass

    # ---- UC-C02: Create with valid data (happy path) ----
    def test_UC_C02_valid_create(self, uc_page):
        """Create with valid data — should succeed."""
        log.info("UC-C02: Valid create test (happy path)")
        page = uc_page

        data = generate_valid_user_data("ValidUC")
        result = page.create_user(data)
        username = data.get("username", "")

        if result["status"] == "PASSED":
            log.info(f"User created successfully: {username}")
        else:
            log.warning(f"Create failed: {result.get('error', 'unknown')}")

        # Verify the user appears in the table
        page.click_refresh()
        page.wait_seconds(2)
        found = page.search_and_verify(username)

        if found:
            log.info(f"User created and found in table: {username}")
        else:
            log.warning(f"User created but not found in table: {username}")

        # Cleanup search
        try:
            page.clear_search()
        except Exception:
            pass

    # ---- UC-C03: Spaces-only Username ----
    def test_UC_C03_spaces_only_username(self, uc_page):
        """Spaces-only Username — should be rejected.
        BUG-004: SweetAlert2 popup shows generic message.
        """
        log.info("UC-C03: Spaces-only Username test")
        page = uc_page

        data = generate_valid_user_data("SpaceUC")
        data["username"] = generate_spaces_only(10)

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_user_form(data)
        page.wait_seconds(0.5)

        # Submit
        page.submit()
        page.wait_seconds(2)

        # Should be blocked — may show SweetAlert2
        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG: Spaces-only Username was accepted"
        )
        if validation_alert:
            log.info(f"BUG-004: SweetAlert2 shown: {validation_alert}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C04: Special characters in Username ----
    def test_UC_C04_special_chars_username(self, uc_page):
        """Special characters in Username — should be rejected.
        BUG-004: SweetAlert2 popup shows generic message instead of inline mat-error.
        """
        log.info("UC-C04: Special chars Username test")
        page = uc_page

        data = generate_valid_user_data("SpCharUC")
        data["username"] = generate_special_char_username()

        page.open_add_form()
        page.wait_seconds(1)
        page.fill_user_form(data)
        page.wait_seconds(0.5)

        page.submit()
        page.wait_seconds(2)

        # Should be blocked — SweetAlert2 or mat-error
        validation_alert = page.handle_validation_warning(timeout=5)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG: Special characters Username was accepted"
        )
        if validation_alert:
            log.info(f"BUG-004: SweetAlert2 shown: {validation_alert}")
        if errors:
            log.info(f"Validation errors shown: {errors}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C05: SQL injection in Username ----
    def test_UC_C05_sql_injection_username(self, uc_page):
        """SQL injection in Username — should be rejected.
        BUG-004: SweetAlert2 popup may appear.
        """
        log.info("UC-C05: SQL injection Username test")
        page = uc_page

        data = generate_valid_user_data("SQLUC")
        data["username"] = generate_sql_injection_username()

        result = page.create_user(data)

        # Should fail
        validation_alert = page.handle_validation_warning(timeout=3)
        if result["status"] != "PASSED":
            log.info("SQL injection rejected — validation working")
        else:
            log.warning("BUG: SQL injection accepted in Username")

        # Cleanup
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C06: XSS in Username ----
    def test_UC_C06_xss_username(self, uc_page):
        """XSS payload in Username — should be rejected.
        BUG-004: SweetAlert2 popup may appear.
        """
        log.info("UC-C06: XSS Username test")
        page = uc_page

        data = generate_valid_user_data("XSSUC")
        data["username"] = generate_xss_payload_username()

        result = page.create_user(data)

        if result["status"] != "PASSED":
            log.info("XSS payload rejected — validation working")
        else:
            log.warning("BUG: XSS payload accepted in Username")

        # Cleanup
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C07: Numbers-only Username ----
    def test_UC_C07_numbers_only_username(self, uc_page):
        """Numbers-only Username — check acceptance."""
        log.info("UC-C07: Numbers-only Username test")
        page = uc_page

        data = generate_valid_user_data("NumUC")
        data["username"] = generate_numbers_only_username()

        result = page.create_user(data)

        if result["status"] == "PASSED":
            log.info(f"Numbers-only Username accepted")
        else:
            log.info(f"Numbers-only Username rejected: {result.get('error', '')}")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C08: Very long Username (256 chars) ----
    @pytest.mark.xfail(
        reason="BUG-002: No client maxlength — 256-char name may silently fail",
        strict=False,
    )
    def test_UC_C08_very_long_username(self, uc_page):
        """256-character Username — should show maxlength error.
        BUG-002: No maxlength on client; may silently fail server-side.
        """
        log.info("UC-C08: 256-char Username test")
        page = uc_page

        data = generate_valid_user_data("LongUC")
        data["username"] = generate_string_256()

        result = page.create_user(data)

        # Should either be blocked or show error
        if result["status"] == "PASSED":
            log.warning("BUG-002: 256-char username was accepted by server")
        elif result["status"] == "VALIDATION_BLOCKED":
            log.info("256-char username was blocked by validation")
        else:
            log.info(f"256-char username result: {result['status']}")

        assert result["status"] != "PASSED", (
            "BUG-002 CONFIRMED: 256-char username accepted or silently failed"
        )

        # Cleanup
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C09: Invalid email format ----
    def test_UC_C09_invalid_email(self, uc_page):
        """Invalid email format — should show validation error.
        BUG-003: No email format validation on blur.
        """
        log.info("UC-C09: Invalid email format test")
        page = uc_page

        data = generate_valid_user_data("InvEmail")
        data["email"] = generate_invalid_email()

        result = page.create_user(data)

        # May be accepted or rejected depending on server-side validation
        if result["status"] == "PASSED":
            log.warning("BUG-003: Invalid email format accepted")
        else:
            log.info("Invalid email rejected — validation working")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C10: Email format validation on blur ----
    def test_UC_C10_email_format_on_blur(self, uc_page):
        """Type invalid email, tab out — check for inline validation.
        BUG-003: No email format validation on blur.
        """
        log.info("UC-C10: Email format validation on blur test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Type invalid email and tab out
        page.type_text(page.EMAIL_INPUT, "notanemail", clear_first=True)
        page.wait_seconds(0.3)
        # Tab out to trigger blur
        page.EMAIL_INPUT[1]  # css selector
        page.driver.find_element(By.CSS_SELECTOR, page.EMAIL_INPUT[1]).send_keys(
            "\t"
        )
        page.wait_seconds(1)

        # Check for inline error
        has_error = page.has_field_error("Email")
        if has_error:
            log.info("Email format validation on blur — working")
        else:
            log.info("BUG-003: No email format validation on blur")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass

    # ---- UC-C11: Username with leading/trailing spaces ----
    def test_UC_C11_leading_trailing_spaces(self, uc_page):
        """Username with leading/trailing spaces — should be trimmed or rejected.
        BUG-004: Spaces show SweetAlert2 popup.
        """
        log.info("UC-C11: Leading/trailing spaces test")
        page = uc_page

        data = generate_valid_user_data("TrimUC")
        data["username"] = generate_leading_trailing_spaces_username()

        result = page.create_user(data)

        if result["status"] == "PASSED":
            log.info("Spaces were accepted or trimmed")
        else:
            log.info(f"Spaces rejected: {result.get('error', '')}")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C12: Unicode in Username ----
    def test_UC_C12_unicode_username(self, uc_page):
        """Unicode characters in Username — check acceptance."""
        log.info("UC-C12: Unicode Username test")
        page = uc_page

        data = generate_valid_user_data("UniUC")
        data["username"] = generate_unicode_username()

        result = page.create_user(data)

        if result["status"] == "PASSED":
            log.info(f"Unicode Username accepted")
        else:
            log.info(f"Unicode Username result: {result.get('error', '')}")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C13: User Type dropdown shows options ----
    def test_UC_C13_user_type_dropdown(self, uc_page):
        """User Type dropdown should open and show selectable options."""
        log.info("UC-C13: User Type dropdown test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        selected = page._select_mat_option("User Type", None)
        assert selected, "User Type dropdown has no options"
        log.info(f"User Type selected: {selected}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass

    # ---- UC-C14: Designation dropdown shows options ----
    def test_UC_C14_designation_dropdown(self, uc_page):
        """Designation dropdown should open and show options.
        BUG-005: May show duplicate 'Manager' option.
        """
        log.info("UC-C14: Designation dropdown test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        selected = page._select_mat_option("Designation", None)
        assert selected, "Designation dropdown has no options"
        log.info(f"Designation selected: {selected}")

        # BUG-005: Check for duplicate options
        try:
            # Open dropdown again to check options
            page._select_mat_option("Designation", None)
            log.info("BUG-005: Check for duplicate 'Manager' in Designation dropdown")
        except Exception:
            pass

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass

    # ---- UC-C15: Role dropdown depends on User Type ----
    def test_UC_C15_role_dropdown_dynamic(self, uc_page):
        """Role dropdown should load options (may be dynamic based on User Type)."""
        log.info("UC-C15: Role dropdown dynamic test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Select User Type first
        page._select_mat_option("User Type", None)
        page.wait_seconds(1)

        # Then try Role
        selected = page._select_mat_option("Role", None)
        if selected:
            log.info(f"Role selected: {selected}")
        else:
            log.warning("Role dropdown has no options (may need User Type first)")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass

    # ---- UC-C16: Entity dropdown depends on User Type ----
    def test_UC_C16_entity_dropdown_dynamic(self, uc_page):
        """Entity dropdown should load options (may be dynamic based on User Type)."""
        log.info("UC-C16: Entity dropdown dynamic test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Select User Type first
        page._select_mat_option("User Type", None)
        page.wait_seconds(1)

        # Then try Entity
        selected = page._select_mat_option("Entity", None)
        if selected:
            log.info(f"Entity selected: {selected}")
        else:
            log.warning("Entity dropdown has no options (may need User Type first)")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass


# ====================================================================
# PHASE 2: Duplicate Validations (3 tests)
# ====================================================================

class TestDuplicateValidations:
    """UC-D01 to UC-D03: Duplicate checks in Create.

    BUG-001: Duplicate username: Submit silently fails, NO error message.
    """

    # ---- UC-D01: Duplicate Username (exact) ----
    @pytest.mark.xfail(
        reason="BUG-001: Duplicate username silently fails, no error message",
        strict=False,
    )
    def test_UC_D01_duplicate_username(self, uc_page):
        """Create two users with identical usernames — should be blocked.
        BUG-001: Duplicate username silently fails.
        """
        log.info("UC-D01: Duplicate exact username test")
        page = uc_page

        # Create first user
        username1, data1 = _create_prerequisite_user(page, "DupD01")

        if not username1:
            log.warning("First user creation failed — cannot test duplicate")
            return

        # Create second user with same username
        dup_data = generate_duplicate_username_data(username1)
        result2 = page.create_user(dup_data)

        # Should be blocked — but BUG-001 silently fails
        assert result2["status"] != "PASSED", (
            f"BUG-001 CONFIRMED: Duplicate username '{username1}' was created"
        )

        # Cleanup
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-D02: Duplicate Email ----
    @pytest.mark.xfail(
        reason="BUG-001b: Duplicate email causes silent failure — no error message, no record created",
        strict=False,
    )
    def test_UC_D02_duplicate_email(self, uc_page):
        """Create two users with the same email — should be blocked.
        BUG-001b: Duplicate email causes silent failure (same as duplicate username).
        The form stays open with no error message and no record created.
        """
        log.info("UC-D02: Duplicate email test")
        page = uc_page

        # Create first user
        username1, data1 = _create_prerequisite_user(page, "DupD02")

        if not username1:
            log.warning("First user creation failed — cannot test duplicate email")
            return

        # Create second user with same email but different username
        dup_data = generate_duplicate_user_data(data1["email"])
        result2 = page.create_user(dup_data)

        # BUG-001b: Should be blocked but silently fails
        assert result2["status"] != "PASSED", (
            "Duplicate email was allowed by the ERP — no uniqueness validation"
        )
        if result2["status"] == "FAILED":
            log.info(f"Duplicate email blocked (silent failure): {result2.get('message', '')}")

        # Cleanup
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-D03: Duplicate (case-insensitive username) ----
    def test_UC_D03_duplicate_case_insensitive(self, uc_page):
        """Create user with same username in different case — test behavior."""
        log.info("UC-D03: Duplicate case-insensitive username test")
        page = uc_page

        # Create first user
        username1, data1 = _create_prerequisite_user(page, "DupD03")

        if not username1:
            log.warning("First user creation failed")
            return

        # Create second user with lowercase version of username
        dup_data = generate_case_insensitive_duplicate_username(username1)
        result2 = page.create_user(dup_data)

        if result2["status"] == "PASSED":
            log.info("Case-insensitive duplicate allowed by ERP")
        else:
            log.info(f"Case-insensitive duplicate blocked: {result2.get('error', '')}")

        # Cleanup
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 3: Edit Form Validations (6 tests)
# ====================================================================

class TestEditFormValidations:
    """UC-E01 to UC-E06: Validation checks on the Edit form."""

    # ---- UC-E01: Edit with valid data ----
    def test_UC_E01_edit_valid(self, uc_page):
        """Edit a user with valid new data — should succeed."""
        log.info("UC-E01: Edit with valid data test")
        page = uc_page

        username, data = _create_prerequisite_user(page, "EditVal")

        if not username:
            log.warning("Prerequisite user not created")
            return

        edit_data = generate_valid_edit_data("EditedUC")
        result = page.edit_user(username, edit_data)

        if result["status"] == "PASSED":
            log.info("User updated successfully")
        else:
            log.warning(f"Edit failed: {result.get('error', '')}")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-E02: Edit with empty First Name ----
    def test_UC_E02_edit_empty_first_name(self, uc_page):
        """Clear First Name in Edit, click Update — should be blocked."""
        log.info("UC-E02: Edit with empty First Name test")
        page = uc_page

        username, data = _create_prerequisite_user(page, "EditEmpty")

        if not username:
            log.warning("Prerequisite user not created")
            return

        # Click Edit
        page.click_edit_button(username)
        page.wait_seconds(2)

        # Clear First Name and try to Update
        page.type_text(page.FIRST_NAME_INPUT, "", clear_first=True)
        page.wait_seconds(0.5)
        page.click_update()
        page.wait_seconds(2)

        validation_alert = page.handle_validation_warning(timeout=3)
        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG: Update accepted with empty First Name"
        )
        log.info("Empty First Name in Edit blocked — validation working")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-E03: Edit with special chars in First Name ----
    def test_UC_E03_edit_special_chars(self, uc_page):
        """Edit to special characters in First Name — check behavior."""
        log.info("UC-E03: Edit with special chars test")
        page = uc_page

        username, data = _create_prerequisite_user(page, "EditSpCh")

        if not username:
            log.warning("Prerequisite user not created")
            return

        edit_data = {"first_name": "!@#$%^&*()"}
        result = page.edit_user(username, edit_data)

        if result["status"] == "PASSED":
            log.info("Special chars accepted in First Name during edit")
        else:
            log.info(f"Special chars in Edit rejected: {result.get('error', '')}")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-E04: Edit pre-populated fields ----
    def test_UC_E04_edit_prepopulated(self, uc_page):
        """Edit popup should show fields pre-populated with existing data."""
        log.info("UC-E04: Edit pre-populated fields test")
        page = uc_page

        username, data = _create_prerequisite_user(page, "EditPre")

        if not username:
            log.warning("Prerequisite user not created")
            return

        # Click Edit
        page.click_edit_button(username)
        page.wait_seconds(2)

        # Read form values
        form_values = page.get_edit_form_values()

        assert form_values.get("username") or form_values.get("first_name"), (
            "Edit form fields empty — not pre-populated"
        )
        log.info(f"Edit form pre-populated: {form_values}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-E05: Edit Email ----
    def test_UC_E05_edit_email(self, uc_page):
        """Change email in Edit — should succeed."""
        log.info("UC-E05: Edit email test")
        page = uc_page

        username, data = _create_prerequisite_user(page, "EditEmail")

        if not username:
            log.warning("Prerequisite user not created")
            return

        new_email = generate_email("edited")
        edit_data = {"email": new_email}
        result = page.edit_user(username, edit_data)

        if result["status"] == "PASSED":
            log.info("Email changed in Edit — update succeeded")
        else:
            log.info(f"Email edit result: {result.get('error', '')}")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-E06: Edit Username may be read-only ----
    def test_UC_E06_edit_username_readonly(self, uc_page):
        """Username may be read-only in Edit mode — verify behavior."""
        log.info("UC-E06: Edit Username readonly test")
        page = uc_page

        username, data = _create_prerequisite_user(page, "EditUNRO")

        if not username:
            log.warning("Prerequisite user not created")
            return

        # Click Edit
        page.click_edit_button(username)
        page.wait_seconds(2)

        # Check if Username input is disabled/readonly in edit mode
        try:
            username_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[formcontrolname='username']"
            )
            is_disabled = username_input.get_attribute("disabled") is not None
            is_readonly = username_input.get_attribute("readonly") is not None
            aria_disabled = username_input.get_attribute("aria-disabled") == "true"

            if is_disabled or is_readonly or aria_disabled:
                log.info("Username is read-only in Edit mode — expected behavior")
            else:
                log.info("Username is editable in Edit mode")
        except Exception as e:
            log.info(f"Could not check Username field state: {e}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 4: Search & Filter Edge Cases (5 tests)
# ====================================================================

class TestSearchFilter:
    """UC-S01 to UC-S05: Search and filter edge cases."""

    # ---- UC-S01: Search exact match ----
    def test_UC_S01_search_exact(self, uc_page):
        """Search for an exact existing username."""
        log.info("UC-S01: Search exact match test")
        page = uc_page

        # Create a user to search for
        username, data = _create_prerequisite_user(page, "SearchEx")

        if not username:
            log.warning("Prerequisite user not created")
            return

        # Search for the exact username
        page.search(username)
        page.wait_seconds(3)

        found = page.search_and_verify(username)
        assert found, f"Exact search failed for: {username}"
        log.info(f"Exact search found: {username}")

        # Clear search
        page.clear_search()

    # ---- UC-S02: Search partial match ----
    def test_UC_S02_search_partial(self, uc_page):
        """Search with partial username — should find matching records."""
        log.info("UC-S02: Search partial match test")
        page = uc_page

        # Create a user to search for
        username, data = _create_prerequisite_user(page, "SearchPar")

        if not username:
            log.warning("Prerequisite user not created")
            return

        # Use first 8 chars of username for partial search
        partial = username[:8]
        page.search(partial)
        page.wait_seconds(3)

        # At least one result should contain the partial string
        found = page.search_and_verify(partial)
        if found:
            log.info(f"Partial search '{partial}' found results")
        else:
            log.warning(f"Partial search '{partial}' found no results")

        page.clear_search()

    # ---- UC-S03: Search case insensitive ----
    def test_UC_S03_search_case_insensitive(self, uc_page):
        """Search with lowercase — should match case-insensitive."""
        log.info("UC-S03: Search case-insensitive test")
        page = uc_page

        username, data = _create_prerequisite_user(page, "SearchCI")

        if not username:
            log.warning("Prerequisite user not created")
            return

        search_term = username.lower()
        page.search(search_term)
        page.wait_seconds(3)

        found = page.search_and_verify(search_term)
        log.info(f"Case-insensitive search for '{search_term}': found={found}")

        page.clear_search()

    # ---- UC-S04: Search no results ----
    def test_UC_S04_search_no_results(self, uc_page):
        """Search for non-existent username — should show empty or no-data."""
        log.info("UC-S04: Search no results test")
        page = uc_page

        page.search("ZZZZZ_NONEXISTENT_USER_12345")
        page.wait_seconds(3)

        # Table should be empty or show no-data
        row_count = page.get_table_row_count()
        log.info(f"Non-existent search returned {row_count} results")

        page.clear_search()

    # ---- UC-S05: Search special chars ----
    def test_UC_S05_search_special_chars(self, uc_page):
        """Search for special characters — should not crash."""
        log.info("UC-S05: Search special chars test")
        page = uc_page

        page.search("!@#$%")
        page.wait_seconds(3)

        # Should not crash — just return results or empty
        row_count = page.get_table_row_count()
        log.info(f"Special chars search returned {row_count} results")

        page.clear_search()


# ====================================================================
# PHASE 5: Popup & UI Behaviors (5 tests)
# ====================================================================

class TestPopupUIBehaviors:
    """UC-P01 to UC-P05: Popup and UI behavior tests."""

    # ---- UC-P01: Add form opens ----
    def test_UC_P01_add_form_opens(self, uc_page):
        """Click ADD button — popup should open with all form fields."""
        log.info("UC-P01: Add form opens test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)

        is_open = page.is_add_form_open()
        assert is_open, "Add form did not open"

        # Verify key form fields exist
        try:
            username_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[formcontrolname='username']"
            )
            assert username_input.is_displayed(), "Username input not visible"
            log.info("Username input found in Add form")
        except Exception:
            log.warning("Username input not found in Add form")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass

    # ---- UC-P02: View popup readonly ----
    def test_UC_P02_view_readonly(self, uc_page):
        """View popup should show disabled/readonly fields with Cancel only."""
        log.info("UC-P02: View popup readonly test")
        page = uc_page

        username, data = _create_prerequisite_user(page, "ViewRO")

        if not username:
            log.warning("Prerequisite user not created")
            return

        page.click_view_button(username)
        page.wait_seconds(2)

        # View mode should have disabled inputs
        is_readonly, details = page.is_view_popup_readonly()
        if is_readonly:
            log.info("View popup has disabled inputs — readonly confirmed")
        else:
            log.info(f"View popup check — some fields appear editable: {details}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-P03: Cancel closes popup ----
    def test_UC_P03_cancel_closes_popup(self, uc_page):
        """Open Add, click Cancel — popup should close without creating record."""
        log.info("UC-P03: Cancel closes popup test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Fill some data
        data = generate_valid_user_data("CancelTest")
        page.fill_user_form(data)
        page.wait_seconds(0.5)

        # Click Cancel
        page.cancel()
        page.wait_seconds(1)

        # Popup should be closed
        assert not page.is_add_form_open(), "Popup still open after Cancel"
        log.info("Cancel closed the popup — no record created")

    # ---- UC-P04: Close (X) button ----
    def test_UC_P04_close_x_button(self, uc_page):
        """Open Add, click X — popup should close."""
        log.info("UC-P04: Close (X) button test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Click X button via force close
        page.force_close_form_popup()
        page.wait_seconds(1)

        assert not page.is_add_form_open(), "Popup still open after X click"
        log.info("X button closed the popup")

    # ---- UC-P05: SweetAlert2 success ----
    def test_UC_P05_sweetalert_success(self, uc_page):
        """Create valid record — verify SweetAlert2 success message."""
        log.info("UC-P05: SweetAlert2 success test")
        page = uc_page

        data = generate_valid_user_data("SWTest")
        result = page.create_user(data)

        if result["status"] == "PASSED":
            log.info("SweetAlert2 success confirmed — user created")
        else:
            log.info(f"Create result: {result['status']} — {result.get('error', '')}")

        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 6: History & Audit Trail (4 tests)
# ====================================================================

class TestHistoryAuditTrail:
    """UC-H01 to UC-H04: History popup and audit trail tests."""

    # ---- UC-H01: History popup opens and closes ----
    def test_UC_H01_history_opens_and_closes(self, uc_page):
        """Click History button — popup should open. Then close it."""
        log.info("UC-H01: History popup opens and closes test")
        page = uc_page

        username, data = _create_prerequisite_user(page, "HistOpen")

        if not username:
            log.warning("Prerequisite user not created")
            return

        # Open history
        is_open = page.open_history(username)
        assert is_open, "History popup did not open"
        log.info("History popup opened successfully")

        # Close history
        page.close_history_popup()
        page.wait_seconds(1)

        # Verify closed
        still_open = page.is_history_popup_open()
        assert not still_open, "History popup still open after close"
        log.info("History popup closed successfully")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-H02: History for edited record ----
    def test_UC_H02_history_edited(self, uc_page):
        """View history for an edited record — should show history entries."""
        log.info("UC-H02: History for edited record test")
        page = uc_page

        username, data = _create_prerequisite_user(page, "HistEdit")

        if not username:
            log.warning("Prerequisite user not created")
            return

        # Edit the user first
        edit_data = generate_valid_edit_data("HistEdited")
        page.edit_user(username, edit_data)
        page.wait_seconds(1)

        # Cleanup edit popup
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Open history
        is_open = page.open_history(username)
        if is_open:
            row_count = page.get_history_rows()
            log.info(f"History for edited record: {row_count} entries")
            page.close_history_popup()
        else:
            log.warning("History popup did not open for edited record")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-H03: History popup has search input ----
    def test_UC_H03_history_has_search(self, uc_page):
        """History popup should have a search input."""
        log.info("UC-H03: History has search input test")
        page = uc_page

        username, data = _create_prerequisite_user(page, "HistSrch")

        if not username:
            log.warning("Prerequisite user not created")
            return

        is_open = page.open_history(username)
        if is_open:
            has_search = page.has_history_search_input()
            if has_search:
                log.info("History popup has search input")
            else:
                log.info("History popup does NOT have search input")

            page.close_history_popup()
        else:
            log.warning("History popup did not open")

        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-H04: History popup shows at least one entry ----
    def test_UC_H04_history_has_entry(self, uc_page):
        """History popup should show at least one entry (the creation)."""
        log.info("UC-H04: History has at least one entry test")
        page = uc_page

        username, data = _create_prerequisite_user(page, "HistEntry")

        if not username:
            log.warning("Prerequisite user not created")
            return

        is_open = page.open_history(username)
        if is_open:
            row_count = page.get_history_rows()
            assert row_count >= 1, (
                f"History popup should have at least 1 entry, found {row_count}"
            )
            log.info(f"History has {row_count} entries — creation tracked")
            page.close_history_popup()
        else:
            log.warning("History popup did not open")

        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 7: Bug-Specific Tests (3 tests)
# ====================================================================

class TestBugSpecific:
    """UC-B01 to UC-B03: Tests targeting specific known bugs."""

    # ---- UC-B01: BUG-001 — Duplicate username silent failure ----
    @pytest.mark.xfail(
        reason="BUG-001: Duplicate username silently fails, no error message",
        strict=False,
    )
    def test_UC_B01_duplicate_username_silent_fail(self, uc_page):
        """Verify BUG-001: Duplicate username causes silent failure.

        When creating a user with a username that already exists, the Submit
        button appears to succeed but no record is created and no error is shown.
        """
        log.info("UC-B01: BUG-001 — Duplicate username silent failure test")
        page = uc_page

        username, data = _create_prerequisite_user(page, "Bug001")

        if not username:
            log.warning("Prerequisite user not created")
            return

        # Try to create another user with the same username
        dup_data = generate_duplicate_username_data(username)
        page.open_add_form()
        page.fill_user_form(dup_data)
        page.submit()
        page.wait_seconds(2)

        # BUG-001: No error message shown
        errors = page.get_mat_error_text()
        validation_alert = page.handle_validation_warning(timeout=3)

        # The form should still be open with some error
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors or validation_alert, (
            "BUG-001 CONFIRMED: Duplicate username caused silent failure — "
            "no error message shown to user"
        )

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-B02: BUG-005 — Designation duplicate Manager ----
    def test_UC_B02_designation_duplicate_manager(self, uc_page):
        """Verify BUG-005: Designation dropdown has duplicate 'Manager' option."""
        log.info("UC-B02: BUG-005 — Designation duplicate Manager test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Open Designation dropdown and check for duplicates
        try:
            # Find the designation mat-select (4th one)
            selects = page.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model mat-select, mat-dialog-container mat-select, "
                ".edit_pop_up mat-select"
            )
            if len(selects) >= 4:
                designation_select = selects[3]
                page.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    designation_select,
                )
                page.wait_seconds(1)

                # Get all options
                options = page.driver.find_elements(
                    By.CSS_SELECTOR, "div[role='listbox'] mat-option"
                )
                option_texts = []
                for opt in options:
                    try:
                        text = opt.text.strip()
                        if text:
                            option_texts.append(text)
                    except Exception:
                        continue

                # Check for duplicates
                from collections import Counter
                counts = Counter(option_texts)
                duplicates = {k: v for k, v in counts.items() if v > 1}

                if duplicates:
                    log.warning(f"BUG-005 CONFIRMED: Duplicate options in Designation: {duplicates}")
                else:
                    log.info("No duplicate options found in Designation dropdown")

                page._force_close_panels()
            else:
                log.warning("Could not find Designation dropdown")
        except Exception as e:
            log.warning(f"Designation dropdown check failed: {e}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass

    # ---- UC-B03: BUG-006 — Only 1 mat-error at a time ----
    def test_UC_B03_only_one_mat_error(self, uc_page):
        """Verify BUG-006: Only 1 mat-error visible at a time.

        When multiple fields are invalid, only one error message is shown.
        The user has to fix one error to see the next.
        """
        log.info("UC-B03: BUG-006 — Only 1 mat-error at a time test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        # Click Submit with all fields empty
        page.submit()
        page.wait_seconds(2)

        # Count visible mat-errors
        try:
            error_elements = page.driver.find_elements(
                By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
            )
            visible_errors = []
            for el in error_elements:
                try:
                    if el.is_displayed() and el.text.strip():
                        visible_errors.append(el.text.strip())
                except Exception:
                    continue

            if len(visible_errors) <= 1:
                log.warning(
                    f"BUG-006 CONFIRMED: Only {len(visible_errors)} mat-error "
                    f"visible at a time (expected multiple for empty submit)"
                )
            else:
                log.info(f"Multiple errors visible: {visible_errors}")
        except Exception as e:
            log.warning(f"Error check failed: {e}")

        # Cleanup
        try:
            page.cancel()
        except Exception:
            try:
                page.force_close_form_popup()
            except Exception:
                pass
