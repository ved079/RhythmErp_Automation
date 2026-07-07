"""
GRN — Playwright UI test suite
================================
Tests:
  1  Smoke         — create GRN, verify ref_no in listing
  2  Calc          — rejected = GP qty - accepted; accepted = GP qty → rejected = 0
  2b Multi-row Calc — all rows formula; mixed valid/invalid rows
  3  Validation    — empty submit blocked + cancel returns to listing
  4  Regression    — accepted > GP qty, zero, negative, blank all show errors
"""

import pytest
import random


# ── Group 1: Smoke ─────────────────────────────────────────────────────────

@pytest.mark.smoke
class TestGRNSmoke:
    def test_create_search_and_view(self, grn_page):
        """Create GRN with valid accepted qty; verify ref_no in listing; view is read-only."""
        page_obj, (supplier_name, _) = grn_page

        page_obj.open_add_form()
        page_obj.fill_form(supplier_name, accepted_qty=1)

        gp_qty = page_obj.read_gp_qty(0)
        assert gp_qty and gp_qty > 0, "GP qty should be auto-patched and > 0"

        page_obj.page.locator(page_obj.SUBMIT_BTN).click()
        page_obj.handle_success_alert()
        page_obj.navigate_to_page()

        ref_no = page_obj.get_ref_no_of_first_row()
        assert ref_no, "Expected a ref_no after GRN creation"

        page_obj.search_by_ref_no(ref_no)
        assert page_obj.is_grn_in_table(ref_no), \
            f"GRN {ref_no} not found in listing after creation"

        # View — must be read-only
        page_obj.click_row_action(0, "View")
        page_obj.page.wait_for_selector("input[readonly]", timeout=25000)
        page_obj.page.wait_for_timeout(500)
        assert page_obj.page.locator(page_obj.SUBMIT_BTN).count() == 0, \
            "Submit must not appear in View mode"
        page_obj.navigate_to_page()


# ── Group 2: Calculation ───────────────────────────────────────────────────

@pytest.mark.workflow
class TestGRNCalc:
    def test_rejected_qty_formula(self, grn_page):
        """rejected = GP qty - accepted; assert auto-calc matches formula."""
        page_obj, (supplier_name, _) = grn_page

        page_obj.open_add_form()
        page_obj.fill_form(supplier_name, accepted_qty=0)  # fill supplier + GP first

        gp_qty = page_obj.read_gp_qty(0)
        assert gp_qty and gp_qty > 0, "GP qty must be auto-patched"

        accepted = max(1, int(gp_qty) - 1)
        page_obj._fill_number_nth(page_obj.ACCEPTED_QTY, 0, accepted)
        page_obj.page.wait_for_timeout(800)

        rejected = page_obj.read_rejected_qty(0)
        expected = gp_qty - accepted
        assert rejected == pytest.approx(expected, abs=0.01), \
            f"rejected={rejected} but expected {gp_qty} - {accepted} = {expected}"

        page_obj.close_popup()

    def test_boundary_accepted_equals_gp_qty(self, grn_page):
        """accepted = GP qty → rejected must be exactly 0 (nothing rejected)."""
        page_obj, (supplier_name, _) = grn_page

        page_obj.open_add_form()
        page_obj.fill_form(supplier_name, accepted_qty=0)

        gp_qty = page_obj.read_gp_qty(0)
        assert gp_qty and gp_qty > 0, "GP qty must be auto-patched"

        page_obj._fill_number_nth(page_obj.ACCEPTED_QTY, 0, int(gp_qty))
        page_obj.page.wait_for_timeout(800)

        rejected = page_obj.read_rejected_qty(0)
        assert rejected == pytest.approx(0, abs=0.01), \
            f"rejected={rejected} but expected 0 when accepted equals GP qty ({gp_qty})"

        assert page_obj.page.locator("mat-error").count() == 0, \
            "No error should appear when accepted = GP qty"

        page_obj.close_popup()

    def test_decimal_accepted_qty(self, grn_page):
        """accepted with 4 decimal places is valid; rejected = GP qty - accepted."""
        page_obj, (supplier_name, _) = grn_page

        page_obj.open_add_form()
        page_obj.fill_form(supplier_name, accepted_qty=0)

        gp_qty = page_obj.read_gp_qty(0)
        assert gp_qty and gp_qty > 1.1234, \
            f"GP qty ({gp_qty}) too small for decimal accepted test"

        accepted = 1.1234
        page_obj._fill_number_nth(page_obj.ACCEPTED_QTY, 0, accepted)
        page_obj.page.wait_for_timeout(800)

        assert page_obj.page.locator("mat-error").count() == 0, \
            "4 decimal places should be valid — no error expected"

        rejected = page_obj.read_rejected_qty(0)
        expected = round(gp_qty - accepted, 4)
        assert rejected == pytest.approx(expected, abs=0.0001), \
            f"rejected={rejected} but expected {gp_qty} - {accepted} = {expected}"

        page_obj.close_popup()


