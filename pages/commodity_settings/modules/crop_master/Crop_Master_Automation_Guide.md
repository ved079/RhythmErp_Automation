# Crop Master — Automation Guide

> **RhythmERP** | Commodity Settings → Crop Master  
> **URL:** `https://rhythmerp.algorhythms.in/#/dynamic-screens/Crop%20Master`  
> **Last Updated:** 2026-05-15  
> **Test Results:** 34 PASSED, 10 XFAIL, 0 FAILED | Effective Pass Rate: 100%

---

## Quick Reference

| Item | Value |
|------|-------|
| Total Test Cases | 44 |
| Execution Time | ~24 min |
| Test ID Prefix | CM- |
| Page Object | `CropMasterPage` |
| Form Fields | Name (required), Description, File Upload, Status Toggle |
| Dropdowns | **NONE** — text inputs only |
| Validation Library | SweetAlert2 |
| App Framework | Angular Material |

---

## Project Structure

```
pages/commodity_settings/modules/crop_master/
├── __init__.py                          # exports CropMasterPage
├── crop_master_page.py                  # Page Object (1003+ lines)
├── cm_report_generator.py               # Excel report generator (294 lines)
├── data/
│   ├── __init__.py                      # exports generators + BUG IDs
│   └── crop_master_data.py              # Test data generators
└── test/
    ├── __init__.py
    ├── conftest.py                      # Fixtures, login, report gen
    └── test_crop_master_validation.py   # 44 test cases (846+ lines)
```

---

## Run Commands

```powershell
# Run all 44 tests
python -m pytest pages/commodity_settings/modules/crop_master/test/test_crop_master_validation.py -v

# Run specific class
python -m pytest pages/commodity_settings/modules/crop_master/test/test_crop_master_validation.py -v -k "TestCreateFormValidations"
python -m pytest pages/commodity_settings/modules/crop_master/test/test_crop_master_validation.py -v -k "TestFileUpload"
python -m pytest pages/commodity_settings/modules/crop_master/test/test_crop_master_validation.py -v -k "TestEditFormValidations"
python -m pytest pages/commodity_settings/modules/crop_master/test/test_crop_master_validation.py -v -k "TestSearchFilter"
python -m pytest pages/commodity_settings/modules/crop_master/test/test_crop_master_validation.py -v -k "TestPopupUIBehaviors"
python -m pytest pages/commodity_settings/modules/crop_master/test/test_crop_master_validation.py -v -k "TestHistoryValidations"

# Run single test
python -m pytest pages/commodity_settings/modules/crop_master/test/test_crop_master_validation.py -v -k "test_empty_form_submit"

# Run with HTML report
python -m pytest pages/commodity_settings/modules/crop_master/test/test_crop_master_validation.py -v --html=report.html
```

---

## Test Classes Breakdown

| Class | Count | Phase | Passed | XFAIL |
|-------|-------|-------|--------|-------|
| TestCreateFormValidations | 15 | Create | 8 | 7 |
| TestFileUpload | 5 | File Upload | 5 | 0 |
| TestEditFormValidations | 5 | Edit | 3 | 2 |
| TestSearchFilter | 5 | Search/Filter | 5 | 0 |
| TestPopupUIBehaviors | 6 | Popup/UI | 6 | 0 |
| TestHistoryValidations | 8 | History | 7 | 1 |
| **Total** | **44** | — | **34** | **10** |

---

## Key Selectors

### Toolbar

| Element | Selector | Notes |
|---------|----------|-------|
| Add Button | `div[mattooltip="ADD"] button` | Tooltip on parent DIV. JS click required. |
| Search Toggle | `button.search-btn` | Toggles search input |
| Filter Button | `div[mattooltip="Filters"] button` | Opens right-side filter panel |
| Refresh Button | `div[mattooltip="REFRESH"] button` | Refreshes table data |
| Search Input | `#erpSearchInput` | Hidden by default, toggle via search button |

### Form Popup

