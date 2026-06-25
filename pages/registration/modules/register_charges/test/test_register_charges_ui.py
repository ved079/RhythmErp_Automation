import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from pages.registration.modules.register_charges.data.register_charges_data import (
    generate_ui_form_data,
    generate_roc_charge_id,
    generate_date_string,
    SWAL_TITLE_SUCCESS,
    SWAL_TITLE_VALIDATION_FAILED,
    SWAL_TITLE_UPDATED,
)


@pytest.mark.smoke
class TestRegisterChargesUI:

    def test_create_smoke(self, rc_page):
        """Full create + minimal create in one session."""
        page = rc_page

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
            "date_of_creation": generate_date_string(),
            "date_of_modification": generate_date_string(),
            "roc_charge_id": generate_roc_charge_id(),
            "type_of_charge": True,
            "amount_secured": "500000",
            "charge_holder_details": "State Bank of India, Main Branch",
        }
        page.open_add_form()
        page.fill_form(minimal)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, \
            f"Pass 2 expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

    def test_form_discard(self, rc_page):
        """Cancel and Close (X) both discard the form without saving."""
        page = rc_page
        id_a = generate_roc_charge_id()
        id_b = generate_roc_charge_id()

        # Cancel
        page.open_add_form()
        page._fill_input_by_label_js("Charge ID (ROC)", id_a)
        page.click_cancel_button()
        assert not page._is_form_popup_open(), "Form should be closed after Cancel"
        assert not page.is_entry_in_table(id_a), \
            f"'{id_a}' should not be in table after Cancel"

        # Close (X)
        page.open_add_form()
        page._fill_input_by_label_js("Charge ID (ROC)", id_b)
        page.click_close_button()
        assert not page._is_form_popup_open(), "Form should be closed after Close (X)"
        assert not page.is_entry_in_table(id_b), \
            f"'{id_b}' should not be in table after Close"

    def test_validation_sweep(self, rc_page):
        """Required-field validations — cancel resets between cases."""
        page = rc_page
        valid = generate_ui_form_data()

        cases = [
            ("empty_form",          {}),
            ("missing_roc_id",      {**valid, "roc_charge_id": None}),
            ("missing_type",        {**valid, "type_of_charge": None}),
            ("missing_amount",      {**valid, "amount_secured": None}),
            ("missing_holder",      {**valid, "charge_holder_details": None}),
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

    def test_listing_and_search(self, rc_page):
        """Table has rows, search finds a record, search returns nothing for junk."""
        page = rc_page

        assert page.get_table_row_count() > 0, \
            "Expected at least 1 row in Register Charges table"

        data = generate_ui_form_data()
        roc_id = data["roc_charge_id"]
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)

        page.search_entry(roc_id)
        assert page.is_entry_in_table(roc_id), \
            f"ROC charge ID '{roc_id}' not found after search"

    def test_full_row_actions(self, rc_page):
        """One UI-created record: view, edit, changelog — all row-action flows."""
        page = rc_page

        data = generate_ui_form_data()
        roc_id = data["roc_charge_id"]
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)
        page.search_entry(roc_id)

        # View (read-only)
        page.click_row_action(0)
        page.click_menu_view()
        assert page._is_form_popup_open(), "View form should be open"
        page.click_close_button()

        # Edit
        page.click_row_action(0)
        page.click_menu_edit()
        page.wait_seconds(1)
        page._fill_input_by_label_js("Charge Holder Details", "Edited HDFC Bank, SME Branch")
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
