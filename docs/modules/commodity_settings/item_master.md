# Module: Item Master
> The most complex commodity module — 3-step stepper with an 8-level dropdown cascade that will destroy your test if you fill fields out of order.

## At a Glance

| Section | Detail |
|---|---|
| Complexity | **Highest** in commodity_settings |
| Steppers | 3 (Additional Details → Define Item Master Details → Product Order Packaging Details) |
| Repeating Rows | Yes — Step 3 grid table with Add Row |
| API Tests | 3 (schema, payload, perf) |
| UI Tests | 1 (validation) |
| Page Object | `item_master_page.py` (~3,150 LOC) |
| Data File | `item_master_data.py` (~843 LOC) |
| Batch Create | `scripts/batch_create.py` |
| attribute_name | `"Item Master"` |

## The ERP Screen

**What it does:** Defines every tradeable item in the system — grains, pulses, spices, FMCG, construction materials, office supplies, electrical goods. Each item is uniquely identified by the concatenation of its Category, Group, Type, and five cascading Attributes. This is the central registry that all other commodity modules (CQP, Base Rate, etc.) reference via FK.

**Navigation URL:** `/#/dynamic-screens/Item%20Master`

**Menu Path:** Commodity Settings → Commodity Master → Item Master

### Step 1 — "Additional Details"

| Field | Type | Required | Notes |
|---|---|---|---|
| Item Name | READONLY text | Auto | Space-separated concat of Attr 1-5; formcontrolname=`name` (NOT `itemName`) |
| Item Code | EDITABLE text | Auto | Dash-separated concat of Attr 1-5; formcontrolname=`code` (NOT `itemCode`) |
| Description | text input | No | Optional free text |
| Item Category | mat-select | **Yes** | **FILL FIRST** — 26 options; searchable |
| Item Group | mat-select | No | 25 options; searchable; NOT required |
| Item Type | mat-select | **Yes** | 2 options (Farm / Non Farm) |
| Item Attribute 1 | mat-select | No | 31 options; cascades from Category+Group+Type |
| Item Attribute 2 | mat-select | No | 32 options; cascades from Attribute 1 |
| Item Attribute 3 | mat-select | No | 29 options; cascades from Attribute 2 |
| Item Attribute 4 | mat-select | No | 28 options; cascades from Attribute 3 |
| Item Attribute 5 | mat-select | No | 28 options; cascades from Attribute 4 |
| UOM | mat-select | **Yes** | 20 options; searchable |
| HSN SAC Code | mat-select | **Yes** | 34 options; searchable |
| Base Uom | mat-select | **Yes** | 20 options; same pool as UOM but INDEPENDENT |
| Base Uom Conversion | text input | **Yes** | Numeric string; max 10 chars |
| Status | toggle | No | Active/Inactive; default Active; in `.big-model` parent |
| Is Critical | toggle | No | Yes/No; default No; on Step 0 stepper content |
| Include Wip Stock Cal | toggle | No | Yes/No; default No; on Step 0 stepper content |
| Is Packing Material | toggle | No | Yes/No; default No; on Step 0 stepper content |

> **⚠️ CRITICAL: "Allow Negative Stock" toggle DOES NOT EXIST.** It was incorrectly listed in V1 spec. Confirmed absent 2026-05-18. There are exactly 3 toggles on Step 1 (plus Status = 4 total), NOT 5.

### Step 2 — "Define Item Master Details"

| Field | Type | Required | Notes |
|---|---|---|---|
| Attachment Type | mat-select | No | Optional combobox |
| File Upload | file input | No | cloud_upload widget |

> Step 2 has NO toggles. It is attachment-only.

### Step 3 — "Product Order Packeging Details" (typo is in the actual ERP)

| Field | Type | Required | Notes |
|---|---|---|---|
| Packaging | mat-select | No | Per-row in `<app-dynamic-details>` grid table |
| Packaging Capacity | number input | No | Per-row |
| Base Packaging Capacity | number input | No | Per-row |

Step 3 uses `<table class="grid-table">` with `<tr>`/`<td>` rows. Starts with 1 default empty row. Add (+) button appends more.

## API Contract

**Endpoint:** `POST /core/dynamic-screen-wrapper/`

**attribute_name:** `"Item Master"`

### Payload Structure (3-step stepper)

```json
{
  "id": "",
  "attribute_name": "Item Master",
  "name": "",
  "code": "",
  "description": "...",
  "item_category": <FK_ID>,
  "item_group": <FK_ID>,
  "item_type": <FK_ID>,
  "item_attribute1": <FK_ID>,
  "item_attribute2": <FK_ID>,
  "item_attribute3": <FK_ID>,
  "item_attribute4": <FK_ID>,
  "item_attribute5": <FK_ID>,
  "uom": <FK_ID>,
  "hsn_sac_code": <FK_ID>,
  "base_uom": <FK_ID>,
  "base_uom_conversion": "1",
  "status": true,
  "children": [
    {
      "stepper_name": "Additional Details",
      "is_stepper": true,
      "details": [],
      "children": [],
      "is_critical": false,
      "include_wip_in_stock_cal": false,
      "is_packing_material": false
    },
    {
      "stepper_name": "Define Item Master Details",
      "is_stepper": true,
      "details": [],
      "children": [],
      "attachment_type": null,
      "item_attachment": null
    },
    {
      "stepper_name": "Product Order Packeging Details",
      "is_stepper": true,
      "details": [],
      "children": []
    }
  ]
}
```

