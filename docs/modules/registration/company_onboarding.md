# Module: Company Onboarding

> The only registration module with a dedicated UPDATE flow class — 6-step stepper with cascading address retries, Luhn-validated GSTINs, and batch creation up to 1,000 companies.

## At a Glance

| Section | Value |
|---|---|
| Complexity Rank | 3rd (unique update architecture) |
| Steppers | 6 (Company Details → Promoters → Address → Business Details → Infrastructure → Configuration) |
| Repeating Rows | Promoters grid, Business Details grid, Infrastructure grid |
| API Tests | Yes |
| UI Tests | Yes (Create + Update) |
| Page Object | `company_onboarding_page.py` (920 LOC) |
| Data File | `company_onboarding_data.py` (943 LOC) |
| Batch Create | Yes (up to 1,000) |
| attribute_name | `CompanyOnboarding` |

## The ERP Screen

The Company Onboarding screen registers new companies into the ERP. It is the only module with a formalized **update flow** implemented as a separate page class.

**Navigation URL:** `/registration/company-onboarding`

### Step 1: Company Details
Core company identity:
- Company Name (free text, required)
- CIN (Corporate Identity Number — generated via `generate_cin()`)
- PAN (generated via `generate_pan()`)
- GSTIN (generated via `generate_luhn_gstin()`)
- Company Type (dropdown)
- Industry Type (dropdown)
- Date of Incorporation
- Authentication Type — **STRING values** `"email"` or `"scanner"`, NOT integer IDs. This is unique in the registration suite where most dropdown values are IDs.

### Step 2: Promoters (Repeating Grid)
Each row represents a company promoter:
- Promoter Name
- Designation (FK)
- DIN/Director ID
- Share Percentage
- Contact Number
- Email

### Step 3: Address (Cascading FKs)
Address fields with cascading dropdowns:
- Address Line 1, Address Line 2
- Country → State → District → Taluka → City/Village (cascading chain)
- Pin Code
- Address Type
- Is Primary

This step has the most complex dropdown interaction in the module. The cascading chain requires 5 sequential dropdown selections where each depends on the previous one's API response. See `_fill_address_location_with_retry()` below.

### Step 4: Business Details (Repeating Grid)
Each row represents a business activity:
- Business Activity Name
- Business Type
- Turnover
- Description

### Step 5: Infrastructure (Repeating Grid)
Each row represents an infrastructure asset:
- Infrastructure Type
- Quantity
- Unit
- Description

### Step 6: Configuration
Final configuration step:
- Base Currency (dropdown — typically INR, USD, EUR)
- Fiscal Year Start
- Fiscal Year End
- Accounting Standard

## API Contract

### Endpoints
```
POST   /api/registration/company-onboarding        # Create
PUT    /api/registration/company-onboarding/{id}    # Update
GET    /api/registration/company-onboarding/{id}    # Read
```

### attribute_name
`CompanyOnboarding`

### Payload Structure
```json
{
  "attribute_name": "CompanyOnboarding",
  "name": "string",
  "cin": "string",
  "pan": "string",
  "gstin": "string",
  "company_type_id": "FK",
  "industry_type_id": "FK",
  "date_of_incorporation": "YYYY-MM-DD",
  "authentication_type": "email|scanner",
  "details": [],
  "children": [
    {
      "attribute_name": "CompanyPromoters",
      "details": [
        {
          "promoter_name": "string",
          "designation_id": "FK",
          "din": "string",
          "share_percentage": "number",
          "contact_number": "string",
          "email": "string"
        }
      ]
    },
    {
      "attribute_name": "CompanyAddress",
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
      "attribute_name": "CompanyBusinessDetails",
      "details": [
        {
          "business_activity": "string",
          "business_type": "string",
          "turnover": "number",
          "description": "string"
        }
      ]
    },
    {
      "attribute_name": "CompanyInfrastructure",
      "details": [
        {
          "infrastructure_type": "string",
          "quantity": "number",
          "unit": "string",
          "description": "string"
        }
      ]
    },
    {
      "attribute_name": "CompanyConfiguration",
      "details": [
        {
          "base_currency_id": "FK",
          "fiscal_year_start": "string",
          "fiscal_year_end": "string",
          "accounting_standard": "string"
        }
      ]
    }
  ]
}
```

