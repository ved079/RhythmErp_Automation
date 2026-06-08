# Module: Supplier

> **The most battle-tested module.** Supplier has the most FK pools, the most scripts, the most documented bugs, and the most war stories. If you understand Supplier, you can handle any module in this project.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Registration |
| **Complexity** | High |
| **Steppers** | 3 steps (Additional Details → Address Details → Bank Details) |
| **Repeating rows** | ✅ Address grid + Bank grid |
| **API tests** | ✅ payload, schema, perf, live (4 files) |
| **UI tests** | ✅ validation |
| **Page object** | ✅ (2,484 LOC) |
| **Data file** | ✅ (1,441 LOC) |
| **batch_create** | ✅ + 7 helper scripts |
| **Knowledge doc** | ✅ Supplier_Automation_Knowledge.md (521 LOC) |

---

## The ERP Screen

Supplier is found under **Registration → Supplier**. It's a 3-step stepper wizard:

### Step 1: Additional Details (includes Universal fields)
The first step is the biggest — it combines universal identification fields with supplier-specific details:
- **Company Name** — text, required
- **Ownership Status** — mat-select (6 options: Private Ltd, Public Ltd, Partnership, etc.)
- **Email** — text, must be valid email format
- **Phone Number** — input with spinner controls (type=number in DOM — a bug)
- **PAN Number** — text, must match PAN format (ABCDE1234F)
- **GSTIN** — text, must pass Luhn mod-36 checksum validation
- **PO Type** — mat-select (2 options)
- **Payment Terms** — mat-select (6 options)
- **Delivery Terms** — mat-select (2 options)
- **Mode of Delivery** — mat-select (5 options)
- **Base Currency** — defaults to INR (ID 1)
- **Country** — defaults to India (ID 8)

### Step 2: Address Details
A grid with repeating address rows. Each row has:
- **Address Type** — mat-select (Shipping / Billing) — **CRITICAL: ERP requires BOTH types**
- **Country** → **State** → **District** → **Taluka** → **Village** — cascading mat-selects
- **Address Line 1 & 2** — text fields
- **Pin Code** — text field
- Add Row (+) / Remove Row buttons

