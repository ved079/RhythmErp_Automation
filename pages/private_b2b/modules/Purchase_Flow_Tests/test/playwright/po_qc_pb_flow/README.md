# po_qc_pb_flow — Test Suite Reference

**File:** `test_po_qc_pb_flow.py`  
**Tenant:** Ganesh Agrotech Pvt Ltd. (`kedar@rhythmflows.com` / `Kedar@999999`)  
**ERP:** `https://rhythmerp.algorhythms.in`  
**Mark:** `@pytest.mark.po_qc_pb`

---

## Overview

Four independent test classes in one file. All share the same session-scoped `logged_in_page` (single browser tab).

| Class | What it tests | Steps |
|---|---|---|
| `TestPO_QC_PB_Single_Item_Flow` | E2E: 1-item PO → QC → PB → PO Closed | 4 |
| `TestPO_QC_PB_MultiRow` | E2E: 3-item PO → QC → PB → PO Closed | 4 |
| `TestPOValidations` / `TestQCValidations` / `TestPBValidations` | Form-level validation spot-checks | ~7 each |
| `TestPOQCPBValidationFlow` | **Combined** progressive validation + real record creation | 29 |

---

## Class 1 & 2 — E2E Flow Tests

### `TestPO_QC_PB_Single_Item_Flow`

Sequential 4-step flow. Each step `pytest.skip`s if the previous step didn't store its ref in `integration_state`.

| Step | Action | Stores |
|---|---|---|
| `test_step1_create_po` | Create PO, qty=100, 1 item (random supplier) | `po_ref_no`, `supplier_name`, `location`, `item_name`, `rate` |
| `test_step2_create_qc` | Select supplier + last PO → fill bags=1, `fill_qc_params_safe`, submit. Retries once on failure. | `qc_ref_no`, `qc_qty` |
| `test_step3_create_pb` | Select supplier + last QC → fill qty details, submit | `pb_ref_no` |
| `test_step4_verify_po_closed` | Assert PO status = Closed | — |

**Known fragility:** `fill_qc_params_safe` can produce a negative QC Rate if deduction % is too high relative to PO rate. The retry covers a transient submit failure but does not re-pick the item. If you see `QC Rate still negative after retries`, check CQP settings for that item.

### `TestPO_QC_PB_MultiRow`

Same 4-step structure but uses `MULTI_ROW_COUNT = 3` items. Items containing "tur" in the name are filtered out (they cause QC param issues). Uses `fill_qc_params_high` (fills all param inputs with 99) for the QC step. Retries `_fill_and_submit` up to 3 times total.

---

## Module Fixture — `po_for_validations`

Scope: `module`. Creates a single PO (qty=50) used by `TestQCValidations` and `TestPBValidations` so they can test supplier-specific flows without each test creating its own PO.

```python
@pytest.fixture(scope="module")
def po_for_validations(logged_in_page): ...
# yields: {"supplier_name", "ref_no", "po_qty", "item_name"}
```

---

## Classes 3–5 — Form Validation Spot-checks

### `TestPOValidations`
Uses `po_page` fixture. Helper `_open_with_one_item` opens form, fills header, selects first item.

| Test | What it checks |
|---|---|
| `test_empty_submit_keeps_form` | mat-errors appear; form stays open |
| `test_cancel_returns_to_listing` | Cancel → listing visible |
| `test_qty_zero_blocked` | qty=0 → mat-error |
| `test_negative_qty_blocked` | qty=-1 → mat-error |
| `test_discount_over_100_blocked` | discount=110 → mat-error |
| `test_negative_interest_blocked` | interest=-5 → "Interest cannot be less than 0" |
| `test_duplicate_item_blocked` | same item in 2 rows → "already added" mat-error |

### `TestQCValidations`
Uses `qc_page` fixture + `po_for_validations`.

| Test | What it checks |
|---|---|
| `test_empty_submit_keeps_form` | mat-errors appear |
| `test_cancel_returns_to_listing` | Cancel works |
| `test_no_supplier_submit_blocked` | no supplier → mat-errors |
| `test_supplier_no_po_submit_blocked` | supplier selected, no PO → mat-errors |
| `test_no_bags_submit_blocked` | supplier+PO but no bags → mat-errors |
| `test_qc_param_popup_empty_done_blocked` | Done in param popup with no Actual Value → error or popup stays open |

### `TestPBValidations`
Uses `pb_page` fixture + `po_for_validations`.

| Test | What it checks |
|---|---|
| `test_empty_submit_keeps_form` | mat-errors appear |
| `test_cancel_returns_to_listing` | Cancel works |
| `test_no_supplier_submit_blocked` | no supplier → mat-errors |
| `test_supplier_no_qc_submit_blocked` | supplier selected, no QC → mat-errors |
| `test_discount_over_100_blocked` | discount=101 → mat-error |
| `test_round_off_credit_over_1_blocked` | credit=2 → mat-error |
| `test_round_off_debit_over_1_blocked` | debit=2 → mat-error |
| `test_qty_zero_in_popup_blocked` | qty=0 in Qty Details popup → error or popup stays open |
| `test_ebw_over_qty_blocked` | Empty Bag Weight > accepted qty → "less than 0" error |
| `test_labour_over_gross_blocked` | Labour Charges > gross amount → amount error |

