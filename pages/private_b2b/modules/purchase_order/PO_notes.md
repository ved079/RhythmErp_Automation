# Purchase Order Module — Playwright Test Suite Notes

## Overview

Playwright test suite for the PO (Purchase Order) ERP module.
PO is a standalone module — it does not depend on GP/GRN/QC and is not part of that chain.

The PO records what is being ordered from a supplier: items, quantities, rates, discount, and interest.
Rate is auto-fetched from the Commodity Base Rate master after item selection.

---

## File Structure

```
pages/private_b2b/modules/purchase_order/
    po_playwright_page.py               # PO page object
    PO_notes.md                         # this file
    test/playwright/
        conftest.py                     # class-scoped browser + function-scoped po_page fixture
        test_po_ui.py                   # test cases
```

---

## Formula

```
txn_amount      = rate × qty                          <- per row (Transaction Amount)
total_po_amount = row_sum × (1 - disc/100 + int/100) <- across all rows (Total PO Amount)
```

Where:
- `rate` is auto-fetched from Commodity Base Rate master after item selection (1500ms wait needed)
- `row_sum = sum(txn_amount_i for all rows)`
- `disc` = Discount % applied to the entire PO (reduces total)
- `int` = Interest % applied to the entire PO (increases total)
- If disc > int → total < row_sum
- If int > disc → total > row_sum
- If disc=0, int=0 → total == row_sum exactly

Tests verify this with abs tolerance 0.50 (rounding on large amounts).

---

## Fixture Structure (conftest.py)

PO conftest uses class-scoped browser like GP (not session-scoped like GRN/QC).
A fresh browser is launched per test class.

```
playwright_instance  (session-scoped)
    -> browser       (class-scoped)
        -> logged_in_page  (class-scoped)
            -> po_page     (function-scoped)
```

po_page fixture:
- Instantiates POPlaywrightPage
- Calls navigate_to_page() to land on PO listing
- Yields the page object
- Teardown calls close_popup() to clean up any open form

PO has no shared session fixtures. Every test that needs a PO calls create_record() directly.
This is the same pattern as GP — each test is fully self-contained.

---

## PO Page Object (po_playwright_page.py)

### Key Selectors

```python
# Header fields (filled once per PO)
SUPPLIER_NAME        = "xpath=//mat-form-field[.//mat-label[contains(.,'Supplier Name')]]//mat-select"
PO_ITEM_TYPE         = "xpath=//mat-form-field[.//mat-label[contains(.,'PO Item Type')]]//mat-select"
PO_TYPE              = "xpath=//mat-form-field[.//mat-label[contains(.,'PO Type')]]//mat-select"
TRANSACTION_CURRENCY = "xpath=//mat-form-field[.//mat-label[contains(.,'Transaction Currency')]]//mat-select"
LOCATION             = "xpath=//mat-form-field[.//mat-label[contains(.,'Location')]]//mat-select"
DEPARTMENT           = "xpath=//mat-form-field[.//mat-label[contains(.,'Department')]]//mat-select"
DIVISION             = "xpath=//mat-form-field[.//mat-label[contains(.,'Division')]]//mat-select"
TYPE_OF_SALE         = "xpath=//mat-form-field[.//mat-label[contains(.,'Type of Sale')]]//mat-select"
PACKAGING_FORWARDING = "xpath=//mat-form-field[.//mat-label[contains(.,'Packaging Forwarding')]]//mat-select"
CONVERSION_RATE      = "xpath=//mat-form-field[.//input[@placeholder='Conversion Rate']]//input"

# Per-row item grid fields (use .nth(row_index) or _fill_number_nth)
ITEM_NAME          = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Name')]]//mat-select"
QUANTITY           = "xpath=//mat-form-field[.//mat-label[contains(.,'Quantity')]]//input"
RATE               = "xpath=//mat-form-field[.//input[@placeholder='Rate']]//input"
EXPECTED_DELIVERY  = "xpath=//mat-form-field[.//mat-label[contains(.,'Expected Delivery Date')]]//input[@placeholder='DD/MM/YYYY']"
DISCOUNT           = "xpath=//mat-form-field[.//mat-label[contains(.,'Discount %')]]//input"
INTEREST           = "xpath=//mat-form-field[.//mat-label[contains(.,'Interest%')]]//input"
TRANSACTION_AMOUNT = "xpath=//mat-form-field[.//mat-label[contains(.,'Transaction Amount')]]//input"
TOTAL_AMOUNT       = "xpath=//mat-form-field[.//mat-label[contains(.,'Total Amount')]]//input"

# Table columns
REF_NO_COL          = "td.cdk-column-transaction_ref_no"
TOTAL_PO_AMOUNT_COL = "td.cdk-column-txn_currency_total_amount"
WORKFLOW_STATUS_COL = "td.cdk-column-workflow_status"
```

