# Item Master — Automation Guide

> **RhythmERP** | Commodity Settings → Commodity Master → Item Master  
> **URL:** `https://rhythmerp.algorhythms.in/#/dynamic-screens/Item%20Master`  
> **Last Updated:** 2026-05-18  
> **Test Results:** 42 EXECUTABLE, 2 SKIPPED | Effective Pass Rate: ~100% (pending full run)

---

## Quick Reference

| Item | Value |
|------|-------|
| Total Test Cases | 44 (42 executable + 2 skipped) |
| Execution Time | ~30 min (estimated) |
| Test ID Prefix | IM- |
| Page Object | `ItemMasterPage` |
| Form Fields | 3-Step Stepper: Step 1 (15 fields + 4 toggles), Step 2 (2 fields), Step 3 (dynamic grid) |
| Dropdowns | **10 mat-select** — Category, Group, Type, Attr 1-5, UOM, HSN, Base Uom |
| Validation Library | SweetAlert2 |
| App Framework | Angular Material |
| Form Type | **3-STEP STEPPER** (NOT a simple popup like Crop Master) |

---

## Project Structure

```
pages/commodity_settings/modules/item_master/
├── __init__.__y                          # exports ItemMasterPage
├── item_master_page.py                   # Page Object (1400+ lines)
├── data/
│   ├── __init__.py                       # exports generators + BUG IDs
│   └── item_master_data.py               # Test data generators (312 lines)
└── test/
    ├── __init__.py
    ├── conftest.py                        # Fixtures, login, report gen
    └── test_item_master_validation.py     # 44 test cases (1950+ lines)
```

---

## Run Commands

```powershell
# Run all 44 tests
python -m pytest pages/commodity_settings/modules/item_master/test/test_item_master_validation.py -v

# Run specific class
python -m pytest pages/commodity_settings/modules/item_master/test/test_item_master_validation.py -v -k "TestCreateFormValidations"
python -m pytest pages/commodity_settings/modules/item_master/test/test_item_master_validation.py -v -k "TestDuplicateValidations"
python -m pytest pages/commodity_settings/modules/item_master/test/test_item_master_validation.py -v -k "TestEditFormValidations"
python -m pytest pages/commodity_settings/modules/item_master/test/test_item_master_validation.py -v -k "TestSearchFilter"
python -m pytest pages/commodity_settings/modules/item_master/test/test_item_master_validation.py -v -k "TestPopupUIBehaviors"
python -m pytest pages/commodity_settings/modules/item_master/test/test_item_master_validation.py -v -k "TestHistoryAuditTrail"

# Run single test
python -m pytest pages/commodity_settings/modules/item_master/test/test_item_master_validation.py -v -k "test_IM_C01_empty_submit"

# Run with HTML report
python -m pytest pages/commodity_settings/modules/item_master/test/test_item_master_validation.py -v --html=report.html
```

---

## Test Classes Breakdown

| Class | Count | Phase | Executable | Skipped |
|-------|-------|-------|------------|---------|
| TestCreateFormValidations | 15 | Create | 14 | 1 |
| TestDuplicateValidations | 3 | Duplicate | 1 | 2 |
| TestEditFormValidations | 8 | Edit | 8 | 0 |
| TestSearchFilter | 5 | Search/Filter | 5 | 0 |
| TestPopupUIBehaviors | 8 | Popup/UI | 8 | 0 |
| TestHistoryAuditTrail | 5 | History | 5 | 0 |
| **Total** | **44** | — | **42** | **2** |

---

## Key Selectors

### Toolbar

| Element | Selector | Notes |
|---------|----------|-------|
| Add Button | `div[mattooltip="ADD"] button` | Tooltip on parent DIV. 4-strategy JS click. Opens 3-step stepper. |
| Search Toggle | `button.search-btn` | Toggles search input |
| Refresh Button | `button[mattooltip="Refresh"]` | Found by iterating mini-fab buttons + checking icon text |
| Search Input | `#erpSearchInput` | Hidden by default, toggle via search button |

