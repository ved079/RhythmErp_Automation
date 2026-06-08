# Module: Member

> Nearly identical to Directors — but with a phone validation gap that accepts 3-digit numbers, and an `is_member_director` toggle that creates a live link between Members and Directors records.

## At a Glance

| Section | Value |
|---|---|
| Complexity Rank | 7th (API-only, near-clone of Directors) |
| Steppers | None (API-only) |
| Repeating Rows | None (KYC via children array) |
| API Tests | Yes (3 files) |
| UI Tests | None (no page object) |
| Page Object | **DOES NOT EXIST** |
| Data File | `member_data.py` (911 LOC) |
| Batch Create | Yes |
| attribute_name | `Member` |

## The ERP Screen

The Member module manages company member/shareholder information. Like Directors, it is accessed as a child form within the Company Onboarding flow rather than as a standalone screen. Members represent shareholders and have a toggle that can link them to the Directors module.

**Navigation URL:** Not directly accessible — Members are created within the Company Onboarding flow or via API.

### Member Fields
- Prefix (FK dropdown — Mr., Mrs., Ms. — 3 options)
- Member Name (free text)
- Date of Birth
- Date of Appointment
- Mobile Number (integer type in API — **NO server-side length validation**)
- Email
- Party Reference (FK — ~330 options)
- **`is_member_director`** (toggle — links Member to Directors)
- `no_class_shares_held` (STRING — e.g., "100 Equity")
- `distintive_number` (ERP typo — missing 'c' in "distinctive")

### The `is_member_director` Toggle
This boolean field is the key differentiator from Directors. When set to `true`:
- The Member record is cross-linked with a Director record
- The system creates a bidirectional relationship between the two entities
- The same person appears in both the Members and Directors lists
- Changes to one may propagate to the other (exact behavior unclear)

This is important for governance scenarios where a company member also serves as a board director.

### Phone Number — No Length Validation
⚠️ **CRITICAL GAP:** The Member phone field has **NO server-side length validation**. The API will accept a 3-digit phone number like `"123"` or even `"1"`. This is different from Directors (where phone format may be enforced) and from Employee (where `^[6-9]\d{9}$` is required). Tests should still generate valid 10-digit Indian phone numbers, but the server will not reject invalid ones.

## API Contract

### Endpoint
```
POST /api/registration/member
```

### attribute_name
`Member`

### Payload Structure
```json
{
  "attribute_name": "Member",
  "prefix_id": "FK",
  "name": "string",
  "dob": "YYYY-MM-DD",
  "date_of_appointment": "YYYY-MM-DD",
  "mobile_no": 123,
  "email": "string",
  "party_ref_id": "FK",
  "is_member_director": false,
  "no_class_shares_held": "100 Equity",
  "distintive_number": "string",
  "details": [],
  "children": []
}
```

### Critical Payload Notes

1. **`distintive_number`** — Same ERP typo as Directors. The field is literally spelled `distintive_number` (missing the 'c'). Must be preserved exactly in payloads.

2. **`no_class_shares_held`** — Must be a STRING like `"100 Equity"`, not an integer. Same convention as Directors.

3. **`mobile_no`** — Must be an INTEGER type (not string). However, unlike Employee, there is **no format or length validation** — even `1` is accepted.

4. **`is_member_director`** — Boolean toggle. When `true`, creates a cross-link with the Directors module.

### FK Dependencies (3 Pools)
| FK Pool | Source | Approx Count |
|---|---|---|
| PREFIX_IDS | Prefix dropdown | 3 |
| KYC_DOC_IDS | KYC Document Type | 2 |
| PARTY_REF_IDS | Party Reference | ~330 |

Note: Member has fewer FK pools than Directors (3 vs 5). Missing: DESIGNATION_IDS, QUALIFICATION_IDS. Members don't have designation or qualification fields.

## Data Layer

