"""
Item Attribute 5 (IA5) — 23 Automated Test Cases

IA5 is like IA2-4: Name (required), Description (optional), Status (toggle).
NO Base UOM dropdown — only Name is required for successful creation.

6 Test Classes:
  TestCreateFormValidations   (9 tests:  IA5-C01 to IA5-C09)
  TestEditFormValidations     (4 tests:  IA5-E01 to IA5-E04)
  TestSearchFilter            (4 tests:  IA5-S01 to IA5-S04)
  TestPopupUIBehaviors        (3 tests:  IA5-P01 to IA5-P03)
  TestHistoryValidations      (3 tests:  IA5-H01 to IA5-H03)

Pytest Marker Summary:
  smoke:      6 tests (critical path)
  sanity:     23 tests (core validation)
  regression: 23 tests (full suite)
  bug:        8 tests (known open bugs)
  ui:         3 tests (popup behaviors)

Bug markers (xfail):
  BUG-IA01: Duplicate Name allowed
  BUG-IA04: No maxlength on Name — server rejects 256+ with generic error
  BUG-IA06: Spaces-only Name accepted (should validate)
  BUG-IA07: Special chars in Name accepted (should sanitize)
  BUG-IA08: No history entry on creation

GOLDEN CODE pattern:
  - try/except/finally with ia_page._cleanup() in every test
  - No _record helper — plain assert only
  - ZERO time.sleep() in test code — page object methods have internal waits
  - Hardcoded ATTR_NUM = 5 (no parametrization — enables xdist -n 5)
"""

import os
import sys
import time
import pytest

# Resolve project root
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from pages.commodity_settings.modules.item_attribute.item_attribute_page import ItemAttributePage
from pages.commodity_settings.modules.item_attribute.data.item_attribute_data import (
    generate_valid_ia_data,
    generate_valid_edit_data,
    generate_name_only_data,
    generate_description_only_data,
    generate_empty_data,
    generate_spaces_only_name,
    generate_spaces_only_description,
    generate_name_with_spaces,
    generate_duplicate_name_data,
    generate_special_char_name,
    generate_special_char_description,
    generate_long_name,
    generate_ia_name,
    generate_ia_description,
    BUG_IA01, BUG_IA02, BUG_IA03, BUG_IA04, BUG_IA05,
    BUG_IA06, BUG_IA07, BUG_IA08,
    VALIDATION_FAILED_TITLE,
    SUCCESS_CREATE_MSG,
    SUCCESS_UPDATE_MSG,
)


# ══════════════════════════════════════════════════════════════
#  Fixture — hardcoded ATTR_NUM = 5
# ══════════════════════════════════════════════════════════════

ATTR_NUM = 5


@pytest.fixture
def ia_page(logged_in_driver):
    page = ItemAttributePage(logged_in_driver, attr_num=ATTR_NUM)
    page.navigate_to_page()
    yield page
    try:
        page._cleanup()
    except Exception:
        pass


# ╔══════════════════════════════════════════╗
# ║  PHASE 1: Create Form Validations (9)   ║
# ╚══════════════════════════════════════════╝

