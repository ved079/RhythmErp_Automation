# Module: Farmer

> The MOST COMPLEX registration module by tab count — variable stepper structure that morphs based on Farmer Category, with 10 repeating row grids, 7 documented bugs, and HTML name attributes that contain literal tab characters.

## At a Glance

| Section | Value |
|---|---|
| Complexity Rank | 1st most complex (by tab count) |
| Steppers | Variable — Walk-in (3 tabs), FPC Member (6 tabs), Borrower (13 tabs) |
| Repeating Rows | Address, Family, Land, Crop, KYC, Bank, Vehicle, Income, Award, Loan |
| API Tests | None |
| UI Tests | Yes |
| Page Object | `farmer_page.py` (4,027 LOC) |
| Data File | `farmer_data.py` (846 LOC) |
| Batch Create | None |
| attribute_name | `Farmer` |

## The ERP Screen

The Farmer registration screen creates farmer entities in the ERP system. It is the only registration module with a **variable stepper structure** — the number and type of steps changes based on the Farmer Category selection.

**Navigation URL:** `/registration/farmer`

### Farmer Category Selection (Gate Step)
Before the stepper begins, the user must select a Farmer Category. This is a **MULTI-SELECT mat-select** — the only one in the entire repository. The selected category determines which tabs appear:

| Farmer Category | Tab Count | Tabs |
|---|---|---|
| Walk-in | 3 | Basic Details → Address → Bank |
| FPC Member | 6 | Basic Details → Address → Family → Land → Crop → Bank |
| Borrower | 13 | Basic Details → Address → Family → Land → Crop → KYC → Bank → Vehicle → Income → Award → Loan → ... → Submit |

### Step Details

**Basic Details:**
- Farmer Name (free text, required — but see BUG-F03)
- Father's/Husband's Name
- Date of Birth (required — Age is READONLY, auto-calculated)
- Gender (dropdown)
- Farmer Category (multi-select mat-select — see BUG-F05)
- No Of Owner (required — but see BUG-F01 and TRAILING TAB below)
- Email (MUST use lowercase — see BUG-F04)
- Phone Number (see NAME COLLISION note)
- Country (MUST ALWAYS be "India")

**Address Tab (repeating grid):**
- Address Line 1, Address Line 2
- Country, State, District, Taluka, City/Village (cascading FKs)
- Pin Code
- Address Type
- ⚠️ `name='Address'` — collides with Address tab in other categories

**Family Tab (repeating grid):**
- Member Name, Relation, Age, Occupation

**Land Tab (repeating grid):**
- Survey Number, Area, Area Unit, Land Type, Ownership Type
- ⚠️ See BUG-F08 — missing in Edit mode

**Crop Tab (repeating grid):**
- Crop Name, Season, Area, Area Unit
- ⚠️ See BUG-F08 — missing in Edit mode

**KYC Tab (repeating grid):**
- Document Type, Document Number
- ⚠️ See BUG-F08 — missing in Edit mode

**Bank Tab (repeating grid):**
- Bank Name, Branch, Account Number, IFSC, Account Type

**Vehicle Tab (repeating grid):**
- Vehicle Type, Registration Number, Owner

**Income Tab (repeating grid):**
- Source, Amount (see BUG-F06 for Amount validation)

**Award Tab (repeating grid):**
- Award Name, Year, Authority

**Loan Tab (repeating grid):**
- Loan Type, Amount (see BUG-F06), Institution

## API Contract

### Endpoint
`POST /api/registration/farmer` (presumed — no API payload builder exists)

### attribute_name
`Farmer`

### Payload Structure
⚠️ **NO API PAYLOAD BUILDER EXISTS.** The Farmer module is currently UI-only. There is no `build_farmer_payload()` function, no FK pool fetch for API usage, and no way to create a farmer via API in the test suite. The payload structure below is inferred from the UI form fields:

