"""
QC — Playwright UI test suite
===============================
Tests:
  1  Smoke         — create QC, verify ref_no in listing, view is read-only
  2  Calc          — single row: all 4 formulas verified
  3  Calc boundary — min deduction [1,1,1], high deduction [50,30,20]
  4  Multi-row Calc — all items: all 4 formulas per row, submit + verify listing
  5  Validation    — empty submit blocked + cancel returns to listing
  6  Regression    — actual_value > max, < min, blank all show errors
"""

import pytest


def _deduction_pct(page_obj, row_index, actual_values):
    """Compute expected deduction_pct using CQP config when available.

    Formula: deduction_pct = sum(actual_value_i * multiplier_i)
    Falls back to multiplier=1 per param if config is missing.
    """
    params = []
    item_names = getattr(page_obj, "item_names", [])
    cqp_config = getattr(page_obj, "cqp_config", {})
    if item_names and cqp_config and row_index < len(item_names):
        params = cqp_config.get(item_names[row_index], [])

    if params and len(params) == len(actual_values):
        return sum(v * p["multiplier"] for p, v in zip(params, actual_values))

    return sum(float(v) for v in actual_values)


def _assert_qc_formulas(page_obj, row_index, actual_values):
    """Assert all 4 QC formulas for a given row after filling actual values.

    Strategy:
    - deduction_pct: verified against our formula with a display-rounding tolerance
      (app may truncate 0.0303 → 0.0; tolerance = max(0.1, 5% of expected))
    - deduction_rate / qc_rate / txn_amount: chain is verified using the APP's own
      displayed deduction_pct so precision matches exactly what the app computed.
    """
    base_rate    = page_obj.read_base_rate(row_index)
    accepted_qty = page_obj.read_accepted_qty(row_index)
    assert base_rate and base_rate > 0,       f"Row {row_index}: base_rate not patched"
    assert accepted_qty and accepted_qty > 0, f"Row {row_index}: accepted_qty not patched"

    expected_deduction_pct = _deduction_pct(page_obj, row_index, actual_values)
    actual_deduction_pct   = page_obj.read_deduction_pct(row_index)

    pct_tol = max(0.1, abs(expected_deduction_pct) * 0.05)
    assert actual_deduction_pct == pytest.approx(expected_deduction_pct, abs=pct_tol), \
        f"Row {row_index}: deduction_pct={actual_deduction_pct}, expected {expected_deduction_pct:.4f}"

    # Chain uses the app's own displayed deduction_pct as the source of truth
    expected_deduction_rate = round(base_rate * actual_deduction_pct / 100, 2)
    expected_qc_rate        = round(base_rate - expected_deduction_rate, 2)
    expected_txn_amount     = round(accepted_qty * expected_qc_rate, 2)

    actual_deduction_rate = page_obj.read_deduction_rate(row_index)
    actual_qc_rate        = page_obj.read_qc_rate(row_index)
    actual_txn_amount     = page_obj.read_txn_amount(row_index)

    assert actual_deduction_rate == pytest.approx(expected_deduction_rate, abs=0.01), \
        f"Row {row_index}: deduction_rate={actual_deduction_rate}, expected {expected_deduction_rate}"
    assert actual_qc_rate == pytest.approx(expected_qc_rate, abs=0.01), \
        f"Row {row_index}: qc_rate={actual_qc_rate}, expected {expected_qc_rate}"
    assert actual_txn_amount == pytest.approx(expected_txn_amount, abs=0.01), \
        f"Row {row_index}: txn_amount={actual_txn_amount}, expected {expected_txn_amount}"


# ── Group 1: Smoke ─────────────────────────────────────────────────────────

@pytest.mark.smoke
class TestQCSmoke:
    def test_create_search_and_view(self, qc_page):
        """Create QC with valid actual values; verify ref_no in listing; view is read-only."""
        page_obj, (supplier_name, _) = qc_page

        page_obj.open_add_form()
        page_obj.select_supplier_and_gp(supplier_name)

        actual_values = page_obj.safe_actual_values(0, max_pct=15)
        print(f"\n[SMOKE] actual_values={actual_values}, sum={sum(actual_values)}")
        page_obj.open_qc_param_popup(0)
        page_obj.fill_actual_values(actual_values)
        page_obj.click_done()

        page_obj.page.locator(page_obj.SUBMIT_BTN).click()
        page_obj.handle_success_alert()
        page_obj.navigate_to_page()

        ref_no = page_obj.get_ref_no_of_first_row()
        assert ref_no, "Expected a ref_no after QC creation"

        page_obj.search_by_ref_no(ref_no)
        assert page_obj.is_qc_in_table(ref_no), \
            f"QC {ref_no} not found in listing after creation"

        page_obj.click_row_action(0, "View")
        page_obj.page.wait_for_selector("input[readonly]", timeout=25000)
        page_obj.page.wait_for_timeout(500)
        assert page_obj.page.locator(page_obj.SUBMIT_BTN).count() == 0, \
            "Submit must not appear in View mode"
        page_obj.navigate_to_page()


# ── Group 2: Single-row Calculation ────────────────────────────────────────

