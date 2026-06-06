# Module: Tax Authority

> **The module that taught us stuck states are real.** Tax Authority has a full `_recover_from_stuck_state()` method because popups and overlays from previous tests would bleed into the next one. It also has the smallest data file at 138 LOC and the most sophisticated searchable-dropdown handling in the project.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Common Settings |
| **Complexity** | Medium (3 fields, 2 FK pools — one with 45+ countries) |
| **Steppers** | 0 — flat popup form |
| **Repeating rows** | No |
| **API tests** | ✅ payload, schema, perf |
| **UI tests** | ✅ validation (~482 LOC) |
| **Page object** | ✅ tax_authority_page.py (975 LOC) |
| **Data file** | ✅ tax_authority_data.py (138 LOC — smallest) |
| **batch_create** | ✅ |

---

## The ERP Screen

Tax Authority is found under **Common Settings → Tax Authority** in the ERP sidebar. It's a flat popup form with 3 fields:

- **Tax Name** — text input, required. The name of the tax authority (e.g. "CGST Authority", "GST Audit Office Mumbai").
- **Tax Type** — mat-select dropdown, required. Currently only 1 option: GST (ID=93). This is a small FK pool.
- **Country** — mat-select dropdown with **search**, required. 45+ countries (India=1, plus 44+ others). This is a LARGE FK pool with a search input inside the dropdown panel.

### Navigation URL
Defined in `tax_authority_data.py` as `TAX_AUTHORITY_PAGE_URL`.

### Key UI Behaviors

1. **NO success SweetAlert (BUG TA-001)** — like Error Code Mst, the form closes silently on success. The `is_success_alert_present()` method exists but always returns False.
2. **Country dropdown is searchable** — the `select_country()` method must type in a search box BEFORE selecting the option, because 45+ countries can't all be visible at once.
3. **Action buttons use `tblActnBtn` pattern** — not a 3-dot kebab menu. Each row has 3 buttons indexed by `row*3 + offset` via XPath.
4. **Add button uses `mat-icon[text()='add']`** — no CSS class, no mattooltip. The button is found by its Material icon text content.

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
```

```json
{
    "id": "",
    "tax_name": "CGST Authority",
    "tax_type_ref_id": 93,
    "country_ref_id": 1,
    "attribute_name": "Tax Authority"
}
```

### Field Mapping

| UI Field | API Key | Type | Required | Notes |
|----------|---------|------|----------|-------|
| Tax Name | `tax_name` | string | Yes | Authority name |
| Tax Type | `tax_type_ref_id` | integer (FK) | Yes | Currently only GST=93 |
| Country | `country_ref_id` | integer (FK) | Yes | FK to Country, India=1 |

### FK Dependencies

| FK Field | Pool Name | Count | Key IDs |
|----------|-----------|-------|---------|
| tax_type_ref_id | TAX_TYPE_IDS | 1 option | GST=93 |
| country_ref_id | COUNTRY_IDS | 45+ countries | India=1, Dubai=2, + 43 more |

---

## Data Layer

### FK Pools

```python
TAX_TYPE_IDS = {"GST": 93}

COUNTRY_IDS = {
    "India": 1, "Dubai": 2, "Afghanistan": 3, "Algeria": 4, "Angola": 5,
    "Argentina": 6, "Australia": 8, "Bahrain": 10, "Bhutan": 13, "Brazil": 16,
    "Canada": 20, "China (offshore)": 25, "Colombia": 26, "Denmark": 32,
    "Egypt": 34, "European Union": 38, "Hong Kong": 46, "Indonesia": 49,
    "Israel": 52, "Kenya": 55, "Kuwait": 56, "Malaysia": 64, "Maldives": 65,
    "Mexico": 67, "Myanmar": 70, "Nepal": 72, "New Zealand": 73, "Nigeria": 74,
    "Oman": 77, "Pakistan": 78, "Philippines": 82, "Qatar": 84, "Russia": 86,
    "Saudi Arabia": 89, "Singapore": 0, "South Africa": 94, "South Korea": 95,
    "Sri Lanka": 96, "Sweden": 98, "Switzerland": 99, "Taiwan": 101,
    "Thailand": 0, "Turkey": 105, "Ukraine": 106, "United Kingdom": 107,
    "United States": 108, "Vietnam": 112,
}
```

**Gotcha**: Some country IDs are 0 (Singapore, Thailand) and some IDs have gaps in numbering. Don't assume sequential IDs.

### Realistic Data

```python
TAX_AUTHORITIES = [
    {"tax_name": "CGST Authority",         "tax_type": "GST", "country": "India"},
    {"tax_name": "SGST Authority",          "tax_type": "GST", "country": "India"},
    {"tax_name": "IGST Authority",          "tax_type": "GST", "country": "India"},
    {"tax_name": "GST Audit Office Mumbai", "tax_type": "GST", "country": "India"},
    # ... 20 Indian GST authorities total
]
```

The data file is only 138 LOC — the smallest in Common Settings — because all 20 authorities share the same tax type (GST) and country (India). There's no variety needed.

### Payload Builder

```python
def build_tax_authority_api_payload(tax_name, tax_type_ref_id, country_ref_id):
    return {
        "id": "",
        "tax_name": tax_name,
        "tax_type_ref_id": tax_type_ref_id,
        "country_ref_id": country_ref_id,
        "attribute_name": "Tax Authority",
    }
