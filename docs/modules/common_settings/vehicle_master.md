# Module: Vehicle Master

> **The largest page object in Common Settings at ~1896 LOC.** Vehicle Master has it all: searchable dropdowns, a custom header component that breaks the Angular refresh button, deprecated methods kept for backward compatibility, and 20 realistic Indian commercial vehicles in its data file. It's the template that Error Code Mst was based on.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Common Settings |
| **Complexity** | Medium-High (5 fields, 2 FK pools) |
| **Steppers** | 0 — flat popup form |
| **Repeating rows** | No |
| **API tests** | ✅ payload, schema, perf |
| **UI tests** | ✅ validation (~1421 LOC) |
| **Page object** | ✅ vehicle_master_page.py (1896 LOC — largest) |
| **Data file** | ✅ vehicle_master_data.py (288 LOC) |
| **batch_create** | ✅ |

---

## The ERP Screen

Vehicle Master is found under **Common Settings → Vehicle Master** in the ERP sidebar. It's a flat popup form with 5 fields:

- **Name** — text input, required. Vehicle name (e.g. "Tata Ace", "BharatBenz 1215R")
- **Vehicle Price** — text input, required, numeric. `type='character'` in UI (no native number validation). Accepts strings like "1500000".
- **Vehicle Type** — mat-select dropdown with search, required. 5 options: Truck (ID=1), Trailer (ID=2), Tanker (ID=3), Mini Truck (ID=4), Pickup (ID=5).
- **Fuel Type** — mat-select dropdown with search, required. 5 options: Diesel (ID=1), Petrol (ID=2), CNG (ID=3), Electric (ID=4), LPG (ID=5).
- **Description** — text input, optional. Free-form text.

### Navigation URL
`https://rhythmerp.algorhythms.in/#/dynamic-screens/Vehicle%20Master`

### Key UI Behaviors

1. **Success SweetAlert appears** — "added successfully" after create, "updated successfully" after edit.
2. **Vehicle Price is `type='character'`** — no HTML5 number validation. Non-numeric input is accepted by the frontend.
3. **Angular refresh button BREAKS the toolbar** — clicking the refresh icon in the ERP toolbar causes the search button to disappear from the DOM permanently. Only a browser refresh (Ctrl+R) is reliable.
4. **NEVER use Keys.ESCAPE** — pressing Escape while a dropdown is open closes the entire popup form, losing all entered data.
5. **Stacked popups** — History popup can open over View popup (z-index 1001 over 1000), creating complex overlay states.

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
```

```json
{
    "id": "",
    "name": "Tata Ace",
    "vehicle_price": 500000,
    "vehicle_type_id": 4,
    "fuel_type_ref_id": 1,
    "description": "Mini truck for intra-city goods transport",
    "attribute_name": "Vehicle Master"
}
```

### Field Mapping

| UI Field | API Key | Type | Required | Notes |
|----------|---------|------|----------|-------|
| Name | `name` | string | Yes | Vehicle name |
| Vehicle Price | `vehicle_price` | number | Yes | Numeric as string in UI |
| Vehicle Type | `vehicle_type_id` | integer (FK) | Yes | FK ID, not display string |
| Fuel Type | `fuel_type_ref_id` | integer (FK) | Yes | FK ID, not display string |
| Description | `description` | string | No | Optional |

### FK Dependencies

| FK Field | Pool Name | Count | Key IDs |
|----------|-----------|-------|---------|
| vehicle_type_id | VEHICLE_TYPE_IDS | 5 | Truck=1, Trailer=2, Tanker=3, Mini Truck=4, Pickup=5 |
| fuel_type_ref_id | FUEL_TYPE_IDS | 5 | Diesel=1, Petrol=2, CNG=3, Electric=4, LPG=5 |

---

## Data Layer

### FK Pools

```python
VEHICLE_TYPE_IDS = {
    "Truck": 1, "Trailer": 2, "Tanker": 3, "Mini Truck": 4, "Pickup": 5,
}

