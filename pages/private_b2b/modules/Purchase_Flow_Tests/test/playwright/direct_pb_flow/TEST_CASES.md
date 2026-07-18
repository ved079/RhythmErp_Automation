# Purchase Flow Tests — Master Reference

**Tenant:** Eco Green Pvt Ltd (direct_pb_flow) / Rolex Traders (po_pb_flow)
**Last updated:** 2026-07-17

---

## Directory Structure

```
Purchase_Flow_Tests/test/playwright/
    direct_pb_flow/
        conftest.py                  # fixtures: browser, login, pb_page
        test_direct_pb_flow.py       # 28 tests across 6 classes
        direct_pb_tests_tracker.xlsx # run/pass tracking spreadsheet
        reports/                     # auto-generated Excel reports per test run
    po_pb_flow/
        conftest.py                  # fixtures: browser, login, po_page, pb_page
        test_po_pb_flow.py           # 12 tests across 6 classes
        PO_PB_FLOW_NOTES.md          # detailed notes for po_pb_flow suite
```

Page objects (do not modify from test side):
```
pages/private_b2b/modules/purchase_booking/direct_pb_playwright_page.py  # DirectPBPlaywrightPage
pages/private_b2b/modules/purchase_booking/pb_playwright_page.py          # PBPlaywrightPage
pages/private_b2b/modules/purchase_order/po_playwright_page.py            # POPlaywrightPage
```

---

## Run Commands

```bash
# direct_pb_flow — individual groups
python -m pytest "pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/direct_pb_flow/test_direct_pb_flow.py::TestRowAndPostSaveSuite" -v -s
python -m pytest "pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/direct_pb_flow/test_direct_pb_flow.py::TestDirectPBCalculations" -v -s
python -m pytest "pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/direct_pb_flow/test_direct_pb_flow.py::TestMultiRowCalculations" -v -s
python -m pytest "pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/direct_pb_flow/test_direct_pb_flow.py::TestValidationSuite" -v -s
python -m pytest "pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/direct_pb_flow/test_direct_pb_flow.py::TestRowMutations" -v -s
python -m pytest "pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/direct_pb_flow/test_direct_pb_flow.py::TestEdgeSuite" -v -s
python -m pytest "pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/direct_pb_flow/test_direct_pb_flow.py::TestDecimalPrecision" -v -s

# direct_pb_flow — full suite
python -m pytest "pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/direct_pb_flow/test_direct_pb_flow.py" -v

# po_pb_flow — full suite
python -m pytest "pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/po_pb_flow/test_po_pb_flow.py" -v
```

---

# direct_pb_flow — `test_direct_pb_flow.py`

**Tenant:** Eco Green Pvt Ltd
**Flow:** PB created directly (no PO / GP / GRN / QC upstream)
**28 tests, 6 classes**
**Last full run: 2026-07-17 — 27 PASSED, 1 XFAIL**

| Group | Tests | Result |
|-------|-------|--------|
| TestRowAndPostSaveSuite | 1 | ✅ PASSED |
| TestDirectPBCalculations | 11 | ✅ 11/11 PASSED |
| TestMultiRowCalculations | 8 | ✅ 7 PASSED, ⚡ 1 XPASS (m1h — ERP now enforces GST validation) |
| TestValidationSuite | 1 | ✅ PASSED (19/19 scenarios) |
| TestRowMutations | 5 | ✅ 4 PASSED, ⚠️ 1 XFAIL (m3c — ERP blocks save with GST off) |
| TestEdgeSuite | 1 | ✅ PASSED (21/21 scenarios) |
| TestDecimalPrecision | 1 | ✅ PASSED |

### Confirmed formula (all calc tests derive from this)

```
net_qty      = qty - empty_bag_weight
Amount       = rate × net_qty              (rate auto-fetched from item master)
Disc Amount  = Amount × disc_pct / 100
Tax (IGST)   = Amount × tax_rate / 100     (applied on gross Amount, not after disc)
Total Amount = Amount - Disc Amount - Labour + Tax
CGST = SGST  = Tax / 2                     (when GST type = CGST+SGST)
Header Total = sum of all row Total Amount fields
```

