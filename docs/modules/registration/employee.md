# Module: Employee

> The simplest registration module — a flat form with no stepper navigation, where the only required field is a status toggle and the API expects `mobile_no` as an integer, not a string.

## At a Glance

| Section | Value |
|---|---|
| Complexity Rank | Simplest registration module |
| Steppers | None — FLAT FORM |
| Repeating Rows | None |
| API Tests | Yes (3 files) |
| UI Tests | Yes (no validation tests) |
| Page Object | `employee_page.py` (1,036 LOC) |
| Data File | `employee_data.py` (653 LOC) |
| Batch Create | Yes |
| attribute_name | `Employee` |

## The ERP Screen

The Employee registration screen creates employee records in the ERP system. Unlike every other registration module, it uses a **flat form** with no stepper navigation at all. All fields are visible on a single page.

**Navigation URL:** `/registration/employee`

### Form Fields
- Employee Name (free text — `^[A-Za-z ]+$` only)
- Employee Code (auto-generated or manual)
- Designation (FK dropdown — 56 options)
- Department (FK dropdown — 0 options, SKIP in tests)
- Phone Number (free text — `^[6-9]\d{9}$` strict Indian format)
- Email (free text)
- Date of Joining
- Party Reference (FK dropdown — ~100 options)
- Status (toggle — **THE ONLY REQUIRED FIELD**)

### The "Only Status Is Required" Anomaly
The Employee form is unique in the ERP because the **only required field is Status** (a simple toggle between Active/Inactive). All other fields — name, phone, email, designation, department — are technically optional. This means the API will accept a payload with nothing but `status: 1`. While the UI form has visual cues suggesting some fields are important, there is no client-side or server-side enforcement beyond the Status toggle.

### Department Has 0 Options
The Department dropdown returns 0 options from the reference API. This is not a bug in the test suite — the ERP simply has no departments configured. All tests must **skip** the Department field. Attempting to select a department will fail because the dropdown has no options to select.

## API Contract

### Endpoint
```
POST /api/registration/employee
```

### attribute_name
`Employee`

### Payload Structure
```json
{
  "attribute_name": "Employee",
  "name": "string (optional)",
  "employee_code": "string (optional)",
  "designation_id": "FK (optional)",
  "department_id": "FK (optional — but no options exist)",
  "mobile_no": 9876543210,
  "email": "string (optional)",
  "date_of_joining": "YYYY-MM-DD (optional)",
  "party_ref_id": "FK (optional)",
  "status": 1,
  "details": [],
  "children": []
}
```

### Key Payload Quirks

1. **`mobile_no` is INTEGER, not string** — The API expects `mobile_no` as an integer (e.g., `9876543210`), NOT a string (`"9876543210"`). This is different from most other modules where phone numbers are strings. Sending a string will result in a 400 error.

2. **`details: []` and `children: []`** — Both arrays are always empty. Employee has no sub-forms, no repeating rows, no KYC, no address, no bank details. This is the only registration module with both arrays empty.

3. **`status` is the only required field** — A payload with only `{"attribute_name": "Employee", "status": 1}` will be accepted.

### FK Dependencies (2 Pools)
| FK Pool | Source | Approx Count |
|---|---|---|
| DESIGNATION_IDS | Designation dropdown | 56 |
| PARTY_REF_IDS | Party Reference dropdown | ~100 |

Note: Department is technically an FK but has 0 options, so it's not usable.

## Data Layer

### FK Pool Loading
Only 2 FK pools are loaded — the smallest of any registration module with FK pools:
```python
DESIGNATION_IDS = fetch_reference_ids("designation")    # ~56 IDs
PARTY_REF_IDS = fetch_reference_ids("party_reference")   # ~100 IDs
```

### Payload Builder
`build_employee_payload()` constructs the API payload:
1. Generates employee name using `^[A-Za-z ]+$` pattern (alpha + spaces only)
2. Generates phone number using `^[6-9]\d{9}$` pattern (Indian mobile format)
3. Generates email address
4. Picks random DESIGNATION_IDS and PARTY_REF_IDS
5. Sets `mobile_no` as INTEGER (critical — not string)
6. Sets `status: 1` (Active)
7. Sets `details: []` and `children: []`
8. Returns complete payload dict

### Generators

**Employee Name** — Generated to match `^[A-Za-z ]+$`:
- Only alphabetic characters and spaces
- No numbers, no special characters, no accents
- Format: `{FirstName} {LastName}` from predefined lists
- Example: "Rajesh Kumar", "Priya Sharma"

**Phone Number** — Generated to match `^[6-9]\d{9}$`:
- Must start with 6, 7, 8, or 9 (Indian mobile prefix rules)
- Followed by 9 random digits
- Total: 10 digits
- Example: "9876543210", "7123456789"
- **IMPORTANT:** Convert to integer before API submission: `int(phone_number)`

### Validation Rules
| Field | Rule | Source |
|---|---|---|
| Employee Name | `^[A-Za-z ]+$` — alpha and spaces only | Server-side |
| Phone Number | `^[6-9]\d{9}$` — Indian mobile format | Server-side |
| mobile_no | Must be INTEGER type in API | Server-side type check |
| Status | Required — must be 0 or 1 | Server-side |
| All other fields | Optional — no validation | — |

## Page Object

### Key Methods

**`fill_employee_form(data)`** — Fills the entire flat form. No stepper navigation needed. Handles:
- Text inputs (Employee Name, Email, Phone)
- FK dropdowns (Designation, Party Reference)
- Date picker (Date of Joining)
- Status toggle

**`skip_department()`** — Explicitly does nothing. This method exists as documentation that Department should be skipped. It's a no-op but serves as a signal to test writers that Department is intentionally omitted.

