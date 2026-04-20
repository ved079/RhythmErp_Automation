# Customer Update Module Reference (`customer_update_section.py`)

This module provides a set of helper functions to perform **update tests** on existing Customer records in the FPC ERP system. It includes utilities for searching, interacting with list‑page action buttons (history, edit, view), verifying history logs, and submitting partial updates.

## Helper Functions

### `search_customer(driver, wait, search_term)`

Types the given search term into the list‑page search box and presses Enter.

| Parameter   | Type  | Description                     |
|-------------|-------|---------------------------------|
| `search_term` | `str` | Text to search for (e.g., customer company name). |

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

### `update_customer_name_only(driver, wait, new_company_name)`

Performs a minimal update – clears the **company_name** field, types a new name, and clicks the **Update** button.

| Parameter         | Type  | Description                   |
|-------------------|-------|-------------------------------|
| `new_company_name` | `str` | New company name for the customer. |

---

## Main Workflow Function

### `update_latest_customer(driver, wait, original_data, updated_data)`

Orchestrates a complete update test on the **first row** of the customer list (assumed to be the most recently created customer):

1. Waits for the table to be fully loaded.
2. Opens the **history** modal and verifies it is empty (no prior edits).
3. Clicks **edit**, updates only the company name via `update_customer_name_only`, and submits.
4. Waits for overlays to clear and the list page to stabilise.
5. Opens **history** again and verifies that the **original company name** appears (indicating the change was logged).
6. Clicks **view** and confirms the form is read‑only.
7. Closes the view modal.

| Parameter      | Type   | Description                                                                 |
|----------------|--------|-----------------------------------------------------------------------------|
| `original_data` | `dict` | Dictionary containing the original customer data (at least `"company_name"`). |
| `updated_data`  | `dict` | Dictionary containing the updated customer data (at least `"company_name"`).  |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).  
Example output during a successful update test:

```
15:10:22 | INFO     | ⚡ Running customer update test on the first row...
15:10:24 | INFO     |    ✅ History button clicked
15:10:26 | INFO     |    ✅ Verified: History is empty (No records found).
15:10:27 | INFO     |    ✅ Modal closed (X button)
15:10:29 | INFO     |    ✅ Edit button clicked
15:10:36 | INFO     | ⚡ Updating customer company name to: Nexus Trade UPDATED
15:10:38 | INFO     |    ✅ Customer Company Name updated.
15:10:39 | INFO     |    ✅ 'Update' button clicked successfully.
15:10:44 | INFO     |    ✅ History button clicked
15:10:46 | INFO     |    ✅ Verified: History successfully logged the previous state.
15:10:48 | INFO     |    ✅ View button clicked
15:10:50 | INFO     |    ✅ Form is read-only (view mode).
15:10:51 | INFO     |    ✅ Modal closed (X button)
15:10:52 | INFO     | ✅ Customer update test completed successfully.
```

## Usage Example

```python
from privateb2b.customer_update_section import update_latest_customer
from data.test_data import customer_data, updated_customer_data

def test_customer_update(driver, wait):
    # Ensure the customer list page is already loaded
    update_latest_customer(driver, wait, customer_data, updated_customer_data)
```

## Maintenance Notes

- **Row Assumption**: The function always operates on the **first row** of the customer table. This is suitable immediately after creating a new customer, but may need adjustment if the test order changes.
- **Action Button Selectors**: The CSS selectors `.bi-clock-history`, `.bi-pencil`, `.bi-eye` rely on Bootstrap Icons classes. Update them if the UI switches icon libraries.
- **Update Button**: The XPath `//button[contains(@class, 'submit') and contains(text(), 'Update')]` assumes the button text is exactly “Update”. Adjust if the text changes.
- **History Verification**: The test checks for the **original company name** inside the history modal after the update, because the history log shows the state *before* the change. If the history format changes, update the verification logic accordingly.
```