### fill_header()

Fills all header fields. Fixed values:
- PO Item Type = "Farm"
- Transaction Currency = "INR"
- Type of Sale = "B2B"
- Packaging Forwarding = "Nil"
- Conversion Rate = "1" (only filled if the field appears in the DOM — it's conditional on currency)

Everything else (Supplier, PO Type, Location, Department, Division) is random.

### create_record(item_configs=None, all_items=False)

Main method. Full flow: open form → fill header → add rows → submit.

- item_configs: list of (qty, disc_pct, int_pct) tuples. Default: [(10, 5, 2)]
- all_items: if True, ignores item_configs and creates one row per available item with (qty=10, disc=0, int=0)

**Key pattern — pre-create all rows upfront:**
All ADD_ROW_BTN clicks happen before any row is filled. This ensures every row's fields exist
in the DOM before _fill_number_nth references them by index. Filling one row at a time while
clicking ADD_ROW_BTN between fills is NOT done here (unlike GP).

Returns `(total_po_amount, [row_dicts])` where row_dicts contains per row:
`{item_name, rate, qty, disc_pct, int_pct, txn_amount, total_amount, live_row_sum}`

`live_row_sum` is the JS-read sum of all row Total Amounts at the moment of submit (added to every
row_dict so tests can compare against Total PO Amount even when disc/int are zero).

### _add_item_row(row_index, qty, disc_pct, int_pct, used_items)

1. Selects a random item (skipping already-used ones via exclude_texts)
2. Waits 1500ms for Rate to auto-fetch from Commodity Base Rate
3. Reads Rate via raw DOM JS (no visibility filter — PO form is always fresh per test)
4. Fills Quantity → triggers Transaction Amount calculation
5. Fills Discount % and Interest % → triggers Total Amount per-row update
6. Reads Transaction Amount and Total Amount back via raw DOM JS
7. Returns the row_dict

### _fill_number_nth(selector, row_index, value)

Uses native JS property setter + dispatchEvent to fill number inputs.
Uses raw DOM index (no offsetParent visibility filter) — acceptable because PO form is opened
fresh per test via open_add_form() and rows are pre-created from index 0.

If DOM pollution ever causes issues here, add the same offsetParent filter from GRN/_read_readonly_nth.

### edit_first_record_qty(new_qty)

Opens Edit on the first listing row, changes quantity, reads new Transaction Amount and Total PO Amount,
then clicks Update. After success alert dismissed, calls navigate_to_page() to return to listing.

Returns `(new_total_po_amount, new_txn_amount)`.

Note: After edit, the listing shows the updated Total PO Amount. Tests search by this amount to verify.

### close_popup()

Checks if .details-form is in DOM — the View form renders as a full-page details-form (not a modal popup).
If it is, calls navigate_to_page() to go back to listing.
Otherwise, clicks Cancel button.

### count_available_items()

Opens the Item Name dropdown on row 0, counts mat-options, then closes by clicking the cdk-overlay-backdrop.
Do NOT use Escape to close — Escape can dismiss the entire form in some Angular form configurations.

---

## Test Cases (test_po_ui.py)

| Class | Test | Markers | Description |
|-------|------|---------|-------------|
| TestPOSmoke | test_create_search_and_status | smoke | disc=2,int=5 → total > row_sum; verify in listing; status="Created" |
| TestPOValidation | test_form_submit_and_cancel | validation | Empty submit keeps form; Cancel returns to listing |
| TestPOListing | test_listing_and_search | smoke | Table has rows; bogus ref-no returns empty |
| TestPOFullWorkflow | test_full_workflow | workflow | disc=5,int=2 → total < row_sum; verify table; edit qty 10→15; verify recalc |
| TestPOFullWorkflow | test_multi_row_total_po_amount_matches_table | workflow | all_items, disc=0,int=0 → total == row_sum; listing matches |
| TestPOFullWorkflow | test_view_popup_read_only | workflow | View action opens read-only form; no Submit button |
| TestPORegression | test_qty_zero_shows_error | regression | qty=0 → mat-error + form stays open |
| TestPORegression | test_qty_negative_shows_error | regression | qty=-1 → mat-error + form stays open |
| TestPORegression | test_discount_over_100_shows_error | regression | disc=110 → mat-error + form stays open |
| TestPORegression | test_interest_negative_shows_error | regression | int=-5 → "Interest cannot be less than 0" mat-error |
| TestPODuplicateItem | test_same_item_twice_shows_error | validation, multi_row | Same item in 2 rows → "already added" mat-error |

Expected result: 11 tests across 6 classes.

### Formula test coverage

Smoke test: disc=2, int=5 → int > disc → total > row_sum (verifies increase direction)
FullWorkflow test: disc=5, int=2 → disc > int → total < row_sum (verifies decrease direction)
Multi-row test: disc=0, int=0 → total == row_sum exactly (verifies identity case)
All three together fully cover the disc/int formula across all sign cases.

---

## Bugs / Quirks

### 1. Rate field not populated immediately after item selection
Rate is auto-fetched from Commodity Base Rate master. There is no loading indicator.
_add_item_row waits 1500ms after item selection before reading the rate via JS.
If rate reads as 0.0, it means the fetch didn't complete in time — increase the wait or add a polling loop.

### 2. Total PO Amount form field is disabled
The form's Total PO Amount field (input[placeholder='Total PO Amount']) is a disabled/readonly field.
Standard Playwright .input_value() may return '' on disabled inputs depending on Angular rendering.
_read_form_total_po_amount() uses JS document.querySelector() to read the raw .value directly.
Fallback: if that also returns None, create_record() falls back to _read_all_row_totals() (JS sum of all TOTAL_AMOUNT inputs).

### 3. View form is full-page, not a modal popup
All other modules (GP, GRN, QC) open View in a modal popup. PO opens View as a full-page .details-form.
close_popup() checks for .details-form presence and calls navigate_to_page() instead of clicking Cancel.
verify_view_popup_read_only() waits for input[readonly] before asserting no Submit button.

### 4. Escape closes whole form on some dropdowns
count_available_items() closes the mat-select panel via .cdk-overlay-backdrop click, not Escape.
_select_random_mat_option_nth also uses backdrop click for the "no options" case.
Escape CAN dismiss the entire PO form in Angular Material form contexts — always use backdrop.

### 5. Conversion Rate field is conditional
CONVERSION_RATE field only appears in the DOM when the selected Transaction Currency is not the base.
fill_header() selects "INR" and then fills Conversion Rate with "1" only if the field count > 0.
Don't unconditionally call .fill() on this field — it will throw if the field isn't there.

### 6. _select_mat_by_text exact-match guard
"Farm" must not match "Non Farm". _select_mat_by_text() does an exact inner_text() comparison
in a loop rather than just filter(has_text=...).first. The has_text filter does substring match,
so "Farm" would match both options. The loop finds the exact-text match.

---

## Angular SPA DOM Pollution — Status for PO

PO uses raw DOM indices (no offsetParent filter) for _fill_number_nth and _add_item_row's _read_nth.

This is safe because:
- po_page fixture is function-scoped (fresh navigate_to_page() per test)
- Conftest is class-scoped browser (no cross-class state accumulation)
- open_add_form() opens a fresh form each test
- Rows are pre-created from index 0 upward in a clean DOM

If tests ever run within the same browser session with multiple form opens, and DOM pollution
appears (wrong values read), add the offsetParent filter from GRN/_read_readonly_nth pattern.

---

## Running the Suite

```bash
# Full suite
python -m pytest pages/private_b2b/modules/purchase_order/test/playwright/test_po_ui.py -v

# By marker
python -m pytest pages/private_b2b/modules/purchase_order/test/playwright/test_po_ui.py -m smoke -v
python -m pytest pages/private_b2b/modules/purchase_order/test/playwright/test_po_ui.py -m workflow -v
python -m pytest pages/private_b2b/modules/purchase_order/test/playwright/test_po_ui.py -m regression -v
python -m pytest pages/private_b2b/modules/purchase_order/test/playwright/test_po_ui.py -m validation -v

# Single test
python -m pytest "pages/private_b2b/modules/purchase_order/test/playwright/test_po_ui.py::TestPOFullWorkflow::test_full_workflow" -v
```

## Environment Variables Required

```
RHYTHMERP_LOGIN_URL   (default: https://rhythmerp.algorhythms.in)
RHYTHMERP_EMAIL
RHYTHMERP_PASSWORD
```
