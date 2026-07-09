# GRN Module — Playwright Test Suite Notes

## Overview

Playwright test suite for the GRN (Goods Receipt Note) ERP module.
Chain: **GP -> GRN**

- GP (Gate Pass) is created first with one or more items
- GRN receives goods against that GP
- GRN form auto-patches GP Quantity per row from the linked GP
- User fills Accepted Quantity; app auto-calculates Rejected Quantity

---

## File Structure

```
pages/private_b2b/modules/grn/
    grn_playwright_page.py          # GRN page object
    GRN_notes.md                    # this file
    test/playwright/
        conftest.py                 # session fixtures: GP -> GRN chain
        test_grn_ui.py              # test cases
```

---

## Formula

```
rejected_qty = gp_qty - accepted_qty
```

This is auto-calculated by the app as soon as accepted_qty is filled.
If accepted_qty > gp_qty, rejected_qty goes negative and a mat-error appears immediately.

---

## Fixture Chain (conftest.py)

```
session_gp / session_gp_multi   (session-scoped)
    -> grn_page / grn_page_multi  (function-scoped)
```

- session_gp: creates GP with 1 random item; returns (supplier_name, gp_ref_no)
- session_gp_multi: creates GP with ALL available items (all_items=True)
- grn_page: navigates to GRN listing; yields (GRNPlaywrightPage, (supplier_name, gp_ref_no))
- grn_page_multi: same but for multi-row GP

GP fixtures are session-scoped so the same GP is reused across all tests in a session.
GRN page fixtures are function-scoped so each test gets a clean navigate_to_page() start.
The teardown calls close_popup() to clean up any open form.

---

## GRN Page Object (grn_playwright_page.py)

### Key selectors

```python
SUPPLIER_NAME = "xpath=//mat-form-field[.//mat-label[contains(.,'Supplier Name')]]//mat-select"
GATE_PASS_NO  = "xpath=//mat-form-field[.//mat-label[contains(.,'Gate Pass No.')]]//mat-select"
ACCEPTED_QTY  = "xpath=//mat-form-field[.//mat-label[contains(.,'Accepted Quantity')]]//input"
REJECTED_QTY  = "xpath=//mat-form-field[.//mat-label[contains(.,'Rejected Quantity')]]//input"
GP_QTY        = "xpath=//mat-form-field[.//mat-label[contains(.,'Gate Pass Quantity')]]//input"
```

### _fill_number_nth(selector, row_index, value)

Uses JS native property setter + dispatchEvent to fill number inputs. This works correctly
for GRN Accepted Quantity because Angular's rejected_qty calculation is triggered by the
input/change events. Uses raw DOM index (not visibility-filtered) — acceptable here because
the GRN form renders fresh on each open_add_form() call.

### _read_readonly_nth(selector, row_index)

Reads readonly inputs (GP Quantity, Rejected Quantity) that are auto-patched by the app.
Uses offsetParent !== null visibility filter to skip hidden stale inputs from previously
closed form sessions that remain in the Angular DOM.

CRITICAL: This visibility filter was added after a bug where the hidden GP_QTY input from
a previous form sat at DOM index 0, causing read_gp_qty(0) to return None. See bug #1 below.

### fill_form(supplier_name, accepted_qty, row_index=0)

1. Selects supplier by exact text match
2. Waits 5s for GP dropdown to load
3. Selects the last available Gate Pass (most recent)
4. If GP dropdown shows empty ("No results found"), wakes up the dropdown by selecting
   a random supplier then re-selecting the correct one
5. Calls _wait_for_gp_patch() to confirm GP Quantity field is populated
6. Fills Accepted Quantity with the given value

### select_supplier_and_gp(supplier_name, expected_rows=1)

Used by multi-row GRN. Selects supplier + GP and waits for rows to auto-patch.
If row count is less than expected_rows after the wait, calls _retry_on_empty_gp()
which hard-reloads the page and reopens the form, then retries once.
Returns the actual row count patched.

### _wait_for_gp_patch(timeout_ms=20000, poll_ms=500)

Polls GP_QTY field index 0 every 500ms until it has a non-empty value.
Raises RuntimeError if it times out — do not silently ignore this or the next
int(gp_qty) call will crash with TypeError.

### count_row_inputs()

Returns how many Accepted Quantity inputs are currently in the DOM.
Used by select_supplier_and_gp to verify all rows auto-patched.
Note: does NOT use visibility filter — counts all DOM instances.