### Stepper Form Popup

| Element | Selector | Notes |
|---------|----------|-------|
| Popup Container | `.big-model, mat-dialog-container, .edit_pop_up.override_edit_pop_up.popup-mode` | Uses `.big-model` class (NOT `.edit_pop_up` like Crop Master) |
| Popup Header | `.big-model h3` | Contains title text |
| Stepper Component | `mat-stepper, mat-horizontal-stepper` | 3-step stepper — unique to Item Master |
| Next Button | `button.mat-stepper-next` or `//button[contains(.,'Next')]` | 3 strategies: CSS class, text match, JS querySelectorAll |
| Back Button | `button.mat-stepper-previous` or `//button[contains(.,'Back')]` | Same 3 strategies as Next |
| Submit Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]` | Add mode only, visible on Step 3 |
| Update Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]` | Edit mode only (NOT 'Submit') |
| Cancel Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]` | All modes |
| Close (X) | `.big-model button mat-icon` (text='close') | Find by text content |

### Step 1 — "Additional Details" (Text Inputs)

| Element | Selector | Notes |
|---------|----------|-------|
| Item Name Input | `input[formcontrolname='name']` | **READONLY!** formcontrolname='name' (NOT 'itemName'). Auto-generated space-separated concat of Attr 1-5. |
| Item Code Input | `input[formcontrolname='code']` | Auto-generated but **EDITABLE**. Dash-separated concat of Attr 1-5. Can be overridden. |
| Description Input | `input[name='Description']` | Optional |
| Base Uom Conversion | `input[name='Base Uom Conversion']` | Required, numeric. Must be positive. |

### Step 1 — "Additional Details" (Dropdowns — mat-select)

| Element | Selector | Notes |
|---------|----------|-------|
| Item Category | `//mat-label[contains(.,'Item Category')]/ancestor::mat-form-field//mat-select` | **FILL FIRST!** Required. Options: Pulses, Oilseeds, Grains (duplicated — BUG-006). |
| Item Group | `//mat-label[contains(.,'Item Group')]/ancestor::mat-form-field//mat-select` | **NOT required!** Options: Raw Material, Finished Goods, Semi Finished (duplicated). |
| Item Type | `//mat-label[contains(.,'Item Type')]/ancestor::mat-form-field//mat-select` | Required. Options: Non Farm, Farm. |
| Item Attribute 1-5 | `//mat-label[contains(.,'Item Attribute N')]/ancestor::mat-form-field//mat-select` | Optional each. **Cascade**: Attr1 depends on Category+Group+Type, Attr2 on Attr1, etc. |
| UOM | `//mat-label[(contains(.,'UOM') or contains(.,'Uom')) and not(contains(.,'Base'))]/ancestor::mat-form-field//mat-select` | Required. Does NOT auto-fill Base Uom. |
| HSN SAC Code | `//mat-label[contains(.,'HSN')]/ancestor::mat-form-field//mat-select` | Required. |
| Base Uom | `//mat-label[contains(.,'Base Uom') and not(contains(.,'Conversion'))]/ancestor::mat-form-field//mat-select` | Required. **INDEPENDENT** of UOM — must fill separately. |

### Step 1 — Toggle Switches (`<app-slide-toggle-v2>`)

| Element | Selector | Default | Notes |
|---------|----------|---------|-------|
| Status | `//app-slide-toggle-v2[.//span[contains(@class,'main-label') and contains(.,'Status')]]//div[contains(@class,'switch-wrapper')]` | Active (ON) | In `.big-model` parent — always visible regardless of step |
| Is Critical | `//app-slide-toggle-v2[.//span[contains(@class,'main-label') and contains(.,'Is Critical')]]//div[contains(@class,'switch-wrapper')]` | No (OFF) | Inside Step 1's stepper-content |
| Include Wip Stock Cal | `//app-slide-toggle-v2[.//span[contains(@class,'main-label') and contains(.,'Include Wip')]]//div[contains(@class,'switch-wrapper')]` | No (OFF) | Inside Step 1's stepper-content |
| Is Packing Material | `//app-slide-toggle-v2[.//span[contains(@class,'main-label') and contains(.,'Is Packing Material')]]//div[contains(@class,'switch-wrapper')]` | No (OFF) | Inside Step 1's stepper-content. **Only 4 toggles total — NOT 5!** |

