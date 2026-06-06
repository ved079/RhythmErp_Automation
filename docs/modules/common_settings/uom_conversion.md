# Module: UOM Conversion

> **The module that got rewritten from scratch.** A backup file (`uom_conversion_page_backup.py`) at 710 LOC exists in the directory — proof that the page object was completely rebuilt. The current version is the most JS-heavy page object in Common Settings, with creative workarounds like opening the Add form just to read dropdown options.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Common Settings |
| **Complexity** | Medium (3 fields, 2 FK pools with 20+ UOMs each) |
| **Steppers** | 0 — flat popup form |
| **Repeating rows** | No |
| **API tests** | ✅ payload, schema, perf |
| **UI tests** | ✅ validation (~1019 LOC) |
| **Page object** | ✅ uom_conversion_page.py (1271 LOC) |
| **Data file** | ✅ uom_conversion_data.py (246 LOC) |
| **batch_create** | ✅ |
| **Backup file** | ✅ uom_conversion_page_backup.py (710 LOC) |

---

## The ERP Screen

UOM Conversion is found under **Common Settings → UOM Conversion** in the ERP sidebar. It's a flat popup form with 3 fields:

- **Source UOM** — mat-select dropdown with search, required. 20+ UOM codes available (KG, MT, QT, NOS, Litres, LTR, MTR, etc.)
- **Target UOM** — mat-select dropdown with search, required. Same 20+ UOM codes as Source
- **Conversion Factor** — numeric input, required. **Uses `type='character'` in the UI** — no native number validation, accepts any text. The value is a decimal representing how many target units equal 1 source unit (e.g. 1 MT = 1000 KG → factor = 1000.0).

### Navigation URL
`https://rhythmerp.algorhythms.in/#/dynamic-screens/UOM%20Conversion`

### Key UI Behaviors

1. **Success SweetAlert appears** — "added successfully" after create, "updated successfully" after edit.
2. **Conversion Factor is `type='character'`** — despite being a numeric field, the UI uses character input. This means:
   - No native HTML5 number validation
   - Non-numeric input (abc, @#$) is accepted by the frontend
   - Scientific notation bug: 22+ digit values cause display as scientific notation (e.g. `9.999999999999999e+21`), making the record **uneditable** through the UI
3. **Source and Target can be the SAME UOM** — self-conversion (KG → KG with factor=1) is allowed
4. **Action buttons use material icon TEXT matching** — not CSS classes or column names. The `_click_action_button()` method matches icon text like 'visibility', 'edit', 'history'

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
```

```json
{
    "id": "",
    "source_uom_code": 249,
    "target_uom_code": 250,
    "conversion_factor": 1000.0,
    "attribute_name": "UOM Conversion"
}
```

### Field Mapping

| UI Field | API Key | Type | Required | Notes |
|----------|---------|------|----------|-------|
| Source UOM | `source_uom_code` | integer (FK) | Yes | UOM ID, not code string |
| Target UOM | `target_uom_code` | integer (FK) | Yes | UOM ID, not code string |
| Conversion Factor | `conversion_factor` | number | Yes | 1 source = factor targets |

**Critical**: The API sends integer IDs (249, 250), NOT the display strings ("KG", "MT"). This is a common trap — the dropdown shows "KG" but the payload must use the FK integer ID.

### FK Dependencies

| FK Field | Pool Name | Count | Key IDs |
|----------|-----------|-------|---------|
| source_uom_code | UOM_IDS | 20 | KG=249, MT=250, QT=251, NOS=252, Litres=253, + 15 more |
| target_uom_code | UOM_IDS | 20 | Same pool as source — shared FK |

---

## Data Layer

### FK Pools

```python
UOM_IDS = {
    "KG": 249, "MT": 250, "QT": 251, "NOS": 252, "Litres": 253,
    "LTR": 501, "MTR": 502, "dozens": 504, "Litre": 506, "ML": 507,
    "MUND": 528, "BIGHA": 529, "SER": 530, "CAN": 531, "SQFT": 532,
    "SET": 533, "KM": 534, "HP": 535, "MM": 536, "SET60": 537,
}
```

Note: Some IDs have gaps (253→501, 502→504, 507→528) — there are auto-generated codes in between that aren't in our pool. The system has 42 total UOM entries; we track 20 that have standard names.

### Realistic Conversion Data

```python
CONVERSIONS = [
    ("MT",   "KG",   1000.0),       # 1 MT = 1000 KG
    ("LTR",  "ML",   1000.0),       # 1 LTR = 1000 ML
    ("KM",   "MTR",  1000.0),       # 1 KM = 1000 MTR
    ("MTR",  "MM",   1000.0),       # 1 MTR = 1000 MM
    ("NOS",  "dozens", 0.083333),   # 1 NOS = 1/12 dozens
    ("MUND", "KG",   37.3242),      # 1 Maund ≈ 37.3242 KG
    ("BIGHA","SQFT",  27225.0),     # 1 Bigha ≈ 27225 sq ft
    ("SET60","NOS",   60.0),        # 1 SET60 = 60 NOS
]
```

The `VALID_CONVERSIONS` list is automatically filtered to only include pairs where BOTH source and target exist in `UOM_IDS`. This prevents API errors from referencing non-existent FK IDs.

### Payload Builder

```python
def build_uom_conversion_api_payload(source_uom_code, target_uom_code, conversion_factor):
    return {
        "id": "",
        "source_uom_code": source_uom_code,
        "target_uom_code": target_uom_code,
        "conversion_factor": conversion_factor,
        "attribute_name": "UOM Conversion",
    }
```

### Validation Rules

```python
FIELD_VALIDATION_RULES = {
    "source_uom_code": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": 20,
        "note": "FK to UOM screen. API sends integer ID, not string code.",
    },
    "target_uom_code": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": 20,
        "note": "FK to UOM screen. Can be same as source (self-conversion allowed).",
    },
    "conversion_factor": {
        "type": "number",
        "required": True,
        "note": "Decimal number. 21-digit values OK, 22+ digits cause "
                "scientific notation display bug (record becomes uneditable). "
                "Input type='character' in UI (no native number validation).",
    },
}
```

---

## Page Object

### Key Methods

| Method | Purpose |
|--------|---------|
| `navigate_to_page()` | URL + `_wait_for_page_ready()` (30s timeout!) |
| `open_add_form()` | **Retries up to 3 times with hard refresh** |
| `select_uom(label, code)` | JS-first searchable dropdown selection |
| `type_conversion_factor(value)` | JS native setter via label traversal |
| `_click_action_button(source, target, action)` | Material icon TEXT matching |
| `get_available_uoms()` | **Opens Add form to read dropdown, then closes it** |
| `get_existing_pairs()` | Read all Source→Target pairs from table |
| `handle_validation_warning()` | SweetAlert Pattern A |
| `handle_validation_download()` | SweetAlert Pattern B |
| `handle_error_toast()` | SweetAlert Pattern C (deprecated) |

### Tricky Bits

**1. `_wait_for_page_ready()` has 30s timeout — longest of any module**

```python
def _wait_for_page_ready(self):
    waited = 0
    while waited < 30:
        has_add = self.driver.execute_script("""
            var addBtn = document.querySelector('app-custom-header .erp-add-btn');
            if (addBtn) return true;
            var icons = document.querySelectorAll('app-custom-header mat-icon, i.material-icons');
            for (var i = 0; i < icons.length; i++) {
                if (icons[i].textContent.trim() === 'add') return true;
            }
            return false;
        """)
        if has_add:
            return
        time.sleep(1)
        waited += 1
    # Last-ditch buffer: give Angular a few more seconds
    time.sleep(3)
