# Purchase Booking (PB) Fix Notes

Full PO → GP → GRN → QC → PB chain now working end-to-end via batch script and web UI.

---

## Root Causes (in order of discovery)

### 1. Missing `purchase_booking_ref_type: 144`
The field was simply absent from our payload. The ERP required it for routing the record
through the correct booking flow. Adding it was a prerequisite for getting past INPUT_VALIDATION.

### 2. `round_off_debit_amount` / `round_off_credit_amount` — must be `null`, not `0.0`
The ERP validator fires only when the field is non-null:
> "Amount should be greater than 0"

Sending `0.0` or `"0.000"` triggers the error. Sending `null` (Python `None`) bypasses it.
Both fields must be null together — sending one null and one non-null crashes the server with a 500.

### 3. `posting_status` must be `""`, not `"Post"`
The UI sends an empty string. Sending `"Post"` was silently accepted at the 201 level
but caused downstream accounting mismatches.

### 4. `section_ref_id` must be `"0"` (string), not `0` (int)
The ERP serializer treats these differently. Integer `0` caused a 500 at the
`section_ref_id`-based ledger lookup step.

### 5. `tds_amount` must be `null`, not `"0.000"`
Same pattern as round_off — non-null zero triggers a validator that expects `> 0`.

### 6. Monetary amounts must be **floats**, not f3-formatted strings
`"1660996.272"` (string) vs `1660996.2716` (float). The ERP CALCULATION step reads
the submitted values numerically; string amounts caused silent truncation that
misaligned the DR/CR totals in accounting.

### 7. **Missing GST** — the biggest one
**Symptom:** `PURCHASE_ACCOUNTING_POST FAILED: Debit credit SUM is not zero`

**Cause:** The ERP's CALCULATION step uses the **item master tax rate** (5% IGST for our
items) to compute the DR side of the journal entry. Our payload had `tax_rate: 0`,
`gst_type: null` — so the CR side (AP + GST) had no GST entry, while the ERP's DR
was 5% higher. The mismatch = the GST amount (e.g. ₹83,049.81 for QC 2251).

**Fix:** Include GST in the payload when `tax_rate > 0`:
- `tax_rate: 5.0`, `gst_type: "IGST"`, `txn_currency_igst_amount: <float>`
- `txn_currency_total_txn_amount = amount_detail + igst` (not just amount_detail)
- Header `txn_currency_total_amount = Σ total_txn` (includes GST)

The old code had `is_gst_set_off=False` suppressing GST even when `tax_rate > 0`.
Removed that gate — GST is now applied whenever `tax_rate > 0`.

### 8. `total_txn` formula was double-subtracting the discount
**Old formula:** `total_txn = amount_detail - discount + gst - labour`

**Problem:** `amount_detail` from the QC (`txn_currency_amount`) is **already post-discount**.
The QC records the net amount after cleaning/drying deductions AND the cash discount.
Subtracting `c_d_deduction` again shifted `total_txn` lower → DR/CR mismatch.

**Fix:** `total_txn = amount_detail + gst - labour`

`txn_currency_discount_amount_details` is still populated (for accounting reference) as the
monetary cash discount = `amount_detail × discount_rate / (100 - discount_rate)`.

### 9. `c_d_deduction` from QC is a **weight deduction**, not the monetary cash discount
`c_d_deduction: 1.0353` is the per-unit C&D (cleaning & drying) weight deduction in
the alternate UOM. It is NOT the total monetary cash discount for the line (which is
computed from `discount_rate × pre_discount_amount`). Using it as `discount_amount`
caused wrong `txn_currency_discount_amount_details` values.

### 10. Zero GST amounts must be `null`, not `"0.000"`
When IGST is used, `txn_currency_cgst_amount` and `txn_currency_sgst_amount` must be `null`.
Sending `"0.000"` for the unused split caused the validator to treat them as present
and attempt a zero-amount posting.

### 11. `uom_conversion` must be a **string**
The ERP serializer expects `"1.0"` not `1.0`. Sending a float caused a type error
in the DYNAMIC_TO_FLAT_MAPPING step.

### 12. `conversion_rate` must be a **string** `"1"`, not float `1.0`
Same serializer quirk — the field is defined as CharField in the ERP model.

---

## Ghost PBs (side-effect, not a code bug)

When `PURCHASE_BOOKING_SAVED` succeeds but `PURCHASE_ACCOUNTING_POST` fails:
- A DB row is written with the PB id (sequence consumed)
- Inventory reservation may be partially committed
- The QC is "soft-claimed" — subsequent attempts for the same QC may fail or corrupt inventory state

**Symptoms:** 500 errors or repeated accounting failures for the same QC even after fixing the payload.

**Workaround:** Always use a fresh QC (no prior PB attempts). The batch script does this
automatically since it generates new QCs via the chain.

---

## What Changed in Code

### `purchase_booking_data.py`
- `build_pb_line`: GST applied when `tax_rate > 0` (removed `is_gst_set_off` gate); all amounts as floats; `isChecked: True`; zero GST slots → `None`; `uom_conversion` → `str`; fixed `total_txn` formula
- `build_pb_payload`: `posting_status: ""`; `section_ref_id: "0"`; `tds_amount: None`; `round_off_*: None`; `conversion_rate: "1"`; `purchase_booking_ref_type: 144`; added `qc_summary: {}`, `omitted_fields: []`, `type_of_bags_ref_id: None`, `item_quality_parameter_ref_id: None`, `so_ref_id: None`; `agent_commision_amount: None`; header amounts as floats

### `purchase_chain.py` (`_pb_items_from_qc`)
- Compute monetary cash discount correctly (`amount_detail × rate / (100 - rate)`)
- Removed `c_d_deduction` as discount proxy
- Removed `is_gst_set_off` param (deprecated)
- `round_off_credit_amount / round_off_debit_amount` → `None` in header (was random values)

### `test_calculations.py`
- All assertions updated to reflect the new correct format (51 tests, all pass)

---

## Verified Working

| Test | QC | Item | GST | Result |
|---|---|---|---|---|
| Direct API (test_pb_gst.py) | 2251 | 8 | 5% IGST | ✅ 28/28 SSE steps |
| Via module (test_pb_via_module.py) | 2254 | 1 | 5% IGST | ✅ 28/28 SSE steps |
| Full web UI flow | multiple | — | — | ✅ Listed in ERP |
| Batch script (purchase_chain.py) | fresh | 8 | 5% IGST | ✅ Full chain |
