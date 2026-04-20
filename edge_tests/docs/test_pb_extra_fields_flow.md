# Purchase Flow with Extra Fields Test (`test_purchase_extra_fields.py`)

This test runs the **full purchase flow** (Gate Pass → QC → Purchase Booking) with dynamically added **Empty Bag Weight** and **Labour Charges** to each commodity. It verifies that the Purchase Booking audit report correctly captures and calculates these extra fields.

## Purpose

- Validates that the Purchase Booking module correctly handles optional fields (empty bag weight, labour charges) when they are present in the test data.
- Ensures the end‑to‑end purchase flow remains functional when these extra fields are supplied.
- Generates the enhanced Excel audit report to confirm mathematical reconciliation of gross/net quantities and labour charges.

## Workflow

1. **Deep copy** the base test data dictionaries to avoid mutating the original shared data.
2. **Enrich Gate Pass items** with randomly generated `empty_bag_weight` and `labour_charges` (using `gen_empty_bag_weight()` and `gen_labour_charges()`).
3. **Sync data** across Gate Pass, QC, and Purchase Booking:
   - Purchase Booking receives the same enriched items list.
   - QC items are rebuilt with the correct `qc_parameters` for each commodity.
4. **Login** and execute the purchase modules sequentially:
   - Gate Pass creation
   - (GRN commented out)
   - QC creation
   - Purchase Booking creation using **`fill_purchase_booking_with_extra_fields`** (the variant that fills the extra fields).
5. The Purchase Booking module automatically generates the Excel audit report.

## Functions Called

| Module | Function | Purpose |
|--------|----------|---------|
| `auth_section` | `perform_login` | Log into the ERP. |
| `nav_section` | `go_to_gatepass_page`, `go_to_qc_page`, `go_to_purchase_booking_page` | Navigate to each form. |
| `gatepass_section` | `fill_gatepass_registration` | Create Gate Pass. |
| `qc_section` | `fill_qc_registration` | Create QC. |
| `purchase_booking_section` | `fill_purchase_booking_with_extra_fields` | Create Purchase Booking **with** empty bag weight and labour charges. |

## Logging

The test uses a module‑level logger. Example output:

```
10:30:00 | INFO     | 
🔐 Logging in...
10:30:05 | INFO     | 
📦 Creating Gate Pass...
10:30:10 | INFO     |    🧪 Added to Soyabean: Empty Bag = 2.34, Labour = 45.67
10:30:20 | INFO     | 
🔬 Creating QC...
10:30:35 | INFO     | 
📑 Creating Purchase Booking (with AUDIT fields)...
10:31:00 | INFO     | 
✅ Full purchase flow with extra fields completed and Excel generated.
```

## Usage

Run the test directly:

```bash
python test_purchase_extra_fields.py
```

## Maintenance Notes

- **Data Copying**: `copy.deepcopy` ensures the original `SHARED_ITEMS_LIST` and other shared data remain unchanged for subsequent tests.
- **GRN Skipped**: The GRN steps are commented out. Uncomment if GRN is required in the flow.
- **Extra Fields Function**: The test deliberately calls `fill_purchase_booking_with_extra_fields` rather than the standard registration function. Ensure this function exists in `purchase_booking_section`.
- **Transaction Date**: `SHARED_TRANSACTION_DATE` is explicitly assigned to all three modules to maintain consistency.
```