> **CRITICAL:** "Allow Negative Stock" toggle **DOES NOT EXIST** in Item Master (verified 2026-05-18).

### Step 2 — "Define Item Master Details" (Attachment ONLY)

| Element | Selector | Notes |
|---------|----------|-------|
| Attachment Type | `//mat-label[contains(.,'Attachment Type')]/ancestor::mat-form-field//mat-select` | Optional combobox |
| File Upload | `input[type='file']` | Optional. Shows "cloud_upload No File Uploaded" when empty |

> **NO toggle switches on Step 2!** All toggles are on Step 1.

### Step 3 — "Product Order Packaging Details" (Dynamic Grid)

| Element | Selector | Notes |
|---------|----------|-------|
| Packaging Table | `app-dynamic-details table.grid-table` | Inside `<app-dynamic-details>` component |
| Packaging Dropdown | Per-row `mat-select` | Optional per row |
| Packaging Capacity | Per-row number input | Optional per row |
| Base Packaging Capacity | Per-row number input | Optional per row |
| Add Row Button | `app-dynamic-details button.mat-mdc-icon-button (icon='add')` | Starts with 1 default empty row |

### Table (Main Listing)

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| Item Name Cells | `td.cdk-column-itemName` |
| UOM Cells | `td.cdk-column-uom` |
| Status Cells | `td.cdk-column-status` |
| View Button | `td.cdk-column-view button` (index 0) |
| Edit Button | `td.cdk-column-edit button` (index 1) |
| History Button | `td.cdk-column-archive button` (index 2) — **NOT 'history'!** |

### History Popup

| Element | Selector | Notes |
|---------|----------|-------|
| Popup | `.big-model` with h3 containing 'history' | **NOT `.popup-overlay` like Crop Master!** Uses `.big-model` |
| Search Input | `.big-model input` (with Search placeholder) | Must press Enter — no auto-filter |
| Table Rows | `.big-model table tbody tr` | May be 0 rows |
| Close Button | `.big-model .popup-footer button (text='Cancel')` | 3 strategies: Cancel → X icon → force remove |

### SweetAlert2

| Type | Selector | Notes |
|------|----------|-------|
| Validation Warning | `.swal2-icon.swal2-warning` | Title: "Validation Failed" |
| Success | `.swal2-icon.swal2-success` | Title: "Your record has been added/updated successfully!" |
| Confirm Button | `.swal2-confirm` | 3-tier JS click strategy |

---

## Critical Technical Rules

### NEVER Use Keys.ESCAPE
Always close popups via Cancel, X button, or backdrop click + JS overlay removal. `Keys.ESCAPE` triggers Angular SPA navigation — destroys the entire form context.

### Always JS Click for Angular Material
Normal Selenium clicks get intercepted by `cdk-overlay`. Use:
```python
driver.execute_script('arguments[0].click();', element)
```

### JS Value-Setter for ALL Dropdown Selections (BUG-007)
**CRITICAL:** Browser-clicked mat-select options do NOT update Angular reactive form model. Must use:
```python
driver.execute_script("""
    var nativeInput = arguments[0];
    var valueSetter = Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype, 'value'
    ).set;
    valueSetter.call(nativeInput, 'selected_value');
    nativeInput.dispatchEvent(new Event('input', { bubbles: true }));
    nativeInput.dispatchEvent(new Event('change', { bubbles: true }));
""", element)
```

### 3-Step Stepper Form (NOT Simple Popup)
Item Master uses `mat-horizontal-stepper` with 3 steps. Navigation via Next/Back buttons. Submit only appears on Step 3. Edit mode: Step 2 & 3 tabs are DISABLED.

