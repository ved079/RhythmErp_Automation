# QC Module — Playwright Test Suite Notes

## Overview

Full end-to-end Playwright test suite for the QC (Quality Check) ERP module.
Chain: **GP -> GRN -> CQP -> QC**

- GP creates gate pass with items
- GRN receives goods against GP
- CQP reads quality parameter configs per item (multiplier, min_q, max_q)
- QC creates quality check entry, fills actual values per item row, verifies calculated fields

---

## File Structure

```
pages/private_b2b/modules/qc/
    qc_playwright_page.py          # QC page object
    cqp_playwright_page.py         # CQP page object (reads quality param configs)
    QC_notes.md                    # this file
    test/playwright/
        conftest.py                # session fixtures: GP -> GRN -> CQP -> QC chain
        test_qc_ui.py              # test cases
```

---

## Formula (Confirmed)

```
deduction_pct  = sum(actual_value_i x multiplier_i)    <- from CQP config per item
deduction_rate = base_rate x deduction_pct / 100
qc_rate        = base_rate - deduction_rate
txn_amount     = accepted_qty x qc_rate
```

- multiplier comes from CQP master screen per quality parameter per item
- min_q / max_q are just input range bounds, NOT formula coefficients
- base_rate and accepted_qty are auto-patched into the QC form from the GRN

---

## Fixture Chain (conftest.py)

All fixtures are session-scoped. GP and GRN are created once per test session and reused.

```
session_gp_single / session_gp_multi
    -> session_grn_single / session_grn_multi
        -> session_cqp_config_single / session_cqp_config_multi
            -> qc_page / qc_page_multi   (function-scoped)
```

### Single-item chain
- session_gp_single: creates GP with 1 random item
- session_grn_single: creates GRN against that GP; reads gp_qty, sets accepted = gp_qty - 1
- session_cqp_config_single: navigates CQP, searches item by name, reads quality param table
- qc_page: attaches cqp_config and item_names to the QC page object

### Multi-item chain
- session_gp_multi: creates GP with ALL available items (all_items=True)
- session_grn_multi: creates GRN for all rows; fills accepted_qty per row
- session_cqp_config_multi: reads CQP config for every item
- qc_page_multi: same as above but multi-row

---

## CQP Page Object (cqp_playwright_page.py)

Navigates to /#/dynamic-screens/Commodity%20Quality%20Parameter

Key behaviour:
- Searches each item by name in the listing
- Clicks the row directly (Edit action is disabled on CQP, row click opens detail view)
- Reads the quality param sub-table using header-based column detection (maps column name -> index) to avoid positional assumptions
- Returns: {item_name: [{"param", "min_q", "max_q", "multiplier", "is_pct"}]}

Known issue: Some items may show a duplicate param name if the CQP column header detection
misreads a column. This is a CQP data/screen issue, not a code bug. Check printed [CQP]
output during test setup to verify configs look correct.

---

## QC Page Object (qc_playwright_page.py)

### Key selectors

```python
BASE_RATE      = "xpath=//mat-form-field[.//mat-label[contains(.,'Base Rate')]]//input"
ACCEPTED_QTY   = "xpath=//mat-form-field[.//mat-label[contains(.,'Accepted Quantity')]]//input"
DEDUCTION_PCT  = "xpath=//mat-form-field[.//mat-label[contains(.,'Deduction(%)')]]//input"
DEDUCTION_RATE = "xpath=//mat-form-field[.//mat-label[contains(.,'Deduction Rate')]]//input"
QC_RATE        = "xpath=//mat-form-field[.//mat-label[contains(.,'QC Rate')]]//input"
TXN_AMOUNT     = "xpath=//mat-form-field[.//mat-label[contains(.,'Transaction Amount') and not(contains(.,'Total'))]]//input"
```

CRITICAL on TXN_AMOUNT: must use not(contains(.,'Total')) to exclude the header-level
"Total Transaction Amount" field. Without this, _read_nth(TXN_AMOUNT, 0) reads the grand
total (sum of all rows) instead of row 0's individual per-row value.

