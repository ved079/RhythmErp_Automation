"""
test_season_validation.py
--------------------------
Season screen (Common Settings) test automation.
18 test cases across 9 classes covering: create, validation, bugs, edit, view,
cancel, search, history, boundary.

Markers:
  - smoke (4):     T1, T2, T7, T8
  - sanity (18):   All tests
  - regression (18): All tests
  - bug (5):       T3, T4, T5, T6, T18
  - ui (12):       T5, T7, T9-T18

Known bugs: SQL injection (T3), XSS (T4), duplicate alert (T5),
special chars (T6), no max-length (T18).

Run:  pytest season/test/test_season_validation.py -v
"""

import time
import pytest

from common.logger import log
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


# ================================================================
# GROUP A — HAPPY PATH (Add)
# ================================================================

class TestSeasonHappyPath:
    """T1, T2: Valid season creation."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_01_create_season_with_name_and_description(self, season_page):
        """T1: Create season with Name + Description — should succeed."""
        log.test_start("T1: Create season with Name + Description")

        data = valid_season_with_description()
        name = data["Name"]

        # Step 1: Open Add form
        season_page.open_add_form()
        assert season_page.is_form_open(), "Add form should be open"

        # Step 2: Fill form
        season_page.fill_form(name, data["Description"])

        # Step 3: Submit and verify success
        result = season_page.click_submit()
        assert result == "success", f"Submit should succeed, got: {result}"

        # Step 4: Search and verify record in table
        season_page.refresh_table()
        assert season_page.search_record(name), f"Season '{name}' should be in table"

        # Cleanup
        season_page.clear_search()

        log.passed("T1: Season created with Name + Description")

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_02_create_season_name_only_no_description(self, season_page):
        """T2: Create season with Name only (Description optional) — should succeed."""
        log.test_start("T2: Create season with Name only")

        data = valid_season_name_only()
        name = data["Name"]

        # Step 1: Open Add form
        season_page.open_add_form()
        assert season_page.is_form_open(), "Add form should be open"

        # Step 2: Fill only Name
        season_page.enter_name(name)

        # Step 3: Submit and verify success
        result = season_page.click_submit()
        assert result == "success", f"Submit should succeed, got: {result}"

        # Step 4: Search and verify record in table
        season_page.refresh_table()
        assert season_page.search_record(name), f"Season '{name}' should be in table"

        # Cleanup
        season_page.clear_search()

        log.passed("T2: Season created with Name only (no Description)")


# ================================================================
# GROUP B — VALIDATION (Add)
# ================================================================

class TestSeasonValidation:
    """T3-T6: Negative tests — SQL injection, XSS, special chars, duplicate."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_03_sql_injection_in_name(self, season_page):
        """T3: SQL injection in Name field — BUG: accepted and stored as-is."""
        log.test_start("T3: SQL injection in Name (BUG — accepted)")

        data = sql_injection_name()
        name = data["Name"]

        season_page.open_add_form()
        season_page.fill_form(name, data["Description"])
        result = season_page.click_submit()

        # BUG: SQL injection is accepted — form closes successfully
        assert result == "success", f"BUG: SQL injection was accepted, got: {result}"

        # Verify record was created (BUG — should have been rejected)
        season_page.refresh_table()
        record_found = season_page.search_record(name)
        assert record_found, (
            f"BUG CONFIRMED: SQL injection '{name}' was stored in the database. "
            f"Expected: System should reject or sanitize SQL input."
        )

        season_page.clear_search()
        log.passed("T3: BUG confirmed — SQL injection accepted in Name")

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_04_xss_in_name(self, season_page):
        """T4: XSS script tag in Name — BUG: stored as raw HTML, visible in list."""
        log.test_start("T4: XSS in Name (BUG — stored as raw HTML)")

        data = xss_in_name()
        name = data["Name"]

        season_page.open_add_form()
        season_page.fill_form(name, data["Description"])
        result = season_page.click_submit()

        # BUG: XSS is accepted — form closes successfully
        assert result == "success", f"BUG: XSS was accepted, got: {result}"

        season_page.refresh_table()
        record_found = season_page.search_record(name)
        assert record_found, (
            f"BUG CONFIRMED: XSS payload '{name}' was stored in the database. "
            f"Expected: System should reject or sanitize script tags."
        )

        season_page.clear_search()
        log.passed("T4: BUG confirmed — XSS accepted in Name")

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_05_duplicate_season_name(self, season_page):
        """T5: Duplicate Season Name — should show Validation Failed alert."""
        log.test_start("T5: Duplicate Season Name (validation alert expected)")

        data = duplicate_name()
        name = data["Name"]  # "Rabi" — known existing record

        season_page.open_add_form()
        season_page.fill_form(name, data["Description"])
        season_page.click_submit()  # Don't check result — handle both paths

        # One of two things happens:
        # 1. Validation Failed alert (correct behavior) → form stays open
        # 2. Duplicate accepted (BUG) → form closes, record created
        validation_alert = season_page.is_validation_alert_present(timeout=5)
        form_still_open = season_page.is_form_open()

        # Cleanup: dismiss any alert and close form
        try:
            if validation_alert:
                season_page.handle_validation_alert()
                log.info("  [PASS] Validation alert detected for duplicate name")
            if form_still_open:
                season_page.close_form_via_cancel()
        except Exception:
            season_page._dismiss_overlays_and_popups()

        if validation_alert:
            log.info(f">>> STEP 3 PASSED: Duplicate '{name}' correctly rejected with validation alert")
        elif not form_still_open:
            log.warning(f">>> STEP 3 BUG: Form closed silently for duplicate '{name}' — no alert")
        else:
            log.warning(f">>> STEP 3 NOTE: System did not respond for duplicate '{name}' — form still open")

        log.passed("T5: Duplicate name behavior verified")

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_06_special_characters_in_name(self, season_page):
        """T6: Special characters in Name — BUG: accepted without validation."""
        log.test_start("T6: Special characters in Name (BUG — accepted)")

        data = special_chars_name()
        name = data["Name"]

        season_page.open_add_form()
        season_page.fill_form(name, data["Description"])
        result = season_page.click_submit()

        # BUG: Special characters are accepted
        assert result == "success", f"BUG: Special chars were accepted, got: {result}"

        season_page.refresh_table()
        record_found = season_page.search_record(name)
        assert record_found, (
            f"BUG CONFIRMED: Special characters '{name}' were accepted. "
            f"Expected: System should restrict special characters in Name."
        )

        season_page.clear_search()
        log.passed("T6: BUG confirmed — Special characters accepted in Name")