| Element | Selector | Notes |
|---------|----------|-------|
| Name Input | `input[name="Name"]` | Capital N! Required field |
| Description Input | `input[name="Description"]` | Optional |
| File Upload | `.edit_pop_up input[type="file"]` | Accepts .png, .jpg, .pdf |
| Status Toggle | `.edit_pop_up .slider` | Click slider, NOT checkbox |
| Submit Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]` | Add mode only |
| Update Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]` | Edit mode only |
| Cancel Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]` | All modes |
| Close (X) | `.popup-header button mat-icon` (text='close') | Find by text content |

### Table

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| Name Cells | `td.cdk-column-name` |
| Status Cells | `td.cdk-column-status` |
| View Button | `td.cdk-column-view button` (index 0) |
| Edit Button | `td.cdk-column-edit button` (index 1) |
| History Button | `td.cdk-column-archive button` (index 2) — **NOT 'history'!** |

### History Popup

| Element | Selector | Notes |
|---------|----------|-------|
| Popup | `.popup-overlay` | **NOT .big-model!** |
| Search Input | `.popup-overlay input` | Must press Enter — no auto-filter |
| Table Rows | `.popup-overlay table tbody tr` | May be 0 rows (BUG-CM07) |

### SweetAlert2

| Type | Selector | Notes |
|------|----------|-------|
| Validation Warning | `.swal2-icon.swal2-warning` | Title: "Validation Failed" |
| Success | `.swal2-icon.swal2-success` | Title: "Your record has been added/updated successfully!" |
| Confirm Button | `.swal2-confirm` | 3-tier JS click strategy |

---

## Critical Technical Rules

### NEVER Use Keys.ESCAPE
Always close popups via Cancel, X button, or JS overlay removal. `Keys.ESCAPE` triggers Angular SPA navigation.

### Always JS Click for Angular Material
Normal Selenium clicks get intercepted by `cdk-overlay`. Use:
```python
driver.execute_script('arguments[0].click();', element)
```

### driver.refresh() After Navigate
`navigate_to_page()` calls `driver.refresh()` after navigation. Without it, stale overlays block the ADD button.

### Search Before Edit/History
After creating a crop, it may not be visible (pagination). Always call `search_crop()` before Edit or History.

### _force_close_panels() Between Actions
Remove leftover CDK overlay panels between form interactions to prevent stacked overlays.

### History Column = 'archive'
The History action column uses CSS class `cdk-column-archive` / `mat-column-archive`, NOT 'history'.

### popup-footer Class is Dynamic
Use `contains(@class,'popup-footer')` instead of exact match — Angular adds extra classes.

### Status Toggle — Click .slider
DO NOT click the checkbox directly. Click the `.slider` element. Read state via `input[type='checkbox'].is_selected()`.

---

## Action Flows

### Create Crop
```python
page.navigate_to_page()
page.open_add_form()
page.type_text(page.NAME_INPUT, "CropName", clear_first=True)
page.type_text(page.DESCRIPTION_INPUT, "Description", clear_first=True)
page.upload_file("/path/to/file.png")        # optional
page.set_status("Inactive")                   # optional, default Active
page._force_close_panels()
page.submit()
page.handle_success_alert(timeout=60)
```

### Edit Crop
```python
page.search_crop("CropName")
page.click_edit_button(crop_name="CropName")
page.type_text(page.NAME_INPUT, "NewName", clear_first=True)
page._force_close_panels()
page.click_update()
page.handle_success_alert(timeout=60)
```

### View Crop
```python
page.search_crop("CropName")
page.click_view_button(crop_name="CropName")
values = page.get_form_field_values()  # dict: name, description, status, has_file
page.close_popup()
```

### Check History
```python
page.search_crop("CropName")
page.click_history_button(crop_name="CropName")
count = page.get_history_row_count()
page.search_in_history("search term")  # must press Enter
page.close_history_popup()
```

---

## Test Data Generators

```python
from pages.commodity_settings.modules.crop_master.data import (
    generate_valid_crop_data,    # Full valid data dict
    generate_crop_name,          # Random name with timestamp
    generate_description,        # Random description
    generate_test_file,          # .png / .jpg / .pdf temp file
    generate_invalid_test_file,  # .txt file (invalid type)
)

