# Supplier Update Module Reference (`supplier_update_section.py`)

This module provides a set of helper functions to perform **update tests** on existing Supplier records in the FPC ERP system. It includes utilities for searching, interacting with list‑page action buttons (history, edit, view), verifying history logs, and submitting partial updates.

## Helper Functions

### `search_supplier(driver, wait, search_term)`

Types the given search term into the list‑page search box and presses Enter.

| Parameter   | Type  | Description                     |
|-------------|-------|---------------------------------|
| `search_term` | `str` | Text to search for (e.g., supplier company name). |

---

### `get_first_row(driver, wait)`

Waits for the table to contain at least one row and returns the first row element.

**Returns:** `WebElement` – the first `<tr>` in the table body.

---

### `click_action_button(driver, wait, button_selector, action_name)`

A bulletproof helper that clicks an action button (edit, view, history) inside the first table row.  
It re‑fetches the element on every attempt to avoid `StaleElementReferenceException` and uses a JavaScript click to bypass overlays.

| Parameter        | Type  | Description                                 |
|------------------|-------|---------------------------------------------|
| `button_selector` | `str` | CSS selector for the button (e.g., `".bi-pencil"`). |
| `action_name`     | `str` | Human‑readable name used for logging.       |

---

### `click_history(driver, wait)`

Clicks the **history** (clock) icon on the first row.

---

### `click_edit(driver, wait)`

Clicks the **edit** (pencil) icon on the first row.

---

### `click_view(driver, wait)`

Clicks the **view** (eye) icon on the first row.

---

### `close_modal(driver, wait)`

Closes the currently open modal by clicking the **X** icon (`.bi-x-lg`) or a **Cancel** button.

---

### `is_history_empty(driver, wait)`

Checks whether the history modal displays a “No records” message.

**Returns:** `True` if empty, `False` otherwise.

---

### `is_history_has_update(driver, wait)`

Checks whether the history modal contains an “Updated” (or similar) entry, indicating that an edit was logged.

**Returns:** `True` if an update log is found, `False` otherwise.

---

### `is_form_readonly(driver, wait)`

Verifies that the **company_name** field inside the view modal is disabled or read‑only.

**Returns:** `True` if the field is locked, `False` otherwise.

---

### `update_supplier_name_only(driver, wait, new_company_name)`

Performs a minimal update – clears the **company_name** field, types a new name, and clicks the **Update** button.

| Parameter         | Type  | Description                   |
|-------------------|-------|-------------------------------|
| `new_company_name` | `str` | New company name for the supplier. |

---

## Main Workflow Function

### `update_latest_supplier(driver, wait, original_data, updated_data)`

Orchestrates a complete update test:

1. Searches for the supplier using `original_data['company_name']`.
2. Opens the **history** modal and verifies it is empty (no prior edits).
3. Clicks **edit**, updates only the company name via `update_supplier_name_only`, and submits.
4. Waits for the SweetAlert confirmation and list‑page reload.
5. Searches again using `updated_data['company_name']`.
6. Opens **history** and verifies that the previous name appears (indicating the change was logged).
7. Clicks **view** and confirms the form is read‑only.

| Parameter      | Type   | Description                                                                 |
|----------------|--------|-----------------------------------------------------------------------------|
| `original_data` | `dict` | Dictionary containing the original supplier data (at least `"company_name"`). |
| `updated_data`  | `dict` | Dictionary containing the updated supplier data (at least `"company_name"`).  |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).  
Example output during a successful update test:

```
14:20:15 | INFO     |    ✅ Searched for: Nexus Logistics Pvt Ltd
14:20:17 | INFO     |    ✅ History button clicked
14:20:19 | INFO     |    ✅ Verified: History is empty (No records found).
14:20:20 | INFO     |    ✅ Modal closed (X button)
14:20:22 | INFO     |    ✅ Edit button clicked
14:20:29 | INFO     | ⚡ Updating company name to: Nexus Logistics Pvt Ltd UPDATED
14:20:31 | INFO     |    ✅ Company Name updated.
14:20:32 | INFO     |    ✅ 'Update' button clicked successfully.
14:20:37 | INFO     |    ✅ Clicked OK on SweetAlert confirmation.
14:20:40 | INFO     |    ✅ Searched for: Nexus Logistics Pvt Ltd UPDATED
14:20:42 | INFO     |    ✅ History button clicked
14:20:44 | INFO     |    ✅ Verified: History successfully logged the previous state.
14:20:46 | INFO     |    ✅ View button clicked
14:20:48 | INFO     |    ✅ Form is read-only (view mode).
14:20:49 | INFO     | ✅ Supplier update test completed successfully.
```

## Usage Example

```python
from privateb2b.supplier_update_section import update_latest_supplier
from data.test_data import supplier_data, updated_supplier_data

def test_supplier_update(driver, wait):
    update_latest_supplier(driver, wait, supplier_data, updated_supplier_data)
```

## Maintenance Notes

- **Action Button Selectors**: The CSS selectors `.bi-clock-history`, `.bi-pencil`, `.bi-eye` rely on Bootstrap Icons classes. If the UI switches to a different icon library, update these selectors.
- **Update Button**: The XPath `//button[contains(@class, 'submit') and contains(text(), 'Update')]` assumes the button text is exactly “Update”. Adjust if the text changes.
- **History Verification**: The current implementation checks for the **original company name** appearing in the history modal after an edit. If the history log format changes, the verification logic may need adjustment.
- **Stale Element Handling**: The retry loop in `click_action_button` ensures robustness against Angular re‑renders. Increase `attempts` or `time.sleep` values if the page is unusually slow.
```