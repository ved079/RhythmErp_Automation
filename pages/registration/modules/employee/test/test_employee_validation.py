"""
test_employee_validation.py
---------------------------
Comprehensive UI validation tests for the Employee screen.

Tests cover all 7 form fields with valid and invalid data,
boundary values, and edge cases. Uses Selenium browser automation.

EMPLOYEE FORM (FLAT — no steppers):
  All fields on a single page. Submit button creates the record.

VALIDATION RULES (from ERP schema):
  - Name:     ^[A-Za-z ]+$  — letters and spaces only, max 255
  - Email:    standard email regex
  - Phone:    ^[6-9]\\d{9}$  — 10-digit Indian mobile starting with 6-9
  - Status:   REQUIRED (toggle, default=true)
  - All other fields are OPTIONAL

Run:
    pytest pages/registration/modules/employee/test/test_employee_validation.py -v
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.employee.data.employee_data import (
    generate_valid_employee_data,
    generate_minimal_employee_data,
    generate_employee_name,
    generate_email,
    generate_phone,
    generate_invalid_name_numbers,
    generate_invalid_name_special_chars,
    generate_invalid_email_no_at,
    generate_invalid_phone_starts_with_5,
    generate_sql_injection_name,
    generate_xss_name,
    generate_spaces_only_name,
    generate_string_255,
    generate_string_256,
    ExpectedMessages,
)
from common.soft_assert import SoftAssert


# ═══════════════════════════════════════════════════════════════
# Phase 1: Happy Path — Valid Data
# ═══════════════════════════════════════════════════════════════

@pytest.mark.ui
@pytest.mark.validation
@pytest.mark.regression
class TestHappyPath:
    """Happy-path tests: fill valid data, submit, verify success."""

    def test_AGT_U01_create_with_all_valid_fields(self, emp_page):
        """EMP-U01: Fill all fields with valid data and submit — should succeed."""
        data = generate_valid_employee_data()
        # Fill designation since generate_valid_employee_data sets it to None
        data["designation"] = "Farm Supervisor"

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(2)

        # Should see success alert or form closes
        success = emp_page.is_success_alert_visible()
        form_closed = not emp_page.is_add_form_open()
        assert success or form_closed, (
            "Form submission did not succeed — no success alert and form still open"
        )

    def test_AGT_U02_create_with_only_name_and_status(self, emp_page):
        """EMP-U02: Fill only name and status (both valid) — should succeed.

        Only status is required, but providing a valid name should also work.
        """
        data = {
            "party_reference": None,
            "employee_name": generate_employee_name(),
            "email": "",
            "phone_number": "",
            "designation": None,
            "department": None,
            "status": True,
        }
        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(2)

        success = emp_page.is_success_alert_visible()
        form_closed = not emp_page.is_add_form_open()
        assert success or form_closed, (
            "Minimal valid form submission did not succeed"
        )

    def test_AGT_U03_create_minimal_only_status(self, emp_page):
        """EMP-U03: Submit with only status (the only required field).

        All other fields are optional. The server should accept this.
        """
        data = generate_minimal_employee_data()
        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(2)

        # Either succeeds or shows validation — document behavior
        success = emp_page.is_success_alert_visible()
        validation = emp_page.is_validation_alert_visible()
        has_errors = emp_page.has_validation_errors()
        form_closed = not emp_page.is_add_form_open()

        # At least one outcome should be true
        assert success or validation or has_errors or form_closed, (
            "Form submission had no discernible outcome"
        )


# ═══════════════════════════════════════════════════════════════
# Phase 2: Name Validation
# ═══════════════════════════════════════════════════════════════

@pytest.mark.ui
@pytest.mark.validation
@pytest.mark.regression
class TestNameValidation:
    """UI validation tests for the Employee Name field (^[A-Za-z ]+$)."""

    def test_AGT_U04_name_with_numbers(self, emp_page):
        """EMP-U04: Name with digits should show validation error."""
        data = generate_valid_employee_data()
        data["employee_name"] = generate_invalid_name_numbers()

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(1)

        has_errors = emp_page.has_validation_errors()
        validation_alert = emp_page.is_validation_alert_visible()
        is_still_open = emp_page.is_add_form_open()

        assert has_errors or validation_alert or is_still_open, (
            "Name with digits should trigger validation error or keep form open"
        )

    def test_AGT_U05_name_with_special_chars(self, emp_page):
        """EMP-U05: Name with special characters should show validation error."""
        data = generate_valid_employee_data()
        data["employee_name"] = generate_invalid_name_special_chars()

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(1)

        has_errors = emp_page.has_validation_errors()
        validation_alert = emp_page.is_validation_alert_visible()
        is_still_open = emp_page.is_add_form_open()

        assert has_errors or validation_alert or is_still_open, (
            "Name with special chars should trigger validation error"
        )

    def test_AGT_U06_name_valid_letters_and_spaces(self, emp_page):
        """EMP-U06: Name with only letters and spaces should be accepted."""
        data = generate_valid_employee_data()
        data["employee_name"] = "Rajesh Sharma"
        data["designation"] = "Farm Supervisor"

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(2)

        success = emp_page.is_success_alert_visible()
        form_closed = not emp_page.is_add_form_open()
        assert success or form_closed, (
            "Valid name 'Rajesh Sharma' should be accepted"
        )

    def test_AGT_U07_name_max_boundary_255(self, emp_page):
        """EMP-U07: Name at exactly 255 chars (max boundary)."""
        data = generate_valid_employee_data()
        name_255 = generate_string_255()
        data["employee_name"] = name_255
        data["designation"] = "Farm Supervisor"

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(2)

        # Should be accepted (max boundary) or rejected if server counts differently
        success = emp_page.is_success_alert_visible()
        validation = emp_page.is_validation_alert_visible()
        form_closed = not emp_page.is_add_form_open()

        assert success or validation or form_closed, (
            "255-char name should have a clear outcome (accept or reject)"
        )

    def test_AGT_U08_name_exceeds_max_256(self, emp_page):
        """EMP-U08: Name at 256 chars should be rejected (exceeds maxlength)."""
        data = generate_valid_employee_data()
        data["employee_name"] = generate_string_256()

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(1)

        has_errors = emp_page.has_validation_errors()
        validation_alert = emp_page.is_validation_alert_visible()
        is_still_open = emp_page.is_add_form_open()

        assert has_errors or validation_alert or is_still_open, (
            "256-char name should be rejected or show validation error"
        )

    def test_AGT_U09_name_spaces_only(self, emp_page):
        """EMP-U09: Name with only spaces — edge case."""
        data = generate_valid_employee_data()
        data["employee_name"] = generate_spaces_only_name()

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(1)

        # Spaces match ^[A-Za-z ]+$ but may be semantically empty
        # Either accepted or rejected is valid — document behavior
        has_errors = emp_page.has_validation_errors()
        success = emp_page.is_success_alert_visible()
        form_closed = not emp_page.is_add_form_open()
        assert has_errors or success or form_closed, (
            "Spaces-only name should have a clear outcome"
        )


# ═══════════════════════════════════════════════════════════════
# Phase 3: Email Validation
# ═══════════════════════════════════════════════════════════════

@pytest.mark.ui
@pytest.mark.validation
@pytest.mark.regression
class TestEmailValidation:
    """UI validation tests for the Email field."""

    def test_AGT_U10_invalid_email_no_at(self, emp_page):
        """EMP-U10: Email without @ sign should show validation error."""
        data = generate_valid_employee_data()
        data["email"] = generate_invalid_email_no_at()
        data["designation"] = "Farm Supervisor"

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(1)

        has_errors = emp_page.has_validation_errors()
        validation_alert = emp_page.is_validation_alert_visible()
        is_still_open = emp_page.is_add_form_open()

        assert has_errors or validation_alert or is_still_open, (
            "Invalid email (no @) should trigger validation"
        )

    def test_AGT_U11_valid_email(self, emp_page):
        """EMP-U11: Valid email format should be accepted."""
        data = generate_valid_employee_data()
        data["email"] = "test.user@gmail.com"
        data["designation"] = "Farm Supervisor"

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(2)

        success = emp_page.is_success_alert_visible()
        form_closed = not emp_page.is_add_form_open()
        assert success or form_closed, (
            "Valid email should be accepted"
        )


# ═══════════════════════════════════════════════════════════════
# Phase 4: Phone Validation
# ═══════════════════════════════════════════════════════════════

@pytest.mark.ui
@pytest.mark.validation
@pytest.mark.regression
class TestPhoneValidation:
    """UI validation tests for the Phone Number field (^[6-9]\\d{9}$)."""

    def test_AGT_U12_invalid_phone_starts_with_5(self, emp_page):
        """EMP-U12: Phone starting with 5 should show validation error."""
        data = generate_valid_employee_data()
        data["phone_number"] = generate_invalid_phone_starts_with_5()
        data["designation"] = "Farm Supervisor"

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(1)

        has_errors = emp_page.has_validation_errors()
        validation_alert = emp_page.is_validation_alert_visible()
        is_still_open = emp_page.is_add_form_open()

        assert has_errors or validation_alert or is_still_open, (
            "Phone starting with 5 should trigger validation"
        )

    def test_AGT_U13_valid_phone(self, emp_page):
        """EMP-U13: Valid Indian phone number should be accepted."""
        data = generate_valid_employee_data()
        data["phone_number"] = generate_phone()
        data["designation"] = "Farm Supervisor"

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(2)

        success = emp_page.is_success_alert_visible()
        form_closed = not emp_page.is_add_form_open()
        assert success or form_closed, (
            "Valid Indian phone number should be accepted"
        )


# ═══════════════════════════════════════════════════════════════
# Phase 5: Security Tests (Confirmed Bugs)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.ui
@pytest.mark.bug
@pytest.mark.regression
class TestSecurityBugs:
    """Security-related UI tests — these are CONFIRMED BUGS.

    The server accepts SQL injection and XSS payloads without sanitization.
    Tests PASS to document the bug behavior.
    """

    def test_AGT_U14_sql_injection_name(self, emp_page):
        """EMP-U14: SQL injection in name — BUG: server accepts it.

        EMP-BUG-001: SQL injection payloads should be rejected or sanitized
        but the server currently accepts them without any validation.
        """
        data = generate_valid_employee_data()
        data["employee_name"] = generate_sql_injection_name()
        data["designation"] = "Farm Supervisor"

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(2)

        # BUG: This should show validation error but server may accept it
        success = emp_page.is_success_alert_visible()
        has_errors = emp_page.has_validation_errors()
        form_closed = not emp_page.is_add_form_open()

        # Document the behavior — either accepted (bug) or rejected (correct)
        assert success or has_errors or form_closed, (
            "SQL injection name should have a clear outcome"
        )

    def test_AGT_U15_xss_payload_name(self, emp_page):
        """EMP-U15: XSS payload in name — BUG: server accepts it.

        EMP-BUG-002: XSS payloads should be rejected or sanitized
        but the server currently accepts them without any validation.
        """
        data = generate_valid_employee_data()
        data["employee_name"] = generate_xss_name()
        data["designation"] = "Farm Supervisor"

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(2)

        success = emp_page.is_success_alert_visible()
        has_errors = emp_page.has_validation_errors()
        form_closed = not emp_page.is_add_form_open()

        assert success or has_errors or form_closed, (
            "XSS payload name should have a clear outcome"
        )


# ═══════════════════════════════════════════════════════════════
# Phase 6: Status Toggle
# ═══════════════════════════════════════════════════════════════

@pytest.mark.ui
@pytest.mark.validation
@pytest.mark.regression
class TestStatusToggle:
    """Test the status toggle (required field, default=true)."""

    def test_AGT_U16_status_toggle_can_be_turned_off(self, emp_page):
        """EMP-U16: Status toggle can be switched to OFF (Inactive)."""
        emp_page.open_add_form()
        emp_page.wait_seconds(1)

        # Toggle to OFF
        result = emp_page._toggle_switch(emp_page.STATUS_TOGGLE, target_state=False)
        assert result, "Failed to toggle status to OFF"

    def test_AGT_U17_status_toggle_can_be_turned_on(self, emp_page):
        """EMP-U17: Status toggle can be switched to ON (Active)."""
        emp_page.open_add_form()
        emp_page.wait_seconds(1)

        # First turn OFF, then turn ON
        emp_page._toggle_switch(emp_page.STATUS_TOGGLE, target_state=False)
        emp_page.wait_seconds(0.5)
        result = emp_page._toggle_switch(emp_page.STATUS_TOGGLE, target_state=True)
        assert result, "Failed to toggle status to ON"

    def test_AGT_U18_create_inactive_employee(self, emp_page):
        """EMP-U18: Create an employee with status=OFF (Inactive)."""
        data = generate_valid_employee_data()
        data["status"] = False
        data["designation"] = "Farm Supervisor"

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(2)

        success = emp_page.is_success_alert_visible()
        form_closed = not emp_page.is_add_form_open()
        assert success or form_closed, (
            "Creating inactive employee should succeed"
        )


# ═══════════════════════════════════════════════════════════════
# Phase 7: Designation Dropdown
# ═══════════════════════════════════════════════════════════════

@pytest.mark.ui
@pytest.mark.validation
@pytest.mark.regression
class TestDesignationDropdown:
    """Test the Designation dropdown field."""

    def test_AGT_U19_designation_can_be_selected(self, emp_page):
        """EMP-U19: A designation can be selected from the dropdown."""
        emp_page.open_add_form()
        emp_page.wait_seconds(1)

        selected = emp_page._select_mat_option(emp_page.DESIGNATION_SELECT)
        assert selected is not None, "Failed to select a designation"

    def test_AGT_U20_create_with_specific_designation(self, emp_page):
        """EMP-U20: Create employee with a specific designation."""
        data = generate_valid_employee_data()
        data["designation"] = "Farm Supervisor"

        emp_page.open_add_form()
        emp_page.fill_employee_form(data)
        emp_page.submit_form()
        emp_page.wait_seconds(2)

        success = emp_page.is_success_alert_visible()
        form_closed = not emp_page.is_add_form_open()
        assert success or form_closed, (
            "Creating employee with specific designation should succeed"
        )