# ── Group 2b: Multi-row Calculation ───────────────────────────────────────

@pytest.mark.workflow
class TestGRNMultiRowCalc:
    def test_multi_row_rejected_qty_formula(self, grn_page_multi):
        """GP with all items → GRN auto-patches all rows.
        For every row: enter random accepted < GP qty, assert rejected = GP qty - accepted.
        """
        page_obj, (supplier_name, _) = grn_page_multi

        page_obj.open_add_form()
        row_count = page_obj.select_supplier_and_gp(supplier_name, expected_rows=2)
        assert row_count > 1, f"Expected multiple rows after GP selection (with retry), got {row_count}"

        gp_qtys = []
        for i in range(row_count):
            gp_qty = page_obj.read_gp_qty(i)
            assert gp_qty and gp_qty > 0, f"Row {i}: GP qty not auto-patched"
            gp_qtys.append(gp_qty)

        accepted_qtys = []
        for i, gp_qty in enumerate(gp_qtys):
            accepted = random.randint(1, max(1, int(gp_qty) - 1)) if gp_qty > 1 else 1
            page_obj._fill_number_nth(page_obj.ACCEPTED_QTY, i, accepted)
            page_obj.page.wait_for_timeout(600)
            accepted_qtys.append(accepted)

        for i, (gp_qty, accepted) in enumerate(zip(gp_qtys, accepted_qtys)):
            rejected = page_obj.read_rejected_qty(i)
            expected = gp_qty - accepted
            assert rejected == pytest.approx(expected, abs=0.01), (
                f"Row {i}: rejected={rejected}, expected {gp_qty} - {accepted} = {expected}"
            )

        page_obj.page.locator(page_obj.SUBMIT_BTN).click()
        page_obj.handle_success_alert()
        page_obj.navigate_to_page()

        ref_no = page_obj.get_ref_no_of_first_row()
        assert ref_no, "Expected a ref_no after multi-row GRN submission"

        page_obj.search_by_ref_no(ref_no)
        assert page_obj.is_grn_in_table(ref_no), \
            f"Multi-row GRN {ref_no} not found in listing after save"

    def test_multi_row_mixed_valid_invalid(self, grn_page_multi):
        """Even rows get accepted > GP qty (invalid); odd rows get valid accepted.
        Submit must be blocked and only invalid rows show mat-error.
        """
        page_obj, (supplier_name, _) = grn_page_multi

        page_obj.open_add_form()
        row_count = page_obj.select_supplier_and_gp(supplier_name, expected_rows=2)
        assert row_count > 1, f"Expected multiple rows, got {row_count}"

        gp_qtys = [page_obj.read_gp_qty(i) for i in range(row_count)]

        for i, gp_qty in enumerate(gp_qtys):
            if i % 2 == 0:
                # invalid — accepted exceeds GP qty
                page_obj._fill_number_nth(page_obj.ACCEPTED_QTY, i, int(gp_qty) + 5)
            else:
                # valid — accepted safely below GP qty
                page_obj._fill_number_nth(page_obj.ACCEPTED_QTY, i, max(1, int(gp_qty) - 1))
            page_obj.page.wait_for_timeout(500)

        error_count_before_submit = page_obj.page.locator("mat-error").count()
        assert error_count_before_submit > 0, \
            "Expected immediate errors on rows where accepted > GP qty"

        page_obj.page.locator(page_obj.SUBMIT_BTN).click(force=True)
        page_obj.page.wait_for_timeout(800)

        assert page_obj.page.locator(page_obj.SUPPLIER_NAME).count() > 0, \
            "Form should stay open when some rows are invalid"
        assert page_obj.page.locator("mat-error").count() > 0, \
            "Errors should still be visible after blocked submit"

        page_obj.close_popup()


