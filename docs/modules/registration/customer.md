# Module: Customer

> The 2nd most complex registration module — 3-stepper flow with 14 FK ID pools and critical structural differences from Supplier that will bite you if you copy-paste.

## At a Glance

| Section | Value |
|---|---|
| Complexity Rank | 2nd most complex |
| Steppers | 3 (Additional Details → Customer Details → Customer Bank Details) |
| Repeating Rows | Address grid (Customer Details), Bank grid (Customer Bank Details) |
| API Tests | Yes |
| UI Tests | Yes |
| Page Object | `customer_page.py` (3,857 LOC) |
| Data File | `customer_data.py` (1,021 LOC) |
| Batch Create | Yes |
| attribute_name | `Customer` |

## The ERP Screen

The Customer registration screen creates new customer entities in the ERP system. It follows a 3-step stepper wizard:

**Navigation URL:** `/registration/customer`

### Step 1: Additional Details
This is the top-level customer identity step. Fields include:
- Customer Name (free text, required)
- Customer Type (dropdown — e.g., Individual, Corporate)
- PAN (free text, server-side uniqueness enforced)
- GST Number (free text)
- Contact Number
- Email
- Status (toggle)

**CRITICAL STRUCTURAL NOTE:** Unlike Supplier, the Additional Details fields live ON the child object itself, NOT inside `details[]`. The `details[]` array is EMPTY for Customer. This is the single biggest difference from Supplier and the root cause of many payload bugs when people copy Supplier test code.

### Step 2: Customer Details (Address Grid)
Contains a repeating Address grid where each row represents an address entry:
- Address Line 1
- Address Line 2
- Country (FK → cascading)
- State (FK → cascading, depends on Country)
- District (FK → cascading, depends on State)
- Taluka (FK → cascading, depends on District)
- City/Village (FK → cascading, depends on Taluka)
- Pin Code
- Address Type (dropdown)
- Is Primary (checkbox)

The cascading address chain uses `get_random_address_chain()` imported from `supplier_data.py` — the only cross-module FK data import in the registration suite.

### Step 3: Customer Bank Details (Bank Grid)
Contains a repeating Bank details grid:
- Bank Name
- Branch Name
- Account Number
- Account Holder Name
- IFSC Code
- Account Type (dropdown — Savings/Current)
- Is Primary (checkbox)

**Bank Account Holder Name Sanitization:** The account holder name must be sanitized before submission — strip all non-alpha characters but keep spaces. This means `O'Brien & Sons Ltd.` becomes `OBrien  Sons Ltd`. The page object has a dedicated sanitizer method.

## API Contract

### Endpoint
`POST /api/registration/customer`

### attribute_name
`Customer`

### Payload Structure
```json
{
  "attribute_name": "Customer",
  "name": "string",
  "pan": "string",
  "gstin": "string",
  "contact_number": "string",
  "email": "string",
  "status": 1,
  "details": [],
  "children": [
    {
      "attribute_name": "CustomerDetails",
      "details": [
        {
          "address_line_1": "string",
          "address_line_2": "string",
          "country_id": "FK",
          "state_id": "FK",
          "district_id": "FK",
          "taluka_id": "FK",
          "city_village_id": "FK",
          "pin_code": "string",
          "address_type": "string",
          "is_primary": true
        }
      ]
    },
    {
      "attribute_name": "CustomerBankDetails",
      "details": [
        {
          "bank_name": "string",
          "branch_name": "string",
          "account_number": "string",
          "account_holder_name": "string",
          "ifsc_code": "string",
          "account_type": "string",
          "is_primary": true
        }
      ]
    }
  ]
}
```

### FK Dependencies (14 Pools)
| FK Pool | Source | Approx Count |
|---|---|---|
| COUNTRY_IDS | Address FK | ~1 |
| STATE_IDS | Address FK (cascading from Country) | ~36 |
| DISTRICT_IDS | Address FK (cascading from State) | Varies |
| TALUKA_IDS | Address FK (cascading from District) | Varies |
| CITY_VILLAGE_IDS | Address FK (cascading from Taluka) | Varies |
| CUSTOMER_TYPE_IDS | Customer Type dropdown | ~5 |
| ADDRESS_TYPE_IDS | Address Type dropdown | ~5 |
| BANK_NAME_IDS | Bank Name dropdown | ~100 |
| ACCOUNT_TYPE_IDS | Account Type dropdown | ~2 |
| INDUSTRY_TYPE_IDS | Industry dropdown | ~20 |
| STATUS_IDS | Status toggle | 2 |
| PARTY_REF_IDS | Party reference | ~100 |
| GST_TREATMENT_IDS | GST Treatment dropdown | ~5 |
| CURRENCY_IDS | Currency dropdown | ~5 |

**Cross-module import:** `get_random_address_chain()` from `supplier_data.py` handles the cascading Country→State→District→Taluka→City chain in a single call, ensuring referential integrity.

## Data Layer

