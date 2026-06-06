# Module: Directors

> An API-only module with no page object — where a documented ERP typo ("distintive_number" missing the 'c') must be preserved in every payload, and `party_ref_id` auto-patches 6+ fields across the record.

## At a Glance

| Section | Value |
|---|---|
| Complexity Rank | 6th (API-only, 1 stepper child) |
| Steppers | 1 KYC stepper child with grid rows |
| Repeating Rows | KYC documents (grid) |
| API Tests | Yes (3 files) |
| UI Tests | None (no page object) |
| Page Object | **DOES NOT EXIST** |
| Data File | `directors_data.py` (1,053 LOC) |
| Batch Create | Yes |
| attribute_name | `Directors` |

## The ERP Screen

The Directors module manages company director information. It is accessed as a child form within the Company Onboarding flow rather than as a standalone screen. Directors are linked to a company and carry KYC document information in a repeating grid.

**Navigation URL:** Not directly accessible — Directors are created within the Company Onboarding stepper (Promoters step) or via API.

### Director Fields
- Prefix (FK dropdown — Mr., Mrs., Ms. — only 3 options)
- Director Name (free text)
- Designation (FK dropdown — 56 options)
- Qualification (FK dropdown — 6 options)
- DIN/PAN (free text)
- Date of Birth
- Date of Appointment
- Mobile Number (**integer type** in API)
- Email
- Party Reference (FK — ~340 options)

### KYC Grid (Repeating Rows)
Each row represents a KYC document:
- Document Type (FK — only 2 options: PAN, DIN)
- Document Number
- **`distintive_number`** — the ERP's typo for "distinctive" (missing 'c')

### no_class_shares_held — String, Not Integer
The `no_class_shares_held` field represents shareholding information. Despite appearing numeric (e.g., "100 Equity"), the API expects this as a **STRING**, not an integer. Sending `100` will fail; you must send `"100 Equity"`. This is a format convention where the number and share class are combined into a single string field.

## API Contract

### Endpoint
```
POST /api/registration/directors
```

### attribute_name
`Directors`

### Payload Structure
```json
{
  "attribute_name": "Directors",
  "prefix_id": "FK",
  "name": "string",
  "designation_id": "FK",
  "qualification_id": "FK",
  "din_pan": "string",
  "dob": "YYYY-MM-DD",
  "date_of_appointment": "YYYY-MM-DD",
  "mobile_no": 9876543210,
  "email": "string",
  "party_ref_id": "FK",
  "no_class_shares_held": "100 Equity",
  "details": [],
  "children": [
    {
      "attribute_name": "DirectorsKYC",
      "details": [
        {
          "kyc_doc_type_id": "FK",
          "document_number": "string",
          "distintive_number": "string"
        }
      ]
    }
  ]
}
```

### Critical Payload Notes

1. **`distintive_number`** — This is NOT a typo in the documentation. The API field is literally spelled `distintive_number` (missing the 'c' in "distinctive"). This is an ERP codebase typo that has been propagated to the database schema and cannot be changed without a migration. **You must use `distintive_number` in payloads.** Using `distinctive_number` will result in the field being silently ignored.

2. **`no_class_shares_held`** — Must be a STRING like `"100 Equity"`, not an integer. The string format is `{number} {class_name}`.

3. **`mobile_no`** — Must be an INTEGER (same as Employee module), not a string.

### FK Dependencies (5 Pools)
| FK Pool | Source | Approx Count |
|---|---|---|
| PREFIX_IDS | Prefix dropdown | 3 |
| DESIGNATION_IDS | Designation dropdown | 56 |
| QUALIFICATION_IDS | Qualification dropdown | 6 |
| PARTY_REF_IDS | Party Reference | ~340 |
| KYC_DOC_IDS | KYC Document Type | 2 |

## Data Layer