---

## Test Cases (test_grn_ui.py)

| Class | Test | Description |
|-------|------|-------------|
| TestGRNSmoke | test_create_search_and_view | Create GRN, verify ref_no in listing, view is read-only |
| TestGRNCalc | test_rejected_qty_formula | rejected = gp_qty - accepted for random accepted |
| TestGRNCalc | test_boundary_accepted_equals_gp_qty | accepted = gp_qty -> rejected must be exactly 0 |
| TestGRNCalc | test_decimal_accepted_qty | accepted with 4 decimal places is valid; rejected = gp_qty - accepted |
| TestGRNMultiRowCalc | test_multi_row_rejected_qty_formula | All items: assert rejected per row, submit, verify listing |
| TestGRNMultiRowCalc | test_multi_row_mixed_valid_invalid | Even rows invalid (accepted > gp_qty), odd rows valid; submit blocked |
| TestGRNValidation | test_empty_submit_and_cancel | Empty submit keeps form open; Cancel returns to listing |
| TestGRNRegression | test_invalid_accepted_qty | accepted > gp_qty, zero, negative, blank all show mat-error |

Expected result when running the full suite: 8 passed

---

## Bugs Encountered and Fixed

### 1. DOM pollution — _read_readonly_nth returning None
Problem: _read_readonly_nth used raw snapshotItem(idx) with no visibility check.
After any previous form session, a hidden GP_QTY input remained at DOM index 0.
read_gp_qty(0) returned None instead of the current form's value.
In the QC conftest, this caused: int(gp_qty) where gp_qty=None -> TypeError crash.
All single-row QC tests errored at setup with:
    TypeError: int() argument must be a string... not 'NoneType'
Fix: Added offsetParent !== null loop to filter visible elements only, identical pattern
to QC's _read_nth. Now reads the first VISIBLE GP_QTY input.

### 2. _wait_for_gp_patch silent timeout
Problem: If GP Quantity never populated (slow server or wrong supplier match),
_wait_for_gp_patch returned silently after 15s. The caller then did int(None) and crashed
with a confusing TypeError rather than a clear GRN-level error.
Fix: Added raise RuntimeError("GRN: GP Quantity field did not populate within timeout...")
at the end of the polling loop. Also increased timeout from 15s to 20s for slow networks.

### 3. GP dropdown shows empty ("No results found") on first open
Problem: The Gate Pass dropdown sometimes shows "No results found" even when valid GPs
exist. This is a timing/lazy-load issue in the Angular dropdown.
Fix: fill_form detects dd-empty-state, then wakes up the dropdown by selecting a random
supplier first, then re-selecting the correct supplier, then retrying GP selection.
select_supplier_and_gp uses _retry_on_empty_gp which hard-reloads the page if row count
is less than expected after the first attempt.

### 4. Multi-row rows not auto-patching after GP selection
Problem: For multi-row GRN, after selecting supplier + GP, sometimes only 1 row appears
instead of all item rows (the GP had multiple items but GRN form only showed 1 row).
This is a race condition — rows patch in asynchronously.
Fix: select_supplier_and_gp checks row_count against expected_rows and retries via
_retry_on_empty_gp (page reload + reopen form) if rows are missing. The 5s wait after
GP selection covers normal patch delay.

---

## Angular SPA DOM Pollution — General Rule

Same rule as QC module. Angular keeps closed form components in the DOM.

For readonly fields (GP_QTY, REJECTED_QTY): use _read_readonly_nth which filters
by offsetParent !== null to skip hidden stale instances.

For fillable fields (ACCEPTED_QTY): _fill_number_nth uses raw DOM index without
visibility filtering. This is acceptable because:
- GRN form is opened fresh each time via open_add_form()
- Angular renders new row inputs at the END of the DOM (after any stale hidden ones)
- Row indices passed in are 0-based relative to the current form's rows

If this ever causes issues, add the same offsetParent filter used in _read_readonly_nth.

---

## Running the Suite

```bash
# Full suite
python -m pytest pages/private_b2b/modules/grn/test/playwright/test_grn_ui.py -v

# By marker
python -m pytest pages/private_b2b/modules/grn/test/playwright/test_grn_ui.py -m smoke -v
python -m pytest pages/private_b2b/modules/grn/test/playwright/test_grn_ui.py -m workflow -v
python -m pytest pages/private_b2b/modules/grn/test/playwright/test_grn_ui.py -m regression -v
```
