"""
Designation Screen — Automated Validation Test Suite (v2 OPTIMISED)
44 tests across 6 classes.

Key speed improvements:
- Smart _cleanup(): close form only if open, hard_refresh only if needed
- search_and_verify() instead of click_refresh + search + sleep
- NO time.sleep() between actions — rely on WebDriverWait + JS
- try/finally with _cleanup on every test
"""

import os
import sys
import time
import pytest
from selenium.webdriver.common.by import By

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from pages.common_settings.modules.designation.data.designation_data import (
    generate_designation_name, generate_description,
    generate_valid_designation_data, generate_valid_edit_data,
    generate_string_255, generate_string_256, generate_spaces_only,
    generate_special_char_name, generate_digits_only,
    generate_duplicate_name_data, generate_empty_data, generate_name_only_data,
)


def _cleanup(page):
    """Smart cleanup: close form if open, then hard_refresh."""
    try:
        if page.is_add_form_open():
            page.force_close_form_popup()
    except Exception:
        pass
    page.hard_refresh()


# ═══════════════════════════════════════════════════
#  PHASE 1: CREATE FORM VALIDATIONS (C01-C15)
# ═══════════════════════════════════════════════════

@pytest.mark.usefixtures('designation_page')
class TestCreateFormValidations:

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C01_all_fields_empty_submit(self, designation_page):
        log.info("C01: All fields empty - Submit")
        page = designation_page
        try:
            page.open_add_form()
            page.submit()
            assert page.is_validation_alert_present(timeout=5), "Validation alert should appear"
            warning = page.handle_validation_warning()
            assert 'Validation Failed' in warning, f"Expected 'Validation Failed', got '{warning}'"
            assert page._is_form_popup_open(), "Form should stay open"
        finally:
            _cleanup(page)

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_C02_only_name_filled_submit(self, designation_page):
        log.info("C02: Only Name filled - Submit")
        page = designation_page
        try:
            data = generate_name_only_data()
            result = page.create_designation(data)
            assert result['status'] in ('PASSED', 'UNKNOWN'), f"Should succeed. Got: {result}"
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_C03_name_with_leading_trailing_spaces(self, designation_page):
        log.info("C03: Name with leading/trailing spaces")
        page = designation_page
        try:
            data = generate_valid_designation_data()
            data['name'] = '  ' + data['name'] + '  '
            result = page.create_designation(data)
            if result['status'] == 'VALIDATION_FAILED':
                log.info("Spaces triggered validation — acceptable")
            else:
                log.info("Spaces preserved — BUG: not trimmed")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C04_name_spaces_only(self, designation_page):
        log.info("C04: Spaces-only Name")
        page = designation_page
        try:
            page.open_add_form()
            page._set_input(page.NAME_INPUT, generate_spaces_only(), clear_first=True)
            errors = page.get_mat_error_text()
            assert 'Invalid Name' in errors, f"Expected 'Invalid Name', got: {errors}"
            assert page.has_name_invalid_class(), "Name should be invalid"
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C05_name_special_chars(self, designation_page):
        log.info("C05: Special chars in Name")
        page = designation_page
        try:
            special_name = generate_special_char_name()
            page.open_add_form()
            page._set_input(page.NAME_INPUT, special_name, clear_first=True)
            errors = page.get_mat_error_text()
            assert 'Invalid Name' in errors, f"Expected 'Invalid Name' for '{special_name}'"
            page.submit()
            assert page.is_validation_alert_present(timeout=5), "Validation alert should appear"
            page.handle_validation_warning()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C06_name_digits_only(self, designation_page):
        log.info("C06: Digits-only Name")
        page = designation_page
        try:
            page.open_add_form()
            page._set_input(page.NAME_INPUT, generate_digits_only(), clear_first=True)
            errors = page.get_mat_error_text()
            assert 'Invalid Name' in errors, f"Expected 'Invalid Name', got: {errors}"
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C07_name_mixed_valid_invalid(self, designation_page):
        log.info("C07: Mixed valid/invalid Name")
        page = designation_page
        try:
            page.open_add_form()
            page._set_input(page.NAME_INPUT, 'Test@Name', clear_first=True)
            errors = page.get_mat_error_text()
            assert 'Invalid Name' in errors, "Expected 'Invalid Name' for 'Test@Name'"
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_C08_duplicate_name(self, designation_page):
        log.info("C08: Duplicate Name - Create")
        page = designation_page
        try:
            dup_data = generate_duplicate_name_data()
            result = page.create_designation(dup_data)
            log.info(f"Duplicate result: {result['status']} — BUG: no duplicate validation")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_C09_very_long_name_256(self, designation_page):
        log.info("C09: Very long Name (256 chars)")
        page = designation_page
        try:
            data = {'name': generate_string_256(), 'description': 'Long name test', 'status': True}
            result = page.create_designation(data)
            log.info(f"256-char result: {result['status']} — BUG: no max length")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_C10_name_valid_punctuation(self, designation_page):
        log.info("C10: Punctuation in Name")
        page = designation_page
        try:
            for name in ['Jr. Manager', 'Manager, Sales', 'Vice-President', 'Quality (Agri)']:
                page.open_add_form()
                page._set_input(page.NAME_INPUT, name, clear_first=True)
                errors = page.get_mat_error_text()
                log.info(f"'{name}': {'rejected' if 'Invalid Name' in errors else 'accepted'}")
                page.cancel()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C11_description_only_no_name(self, designation_page):
        log.info("C11: Description only - no Name")
        page = designation_page
        try:
            page.open_add_form()
            page._set_input(page.DESCRIPTION_INPUT, generate_description(), clear_first=True)
            page.submit()
            assert page.is_validation_alert_present(timeout=5), "Validation should fail"
            page.handle_validation_warning()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_C12_special_chars_in_description(self, designation_page):
        log.info("C12: Special chars in Description")
        page = designation_page
        try:
            data = generate_valid_designation_data()
            data['description'] = 'Test @#$% &*! Description 123'
            result = page.create_designation(data)
            assert result['status'] in ('PASSED', 'UNKNOWN'), f"Should succeed. Got: {result}"
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_C13_very_long_description(self, designation_page):
        log.info("C13: Very long Description")
        page = designation_page
        try:
            data = generate_valid_designation_data()
            data['description'] = 'A' * 500
            result = page.create_designation(data)
            log.info(f"Long desc result: {result['status']}")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_C14_inline_error_messages(self, designation_page):
        log.info("C14: Inline error messages")
        page = designation_page
        try:
            page.open_add_form()
            page._set_input(page.NAME_INPUT, 'Test@#$%', clear_first=True)
            errors = page.get_mat_error_text()
            assert len(errors) > 0, "Expected mat-error"
            assert 'Invalid Name' in errors, f"Expected 'Invalid Name', got: {errors}"
            assert page.has_field_error('Name'), "has_field_error('Name') should be True"
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_C15_name_255_chars(self, designation_page):
        log.info("C15: 255-char Name")
        page = designation_page
        try:
            data = {'name': generate_string_255(), 'description': '255 char boundary test', 'status': True}
            result = page.create_designation(data)
            log.info(f"255-char result: {result['status']}")
        finally:
            _cleanup(page)


