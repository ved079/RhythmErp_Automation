# Module: Season

> **The module that taught us the ERP can hang forever.** A duplicate "Rabi" name will freeze the entire browser session indefinitely. This module also has the deepest Angular state inspection code in the project — clearly born from painful debugging sessions.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Common Settings |
| **Complexity** | Simple (3 fields, 0 FK pools) |
| **Steppers** | 0 — flat popup form |
| **Repeating rows** | No |
| **API tests** | ✅ payload, schema, perf |
| **UI tests** | ✅ validation (~807 LOC) |
| **Page object** | ✅ season_page.py (920 LOC) |
| **Data file** | ✅ season_data.py (425 LOC) |
| **batch_create** | ✅ |

---

## The ERP Screen

Season is found under **Common Settings → Season** in the ERP sidebar. It's a flat popup form with 3 fields:

- **Name** — text input, `type="character"` (letters and spaces only), required. Rejects underscores, digits, and special characters just like Designation.
- **Description** — text input, `type="character"`, optional. Can be left blank.
- **Status** — checkbox (not a toggle!). Uses a standard `input[type='checkbox']`, unlike Designation's `app-slide-toggle-v2`.

The form opens as a popup (`.edit_pop_up` dialog). The kebab menu uses **`button.erp-row-trigger`** — a different CSS class than the `td.cdk-column-actions button` used by most other modules. This inconsistency cost hours of debugging.

### Navigation URL
`https://rhythmerp.algorhythms.in/#/dynamic-screens/Season`

### Key UI Behaviors

1. **Success SweetAlert appears** — Season shows "Your record has been added successfully!" after create, and "Your record has been updated successfully!" after edit.
2. **Duplicate "Rabi" causes INFINITE HANG** — submitting a season named "Rabi" when "Rabi" already exists causes the system to hang indefinitely. No error, no timeout, just a frozen browser. This is the most critical known bug in Common Settings.
3. **Status is a CHECKBOX, not a toggle** — unlike Designation's `app-slide-toggle-v2`, Season uses a plain `input[type='checkbox']`. This is inconsistent with the rest of the ERP.
4. **`type="character"` rejects SQL injection chars** — single quotes, semicolons, and dashes are all blocked by the frontend validator. SQL injection testing is effectively impossible on this field.

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
```

```json
{
    "id": "",
    "attribute_name": "Season",
    "name": "Kharif",
    "description": "Monsoon cropping season",
    "status": true
}
```

### Field Mapping

| UI Field | API Key | Type | Required | Notes |
|----------|---------|------|----------|-------|
| Name | `name` | string | Yes | Letters and spaces only (frontend enforced) |
| Description | `description` | string | No | Can be `null` or empty |
| Status | `status` | boolean | No | Defaults to `true` |

### FK Dependencies

**None.** Season has zero FK dropdown fields. `DEFAULT_SEASON_FK_IDS = {}`

---

## Data Layer

### FK Pools

None.

### Payload Builder

```python
def build_season_api_payload(data=None, dropdown_ids=None):
    if data is None:
        data = valid_season_with_description()
    return {
        "id": "",
        "attribute_name": "Season",
        "name": data.get(FIELD_NAME, ""),
        "description": data.get(FIELD_DESCRIPTION, "") or None,
        "status": True,
    }