---

## Class 6 — `TestPOQCPBValidationFlow` (29 steps)

**The main combined class.** All 29 steps run in order on the same `logged_in_page`. `integration_state` (class-scoped dict) passes data between the three creation steps.

### Flow

```
PO validation (steps 01–14)
    └─ progressive fill: each step adds one field, submits, checks remaining errors
    └─ invalid-value tests: rate=0, qty=0, discount=150 (fresh form each, cancelled)

CREATE actual PO (step 15)
    └─ stores val_supplier, val_po_ref

QC validation (steps 16–20)
    └─ uses val_supplier for all supplier selects
    └─ step 18 selects "last PO" = the PO from step 15

CREATE actual QC (step 21)
    └─ uses val_supplier + last PO = step 15's PO
    └─ stores val_qc_ref

PB validation (steps 22–28)
    └─ uses val_supplier for all supplier selects
    └─ step 24 selects "last QC" = the QC from step 21

CREATE actual PB (step 29)
    └─ hard reload listing before create (clears stale form state)
    └─ uses val_supplier + last QC = step 21's QC
    └─ prints FLOW COMPLETE with all three ref nos
```

### Step Reference

#### PO validation steps (form stays open, progressive fill)

| Step | Field filled | Errors asserted to disappear |
|---|---|---|
| 01 | (none — empty submit) | All 19 errors in `_VAL_PO_EMPTY` |
| 02 | Supplier Name | Supplier Name gone; 12 remain |
| 03 | Item Category | Item Category gone; 11 remain |
| 04 | Conversion Rate = "1" | Conversion Rate gone; 10 remain |
| 05 | Location | Location gone; 9 remain |
| 06 | Department | Department gone; 8 remain |
| 07 | Division | Division gone; 7 remain |
| 08 | Type of Sale | Type of Sale gone; 6 remain |
| 09 | Packaging Forwarding | Packaging Forwarding gone; 5 remain |
| 10 | Item Name | UOM auto-fills; only Quantity + Total Amount remain |
| 11 | Quantity = 10 | No errors → form submits (success or `_val_assert_no_errors`) |

#### PO invalid-value tests (fresh form each via `_po_prefill_full`, cancel at end)

| Step | Setup | Expected errors |
|---|---|---|
| 12 | All valid, Rate = 0 | `_VAL_PO_RATE_ZERO`: Total PO Amount, Rate, Total Amount |
| 13 | All valid, Quantity = 0 | `_VAL_PO_QTY_ZERO`: Total PO Amount, Quantity, Total Amount |
| 14 | All valid, Discount = 150 | `_VAL_PO_DISCOUNT_INVALID`: Total PO Amount, Discount % |

#### QC validation steps

| Step | Action | Errors asserted |
|---|---|---|
| 16 | Empty submit | `_VAL_QC_EMPTY` (12 errors) |
| 17 | Select supplier (val_supplier) | `_VAL_QC_AFTER_SUPPLIER` (11 errors) |
| 18 | Select last PO | `_VAL_QC_AFTER_PO`: only Conversion Rate |
| 19 | Conversion Rate = "1" | No errors → form submits |
| 20 | Bags = 0 on fresh form (val_supplier) | `_VAL_QC_BAGS_INVALID`: "Enter a valid bag quantity." |

#### PB validation steps (each opens fresh form via `_pb_prefill_full`)

| Step | Setup | Expected errors |
|---|---|---|
| 22 | Empty submit | `_VAL_PB_EMPTY` (14 errors) |
| 23 | Supplier selected | `_VAL_PB_AFTER_SUPPLIER` (5 errors) |
| 24 | QC selected (val_supplier + last QC) | `_VAL_PB_AFTER_QC`: only Conversion Rate |
| 25 | Conversion Rate = "1" | No errors → form submits |
| 26 | Discount = 150 (`_val_fill_native`) | `_VAL_PB_DISCOUNT_INVALID`: Total Amount + "Cannot be greater than 100%" |
| 27 | Empty Bag Weight = -1 (`_val_fill_native`) | `_VAL_PB_BAG_WEIGHT_NEG`: "Empty Bag Weight cannot be negative." |
| 28 | Empty Bag Weight > accepted qty | `_VAL_PB_BAG_WEIGHT_GT_QTY`: Amount, Total Amount, Net Quantity, Transaction Amount |

---

## Helper Functions (module-level)

