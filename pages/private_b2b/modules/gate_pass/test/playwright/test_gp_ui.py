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
  7  Edit       — remove rows, add rows, ref_no unchanged, qty/bags saved
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


# ── Group 7: Edit flow ─────────────────────────────────────────────────────
# One GP is created once (class-scoped) and all 4 tests operate on it in sequence:
#   remove rows → add rows → verify ref_no unchanged → verify qty/bags saved

@pytest.fixture(scope="class")
def edit_gp_state(logged_in_page):
    """Create one all-items GP shared across the entire TestGPEdit class."""
    from pages.private_b2b.modules.gate_pass.gp_playwright_page import GPPlaywrightPage
    p = GPPlaywrightPage(logged_in_page)
    p.navigate_to_page()
    ref_no, row_dicts = p.create_record(all_items=True)
    assert len(row_dicts) >= 2, "Need at least 2 items for edit tests"
    print(f"\n[EDIT-FIXTURE] created GP {ref_no} with {len(row_dicts)} rows")
    yield ref_no, row_dicts


@pytest.mark.workflow
class TestGPEdit:
    def test_edit_remove_rows(self, gp_page, edit_gp_state):
        """Remove a random subset of rows from the shared GP; verify via View.

        Multi-row GPs already show minus buttons in edit — no blank row needed.
        Delete in descending index order so lower indices stay stable.
        After this test the GP has 1..N-1 rows remaining.
        """
        ref_no, row_dicts = edit_gp_state
        n = len(row_dicts)

        keep_count = random.randint(1, n - 1)
        keep_indices = set(random.sample(range(n), keep_count))
        remove_indices = sorted([i for i in range(n) if i not in keep_indices], reverse=True)

        to_keep   = [row_dicts[i]["item_name"] for i in keep_indices]
        to_remove = [row_dicts[i]["item_name"] for i in range(n) if i not in keep_indices]
        print(f"\n[EDIT-REMOVE] keeping indices={sorted(keep_indices)}: {to_keep}")
        print(f"[EDIT-REMOVE] removing indices={remove_indices}: {to_remove}")

        gp_page.navigate_to_page()
        gp_page.search_by_ref_no(ref_no)
        gp_page.open_edit_form(0)

        for idx in remove_indices:
            gp_page.delete_row_nth(idx)

        gp_page.submit_update()

        gp_page.navigate_to_page()
        gp_page.search_by_ref_no(ref_no)
        gp_page.click_row_action(0, "View")
        gp_page.page.wait_for_selector("input[readonly]", timeout=25000)
        gp_page.page.wait_for_selector("tbody.main_tbody", timeout=10000)
        gp_page.page.wait_for_timeout(500)

        remaining = gp_page.read_item_names_from_form()
        for item in to_keep:
            assert item in remaining, \
                f"'{item}' should still be present, got: {remaining}"
        for item in to_remove:
            assert item not in remaining, \
                f"'{item}' should have been removed but found in: {remaining}"

        gp_page.navigate_to_page()

    def test_edit_add_rows(self, gp_page, edit_gp_state):
        """Add 2 new rows to the GP (now in reduced state from test_edit_remove_rows).

        Reads current form state first so it works regardless of how many rows remain.
        """
        ref_no, _ = edit_gp_state

        gp_page.navigate_to_page()
        gp_page.search_by_ref_no(ref_no)
        gp_page.open_edit_form(0)

        current_items = gp_page.read_item_names_from_form()
        current_count = gp_page.count_form_rows()
        print(f"\n[EDIT-ADD] current rows={current_count}: {current_items}")

        for _ in range(2):
            gp_page.page.locator(gp_page.ADD_ROW_BTN).click()
            gp_page.page.wait_for_timeout(600)

        assert gp_page.count_form_rows() == current_count + 2

        used = set(current_items)
        new_items = []
        for i in range(current_count, current_count + 2):
            rd = gp_page._add_item_row(i, random.randint(1, 5), random.randint(1, 50), used_items=used)
            if rd["item_name"]:
                used.add(rd["item_name"])
                new_items.append(rd["item_name"])

        print(f"[EDIT-ADD] added: {new_items}")
        gp_page.submit_update()

        gp_page.navigate_to_page()
        gp_page.search_by_ref_no(ref_no)
        gp_page.click_row_action(0, "View")
        gp_page.page.wait_for_selector("input[readonly]", timeout=25000)
        gp_page.page.wait_for_selector("tbody.main_tbody", timeout=10000)
        gp_page.page.wait_for_timeout(500)

        all_items = gp_page.read_item_names_from_form()
        for item in new_items:
            assert item in all_items, \
                f"Newly added '{item}' not found in View, got: {all_items}"
        assert len(all_items) == current_count + len(new_items), \
            f"Expected {current_count + len(new_items)} rows in View, got {len(all_items)}"

        gp_page.navigate_to_page()

    def test_edit_ref_no_unchanged(self, gp_page, edit_gp_state):
        """GP reference number must not change after editing."""
        ref_no, _ = edit_gp_state

        gp_page.navigate_to_page()
        gp_page.search_by_ref_no(ref_no)
        gp_page.open_edit_form(0)
        gp_page._fill_number_nth(gp_page.NO_OF_BAGS, 0, random.randint(1, 8))
        gp_page.submit_update()

        gp_page.navigate_to_page()
        gp_page.search_by_ref_no(ref_no)
        assert gp_page.is_gp_in_table(ref_no), \
            f"GP {ref_no} not found after edit — ref_no appears to have changed"

    def test_edit_qty_bags_saved(self, gp_page, edit_gp_state):
        """Edit NO. of Bags and Quantity; values must persist in View.

        Uses offsetParent visibility filter in JS to skip hidden stale inputs
        from previously closed form sessions (Angular SPA DOM pollution).
        """
        ref_no, _ = edit_gp_state
        new_bags = 9
        new_qty  = 77

        gp_page.navigate_to_page()
        gp_page.search_by_ref_no(ref_no)
        gp_page.open_edit_form(0)
        gp_page._fill_number_nth(gp_page.NO_OF_BAGS, 0, new_bags)
        gp_page._fill_number_nth(gp_page.QUANTITY, 0, new_qty)
        gp_page.submit_update()

        gp_page.navigate_to_page()
        gp_page.search_by_ref_no(ref_no)
        gp_page.click_row_action(0, "View")
        gp_page.page.wait_for_selector("input[readonly]", timeout=25000)
        gp_page.page.wait_for_selector("tbody.main_tbody", timeout=10000)
        gp_page.page.wait_for_timeout(500)

        def _read_first_visible(xpath):
            return gp_page.page.evaluate("""
                ([xpath]) => {
                    const r = document.evaluate(xpath, document, null,
                        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    for (let i = 0; i < r.snapshotLength; i++) {
                        const el = r.snapshotItem(i);
                        if (el.offsetParent !== null) return el.value;
                    }
                    return '';
                }
            """, [xpath])

        bags_val = _read_first_visible(gp_page.NO_OF_BAGS.replace("xpath=", ""))
        qty_val  = _read_first_visible(gp_page.QUANTITY.replace("xpath=", ""))

        assert bags_val and int(float(bags_val)) == new_bags, \
            f"NO. of Bags in View: expected {new_bags}, got '{bags_val}'"
        assert qty_val and int(float(qty_val)) == new_qty, \
            f"Quantity in View: expected {new_qty}, got '{qty_val}'"

        gp_page.navigate_to_page()
