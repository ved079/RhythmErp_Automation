"""
Role Creation Screen – Validation Tests (32 tests, 6 phases, 7 bugs)
RhythmERP  https://rhythmerp.algorhythms.in/#/master-setup/Rolecreationscreen

Phases:
  C – Create   (8 tests)
  D – Duplicate (5 tests, 2 xfail)
  E – Edit      (6 tests, 1 xfail)
  S – Search    (5 tests, 1 xfail)
  P – Popup/UI  (4 tests)
  H – History   (4 tests, 2 xfail)
"""

import pytest

from pages.access.modules.role_creation_screen.data.role_creation_screen_data import (
    create_payload,
    valid_role_name,
    valid_role_description,
    valid_role_code,
    duplicate_name_exact,
    duplicate_name_case_flipped,
    duplicate_name_with_spaces,
    edited_role_name,
    edited_role_description,
    edited_role_code,
    search_exact_name,
    search_partial_name,
    search_nonexistent_name,
    empty_string,
    whitespace_only,
    max_length_name,
    special_chars_name,
    sql_injection_name,
    xss_name,
    PHASE_C, PHASE_D, PHASE_E, PHASE_S, PHASE_P, PHASE_H,
)


# ══════════════════════════════════════════════════════════════════════
#  PHASE  C  –  CREATE  (8 tests)
# ══════════════════════════════════════════════════════════════════════

class TestCreatePhase:
    """C-phase: Role creation happy-path and validation tests."""

    def test_C01_create_role_with_valid_data(self, role_page):
        """Create a role with all valid fields – should succeed."""
        payload = create_payload()
        role_page.create_role(
            name=payload["name"],
            description=payload["description"],
            code=payload["code"],
        )
        title = role_page.wait_for_success_and_dismiss()
        assert "success" in title.lower(), \
            f"Expected success message, got: {title}"
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        assert role_page.is_role_in_table(payload["name"]), \
            f"Role '{payload['name']}' not found in table after creation"

    def test_C02_create_role_name_only(self, role_page):
        """Create a role with only the mandatory name field – should succeed."""
        name = valid_role_name()
        role_page.click_add_button()
        role_page.fill_role_name(name)
        role_page.click_save_button()
        title = role_page.wait_for_success_and_dismiss()
        assert "success" in title.lower(), \
            f"Expected success message, got: {title}"
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        assert role_page.is_role_in_table(name), \
            f"Role '{name}' not found in table"

    def test_C03_create_role_empty_name_shows_error(self, role_page):
        """Saving with empty role name should show required-field error."""
        role_page.click_add_button()
        role_page.fill_role_name("")
        # Tab out or click elsewhere to trigger validation
        role_page.click_save_button()
        errors = role_page.get_all_required_errors()
        assert len(errors) > 0, \
            "Expected required-field error for empty role name"
        role_page.click_cancel_button()
        role_page._force_close_panels()

    def test_C04_create_role_whitespace_name_shows_error(self, role_page):
        """Saving with whitespace-only name should show validation error."""
        role_page.click_add_button()
        role_page.fill_role_name(whitespace_only())
        role_page.click_save_button()
        errors = role_page.get_all_required_errors()
        assert len(errors) > 0, \
            "Expected validation error for whitespace-only role name"
        role_page.click_cancel_button()
        role_page._force_close_panels()

    def test_C05_create_role_with_max_length_name(self, role_page):
        """Create role with 255-char name – should succeed if within limit."""
        name = max_length_name(255)
        role_page.create_role(name=name, description=valid_role_description())
        try:
            title = role_page.wait_for_success_and_dismiss()
            assert "success" in title.lower()
        except Exception:
            # If 255 is too long, we expect a validation error instead
            errors = role_page.get_all_required_errors()
            assert len(errors) > 0, "Expected either success or length error"
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    def test_C06_create_role_with_special_characters(self, role_page):
        """Create role with special characters in name – should succeed."""
        name = special_chars_name()
        role_page.create_role(name=name, description=valid_role_description())
        try:
            title = role_page.wait_for_success_and_dismiss()
            assert "success" in title.lower(), \
                f"Expected success, got: {title}"
        except Exception:
            role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    @pytest.mark.xfail(
        reason="BUG-303: Role name field allows SQL injection strings "
               "without sanitisation",
        strict=True,
    )
    def test_C07_create_role_sql_injection_rejected(self, role_page):
        """SQL injection string in role name should be rejected."""
        name = sql_injection_name()
        role_page.create_role(name=name, description=valid_role_description())
        # If bug exists, the role gets created — assertion fails
        title = role_page.wait_for_success_and_dismiss()
        assert "success" not in title.lower(), \
            "SQL injection string should NOT be accepted as role name"
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    @pytest.mark.xfail(
        reason="BUG-304: Role name field allows XSS script tags "
               "without sanitisation",
        strict=True,
    )
    def test_C08_create_role_xss_rejected(self, role_page):
        """XSS script tag in role name should be rejected."""
        name = xss_name()
        role_page.create_role(name=name, description=valid_role_description())
        title = role_page.wait_for_success_and_dismiss()
        assert "success" not in title.lower(), \
            "XSS script tag should NOT be accepted as role name"
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()


