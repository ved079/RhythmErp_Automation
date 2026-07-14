# PO → PB Flow Tests — Developer Notes

## Overview

End-to-end Playwright test suite covering the direct Purchase Order → Purchase Booking flow
on the **Rolex Traders** ERP tenant. No GP / GRN / QC in this chain — PBs are booked straight
against a PO.

**12 tests across 6 classes. Full run takes ~23 minutes** (real browser, slow_mo=150ms).

---

## File Structure

```
pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/po_pb_flow/
    conftest.py              # fixtures: browser, login, po_page, pb_page
    test_po_pb_flow.py       # all 12 tests
    PO_PB_FLOW_NOTES.md      # this file
```

Page objects used (not owned by this suite — do not modify here):

```
pages/private_b2b/modules/purchase_order/po_playwright_page.py   # POPlaywrightPage
pages/private_b2b/modules/purchase_booking/pb_playwright_page.py  # PBPlaywrightPage
```

---

## Credentials & Tenant

```
Login URL : https://rhythmerp.algorhythms.in   (RHYTHMERP_LOGIN_URL)
Email     : kedar@rhythmflows.com               (RHYTHMERP_PB_EMAIL)
Password  : Kedar@999999                        (RHYTHMERP_PB_PASSWORD)
Tenant    : Rolex Traders                       (RHYTHMERP_PB_TENANT)
```

Override any of these via environment variables before running.

---

## Fixture Architecture

```
playwright_instance  (session-scoped)
    └─ browser           (session-scoped, headless=False, slow_mo=150)
        └─ browser_context  (session-scoped)
            └─ logged_in_page  (session-scoped) ← single shared browser tab
                ├─ po_page         (function-scoped) → navigate to PO listing on setup
                ├─ pb_page         (function-scoped) → navigate to PB listing on setup
                └─ po_for_pb_validation  (class-scoped) → creates one PO for TestPBValidations
```

### Critical constraint — one shared browser tab

All fixtures share the same `logged_in_page` object (one browser tab). Navigation is not
isolated between fixtures. When a test uses **both** `po_page` and `pb_page`, the fixture
setup order matters:

1. `po_page` setup: navigates to PO listing
2. `pb_page` setup: navigates to PB listing (overwrites step 1)

At test start the browser is on **PB listing**. If the test needs to use `po_page` first,
it must call `po_page.navigate_to_page()` explicitly at the top of the test.

Similarly, after `po_page.create_record_for_integration()` the browser ends on PO listing.
Before calling `pb_page.create_record_from_po()`, always call `pb_page.navigate_to_page()`
so `pb_page.open_add_form()` clicks the correct ADD button.

**If you forget `pb_page.navigate_to_page()` before `create_record_from_po()`, the PO ADD
button gets clicked instead, a PO form opens, and you get:
`AssertionError: No item rows auto-patched after PO selection`**

---

## Test Classes

### TestPO_PB_DirectFlow — `test_single_item_flow`

Single-item PO with disc=5%, int=2% → PB must carry same qty, rate, txn.

```
item_configs = [(qty=10, disc=5, int=2)]
```

Asserts per row: `pb_qty == po_qty`, `|pb_rate - po_rate| < 0.01`, `|pb_txn - po_txn| < 1.0`
Asserts total: `|pb_total - sum(po_txn_amounts)| < 1.0`

---

### TestPO_PB_MultiRow — `test_multi_row_flow`

2-item PO with different disc/int per row → PB must match every row independently.

```
item_configs = [(qty=10, disc=5, int=2), (qty=5, disc=3, int=1)]
```

Uses `_assert_pb_rows()` helper which zips PO and PB rows and asserts each pair.

---

### TestPO_PB_CustomRate — `test_custom_rate_flow`

Verifies the PO Rate field is editable. Rate auto-fetches from Commodity Base Rate master
after item selection (2s wait). Test overrides it to 90% of auto-fetched value.
PB must carry the custom rate, not the original.

Key pattern for reading auto-fetched rate (PO form has no loading indicator):
```python
for _ in range(5):
    raw = page.evaluate(JS_XPATH_READER, [RATE_XPATH, 0])
    if raw and float(raw) > 0:
        auto_rate = float(raw)
        break
    page.wait_for_timeout(800)
```
If `auto_rate == 0` after the loop, the rate fetch timed out — check ERP connectivity.

---

### TestPO_PB_NoGST — `test_no_gst_flow`

PO created with `enable_gst=False`. Without GST, `txn_amount = rate × qty` exactly.
PB must reproduce the same txn without adding tax.