### FK Dependencies
| FK Pool | Source | Approx Count |
|---|---|---|
| COMPANY_TYPE_IDS | Company Type dropdown | ~8 |
| INDUSTRY_TYPE_IDS | Industry Type dropdown | ~30 |
| DESIGNATION_IDS | Promoter Designation | ~56 |
| COUNTRY_IDS | Address cascading | ~1 |
| STATE_IDS | Address cascading | ~36 |
| DISTRICT_IDS | Address cascading | Varies |
| TALUKA_IDS | Address cascading | Varies |
| CITY_VILLAGE_IDS | Address cascading | Varies |
| CURRENCY_IDS | Base Currency | ~10 |
| ADDRESS_TYPE_IDS | Address Type | ~5 |

### Authentication Type — String, Not ID
The `authentication_type` field uses **string values** `"email"` and `"scanner"` instead of integer foreign key IDs. This is an important difference from most other dropdown fields in the ERP. The API payload must use the string value directly, not an ID lookup.

## Data Layer

### FK Pool Loading
Standard FK pool loading at module init. Address FK pools (Country → City) are loaded via cascading API calls that respect the dependency chain.

### Payload Builder
`build_company_onboarding_payload()` constructs the complete API payload:
1. Generates unique company name
2. Generates CIN via `generate_cin()`
3. Generates PAN via `generate_pan()`
4. Generates GSTIN via `generate_luhn_gstin()`
5. Builds Promoters rows (1-3 default)
6. Builds Address row with full cascading FK chain
7. Builds Business Details rows (1-2 default)
8. Builds Infrastructure rows (1-2 default)
9. Builds Configuration with Base Currency
10. Sets `authentication_type` as string ("email" or "scanner")
11. Returns complete payload dict

### Generators

**`generate_luhn_gstin()`** — Generates a GSTIN with a valid Luhn check digit:
- Format: `{2-digit state code}{PAN}{entity_char}{blank_char}{check_digit}`
- The last digit is computed using the Luhn algorithm to ensure the GSTIN passes checksum validation
- State code is randomly selected from valid Indian state codes
- PAN portion follows the standard `AAAAA0000A` format

**`generate_pan()`** — Standard PAN generator: `AAAAA0000A` format. Shared logic with other modules but implemented locally.

**`generate_cin()`** — Generates a Corporate Identity Number:
- Format: `{listing_code}{5-digit year}{2-digit state}{2-digit industry}{4-digit seq}{1 check}`
- 21 characters total
- Follows the MCA CIN format specification

### Batch Creation
`generate_batch_payloads(count)` generates up to 1,000 company payloads:
- Each payload has a unique name, CIN, PAN, and GSTIN
- Uses sequential numbering appended to base names
- Pre-validates all generated identifiers for uniqueness within the batch
- Returns a list of payload dicts ready for sequential API submission
- CO_SUBMISSIONS global tracking list records all submitted company IDs for cleanup

### CO_SUBMISSIONS Global
A module-level list `CO_SUBMISSIONS` tracks all company IDs created during a test session. This enables:
- Cleanup in teardown fixtures
- Tracking for update tests (pick a random created company to update)
- Verification that batch submissions completed

### Validation Rules
- **GSTIN**: Must pass Luhn checksum validation
- **PAN**: Format `^[A-Z]{5}[0-9]{4}[A-Z]$`
- **CIN**: 21-character MCA format
- **Authentication Type**: Must be `"email"` or `"scanner"` (string, not ID)
- **Share Percentage**: Should sum to 100 across all promoters (not enforced)
- **Base Currency**: Required for Configuration step

## Page Object

### Class Hierarchy
```
CompanyOnboardingPage          # Base class — Create flow
    └── CompanyOnboardingUpdatePage  # Inherits — Update flow
```

`CompanyOnboardingUpdatePage` inherits from `CompanyOnboardingPage` and adds update-specific methods while reusing all the fill/submit logic from the base class.

### Key Methods

**`fill_company_details(data)`** — Fills Step 1. Handles `authentication_type` as string selection from dropdown.

**`add_promoter_row(data)`** — Adds a row to the Promoters grid in Step 2.

**`_fill_address_location_with_retry(data, max_attempts=15)`** — The most critical method in the module. Fills the cascading address dropdowns in Step 3 with up to **15 retry attempts**. The cascading dropdowns (Country → State → District → Taluka → City) are notoriously flaky because:
1. Each dropdown selection triggers an API call
2. The API response may be slow (200ms-2s)
3. The next dropdown's options depend on the previous selection
4. Stale options from a previous selection may persist in the DOM
5. The mat-select panel may not open on first click