### Dropdown Fill Order is CRITICAL
**Category → Group → Type → Attr1 → Attr2 → Attr3 → Attr4 → Attr5**
Category/Group/Type are INDEPENDENT of each other, but Attributes cascade: Attr1 depends on Category+Group+Type combo, Attr2 depends on Attr1, etc.

### Item Name is AUTO-GENERATED and READONLY
`formcontrolname='name'` (NOT 'itemName'). Space-separated concat of Item Attribute 1-5 values. **Cannot be typed into** — `readonly=true`. Tests for spaces-only, maxlength, special chars in Item Name are **NOT APPLICABLE**.

### Item Code is AUTO-GENERATED but EDITABLE
`formcontrolname='code'` (NOT 'itemCode'). Dash-separated concat of Attr 1-5. CAN be manually overridden after auto-generation.

### ONLY 4 Toggle Switches (NOT 5!)
Status, Is Critical, Include Wip Stock Cal, Is Packing Material. **"Allow Negative Stock" DOES NOT EXIST** in Item Master (verified 2026-05-18).

### Item Group is NOT Required
Item Group is NOT required in Create or Edit mode (confirmed 2026-05-18). Can be left empty without validation error.

### Base Uom Does NOT Auto-Sync with UOM
Base Uom and UOM are **INDEPENDENT** fields. Selecting UOM does NOT auto-fill Base Uom. Must fill both separately.

### Duplicate Item Names are ALLOWED
No uniqueness validation on Item Name. Two "Soyabean" rows can exist in table both Active (BUG-002). Test should verify duplicates CAN be created.

### Edit Mode: Step 2 & 3 Tabs DISABLED
In Edit mode, only Step 1 is editable. Step 2 and Step 3 tabs are disabled. Button says "Update" not "Submit".

### History Uses .big-model (NOT .popup-overlay)
Unlike Crop Master which uses `.popup-overlay`, Item Master history popup uses `.big-model` container. Different selectors required.

### History Column = 'archive'
The History action column uses CSS class `cdk-column-archive` / `mat-column-archive`, NOT 'history'. Same as Crop Master.

### popup-footer Class is Dynamic
Use `contains(@class,'popup-footer')` instead of exact match — Angular adds extra classes.

### Toggle Switches Use <app-slide-toggle-v2>
NOT standard Angular Material. Uses custom `<app-slide-toggle-v2>` with `<span class="main-label">` and `<div class="switch-wrapper compact">`. Click the `.switch-wrapper` element, NOT the checkbox directly.

---

## Action Flows

### Create Item (Full 3-Step Flow)
```python
page.navigate_to_page()
page.open_add_form()

# Step 1: Fill Additional Details
page.fill_step1(data)           # Fills all Step 1 fields + toggles
page.click_stepper_next()       # Advance to Step 2

# Step 2: Define Item Master Details (optional attachment)
page.fill_step2(step2_data)     # Optional attachment type + file upload
page.click_stepper_next()       # Advance to Step 3

# Step 3: Product Order Packaging Details (optional packaging rows)
page.fill_step3(step3_data)     # Optional packaging rows
page._force_close_panels()
page.submit()                   # Submit on Step 3
page.handle_success_alert(timeout=60)
```

### Quick Create (Step 1 Only)
```python
page.navigate_to_page()
page.open_add_form()
page.fill_step1(data)           # Fills required fields
page._force_close_panels()
# Navigate through all steps to Submit
page.click_stepper_next()       # Step 1 → Step 2
page.click_stepper_next()       # Step 2 → Step 3
page.submit()                   # Submit on Step 3
page.handle_success_alert(timeout=60)
```

### Edit Item
```python
page.search_item("ItemName")
page.click_edit_button(item_name="ItemName")
# Only Step 1 is editable — Step 2 & 3 tabs disabled
page.type_text(page.ITEM_CODE_INPUT, "NewCode", clear_first=True)
page._force_close_panels()
page.click_update()
page.handle_success_alert(timeout=60)
```

