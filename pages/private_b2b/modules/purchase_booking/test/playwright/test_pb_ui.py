"""
Purchase Booking — Playwright UI test suite
============================================
Tests:
  1  Smoke        — create PB, verify ref_no in listing, verify txn_amount formula
  2  Multi-row    — all items: fill qty details per row, verify formula per row, submit
  3  Calculations — EBW, Labour, combined, Discount %, Round Off, Partial booking,
                    Other charges (transportation), Master total formula
  4  Validation   — submit empty form, assert validation errors appear
"""

import pytest


@pytest.mark.smoke
class TestPBSmoke:
    def test_create_search_and_verify(self, pb_page):
        """Create PB with same qty as QC grn_qty; verify ref_no in listing and formula."""
        page_obj, (supplier_name, grn_qtys) = pb_page

        # Vanilla: bags=1, qty=grn_qty per row
        row_configs = [(1, q) for q in grn_qtys]
        print(f"\n[SMOKE] supplier={supplier_name} row_configs={row_configs}")

        total, row_dicts = page_obj.create_record(supplier_name, row_configs)

        # Formula: txn_amount = rate × net_qty  (empty_bag_weight=0, labour=0)
        for i, r in enumerate(row_dicts):
            assert r["rate"] and r["rate"] > 0, f"Row {i}: rate not auto-patched from QC"
            assert r["net_qty"] and r["net_qty"] > 0, f"Row {i}: net_qty not calculated"
            expected_txn = round(r["rate"] * r["net_qty"], 2)
            assert abs(r["txn_amount"] - expected_txn) < 0.50, (
                f"Row {i}: txn_amount={r['txn_amount']:.2f} "
                f"!= rate {r['rate']:.2f} × net_qty {r['net_qty']:.2f} = {expected_txn:.2f}"
            )
            print(f"[SMOKE] row={i} rate={r['rate']} net_qty={r['net_qty']} txn={r['txn_amount']}")

        assert total > 0, "Total PB amount must be > 0"

        # Verify in listing — record just created so it's the first row
        ref_no = page_obj.get_ref_no_of_first_row()
        assert ref_no and ref_no.startswith("PURB/"), \
            f"Expected PB ref_no in first row, got: {ref_no}"

        print(f"[SMOKE] PB created: {ref_no}, total={total}")


# ── Group 2: Multi-row ─────────────────────────────────────────────────────────

@pytest.mark.calc
class TestPBMultiRow:
    def test_multi_row_formula(self, pb_page_multi):
        """GP with all items → QC auto-patches all rows in PB.
        Per row: fill qty details (bags=1, qty=grn_qty), verify txn_amount = rate × net_qty.
        Submit and verify ref_no in listing.
        """
        page_obj, (supplier_name, grn_qtys) = pb_page_multi

        row_configs = [(1, q) for q in grn_qtys]
        print(f"\n[MULTI] supplier={supplier_name} row_configs={row_configs}")

        total, row_dicts = page_obj.create_record(supplier_name, row_configs)

        assert len(row_dicts) >= 2, f"Expected multiple rows, got {len(row_dicts)}"

        for i, r in enumerate(row_dicts):
            assert r["rate"] and r["rate"] > 0, f"Row {i}: rate not auto-patched from QC"
            assert r["net_qty"] and r["net_qty"] > 0, f"Row {i}: net_qty not calculated"
            expected_txn = round(r["rate"] * r["net_qty"], 2)
            assert abs(r["txn_amount"] - expected_txn) < 0.50, (
                f"Row {i}: txn_amount={r['txn_amount']:.2f} "
                f"!= rate {r['rate']:.2f} × net_qty {r['net_qty']:.2f} = {expected_txn:.2f}"
            )
            print(f"[MULTI] row={i} rate={r['rate']} net_qty={r['net_qty']} txn={r['txn_amount']}")

        assert total > 0, "Total PB amount must be > 0"
        expected_total = sum(r["txn_amount"] for r in row_dicts)
        assert abs(total - expected_total) < 1.0, (
            f"Master total {total:.2f} != sum of row txn_amounts {expected_total:.2f}"
        )

        ref_no = page_obj.get_ref_no_of_first_row()
        assert ref_no and ref_no.startswith("PURB/"), \
            f"Expected PB ref_no in first row, got: {ref_no}"

        print(f"[MULTI] PB created: {ref_no}, total={total}, rows={len(row_dicts)}")


# ── Group 3: Calculation tests ──────────────────────────────────────────────────