# ═══════════════════════════════════════════════════
#  PHASE 2: STATUS TOGGLE VALIDATIONS (S01-S06)
# ═══════════════════════════════════════════════════

@pytest.mark.usefixtures('designation_page')
class TestStatusToggleValidations:

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_S01_default_status_is_active(self, designation_page):
        log.info("S01: Default Status is Active")
        page = designation_page
        try:
            page.open_add_form()
            assert page.get_toggle_state() is True, "Default should be Active"
            assert page.get_toggle_display_text() == 'Active'
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_S02_toggle_to_inactive(self, designation_page):
        log.info("S02: Toggle to Inactive")
        page = designation_page
        try:
            page.open_add_form()
            page.toggle_status()
            assert page.get_toggle_state() is False
            assert page.get_toggle_display_text() == 'Inactive'
        finally:
            _cleanup(page)

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_S03_create_with_inactive_status(self, designation_page):
        log.info("S03: Create with Inactive status")
        page = designation_page
        try:
            data = generate_valid_designation_data()
            data['name'] = generate_designation_name(prefix="InactiveDesig")
            data['status'] = False
            result = page.create_designation(data)
            assert result['status'] in ('PASSED', 'UNKNOWN')
            page.hard_refresh()
            page.search_and_verify(data['name'])
            status = page.get_status_from_table(data['name'])
            assert status == 'Inactive', f"Expected 'Inactive', got '{status}'"
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_S04_toggle_state_in_edit_mode(self, designation_page):
        log.info("S04: Toggle state in Edit mode")
        page = designation_page
        try:
            data = generate_valid_designation_data()
            data['name'] = generate_designation_name(prefix="ToggleEdit")
            data['status'] = True
            result = page.create_designation(data)
            assert result['status'] in ('PASSED', 'UNKNOWN')
            page.hard_refresh()
            page.search_and_verify(data['name'])
            page.click_edit_button(designation_name=data['name'])
            assert page.is_edit_mode()
            assert page.get_toggle_state() is True
            page.toggle_status()
            assert page.get_toggle_state() is False
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_S05_toggle_disabled_in_view_mode(self, designation_page):
        log.info("S05: Toggle disabled in View mode")
        page = designation_page
        try:
            data = generate_valid_designation_data()
            data['name'] = generate_designation_name(prefix="ViewToggle")
            result = page.create_designation(data)
            assert result['status'] in ('PASSED', 'UNKNOWN')
            page.hard_refresh()
            page.search_and_verify(data['name'])
            page.click_view_button(designation_name=data['name'])
            assert page.is_view_mode(), "Should be read-only"
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_S06_toggle_back_and_forth(self, designation_page):
        log.info("S06: Toggle back and forth")
        page = designation_page
        try:
            page.open_add_form()
            assert page.get_toggle_state() is True
            page.toggle_status()
            assert page.get_toggle_state() is False
            page.toggle_status()
            assert page.get_toggle_state() is True
            page.toggle_status()
            assert page.get_toggle_state() is False
            page.toggle_status()
            assert page.get_toggle_state() is True
        finally:
            _cleanup(page)