### FK Dependencies

| Field | Source Table | Options | Required |
|---|---|---|---|
| item_category | Item Category | 26 | Yes |
| item_group | Item Group | 25 | No |
| item_type | Item Type (hardcoded) | 2 (Farm / Non Farm) | Yes |
| item_attribute1 | Item Attribute1 | 31 | No |
| item_attribute2 | Item Attribute2 | 32 | No |
| item_attribute3 | Item Attribute3 | 29 | No |
| item_attribute4 | Item Attribute4 | 28 | No |
| item_attribute5 | Item Attribute5 | 28 | No |
| uom | UOM | 20 | Yes |
| hsn_sac_code | HSN SAC Code | 34 | Yes |
| base_uom | UOM (same pool) | 20 | Yes |

## Data Layer

### FK Pools

All FK IDs are stored in `DEFAULT_ITEM_MASTER_FK_IDS` dict with 11 sub-dicts:

- `ITEM_CATEGORY_OPTIONS` — 26 entries (Green Veggies id=61 through Fertilizers id=81, plus Rice Varieties, etc.)
- `ITEM_GROUP_OPTIONS` — 25 entries (IG001 id=85 through PROC020 id=109)
- `ITEM_TYPE_OPTIONS` — 2 entries (Farm=113, Non Farm=114)
- `ITEM_ATTRIBUTE1_OPTIONS` — 31 entries (Soyabean=117 through Quinoa=147)
- `ITEM_ATTRIBUTE2_OPTIONS` — 32 entries (Green=65 through Corrugated Box=96)
- `ITEM_ATTRIBUTE3_OPTIONS` — 29 entries (Color=1 through Second Sort=29)
- `ITEM_ATTRIBUTE4_OPTIONS` — 28 entries (Moisture Resistant=55 through BOPP Film=82)
- `ITEM_ATTRIBUTE5_OPTIONS` — 28 entries (Premium Grade=51 through Global GAP=78)
- `UOM_OPTIONS` — 20 entries (KG=249 through SET60=537)
- `HSN_SAC_CODE_OPTIONS` — 34 entries (995411=108 through 2009=141)
- `BASE_UOM_OPTIONS` — same pool as UOM_OPTIONS

### Payload Builder

`build_item_master_api_payload()` resolves display names to FK IDs via `_resolve_fk()`. Takes 12 positional args (category through description) plus optional toggles and conversion factor.

`generate_item_master_payloads(count, offset)` iterates `ITEM_MASTER_DATA_POOL` (30+ realistic commodity entries across Food Grains, Pulses, Oilseeds, Spices, Fresh Produce, Dairy, Office, Cotton, Chemical, Packaged Foods).

### Validation Rules

| Field | Type | Required | Max Length | Note |
|---|---|---|---|---|
| name | character | No | 255 | AUTO-GENERATED, readonly in UI |
| code | character | No | 255 | AUTO-GENERATED, editable |
| description | character | No | 255 | Optional |
| base_uom_conversion | character | **Yes** | 10 | Numeric string |
| item_category | dropdown | **Yes** | — | 26 FK options |
| item_type | dropdown | **Yes** | — | 2 FK options |
| uom | dropdown | **Yes** | — | 20 FK options |
| hsn_sac_code | dropdown | **Yes** | — | 34 FK options |
| base_uom | dropdown | **Yes** | — | 20 FK options |

## Page Object

### Key Methods

| Method | Purpose |
|---|---|
| `navigate_to_page()` | Navigate + refresh to clear SPA state |
| `open_add_form()` | 4-strategy ADD button click |
| `fill_step1(data)` | Fill all Step 1 fields in correct order |
| `click_stepper_next()` | Advance to next step (3 strategies) |
| `click_stepper_back()` | Go to previous step |
| `get_current_step_index()` | Read active step (0/1/2) |
| `go_to_step(index)` | Jump to step by header click |
| `submit()` | Click Submit (Create mode) |
| `_select_mat_option()` | Select from mat-select dropdown |
| `_force_close_panels()` | JS removal of CDK overlay panes |
| `_close_select_panel()` | Backdrop click → JS removal fallback |

### Tricky Bits

1. **Dropdown fill order is CRITICAL:** You MUST fill `Category → Group → Type → Attr1 → Attr2 → Attr3 → Attr4 → Attr5` in that exact sequence. Filling Attr3 before Attr1 results in an empty dropdown — Angular only loads dependent options after the parent is selected.

2. **Browser-clicked mat-select options DON'T update Angular form model:** A standard Selenium `.click()` on a `mat-option` visibly selects it but the reactive form control remains `null`. You MUST use JS value-setter + `dispatchEvent` for all dropdown selections. The `_select_mat_option` method handles this by triggering Angular change detection.

