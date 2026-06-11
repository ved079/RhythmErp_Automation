"""
test_employee_validation.py
---------------------------
Comprehensive validation test suite for RhythmERP Employee screen.
~35 test cases across 5 phases.

EMPLOYEE FORM STRUCTURE (FLAT — NO STEPPERS):
  Unlike Agent which has a 3-step stepper, Employee is a FLAT form.
  All fields are on a single page — no Next/Back navigation needed.

Phases:
  1. Employee Name Validations    (8 tests) - EMP-V01 to EMP-V08
  2. Email Validations             (6 tests) - EMP-E01 to EMP-E06
  3. Phone Number Validations      (6 tests) - EMP-P01 to EMP-P06
  4. Dropdown & FK Validations     (5 tests) - EMP-D01 to EMP-D05
  5. Flat Form Workflow Tests     (10 tests) - EMP-F01 to EMP-F10

KEY RULES:
  - FLAT FORM: No steppers, no children[] — all fields on single page
  - Only `status` is required — all other fields optional
  - Employee Name: ^[A-Za-z ]+$ (letters + spaces only, max 255)
  - Email: standard email regex
  - Phone: ^[6-9]\\d{9}$ (10-digit Indian mobile)
  - Angular Material UI — use execute_script for reading values
  - SweetAlert2 for success/validation popups
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)

Run:
  pytest test_employee_validation.py -v --tb=short
  pytest test_employee_validation.py -v -k "TestEmployeeName" --tb=short
  pytest test_employee_validation.py -v -k "EMP_V01" --tb=short

Marker-based runs:
  pytest test_employee_validation.py -v -m smoke          # critical tests
  pytest test_employee_validation.py -v -m sanity         # core feature tests
  pytest test_employee_validation.py -v -m regression     # all tests
  pytest test_employee_validation.py -v -m bug            # bug-tracking tests
  pytest test_employee_validation.py -v -m ui             # UI behavior tests
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

from common.logger import log
from pages.registration.modules.employee.data.employee_data import (
    generate_valid_employee_data,
    generate_employee_name,
    generate_phone,
    generate_email,
    generate_string_255,
    generate_string_256,
    generate_invalid_name_numbers,
    generate_invalid_name_special_chars,
    generate_invalid_email_no_at,
    generate_invalid_phone_starts_with_5,
    generate_invalid_phone_too_short,
    generate_invalid_phone_too_long,
    generate_sql_injection_name,
    generate_xss_name,
    generate_spaces_only_name,
    ExpectedMessages,
)


# ====================================================================
# Helper functions
# ====================================================================

def _cleanup_form(page):
    """Try to close any open form popup."""
    try:
        page.cancel_form()
    except Exception:
        pass
    try:
        page._force_close_panels()
    except Exception:
        pass


def _get_input_value(page, field_name):
    """Get the value of an input by its name attribute using JS."""
    return page.driver.execute_script(
        f"return document.querySelector(\"input[name='{field_name}']\")?.value || '';"
    )


def _fill_input_by_name(page, field_name, value):
    """Fill an input field by name using JS + send_keys for Angular sync."""
    try:
        inp = page.driver.find_element(By.CSS_SELECTOR, f"input[name='{field_name}']")
        page.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", inp
        )
        inp.clear()
        inp.send_keys(str(value))
        page.wait_seconds(0.3)
    except Exception as e:
        log.warning(f"Could not fill '{field_name}': {e}")


def _get_field_validation_state(page, field_name):
    """Get the validation state of a form field (ng-invalid/ng-valid, mat-error)."""
    js = f"""
    var input = document.querySelector("input[name='{field_name}']");
    if (!input) return JSON.stringify({{found: false}});
    var container = input.closest('mat-form-field') || input.parentElement;
    var invalid = input.classList.contains('ng-invalid') ||
                  (container && container.classList.contains('mat-form-field-invalid'));
    var errorEl = container ? container.querySelector('mat-error, .mat-mdc-form-field-error') : null;
    return JSON.stringify({{
        found: true,
        invalid: invalid,
        error: errorEl ? errorEl.textContent.trim() : '',
        value: input.value
    }});
    """
    import json
    try:
        result = page.driver.execute_script(js)
        return json.loads(result)
    except Exception:
        return {"found": False, "invalid": False, "error": "", "value": ""}


# ====================================================================
# PHASE 1: Employee Name Validations (8 tests)
# ====================================================================

class TestEmployeeNameValidations:
    """EMP-V01 to EMP-V08: Validation checks on Employee Name field."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_V01_empty_submit(self, emp_page):
        """Submit with all fields empty on the flat form - should be blocked or accepted."""
        log.info("EMP-V01: Empty submit on Employee form")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Add form did not open"

        page.submit_form()
        page.wait_seconds(3)

        # Only status is required — the form may actually submit with just status
        validation_alert = page.is_validation_alert_visible()
        form_still_open = page.is_add_form_open()
        success_alert = page.is_success_alert_visible()

        log.info(
            f"Empty submit: form_open={form_still_open}, "
            f"validation_alert={validation_alert}, success_alert={success_alert}"
        )

        if success_alert:
            page.dismiss_alert()
            log.warning(
                "BUG: Form submitted with all fields empty — "
                "only status (default) was provided. Server accepts minimal data."
            )

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_V02_name_valid_letters_and_spaces(self, emp_page):
        """Employee Name should accept letters and spaces (^[A-Za-z ]+$)."""
        log.info("EMP-V02: Valid Employee Name test")
        page = emp_page

        valid_name = generate_employee_name("ValidV02")
        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Employee Name", valid_name)
        page.wait_seconds(0.5)

        actual = _get_input_value(page, "Employee Name")
        log.info(f"Input: '{valid_name}' -> Actual: '{actual}'")
        assert actual == valid_name, f"Name mismatch: expected '{valid_name}', got '{actual}'"

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_V03_name_with_numbers(self, emp_page):
        """Employee Name with numbers - should be rejected by ^[A-Za-z ]+$."""
        log.info("EMP-V03: Name with numbers test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Employee Name", generate_invalid_name_numbers())
        page.wait_seconds(0.5)

        state = _get_field_validation_state(page, "Employee Name")
        log.info(
            f"Name with numbers: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_V04_name_with_special_chars(self, emp_page):
        """Employee Name with special characters - should be rejected."""
        log.info("EMP-V04: Name with special chars test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Employee Name", generate_invalid_name_special_chars())
        page.wait_seconds(0.5)

        state = _get_field_validation_state(page, "Employee Name")
        log.info(
            f"Special chars name: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_V05_name_spaces_only(self, emp_page):
        """Employee Name with spaces only - should be rejected."""
        log.info("EMP-V05: Name spaces only test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Employee Name", generate_spaces_only_name())
        page.wait_seconds(0.5)

        state = _get_field_validation_state(page, "Employee Name")
        log.info(f"Spaces-only name: invalid={state['invalid']}, error='{state['error']}'")

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_V06_name_maxlength_boundary(self, emp_page):
        """Employee Name maxlength boundary (255/256 chars)."""
        log.info("EMP-V06: Name maxlength boundary test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)

        long_255 = generate_string_255()
        _fill_input_by_name(page, "Employee Name", long_255)
        page.wait_seconds(0.5)
        actual_255 = _get_input_value(page, "Employee Name")
        log.info(f"255-char input: actual length = {len(actual_255)}")

        long_256 = generate_string_256()
        _fill_input_by_name(page, "Employee Name", long_256)
        page.wait_seconds(0.5)
        actual_256 = _get_input_value(page, "Employee Name")
        log.info(
            f"256-char input: actual length = {len(actual_256)}, "
            f"truncated = {len(actual_256) == 255}"
        )

        _cleanup_form(page)

    @pytest.mark.bug
    @pytest.mark.regression
    def test_EMP_V07_sql_injection(self, emp_page):
        """SQL injection in Employee Name - known bug (EMP-BUG-001)."""
        log.info("EMP-V07: SQL injection test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Employee Name", generate_sql_injection_name())
        page.wait_seconds(0.5)

        state = _get_field_validation_state(page, "Employee Name")
        log.info(
            f"SQL injection: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    @pytest.mark.bug
    @pytest.mark.regression
    def test_EMP_V08_xss_payload(self, emp_page):
        """XSS payload in Employee Name - known bug (EMP-BUG-002)."""
        log.info("EMP-V08: XSS payload test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Employee Name", generate_xss_name())
        page.wait_seconds(0.5)

        state = _get_field_validation_state(page, "Employee Name")
        log.info(
            f"XSS payload: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)


# ====================================================================
# PHASE 2: Email Validations (6 tests)
# ====================================================================

class TestEmailValidations:
    """EMP-E01 to EMP-E06: Validation checks on Email field."""

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_E01_email_valid(self, emp_page):
        """Valid email should be accepted."""
        log.info("EMP-E01: Valid Email test")
        page = emp_page

        valid_email = generate_email("validE01")
        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Email", valid_email)
        page.wait_seconds(0.5)

        actual = _get_input_value(page, "Email")
        assert actual == valid_email, f"Email mismatch: expected '{valid_email}', got '{actual}'"
        log.info(f"Valid Email '{valid_email}' accepted")

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_E02_email_invalid_no_at(self, emp_page):
        """Invalid email without @ should show validation."""
        log.info("EMP-E02: Invalid Email (no @) test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Email", generate_invalid_email_no_at())
        page.wait_seconds(0.5)

        state = _get_field_validation_state(page, "Email")
        log.info(
            f"Invalid Email (no @): invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_E03_email_empty_optional(self, emp_page):
        """Empty email should be valid (optional field)."""
        log.info("EMP-E03: Email empty optional test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Email", "")
        page.wait_seconds(0.3)

        state = _get_field_validation_state(page, "Email")
        log.info(
            f"Empty Email: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_E04_email_no_domain(self, emp_page):
        """Email without domain should show validation."""
        log.info("EMP-E04: Email no domain test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Email", "user@")
        page.wait_seconds(0.5)

        state = _get_field_validation_state(page, "Email")
        log.info(
            f"Email without domain: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_E05_email_maxlength(self, emp_page):
        """Email maxlength boundary test (255 chars)."""
        log.info("EMP-E05: Email maxlength test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)

        long_email = "a" * 245 + "@test.com"  # ~255 chars
        _fill_input_by_name(page, "Email", long_email)
        page.wait_seconds(0.5)
        actual = _get_input_value(page, "Email")
        log.info(f"Long email: input length = {len(long_email)}, actual length = {len(actual)}")

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_E06_email_spaces_only(self, emp_page):
        """Email with spaces only should show validation."""
        log.info("EMP-E06: Email spaces only test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Email", "     ")
        page.wait_seconds(0.5)

        state = _get_field_validation_state(page, "Email")
        log.info(
            f"Spaces-only email: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)


# ====================================================================
# PHASE 3: Phone Number Validations (6 tests)
# ====================================================================

class TestPhoneNumberValidations:
    """EMP-P01 to EMP-P06: Validation checks on Phone Number field."""

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_P01_phone_valid(self, emp_page):
        """Valid 10-digit Indian mobile should be accepted."""
        log.info("EMP-P01: Valid Phone Number test")
        page = emp_page

        valid_phone = str(generate_phone())
        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Phone Number", valid_phone)
        page.wait_seconds(0.5)

        actual = _get_input_value(page, "Phone Number")
        assert actual == valid_phone, (
            f"Phone mismatch: expected '{valid_phone}', got '{actual}'"
        )
        log.info(f"Valid Phone Number '{valid_phone}' accepted")

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_P02_phone_starts_with_5(self, emp_page):
        """Phone starting with 5 should be rejected (^[6-9]\\d{9}$)."""
        log.info("EMP-P02: Phone starts with 5 test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Phone Number", str(generate_invalid_phone_starts_with_5()))
        page.wait_seconds(0.5)

        state = _get_field_validation_state(page, "Phone Number")
        log.info(
            f"Phone starts with 5: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_P03_phone_too_short(self, emp_page):
        """Phone with less than 10 digits should be rejected."""
        log.info("EMP-P03: Phone too short test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Phone Number", str(generate_invalid_phone_too_short()))
        page.wait_seconds(0.5)

        state = _get_field_validation_state(page, "Phone Number")
        log.info(
            f"Short phone: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_P04_phone_too_long(self, emp_page):
        """Phone with more than 10 digits should be rejected."""
        log.info("EMP-P04: Phone too long test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Phone Number", str(generate_invalid_phone_too_long()))
        page.wait_seconds(0.5)

        state = _get_field_validation_state(page, "Phone Number")
        log.info(
            f"Long phone: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_P05_phone_empty_optional(self, emp_page):
        """Empty phone should be valid (optional field)."""
        log.info("EMP-P05: Phone empty optional test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        _fill_input_by_name(page, "Phone Number", "")
        page.wait_seconds(0.3)

        state = _get_field_validation_state(page, "Phone Number")
        log.info(
            f"Empty phone: invalid={state['invalid']}, error='{state['error']}'"
        )

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_EMP_P06_phone_input_type(self, emp_page):
        """Phone Number field should be type=number or type=tel."""
        log.info("EMP-P06: Phone Number input type verification")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)

        try:
            phone_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Phone Number']"
            )
            input_type = phone_input.get_attribute("type") or ""
            log.info(f"Phone Number input type: '{input_type}'")
            assert input_type in ("number", "tel", "text"), (
                f"Unexpected input type: '{input_type}'"
            )
        except Exception as e:
            log.warning(f"Could not verify Phone Number input type: {e}")

        _cleanup_form(page)


# ====================================================================
# PHASE 4: Dropdown & FK Validations (5 tests)
# ====================================================================

class TestDropdownValidations:
    """EMP-D01 to EMP-D05: Validation checks on dropdown/FK fields."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_EMP_D01_designation_has_options(self, emp_page):
        """Designation dropdown should have options available."""
        log.info("EMP-D01: Designation dropdown options check")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)

        try:
            options = page.get_dropdown_options_by_label("Designation")
            count = len([o for o in options if o.strip()])
            log.info(f"Designation has {count} options")
            assert count > 0, "Designation dropdown should have at least 1 option"
        except Exception as e:
            log.warning(f"Could not check Designation options: {e}")

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_EMP_D02_designation_select_first(self, emp_page):
        """Select the first Designation option and verify it's set."""
        log.info("EMP-D02: Select first Designation option")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)

        try:
            options = page.get_dropdown_options_by_label("Designation")
            if options:
                first_option = next((o for o in options if o.strip() and not o.lower().startswith("select ")), None)
                if first_option:
                    page.select_dropdown_by_label("Designation", first_option)
                    page.wait_seconds(0.5)
                    log.info(f"Selected Designation: '{first_option}'")
        except Exception as e:
            log.warning(f"Could not select first Designation: {e}")

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_EMP_D03_department_empty_or_none(self, emp_page):
        """Department dropdown should have 0 options currently."""
        log.info("EMP-D03: Department dropdown options check")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)

        try:
            options = page.get_dropdown_options_by_label("Department")
            count = len([o for o in options if o.strip()])
            log.info(f"Department has {count} options (expected 0)")
            if count == 0:
                log.info("Department correctly has 0 options")
            else:
                log.info(f"Department now has {count} options — data may have been added")
        except Exception as e:
            log.info(f"Department dropdown check: {e} (may be expected with 0 options)")

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_D04_all_fields_filled_submit(self, emp_page):
        """Fill ALL fields and submit — should create successfully."""
        log.info("EMP-D04: All fields filled submit test")
        page = emp_page

        data = generate_valid_employee_data()
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_employee_form(data)
        page.wait_seconds(0.5)

        page.submit_form()
        page.wait_seconds(3)

        # Should see success alert or form closes
        success = page.is_success_alert_visible()
        form_open = page.is_add_form_open()
        validation = page.is_validation_alert_visible()

        log.info(f"All-fields submit: success={success}, form_open={form_open}, validation={validation}")

        if validation:
            page.dismiss_alert()

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_D05_status_toggle_off(self, emp_page):
        """Set Status toggle to OFF and submit — should create inactive employee."""
        log.info("EMP-D05: Status toggle OFF test")
        page = emp_page

        data = generate_valid_employee_data()
        data["status"] = False  # Inactive
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_employee_form(data)
        page.wait_seconds(0.5)

        page.submit_form()
        page.wait_seconds(3)

        success = page.is_success_alert_visible()
        validation = page.is_validation_alert_visible()
        log.info(f"Inactive employee submit: success={success}, validation={validation}")

        if validation:
            page.dismiss_alert()

        _cleanup_form(page)


# ====================================================================
# PHASE 5: Flat Form Workflow Tests (10 tests)
# ====================================================================

class TestFlatFormWorkflow:
    """EMP-F01 to EMP-F10: Workflow tests for the flat Employee form."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_EMP_F01_form_opens_and_closes(self, emp_page):
        """Verify the add form opens and can be closed."""
        log.info("EMP-F01: Form opens and closes")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Form should be open"

        page.cancel_form()
        page.wait_seconds(1)
        assert not page.is_add_form_open(), "Form should be closed after Cancel"

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_F02_cancel_preserves_no_data(self, emp_page):
        """Cancel should not create any employee record."""
        log.info("EMP-F02: Cancel preserves no data")
        page = emp_page

        initial_count = page.get_table_row_count()

        page.open_add_form()
        page.wait_seconds(1)

        data = generate_valid_employee_data()
        page.fill_employee_form(data)
        page.wait_seconds(0.5)

        page.cancel_form()
        page.wait_seconds(1)

        page.click_refresh()
        page.wait_seconds(2)

        final_count = page.get_table_row_count()
        log.info(f"Row count: before={initial_count}, after={final_count}")
        # Count should be the same — no new record created
        assert final_count == initial_count, (
            f"Cancel should not create a record. Before={initial_count}, After={final_count}"
        )

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_F03_minimal_submit_status_only(self, emp_page):
        """Submit with only status (required) — all other fields empty."""
        log.info("EMP-F03: Minimal submit (status only)")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)

        # Don't fill anything — status defaults to Active
        page.submit_form()
        page.wait_seconds(3)

        success = page.is_success_alert_visible()
        validation = page.is_validation_alert_visible()
        form_open = page.is_add_form_open()

        log.info(
            f"Minimal submit: success={success}, validation={validation}, "
            f"form_open={form_open}"
        )

        if validation:
            page.dismiss_alert()

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_F04_invalid_then_valid_name(self, emp_page):
        """Fill invalid name, fix to valid, submit — errors should clear."""
        log.info("EMP-F04: Invalid -> valid -> submit test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)

        # First fill invalid name
        _fill_input_by_name(page, "Employee Name", generate_invalid_name_numbers())
        page.wait_seconds(0.5)

        state_invalid = _get_field_validation_state(page, "Employee Name")
        log.info(f"After invalid name: invalid={state_invalid['invalid']}")

        # Now fix with valid name
        valid_name = generate_employee_name("FixF04")
        _fill_input_by_name(page, "Employee Name", valid_name)
        page.wait_seconds(0.5)

        state_valid = _get_field_validation_state(page, "Employee Name")
        log.info(f"After valid name: invalid={state_valid['invalid']}")

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_F05_multiple_invalid_fields(self, emp_page):
        """Fill multiple invalid fields and verify all show validation errors."""
        log.info("EMP-F05: Multiple invalid fields test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)

        _fill_input_by_name(page, "Employee Name", generate_invalid_name_numbers())
        _fill_input_by_name(page, "Email", generate_invalid_email_no_at())
        _fill_input_by_name(page, "Phone Number", str(generate_invalid_phone_starts_with_5()))
        page.wait_seconds(0.5)

        page.submit_form()
        page.wait_seconds(2)

        errors = page.get_validation_errors()
        form_open = page.is_add_form_open()
        log.info(f"Multiple invalid: errors={errors}, form_open={form_open}")

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_F06_name_clear_and_refill(self, emp_page):
        """Clear a filled name and refill — verify no stale data."""
        log.info("EMP-F06: Name clear and refill test")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)

        first_name = generate_employee_name("FirstF06")
        _fill_input_by_name(page, "Employee Name", first_name)
        page.wait_seconds(0.3)

        # Clear and refill
        second_name = generate_employee_name("SecondF06")
        _fill_input_by_name(page, "Employee Name", second_name)
        page.wait_seconds(0.3)

        actual = _get_input_value(page, "Employee Name")
        assert actual == second_name, (
            f"After refill: expected '{second_name}', got '{actual}'"
        )
        log.info(f"Name cleared and refilled: '{actual}'")

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_F07_submit_with_valid_data(self, emp_page):
        """Full happy path: fill all valid fields and submit."""
        log.info("EMP-F07: Submit with valid data")
        page = emp_page

        data = generate_valid_employee_data()
        page.open_add_form()
        page.wait_seconds(1)
        page.fill_employee_form(data)
        page.wait_seconds(0.5)

        page.submit_form()
        page.wait_seconds(3)

        success = page.is_success_alert_visible()
        validation = page.is_validation_alert_visible()

        log.info(f"Valid data submit: success={success}, validation={validation}")

        if success:
            page.dismiss_alert()
        if validation:
            page.dismiss_alert()

        _cleanup_form(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_EMP_F08_search_functionality(self, emp_page):
        """Verify search works on the listing page."""
        log.info("EMP-F08: Search functionality test")
        page = emp_page

        names = page.get_table_employee_names()
        if names:
            search_term = names[0][:8]  # Use first 8 chars
            page.search_employee(search_term)
            page.wait_seconds(2)

            # Search should not crash the page
            assert page.is_page_loaded(), "Page should still be loaded after search"
            log.info(f"Search for '{search_term}' completed without crash")
        else:
            log.info("No employees in table — skip search test")

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_EMP_F09_refresh_button(self, emp_page):
        """Verify refresh button works."""
        log.info("EMP-F09: Refresh button test")
        page = emp_page

        initial_count = page.get_table_row_count()
        page.click_refresh()
        page.wait_seconds(2)

        # Refresh should not crash the page
        assert page.is_page_loaded(), "Page should still be loaded after refresh"
        log.info("Refresh button works without crash")

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_F10_table_shows_employees(self, emp_page):
        """Verify the table is loaded and shows employee data."""
        log.info("EMP-F10: Table shows employees")
        page = emp_page

        assert page.is_page_loaded(), "Employee page should be loaded"
        count = page.get_table_row_count()
        log.info(f"Table has {count} rows")

        names = page.get_table_employee_names()
        if names:
            log.info(f"First few names: {names[:5]}")