FUEL_TYPE_IDS = {
    "Diesel": 1, "Petrol": 2, "CNG": 3, "Electric": 4, "LPG": 5,
}
```

### Realistic Data — 20 Indian Commercial Vehicles

```python
VEHICLES = [
    {"name": "Tata Ace",               "price": 500000,  "vehicle_type": "Mini Truck", "fuel_type": "Diesel"},
    {"name": "Ashok Leyland Dost",     "price": 750000,  "vehicle_type": "Pickup",     "fuel_type": "Diesel"},
    {"name": "Mahindra Bolero Pickup",  "price": 850000,  "vehicle_type": "Pickup",     "fuel_type": "Diesel"},
    {"name": "Tata 407",              "price": 1200000, "vehicle_type": "Truck",       "fuel_type": "Diesel"},
    {"name": "BharatBenz 1215R",       "price": 2200000, "vehicle_type": "Truck",       "fuel_type": "Diesel"},
    {"name": "Tata Prima 4028",        "price": 3500000, "vehicle_type": "Trailer",     "fuel_type": "Diesel"},
    {"name": "Mahindra Champion Load", "price": 350000,  "vehicle_type": "Mini Truck",  "fuel_type": "CNG"},
    {"name": "Eicher Pro 2049 CNG",    "price": 1100000, "vehicle_type": "Truck",       "fuel_type": "CNG"},
    {"name": "Tata Signa 5528",       "price": 4500000, "vehicle_type": "Trailer",     "fuel_type": "Diesel"},
    # ... 20 total
]
```

All vehicles are realistic Indian commercial vehicles with actual market prices (in INR). The data covers the full range from 3-wheelers (₹2 lakh) to 55-tonne tractor trailers (₹45 lakh).

### Payload Builder

```python
def build_vehicle_master_api_payload(name, vehicle_price, vehicle_type_id,
                                      fuel_type_ref_id, description=""):
    return {
        "id": "",
        "name": name,
        "vehicle_price": vehicle_price,
        "vehicle_type_id": vehicle_type_id,
        "fuel_type_ref_id": fuel_type_ref_id,
        "description": description,
        "attribute_name": "Vehicle Master",
    }
```

---

## Page Object

### Key Methods

| Method | Purpose |
|--------|---------|
| `navigate_to_page()` | Direct URL navigation |
| `hard_refresh()` | Browser refresh (NOT Angular refresh!) |
| `open_add_form()` | JS click Add button (Selenium fallback) |
| `fill_vehicle_form(data)` | Fill all 5 fields, random dropdown if not specified |
| `_select_random_from_dropdown(locator, label)` | Picks random option from live UI |
| `ensure_vehicle_visible(name)` | **3-tier search** (direct → search → hard refresh + search) |
| `_click_action_menu_item(name, action)` | 3-dot menu with search fallback for pagination |
| `_js_click_popup_button(text)` | Read + dismiss SweetAlert in single JS call |
| `_select_mat_option(locator, text)` | Mat-select with search panel |
| `click_refresh()` | **Always uses hard_refresh()** — Angular refresh is broken |

### Tricky Bits

**1. Angular refresh button BREAKS the toolbar — search button disappears**

This is the most dangerous bug in Vehicle Master. The ERP has a refresh button (icon with "refresh" text) in the toolbar. Clicking it causes the search button to disappear from the DOM permanently. No amount of waiting or overlay cleanup will bring it back. Only a full browser refresh (Ctrl+R or `driver.refresh()`) restores the toolbar.

```python
def click_refresh(self):
    """Refresh the page using hard_refresh (browser refresh).
    Angular's refresh button breaks the toolbar — search button
    disappears from DOM permanently. Browser refresh is reliable."""
    self.hard_refresh()  # ALWAYS use browser refresh, never the toolbar button
```

**Why this happens**: The Angular refresh button triggers a component-level re-render that doesn't include the search toggle. It's a bug in the ERP's custom header component (`app-custom-header`), not in our code.

**2. `ensure_vehicle_visible()` — 3-tier search strategy**

Vehicle records may span multiple pages (the table has pagination). Finding a specific vehicle requires a multi-tier approach:

```python
def ensure_vehicle_visible(self, vehicle_name, timeout=8):
    # Tier 1: Check if already in current table view
    if self.is_vehicle_in_table(vehicle_name):
        return True
    
    # Tier 2: Search for it
    self.search_vehicle(vehicle_name)
    if self.is_vehicle_in_table(vehicle_name):
        return True
    
    # Tier 3: Hard refresh then search again
    self.hard_refresh()
    self.search_vehicle(vehicle_name)
    if self.is_vehicle_in_table(vehicle_name):
        return True
    
    raise Exception(f"Vehicle '{vehicle_name}' not found")
```

Tier 3 is needed because the search index can become stale — a recently created vehicle might not be findable until the page is refreshed.

**3. `_select_random_from_dropdown()` — picks random option from live UI**

When test data doesn't specify a vehicle_type or fuel_type, the page object picks a random option from the dropdown:

```python
def _select_random_from_dropdown(self, select_locator, label_text):
    # Open dropdown, read all options, pick one at random
    self.click(select_locator)
    options = self.driver.find_elements(By.CSS_SELECTOR, "mat-option")
    if options:
        random.choice(options).click()
```

This is useful for exploratory testing and load testing where you don't care about specific dropdown values, just that the form can be filled and submitted. The alternative — hardcoding "Truck" and "Diesel" every time — would create unrealistic data distributions.

**4. Deprecated methods kept for backward compatibility**

```python
def _click_action_button(self, vehicle_name, action_xpath_template):
    """DEPRECATED — delegates to _click_action_menu_item()."""

