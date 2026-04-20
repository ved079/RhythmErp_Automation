# Report Reconciliation Runner Reference (`run_reconciliation_reports.py`)

This script is the dedicated entry point for executing the **Payable** and **Receivable** deep‑dive reconciliation tests. It handles login, browser configuration, download preferences, and runs both report audit suites sequentially.

## Purpose

- Authenticates with the FPC ERP system using credentials from `config.py`.
- Configures Chrome with custom download settings (saves files to a local `downloads/` folder).
- Executes the following reconciliation modules in order:
  - Payable Reconciliation (`run_payable_reconciliation`)
  - Receivable Reconciliation (`run_receivable_reconciliation`)
- Logs progress and saves a screenshot if a critical error occurs.

## Structure

| Section | Description |
|---------|-------------|
| **Path Setup** | Inserts the project root into `sys.path` to allow absolute imports of `common`, `data`, and `reports`. |
| **Logger Configuration** | Sets up a module‑level logger with timestamps. |
| **Chrome Options** | Configures the download directory, disables download prompts, and enables safe browsing bypass. |
| **Imports** | Loads authentication, configuration, test data, and the two reconciliation functions. |
| **`main` block** | Orchestrates login and sequential execution of the reconciliation tests inside a try‑except block. |
| **Cleanup** | The `finally` block ensures the browser is closed. |

## Reconciliation Modules Called

| Function | Module File | Purpose |
|----------|-------------|---------|
| `run_payable_reconciliation` | `payable_recouncliation_test.py` | Audits the Payable report, expanding all supplier rows and validating child ledger sums. |
| `run_receivable_reconciliation` | `receivable_reconciliation_test.py` | Audits the Receivable report, expanding all customer rows and validating child ledger sums. |

## How to Run

1. Ensure the virtual environment is activated.
2. Run the script from the project root:
   ```powershell
   python reports\test_cases\run_reconciliation_reports.py
   ```

## Enabling/Disabling Tests

To skip a test, simply **comment out** its corresponding line in the `try` block. For example:

```python
# run_payable_reconciliation(driver, wait, payable_data)   # Skipped
run_receivable_reconciliation(driver, wait, receivable_data)  # Executed
```

## Logging Output

The script uses the `logging` module with a console handler. Output includes timestamps and severity levels (`INFO`, `ERROR`).

**Example Console Output:**

```
12:00:00 | INFO     | 🚀 LOGGING INTO FPC PORTAL...
12:00:05 | INFO     | ✅ Login Successful
12:00:05 | INFO     | 
▶️ [RUNNING TEST 1]: Payable Deep-Dive Reconciliation
12:00:06 | INFO     | --- INITIATING PAYABLE RECONCILIATION SUITE ---
...
12:02:30 | INFO     | ✅ Full reconciliation complete! Audit saved to: C:\...\Payable_Audit_Reconciliation_20260415_120230.xlsx
12:02:30 | INFO     | --- INITIATING RECEIVABLE RECONCILIATION SUITE ---
...
12:04:45 | INFO     | ✅ Full reconciliation complete! Audit saved to: C:\...\Receivable_Audit_Reconciliation_20260415_120445.xlsx
12:04:45 | INFO     | ✅ [PAYABLE RECONCILIATION COMPLETED]
12:04:45 | INFO     | 
🏆 ALL REPORT TEST SUITES EXECUTED SUCCESSFULLY!
12:04:45 | INFO     | 
🧹 Cleaning up and closing browser...
```

## Maintenance Notes

- **ChromeDriver**: Ensure the installed ChromeDriver matches your Chrome browser version. The script uses `webdriver.Chrome()` without explicit driver path, relying on `chromedriver` being in PATH or managed by `webdriver-manager`.
- **Download Directory**: The script creates a `downloads` subfolder relative to the script's location. Update the `download_dir` variable if a different location is needed.
- **Adding New Reconciliation Tests**: Import the new test function and add a call to it inside the `try` block. Ensure the corresponding test data dictionary is imported from `data.test_data`.
- **Error Handling**: If a critical error occurs, a screenshot named `reports_runner_fatal_error.png` is saved in the current working directory.
```