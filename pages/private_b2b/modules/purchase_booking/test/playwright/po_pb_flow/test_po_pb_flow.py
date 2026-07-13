"""
PO → PB direct flow tests (Rolex Traders tenant).

Flow: create PO → create PB directly against it (no GP / GRN / QC).

Classes:
  TestPO_PB_DirectFlow   — single-item PO with disc/int → PB qty/rate/txn assertions
  TestPO_PB_MultiRow     — 2-item PO with per-row disc/int → PB assertions per row
  TestPO_PB_CustomRate   — manually override PO rate → PB must carry the new rate
  TestPO_PB_NoGST        — PO with GST off → PB txn = qty × rate (no tax)
  TestPOValidations      — PO form validation rules (Rolex Traders tenant)
"""

import pytest


def _assert_pb_rows(po_rows, pb_rows, po_ref_no):
    """Shared row-level assertion + pretty-print used by all PB test steps."""
    assert len(pb_rows) == len(po_rows), (
        f"PB row count {len(pb_rows)} != PO row count {len(po_rows)}"
    )

    print(f"\n  PO: {po_ref_no}")
    print(f"  {'Row':<4} {'Item':<20} {'PO qty':>7} {'PB qty':>7} {'Rate':>9} "
          f"{'Disc%':>6} {'Int%':>5} {'PO txn':>11} {'PB txn':>11}")
    print(f"  {'-'*85}")

    for i, (po_r, pb_r) in enumerate(zip(po_rows, pb_rows)):
        po_qty  = int(po_r["qty"])
        po_rate = po_r["rate"]
        disc    = po_r.get("disc_pct", 0) or 0
        intr    = po_r.get("int_pct",  0) or 0
        po_txn  = po_r["txn_amount"]   # ERP-calculated at PO creation
        pb_qty  = pb_r["net_qty"]
        pb_rate = pb_r["rate"]
        pb_txn  = pb_r["txn_amount"]

        assert pb_qty == po_qty, f"Row {i}: PB qty {pb_qty} != PO qty {po_qty}"
        assert abs(pb_rate - po_rate) < 0.01, (
            f"Row {i}: PB rate {pb_rate} != PO rate {po_rate}"
        )
        assert abs(pb_txn - po_txn) < 1.0, (
            f"Row {i}: PB txn {pb_txn} != PO txn {po_txn} "
            f"(qty={po_qty}, rate={po_rate}, disc={disc}%, int={intr}%)"
        )

        print(f"  {i:<4} {po_r['item_name']:<20} {po_qty:>7} {pb_qty:>7} {po_rate:>9.2f} "
              f"{disc:>6} {intr:>5} {po_txn:>11.2f} {pb_txn:>11.2f}")

    print(f"  {'-'*85}")


# ── Single-item flow (with discount & interest) ───────────────────────────────

@pytest.mark.po_pb
class TestPO_PB_DirectFlow:

    def test_step1_create_po(self, po_page, integration_state):
        """Create a single-item PO with 5% discount and 2% interest."""
        total, row_dicts, supplier_name, location, ref_no = \
            po_page.create_record_for_integration(item_configs=[(10, 5, 2)])

        assert ref_no,        "PO ref_no must be non-empty"
        assert supplier_name, "Supplier must be captured"
        assert total > 0,     "PO total must be > 0"

        integration_state["po_ref_no"]     = ref_no
        integration_state["supplier_name"] = supplier_name
        integration_state["po_total"]      = total
        integration_state["po_rows"]       = row_dicts

        r = row_dicts[0]
        print("\n" + "=" * 60)
        print(f"  PO created:    {ref_no}")
        print(f"  Supplier:      {supplier_name}")
        print(f"  Item:          {r['item_name']}")
        print(f"  Rate:          {r['rate']:.2f}  Qty: {r['qty']}")
        print(f"  Disc%: {r['disc_pct']}  Int%: {r['int_pct']}  Txn: {r['txn_amount']:.2f}")
        print(f"  PO Total:      {total:.2f}")
        print("=" * 60)

    def test_step2_create_pb(self, pb_page, integration_state):
        """Create PB; qty/rate/txn must match PO (disc & int already baked into txn)."""
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        supplier_name = integration_state["supplier_name"]
        po_rows       = integration_state["po_rows"]

        row_configs = [(1, int(r["qty"])) for r in po_rows]
        total_amount, pb_rows = pb_page.create_record_from_po(
            supplier_name, row_configs=row_configs
        )

        assert total_amount > 0, "PB total must be > 0"

        print("\n" + "=" * 60)
        _assert_pb_rows(po_rows, pb_rows, integration_state["po_ref_no"])

        expected_total = sum(r["txn_amount"] for r in po_rows)
        assert abs(total_amount - expected_total) < 1.0, (
            f"PB total {total_amount} != expected {expected_total}"
        )
        integration_state["pb_total"] = total_amount
        print(f"  TOTAL  expected: {expected_total:.2f}   actual: {total_amount:.2f}  -> MATCH")
        print("=" * 60)


# ── Multi-item flow (with discount & interest per row) ────────────────────────

@pytest.mark.po_pb
class TestPO_PB_MultiRow:

    def test_step1_create_po_multi(self, po_page, integration_state):
        """Create a 2-item PO: row0 disc=5%/int=2%, row1 disc=3%/int=1%."""
        total, row_dicts, supplier_name, location, ref_no = \
            po_page.create_record_for_integration(
                item_configs=[(10, 5, 2), (5, 3, 1)]
            )

        assert ref_no,              "PO ref_no must be non-empty"
        assert len(row_dicts) == 2, f"Expected 2 PO rows, got {len(row_dicts)}"
        assert total > 0,           "PO total must be > 0"

        integration_state["po_ref_no"]     = ref_no
        integration_state["supplier_name"] = supplier_name
        integration_state["po_total"]      = total
        integration_state["po_rows"]       = row_dicts

        print("\n" + "=" * 60)
        print(f"  PO created:    {ref_no}  |  Supplier: {supplier_name}")
        for i, r in enumerate(row_dicts):
            print(f"  Row {i}: {r['item_name']:<20}  qty={r['qty']}  rate={r['rate']:.2f}"
                  f"  disc={r['disc_pct']}%  int={r['int_pct']}%  txn={r['txn_amount']:.2f}")
        print(f"  PO Total:      {total:.2f}")
        print("=" * 60)

    def test_step2_create_pb_multi(self, pb_page, integration_state):
        """Create PB for all rows; qty/rate/txn must match PO row by row."""
        if not integration_state.get("po_ref_no"):
            pytest.skip("PO not created in step 1")

        supplier_name = integration_state["supplier_name"]
        po_rows       = integration_state["po_rows"]

        row_configs = [(1, int(r["qty"])) for r in po_rows]
        total_amount, pb_rows = pb_page.create_record_from_po(
            supplier_name, row_configs=row_configs
        )

        assert total_amount > 0, "PB total must be > 0"

        print("\n" + "=" * 60)
        _assert_pb_rows(po_rows, pb_rows, integration_state["po_ref_no"])

        expected_total = sum(r["txn_amount"] for r in po_rows)
        assert abs(total_amount - expected_total) < 1.0, (
            f"PB total {total_amount} != expected {expected_total}"
        )
        integration_state["pb_total"] = total_amount
        print(f"  TOTAL  expected: {expected_total:.2f}   actual: {total_amount:.2f}  -> MATCH")
        print("=" * 60)
