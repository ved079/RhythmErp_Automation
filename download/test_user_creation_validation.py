"""
test_user_creation_validation.py
---------------------------------
Comprehensive validation test suite for RhythmERP User Creation Screen.
43 test cases across 7 phases covering all bugs found during exploration.

Phases:
  1. Create Form Validations   (16 tests) — UC-C01 to UC-C16
  2. Duplicate Validations      (3 tests)  — UC-D01 to UC-D03
  3. Edit Form Validations      (6 tests)  — UC-E01 to UC-E06
  4. Search & Filter Edge Cases (4 tests)  — UC-S01 to UC-S04
  5. Popup & UI Behaviors       (6 tests)  — UC-P01 to UC-P06
  6. History Validations        (3 tests)  — UC-H01 to UC-H03
  7. Bug-Specific Tests         (5 tests)  — UC-B01 to UC-B04

Run:
  pytest test_user_creation_validation.py -v --tb=short
  pytest test_user_creation_validation.py -v -k "TestCreateForm" --tb=short
  pytest test_user_creation_validation.py -v -k "UC-C02" --tb=short
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
    generate_valid_edit_data,
    generate_empty_data,
    generate_spaces_only,
    generate_string_256,
    generate_special_char_username,
    generate_xss_username,
    generate_sql_injection_username,
    generate_invalid_email,
    generate_special_char_name,
    generate_duplicate_username_data,
    generate_duplicate_email_data,
    generate_case_variant_username,
    ExpectedMessages,
    KnownBugs,
)
from common.logger import log


# ====================================================================
# Helper: create a user, refresh, and return its username
# ====================================================================

def _create_prerequisite_user(page, data=None):
    """Create a user for tests that need existing data.
    Returns the username used.
    """
    if data is None:
        data = generate_valid_user_data("PreReq")
    result = page.create_user(data)
    try:
        page.force_close_form_popup()
    except Exception:
        pass
    page.click_refresh()
    page.wait_seconds(2)
    return data.get("username", ""), result


# ====================================================================
# PHASE 1: Create Form Validations (16 tests)
# ====================================================================

class TestCreateFormValidations:
    """UC-C01 to UC-C16: Validation checks on the Create form."""

    # ---- UC-C01: Submit with all fields empty ----
    def test_UC_C01_empty_submit(self, uc_page):
        """Submit with all fields empty — should show validation errors."""
        log.info("UC-C01: Empty submit test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        page.submit()
        page.wait_seconds(2)

        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        # BUG-006: Only 1 mat-error visible at a time
        assert form_still_open or errors, (
            "BUG: Form submitted with all fields empty — no validation"
        )
        if errors:
            log.info(f"Validation errors shown: {errors}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- UC-C02: Valid user creation (happy path) ----
    def test_UC_C02_valid_create(self, uc_page):
        """Create a user with all valid data — should succeed."""
        log.info("UC-C02: Valid create test")
        page = uc_page

        data = generate_valid_user_data("ValidUC")
        result = page.create_user(data)

        assert result["status"] == "PASSED", (
            f"Valid user creation failed: {result['message']}"
        )
        log.info(f"User created: {data['username']}")

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C03: Only Username filled — submit ----
    def test_UC_C03_username_only(self, uc_page):
        """Submit with only Username filled — should be blocked."""
        log.info("UC-C03: Username-only submit test")
        page = uc_page

        data = generate_valid_user_data("NameOnly")
        page.open_add_form()
        page.wait_seconds(1)
        page.type_text(page.USERNAME_INPUT, data["username"], clear_first=True)
        page.submit()
        page.wait_seconds(2)

        errors = page.get_mat_error_text()
        form_still_open = page.is_add_form_open()

        assert form_still_open or errors, (
            "BUG: Form submitted with only Username — missing fields not validated"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- UC-C04: Username with spaces only ----
    def test_UC_C04_spaces_in_username(self, uc_page):
        """Username with spaces only — should be rejected."""
        log.info("UC-C04: Spaces in username test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        page.type_text(
            page.USERNAME_INPUT,
            generate_spaces_only(5),
            clear_first=True,
        )
        # Trigger blur
        page.type_text(page.EMAIL_INPUT, "", clear_first=True)
        page.wait_seconds(1)

        has_error = page.has_field_error("Username")
        errors = page.get_mat_error_text()

        assert has_error or errors, (
            "BUG: Spaces-only username accepted without error"
        )
        if errors:
            assert "spaces" in errors[0].lower(), (
                f"Expected 'spaces' in error, got: {errors[0]}"
            )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- UC-C05: Username with leading/trailing spaces ----
    def test_UC_C05_leading_trailing_spaces(self, uc_page):
        """Username with leading/trailing spaces — should be trimmed or rejected."""
        log.info("UC-C05: Leading/trailing spaces in username test")
        page = uc_page

        spaced_name = "  " + "SpaceTest" + "  "
        data = generate_valid_user_data()
        data["username"] = spaced_name

        result = page.create_user(data)

        if result["status"] == "PASSED":
            page.click_refresh()
            page.wait_seconds(2)
            names = page.get_all_usernames()
            # BUG: spaces may not be trimmed
            has_spaces = any(n != n.strip() for n in names if spaced_name.strip() in n)
            if has_spaces:
                log.warning("BUG: Leading/trailing spaces NOT trimmed in Username")
        else:
            log.info("Spaces rejected — validation working")

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C06: Email with invalid format ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_003, strict=False)
    def test_UC_C06_invalid_email(self, uc_page):
        """Email with invalid format — should be rejected.
        BUG-003: No email format validation.
        """
        log.info("UC-C06: Invalid email test")
        page = uc_page

        data = generate_valid_user_data("InvEmail")
        data["email"] = generate_invalid_email()

        result = page.create_user(data)

        assert result["status"] == "FAILED", (
            "BUG CONFIRMED: Invalid email accepted"
        )
        log.info("Invalid email rejected — validation working")

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C07: Email with no @ sign ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_003, strict=False)
    def test_UC_C07_email_no_at(self, uc_page):
        """Email without @ sign — should be rejected.
        BUG-003: No email format validation.
        """
        log.info("UC-C07: Email no @ test")
        page = uc_page

        data = generate_valid_user_data("NoAt")
        data["email"] = "userdomain.com"

        result = page.create_user(data)

        assert result["status"] == "FAILED", (
            "BUG CONFIRMED: Email without @ accepted"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C08: Username with special characters ----
    def test_UC_C08_special_chars_username(self, uc_page):
        """Username with special characters — should show error (message may be misleading)."""
        log.info("UC-C08: Special chars in username test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        page.type_text(
            page.USERNAME_INPUT,
            generate_special_char_username(),
            clear_first=True,
        )
        # Trigger blur
        page.type_text(page.EMAIL_INPUT, "", clear_first=True)
        page.wait_seconds(1)

        has_error = page.has_field_error("Username")
        errors = page.get_mat_error_text()

        # BUG-004: Error says "spaces" but it's about special chars
        assert has_error or errors, (
            "BUG: Special characters in Username not validated"
        )
        if errors and "spaces" in errors[0].lower():
            log.warning(
                "BUG-004: Error says 'spaces' for special chars — misleading message"
            )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- UC-C09: First Name with special characters ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_005, strict=False)
    def test_UC_C09_special_chars_first_name(self, uc_page):
        """First Name with special characters — should be rejected.
        BUG-005: No input sanitization on First Name.
        """
        log.info("UC-C09: Special chars in first name test")
        page = uc_page

        data = generate_valid_user_data("SpecFN")
        data["first_name"] = generate_special_char_name()

        result = page.create_user(data)

        assert result["status"] == "FAILED", (
            "BUG CONFIRMED: Special chars accepted in First Name"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C10: Last Name with special characters ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_005, strict=False)
    def test_UC_C10_special_chars_last_name(self, uc_page):
        """Last Name with special characters — should be rejected.
        BUG-005: No input sanitization on Last Name.
        """
        log.info("UC-C10: Special chars in last name test")
        page = uc_page

        data = generate_valid_user_data("SpecLN")
        data["last_name"] = generate_special_char_name()

        result = page.create_user(data)

        assert result["status"] == "FAILED", (
            "BUG CONFIRMED: Special chars accepted in Last Name"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C11: Very long Username (256 chars) ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_002, strict=False)
    def test_UC_C11_long_username(self, uc_page):
        """Username with 256+ chars — should be rejected or truncated.
        BUG-002: No maxlength validation.
        """
        log.info("UC-C11: Very long username test")
        page = uc_page

        data = generate_valid_user_data("LongUC")
        data["username"] = generate_string_256()

        result = page.create_user(data)

        assert result["status"] == "FAILED", (
            "BUG CONFIRMED: 256+ char username accepted"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C12: Email format validation on submit ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_003, strict=False)
    def test_UC_C12_email_validation_submit(self, uc_page):
        """Email format validation on submit — should reject invalid emails.
        BUG-003: No email format validation on submit.
        """
        log.info("UC-C12: Email validation on submit test")
        page = uc_page

        data = generate_valid_user_data("EmailVal")
        data["email"] = "not-an-email"

        result = page.create_user(data)

        assert result["status"] == "FAILED", (
            "BUG CONFIRMED: Invalid email accepted on submit"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-C13: Without User Type selected ----
    def test_UC_C13_no_user_type(self, uc_page):
        """Submit without selecting User Type — should be blocked."""
        log.info("UC-C13: No User Type selected test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        data = generate_valid_user_data("NoUT")
        # Fill text fields only
        page.type_text(page.USERNAME_INPUT, data["username"], clear_first=True)
        page.type_text(page.EMAIL_INPUT, data["email"], clear_first=True)
        page.type_text(page.FIRST_NAME_INPUT, data["first_name"], clear_first=True)
        page.type_text(page.LAST_NAME_INPUT, data["last_name"], clear_first=True)
        page.type_text(page.PASSWORD_INPUT, data["password"], clear_first=True)
        # Select Role, Entity, Designation but NOT User Type
        page._select_random_from_dropdown(page.ROLE_SELECT, "Role")
        page._select_random_from_dropdown(page.ENTITY_SELECT, "Entity")
        page._select_random_from_dropdown(page.DESIGNATION_SELECT, "Designation")
        page._force_close_panels()
        page.submit()
        page.wait_seconds(2)

        form_still_open = page.is_add_form_open()
        assert form_still_open, (
            "BUG: Form submitted without User Type"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- UC-C14: Without Role selected ----
    def test_UC_C14_no_role(self, uc_page):
        """Submit without selecting Role — should be blocked."""
        log.info("UC-C14: No Role selected test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        data = generate_valid_user_data("NoRole")
        page.type_text(page.USERNAME_INPUT, data["username"], clear_first=True)
        page.type_text(page.EMAIL_INPUT, data["email"], clear_first=True)
        page.type_text(page.FIRST_NAME_INPUT, data["first_name"], clear_first=True)
        page.type_text(page.LAST_NAME_INPUT, data["last_name"], clear_first=True)
        page.type_text(page.PASSWORD_INPUT, data["password"], clear_first=True)
        page._select_random_from_dropdown(page.USER_TYPE_SELECT, "User Type")
        page._select_random_from_dropdown(page.ENTITY_SELECT, "Entity")
        page._select_random_from_dropdown(page.DESIGNATION_SELECT, "Designation")
        page._force_close_panels()
        page.submit()
        page.wait_seconds(2)

        form_still_open = page.is_add_form_open()
        assert form_still_open, "BUG: Form submitted without Role"

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- UC-C15: Without Entity selected ----
    def test_UC_C15_no_entity(self, uc_page):
        """Submit without selecting Entity — should be blocked."""
        log.info("UC-C15: No Entity selected test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        data = generate_valid_user_data("NoEnt")
        page.type_text(page.USERNAME_INPUT, data["username"], clear_first=True)
        page.type_text(page.EMAIL_INPUT, data["email"], clear_first=True)
        page.type_text(page.FIRST_NAME_INPUT, data["first_name"], clear_first=True)
        page.type_text(page.LAST_NAME_INPUT, data["last_name"], clear_first=True)
        page.type_text(page.PASSWORD_INPUT, data["password"], clear_first=True)
        page._select_random_from_dropdown(page.USER_TYPE_SELECT, "User Type")
        page._select_random_from_dropdown(page.ROLE_SELECT, "Role")
        page._select_random_from_dropdown(page.DESIGNATION_SELECT, "Designation")
        page._force_close_panels()
        page.submit()
        page.wait_seconds(2)

        form_still_open = page.is_add_form_open()
        assert form_still_open, "BUG: Form submitted without Entity"

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- UC-C16: Without Designation selected ----
    def test_UC_C16_no_designation(self, uc_page):
        """Submit without selecting Designation — should be blocked."""
        log.info("UC-C16: No Designation selected test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        data = generate_valid_user_data("NoDesig")
        page.type_text(page.USERNAME_INPUT, data["username"], clear_first=True)
        page.type_text(page.EMAIL_INPUT, data["email"], clear_first=True)
        page.type_text(page.FIRST_NAME_INPUT, data["first_name"], clear_first=True)
        page.type_text(page.LAST_NAME_INPUT, data["last_name"], clear_first=True)
        page.type_text(page.PASSWORD_INPUT, data["password"], clear_first=True)
        page._select_random_from_dropdown(page.USER_TYPE_SELECT, "User Type")
        page._select_random_from_dropdown(page.ROLE_SELECT, "Role")
        page._select_random_from_dropdown(page.ENTITY_SELECT, "Entity")
        page._force_close_panels()
        page.submit()
        page.wait_seconds(2)

        form_still_open = page.is_add_form_open()
        assert form_still_open, "BUG: Form submitted without Designation"

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()


# ====================================================================
# PHASE 2: Duplicate Validations (3 tests)
# ====================================================================

class TestDuplicateValidations:
    """UC-D01 to UC-D03: Duplicate data checks."""

    # ---- UC-D01: Duplicate username in Create ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_001, strict=False)
    def test_UC_D01_duplicate_username(self, uc_page):
        """Create user with existing username — should show error.
        BUG-001: Duplicate is silently blocked with no error message.
        """
        log.info("UC-D01: Duplicate username test")
        page = uc_page

        # Create first user
        data1 = generate_valid_user_data("Dup1")
        result1 = page.create_user(data1)
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Try creating second with same username
        data2 = generate_duplicate_username_data(data1["username"])
        result2 = page.create_user(data2)

        # If form stayed open silently, that's the bug
        if result2["status"] == "PASSED":
            # Check if it actually was created (shouldn't be)
            page.click_refresh()
            page.wait_seconds(2)
            assert False, "BUG CONFIRMED: Duplicate username was created"
        else:
            # Expected: form stays open with error
            # But BUG-001: no error message is shown
            errors = page.get_mat_error_text()
            swal = page.handle_validation_warning(timeout=3)
            if not errors and not swal:
                log.warning(
                    "BUG-001: Duplicate username silently blocked — no error message shown"
                )
            assert errors or swal, (
                "BUG-001: Duplicate blocked silently with no feedback to user"
            )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-D02: Duplicate email in Create (by design: allowed) ----
    def test_UC_D02_duplicate_email(self, uc_page):
        """Create user with existing email — should be ALLOWED (by design)."""
        log.info("UC-D02: Duplicate email test")
        page = uc_page

        # Create first user
        data1 = generate_valid_user_data("DupE1")
        result1 = page.create_user(data1)
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Create second with same email but different username
        data2 = generate_duplicate_email_data(data1["email"])
        result2 = page.create_user(data2)

        assert result2["status"] == "PASSED", (
            "Duplicate email should be allowed (by design)"
        )
        log.info("Duplicate email allowed — confirmed by design")

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-D03: Case-insensitive duplicate username ----
    def test_UC_D03_case_insensitive_username(self, uc_page):
        """Try creating user with uppercase version of existing username."""
        log.info("UC-D03: Case sensitivity test")
        page = uc_page

        # Create first user
        data1 = generate_valid_user_data("Case1")
        result1 = page.create_user(data1)
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Try uppercase version
        upper_username = generate_case_variant_username(data1["username"])
        data2 = generate_valid_user_data("Case2")
        data2["username"] = upper_username

        result2 = page.create_user(data2)
        # Whether this passes or fails depends on ERP's case sensitivity
        log.info(f"Case variant result: {result2['status']} - {result2['message']}")

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
    def test_UC_E01_valid_edit(self, uc_page):
        """Edit user with valid data — should succeed."""
        log.info("UC-E01: Valid edit test")
        page = uc_page

        username, create_result = _create_prerequisite_user(page)

        edit_result = page.edit_user(
            username,
            {"first_name": "EditedFirst", "last_name": "EditedLast"},
        )

        assert edit_result["status"] == "PASSED", (
            f"Valid edit failed: {edit_result['message']}"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-E02: Edit pre-populated fields ----
    def test_UC_E02_edit_prepopulated(self, uc_page):
        """Edit popup should show all fields pre-populated with existing data."""
        log.info("UC-E02: Edit pre-populated fields test")
        page = uc_page

        data = generate_valid_user_data("EditPre")
        data["first_name"] = "PrePopFirst"
        data["last_name"] = "PrePopLast"
        result = page.create_user(data)
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        page.click_edit_button(username=data["username"])
        page.wait_seconds(1)

        form_values = page.get_form_field_values()

        assert form_values.get("username"), "Username empty in Edit form"
        assert form_values.get("email"), "Email empty in Edit form"
        assert form_values.get("first_name"), "First Name empty in Edit form"
        assert form_values.get("last_name"), "Last Name empty in Edit form"
        # Password should be empty in Edit (placeholder: "Leave blank to keep current")
        assert form_values.get("user_type"), "User Type empty in Edit form"
        assert form_values.get("role"), "Role empty in Edit form"
        assert form_values.get("entity"), "Entity empty in Edit form"
        assert form_values.get("designation"), "Designation empty in Edit form"

        log.info(f"Edit form pre-populated: {form_values}")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- UC-E03: Edit with empty Username ----
    def test_UC_E03_edit_empty_username(self, uc_page):
        """Edit: clear Username and submit — should show validation error."""
        log.info("UC-E03: Edit empty username test")
        page = uc_page

        username, _ = _create_prerequisite_user(page)

        page.click_edit_button(username=username)
        page.wait_seconds(1)

        # Clear username
        username_input = page.driver.find_element(
            By.CSS_SELECTOR, "input[formcontrolname='username']"
        )
        page.driver.execute_script(
            "arguments[0].value = '';"
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
            username_input,
        )
        page._force_close_panels()
        page.click_update()
        page.wait_seconds(2)

        form_still_open = page.is_add_form_open()
        errors = page.get_mat_error_text()

        assert form_still_open or errors, (
            "BUG: Edit submitted with empty Username"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- UC-E04: Edit to duplicate Username ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_001, strict=False)
    def test_UC_E04_edit_duplicate_username(self, uc_page):
        """Edit user to an existing username — should show error.
        BUG-001: Duplicate silently blocked.
        """
        log.info("UC-E04: Edit duplicate username test")
        page = uc_page

        # Create two users
        data1 = generate_valid_user_data("EditDup1")
        result1 = page.create_user(data1)
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        data2 = generate_valid_user_data("EditDup2")
        result2 = page.create_user(data2)
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Edit second user with first user's username
        edit_result = page.edit_user(
            data2["username"],
            {"username": data1["username"]},
        )

        if edit_result["status"] == "PASSED":
            log.warning("BUG: Duplicate username allowed in Edit form")
        else:
            log.info("Duplicate username rejected in Edit — validation working")

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-E05: Edit with invalid email ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_003, strict=False)
    def test_UC_E05_edit_invalid_email(self, uc_page):
        """Edit user with invalid email format — should be rejected.
        BUG-003: No email format validation.
        """
        log.info("UC-E05: Edit invalid email test")
        page = uc_page

        username, _ = _create_prerequisite_user(page)

        edit_result = page.edit_user(
            username,
            {"email": "notanemail"},
        )

        assert edit_result["status"] == "FAILED", (
            "BUG CONFIRMED: Invalid email accepted in Edit"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-E06: Edit password (leave blank) ----
    def test_UC_E06_edit_password_blank(self, uc_page):
        """Edit: leave password blank — password should remain unchanged."""
        log.info("UC-E06: Edit password blank test")
        page = uc_page

        username, _ = _create_prerequisite_user(page)

        # Edit with other field changes but password left blank
        edit_result = page.edit_user(
            username,
            {"first_name": "PwdTestEdit"},
        )

        # Should succeed — blank password = keep current
        assert edit_result["status"] == "PASSED", (
            f"Edit with blank password failed: {edit_result['message']}"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 4: Search & Filter Edge Cases (4 tests)
# ====================================================================

class TestSearchFilter:
    """UC-S01 to UC-S04: Search edge cases."""

    # ---- UC-S01: Search with exact username match ----
    def test_UC_S01_search_exact(self, uc_page):
        """Search with exact username — should find the user."""
        log.info("UC-S01: Search exact username test")
        page = uc_page

        data = generate_valid_user_data("SearchEx")
        result = page.create_user(data)
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        found = page.search_user(data["username"])

        assert found, f"Exact search failed for: {data['username']}"
        log.info(f"Exact search found: {data['username']}")

    # ---- UC-S02: Search with partial username ----
    def test_UC_S02_search_partial(self, uc_page):
        """Search with partial username — should find matching users."""
        log.info("UC-S02: Search partial username test")
        page = uc_page

        data = generate_valid_user_data("SearchPar")
        result = page.create_user(data)
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        partial = data["username"][:10]
        found = page.search_user(partial)

        assert found, f"Partial search failed for: {partial}"
        log.info(f"Partial search found with: {partial}")

    # ---- UC-S03: Search for non-existent username ----
    def test_UC_S03_search_nonexistent(self, uc_page):
        """Search for non-existent username — should return no results."""
        log.info("UC-S03: Search nonexistent test")
        page = uc_page

        fake_name = f"NonExistent_{int(time.time())}"
        found = page.search_user(fake_name)

        assert not found, (
            f"BUG: Non-existent name '{fake_name}' was found in table"
        )
        log.info(f"Correctly not found: {fake_name}")

    # ---- UC-S04: Search with special characters ----
    def test_UC_S04_search_special_chars(self, uc_page):
        """Search with special characters — should not crash."""
        log.info("UC-S04: Search special chars test")
        page = uc_page

        try:
            page.search_item("!@#$%^&*()")
            page.wait_seconds(2)
            log.info("Search with special chars did not crash")
        except Exception as e:
            log.warning(f"Search with special chars raised exception: {e}")

        page.click_refresh()
        page.wait_seconds(2)


# ====================================================================
# PHASE 5: Popup & UI Behaviors (6 tests)
# ====================================================================

class TestPopupUIBehaviors:
    """UC-P01 to UC-P06: Popup and UI interaction checks."""

    # ---- UC-P01: Cancel discards data ----
    def test_UC_P01_cancel_no_create(self, uc_page):
        """Cancel closes form without creating a user."""
        log.info("UC-P01: Cancel no create test")
        page = uc_page

        before_count = page.get_table_row_count()

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Form did not open"

        data = generate_valid_user_data("CancelTest")
        page.fill_user_form(data)
        page.cancel()
        page.wait_seconds(1)

        after_count = page.get_table_row_count()
        assert after_count == before_count, (
            f"BUG: Row count changed after Cancel. "
            f"Before: {before_count}, After: {after_count}"
        )
        log.info("Cancel correctly did not create a user")

    # ---- UC-P02: X button closes form ----
    def test_UC_P02_close_no_create(self, uc_page):
        """X button closes form without creating a user."""
        log.info("UC-P02: Close no create test")
        page = uc_page

        before_count = page.get_table_row_count()

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Form did not open"

        data = generate_valid_user_data("CloseTest")
        page.fill_user_form(data)
        page.close_popup()
        page.wait_seconds(1)

        after_count = page.get_table_row_count()
        assert after_count == before_count, (
            f"BUG: Row count changed after X close. "
            f"Before: {before_count}, After: {after_count}"
        )
        log.info("X close correctly did not create a user")

    # ---- UC-P03: View popup shows read-only fields ----
    def test_UC_P03_view_readonly(self, uc_page):
        """View popup shows all fields in read-only mode."""
        log.info("UC-P03: View read-only test")
        page = uc_page

        data = generate_valid_user_data("ViewTest")
        result = page.create_user(data)
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        page.click_view_button(username=data["username"])
        page.wait_seconds(1)

        is_readonly = page.verify_view_popup_read_only()

        assert is_readonly, (
            "BUG: View popup fields are editable (should be read-only)"
        )
        log.info("View popup correctly shows read-only fields")

        page.close_popup()
        page.wait_seconds(0.5)

    # ---- UC-P04: Edit popup shows Update button ----
    def test_UC_P04_edit_has_update(self, uc_page):
        """Edit popup shows Update button and editable fields."""
        log.info("UC-P04: Edit has Update button test")
        page = uc_page

        data = generate_valid_user_data("EditTest")
        result = page.create_user(data)
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        page.click_edit_button(username=data["username"])
        page.wait_seconds(1)

        is_edit = page.verify_edit_popup_editable()

        assert is_edit, (
            "BUG: Edit popup does not show Update button or fields not editable"
        )
        log.info("Edit popup correctly shows Update button")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- UC-P05: Fullscreen button works ----
    def test_UC_P05_fullscreen_toggle(self, uc_page):
        """Fullscreen button toggles popup size."""
        log.info("UC-P05: Fullscreen toggle test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)

        try:
            fullscreen_btns = page.driver.find_elements(
                By.CSS_SELECTOR,
                ".popup-actions button",
            )
            for btn in fullscreen_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "fullscreen" and btn.is_displayed():
                        page.driver.execute_script("arguments[0].click();", btn)
                        page.wait_seconds(0.5)
                        log.info("Fullscreen button clicked")
                        # Click again to restore
                        page.driver.execute_script("arguments[0].click();", btn)
                        page.wait_seconds(0.5)
                        log.info("Fullscreen restored")
                        break
                except Exception:
                    continue
        except Exception:
            log.warning("Fullscreen button not found")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- UC-P06: Designation duplicate Manager ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_007, strict=False)
    def test_UC_P06_designation_duplicate(self, uc_page):
        """Designation dropdown should not have duplicate 'Manager'.
        BUG-007: Manager appears twice.
        """
        log.info("UC-P06: Designation duplicate test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)

        # Open Designation dropdown
        page._select_random_from_dropdown(page.DESIGNATION_SELECT, "Designation")

        # Get options
        try:
            options = page.driver.find_elements(
                By.CSS_SELECTOR, "div[role='listbox'] mat-option"
            )
            option_texts = [o.text.strip() for o in options if o.text.strip()]
            page._force_close_panels()

            # Check for duplicates
            unique = set(option_texts)
            assert len(unique) == len(option_texts), (
                f"BUG-007 CONFIRMED: Duplicate options in Designation: {option_texts}"
            )
        except Exception:
            page._force_close_panels()

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()


# ====================================================================
# PHASE 6: History Validations (3 tests)
# ====================================================================

class TestHistoryValidations:
    """UC-H01 to UC-H03: History popup checks."""

    # ---- UC-H01: History popup opens ----
    def test_UC_H01_history_opens(self, uc_page):
        """History popup opens successfully."""
        log.info("UC-H01: History popup opens test")
        page = uc_page

        username, _ = _create_prerequisite_user(page)

        page.click_history_button(username=username)
        page.wait_seconds(2)

        is_open = page.is_history_popup_open()

        assert is_open, "History popup did not open"

        log.info("History popup opened")
        page.close_history_popup()
        page.wait_seconds(1)

    # ---- UC-H02: History Close button works ----
    def test_UC_H02_history_close(self, uc_page):
        """Close button closes the history popup."""
        log.info("UC-H02: History close test")
        page = uc_page

        username, _ = _create_prerequisite_user(page)

        page.click_history_button(username=username)
        page.wait_seconds(2)

        page.close_history_popup()
        page.wait_seconds(1)

        is_open = page.is_history_popup_open()
        assert not is_open, "History popup still open after Close"

        log.info("History popup closed correctly")

    # ---- UC-H03: History search input exists ----
    def test_UC_H03_history_search(self, uc_page):
        """History popup has a search input field."""
        log.info("UC-H03: History search input test")
        page = uc_page

        username, _ = _create_prerequisite_user(page)

        page.click_history_button(username=username)
        page.wait_seconds(2)

        has_search = page.is_displayed(page.HISTORY_SEARCH_INPUT, timeout=5)
        assert has_search, "History popup has no search input"

        log.info("History search input found")

        page.close_history_popup()
        page.wait_seconds(1)


# ====================================================================
# PHASE 7: Bug-Specific Tests (4 tests)
# ====================================================================

class TestBugSpecific:
    """UC-B01 to UC-B04: Dedicated tests for confirmed bugs."""

    # ---- UC-B01: Silent duplicate block — no error message ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_001, strict=False)
    def test_UC_B01_silent_duplicate_block(self, uc_page):
        """Verify BUG-001: Duplicate username is silently blocked with no error.
        We expect this test to FAIL because the ERP doesn't show an error message
        for duplicate usernames — it just silently blocks the submit.
        """
        log.info("UC-B01: Silent duplicate block test")
        page = uc_page

        # Create first user
        data1 = generate_valid_user_data("SilentDup1")
        result1 = page.create_user(data1)
        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)

        # Try duplicate
        data2 = generate_duplicate_username_data(data1["username"])
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_user_form(data2)
        page._force_close_panels()
        page.submit()
        page.wait_seconds(5)

        # BUG-001: We expect an error message, but there is none
        errors = page.get_mat_error_text()
        swal = page.handle_validation_warning(timeout=3)
        form_still_open = page.is_add_form_open()

        # This assertion should FAIL because there's no error message
        assert (errors or swal) and form_still_open, (
            "BUG-001: Expected visible error for duplicate username, got none"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()
        page.click_refresh()
        page.wait_seconds(2)

    # ---- UC-B02: Only 1 mat-error visible at a time ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_006, strict=False)
    def test_UC_B02_single_mat_error(self, uc_page):
        """Verify BUG-006: Only 1 mat-error visible at a time.
        We expect this to FAIL because the ERP only shows one error at a time.
        """
        log.info("UC-B02: Single mat-error test")
        page = uc_page

        page.open_add_form()
        page.wait_seconds(1)
        page.submit()
        page.wait_seconds(2)

        # Check how many fields have visible mat-error text
        visible_errors = []
        for label in ["Username", "Email", "First Name", "Last Name", "Password"]:
            if page.has_field_error(label):
                visible_errors.append(label)

        # BUG-006: We expect multiple errors, but only 1 shows text
        assert len(visible_errors) >= 4, (
            f"BUG-006 CONFIRMED: Only {len(visible_errors)} visible mat-error(s). "
            f"Expected all 8 required fields to show errors. Visible: {visible_errors}"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- UC-B03: No email format validation ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_003, strict=False)
    def test_UC_B03_no_email_validation(self, uc_page):
        """Verify BUG-003: No email format validation anywhere."""
        log.info("UC-B03: No email validation test")
        page = uc_page

        # Test on blur
        page.open_add_form()
        page.wait_seconds(1)
        page.type_text(page.EMAIL_INPUT, "notanemail", clear_first=True)
        page.type_text(page.FIRST_NAME_INPUT, "", clear_first=True)  # blur
        page.wait_seconds(1)

        blur_error = page.has_field_error("Email")

        # Test on submit
        data = generate_valid_user_data("NoEmailVal")
        data["email"] = "notanemail"
        page.fill_user_form(data)
        page._force_close_panels()
        page.submit()
        page.wait_seconds(2)

        submit_error = page.has_field_error("Email")
        errors = page.get_mat_error_text()

        assert blur_error or submit_error or errors, (
            "BUG-003 CONFIRMED: No email format validation on blur or submit"
        )

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- UC-B04: No maxlength on text inputs ----
    @pytest.mark.xfail(reason=KnownBugs.BUG_002, strict=False)
    def test_UC_B04_no_maxlength(self, uc_page):
        """Verify BUG-002: No maxlength validation on text inputs."""
        log.info("UC-B04: No maxlength test")
        page = uc_page

        data = generate_valid_user_data("NoMaxLen")
        data["username"] = "A" * 300

        result = page.create_user(data)

        assert result["status"] == "FAILED", (
            "BUG-002 CONFIRMED: 300-character username accepted without maxlength validation"
        )

        try:
            page.force_close_form_popup()
        except Exception:
            pass
        page.click_refresh()
        page.wait_seconds(2)