### Step 3: Bank Details
A grid with repeating bank rows. Each row has:
- **Bank Account Number** — numeric, 9-16 digits
- **Account Holder Name** — alpha-only (no & or special chars)
- **Account Type** — mat-select (Current / Saving)
- **Bank Name** — text
- **IFSC Code** — 11 chars
- **Bank Proof** — mat-select (3 options)
- Add Row (+) / Remove Row buttons

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
```

```json
{
    "attribute_name": "Supplier",
    "company_name": "Test Supplier Pvt Ltd",
    "ownership_status": 83,
    "email": "test@example.com",
    "phone_number": 9876543210,
    "pan_number": "ABCDE1234F",
    "gstin": "27AADCB2230F1Z5",
    "po_type": 46,
    "payment_terms": 28,
    "delivery_terms": 36,
    "mode_of_delivery": 39,
    "currency_ref_id": 1,
    "country_ref_id": 8,
    "details": [],
    "children": [
        {
            "stepper_name": "Address Details",
            "is_stepper": true,
            "details": [
                {
                    "address_type": 43,
                    "country_ref_id": 8,
                    "state_ref_id": 14,
                    "district_ref_id": 183,
                    "taluka_ref_id": 1403,
                    "village_ref_id": 0,
                    "address_line1": "123 Test Street",
                    "address_line2": "Area Name",
                    "pin_code": "411001"
                },
                {
                    "address_type": 42,
                    "country_ref_id": 8,
                    ...
                }
            ]
        },
        {
            "stepper_name": "Bank Details",
            "is_stepper": true,
            "details": [
                {
                    "account_no": "1234567890",
                    "account_holder_name": "Test Supplier",
                    "account_type": 1849,
                    "bank_name": "TEST BANK",
                    "ifsc_code": "SBIN0001234",
                    "bank_proof": 29
                }
            ]
        }
    ]
}
```

### Key Structural Notes

1. **Step 1 fields go directly on the root object**, not inside `details[]`. The `details` array is empty for Step 1.
2. **Steps 2 and 3 are `children`** with `is_stepper: true` and their own `details[]` arrays.
3. **Address rows are `details` inside the Address child**, not top-level `details`.
4. **Phone number is sent as integer**, not string — the API expects `9876543210` not `"9876543210"`.

---

## The Critical Dual Address Rule

**⚠️ THE MOST IMPORTANT THING ABOUT THIS MODULE**

The ERP enforces that Supplier entries MUST have BOTH a Shipping address (type 43) AND a Billing address (type 42). Creating a Supplier with only one address type — regardless of which type — will return a 400 error:

```
"Shipping address is required for Supplier roles"
"Billing address is required for Supplier roles"
```

This was discovered after 2 days of debugging batch_create failures where ALL 10 entries failed with a cryptic error. The fix requires:

```python
# In supplier_data.py — generate_valid_supplier_data() must return TWO addresses:
step2_addresses = [
    {"address_type": 43, ...},  # Shipping (MUST be first)
    {"address_type": 42, ...},  # Billing (MUST be second)
]
```

### The UI Implication

When filling the Address stepper, you need 2 address rows. The page object must:
1. Click "Add Row" to create the second row
2. Use row-scoped locators to fill each row independently (not generic XPaths that always match row 1)

This is the `fill_step2_address()` fix — generic locators match the first row both times, so the second fill overwrites the first row instead of filling the second.

---

## Data Layer

### FK Pools (12 total)

```python
OWNERSHIP_STATUS_IDS = {
    "Private Limited Company": 83, "Public Limited Company": 84,
    "Partnership": 85, "Proprietorship": 86,
    "Limited Liability Partnership": 87, "Hindu Undivided Family": 88
}
PO_TYPE_IDS = {"Purchase Order": 46, "Blanket Purchase Order": 47}
ADDRESS_TYPE_IDS = {"Shipping": 43, "Billing": 42}
ACCOUNT_TYPE_IDS = {"Current": 1849, "Saving": 1850}
PAYMENT_TERMS_IDS = {
    "Advance Payment": 28, "Net 15": 29, "Net 30": 30,
    "Net 45": 31, "Net 60": 32, "On Delivery": 33
}
DELIVERY_TERMS_IDS = {"Ex Works": 36, "FOB": 37}
MODE_OF_DELIVERY_IDS = {
    "Road": 39, "Rail": 40, "Air": 41, "Water": 42, "Courier": 43
}
BANK_DOC_IDS = {"Passbook": 29, "Cancelled Cheque": 30, "Bank Statement": 31}
DEFAULT_CURRENCY_REF_ID = 1  # INR
DEFAULT_COUNTRY_REF_ID = 8   # India
```

### The Address Chain Pool

The cascading address dropdowns require valid FK chains. The data file has a pool of **~30 verified chains**:

```python
_ADDRESS_CHAINS = [
    {"state_ref_id": 14, "district_ref_id": 183, "taluka_ref_id": 1403, "village_ref_id": 0},
    {"state_ref_id": 14, "district_ref_id": 183, "taluka_ref_id": 1404, "village_ref_id": 0},
    ...  # 28 more chains
]
```

These were harvested from the live ERP using `scripts/harvest_chains.py` and cached in `data/harvested_chains.json`.

### Key Generators

- **`generate_gstin()`** — Generates GSTINs that pass Luhn mod-36 checksum. Random GSTINs are REJECTED by the ERP with a 400 error. This was a painful discovery — the function implements the full checksum algorithm.
- **`generate_office_number()`** — Returns `None`. The ERP API rejects formatted landline numbers (e.g., "020-25531234"). Since the field is optional, we leave it blank.
- **`get_random_address_chain()`** — Picks a random chain from the verified pool. Also used by Customer and Company Onboarding (imported from this file).

### The Wrong Payment Terms Story

The `PAYMENT_TERMS_IDS` have a comment: "OLD IDs [28-34] were WRONG — they belonged to a different dropdown". The original IDs were harvested from the wrong dropdown endpoint. The correct IDs were discovered through trial and error after batch_create silently created entries with wrong payment terms. Always verify your FK IDs against the actual dropdown you're targeting.

---

## Page Object

### The Stepper Navigation Pattern

```python
def create_supplier(self, data):
    self.navigate_to_page()
    self._wait_for_page_ready()
    self.fill_step1_additional_details(data)     # Fill Step 1
    self._click_next_button()                     # Next →
    self.fill_step2_address(data)                 # Fill Step 2
    self._click_next_button()                     # Next →
    self.fill_step3_bank(data)                    # Fill Step 3
    self._click_submit_button()                   # Submit
    self._handle_submit_response()                # Handle success/error
