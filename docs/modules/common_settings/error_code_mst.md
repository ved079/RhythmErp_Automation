# Module: Error Code Mst

> **The silent-success module.** Unlike most modules, Error Code Mst does NOT show a success SweetAlert — the form just closes silently on success. This behavior has caught out every developer at least once, leading to false-negative test failures.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Common Settings |
| **Complexity** | Medium (4 fields, 1 FK pool, custom toggle) |
| **Steppers** | 0 — flat popup form |
| **Repeating rows** | No |
| **API tests** | ✅ schema, perf |
| **UI tests** | ✅ validation (~539 LOC) |
| **Page object** | ✅ error_code_mst_page.py (943 LOC) |
| **Data file** | ✅ error_code_mst_data.py (341 LOC) |
| **batch_create** | ✅ |

---

## The ERP Screen

Error Code Mst is found under **Common Settings → Error Code Mst** in the ERP sidebar. It's a flat popup form with 4 fields:

- **Error Code Type** — mat-select dropdown, required. 4 fixed options: Farmer (ID=643), Debit Note (ID=216), Credit Note (ID=215), Workflow (ID=140).
- **Code** — text input, required. Error code identifier, typically alphanumeric with hyphens (e.g. "FM-DOC", "DN-REJ").
- **Description** — text input, required. Human-readable description of the error code.
- **Is Qty/Amt** — custom `app-slide-toggle-v2` toggle. Two options: "Qty" (checked/on) or "Amount" (unchecked/off, default).

### Navigation URL
`https://rhythmerp.algorhythms.in/#/dynamic-screens/Error%20Code%20Mst`

### Key UI Behaviors

1. **NO success SweetAlert** — this is the defining quirk. After successful create or update, the form popup closes silently. No "added successfully" toast, no SweetAlert, nothing. You detect success by checking that the form is no longer visible.
2. **Validation SweetAlert DOES appear** — "Validation Failed" SweetAlert appears for empty required fields or other validation errors. Only success is silent.
3. **Custom toggle `app-slide-toggle-v2`** — uses a checkbox under the hood. The toggle displays "Amount" when unchecked and "Qty" when checked. Clicking the checkbox + dispatching `change` and `input` events triggers Angular's change detection.
4. **Row actions use COLUMN-BASED CSS, not 3-dot menu** — unlike most modules that use a kebab menu, Error Code Mst has separate action buttons per column: `mat-column-view`, `mat-column-edit`, `mat-column-archive`.

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
```

```json
{
    "id": "",
    "error_code_type": 643,
    "code": "FM-DOC",
    "description": "Farmer documentation incomplete or missing",
    "is_qty_amount": "Qty",
    "attribute_name": "ErrorCodeMst"
}
```

### Field Mapping

| UI Field | API Key | Type | Required | Notes |
|----------|---------|------|----------|-------|
| Error Code Type | `error_code_type` | integer (FK) | Yes | FK ID, not display string |
| Code | `code` | string | Yes | Alphanumeric with hyphens |
| Description | `description` | string | Yes | Human-readable |
| Is Qty/Amt | `is_qty_amount` | string enum | Yes | "Qty" or "Amount" |

### FK Dependencies

| FK Field | Pool Name | Options | IDs |
|----------|-----------|---------|-----|
| error_code_type | ERROR_CODE_TYPE_IDS | 4 types | Farmer=643, Debit Note=216, Credit Note=215, Workflow=140 |

Note: `attribute_name` is `"ErrorCodeMst"` — no space, PascalCase. Different from the UI display "Error Code Mst".

---

## Data Layer

### FK Pools

```python
ERROR_CODE_TYPE_IDS = {
    "Farmer":      643,
    "Debit Note":  216,
    "Credit Note": 215,
    "Workflow":    140,
}
```

### Realistic Data

The data file includes semantically appropriate code/description pairs for each error type:

| Type | Code Examples | Description Examples |
|------|--------------|---------------------|
| Farmer | FM-DOC, FM-KYC, FM-LAND, FM-BANK, FM-VERIFY | Documentation incomplete, KYC failed, Land record discrepancy |
| Debit Note | DN-REJ, DN-SHORT, DN-DAMG, DN-PRICE, DN-QTY | Rejected material, Quantity shortage, Damaged goods |
| Credit Note | CN-RETN, CN-OVER, CN-ADJ, CN-DISC, CN-REBATE | Returned goods, Overpayment adjustment, Discount not applied |
| Workflow | WF-APPR, WF-REJ, WF-HOLD, WF-ESC, WF-RTRY | Approval pending, Rejected, On hold, Escalation |

### Payload Builder

```python
def build_error_code_mst_api_payload(error_code_type_id, code, description,
                                      is_qty_amount="Qty"):
    return {
        "id": "",
        "error_code_type": error_code_type_id,
        "code": code,
        "description": description,
        "is_qty_amount": is_qty_amount,
        "attribute_name": "Error Code Mst",
    }