```

### Generators

- `valid_season_name()` — generates `"SEASON XXXXXX"` with random alphanumeric suffix
- `generate_realistic_season_name()` — picks from 38 realistic Indian agricultural/commodity season names across categories: major cropping (Kharif, Rabi, Zaid), climatic, agricultural variants, commodity-specific, regional Indian (Vasant Ritu, Grishma Ritu, etc.), sugarcane/cotton, trading, and fiscal/calendar
- `SEASON_DESCRIPTIONS` — dict mapping each realistic name to a professional description (e.g. "Rabi" → "Winter cropping season (October–March), major crops: wheat, mustard, gram")
- `duplicate_name()` — returns `{"Name": "Rabi", ...}` for testing the infinite hang bug. **USE WITH CAUTION AND TIMEOUT.**

### Validation Rules

```python
FIELD_VALIDATION_RULES = {
    "name": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "Letters and spaces only (type='character'). Frontend rejects "
                 "underscores, digits, special chars.",
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

---

## Page Object

### Key Methods

| Method | Purpose |
|--------|---------|
| `navigate_to_season()` | Direct URL navigation + wait for table |
| `open_add_form()` | Clicks Add button via JS |
| `enter_name(name)` | JS native setter (no intermediate empty state) |
| `click_submit()` | Click Submit + `_handle_post_submit()` |
| `_handle_post_submit()` | **THE deep inspection method** — see below |
| `search_record(text)` | All-JS search (open toggle → set value → Enter) |
| `search_and_verify(name)` | Combined search + existence check (10s poll) |
| `_dismiss_overlays_and_popups()` | Uses `Keys.ESCAPE` (inconsistency with Bank!) |

### Tricky Bits

**1. The Deep Angular State Inspector in `_handle_post_submit()`**
This method is unlike anything else in the project. When a validation alert is detected after submit, it doesn't just log the alert — it dumps the ENTIRE Angular form state:

```python
debug_info = self.driver.execute_script("""
    var result = {};
    // DOM values
    result.dom_name = nameEl ? nameEl.value : 'NOT_FOUND';
    result.dom_desc = descEl ? descEl.value : 'NOT_FOUND';
    // mat-error elements
    result.mat_errors = [];
    // ng-invalid classes
    result.ng_invalid_count = invalids.length;
    result.ng_invalid_details = [...];  // tag + class for each
    // Angular FormControl state
    result.has_ng_context = !!formEl.__ngContext__;
    // All form inputs with name, type, value, required, disabled, classes
    result.all_inputs = [...];
    return result;
""")
```

This was clearly added during a painful debugging session where validation failures were opaque. The lesson: if you're fighting Angular validation, dump everything — DOM values, Angular classes, FormControl state, and all input metadata. It's the only way to figure out what Angular thinks is wrong.

**2. Kebab menu uses `button.erp-row-trigger`**
Most modules use `td.cdk-column-actions button` for the 3-dot menu. Season uses `button.erp-row-trigger`. This is a **different CSS class** and your locators must match. The `_click_action_menu_item()` method handles this, but if you're writing a new test, be aware of this inconsistency.

**3. Uses `Keys.ESCAPE` — inconsistency with Bank**
The `_dismiss_overlays_and_popups()` method uses `ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()` to dismiss overlays. This directly contradicts the Bank module's rule: "NEVER use Keys.ESCAPE." The truth is more nuanced:
- Bank: Escape closes the ENTIRE popup form, losing all data → NEVER use it
- Season: Escape only dismisses CDK overlay panels → safe to use

**Always test what Escape does on YOUR specific module before using it.**

**4. `enter_name()` uses JS native setter without clearing first**
Unlike some modules that clear the input then set the value (triggering Angular's required-field validation on the empty state), Season sets the value in one atomic step:
```python
nativeSet.call(el, arguments[0]);  // Set value directly — no intermediate empty state
el.dispatchEvent(new Event('input', {bubbles: true}));
el.dispatchEvent(new Event('change', {bubbles: true}));
el.dispatchEvent(new Event('blur', {bubbles: true}));
```
This avoids the "required field flashes red" issue during edit mode where the field already has a value.

### Locator Strategies

| Element | Locator | Notes |
|---------|---------|-------|
| Name input | `input[name='Name']` | Standard |
| Description input | `input[name='Description']` | Standard |
| Status checkbox | `div.edit_pop_up input[type='checkbox']` | Checkbox, NOT toggle |
| 3-dot menu | `button.erp-row-trigger` | Different from most modules! |
| Submit button | `.popup-footer button[type='submit']` | type='submit', not text match |
| Search toggle | `button[aria-label='Search']` | aria-label, not CSS class |

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| SEA-001 | **Critical** | Duplicate name "Rabi" causes system to **HANG INDEFINITELY**. No error, no timeout, no response — the browser tab becomes completely unresponsive. Must kill the tab. Other duplicate names may also trigger this. |
| SEA-002 | Medium | No general duplicate name validation — duplicates of non-"Rabi" names accepted silently (same as DES-001). |
| SEA-003 | Low | Status field is a checkbox while other modules use toggle switches — inconsistent UX. |

**SEA-001 is the most dangerous bug in Common Settings.** If you're running automated tests against a live ERP, the duplicate "Rabi" test will hang your entire test suite. Always wrap duplicate-name tests in a timeout mechanism.

---

## War Stories

### "The Day Rabi Killed Our Test Suite"
We had a test that tried to create a season named "Rabi" to verify duplicate validation. The test never completed. The browser hung. The Selenium WebDriver timed out after 300 seconds. The entire CI pipeline stalled. After investigation, we discovered that "Rabi" is a pre-existing record in the ERP, and the duplicate check doesn't return an error — it just... hangs. The HTTP request never completes. The server never responds.

**The fix in test data**: `duplicate_name()` returns `{"Name": "Rabi"}` but tests that use it MUST set a page-load timeout or JavaScript timeout. Never run this test in a CI pipeline without a hard timeout.

### "The Angular State Inspector Was Born Here"
During early development, Season's validation failures were maddeningly opaque. The SweetAlert would say "Validation Failed" but wouldn't say WHICH field failed. Angular's reactive form would mark fields as `ng-invalid` but we couldn't see which ones from Selenium. So we wrote the deep inspector in `_handle_post_submit()` that dumps everything — DOM values, mat-error text, ng-invalid classes, Angular __ngContext__, and all input metadata. That inspector saved us dozens of hours. It's still there, and it's still useful when validation failures are mysterious.

### "The Escape Key Inconsistency"
Season uses `Keys.ESCAPE` in `_dismiss_overlays_and_popups()`. Bank says "NEVER use Keys.ESCAPE." Who's right? Both, for their specific modules. In Bank, pressing Escape while a dropdown is open closes the entire popup form. In Season, Escape only dismisses the dropdown overlay. **The lesson: every module has its own Escape key behavior. Test it before assuming anything.**

---

## Test Coverage

| Test Type | Status | Count |
|-----------|--------|-------|
| API: Payload | ✅ Complete | ~15 tests |
| API: Schema | ✅ Complete | ~8 tests |
| API: Performance | ✅ Complete | ~5 tests |
| UI: Validation | ✅ Complete | ~18 tests |

### Key Validation Tests
- Valid create with name + description
- Valid create with name only (description optional)
- Empty name → Validation Failed SweetAlert
- Special chars in name → rejected by `type="character"`
- SQL injection chars → rejected by `type="character"`
- XSS script tags → rejected by `type="character"`
- Duplicate name "Rabi" → **CRITICAL: system hangs** (test with timeout!)
- Very long name (200 chars) → accepted
- Numbers-only name → behavior depends on `type="character"`
- Leading/trailing spaces → trimmed or accepted
- View mode → read-only verification
- Edit → update and verify
- History → audit trail check

---

## Files

```
pages/common_settings/modules/season/
├── season_page.py                  (920 LOC)
├── Season_Automation_Guide.md
├── data/
│   └── season_data.py              (425 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_season_validation.py   (807 LOC)
    └── api/
        ├── conftest.py
        ├── test_season_payload.py
        ├── test_season_schema.py
        └── test_season_perf.py
```

---

## Lessons for New Modules

1. **Always test what duplicate names do** — some modules reject them, some accept silently, and some (like Season) hang indefinitely. Don't assume any particular behavior.
2. **The `erp-row-trigger` vs `cdk-column-actions` inconsistency** means you should never copy-paste locators from another module without verifying the actual CSS classes on your target page.
3. **The deep Angular state inspector** in `_handle_post_submit()` is worth copying to any module where validation failures are opaque. It turns "Validation Failed" into a complete diagnostic dump.
4. **`type="character"` blocks SQL injection** — if you're testing security on a `type="character"` field, save yourself the time. The frontend validator rejects injection chars before they reach the server.