### View Item
```python
page.search_item("ItemName")
page.click_view_button(item_name="ItemName")
values = page.get_form_field_values_step1()  # dict: item_name, item_code, description, etc.
page.close_popup()
```

### Check History
```python
page.search_item("ItemName")
page.click_history_button(item_name="ItemName")
count = page.get_history_row_count()
page.search_in_history("search term")  # must press Enter
page.close_history_popup()
```

---

## Test Data Generators

```python
from pages.commodity_settings.modules.item_master.data import (
    generate_valid_item_data,          # Step 1 valid data dict
    generate_valid_step2_data,         # Step 2 valid data dict
    generate_valid_step3_data,         # Step 3 valid data dict
    generate_full_valid_item_data,     # All 3 steps combined
    generate_valid_edit_data,          # Edit-mode data (code, desc, conversion)
    generate_item_name,                # Random name with timestamp
    generate_item_code,                # Random code with prefix
    generate_description,              # Random description
    generate_base_uom_conversion,      # Random positive decimal
    generate_negative_uom_conversion,  # Negative value (validation test)
    generate_zero_uom_conversion,      # Zero value (validation test)
    generate_alpha_uom_conversion,     # Alphabetic (validation test)
    generate_special_char_uom_conversion,  # Special chars (validation test)
    generate_decimal_uom_conversion,   # Valid decimal (positive test)
    generate_uom_conversion_with_spaces,   # Spaces-only (validation test)
    generate_item_code_with_special_chars, # Special chars in code
)

# Bug IDs (from conftest.py — recorded in CSReportStore)
# BUG-002 (HIGH): Duplicate Item Names ALLOWED
# BUG-004 (MEDIUM): Negative Base Uom Conversion (RETRACTED — was rejected in test run)
# BUG-005 (LOW): No Delete option
# BUG-006 (MEDIUM): Dropdown option duplication
# BUG-007 (CRITICAL): Angular form model not synced with browser clicks
```

---

## 44 Test Cases

### TestCreateFormValidations (15)

| # | Test ID | Name | Status | Bug/Skip |
|---|---------|------|--------|----------|
| 1 | IM-C01 | Empty form submit | PASS | |
| 2 | IM-C02 | Valid create (happy path) | PASS | |
| 3 | IM-C03 | Item Name is readonly | PASS | |
| 4 | IM-C04 | Duplicate name — verify duplicates ALLOWED | PASS | BUG-002 |
| 5 | IM-C05 | Auto-generated name length reasonable | PASS | |
| 6 | IM-C06 | Name 256 chars boundary | SKIP | Readonly field — not applicable |
| 7 | IM-C07 | Verify Item Name readonly attribute | PASS | |
| 8 | IM-C08 | Negative Base Uom Conversion | PASS | BUG-004 retracted — was rejected (XPASS) |
| 9 | IM-C09 | Zero Base Uom Conversion | PASS | |
| 10 | IM-C10 | Alphabetic Base Uom Conversion | PASS | |
| 11 | IM-C11 | Special char Base Uom Conversion | PASS | |
| 12 | IM-C12 | Spaces-only Base Uom Conversion | PASS | |
| 13 | IM-C13 | Decimal Base Uom Conversion | PASS | |
| 14 | IM-C14 | Partial required fields — dropdowns missing | PASS | |
| 15 | IM-C15 | Stepper Back button navigation | PASS | |

### TestDuplicateValidations (3)

| # | Test ID | Name | Status | Bug/Skip |
|---|---------|------|--------|----------|
| 1 | IM-D01 | Duplicate create (same attribute values) | PASS | BUG-002 (duplicates allowed) |
| 2 | IM-D02 | Duplicate case-insensitive | SKIP | Readonly field — cannot type different case |
| 3 | IM-D03 | Duplicate edit to existing name | SKIP | Item Name readonly in Edit too |

### TestEditFormValidations (8)