def _click_action_button_by_index(self, row_index, action_xpath_template):
    """DEPRECATED — finds vehicle name by index, then uses _click_action_menu_item()."""
```

These methods were the original row-action approach (column-based CSS selectors). They were replaced by the 3-dot kebab menu pattern but kept as delegates for backward compatibility with existing tests. **Never use these in new code** — always use `_click_action_menu_item()`.

**5. `_js_click_popup_button()` — read and dismiss in single JS call**

```python
def handle_success_alert(self, timeout=1):
    WebDriverWait(self.driver, timeout).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-container"))
    )
    result = self.driver.execute_script("""
        var title = '';
        var titleEl = document.querySelector('#swal2-title');
        if (titleEl) title = titleEl.textContent.trim();
        var btn = document.querySelector('.swal2-confirm');
        if (btn) btn.click();
        document.querySelectorAll('.swal2-container').forEach(function(el) { el.remove(); });
        return title;
    """)
    return result if result else ""
```

This reads the SweetAlert title AND clicks confirm AND removes the container in a single JS call. Three operations in one round-trip to the browser, saving ~1 second per alert compared to the Selenium approach (read title → click button → wait for dismiss).

**6. NEVER use Keys.ESCAPE**

Documented in the page object header:
```
KEY RULES:
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
```

Pressing Escape while a dropdown overlay is open closes the ENTIRE popup form, losing all entered data. This is different from Tax Rate where Escape only closes the dropdown panel. **Vehicle Master is in the "never Escape" camp along with Bank.**

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| VM-001 | **High** | Angular refresh button breaks toolbar — search button disappears from DOM permanently. Must use browser refresh instead. |
| VM-002 | Medium | Vehicle Price is `type='character'` — no native number validation. Non-numeric input accepted by frontend. |
| VM-003 | Low | Stacked popups (History over View) can cause z-index conflicts that block interaction with the underlying popup |

---

## War Stories

### "The Refresh Button That Ate the Search Bar"
We were debugging a test that couldn't find the search button after clicking the ERP's refresh icon. After clicking refresh, the search toggle (`button.search-btn`) was simply gone from the DOM. Not hidden — gone. Inspecting the page source showed it was no longer rendered by Angular's component tree. The custom header component (`app-custom-header`) apparently doesn't re-include the search toggle on refresh.

The fix: always use `driver.refresh()` (full browser refresh) instead of the toolbar's refresh button. The `click_refresh()` method now exclusively uses `hard_refresh()`. If you ever see a test clicking the toolbar refresh button, that's a bug in the test.

### "Finding Vehicles Across Pages"
Vehicle Master can have hundreds of records, and the table uses pagination. A vehicle you just created might be on page 2 or page 5. The `ensure_vehicle_visible()` method was born from this — it tries direct table scan first (fast), then search (handles pagination), then hard refresh + search (handles stale search index). Without the 3-tier approach, ~30% of post-create verifications would fail because the vehicle wasn't on the first page.

### "The Deprecated Methods That Won't Die"
The original Vehicle Master page object used column-based CSS selectors for row actions: `mat-column-view button`, `mat-column-edit button`, `mat-column-archive button`. When the ERP updated to use a 3-dot kebab menu, we added `_click_action_menu_item()`. But removing the old methods would break 50+ existing tests. So we kept them as delegates:

```python
def _click_action_button(self, vehicle_name, action_xpath_template):
    """DEPRECATED — delegates to _click_action_menu_item()."""
    if "cdk-column-view" in action_xpath_template:
        return self._click_action_menu_item(vehicle_name, "View")
    elif "cdk-column-edit" in action_xpath_template:
        return self._click_action_menu_item(vehicle_name, "Edit")
    elif "cdk-column-history" in action_xpath_template:
        return self._click_action_menu_item(vehicle_name, "History")
```

The lesson: backward compatibility is important, but deprecated methods should be clearly marked and eventually removed. Don't let dead code accumulate indefinitely.

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
- Valid create with random dropdown values
- Valid create with description (optional field)
- Empty name → validation error
- Empty price → validation error
- Missing vehicle type → validation error
- Missing fuel type → validation error
- Special characters in name
- 255-char and 256-char names
- Zero price
- Negative price
- Alphabetic price (invalid)
- Decimal price
- Price with special characters
- Duplicate name → behavior depends on ERP state
- View mode → read-only
- Edit → update and verify
- History → audit trail check
- Stacked popup handling (History over View)

---

## Files

```
pages/common_settings/modules/vehicle_master/
├── vehicle_master_page.py          (1896 LOC — largest!)
├── Vehicle_Master_Automation_Guide.md
├── data/
│   └── vehicle_master_data.py     (288 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_vehicle_master_validation.py  (1421 LOC)
    └── api/
        ├── conftest.py
        ├── test_vehicle_master_payload.py
        ├── test_vehicle_master_schema.py
        └── test_vehicle_master_perf.py
```
