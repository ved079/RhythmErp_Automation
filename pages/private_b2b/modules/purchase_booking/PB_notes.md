# Purchase Booking Module — Notes

## Overview

Purchase Booking (PB) is the financial settlement step after QC.
Chain position: **GP → GRN → QC → PB**

PB records what is actually being paid to the supplier — it uses the QC-derived net rate
and a separate quantity (alternate_qty) that the operator enters, which may differ from
the QC's accepted quantity. There is no validation forcing PB qty == QC qty.

ERP URL: `/#/purchase/purchase-booking`
REST endpoint: `/procure_to_pay/purchase-booking/`
DB master table: `tbl_purchase_booking_mst`
DB detail table: `tbl_purchase_booking_details`
DB sub-detail table: `tbl_purchase_booking_sub_details`

---

## Formula (confirmed from live GET response id=1242, QC id=571)

### Per line item

```
alternate_net_qty             = alternate_qty - empty_bag_weight
txn_currency_amount_detail    = rate × alternate_net_qty - labour_charges
txn_currency_igst_amount      = txn_currency_amount_detail × igst_rate / 100
txn_currency_cgst_amount      = txn_currency_amount_detail × cgst_rate / 100
txn_currency_sgst_amount      = txn_currency_amount_detail × sgst_rate / 100
txn_currency_tax_amount       = igst_amt + cgst_amt + sgst_amt
txn_currency_total_txn_amount = txn_currency_amount_detail + txn_currency_tax_amount
```

### Master level

```
txn_currency_amount       = SUM(txn_currency_total_txn_amount)   <- same value as below
txn_currency_total_amount = SUM(txn_currency_total_txn_amount)
total_quantity            = SUM(alternate_net_qty)
```

Both master amount fields are identical — the ERP stores the same value in both.

### UI formula (confirmed via Playwright calc tests)

The UI exposes different field names but the maths is the same:

```
Transaction Amount (per row, UI)  = rate × net_qty          ← gross; never shows deductions
net_qty                           = qty - empty_bag_weight
per-row final                     = gross - (gross × disc_pct/100) - labour + round_debit - round_credit
Master Total Amount               = SUM(per-row finals)
```

Key observations:
- **Transaction Amount is always gross** — labour and discount do not appear there, only in Master Total.
- **Round Off is per-row** — separate Debit (+) and Credit (−) fields on each item row; max value 1 each.
- **EBW can be a float** (e.g. 3455.5) — net_qty becomes fractional (e.g. 0.5).
- **Transportation** is stored in `other_charges` dict and does **not** affect Total Amount.
- **1 QC → 1 PB constraint** — once a PB is created from a QC, that QC is hidden from the dropdown and cannot be reused.

---

## Rate Linkage from QC

The `rate` field in PB detail comes from QC's calculated net rate:

```
QC:  qc_deduction_rate = base_rate × deduction_percent / 100
QC:  net_rate          = base_rate - qc_deduction_rate       → this becomes PB rate
PB:  txn_amount        = net_rate × alternate_net_qty
```

Verified from real data:
```
QC  base_rate=3033, deduction_pct=12% → net_rate=2669.04
PB  rate=2669.04 (exact match)
QC  qty=13 → QC total = 13 × 2669.04 = 34697.52
PB  qty=10 → PB total = 10 × 2669.04 = 26690.40
Gap:  3 × 2669.04 = 8007.12 (unbilled in PB)
```

**PB quantity is set independently by the operator — there is no ERP validation enforcing PB qty == QC qty.**

---

## Payload Structure

### Master (tbl_purchase_booking_mst)

| Field | Type | Notes |
|-------|------|-------|
| transaction_date | str (ISO date) | today |
| transaction_ref_no | str | empty "" on create; auto-assigned by ERP |
| supplier_ref_id | int | FK to supplier |
| supplier_ref_type | str | "Farmer" / "Supplier" / "Customer" / "Operator" / "Agent" |
| qc_ref_id_id | int | FK to QC entry (Django double-_id convention) |
| grn_ref_id_id | int | FK to GRN entry |
| po_ref_id_id | int or null | FK to PO (optional) |
| supplier_payment_terms_ref_id | int or null | payment terms FK |
| base_currency | int | 8 = INR |
| txn_currency | int | 8 = INR |
| conversion_rate | str | "1" (sent as string) |
| txn_currency_amount | int | master total (SUM of lines) |
| txn_currency_total_amount | int | same as above |
| total_quantity | int | SUM of alternate_net_qty |
| is_tds_applicable | bool | False by default |
| section_ref_id | str | "0" by default |
| tds_percent_applicable | null | |
| tds_amount | int | 0 |
| parameter1 | int | Division |
| parameter2 | int | Department |
| parameter5 | int | Location |
| parameter6 | int | Type of Sale |
| round_off_credit_amount | int | 0 |
| round_off_debit_amount | int | 0 |
| remark | str | "" |
| posting_status | str | "" |
| gst_registration_type | null | |
| purchase_booking_details | list | line items (see below) |
| grn_details | list | [] on create |
| other_charges | dict | agent/transport charges |

