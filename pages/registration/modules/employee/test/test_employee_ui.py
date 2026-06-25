import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from pages.registration.modules.employee.data.employee_data import (
    generate_ui_form_data,
    generate_employee_name,
    generate_phone,
    generate_email,
    SWAL_TITLE_SUCCESS,
    SWAL_TITLE_VALIDATION_FAILED,
    SWAL_TITLE_UPDATED,
)


@pytest.mark.smoke
class TestEmployeeUI:

    def test_create_smoke(self, emp_page):
        """Full create (all fields auto-picked) + minimal create in one session."""
        page = emp_page

        # Pass 1: all fields auto-picked (designation/department selected by UI)
        data = generate_ui_form_data()
        page.open_add_form()
        page.fill_employee_form(data)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, \
            f"Pass 1 expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

        # Pass 2: required fields only (no department)
        minimal = {
            "party_reference": None,
            "employee_name": generate_employee_name(),
            "email": generate_email(),
            "phone_number": str(generate_phone()),
            "designation": None,   # auto-pick
            "department": None,    # skip
            "status": True,
        }
        page.open_add_form()
        page.fill_employee_form(minimal)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, \
            f"Pass 2 expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

    def test_form_discard(self, emp_page):
        """Cancel and Close (X) both discard the form without saving."""
        page = emp_page
        name_a = generate_employee_name()
        name_b = generate_employee_name()

        # Cancel
        page.open_add_form()
        page.type_text(page.EMPLOYEE_NAME_INPUT, name_a, clear_first=True)
        page.cancel_form()
        assert not page._is_form_popup_open(), "Form should be closed after Cancel"
        assert not page.is_entry_in_table(name_a), \
            f"'{name_a}' should not be in table after Cancel"

        # Close (X)
        page.open_add_form()
        page.type_text(page.EMPLOYEE_NAME_INPUT, name_b, clear_first=True)
        page.click_close_button()
        assert not page._is_form_popup_open(), "Form should be closed after Close (X)"
        assert not page.is_entry_in_table(name_b), \
            f"'{name_b}' should not be in table after Close"

    def test_validation_sweep(self, emp_page):
        """Required-field validations — cancel resets between cases."""
        page = emp_page
        valid = generate_ui_form_data()

        cases = [
            ("empty_form",          {"party_reference": None, "employee_name": "", "email": "", "phone_number": "", "designation": "", "department": None, "status": True}),
            ("missing_name",        {**valid, "employee_name": ""}),
            ("missing_phone",       {**valid, "phone_number": ""}),
            ("missing_designation", {**valid, "designation": ""}),
        ]

        for label, data in cases:
            page.open_add_form()
            page.fill_employee_form(data)
            page.submit_form()
            swal_title = page.handle_validation_warning(timeout=5)
            mat_errors = page.get_mat_error_text()
            assert bool(swal_title) or bool(mat_errors), \
                f"No validation triggered for case: '{label}'"
            page.cancel_form()

    def test_listing_and_search(self, emp_page):
        """Table has rows; search finds a created record by employee name."""
        page = emp_page

        assert page.get_table_row_count() > 0, \
            "Expected at least 1 row in Employee table"

        data = generate_ui_form_data()
        emp_name = data["employee_name"]
        page.open_add_form()
        page.fill_employee_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)

        page.search_entry(emp_name)
        assert page.is_entry_in_table(emp_name), \
            f"Employee name '{emp_name}' not found after search"

    def test_full_row_actions(self, emp_page):
        """One UI-created record: view, edit (re-submit unchanged), changelog."""
        page = emp_page

        data = generate_ui_form_data()
        emp_name = data["employee_name"]
        page.open_add_form()
        page.fill_employee_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)
        page.search_entry(emp_name)

        # View (read-only)
        page.open_row_menu(0)
        page.click_view_from_menu()
        assert page._is_form_popup_open(), "View form should be open"
        page.click_close_button()

        # Edit — re-submit without changes
        page.open_row_menu(0)
        page.click_edit_from_menu()
        page.wait_seconds(1)
        page.update()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_UPDATED, \
            f"Expected '{SWAL_TITLE_UPDATED}', got: '{title}'"

        # Change log
        page.open_row_menu(0)
        page.click_menu_history()
        page.wait_seconds(4)
        panel = page.driver.find_elements(*page.CHANGE_LOG_PANEL)
        assert panel and panel[0].is_displayed(), "Change log table should be visible"
