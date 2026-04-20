# Employee Registration Module Reference (`employee_section.py`)

This module automates the **Employee Registration** form in the FPC ERP system. It fills the employee's personal details, designation, and role, then submits the form.

## Main Function

### `fill_employee_registration(driver, wait, data)`

Orchestrates the complete employee registration workflow.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary matching the structure of `test_data.employee_data`. |

**Steps Performed:**

1. **Wait for Form Load**  
   - Waits for the `emp_name` input (using `formcontrolname`) to confirm the form is ready.

2. **Fill Employee Details**  
   - Employee Name (`control_name="emp_name"`)  
   - Email (`control_name="email"`)  
   - Phone (`control_name="phone"`)  

3. **Select Dropdowns**  
   - Designation (`control_name="designation"`, searchable)  
   - Maker/Checker (`control_name="maker_checker"`, searchable)  

4. **Submission**  
   - Clicks the submit button via `click_submit(driver, wait)`  
   - Waits 3 seconds and logs completion

## Logging

All actions are logged with timestamps and severity levels (`INFO`).

**Example Console Output:**
```
10:54:54 | INFO     | ⚡ Starting Employee Registration...
10:54:55 | INFO     |    ✅ Filled emp_name: Kavya Mercer
10:54:56 | INFO     |    ✅ Filled email: kavya.7994@example.com
10:54:57 | INFO     |    ✅ Filled phone: 9395599029
10:54:59 | INFO     | 📤 Submitting the form...
10:55:00 | INFO     | ✅ Submit button clicked
10:55:03 | INFO     | 🚀 Employee Registration Completed Successfully!
```

## Usage Example

```python
from Registration.employee_section import fill_employee_registration
from data.test_data import employee_data

def test_employee(driver, wait):
    fill_employee_registration(driver, wait, employee_data)
```

## Maintenance Notes

- **Form Load Detection**: The function uses `//input[@formcontrolname='emp_name']` to verify the form is visible. Update the XPath if the field name changes.
- **Dropdowns**: Both dropdowns use `searchable=True`. If the dropdowns are not searchable in the UI, change to `searchable=False` to avoid unnecessary attempts to find a search input.
- **Submission Wait**: The 3‑second sleep after submit is a simple wait for the success response. Consider replacing with a `WebDriverWait` for a success indicator (e.g., list page table) if the page load time varies.
```