### Line item (purchase_booking_details)

| Field | Type | Notes |
|-------|------|-------|
| item_ref_id | int | FK to item |
| hsn_sac_no | int | HSN/SAC code FK |
| no_of_bags | int | bag count |
| alternate_qty | int | quantity in alternate UOM |
| alternate_uom | int | alternate UOM FK |
| quantity | int | base UOM quantity |
| uom | int | base UOM FK |
| rate | int | net rate from QC |
| txn_currency_amount | int | = quantity × rate (simplified; backend computes full formula) |
| amount | int | same as txn_currency_amount |
| gst_percent | null | |
| igst / cgst / sgst | null | |
| is_gst_set_off | bool | False |
| tax_rate | null | |

### other_charges

```json
{
    "agent_ref_id": null,
    "is_rate_percentage": false,
    "agent_commision": null,
    "agent_commision_amount": 0,
    "transportation_amount": 0
}
```

---

## Supplier Type Constants (Role Type master — same across all tenants)

```python
SUPPLIER_TYPE_FARMER   = 1769  → "Farmer"
SUPPLIER_TYPE_SUPPLIER = 1771  → "Supplier"
SUPPLIER_TYPE_CUSTOMER = 1770  → "Customer"
SUPPLIER_TYPE_OPERATOR = 1814  → "Operator"
SUPPLIER_TYPE_AGENT    = 1855  → "Agent"
```

`supplier_ref_type` is sent as a string name, NOT an integer. The integer constants are for
resolving from the dropdown (which returns integer IDs), then must be converted to name string
before sending in the payload. `build_pb_payload()` handles this automatically.

---

## File Structure

```
pages/private_b2b/modules/purchase_booking/
    PB_notes.md                         # this file
    __init__.py
    api/
        endpoints.py                    # URL builders
        __init__.py
    data/
        purchase_booking_data.py        # payload builders + calc helpers
    scripts/
        batch_create.py                 # CLI batch creation script
    utils/
        api_purchase_booking_utils.py   # PBAPIUtils CRUD wrapper
    test/
        api/
            conftest.py                 # pb_api fixture (requires ERP_TOKEN)
            test_calculations.py        # pure unit tests (no network)
            test_live.py                # live ERP tests (require token)
            test_schema.py              # schema structure tests (require token)
        playwright/
            conftest.py                 # session-scoped GP→GRN→QC chain fixtures
            pb_playwright_page.py       # PBPlaywrightPage page object
            test_pb_ui.py               # full Playwright UI test suite (see below)
```

---

## API Layer

### PBAPIUtils (utils/api_purchase_booking_utils.py)

```python
pb_api.create_pb(payload)         # POST /procure_to_pay/purchase-booking/
pb_api.get_pb(entry_id)           # GET  /procure_to_pay/purchase-booking/{id}/
pb_api.list_pbs(page, page_size)  # GET  /procure_to_pay/purchase-booking/?page_number=...
pb_api.update_pb(entry_id, payload) # PUT /procure_to_pay/purchase-booking/{id}/
pb_api.get_schema()               # GET  /core/dynamic-screen/Purchase Booking/
pb_api.last_response()            # raw requests.Response from the last call
```

All methods return parsed JSON dict or None on failure.
`_last_status` holds the HTTP status code of the last call.

### FK field naming quirk

Django REST FK write fields use double `_id` suffix:
```python
"qc_ref_id_id":  571   # NOT "qc_ref_id"
"grn_ref_id_id": 859   # NOT "grn_ref_id"
"po_ref_id_id":  null  # NOT "po_ref_id"
```
GET responses return the computed/display form; POST payload must use the `_id_id` form.

---

## batch_create.py — How It Works

CLI script for seeding PB records in bulk.

```bash
python pages/private_b2b/modules/purchase_booking/scripts/batch_create.py \
    --token <jwt> --tenant 751 --count 3

# Dry run (print payloads, no creates)
python ... --dry-run

# Pin supplier
python ... --supplier 100 --count 5

# Farmer or Supplier type
python ... --supplier-type farmer   # default
python ... --supplier-type supplier
```

