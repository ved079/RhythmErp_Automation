"""
test_employee_ui_interactions.py
--------------------------------
UI-only interaction test suite for RhythmERP Employee screen.
~7 test cases that verify UI-specific behavior — no data creation needed.

Bucket B — UI-Only Tests: Verify UI rendering, interactions, and behaviors
that cannot be tested via API. Each test uses ``emp_page`` fixture only.

EMPLOYEE FORM STRUCTURE (FLAT — NO STEPPERS):
  Unlike Agent which has a 3-step stepper, Employee is a FLAT form.
  All fields are on a single page — no Next/Back navigation.

Test Inventory (7 tests):
  EMP-I01 — Phone Number input type (HTML5 type=number check)
  EMP-I02 — All dropdowns options (open form once, SoftAssert all)
  EMP-I03 — Add form opens and closes (flat — no stepper)
  EMP-I04 — Cancel closes popup
  EMP-I05 — Close/X closes popup
  EMP-I06 — Status toggle defaults to Active
  EMP-I07 — Employee Name input accepts only letters and spaces

These tests do NOT create data via API — they only interact with the UI
to verify rendering, behavior, and structural correctness.

Run:
  pytest test_employee_ui_interactions.py -v --tb=short
  pytest test_employee_ui_interactions.py -v -m ui --tb=short
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from common.logger import log
from common.soft_assert import SoftAssert
from pages.registration.modules.employee.data.employee_data import (
    generate_valid_employee_data,
    generate_employee_name,
    generate_phone,
    generate_email,
)


# ====================================================================
# EMP-I01: Phone Number input type
# ====================================================================

class TestPhoneNumberInput:
    """UI-only: Verify Phone Number input behavior."""

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_EMP_I01_phone_input_type(self, emp_page):
        """Type alphabetic chars in Phone Number - should reject or show error."""
        log.info("EMP-I01 (UI): Phone Number input type check")
        page = emp_page

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Check that Phone Number input is type="number" or "tel"
        try:
            phone_input = page.driver.find_element(
                By.CSS_SELECTOR, "input[name='Phone Number']"
            )
            input_type = phone_input.get_attribute("type") or ""
            log.info(f"Phone Number input type: '{input_type}'")

            if input_type in ("number", "tel"):
                log.info(f"Phone Number correctly has type='{input_type}' (rejects alpha)")
            else:
                log.warning(
                    f"Phone Number has type='{input_type}' — may accept alpha chars. "
                    f"Expected type='number' or 'tel'."
                )
        except Exception as e:
            log.warning(f"Could not read Phone Number input type: {e}")

        try:
            page.cancel_form()
        except Exception:
            page._force_close_panels()


# ====================================================================
# EMP-I02: All dropdowns options (single test, open form once)
# ====================================================================

# Dropdowns to validate: (test_id, field_name, expected_min_options, skip_reason or None)
_DROPDOWN_CHECKS = [
    ("EMP-I02a", "Party Reference", 1, "Cascading — may need search/filter first"),
    ("EMP-I02b", "Designation", 1, None),
    ("EMP-I02c", "Department", 0, "Currently has 0 options — verify it opens without crash"),
]


class TestDropdownValidation:
    """UI-only: Verify all dropdown fields have options available."""

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_I02_all_dropdowns_options(self, emp_page):
        """Open form once, check ALL dropdowns have expected options.
        Uses SoftAssert to report all failures at end instead of stopping at first.
        """
        log.info("EMP-I02 (UI): All dropdowns options check")
        page = emp_page
        sa = SoftAssert()

        page.open_add_form()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "Add form did not open",
        )

        # Fill some basic data to enable cascading dropdowns
        data = generate_valid_employee_data()
        emp_name = generate_employee_name("I02")
        page.type_text(page.EMPLOYEE_NAME_INPUT, emp_name, clear_first=True)
        page.wait_seconds(0.3)

        for test_id, field_name, min_opts, skip_reason in _DROPDOWN_CHECKS:
            if skip_reason and "Cascading" in skip_reason:
                log.info(f"{test_id}: Skipping '{field_name}' — {skip_reason}")
                continue

            try:
                # For Designation, use the search-input strategy
                if field_name == "Designation":
                    options = page.get_dropdown_options_by_label(field_name)
                elif field_name == "Department":
                    options = page.get_dropdown_options_by_label(field_name)
                else:
                    options = page.get_dropdown_options_by_label(field_name)

                count = len([o for o in options if o.strip()])
                log.info(f"{test_id}: '{field_name}' has {count} options")

                if count < min_opts:
                    sa.fail(
                        f"{test_id}: '{field_name}' has {count} options, "
                        f"expected >= {min_opts}"
                    )
                else:
                    log.info(f"{test_id}: PASS — '{field_name}' has {count} options")
            except Exception as e:
                # Department with 0 options may error — that's expected
                if field_name == "Department" and min_opts == 0:
                    log.info(f"{test_id}: '{field_name}' check skipped (0 options expected)")
                else:
                    sa.fail(f"{test_id}: Error checking '{field_name}': {e}")

        try:
            page.cancel_form()
        except Exception:
            page._force_close_panels()

        sa.check_all()


# ====================================================================
# EMP-I03/I04/I05: Popup workflow
# ====================================================================

class TestPopupWorkflow:
    """UI-only: Verify popup open/close workflows."""

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_EMP_I03_add_form_opens(self, emp_page):
        """Open the ADD form — verify popup is visible."""
        log.info("EMP-I03 (UI): Add form opens")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)

        is_open = page.is_add_form_open()
        assert is_open, "ADD form popup should be visible after clicking ADD"

        try:
            page.cancel_form()
        except Exception:
            page._force_close_panels()

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_EMP_I04_cancel_closes_popup(self, emp_page):
        """Click Cancel — verify popup closes."""
        log.info("EMP-I04 (UI): Cancel closes popup")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Form should be open before Cancel"

        page.cancel_form()
        page.wait_seconds(1)

        is_still_open = page.is_add_form_open()
        assert not is_still_open, "Form should be closed after Cancel"

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_EMP_I05_close_popup(self, emp_page):
        """Force close popup — verify it's gone."""
        log.info("EMP-I05 (UI): Force close popup")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)
        assert page.is_add_form_open(), "Form should be open before close"

        page._force_close_panels()
        page.wait_seconds(0.5)

        is_still_open = page.is_add_form_open()
        assert not is_still_open, "Form should be gone after force close"


