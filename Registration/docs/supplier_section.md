
# Supplier Registration Module Reference (`supplier_section.py`)

This module automates the **Supplier Registration** form in the FPC ERP system. It fills basic company information, expands and populates additional details, handles two address blocks (billing and shipping), and uploads a bank proof file before final submission.

## Helper Functions

### `expand_section(driver, wait, section_text)`

Expands a collapsible accordion section by clicking its header.

| Parameter | Type | Description |
|-----------|------|-------------|
| `section_text` | `str` | Text contained in the `<strong>` element of the accordion header. |

**Behavior:**  
- Locates the header using the XPath `//div[@class='header accordian']//strong[contains(text(), '{section_text}')]`.  
- Scrolls into view and clicks.  
- Logs success or a warning if the section cannot be expanded.

---

### `fill_address(driver, wait, index, address_data)`

Fills an address block (billing or shipping) at a specific index.

| Parameter | Type | Description |
|-----------|------|-------------|
| `index` | `int` | `0` for billing address, `1` for shipping address. |
| `address_data` | `dict` | Dictionary containing address fields (`address_type`, `state`, `district`, `taluka`, `village`, `pin_code`, `address`, optional `country`). |

**Behavior:**  
- Selects **Address Type** (`control_id="address_type{index}"`).  
- Fills the **Address** textarea (located by `name="Address"` at the given index).  
- Selects **State**, **District**, **Taluka**, **Village** sequentially (IDs: `state_ref_id_id{index}`, `district_ref_id_id{index}`, `sub_district_ref_id_id{index}`, `village_ref_id{index}`).  
- Fills **Pincode** (ID: `pin_code` at index).  
- Optionally selects **Country** if present in the data.

---

### `fill_bank_details(driver, wait, bank_data)`

Fills the bank details section and uploads a bank proof file.

| Parameter | Type | Description |
|-----------|------|-------------|
| `bank_data` | `dict` | Dictionary containing bank fields (`bank_name`, `branch_name`, `ifsc`, `account_type`, `account_holder_name`, `account_number`, `bank_proof`, `bank_proof_file`). |

**Behavior:**  
- Fills **Bank Name**, **Branch Code**, **IFSC Code**, **Account Holder Name**, **Account Number** (all by ID).  
- Selects **Account Type** (`control_id="account_type0"`) and **Bank Proof** (`control_id="bank_doc_id0"`).  
- If `bank_proof_file` is provided, attempts to locate a file input using multiple fallback selectors and uploads the file.  
- Logs a warning if the file input cannot be found or upload fails.

---

## Main Function

### `fill_supplier_registration(driver, wait, data)`

Orchestrates the complete supplier registration workflow.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary matching the structure of `test_data.supplier_data`. |

**Steps Performed:**

1. **Basic Information** (already visible)  
   - Supplier Status (`supplier_status`)  
   - Company Name (`company_name`)  
   - PO Type (`po_type_ref_id`)  
   - Email (`email_id`), Mobile (`mobile_no`), PAN (`pan_no`)  
   - Ownership Status (`ownership_status_ref_id`)

2. **Additional Details** (expands accordion)  
   - Contact Person Name (`display_name_as`)  
   - Office Number (`office_no`)  
   - Payment Terms, Delivery Terms, Mode of Delivery (if provided)

3. **Supplier Details** (expands accordion)  
   - Fills **Billing Address** using `fill_address(…, index=0)`  
   - Clicks the **"+" button** (`button.apply-button`) to add a second address block  
   - Fills **Shipping Address** using `fill_address(…, index=1)`  
   - Enters **GSTIN** if provided

4. **Supplier Bank Details** (expands accordion)  
   - Calls `fill_bank_details()` to populate bank fields and upload proof

5. **Submission**  
   - Clicks the submit button via `click_submit(driver, wait)`  
   - Waits briefly and logs completion

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`).

**Example Console Output:**
```
10:23:45 | INFO     | ⚡ Starting Supplier Registration...
10:23:47 | INFO     |    ✅ Expanded 'Additional Details' section
10:23:52 | INFO     |    ✅ Expanded 'Supplier Details' section
10:23:55 | INFO     |    📍 Filling Address Block 0...
10:24:00 | INFO     |    ✅ Address Block 0 filled.
10:24:05 | INFO     |    📍 Filling Address Block 1...
10:24:10 | INFO     |    ✅ Address Block 1 filled.
10:24:12 | INFO     |    ✅ Expanded 'Supplier Bank Details' section
10:24:14 | INFO     | 🏦 Filling Bank Details...
10:24:16 | INFO     | 📂 Uploading bank proof file...
10:24:18 | INFO     |    Found file input using: input[type='file']
10:24:19 | INFO     |    ✅ Uploaded: C:\...\blank.pdf
10:24:22 | INFO     | 🏦 Bank details filled.
10:24:23 | INFO     | 📤 Submitting the form...
10:24:25 | INFO     | ✅ Submit button clicked
10:24:27 | INFO     | 🚀 Supplier Registration Completed Successfully!
```

## Usage Example

```python
from Registration.supplier_section import fill_supplier_registration
from data.test_data import supplier_data

def test_supplier(driver, wait):
    fill_supplier_registration(driver, wait, supplier_data)
```

## Maintenance Notes

- **Accordion Headers**: The text passed to `expand_section` must match exactly the `<strong>` content (e.g., `"Additional Details"`, `"Supplier Details"`, `"Supplier Bank Details"`). Update if the UI text changes.
- **Address Indexes**: The billing address is always index `0`. The shipping address becomes index `1` after clicking the **"+" button**. Ensure the UI adds exactly one new block per click.
- **File Upload**: The function attempts multiple selectors to find the file input. If a new design changes the input placement, add the new selector to the `selectors` list.
- **Waits**: `time.sleep(4)` calls are placed after expanding sections to allow Angular animations to complete. Adjust if the UI becomes faster or slower.
```