# Module: Tax Rate

> **The most complex module in Common Settings.** The ONLY module with a stepper, the ONLY module where Edit is disabled (you must use "Version" instead), and the module with a critical note in the code: "NEVER remove `.cdk-overlay-container` — kills Angular's overlay rendering engine permanently."

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Common Settings |
| **Complexity** | **Highest** in Common Settings |
| **Steppers** | 1 — "Define Tax Rate Details" with sub-table |
| **Repeating rows** | Yes — HSN Number + Tax Rate rows in sub-table |
| **API tests** | ✅ payload, schema, perf |
| **UI tests** | ✅ validation (~418 LOC) |
| **Page object** | ✅ tax_rate_page.py (1139 LOC) |
| **Data file** | ✅ tax_rate_data.py (461 LOC) |
| **batch_create** | ✅ |

---

## The ERP Screen

Tax Rate is found under **Common Settings → Tax Rate** in the ERP sidebar. It has a **stepper** structure — the only Common Settings module that does:

### Header Fields (6 fields):
- **Tax Rate Name** — text input, required. (e.g. "GST 18%")
- **Tax Type** — mat-select dropdown, required. 1 option: GST (ID=93)
- **Tax Authority** — mat-select dropdown, required. 20 Indian GST authorities (IDs 103-122)
- **From Date** — date picker, required. **Has `name=null`** — must use mat-label traversal for locator
- **To Date** — date picker, required. **Has `name=null`** — must use mat-label traversal. Defaults to 2099-12-30
- **Revision Status** — text input, required. Enum: "Active"

### Sub-Table ("Define Tax Rate Details" stepper):
- **HSN Number** — mat-select dropdown in each row. 24 HSN/SAC codes available (IDs 108-131)
- **Tax Rate** — numeric input in each row. Tax percentage (e.g. 18.0, 5.0, 28.0)

The sub-table starts with **1 empty row pre-created**. Additional rows are added by clicking the "Add" button.

### Navigation URL
Defined in `tax_rate_data.py` as `PAGE_URL`.

### Key UI Behaviors

1. **Edit button is DISABLED** — you cannot edit a tax rate directly. Instead, you use the "Version" button (folder icon) which opens the form with a "Create Version" button. This creates a new version of the tax rate with updated values.
2. **NO success SweetAlert** — the form closes silently on both create and version, like Error Code Mst and Tax Authority.
3. **From Date auto-fills** when the form opens. To Date defaults to 2099-12-30.
4. **Sub-table fills BOTTOM-UP** — `fill_sub_table()` iterates from `needed-1` down to `0`. This avoids Angular re-rendering issues when earlier rows are modified.
5. **4 action buttons per row** — View (eye), Edit (pencil, DISABLED), Version (folder), History (archive). The Version button is unique to this module.

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
```

```json
{
    "id": "",
    "tax_rate_name": "GST 18%",
    "tax_type_ref_id": 93,
    "tax_authority_ref_id": 103,
    "from_date": "2025-04-01",
    "to_date": "2026-03-31",
    "revision_status": "Active",
    "attribute_name": "TaxRate",
    "children": [
        {
            "stepper_name": "Define Tax Rate Details",
            "is_stepper": true,
            "details": [
                {"hsn_sac_number": 108, "tax_rate": 18.0},
                {"hsn_sac_number": 109, "tax_rate": 18.0}
            ],
            "children": []
        }
    ]
}
```

### Critical: The `children[]` structure

Tax Rate is the ONLY Common Settings module with a `children[]` array containing stepper data. The structure:
- `children[0].stepper_name` = "Define Tax Rate Details"
- `children[0].is_stepper` = `true`
- `children[0].details[]` = array of sub-table row objects
- `children[0].children[]` = always empty (no nested steppers)

Other modules have `"children": []` (empty). This structural difference means Tax Rate's API payload builder is fundamentally different from all flat-screen modules.

### FK Dependencies

| FK Field | Pool Name | Count | Key IDs |
|----------|-----------|-------|---------|
| tax_type_ref_id | TAX_TYPE_IDS | 1 | GST=93 |
| tax_authority_ref_id | TAX_AUTHORITY_IDS | 20 | CGST=103, SGST=104, IGST=105, + 17 more (103-122) |
| hsn_sac_number (sub-table) | HSN_SAC_NUMBER_IDS | 24 | 995411=108, 995412=109, + 22 more (108-131) |

---

## Data Layer

### FK Pools

```python
TAX_TYPE_IDS = {"GST": 93}