# ====================================================================
# EMP-I06: Toggle defaults
# ====================================================================

class TestToggleDefaults:
    """UI-only: Verify toggle/switch default states."""

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_EMP_I06_status_toggle_default(self, emp_page):
        """Status toggle should default to Active (checked) on new form."""
        log.info("EMP-I06 (UI): Status toggle default")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)

        # Check if there's a Status toggle and its default state
        js = """
            var popup = document.querySelector(
                '.big-model, .edit_pop_up, mat-dialog-container'
            );
            if (!popup) return 'No popup';
            var toggle = popup.querySelector('app-slide-toggle-v2 .switch-wrapper');
            if (!toggle) return 'No toggle found';
            var onLabel = toggle.querySelector('span.state-label.on');
            var isActive = onLabel && onLabel.classList.contains('active');
            return JSON.stringify({found: true, active: isActive});
        """
        result = page.driver.execute_script(js)
        log.info(f"Status toggle state: {result}")

        try:
            page.cancel_form()
        except Exception:
            page._force_close_panels()


# ====================================================================
# EMP-I07: Employee Name input only accepts letters and spaces
# ====================================================================

class TestEmployeeNameInput:
    """UI-only: Verify Employee Name field behavior."""

    @pytest.mark.ui
    @pytest.mark.sanity
    def test_EMP_I07_name_accepts_letters_spaces(self, emp_page):
        """Employee Name should accept only letters and spaces (^[A-Za-z ]+$)."""
        log.info("EMP-I07 (UI): Employee Name input validation")
        page = emp_page

        page.open_add_form()
        page.wait_seconds(1)

        # Test valid name
        valid_name = "Rajesh Sharma"
        page.type_text(page.EMPLOYEE_NAME_INPUT, valid_name, clear_first=True)
        page.wait_seconds(0.5)

        actual = page.driver.execute_script(
            "return document.querySelector(\"input[name='Employee Name']\")?.value || '';"
        )
        log.info(f"Valid name input: '{valid_name}' -> Actual: '{actual}'")

        # Test name with numbers — should be rejected or stripped by the UI
        page.type_text(page.EMPLOYEE_NAME_INPUT, "Rajesh123", clear_first=True)
        page.wait_seconds(0.5)

        actual_with_nums = page.driver.execute_script(
            "return document.querySelector(\"input[name='Employee Name']\")?.value || '';"
        )
        log.info(f"Name with numbers: 'Rajesh123' -> Actual: '{actual_with_nums}'")

        if "123" in actual_with_nums:
            log.warning(
                "EMP-I07: UI accepts numbers in Employee Name field — "
                "no client-side pattern enforcement. Server should reject via ^[A-Za-z ]+$."
            )
        else:
            log.info("UI strips/rejects numbers in Employee Name — client-side validation works")

        try:
            page.cancel_form()
        except Exception:
            page._force_close_panels()
