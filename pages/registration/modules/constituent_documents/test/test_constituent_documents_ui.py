import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from pages.registration.modules.constituent_documents.data.constituent_documents_data import (
    generate_ui_form_data,
    generate_cin_no,
    generate_date_string,
    SWAL_TITLE_SUCCESS,
    SWAL_TITLE_VALIDATION_FAILED,
    SWAL_TITLE_UPDATED,
)


@pytest.mark.smoke
class TestConstituentDocumentsUI:

    def test_create_smoke(self, cd_page):
        """Full create (2 document rows) + minimal create (1 row) in one session."""
        page = cd_page

        # Pass 1: full data with 2 document rows
        data = generate_ui_form_data()
        data["document_rows"] = [True, True]  # 2 rows
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, \
            f"Pass 1 expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

        # Pass 2: minimal (1 document row)
        minimal = {
            "cin_no": generate_cin_no(),
            "cin_date": generate_date_string(),
            "document_rows": [True],
        }
        page.open_add_form()
        page.fill_form(minimal)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, \
            f"Pass 2 expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

    def test_form_discard(self, cd_page):
        """Cancel and Close (X) both discard the form without saving."""
        page = cd_page
        cin_a = generate_cin_no()
        cin_b = generate_cin_no()

        # Cancel
        page.open_add_form()
        page._fill_input_by_label_js("CIN No", cin_a)
        page.click_cancel_button()
        assert not page._is_form_popup_open(), "Form should be closed after Cancel"
        assert not page.is_entry_in_table(cin_a), \
            f"'{cin_a}' should not be in table after Cancel"

        # Close (X)
        page.open_add_form()
        page._fill_input_by_label_js("CIN No", cin_b)
        page.click_close_button()
        assert not page._is_form_popup_open(), "Form should be closed after Close (X)"
        assert not page.is_entry_in_table(cin_b), \
            f"'{cin_b}' should not be in table after Close"

    def test_validation_sweep(self, cd_page):
        """Required-field validations — cancel resets between cases."""
        page = cd_page
        valid = generate_ui_form_data()

        cases = [
            ("empty_form",          {}),
            ("missing_cin_no",      {**valid, "cin_no": None}),
            ("missing_cin_date",    {**valid, "cin_date": None}),
            ("no_document_rows",    {**valid, "document_rows": []}),
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

    def test_listing_and_search(self, cd_page):
        """Table has rows; search finds a created record by CIN No."""
        page = cd_page

        assert page.get_table_row_count() > 0, \
            "Expected at least 1 row in Constituent Documents table"

        data = generate_ui_form_data()
        cin_no = data["cin_no"]
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)

        page.search_entry(cin_no)
        assert page.is_entry_in_table(cin_no), \
            f"CIN No '{cin_no}' not found after search"

    def test_full_row_actions(self, cd_page):
        """One UI-created record: view, edit (add doc row), changelog."""
        page = cd_page

        data = generate_ui_form_data()
        cin_no = data["cin_no"]
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)
        page.search_entry(cin_no)

        # View (read-only)
        page.click_row_action(0)
        page.click_menu_view()
        assert page._is_form_popup_open(), "View form should be open"
        page.click_close_button()

        # Edit — add one more document row and fill only that new row (index 1)
        page.click_row_action(0)
        page.click_menu_edit()
        page.wait_seconds(1)
        page.add_document_row()
        page.wait_seconds(0.5)
        page._select_document_name_in_row(1)
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
