# Agent Update Module Reference (`agent_update_section.py`)

This module provides a set of helper functions to perform **update tests** on existing Agent records in the FPC ERP system. It includes utilities for searching, interacting with list‑page action buttons (history, edit, view), verifying history logs, and submitting partial updates.

## Helper Functions

### `search_agent(driver, wait, search_term)`

Types the given search term into the list‑page search box and presses Enter.

| Parameter   | Type  | Description                     |
|-------------|-------|---------------------------------|
| `search_term` | `str` | Text to search for (e.g., agent name). |

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

Verifies that the **agent_name** field inside the view modal is disabled or read‑only.

**Returns:** `True` if the field is locked, `False` otherwise.

---

### `update_agent_name_only(driver, wait, new_agent_name)`

Performs a minimal update – clears the **agent_name** field, types a new name, and clicks the **Update** button.

| Parameter      | Type  | Description                |
|----------------|-------|----------------------------|
| `new_agent_name` | `str` | New name for the agent.    |

**Note:** The Update button is located with a strict XPath that targets only buttons inside the `.footer .right` container to avoid ambiguity.

---

## Main Workflow Function

### `update_latest_agent(driver, wait, original_data, updated_data)`

Orchestrates a complete update test:

1. Searches for the agent using `original_data['agent_name']`.
2. Opens the **history** modal and verifies it is empty (no prior edits).
3. Clicks **edit**, updates only the agent name via `update_agent_name_only`, and submits.
4. Waits for the SweetAlert confirmation and list‑page reload.
5. Searches again using `updated_data['agent_name']`.
6. Opens **history** and verifies that the **original name** appears (indicating the change was logged).
7. Clicks **view** and confirms the form is read‑only.

| Parameter      | Type   | Description                                                                 |
|----------------|--------|-----------------------------------------------------------------------------|
| `original_data` | `dict` | Dictionary containing the original agent data (at least `"agent_name"`).     |
| `updated_data`  | `dict` | Dictionary containing the updated agent data (at least `"agent_name"`).      |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).  
Example output during a successful update test:

```
16:05:12 | INFO     |    ✅ Searched for: Apex Trade Networks
16:05:14 | INFO     |    ✅ History button clicked
16:05:16 | INFO     |    ✅ Verified: History is empty.
16:05:17 | INFO     |    ✅ Modal closed (X button)
16:05:19 | INFO     |    ✅ Edit button clicked
16:05:26 | INFO     | ⚡ Updating agent name to: Apex Trade Networks UPDATED
16:05:28 | INFO     |    ✅ Agent Name updated.
16:05:29 | INFO     |    ✅ 'Update' button clicked successfully.
16:05:34 | INFO     |    ✅ Searched for: Apex Trade Networks UPDATED
16:05:36 | INFO     |    ✅ History button clicked
16:05:38 | INFO     |    ✅ Verified: History successfully logged the previous state.
16:05:40 | INFO     |    ✅ View button clicked
16:05:42 | INFO     |    ✅ Form is read-only (view mode).
16:05:43 | INFO     | ✅ Agent update test completed successfully.
```

## Usage Example

```python
from privateb2b.agent_update_section import update_latest_agent
from data.test_data import agent_data, updated_agent_data

def test_agent_update(driver, wait):
    update_latest_agent(driver, wait, agent_data, updated_agent_data)
```

## Maintenance Notes

- **Action Button Selectors**: The CSS selectors `.bi-clock-history`, `.bi-pencil`, `.bi-eye` rely on Bootstrap Icons classes. Update them if the UI switches icon libraries.
- **Update Button**: The strict XPath `//div[contains(@class, 'footer')]//div[contains(@class, 'right')]//button[contains(@class, 'submit') and contains(., 'Update')]` ensures the correct button is clicked even if multiple “Update” buttons exist on the page. Adjust if the footer structure changes.
- **History Verification**: The test checks for the **original agent name** inside the history modal after the update, because the history log shows the state *before* the change. If the history format changes, update the verification logic accordingly.
- **Stale Element Handling**: The retry loop in `click_action_button` ensures robustness against Angular re‑renders. Increase `attempts` or `time.sleep` values if the page is unusually slow.
```