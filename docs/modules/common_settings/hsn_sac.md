# Module: HSN SAC

> **The Indian GST data module.** Contains real HSN/SAC codes from the Indian taxation system and the most sophisticated dropdown handling in the project — JS-first with ActionChains fallback. If you're working with any module that has mat-select dropdowns, study `_select_mat_option()` here first.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Common Settings |
| **Complexity** | Simple-Medium (3 fields, 1 FK pool) |
| **Steppers** | 0 — flat popup form |
| **Repeating rows** | No |
| **API tests** | ✅ payload, schema, perf |
| **UI tests** | ✅ validation (~442 LOC) |
| **Page object** | ✅ hsn_sac_page.py (1164 LOC) |
| **Data file** | ✅ hsn_sac_data.py (331 LOC) |
| **batch_create** | ✅ |

---

## The ERP Screen

HSN SAC is found under **Common Settings → HSN SAC** in the ERP sidebar. It's a flat popup form with 3 fields (all required):

- **HSN SAC Number** — text input, `type="character"`, required. Accepts 4-digit HSN codes (Commodity) and 6-digit SAC codes (Services).
- **HSN SAC Type** — mat-select dropdown, required. 4 fixed options: Services (ID=212), Transportation (ID=162), Commission (ID=161), Commodity (ID=159).
- **HSN SAC Description** — text input, `type="character"`, required. Human-readable description of the code.

The form opens as a popup (`.big-model` dialog). Uses the "UOM gold-standard speed patterns" — fast polling (0.1s intervals), JS-first interactions, single-strategy methods.

### Navigation URL
`https://rhythmerp.algorhythms.in/#/dynamic-screens/HSN%20SAC`

Note: URL has `%20` encoding for the space in "HSN SAC".

### Key UI Behaviors

1. **Success SweetAlert appears** — shows "added successfully" after create, "updated successfully" after edit.
2. **All 3 fields are required** — submitting with any empty field triggers "Validation Failed" SweetAlert.
3. **HSN SAC Type dropdown has 4 fixed options** — this is a small FK pool that doesn't change, making it reliable for testing.
4. **Row action buttons have both 3-dot menu AND column-based fallback** — the `_click_action_menu_item()` method tries the 3-dot kebab menu first, then falls back to `mat-column-view`, `mat-column-edit`, `mat-column-archive` button locators.

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
```

```json
{
    "id": "",
    "hsn_sac_no": "998311",
    "hsn_sac_type": 212,
    "hsn_sac_description": "Licensing services for the right to use computer software",
    "attribute_name": "HSN SAC"
}
```

### Field Mapping

| UI Field | API Key | Type | Required | Notes |
|----------|---------|------|----------|-------|
| HSN SAC Number | `hsn_sac_no` | string | Yes | 4-digit (HSN) or 6-digit (SAC) code |
| HSN SAC Type | `hsn_sac_type` | integer (FK) | Yes | FK ID, not display string |
| HSN SAC Description | `hsn_sac_description` | string | Yes | Human-readable description |

### FK Dependencies

| FK Field | Pool Name | Options | IDs |
|----------|-----------|---------|-----|
| hsn_sac_type | HSN_SAC_TYPE_IDS | 4 types | Services=212, Transportation=162, Commission=161, Commodity=159 |

---

## Data Layer

### FK Pools

```python
HSN_SAC_TYPE_IDS = {
    "Services":       212,
    "Transportation": 162,
    "Commission":     161,
    "Commodity":      159,
}
```

### Test Data Pools

The data file contains **real codes from the Indian GST system** organized by type:

| Type | Pool | Count | Example |
|------|------|-------|---------|
| Commodity | `HSN_COMMODITY` | 30 codes | "0101" (Live horses), "1006" (Rice), "8471" (Computers) |
| Services | `SAC_SERVICES` | 28 codes | "998311" (Software licensing), "998621" (Banking) |
| Transportation | `SAC_TRANSPORTATION` | 10 codes | "996411" (Road freight), "996413" (Air freight) |
| Commission | `SAC_COMMISSION` | 10 codes | "996111" (Sale commission), "996531" (Auction) |

### Payload Builder

```python
def build_hsn_sac_api_payload(hsn_sac_no, hsn_sac_type_id, hsn_sac_description):
    return {
        "id": "",
        "hsn_sac_no": hsn_sac_no,
        "hsn_sac_type": hsn_sac_type_id,
        "hsn_sac_description": hsn_sac_description,
        "attribute_name": "HSN SAC",
    }