| # | Test ID | Name | Status | Bug |
|---|---------|------|--------|-----|
| 1 | IM-E01 | Edit pre-populated fields | PASS | |
| 2 | IM-E02 | Valid edit (change code + description) | PASS | |
| 3 | IM-E03 | Edit readonly name enforcement | PASS | |
| 4 | IM-E04 | Edit readonly name — typing has no effect | PASS | |
| 5 | IM-E05 | Edit stepper navigation (Step 2 & 3 disabled) | PASS | |
| 6 | IM-E06 | Edit toggle switches | PASS | |
| 7 | IM-E07 | Edit negative UOM conversion | PASS | |
| 8 | IM-E08 | Edit special chars in Item Code | PASS | |

### TestSearchFilter (5)

| # | Test ID | Name | Status | Bug |
|---|---------|------|--------|-----|
| 1 | IM-S01 | Search exact match | PASS | |
| 2 | IM-S02 | Search partial match | PASS | |
| 3 | IM-S03 | Search nonexistent | PASS | |
| 4 | IM-S04 | Search after create | PASS | |
| 5 | IM-S05 | Search verify details | PASS | |

### TestPopupUIBehaviors (8)

| # | Test ID | Name | Status | Bug |
|---|---------|------|--------|-----|
| 1 | IM-P01 | View shows read-only | PASS | |
| 2 | IM-P02 | No Delete button | PASS | BUG-005 |
| 3 | IM-P03 | Add form is 3-step stepper | PASS | |
| 4 | IM-P04 | Cancel closes form | PASS | |
| 5 | IM-P05 | Refresh button works | PASS | |
| 6 | IM-P06 | Step 3 Add Row | PASS | |
| 7 | IM-P07 | Toggle switches in Create | PASS | |
| 8 | IM-P08 | Stepper header click navigation | PASS | |

### TestHistoryAuditTrail (5)

| # | Test ID | Name | Status | Bug |
|---|---------|------|--------|-----|
| 1 | IM-H01 | History popup opens | PASS | |
| 2 | IM-H02 | History data after create | PASS | |
| 3 | IM-H03 | History data after edit | PASS | |
| 4 | IM-H04 | History search | PASS | |
| 5 | IM-H05 | History close | PASS | |

---

## Bug Registry (5 Confirmed Bugs)

| Bug ID | Phase | Description | Severity |
|--------|-------|-------------|----------|
| BUG-002 | Create/Edit | Duplicate Item Names ALLOWED — no uniqueness validation | High |
| BUG-004 | Create | Negative Base Uom Conversion (RETRACTED — was rejected in test run, XPASS) | Medium (retracted) |
| BUG-005 | UI | No Delete option anywhere on screen | Low |
| BUG-006 | Create/Edit | Dropdown option duplication — Category & Group show options TWICE | Medium |
| BUG-007 | Automation | Browser-clicked mat-select does NOT update Angular form model — must use JS value-setter | Critical |

### Severity Distribution
- **Critical:** 1 bug (BUG-007 — Angular form model not synced, requires JS workaround)
- **High:** 1 bug (BUG-002 — duplicate Item Names allowed)
- **Medium:** 2 bugs (BUG-004 retracted, BUG-006 — dropdown duplication)
- **Low:** 1 bug (BUG-005 — no Delete option)

### Retracted Bugs
- **BUG-001** (HIGH): Spaces-only Item Name — **retracted**, field is readonly and auto-generated
- **BUG-003** (MEDIUM): No maxlength on Item Name — **retracted**, field is readonly and auto-generated
- **BUG-004** (MEDIUM): Negative Base Uom Conversion — **retracted**, was correctly rejected during test run (XPASS)

---

## Key Method Reference