### FK Pool Loading
FK IDs are loaded at module init time from reference API endpoints. The 14 pools are stored as module-level lists and randomly sampled during payload construction.

### Payload Builder
`build_customer_payload()` constructs the full API payload:
1. Generates a unique company name via `generate_company_name()`
2. Generates PAN via `generate_pan()`
3. Fetches a random address chain from `supplier_data.get_random_address_chain()`
4. Assembles the `details: []` (EMPTY!) and `children[]` arrays
5. Sanitizes bank account holder name (strip non-alpha, keep spaces)
6. Returns complete payload dict

### Generators

**`generate_company_name()`** — Uses 7 distinct patterns to create realistic company names while avoiding collisions:
1. `{Prefix} {Industry} {Suffix}` — e.g., "Nova Digital Solutions"
2. `{Adjective} {Noun} {Type}` — e.g., "Swift Horizon Enterprises"
3. `{City} {Industry} Pvt Ltd` — e.g., "Mumbai Logistics Pvt Ltd"
4. `{Founder} {And} {Founder} {Type}` — e.g., "Sharma And Patel Associates"
5. `{Acronym} {Industry} Group` — e.g., "KLM Pharma Group"
6. `{Color} {Animal} {Suffix}` — e.g., "Blue Falcon Industries"
7. `{Region} {Product} Corp` — e.g., "Western Steel Corp"

Each pattern appends a random 3-digit suffix to guarantee uniqueness even under concurrent test runs.

**`generate_pan()`** — Generates a valid-format PAN: `AAAAA0000A` (5 alpha + 4 digit + 1 alpha). PAN uniqueness is enforced server-side; if a collision occurs, the API returns a 409 and the test must regenerate.

**Address Chain Generator** — Delegated to `supplier_data.get_random_address_chain()` which:
1. Picks a random Country ID (always India for domestic customers)
2. Queries State IDs for that country
3. Picks a random State, queries District IDs
4. Picks a random District, queries Taluka IDs
5. Picks a random Taluka, queries City/Village IDs
6. Returns the full chain as a dict of IDs

### Dual Generator System
The module has both:
- **Old timestamp-based generators** — e.g., `f"Customer_{int(time.time())}"` — still present for backward compatibility
- **New realistic data generators** — e.g., `generate_company_name()` — preferred for all new tests

### Validation Rules
- **PAN**: Must be unique (server-side enforcement). Format: `^[A-Z]{5}[0-9]{4}[A-Z]$`
- **GST**: Must match GST format when provided
- **Account Holder Name**: Strip non-alpha characters (keep spaces) before submission
- **Pin Code**: 6-digit Indian pin code
- **IFSC**: 11-character format `AAAA0XXXXXX`
- **Email**: Standard email format

## Page Object

### Key Methods

**`fill_additional_details(data)`** — Fills Step 1 fields. Handles the standard text inputs and dropdown selects. Does NOT write into `details[]`.

**`add_address_row(data)`** — Adds a row to the Address grid in Step 2. Uses `get_random_address_chain()` to populate cascading dropdowns. Each dropdown selection triggers an API call to fetch the next level's options.

**`add_bank_row(data)`** — Adds a row to the Bank grid in Step 3. Sanitizes the account holder name.

**`navigate_to_step(step_number)`** — Clicks stepper headers to navigate between steps.

**`submit_customer()`** — Clicks the final Submit button.

### Tricky Bits

1. **BUG-001: mat-select doesn't update Angular reactive form model** — When a mat-select dropdown is clicked via standard Playwright `.click()` + `.select_option()`, the UI updates visually but the Angular reactive form model does NOT reflect the change. On form submission, the field is still `null`. **Workaround:** Use JavaScript `dispatchEvent(new Event('change'))` after setting the value, or use the custom `_select_mat_option()` helper that fires both the UI interaction and the model sync.

2. **BUG-002: Stepper allows advancing with empty required fields** — The stepper "Next" button is always enabled. Clicking it advances to the next step even when required fields are empty. Validation only fires when the final Submit button is clicked. This means tests can fill steps out of order or skip fields and only discover failures at submission time.

3. **details[] is EMPTY** — The `details` array on the root customer object is always `[]`. All meaningful data lives in the `children` arrays. This is different from Supplier where `details[]` contains the main record data.

4. **Bank account holder name sanitization** — The page object must strip non-alpha characters (keep spaces) from the account holder name. If you forget this, the API will accept it but downstream processing fails.

5. **Cascading address dropdowns** — Each dropdown selection triggers an API call. Tests must wait for the response before interacting with the next dropdown. The page object uses explicit waits for option list population.

### Locator Strategies
- Stepper headers: `mat-step-header` by index
- Form fields: `input[formcontrolname='<field>']`
- mat-select dropdowns: `mat-select` + `mat-option` text match
- Grid add buttons: `button` with icon class `mat-icon` and text "add"
- Grid rows: `mat-row` within the specific grid container

## Known Bugs