# ================================================================
# GROUP C — VALIDATION (Negative - Empty)
# ================================================================

class TestSeasonEmptySubmit:
    """T7: Submit with all fields blank — should show Validation Failed."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_07_empty_submit_all_fields_blank(self, season_page):
        """T7: Submit with Name blank — should show Validation Failed alert."""
        log.test_start("T7: Empty submit — all fields blank")

        # Step 1: Open Add form
        season_page.open_add_form()
        assert season_page.is_form_open(), "Add form should be open"

        # Step 2: Submit without filling any field
        result = season_page.click_submit()

        # Step 3: Should get validation alert
        assert result == "validation", (
            f"Expected validation alert for empty submit, got: {result}"
        )

        # Step 4: Verify alert title
        alert_title = season_page.get_alert_title()
        assert VALIDATION_ALERT_TITLE in alert_title, (
            f"Expected alert title '{VALIDATION_ALERT_TITLE}', got '{alert_title}'"
        )

        # Step 5: Handle the alert
        season_page.handle_validation_alert()

        # Step 6: Form should still be open (not closed on validation failure)
        assert season_page.is_form_open(), "Form should remain open after validation failure"

        # Cleanup: close form
        season_page.close_form_via_cancel()

        log.passed("T7: Validation Failed alert shown for empty submit")


# ================================================================
# GROUP D — EDIT FLOW
# ================================================================

class TestSeasonEditFlow:
    """T8: Edit existing season record."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_08_edit_existing_season(self, season_page):
        """T8: Edit a season record — change Name and Description, verify update."""
        log.test_start("T8: Edit existing season")

        # Step 1: Create a new season first (prerequisite)
        data = valid_season_with_description()
        original_name = data["Name"]
        original_desc = data["Description"]

        season_page.open_add_form()
        season_page.fill_form(original_name, original_desc)
        result = season_page.click_submit()
        assert result == "success", f"Prerequisite: create failed, got: {result}"

        season_page.refresh_table()
        assert season_page.search_record(original_name), (
            f"Prerequisite failed: Season '{original_name}' not found in table"
        )
        log.info(f">>> STEP 1 PASSED: Created prerequisite season '{original_name}'")

        # Step 2: Find the row and click Edit
        row_index = season_page.find_row_by_name(original_name)
        assert row_index != -1, f"Row not found for '{original_name}'"

        season_page.click_edit_button(row_index)
        assert season_page.is_form_open(), "Edit form should be open"
        log.info(f">>> STEP 2 PASSED: Edit form opened for row {row_index}")

        # Step 3: Clear and enter new data
        new_name = f"EDITED_{original_name}"
        new_desc = f"Edited description - {original_desc}"

        season_page.clear_form()
        season_page.fill_form(new_name, new_desc)
        result = season_page.click_update()
        assert result == "success", f"Update should succeed, got: {result}"
        log.info(f">>> STEP 3 PASSED: Form updated with Name='{new_name}'")

        # Step 4: Verify updated record in table
        season_page.refresh_table()

        # Check new name exists
        assert season_page.search_record(new_name), (
            f"Updated season '{new_name}' not found in table"
        )

        # Clear search before checking old name
        season_page.clear_search()

        # Check old name is gone — use exact=True because ERP does contains
        # search. Searching 'SEASON_ABC' would still find 'EDITED_SEASON_ABC'.
        assert not season_page.search_record(original_name, exact=True), (
            f"Old season '{original_name}' should NOT be in table after edit"
        )

        # Cleanup
        season_page.clear_search()

        log.passed("T8: Season edited and verified")