```

30 seconds is extreme. The reason: UOM Conversion uses `app-custom-header` (a custom component) instead of the standard toolbar. This component loads asynchronously and can take 15-20 seconds to render. The two-strategy check (`.erp-add-btn` first, then icon text) handles both the fast-path and slow-path rendering.

**2. `open_add_form()` retries up to 3 times with HARD REFRESH**

```python
def open_add_form(self):
    for attempt in range(1, 4):
        try:
            result = self.driver.execute_script(js)
            return result
        except Exception as e:
            if attempt < 3:
                self._force_close_panels()
                self.force_close_form_popup()
                self.hard_refresh()  # location.reload(true)
    raise last_exc
```

This is the most aggressive form-opening strategy in the project. If the Add button doesn't respond, it force-closes all overlays, closes any stuck form popups, and does a full `location.reload(true)`. This was necessary because the `app-custom-header` component would sometimes get into a state where clicks were swallowed silently.

**3. `_click_action_button()` uses material icon TEXT matching**

Instead of CSS classes or column names, this method finds action buttons by their Material icon text content:

```python
icon_map = {
    "view": "visibility",
    "edit": "edit",
    "history": "history",
}
icon_text = icon_map.get(action_icon, action_icon)

# Click the menu item whose icon text matches
js_menu_item = """
var menu = document.querySelector('.mat-mdc-menu-panel');
var items = menu.querySelectorAll('button.mat-mdc-menu-item');
for (var i = 0; i < items.length; i++) {
    var icon = items[i].querySelector('i.material-icons');
    if (icon && icon.textContent.trim() === arguments[0]) {
        items[i].click();
        return 'clicked menu item: ' + arguments[0];
    }
}
"""
```

This is more resilient than CSS-based locators because icon text rarely changes between ERP versions, while CSS classes do.

**4. `get_available_uoms()` — creative workaround for reading dropdown options**

```python
def get_available_uoms(self):
    """Read all available UOM codes from the Source UOM dropdown.
    Opens the Add form popup temporarily to access the dropdown,
    then closes it. Returns a list of UOM code strings."""
    
    self.open_add_form()           # Must open popup — dropdown only exists inside the form
    # ... read dropdown options via JS ...
    self.force_close_form_popup()  # Close the form we opened just for reading