```json
{
  "attribute_name": "Farmer",
  "name": "string",
  "father_husband_name": "string",
  "dob": "YYYY-MM-DD",
  "gender_id": "FK",
  "farmer_category_ids": ["FK"],
  "no_of_owner": "integer",
  "email": "string (lowercase!)",
  "phone_number": "string",
  "country_id": "FK (always India)",
  "details": [],
  "children": [
    {
      "attribute_name": "FarmerAddress",
      "details": [/* repeating address rows */]
    },
    {
      "attribute_name": "FarmerFamily",
      "details": [/* repeating family rows */]
    },
    {
      "attribute_name": "FarmerLand",
      "details": [/* repeating land rows */]
    },
    {
      "attribute_name": "FarmerCrop",
      "details": [/* repeating crop rows */]
    },
    {
      "attribute_name": "FarmerKYC",
      "details": [/* repeating KYC rows */]
    },
    {
      "attribute_name": "FarmerBank",
      "details": [/* repeating bank rows */]
    }
    /* ... more children for Vehicle, Income, Award, Loan */
  ]
}
```

### FK Dependencies
Due to the absence of an API payload builder, FK pools are not formally defined. UI dropdowns pull from:
- Gender IDs
- Farmer Category IDs (multi-select)
- Country/State/District/Taluka/City cascading chain
- Land Type IDs
- Area Unit IDs
- Crop IDs
- Season IDs
- KYC Document Type IDs
- Bank IDs
- Account Type IDs
- Vehicle Type IDs
- Loan Type IDs
- Ownership Type IDs
- Relation IDs
- Occupation IDs

## Data Layer

### Current State: Minimal
The `farmer_data.py` file (846 LOC) provides:
- Hardcoded test data dictionaries for each Farmer Category
- Farmer name generation (basic)
- DOB generation with corresponding Age calculation
- Phone number generation (Indian format)

### Missing Components
- **No FK pool fetching** — all dropdown values are selected from live UI at runtime
- **No `build_farmer_payload()`** — cannot create farmers via API
- **No `generate_batch_payloads()`** — no batch creation capability
- **No address chain generator** — address cascading is handled entirely through UI interactions

### Validation Rules (Observed from UI)
- **Farmer Name**: Should be alpha-only, but BUG-F03 allows special characters
- **Email**: MUST be lowercase (BUG-F04 — uppercase is rejected by server)
- **Age**: READONLY, auto-calculated from DOB
- **Country**: MUST ALWAYS be "India"
- **No Of Owner**: Required field (despite missing asterisk — BUG-F01)
- **Phone Number**: Indian format expected
- **Amount fields**: Should be positive but accept 0 and `.prefix` (BUG-F06)

## Page Object

### Key Methods

**`select_farmer_category(categories)`** — Selects one or more categories from the multi-select mat-select. This is the only multi-select mat-select in the entire repo. The method must handle the mat-select's panel opening, clicking multiple options, and closing the panel.

**`click_stepper_header(step_index)`** — Navigates to a specific stepper tab. Contains a **force-click workaround** that removes the `aria-disabled` attribute before clicking. Without this, the stepper prevents jumping to non-adjacent tabs:
```python
def click_stepper_header(self, step_index):
    header = self.page.locator(f"mat-step-header:nth-of-type({step_index + 1})")
    # Remove aria-disabled to allow jumping to non-adjacent steps
    self.page.evaluate(
        f'document.querySelector("mat-step-header:nth-of-type({step_index + 1})").removeAttribute("aria-disabled")'
    )
    header.click()
```

**`add_address_row(data)`** — Adds a row to the Address grid. ⚠️ Must scope locators to the active panel because `name='Address'` appears in multiple tabs.

**`add_family_row(data)`** — Adds a row to the Family grid.

**`add_land_row(data)`** / **`add_crop_row(data)`** / **`add_kyc_row(data)`** — Grid row helpers for the respective tabs.

**`fill_basic_details(data)`** — Fills the Basic Details form. Must handle the TRAILING TAB character in `No Of Owner`'s HTML name attribute.

### Tricky Bits

1. **TRAILING TAB CHARACTERS in HTML name attributes** — Some input elements have a literal `\t` (tab character) in their `name` attribute. For example: `input[name='No Of Owner\t']`. This means CSS attribute selectors like `input[name='No Of Owner']` will FAIL. **Workaround:** Use XPath `contains()`:
   ```python
   self.page.locator("//input[contains(@name, 'No Of Owner')]")
   ```
   This affects `No Of Owner` and potentially other fields.

