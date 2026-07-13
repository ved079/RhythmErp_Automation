# Purchase Flow Tests — Developer Notes

## Overview

End-to-end integration tests covering the full PO → GP → GRN chain for private B2B.
These tests are sequential within each class (later steps depend on state from earlier ones)
and use parallel threading to simulate real-world concurrent usage across two browser sessions.

---

## File Structure

```
pages/private_b2b/modules/Purchase_Flow_Tests/
    PURCHASE_FLOW_NOTES.md              # this file
    test/playwright/
        conftest.py                     # class-scoped browser, integration_state fixture
        test_po_gp_grn.py               # PO → GP → GRN flows (16 tests, 4 classes)
        #   TestPOGPGRNFlow              3  PO → GP → GRN (smoke)
        #   TestPOSingleItemFullCycle    6  PO → GP1 → GRN1 → GP2 → GRN2 → PO Closed
        #   TestPO_GP_GRN_Single_Item_Flow  3  PO → GP1‖GP2 → GRN1‖GRN2 → PO Closed (parallel)
        #   TestPO_GP_GRN_Multi_Item_Flow   4  PO → 4 GPs in 2 parallel pairs → PO Closed
        test_po_grn_qc_pb.py            # PO → GP → GRN → QC → PB → Closed (12 tests, 2 classes)
        #   TestPO_GRN_QC_PB_Single_Item_Flow  6  PO → GP → GRN → QC → PB → PO Closed (1 item)
        #   TestPO_GRN_QC_PB_Multi_Item_Flow   6  PO → GP → GRN → QC → PB → PO Closed (3 items)
        test_gp_grn_qc_pb.py            # GP → GRN → QC → PB, no PO (8 tests, 2 classes)
        #   TestGP_GRN_QC_PB_Single_Item_Flow  4  GP → GRN (no PO) → QC → PB (1 item)
        #   TestGP_GRN_QC_PB_Multi_Item_Flow   4  GP → GRN (no PO) → QC → PB (3 items)
```

---

## Test Classes

### TestPOGPGRNFlow — 3 tests (smoke)
`PO → GP → GRN`. Single item, single pair. Verifies PO is not yet closed after one partial GRN.

### TestPOSingleItemFullCycle — 6 tests (sequential 2 GPs)
`PO → GP1 → GRN1 → GP2 → GRN2 → PO Closed`. Two GP→GRN flows run sequentially. PO closes after both GRNs exhaust the qty.

### TestPO_GP_GRN_Single_Item_Flow — 3 tests (parallel GP+GRN)
`PO → GP1‖GP2 → GRN1‖GRN2 → PO Closed`. Two GP→GRN flows run in parallel threads. Submit sequencing via `threading.Event` avoids duplicate ref numbers.

### TestPO_GP_GRN_Multi_Item_Flow — 4 tests (4 GPs in 2 parallel pairs)
```
PO:  A=25  B=20  C=15

Pair 1 (parallel):
  GP1 → GRN1 :  A=10
  GP2 → GRN2 :  B=10, C=8

Pair 2 (parallel, after Pair 1 GRNs committed):
  GP3 → GRN3 :  A=15, B=5
  GP4 → GRN4 :  B=5,  C=7

Totals: A=10+15=25 ✓  B=10+5+5=20 ✓  C=8+7=15 ✓  → PO Closed
```

### TestPO_GRN_QC_PB_Single_Item_Flow (1-item full chain)
Sequential E2E: PO (qty=100) → GP → GRN (linked to PO) → QC (fills actual values) → PB → PO Closed.
CQP config is read per item before QC to generate safe actual values (deduction_pct ≤ 15%).

### TestPO_GRN_QC_PB_Multi_Item_Flow (3-item full chain)
Sequential E2E: PO (A=25, B=20, C=15) → GP (3 items) → GRN (3 rows) → QC (3 rows) → PB (3 rows) → PO Closed.
GRN accepted_qty per row is read back from the form and threaded through QC → PB.

---

## Architecture

### Per-thread Playwright instances
Parallel workers each create their own `sync_playwright()` + browser + login.
Playwright's sync API binds a Page to the OS thread that created it — sharing
across threads raises `greenlet.error: Cannot switch to a different thread`.