```

This is a creative workaround. The Source UOM dropdown only exists inside the Add form popup. To read available options (e.g. for finding fresh Source→Target pairs), you have to temporarily open the form, read the dropdown, then close it. This is safe because the form is never submitted — just opened for reading.

**5. 22+ digit conversion factors cause scientific notation bug**

If you enter a conversion factor with 22 or more digits (e.g. `9999999999999999999999`), the ERP stores it correctly but displays it in scientific notation (`9.999999999999999e+21`). The record then becomes **uneditable** — when you try to open it in Edit mode, the form cannot parse the scientific notation back into the input field. The only fix is to delete the record via API and recreate it with a shorter value.

This is a critical gotcha for boundary testing. The `generate_large_conversion_factor(n=22)` function generates exactly 22 digits to trigger this bug.

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| UOMC-001 | **Critical** | 22+ digit conversion factors cause scientific notation display bug — record becomes permanently uneditable through the UI |
| UOMC-002 | Medium | Conversion Factor uses `type='character'` — no native number validation. Non-numeric input (abc, @#$) accepted by frontend, may cause server-side errors |
| UOMC-003 | Low | `_wait_for_page_ready()` takes up to 30s on slow connections — makes test runs slow |

---

## War Stories

### "The Page Object Rewrite"
The backup file (`uom_conversion_page_backup.py`, 710 LOC) is a snapshot of the page object before a complete rewrite. The original version used Selenium-first interactions with lots of `time.sleep()` and multi-fallback click chains. It was slow (~8 minutes for a full test run) and flaky (dropdowns failing ~20% of the time).

The rewrite (1271 LOC — almost double the size) switched to JS-first interactions, added retry logic, and implemented the `get_available_uoms()` / `get_existing_pairs()` dynamic discovery pattern. The result: ~3 minute test runs and <5% flakiness. The lesson: **sometimes a rewrite is cheaper than patching.**

### "The Scientific Notation Trap"
We had a boundary test that entered a 30-digit conversion factor. The ERP accepted it without error. We thought the test passed. Then when we tried to edit that record later, the Edit form showed `9.999e+29` in the input field, and Angular couldn't parse it — the field was stuck with the scientific notation string. We couldn't save any changes. The record was effectively bricked.

The fix: delete via API (`DELETE /core/dynamic-screen-wrapper/`) and recreate with a sane value. The `generate_large_conversion_factor(n=22)` function now generates exactly the minimum digits to trigger the bug, making it a reliable test case.

### "Opening a Form Just to Read a Dropdown"
The `get_available_uoms()` method is the most creative workaround in the project. We needed to know which UOM codes were available for creating fresh Source→Target pairs, but the dropdown only exists inside the Add form popup. Our options:
1. Hardcode the list → breaks when new UOMs are added
2. Read from API → adds network dependency
3. Open the form, read the dropdown, close the form → works perfectly

Option 3 is what we chose. It's slightly slower (adds ~3 seconds per call) but always reflects the live state of the ERP. The `get_existing_pairs()` method reads from the main table (no form needed) to find pairs that already exist, so we can avoid creating duplicates.

---

## Test Coverage

| Test Type | Status | Count |
|-----------|--------|-------|
| API: Payload | ✅ Complete | ~15 tests |
| API: Schema | ✅ Complete | ~8 tests |
| API: Performance | ✅ Complete | ~5 tests |
| UI: Validation | ✅ Complete | ~18 tests |

### Key Validation Tests
- Valid conversion with all fields
- Decimal conversion factors (1.5, 37.3242)
- Very large factors (21 digits OK, 22+ triggers bug)
- Negative conversion factors
- Zero conversion factor
- Non-numeric (text) in conversion factor
- Special characters in conversion factor
- Same source and target UOM (self-conversion)
- Empty fields → Validation Failed
- Missing dropdown selections
- Scientific notation display bug

---

## Files

```
pages/common_settings/modules/uom_conversion/
├── uom_conversion_page.py          (1271 LOC)
├── uom_conversion_page_backup.py   (710 LOC — pre-rewrite snapshot)
├── UOM_Conversion_Automation_Guide.md
├── data/
│   └── uom_conversion_data.py     (246 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_uom_conversion_validation.py  (1019 LOC)
    └── api/
        ├── conftest.py
        ├── test_uom_conversion_payload.py
        ├── test_uom_conversion_schema.py
        └── test_uom_conversion_perf.py
```