2. **NAME COLLISIONS across tabs** — The field `name='Address'` appears in 3 different tabs, and `name='Phone Number'` appears in 2 tabs. If you use a simple `input[name='Address']` selector, you'll match elements in inactive tabs. **All locators MUST be scoped to the active panel**, e.g.:
   ```python
   self.page.locator(".mat-tab-body-active input[name='Address']")
   # or better, scope to the specific stepper content area
   ```

3. **Multi-select mat-select** — The Farmer Category dropdown is the only multi-select mat-select in the entire repo. Standard `select_option()` doesn't work for multi-select. The page object must:
   - Click the mat-select trigger
   - Click each desired option
   - Click outside or press Escape to close the panel
   But see BUG-F05 — the placeholder option is selectable!

4. **Force-click stepper headers** — The stepper's `aria-disabled` attribute prevents clicking non-adjacent tabs. The `click_stepper_header()` method removes this attribute via JavaScript before clicking.

5. **Borrower category 13-tab navigation** — The Borrower category has 13 tabs, making it the longest stepper flow in the entire ERP. Tests must advance through all 13 tabs sequentially. Any failure mid-flow is extremely time-consuming to debug because you have to re-navigate from the beginning.

6. **Age auto-calculation** — The Age field is READONLY and auto-populated from DOB. Tests must NOT attempt to write to the Age field directly. Instead, set the DOB and verify the calculated age.

### Locator Strategies
- Active panel scope: `.mat-tab-body-active` prefix for all form field selectors
- Trailing tab fields: XPath `contains(@name, '...')` instead of CSS `[name='...']`
- Multi-select options: `mat-option` within the open `mat-select` panel
- Stepper headers: `mat-step-header` by index
- Grid rows: `mat-row` within tab-specific grid containers
- Add row buttons: `button` with `mat-icon` text "add" within grid container

## Known Bugs

| Bug ID | Severity | Description |
|---|---|---|
| BUG-F01 | Medium | "No Of Owner" field is required but has no red asterisk indicator, making it appear optional. Tests must always fill it. |
| BUG-F02 | High | Deselecting and reselecting a farmer category freezes the Next/Back buttons. The stepper becomes completely unresponsive. Must refresh the page and start over. |
| BUG-F03 | Medium | Farmer Name accepts special characters (e.g., `@#$%`). No client-side validation for alpha-only names. Server may or may not reject. |
| BUG-F04 | High | Email field rejects uppercase letters. ALWAYS use `.lower()` when generating email addresses. This is a server-side restriction that produces a confusing error message. |
| BUG-F05 | Medium | Farmer Category placeholder text (e.g., "Select Category") is selectable as an option. Selecting it produces undefined behavior. Tests must skip the first option. |
| BUG-F06 | Medium | Amount fields (Income, Loan) accept `0` and values with `.` prefix (e.g., `.500` means `0.5`). No minimum value validation. |
| BUG-F08 | Critical | Edit mode is missing Land, Crop, and KYC tabs entirely. These tabs are visible in Create mode but disappear when editing an existing farmer. Data in these tabs becomes inaccessible. |
| BUG-F09 | Low | Character count indicator (e.g., "45/100") disappears when a validation error is shown for the same field. Returns after error is resolved. |

## War Stories

### The Invisible Tab Character

For months, the Farmer "No Of Owner" field was failing in automated tests with "Element not found" errors. The test code used `input[name='No Of Owner']` — a perfectly reasonable CSS selector. The field was clearly visible on screen. Manual inspection of the DOM showed `name='No Of Owner'`. But Playwright couldn't find it. Someone eventually did a `page.evaluate("document.querySelector('input[name*=Owner]').getAttribute('name').charCodeAt(9)")` and discovered the 10th character was `\t` — a literal tab character appended to the name attribute. The HTML template had an accidental indentation that was being included in the `name` attribute binding. The fix was to switch all such fields to XPath `contains()` selectors. To this day, nobody knows how many other fields might have trailing whitespace in their name attributes.

### The Frozen Stepper

