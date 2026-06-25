import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from pages.registration.modules.directors.data.directors_data import (
    generate_valid_directors_data,
    generate_minimal_directors_data,
    generate_director_name,
    generate_valid_kyc_row,
    SWAL_TITLE_SUCCESS,
    SWAL_TITLE_VALIDATION_FAILED,
    SWAL_TITLE_UPDATED,
)


@pytest.mark.smoke
class TestDirectorsUI:

    def test_create_smoke(self, dir_page):
        """Full create + minimal create in one session."""
        page = dir_page

        # Pass 1: all fields + 3 KYC rows
        data = generate_valid_directors_data()
        data["kyc_details"] = [
            generate_valid_kyc_row(65),
            generate_valid_kyc_row(66),
            generate_valid_kyc_row(65),
        ]
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, f"Pass 1 expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

        # Pass 2: required fields only + one KYC row (ERP requires at least one)
        minimal = generate_minimal_directors_data()
        minimal["kyc_details"] = [generate_valid_kyc_row(65)]
        page.open_add_form()
        page.fill_form(minimal)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, f"Pass 2 expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

    def test_form_discard(self, dir_page):
        """Cancel and Close (X) both discard the form without saving."""
        page = dir_page
        name_a = generate_director_name()
        name_b = generate_director_name()

        # Cancel
        page.open_add_form()
        page._fill_input_by_label_js("Name of Director/KMP", name_a)
        page.click_cancel_button()
        assert not page._is_form_popup_open(), "Form should be closed after Cancel"
        assert not page.is_director_in_table(name_a), f"'{name_a}' should not be in table after Cancel"

        # Close (X)
        page.open_add_form()
        page._fill_input_by_label_js("Name of Director/KMP", name_b)
        page.click_close_button()
        assert not page._is_form_popup_open(), "Form should be closed after Close (X)"
        assert not page.is_director_in_table(name_b), f"'{name_b}' should not be in table after Close"

    def test_kyc_row_management(self, dir_page):
        """Add two KYC rows, remove the second, submit with one remaining."""
        page = dir_page
        data = generate_valid_directors_data()
        data["kyc_details"] = [
            generate_valid_kyc_row(65),
            generate_valid_kyc_row(66),
        ]
        page.open_add_form()
        page.fill_form(data)
        page.remove_kyc_row(1)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, f"Expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

    def test_validation_sweep(self, dir_page):
        """All required-field validations in one session — cancel resets between cases."""
        page = dir_page
        valid = generate_valid_directors_data()

        cases = [
            ("empty_form",        {}),
            ("missing_prefix",    {**valid, "prefix": None}),
            ("missing_desig",     {**valid, "designation": None}),
            ("missing_qual",      {**valid, "qualification": None}),
            ("missing_kyc",       {**valid, "kyc_details": []}),
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

    def test_listing_and_search(self, dir_page):
        """Table has rows, search finds a record, search returns nothing for junk."""
        page = dir_page

        # Table populated
        assert page.get_table_row_count() > 0, "Expected at least 1 row in Directors table"

        # Create via UI so we control the pan_no
        data = generate_valid_directors_data()
        data["kyc_details"] = [generate_valid_kyc_row(65)]
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)

        page.search_director(data["pan_no"])
        assert page.is_director_in_table(data["director_name"]), \
            f"Director '{data['director_name']}' not found after search"

        # Search returns nothing for junk
        page.search_director("ZZZNOTEXIST99999")
        count = page.get_table_row_count()
        assert count == 0, f"Expected 0 rows for non-existent search, got {count}"

    def test_full_row_actions(self, dir_page):
        """One UI-created record: view, edit, changelog — all row-action flows."""
        page = dir_page

        data = generate_valid_directors_data()
        data["kyc_details"] = [generate_valid_kyc_row(65)]
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)
        page.search_director(data["pan_no"])

        # View (read-only)
        page.click_row_action(0)
        page.click_menu_view()
        assert page._is_form_popup_open(), "View form should be open"
        page.click_close_button()

        # Edit
        page.click_row_action(0)
        page.click_menu_edit()
        page.wait_seconds(1)
        new_name = f"Edited {generate_director_name()}"
        page._fill_input_by_label_js("Name of Director/KMP", new_name)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_UPDATED, f"Expected '{SWAL_TITLE_UPDATED}', got: '{title}'"

        # Change log
        page.click_row_action(0)
        page.click_menu_history()
        page.wait_seconds(2)
        panel = page.driver.find_elements(*page.CHANGE_LOG_PANEL)
        assert panel and panel[0].is_displayed(), "Change log table should be visible"
