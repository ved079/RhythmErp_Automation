# Receivable Reconciliation Test Module Reference (`receivable_reconciliation_test.py`)

This module performs a **deep‑dive audit** of the **Receivable Report** in the FPC ERP system. It navigates to the Receivable report, expands every customer row, extracts the child ledger entries, verifies that the sum of child transactions matches the parent row totals, validates the closing balance calculation, and generates a comprehensive multi‑sheet Excel audit report with screenshots and checksums.

## Purpose

- Automates end‑to‑end reconciliation of the Receivable report.
- Ensures that the displayed transaction totals (Credit/Debit) for each customer exactly match the sum of the underlying child ledger entries.
- Validates the closing balance formula: `Closing = Opening + Transactions`.
- Produces a professional audit trail including raw child data, a summary of pass/fail results, metadata, and a screenshot of the final report state.

## Functions

### UI Interaction Helpers

These functions are identical to those used in the Payable reconciliation module and handle navigation, form filling, and report viewing.

| Function | Description |
|----------|-------------|
| `select_dropdown(...)` | Universal Angular Material dropdown selection. |
| `go_to_reports_page(driver, wait)` | Navigates to the Reports hub and waits for the page to load. |
| `select_report_name(driver, wait, report_name="Receivable")` | Selects "Receivable" from the report dropdown. |
| `fill_receivable_form(driver, wait, data)` | Fills the Receivable form (currently only sets the file format). |
| `click_view(driver, wait)` | Clicks the **View** button and waits for the report table to load. |
| `click_download(driver, wait)` | Triggers the system download of the report. |

### Reconciliation & Math Helpers

| Function | Description |
|----------|-------------|
| `clean_amount(amount_str)` | Converts a string amount (with commas) to a float. |
| `set_pagination_max(driver, wait)` | Forces the report pagination to 1000 items per page to ensure all rows are rendered. |
| `extract_nested_ledger(driver, parent_row)` | Extracts opening, transaction, and closing balances from the expanded child table of a given parent row. |

### Main Executor

#### `run_receivable_reconciliation(driver, wait, data)`

Orchestrates the complete reconciliation workflow.

| Parameter | Type | Description |
|-----------|------|-------------|
| `driver` | `WebDriver` | Selenium WebDriver instance. |
| `wait` | `WebDriverWait` | WebDriverWait instance. |
| `data` | `dict` | Report parameters (must contain `file_format`). |

**Steps Performed:**

1. Navigate to the Reports page and fill the Receivable form.
2. Click **View** to generate the report.
3. Force pagination to 1000 rows.
4. Iterate over every expandable parent row (customer):
   - Extract parent totals (Opening, Transaction, Closing).
   - Expand the row and scrape all child ledger entries.
   - Calculate the sum of child credits/debits and compare with parent transaction totals.
   - Recalculate the expected closing balance and compare with the displayed closing balance.
   - Record the results and any discrepancies.
5. Perform a global header reconciliation (compare UI total transaction amount with the sum of all parent transaction nets).
6. Capture a screenshot of the final report state.
7. Compute an MD5 checksum of the results.
8. Generate a multi‑sheet Excel workbook containing:
   - **Reconciliation_Summary** – Pass/fail status for each customer and the global total.
   - **Raw_Child_Data** – Every child ledger row with running balance and transaction counter.
   - **Audit_Trail** – Timestamped log of actions.
   - **Metadata** – Timestamp, screenshot path, checksum, and test duration.
9. Trigger the system download of the report.

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).  
An internal `log_action` function also records actions to the audit trail sheet.

**Example Console Output:**

```
12:00:00 | INFO     | --- INITIATING RECEIVABLE RECONCILIATION SUITE ---
12:00:01 | INFO     |    [LOG] 2026-04-15 12:00:01 - Start reconciliation suite
12:00:02 | INFO     | Navigating to Reports page...
12:00:04 | INFO     |    🔽 Selecting Report Name: Receivable...
12:00:06 | INFO     | 📝 Filling Receivable form...
12:00:08 | INFO     |    ✅ View button clicked
12:00:11 | INFO     | ✅ Report table loaded.
12:00:12 | INFO     | 🚀 Forcing pagination to 1000 items for deep-dive audit...
12:00:14 | INFO     | ✅ Pagination set. All rows rendered.
12:00:15 | INFO     | 📊 Found 5 customers to audit. Commencing row checks...
...
12:02:00 | INFO     | ✅ Full reconciliation complete! Audit saved to: C:\...\Receivable_Audit_Reconciliation_20260415_120200.xlsx
```

## Usage Example

```python
from reports.test_cases.receivable_reconciliation_test import run_receivable_reconciliation
from data.test_data import receivable_data

def test_receivable_reconciliation(driver, wait):
    run_receivable_reconciliation(driver, wait, receivable_data)
```

## Generated Excel Report Structure

| Sheet Name | Content |
|------------|---------|
| `Reconciliation_Summary` | One row per customer with parent totals, child sums, match status, and math integrity. Includes a final global reconciliation row. |
| `Raw_Child_Data` | Every individual child ledger entry with running balance and transaction counter. |
| `Audit_Trail` | Timestamped log of all major actions performed during the test. |
| `Metadata` | Report timestamp, screenshot path, data checksum, and test duration. |

All amount columns are formatted with the Indian number format (`#,##,##0.00`).

## Maintenance Notes

- **Report Name**: The module assumes the report is named `"Receivable"`. Update the string in `select_report_name` and `fill_receivable_form` if the UI text changes.
- **Parent Row Identification**: Parent rows are located by the presence of an `<i>` element with class `fa-angle-right` or `fa-angle-down`. Update the XPath if the icon classes change.
- **Column Indices**: The parent row parsing expects columns at specific indices (e.g., customer name at index 1, opening credit at index 2, etc.). If the report layout changes, adjust the indices in the main loop.
- **File Paths**: The screenshot and Excel output directories are hardcoded to `C:\Users\vedantd\Desktop\selenium files\reports\test_cases\...`. Update these paths if the project is moved to a different location or user.
- **Pagination**: The function attempts to set the page size to 1000 via the `<select>` with ID `itemsPerPage`. If the ID changes, update the selector in `set_pagination_max`.
```