```

---

## Page Object

### Key Methods

| Method | Purpose |
|--------|---------|
| `navigate_to_tax_authority()` | URL + `_recover_from_stuck_state()` + wait for table |
| `_recover_from_stuck_state()` | Full recovery: dismiss SweetAlerts, remove backdrops, close forms/popups |
| `open_add_form()` | Recover stuck state + click Add button |
| `_open_dropdown(locator, label)` | **3-strategy dropdown opener** (Selenium, JS, ActionChains) |
| `select_tax_type(type)` | Standard mat-select with 3-attempt retry |
| `select_country(country)` | **Searchable dropdown** — types in search box first |
| `fill_all_fields(data, max_cycles=3)` | **Retry with page refresh** when dropdowns fail |
| `create_record(data)` | Alert-first detection + form-close = success |
| `_do_js_search(text)` | Atomic JS search (toggle → set value → Enter) |

### Tricky Bits

**1. `_recover_from_stuck_state()` — full stuck-state recovery**

This is the most comprehensive state recovery method in the project. It runs BEFORE navigation:

```python
def _recover_from_stuck_state(self):
    # 1. Dismiss any SweetAlert popup
    # 2. Remove CDK overlay backdrops via JavaScript
    # 3. Close form popup if open (via Cancel button)
    # 4. Close history popup if open (via Cancel button)
```

Why this exists: when a previous test fails mid-way through (e.g. after creating a record but before dismissing the success alert), the SweetAlert or form popup remains open. The next test navigates to the page, but the stuck overlay blocks all interaction. `_recover_from_stuck_state()` ensures a clean slate before every navigation.

**2. `_open_dropdown()` — 3 click strategies with retry**

The dropdown opener tries three different click strategies in sequence:

```python
def _open_dropdown(self, trigger_locator, label="dropdown"):
    for attempt in range(3):
        if attempt == 0:
            self.click(trigger_locator)                      # Strategy 1: BasePage click
        elif attempt == 1:
            el = self.find_element(trigger_locator)
            self.driver.execute_script("arguments[0].click();", el)  # Strategy 2: JS click
        else:
            el = self.find_element(trigger_locator)
            ActionChains(self.driver).move_to_element(el).click().perform()  # Strategy 3: ActionChains
        self.wait_seconds(1)
        if self.driver.find_elements(By.CSS_SELECTOR, "mat-option"):
            return True  # Dropdown opened successfully
    return False
```

Each strategy works in different scenarios:
- Strategy 1 (Selenium click): Works when no overlays are blocking
- Strategy 2 (JS click): Works when a transparent overlay is blocking the click
- Strategy 3 (ActionChains): Works when the element needs focus/move-to-first

**3. `select_country()` — types in the search box before selecting**

The Country dropdown is too large to display all options at once. It has a search input inside the dropdown panel:

```python
def select_country(self, country):
    if not self._open_dropdown(self.COUNTRY_SELECT, "Country"):
        return False
    # Type search text first
    for sel in [".cdk-overlay-pane input[type='text']", ".cdk-overlay-pane input"]:
        try:
            search_input = self.driver.find_element(By.CSS_SELECTOR, sel)
            if search_input.is_displayed():
                search_input.clear()
                search_input.send_keys(country)
                self.wait_seconds(1)
                break
        except Exception:
            continue
    # Then click the first matching option
    first_option = ("xpath", "(//mat-option)[1]")
    # ... click with retry ...