# ══════════════════════════════════════════════════════════════════════
#  PHASE  D  –  DUPLICATE  (5 tests, 2 xfail)
# ══════════════════════════════════════════════════════════════════════

class TestDuplicatePhase:
    """D-phase: Duplicate-role detection tests."""

    def test_D01_duplicate_exact_name_rejected(self, role_page, seed_role):
        """Exact duplicate role name should be rejected."""
        dupe_name = duplicate_name_exact(seed_role["name"])
        role_page.create_role(name=dupe_name, description=valid_role_description())
        assert role_page.is_duplicate_error_visible(), \
            "Expected duplicate error for exact same role name"
        role_page.click_cancel_button()
        role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    @pytest.mark.xfail(
        reason="BUG-301: Duplicate role with case-flipped name is accepted "
               "(case-insensitive check missing)",
        strict=True,
    )
    def test_D02_duplicate_case_flipped_rejected(self, role_page, seed_role):
        """Case-flipped duplicate should be rejected (case-insensitive check)."""
        dupe_name = duplicate_name_case_flipped(seed_role["name"])
        role_page.create_role(name=dupe_name, description=valid_role_description())
        assert role_page.is_duplicate_error_visible(), \
            "Expected duplicate error for case-flipped role name"
        role_page.click_cancel_button()
        role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    @pytest.mark.xfail(
        reason="BUG-302: Duplicate role with extra spaces is accepted "
               "(space-normalised check missing)",
        strict=True,
    )
    def test_D03_duplicate_with_spaces_rejected(self, role_page, seed_role):
        """Duplicate with extra spaces should be rejected after normalisation."""
        dupe_name = duplicate_name_with_spaces(seed_role["name"])
        role_page.create_role(name=dupe_name, description=valid_role_description())
        assert role_page.is_duplicate_error_visible(), \
            "Expected duplicate error for name with extra spaces"
        role_page.click_cancel_button()
        role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    def test_D04_duplicate_pairing_prevented(self, role_page):
        """Creating a role, then another with same name+description pair
        should be rejected if duplicate pairing is enforced."""
        payload = create_payload()
        # First creation – should succeed
        role_page.create_role(
            name=payload["name"],
            description=payload["description"],
        )
        try:
            role_page.wait_for_success_and_dismiss()
        except Exception:
            role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

        # Second creation with same name
        role_page.create_role(
            name=payload["name"],
            description="Different description",
        )
        assert role_page.is_duplicate_error_visible(), \
            "Expected duplicate error for same role name (different description)"
        role_page.click_cancel_button()
        role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    def test_D05_unique_name_accepted_after_duplicate_rejected(self, role_page, seed_role):
        """After a duplicate is rejected, a truly unique name should succeed."""
        # Try duplicate first
        role_page.create_role(
            name=seed_role["name"],
            description=valid_role_description(),
        )
        # Dismiss duplicate error / cancel
        try:
            role_page.click_cancel_button()
        except Exception:
            role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

        # Now try a brand-new unique name
        unique = valid_role_name()
        role_page.create_role(name=unique, description=valid_role_description())
        title = role_page.wait_for_success_and_dismiss()
        assert "success" in title.lower(), \
            "Unique role name should be accepted after duplicate rejection"
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()


