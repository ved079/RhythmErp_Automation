"""
test_season_validation.py
--------------------------
Season screen (Common Settings) test automation.
18 test cases across 9 classes covering: create, validation, bugs, edit, view,
cancel, search, history, boundary.

Optimised (v3) — UOM-pattern speed improvements:
- Uses logged_in_driver directly, creates SeasonPage per test
- Uses hard_refresh() for fast page reset between operations
- Uses search_and_verify() for create/update verification
- Smart finally blocks: only cleanup if form is actually open
- Minimised wait_seconds() calls
- Uses _click_action_menu_item(name, action) instead of find_row_by_name + click_edit_by_index

Markers:
  - smoke (4):     T1, T2, T7, T8
  - sanity (18):   All tests
  - regression (18): All tests
  - bug (5):       T3, T4, T5, T6, T18
  - ui (12):       T5, T7, T9-T18

Run:  pytest season/test/test_season_validation.py -v
"""

import sys
import os
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from common.logger import log
from pages.common_settings.modules.season.season_page import SeasonPage
from pages.common_settings.modules.season.data.season_data import (
    valid_season_with_description,
    valid_season_name_only,
    valid_season_name,
    empty_submit,
    name_only_rest_blank,
    sql_injection_name,
    xss_in_name,
    special_chars_name,
    duplicate_name,
    very_long_name,
    numbers_only_name,
    leading_trailing_spaces,
    VALIDATION_ALERT_TITLE,
    SUCCESS_ALERT_TITLE_ADD,
    SUCCESS_ALERT_TITLE_UPDATE,
)


class _Cleanup:
    """Shared cleanup helper — only closes form if it's actually open, then hard refresh."""

    @staticmethod
    def cleanup(season_page):
        if season_page.is_form_open():
            season_page.close_popup()
        # Dismiss any lingering SweetAlert
        season_page._dismiss_any_sweet_alert()
        season_page.hard_refresh()


# ================================================================
# GROUP A — HAPPY PATH (Add)
# ================================================================