Resolution order:
1. Fetch suppliers from live ERP listing
2. Resolve Location name→ID map from PB parameter5 dropdown
3. Fetch Commodity Base Rate (CBR) per location → {location_id: {item_id: {rate, uom}}}
4. Resolve Division / Department / Type of Sale / Currency dropdowns
5. Optionally find QC entries per supplier (for qc_ref_id linkage)
6. Build one payload per count using random supplier + CBR rate

Rate source: CBR (same source the QC uses for base_rate). In a linked create, you'd pass
the QC's net_rate directly instead of CBR base_rate.

---

## Test Coverage

### test_calculations.py (no network)

| Class | Tests |
|-------|-------|
| TestLineAmount | qty×rate, zero cases, large values |
| TestMasterTotal | single/multi item sum, empty |
| TestBuildPbItem | defaults, explicit qty, line amount, required keys, no id/details, GST=None |
| TestPayloadStructure | all master keys, no id, FK double-_id, supplier_ref_type string, TDS defaults, other_charges keys, grn_details=[] |

### test_live.py (requires ERP_TOKEN)

| Class | Tests |
|-------|-------|
| TestLiveCreate | create returns id, has ref_no, GET roundtrip, multi-item, unique ref_nos |
| TestLiveCalculations | net_quantity from ebw, txn_amount, labour deduction, master total_quantity, master amount=sum of lines |
| TestLiveMasterAggregates | 5-line total qty, bag weight reduces total qty |
| TestLiveIntegrity | GET twice identical, all detail keys present in GET, listing includes created entry |

### test_schema.py (requires ERP_TOKEN)

Verifies schema reachable, screen name, master/detail/sub-detail table names, expected
master fields, purchase_booking_details is stepper+grid, has quantity_details sub-grid,
supplier_ref_type dropdown has Farmer+Supplier, location and supplier dropdowns non-empty.

---

## Bugs / Quirks

### 1. Schema field_keys differ from real API field names
The ERP schema endpoint returns field_keys like `qc_ref_id` but the actual POST payload
and GET response use `qc_ref_id_id` (double suffix). The data builder uses the real names,
not schema names. Schema tests verify structure, not field names.

### 2. supplier_ref_type is string in payload, integer in dropdown
Dropdown options return integer role type IDs (1769=Farmer etc). The POST payload expects
the string name ("Farmer"). `build_pb_payload()` auto-converts int → string via SUPPLIER_TYPE_NAMES.

### 3. txn_currency_amount and txn_currency_total_amount are the same
Both master fields hold the same sum. This is ERP design, not a bug. Always set both to
the same value when building payloads manually.

### 4. conversion_rate sent as string "1", not int/float
The ERP expects conversion_rate as a JSON string even when the value is 1. Sending as int
or float may cause a 400. `build_pb_payload()` defaults to "1".

### 5. PB qty does not have to match QC qty
There is no server-side validation that `alternate_qty` in PB equals the QC's `grn_qty`.
Operators can book less (partial booking) or theoretically more. Test data should account
for this — don't assume they're equal.

### 6. Rate flows from QC, not re-fetched from CBR
In a real create linked to a QC, the line rate should be the QC's `net_rate` (base_rate -
deduction). The batch_create.py script uses CBR base_rate because it creates standalone PBs
without a QC link. When building linked PBs, fetch the QC response and extract
`qc_details[i].rate` for each line.

---

## Playwright UI Test Suite

### Page Object — `pb_playwright_page.py`

Key selectors:
```python
EMPTY_BAG_WEIGHT   = "xpath=//mat-form-field[.//mat-label[contains(.,'Empty Bag Weight (KG)')]]//input"
LABOUR_CHARGES     = "xpath=//mat-form-field[.//mat-label[contains(.,'Labour Charges')]]//input"
DISC_PERCENTAGE    = "xpath=//mat-form-field[.//mat-label[contains(.,'Discount Percentage')]]//input"
ROUND_OFF_CREDIT   = "xpath=//mat-form-field[.//mat-label[normalize-space()='Round Off Credit Amount(-)']]//input"
ROUND_OFF_DEBIT    = "xpath=//mat-form-field[.//mat-label[normalize-space()='Round Off Debit Amount(+)']]//input"
TRANSPORTATION_AMOUNT = "xpath=//mat-form-field[.//mat-label[contains(.,'Transportation Amount')]]//input"
AGENT_COMMISSION_AMT  = "xpath=//mat-form-field[.//mat-label[contains(.,'Agent Commision Amount')]]//input"
```