### FK Pool Loading
3 FK pools loaded at module init:
```python
PREFIX_IDS = fetch_reference_ids("prefix")              # 3 IDs
KYC_DOC_IDS = fetch_reference_ids("kyc_document_type")  # 2 IDs
PARTY_REF_IDS = fetch_reference_ids("party_reference")  # ~330 IDs
```

### Payload Builder
`build_member_payload()` constructs the API payload:
1. Picks a random prefix from PREFIX_IDS (3 options)
2. Generates a member name
3. Generates dates (DOB, appointment)
4. Generates mobile number as INTEGER (no length validation on server)
5. Generates email
6. Picks a random party_ref_id from PARTY_REF_IDS
7. Sets `is_member_director` (default: `false`, configurable)
8. Formats `no_class_shares_held` as string (e.g., `"100 Equity"`)
9. Sets `distintive_number` (with the typo preserved)
10. Returns complete payload dict

### Member vs Directors — Structural Comparison

| Aspect | Directors | Member |
|---|---|---|
| FK Pools | 5 (Prefix, Designation, Qualification, PartyRef, KYCDoc) | 3 (Prefix, PartyRef, KYCDoc) |
| Designation field | ✅ Yes | ❌ No |
| Qualification field | ✅ Yes | ❌ No |
| DIN/PAN field | ✅ Yes | ❌ No |
| is_member_director | ❌ No | ✅ Yes |
| Phone validation | Some enforcement | **None** (3 digits accepted) |
| Data file LOC | 1,053 | 911 |
| Party ref count | ~340 | ~330 |
| distintive_number typo | ✅ Same | ✅ Same |
| no_class_shares_held string | ✅ Same | ✅ Same |

### Generators
- **Member Name**: Standard name generator (alpha only)
- **Mobile Number**: Generated as 10-digit Indian format but server doesn't validate
- **no_class_shares_held**: `f"{random.randint(1, 10000)} Equity"` — string format
- **distintive_number**: Generated string, preserving the typo in the field name

### Validation Rules
| Field | Rule | Source |
|---|---|---|
| name | Required | Server-side |
| mobile_no | Must be INTEGER type, **NO length/format validation** | Server-side |
| no_class_shares_held | Must be STRING format | Server-side |
| distintive_number | Literally spelled without 'c' | ERP schema |
| is_member_director | Boolean | Server-side |
| party_ref_id | Valid FK required | Server-side FK check |
| prefix_id | Valid FK | Server-side FK check |

## Page Object

### Does Not Exist
There is **no page object** for the Member module. All test automation is API-only. This is the same situation as Directors — both modules are API-only with no UI automation.

### Implications of Missing Page Object
1. **No UI regression coverage** — Member UI breakage won't be caught
2. **No visual validation** — Cannot verify member data display
3. **No end-to-end coverage** — Cannot test Company Onboarding → Add Member → Verify
4. **No `is_member_director` UI test** — Cannot verify the toggle's behavior in the UI

## Known Bugs

| Bug ID | Severity | Description |
|---|---|---|
| ERP-TYPO-002 | Low | Same as Directors: `distintive_number` is missing the 'c' in "distinctive". Database schema issue. |
| PHONE-001 | High | Phone number has NO server-side length validation. 3-digit numbers like `123` are accepted. This could cause downstream issues in SMS notifications, phone formatting, etc. |

**Known Issues:**
- `no_class_shares_held` string format acceptance is undocumented
- `is_member_director` cross-linking behavior is partially understood
- `mobile_no` integer type inconsistency with string-based phone fields in other modules

## War Stories

### The Three-Digit Phone Number

While writing negative test cases for the Member API, an engineer decided to test the phone number boundary. They sent `mobile_no: 1`. The API returned 201 Created. They sent `mobile_no: 12`. 201 Created. `mobile_no: 123`. 201 Created. A 3-digit phone number was accepted without any error. This was shocking — the Employee module enforces `^[6-9]\d{9}$`, and even Directors has some phone validation. But Member accepts literally any integer as a phone number. This is a real data quality risk because downstream systems (SMS gateways, phone formatters, IVR systems) will fail when they encounter a 3-digit phone number. The bug is documented but not fixed. Tests still generate valid 10-digit numbers, but the lack of validation means garbage data can enter the system through the API.

