# Customer Registration Module Reference (`customer_section.py`)

This module automates the **Customer Registration** form in the FPC ERP system. It fills company information, expands and populates additional business details, handles two address blocks (billing and shipping), and uploads a bank proof file before submission.

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

### `fill_address_customer(driver, wait, index, address_data)`

Fills an address block (billing or shipping) at a specific index.

| Parameter | Type | Description |
|-----------|------|-------------|
| `index` | `int` | `0` for billing address, `1` for shipping address. |
| `address_data` | `dict` | Dictionary containing address fields (`address_type`, `state`, `district`, `taluka`, `village`, `pin_code`, `address`). |

**Behavior:**  
- Selects **Address Type** (`control_id="address_type{index}"`).  
- Fills the **Address** input (located by `id="address"` at the given index).  
- Selects **State**, **District**, **Taluka**, **Village** sequentially (IDs: `state_ref_id_id{index}`, `district_ref_id_id{index}`, `sub_district_ref_id_id{index}`, `village_ref_id{index}`).  
- Fills **Pincode** (ID: `pin_code` at index).  
- Logs completion or warnings if elements are missing.

---

### `fill_bank_details_customer(driver, wait, bank_data)`

Fills the customer bank details section and uploads a bank proof file.

| Parameter | Type | Description |
|-----------|------|-------------|
| `bank_data` | `dict` | Dictionary containing bank fields (`bank_name`, `branch_name`, `ifsc`, `account_type`, `account_holder_name`, `account_number`, `bank_proof`, `bank_proof_file`). |

**Behavior:**  
- Fills **Bank Name**, **Branch Code**, **IFSC Code**, **Account Holder Name**, **Account Number** (all via `fill_input` with control IDs).  
- Selects **Account Type** (`control_id="account_type0"`) and **Bank Proof** (`control_id="bank_doc_id0"`) using `select_dropdown`.  
- If `bank_proof_file` is provided, attempts to locate a file input using multiple fallback selectors and uploads the file.  
- Logs a warning if the file input cannot be found or upload fails.

---

## Main Function

### `fill_customer_registration(driver, wait, data)`

Orchestrates the complete customer registration workflow.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary matching the structure of `test_data.customer_data`. |

**Steps Performed:**

1. **Basic Company Information**  
   - Company Name (`input#company_name[name='Company Name']`)  
   - Supply Type (`supply_type_ref_id`)  
   - Customer Type (`customer_type_ref_id`)  
   - Sale Type (`sale_type_ref_id`)  
   - Email (`email_id`), Mobile (`mobile_no`), PAN (`pan_no`)  
   - Ownership Status (`ownership_status_ref_id`)

2. **Additional Details** (expands accordion)  
   - Contact Person (`display_name_as`)  
   - Office Number (`office_no`)  
   - Preferred Payment Method, GST Registration Type, Payment Terms, Delivery Terms, Mode of Delivery, Courier Terms (if provided)  
   - Deposit, Quantity Tolerance, Rate Tolerance

3. **Customer Details** (expands accordion)  
   - Fills **Billing Address** using `fill_address_customer(…, index=0)`  
   - Clicks the **"+" button** (`button.apply-button`) to add a second address block  
   - Fills **Shipping Address** using `fill_address_customer(…, index=1)`

4. **Customer Bank Details** (expands accordion)  
   - Calls `fill_bank_details_customer()` to populate bank fields and upload proof

5. **Submission**  
   - Clicks the submit button via `click_submit(driver, wait)`  
   - Waits 3 seconds and logs completion

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`).

**Example Console Output:**
```
10:30:15 | INFO     | ⚡ Starting Customer Registration...
10:30:17 | INFO     |    ✅ Expanded 'Additional Details' section
10:30:22 | INFO     |    ✅ Expanded 'Customer Details' section
10:30:24 | INFO     |    📍 Filling Customer Address Block 0...
10:30:30 | INFO     |    ✅ Customer Address Block 0 filled.
10:30:33 | INFO     |    📍 Filling Customer Address Block 1...
10:30:39 | INFO     |    ✅ Customer Address Block 1 filled.
10:30:41 | INFO     |    ✅ Expanded 'Customer Bank Details' section
10:30:42 | INFO     | 🏦 Filling Customer Bank Details...
10:30:44 | INFO     | 📂 Uploading bank proof file...
10:30:46 | INFO     |    Found file input using: input[type='file']
10:30:47 | INFO     |    ✅ Uploaded: C:\...\blank.pdf
10:30:49 | INFO     | 🏦 Customer Bank details filled.
10:30:50 | INFO     | 📤 Submitting the form...
10:30:51 | INFO     | ✅ Submit button clicked
10:30:54 | INFO     | 🚀 Customer Registration Completed Successfully!
```

## Usage Example

```python
from Registration.customer_section import fill_customer_registration
from data.test_data import customer_data

def test_customer(driver, wait):
    fill_customer_registration(driver, wait, customer_data)
```

## Maintenance Notes

- **Company Name Field**: Uses a specific CSS selector `input#company_name[name='Company Name']` to avoid ambiguity. Update if the UI changes the `id` or `name` attribute.
- **Accordion Headers**: The text passed to `expand_section` must match exactly the `<strong>` content (`"Additional Details"`, `"Customer Details"`, `"Customer Bank Details"`).
- **Address Indexes**: The billing address is always index `0`. The shipping address becomes index `1` after clicking the **"+" button**. Ensure the UI adds exactly one new block per click.
- **File Upload**: The function attempts multiple selectors to find the file input. If a new design changes the input placement, add the new selector to the `selectors` list.
- **Waits**: `time.sleep(1)` calls between cascading dropdowns (state → district → taluka → village) allow dependent options to load. Adjust if the UI becomes slower or faster.
```