# Module: Designation

> **The simplest module in Common Settings.** Three fields, zero FK pools, one toggle — if you're new to this project, read this doc first to understand the baseline patterns before tackling the complex modules.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Common Settings |
| **Complexity** | Simple (lowest in Common Settings) |
| **Steppers** | 0 — flat popup form |
| **Repeating rows** | No |
| **API tests** | ✅ payload, schema, perf |
| **UI tests** | ✅ validation (~1265 LOC) |
| **Page object** | ✅ designation_page.py (940 LOC) |
| **Data file** | ✅ designation_data.py (337 LOC) |
| **batch_create** | ✅ |
| **Report generator** | ✅ des_report_generator.py (339 LOC) |

---

## The ERP Screen

Designation is found under **Common Settings → Designation** in the ERP sidebar. It's a flat popup form with 3 fields:

- **Name** — text input, `type="character"` (letters and spaces ONLY), required. The frontend pattern validator rejects digits, underscores, and all special characters with an `"Invalid Name"` mat-error. This is the most restrictive `type="character"` field in the project.
- **Description** — text input, `type="character"`, optional. Can be left empty.
- **Status** — toggle switch (Active/Inactive). Uses `app-slide-toggle-v2` component (not a standard checkbox). Default is Active.

The form opens as a popup (`.edit_pop_up` dialog), not a stepper. There are no children, no FK dropdowns, no repeating rows — just three flat fields.

### Navigation URL
`https://rhythmerp.algorhythms.in/#/dynamic-screens/Designation`

### Key UI Behaviors

1. **Name field validation is immediate** — Angular's `type="character"` validator fires on blur, showing `mat-error` instantly. No server round-trip needed.
2. **Duplicate names accepted silently** — the backend has NO duplicate name validation. Submitting "CEO" when "CEO" already exists creates a second "CEO" record with no error or warning.
3. **Success SweetAlert appears** — unlike Tax Authority and Tax Rate, Designation DOES show a "Your record has been added successfully!" SweetAlert2 popup after create/update.
4. **Toggle uses app-slide-toggle-v2** — not a standard Angular Material slide-toggle. The `.slider` child element is the click target, not the host element.

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
```

```json
{
    "id": "",
    "attribute_name": "Designation",
    "name": "Managing Director",
    "description": "Senior management role",
    "status": true
}
```

### Field Mapping

| UI Field | API Key | Type | Required | Notes |
|----------|---------|------|----------|-------|
| Name | `name` | string | Yes | Letters and spaces only (frontend enforced) |
| Description | `description` | string | No | Can be `null` or empty string |
| Status | `status` | boolean | No | Defaults to `true` |

### FK Dependencies

**None.** Designation has zero FK dropdown fields — one of only 3 modules (with Season and Bank) that have no foreign key dependencies. The `dropdown_ids` parameter in `build_designation_api_payload()` exists purely for interface consistency with other modules.

---

## Data Layer

### FK Pools

None. `DEFAULT_DESIGNATION_FK_IDS = {}`

### Payload Builder

```python
def build_designation_api_payload(data=None, dropdown_ids=None):
    if data is None:
        data = generate_valid_designation_data()
    return {
        "id": "",
        "attribute_name": "Designation",
        "name": data.get("name", ""),
        "description": data.get("description", "") or None,
        "status": data.get("status", True),
    }