TAX_AUTHORITY_IDS = {
    "CGST Authority": 103, "SGST Authority": 104, "IGST Authority": 105,
    "GST Audit Office Mumbai": 106, "GST Audit Office Delhi": 107,
    "GST Commissionerate Pune": 108, "GST Commissionerate Chennai": 109,
    "GST Commissionerate Kolkata": 110, "Central Tax Authority Bengaluru": 111,
    "Central Tax Authority Hyderabad": 112, "State Tax Authority Gujarat": 113,
    "State Tax Authority Rajasthan": 114, "State Tax Authority Maharashtra": 115,
    "State Tax Authority Karnataka": 116, "GST Refund Office Mumbai": 117,
    "GST Refund Office Delhi": 118, "Customs GST Authority": 119,
    "GST Appellate Tribunal": 120, "State Tax Authority Madhya Pradesh": 121,
    "GST Enforcement Wing": 122,
}

HSN_SAC_NUMBER_IDS = {
    "995411": 108, "995412": 109, "995421": 110, "995422": 111,
    "0101": 112, "0201": 113, "0301": 114, "0401": 115,
    "0501": 116, "0601": 117, "0701": 118, "0801": 119,
    "0901": 120, "1001": 121, "995413": 122, "995414": 123,
    "995415": 124, "996311": 125, "996312": 126, "997111": 127,
    "997112": 128, "997113": 129, "996211": 130, "996212": 131,
}
```

### GST Rate Structures

The data file includes **20 realistic Indian GST rate structures**:

```python
GST_RATES = [
    {"name": "GST 0% (Nil)",  "rate": 0.0,  "cgst": 0.0,  "sgst": 0.0,  "igst": 0.0,  "cess": 0.0},
    {"name": "GST 5%",        "rate": 5.0,  "cgst": 2.5,  "sgst": 2.5,  "igst": 5.0,  "cess": 0.0},
    {"name": "GST 18%",       "rate": 18.0, "cgst": 9.0,  "sgst": 9.0,  "igst": 18.0, "cess": 0.0},
    {"name": "GST 28%",       "rate": 28.0, "cgst": 14.0, "sgst": 14.0, "igst": 28.0, "cess": 0.0},
    {"name": "GST 28% + 204% Cess", "rate": 28.0, "cess": 204.0},  # For cigarettes
    # ... 20 total
]
```

These are the actual GST slab rates used in India. The `cgst`, `sgst`, `igst`, and `cess` breakdowns are stored for reference but the ERP sub-table only stores the total `tax_rate` value.

### Payload Builder

```python
def build_tax_rate_api_payload(tax_rate_name, tax_type_ref_id, tax_authority_ref_id,
                                from_date, to_date, revision_status="Active",
                                tax_detail_lines=None):
    children_details = tax_detail_lines or [{}]
    return {
        "id": "",
        "tax_rate_name": tax_rate_name,
        "tax_type_ref_id": tax_type_ref_id,
        "tax_authority_ref_id": tax_authority_ref_id,
        "from_date": from_date,
        "to_date": to_date,
        "revision_status": revision_status,
        "attribute_name": "TaxRate",
        "children": [{
            "stepper_name": "Define Tax Rate Details",
            "is_stepper": True,
            "details": children_details,
            "children": [],
        }],
    }
