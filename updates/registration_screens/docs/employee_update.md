# Employee Update Module Reference (`employee_update_section.py`)

This module provides helper functions to perform **update tests** on existing Employee records in the FPC ERP system. It includes utilities for searching, interacting with list‑page action buttons (history, edit, view), verifying history logs, and submitting partial updates.

## Helper Functions

### `search_employee(driver, wait, search_term)`

Types the given search term into the list‑page search box and presses Enter.

| Parameter   | Type  | Description                       |
|-------------|-------|-----------------------------------|
| `search_term` | `str` | Text to search for (e.g., employee name). |

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

Verifies that the **emp_name** field (located by `formcontrolname`) inside the view modal is disabled or read‑only.

**Returns:** `True` if the field is locked, `False` otherwise.

---

### `update_employee_name_only(driver, wait, new_employee_name)`

Performs a minimal update – clears the **emp_name** field, types a new name, and clicks the **Update** button.

| Parameter         | Type  | Description                   |
|-------------------|-------|-------------------------------|
| `new_employee_name` | `str` | New name for the employee.    |

---

## Main Workflow Function

### `update_latest_employee(driver, wait, original_data, updated_data)`

Orchestrates a complete update test:

1. Searches for the employee using `original_data['employee_name']`.
2. Clicks **edit**, updates only the employee name via `update_employee_name_only`, and submits.
3. Waits for overlays to clear and the list page to stabilise.
4. Searches again using `updated_data['employee_name']`.
5. Clicks **view** and confirms the form is read‑only.

| Parameter      | Type   | Description                                                                 |
|----------------|--------|-----------------------------------------------------------------------------|
| `original_data` | `dict` | Dictionary containing the original employee data (at least `"employee_name"`). |
| `updated_data`  | `dict` | Dictionary containing the updated employee data (at least `"employee_name"`).  |

*Note:* This implementation skips the history verification steps (they are commented out) because the employee module may not fully support history tracking. The view and read‑only checks are still performed.

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).  
Example output during a successful update test:

```
16:20:15 | INFO     | ⚡ Running employee update test...
16:20:17 | INFO     |    ✅ Searched for: John Doe
16:20:19 | INFO     |    ✅ Edit button clicked
16:20:26 | INFO     | ⚡ Updating employee name to: John Doe UPDATED
16:20:28 | INFO     |    ✅ Employee Name updated.
16:20:29 | INFO     |    ✅ 'Update' button clicked successfully.
16:20:34 | INFO     |    ✅ Searched for: John Doe UPDATED
16:20:36 | INFO     |    ✅ View button clicked
16:20:38 | INFO     |    ✅ Form is read-only (view mode).
16:20:39 | INFO     |    ✅ Modal closed (X button)
16:20:40 | INFO     | ✅ Employee update test completed successfully.
```

## Usage Example

```python
from updates.employee_update_section import update_latest_employee
from data.test_data import employee_data, updated_employee_data

def test_employee_update(driver, wait):
    update_latest_employee(driver, wait, employee_data, updated_employee_data)
```

## Maintenance Notes

- **Employee Name Locator**: The function uses an XPath `//input[@formcontrolname='emp_name']` to locate the name field. Update this if the `formcontrolname` changes.
- **Action Button Selectors**: The CSS selectors `.bi-clock-history`, `.bi-pencil`, `.bi-eye` rely on Bootstrap Icons classes. Update them if the UI switches icon libraries.
- **Update Button**: The XPath `//button[contains(@class, 'submit') and contains(text(), 'Update')]` assumes the button text is exactly “Update”. Adjust if the text changes.
- **History Verification**: Currently commented out. Uncomment and adjust if employee history tracking becomes available.
```