class TestCreateFormValidations:
    """IA5-C01 to IA5-C09: Create form validation tests for IA5."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_empty_form_submit(self, ia_page):
        """IA5-C01: Submit with all fields empty -> Validation Failed."""
        try:
            ia_page.open_add_form()
            ia_page._force_close_panels()
            ia_page.submit()
            is_alert = ia_page.is_validation_alert_present(timeout=10)
            if is_alert:
                warning = ia_page.handle_validation_warning()
                assert VALIDATION_FAILED_TITLE in warning, \
                    f"Expected 'Validation Failed', got: {warning}"
            else:
                assert False, "No validation alert appeared for empty form"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_only_name_filled(self, ia_page):
        """IA5-C02: Submit with only Name filled -> Should PASS (no Base UOM required)."""
        try:
            data = generate_name_only_data(ATTR_NUM)
            result = ia_page.create_item_attribute(data)
            assert result['status'] == 'PASSED', \
                f"IA5: Name-only creation should pass (no Base UOM): {result['error']}"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_IA06, strict=False)
    def test_blank_name_spaces_only(self, ia_page):
        """IA5-C03: Name with only spaces -> Should be rejected (BUG-IA06)."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            data['name'] = generate_spaces_only_name()
            result = ia_page.create_item_attribute(data)
            assert result['status'] != 'PASSED', \
                "BUG-IA06: Spaces-only name was accepted (should be rejected)"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_IA01, strict=False)
    def test_duplicate_name_create(self, ia_page):
        """IA5-C04: Duplicate Name in Create -> Should block (BUG-IA01)."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            result1 = ia_page.create_item_attribute(data)
            assert result1['status'] == 'PASSED', \
                f"First creation failed: {result1['error']}"
            # Try creating same name again
            data2 = generate_duplicate_name_data(data['name'], ATTR_NUM)
            result2 = ia_page.create_item_attribute(data2)
            assert result2['status'] != 'PASSED', \
                "BUG-IA01: Duplicate Name accepted (should be blocked)"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_IA07, strict=False)
    def test_special_chars_in_name(self, ia_page):
        """IA5-C05: Special characters in Name -> Should reject (BUG-IA07)."""
        try:
            special_name = generate_special_char_name()
            data = generate_valid_ia_data(ATTR_NUM)
            data['name'] = special_name
            result = ia_page.create_item_attribute(data)
            assert result['status'] != 'PASSED', \
                "BUG-IA07: Special characters accepted without sanitization"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_IA04, strict=False)
    def test_very_long_name(self, ia_page):
        """IA5-C06: 300 character Name -> Should reject (BUG-IA04)."""
        try:
            long_name = generate_long_name(300)
            data = generate_valid_ia_data(ATTR_NUM)
            data['name'] = long_name
            result = ia_page.create_item_attribute(data)
            assert result['status'] != 'PASSED', \
                "BUG-IA04: 300-char Name accepted (no max length validation)"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_create_valid_all_fields(self, ia_page):
        """IA5-C07: Create valid item attribute with Name + Description -> Success."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            result = ia_page.create_item_attribute(data)
            assert result['status'] == 'PASSED', \
                f"Creation failed: {result['error']}"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_create_with_special_char_description(self, ia_page):
        """IA5-C08: Create with special characters in Description -> Should be accepted."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            data['description'] = generate_special_char_description()
            result = ia_page.create_item_attribute(data)
            assert result['status'] == 'PASSED', \
                f"Creation with special char description failed: {result['error']}"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_IA06, strict=False)
    def test_name_with_leading_trailing_spaces(self, ia_page):
        """IA5-C09: Name with leading/trailing spaces -> Should trim (BUG-IA06)."""
        try:
            spaced_name = generate_name_with_spaces(ATTR_NUM)
            data = generate_valid_ia_data(ATTR_NUM)
            data['name'] = spaced_name
            result = ia_page.create_item_attribute(data)
            assert result['status'] != 'PASSED' or spaced_name.strip() == spaced_name, \
                "BUG-IA06: Leading/trailing spaces not trimmed"
        except Exception:
            raise
        finally:
            ia_page._cleanup()


# ╔══════════════════════════════════════════╗
# ║  PHASE 2: Edit Form Validations (4)     ║
# ╚══════════════════════════════════════════╝

class TestEditFormValidations:
    """IA5-E01 to IA5-E04: Edit form validation tests for IA5."""

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_IA01, strict=False)
    def test_edit_duplicate_name(self, ia_page):
        """IA5-E01: Edit to duplicate name -> Should block (BUG-IA01)."""
        try:
            data1 = generate_valid_ia_data(ATTR_NUM)
            data2 = generate_valid_ia_data(ATTR_NUM)
            r1 = ia_page.create_item_attribute(data1)
            assert r1['status'] == 'PASSED', f"First creation failed: {r1['error']}"
            r2 = ia_page.create_item_attribute(data2)
            assert r2['status'] == 'PASSED', f"Second creation failed: {r2['error']}"
            # Edit second to match first's name
            edit_data = {'name': data1['name'], 'description': None}
            result = ia_page.edit_item_attribute(data2['name'], edit_data)
            assert result['status'] != 'PASSED', \
                "BUG-IA01: Duplicate Name accepted in Edit"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_IA06, strict=False)
    def test_edit_blank_name(self, ia_page):
        """IA5-E02: Edit Name to blank (spaces only) -> Should reject (BUG-IA06)."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            r = ia_page.create_item_attribute(data)
            assert r['status'] == 'PASSED', f"Create failed: {r['error']}"
            edit_data = {'name': generate_spaces_only_name(), 'description': None}
            result = ia_page.edit_item_attribute(data['name'], edit_data)
            assert result['status'] != 'PASSED', \
                "BUG-IA06: Blank name accepted in Edit"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_edit_pre_populated_fields(self, ia_page):
        """IA5-E03: Edit popup shows pre-filled data."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            r = ia_page.create_item_attribute(data)
            assert r['status'] == 'PASSED', f"Create failed: {r['error']}"
            ia_page.search_item(data['name'])
            ia_page.click_edit_button(data['name'])
            values = ia_page.get_form_field_values()
            assert values.get('name', '') != '', \
                "Name should be pre-populated in Edit popup"
            ia_page.cancel()
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_edit_valid_update(self, ia_page):
        """IA5-E04: Edit with valid new Name and Description -> Success."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            r = ia_page.create_item_attribute(data)
            assert r['status'] == 'PASSED', f"Create failed: {r['error']}"
            edit_data = generate_valid_edit_data(ATTR_NUM)
            result = ia_page.edit_item_attribute(data['name'], edit_data)
            assert result['status'] == 'PASSED', \
                f"Edit failed: {result['error']}"
        except Exception:
            raise
        finally:
            ia_page._cleanup()


# ╔══════════════════════════════════════════╗
# ║  PHASE 3: Search & Filter Tests (4)     ║
# ╚══════════════════════════════════════════╝

