
# Test Data Module Reference (`test_data.py`)

This module is the **single source of truth** for all test data used in the FPC automation suite. It generates realistic, randomized data for registrations, purchase flows, sales flows, and reports. All test scripts import their required data from here, ensuring consistency and avoiding duplication.

## How It Works

1. **Helper Functions** – Small functions that generate random names, numbers, dates, emails, etc.
2. **Shared Variables** – Generated **once per execution** and reused across multiple modules (e.g., the same supplier is used in Gate Pass, GRN, QC, and Purchase Booking).
3. **Data Dictionaries** – Structured dictionaries ready for direct use in test functions. They reference the shared variables and helper functions.

## Helper Functions (Alphabetical)

| Function | Returns | Description |
|----------|---------|-------------|
| `gen_balance_type()` | `str` | Random balance type (`All`, `Closing Balance`). |
| `gen_company()` | `str` | Random company name with suffix. |
| `gen_customer()` | `str` | Random existing customer name (from predefined list). |
| `gen_customer_po_number()` | `str` | Random PO number (`POxxxxx`). |
| `gen_due_status()` | `str` | Random due status (`All`, `Past Due`). |
| `gen_email(base_name)` | `str` | Email based on a name/company (e.g., `john.1234@example.com`). |
| `gen_empty_bag_weight()` | `float` | Random weight between 0 and 5. |
| `gen_gender()` | `str` | `Male` or `Female`. |
| `gen_group_by(transaction_type)` | `str` | Grouping option for ageing reports. |
| `gen_item()` | `str` | Random commodity (`Soyabean`, `Chana`, `Tur-Red`, `Maize-Yellow`). |
| `gen_labour_charges()` | `float` | Random labour charges (0–100). |
| `gen_level()` | `str` | Random account level for reports. |
| `gen_multiple_items()` | `list[dict]` | Generates 1 item with random bags/quantity and QC parameters. |
| `gen_name()` | `str` | Random person name (first + last). |
| `gen_no_of_bags()` | `int` | Random bags count (10–500). |
| `gen_office()` | `str` | Random Pune‑style office number. |
| `gen_pan()` | `str` | Valid‑format PAN (5 letters + 4 digits + 1 letter). |
| `gen_phone()` | `str` | Random 10‑digit Indian mobile. |
| `gen_quantity()` | `float` | Random quantity (100–500). |
| `gen_quantity_sales()` | `float` | Random sales quantity (1–5). |
| `gen_random_financial_date()` | `str` | Random date within configured range, formatted `dd/mm/yyyy`. |
| `gen_rate()` | `float` | Random rate (50000–80000). |
| `gen_sales_order_items()` | `list[dict]` | 1–3 items with quantity, rate, tax, and delivery date. |
| `gen_supplier()` | `str` | Random supplier from predefined list (includes Farmer/Supplier suffix). |
| `gen_tax_rate()` | `str` | Random tax rate (`0`, `5`, `12`, `18`). |
| `gen_transaction_type()` | `str` | `Purchase` (used for ageing reports). |
| `gen_transportation_charges()` | `float` | Random transport charges (0–1000). |
| `gen_view_type()` | `str` | `Vertical` or `Horizontal`. |
| `get_qc_parameters(item)` | `dict` | Returns QC parameters specific to the commodity. |

## Shared Purchase Flow Variables

These variables are generated **once** when the module is imported and reused by Gate Pass, GRN, QC, and Purchase Booking. This guarantees that all four modules work with the same supplier, transaction date, and items.

| Variable | Description |
|----------|-------------|
| `SHARED_SUPPLIER` | The supplier selected for the entire purchase flow. |
| `SHARED_ITEM_TYPE` | Item type (`Farm`). |
| `SHARED_TRANSACTION_DATE` | The transaction date used in all purchase modules. |
| `SHARED_ITEMS_LIST` | List of items (with bags, quantity, QC parameters) used across Gate Pass, QC, and Purchase Booking. |

## Dynamic Variables (One‑Time Generation)

These are generated once and used to build the registration data dictionaries.

| Variable | Used In |
|----------|---------|
| `f_name` | Farmer name |
| `s_company` | Supplier company name |
| `s_pan` / `s_gstin` | Supplier PAN / GSTIN |
| `a_name` | Agent name |
| `c_company` / `c_pan` | Customer company / PAN |
| `e_name` | Employee name |
| `current_transaction_type` | Ageing report |

## Data Dictionaries – Quick Reference

### Registration Dictionaries

| Dictionary | Used In Test Module |
|------------|---------------------|
| `farmer_data` | `farmer_section.py` |
| `supplier_data` | `supplier_section.py` |
| `agent_data` | `agent_section.py` |
| `customer_data` | `customer_section.py` |
| `employee_data` | `employee_section.py` |

Each also has an `updated_*` variant (e.g., `updated_supplier_data`) for edit tests.

### Purchase Flow Dictionaries

| Dictionary | Used In Test Module |
|------------|---------------------|
| `gatepass_data` | `gatepass_test.py` |
| `grn_data` | `grn_test.py` |
| `qc_data` | `qc_test.py` |
| `purchase_booking_data` | `purchase_booking_test.py` |

### Sales Flow Dictionaries

| Dictionary | Used In Test Module |
|------------|---------------------|
| `sales_order_data` | `sales_order_test.py` |
| `dispatch_note_data` | `dispatch_test.py` |
| `invoice_data` | `invoice_test.py` |
| `receipt_data` | `receipt_test.py` |

### Report Dictionaries

| Dictionary | Report |
|------------|--------|
| `trial_balance_data` | Trial Balance |
| `balance_sheet_data` | Balance Sheet |
| `profit_loss_data` | Profit & Loss |
| `payable_data` | Payable Report |
| `receivable_data` | Receivable Report |
| `inventory_report_data` | Inventory Report |
| `inventory_summary_data` | Inventory Summary |
| `ageing_report_data` | Ageing Report |
| `ledger_enquiry_data` | Ledger Enquiry |
| `day_book_data` | Day Book |
| `sales_order_status_data` | Sales Order Status |
| `supplier_balance_data` | Supplier Balance |
| `customer_balance_data` | Customer Balance |
| `statistics_data` | Statistics |
| `weighted_average_rate_data` | Weighted Average Rate |

## Usage in Test Scripts

```python
from data.test_data import sales_order_data, dispatch_note_data

def test_sales_order():
    fill_sales_order(driver, wait, sales_order_data)
```

## Maintenance Notes

- **Adding a new field** – Add the key to the appropriate dictionary. If it needs dynamic generation, create a helper function.
- **Changing shared flow** – Modify `SHARED_*` variables or the functions that generate them (e.g., `gen_multiple_items`).
- **Updating QC parameters** – Edit `get_qc_parameters()` when commodity‑specific parameters change.
- **Hardcoded file paths** – Update the paths in `supplier_data`, `agent_data`, `customer_data`, etc., if the project location changes. (Consider using relative paths in the future.)
```