A QA engineer was manually testing the FPC Member flow. They selected "FPC Member" as the category, then accidentally deselected it and reselected it. The stepper headers all became grayed out. The Next button stopped working. The Back button stopped working. Even the Farmer Category dropdown itself became unresponsive. The only recovery was a full page refresh, which of course lost all entered data. This bug (BUG-F02) is still open. The workaround in automation is to select the category ONCE and never modify it. If a test needs to change the category, it must start a fresh registration instead of reselecting.

### The Case-Sensitive Email Trap

An automation engineer spent an entire day debugging why some Farmer creation tests passed and others failed. The failing tests all had one thing in common: the generated email addresses contained uppercase letters (e.g., `JohnDoe@test.com`). The server was silently rejecting these, returning a vague "Invalid data" error with no indication that the email was the problem. After discovering BUG-F04, the fix was trivial — `email.lower()` — but finding it required inspecting the server logs because the error response gave no clues. This is now documented as a hard rule: **ALWAYS lowercase farmer emails**.

### The Phantom Tabs in Edit Mode

A test was written to verify that farmer data persists after creation. The test created a Borrower-type farmer with Land, Crop, and KYC data, then navigated to the Edit screen to verify the data. The test failed — not because the data was wrong, but because the Land, Crop, and KYC tabs simply didn't exist in Edit mode (BUG-F08). The tabs were present during creation but vanished entirely when editing. The data was still in the database but inaccessible through the UI. This is a critical bug that makes it impossible to edit land, crop, or KYC information for any farmer.

## Test Coverage

| Test Type | Status | Count |
|---|---|---|
| API Create Tests | ❌ None | 0 |
| API Update Tests | ❌ None | 0 |
| API Validation Tests | ❌ None | 0 |
| API Batch Create | ❌ None | 0 |
| UI Create — Walk-in | ✅ Passing | ~6 |
| UI Create — FPC Member | ✅ Passing | ~10 |
| UI Create — Borrower | ✅ Passing | ~15 |
| UI Edit Flow | ⚠️ Partial | ~3 (limited by BUG-F08) |
| UI Multi-select Category | ✅ Passing | ~4 |
| UI Repeating Rows | ✅ Passing | ~12 |
| UI Bug Regression | ✅ Passing | ~7 |

## Files

```
registration/
├── farmer_page.py       4,027 LOC   # Page object — largest in registration
├── farmer_data.py         846 LOC   # Data layer, test data, generators
├── test_farmer_ui.py    ~1,200 LOC  # UI automation tests (all categories)
└── (no API test files)              # Major gap
```

## What's Missing

1. **API payload builder** — The most critical gap. Without `build_farmer_payload()`, there are no API tests, no batch creation, no way to rapidly seed farmer data for other tests. Building this requires mapping all 10 repeating row types to their API `children` structures.

2. **API tests** — Zero API test coverage. No create, update, delete, or validation tests via API. This means no fast feedback on server-side logic changes.

3. **Batch creation** — No `generate_batch_payloads()` for bulk farmer creation. For load testing or data seeding, farmers must be created one at a time through the UI, which is extremely slow for the 13-tab Borrower flow.

4. **FK pool definitions** — No formal FK ID pools. All dropdown selections happen through live UI interaction, making tests slow and dependent on the application being fully operational.

5. **Edit mode coverage** — BUG-F08 makes Land/Crop/KYC tabs invisible in Edit mode. There are no tests for editing these data sections because they're inaccessible. This also means no regression test will catch when this bug is fixed.

6. **Negative test cases** — Missing tests for: special characters in Farmer Name (BUG-F03 regression), uppercase email (BUG-F04 regression), 0-value amounts (BUG-F06 regression), selecting category placeholder (BUG-F05 regression).

7. **Cross-category data preservation** — No tests verify what happens to data when a farmer's category is changed (e.g., Walk-in → Borrower). Does the new tab data get added? Does the old tab data persist?

8. **Concurrent field name scoping tests** — No dedicated tests for the `name='Address'` collision across tabs or the `name='Phone Number'` collision. The locator scoping strategy is implemented but not explicitly tested.

9. **Trailing tab character inventory** — Only `No Of Owner` is known to have a trailing `\t`. No systematic scan has been done to check if other fields have the same issue.

10. **Performance tests** — The 13-tab Borrower flow takes a long time even in automation. No benchmarks exist for acceptable completion time.