| Function | Purpose |
|---|---|
| `_val_assert_errors(page, expected_errors)` | XPath via `mat-label → ancestor::mat-form-field → mat-error`. Fails with list of MISSING errors. |
| `_val_assert_no_errors(page)` | Fails if any `mat-error` exists. |
| `_val_open_form(page, url)` | `goto(url)` → wait for listing → click `erp-add-btn` → wait for Supplier Name field. Retries once on timeout. |
| `_val_submit(page)` | Clicks Submit inside `.popup-footer`. |
| `_val_cancel(page)` | Clicks Cancel inside `.popup-footer`, falls back to Escape. |
| `_val_select_first(page, label)` | Opens mat-select for label → clicks first option. |
| `_val_select_last(page, label)` | Opens mat-select for label → clicks last option. |
| `_val_select_text(page, label, text)` | Opens mat-select → finds option by exact text. |
| `_val_fill(page, label, value)` | JS native setter + `input`/`change`/`blur` events. Works for most text inputs. |
| `_val_fill_native(page, label, value)` | Playwright `fill()` + JS `blur`/`change` (no Tab). Use for `type="number"` inputs where `_val_fill` doesn't trigger Angular validation. |
| `_po_prefill_full(page)` | Opens fresh PO form, selects Supplier/ItemCat/Location/Dept/Division/TypeOfSale/Packaging/ItemName, sets ConversionRate=1. |
| `_pb_prefill_full(page, supplier_name)` | Opens fresh PB form, selects specific supplier + last QC, sets ConversionRate=1. Waits 6s after QC select for auto-patch. |

---

## Known Gotchas & Fixes

### Rate field — Angular auto-fill overwrites typed value (step 12)

**Problem:** Selecting an Item Name triggers an API call that auto-fills Rate with the market rate. `_val_fill_native("Rate", "0")` sets the value, then the API response comes back and overwrites it.

**Fix in step 12:**
1. `_val_fill_native("Rate", "0")` — the blur triggers the API re-fetch
2. `wait_for_timeout(3000)` — wait for the API response to land (overwrites "0")
3. JS setter sets Rate back to "0" **without blur** (`blur` is omitted on purpose — it re-triggers the fetch)
4. Submit immediately — Angular validates on submit and sees rate=0

**Do NOT use Tab** after filling Rate: Tab triggers Angular's blur handler which fires the rate API call.

### mat-select needs CDP-style clicks (all `_val_select_*` helpers)

Angular `mat-select` doesn't respond to JS `.click()` on the native select element. All helpers use `page.locator(...).click(force=True)` (Playwright CDP click), then wait for `.mat-mdc-select-panel` to appear before clicking the option.

### `_val_fill` vs `_val_fill_native`

Use `_val_fill` for most text inputs. Use `_val_fill_native` when the field is `type="number"` and Angular's reactive form doesn't pick up the JS setter — specifically:
- `Discount Percentage` in PB (step 26)
- `Empty Bag Weight` in PB (steps 27, 28)
- `Quantity` and `Rate` in PO invalid-value tests (steps 12, 13)

### PB create (step 29) — hard reload before create

After all PB validation steps, the browser is left on the PB listing URL but Angular's SPA state may have stale form overlays. `navigate_to_page()` alone isn't enough. Step 29 does `goto(_PB_URL)` + `reload()` + waits for the listing table before calling `pb.create_record(...)`.

### QC "QC" label vs "QC Reference"

The PB form's QC dropdown mat-label is `"QC"` (placeholder: "Select qc"), NOT `"QC Reference"`. Use `_val_select_last(page, "QC")` and `_val_select_text(page, "QC", ...)`.

### Conversion Rate error text

The Conversion Rate mat-form-field shows both `"The conversion rate entered is invalid"` and `"This field is required."` in the DOM simultaneously, but only `"This field is required."` is reliably found by the `ancestor::mat-form-field` XPath. Always use `"This field is required."` in the expected errors list for Conversion Rate.

### Form stays open between progressive steps 01–11

Steps 01–10 do NOT cancel/reload. They keep adding fields to the same open form. Step 11 submits — on success Angular closes the form and navigates to the listing; on failure `_val_assert_no_errors` will catch it. Steps 12–14 each call `_po_prefill_full` which opens a brand new form via `goto`.

### `"Rate is required"` disappears after Item Name is selected

When Item Name is selected, the ERP auto-fills Rate via API. So in steps 13 and 14 (which use `_po_prefill_full`), Rate is not required and `"Rate is required"` must NOT be in the expected errors list.

---

## Running the Tests

```bash
# Full class (29 steps, ~6–7 min)
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/po_qc_pb_flow/test_po_qc_pb_flow.py::TestPOQCPBValidationFlow -v -s

# Single step
python -m pytest ...::TestPOQCPBValidationFlow::test_po_step12_rate_zero -v -s

# All po_qc_pb marked tests
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/po_qc_pb_flow/ -m po_qc_pb -v -s
```

All 29 steps passed cleanly as of 2026-07-18.
PO = PUR/2026-2027/000073 | QC = QC/2026-2027/000038 | PB = PURB/2026-2027/000026