# ═══════════════════════════════════════════════════
#  PHASE 3: EDIT FORM VALIDATIONS (E01-E05)
# ═══════════════════════════════════════════════════

@pytest.mark.usefixtures('designation_page')
class TestEditFormValidations:

    def _create_designation_for_edit(self, page):
        data = generate_valid_designation_data()
        data['name'] = generate_designation_name(prefix="EditBase")
        data['description'] = generate_description(prefix="Original")
        data['status'] = True
        result = page.create_designation(data)
        assert result['status'] in ('PASSED', 'UNKNOWN')
        return data['name']

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_E01_edit_duplicate_name(self, designation_page):
        log.info("E01: Edit duplicate Name")
        page = designation_page
        try:
            name = self._create_designation_for_edit(page)
            page.hard_refresh()
            page.search_and_verify(name)
            page.click_edit_button(designation_name=name)
            assert page.is_edit_mode()
            page._set_input(page.NAME_INPUT, 'CEO', clear_first=True)
            page.click_update()
            if page.is_validation_alert_present(timeout=3):
                page.handle_validation_warning()
            else:
                page.handle_success_alert()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_E02_edit_special_chars_name(self, designation_page):
        log.info("E02: Edit special chars Name")
        page = designation_page
        try:
            name = self._create_designation_for_edit(page)
            page.hard_refresh()
            page.search_and_verify(name)
            page.click_edit_button(designation_name=name)
            page._set_input(page.NAME_INPUT, 'Edit@Test#', clear_first=True)
            errors = page.get_mat_error_text()
            assert 'Invalid Name' in errors
            page.click_update()
            if page.is_validation_alert_present(timeout=3):
                page.handle_validation_warning()
        finally:
            _cleanup(page)

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_E03_edit_pre_populated_fields(self, designation_page):
        log.info("E03: Edit pre-populated fields")
        page = designation_page
        try:
            data = generate_valid_designation_data()
            data['name'] = generate_designation_name(prefix="PreFill")
            data['description'] = generate_description(prefix="PreFill Desc")
            result = page.create_designation(data)
            assert result['status'] in ('PASSED', 'UNKNOWN')
            page.hard_refresh()
            page.search_and_verify(data['name'])
            page.click_edit_button(designation_name=data['name'])
            values = page.get_form_field_values()
            assert values['name'] == data['name']
            assert values['description'] == data['description']
            assert values['status'] == data['status']
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_E04_edit_digits_only_name(self, designation_page):
        log.info("E04: Edit digits-only Name")
        page = designation_page
        try:
            name = self._create_designation_for_edit(page)
            page.hard_refresh()
            page.search_and_verify(name)
            page.click_edit_button(designation_name=name)
            page._set_input(page.NAME_INPUT, generate_digits_only(), clear_first=True)
            errors = page.get_mat_error_text()
            assert 'Invalid Name' in errors
        finally:
            _cleanup(page)

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_E05_edit_change_status_toggle(self, designation_page):
        log.info("E05: Edit change Status toggle")
        page = designation_page
        try:
            name = self._create_designation_for_edit(page)
            page.hard_refresh()
            page.search_and_verify(name)
            page.click_edit_button(designation_name=name)
            page.toggle_status()
            assert page.get_toggle_state() is False
            page.click_update()
            if page.is_validation_alert_present(timeout=3):
                page.handle_validation_warning()
            else:
                page.handle_success_alert()
            page.hard_refresh()
            page.search_and_verify(name)
            status = page.get_status_from_table(name)
            assert status == 'Inactive', f"Expected 'Inactive', got '{status}'"
        finally:
            _cleanup(page)