> **Critical:** Rate is auto-fetched — `_fill_number_nth(RATE)` does NOT stick.
> Always read Amount back from ERP after item selection; never hardcode expected values.

---

## Group 1 — TestRowAndPostSaveSuite

**Class:** `TestRowAndPostSaveSuite`
**Tests:** 1 (`test_rps1_row_behaviour_and_post_save`)
**Scenarios inside:** 4 (R_TC1 – R_TC4)
**Last run: 2026-07-17 ✅ PASSED**

### What it tests
Row-level behaviour and post-save restrictions — things that happen around the item grid and after a record is committed.

### Scenarios

| ID | Scenario | Assertion |
|----|----------|-----------|
| R_TC1 | Add same item in row 0 and row 1 | Row 1 shows inline error `"This item is already added in the order"` |
| R_TC2 | Delete a row that has a filled item | Remaining empty row shows ₹0, no stale values carried over |
| R_TC3 | Replace item in row with a different item (same qty) | Transaction amount recalculates fresh for the new item's rate |
| R_TC4 | Save a PB then check action menu | Edit option must be absent or disabled — saved PBs are immutable |

### Output
Exports Excel report to `reports/rps1_<timestamp>.xlsx`

### Known quirks
- ERP sometimes throws JS `"Cannot set properties of null (setting 'status')"` on save even though the record was created. The test handles this: dismisses the alert and navigates to the list to verify ref_no was generated.
- R_TC3 may show same Amount for two items if they share the same master rate — assertion is `Amount > 0`, not that amounts differ.

### If this test breaks

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| R_TC1 fails | ERP changed duplicate-item error message wording | Update expected text in assertion |
| R_TC2 fails — stale value remains | Angular not clearing bindings on delete | Check `DELETE_ROW_BTN` selector |
| R_TC3 fails — Amount = 0 | Item replacement not triggering rate re-fetch | Check `_pick_nudge_item` + `_select_mat_by_text_nth` sequence |
| R_TC4 fails — Edit shown | ERP enabled Edit for saved PBs | Check `EDIT_MENU_ITEM` XPath |

---

## Group 2 — TestDirectPBCalculations

**Class:** `TestDirectPBCalculations`
**Tests:** 11
**TOL:** ±0.02
**Last run: 2026-07-17 ✅ 11/11 PASSED**

### Fixed inputs used across all tests
```
ITEM     = ITEMS[0]   (first item in known list)
QTY      = 100
EBW      = 20         → net_qty = 80
DISC_PCT = 10%
LABOUR   = 200
TAX_RATE = 5%
```

### Tests

| Test | ID | What it checks |
|------|----|----------------|
| `test_cs1_all_single_row_calc_checks` | CS1 | All 9 calc assertions in one form, saves and verifies View total matches form total |
| `test_c_tc1_amount_auto_computed_from_rate_and_net_qty` | C_TC1 | Amount = rate × net_qty > 0 |
| `test_c_tc2_discount_amount_equals_amount_times_disc_pct` | C_TC2 | Disc Amount = Amount × 10% |
| `test_c_tc3_total_no_tax_equals_amount_minus_discount` | C_TC3 | Total (no tax, no labour) = Amount − Disc |
| `test_c_tc4_total_deducts_labour_charges` | C_TC4 | Total = Amount − Disc − Labour |
| `test_c_tc5_net_qty_reduces_by_empty_bag_weight` | C_TC5 | net_qty = qty(1000) − EBW(200) = 800 |
| `test_c_tc6_net_qty_equals_full_qty_when_no_ebw` | C_TC6 | net_qty = qty(500) when EBW=0 |
| `test_c_tc7_fractional_ebw_gives_fractional_net_qty` | C_TC7 | net_qty = 1000 − 999.5 = 0.5 |
| `test_c_tc8_igst_amount_equals_amount_times_tax_rate` | C_TC8 | IGST = Amount × 5%; CGST = SGST = 0 |
| `test_c_tc9_cgst_and_sgst_each_half_of_igst_equivalent` | C_TC9 | CGST = SGST = Amount × 2.5%; IGST = 0 |
| `test_c_tc10_header_total_equals_sum_of_two_rows` | C_TC10 | 2-row form: Header Total = row0 + row1 |

### CS1 sub-assertions (run inside `test_cs1_all_single_row_calc_checks`)

