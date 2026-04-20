# Global Excel Download Test (`test_download_all_excel_files.py`)

This test systematically navigates to the **list page** of every major module in the FPC ERP system and verifies that the **"Download Excel"** button works correctly, producing a non‑empty `.xlsx` or `.xls` file.

## Purpose

- Validate the Excel export functionality across **all registration and transaction modules** (Supplier, Agent, Customer, Employee, Purchase Order, Gate Pass, GRN, QC, Purchase Booking, Sales Order, Lot Creation, Dispatch Note, Invoice, Receipt).
- Ensure that the download is triggered successfully and the file is created with data.
- Provide a single automated check for report/export availability without needing to create new records each time.

## Workflow

1. **Login** using `auth_section.perform_login`.
2. **Iterate** over a predefined list of modules, each with a dedicated navigation function that:
   - Navigates directly to the **list page** (not the creation form).
   - Handles menu expansion (B2B → Purchase or Sales) automatically.
   - Waits for the data table to be present.
3. **Locate** the "Download Excel" button (using two fallback XPath selectors).
4. **Clear** any previous `.xlsx`/`.xls` files from the download directory.
5. **Click** the download button via JavaScript to avoid interception.
6. **Wait** for a new Excel file to appear (up to 30 seconds).
7. **Assert** that the downloaded file has a non‑zero size.
8. **Delete** the file to keep the directory clean.
9. **Log** success for each module and a final summary.

## Helper Functions

| Function | Description |
|----------|-------------|
| `set_download_preferences(driver, download_dir)` | Configures Chrome to download files to a specific folder without prompting. |
| `wait_for_download(download_dir, timeout=30)` | Polls the download directory until a new Excel file appears, then returns its full path. |
| `close_overlays(driver, wait)` | Closes any lingering CDK overlays or SweetAlert popups that might block clicks. |
| `smart_click(driver, wait, element)` | Scrolls the element into view and clicks it using JavaScript. |
| `is_element_visible(driver, by, value)` | Returns `True` if the element is present and displayed. |

### Navigation Functions

Each `go_to_xxx_list` function follows the same pattern:
- Logs the navigation step.
- Closes any open overlays.
- Scrolls to the top.
- Clicks the appropriate menu link, expanding parent menus (B2B, Purchase, Sales) if necessary.
- Waits for the `<table>` element to confirm the list page is fully loaded.

## Logging

All actions are logged with timestamps and severity levels. Example output for a single module:

```
10:30:00 | INFO     |    Navigating to Supplier list...
10:30:02 | INFO     |    ✅ Supplier list loaded.
10:30:02 | INFO     | 
📁 Testing Excel download for: Supplier
10:30:05 | INFO     |    ✅ Downloaded: Supplier.xlsx (12456 bytes)
```

## Usage

Run the test directly:

```bash
python test_download_all_excel_files.py
```

## Maintenance Notes

- **Menu Structure**: The navigation functions assume the side menu contains links with exact text (e.g., `"Supplier"`, `"Gate Pass"`, `"Sales Order"`). If the UI text changes, update the `By.LINK_TEXT` locators.
- **Download Button XPath**: Two selectors are tried:
  1. `//button[.//span[text()='Download Excel']]` (exact match inside a span)
  2. `//button[contains(.,'Download Excel')]` (loose match)
  If the button design changes, adjust these XPaths.
- **Download Directory**: Files are saved to a `downloads` folder in the current working directory. Ensure the test has write permissions.
- **File Cleanup**: The test deletes each file after verifying its size. If you need to keep the files for inspection, comment out the `os.remove(downloaded_file)` line.
```