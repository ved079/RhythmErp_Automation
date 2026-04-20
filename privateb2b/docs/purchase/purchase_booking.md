# Purchase Booking Module Reference (`purchase_booking_section.py`)

This module automates the **Purchase Booking** creation process in the FPC ERP system. It selects a supplier, picks the latest QC (which auto‑populates commodity rows), fills quantity details via modals, handles tax rates, uploads attachments, and generates an Excel audit report of the saved transaction.

## Helper Functions

### `wait_for_backdrop_to_clear(wait)`

Waits for any Angular CDK overlay backdrop to disappear. Used after modal submissions to ensure the UI is ready for the next action.

### `add_quantity_details(driver, wait, no_of_bags, quantity, row_index)`

Opens the quantity modal for a specific row, fills the bags and quantity, and submits the modal.

| Parameter | Type | Description |
|-----------|------|-------------|
| `no_of_bags` | `int` | Number of bags to enter. |
| `quantity` | `float` | Quantity to enter. |
| `row_index` | `int` | Zero‑based index of the commodity row. |

### `select_first_qc_option(driver, wait)`

Opens the QC dropdown and selects the first enabled, non‑placeholder option. Raises an exception if no valid QC is found.

### `upload_grn_attachment(driver, wait, file_path)`

Expands the **GRN details** accordion (if present) and uploads a file using the file input. Skips accordion expansion gracefully if it fails.

### `generate_pb_excel_report(scraped_items, global_total_ui)`

Generates a formatted Excel audit report containing:
- Item‑level details (rate, gross/net quantity, empty bag weight, labour, IGST, total).
- Grand totals row.
- Math audit row comparing UI global total with calculated values.

### `search_and_export_latest_pb(driver, wait, supplier_raw_name)`

Searches for the supplier on the PB list page, opens the view modal of the latest record, scrapes all item data, and calls `generate_pb_excel_report`.

## Main Functions

### `fill_purchase_booking_registration(driver, wait, data)`

Creates a standard Purchase Booking.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary matching `test_data.purchase_booking_data`. |

**Steps:**
1. Clicks **Add New Purchase Booking** (handles spinners).
2. Sets transaction date.
3. Selects supplier and first QC option.
4. Sets payment terms.
5. For each commodity:
   - Calls `add_quantity_details()`.
   - Sets Tax Rate (dropdown) and IGST Rate (input) based on item name.
6. Uploads attachment via `upload_grn_attachment()`.
7. Submits the form.
8. Calls `search_and_export_latest_pb()` to generate the audit report.

### `fill_purchase_booking_with_extra_fields(driver, wait, data)`

Extended version that also fills **Empty Bag Weight** and **Labour Charges** if present in `item_data`. Use this for tests requiring these additional fields.

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**
```
15:30:12 | INFO     | ⚡ Starting Purchase Booking Registration...
15:30:15 | INFO     |    ➡️ Forcing click on '+ Add New Purchase Booking'...
15:30:16 | INFO     |    ✅ Clicked 'Add New Purchase Booking' successfully!
15:30:17 | INFO     |    ⏳ Waiting for PB form to load...
15:30:19 | INFO     |    📅 Setting PB Transaction Date to: 14/04/2026
15:30:20 | INFO     | ➡️ Selecting QC (first valid option)
15:30:24 | INFO     |    ✅ Selected QC: QC/2026-2027/000016
15:30:27 | INFO     |    📦 Processing 1 items for Purchase Booking...
15:30:28 | INFO     |       ➡️ Setting details for Row 1: Soyabean
15:30:29 | INFO     |    ✅ Add button clicked for Row 1
15:30:31 | INFO     |    ✅ Modal submitted
15:30:33 | INFO     |          ✅ Tax Rate set to 5
15:30:34 | INFO     |          ✅ IGST Rate set to 5
15:30:35 | INFO     |    ✅ GRN details accordion expanded
15:30:36 | INFO     |    ✅ File uploaded: C:\...\blank.pdf
15:30:37 | INFO     | 📤 Submitting the Final Purchase Booking form...
15:30:38 | INFO     | ✅ Final Submit button clicked
15:30:41 | INFO     | 🚀 Purchase Booking Saved Successfully!
15:30:42 | INFO     | 🔍 Auditing finalized data for: Kavya Singh
15:30:46 | INFO     |    📊 UI Global Total: 527374.8 | PB: PURB/2026-2027/000012
15:30:48 | INFO     | 📊 Generating Enhanced Audit Report...
15:30:49 | INFO     | ✅ Formatted Audit Report saved: C:\...\PB_Audit_20260414_153049.xlsx
```

## Usage Example

```python
from privateb2b.purchase_booking_section import fill_purchase_booking_registration
from data.test_data import purchase_booking_data

def test_purchase_booking(driver, wait):
    fill_purchase_booking_registration(driver, wait, purchase_booking_data)
```

## Maintenance Notes

- **QC Selection**: The function iterates through all `mat-option` elements and picks the first one that is enabled and not a placeholder (`"Select"`). Ensure test data contains at least one valid QC for the supplier.
- **Tax Rate Mapping**: Item‑specific tax rates are hardcoded (`"Soyabean"`, `"Chana"` → 5%; `"Tur-Red"` → 0%). Update the mapping if business rules change.
- **File Upload**: The file input selector `input[type='file'][id^='bank_upload_']` relies on a dynamic ID prefix. If the UI changes the ID pattern, update the selector.
- **Excel Audit**: The report is saved in `download_files/` with a timestamp. Ensure the folder is writable and that `pandas` and `xlsxwriter` are installed.
- **Post‑Submit Wait**: `time.sleep(3)` after QC selection allows the backend to populate rows. Adjust if network latency varies.
```