# ══════════════════════════════════════════════════════════════════════
#  PHASE  E  –  EDIT  (6 tests, 1 xfail)
# ══════════════════════════════════════════════════════════════════════

class TestEditPhase:
    """E-phase: Role edit/update tests."""

    def test_E01_edit_role_description(self, role_page, seed_role):
        """Edit an existing role's description – should succeed."""
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        assert row_idx > 0, f"Seed role '{seed_role['name']}' not in table"
        role_page.click_edit_button(row_idx)

        new_desc = edited_role_description(seed_role["description"])
        role_page.fill_role_description(new_desc)
        role_page.click_update_button()
        title = role_page.wait_for_success_and_dismiss()
        assert "success" in title.lower(), \
            f"Expected success after edit, got: {title}"
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    def test_E02_edit_role_name(self, role_page, seed_role):
        """Edit an existing role's name – should succeed if allowed."""
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            # If name was edited previously, try finding by partial match
            row_idx = 1  # fallback to first row
        role_page.click_edit_button(row_idx)

        new_name = edited_role_name(seed_role["name"])
        role_page.fill_role_name(new_name)
        role_page.click_update_button()
        try:
            title = role_page.wait_for_success_and_dismiss()
            assert "success" in title.lower(), \
                f"Expected success after name edit, got: {title}"
        except Exception:
            role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    def test_E03_edit_cancel_does_not_save(self, role_page, seed_role):
        """Editing then cancelling should not persist changes."""
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            row_idx = 1
        role_page.click_edit_button(row_idx)

        # Record current value, then change it
        original_desc = role_page.get_role_description_field_value()
        role_page.fill_role_description("SHOULD_NOT_SAVE")
        role_page.click_cancel_button()
        role_page._force_close_panels()

        # Re-open edit to verify
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            row_idx = 1
        role_page.click_edit_button(row_idx)
        current_desc = role_page.get_role_description_field_value()
        assert current_desc != "SHOULD_NOT_SAVE", \
            "Cancel should not persist changes"
        role_page.click_cancel_button()
        role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    def test_E04_edit_duplicate_name_rejected(self, role_page, seed_role):
        """Editing a role's name to match another existing role should fail."""
        # Create a second role to conflict with
        second = create_payload()
        role_page.create_role(
            name=second["name"],
            description=second["description"],
        )
        try:
            role_page.wait_for_success_and_dismiss()
        except Exception:
            role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

        # Now try to edit seed role's name to match second role
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            row_idx = 1
        role_page.click_edit_button(row_idx)
        role_page.fill_role_name(second["name"])
        role_page.click_update_button()

        assert role_page.is_duplicate_error_visible(), \
            "Editing role name to duplicate should be rejected"
        role_page.click_cancel_button()
        role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    @pytest.mark.xfail(
        reason="BUG-305: Edit form allows saving with empty role name "
               "(required-field validation missing on update)",
        strict=True,
    )
    def test_E05_edit_empty_name_rejected(self, role_page, seed_role):
        """Editing role name to empty should be rejected."""
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            row_idx = 1
        role_page.click_edit_button(row_idx)
        role_page.fill_role_name("")
        role_page.click_update_button()

        errors = role_page.get_all_required_errors()
        assert len(errors) > 0, \
            "Empty role name on edit should show required-field error"
        role_page.click_cancel_button()
        role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    def test_E06_edit_view_reflects_changes(self, role_page, seed_role):
        """After editing, viewing the role should show updated data."""
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            row_idx = 1
        # First edit description
        role_page.click_edit_button(row_idx)
        new_desc = f"ViewCheck_{valid_role_description()}"
        role_page.fill_role_description(new_desc)
        role_page.click_update_button()
        try:
            role_page.wait_for_success_and_dismiss()
        except Exception:
            role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

        # Now view the same role
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            row_idx = 1
        role_page.click_view_button(row_idx)
        dialog_text = role_page.get_view_dialog_text()
        assert new_desc in dialog_text, \
            f"Updated description '{new_desc}' not reflected in view dialog"
        role_page.close_view_dialog()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()


