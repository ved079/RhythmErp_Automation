# Helper Functions Reference (`helper.py`)

This module provides reusable utility functions for interacting with the FPC UI. It handles Angular Material dropdowns, text/date inputs, and form submission reliably.

## Functions

### `select_dropdown(driver, wait, value=None, control_name=None, label_text=None, control_id=None, searchable=False)`

Selects an option from an Angular Material `mat-select` dropdown.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | `str` | Text of the option to select (partial match allowed). |
| `control_name` | `str` | `formcontrolname` attribute of the `mat-select`. |
| `label_text` | `str` | Text of the `<mat-label>` associated with the dropdown. |
| `control_id` | `str` | HTML `id` attribute of the `mat-select`. |
| `searchable` | `bool` | If `True`, types `value` into the overlay search box before selecting. If search box not found, skips filtering gracefully. |

**Behavior:**
- Scrolls the dropdown into view and clicks it.
- Waits for the overlay pane to appear.
- If `searchable=True`, attempts to filter by typing in the search input.
- Finds the option containing `value` (case‑insensitive, partial match) and clicks it.
- Waits for the overlay to close.

**Examples:**
```python
# By formcontrolname, with search
select_dropdown(driver, wait, value="Maharashtra", control_name="state", searchable=True)

# By label text, no search
select_dropdown(driver, wait, value="Male", label_text="Gender", searchable=False)

# By HTML id
select_dropdown(driver, wait, value="Active", control_id="status", searchable=False)
```

---

### `fill_input(driver, wait, value, control_name=None, control_id=None)`

Fills a text input, number field, or Angular Material datepicker.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | `str` | Text or number to enter. |
| `control_name` | `str` | `formcontrolname` attribute of the `<input>`. |
| `control_id` | `str` | HTML `id` attribute of the `<input>`. |

**Behavior:**
- Locates the input element.
- Scrolls it into view and clicks to focus (bypassing any floating labels).
- Clears existing content using `Ctrl+A` + `Backspace`.
- Types the `value`.
- Presses `Tab` to force Angular change detection (critical for datepickers).

**Examples:**
```python
# Fill a regular input
fill_input(driver, wait, "John Doe", control_id="name")

# Fill a datepicker
fill_input(driver, wait, "10/04/2026", control_name="transaction_date")
```

---

### `click_submit(driver, wait)`

Clicks the form's submit button using JavaScript to avoid interception by Angular Material overlays.

**Parameters:** (none beyond driver/wait)

**Behavior:**
- Waits for a `<button class="submit">` to be clickable.
- Scrolls it into view.
- Clicks via JavaScript.

**Example:**
```python
click_submit(driver, wait)
```

---

## Logging

All functions log their actions using a module-level logger with timestamps and severity levels.

**Example Output:**
```
10:23:45 | INFO     |    ✅ Filled transaction_date: 10/04/2026
10:23:46 | INFO     | ✅ Submit button clicked
10:23:47 | ERROR    | ❌ Failed to fill email: element not found
```

- `INFO` – Normal successful actions.
- `ERROR` – Failures that raise exceptions.

---

## Error Handling

- If any function fails, it logs an error, saves a screenshot (e.g., `fill_error_email.png`), and raises the exception.
- `select_dropdown` gracefully handles missing search inputs (when `searchable=True` but no search box exists) by skipping filtering instead of crashing.

---

## Usage in Test Scripts

```python
from common.helper import select_dropdown, fill_input, click_submit

# Example usage inside a test
select_dropdown(driver, wait, value="Vedant Enterprises", control_name="customer_ref_id", searchable=True)
fill_input(driver, wait, "10/04/2026", control_name="transaction_date")
click_submit(driver, wait)
```
```