Assertion: `|txn_amount - rate * qty| < 0.50`

If this fails with a larger difference, GST is being applied despite being disabled.

---

### TestPOValidations — 3 tests

Validation rules for the PO form on Rolex Traders tenant. All use `function-scoped`
`po_page` (fresh navigate per test).

| Test | What it checks |
|------|---------------|
| `test_empty_submit_and_cancel` | Submit empty form → stays open; Cancel → listing visible |
| `test_field_validations` | qty=0, qty=-1, disc=110, int=-5 → mat-error appears each time |
| `test_duplicate_item_blocked` | Same item in 2 rows → `already added` mat-error |

`test_field_validations` is a single test that opens/closes the form 4 times (one per
invalid-input scenario). Each sub-check calls `_open_with_one_item()` (open form + fill
header + select random item + wait 1.5s) then fills the bad value and asserts.

---

### TestPBValidations — 5 tests

Validation rules for the PB form. Uses a **class-scoped** `po_for_pb_validation` fixture
that creates one PO (qty=20, GST off, no disc/int) once and reuses it across all tests.
Tests cancel without submitting so the PO remains selectable for the next test.

| Test | What it checks |
|------|---------------|
| `test_empty_submit_and_cancel` | Submit empty PB → mat-errors + form stays; Cancel → listing |
| `test_no_po_selected_submit_blocked` | Select supplier only (no PO) → mat-errors on submit |
| `test_header_field_limits_blocked` | Discount>100, Round Off Credit>1, Round Off Debit>1 → mat-error |
| `test_qty_popup_validations_blocked` | EBW>qty, labour>gross, qty=0 in popup → error/popup stays |
| `test_transportation_does_not_affect_total` | Transportation charge must NOT change Total Amount |

---

## Key Helpers

### `_assert_pb_rows(po_rows, pb_rows, po_ref_no)`
Module-level helper. Zips PO and PB row dicts, asserts qty/rate/txn per row, prints table.

### `_open_with_one_item(self, po_page)` (TestPOValidations)
Opens PO add form, fills header (random supplier/location etc.), selects random item, waits
1.5s for Rate to auto-fetch. Used before every field-level validation check.

### `_open_pb_with_po(self, pb_page, supplier_name)` (TestPBValidations)
Opens PB add form, selects supplier, selects most-recent PO, waits for items to auto-patch.

### `_fill_native(self, pb_page, selector, value)` (TestPBValidations)
Fills a number input via Playwright native click + fill + Tab (not JS setter). This triggers
Angular's `blur` event so validators fire and mark the field `touched`/`dirty`.
Falls back to `xpath.first` if the visible filter returns nothing.

### `_visible_errors(self, pb_page)` (TestPBValidations)
Returns list of **visible** mat-error texts using JS `offsetParent !== null` filter.
Use this instead of `page.locator("mat-error").all()` when prior tests have left stale
hidden mat-error elements in the Angular SPA DOM.

### `_cancel(self, pb_page)` (TestPBValidations)
Closes any open qty-popup (Escape if DONE_BTN visible), then calls `navigate_to_page()` to
return to PB listing. Does not rely on clicking a Cancel button — navigation is safer in an
Angular SPA where the form state may be dirty.

---

## Angular SPA DOM Quirks & Known Fixes

### 1. `mat-error` elements present but not visible

**Symptom:** `wait_for_selector("mat-error")` times out even though `locator("mat-error").count() > 0`.

**Cause:** Angular renders `mat-error` elements in the DOM even when they are hidden (`display:none`).
Prior tests leave stale mat-errors in the DOM. `wait_for_selector` waits for **visible** state by
default — it will hang if only hidden/stale errors are present.

**Fix:** Use JS `offsetParent` filter to count only truly visible errors:
```python
errors = page.evaluate("""
    () => Array.from(document.querySelectorAll('mat-error'))
               .filter(el => el.offsetParent !== null)
               .map(el => el.innerText.trim())
""")
assert len(errors) > 0
```
Or: click Submit first to force Angular to surface all validators, then check.

---

### 2. `_fill_native` vs `_fill_number_nth` — when to use which

| Method | Mechanism | When to use |
|--------|-----------|-------------|
| `_fill_number_nth(selector, idx, value)` | JS property setter + `dispatchEvent('input', 'change')` | Header fields where Angular reads value via JS binding; instant, no blur needed |
| `_fill_native(selector, value)` | Playwright click + fill + Tab (real DOM events) | Fields where Angular validator only fires on `blur`/`touched` — needed for discount, round-off credit, labour charges in PB form |