| Bug ID | Severity | Description |
|---|---|---|
| BUG-001 | Critical | Browser-clicked mat-select does NOT update Angular reactive form model. UI shows selection but model remains null. Requires JS value-setter workaround. |
| BUG-002 | High | Stepper allows advancing even with empty required fields. Validation only fires on Submit, not on Next. |

## War Stories

### The Empty details[] Trap

A new team member was tasked with writing Customer API tests. They had previously worked on Supplier and copied the Supplier payload builder wholesale. The Supplier builder puts main fields inside `details[0]` and uses `children` for sub-forms. They built the Customer payload the same way — main fields in `details[0]`, addresses in `children[0]`, banks in `children[1]`. Every single API call returned a 201 but the created customer was missing all its basic information. The name, PAN, GST — all gone. After two days of debugging, they discovered that Customer's Additional Details fields live ON the child object itself, and `details[]` must be empty. The 201 was "successful" because the server ignored the unexpected `details[0]` and saved an empty shell. The fix was one line — `details: []` — but finding it required tracing the server's deserialization logic.

### The Phantom mat-select

During UI automation development, a test was failing intermittently on the Customer Type dropdown. The test would select "Corporate" from the dropdown, the UI would show "Corporate" highlighted, the test would advance to Step 2, fill everything, and submit. The API response came back with `customer_type: null`. At first, the assumption was a timing issue — maybe the form hadn't settled. Adding longer waits didn't help. Then someone noticed that the Angular reactive form's value was never actually updated by the mat-select click. The mat-select component has a known bug where programmatic clicks don't propagate to the FormControl. The fix was a two-step process: first set the value on the native `<select>` element, then dispatch a `change` event so Angular picks it up. This bug affects every mat-select in the Customer form and is the reason the custom `_select_mat_option()` helper exists.

### PAN Collision Roulette

In parallel test execution, two test runners hit the Customer creation endpoint at nearly the same time with independently generated PANs. Both generated valid-format PANs, but by pure chance, the random 5-letter + 4-digit + 1-letter combination collided. The first request succeeded (201), the second got a 409 Conflict. The test framework's retry logic kicked in and regenerated the PAN, but the retry happened so fast that the server's PAN uniqueness index hadn't fully committed, leading to a brief window where the same PAN could be inserted twice. This was eventually resolved by adding `generate_company_name()`'s pattern-based approach with guaranteed-unique suffixes, and by adding a `time.sleep(0.5)` after PAN regeneration retries.

## Test Coverage

| Test Type | Status | Count |
|---|---|---|
| API Create Tests | ✅ Passing | ~15 |
| API Update Tests | ✅ Passing | ~8 |
| API Validation Tests | ✅ Passing | ~10 |
| API Batch Create | ✅ Passing | ~3 |
| UI Create Tests | ✅ Passing | ~12 |
| UI Stepper Navigation | ✅ Passing | ~5 |
| UI Address Grid | ✅ Passing | ~8 |
| UI Bank Grid | ✅ Passing | ~6 |
| Knowledge Doc | ✅ Exists | 1 (464 LOC) |

## Files

```
registration/
├── customer_page.py          3,857 LOC   # Page object
├── customer_data.py          1,021 LOC   # Data layer, FK pools, generators
├── test_customer_api.py      ~200 LOC    # API create/update tests
├── test_customer_api_validation.py ~150 LOC # API validation tests
├── test_customer_ui.py       ~300 LOC    # UI automation tests
├── test_customer_batch.py    ~100 LOC    # Batch creation tests
└── Customer_Automation_Knowledge.md 464 LOC # Knowledge transfer doc
```

## What's Missing

1. **Supplier data independence** — Customer currently imports `get_random_address_chain()` from `supplier_data.py`. This creates a coupling between the two modules. The address chain generator should be extracted into a shared `address_utils.py` module.

2. **PAN uniqueness retry in UI tests** — The UI flow has no mechanism to detect a PAN collision (server returns an error toast) and retry with a new PAN. Tests that use pre-generated PANs can fail in parallel runs.

3. **Old generator cleanup** — The timestamp-based generators (`f"Customer_{int(time.time())}"`) are still present and used in some legacy tests. These should be migrated to `generate_company_name()`.

4. **Negative test coverage** — Missing tests for: invalid PAN format, invalid GST format, IFSC format validation, pin code format validation, duplicate email handling.

5. **Update flow UI tests** — Currently only Create flow has UI tests. There are no UI tests for editing an existing customer's details, addresses, or bank information.

6. **Concurrent creation stress tests** — No tests verify behavior when multiple customers are created simultaneously with similar data.

7. **Address grid edge cases** — No tests for: adding 10+ address rows, removing address rows, setting multiple addresses as primary, mixing domestic and international addresses.

8. **Bank grid edge cases** — No tests for: IFSC code validation, account number format, adding 5+ bank accounts, duplicate bank account detection.

9. **Stepper backward navigation** — BUG-002 means validation doesn't fire on Next, but there are no tests verifying what happens when you go back and change data in a previous step after already advancing.