The retry logic:
```python
def _fill_address_location_with_retry(self, data, max_attempts=15):
    for attempt in range(max_attempts):
        try:
            self.select_country(data['country_id'])
            self.wait_for_state_options()
            self.select_state(data['state_id'])
            self.wait_for_district_options()
            self.select_district(data['district_id'])
            self.wait_for_taluka_options()
            self.select_taluka(data['taluka_id'])
            self.wait_for_city_options()
            self.select_city(data['city_id'])
            return  # Success
        except (TimeoutError, StaleElementError):
            self._reset_address_dropdowns()
            continue
    raise Exception(f"Failed to fill address after {max_attempts} attempts")
```

**`add_business_detail_row(data)`** — Adds a row to the Business Details grid in Step 4.

**`add_infrastructure_row(data)`** — Adds a row to the Infrastructure grid in Step 5.

**`fill_configuration(data)`** — Fills the Configuration step (Step 6) including Base Currency.

**`submit()`** — Clicks the final Submit/Create button.

### Update Flow Methods (CompanyOnboardingUpdatePage)

**`open_edit(company_id)`** — Navigates to the edit page for an existing company.

**`read_all_steps()`** — Reads the current values from all 6 steps WITHOUT modifying them. Returns a dict snapshot.

**`apply_updates(update_data)`** — Modifies specific fields across steps with the provided update data.

**`click_update()`** — Clicks the Update button (replaces Submit in edit mode).

**`verify_update(before, after)`** — Compares the before and after snapshots to confirm updates were applied correctly.

The update flow pattern is:
1. `open_edit(company_id)` — Navigate to edit
2. `read_all_steps()` — Capture "before" state
3. `apply_updates(update_data)` — Modify fields
4. `click_update()` — Submit changes
5. `read_all_steps()` — Capture "after" state
6. `verify_update(before, after)` — Assert changes

### Tricky Bits

1. **Cascading address dropdown retries** — The 15-attempt retry loop exists because the cascading dropdowns are the flakiest part of the entire module. In CI, 2-3 attempts are typical. Locally, it usually succeeds on the first try. Tests must account for the extended wait time.

2. **Authentication Type string values** — Unlike every other dropdown in the ERP, `authentication_type` uses string values ("email", "scanner") not integer IDs. Tests that treat it as an FK lookup will fail. The page object has a dedicated `_select_auth_type()` method that handles this.

3. **Update flow inheritance** — `CompanyOnboardingUpdatePage` inherits from `CompanyOnboardingPage`, which means all the fill methods from Create are available in Update. However, some fields may be read-only in Update mode. The `apply_updates()` method handles this by checking field editability before attempting to fill.

4. **CO_SUBMISSIONS cleanup** — If a test session crashes mid-execution, the CO_SUBMISSIONS list won't be cleaned up, leaving orphan companies in the test environment. The teardown fixture handles this, but it's not bulletproof.

5. **Promoter share percentage** — No validation enforces that promoter shares sum to 100%. Tests can create companies with 0% total or 200% total shares. This is a business logic gap, not a technical bug.