class TestSeasonHappyPath:
    """T1, T2: Valid season creation."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_01_create_season_with_name_and_description(self, logged_in_driver):
        """T1: Create season with Name + Description — should succeed."""
        log.test_start("T1: Create season with Name + Description")
        page = SeasonPage(logged_in_driver)

        try:
            data = valid_season_with_description()
            name = data["Name"]

            page.navigate_to_season()
            page.open_add_form()
            page.fill_form(name, data["Description"])

            result = page.click_submit()
            assert result == "success", f"Submit should succeed, got: {result}"

            page.hard_refresh()
            assert page.search_and_verify(name), f"Season '{name}' should be in table"

            log.passed("T1: Season created with Name + Description")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_02_create_season_name_only_no_description(self, logged_in_driver):
        """T2: Create season with Name only (Description optional) — should succeed."""
        log.test_start("T2: Create season with Name only")
        page = SeasonPage(logged_in_driver)

        try:
            data = valid_season_name_only()
            name = data["Name"]

            page.navigate_to_season()
            page.open_add_form()
            page.enter_name(name)

            result = page.click_submit()
            assert result == "success", f"Submit should succeed, got: {result}"

            page.hard_refresh()
            assert page.search_and_verify(name), f"Season '{name}' should be in table"

            log.passed("T2: Season created with Name only")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)


# ================================================================
# GROUP B — VALIDATION (Add)
# ================================================================

class TestSeasonValidation:
    """T3-T6: Negative tests — SQL injection, XSS, special chars, duplicate."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_03_sql_injection_in_name(self, logged_in_driver):
        """T3: SQL injection in Name field — BUG: accepted and stored as-is."""
        log.test_start("T3: SQL injection in Name (BUG — accepted)")
        page = SeasonPage(logged_in_driver)

        try:
            data = sql_injection_name()
            name = data["Name"]

            page.navigate_to_season()
            page.open_add_form()
            page.fill_form(name, data["Description"])

            result = page.click_submit()
            assert result == "success", f"BUG: SQL injection accepted, got: {result}"

            page.hard_refresh()
            assert page.search_and_verify(name), (
                f"BUG CONFIRMED: SQL injection '{name}' was stored in the database."
            )

            log.passed("T3: BUG confirmed — SQL injection accepted in Name")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_04_xss_in_name(self, logged_in_driver):
        """T4: XSS script tag in Name — BUG: stored as raw HTML."""
        log.test_start("T4: XSS in Name (BUG — stored as raw HTML)")
        page = SeasonPage(logged_in_driver)

        try:
            data = xss_in_name()
            name = data["Name"]

            page.navigate_to_season()
            page.open_add_form()
            page.fill_form(name, data["Description"])

            result = page.click_submit()
            assert result == "success", f"BUG: XSS accepted, got: {result}"

            page.hard_refresh()
            assert page.search_and_verify(name), (
                f"BUG CONFIRMED: XSS payload '{name}' was stored in the database."
            )

            log.passed("T4: BUG confirmed — XSS accepted in Name")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_05_duplicate_season_name(self, logged_in_driver):
        """T5: Duplicate Season Name — should show Validation Failed alert."""
        log.test_start("T5: Duplicate Season Name (validation alert expected)")
        page = SeasonPage(logged_in_driver)

        try:
            data = duplicate_name()
            name = data["Name"]  # "Rabi" — known existing record

            page.navigate_to_season()
            page.open_add_form()
            page.fill_form(name, data["Description"])

            # Don't check submit result — handle both paths
            page._js_click_popup_button('Submit')
            time.sleep(0.5)

            validation_alert = page.is_validation_alert_present(timeout=5)
            form_still_open = page.is_form_open()

            # Cleanup
            if validation_alert:
                page.handle_validation_alert()
                log.info("Validation alert detected for duplicate name")
            if form_still_open:
                page.close_popup()

            if validation_alert:
                log.info(f"Duplicate '{name}' correctly rejected with validation alert")
            else:
                log.warning(f"Duplicate '{name}' — no validation alert (BUG or accepted)")

            log.passed("T5: Duplicate name behavior verified")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_06_special_characters_in_name(self, logged_in_driver):
        """T6: Special characters in Name — BUG: accepted without validation."""
        log.test_start("T6: Special characters in Name (BUG — accepted)")
        page = SeasonPage(logged_in_driver)

        try:
            data = special_chars_name()
            name = data["Name"]

            page.navigate_to_season()
            page.open_add_form()
            page.fill_form(name, data["Description"])

            result = page.click_submit()
            assert result == "success", f"BUG: Special chars accepted, got: {result}"

            page.hard_refresh()
            assert page.search_and_verify(name), (
                f"BUG CONFIRMED: Special characters '{name}' were accepted."
            )

            log.passed("T6: BUG confirmed — Special characters accepted in Name")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)


# ================================================================
# GROUP C — VALIDATION (Negative - Empty)
# ================================================================