```

The `generate_hsn_sac_api_payloads()` function distributes entries across all 4 types by cycling through `type_names[i % len(type_names)]`, ensuring variety in batch creation.

### Validation Rules

```python
FIELD_VALIDATION_RULES = {
    "hsn_sac_no": {
        "type": "character",
        "required": True,
        "max_length": 255,
        "note": "HSN code (4+ digits) or SAC code (6 digits). Alphanumeric.",
    },
    "hsn_sac_type": {
        "type": "dropdown",
        "required": True,
        "fk_options_count": 4,
        "note": "FK to HSN/SAC Type. 4 options.",
    },
    "hsn_sac_description": {
        "type": "character",
        "required": True,
        "max_length": 255,
    },
}
```

---

## Page Object

### Key Methods

| Method | Purpose |
|--------|---------|
| `navigate_to_page()` | Direct URL navigation with `%20` encoding |
| `open_add_form()` | JS click Add button (Selenium fallback) |
| `select_hsn_sac_type(option_text)` | Select from 4-option dropdown |
| `fill_all_fields(data, max_retries=2)` | Fill with retry — dropdowns first |
| `_select_mat_option(locator, text)` | **JS-first dropdown selector** |
| `get_form_field_values()` | **JS JSON.stringify()** for dropdown reading |
| `_click_action_menu_item(code, action)` | 3-dot menu + row-index fallback |
| `handle_success_alert()` | Read title + dismiss + cleanup in ONE JS call |

### Tricky Bits

**1. `_select_mat_option()` — JS-first with ActionChains fallback**

This is the most sophisticated dropdown selection in the project:

```python
def _select_mat_option(self, select_locator, option_text):
    # Step 1: Click dropdown trigger via JS
    select_el = self.driver.find_element(*select_locator)
    self.driver.execute_script("arguments[0].click();", select_el)
    
    # Step 2: Wait for overlay panel (2s timeout)
    # If timeout → Fallback: ActionChains click
    ActionChains(self.driver).move_to_element(select_el).click().perform()
    
    # Step 3: Find matching option via JS (fast)
    clicked = self.driver.execute_script("""
        var options = document.querySelectorAll(
            'div.mat-mdc-select-panel mat-option, [role="option"]'
        );
        for (var i = 0; i < options.length; i++) {
            if (options[i].textContent.indexOf(arguments[0]) !== -1) {
                options[i].click();
                return true;
            }
        }
        return false;
    """, option_text)
