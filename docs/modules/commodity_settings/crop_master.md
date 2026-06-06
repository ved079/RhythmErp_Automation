# Module: Crop Master
> Flat, no-FK commodity screen that proves simple doesn't mean bug-free — and that `driver.refresh()` is not optional.

## At a Glance

| Section | Detail |
|---|---|
| Complexity | **Medium** |
| Steppers | 0 — flat popup form |
| Repeating Rows | No |
| API Tests | 3 (schema, payload, perf) |
| UI Tests | 1 (validation) |
| Page Object | `crop_master_page.py` (~1,505 LOC) |
| Data File | `crop_master_data.py` (~422 LOC) |
| Batch Create | `scripts/batch_create.py` |
| Report Generator | `cm_report_generator.py` (unique to this module) |
| attribute_name | `"Crop Master"` |

## The ERP Screen

**What it does:** Defines crop types in the system — cereals, pulses, oilseeds, spices, vegetables, fruits, fiber crops, plantation crops, fodder, and medicinal plants. Crops are the simplest commodity entity with just a name, description, file upload, and status toggle. Despite its simplicity, it has 9 documented bugs.

**Navigation URL:** `/#/dynamic-screens/Crop%20Master`

**Menu Path:** Commodity Settings → Crop Master

### Form Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| Name | text input | **Yes** | `name="Name"`; capital N; no maxlength |
| Description | text input | No | `name="Description"`; capital D |
| File Upload | file input | No | `.png`, `.jpg`, `.pdf` only |
| Status | toggle switch | No | Active/Inactive; default Active; custom `.slider` component |

### Table Columns

| Column | CSS Class |
|---|---|
| View | `cdk-column-view` |
| Edit | `cdk-column-edit` |
| History | `cdk-column-archive` (NOT `cdk-column-history`) |
| Name | `cdk-column-name` / `mat-column-name` |
| Description | `cdk-column-description` / `mat-column-description` |
| Status | `cdk-column-status` / `mat-column-status` |

## API Contract

**Endpoint:** `POST /core/dynamic-screen-wrapper/`

**attribute_name:** `"Crop Master"`

### Payload Structure (flat — no steppers, no children)

```json
{
  "id": "",
  "attribute_name": "Crop Master",
  "name": "Foxtail Millet",
  "description": "Thinai — drought-resistant small millet grown in dryland areas",
  "status": true
}
```

### FK Dependencies

**None.** `DEFAULT_CROP_MASTER_FK_IDS = {}`

This is the only commodity_settings module with zero FK dropdowns. The form has no mat-select elements at all — just text inputs, a file upload, and a toggle.

## Data Layer

### FK Pools

None. `DEFAULT_CROP_MASTER_FK_IDS = {}`

### Payload Builder

`build_crop_master_api_payload(name, description, status)` constructs a flat payload. No FK resolution needed.

`generate_crop_master_payloads(count, offset)` iterates `CROP_MASTER_API_DATA` — a pool of 80+ realistic crop entries organized by category:

- **Cereals & Millets** (10): Foxtail Millet, Proso Millet, Triticale, Oats, Quinoa, Buckwheat, etc.
- **Pulses & Legumes** (10): Moong Dal, Urad Dal, Masoor Dal, Horse Gram, Lobia, Rajma, etc.
- **Oilseeds** (8): Groundnut, Sunflower, Safflower, Sesame, Linseed, Castor, etc.
- **Spices & Condiments** (10): Turmeric, Black Pepper, Cardamom, Cumin, Nutmeg, Clove, etc.
- **Vegetables** (6): Onion, Potato, Brinjal, Cauliflower, Cabbage, Okra
- **Fruits** (10): Banana, Guava, Papaya, Litchi, Grape, Orange, Pineapple, etc.
- **Fiber Crops** (4): Jute, Mesta, Ramie, Sunn Hemp
- **Plantation & Cash Crops** (5): Coffee, Arecanut, Cocoa, Vanilla, Cashew
- **Fodder & Forage** (5): Sorghum Fodder, Berseem, Lucerne, Napier Grass, Oat Fodder
- **Medicinal & Aromatic** (8): Ashwagandha, Aloe Vera, Lemongrass, Vetiver, Stevia, etc.

Wrap-around deduplication appends `(Batch N)` suffix for pool reuse.

### Validation Rules

| Field | Type | Required | Max Length | Note |
|---|---|---|---|---|
| name | character | **Yes** | 255 | Duplicates currently allowed (BUG-CM02) |
| description | character | No | 255 | Optional |
| status | toggle | No | — | Default: Active (True) |

## Page Object

### Key Methods

| Method | Purpose |
|---|---|
| `navigate_to_page()` | Navigate + **refresh** to clear SPA state |
| `open_add_form()` | 4-strategy ADD button click |
| `fill_crop_form(data)` | Fill Name → Description → File → Status |
| `toggle_status()` | Click `.slider` via JS (NOT the hidden checkbox) |
| `get_current_status()` | Read `state-label.on.active` / `state-label.off.active` |
| `set_status(desired)` | Toggle only if current ≠ desired |
| `upload_file(path)` | `send_keys` on `input[type='file']` |
| `search_crop(name)` | JS value injection + `input` event dispatch + Enter |
| `click_view/edit/history_button()` | Action buttons with 2-strategy approach |

### Tricky Bits