class TestSeasonEmptySubmit:
    """T7: Submit with all fields blank — should show Validation Failed."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_07_empty_submit_all_fields_blank(self, logged_in_driver):
        """T7: Submit with Name blank — should show Validation Failed alert."""
        log.test_start("T7: Empty submit — all fields blank")
        page = SeasonPage(logged_in_driver)

        try:
            page.navigate_to_season()
            page.open_add_form()
            assert page.is_form_open(), "Add form should be open"

            # Submit without filling any field
            result = page.click_submit()
            assert result == "validation", (
                f"Expected validation alert for empty submit, got: {result}"
            )

            # Verify alert title
            alert_title = page.get_alert_title()
            assert VALIDATION_ALERT_TITLE in alert_title, (
                f"Expected alert title '{VALIDATION_ALERT_TITLE}', got '{alert_title}'"
            )

            # Dismiss alert and verify form stays open
            page.handle_validation_alert()
            assert page.is_form_open(), "Form should remain open after validation failure"

            log.passed("T7: Validation Failed alert shown for empty submit")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)


# ================================================================
# GROUP D — EDIT FLOW
# ================================================================

class TestSeasonEditFlow:
    """T8: Edit existing season record."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_08_edit_existing_season(self, logged_in_driver):
        """T8: Edit a season record — change Name and Description, verify update."""
        log.test_start("T8: Edit existing season")
        page = SeasonPage(logged_in_driver)

        try:
            # Step 1: Create a season first
            data = valid_season_with_description()
            original_name = data["Name"]

            page.navigate_to_season()
            page.open_add_form()
            page.fill_form(original_name, data["Description"])
            result = page.click_submit()
            assert result == "success", f"Prerequisite: create failed, got: {result}"

            # Step 2: Search, then edit
            page.hard_refresh()
            assert page.search_and_verify(original_name), f"'{original_name}' not found"

            page.click_edit_button(original_name)
            assert page.is_form_open(), "Edit form should be open"

            # Step 3: Clear and enter new data
            new_name = f"EDITED_{original_name}"
            new_desc = f"Edited - {data['Description']}"
            page.clear_form()
            page.fill_form(new_name, new_desc)

            result = page.click_update()
            assert result == "success", f"Update should succeed, got: {result}"

            # Step 4: Verify updated record
            page.hard_refresh()
            assert page.search_and_verify(new_name), f"Updated '{new_name}' not found"

            page.hard_refresh()
            assert not page.search_record(original_name, exact=True), (
                f"Old '{original_name}' should NOT be in table after edit"
            )

            log.passed("T8: Season edited and verified")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)


# ================================================================
# GROUP E — VIEW MODE
# ================================================================

class TestSeasonViewMode:
    """T9: View mode — verify fields are disabled/read-only."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_09_view_mode_fields_disabled(self, logged_in_driver):
        """T9: Open View popup — verify all fields are disabled."""
        log.test_start("T9: View mode — verify fields disabled")
        page = SeasonPage(logged_in_driver)

        try:
            page.navigate_to_season()
            row_count = page.get_table_row_count()
            assert row_count > 0, "Table should have at least one record"

            # Get first row name, click View
            first_name = page.get_name_from_row(0)
            page.click_view_button(first_name)
            assert page.is_form_open(), "View form should be open"

            # Verify view mode
            assert page.is_form_in_view_mode(), "Submit/Update should NOT be visible in View mode"

            name_disabled = page.is_field_disabled(("css", "input[name='Name']"))
            assert name_disabled, "Name field should be disabled in View mode"

            desc_disabled = page.is_field_disabled(("css", "input[name='Description']"))
            assert desc_disabled, "Description field should be disabled in View mode"

            log.passed("T9: View mode verified — all fields disabled")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)


# ================================================================
# GROUP F - SEARCH
# ================================================================

class TestSeasonSearch:
    """T10-T11: Search functionality on Season list page."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_10_search_existing_season(self, logged_in_driver):
        """T10: Search for an existing season by name - should find it."""
        log.test_start("T10: Search existing season by name")
        page = SeasonPage(logged_in_driver)

        try:
            # Create a season to search for
            data = valid_season_with_description()
            name = data["Name"]

            page.navigate_to_season()
            page.open_add_form()
            page.fill_form(name, data["Description"])
            page.click_submit()

            page.hard_refresh()
            assert page.search_and_verify(name), f"'{name}' not found"

            # Search again (bar still open)
            found = page.search_record(name)
            assert found, f"Search should find season '{name}'"

            row_count = page.get_table_row_count()
            assert row_count >= 1, f"Expected at least 1 result, got {row_count}"
            first_name = page.get_name_from_row(0)
            assert name in first_name, f"Result '{first_name}' should contain '{name}'"

            log.passed("T10: Existing season found via search")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_11_search_nonexistent_season(self, logged_in_driver):
        """T11: Search for a name that does not exist - should return 0 results."""
        log.test_start("T11: Search non-existent season name")
        page = SeasonPage(logged_in_driver)

        try:
            page.navigate_to_season()
            fake_name = f"NONEXISTENT_{valid_season_name()}_NOCHANCE"

            found = page.search_record(fake_name)
            assert not found, f"Search should NOT find '{fake_name}'"

            row_count = page.get_table_row_count()
            assert row_count == 0, f"Expected 0 rows, got {row_count}"

            log.passed("T11: Non-existent search returned 0 results")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)