@pytest.mark.calc
class TestQCCalc:
    def test_single_row_formula(self, qc_page):
        """Random actual values → assert deduction%, deduction_rate, qc_rate, txn_amount."""
        page_obj, (supplier_name, _) = qc_page

        page_obj.open_add_form()
        page_obj.select_supplier_and_gp(supplier_name)

        actual_values = page_obj.safe_actual_values(0, max_pct=30)
        print(f"\n[CALC] actual_values={actual_values}, sum={sum(actual_values)}")
        page_obj.open_qc_param_popup(0)
        page_obj.fill_actual_values(actual_values)
        page_obj.click_done()
        page_obj.page.wait_for_timeout(800)

        _assert_qc_formulas(page_obj, 0, actual_values)
        page_obj.close_popup()

    def test_boundary_min_deduction(self, qc_page):
        """actual_values = min_q per param → minimum possible deduction → all formulas hold.

        Formula: deduction_pct = sum(actual_value * multiplier). Smallest valid values → lowest deduction.
        """
        page_obj, (supplier_name, _) = qc_page

        page_obj.open_add_form()
        page_obj.select_supplier_and_gp(supplier_name)

        params = []
        item_names = getattr(page_obj, "item_names", [])
        cqp_config = getattr(page_obj, "cqp_config", {})
        if item_names and cqp_config:
            params = cqp_config.get(item_names[0], [])

        # min_q per param → smallest valid actual_value → minimum deduction
        actual_values = [int(p["min_q"]) for p in params] if params else [1, 1, 1]
        page_obj.open_qc_param_popup(0)
        page_obj.fill_actual_values(actual_values)
        page_obj.click_done()
        page_obj.page.wait_for_timeout(800)

        _assert_qc_formulas(page_obj, 0, actual_values)
        page_obj.close_popup()

    def test_boundary_high_deduction(self, qc_page):
        """High deduction (up to 60% of base_rate) → all formulas hold, qc_rate stays positive."""
        page_obj, (supplier_name, _) = qc_page

        page_obj.open_add_form()
        page_obj.select_supplier_and_gp(supplier_name)

        actual_values = page_obj.safe_actual_values(0, max_pct=60)
        print(f"\n[HIGH] actual_values={actual_values}, sum={sum(actual_values)}")
        page_obj.open_qc_param_popup(0)
        page_obj.fill_actual_values(actual_values)
        page_obj.click_done()
        page_obj.page.wait_for_timeout(800)

        _assert_qc_formulas(page_obj, 0, actual_values)

        qc_rate = page_obj.read_qc_rate(0)
        assert qc_rate is not None and qc_rate > 0, \
            f"qc_rate should be positive at 60% deduction, got {qc_rate}"

        page_obj.close_popup()


# ── Group 3: Multi-row Calculation ─────────────────────────────────────────

@pytest.mark.calc
class TestQCMultiRowCalc:
    def test_multi_row_formula(self, qc_page_multi):
        """GP with all items → QC auto-patches all rows.
        Per row: fill 3 random actual values, assert all 4 formulas.
        Submit + verify ref_no in listing.
        """
        page_obj, (supplier_name, _) = qc_page_multi

        page_obj.open_add_form()
        page_obj.select_supplier_and_gp(supplier_name)

        row_count = page_obj.count_item_rows()
        assert row_count > 1, f"Expected multiple item rows, got {row_count}"

        all_actual_values = []
        for i in range(row_count):
            actual_values = page_obj.safe_actual_values(i, max_pct=20)
            print(f"\n[MULTI] row={i} actual_values={actual_values}, sum={sum(actual_values)}")
            page_obj.open_qc_param_popup(i)
            page_obj.fill_actual_values(actual_values)
            page_obj.click_done()
            page_obj.page.wait_for_timeout(800)
            all_actual_values.append(actual_values)

        for i, actual_values in enumerate(all_actual_values):
            _assert_qc_formulas(page_obj, i, actual_values)

        page_obj.page.locator(page_obj.SUBMIT_BTN).click()
        page_obj.handle_success_alert()
        page_obj.navigate_to_page()

        ref_no = page_obj.get_ref_no_of_first_row()
        assert ref_no, "Expected a ref_no after multi-row QC submission"

        page_obj.search_by_ref_no(ref_no)
        assert page_obj.is_qc_in_table(ref_no), \
            f"Multi-row QC {ref_no} not found in listing after save"


# ── Group 4: Validation ────────────────────────────────────────────────────

@pytest.mark.validation
class TestQCValidation:
    def test_empty_submit_and_cancel(self, qc_page):
        """Empty submit must keep form open; Cancel must return to listing."""
        page_obj, _ = qc_page

        page_obj.open_add_form()
        page_obj.page.locator(page_obj.SUBMIT_BTN).click(force=True)
        page_obj.page.wait_for_timeout(800)
        assert page_obj.page.locator(page_obj.SUPPLIER_NAME).count() > 0, \
            "Form should stay open after empty submit"

        page_obj.close_popup()
        assert page_obj.page.locator("table.mat-mdc-table").count() > 0, \
            "Listing table not visible after cancel"