| Sub-ID | Assert |
|--------|--------|
| C_TC1 | Amount > 0 |
| C_TC2 | net_qty = qty − EBW = 80 |
| C_TC3 | Disc Amount = Amount × 10% |
| C_TC4 | IGST = Amount × 5% |
| C_TC5 | CGST = 0 (mode is IGST) |
| C_TC6 | SGST = 0 (mode is IGST) |
| C_TC7 | Tax Total = IGST Amount |
| C_TC8 | Total = Amount − Disc − Labour + IGST |
| C_TC9 | View Total (after save) = Form Total |

CS1 exports `reports/cs1_<timestamp>.xlsx`.

### If this test breaks

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Amount = 0 | Item rate not fetched | Check `_pick_nudge_item` + wait timing after item select |
| Disc/Tax mismatch | ERP changed formula | Re-read Amount from DOM and recompute expected dynamically |
| View total ≠ form total | ERP rounding differently in View | Widen TOL or investigate rounding layer |
| GST type not switching | `select_gst_type()` selector stale | Update selector in page object |

---

## Group 3 — TestMultiRowCalculations

**Class:** `TestMultiRowCalculations`
**Tests:** 8
**TOL:** ±0.05
**Last run: 2026-07-17 ✅ 7/8 PASSED, ⚡ 1 XPASS (m1h)**

> **XPASS note — `test_m1h_gst_validation_future_ready`:** Was marked `xfail` (expected to fail) but passed. ERP now enforces GST rate + type validation. Remove the `xfail` marker from this test when convenient.

### Tests

| Test | ID | Result | What it checks |
|------|----|----------------|
| `test_m1_five_rows_varied_inputs_header_equals_sum` | M1 | ✅ | 5 random rows (random item/qty/disc/labour/EBW, GST off) → Header = sum of rows; saves and checks ref_no |
| `test_m1b_header_disc_equals_sum_of_row_discs` | M1b | ✅ | 4 rows, ≥3 with disc > 0 → ≥3 non-zero Discount Amount fields exist |
| `test_m1c_ebw_per_row_net_qty_affects_totals` | M1c | ✅ | 3 rows with random EBW → each row Total > 0, Header = sum |
| `test_m1d_all_20_items_header_equals_sum` | M1d | ✅ | All 20 available items in 20 rows → Header = sum |
| `test_m1f_many_rows_all_fields_random` | M1f | ✅ | Many rows, all fields fully random (qty/disc/labour/EBW/GST) → Header = sum |
| `test_m1e_gst_mixed_all_rows_header_sum` | M1e | ✅ | Rows with mixed GST types (IGST / CGST+SGST / off) → Header Total = sum |
| `test_m1g_gst_split_verification` | M1g | ✅ | Per-row: CGST = SGST = Amount × (tax_rate/2); IGST = 0 when CGST+SGST mode |
| `test_m1h_gst_validation_future_ready` | M1h | ⚡ XPASS | Future-ready GST assertions — ERP now enforces it (was xfail, now passes) |

### Random inputs (seeded)
All random choices use `_rng = random.Random(42)` by default.
Override seed with `TEST_SEED=<n>` env var for reproducibility.

```python
DISC_CHOICES   = [0, 5, 10, 15, 20, 25]
LABOUR_CHOICES = [0, 100, 250, 500, 1000]
```

### If this test breaks

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Header ≠ sum of rows | ERP added an adjustment/rounding row to DOM | Check if a new row appears in `TOTAL_AMOUNT` locator count |
| Row Total = 0 | Rate fetch failed for that row | Check `_add_rows` nudge+select sequence for rows beyond row 0 |
| m1d fails on 20 items | Item count in `ITEMS` list changed | Verify `ITEMS` list in `direct_pb_playwright_page.py` |
| GST contamination (m1g/m1h) | GST type switch affecting other rows | Increase wait between row GST selections |

---

## Group 4 — TestValidationSuite

**Class:** `TestValidationSuite`
**Tests:** 1 (`test_vs1_all_validations_one_form`)
**Scenarios inside:** 19 (V_TC1 – V_TC19)
**Last run: 2026-07-17 ✅ PASSED (19/19 scenarios)**