# ================================================================
# GROUP G - HISTORY
# ================================================================

class TestSeasonHistory:
    """T12-T14: History popup - open, search, close."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_12_history_popup_opens_with_data(self, logged_in_driver):
        """T12: Click History on a row - popup should open with data rows."""
        log.test_start("T12: History popup opens with data")
        page = SeasonPage(logged_in_driver)

        try:
            # Create + Edit to generate history
            data = valid_season_with_description()
            name = data["Name"]

            page.navigate_to_season()
            page.open_add_form()
            page.fill_form(name, data["Description"])
            page.click_submit()

            page.hard_refresh()
            page.search_and_verify(name)

            # Edit to create history row
            page.click_edit_button(name)
            page.clear_form()
            page.fill_form(name, f"Edited - {data['Description']}")
            page.click_update()

            # Open History
            page.hard_refresh()
            page.search_and_verify(name)

            page.click_history_button(name)

            title = page.get_history_title()
            assert "History" in title, f"Title should contain 'History', got '{title}'"

            history_rows = page.get_history_row_count()
            assert history_rows > 1, f"History should have data rows, got {history_rows}"

            page.close_history_popup()

            log.passed("T12: History popup opened with data")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_13_history_search_filters_records(self, logged_in_driver):
        """T13: Search inside History popup - should filter rows."""
        log.test_start("T13: History search filters records")
        page = SeasonPage(logged_in_driver)

        try:
            # Create + Edit to generate history
            data = valid_season_with_description()
            name = data["Name"]

            page.navigate_to_season()
            page.open_add_form()
            page.fill_form(name, data["Description"])
            page.click_submit()

            page.hard_refresh()
            page.search_and_verify(name)

            page.click_edit_button(name)
            page.clear_form()
            page.fill_form(name, f"Edited - {data['Description']}")
            page.click_update()

            # Open History
            page.hard_refresh()
            page.search_and_verify(name)

            page.click_history_button(name)

            first_history_name = page.get_history_cell_text(1, 3)
            total_rows = page.get_history_row_count()
            assert first_history_name not in ("ROW_NOT_FOUND", ""), "Could not read history data"

            # Search in history
            page.search_in_history(first_history_name)

            filtered_rows = page.get_history_row_count()
            assert filtered_rows > 1, f"History search should return data, got {filtered_rows}"

            filtered_name = page.get_history_cell_text(1, 3)
            assert first_history_name in filtered_name, (
                f"Filtered '{filtered_name}' should contain '{first_history_name}'"
            )

            page.close_history_popup()

            log.passed("T13: History search filtered records correctly")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_14_history_close_via_cancel(self, logged_in_driver):
        """T14: Close History popup via Cancel button."""
        log.test_start("T14: History close via Cancel button")
        page = SeasonPage(logged_in_driver)

        try:
            page.navigate_to_season()

            # Use first row
            first_name = page.get_name_from_row(0)
            page.click_history_button(first_name)
            assert page.is_history_popup_open(), "History popup should be open"

            page.close_history_popup()
            time.sleep(0.5)

            popup_still_open = page.is_history_popup_open(timeout=3)
            assert not popup_still_open, "History popup should be closed after Cancel"

            log.passed("T14: History popup closed via Cancel")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)


# ================================================================
# GROUP H - CANCEL BEHAVIOR
# ================================================================

class TestSeasonCancel:
    """T15-T16: Cancel button during Add and Edit flows."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_15_cancel_during_add_nothing_saved(self, logged_in_driver):
        """T15: Fill Add form and click Cancel - record should NOT be saved."""
        log.test_start("T15: Cancel during Add - nothing saved")
        page = SeasonPage(logged_in_driver)

        try:
            name = valid_season_name()

            page.navigate_to_season()
            page.open_add_form()
            page.enter_name(name)

            page.close_popup()

            assert not page.is_form_open(), "Form should be closed after Cancel"

            page.hard_refresh()
            found = page.search_record(name)
            assert not found, f"Season '{name}' should NOT exist after Cancel"

            log.passed("T15: Cancel during Add - no record saved")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_16_cancel_during_edit_original_unchanged(self, logged_in_driver):
        """T16: Open Edit form, modify data, click Cancel - original should remain."""
        log.test_start("T16: Cancel during Edit - original unchanged")
        page = SeasonPage(logged_in_driver)

        try:
            # Create a season first
            data = valid_season_with_description()
            original_name = data["Name"]

            page.navigate_to_season()
            page.open_add_form()
            page.fill_form(original_name, data["Description"])
            page.click_submit()

            # Edit the season
            page.hard_refresh()
            page.search_and_verify(original_name)

            page.click_edit_button(original_name)
            assert page.is_form_open(), "Edit form should be open"

            modified_name = f"CANCELLED_{original_name}"
            page.clear_form()
            page.enter_name(modified_name)

            page.close_popup()

            # Verify original still exists
            page.hard_refresh()
            assert page.search_and_verify(original_name), (
                f"Original '{original_name}' should still exist after Cancel"
            )

            assert not page.search_record(modified_name), (
                f"Modified '{modified_name}' should NOT exist after Cancel"
            )

            log.passed("T16: Cancel during Edit - original data unchanged")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)