### Locator Strategies
- Stepper headers: `mat-step-header` by step text or index
- Form fields: `input[formcontrolname='<field>']`
- Authentication Type: Custom dropdown handler (string values, not IDs)
- Cascading dropdowns: `mat-select` + wait for `mat-option` population + click option
- Grid rows: `mat-row` within step-specific grid container
- Update button: `button` with text "Update" (distinct from Create's "Submit")

## Known Bugs

| Bug ID | Severity | Description |
|---|---|---|
| — | — | No formally tracked bugs in the bug tracker. See War Stories for known issues. |

**Known Issues (not formally tracked):**
- Cascading address dropdowns are flaky — require retry mechanism
- Promoter share percentage has no sum-to-100 validation
- CIN format is not validated client-side (only generated correctly by automation)

## War Stories

### The 15-Retry Address Dance

When the Company Onboarding UI tests were first added to CI, the Address step had a 40% failure rate. The cascading dropdowns (Country → State → District → Taluka → City) would randomly fail because the API responses backing each dropdown were sometimes slow enough that the next dropdown's options hadn't loaded yet. A simple "select Country, wait 1 second, select State" approach didn't work because the wait time varied wildly (200ms to 3s). The solution was `_fill_address_location_with_retry()`, which tries the entire chain up to 15 times. In CI, most runs succeed within 3 attempts. The retry loop adds ~10 seconds to the average test time but brought the pass rate from 60% to 99%.

### The String Authentication Surprise

An engineer was writing API tests for Company Onboarding and did what they'd done for every other module: fetch the FK IDs from a reference endpoint, pick a random one, and put it in the payload. For `authentication_type`, they fetched an ID of `3` and sent `"authentication_type": 3`. The API returned a 400 with a cryptic "Invalid value" error. After 30 minutes of debugging, they inspected the network tab in the browser and saw that the actual value sent was `"authentication_type": "email"`. The dropdown wasn't backed by an FK pool at all — it was a simple string enum. The fix was a one-line change from ID to string, but the discovery process required reverse-engineering the frontend's API call.

### The Luhn Check That Wasn't

The `generate_luhn_gstin()` function was written to produce GSTINs that pass Luhn checksum validation. For months, it worked fine. Then the ERP team updated their GSTIN validation on the server to enforce the Luhn check digit. All existing test data with manually-crafted GSTINs (from before the generator existed) immediately started failing. The batch of ~200 companies created for a demo the next day were all invalid. The team had to regenerate all test data using the Luhn-compliant generator. The lesson: always use the generators, never hard-code identifiers.

### The Update Page Inheritance Dilemma

When the Update flow was being designed, there was debate about whether to create a standalone `CompanyOnboardingUpdatePage` or inherit from `CompanyOnboardingPage`. The inheritance approach won because ~90% of the code is identical — the same fill methods, the same locators, the same grid interactions. The only differences are: (1) the submit button says "Update" instead of "Create", (2) some fields may be read-only in edit mode, and (3) there's a read-then-verify pattern. The inheritance works well, but it does mean that a bug in the base class affects both Create and Update flows.

## Test Coverage

| Test Type | Status | Count |
|---|---|---|
| API Create Tests | ✅ Passing | ~12 |
| API Update Tests | ✅ Passing | ~8 |
| API Validation Tests | ✅ Passing | ~6 |
| API Batch Create | ✅ Passing | ~3 |
| UI Create Tests | ✅ Passing | ~10 |
| UI Update Tests | ✅ Passing | ~8 |
| UI Validation Tests | ✅ Passing | ~5 |
| UI Address Step (with retry) | ✅ Passing | ~4 |

## Files

```
registration/
├── company_onboarding_page.py          920 LOC   # Page object (Create)
├── company_onboarding_update_page.py   ~300 LOC  # Update page (inherits from above)
├── company_onboarding_data.py          943 LOC   # Data layer, FK pools, generators
├── test_company_onboarding_api.py      ~200 LOC  # API create tests
├── test_company_onboarding_api_update.py ~180 LOC # API update tests
├── test_company_onboarding_api_validation.py ~120 LOC # API validation tests
├── test_company_onboarding_ui.py       ~350 LOC  # UI create tests
├── test_company_onboarding_ui_update.py ~300 LOC # UI update tests
└── test_company_onboarding_batch.py    ~100 LOC  # Batch creation tests
```

## What's Missing

1. **CIN format server-side validation** — The CIN is generated correctly by automation but the server doesn't validate the format. Invalid CINs are accepted silently. No test verifies server-side CIN format enforcement.

2. **Promoter share percentage validation** — No test verifies that total promoter shares should sum to 100%. No test for the boundary case of 0% or >100% total shares.

3. **Address step parallel execution** — The cascading address retry mechanism makes tests slow. No effort has been made to optimize the API calls or cache address chains for reuse.

4. **Update flow read-only field verification** — No comprehensive test that verifies which fields become read-only in Update mode and which remain editable.

5. **CO_SUBMISSIONS resilience** — The global tracking list is not persisted. If the test runner crashes, cleanup doesn't happen. A database-backed tracking mechanism would be more robust.

6. **Batch creation error handling** — `generate_batch_payloads()` doesn't handle partial failures. If company #47 of 100 fails, the remaining companies are still submitted but the failed one is silently skipped.

7. **Infrastructure and Business Details negative tests** — No tests for: empty rows, rows with only some fields filled, duplicate entries.

8. **Configuration step validation** — No tests for: future fiscal year dates, invalid accounting standards, missing base currency.

9. **Cross-step dependency tests** — No tests verify that changing data in Step 1 (e.g., Company Type) properly affects available options in later steps.
