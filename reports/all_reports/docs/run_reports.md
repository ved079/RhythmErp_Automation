# Report Runner Reference (`run_report.py`)

This script is the primary entry point for executing **all FPC report modules** in sequence. It handles login, browser configuration, download preferences, and runs a comprehensive suite of financial and inventory reports.

## Purpose

- Authenticates with the FPC ERP system using credentials from `config.py`.
- Configures Chrome with custom download settings (saves files to `downloads/` folder).
- Executes the following report modules in order (some commented out):
  - Profit & Loss
  - Payable Report
  - Receivable Report
  - Inventory Report
  - Inventory Summary
  - Ledger Enquiry
  - Day Book
  - Sales Order Status
  - Supplier Balance
  - Customer Balance
  - Statistics
  - Weighted Average Rate
- Logs errors and saves screenshots if a report fails.

## Structure

| Section | Description |
|---------|-------------|
| **Path Setup** | Inserts the project root into `sys.path` to allow absolute imports of `common`, `reports`, and `data`. |
| **Chrome Options** | Configures download directory, disables download prompts, and enables safe browsing bypass. |
| **Imports** | Loads all report modules using aliases (`run_trial_balance`, `run_balance_sheet`, etc.) and imports test data dictionaries. |
| **`set_download_preferences()`** | Uses Chrome DevTools Protocol to set the download path. |
| **`main()`** | Orchestrates login and sequential report execution inside a try‑except block. |
| **Cleanup** | The `finally` block waits 3 seconds and closes the browser. |

## Report Module Aliases

| Alias | Module File | Report Name |
|-------|-------------|-------------|
| `run_trial_balance` | `trial_balance.py` | Trial Balance |
| `run_balance_sheet` | `balance_sheet.py` | Balance Sheet |
| `run_profit_loss` | `profit_loss.py` | Profit & Loss |
| `run_payable` | `payable.py` | Payable Report |
| `run_rec` | `receivable.py` | Receivable Report |
| `ir` | `inventory_report1.py` | Inventory Report |
| `ir1` | `inventory_summary.py` | Inventory Summary |
| `ir2` | `ageing_report.py` | Ageing Report |
| `ir3` | `ledger_enquiry.py` | Ledger Enquiry |
| `ir4` | `day_book.py` | Day Book |
| `ir5` | `sales_order_status.py` | Sales Order Status |
| `ir6` | `supplier_balance.py` | Supplier Balance |
| `ir7` | `customer_balance.py` | Customer Balance |
| `ir8` | `statistics.py` | Statistics |
| `ir9` | `weighted_average_rate.py` | Weighted Average Rate |

## How to Run

1. Ensure the virtual environment is activated.
2. Run the script from the project root:
   ```powershell
   python reports\run_report.py
   ```

## Enabling/Disabling Reports

To skip a report, simply **comment out** its corresponding line in `main()`. For example:

```python
# run_trial_balance(driver, wait, trial_balance_data)   # Skipped
run_profit_loss(driver, wait, profit_loss_data)          # Executed
```

## Logging Output

The script uses `print()` statements (not the `logging` module). Output appears in the console as plain text.

**Example Console Output:**
```
🔐 Logging in...
✅ Login Successful
Navigating to Reports page...
   ✅ Success overlays cleared.
   ✅ Clicked All Reports menu
✅ Reports page loaded.
...
✅ Download triggered successfully.
```

## Maintenance Notes

- **ChromeDriver**: Ensure the installed ChromeDriver matches your Chrome browser version. The script uses `webdriver.Chrome()` without explicit driver path, relying on `chromedriver` being in PATH or managed by `webdriver-manager`.
- **Download Directory**: The script uses `C:\Users\vedantd\Downloads` for downloads. Update the `download.default_directory` preference in `chrome_options` if you need a different location.
- **Adding New Reports**: Import the new report module with an alias, then add a call to its `run()` function inside `main()`. Ensure the corresponding test data dictionary is imported from `data.test_data`.
- **Error Handling**: If a report fails, the script saves a screenshot named `trial_balance_error.png` (this name is generic; consider renaming dynamically based on the failing report).
```