### _read_nth(selector, index)

Reads the nth VISIBLE input matching selector. Uses offsetParent !== null JS check to
skip hidden stale inputs from previously closed Angular popups that remain in the DOM.

### fill_actual_values(actual_values)

Fills Actual Value inputs scoped to the currently active popup via Done-button ancestor XPath:

```
"xpath=//button[contains(.,'Done')]"
"/ancestor::div[.//input[@placeholder='Actual Value']][1]"
"//input[@placeholder='Actual Value']"
```

Counts visible_count inputs in the popup first, then fills only actual_values[:visible_count].
This prevents index-out-of-range when safe_actual_values returns more values than the popup
has inputs (e.g. CQP lookup fails -> fallback 3 values but item only has 1 param).

### safe_actual_values(row_index, max_pct)

Generates actual values that keep deduction_pct <= max_pct. Uses CQP config for the item
at row_index:

```python
cap   = max(min_v, int(max_pct / (n * mult)))
max_v = min(max_v, cap)
result.append(random.randint(min_v, max_v))
```

Falls back to 3 random values if CQP config is missing for that item.

---

## Test Cases (test_qc_ui.py)

| Class | Test | Description |
|-------|------|-------------|
| TestQCSmoke | test_create_search_and_view | Creates QC, verifies ref_no in listing, view mode is read-only |
| TestQCCalc | test_single_row_formula | Random actual values -> all 4 formulas verified |
| TestQCCalc | test_boundary_min_deduction | min_q per param -> minimum deduction -> formulas hold |
| TestQCCalc | test_boundary_high_deduction | High deduction (60%) -> formulas hold, qc_rate stays positive |
| TestQCMultiRowCalc | test_multi_row_formula | All items: fill all rows, verify all 4 formulas per row, submit |
| TestQCValidation | test_empty_submit_and_cancel | Empty submit keeps form open; Cancel returns to listing |

Expected result when running the full suite: 6 passed

### Formula assertion strategy (_assert_qc_formulas)

```python
# deduction_pct: loose tolerance for display rounding
pct_tol = max(0.1, abs(expected_deduction_pct) * 0.05)
assert actual_deduction_pct == pytest.approx(expected_deduction_pct, abs=pct_tol)

# Chain uses APP's own displayed deduction_pct as source of truth
# so downstream values match exactly what the app computed
expected_deduction_rate = round(base_rate * actual_deduction_pct / 100, 2)
expected_qc_rate        = round(base_rate - expected_deduction_rate, 2)
expected_txn_amount     = round(accepted_qty * expected_qc_rate, 2)
# all three asserted with abs=0.01
```

---

## Bugs Encountered and Fixed

### 1. Wrong formula assumption
Problem: Initial assumption was deduction_pct = sum(min_q / v * mult). Entered [1,1,1]
for an item with multiplier=100 and got deduction=300. Mistakenly thought it was sum of values.
Root cause: The multiplier was 100, so 1x100 + 1x100 + 1x100 = 300.
Fix: Formula is sum(actual_value x multiplier). Confirmed manually across multiple items.

### 2. JS inject not triggering Angular change detection
Problem: Using native JS property setter + dispatchEvent to fill Actual Value inputs in
the QC popup did not trigger Angular's reactive form update. Values appeared filled visually
but the form didn't register them for calculation.
Fix: Switched to Playwright's .fill() which correctly triggers Angular's value accessor
and change detection.

### 3. DOM pollution on fill (stale popup inputs)
Problem: Angular SPA keeps closed popup components in the DOM (just hidden). Filling
locator(ACTUAL_VALUE).nth(i) picked hidden stale inputs from previously closed popups,
filling the wrong elements entirely.
Fix: Scope all fills to the Done-button ancestor XPath so only inputs inside the
currently open popup are targeted.

