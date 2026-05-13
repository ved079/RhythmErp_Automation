# Error Code Mst — Screen Knowledge

> Module: `Common Settings > Error Code Mst`
> URL: `https://rhythmerp.algorhythms.in/#/dynamic-screens/Error%20Code%20Mst`
> Generated: 2026-05-14

---

## 1. Module Overview

Error Code Mst is a **dynamic screen** under Common Settings used to manage error code definitions. Each record maps an **Error Code Type** + **Code** combination to a description and a quantity/amount flag. The module follows the **Vehicle Master proven pattern** for layout, toolbar, table, and popups.

---

## 2. Form Fields (4 Fields)

| # | Field Label | Type | Required | Selector / Locator | Notes |
|---|-------------|------|----------|-------------------|-------|
| 1 | Error Code Type | `mat-select` dropdown | Yes | `//mat-label[contains(.,'Error Code Type')]/ancestor::mat-form-field//mat-select` | Standard mat-select with built-in search. **NOT** app-dropdown-v2. |
| 2 | Code | Text input | Yes | `input[name='Code']` | No max-length restriction. Accepts special characters. |
| 3 | Description | Text input | No (optional) | `input[name='Description']` | No max-length restriction. Can be left blank. |
| 4 | Is Qty/Amt | `app-slide-toggle-v2` | N/A (default=Amount) | `.switch-container.vertical input[type='checkbox']` | Default = Amount (unchecked/No). Toggle = Quantity (checked/Yes). |

### Dropdown Options (Fixed — 4 Options)
The Error Code Type dropdown has exactly **4 static options** — they are NOT dynamically loaded:

1. `Farmer`
2. `Debit Note`
3. `Credit Note`
4. `Workflow`

The dropdown includes a built-in search box that filters options as you type.

### Toggle Behavior
- **Amount** (default, off) → table displays **"No"** in Is Qty/Amt column
- **Quantity** (on) → table displays **"Yes"** in Is Qty/Amt column
- Component: `app-slide-toggle-v2` — custom Angular toggle
- **Automation note**: Click the `<input type="checkbox">` directly + dispatch `change` + `input` events for Angular change detection. Clicking the wrapper `.switch-container.vertical` does NOT reliably trigger Angular binding.

---

## 3. Toolbar

| Button | Tooltip | Locator |
|--------|---------|---------|
| Add | ADD | `//*[@mattooltip='ADD']/button` |
| Refresh | REFRESH | `//*[@mattooltip='REFRESH']/button` |
| More | More | `//button[@mattooltip='More']` |

---

## 4. Table Structure

- **Table ID**: `table#excel-table`
- **Rows**: `table#excel-table tbody tr`
- **Pagination**: **YES** — 10 rows per page (paginator present)
- **Search**: **NO** — there is no table-level search/filter input

### Table Columns

| Column | CSS Class | Content |
|--------|-----------|---------|
| View (eye icon) | `mat-column-view` | Action button |
| Edit (pencil icon) | `mat-column-edit` | Action button |
| History (archive icon) | `mat-column-archive` | Action button |
| Error Code Type | `mat-column-error_code_type` | Text from dropdown |
| Code | `mat-column-code` | Text value |
| Description | `mat-column-description` | Text value |
| Is Qty/Amt | `mat-column-is_qty_amount` | "Yes" or "No" |

---

## 5. Popup / Form Modes

The form popup uses the standard Vehicle Master popup structure:

### Form Popup Locators
```python
POPUP_CONTAINER = "//div[contains(@class,'edit_pop_up') and contains(@class,'popup-mode')]"
POPUP_HEADER    = ".popup-header"
POPUP_TITLE     = ".big-model h3"
POPUP_FOOTER    = "//div[contains(@class,'popup-footer')]"
CANCEL_BUTTON   = "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
SUBMIT_BUTTON   = "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
UPDATE_BUTTON   = "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
CLOSE_X_BUTTON  = "//div[contains(@class,'big-model')]//button//mat-icon[contains(text(),'close')]"
```

### Mode Detection
| Mode | How to Detect | Submit? | Update? | Fields |
|------|---------------|---------|---------|--------|
| **Create** (Add) | Opened via ADD button | Yes (visible) | No | All enabled |
| **Edit** | Opened via row Edit button | No | Yes (visible) | All enabled |
| **View** | Opened via row View button | No | No | All disabled |

### Key Mode Behaviors
- **View mode**: All fields are **disabled** (readonly). Only the **Cancel** button is present. No Submit or Update button.
- **Edit mode**: The **Update** button replaces the Submit button. All fields are enabled and **pre-filled** with existing data.
- **Close detection**: Form popup is visible when `div.big-model` is displayed. Check `is_displayed()` for open/closed detection.

---

## 6. Success / Error Behavior

### Success (Create/Update)
- **NO success SweetAlert2 popup** — the form closes **silently** on successful create or update.
- Detection: Check if form popup is no longer displayed after submit.

### Validation Failed
- SweetAlert2 popup with title **"Validation Failed"**
- No specific message content — same generic popup for ALL validation errors (empty fields, missing required, duplicates)
- SweetAlert2 locators:
  ```python
  SWAL_CONTAINER = ".swal2-container"
  SWAL_TITLE     = "#swal2-title"
  SWAL_CONTENT   = ".swal2-html-container"
  SWAL_CONFIRM   = ".swal2-confirm"
  ```