1. **`refresh()` is CRITICAL:** Crop Master's `navigate_to_page()` calls `self.driver.refresh()` after navigation. Without it, leftover Angular SPA state (stale overlays, zombie form popups) can block the ADD button. This was the first module where we discovered the SPA state problem and it became the pattern for all subsequent modules.

2. **Status toggle uses custom `.slider`:** The toggle is NOT a standard Angular Material `mat-slide-toggle`. It's a custom component using `.slider` CSS class with `.switch-container` wrapper. Clicking the hidden `<input type="checkbox">` directly doesn't work. You must click the visible `.slider` element via JS.

3. **Search uses JS value injection:** The search input is an Angular reactive form control. Standard `send_keys()` + `clear()` often doesn't trigger Angular's change detection. The working approach is:
   ```python
   nativeInputValueSetter.call(input, search_text)
   input.dispatchEvent(new Event('input', {bubbles: true}))
   input.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter'}))
   ```

4. **History popup uses `.popup-overlay`:** Unlike Vehicle Master which uses `.big-model`, Crop Master's history popup is in a `div.popup-overlay` container. The close button XPath differs.

5. **SweetAlert2 auto-dismisses quickly:** The success toast may auto-dismiss before the test can read it. Wait with explicit timeout.

### Locator Strategies

| Element | Strategy | Rationale |
|---|---|---|
| Name/Description inputs | CSS `input[name='Name']` / `input[name='Description']` | Capital N/D in name attr |
| Status toggle | CSS `.edit_pop_up .slider` | Custom component, not mat-slide-toggle |
| History popup | CSS `.popup-overlay` + `h3` contains 'history' | Different from Vehicle Master's `.big-model` |
| Table cells | CSS `td.cdk-column-name`, `td.cdk-column-archive` | Standard cdk column classes |

## Known Bugs

| Bug ID | Severity | Description |
|---|---|---|
| BUG-CM01 | HIGH | Blank name accepted on Create — no client-side validation |
| BUG-CM02 | HIGH | Duplicate names allowed — no uniqueness constraint |
| BUG-CM03 | MEDIUM | Leading/trailing spaces not trimmed — saved as-is |
| BUG-CM04 | MEDIUM | No per-field inline `mat-error` elements — only SweetAlert2 |
| BUG-CM05 | MEDIUM | No maxlength validation — 300+ char names accepted |
| BUG-CM06 | MEDIUM | Special characters accepted without sanitization |
| BUG-CM07 | LOW | No history entry on creation — history table empty |
| BUG-CM08 | LOW | History sort doesn't work |
| BUG-CM09 | MEDIUM | Blank name accepted on Edit — same as BUG-CM01 |

## War Stories

### The Refresh That Saved Everything

Crop Master was the first module where we noticed intermittent ADD button failures. The button was visible, clickable, but nothing happened. After hours of debugging, we realized the Angular SPA kept stale overlays and zombie form popups from previous test runs. Adding `self.driver.refresh()` after `navigate_to()` fixed it instantly. This became a mandatory pattern for every module's `navigate_to_page()` method.

### The Status Toggle That Wouldn't Toggle

We initially tried clicking the `<input type="checkbox">` inside the status toggle component. Selenium reported success, the element was clicked, but the visual state didn't change — Angular's reactive form didn't register the change. After inspecting the DOM, we discovered the visual toggle was a `.slider` div that intercepted clicks and toggled the checkbox internally. Clicking the checkbox directly bypassed the component's change detection. The fix: always click the `.slider` element via JS.

### Nine Bugs in the Simplest Screen

Crop Master has the simplest form in the entire commodity_settings section — just Name, Description, File, Status. Yet it has 9 documented bugs, the most per-field of any module. The lesson: simplicity in form design doesn't correlate with correctness in validation. The server accepts virtually anything and the client-side validation is nearly non-existent.

## Test Coverage

| Test Type | Status | Count | File |
|---|---|---|---|
| API Schema | ✅ Pass | ~8 | `test/api/test_crop_master_schema.py` |
| API Payload | ✅ Pass | ~6 | `test/api/test_crop_master_payload.py` |
| API Performance | ✅ Pass | ~3 | `test/api/test_crop_master_perf.py` |
| UI Validation | ✅ Pass | ~12 | `test/test_crop_master_validation.py` |
| Batch Create | ✅ Working | — | `scripts/batch_create.py` |

## Files

```
crop_master/
├── __init__.py                          ~0 LOC
├── crop_master_page.py                  ~1,505 LOC
├── cm_report_generator.py               ~250 LOC
├── Crop_Master_Automation_Guide.md      ~120 LOC
├── data/
│   ├── __init__.py                      ~0 LOC
│   └── crop_master_data.py             ~422 LOC
├── scripts/
│   └── batch_create.py                  ~80 LOC
├── test/
│   ├── __init__.py                      ~0 LOC
│   ├── conftest.py                      ~40 LOC
│   ├── test_crop_master_validation.py   ~280 LOC
│   └── api/
│       ├── __init__.py                  ~0 LOC
│       ├── conftest.py                  ~55 LOC
│       ├── test_crop_master_schema.py   ~150 LOC
│       ├── test_crop_master_payload.py  ~130 LOC
│       └── test_crop_master_perf.py     ~70 LOC
└── Crop_Master_Automation_Spec_Final_Updated.xlsx
```