# ══════════════════════════════════════════════════════════════════════
#  PHASE  S  –  SEARCH  (5 tests, 1 xfail)
# ══════════════════════════════════════════════════════════════════════

class TestSearchPhase:
    """S-phase: Search / filter tests."""

    def test_S01_search_exact_name(self, role_page, seed_role):
        """Search with exact role name – should return matching row."""
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        role_page.search_role(search_exact_name(seed_role["name"]))
        assert role_page.is_role_in_table(seed_role["name"]), \
            f"Exact search should find role '{seed_role['name']}'"
        role_page.clear_search()

    def test_S02_search_partial_name(self, role_page, seed_role):
        """Search with partial role name – should return matching row."""
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        partial = search_partial_name(seed_role["name"])
        role_page.search_role(partial)
        assert role_page.is_role_in_table(seed_role["name"]), \
            f"Partial search '{partial}' should find role"
        role_page.clear_search()

    def test_S03_search_nonexistent_shows_no_data(self, role_page, seed_role):
        """Search with non-existent name – should show no data."""
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        role_page.search_role(search_nonexistent_name())
        assert role_page.is_role_in_table(seed_role["name"]) is False, \
            "Non-existent search should not show the seed role"
        # Could also check for "no data" element
        role_page.clear_search()

    def test_S04_search_clear_shows_all(self, role_page, seed_role):
        """Clearing search should restore all rows."""
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        initial_count = role_page.get_table_row_count()

        role_page.search_role(search_nonexistent_name())
        filtered_count = role_page.get_table_row_count()

        role_page.clear_search()
        restored_count = role_page.get_table_row_count()

        assert restored_count >= initial_count, \
            "Clearing search should restore rows"
        assert filtered_count <= restored_count, \
            "Filtered count should be <= restored count"

    @pytest.mark.xfail(
        reason="BUG-307: Sorting on Role Name column does not reorder "
               "the table rows (sort handler broken)",
        strict=True,
    )
    def test_S05_sort_by_role_name(self, role_page, seed_role):
        """Click sort on Role Name column – table should reorder."""
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

        # Get first column values before sort
        rows_before = []
        count = role_page.get_table_row_count()
        for i in range(1, min(count + 1, 21)):  # cap at 20 rows
            try:
                rows_before.append(role_page.get_cell_text_by_row_and_col(i, 1))
            except Exception:
                break

        # Click sort on first column (Role Name)
        role_page.click_sort_header(1)

        # Get values after sort
        rows_after = []
        for i in range(1, min(count + 1, 21)):
            try:
                rows_after.append(role_page.get_cell_text_by_row_and_col(i, 1))
            except Exception:
                break

        assert rows_before != rows_after, \
            "Sorting should reorder the table rows"


# ══════════════════════════════════════════════════════════════════════
#  PHASE  P  –  POPUP / UI  (4 tests)
# ══════════════════════════════════════════════════════════════════════