`create_record` fill order per row: **EBW → Labour → Discount → Round Off → open popup → fill bags/qty → Done**
Transportation filled after all rows, before reading master total.

`_fill_number_nth(selector, i, value)` — uses `offsetParent` JS filter to skip hidden/stale Angular inputs.

### Fixtures (`conftest.py`)

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `session_qc_for_pb` | session | GP(1 item) → GRN → CQP → QC; returns `(supplier_name, grn_qtys)` |
| `session_qc_for_pb_multi` | session | GP(all items) → GRN(multi) → CQP → QC(multi); returns `(supplier_name, grn_qtys)` |
| `pb_page` | function | navigates to PB listing; yields `(page_obj, (supplier_name, grn_qtys))` using single-item QC |
| `pb_page_multi` | function | same but uses multi-item QC |
| `pb_bare_page` | function | navigates to PB listing only — no QC chain; for validation tests that don't submit |

### Test Classes (`test_pb_ui.py`)

#### `TestPBSmoke` (`-m smoke`)
- `test_create_search_and_verify` — single row, vanilla qty, asserts `ref_no.startswith("PURB/")` and `txn_amount ≈ rate × net_qty`

#### `TestPBMultiRow` (`-m multirow`)
- `test_multi_row_formula` — all items, one row per item, asserts per-row formula and `total = SUM(txn_amounts)`

#### `TestPBCalc` (`-m calc`)
- `test_all_calculations` — all calc scenarios in ONE PB (1 QC → 1 PB constraint):

| Row | Scenario |
|-----|----------|
| 0 | Float EBW: `ebw = qty - 0.5` → `net_qty = 0.5` (extreme fractional) |
| 1 | Discount 10% + Labour 500 combined |
| 2 | EBW + Discount + Labour (all three deductions) |
| 3 | Discount % only |
| 4 | Round Off: debit=1.0, credit=0.5 |
| 5 | Partial booking: `qty = grn_qty // 2` |

Transportation = 100 (other charges, does not affect Total Amount).
Master total assertion: `SUM(gross_i - disc_i - labour_i + debit_i - credit_i)` ± 2.0

#### `TestPBValidation` (`-m validation`)

| Test | Fixture | Scenario | Asserted error |
|------|---------|----------|----------------|
| `test_submit_empty_form` | `pb_bare_page` | Submit with no fields filled | 14 mat-errors appear |
| `test_ebw_greater_than_qty` | `pb_page` | EBW = qty + 5 → net_qty negative | `"Amount cannot be less than 0"` |
| `test_discount_above_100` | `pb_page` | Discount = 101% | `"Cannot be greater than 100%"` |
| `test_labour_exceeds_gross` | `pb_page` | Labour = 999999 | `"Amount cannot be less than 0"` on Total Amount |

Validation tests open the form and assert client-side Angular mat-errors **without submitting** — QC stays unconsumed.

---

## Running the Tests

```bash
# Unit tests only (no token needed)
python -m pytest pages/private_b2b/modules/purchase_booking/test/api/test_calculations.py -v

# All tests including live (token required)
ERP_TOKEN=<jwt> ERP_TENANT_ID=751 \
python -m pytest pages/private_b2b/modules/purchase_booking/test/api/ -v

# By marker (API)
python -m pytest pages/private_b2b/modules/purchase_booking/test/api/ -m calculation -v
python -m pytest pages/private_b2b/modules/purchase_booking/test/api/ -m live -v
python -m pytest pages/private_b2b/modules/purchase_booking/test/api/ -m schema -v

# Playwright UI tests (browser opens; credentials via RHYTHMERP_EMAIL / RHYTHMERP_PASSWORD)
python -m pytest pages/private_b2b/modules/purchase_booking/test/playwright/test_pb_ui.py -v -s
python -m pytest pages/private_b2b/modules/purchase_booking/test/playwright/test_pb_ui.py -m smoke -v -s
python -m pytest pages/private_b2b/modules/purchase_booking/test/playwright/test_pb_ui.py -m calc -v -s
python -m pytest pages/private_b2b/modules/purchase_booking/test/playwright/test_pb_ui.py -m validation -v -s
```

## Environment Variables Required

```
ERP_TOKEN       JWT from browser session (for live + schema tests)
ERP_TENANT_ID   Tenant ID (default: 751)
```
