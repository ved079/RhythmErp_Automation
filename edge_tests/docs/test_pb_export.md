# Purchase Booking Export Test (`test_pb_export.py`)

This test performs a **standalone search and export** of the latest Purchase Booking for the shared supplier. It bypasses the creation flow and directly validates the search, view, and Excel audit report generation functionality on existing data.

## Purpose

- Verifies that the `search_and_export_latest_pb` function works correctly on the Purchase Booking list page.
- Confirms that the supplier search filters the table and that the view modal opens without errors.
- Ensures the Excel audit report is generated successfully for an existing Purchase Booking.

## Workflow

1. **Login** to the ERP using `auth_section.perform_login`.
2. **Navigate** directly to the Purchase Booking list page via `nav_section.go_to_purchase_booking_page`.
3. **Search and Export** using `purchase_booking_section.search_and_export_latest_pb`, passing the shared supplier name (`SHARED_SUPPLIER`).
4. The function automatically:
   - Types the supplier name into the search box and presses Enter.
   - Clicks the **View** button on the first row.
   - Waits for the view modal to load.
   - Scrapes all item details and the global total.
   - Generates the formatted Excel audit report in the `download_files/` folder.
5. Logs success or failure.

## Logging

The test uses a module‑level logger. Example output:

```
10:45:00 | INFO     | Step 1: Logging in...
10:45:05 | INFO     | 
Step 2: Navigating to Purchase Booking page...
10:45:08 | INFO     | 
Step 3: Searching and Exporting...
10:45:12 | INFO     | 🔍 Auditing finalized data for: Kavya Singh
10:45:15 | INFO     |    📊 UI Global Total: 527374.8 | PB: PURB/2026-2027/000012
10:45:18 | INFO     | 📊 Generating Enhanced Audit Report...
10:45:20 | INFO     | ✅ Formatted Audit Report saved: C:\...\PB_Audit_20260415_104520.xlsx
10:45:20 | INFO     | 
🎉 Test Case Completed Successfully!
10:45:20 | INFO     | 
Closing browser...
```

## Usage

Run the test directly:

```bash
python test_pb_export.py
```

Or with pytest:

```bash
pytest test_pb_export.py -v
```

## Maintenance Notes

- **Shared Supplier**: The test uses `SHARED_SUPPLIER` from `test_data`. Ensure that at least one Purchase Booking exists for this supplier in the system.
- **Search Box Selector**: The function `search_and_export_latest_pb` relies on `input.search-field`. Update if the UI changes.
- **View Button**: The view button is located by the eye icon (`bi-eye`). If the icon class changes, update the XPath in `purchase_booking_section`.
- **Excel Report**: The generated report is saved in `download_files/` with a timestamp. Ensure the folder is writable.
```