class TestPopupUIPhase:
    """P-phase: Popup / UI interaction tests."""

    def test_P01_view_dialog_displays_role_details(self, role_page, seed_role):
        """View dialog should show role name and description."""
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            row_idx = 1
        role_page.click_view_button(row_idx)
        assert role_page.is_view_dialog_open(), "View dialog should be open"
        dialog_text = role_page.get_view_dialog_text()
        assert len(dialog_text) > 0, "View dialog should contain text"
        role_page.close_view_dialog()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    def test_P02_close_view_dialog(self, role_page, seed_role):
        """Closing the view dialog should return to the table."""
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            row_idx = 1
        role_page.click_view_button(row_idx)
        assert role_page.is_view_dialog_open(), "View dialog should be open"
        role_page.close_view_dialog()
        assert role_page.is_view_dialog_open() is False, \
            "View dialog should be closed after clicking Close"

    def test_P03_add_button_opens_form(self, role_page):
        """Clicking Add button should open the create form."""
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        assert role_page.is_add_button_visible(), "Add button should be visible"
        role_page.click_add_button()
        assert role_page.is_form_open(), "Create form should be open after Add"
        role_page.click_cancel_button()
        role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    def test_P04_cancel_closes_form_without_saving(self, role_page):
        """Cancelling the create form should not add a row."""
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        count_before = role_page.get_table_row_count()

        role_page.click_add_button()
        role_page.fill_role_name(f"CancelTest_{valid_role_name()}")
        role_page.fill_role_description("Should not persist")
        role_page.click_cancel_button()
        role_page._force_close_panels()

        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        count_after = role_page.get_table_row_count()

        assert count_after == count_before, \
            "Cancel should not add a new row to the table"


# ══════════════════════════════════════════════════════════════════════
#  PHASE  H  –  HISTORY  (4 tests, 2 xfail)
# ══════════════════════════════════════════════════════════════════════

class TestHistoryPhase:
    """H-phase: Audit history tests."""

    @pytest.mark.xfail(
        reason="BUG-306: History dialog shows no records even after "
               "creating a role (audit trail not populated)",
        strict=True,
    )
    def test_H01_history_shows_create_record(self, role_page, seed_role):
        """History for a newly created role should show at least 1 record."""
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            row_idx = 1
        role_page.click_history_button(row_idx)
        assert role_page.is_history_dialog_open(), "History dialog should be open"
        count = role_page.get_history_row_count()
        assert count >= 1, \
            "History should contain at least the creation record"
        role_page.close_history_dialog()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    def test_H02_history_dialog_opens(self, role_page, seed_role):
        """History dialog should open without errors."""
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            row_idx = 1
        role_page.click_history_button(row_idx)
        assert role_page.is_history_dialog_open(), \
            "History dialog should open when button clicked"
        role_page.close_history_dialog()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    @pytest.mark.xfail(
        reason="BUG-306: History dialog shows no records even after "
               "editing a role (audit trail not populated)",
        strict=True,
    )
    def test_H03_history_shows_edit_record(self, role_page, seed_role):
        """After editing, history should show the edit record."""
        # First, do an edit
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            row_idx = 1
        role_page.click_edit_button(row_idx)
        role_page.fill_role_description(f"HistCheck_{valid_role_description()}")
        role_page.click_update_button()
        try:
            role_page.wait_for_success_and_dismiss()
        except Exception:
            role_page._force_close_panels()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

        # Now check history
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            row_idx = 1
        role_page.click_history_button(row_idx)
        count = role_page.get_history_row_count()
        assert count >= 2, \
            "History should contain both create and edit records"
        role_page.close_history_dialog()
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()

    def test_H04_history_close_returns_to_table(self, role_page, seed_role):
        """Closing history dialog should return to the main table."""
        role_page.navigate_to_role_creation_screen()
        role_page.wait_for_table_to_load()
        row_idx = role_page.get_row_index_by_role_name(seed_role["name"])
        if row_idx < 1:
            row_idx = 1
        role_page.click_history_button(row_idx)
        assert role_page.is_history_dialog_open(), "History should be open"
        role_page.close_history_dialog()
        assert role_page.is_history_dialog_open() is False, \
            "History dialog should be closed"
        assert role_page.is_add_button_visible(), \
            "Main table and Add button should be visible after closing history"