3. **NEVER use `Keys.ESCAPE`:** It closes the entire stepper popup form, not just the dropdown overlay. Use `_close_dropdown_panel_only()` which does backdrop click + JS overlay removal.

4. **Toggle switches use custom component:** `<app-slide-toggle-v2>` with `<span class="main-label">` and `<div class="switch-wrapper compact">`. These are NOT standard Angular Material mat-slide-toggle.

5. **Stacked popups:** History → View can stack with z-index 1001 over 1000. Close history before opening view.

6. **Step 2 & 3 disabled in Edit mode:** Only Step 1 is editable after creation.

7. **Edit button says "Update":** Not "Submit".

8. **History column uses `mat-column-archive`** — NOT `mat-column-history`.

### Locator Strategies

| Element | Strategy | Rationale |
|---|---|---|
| Dropdowns | XPath by `mat-label` text | `name`/`formcontrolname` attributes vary across environments |
| Toggles | XPath by `app-slide-toggle-v2` + `main-label` | Custom component, not standard Angular |
| Stepper steps | CSS `mat-step-header` with `selected`/`active` class | Angular Material stepper API |
| Action buttons | XPath by `cdk-column-{action}` + item name text | Column classes are stable |
| Overlay panels | JS `document.querySelectorAll` + remove | Only reliable way to close without ESC |

## Known Bugs

| Bug ID | Severity | Description |
|---|---|---|
| IM-001 | HIGH | Browser-clicked mat-select options don't update Angular reactive form model — must use JS value-setter |
| IM-002 | MEDIUM | Duplicate Item Names ALLOWED — no uniqueness constraint |
| IM-003 | LOW | Base Uom does NOT auto-sync with UOM — they are independent fields |
| IM-004 | LOW | Item Group listed as required in some old specs but is NOT required (confirmed 2026-05-18) |
| IM-005 | LOW | Step 3 title has typo "Packeging" on the actual ERP page |

## War Stories

### The Dropdown Cascade That Ate Three Days

We spent three days debugging why `fill_step1()` would succeed for Category and Type but then fail silently on Attribute 1 — the dropdown appeared empty. The root cause: we were filling Category → Type → Group (skipping Group, which was optional) but the ERP's Angular code requires Group to be filled (even with a blank/first-option value) before the Attribute dropdowns load their options. The fix was to enforce the strict fill order: `Category → Group → Type → Attr1 → Attr2 → Attr3 → Attr4 → Attr5`, even though Group is not marked "required" in the business sense. After that, we also discovered that even with the correct fill order, browser-clicked options didn't register in Angular's reactive form model — the form appeared filled but submitted with null values. We had to rewrite `_select_mat_option()` to use `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set` + `dispatchEvent(new Event('input', {bubbles: true}))` for every dropdown.

### The Escape Key Incident

A junior engineer used `Keys.ESCAPE` to close a dropdown overlay inside the stepper form. It worked — the dropdown closed. But it also closed the entire stepper popup form, losing 20 seconds of carefully filled data. After that, we added `NEVER use Keys.ESCAPE` as a docstring comment in every method and implemented `_force_close_panels()` which removes overlay panes via JS `document.querySelectorAll` + `.remove()`. This pattern was later copied to every other module.

### The "4 Toggles" Myth

The original V1 spec listed "Allow Negative Stock" as a toggle on Item Master. We wrote tests for it, wrote locators for it, and spent hours wondering why the toggle didn't exist on the screen. Browser exploration on 2026-05-18 confirmed: only Status, Is Critical, Include Wip Stock Cal, and Is Packing Material exist. "Allow Negative Stock" was never implemented. The lesson: always verify the actual ERP screen before writing automation, even if the spec says otherwise.

## Test Coverage

| Test Type | Status | Count | File |
|---|---|---|---|
| API Schema | ✅ Pass | ~10 | `test/api/test_item_master_schema.py` |
| API Payload | ✅ Pass | ~8 | `test/api/test_item_master_payload.py` |
| API Performance | ✅ Pass | ~3 | `test/api/test_item_master_perf.py` |
| UI Validation | ✅ Pass | ~15 | `test/test_item_master_validation.py` |
| Batch Create | ✅ Working | — | `scripts/batch_create.py` |

## Files

```
item_master/
├── __init__.py                          ~0 LOC
├── item_master_page.py                  ~3,150 LOC
├── data/
│   ├── __init__.py                      ~0 LOC
│   └── item_master_data.py             ~843 LOC
├── scripts/
│   └── batch_create.py                  ~120 LOC
├── test/
│   ├── __init__.py                      ~0 LOC
│   ├── conftest.py                      ~45 LOC
│   ├── test_item_master_validation.py   ~350 LOC
│   └── api/
│       ├── __init__.py                  ~0 LOC
│       ├── conftest.py                  ~60 LOC
│       ├── test_item_master_schema.py   ~180 LOC
│       ├── test_item_master_payload.py  ~150 LOC
│       └── test_item_master_perf.py     ~80 LOC
└── Item_Master_Automation_Spec_Final_Updated.xlsx
```
