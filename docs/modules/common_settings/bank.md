# Module: Bank

> **The OG module.** This was the first module automated in the entire project. Many patterns invented here were copied to every other module. Understanding Bank means understanding 80% of the codebase's conventions.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Common Settings |
| **Complexity** | Medium |
| **Steppers** | 0 — popup form (NOT a stepper) |
| **Repeating rows** | No |
| **API tests** | ✅ payload, schema, perf |
| **UI tests** | ✅ validation |
| **Page object** | ✅ (1,737 LOC) |
| **Data file** | ✅ (545 LOC) |
| **batch_create** | ✅ |

---

## The ERP Screen

Bank is found under **Common Settings → Bank** in the ERP sidebar. It's a simple popup form with these fields:
- **Bank Name** — text, required, ALL UPPERCASE only, minimum 10 characters
- **IFSC Code** — text, required, exactly 11 characters
- **Account Type** — mat-select dropdown (Current / Saving)
- **GL Account** — mat-select dropdown (10+ options like "BANK 1", "Cash", etc.)

The form opens as a popup (`.big-model` dialog), not a stepper. This is important — many later modules ARE steppers, but Bank established the patterns for popup interaction.

### Navigation URL
`/#/master-setup/bank`

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
```

```json
{
    "attribute_name": "Bank",
    "bank_name": "TEST BANK ABCD",
    "ifsc_code": "SBIN0001234",
    "account_type": 1849,
    "account_ref_id": 1005,
    "details": [],
    "children": []
}
```

- `details` and `children` are always empty — Bank has no stepper children or repeating rows
- `account_type` and `account_ref_id` are FK references (integer IDs, not display strings)

---

## Data Layer

### FK Pools

```python
ACCOUNT_TYPE_IDS = {"Current": 1849, "Saving": 1850}
ACCOUNT_REF_IDS = {
    "BANK 1": 1005, "BANK 2": 1006, "BANK 3": 1007,
    "Cash": 767, "Bank OD A/c": 768, ...
}
```

### Payload Builder

```python
def build_bank_api_payload(fk_ids=None):
    fk = {**DEFAULT_BANK_FK_IDS, **(fk_ids or {})}
    return {
        "attribute_name": "Bank",
        "bank_name": f"TEST BANK {uuid4().hex[:6].upper()}",
        "ifsc_code": generate_ifsc(),
        "account_type": fk["account_type"],
        "account_ref_id": fk["account_ref_id"],
        "details": [],
        "children": [],
    }
```

### Generators

- `generate_ifsc()` — generates a realistic 11-character IFSC code (4 letters + 0 + 6 digits, matching the Indian banking format)
- Bank names are always generated in UPPERCASE because the ERP enforces this

---

## Page Object

### Key Methods

| Method | Purpose |
|--------|---------|
| `navigate_to_page()` | Opens the Bank screen via direct URL |
| `fill_all_fields(data)` | Fills the entire popup form |
| `submit_form()` | Clicks Submit (or Update in edit mode) |
| `verify_bank_exists(name)` | Searches for a bank in the table |

### Tricky Bits

**1. No `formcontrolname` attributes**
Unlike most modules, Bank's inputs only have `name` attributes. And they're case-sensitive — `name="Bank Name"` not `name="bankName"`. All locators must use exact case:
```python
BANK_NAME_INPUT = ("css", 'input[name="Bank Name"]')
```

**2. Edit mode says "Update" not "Submit"**
When editing an existing bank, the submit button text changes from "Submit" to "Update". The page object handles both:
```python
def submit_form(self):
    # Try Update first (edit mode), then Submit (create mode)
    try:
        update_btn = self.find_clickable_element(("xpath", "//button[contains(.,'Update')]"))
        update_btn.click()
    except:
        submit_btn = self.find_clickable_element(("xpath", "//button[contains(.,'Submit')]"))
        submit_btn.click()
```

**3. ALL UPPERCASE bank names**
The ERP rejects lowercase bank names. Always generate names in uppercase:
```python
bank_name = f"TEST BANK {uuid4().hex[:6].upper()}"
```

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| BUG-003 | Medium | Global search does NOT filter the Bank table — typing in search has no effect |
| BUG-004 | Critical | Browser-clicked mat-select options do NOT update Angular reactive form model — must use JS value-setter |
| BUG-005 | Medium | No Delete functionality — the Delete button doesn't exist |
| BUG-006 | Low | History button opens View popup instead of history |

BUG-004 is the most impactful. It was discovered in Bank and the fix (JS value-setter + dispatchEvent) became the standard pattern for every module that followed.

---

## War Stories

### "Dropdown Selections Don't Work"
This was the first major discovery in the project. Selenium could click dropdown options, the visual showed the selected value, but Angular's form model didn't register it. The form would submit with empty dropdown values. The fix — dispatching 8 different events and toggling CSS classes — was developed here and became `_sync_dropdown_angular_model()` used everywhere.

### "Never Use Keys.ESCAPE"
Discovered in Bank: pressing Escape while a dropdown overlay is open closes the entire popup form instead of just the overlay. Lost all entered data. This became a project-wide rule documented in every module.

### "IFSC Code Must Be Exactly 11 Characters"
The ERP validates IFSC code length on the server side. Shorter or longer codes are rejected with a vague error. The `generate_ifsc()` function was built to always produce exactly 11 characters.

---

## Test Coverage

| Test Type | Status | Count |
|-----------|--------|-------|
| API: Payload | ✅ Complete | ~25 tests |
| API: Schema | ✅ Complete | ~10 tests |
| API: Performance | ✅ Complete | ~5 tests |
| UI: Validation | ✅ Complete | ~15 tests |

---

## Files

```
pages/common_settings/modules/bank/
├── bank_page.py                    (1,737 LOC)
├── data/
│   └── bank_data.py                (545 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_bank_validation.py
    └── api/
        ├── conftest.py
        ├── test_bank_payload.py
        ├── test_bank_schema.py
        └── test_bank_perf.py
```

---

## Lessons for New Modules

1. **Start with Bank's patterns** — popup interaction, JS value-setter, backdrop click for overlays
2. **Test single create before batch_create** — if the data layer is wrong, batch_create will fail ALL entries
3. **Always check for `formcontrolname` vs `name`** — Bank uses `name`, most others use `formcontrolname`. Your locators must match.
4. **Don't assume success SweetAlert exists** — Bank has one, but many modules don't. Check the actual ERP behavior.