# Bug IDs
from pages.commodity_settings.modules.crop_master.data import (
    BUG_CM01,  # Blank name accepted on Create
    BUG_CM02,  # Duplicate name allowed
    BUG_CM03,  # Spaces not trimmed
    BUG_CM04,  # No inline errors
    BUG_CM05,  # No max length validation
    BUG_CM06,  # Special chars accepted
    BUG_CM07,  # No history entry on creation
    BUG_CM08,  # Column sort broken
    BUG_CM09,  # Blank name accepted on Edit
)
```

---

## 44 Test Cases

### TestCreateFormValidations (15)

| # | Test ID | Name | Status | Bug |
|---|---------|------|--------|-----|
| 1 | CM-C01 | Empty form submit | PASS | |
| 2 | CM-C02 | Only Name filled | PASS | |
| 3 | CM-C03 | Blank name (spaces only) | XFAIL | BUG-CM01 |
| 4 | CM-C04 | Name with leading/trailing spaces | XFAIL | BUG-CM03 |
| 5 | CM-C05 | Duplicate Name - Create | XFAIL | BUG-CM02 |
| 6 | CM-C06 | Special chars in Name | XFAIL | BUG-CM06 |
| 7 | CM-C07 | Very long Name (300 chars) | XFAIL | BUG-CM05 |
| 8 | CM-C08 | No inline errors | XFAIL | BUG-CM04 |
| 9 | CM-C09 | Create Active status | PASS | |
| 10 | CM-C10 | Create Inactive status | PASS | |
| 11 | CM-C11 | Create with Description | PASS | |
| 12 | CM-C12 | Create without Description | PASS | |
| 13 | CM-C13 | Blank description (spaces) | PASS | |
| 14 | CM-C14 | Description with special chars | PASS | |
| 15 | CM-C15 | Create valid all fields | PASS | |

### TestFileUpload (5)

| # | Test ID | Name | Status | Bug |
|---|---------|------|--------|-----|
| 1 | CM-F01 | Upload PNG file | PASS | |
| 2 | CM-F02 | Upload JPG file | PASS | |
| 3 | CM-F03 | Upload PDF file | PASS | |
| 4 | CM-F04 | Upload invalid file type (.txt) | PASS | |
| 5 | CM-F05 | No file uploaded | PASS | |

### TestEditFormValidations (5)

| # | Test ID | Name | Status | Bug |
|---|---------|------|--------|-----|
| 1 | CM-E01 | Edit duplicate Name | XFAIL | BUG-CM02 |
| 2 | CM-E02 | Edit blank Name (spaces) | XFAIL | BUG-CM09 |
| 3 | CM-E03 | Edit pre-populated fields | PASS | |
| 4 | CM-E04 | Edit status Active → Inactive | PASS | |
| 5 | CM-E05 | Edit status Inactive → Active | PASS | |

### TestSearchFilter (5)

| # | Test ID | Name | Status | Bug |
|---|---------|------|--------|-----|
| 1 | CM-S01 | Search exact match | PASS | |
| 2 | CM-S02 | Search partial match | PASS | |
| 3 | CM-S03 | Search nonexistent | PASS | |
| 4 | CM-S04 | Filter by Status | PASS | |
| 5 | CM-S05 | Filter by Name category | PASS | |

### TestPopupUIBehaviors (6)

| # | Test ID | Name | Status | Bug |
|---|---------|------|--------|-----|
| 1 | CM-P01 | Cancel discards data | PASS | |
| 2 | CM-P02 | X close discards data | PASS | |
| 3 | CM-P03 | View shows read-only | PASS | |
| 4 | CM-P04 | Edit has Update button | PASS | |
| 5 | CM-P05 | History popup opens | PASS | |
| 6 | CM-P06 | Status toggle works | PASS | |

### TestHistoryValidations (8)

| # | Test ID | Name | Status | Bug |
|---|---------|------|--------|-----|
| 1 | CM-H01 | History after create | XFAIL | BUG-CM07 |
| 2 | CM-H02 | History after edit | PASS | |
| 3 | CM-H03 | History search Enter key | PASS | |
| 4 | CM-H04 | History search no match | PASS | |
| 5 | CM-H05 | History columns | PASS | |
| 6 | CM-H06 | History Close button | PASS | |
| 7 | CM-H07 | History X icon close | PASS | |
| 8 | CM-H08 | History column sort | XFAIL | BUG-CM08 |

---

## Bug Registry (9 Confirmed Bugs)

| Bug ID | Phase | Description | Severity |
|--------|-------|-------------|----------|
| BUG-CM01 | Create | Blank (spaces-only) Name accepted on Create | High |
| BUG-CM02 | Create/Edit | Duplicate Crop Name allowed | High |
| BUG-CM03 | Create | Leading/trailing spaces NOT trimmed | Medium |
| BUG-CM04 | Create/Edit | No per-field inline error messages | Low-Medium |
| BUG-CM05 | Create | No max length validation on Name | Low |
| BUG-CM06 | Create | Special characters accepted without sanitization | Low-Medium |
| BUG-CM07 | History | No history entries created on crop creation | Medium |
| BUG-CM08 | History | Column sort doesn't reorder rows | Medium |
| BUG-CM09 | Edit | Blank (spaces-only) Name accepted on Edit | High |

### Severity Distribution
- **High:** 4 bugs (BUG-CM01, CM02, CM09 — blank/duplicate name issues)
- **Medium:** 3 bugs (BUG-CM03, CM07, CM08 — trim, history, sort)
- **Low-Medium:** 2 bugs (BUG-CM04, CM06 — inline errors, special chars)
- **Low:** 1 bug (BUG-CM05 — max length)

---

## Key Method Reference

| Method | Purpose | Key Strategy |
|--------|---------|--------------|
| `navigate_to_page()` | Go to Crop Master | navigate + refresh + wait for page ready |
| `open_add_form()` | Click ADD button | 4 strategies, JS click, verify popup open |
| `fill_crop_form(data)` | Fill all fields | type_text for inputs, send_keys for file, .slider for status |
| `submit()` | Click Submit | 3-tier JS click |
| `click_update()` | Click Update | Same 3-tier JS click |
| `search_crop(name)` | Search in table | JS value injection + input event + Enter. 5 retries |
| `create_crop(data)` | One-call create | open_add → fill → submit → alert → cleanup |
| `edit_crop(name, data)` | One-call edit | search → click_edit → fill → update → alert |
| `check_history(name)` | One-call history | search → click_history → read rows → close |
| `toggle_status()` | Toggle switch | JS click .slider (NOT checkbox) |
| `get_current_status()` | Read status | checkbox.is_selected() → 'Active'/'Inactive' |
| `handle_success_alert()` | Handle SweetAlert2 success | Wait title → 3-tier confirm click → wait invisible |
| `handle_validation_warning()` | Handle SweetAlert2 warning | Wait title → JS click confirm → wait invisible |
| `close_history_popup()` | Close History | 3 JS strategies: Cancel → X icon → force remove |
| `_force_close_panels()` | Remove CDK overlays | JS removes stale cdk-overlay-backdrop + pane |
| `_cleanup_swal2()` | Remove SweetAlert2 remnants | JS removes .swal2-container + backdrop |

---

## Fixture Architecture

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `driver` | session | Single browser instance for all 44 tests |
| `logged_in_driver` | session | Login once, session maintained across all tests |
| `crop_master_page` | function | Fresh `navigate_to_page()` per test with `driver.refresh()` |
| `_cm_report_generator` | session (autouse) | Starts timer, registers 9 known issues, generates Excel report |

---

## Differences from Other Modules

| Feature | Crop Master | Vehicle Master |
|---------|-------------|----------------|
| Section | Commodity Settings | Common Settings |
| Dropdowns | **NONE** | 2 (Type, Category) |
| History Container | `.popup-overlay` | `.big-model` |
| History Column CSS | `cdk-column-archive` | `cdk-column-archive` |
| Form Complexity | 4 fields (Name, Desc, File, Status) | More fields with dropdowns |
| Search Method | JS value injection + event dispatch | Similar pattern |