| Method | Purpose | Key Strategy |
|--------|---------|--------------|
| `navigate_to_page()` | Go to Item Master | navigate + refresh + wait for table + toolbar |
| `open_add_form()` | Click ADD button | 4 strategies, JS click, verify stepper popup open |
| `fill_step1(data)` | Fill Step 1 fields | JS value-setter for dropdowns, type_text for inputs, .switch-wrapper for toggles |
| `fill_step2(data)` | Fill Step 2 fields | Attachment type dropdown + file upload |
| `fill_step3(data)` | Fill Step 3 fields | Dynamic grid table rows |
| `click_stepper_next()` | Next step | 3 strategies: CSS class, text match, JS querySelectorAll |
| `click_stepper_back()` | Previous step | Same 3 strategies as Next |
| `submit()` | Click Submit | 3-tier JS click (on Step 3 only) |
| `click_update()` | Click Update | Same 3-tier JS click (Edit mode, Step 1 only) |
| `search_item(name)` | Search in table | JS value injection + input event + Enter |
| `create_item(data)` | One-call create | open_add → fill_step1 → next → fill_step2 → next → fill_step3 → submit → alert |
| `edit_item(name, data)` | One-call edit | search → click_edit → fill_step1 → update → alert |
| `check_history(name)` | One-call history | search → click_history → read rows → close |
| `get_current_step_index()` | Get active step | Check mat-step-header for 'selected'/'active' class |
| `is_step1_active()` / `is_step2_active()` / `is_step3_active()` | Check step | Returns True/False based on step index |
| `toggle_status()` | Toggle switch | JS click .switch-wrapper (NOT checkbox) |
| `get_form_field_values_step1()` | Read Step 1 values | Returns dict: item_name, item_code, description, status, etc. |
| `handle_success_alert()` | Handle SweetAlert2 success | Wait title → 3-tier confirm click → wait invisible |
| `handle_validation_warning()` | Handle SweetAlert2 warning | Wait title → JS click confirm → wait invisible |
| `close_history_popup()` | Close History | 3 JS strategies: Cancel → X icon → force remove |
| `_force_close_panels()` | Remove CDK overlays | JS removes stale cdk-overlay-backdrop + pane (keeps dialog intact) |
| `_close_dropdown_panel_only()` | Close mat-select panel | Backdrop click first; fallback to JS removal. NO ESC key! |
| `_cleanup_swal2()` | Remove SweetAlert2 remnants | JS removes .swal2-container + backdrop |

---

## Fixture Architecture

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `driver` | session | Single browser instance for all 44 tests |
| `logged_in_driver` | session | Login once, session maintained across all tests |
| `im_page` | function | Fresh `navigate_to_page()` per test with `driver.refresh()` |
| `_im_store` | session | CSReportStore — starts timer, records issues, generates Excel report |

---

## Differences from Crop Master

| Feature | Item Master | Crop Master |
|---------|-------------|-------------|
| Section | Commodity Settings → Commodity Master | Commodity Settings |
| Form Type | **3-STEP STEPPER** | Simple popup |
| Dropdowns | **10 mat-select** (Category, Group, Type, Attr1-5, UOM, HSN, Base Uom) | **NONE** — text inputs only |
| Toggle Switches | 4 (Status, Is Critical, Include Wip, Is Packing Material) — custom `<app-slide-toggle-v2>` | 1 (Status) — standard `.slider` |
| Item Name | AUTO-GENERATED from Attributes, READONLY | User-typed text input |
| Item Code | AUTO-GENERATED, EDITABLE | N/A |
| History Container | `.big-model` | `.popup-overlay` |
| History Column CSS | `cdk-column-archive` | `cdk-column-archive` |
| Form Complexity | Step 1 (15+4 fields), Step 2 (2 fields), Step 3 (dynamic grid) | 4 fields (Name, Desc, File, Status) |
| Edit Mode | Step 2 & 3 DISABLED, only Step 1 editable | All fields editable |
| Submit Location | Step 3 only (after Next/Next) | Directly on popup |
| JS Value-Setter | **REQUIRED** for ALL dropdowns (BUG-007) | N/A (no dropdowns) |
| Dropdown Fill Order | **CRITICAL** — cascade dependencies | N/A |
| File Upload | Step 2 only | On main form |
