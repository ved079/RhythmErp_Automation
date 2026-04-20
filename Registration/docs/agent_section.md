# Agent Registration Module Reference (`agent_section.py`)

This module automates the **Agent Registration** form in the FPC ERP system. It fills basic agent information, expands and populates address details, handles payment preferences, and uploads a bank proof file before submission.

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

### `fill_bank_details_agent(driver, wait, bank_data)`

Fills the agent bank details section and uploads a bank proof file.

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

### `fill_agent_registration(driver, wait, data)`

Orchestrates the complete agent registration workflow.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary matching the structure of `test_data.agent_data`. |

**Steps Performed:**

1. **Basic Information**  
   - Agent Name (`agent_name`)  
   - Phone (`phone`)  
   - Email (`email`)  
   - Basis Type (`basis_type_id`) – searchable dropdown  
   - Commission (`commission`)

2. **Address Details** (expands accordion via `expand_section`)  
   - State, District, Taluka, Village (searchable dropdowns)  
   - Address textarea (located by `name="Address"`)  
   - Pincode (`pincode`)

3. **Payment Details** (expands accordion)  
   - Payment Terms (`payment_terms`) – if provided  
   - Preferred Payment Method (`preferred_payment_method`) – if provided

4. **Agent Bank Details** (expands accordion)  
   - Calls `fill_bank_details_agent()` to populate bank fields and upload proof

5. **Submission**  
   - Clicks the submit button via `click_submit(driver, wait)`  
   - Waits 3 seconds and logs completion

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`).

**Example Console Output:**
```
10:25:32 | INFO     | ⚡ Starting Agent Registration...
10:25:34 | INFO     |    ✅ Filled agent_name: Apex Trade Networks
10:25:35 | INFO     |    ✅ Filled phone: 9876543210
10:25:36 | INFO     |    ✅ Filled email: apex.1234@example.com
10:25:38 | INFO     |    ✅ Expanded 'Address Details' section
10:25:42 | INFO     |    ✅ Filled pincode: 412105
10:25:43 | INFO     |    ✅ Expanded 'Payment Details' section
10:25:44 | INFO     |    ✅ Expanded 'Agent Bank Details' section
10:25:45 | INFO     | 🏦 Filling Agent Bank Details...
10:25:47 | INFO     | 📂 Uploading bank proof file...
10:25:49 | INFO     |    Found file input using: input[type='file']
10:25:50 | INFO     |    ✅ Uploaded: C:\...\blank.pdf
10:25:52 | INFO     | 🏦 Agent Bank details filled.
10:25:53 | INFO     | 📤 Submitting the form...
10:25:54 | INFO     | ✅ Submit button clicked
10:25:57 | INFO     | 🚀 Agent Registration Completed Successfully!
```

## Usage Example

```python
from Registration.agent_section import fill_agent_registration
from data.test_data import agent_data

def test_agent(driver, wait):
    fill_agent_registration(driver, wait, agent_data)
```

## Maintenance Notes

- **Accordion Headers**: The text passed to `expand_section` must match exactly the `<strong>` content (`"Address Details"`, `"Payment Details"`, `"Agent Bank Details"`). Update if the UI text changes.
- **Address Textarea**: Located by `name="Address"`. If multiple address blocks are present (like in Supplier), this will target the first one. Currently only one address is used.
- **File Upload**: The function attempts multiple selectors to find the file input. If a new design changes the input placement, add the new selector to the `selectors` list.
- **Waits**: `time.sleep(1)` calls between cascading dropdowns (state → district → taluka → village) allow dependent options to load. Adjust if the UI becomes slower or faster.
```