```

The `generate_error_code_mst_api_payloads()` cycles through all 4 error types for variety and appends index suffixes to ensure unique codes within a batch.

### Validation Rules

```python
FIELD_VALIDATION_RULES = {
    "error_code_type": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": 4,
    },
    "code": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Alphanumeric with hyphens (e.g. FM-DOC, DN-REJ).",
    },
    "description": {
        "type": "character",
        "required": True,
        "max_length": 255,
    },
    "is_qty_amount": {
        "type": "character",
        "required": True,
        "note": "Enum: 'Qty' or 'Amount'.",
    },
}
```

---

## Page Object

### Key Methods

| Method | Purpose |
|--------|---------|
| `navigate_to_page()` | URL + force refresh + wait for table |
| `open_add_form()` | JS click Add button + verify popup |
| `select_error_code_type(text)` | mat-select with 4 options |
| `fill_all_fields(data, max_retries=3)` | **Dropdown first with up to 3 retries + page refresh** |
| `toggle_is_qty_amt(state)` | Click checkbox + dispatch Angular events |
| `create_record(data)` | One-call create — alert-first detection |
| `edit_record(row_index, data)` | One-call edit — alert-first detection |
| `click_view_on_row(row_index)` | Column-based `mat-column-view` button |
| `click_edit_on_row(row_index)` | Column-based `mat-column-edit` button |
| `click_history_on_row(row_index)` | Column-based `mat-column-archive` button |

### Tricky Bits

**1. Does NOT extend BasePage — standalone class**

Unlike most Common Settings modules (Designation, Season, Tax Authority, etc.), `ErrorCodeMstPage` is a standalone class that doesn't inherit from `BasePage`. It manages its own `WebDriverWait`, element finding, and click methods. This means:
- No `self.click()`, `self.find_element()`, `self.wait_for_visible()` from BasePage
- All interactions use `self.driver.execute_script()` or direct Selenium calls
- `self.wait = WebDriverWait(driver, 15)` is its own wait instance

If you're used to BasePage patterns, this module will feel different. The standalone approach was chosen because Error Code Mst was built based on "Vehicle Master proven patterns" which is also standalone.

**2. `fill_all_fields()` has retry logic with PAGE REFRESH**

The `fill_all_fields()` method is the most defensive in the project:

```python
def fill_all_fields(self, data, max_retries=3):
    for attempt in range(1, max_retries + 1):
        success = self._fill_all_fields_once(data)
        if success:
            return True
        print(f"  [Retry {attempt}/{max_retries}] Dropdown didn't register, retrying...")
        self.cancel()
        time.sleep(1)
        self.driver.refresh()      # HARD REFRESH
        time.sleep(2)
        self._wait_for_page_ready()
        time.sleep(1)
        self.open_add_form()       # Re-open form
        time.sleep(1.5)
    return False
```

If the dropdown fails to register (Angular doesn't accept the selection), it:
1. Cancels the current form
2. Hard-refreshes the page (full browser refresh)
3. Waits for the page to reload
4. Re-opens the Add form
5. Tries again — up to 3 times

This was necessary because the Error Code Type dropdown was the most unreliable in testing — it would sometimes visually show the selected value but Angular wouldn't register it in the form model.

**3. Row actions use column CSS — NO kebab menu**

Error Code Mst doesn't have a 3-dot kebab menu at all. Instead, each row has separate action buttons in dedicated columns:

```python
VIEW_BUTTON = (By.XPATH, "//td[contains(@class,'mat-column-view')]//button")
EDIT_BUTTON = (By.XPATH, "//td[contains(@class,'mat-column-edit')]//button")
HISTORY_BUTTON = (By.XPATH, "//td[contains(@class,'mat-column-archive')]//button")
```

This is simpler but requires row-index-based selection. The `click_view_on_row(row_index)` method finds the row by index and clicks the button in that row's column.

**4. The custom `app-slide-toggle-v2` toggle**

The toggle is NOT a standard Angular Material slide-toggle. It's a custom component with a hidden checkbox:

```python
TOGGLE_CONTAINER = ("css", ".switch-container.vertical")
TOGGLE_CHECKBOX = ("css", ".switch-container.vertical input[type='checkbox']")
```

To toggle it:
```python
cb = self.driver.find_element(*self.TOGGLE_CHECKBOX)
current = self.is_toggle_quantity()
want_on = (state == TOGGLE_QUANTITY)
if current != want_on:
    self.driver.execute_script("""
        var cb = arguments[0];
        cb.click();
        cb.dispatchEvent(new Event('change', {bubbles: true}));
        cb.dispatchEvent(new Event('input', {bubbles: true}));
    """, cb)
