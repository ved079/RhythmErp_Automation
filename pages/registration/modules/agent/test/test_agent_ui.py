import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from pages.registration.modules.agent.data.agent_data import (
    generate_ui_form_data,
    generate_agent_name,
    SWAL_TITLE_SUCCESS,
    SWAL_TITLE_VALIDATION_FAILED,
    SWAL_TITLE_UPDATED,
)


@pytest.mark.smoke
class TestAgentUI:

    def test_create_smoke(self, agt_page):
        """Full create (all cascade auto-picked) × 2 in one session."""
        page = agt_page

        # Pass 1: all fields
        data = generate_ui_form_data()
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, \
            f"Pass 1 expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

        # Pass 2: second unique agent
        data2 = generate_ui_form_data()
        page.open_add_form()
        page.fill_form(data2)
        page.submit_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_SUCCESS, \
            f"Pass 2 expected '{SWAL_TITLE_SUCCESS}', got: '{title}'"

    def test_form_discard(self, agt_page):
        """Cancel and Close (X) both discard the form without saving."""
        page = agt_page
        name_a = generate_agent_name()
        name_b = generate_agent_name()

        # Cancel — fill agent name on Step 0 then cancel
        page.open_add_form()
        page._fill_input_by_name("Agent Name", name_a)
        page.click_cancel_button()
        assert not page._is_form_popup_open(), "Form should be closed after Cancel"
        assert not page.is_entry_in_table(name_a), \
            f"'{name_a}' should not be in table after Cancel"

        # Close (X)
        page.open_add_form()
        page._fill_input_by_name("Agent Name", name_b)
        page.click_close_button()
        assert not page._is_form_popup_open(), "Form should be closed after Close (X)"
        assert not page.is_entry_in_table(name_b), \
            f"'{name_b}' should not be in table after Close"

    def test_validation_sweep(self, agt_page):
        """Required-field validations on Step 0 — cancel resets between cases."""
        page = agt_page

        cases = [
            ("empty_form",     {"agent_name": "", "phone_number": "", "email": ""}),
            ("missing_name",   {"agent_name": "", "phone_number": "9876543210", "email": "test@test.com"}),
            ("missing_phone",  {"agent_name": generate_agent_name(), "phone_number": "", "email": "test@test.com"}),
            ("missing_email",  {"agent_name": generate_agent_name(), "phone_number": "9876543210", "email": ""}),
        ]

        for label, partial in cases:
            page.open_add_form()
            if partial.get("agent_name"):
                page._fill_input_by_name("Agent Name", partial["agent_name"])
            if partial.get("phone_number"):
                page._fill_input_by_name("Phone Number", partial["phone_number"])
            if partial.get("email"):
                page._fill_input_by_name("Email", partial["email"])
            # Try to advance to next step or submit — validation triggers on Next click
            try:
                page.click_next()
            except Exception:
                pass
            swal_title = page.handle_validation_warning(timeout=5)
            mat_errors = page.get_mat_error_text()
            assert bool(swal_title) or bool(mat_errors), \
                f"No validation triggered for case: '{label}'"
            page.click_cancel_button()

    def test_listing_and_search(self, agt_page):
        """Table has rows; search finds a created record by agent name."""
        page = agt_page

        assert page.get_table_row_count() > 0, \
            "Expected at least 1 row in Agent table"

        data = generate_ui_form_data()
        agent_name = data["agent_name"]
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)

        page.search_entry(agent_name)
        assert page.is_entry_in_table(agent_name), \
            f"Agent name '{agent_name}' not found after search"

    def test_full_row_actions(self, agt_page):
        """One UI-created record: view, edit (re-submit through all steps), changelog."""
        page = agt_page

        data = generate_ui_form_data()
        agent_name = data["agent_name"]
        page.open_add_form()
        page.fill_form(data)
        page.submit_form()
        page.handle_success_alert(timeout=15)
        page.search_entry(agent_name)

        # View (read-only)
        page.click_row_action(0)
        page.click_menu_view()
        assert page._is_form_popup_open(), "View form should be open"
        page.click_close_button()

        # Edit — navigate through stepper steps then Update
        page.click_row_action(0)
        page.click_menu_edit()
        page.wait_seconds(1)
        page.click_next()   # Step 0 → Step 1
        page.wait_seconds(0.5)
        page.click_next()   # Step 1 → Step 2
        page.wait_seconds(0.5)
        page.update_form()
        title = page.handle_success_alert(timeout=15)
        assert title == SWAL_TITLE_UPDATED, \
            f"Expected '{SWAL_TITLE_UPDATED}', got: '{title}'"

        # Change log
        page.click_row_action(0)
        page.click_menu_history()
        page.wait_seconds(4)
        panel = page.driver.find_elements(*page.CHANGE_LOG_PANEL)
        assert panel and panel[0].is_displayed(), "Change log table should be visible"
