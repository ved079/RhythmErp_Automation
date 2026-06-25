import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from pages.registration.modules.miscellaneous_documents.data.miscellaneous_documents_data import (
    generate_ui_form_data,
    generate_name,
    generate_document_no,
    generate_date_string,
    generate_brief_details,
    SWAL_TITLE_SUCCESS,
    SWAL_TITLE_VALIDATION_FAILED,
    SWAL_TITLE_UPDATED,
)


@pytest.mark.smoke
class TestMiscellaneousDocumentsUI:

    def test_create_smoke(self, misc_page):
        """Full create + minimal create in one session."""
        page = misc_page

        # Pass 1: all fields
        data = generate_ui_form_data()
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, \
            f"Pass 1 expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

        # Pass 2: required fields only (no expiry_date)
        minimal = {
            "name": generate_name(),
            "document_no": str(generate_document_no()),
            "registered_date": generate_date_string(),
            "brief_details": generate_brief_details(),
        }
        page.open_add_form()
        page.fill_form(minimal)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, \
            f"Pass 2 expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

    def test_form_discard(self, misc_page):
        """Cancel and Close (X) both discard the form without saving."""
        page = misc_page
        name_a = generate_name()
        name_b = generate_name()

        # Cancel
        page.open_add_form()
        page._fill_input_by_label_js("Document Name", name_a)
        page.click_cancel_button()
        assert not page._is_form_popup_open(), "Form should be closed after Cancel"
        assert not page.is_entry_in_table(name_a), \
            f"'{name_a}' should not be in table after Cancel"

        # Close (X)
        page.open_add_form()
        page._fill_input_by_label_js("Document Name", name_b)
        page.click_close_button()
        assert not page._is_form_popup_open(), "Form should be closed after Close (X)"
        assert not page.is_entry_in_table(name_b), \
            f"'{name_b}' should not be in table after Close"

    def test_validation_sweep(self, misc_page):
        """Required-field validations — cancel resets between cases."""
        page = misc_page
        valid = generate_ui_form_data()

        cases = [
            ("empty_form",              {}),
            ("missing_name",            {**valid, "name": None}),
            ("missing_document_no",     {**valid, "document_no": None}),
            ("missing_registered_date", {**valid, "registered_date": None}),
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

    def test_listing_and_search(self, misc_page):
        """Table has rows; search finds a created record by Document Name."""
        page = misc_page

        assert page.get_table_row_count() > 0, \
            "Expected at least 1 row in Miscellaneous Documents table"

        data = generate_ui_form_data()
        doc_name = data["name"]
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)

        page.search_entry(doc_name)
        assert page.is_entry_in_table(doc_name), \
            f"Document Name '{doc_name}' not found after search"

    def test_full_row_actions(self, misc_page):
        """One UI-created record: view, edit (change brief_details), changelog."""
        page = misc_page

        data = generate_ui_form_data()
        doc_name = data["name"]
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)
        page.search_entry(doc_name)

        # View (read-only)
        page.click_row_action(0)
        page.click_menu_view()
        assert page._is_form_popup_open(), "View form should be open"
        page.click_close_button()

        # Edit — change Brief Details
        page.click_row_action(0)
        page.click_menu_edit()
        page.wait_seconds(1)
        page._fill_input_by_label_js("Brief Details", "Updated details for automated test")
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