### What it tests
All field-level and business-rule validations in a single form session. Collects pass/fail per scenario and asserts at the end — so all failures are visible at once, not just the first.

### Scenarios

| ID | Action | Expected |
|----|--------|----------|
| V_TC1 | Search `"LK suppliers"` in supplier dropdown | Supplier not found (absent) |
| V_TC2 | Submit empty form (no supplier) | ≥1 mat-error containing `"required"` |
| V_TC3 | Submit with supplier only (no location/dept/type) | ≥1 mat-error containing `"required"` |
| V_TC4 | Submit with no item rows filled | ≥1 mat-error containing `"Amount"` |
| V_TC5 | Type `"abc"` into Rate field | Field stays empty — non-numeric rejected |
| V_TC6 | Type `"@#$"` into Rate field | Field stays empty — special chars rejected |
| V_TC7 | qty=blank, rate=100 → submit | mat-error containing `"quantity"` |
| V_TC8 | qty=0 → submit | mat-error containing `"quantity"` |
| V_TC9 | qty=-5 → submit | mat-error containing `"quantity"` |
| V_TC10 | qty=10, rate=blank → submit | mat-error containing `"required"` |
| V_TC11 | rate=0 → submit | mat-error containing `"Amount"` |
| V_TC12 | rate=-100 → submit | mat-error `"Rate cannot be less than 0"` |
| V_TC13 | EBW=-1 → submit | mat-error containing `"bag"` |
| V_TC14 | labour=-500 → submit | mat-error `"Labour Charges cannot be negative"` |
| V_TC15 | disc=-10% → submit | mat-error containing `"discount"` |
| V_TC16 | disc=110% → submit | mat-error `"Cannot be less than 0%"` |
| V_TC17 | disc=0 after disc was entered | Transaction amount unchanged |
| V_TC18 | qty=rate=99999999999 → submit | ≥1 mat-error, form stays open |
| V_TC19 | Search `"Bottle"` (inactive item) | Item absent — xfail (ERP filtering not yet active) |

### Output
Exports `reports/vs1_<timestamp>.xlsx`

### If this test breaks

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| V_TC2/V_TC3 error count drops | ERP made previously required fields optional | Update expected keyword |
| V_TC5/V_TC6 field accepts non-numeric | Angular input type changed | Check `_type_into_rate` mechanism |
| V_TC16 keyword not found | Error text changed | Print `errors` list and update keyword |
| V_TC19 no longer xfail | ERP implemented inactive item filtering | Remove xfail, assert item is absent normally |

---

## Group 5 — TestRowMutations

**Class:** `TestRowMutations`
**Tests:** 5
**TOL:** ±0.02
**Last run: 2026-07-17 ✅ 4/5 PASSED, ⚠️ 1 XFAIL (m3c)**

### What it tests
Dynamic state changes after rows are added — delete rows, change qty/disc on existing rows, add new rows mid-session — then verify the header re-derives correctly. Most tests save and cross-check totals in View.

### Tests

| Test | ID | Sequence | Assertion |
|------|----|----------|-----------|
| `test_m2_add_n_delete_random_header_updates` | M2 | ✅ | Add N rows → read header → delete random subset → read header again | Header after delete = sum of surviving rows |
| `test_m2b_delete_all_but_one_header_equals_single_row` | M2b | ✅ | Add multiple rows → delete all but one | Header = remaining single row total |
| `test_m3_mutate_disc_delete_add_recheck` | M3 | ✅ | Add rows with disc → change disc on one row → delete one row → add a new row | Header = sum after every mutation step |
| `test_m3b_change_qty_on_existing_rows_header_recalcs` | M3b | ✅ | Add rows → change qty on existing rows | Header updates to reflect new qty-derived totals |
| `test_m3c_change_disc_on_existing_rows_header_recalcs` | M3c | ⚠️ XFAIL | Add rows (GST off) → change disc% on existing rows | Calc assertions pass; save blocked by ERP validation |