If `_fill_native` doesn't trigger the error, click Submit as a fallback (forces all validators).

---

### 3. Rate auto-fetch race on multi-row PO

Rate is fetched from Commodity Base Rate after item selection. There is no loading indicator.
For rows beyond row 0, Angular's `selectionChange` wiring may not fire correctly until the
component is "nudged" (see PO_notes.md bug #7). `create_record_for_integration` handles this
internally — tests do not need to do anything special.

---

### 4. `open_add_form()` does not navigate first

`PBPlaywrightPage.open_add_form()` assumes the browser is already on the PB listing page.
It does NOT call `navigate_to_page()` internally. If you call it while on any other page,
the ADD button click will open the wrong form.

**Always call `pb_page.navigate_to_page()` before `create_record_from_po()` in any test
that uses both `po_page` and `pb_page`.**

---

### 5. Error text varies by ERP version

The labour/amount error text is matched broadly because it has changed between ERP builds:

```python
assert any(
    "less than 0" in e or "cannot" in e.lower()
    or "greater than 0" in e or "must be" in e.lower()
    for e in errors
)
```

If this assertion starts failing, print `errors` and add the new text pattern to the `any()`.

---

## Running the Suite

```bash
# Full suite (~23 min)
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/po_pb_flow/test_po_pb_flow.py -v

# Only flow tests (~12 min)
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/po_pb_flow/test_po_pb_flow.py -m po_pb -k "Flow or MultiRow or CustomRate or NoGST" -v

# Only validation tests (~11 min)
python -m pytest pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/po_pb_flow/test_po_pb_flow.py -k "Validations" -v

# Single test
python -m pytest "pages/private_b2b/modules/Purchase_Flow_Tests/test/playwright/po_pb_flow/test_po_pb_flow.py::TestPO_PB_DirectFlow::test_single_item_flow" -v -s
```

---

## Common Failures & Diagnosis

| Error message | Likely cause | Fix |
|---------------|-------------|-----|
| `No item rows auto-patched after PO selection` | `pb_page.open_add_form()` clicked the PO ADD button, not the PB one — browser was on wrong page | Add `pb_page.navigate_to_page()` before `create_record_from_po()` |
| `Rate did not auto-fetch after item selection` | ERP rate API slow or item has no base rate in master | Increase `wait_for_timeout` in rate-polling loop, or check Commodity Base Rate master |
| `wait_for_selector("mat-error") timeout` | Stale hidden mat-errors in SPA DOM; the new error never appeared visibly | Use `_visible_errors()` helper; click Submit to force Angular validators |
| `PB rate X != PO rate Y` | Rate field not correctly overridden; JS setter may have been overwritten by Angular reactivity | Use `_fill_number_nth` then verify value back via JS before submitting |
| `PB txn X != PO txn Y` | PO txn uses disc/int baked in but PB is reading raw qty×rate | Check that `txn_amount` in po_rows comes from ERP-calculated value, not a formula recomputed in Python |
| `Expected mat-errors when no PO is selected` — 0 errors | ERP changed PO validation to show toast instead of mat-error | Check what error element the ERP actually renders and update selector |
| `AssertionError: GST must be off` | `enable_gst=False` param not implemented in `create_record_for_integration` for this tenant | Check GST toggle selector in PO page object |
| Fixture `po_for_pb_validation` error | PO creation failed; the fixture creates a real PO — ERP must be reachable | Check ERP login and network connectivity |
| `close_popup()` hangs during teardown | Browser was closed mid-test (KeyboardInterrupt); teardown tries to interact with closed page | Safe to ignore during Ctrl+C — not a test failure |

---

## Formula Reference

### PO amounts

```
txn_amount (per row) = rate × qty
total_po_amount      = sum(txn_amount_i) × (1 - disc/100 + int/100)
```

disc and int are **PO-level** (not per-row). If disc > int, total < row_sum. If int > disc, total > row_sum.

### PB amounts

PB does NOT recompute from rate/qty. It inherits `txn_amount` directly from the PO row.
So `pb_txn_amount == po_txn_amount` (within rounding tolerance of 1.0).

Transportation and other charges are separate fields and do **not** modify Total Amount.

---

## Test Count History

| Version | Tests | Notes |
|---------|-------|-------|
| Original | 25 | 4 flow classes × 2 steps + 7 PO validations + 10 PB validations |
| Consolidated | 12 | Merged step1+step2 into 1 per flow; merged validation groups |