```

### Validation Rules

```python
FIELD_VALIDATION_RULES = {
    "tax_rate_name":      {"type": "character", "required": True},
    "tax_type_ref_id":    {"type": "dropdown",  "required": True, "fk_options_count": 1},
    "tax_authority_ref_id": {"type": "dropdown", "required": True, "fk_options_count": 20},
    "from_date":          {"type": "date",      "required": True},
    "to_date":            {"type": "date",      "required": True},
    "revision_status":    {"type": "character", "required": True},
    "hsn_sac_number":     {"type": "dropdown",  "required": True, "fk_options_count": 24},
    "tax_rate":           {"type": "number",    "required": True},
}
```

---

## Page Object

### Key Methods

| Method | Purpose |
|--------|---------|
| `navigate_to_page()` | URL + `force_cleanup_all()` + wait for table |
| `force_cleanup_all()` | **THE most critical method** — see below |
| `open_add_form()` | Cleanup + click Add button |
| `fill_all_fields(data)` | Fill header fields (dropdowns first) |
| `fill_sub_table(rows)` | **Bottom-up sub-table fill** |
| `fill_sub_table_row(row_data, index)` | Fill HSN Number + Tax Rate for one row |
| `submit()` | Click Submit (Create mode) |
| `click_create_version()` | Click "Create Version" (Version mode) |
| `_set_date_field(locator, value)` | JS native setter for date fields with `name=null` |
| `_force_close_panels()` | **ONLY removes backdrops, NEVER containers or panes** |

### Tricky Bits

**1. CRITICAL: "NEVER remove `.cdk-overlay-container`"**

This is the most important note in the entire Tax Rate page object. The `force_cleanup_all()` method explicitly states:

> "NEVER remove `.cdk-overlay-container` or `.cdk-overlay-pane`. Only remove `.cdk-overlay-backdrop` (the dark sheet). Removing the container/pane kills Angular's overlay rendering engine permanently."

The cleanup code:
```python
# SAFE: Only remove backdrops
self.driver.execute_script("""
    document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove());
""")

# DANGEROUS: Never do this
# self.driver.execute_script("""
#     document.querySelectorAll('.cdk-overlay-container').forEach(el => el.remove());
# """)
```

**Why this matters**: Angular's CDK overlay system creates a single `.cdk-overlay-container` element at app bootstrap. It reuses this container for ALL overlays — dropdown panels, dialog boxes, toast notifications, SweetAlert popups. If you remove it from the DOM, Angular can't create new overlays until the entire app is reloaded (full page refresh). Dropdown menus will never open again. Dialogs will never appear. **The page becomes permanently broken.**

**2. Date fields have `name=null` — must use mat-label traversal**

Both From Date and To Date inputs have `name=null` in the DOM. You cannot use `input[name='From Date']` because the attribute doesn't exist. Instead, locators must traverse from the `mat-label`:

```python
FROM_DATE_INPUT = ("xpath", "//mat-label[contains(.,'From Date')]/ancestor::mat-form-field//input")
TO_DATE_INPUT = ("xpath", "//mat-label[contains(.,'To Date')]/ancestor::mat-form-field//input")
```

The `_set_date_field()` method sets the value via JS native setter + dispatches `input`, `change`, and `blur` events.

**3. Sub-table fills BOTTOM-UP**

```python
def fill_sub_table(self, sub_table_rows):
    # ... switch to sub-table tab ...
    # Add extra rows if needed
    for _ in range(max(0, needed - current_rows)):
        self.add_sub_table_row()
    
    # Fill rows from bottom-up (pattern #9)
    for i in range(needed - 1, -1, -1):
        self.fill_sub_table_row(sub_table_rows[i], row_index=i)