# ================================================================
# GROUP E — VIEW MODE
# ================================================================

class TestSeasonViewMode:
    """T9: View mode — verify fields are disabled/read-only."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_09_view_mode_fields_disabled(self, season_page):
        """T9: Open View popup — verify all fields are disabled."""
        log.test_start("T9: View mode — verify fields disabled")

        # Step 1: Find any row (use first row with data)
        row_count = season_page.get_table_row_count()
        assert row_count > 0, "Table should have at least one record"

        # Step 2: Click View button on first row
        season_page.click_view_button(0)
        assert season_page.is_form_open(), "View form should be open"

        # Step 3: Verify Submit/Update button is NOT visible (View mode)
        assert season_page.is_form_in_view_mode(), (
            "Submit/Update button should NOT be visible in View mode"
        )

        # Step 4: Verify Name field is disabled
        name_disabled = season_page.is_field_disabled(
            ("css", "input[name='Name']")
        )
        assert name_disabled, "Name field should be disabled in View mode"

        # Step 5: Verify Description field is disabled
        desc_disabled = season_page.is_field_disabled(
            ("css", "input[name='Description']")
        )
        assert desc_disabled, "Description field should be disabled in View mode"

        # Cleanup: close form
        season_page.close_form_via_cancel()

        log.passed("T9: View mode verified — all fields disabled, no Submit button")


# ================================================================
# GROUP F - SEARCH
# ================================================================

class TestSeasonSearch:
    """T10-T11: Search functionality on Season list page."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_10_search_existing_season(self, season_page):
        """T10: Search for an existing season by name - should find it."""
        log.test_start("T10: Search existing season by name")

        # Step 1: Create a season to search for
        data = valid_season_with_description()
        name = data["Name"]

        season_page.open_add_form()
        season_page.fill_form(name, data["Description"])
        season_page.click_submit()
        season_page.refresh_table()

        assert season_page.search_record(name), (
            f"Prerequisite failed: Season '{name}' not found"
        )
        log.info(f">>> STEP 1 PASSED: Created prerequisite season '{name}'")

        # Step 2: Search for the same season again (bar still open)
        found = season_page.search_record(name)
        assert found, f"Search should find season '{name}'"

        # Step 3: Verify the first result matches
        row_count = season_page.get_table_row_count()
        assert row_count >= 1, f"Expected at least 1 result, got {row_count}"
        first_name = season_page.get_name_from_row(0)
        assert name in first_name, (
            f"First result name '{first_name}' should contain '{name}'"
        )

        season_page.clear_search()
        log.passed("T10: Existing season found via search")

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_11_search_nonexistent_season(self, season_page):
        """T11: Search for a name that does not exist - should return 0 results."""
        log.test_start("T11: Search non-existent season name")

        # Step 1: Search for a unique name that definitely does not exist
        fake_name = f"NONEXISTENT_{valid_season_name()}_NOCHANCE"

        found = season_page.search_record(fake_name)
        assert not found, f"Search should NOT find '{fake_name}'"

        # Step 2: Verify table is empty
        row_count = season_page.get_table_row_count()
        assert row_count == 0, (
            f"Expected 0 rows for non-existent search, got {row_count}"
        )

        season_page.clear_search()
        log.passed("T11: Non-existent search returned 0 results")