### Duplicate Detection
- Uses the **same generic "Validation Failed"** SweetAlert2 — there is NO specific "duplicate record" message.
- Duplicate is defined by: **same Error Code Type + same Code** combination.
- Two records with the same Code but different Error Code Types are allowed.

---

## 7. History Popup

Opened via the archive/history button on each table row.

### History Locators
```python
HISTORY_POPUP       = ".popup-content"
HISTORY_TITLE       = "//h3[contains(.,'History')]"
HISTORY_CANCEL      = "//div[contains(@class,'popup')]//button[contains(.,'Cancel')]"
HISTORY_TABLE_ROWS  = ".edit_pop_up table tbody tr"
HISTORY_SEARCH      = ".edit_pop_up input[placeholder='Search box']"
NO_DATA_IMAGE       = ".edit_pop_up img[alt='No Data Available']"
```

### History Behaviors
- Newly created records show **"No Data Available"** (no history entries).
- History popup includes a search box for filtering history entries.
- Closed via Cancel button.

---

## 8. Proven Automation Patterns

### Field Fill Order (Critical)
**Always fill in this order**: Dropdown → Text fields → Toggle

1. Select Error Code Type (dropdown) first — most likely to fail, needs retry
2. Fill Code (text input)
3. Fill Description (text input)
4. Set Is Qty/Amt toggle last

### Dropdown Click Quirk
The mat-select dropdown sometimes **doesn't open on first click**. Automation strategy:
- Click dropdown trigger via JS `execute_script("arguments[0].click();")`
- Wait 1.5s for overlay panel
- If no panel opens → retry with ActionChains click
- If still no panel → return False (caller should retry entire form)

### Text Input Pattern
```python
el.clear()
el.send_keys(text)
# Dispatch input event for Angular reactivity
driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", el)
```

### Toggle Click Pattern (Critical)
```python
cb = driver.find_element(By.CSS_SELECTOR, ".switch-container.vertical input[type='checkbox']")
driver.execute_script("""
    var cb = arguments[0];
    cb.click();
    cb.dispatchEvent(new Event('change', {bubbles: true}));
    cb.dispatchEvent(new Event('input', {bubbles: true}));
""", cb)
```

### Submit Detection Order (Critical)
After clicking Submit/Update, check in this order:
1. **First**: Check for validation SweetAlert2 alert (timeout=5s)
2. **Then**: Check if form popup closed (success)
- Wrong order causes false positives when duplicate validation alert appears.

### Overlay Cleanup
After dropdown selection, leftover CDK overlay panels may block other interactions:
```python
driver.execute_script("""
    document.querySelectorAll('.cdk-overlay-backdrop:not(.cdk-overlay-dark)').forEach(el => el.remove());
    document.querySelectorAll('.cdk-overlay-pane:not(.mat-mdc-dialog-container)').forEach(el => el.remove());
""")
```

### SweetAlert2 Cleanup
```python
driver.execute_script("""
    document.querySelectorAll('.swal2-container').forEach(el => el.remove());
    document.querySelectorAll('.swal2-backdrop-show').forEach(el => el.remove());
""")
```

---

## 9. Quirks & Gotchas

| # | Quirk | Impact | Workaround |
|---|-------|--------|------------|
| 1 | **No success SweetAlert2** | Can't confirm success via popup | Check form close instead |
| 2 | **Generic "Validation Failed"** | Can't distinguish empty vs duplicate | Accept as-is — both show same alert |
| 3 | **Pagination at 10 rows** | Row count assertions are fragile | Use `is_code_in_table()` instead of `get_table_row_count()` |
| 4 | **No table search** | Can't filter rows to find records | Loop through visible rows with `find_code_row_index()` |
| 5 | **Dropdown click unreliable** | Selection may not register | Built-in retry logic (3 attempts) |
| 6 | **Toggle wrapper click doesn't work** | Toggle state not saved | Click `<input checkbox>` + dispatch events |
| 7 | **No max-length on text fields** | Can enter 300+ char codes | Not a bug — ERP accepts long values |
| 8 | **Special characters accepted** | Code like `TEST@#$%^&*()` works | Not sanitized by ERP |
| 9 | **Form closes silently** | No feedback on successful submit | Only detect via form visibility check |

---

## 10. Test Coverage Summary

### Test Suite: 22 Tests — 22/22 Passing

| Class | Tests | IDs | Coverage |
|-------|-------|-----|----------|
| TestCreateFormValidations | 8 | C01–C08 | Empty submit, missing dropdown, missing code, valid create, optional description, duplicate, toggle quantity, special chars |
| TestViewFormBehaviors | 3 | V01–V03 | Fields disabled, correct data display, cancel closes |
| TestEditFormValidations | 5 | E01–E05 | Update button, fields enabled, pre-filled data, update changes table, edit duplicate |
| TestHistoryValidations | 3 | H01–H03 | Popup opens, content/no-data, cancel closes |
| TestTableOperations | 3 | T01–T03 | New record in table, column values match, toggle default shows No |

---

## 11. File Structure

```
pages/common_settings/modules/error_code_mst/
    __init__.py
    error_code_mst_page.py          # Page Object (40 methods)
    data/
        __init__.py
        error_code_mst_data.py      # Constants + 7 generators + 8 edge-case datasets
    test/
        __init__.py
        conftest.py                 # Session driver, login, ecm_page fixture
        test_error_code_mst_validation.py   # 22 tests across 5 classes
        reports/                    # Auto-generated Excel reports
```

---

## 12. Automation Spec

Excel spec with 13 sheets: `/download/Error_Code_Mst_Automation_Spec_Final.xlsx`
