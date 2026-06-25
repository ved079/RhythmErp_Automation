import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from pages.registration.modules.register_of_loan.data.register_of_loan_data import (
    generate_ui_form_data,
    generate_bank_name,
    generate_date_string,
    SWAL_TITLE_SUCCESS,
    SWAL_TITLE_VALIDATION_FAILED,
    SWAL_TITLE_UPDATED,
)


@pytest.mark.smoke
class TestRegisterOfLoanUI:

    def test_create_smoke(self, loan_page):
        """Full create + minimal create in one session."""
        page = loan_page

        # Pass 1: all fields
        data = generate_ui_form_data()
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, \
            f"Pass 1 expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

        # Pass 2: required fields only
        minimal = {
            "sanction_date": generate_date_string(),
            "bank_name": generate_bank_name(),
            "sanction_amount": "1000000",
            "facility_details": True,
            "disbursement_amount": "800000",
            "emi_servicing_date": generate_date_string(),
            "instalment_amount": "50000",
            "reminder_period_in_days": "30",
            "emi_period_label": True,
            "outstanding_amount": "700000",
        }
        page.open_add_form()
        page.fill_form(minimal)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, \
            f"Pass 2 expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

    def test_form_discard(self, loan_page):
        """Cancel and Close (X) both discard the form without saving."""
        page = loan_page
        bank_a = generate_bank_name() + " Alpha"
        bank_b = generate_bank_name() + " Beta"

        # Cancel
        page.open_add_form()
        page._fill_input_by_label_js("Bank Name", bank_a)
        page.click_cancel_button()
        assert not page._is_form_popup_open(), "Form should be closed after Cancel"
        assert not page.is_entry_in_table(bank_a), \
            f"'{bank_a}' should not be in table after Cancel"

        # Close (X)
        page.open_add_form()
        page._fill_input_by_label_js("Bank Name", bank_b)
        page.click_close_button()
        assert not page._is_form_popup_open(), "Form should be closed after Close (X)"
        assert not page.is_entry_in_table(bank_b), \
            f"'{bank_b}' should not be in table after Close"

    def test_validation_sweep(self, loan_page):
        """Required-field validations — cancel resets between cases."""
        page = loan_page
        valid = generate_ui_form_data()

        cases = [
            ("empty_form",           {}),
            ("missing_bank_name",    {**valid, "bank_name": None}),
            ("missing_sanction_date", {**valid, "sanction_date": None}),
            ("missing_facility",     {**valid, "facility_details": None}),
            ("missing_emi_period",   {**valid, "emi_period_label": None}),
        ]

        for label, data in cases:
            page.open_add_form()
            page.fill_form(data)
            page.submit_form()
            swal_title = page.handle_validation_warning(timeout=5)
            mat_errors = page.get_mat_error_text()
            assert bool(swal_title) or bool(mat_errors), \
                f"No validation triggered for case: '{label}'"
            page.click_cancel_button()

    def test_listing_and_search(self, loan_page):
        """Table has rows; search finds a created record by bank name."""
        page = loan_page

        assert page.get_table_row_count() > 0, \
            "Expected at least 1 row in Register of Loan table"

        data = generate_ui_form_data()
        bank_name = data["bank_name"]
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)

        page.search_entry(bank_name)
        assert page.is_entry_in_table(bank_name), \
            f"Bank name '{bank_name}' not found after search"

    def test_full_row_actions(self, loan_page):
        """One UI-created record: view, edit, changelog — all row-action flows."""
        page = loan_page

        data = generate_ui_form_data()
        bank_name = data["bank_name"]
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)
        page.search_entry(bank_name)

        # View (read-only)
        page.click_row_action(0)
        page.click_menu_view()
        assert page._is_form_popup_open(), "View form should be open"
        page.click_close_button()

        # Edit — change bank name
        edited_bank = "Edited " + bank_name
        page.click_row_action(0)
        page.click_menu_edit()
        page.wait_seconds(1)
        page._fill_input_by_label_js("Bank Name", edited_bank)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_UPDATED, \
            f"Expected '{SWAL_TITLE_UPDATED}', got: '{title}'"

        # Change log
        page.click_row_action(0)
        page.click_menu_history()
        page.wait_seconds(4)
        panel = page.driver.find_elements(*page.CHANGE_LOG_PANEL)
        assert panel and panel[0].is_displayed(), "Change log table should be visible"