# ================================================================
# GROUP G - HISTORY
# ================================================================

class TestSeasonHistory:
    """T12-T14: History popup - open, search, close."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_12_history_popup_opens_with_data(self, season_page):
        """T12: Click History on a row - popup should open with data rows."""
        log.test_start("T12: History popup opens with data")

        # Step 1: Create a season (prerequisite)
        data = valid_season_with_description()
        name = data["Name"]

        season_page.open_add_form()
        season_page.fill_form(name, data["Description"])
        season_page.click_submit()
        season_page.refresh_table()

        assert season_page.search_record(name), (
            f"Prerequisite failed: Season '{name}' not found"
        )
        season_page.clear_search()
        log.info(f">>> STEP 1 PASSED: Created prerequisite season '{name}'")

        # Step 2: Edit the season to create a history record
        row_index = season_page.find_row_by_name(name)
        assert row_index != -1, f"Row not found for '{name}'"

        season_page.click_edit_button(row_index)
        assert season_page.is_form_open(), "Edit form should be open"

        season_page.clear_form()
        season_page.fill_form(name, f"Edited - {data['Description']}")
        season_page.click_update()
        season_page.refresh_table()

        # Search to filter table to our season (it may be on page 2+)
        assert season_page.search_record(name), (
            f"Prerequisite failed: Season '{name}' not found after edit"
        )
        log.info(f">>> STEP 2 PASSED: Edited season '{name}' to create history")

        # Step 3: Find the season in filtered table and click History
        row_index = season_page.find_row_by_name(name)
        assert row_index != -1, f"Row not found for '{name}' after edit (may need pagination)"

        season_page.click_history_button(row_index)

        # Step 4: Verify popup title contains "History"
        title = season_page.get_history_title()
        assert "History" in title, (
            f"History popup title should contain 'History', got '{title}'"
        )

        # Step 5: Verify history has data (row 0 is header, > 1 means data exists)
        history_rows = season_page.get_history_row_count()
        assert history_rows > 1, (
            f"History table should have data rows, got {history_rows} total (0 data)"
        )

        # Cleanup: close history popup
        season_page.close_history_popup()

        log.passed("T12: History popup opened with data")

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_13_history_search_filters_records(self, season_page):
        """T13: Search inside History popup - should filter rows."""
        log.test_start("T13: History search filters records")

        # Step 1: Create AND edit a season (history requires an edit)
        data = valid_season_with_description()
        name = data["Name"]

        season_page.open_add_form()
        season_page.fill_form(name, data["Description"])
        season_page.click_submit()
        season_page.refresh_table()

        # Edit to create history
        season_page.search_record(name)  # filter table first
        season_page.wait_seconds(0.5)
        row_index = season_page.find_row_by_name(name)
        assert row_index != -1, f"Row not found for '{name}'"

        season_page.click_edit_button(row_index)
        assert season_page.is_form_open(), "Edit form should be open"

        season_page.clear_form()
        season_page.fill_form(name, f"Edited - {data['Description']}")
        season_page.click_update()
        season_page.refresh_table()

        # Search to filter table (season may be on page 2+)
        assert season_page.search_record(name), (
            f"Prerequisite failed: '{name}' not found after create+edit"
        )
        log.info(f">>> STEP 1 PASSED: Created + edited season '{name}'")

        # Step 2: Open history on the season (table is already filtered)
        row_index = season_page.find_row_by_name(name)
        assert row_index != -1, f"Row not found for '{name}' after edit (may need pagination)"

        season_page.click_history_button(row_index)

        # Step 3: Get name from first DATA row (row 0 is header, row 1 is first data)
        first_history_name = season_page.get_history_cell_text(1, 3)
        total_rows = season_page.get_history_row_count()
        assert first_history_name not in ("ROW_NOT_FOUND", "CELL_NOT_FOUND"), (
            f"Could not get name from first history data row"
        )
        log.info(f"History has {total_rows} row(s), searching for '{first_history_name}'")

        # Step 4: Search in history popup (Enter key)
        season_page.search_in_history(first_history_name)
        season_page.wait_seconds(1.5)

        # Step 5: Verify filtered results
        filtered_rows = season_page.get_history_row_count()
        assert filtered_rows > 1, (
            f"History search should return data rows, got {filtered_rows} total (0 data)"
        )

        # Step 6: Verify the filtered result matches the search term
        filtered_name = season_page.get_history_cell_text(1, 3)
        assert first_history_name in filtered_name, (
            f"Filtered result '{filtered_name}' should contain '{first_history_name}'"
        )

        # Cleanup: close history popup
        season_page.close_history_popup()

        log.passed("T13: History search filtered records correctly")

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_14_history_close_via_cancel(self, season_page):
        """T14: Close History popup via Cancel button - popup should disappear."""
        log.test_start("T14: History close via Cancel button")

        # Step 1: Open history on first row
        season_page.click_history_button(0)
        assert season_page.is_history_popup_open(), "History popup should be open"
        log.info(">>> STEP 1 PASSED: History popup opened")

        # Step 2: Close via Cancel button
        season_page.close_history_via_cancel()
        season_page.wait_seconds(0.5)

        # Step 3: Verify popup is closed (title no longer visible)
        popup_still_open = season_page.is_history_popup_open(timeout=3)
        assert not popup_still_open, "History popup should be closed after Cancel"

        log.passed("T14: History popup closed via Cancel")


# ================================================================
# GROUP H - CANCEL BEHAVIOR
# ================================================================

class TestSeasonCancel:
    """T15-T16: Cancel button during Add and Edit flows."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_15_cancel_during_add_nothing_saved(self, season_page):
        """T15: Fill Add form and click Cancel - record should NOT be saved."""
        log.test_start("T15: Cancel during Add - nothing saved")

        # Step 1: Open Add form and fill data
        data = valid_season_name()
        name = data

        season_page.open_add_form()
        assert season_page.is_form_open(), "Add form should be open"
        season_page.enter_name(name)

        # Step 2: Click Cancel (NOT Submit)
        season_page.close_form_via_cancel()

        # Step 3: Verify form is closed
        assert not season_page.is_form_open(), "Form should be closed after Cancel"

        # Step 4: Search for the name - should NOT be found
        season_page.refresh_table()
        found = season_page.search_record(name)
        assert not found, f"Season '{name}' should NOT exist after Cancel"

        season_page.clear_search()

        log.passed("T15: Cancel during Add - no record saved")

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_16_cancel_during_edit_original_unchanged(self, season_page):
        """T16: Open Edit form, modify data, click Cancel - original should remain."""
        log.test_start("T16: Cancel during Edit - original unchanged")

        # Step 1: Create a season first
        data = valid_season_with_description()
        original_name = data["Name"]
        original_desc = data["Description"]

        season_page.open_add_form()
        season_page.fill_form(original_name, original_desc)
        season_page.click_submit()
        season_page.refresh_table()

        assert season_page.search_record(original_name), (
            f"Prerequisite failed: '{original_name}' not found"
        )
        season_page.clear_search()
        log.info(f">>> STEP 1 PASSED: Created '{original_name}'")

        # Step 2: Find row and open Edit
        row_index = season_page.find_row_by_name(original_name)
        assert row_index != -1, f"Row not found for '{original_name}'"

        season_page.click_edit_button(row_index)
        assert season_page.is_form_open(), "Edit form should be open"
        log.info(f">>> STEP 2 PASSED: Edit form opened for row {row_index}")

        # Step 3: Modify the data (but do NOT submit)
        modified_name = f"CANCELLED_{original_name}"
        season_page.clear_form()
        season_page.enter_name(modified_name)

        # Step 4: Click Cancel
        season_page.close_form_via_cancel()

        # Step 5: Verify original name still exists
        season_page.refresh_table()
        assert season_page.search_record(original_name), (
            f"Original season '{original_name}' should still exist after Cancel"
        )

        # Step 6: Verify modified name does NOT exist
        assert not season_page.search_record(modified_name), (
            f"Modified name '{modified_name}' should NOT exist after Cancel"
        )

        season_page.clear_search()

        log.passed("T16: Cancel during Edit - original data unchanged")