```

The three-tier approach (JS click → ActionChains fallback → JS option selection) was developed because Selenium clicks on mat-select triggers would sometimes not open the dropdown panel, especially when a CDK overlay was still visible from a previous interaction.

**2. `get_form_field_values()` — JS JSON.stringify() for complex dropdown reading**

Reading the selected value of a mat-select dropdown is surprisingly hard. The value isn't in a standard `value` attribute — it's rendered as text inside a complex Angular Material component. HSN SAC solves this with XPath-based label traversal:

```python
result = self.driver.execute_script("""
    var typeLabel = document.evaluate(
        "//mat-label[contains(.,'HSN SAC Type')]",
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    ).singleNodeValue;
    if (typeLabel) {
        var typeSelect = typeLabel.closest('mat-form-field')
            ? typeLabel.closest('mat-form-field').querySelector('mat-select')
            : null;
        values.hsn_sac_type = typeSelect ? typeSelect.textContent.trim() : '';
    }
    return JSON.stringify(values);
""")
```

The `JSON.stringify()` + `json.loads()` pattern avoids the Selenium limitation of only returning simple types from JavaScript execution. This pattern is used in Vehicle Master and other modules too.

**3. `_click_action_menu_item()` — dual strategy with row-index fallback**

If the 3-dot kebab menu doesn't work (element not found, row not visible), the method falls back to column-based button locators:

```python
# Primary: 3-dot menu
VIEW_BUTTON = (By.XPATH, "//td[contains(@class,'mat-column-view')]//button")
EDIT_BUTTON = (By.XPATH, "//td[contains(@class,'mat-column-edit')]//button")
HISTORY_BUTTON = (By.XPATH, "//td[contains(@class,'mat-column-archive')]//button")
```

This dual strategy makes HSN SAC the most resilient module for row actions.

**4. `_force_close_panels()` removes CDK overlay panes but NOT dialogs**

```python
def _force_close_panels(self):
    self.driver.execute_script("""
        document.querySelectorAll('div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)')
            .forEach(function(el) { el.remove(); });
        document.querySelectorAll('div.cdk-overlay-pane').forEach(function(el) {
            if (!el.querySelector('mat-dialog-container')) el.remove();
        });
    """)
```

The check for `mat-dialog-container` is critical — removing a dialog container would close the entire form popup. This pattern is safe for all modules.

### Locator Strategies

| Element | Locator | Notes |
|---------|---------|-------|
| HSN Number input | `input[name='HSN SAC Number']` | Name attr with spaces |
| HSN Type dropdown | XPath: `mat-label[contains(.,'HSN SAC Type')]` → `mat-select` | Label traversal |
| HSN Description input | `input[name='HSN SAC Description']` | Name attr with spaces |
| View button | `td.mat-column-view button` | Column-based fallback |
| Edit button | `td.mat-column-edit button` | Column-based fallback |
| History button | `td.mat-column-archive button` | Column-based fallback |

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| HSN-001 | Medium | No duplicate HSN/SAC number validation — duplicate codes accepted silently |
| HSN-002 | Low | `_select_mat_option()` returns `False` when dropdown doesn't open but doesn't raise — caller must check return value |
| HSN-003 | Low | Search uses `button.search-btn` which may not be clickable if toolbar hasn't fully rendered |

---

## War Stories

### "The Dropdown That Wouldn't Open"
HSN SAC was the first module where we hit the "dropdown doesn't open" problem consistently. Clicking a mat-select via Selenium would sometimes open the panel, sometimes not. The fix was the three-tier approach: JS click first, ActionChains click as fallback. This pattern became standard for every module with mat-select dropdowns.

### "JSON.stringify() Saves the Day"
Reading form values for verification was a constant pain. `element.text` returns stale values, `get_attribute('value')` doesn't work for dropdowns, and Angular Material's internal state is opaque from Selenium. The breakthrough was using `JSON.stringify()` inside the JS execution and parsing the result in Python. This gave us a reliable way to read ALL form field values — including dropdowns — in a single round-trip.

### "Column-Based Buttons vs 3-Dot Menu"
When we first automated HSN SAC, we used the 3-dot kebab menu for all row actions. Then the ERP updated and the kebab menu stopped appearing for some rows. We added column-based button locators (`mat-column-view`, `mat-column-edit`, `mat-column-archive`) as a fallback, and the dual strategy has been reliable ever since. The lesson: **always have a fallback locator strategy for row actions.**

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
pages/common_settings/modules/hsn_sac/
├── hsn_sac_page.py                 (1164 LOC)
├── HSN_SAC_Automation_Guide.md
├── data/
│   └── hsn_sac_data.py             (331 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_hsn_sac_validation.py  (442 LOC)
    └── api/
        ├── conftest.py
        ├── test_hsn_sac_payload.py
        ├── test_hsn_sac_schema.py
        └── test_hsn_sac_perf.py
```
