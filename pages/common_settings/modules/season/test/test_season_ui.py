import sys
import os
import pytest
from common.logger import log

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pages.common_settings.modules.season.season_page import SeasonPage
from pages.common_settings.modules.season.data.season_data import valid_season_name


@pytest.mark.ui
class TestSeasonUI:
    """UI tests for Season (replaces test_season_validation.py)."""

    def _cleanup(self, page):
        if page.is_form_open():
            page.close_popup()
        page._dismiss_any_sweet_alert()
        page.hard_refresh()

    # --- STANDALONE TESTS ---

    def test_empty_name_shows_error(self, logged_in_driver):
        """Submit with no name — must show validation alert."""
        page = SeasonPage(logged_in_driver)
        try:
            page.navigate_to_season()
            page.open_add_form()
            result = page.click_submit()
            assert result == "validation", "Empty name must trigger validation alert"
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_special_char_name_rejected(self, logged_in_driver):
        """Name with @#$% must be rejected by frontend."""
        page = SeasonPage(logged_in_driver)
        try:
            page.navigate_to_season()
            page.open_add_form()
            page.enter_name("@#$%")
            result = page.click_submit()
            assert result == "validation", "Special chars must trigger validation"
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_hyphen_name_rejected_by_frontend(self, logged_in_driver):
        """Hyphen in name rejected by frontend (even though API accepts it).
        Frontend is more restrictive than backend on this character."""
        page = SeasonPage(logged_in_driver)
        try:
            page.navigate_to_season()
            page.open_add_form()
            page.enter_name("Kharif-2025")
            result = page.click_submit()
            assert result == "validation", \
                "Hyphen must be rejected by frontend (frontend-only restriction)"
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_underscore_name_rejected(self, logged_in_driver):
        """Underscore in name rejected by both frontend and backend."""
        page = SeasonPage(logged_in_driver)
        try:
            page.navigate_to_season()
            page.open_add_form()
            page.enter_name("Kharif_2025")
            result = page.click_submit()
            assert result == "validation", "Underscore must be rejected"
            assert page.is_form_open()
        finally:
            self._cleanup(page)

    def test_cancel_discards_form(self, logged_in_driver):
        """Fill form then cancel — record must NOT be created."""
        page = SeasonPage(logged_in_driver)
        try:
            page.navigate_to_season()
            page.open_add_form()
            name = valid_season_name()
            page.enter_name(name)
            page.close_popup()
            page.hard_refresh()
            found = page.search_record(name, exact=True)
            assert not found, "Canceled form must not create a record"
        finally:
            self._cleanup(page)

    def test_numbers_in_name_accepted(self, logged_in_driver):
        """Numbers in name accepted by frontend (Season 2025 style)."""
        page = SeasonPage(logged_in_driver)
        try:
            page.navigate_to_season()
            page.open_add_form()
            name = f"Season {valid_season_name()[:6]}"
            page.enter_name(name)
            result = page.click_submit()
            assert result == "success", "Numbers in name must be accepted"
        finally:
            self._cleanup(page)

    # --- TESTS USING shared_season ---

    def test_view_mode_readonly(self, logged_in_driver, shared_season):
        """View mode must have all fields disabled."""
        page = SeasonPage(logged_in_driver)
        try:
            page.navigate_to_season()
            assert page.search_and_verify(shared_season), "Shared season must be found"
            page.click_view_button(shared_season)
            assert page.is_form_in_view_mode(), "All fields must be disabled in view mode"
            page.close_popup()
        finally:
            self._cleanup(page)

    def test_history_shows_after_create(self, logged_in_driver, shared_season):
        """History appears immediately after create — no edit needed (confirmed manually)."""
        page = SeasonPage(logged_in_driver)
        try:
            page.navigate_to_season()
            assert page.search_and_verify(shared_season), "Shared season must be found"
            page.click_history_button(shared_season)
            assert page.is_history_popup_open(), "History popup must open"
            assert page.get_history_row_count() >= 1, \
                "History must have at least 1 row immediately after create"
            page.close_history_popup()
        finally:
            self._cleanup(page)

    def test_edit_empty_name_blocked(self, logged_in_driver, shared_season):
        """Clear name in edit mode — update must be blocked."""
        page = SeasonPage(logged_in_driver)
        try:
            page.navigate_to_season()
            assert page.search_and_verify(shared_season), "Shared season must be found"
            page.click_edit_button(shared_season)
            page.enter_name("")
            result = page.click_update()
            assert result == "validation", "Empty name on edit must be blocked"
        finally:
            self._cleanup(page)

    def test_status_toggle_persists(self, logged_in_driver):
        """Create record, toggle status to Inactive, verify persists after refresh."""
        page = SeasonPage(logged_in_driver)
        try:
            page.navigate_to_season()
            page.open_add_form()
            name = valid_season_name()
            page.enter_name(name)
            page.click_submit()
            page.hard_refresh()
            assert page.search_and_verify(name), "Record must be created"
            page.click_edit_button(name)
            page.driver.execute_script("""
                var cb = document.querySelector("div.edit_pop_up input[type='checkbox']");
                if (cb) cb.click();
            """)
            page.click_update()
            page.hard_refresh()
            assert page.search_and_verify(name), "Record must be found after edit"
            page.click_edit_button(name)
            is_checked = page.driver.execute_script("""
                var cb = document.querySelector("div.edit_pop_up input[type='checkbox']");
                return cb ? cb.checked : null;
            """)
            assert is_checked is False, "Toggle must persist as Inactive"
        finally:
            self._cleanup(page)