### Submit sequencing via threading.Event
GP submits and GRN submits are serialised with `threading.Event` pairs:
- `gp_done_event` — Tab 2 waits for Tab 1's GP to commit before submitting its own GP
- `grn_done_event` — Tab 2 waits for Tab 1's GRN to commit before submitting its own GRN

Without this, both threads hit Submit simultaneously and the ERP assigns the same
auto-increment ref number to both records.

### `_run_parallel_pair(supplier, location, po_ref_no, items_a, items_b, label_a, label_b)`
Reusable helper that spins two `_gp_grn_worker` threads with the event chain wired up.

### `_gp_grn_worker(...)`
Universal worker — accepts `items` as a list of `(item_name, bags, qty)` tuples.
Both GP and GRN form-filling run in parallel; only the Submit clicks are sequenced.

---

## Key Quirks

### 1. PO status recalculation requires a new PO INSERT
The ERP only marks a PO as "Closed" (balance exhausted) when a new PO record is
inserted — a simple page refresh or form open/cancel does not trigger recalculation.
`trigger_po_status_recalculation()` creates a minimal throwaway PO to fire this trigger.

### 2. Multi-row item selection — Angular selectionChange doesn't fire for rows 2+ (PO and GP)
Affects both PO (`create_record_for_integration`) and GP (`fill_items_form`).
See `PO_notes.md § Bugs/Quirks #7` for full root-cause explanation.

**Workaround (same pattern in both modules):**
Switch from pre-create-all-rows to add-row-then-fill. For each new row i > 0, after selecting its item:
1. Select row 0's item on row i (triggers duplicate-item warning → wakes Angular's selectionChange)
2. Re-select the correct item for row i → fields now auto-patch correctly

For PO this fixes rate auto-fetch. For GP this fixes item registration so the form submits correctly.

### 3. GRN form uses placeholder-based XPath (no mat-label)
GRN's Supplier, Gate Pass, and PO dropdowns have no `mat-label` — only placeholder text.
Selectors use `//mat-select[.//span[contains(@class,'mat-mdc-select-placeholder') and contains(.,'...')]]`.

### 4. Location + Type of Sale must match between PO and GP for GRN linkage
GRN's "Select purchase order" dropdown only shows POs that match the GP's location
and type_of_sale. Mismatched fields mean the PO won't appear in the GRN dropdown.
`TestPOMultiItemParallelCycle` hardcodes location="Pune" across all steps.

### 5. GP ref number read timing
Each worker reads its own GP ref number immediately after `navigate_to_page()` in
`submit_items_form` — before GRN filling starts. This ensures the correct ref is
captured even under parallel server load.

---

## Running

```bash
# PO→GP→GRN flows (test_po_gp_grn.py)
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/test_po_gp_grn.py -v -s
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/test_po_gp_grn.py::TestPO_GP_GRN_Single_Item_Flow -v -s
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/test_po_gp_grn.py::TestPO_GP_GRN_Multi_Item_Flow -v -s

# PO→GP→GRN→QC→PB→Closed flows (test_po_grn_qc_pb.py)
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/test_po_grn_qc_pb.py -v -s
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/test_po_grn_qc_pb.py::TestPO_GRN_QC_PB_Single_Item_Flow -v -s
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/test_po_grn_qc_pb.py::TestPO_GRN_QC_PB_Multi_Item_Flow -v -s

# GP→GRN→QC→PB flows, no PO (test_gp_grn_qc_pb.py)
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/test_gp_grn_qc_pb.py -v -s
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/test_gp_grn_qc_pb.py::TestGP_GRN_QC_PB_Single_Item_Flow -v -s
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/test_gp_grn_qc_pb.py::TestGP_GRN_QC_PB_Multi_Item_Flow -v -s

# All 36 tests
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/ -v -s -m integration
```

## Environment Variables Required

```
RHYTHMERP_LOGIN_URL   (default: https://rhythmerp.algorhythms.in)
RHYTHMERP_EMAIL
RHYTHMERP_PASSWORD
```