# ── Group 3: Validation ────────────────────────────────────────────────────

@pytest.mark.validation
class TestGRNValidation:
    def test_empty_submit_and_cancel(self, grn_page):
        """Empty submit must keep form open; Cancel must return to listing."""
        page_obj, _ = grn_page

        page_obj.open_add_form()
        page_obj.page.locator(page_obj.SUBMIT_BTN).click(force=True)
        page_obj.page.wait_for_timeout(800)
        assert page_obj.page.locator(page_obj.SUPPLIER_NAME).count() > 0, \
            "Form should stay open after empty submit"

        page_obj.close_popup()
        assert page_obj.page.locator("table.mat-mdc-table").count() > 0, \
            "Listing table not visible after cancel"


# ── Group 4: Regression ────────────────────────────────────────────────────

@pytest.mark.regression
class TestGRNRegression:
    def test_invalid_accepted_qty(self, grn_page):
        """accepted > GP qty → error; zero → error; negative → error; blank + submit → required."""
        page_obj, (supplier_name, _) = grn_page

        page_obj.open_add_form()
        page_obj.fill_form(supplier_name, accepted_qty=0)

        gp_qty = page_obj.read_gp_qty(0)
        assert gp_qty and gp_qty > 0, "GP qty must be auto-patched"

        # accepted > GP qty → rejected goes negative → error on rejected field (immediate)
        page_obj._fill_number_nth(page_obj.ACCEPTED_QTY, 0, int(gp_qty) + 1)
        page_obj.page.wait_for_timeout(600)
        assert page_obj.page.locator("mat-error").count() > 0, \
            "Expected error when accepted > GP qty"

        # zero accepted → error after submit
        page_obj._fill_number_nth(page_obj.ACCEPTED_QTY, 0, 0)
        page_obj.page.locator(page_obj.SUBMIT_BTN).click(force=True)
        page_obj.page.wait_for_timeout(800)
        assert page_obj.page.locator("mat-error").count() > 0, \
            "Expected error for accepted=0"

        # negative accepted → error after submit
        page_obj._fill_number_nth(page_obj.ACCEPTED_QTY, 0, -1)
        page_obj.page.locator(page_obj.SUBMIT_BTN).click(force=True)
        page_obj.page.wait_for_timeout(800)
        assert page_obj.page.locator("mat-error").count() > 0, \
            "Expected error for accepted=-1"

        # blank + submit → required
        page_obj._fill_number_nth(page_obj.ACCEPTED_QTY, 0, "")
        page_obj.page.locator(page_obj.SUBMIT_BTN).click(force=True)
        page_obj.page.wait_for_timeout(800)
        assert page_obj.page.locator("mat-error").count() > 0, \
            "Expected required error for blank accepted qty"

        # more than 4 decimal places → validation error (immediate)
        page_obj._fill_number_nth(page_obj.ACCEPTED_QTY, 0, 1.12345)
        page_obj.page.wait_for_timeout(600)
        errors = page_obj.page.locator("mat-error")
        assert errors.count() > 0 and any(
            "4 decimal" in e.inner_text() for e in errors.all()
        ), "Expected 'maximum of 4 decimal places' error for 5-decimal input"

        page_obj.close_popup()