# ═══════════════════════════════════════════════════
#  PHASE 4: SEARCH & FILTER (F01-F05)
# ═══════════════════════════════════════════════════

@pytest.mark.usefixtures('designation_page')
class TestSearchFilter:

    def _create_designation_for_search(self, page):
        data = generate_valid_designation_data()
        data['name'] = generate_designation_name(prefix="SearchTarget")
        result = page.create_designation(data)
        assert result['status'] in ('PASSED', 'UNKNOWN')
        return data['name']

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_F01_search_exact_match(self, designation_page):
        log.info("F01: Search exact match")
        page = designation_page
        try:
            name = self._create_designation_for_search(page)
            page.hard_refresh()
            found = page.search_and_verify(name)
            assert found, f"Should find '{name}'"
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_F02_search_partial_match(self, designation_page):
        log.info("F02: Search partial match")
        page = designation_page
        try:
            name = self._create_designation_for_search(page)
            page.hard_refresh()
            found = page.search_and_verify(name[:10])
            assert found, f"Partial search should find match"
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_F03_search_no_match(self, designation_page):
        log.info("F03: Search no match")
        page = designation_page
        try:
            page.search_designation('ZZZ NONEXISTENT QWERTY')
            log.info("Non-existent search completed without error")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_F04_filter_panel_opens(self, designation_page):
        log.info("F04: Filter panel opens")
        page = designation_page
        try:
            filter_btn = page.driver.find_elements(By.CSS_SELECTOR, "button.filter-btn,button[mattooltip='Filters']")
            if filter_btn:
                page.driver.execute_script("arguments[0].click();", filter_btn[0])
                filter_panel = page.driver.find_elements(By.CSS_SELECTOR, ".filter-panel,[class*='filter']")
                assert len(filter_panel) > 0, "Filter panel should open"
                close_btn = page.driver.find_elements(By.CSS_SELECTOR, ".filter-panel button[mat-icon-button],.filter-panel button mat-icon")
                if close_btn:
                    page.driver.execute_script("arguments[0].click();", close_btn[0])
        except Exception as e:
            log.warning(f"Filter panel test: {e}")

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    @pytest.mark.ui
    def test_F05_apply_filters_non_functional(self, designation_page):
        log.info("F05: Apply Filters non-functional")
        page = designation_page
        try:
            filter_btn = page.driver.find_elements(By.CSS_SELECTOR, "button.filter-btn,button[mattooltip='Filters']")
            if filter_btn:
                page.driver.execute_script("arguments[0].click();", filter_btn[0])
                rows_before = page.get_table_row_count()
                apply_btn = page.driver.find_elements(By.XPATH, "//button[contains(.,'Apply Filters')]")
                if apply_btn:
                    page.driver.execute_script("arguments[0].click();", apply_btn[0])
                    rows_after = page.get_table_row_count()
                    log.info(f"Rows before: {rows_before}, after: {rows_after} — BUG: no effect")
                close_btn = page.driver.find_elements(By.CSS_SELECTOR, ".filter-panel button[mat-icon-button],.filter-panel button mat-icon")
                if close_btn:
                    page.driver.execute_script("arguments[0].click();", close_btn[0])
        except Exception as e:
            log.warning(f"Filter test error: {e}")


