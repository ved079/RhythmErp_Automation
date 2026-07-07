"""
Gate Pass — Playwright UI test suite
=====================================
Tests:
  1  Smoke      — create GP, verify ref no in listing
  2  Validation — empty submit blocked + cancel returns to listing
  3  Listing    — table has rows + bogus search returns empty
  4  Multi-row  — all available items, verify row count
  5  View       — View action shows read-only form (no Submit button)
  6  Regression — invalid qty/bags (0, negative, blank) show mat-error
"""

import pytest
import random


# ── Group 1: Smoke ─────────────────────────────────────────────────────────

@pytest.mark.smoke
class TestGPSmoke:
    def test_create_and_search(self, gp_page):
        """Create a single-item Gate Pass; verify it appears in listing."""
        ref_no, row_dicts = gp_page.create_record([(random.randint(1, 10), random.randint(1, 100))])
        assert ref_no, "Expected a ref_no after creation"
        assert len(row_dicts) == 1, f"Expected 1 row dict, got {len(row_dicts)}"
        gp_page.search_by_ref_no(ref_no)
        assert gp_page.is_gp_in_table(ref_no), \
            f"Gate Pass {ref_no} not found in table after creation"


# ── Group 2: Validation ────────────────────────────────────────────────────

@pytest.mark.validation
class TestGPValidation:
    def test_form_submit_and_cancel(self, gp_page):
        """Empty submit must not close the form; Cancel must return to listing."""
        gp_page.open_add_form()
        gp_page.page.locator(gp_page.SUBMIT_BTN).click(force=True)
        gp_page.page.wait_for_timeout(800)
        assert gp_page.page.locator(gp_page.SUPPLIER_NAME).count() > 0, \
            "Empty form should not have closed after Submit"
        gp_page.close_popup()
        assert gp_page.page.locator("table.mat-mdc-table").count() > 0, \
            "Listing table not visible after cancelling form"


# ── Group 3: Listing ───────────────────────────────────────────────────────

@pytest.mark.smoke
class TestGPListing:
    def test_listing_and_search(self, gp_page):
        """Table must have rows; bogus ref-no search must return empty."""
        assert gp_page.get_table_row_count() > 0, "GP listing must have at least one row"
        gp_page.search_by_ref_no("GP/XXXX/9999999")
        assert not gp_page.is_gp_in_table("GP/XXXX/9999999"), \
            "Bogus ref-no should not match any row"


# ── Group 4: Multi-row ─────────────────────────────────────────────────────

@pytest.mark.workflow
class TestGPMultiRow:
    def test_multi_row_create(self, gp_page):
        """Create GP with all available items; verify all rows created."""
        ref_no, row_dicts = gp_page.create_record(all_items=True)
        assert len(row_dicts) >= 2, f"Expected at least 2 item rows, got {len(row_dicts)}"
        assert ref_no, "Expected a ref_no after multi-row creation"
        gp_page.search_by_ref_no(ref_no)
        assert gp_page.is_gp_in_table(ref_no), \
            f"Gate Pass {ref_no} not found in table after multi-row creation"


# ── Group 5: View ──────────────────────────────────────────────────────────

@pytest.mark.workflow
class TestGPView:
    def test_view_popup_read_only(self, gp_page):
        """View action must open read-only form with no Submit button."""
        gp_page.click_row_action(0, "View")
        gp_page.page.wait_for_selector("input[readonly]", timeout=25000)
        gp_page.page.wait_for_timeout(500)
        assert gp_page.page.locator(gp_page.SUBMIT_BTN).count() == 0, \
            "Submit must not appear in View mode"
        gp_page.navigate_to_page()


# ── Group 6: Regression ────────────────────────────────────────────────────

MAT_ERROR = "mat-error"


@pytest.mark.regression
class TestGPRegression:
    def _open_filled_form(self, gp_page):
        """Open add form and fill header + first item row with valid values, return to caller."""
        gp_page.open_add_form()
        gp_page.fill_header()
        # fill item row with valid values first
        gp_page._select_random_mat_option_nth(gp_page.ITEM_NAME, 0)
        gp_page.page.wait_for_timeout(500)

    def test_zero_quantity_shows_error(self, gp_page):
        """qty=0 on item row must show mat-error."""
        self._open_filled_form(gp_page)
        gp_page._fill_number_nth(gp_page.NO_OF_BAGS, 0, 1)
        gp_page._fill_number_nth(gp_page.QUANTITY, 0, 0)
        gp_page.page.locator(gp_page.SUBMIT_BTN).click(force=True)
        gp_page.page.wait_for_timeout(800)
        assert gp_page.page.locator(MAT_ERROR).count() > 0, \
            "Expected mat-error for qty=0"
        gp_page.close_popup()

    def test_negative_quantity_shows_error(self, gp_page):
        """qty=-1 on item row must show mat-error."""
        self._open_filled_form(gp_page)
        gp_page._fill_number_nth(gp_page.NO_OF_BAGS, 0, 1)
        gp_page._fill_number_nth(gp_page.QUANTITY, 0, -1)
        gp_page.page.locator(gp_page.SUBMIT_BTN).click(force=True)
        gp_page.page.wait_for_timeout(800)
        assert gp_page.page.locator(MAT_ERROR).count() > 0, \
            "Expected mat-error for qty=-1"
        gp_page.close_popup()

    def test_zero_bags_shows_error(self, gp_page):
        """bags=0 on item row must show mat-error."""
        self._open_filled_form(gp_page)
        gp_page._fill_number_nth(gp_page.NO_OF_BAGS, 0, 0)
        gp_page._fill_number_nth(gp_page.QUANTITY, 0, 1)
        gp_page.page.locator(gp_page.SUBMIT_BTN).click(force=True)
        gp_page.page.wait_for_timeout(800)
        assert gp_page.page.locator(MAT_ERROR).count() > 0, \
            "Expected mat-error for bags=0"
        gp_page.close_popup()

    def test_blank_qty_and_bags_shows_error(self, gp_page):
        """Leaving qty and bags blank must show required mat-error."""
        self._open_filled_form(gp_page)
        gp_page.page.locator(gp_page.SUBMIT_BTN).click(force=True)
        gp_page.page.wait_for_timeout(800)
        assert gp_page.page.locator(MAT_ERROR).count() > 0, \
            "Expected mat-error for blank qty/bags"
        gp_page.close_popup()