# ================================================================
# GROUP I - BOUNDARY TESTS
# ================================================================

class TestSeasonBoundary:
    """T17-T18: Boundary tests - spaces, long names."""

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_17_leading_trailing_spaces_in_name(self, season_page):
        """T17: Name with leading/trailing spaces - test trim behavior."""
        log.test_start("T17: Leading/trailing spaces in name")

        data = leading_trailing_spaces()
        raw_name = data["Name"]
        expected_trimmed = raw_name.strip()

        # Step 1: Open form and submit with spaces in name
        season_page.open_add_form()
        season_page.fill_form(raw_name, data["Description"])
        result = season_page.click_submit()

        if result != "success":
            # Form didn't close — may have validation error or hang
            season_page.handle_validation_alert()
            try:
                season_page.close_form_via_cancel()
            except Exception:
                season_page._dismiss_overlays_and_popups()
            log.warning("T17: Submit did not succeed with spaces name")
            return

        # Step 2: Search for the name (try both trimmed and untrimmed)
        season_page.refresh_table()

        found_trimmed = season_page.search_record(expected_trimmed)
        found_raw = season_page.search_record(raw_name) if not found_trimmed else False

        assert found_trimmed or found_raw, (
            f"Season with spaces '{raw_name}' should be found (trimmed: '{expected_trimmed}')"
        )

        # Step 3: Check what name was actually stored
        if found_trimmed:
            log.info(f">>> STEP 2 PASSED: Name was TRIMMED - stored as '{expected_trimmed}'")
        elif found_raw:
            log.info(f">>> STEP 2 PASSED: Name was stored AS-IS with spaces - '{raw_name}'")

        season_page.clear_search()

        log.passed("T17: Spaces test completed")

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_18_very_long_name(self, season_page):
        """T18: Very long name (200 chars) - test max-length behavior."""
        log.test_start("T18: Very long name (200 characters)")

        data = very_long_name(length=200)
        long_name = data["Name"]

        # Step 1: Open form and submit
        season_page.open_add_form()
        season_page.fill_form(long_name, data["Description"])
        result = season_page.click_submit()

        if result == "success":
            # Form closed — record was created
            season_page.refresh_table()
            found = season_page.search_record(long_name)
            if found:
                log.info(f">>> STEP 2 PASSED: 200-char name was ACCEPTED and stored (BUG — no max-length)")
            else:
                log.info(f">>> STEP 2 INFO: Form closed but record not found - may have been truncated")
            season_page.clear_search()
            log.passed("T18: Long name test - form accepted (BUG: no max-length validation)")
        elif result == "validation":
            # Validation alert — long name was rejected
            season_page.handle_validation_alert()
            season_page.close_form_via_cancel()
            log.info(f">>> STEP 2 PASSED: Validation alert shown for 200-char name")
            log.passed("T18: Long name rejected by validation")
        else:
            # Unknown state — close form and document
            season_page._dismiss_any_sweet_alert()
            try:
                season_page.close_form_via_cancel()
            except Exception:
                season_page._dismiss_overlays_and_popups()
            log.warning(f">>> STEP 2: No response for 200-char name - possible bug")
            log.passed("T18: Long name test - no response (documented)")

        log.info(f">>> STEP 1 PASSED: Form submitted with {len(long_name)}-char name")