```

The two CSS selectors for the search input are needed because Angular Material renders the search input differently depending on the dropdown configuration.

**4. `fill_all_fields()` — retry with FULL page re-navigation**

If any dropdown fails, the method doesn't just retry the dropdown — it re-navigates to the entire page:

```python
def fill_all_fields(self, data, max_cycles=3, is_edit=False):
    for cycle in range(1, max_cycles + 1):
        if not is_edit:
            self.navigate_to_tax_authority()  # Full re-navigation
            self.open_add_form()
        # Try filling dropdowns again...
```

This is more aggressive than Error Code Mst's `driver.refresh()` — it does a full `navigate_to_tax_authority()` which includes stuck-state recovery. The rationale: if dropdowns are failing, something is fundamentally wrong with the page state, and only a full re-navigation will fix it.

**5. Action buttons use `tblActnBtn` pattern (XPath indexing)**

Unlike HSN SAC's column-based buttons or most modules' 3-dot menu, Tax Authority uses a class-based pattern:

```python
def _view_button(self, row_index):
    return ("xpath", f"(//button[contains(@class,'tblActnBtn')])[{row_index * 3 + 1}]")
def _edit_button(self, row_index):
    return ("xpath", f"(//button[contains(@class,'tblActnBtn')])[{row_index * 3 + 2}]")
def _history_button(self, row_index):
    return ("xpath", f"(//button[contains(@class,'tblActnBtn')])[{row_index * 3 + 3}]")
```

The formula `row_index * 3 + offset` works because each row has exactly 3 action buttons with the `tblActnBtn` class. The XPath indexing is 1-based, so row 0's buttons are at indices 1, 2, 3.

**Gotcha**: This pattern breaks if any row has a different number of buttons, or if the table has header/footer rows that also contain `tblActnBtn` elements. Always verify the actual DOM structure.

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| TA-001 | Medium | No success SweetAlert — form closes silently on create/update. Makes automated success detection harder. |
| TA-002 | Low | `tblActnBtn` XPath indexing breaks if table has filter rows with action buttons |
| TA-003 | Low | Country IDs for Singapore and Thailand are 0 (not sequential) — may cause API issues if backend expects positive integers |

---

## War Stories

### "The Stuck State That Ate Our Tests"
Tax Authority tests were flaky for weeks. Every fifth test would fail with "ElementNotInteractableException" because a SweetAlert from the previous test was still open. We tried `driver.refresh()` between tests, but the SweetAlert persisted through refreshes (Angular's service worker caches it).

The breakthrough was `_recover_from_stuck_state()`. By running it BEFORE navigation (not after failure), we ensure a clean slate. This method should be copied to every module that has flaky test issues — it's the nuclear option for state recovery.

### "The Country Search Box That Didn't Exist"
Our first attempt at `select_country()` just opened the dropdown and clicked the first option. It worked for "India" (which is always at the top) but failed for "Vietnam" (which is at the bottom). The dropdown only shows 10-15 countries at a time — the rest are behind a search. We had to discover the search input inside the dropdown panel and type the country name before selecting.

The two CSS selectors (`.cdk-overlay-pane input[type='text']` and `.cdk-overlay-pane input`) are needed because the search input's `type` attribute varies between dropdown configurations. Some dropdowns have `type='text'`, others just have `input` without a type attribute.

### "The Smallest Data File"
At 138 LOC, `tax_authority_data.py` is the smallest data file in Common Settings. This is because all 20 authorities share the same tax type and country — there's no structural variety needed. The lesson: data file size is NOT proportional to module complexity. Tax Authority has complex dropdown handling but simple data.

---

## Test Coverage

| Test Type | Status | Count |
|-----------|--------|-------|
| API: Payload | ✅ Complete | ~12 tests |
| API: Schema | ✅ Complete | ~8 tests |
| API: Performance | ✅ Complete | ~5 tests |
| UI: Validation | ✅ Complete | ~15 tests |

---

## Files

```
pages/common_settings/modules/tax_authority/
├── tax_authority_page.py           (975 LOC)
├── Tax_Authority_Automation_Guide.md
├── data/
│   └── tax_authority_data.py       (138 LOC — smallest!)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_tax_authority_validation.py  (482 LOC)
    └── api/
        ├── conftest.py
        ├── test_tax_authority_payload.py
        ├── test_tax_authority_schema.py
        └── test_tax_authority_perf.py
```