```

The checkbox click + event dispatch is needed because Angular's change detection doesn't fire from a plain Selenium `.click()` on this component.

**5. Success detection: form-closed = success**

Since there's no success SweetAlert, the `create_record()` and `edit_record()` methods detect success by checking if the form closed:

```python
def create_record(self, data):
    # ... fill and submit ...
    
    # Check for validation alert FIRST
    if self.is_validation_alert_present(timeout=5):
        # Validation failed — handle alert
        return {"status": "failed", ...}
    
    # No alert — wait for form to close = success
    time.sleep(3)
    if self.is_form_closed():
        return {"status": "success", "message": "Record created (form closed silently)"}
    else:
        return {"status": "failed", "error": "Form still open after submit"}
```

The "alert-first" pattern is crucial — checking for the form closing BEFORE checking for validation alerts would give false positives (form might close for other reasons).

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| ECM-001 | Medium | No success SweetAlert — form closes silently. Makes success detection harder than other modules. |
| ECM-002 | Low | `is_toggle_quantity()` uses `cb.is_selected()` which can return stale values if the DOM hasn't updated after a click |
| ECM-003 | Low | `navigate_to_page()` does a force refresh after navigation — sometimes needed because the initial page load doesn't render the table |

---

## War Stories

### "Wait, Did It Succeed or Not?"
The first time we ran a create test against Error Code Mst, the test failed with "Form still open after submit." We assumed the creation had failed, but when we checked the ERP, the record was there. The form had closed successfully — it just didn't show a SweetAlert. Every other module shows one. This one doesn't.

The fix was the "alert-first then form-close" pattern: check for validation alerts first (they DO appear), then check if the form closed (that's success). The `time.sleep(3)` after submit is unfortunately necessary because there's no SweetAlert to wait for — you just have to give the form time to close.

### "The Dropdown That Keeps Forgetting"
The Error Code Type dropdown was the flakiest element we'd encountered. We'd select "Farmer", the dropdown would show "Farmer", we'd submit, and — "Validation Failed: Error Code Type is required." Angular hadn't registered the selection. This happened about 20% of the time.

The `fill_all_fields()` retry loop was born from this. When the dropdown fails to register, we cancel the form, hard-refresh the page, re-open the form, and try again. With 3 retries, the success rate is effectively 100%. The cost is about 5 extra seconds on the rare occasions a retry is needed.

### "Column Buttons vs Kebab Menu — Why Not Both?"
Error Code Mst uses column-based action buttons (View/Edit/History as separate columns in the table). Most other modules use a 3-dot kebab menu. We initially wrote code assuming a kebab menu, then had to rewrite it when we discovered the different UI. The lesson: **always visually inspect the ERP screen before writing page object code.** Assumptions about UI patterns will burn you.

---

## Test Coverage

| Test Type | Status | Count |
|-----------|--------|-------|
| API: Payload | ✅ Complete | ~10 tests |
| API: Schema | ✅ Complete | ~8 tests |
| API: Performance | ✅ Complete | ~5 tests |
| UI: Validation | ✅ Complete | ~15 tests |

---

## Files

```
pages/common_settings/modules/error_code_mst/
├── error_code_mst_page.py          (943 LOC)
├── Error_Code_Mst_Screen_Knowledge.md
├── data/
│   └── error_code_mst_data.py     (341 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_error_code_mst_validation.py  (539 LOC)
    └── api/
        ├── conftest.py
        ├── test_error_code_mst_payload.py
        ├── test_error_code_mst_schema.py
        └── test_error_code_mst_perf.py
```