@pytest.mark.calc
class TestPBCalc:
    """
    All six formula scenarios in ONE PB record using the multi-row QC session.

    Since 1 QC → 1 PB (QC is hidden once PB is created), we use pb_page_multi
    which provides a multi-row QC. Each item row gets a different calc scenario.
    Round-off debit and credit are both filled on the header of the same PB
    and verified as: master_total = SUM(txn) + debit - credit.

    Row assignments (graceful if fewer items available):
        row 0 → EBW only
        row 1 → Labour only
        row 2 → EBW + Labour combined
        row 3 → Discount %
        row 4+ → vanilla

    Formulas:
        net_qty = qty - ebw
        txn     = rate × net_qty - labour
        master  = SUM(txn) + round_off_debit - round_off_credit
    """

    def test_all_calculations(self, pb_page_multi):
        """
        One PB, all formulas verified.

        Row assignments:
            row 0 → EBW only          → net_qty = qty - ebw; gross = rate × net_qty
            row 1 → Labour only        → final = gross - labour
            row 2 → EBW + Labour       → net_qty = qty - ebw; final = gross - labour
            row 3 → Discount %         → final = gross × (1 - disc/100)
            row 4 → Round Off debit/credit → final = gross + debit - credit
            row 5+ → vanilla

        Master Total = SUM(per-row finals)
        gross = rate × net_qty  (what UI shows as Transaction Amount — no deductions)
        """
        page_obj, (supplier_name, grn_qtys) = pb_page_multi
        n = len(grn_qtys)
        assert n >= 2, f"Need at least 2 item rows for calc test; got {n}"

        LABOUR = 500.0
        DISC   = 10.0
        DEBIT  = 1.0    # ERP max per row is 1
        CREDIT = 0.5    # ERP max per row is 1

        row_configs      = [(1, q) for q in grn_qtys]
        row_ebw          = [None] * n
        row_labour       = [None] * n
        row_discount     = [None] * n
        row_round_debit  = [None] * n
        row_round_credit = [None] * n

        ebw_0 = max(1, grn_qtys[0] // 5)
        row_ebw[0] = ebw_0                              # row 0: EBW only

        if n >= 2:
            row_labour[1] = LABOUR                      # row 1: Labour only

        if n >= 3:
            ebw_2 = max(1, grn_qtys[2] // 5)
            row_ebw[2]    = ebw_2                       # row 2: EBW + Labour
            row_labour[2] = LABOUR

        if n >= 4:
            row_discount[3] = DISC                      # row 3: Discount %

        if n >= 5:
            row_round_debit[4]  = DEBIT                 # row 4: Round Off debit + credit
            row_round_credit[4] = CREDIT

        # row 5: Partial booking — intentionally book less than QC accepted qty
        partial_qty = None
        if n >= 6:
            partial_qty = max(1, grn_qtys[5] // 2)
            row_configs[5] = (1, partial_qty)           # override to partial qty

        TRANSPORT = 100.0

        print(f"\n[CALC] supplier={supplier_name} rows={n} grn_qtys={grn_qtys}")
        if partial_qty:
            print(f"       row 5 partial: {partial_qty} of {grn_qtys[5]} (QC accepted)")

        total, rows = page_obj.create_record(
            supplier_name,
            row_configs=row_configs,
            row_ebw=row_ebw,
            row_labour=row_labour,
            row_discount=row_discount,
            row_round_debit=row_round_debit,
            row_round_credit=row_round_credit,
            transportation=TRANSPORT,
        )

        failures = []

        # ── Row 0: EBW ───────────────────────────────────────────────────
        # UI Transaction Amount = rate × net_qty (gross); net_qty reflects EBW
        r = rows[0]
        expected_net = grn_qtys[0] - ebw_0
        expected_gross = round(r["rate"] * expected_net, 2)
        print(f"[ROW 0 / EBW] qty={grn_qtys[0]} ebw={ebw_0} "
              f"net_qty={r['net_qty']} gross={r['txn_amount']:.2f} expected_gross={expected_gross:.2f}")
        if abs(r["net_qty"] - expected_net) >= 0.05:
            failures.append(f"[EBW] net_qty={r['net_qty']:.2f} != qty {grn_qtys[0]} - ebw {ebw_0} = {expected_net}")
        if abs(r["txn_amount"] - expected_gross) >= 1.0:
            failures.append(f"[EBW] gross={r['txn_amount']:.2f} != rate {r['rate']:.2f} × net_qty {expected_net} = {expected_gross:.2f}")

        # ── Row 1: Labour ─────────────────────────────────────────────────
        # Transaction Amount (gross) stays rate×net_qty; labour only reduces master total
        if n >= 2:
            r = rows[1]
            print(f"[ROW 1 / LABOUR] qty={grn_qtys[1]} net_qty={r['net_qty']} gross={r['txn_amount']:.2f} labour={LABOUR}")

        # ── Row 2: EBW + Labour ───────────────────────────────────────────
        if n >= 3:
            r = rows[2]
            expected_net = grn_qtys[2] - ebw_2
            expected_gross = round(r["rate"] * expected_net, 2)
            print(f"[ROW 2 / EBW+LABOUR] qty={grn_qtys[2]} ebw={ebw_2} "
                  f"net_qty={r['net_qty']} gross={r['txn_amount']:.2f} labour={LABOUR}")
            if abs(r["net_qty"] - expected_net) >= 0.05:
                failures.append(f"[COMBINED/EBW] net_qty={r['net_qty']:.2f} != qty {grn_qtys[2]} - ebw {ebw_2} = {expected_net}")
            if abs(r["txn_amount"] - expected_gross) >= 1.0:
                failures.append(f"[COMBINED/EBW] gross={r['txn_amount']:.2f} != {expected_gross:.2f}")

        # ── Row 3: Discount % ─────────────────────────────────────────────
        # Transaction Amount (gross) stays unchanged; discount only reduces master total
        if n >= 4:
            r = rows[3]
            print(f"[ROW 3 / DISC] qty={grn_qtys[3]} net_qty={r['net_qty']} gross={r['txn_amount']:.2f} disc={DISC}%")

        # ── Row 4: Round Off ──────────────────────────────────────────────
        if n >= 5:
            r = rows[4]
            print(f"[ROW 4 / ROUNDOFF] qty={grn_qtys[4]} gross={r['txn_amount']:.2f} debit={DEBIT} credit={CREDIT}")

        # ── Row 5: Partial booking ────────────────────────────────────────
        if n >= 6 and partial_qty is not None:
            r = rows[5]
            full_gross = r["rate"] * grn_qtys[5]
            print(f"[ROW 5 / PARTIAL] grn_qty={grn_qtys[5]} booked={partial_qty} "
                  f"net_qty={r['net_qty']} gross={r['txn_amount']:.2f} full_would_be={full_gross:.2f}")
            if r["net_qty"] != partial_qty:
                failures.append(f"[PARTIAL] net_qty={r['net_qty']} != partial_qty {partial_qty}")
            if r["txn_amount"] >= full_gross - 0.01:
                failures.append(
                    f"[PARTIAL] txn={r['txn_amount']:.2f} should be < full gross {full_gross:.2f}"
                )

        # Transportation is stored in other_charges, does not affect Total Amount
        print(f"[OTHER CHARGES] transportation={TRANSPORT} (stored separately, not in total)")

        # ── Master Total = SUM of per-row finals ──────────────────────────
        # final_i = gross_i - gross_i×disc_i/100 - labour_i + debit_i - credit_i
        expected_total = 0.0
        for i, r in enumerate(rows):
            gross    = r["txn_amount"] or 0
            disc_pct = row_discount[i] or 0
            labour   = row_labour[i]  or 0
            debit    = row_round_debit[i]  or 0
            credit   = row_round_credit[i] or 0
            expected_total += gross - (gross * disc_pct / 100) - labour + debit - credit

        expected_total = round(expected_total, 2)
        print(f"[MASTER] expected={expected_total:.2f} got={total:.2f}")
        if abs(total - expected_total) >= 2.0:
            failures.append(
                f"[MASTER] total={total:.2f} != expected {expected_total:.2f} "
                f"(delta={total - expected_total:.2f})"
            )

        ref_no = page_obj.get_ref_no_of_first_row()
        assert ref_no and ref_no.startswith("PURB/"), f"Expected PURB/ ref_no, got: {ref_no}"
        print(f"[CALC] PB created: {ref_no}")

        assert not failures, "Calculation failures:\n" + "\n".join(failures)


# ── Group 4: Validation ────────────────────────────────────────────────────────

@pytest.mark.validation
class TestPBValidation:
    """Submit empty/incomplete PB form and assert the ERP shows validation errors.

    No GP→GRN→QC chain needed — uses pb_bare_page which just navigates to the
    PB listing. We open the add form and immediately click Submit without filling
    anything, expecting Angular mat-errors or a SweetAlert validation response.
    """

    def test_submit_empty_form(self, pb_bare_page):
        """Open PB add form, submit without filling any fields, expect validation errors."""
        page_obj = pb_bare_page
        page_obj.open_add_form()

        # Click Submit without filling Supplier, QC, Currency, or any item data
        page_obj.page.locator(page_obj.SUBMIT_BTN).click()
        page_obj.page.wait_for_timeout(2000)

        # Angular client-side validation → mat-error elements
        mat_errors = page_obj.page.locator("mat-error").count()

        # Server-side validation → SweetAlert with "Validation" in title
        swal_visible = page_obj.page.locator(".swal2-container").is_visible()
        swal_title = ""
        if swal_visible:
            swal_title = page_obj.page.locator("#swal2-title").inner_text().strip()
            # Dismiss the alert so fixture teardown can close the popup cleanly
            page_obj.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            page_obj.page.wait_for_timeout(500)

        print(f"\n[VALIDATION] mat_errors={mat_errors} swal_visible={swal_visible} swal_title='{swal_title}'")

        assert mat_errors > 0 or (swal_visible and ("Validation" in swal_title or "Failed" in swal_title)), (
            f"Expected validation errors on empty submit; "
            f"mat_errors={mat_errors}, swal='{swal_title}'"
        )