**`submit_employee()`** — Clicks the Submit button on the form.

### Tricky Bits

1. **No stepper = simple but different** — Every other registration module uses steppers. Employee doesn't. Tests that are written following the stepper pattern (navigate to step, fill, next) won't apply here. The test structure is simpler but the deviation from the norm can confuse engineers who expect steppers.

2. **mobile_no integer type** — The most common mistake in Employee API tests is sending `mobile_no` as a string. The API will return a 400 with a type error. The payload builder handles this automatically, but anyone constructing payloads manually must remember to use `int()`.

3. **Department dropdown is empty** — If a test tries to interact with the Department dropdown, it will fail because there are 0 options. The `skip_department()` method documents this, but it's easy to miss.

4. **Minimal validation** — Because most fields are optional, tests can't rely on validation errors to catch missing data. An Employee with just a status toggle will be created successfully, which can be surprising.

5. **Employee Name regex** — The name field only accepts `^[A-Za-z ]+$`. Tests that generate names with special characters (apostrophes, hyphens) will fail. Common Indian names like "O'Brien" or "De-Souza" are not valid.

### Locator Strategies
- Form fields: `input[formcontrolname='<field>']`
- Status toggle: `mat-slide-toggle` or `mat-checkbox`
- Designation dropdown: `mat-select[formcontrolname='designation_id']`
- Party Reference dropdown: `mat-select[formcontrolname='party_ref_id']`
- Submit button: `button` with text "Submit"
- No stepper headers, no grid containers, no repeating row add buttons

## Known Bugs

| Bug ID | Severity | Description |
|---|---|---|
| — | — | No formally tracked bugs. The module's simplicity limits bug surface area. |

**Known Issues:**
- Department dropdown has 0 options — likely a configuration issue in the ERP, not a code bug
- Minimal validation means junk data can be submitted (only status is required)

## War Stories

### The String Phone Number

An engineer was writing Employee API tests and followed the pattern from the Customer module, where phone numbers are strings. They sent `"mobile_no": "9876543210"` in the payload. The API returned a 400 with the message `"mobile_no must be a number"`. Confused (because phone numbers are strings in every other module), they checked the API documentation — no mention of the integer requirement. They checked the database schema — `mobile_no` was defined as `BIGINT`. The fix was simple (`int(phone_number)`), but the discovery required inspecting the database because the API documentation didn't mention the type constraint. To this day, Employee is the only module where phone numbers are integers.

### The Empty Employee

During a code review, someone noticed that the Employee API accepts a payload with nothing but `status: 1`. As an experiment, they submitted `{"attribute_name": "Employee", "status": 1}`. The API returned 201 Created. The database now had an employee with no name, no phone, no email, no designation — just an ID and an Active status. The downstream reporting module crashed when it tried to generate an employee directory that included this nameless entry. The lesson: "optional" in the API doesn't mean "reasonable to omit." Tests should always fill at least name and phone, even though the API doesn't require it.

### The Department Ghost Town

A new team member was writing a test that fills every field on the Employee form. When they got to the Department dropdown, the test hung — the dropdown opened but had no options. The test was waiting for at least one option to appear (with a 30-second timeout). After the timeout, the test failed. Investigation revealed that the Department reference endpoint returns an empty array. No departments exist in the test environment. The fix was to add a `skip_department()` call and a comment explaining why. The real question — should a department-less employee be valid? — remains unanswered.

## Test Coverage

| Test Type | Status | Count |
|---|---|---|
| API Create Tests | ✅ Passing | ~8 |
| API Update Tests | ✅ Passing | ~5 |
| API Validation Tests | ✅ Passing | ~4 |
| API Batch Create | ✅ Passing | ~2 |
| UI Create Tests | ✅ Passing | ~6 |
| UI Validation Tests | ❌ None | 0 |

## Files

```
registration/
├── employee_page.py        1,036 LOC   # Page object (flat form)
├── employee_data.py          653 LOC   # Data layer, FK pools, generators
├── test_employee_api.py      ~150 LOC   # API create/update tests
├── test_employee_api_validation.py ~100 LOC # API validation tests
├── test_employee_batch.py     ~80 LOC   # Batch creation tests
└── test_employee_ui.py       ~200 LOC   # UI automation tests
```

## What's Missing

1. **UI validation tests** — Zero tests for UI-side validation. No tests verify what happens when you submit the form with: special characters in Employee Name, invalid phone format, invalid email format, no name, etc.

2. **Department field resolution** — The Department dropdown has 0 options. This needs to be either: (a) configured in the test environment, (b) removed from the form if unused, or (c) explicitly documented as skip-with-reason in all test code.

3. **Negative API validation tests** — Missing tests for: string `mobile_no` (type error), special characters in name (regex violation), phone number not starting with 6-9, empty `status` field (the one required field).

4. **Update flow** — No API or UI tests for updating an existing employee. Can you change the designation? Deactivate an employee? Change the phone number?

5. **Employee Name edge cases** — No tests for: maximum length names, single-character names, names with multiple consecutive spaces, names that are just spaces (should fail the regex but worth verifying).

6. **Batch creation edge cases** — The batch creation only tests small batches (~5). No test for large batches (100+) or for duplicate employee names in the same batch.

7. **Status toggle tests** — No dedicated tests for the status toggle. Can you create an employee with `status: 0` (Inactive)? Can you toggle from Active to Inactive via API?

8. **Party Reference relationship** — No tests verify that the `party_ref_id` FK relationship works correctly. What happens if you use an invalid party_ref_id?

9. **Employee code auto-generation** — If Employee Code is auto-generated, no test verifies the generation format or uniqueness.