```

This stepper pattern (fill → next → fill → next → fill → submit) is used by Supplier, Customer, and Company Onboarding.

### The `_sync_dropdown_angular_model()` Method

Supplier has the most sophisticated version of this method. It dispatches 8 events and toggles 6 CSS classes:

```python
def _sync_dropdown_angular_model(self, element):
    script = """
    var el = arguments[0];
    // Dispatch all events Angular listens to
    ['focusin', 'keydown', 'change', 'input', 'keyup', 'focusout', 'blur']
        .forEach(e => el.dispatchEvent(new Event(e, {bubbles: true})));

    // Toggle CSS classes for Angular validation state
    el.classList.replace('ng-untouched', 'ng-touched');
    el.classList.replace('ng-pristine', 'ng-dirty');
    el.classList.replace('ng-invalid', 'ng-valid');
    """
    self.driver.execute_script(script, element)
```

This was developed through extensive debugging of Angular's reactive form model. The full event list was determined by reading Angular's source code and testing which events trigger form model updates.

### Row-Scoped Locators for Address and Bank Grids

When filling the second address row, generic XPaths always match the first row. The fix uses row-indexed XPath:

```python
def fill_step2_address(self, data, row_index=0):
    if row_index > 0:
        # Use row-scoped XPath for second and subsequent rows
        row_xpath = f"(//div[contains(@class,'address-form-row')])[{row_index + 1}]"
        address_type = self.driver.find_element(
            By.XPATH, f"{row_xpath}//mat-label[contains(.,'Address Type')]..."
        )
    else:
        # First row — generic locators work fine
        address_type = self.driver.find_element(*ADDRESS_TYPE_SELECT)