```

Why bottom-up? When you fill row 0 first and then move to row 1, Angular sometimes re-renders row 0, clearing its values. Filling from the bottom avoids this because lower rows don't trigger re-renders of higher rows. This was a hard-won discovery — top-down filling caused ~30% data loss.

**4. Edit button is DISABLED — must use "Version" instead**

The Edit button (pencil icon) is always present but always disabled (`disabled="true"`). To modify an existing tax rate, you must use the Version button (folder icon), which opens the form with a "Create Version" button instead of "Submit". This creates a new version of the tax rate with updated values.

```python
def click_version_on_row(self, row_index):
    """Opens editable form with 'Create Version' button (TR-02)."""
    self.click(self._version_button(row_index))
    self.wait_for_form_to_open()
```

**5. Sub-table starts with 1 empty row pre-created**

When the Add form opens, the sub-table already has 1 empty row. You don't need to click "Add" for the first row. For additional rows, `add_sub_table_row()` clicks the Add button inside the form popup.

**6. `_force_close_panels()` uses Escape, not DOM removal**

Unlike other modules that remove CDK overlay panes from the DOM, Tax Rate sends the Escape key:

```python
def _force_close_panels(self):
    has_overlay = self.driver.execute_script(
        "return document.querySelectorAll('.cdk-overlay-backdrop').length > 0;"
    )
    if has_overlay:
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
```

This is safe because Escape only closes the dropdown panel, not the form popup (the form has its own Cancel button). But note: this contradicts Bank's rule of "NEVER use Keys.ESCAPE." Tax Rate can use it safely; Bank cannot.

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| TR-01 | **Critical** | Removing `.cdk-overlay-container` from DOM kills Angular's overlay rendering engine permanently — page must be fully refreshed |
| TR-02 | High | Edit button is always disabled — must use "Version" instead (by design, but confusing) |
| TR-03 | Medium | No success SweetAlert on create/version — form closes silently |
| TR-04 | Low | Date fields have `name=null` — can't use standard `input[name='...']` locators |

---

## War Stories

### "The Day We Killed Angular's Overlay Engine"
We were debugging a stuck dropdown overlay and decided to remove ALL `.cdk-overlay-container` elements from the DOM to clear the state. It worked — the overlay disappeared. But then no dropdown would ever open again. Not just on Tax Rate, but on any page we navigated to afterward. Angular's CDK creates one overlay container at bootstrap and reuses it forever. Remove it, and Angular can't render any overlays.

The fix was a hard browser refresh. The lesson: **never remove `.cdk-overlay-container` or `.cdk-overlay-pane` from the DOM.** Only remove `.cdk-overlay-backdrop` elements. This is now documented as a critical note in the page object.

### "The Bottom-Up Mystery"
Sub-table filling was losing data. We'd fill row 0 (HSN=995411, Rate=18.0), then fill row 1 (HSN=995412, Rate=5.0), and when we checked, row 0 would be empty. Angular's change detection was re-rendering the sub-table when new rows were added or existing rows were modified, sometimes clearing previously filled values.

The fix was counter-intuitive: fill from the bottom up. Start with the last row and work upward. This works because Angular only re-renders rows that come AFTER the modified row, not before. Filling bottom-up means no previously filled row is ever "after" the current one.

### "Version, Not Edit"
The Edit button being permanently disabled confused everyone. We spent hours trying to click it, thinking it was a timing issue (maybe it enables after the form loads?). It never enables. The ERP's design is that tax rates are versioned — you don't edit an existing rate, you create a new version. This is probably correct from an audit trail perspective, but it's unusual and undocumented.

---

## Test Coverage

| Test Type | Status | Count |
|-----------|--------|-------|
| API: Payload | ✅ Complete | ~15 tests |
| API: Schema | ✅ Complete | ~8 tests |
| API: Performance | ✅ Complete | ~5 tests |
| UI: Validation | ✅ Complete | ~12 tests |

---

## Files

```
pages/common_settings/modules/tax_rate/
├── tax_rate_page.py                (1139 LOC)
├── data/
│   └── tax_rate_data.py            (461 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_tax_rate_validation.py  (418 LOC)
    └── api/
        ├── conftest.py
        ├── test_tax_rate_payload.py
        ├── test_tax_rate_schema.py
        └── test_tax_rate_perf.py
```