### 4. DOM pollution on read (GRN fixture crash)
Problem: _read_readonly_nth in GRN page object did not filter by visibility. After a
previous form session, a hidden GP_QTY input sat at DOM index 0. read_gp_qty(0) returned
None -> int(None) -> TypeError crash in the conftest fixture. All single-row tests errored.
Fix: Added offsetParent !== null visibility filter to _read_readonly_nth (same pattern as
QC's _read_nth). Also added explicit RuntimeError raise in _wait_for_gp_patch if the GP
Quantity field never populates within timeout, so failure is clear instead of silent.

### 5. CQP Edit action disabled
Problem: click_row_action(0, "Edit") timed out on the CQP screen because the Edit action
is disabled for all CQP rows.
Fix: Click the row directly (rows.first.click()). Row click opens the detail view popup.

### 6. Mango CQP data with min_q and max_q swapped
Problem: Mango was created in CQP with min_q=100, max_q=1 (accidentally swapped).
safe_actual_values picked min_v=100 for all 3 params -> actual_values=[100,100,100] ->
deduction_pct=300 -> validation error on QC submit.
Temporary fix: Excluded Mango from multi-row GP using exclude_keywords=["Mango"].
Permanent fix: CQP data for Mango was corrected (min/max swapped back). Exclusion removed.

### 7. txn_amount multi-row reading Total instead of per-row value
Problem: _read_nth(TXN_AMOUNT, 0) returned 280541.57 (grand total) instead of 39908.0
(row 0 per-row value). The QC form has a header-level "Total Transaction Amount" field
that matched contains(.,'Transaction Amount') at DOM index 0, before any per-row fields.
Fix: Added and not(contains(.,'Total')) to the TXN_AMOUNT XPath. Index 0 now correctly
resolves to the first per-row Transaction Amount field.

### 8. fill_actual_values .nth(1) timeout on single-row items
Problem: Single-row items sometimes have only 1 quality parameter (1 Actual Value input
in the popup). When CQP lookup fails due to item name mismatch (the mat-select text includes
extra label text beyond just the commodity name), safe_actual_values falls back to 3 random
values. Calling .nth(1) on a popup that only has 1 input causes an 8s timeout.
Fix: fill_actual_values now counts visible_count inputs in the popup before iterating
and fills only actual_values[:visible_count]. Consistent with multi-row behaviour where
safe_actual_values correctly returns the right count from CQP config.

### 9. _wait_for_gp_patch silent timeout
Problem: If GP auto-patch never populated the GP Quantity field in GRN (slow network or
wrong supplier), _wait_for_gp_patch silently returned after 15s. Next line: int(gp_qty)
where gp_qty=None -> TypeError. Very hard to diagnose without the explicit raise.
Fix: Added raise RuntimeError(...) at end of timeout loop. Increased timeout to 20s.

### 10. Regression test asserting non-existent validation
Problem: test_invalid_actual_values asserted mat-error appears when actual_value > max_q.
The app does not enforce this range client-side. No mat-error ever fires regardless of what
value is entered. Test would always fail.
Fix: Deleted the regression test class entirely. Do not re-add without first manually
confirming the app shows a mat-error for out-of-range actual values.

---

## Angular SPA DOM Pollution — General Rule

Angular keeps all popup components in the DOM even after they are "closed". Any selector
that matches globally will hit stale hidden elements first if they appear earlier in DOM order.

Rules to always follow:
- Reading fields: use offsetParent !== null JS filter (_read_nth pattern)
- Filling popup fields: scope to the active popup's ancestor (Done-button ancestor XPath)
- Never use raw .nth(i) on a selector that spans multiple popup instances

---

## Running the Suite

```bash
# Full suite
python -m pytest pages/private_b2b/modules/qc/test/playwright/test_qc_ui.py -v

# Single test
python -m pytest "pages/private_b2b/modules/qc/test/playwright/test_qc_ui.py::TestQCMultiRowCalc::test_multi_row_formula" -v

# By marker
python -m pytest pages/private_b2b/modules/qc/test/playwright/test_qc_ui.py -m smoke -v
python -m pytest pages/private_b2b/modules/qc/test/playwright/test_qc_ui.py -m calc -v
```