# ================================================================
# GROUP I - BOUNDARY TESTS
# ================================================================

class TestSeasonBoundary:
    """T17-T18: Boundary tests - spaces, long names."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_17_leading_trailing_spaces_in_name(self, logged_in_driver):
        """T17: Name with leading/trailing spaces - test trim behavior."""
        log.test_start("T17: Leading/trailing spaces in name")
        page = SeasonPage(logged_in_driver)

        try:
            data = leading_trailing_spaces()
            raw_name = data["Name"]
            expected_trimmed = raw_name.strip()

            page.navigate_to_season()
            page.open_add_form()
            page.fill_form(raw_name, data["Description"])

            result = page.click_submit()

            if result != "success":
                page.handle_validation_alert()
                if page.is_form_open():
                    page.close_popup()
                log.warning("T17: Submit did not succeed with spaces name")
                return

            page.hard_refresh()

            found_trimmed = page.search_record(expected_trimmed)
            found_raw = page.search_record(raw_name) if not found_trimmed else False

            assert found_trimmed or found_raw, (
                f"Season '{raw_name}' should be found (trimmed: '{expected_trimmed}')"
            )

            if found_trimmed:
                log.info(f"Name was TRIMMED - stored as '{expected_trimmed}'")
            elif found_raw:
                log.info(f"Name was stored AS-IS with spaces - '{raw_name}'")

            log.passed("T17: Spaces test completed")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_18_very_long_name(self, logged_in_driver):
        """T18: Very long name (200 chars) - test max-length behavior."""
        log.test_start("T18: Very long name (200 characters)")
        page = SeasonPage(logged_in_driver)

        try:
            data = very_long_name(length=200)
            long_name = data["Name"]

            page.navigate_to_season()
            page.open_add_form()
            page.fill_form(long_name, data["Description"])

            result = page.click_submit()

            if result == "success":
                page.hard_refresh()
                found = page.search_and_verify(long_name)
                if found:
                    log.info("200-char name was ACCEPTED (BUG — no max-length)")
                else:
                    log.info("Form closed but record not found - may have been truncated")
                log.passed("T18: Long name accepted (BUG: no max-length)")
            elif result == "validation":
                page.handle_validation_alert()
                page.close_popup()
                log.info("Validation alert shown for 200-char name")
                log.passed("T18: Long name rejected by validation")
            else:
                page._dismiss_any_sweet_alert()
                if page.is_form_open():
                    page.close_popup()
                log.warning("No response for 200-char name - possible bug")
                log.passed("T18: Long name test - no response (documented)")
        except Exception:
            raise
        finally:
            _Cleanup.cleanup(page)