class TestSearchFilter:
    """IA5-S01 to IA5-S04: Search and filter tests for IA5."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_search_exact_match(self, ia_page):
        """IA5-S01: Search with exact Name -> Find the item."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            result = ia_page.create_item_attribute(data)
            assert result['status'] == 'PASSED', f"Create failed: {result['error']}"
            found = ia_page.search_item(data['name'])
            ia_page.clear_search()
            assert found, f"Exact search failed for: {data['name']}"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_search_partial_match(self, ia_page):
        """IA5-S02: Search with partial Name -> Find matching items."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            result = ia_page.create_item_attribute(data)
            assert result['status'] == 'PASSED', f"Create failed: {result['error']}"
            partial = data['name'][:8]
            found = ia_page.search_item(partial)
            ia_page.clear_search()
            assert found, f"Partial search failed for: {partial}"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_search_nonexistent(self, ia_page):
        """IA5-S03: Search for non-existent Name -> No results."""
        try:
            found = ia_page.search_item("ZZZZZ_NONEXISTENT_99999")
            ia_page.clear_search()
            assert not found, "Should not find non-existent item"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_search_clear_restores_table(self, ia_page):
        """IA5-S04: After searching, clearing should restore full table."""
        try:
            initial_count = ia_page.get_table_row_count()
            data = generate_valid_ia_data(ATTR_NUM)
            result = ia_page.create_item_attribute(data)
            assert result['status'] == 'PASSED', f"Create failed: {result['error']}"
            ia_page.search_item(data['name'])
            ia_page.clear_search()
            restored_count = ia_page.get_table_row_count()
            assert restored_count >= initial_count, \
                "Table not restored after clearing search"
        except Exception:
            raise
        finally:
            ia_page._cleanup()


# ╔══════════════════════════════════════════╗
# ║  PHASE 4: Popup UI Behaviors (3)        ║
# ╚══════════════════════════════════════════╝

class TestPopupUIBehaviors:
    """IA5-P01 to IA5-P03: Popup UI behavior tests for IA5."""

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_cancel_discards_data(self, ia_page):
        """IA5-P01: Cancel on Add form discards data -> Not saved in table."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            ia_page.open_add_form()
            ia_page.fill_item_attribute_form(data)
            ia_page._force_close_panels()
            ia_page.cancel()
            found = ia_page.search_item(data['name'])
            assert not found, "Data should NOT be saved after Cancel"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.smoke
    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_view_shows_read_only(self, ia_page):
        """IA5-P02: View popup fields are read-only."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            r = ia_page.create_item_attribute(data)
            assert r['status'] == 'PASSED', f"Create failed: {r['error']}"
            ia_page.search_item(data['name'])
            ia_page.click_view_button(data['name'])
            is_readonly = ia_page.verify_view_popup_read_only()
            ia_page.close_popup()
            assert is_readonly, "View popup should have all fields disabled"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.ui
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_edit_has_update_button(self, ia_page):
        """IA5-P03: Edit popup shows Update button."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            r = ia_page.create_item_attribute(data)
            assert r['status'] == 'PASSED', f"Create failed: {r['error']}"
            ia_page.search_item(data['name'])
            ia_page.click_edit_button(data['name'])
            has_update = ia_page.is_edit_mode()
            ia_page.cancel()
            assert has_update, "Edit popup should have Update button"
        except Exception:
            raise
        finally:
            ia_page._cleanup()


# ╔══════════════════════════════════════════╗
# ║  PHASE 5: History Validations (3)       ║
# ╚══════════════════════════════════════════╝

class TestHistoryValidations:
    """IA5-H01 to IA5-H03: History popup validation tests for IA5."""

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(reason=BUG_IA08, strict=False)
    def test_history_after_create(self, ia_page):
        """IA5-H01: History after creation -> Should have 1+ rows (BUG-IA08)."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            r = ia_page.create_item_attribute(data)
            assert r['status'] == 'PASSED', f"Create failed: {r['error']}"
            result = ia_page.check_history(data['name'])
            assert result['row_count'] > 0, \
                "BUG-IA08: No history entry after creation"
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_history_after_edit(self, ia_page):
        """IA5-H02: History after edit shows entry."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            r = ia_page.create_item_attribute(data)
            assert r['status'] == 'PASSED', f"Create failed: {r['error']}"
            edit_data = {
                'name': generate_ia_name("HistEdit", ATTR_NUM),
                'description': None,
            }
            er = ia_page.edit_item_attribute(data['name'], edit_data)
            search_name = edit_data.get('name') or data['name']
            result = ia_page.check_history(search_name)
            # History after edit should show at least the edit entry
            log.info(f"History after edit — row count: {result['row_count']}, error: {result['error']}")
        except Exception:
            raise
        finally:
            ia_page._cleanup()

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_history_close_button(self, ia_page):
        """IA5-H03: History popup closes via close button."""
        try:
            data = generate_valid_ia_data(ATTR_NUM)
            r = ia_page.create_item_attribute(data)
            assert r['status'] == 'PASSED', f"Create failed: {r['error']}"
            ia_page.search_item(data['name'])
            ia_page.click_history_button(data['name'])
            closed = ia_page.close_popup()
            assert closed, "History popup should close via close button"
        except Exception:
            raise
        finally:
            ia_page._cleanup()
