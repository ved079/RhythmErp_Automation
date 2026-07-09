# Gate Pass Module — Playwright Test Suite Notes

## Overview

Playwright test suite for the GP (Gate Pass) ERP module.
GP is the entry point of the entire purchase chain: GP -> GRN -> CQP -> QC.
Every GRN, and every QC entry, depends on a GP existing first.

---

## File Structure

```
pages/private_b2b/modules/gate_pass/
    gp_playwright_page.py           # GP page object
    GP_notes.md                     # this file
    test/playwright/
        conftest.py                 # class-scoped browser + function-scoped gp_page fixture
        test_gp_ui.py               # test cases
```

---

## What GP Does

A Gate Pass records the arrival of goods at the facility. Key fields:

Header fields (filled once per GP):
- Supplier Name (mat-select, random)
- Item Type (mat-select, fixed to "Farm")
- Delivery Terms (mat-select, fixed to "Spot")
- IN Time (datetime picker via owl-dt)
- Location, Department, Division, Type of Sale (mat-selects, all random)
- Distance (text, hardcoded "1")
- Vehicle Number (text, hardcoded "MH14KK2354")
- Driver Name (text, hardcoded "TestDriver")
- Driver Number (number field, hardcoded 9999988888)

Item grid (one row per item):
- Item Name (mat-select, random, unique per row)
- NO. of Bags (number, random 1-10)
- Quantity (number, random 1-100)

On submit, the app creates the GP and shows a SweetAlert2 confirmation or validation error.
If validation error: downloads an Excel file with the error details.

---

## Fixture Structure (conftest.py)

GP conftest uses class-scoped browser and browser_context (unlike GRN/QC which use session-scoped).
This means a fresh browser is launched per test class. Tradeoff: isolation vs speed.

```
playwright_instance  (session-scoped)
    -> browser       (class-scoped)
        -> browser_context  (class-scoped)
            -> logged_in_page  (class-scoped)
                -> gp_page     (function-scoped)
```

gp_page fixture:
- Instantiates GPPlaywrightPage
- Calls navigate_to_page() to land on GP listing
- Yields the page object
- Teardown calls close_popup() to clean up any open form

Note: GP tests do NOT use a shared session GP fixture. Each test that needs a GP calls
create_record() directly. This is different from GRN/QC where one GP is created per session
and reused. GP tests are more self-contained.

---

## GP Page Object (gp_playwright_page.py)

### Key selectors

```python
SUPPLIER_NAME  = "xpath=//mat-form-field[.//mat-label[contains(.,'Supplier Name')]]//mat-select"
ITEM_TYPE      = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Type')]]//mat-select"
ITEM_NAME      = "xpath=//mat-form-field[.//mat-label[contains(.,'Item Name')]]//mat-select"
NO_OF_BAGS     = "xpath=//mat-form-field[.//mat-label[contains(.,'NO. of Bags')]]//input"
QUANTITY       = "xpath=//mat-form-field[.//mat-label[contains(.,'Quantity')]]//input"
ADD_ROW_BTN    = "button.add-row-btn"
```

### create_record(item_configs=None, all_items=False, exclude_keywords=None)

Main method. Full flow: open form -> fill header -> add rows -> submit.

- item_configs: list of (bags, qty) tuples. Defaults to 1 random row.
- all_items: if True, counts available items in the dropdown and creates that many rows.
- exclude_keywords: list of keyword strings to exclude from item selection (contains-match).
  Used when a specific item has bad master data and must be skipped.
  Example: exclude_keywords=["Mango"] skips any option whose text contains "Mango".

Returns (ref_no, [row_dicts]) where row_dicts is a list of
{"item_name": str, "bags": int, "qty": int} per row.

Multi-row flow:
1. Count available items via count_available_items()
2. Build item_configs list of that length
3. Click ADD_ROW_BTN (total_rows - 1) times to get the right number of rows
4. Fill each row with _add_item_row(), tracking used_items to avoid duplicates
5. If a row gets no item (all excluded), break early

### _add_item_row(row_index, bags, qty, used_items, exclude_keywords)

- Calls _select_random_mat_option_nth to pick an item not already in used_items
  and not matching any exclude_keywords
- Fills NO_OF_BAGS and QUANTITY via _fill_number_nth
- Returns {"item_name", "bags", "qty"}

### _select_random_mat_option_nth(selector, row_index, exclude_texts, exclude_keywords)

Clicks the mat-select at row_index, waits for panel, filters options:
- exclude_texts: exact match exclusion (used for already-selected items)
- exclude_keywords: contains match exclusion (used for bad-data items like Mango)

If no valid options remain after filtering, closes the panel and returns empty string.

### fill_header()

Fills all header fields. Item Type is always "Farm", Delivery Terms always "Spot".
Everything else is random. Driver number is hardcoded 9999988888 (passes phone validation).

### fill_in_time(hour=10, minute=0)

The IN Time field uses owl-datetime-picker. Cannot be filled with standard .fill().
Uses JS to set the timer input values directly and then clicks the "Set" button.

### handle_success_alert(downloads_dir=None)

Waits for SweetAlert2 popup after submit:
- If title contains "Validation" or "Failed": clicks confirm to trigger Excel download,
  saves it to test_downloads/gate_pass/, then raises RuntimeError so the test fails clearly.
- Otherwise: clicks confirm via JS evaluate (more reliable than Playwright click for swal2),
  waits for container to hide, waits for listing table.

The Excel download contains row-level validation errors from the backend — check it when
GP creation fails unexpectedly. Saved path is printed to stdout.

### count_available_items()