> **XFAIL note — `test_m3c`:** ERP requires GST to be ON to save a PB. `set_gst_off=True` triggers "Validation Failed" popup on submit, blocking the save. The disc/header calc assertions all pass — only the final save step fails. Fix: confirmed 2026-07-17 — previously `_add_rows(set_gst_off=True)` also called `select_tax_rate()` + `select_gst_type()` after enabling GST off (those fields don't render when GST is off, causing a 30s timeout). Removed those calls. Save block is an ERP business rule; marked `xfail(strict=False)`. If ERP ever allows saving with GST off, remove the marker.

### Cross-check mechanism (`_cross_check_view`)
After saving, opens View for the saved record and waits up to **90 seconds** for `Total Amount[0]` to populate before asserting.
If it stays 0 after 90s — assertion fails with a clear timeout message.

### If this test breaks

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Header ≠ sum after delete | Angular `*ngFor` not recalculating on delete | Increase wait after `DELETE_ROW_BTN` click |
| View total = 0 after 90s | ERP View form very slow | Increase timeout in `_cross_check_view` |
| Qty change not reflected in Total | `_fill_number_nth` not triggering Angular `change` | Add Tab/blur after fill in page object |
| Disc change not reflected | Same as above | Check `dispatchEvent` in `_fill_number_nth` |

---

## Group 6 — TestEdgeSuite

**Class:** `TestEdgeSuite`
**Tests:** 1 (`test_es1_all_edge_cases`)
**Scenarios inside:** 21 (E_TC1 – E_TC21)
**Seed:** 42 (fixed — all items/qtys reproducible)
**Last run: 2026-07-17 ✅ PASSED (21/21 scenarios)**

### What it tests
Boundary and non-obvious calculation scenarios. All run in one test to share form setup overhead.

### Scenarios

| ID | Setup | Assertion |
|----|-------|-----------|
| E_TC1 | EBW = Qty (e.g. 1359=1359) | net_qty = 0 → Total = 0 |
| E_TC2 | EBW > Qty (1604 > 1568), disc=5%, labour=100 | net_qty < 0 → Total ≤ 0 |
| E_TC3 | disc=100%, labour=1000 | Total = −1000 (only labour remains) |
| E_TC4 | disc=50% | Total after disc = exactly half of undiscounted total |
| E_TC5 | GST type IGST → switch to CGST+SGST | IGST clears to 0; CGST and SGST populate |
| E_TC6 | GST type CGST+SGST → switch to IGST | CGST/SGST clear to 0; IGST populates |
| E_TC7 | Increase qty ×3 after disc=20% | Disc amount and Total both grow proportionally |
| E_TC8 | Set qty = 0 after Amount already calculated | Total drops to 0 |
| E_TC9 | No disc, no tax, labour=1000 | Total = Amount − 1000 exactly |
| E_TC10 | Fill disc+labour BEFORE selecting item | After item selected, recalc is correct |
| E_TC11 | Fill EBW BEFORE selecting item | After item selected, net_qty = qty − EBW |
| E_TC12 | Select item_a, disc=10%, then change to item_b | disc% retained; disc_amount recalculated for item_b's Amount |
| E_TC13 | Clear qty after GST calculated | IGST and Total recalc to 0 |
| E_TC14 | Delete row 1 after GST on both rows | Header reflects only remaining row |
| E_TC15 | Delete row after EBW entered | Header = surviving row total |
| E_TC16 | Re-add same item after deleting it | Fresh Amount > 0 (no stale zero cached) |
| E_TC17 | Change item after qty/rate filled | Amount > 0 (HSN/rate refreshes for new item) |
| E_TC18 | Enter qty BEFORE selecting item | After item selected, Amount computes correctly |
| E_TC19 | Attempt to clear item name from mat-select | xfail — mat-select has no clear gesture; Amount stays |
| E_TC20 | Change rate after disc=5% | Disc amount refreshes for new Amount |
| E_TC21 | disc=10%, then switch GST IGST→CGST+SGST | IGST clears; CGST=SGST=half of IGST equivalent |

### Output
Exports `reports/es1_<timestamp>.xlsx`

### If this test breaks

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| E_TC1/E_TC2 Total not 0/negative | ERP flooring net_qty to 0 | Update assertion to match new ERP behaviour |
| E_TC5/E_TC6 GST switch not clearing | `select_gst_type()` needs wait after switching | Add `wait_for_timeout` after GST type selection |
| E_TC10/E_TC11 recalc wrong | Angular not firing `selectionChange` when other fields have values | Add extra wait after item selection |
| E_TC19 no longer xfail | ERP added a clear button to mat-select | Remove xfail, assert Amount clears |

---

## Group 7 — TestDecimalPrecision

**Class:** `TestDecimalPrecision`
**Tests:** 1 (`test_dp1_5dp_qty_rejected_4dp_accepted_total_2dp`)
**Last run: 2026-07-17 ✅ PASSED**

### What it tests
Decimal place enforcement rules:
- **Quantity:** max 4 decimal places — 5dp shows inline error
- **Rate:** up to 3 decimal places accepted
- **Total Amount:** always displayed rounded to 2 decimal places

### Sequence
1. Open form, select random item
2. Enter 5dp qty → Tab → assert error `"Quantity can have a maximum of 4 decimal places."`
3. Clear → enter 4dp qty → assert no error
4. Set rate to 3dp value
5. Save → open View → assert View total = Form total and total is ≤ 2dp

### If this test breaks

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| 5dp error not shown | ERP changed max decimal places or removed inline validator | Check mat-error text and update `QTY_ERROR_TEXT` |
| 4dp qty rejected | ERP tightened rule (e.g. max 2dp now) | Update test inputs and `QTY_ERROR_TEXT` |
| Total not 2dp | ERP showing more decimal places | Update TOL and assertion |
| View total ≠ Form total | Rounding applied at save differs from display | Use a fixed rate×qty with a known 2dp result |

---

---

# po_pb_flow — `test_po_pb_flow.py`

**Tenant:** Rolex Traders
**Flow:** PO → PB direct (no GP / GRN / QC)
**12 tests, 6 classes**
**Full run ~23 minutes**

> See `po_pb_flow/PO_PB_FLOW_NOTES.md` for complete details.

## Groups Summary

| Class | Tests | What it covers |
|-------|-------|----------------|
| `TestPO_PB_DirectFlow` | 1 | Single-item PO (disc=5%, int=2%) → PB qty/rate/txn match |
| `TestPO_PB_MultiRow` | 1 | 2-item PO per-row disc/int → PB matches every row |
| `TestPO_PB_CustomRate` | 1 | PO rate overridden to 90% of auto-fetch → PB carries custom rate |
| `TestPO_PB_NoGST` | 1 | GST off → txn = qty×rate exactly, no tax in PB |
| `TestPOValidations` | 3 | PO form: empty submit, field limits, duplicate item |
| `TestPBValidations` | 5 | PB form: empty submit, no PO, header limits, qty popup, transportation |

## Key rules

**Shared browser tab:** Both `po_page` and `pb_page` share one tab. Fixture listed last in test signature navigates last.
Always put `pb_page` before `po_page` — so execution starts on PO listing.
Always call `pb_page.navigate_to_page()` before `create_record_from_po()`.

**Auto-fetched PO fields:** `PO_TYPE` and `TRANSACTION_CURRENCY` are auto-fetched after supplier selection.
They use `_try_select_random_mat_option` / `_try_select_mat_by_text` which silently skip if the dropdown panel does not appear.

---

## Common Failures Across All Suites

| Error | Cause | Fix |
|-------|-------|-----|
| `wait_for_selector(".mat-mdc-select-panel") timeout` | Field is auto-fetched/disabled | Use `_try_select_*` variant that catches the timeout |
| `Amount = 0` after item selection | Rate not fetched yet | Add `wait_for_timeout(1000)` after item select |
| `mat-error count = 0` after submit | Stale hidden errors in Angular SPA DOM | Use `visible_errors()` which filters by `offsetParent !== null` |
| `No item rows auto-patched after PO selection` | Wrong page active when `open_add_form()` clicked | Call `navigate_to_page()` before `create_record_from_po()` |
| `Header Total ≠ sum of rows` | Angular did not re-fire aggregation after mutation | Increase wait after row add/delete/change |
| `View total = 0 after 90s` | ERP View form slow | Increase `_cross_check_view` timeout |
| `"Cannot set properties of null (setting 'status')"` swal | Known ERP backend JS bug on save | Test handles it: dismiss + navigate + verify ref_no was created |
| Fixture teardown `close_popup()` hangs | Browser closed mid-test (Ctrl+C) | Safe to ignore — not a test failure |