```

The `dropdown_ids` parameter is accepted but completely ignored — it exists so that `generate_batch_payloads()` has the same signature as modules that DO have FK dropdowns.

### Generators

- `generate_designation_name(prefix="AutoDesig")` — generates a name with random 8-char alphabetic suffix (e.g. "AutoDesig XRKQWMNP"). Always safe for `type="character"`.
- `generate_realistic_designation_name()` — picks from 87 realistic Indian job titles across categories (Senior Management, Middle Management, Supervisory, Officers & Executives, Coordinators & Analysts, Engineers & Technical, Clerical & Administrative, Inspectors & Auditors, Technicians, Specialized).
- `reset_designation_name_pool()` — clears the dedup tracker before a new batch. **MUST call this before generating a batch** or you'll get suffixed names like "Manager XRK" instead of "Manager".
- `generate_string_255()` / `generate_string_256()` — boundary test strings (all alphabetic + spaces, passes `type="character"`).

### Validation Rules

```python
FIELD_VALIDATION_RULES = {
    "name": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Letters and spaces only. Frontend rejects digits, underscores, "
                 "special chars with 'Invalid Name' mat-error.",
    },
    "description": {
        "type": "character",
        "required": False,
        "max_length": 255,
    },
    "status": {
        "type": "toggle",
        "required": False,
        "default": True,
    },
}
```

**Critical gotcha**: The `type="character"` validator on Name is the strictest in the project. Test data generators must NEVER include digits, underscores, or special characters in designation names. The `generate_designation_name()` function uses `string.ascii_uppercase` specifically to avoid this trap.

---

## Page Object

### Key Methods

| Method | Purpose |
|--------|---------|
| `navigate_to_page()` | Opens Designation screen via direct URL |
| `open_add_form()` | Clicks Add button via JS (falls back to Selenium) |
| `fill_designation_form(data)` | Fills Name, Description, and toggles Status if needed |
| `submit()` | Clicks Submit via JS popup button |
| `_handle_submit_response()` | **v5 combined handler** — single poll for any SweetAlert |
| `create_designation(data)` | One-call flow: open → fill → submit → handle response |
| `edit_designation(name, data)` | One-call flow: search → edit → fill → update → handle |
| `search_designation(name)` | Multi-strategy search (direct + toggle + JS events) |
| `verify_designation_exists(name)` | Fast 2s poll with 0.2s intervals |
| `get_mat_error_text(field)` | DOM-walking mat-error extractor (up to 20 parent levels) |

### Tricky Bits

**1. Does NOT extend BasePage — uses it via composition**
Wait, actually it DOES extend BasePage. The class declaration is `class DesignationPage(BasePage)`. But it implements many methods that BasePage doesn't provide. Don't confuse this with Error Code Mst which truly is standalone.

**2. v5 Speed Optimization: `_handle_submit_response()`**
The single biggest speed win in this module. The old pattern was:
```
is_validation_alert_present(2s timeout) → handle_success_alert(2s timeout) = 4-5s per create
```
The new pattern:
```
Single 3s poll for ANY SweetAlert → read title + icon → click appropriate button = 1-2s per create
```
This saves 2-3 seconds per create operation. Across 44 tests, that's ~2 minutes saved per test run.

**3. Toggle clicking targets `.slider`, not the host element**
```python
js = """
var toggle = document.querySelector('app-slide-toggle-v2');
var slider = toggle.querySelector('.slider');  // THIS is the click target
slider.click();
"""
```
Clicking `app-slide-toggle-v2` directly does nothing. The `.slider` child is the actual interactive element.

**4. `_set_input()` uses JS native setter**
All text input uses `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set` to bypass Angular's change detection issues. Simple `send_keys()` was abandoned early because Angular would sometimes not register the value.

### Locator Strategies

| Element | Locator | Notes |
|---------|---------|-------|
| Name input | `input[name='Name']` | Standard name attribute |
| Description input | `input[name='Description']` | Standard name attribute |
| Submit button | `.popup-footer button` containing "Submit" | Text-based, not CSS class |
| Update button | `.popup-footer button` containing "Update" | Same strategy as Submit |
| 3-dot menu | `td.cdk-column-actions button` | Standard kebab menu |
| Toggle | `app-slide-toggle-v2 .slider` | Click the slider child, not the host |

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| DES-001 | Medium | No duplicate name validation — duplicate designations accepted silently. Submitting "CEO" when "CEO" already exists creates a second identical record. |
| DES-002 | Low | No max-length validation on Name field — strings longer than 255 characters are accepted by the frontend (though the backend may truncate). |
| DES-003 | Low | Description field accepts digits and special chars while Name field rejects them — inconsistent `type="character"` enforcement. |

---

## War Stories

### "The Duplicate Name Bug That Nobody Cares About"
Designation was the first module where we discovered the "no duplicate validation" pattern. We created a test expecting a validation error when submitting "CEO" twice. The test failed — the ERP happily accepted the duplicate. We reported it, but the business team said "it's fine, we'll manage it manually." This bug exists in Season, Bank, UOM, and several other modules. If you're writing a duplicate-name test for ANY module, expect it to fail.

### "Invalid Name But Valid Data"
The `type="character"` validator on the Name field was a surprise. We initially generated names like "Test_Manager_001" (with underscores and digits) and they were all rejected with "Invalid Name" mat-error. The fix was to switch all generators to alphabetic-only suffixes. This lesson was painful enough that every data file now has a comment: `"Uses spaces (not underscores) because the ERP Name field has a type='character' validator that rejects underscores."`

### "The Report Generator That Almost Wasn't"
Designation is the ONLY module with its own report generator (`des_report_generator.py`). It was written early in the project when we thought every module would need one. Later, a shared `cs_report_generator.py` was created for all Common Settings modules. The Designation-specific one is kept for backward compatibility but is effectively deprecated — use the shared one for new work.

---

## Test Coverage

| Test Type | Status | Count |
|-----------|--------|-------|
| API: Payload | ✅ Complete | ~15 tests |
| API: Schema | ✅ Complete | ~8 tests |
| API: Performance | ✅ Complete | ~5 tests |
| UI: Validation | ✅ Complete | ~20 tests |

### Key Validation Tests
- Valid create with all fields
- Valid create with name only (description optional)
- Empty name → Validation Failed SweetAlert
- Special chars in name → "Invalid Name" mat-error
- Digits in name → "Invalid Name" mat-error
- Underscores in name → "Invalid Name" mat-error
- Spaces-only name → "Invalid Name" mat-error
- Duplicate name → **accepted** (BUG DES-001)
- 255-char name → accepted
- 256-char name → accepted (no max-length validation)
- Toggle status → Active/Inactive switch
- View mode → read-only, no Submit/Update button
- Edit → Update button appears, changes persist
- History → shows audit trail

---

## Files

```
pages/common_settings/modules/designation/
├── designation_page.py             (940 LOC)
├── des_report_generator.py         (339 LOC)
├── data/
│   └── designation_data.py         (337 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_designation_validation.py  (1265 LOC)
    └── api/
        ├── conftest.py
        ├── test_designation_payload.py
        ├── test_designation_schema.py
        └── test_designation_perf.py
```

---

## Lessons for New Modules

1. **Start with Designation as your template** — it's the simplest working example of every pattern: popup form, JS input, SweetAlert handling, toggle, search, table verification, and one-call create/edit flows.
2. **Never assume duplicate validation exists** — test for it, but don't expect it. Most modules don't validate duplicates.
3. **`type="character"` is a landmine** — always check the actual field type before generating test data. Some modules use `type="text"` which accepts anything, while others use `type="character"` which is very restrictive.
4. **The v5 `_handle_submit_response()` pattern** should be copied to every module that shows SweetAlert — it saves 2-3 seconds per operation vs. the old double-wait approach.