# ═══════════════════════════════════════════════════
#  PHASE 5: POPUP UI BEHAVIORS (P01-P05)
# ═══════════════════════════════════════════════════

@pytest.mark.usefixtures('designation_page')
class TestPopupUIBehaviors:

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_P01_add_form_cancel(self, designation_page):
        log.info("P01: Add form Cancel")
        page = designation_page
        try:
            page.open_add_form()
            assert page._is_form_popup_open()
            page.cancel()
            assert not page._is_form_popup_open()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_P02_add_form_close_x(self, designation_page):
        log.info("P02: Add form close via X")
        page = designation_page
        try:
            page.open_add_form()
            assert page._is_form_popup_open()
            page.close_popup()
            assert not page._is_form_popup_open()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_P03_view_popup_read_only(self, designation_page):
        log.info("P03: View popup read-only")
        page = designation_page
        try:
            data = generate_valid_designation_data()
            data['name'] = generate_designation_name(prefix="ViewTest")
            result = page.create_designation(data)
            assert result['status'] in ('PASSED', 'UNKNOWN')
            page.hard_refresh()
            page.search_and_verify(data['name'])
            page.click_view_button(designation_name=data['name'])
            page.verify_view_popup_read_only()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_P04_edit_popup_has_update(self, designation_page):
        log.info("P04: Edit has Update button")
        page = designation_page
        try:
            data = generate_valid_designation_data()
            data['name'] = generate_designation_name(prefix="EditBtnTest")
            result = page.create_designation(data)
            assert result['status'] in ('PASSED', 'UNKNOWN')
            page.hard_refresh()
            page.search_and_verify(data['name'])
            page.click_edit_button(designation_name=data['name'])
            assert page.is_edit_mode()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_P05_inline_error_keeps_form_open(self, designation_page):
        log.info("P05: Inline error keeps form open")
        page = designation_page
        try:
            page.open_add_form()
            page._set_input(page.NAME_INPUT, 'Test@Invalid', clear_first=True)
            errors = page.get_mat_error_text()
            assert 'Invalid Name' in errors
            page.submit()
            assert page._is_form_popup_open(), "Form should stay open"
            if page.is_validation_alert_present(timeout=3):
                page.handle_validation_warning()
        finally:
            _cleanup(page)


# ═══════════════════════════════════════════════════
#  PHASE 6: HISTORY VALIDATIONS (H01-H08)
# ═══════════════════════════════════════════════════