### FK Pool Loading
5 FK pools loaded at module init:
```python
PREFIX_IDS = fetch_reference_ids("prefix")           # 3 IDs
DESIGNATION_IDS = fetch_reference_ids("designation")  # 56 IDs
QUALIFICATION_IDS = fetch_reference_ids("qualification")  # 6 IDs
PARTY_REF_IDS = fetch_reference_ids("party_reference")    # ~340 IDs
KYC_DOC_IDS = fetch_reference_ids("kyc_document_type")   # 2 IDs
```

### Payload Builder
`build_directors_payload()` constructs the API payload:
1. Picks a random prefix from PREFIX_IDS (3 options)
2. Generates a director name
3. Picks a random designation from DESIGNATION_IDS
4. Picks a random qualification from QUALIFICATION_IDS
5. Generates DIN/PAN
6. Generates dates (DOB, appointment)
7. Generates mobile number as INTEGER
8. Generates email
9. Picks a random party_ref_id from PARTY_REF_IDS
10. Formats `no_class_shares_held` as string (e.g., `"100 Equity"`)
11. Builds KYC children with `distintive_number` (the typo field)
12. Returns complete payload dict

### The `party_ref_id` Auto-Patch
When a `party_ref_id` is included in the payload, the server **auto-patches 6+ fields** on the director record:
- Director Name (overwritten with party ref name)
- Email (overwritten with party ref email)
- Phone/Mobile (overwritten with party ref phone)
- Address information (overwritten with party ref address)
- DIN/PAN (potentially overwritten)
- Date of Birth (potentially overwritten)

This means:
- If you set `name: "Rajesh Kumar"` and `party_ref_id: 42`, the created director's name will be whatever name is associated with party_ref_id 42, NOT "Rajesh Kumar"
- Tests that verify field values after creation must account for this auto-patch
- The auto-patch only happens on Create, not Update

### Generators
- **Director Name**: Standard name generator (alpha only)
- **DIN/PAN**: Format-compliant generator
- **Mobile Number**: `^[6-9]\d{9}$` as integer
- **no_class_shares_held**: `f"{random.randint(1, 10000)} Equity"` — always "Equity" class for simplicity

### Validation Rules
| Field | Rule | Source |
|---|---|---|
| name | Required (but auto-patched by party_ref_id) | Server-side |
| mobile_no | Must be INTEGER type | Server-side type check |
| no_class_shares_held | Must be STRING format | Server-side type check |
| distintive_number | Literally spelled without 'c' | ERP schema |
| din_pan | Format validation | Server-side |
| party_ref_id | Valid FK required | Server-side FK check |

## Page Object

### Does Not Exist
There is **no page object** for the Directors module. All test automation is API-only. Directors are created and managed entirely through API calls, not through the ERP's UI (or at least, the UI flow hasn't been automated yet).

This means:
- No Playwright locators
- No stepper navigation
- No UI interaction patterns
- No visual validation
- All testing is done via HTTP requests and response assertions

### Implications of Missing Page Object
1. **No UI regression coverage** — If the Directors UI breaks, there are no automated tests to catch it
2. **No visual validation** — Cannot verify that director data displays correctly on screen
3. **No end-to-end coverage** — Cannot test the full flow from Company Onboarding → Add Director → Verify in UI
4. **API-only confidence** — We know the API works, but we don't know if the UI correctly presents the data

## Known Bugs

| Bug ID | Severity | Description |
|---|---|---|
| ERP-TYPO-001 | Low | API field `distintive_number` is missing the 'c' in "distinctive". This is a database schema issue that cannot be fixed without a migration. All payloads must use the misspelled version. |

**Known Issues:**
- `party_ref_id` auto-patch silently overwrites user-provided field values
- `no_class_shares_held` string format is undocumented — discovered through trial and error
- `mobile_no` integer type is inconsistent with most other modules

## War Stories

### The Missing 'C'