Opens the first Item Name dropdown, counts options, closes panel.
Used by create_record(all_items=True) to know how many rows to add.

---

## Test Cases (test_gp_ui.py)

| Class | Test | Description |
|-------|------|-------------|
| TestGPSmoke | test_create_and_search | Create single-item GP; verify ref_no in listing |
| TestGPValidation | test_form_submit_and_cancel | Empty submit keeps form open; Cancel returns to listing |
| TestGPListing | test_listing_and_search | Table has rows; bogus ref-no search returns empty |
| TestGPMultiRow | test_multi_row_create | Create GP with all available items; verify row count >= 2 |
| TestGPView | test_view_popup_read_only | View action opens read-only form with no Submit button |
| TestGPRegression | test_zero_quantity_shows_error | qty=0 shows mat-error |
| TestGPRegression | test_negative_quantity_shows_error | qty=-1 shows mat-error |
| TestGPRegression | test_zero_bags_shows_error | bags=0 shows mat-error |
| TestGPRegression | test_blank_qty_and_bags_shows_error | Blank qty/bags shows required mat-error |

Expected result: 9 passed

Note: Regression tests use _open_filled_form() helper which opens the form and fills
header + selects an item, leaving qty/bags blank for the test to fill with invalid values.

---

## How GP Feeds Downstream Modules

When create_record() returns, the caller gets:
- ref_no: the GP reference number (e.g. GP/2026-2027/000261)
- row_dicts: list of {"item_name", "bags", "qty"} per row

The item_names list extracted from row_dicts is passed through to:
- GRN conftest: to know which supplier created the GP (read from listing first-row column)
- CQP conftest: to search and read quality param config for each item
- QC page object: attached as page_obj.item_names for safe_actual_values() lookup

IMPORTANT: The item_name in row_dicts is the FULL inner_text() of the mat-option,
which may include extra label text beyond just the commodity name (e.g. "Mango Matte Grey Puny Square"
instead of just "Mango"). This means CQP search by this full text may fail to find the item
if CQP only indexes by commodity name. When this happens, cqp_config[item_name] = [] and
safe_actual_values falls back to 3 random values. See QC_notes.md bug #8.

---

## Bugs Encountered and Fixed

### 1. ADD_ROW_BTN click blocked by overlay backdrop
Problem: When creating multi-row GP, clicking ADD_ROW_BTN timed out with:
    <div class="cdk-overlay-backdrop cdk-overlay-transparent-backdrop"> intercepts pointer events
This happened when a mat-select panel from the previous row's item selection was still
animating closed. The transparent backdrop was still covering the button.
Fix: Wait for .mat-mdc-select-panel to be hidden after each item selection before returning
from _select_random_mat_option_nth. The existing try/except wait handles this.

### 2. Mango excluded from multi-row GP (temporary)
Problem: Mango's CQP entry had min_q=100, max_q=1 (accidentally swapped). When QC tests
ran with Mango in the multi-row GP, safe_actual_values() generated [100,100,100] -> 300%
deduction -> QC submit validation error.
Fix: Added exclude_keywords parameter to create_record(), _add_item_row(), and
_select_random_mat_option_nth(). The QC multi-row fixture used:
    gp.create_record(all_items=True, exclude_keywords=["Mango"])
Once the Mango CQP data was corrected (min/max swapped back), the exclusion was removed.
The exclude_keywords parameter remains in the code for future use.

### 3. Item name from mat-select includes extra label text
Problem: _select_random_mat_option_nth returns inner_text().strip() of the mat-option.
Mat-options sometimes render as "Mango Matte Grey Puny Square" with descriptors after
the commodity name. CQP search for this full string finds no results, leaving cqp_config
empty for that item and causing safe_actual_values fallback.
Status: Known issue, not fully fixed. Workaround: fill_actual_values caps to visible input
count so extra values from the fallback don't cause timeouts. CQP lookup improvement
(e.g. search by first word only) is a future improvement.

### 4. handle_success_alert not handling slow swal2 dismiss
Problem: After clicking confirm on the swal2 popup, occasionally the container lingered
and the next navigate_to_page() or wait_for_selector("table...") ran before the popup
fully closed, causing selector conflicts.
Fix: Used JS evaluate for the confirm click (document.querySelector('.swal2-confirm')?.click())
which fires without waiting for Playwright's actionability checks. Combined with
wait_for_selector(".swal2-container", state="hidden") in a try/except to give it time.

---

## IN Time Picker — Special Handling

The owl-datetime-picker cannot be interacted with using standard Playwright fill/type.
It renders two separate number inputs (.owl-dt-timer-input) for hour and minute.

fill_in_time() approach:
1. Click the IN Time input to open the picker
2. Wait for .owl-dt-timer-input to appear
3. JS-set both inputs (hour=10, minute=0) with input+change events
4. JS-click the "Set" button by searching button text

Always uses hardcoded 10:00. Change the defaults if the app enforces business hours validation.

---

## Running the Suite

```bash
# Full suite
python -m pytest pages/private_b2b/modules/gate_pass/test/playwright/test_gp_ui.py -v

# By marker
python -m pytest pages/private_b2b/modules/gate_pass/test/playwright/test_gp_ui.py -m smoke -v
python -m pytest pages/private_b2b/modules/gate_pass/test/playwright/test_gp_ui.py -m regression -v
python -m pytest pages/private_b2b/modules/gate_pass/test/playwright/test_gp_ui.py -m workflow -v
```

## Environment Variables Required

```
RHYTHMERP_LOGIN_URL   (default: https://rhythmerp.algorhythms.in)
RHYTHMERP_EMAIL
RHYTHMERP_PASSWORD
```