### The Director-Member Identity Crisis

A test was written to verify the `is_member_director` toggle. It created a Member with `is_member_director: true`. The API returned 201 Created. Then the test queried the Directors endpoint and found a new Director with the same name and details. The Member had automatically created a corresponding Director record. So far so good. But then the test updated the Member's email address. The Director's email did NOT update. The two records were linked but not synchronized. This means the `is_member_director` flag creates a one-time copy, not a live synchronization. Tests that expect the two records to stay in sync will fail.

### The Copy-Paste Bug That Wasn't

When the Member module was first being automated, the team decided to copy the Directors data layer and adapt it. They carefully changed `attribute_name` from "Directors" to "Member", removed the Designation and Qualification FK pools, added the `is_member_director` field, and updated the generators. The tests passed. Then they noticed that the `distintive_number` typo was present in both modules. They assumed it was a copy-paste error and "fixed" it to `distinctive_number` in the Member payload. The API silently ignored the correctly-spelled field. The same typo exists in both modules because it's in the database schema, not in the test code. The lesson: when two modules share a weird quirk, it's probably in the shared infrastructure, not in the test code.

## Test Coverage

| Test Type | Status | Count |
|---|---|---|
| API Create Tests | ✅ Passing | ~8 |
| API Update Tests | ✅ Passing | ~4 |
| API Validation Tests | ✅ Passing | ~5 |
| API Batch Create | ✅ Passing | ~2 |
| UI Tests | ❌ None | 0 |
| is_member_director Toggle | ⚠️ Partial | ~2 |

## Files

```
registration/
├── (no page object file)         # DOES NOT EXIST
├── member_data.py          911 LOC   # Data layer, FK pools, generators
├── test_member_api.py            ~150 LOC  # API create/update tests
├── test_member_api_validation.py ~100 LOC  # API validation tests
└── test_member_batch.py           ~80 LOC  # Batch creation tests
```

## What's Missing

1. **Page object** — Same gap as Directors. No UI automation, no visual validation, no end-to-end coverage.

2. **Phone validation tests** — Despite the known gap (PHONE-001), there are no dedicated tests that verify the absence of phone validation. Tests should explicitly document this gap and perhaps add a `@pytest.mark.xfail` test that proves 3-digit numbers are accepted.

3. **`is_member_director` comprehensive testing** — The toggle's behavior is partially tested. Missing tests for:
   - Setting `is_member_director: true` and then updating the Member — does the Director update?
   - Setting `is_member_director: false` after it was `true` — does the Director record get deleted or orphaned?
   - Creating a Director with the same details as an existing Member with `is_member_director: true` — does a duplicate get created?
   - The exact fields that are copied from Member to Director

4. **Cross-linking with Directors** — No test verifies that the Member → Director cross-link works bidirectionally. Can you navigate from the Director record to the Member record?

5. **Negative tests for `distintive_number`** — No tests for: empty value, numeric-only value, special characters. What does the server accept?

6. **`no_class_shares_held` format exploration** — Only "Equity" class is tested. What about Preference shares? Multiple classes? What about the format itself — is `"100 Equity"` the only accepted format?

7. **Update flow** — No tests for updating an existing Member. Can you change `is_member_director` after creation? Can you toggle it off? What happens to the linked Director?

8. **Batch creation with `is_member_director`** — Batch tests create Members with `is_member_director: false`. No test verifies batch creation where some Members are also Directors.

9. **Comparison test with Directors** — No automated test verifies that Member and Directors share the same `distintive_number` typo. A schema comparison test would catch if one module's typo is fixed but not the other's.

10. **Party reference auto-patch** — Does the `party_ref_id` auto-patch behavior (documented for Directors) also apply to Members? No test verifies this either way.