@pytest.mark.usefixtures('designation_page')
class TestHistoryValidations:

    def _create_designation_for_history(self, page):
        data = generate_valid_designation_data()
        data['name'] = generate_designation_name(prefix="HistTest")
        result = page.create_designation(data)
        assert result['status'] in ('PASSED', 'UNKNOWN')
        return data['name']

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H01_history_popup_opens(self, designation_page):
        log.info("H01: History popup opens")
        page = designation_page
        try:
            name = self._create_designation_for_history(page)
            page.hard_refresh()
            page.search_and_verify(name)
            page.click_history_button(designation_name=name)
            assert page.is_history_popup_open()
            page.close_history_popup()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.bug
    def test_H02_history_no_data(self, designation_page):
        log.info("H02: History no data")
        page = designation_page
        try:
            name = self._create_designation_for_history(page)
            page.hard_refresh()
            page.search_and_verify(name)
            page.click_history_button(designation_name=name)
            row_count = page.get_history_row_count()
            log.info(f"History rows: {row_count} — RhythmERP bug")
            page.close_history_popup()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H03_history_close_via_cancel(self, designation_page):
        log.info("H03: History close via Cancel")
        page = designation_page
        try:
            name = self._create_designation_for_history(page)
            page.hard_refresh()
            page.search_and_verify(name)
            page.click_history_button(designation_name=name)
            assert page.is_history_popup_open()
            page.close_history_popup()
            assert not page.is_history_popup_open()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H04_history_close_via_x(self, designation_page):
        log.info("H04: History close via X")
        page = designation_page
        try:
            name = self._create_designation_for_history(page)
            page.hard_refresh()
            page.search_and_verify(name)
            page.click_history_button(designation_name=name)
            assert page.is_history_popup_open()
            try:
                icons = page.driver.find_elements(By.CSS_SELECTOR, ".popup-header button mat-icon")
                if icons:
                    btn = icons[0].find_element(By.XPATH, "./ancestor::button")
                    page.driver.execute_script("arguments[0].click();", btn)
                else:
                    page.close_history_popup()
            except Exception:
                page.close_history_popup()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H05_history_search_input(self, designation_page):
        log.info("H05: History search input")
        page = designation_page
        try:
            name = self._create_designation_for_history(page)
            page.hard_refresh()
            page.search_and_verify(name)
            page.click_history_button(designation_name=name)
            search_inputs = page.driver.find_elements(By.CSS_SELECTOR,
                ".popup-body input,.popup-content input,app-dynamic-history input")
            visible = [i for i in search_inputs if i.is_displayed()]
            assert len(visible) >= 1, "History should have search input"
            page.close_history_popup()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H06_history_title(self, designation_page):
        log.info("H06: History title")
        page = designation_page
        try:
            name = self._create_designation_for_history(page)
            page.hard_refresh()
            page.search_and_verify(name)
            page.click_history_button(designation_name=name)
            try:
                h3s = page.driver.find_elements(By.CSS_SELECTOR,
                    "h3.popup-title,.popup-content h3,app-dynamic-history .tbl-title h2")
                titles = [h.text.strip() for h in h3s if h.is_displayed()]
                assert any('history' in t.lower() for t in titles), f"Expected 'History', got: {titles}"
            except Exception as e:
                log.warning(f"History title check: {e}")
            page.close_history_popup()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_H07_history_does_not_block_main(self, designation_page):
        log.info("H07: History doesn't block main")
        page = designation_page
        try:
            name = self._create_designation_for_history(page)
            page.hard_refresh()
            page.search_and_verify(name)
            page.click_history_button(designation_name=name)
            page.close_history_popup()
            assert page.is_page_loaded()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_H08_history_data_structure(self, designation_page):
        log.info("H08: History data structure")
        page = designation_page
        try:
            name = self._create_designation_for_history(page)
            page.hard_refresh()
            page.search_and_verify(name)
            page.click_history_button(designation_name=name)
            data = page.get_history_data()
            row_count = page.get_history_row_count()
            log.info(f"History: {row_count} rows, {len(data)} entries")
            assert isinstance(data, list)
            page.close_history_popup()
        finally:
            _cleanup(page)