```

---

## Known Bugs

| Bug ID | Severity | Description | Status |
|--------|----------|-------------|--------|
| BUG-001 | Medium | Company Name accepts special characters | Open |
| BUG-002 | Medium | No email format validation | **FIXED** (ERP now shows "Invalid Email") |
| BUG-003 | Low | Phone Number has spinner controls (type=number) | Open |
| BUG-004 | Medium | No PAN format validation | **FIXED** (ERP now shows "Invalid PAN Number") |
| BUG-005 | Medium | No Update button in Edit mode | **FIXED** (Update button now visible) |

---

## War Stories

### "Batch Create 10/10 Failures"
The `batch_create.py` script was creating suppliers with a single address type. The ERP silently accepted them until a validation was added server-side that requires BOTH Billing and Shipping addresses. All 10 batch entries failed with "Shipping address is required for Supplier roles". Fix: `supplier_data.py` now generates 2 addresses per supplier.

### "Luhn-Valid GSTIN Generation"
Random GSTIN strings like "27AABCU9603R1ZM" are validated server-side using a Luhn mod-36 checksum. If the checksum doesn't match, the ERP returns a 400 error. The `generate_gstin()` function implements the full algorithm to produce valid GSTINs. This took a full day of debugging — the error message didn't mention checksums, just "Invalid GSTIN".

### "The Office Number That Breaks Everything"
Attempting to set an office/landline number like "020-25531234" causes the API to reject the entire payload. The field is optional, so the solution is to simply not set it. `generate_office_number()` returns `None`.

### "The Wrong FK Pool"
Payment Terms IDs were initially harvested from the wrong dropdown endpoint. The IDs 28-34 existed but pointed to different options. Entries were created with wrong payment terms that didn't match what was selected in the UI. Discovered when a manual tester noticed the mismatch.

### "The Address Chain Harvesting Toolchain"
Cascading address FKs (Country → State → District → Taluka) can't be randomly generated — they must be valid chains in the ERP database. A whole toolchain was built:
- `scripts/harvest_chains.py` — discovers valid chains from the API
- `scripts/verify_chains.py` — verifies harvested chains are still valid
- `scripts/capture_cascade.py` — captures the cascading dropdown behavior
- `scripts/discover_dropdowns.py` — discovers all dropdown options for a screen
- `scripts/harvest_full.py` — full harvest of all FK data
- `data/harvested_chains.json` — cached results

---

## Helper Scripts

| Script | Purpose |
|--------|---------|
| `batch_create.py` | Bulk-create suppliers via API |
| `discover_dropdowns.py` | Find all dropdown options for the Supplier screen |
| `harvest_chains.py` | Harvest valid address FK chains from the API |
| `harvest_full.py` | Full FK data harvest |
| `verify_chains.py` | Verify harvested chains are still valid |
| `capture_cascade.py` | Capture cascading dropdown behavior for debugging |
| `discover_payment_terms.py` | Specifically discover payment terms dropdown options |
| `quick_test.py` | Quick smoke test for supplier creation |

---

## Test Coverage

| Test Type | Status | Count |
|-----------|--------|-------|
| API: Payload | ✅ Complete | ~30 tests |
| API: Schema | ✅ Complete | ~15 tests |
| API: Performance | ✅ Complete | ~5 tests |
| API: Live | ✅ Complete | ~10 tests (creates real entries) |
| UI: Validation | ✅ Complete | ~42 tests |

The `test_supplier_live.py` is unique — it creates real entries in the ERP and verifies they persist. This is the only module with a dedicated "live" test suite.

---

## Files

```
pages/registration/modules/supplier/
├── supplier_page.py                (2,484 LOC)
├── Supplier_Automation_Knowledge.md  (521 LOC)
├── Supplier_Automation_Spec_Final.xlsx
├── data/
│   ├── supplier_data.py            (1,441 LOC)
│   └── harvested_chains.json
├── scripts/
│   ├── batch_create.py
│   ├── discover_dropdowns.py
│   ├── harvest_chains.py
│   ├── harvest_full.py
│   ├── verify_chains.py
│   ├── capture_cascade.py
│   ├── discover_payment_terms.py
│   └── quick_test.py
└── test/
    ├── conftest.py
    ├── test_supplier_validation.py
    └── api/
        ├── conftest.py
        ├── test_supplier_payload.py
        ├── test_supplier_schema.py
        ├── test_supplier_perf.py
        └── test_supplier_live.py
```

---

## What Supplier Teaches You

1. **Multi-stepper navigation** — fill → next → fill → next → fill → submit
2. **Repeating row grids** — add row button, row-scoped locators
3. **Cascading FK chains** — Country → State → District → Taluka → Village
4. **Dual address validation** — ERP enforces both Billing AND Shipping for Suppliers
5. **Luhn-valid GSTIN generation** — server-side checksum validation
6. **The full helper script toolchain** — harvest, verify, capture, discover
7. **`_sync_dropdown_angular_model()`** — the definitive JS event dispatch pattern

If you read only one module doc, make it this one.