An engineer was writing Directors API tests and carefully typed `distinctive_number` in their payload. The API returned 201 Created. Everything looked fine. Then they queried the created director and noticed that `distinctive_number` was `null` in the response, even though they'd sent a value. After an hour of debugging — checking the payload, the request body, the response parsing — they compared their payload with a recorded browser request. The browser used `distintive_number` (no 'c'). The server had silently ignored the correctly-spelled field and saved the record without it. The typo is in the database schema, the ORM model, and the API contract. It will likely never be fixed because changing it would break every existing integration.

### The Phantom Auto-Patch

A test was creating a director with a specific name ("Test Director Alpha") and then verifying that the created director's name matched. The assertion failed — the name came back as "Vikram Singh" (or whatever the party_ref_id's name was). The test writer assumed the API was broken. After investigation, they discovered the `party_ref_id` auto-patch behavior. When you provide a `party_ref_id`, the server overwrites several fields with data from the party reference record. This is by design — it's a data normalization feature — but it's completely undocumented. The fix was to either: (a) not provide a `party_ref_id` if you want to keep your field values, or (b) verify against the party reference data instead of your input data.

### The Integer Shares That Weren't

The `no_class_shares_held` field looks like it should be a number. "100 shares of Equity class" — naturally, an engineer sent `"no_class_shares_held": 100` as an integer. The API returned 201 Created, but the value was `null` in the response. The field expects a STRING format like `"100 Equity"`. The server silently rejected the integer value without returning an error. The test appeared to pass (201 status) but the data was wrong. This is particularly insidious because a superficial test that only checks the status code would pass while the actual data is corrupted.

## Test Coverage

| Test Type | Status | Count |
|---|---|---|
| API Create Tests | ✅ Passing | ~10 |
| API Update Tests | ✅ Passing | ~5 |
| API Validation Tests | ✅ Passing | ~6 |
| API Batch Create | ✅ Passing | ~2 |
| UI Tests | ❌ None | 0 |

## Files

```
registration/
├── (no page object file)         # DOES NOT EXIST
├── directors_data.py    1,053 LOC   # Data layer, FK pools, generators, payload builder
├── test_directors_api.py          ~180 LOC  # API create/update tests
├── test_directors_api_validation.py ~120 LOC # API validation tests
└── test_directors_batch.py         ~80 LOC  # Batch creation tests
```

## What's Missing

1. **Page object** — The most significant gap. Without a page object, there's no UI test coverage. Directors created via API cannot be verified in the UI. If the Directors screen has display bugs, they won't be caught by automation.

2. **UI test suite** — No UI tests at all. The Directors flow within Company Onboarding (adding directors to the Promoters step) is not automated.

3. **`party_ref_id` auto-patch documentation** — The auto-patch behavior is discovered through trial and error. It should be documented in the API contract and tested explicitly.

4. **Negative tests for auto-patch** — No tests verify what happens when: `party_ref_id` is invalid, `party_ref_id` points to a party with missing fields, `party_ref_id` conflicts with explicitly set fields.

5. **KYC grid edge cases** — No tests for: multiple KYC documents of the same type, KYC document number format validation, empty KYC grid (is it required?).

6. **`no_class_shares_held` format validation** — No tests verify what formats are accepted beyond `"100 Equity"`. What about `"100 Preference"` or `"50 Equity 50 Preference"` or just `"100"`?

7. **Update flow** — No tests for updating an existing director. Can you change the designation? Remove a KYC document? Change `party_ref_id`?

8. **Cross-module integration** — No tests verify that a Director created via API appears correctly in the Company Onboarding UI's Promoters grid.

9. **`distintive_number` regression test** — No test explicitly verifies that the typo is preserved. If the ERP team ever fixes the typo, the test suite should catch it (or be updated). A dedicated regression test for the field name would be valuable.

10. **Batch creation with party_ref_id** — Batch tests create directors without `party_ref_id`. No test verifies batch creation where each director has a different `party_ref_id` and the auto-patch applies correctly to all.
