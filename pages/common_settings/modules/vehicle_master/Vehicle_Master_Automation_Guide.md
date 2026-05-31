# Vehicle Master — Screen Knowledge Document

> **RhythmERP** | Common Settings > Vehicle Master  
> **Last Verified**: 13-May-2026 | **43/43 Tests Passing**

---

## 1. Screen Overview

**Vehicle Master** is a master data screen in RhythmERP under **Common Settings**. It manages vehicle records — each vehicle has a Name, Price, Vehicle Type, Fuel Type, and optional Description.

| Detail | Value |
|--------|-------|
| **Navigation** | Sidebar → Common Settings → Vehicle Master |
| **URL** | `https://rhythmerp.algorhythms.in/#/dynamic-screens/Vehicle%20Master` |
| **Framework** | Angular Material (mat-select, cdk-overlay, mat-dialog, mat-table) |
| **Alerts** | SweetAlert2 (swal2-title, swal2-confirm) |
| **Validation** | Only 4 required fields — many gaps (see Section 8) |
| **Known Bugs** | 13 (1 Critical, 5 High, 3 Medium, 4 Low) |

### What You Can Do on This Screen

- **Create** a new vehicle via ADD button → popup form → Submit
- **Edit** an existing vehicle via row Edit button → popup form → Update
- **View** a vehicle's details (read-only) via row View button
- **Search** vehicles by name via toolbar search bar
- **Filter** vehicles by category via Filter panel (BROKEN — Apply Filters does nothing)
- **Check History** of changes via row History button → history popup

---

## 2. Screen Layout

### Toolbar (Top Bar)

```
┌──────────────────────────────────────────────────────────────────┐
│  [🔍 Search]  [+ ADD]  [≛ Filter]  [↻ Refresh]  [⋮ More]      │
└──────────────────────────────────────────────────────────────────┘
```

| Button | Icon | Selector | What It Does |
|--------|------|----------|-------------|
| **Search** | search icon | `button.search-btn` | Toggles search input bar. Click again to hide. |
| **ADD** | + (plus) icon | `div[mattooltip='ADD'] button` | Opens Create form popup. **Tooltip is on parent div, not button.** |
| **Filter** | filter_list icon | `button.filter-btn` | Opens right-side filter panel. **BROKEN — Apply Filters non-functional.** |
| **Refresh** | refresh icon | Find by mat-icon text "refresh" | Refreshes table data. |
| **More** | ⋮ (vertical dots) | `button[mattooltip='More']` | Opens menu (Export to Excel, etc.) |

### Search Bar (Hidden by Default)

After clicking the Search toggle, an input bar appears:

| Element | Selector | Notes |
|---------|----------|-------|
| Search Input | `input#erpSearchInput` | Stable ID. Hidden by default. |
| Search Behavior | Type text → press Enter | Filters table by Name. Partial match supported. |

### Table

```
┌──────┬──────┬─────────┬──────────┬───────────────┬─────────────┐
│ View │ Edit │ History │   Name   │ Vehicle Price │ Description │
│  👁  │  ✏️  │   🕐    │          │               │             │
├──────┼──────┼─────────┼──────────┼───────────────┼─────────────┤
│  btn │  btn │   btn   │  Ramesh  │    550000     │  Test data  │
│  btn │  btn │   btn   │  Tractor │    abcDEF     │             │
└──────┴──────┴─────────┴──────────┴───────────────┴─────────────┘
```

| Column | CSS Class | Sortable? | Notes |
|--------|-----------|-----------|-------|
| View | `mat-column-view` | No | Action button column |
| Edit | `mat-column-edit` | No | Action button column. Has `mattooltip="Click to edit"` |
| **History** | **`mat-column-archive`** | No | **CRITICAL: CSS class is "archive" NOT "history"!** |
| Name | `mat-column-name` | Yes | Sort header present |
| Vehicle Price | `mat-column-vehicle_price` | Yes | Underscore in class name. May contain non-numeric values (bugs). |
| Description | `mat-column-description` | Yes | May be empty |

### Table Selectors

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| All rows | `table#excel-table tbody tr` |
| Name cells | `td.cdk-column-name` or `td.mat-column-name` |
| Price cells | `td.cdk-column-vehicle_price` or `td.mat-column-vehicle_price` |
| No data message | `td.no-data` or `tr.mat-mdc-no-data-row` |

### Row Action Buttons (Per Row)

| Action | Position | Selector | Fallback |
|--------|----------|----------|----------|
| **View** | 1st button (index 0) | `td.mat-column-view button` | Click row button[0] |
| **Edit** | 2nd button (index 1) | `td.mat-column-edit button[mattooltip='Click to edit']` | Click row button[1] |
| **History** | 3rd button (index 2) | `td.mat-column-archive button` | Click row button[2] |

---

## 3. Add / Edit / View Form

All three modes use the **same popup container** — only the field states and footer buttons differ.

### Popup Structure

```
┌─────────────────────────────────────────────┐
│  Vehicle Master          [⛶] [✕]           │  ← Header (.popup-header)
├─────────────────────────────────────────────┤
│                                             │
│  Name *            [________________]       │
│  Vehicle Price *   [________________]       │
│  Vehicle Type *    [▼ Select...     ]       │  ← mat-select dropdown
│  Fuel Type *       [▼ Select...     ]       │  ← mat-select dropdown
│  Description       [________________]       │
│                                             │
├─────────────────────────────────────────────┤
│              [Cancel]  [Submit/Update]       │  ← Footer (.popup-footer)
└─────────────────────────────────────────────┘
```

### Field Catalog (5 Fields)

| Field | Type | Required | Selector | Behavior |
|-------|------|----------|----------|----------|
| **Name** | text input | YES | `input[name='Name']` | `type="character"`. No max length. No trimming. Accepts special chars. |
| **Vehicle Price** | text input | YES | `input[name='Vehicle Price']` | `type="character"` (NOT number!). No numeric validation at all. |
| **Vehicle Type** | mat-select dropdown | YES | `//mat-label[contains(.,'Vehicle Type')]/ancestor::mat-form-field//mat-select` | Searchable dropdown. Dynamic options — never hardcode. |
| **Fuel Type** | mat-select dropdown | YES | `//mat-label[contains(.,'Fuel Type')]/ancestor::mat-form-field//mat-select` | Searchable dropdown. Dynamic options — never hardcode. |
| **Description** | text input | NO | `input[name='Description']` | Optional. Can be left empty. |

### Field State Comparison

| Field | Add Mode | Edit Mode | View Mode |
|-------|----------|-----------|-----------|
| Name | Enabled, Empty | Enabled, Pre-filled | **Disabled**, Pre-filled |
| Vehicle Price | Enabled, Empty | Enabled, Pre-filled | **Disabled**, Pre-filled |
| Vehicle Type | Enabled, Empty | Enabled, Pre-selected | **Disabled**, Pre-selected |
| Fuel Type | Enabled, Empty | Enabled, Pre-selected | **Disabled**, Pre-selected |
| Description | Enabled, Empty | Enabled, Pre-filled/Empty | **Disabled**, Pre-filled/Empty |
| **Submit button** | **Present** | — | **ABSENT** |
| **Update button** | — | **Present** | **ABSENT** |
| **Cancel button** | Present | Present | Present (only button) |

### Popup Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Popup container | `.big-model` or `.edit_pop_up.popup-mode` | _is_form_popup_open() checks this |
| Popup header | `.popup-header` | Contains title + X button |
| Popup title | `.big-model h3` | Text: "Vehicle Master" |
| Close (X) button | `.popup-header button mat-icon` (text="close") | Found by icon text, not CSS class |
| Popup footer | `div[contains(@class,'popup-footer')]` | **Use contains() — Angular adds extra classes!** |
| Submit (Add) | `//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]` | JS click required |
| Update (Edit) | `//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]` | JS click required |
| Cancel | `//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]` | JS click required |

### How to Detect Current Mode

```
Add Mode:    Submit button visible + Update button absent + fields enabled
Edit Mode:   Update button visible + Submit button absent + fields enabled + pre-filled
View Mode:   No Submit/Update button + all fields disabled + Cancel only
```

---

## 4. Dropdowns

Both Vehicle Type and Fuel Type are **Angular Material mat-select** dropdowns with **built-in search**.

### How They Work

1. Click the mat-select trigger → CDK overlay panel opens
2. A search input appears at the top of the dropdown
3. Type to filter options in real-time
4. Click an option to select it → dropdown closes
5. Selected value appears in the form field

### Dropdown Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Dropdown panel | `div.mat-mdc-select-panel` | The active dropdown list |
| Options | `div.mat-mdc-select-panel mat-option` | Read dynamically — never hardcode option text |
| Search input (inside dropdown) | `div[role='listbox'] input` | Placeholder: "Search..." |
| No results | `mat-option[disabled]` | Text: "No results found" when search has no match |
| Overlay backdrop | `.cdk-overlay-backdrop` | Click this to close dropdown without selecting |

### Key Rules for Automation

| Rule | Why |
|------|-----|
| **Never hardcode option text** | Options vary by tenant/configuration. Always read from live UI. |
| **Wait for visibility, not presence** | `visibility_of_element_located` not `presence_of_element_located` — stale hidden options from previous dropdowns cause false positives. |
| **Close leftover panels first** | Call `_close_select_panel()` before opening a new dropdown — CDK overlay panels can stack. |
| **Force close after selection** | Call `_force_close_panels()` after selecting — removes lingering overlay elements. |
| **Use JS click for options** | Normal Selenium clicks can be intercepted by overlay backdrop. |

---

## 5. History Popup

### How to Open

Click the **History** button (3rd action button per row, clock icon) in the table. The popup opens as an overlay.

### Popup Structure

```
┌─────────────────────────────────────────────────────┐
│  Vehicle Master History              [⛶] [✕]       │  ← .popup-header
├─────────────────────────────────────────────────────┤
│  [🔍 Search in table]  [↻] [⋮]                     │  ← Toolbar
├──────┬──────────────┬──────────────┬─────┬──────────┤
│ View │ Creation Time│ Updated Time │ Name│ Price... │  ← Table
│  👁  │ 11 May 2026  │ 11 May 2026  │ ... │  ...     │
└──────┴──────────────┴──────────────┴─────┴──────────┘
│                        [Cancel]                      │  ← .popup-footer
└─────────────────────────────────────────────────────┘
```

### History Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| History popup | `h3.popup-title` (text contains "history") | `is_history_popup_open()` checks this |
| History title | `h3.popup-title` | Text: "Vehicle Master History" |
| History search input | `.big-model input` (visible one) | **MUST press Enter — no auto-filter!** |
| History table | `.big-model table tbody tr` | May be empty — "No data available" |
| History table headers | `.big-model table th` | 6 columns when data exists |
| Cancel button | `.popup-footer button` (text="Cancel") | Close button text is "Cancel", NOT "Close" |
| X icon | `.popup-header button mat-icon` (text="close") | Same as form popup X icon |

### Stacked View (View Inside History)

- Clicking **View** on a history row opens a **stacked View popup** on top of History
- View popup has z-index 1001, History has z-index 1000
- Cancel on View closes ONLY the View popup — History remains open below

### Important Findings

| Finding | Impact |
|---------|--------|
| **RhythmERP does NOT create history entries** on vehicle creation or edit | History popup shows "No data available" — 0 rows. Tests check popup opens, not row count. |
| **History sort doesn't reorder rows** | Clicking column headers toggles sort indicators but data stays in same order. (Bug #10) |
| **History search requires Enter key** | Typing alone does NOT filter. Must press Keys.RETURN after typing. |
| **History column CSS = "archive"** | The History action column uses class `mat-column-archive`, NOT `mat-column-history` or `cdk-column-history`. |

---

## 6. SweetAlert2 Messages

RhythmERP uses **SweetAlert2** for all validation and success feedback.

### Validation Failed (Warning Modal)

Appears when you Submit/Update with invalid or missing required fields.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-container` | Centered modal, z-index 1060 |
| Warning icon | `.swal2-icon.swal2-warning` | Yellow triangle |
| Title | `#swal2-title` | "Validation Failed" |
| Content | `.swal2-html-container` | "Please correct the highlighted fields" |
| OK button | `.swal2-confirm` | Text: "OK". Click to dismiss. |

**Triggers**: Empty Name, empty Price, no Vehicle Type, no Fuel Type on Submit/Update.

### Success — Record Added (Toast)

Appears after successful vehicle creation.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-container` | Top-right toast |
| Success icon | `.swal2-icon.swal2-success` | Green checkmark |
| Title | `#swal2-title` | "Your record has been added successfully!" |
| OK button | `.swal2-confirm` | Auto-dismisses after ~3 seconds if not clicked |

### Success — Record Updated (Toast)

Appears after successful vehicle edit.

| Element | Selector | Content |
|---------|----------|---------|
| Title | `#swal2-title` | "Your record has been updated successfully!" |

### Key Notes for Automation

- **No per-field inline error messages** — there are no `mat-error` elements under individual fields. Only the generic SweetAlert2 popup. (Bug #12)
- **Success toast auto-dismisses** after ~3 seconds. Automation must either click the confirm button quickly or wait for the container to disappear.
- **Leftover swal2-container elements** can block subsequent actions — must be JS-removed after handling.
- **Confirm button needs JS click** — direct Selenium click often fails due to z-index layering.

---

## 7. All Selectors (Verified)

### Login Page

| Element | Selector |
|---------|----------|
| Email Input | `input[formcontrolname="email"]` |
| Password Input | `input[formcontrolname="password"]` |
| Tenant Dropdown | `mat-select` |
| Tenant Search | `.cdk-overlay-container .search-container input` |
| Tenant Option | `.cdk-overlay-container mat-option` |
| Login Button | `button[type="submit"][color="primary"]` — **REQUIRES JS CLICK** |

### Toolbar

| Element | Selector |
|---------|----------|
| Search Toggle | `button.search-btn` |
| ADD Button | `div[mattooltip='ADD'] button` |
| Filter Button | `button.filter-btn` |
| Refresh Button | Find mini-fab button where mat-icon text = "refresh" |
| Search Input | `input#erpSearchInput` |

### Table

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| Table Rows | `table#excel-table tbody tr` |
| Name Cell | `td.cdk-column-name` or `td.mat-column-name` |
| Price Cell | `td.cdk-column-vehicle_price` or `td.mat-column-vehicle_price` |
| Description Cell | `td.cdk-column-description` or `td.mat-column-description` |
| View Button | `td.mat-column-view button` |
| Edit Button | `td.mat-column-edit button` |
| **History Button** | **`td.mat-column-archive button`** (NOT `cdk-column-history`!) |
| No Data Row | `td.no-data` or `tr.mat-mdc-no-data-row` |

### Form Popup

| Element | Selector |
|---------|----------|
| Popup Open Check | `div.big-model` (is_displayed) |
| Popup Title | `.big-model h3` |
| Name Input | `input[name='Name']` |
| Vehicle Price Input | `input[name='Vehicle Price']` |
| Vehicle Type Select | `//mat-label[contains(.,'Vehicle Type')]/ancestor::mat-form-field//mat-select` |
| Fuel Type Select | `//mat-label[contains(.,'Fuel Type')]/ancestor::mat-form-field//mat-select` |
| Description Input | `input[name='Description']` |
| Submit Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]` |
| Update Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]` |
| Cancel Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]` |
| X Close Icon | `.popup-header button mat-icon` where text = "close" |

### History Popup

| Element | Selector |
|---------|----------|
| History Open Check | `h3.popup-title` where text contains "history" |
| History Title | `h3.popup-title` — text: "Vehicle Master History" |
| History Table Rows | `.big-model table tbody tr` |
| History Search Input | `.big-model input` (visible input inside popup) |
| History Cancel | `.popup-footer button` text = "Cancel" |
| History X Icon | `.popup-header button mat-icon` text = "close" |

### SweetAlert2

| Element | Selector |
|---------|----------|
| Title | `#swal2-title` |
| Confirm Button | `.swal2-confirm` |
| Container | `.swal2-container` |
| Warning Icon | `.swal2-icon.swal2-warning` |
| Success Icon | `.swal2-icon.swal2-success` |

### Dropdown Options

| Element | Selector |
|---------|----------|
| Options Panel | `div.mat-mdc-select-panel` |
| Option Elements | `div.mat-mdc-select-panel mat-option` |
| Dropdown Search | `div[role='listbox'] input` |
| No Results | `mat-option[disabled]` |
| Overlay Backdrop | `.cdk-overlay-backdrop` |

---

## 8. Validation Matrix

### What IS Validated

| # | Validation | Trigger | What Happens |
|---|-----------|---------|-------------|
| 1 | Name required | Submit/Update with empty Name | SweetAlert2: "Validation Failed — Please correct the highlighted fields". Form stays open. |
| 2 | Vehicle Price required | Submit/Update with empty Price | Same as above. |
| 3 | Vehicle Type required | Submit/Update with no Vehicle Type | Same as above. |
| 4 | Fuel Type required | Submit/Update with no Fuel Type | Same as above. |
| 5 | Description optional | Submit with empty Description | No error. Record created. |

### What is NOT Validated (Gaps = Bugs)

| # | Missing Validation | What Should Happen | What Actually Happens | Severity |
|---|-------------------|--------------------|-----------------------|----------|
| 1 | Price numeric check | Reject alphabets | Accepts "abc", "xyz123" | **HIGH** |
| 2 | Price positive check | Reject negative values | Accepts -5000, -100 | **HIGH** |
| 3 | Price minimum value | Reject zero | Accepts 0 | **MEDIUM** |
| 4 | Price special chars | Reject !@#$ etc. | Accepts special characters | **HIGH** |
| 5 | Name unique constraint | Block duplicate names | Allows duplicates in both Create & Edit | **HIGH** |
| 6 | Name max length | Restrict at 255 chars | Accepts 256+ chars | **LOW** |
| 7 | Name input sanitization | Restrict special chars | Accepts "!@#$%^&*()" | **LOW-MEDIUM** |
| 8 | Name whitespace trimming | Trim leading/trailing spaces | Stores "  Name  " with spaces | **MEDIUM** |
| 9 | Per-field inline errors | Show error below each field | Only generic SweetAlert2 popup | **LOW-MEDIUM** |
| 10 | History sort | Reorder rows on click | Sort icon toggles but rows don't move | **MEDIUM** |

---

## 9. Bug Registry (13 Bugs)

### Critical (1)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#7** | Apply Filters completely non-functional | 1. Click Filter button. 2. Select any filter category (Name, Price, etc.). 3. Click "Apply Filters". | Table filters to matching rows. | Nothing happens. No request sent. Zero effect. |

### High (5)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#1** | Duplicate Name allowed (Create) | 1. Create vehicle with Name "Ramesh". 2. Create another vehicle with same Name "Ramesh". | Error: "Name already exists". | Second vehicle created. No warning. |
| **#2** | Duplicate Name allowed (Edit) | 1. Edit a vehicle. 2. Change its Name to another existing vehicle's Name. | Error: "Name already exists". | Edit succeeds. Two vehicles with same Name. |
| **#3** | Negative Price accepted (Create) | 1. Create vehicle. 2. Enter Price "-5000". 3. Submit. | Error: "Price must be positive". | Vehicle created with Price = -5000. |
| **#4** | Negative Price accepted (Edit) | 1. Edit vehicle. 2. Change Price to "-100". 3. Update. | Error: "Price must be positive". | Price updated to -100. |
| **#5** | Alphabets accepted in Price | 1. Create/Edit vehicle. 2. Enter Price "abcDEF". 3. Submit/Update. | Error: "Price must be numeric". | Price saved as "abcDEF". |
| **#6** | Special chars accepted in Price | 1. Create/Edit vehicle. 2. Enter Price "!@#$". 3. Submit/Update. | Error: "Invalid characters". | Price saved as "!@#$". |

### Medium (3)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#8** | Zero Price accepted | 1. Create/Edit vehicle. 2. Enter Price "0". 3. Submit/Update. | Error: "Price must be greater than 0". | Price = 0 saved. |
| **#9** | Spaces not trimmed in Name | 1. Create vehicle. 2. Enter Name "  SpaceTest  ". 3. Submit. | Name trimmed to "SpaceTest". | Name stored as "  SpaceTest  " with spaces. |
| **#10** | History column sort doesn't work | 1. Open History popup. 2. Click "Creation Time" column header. | Rows reorder by sort direction. | Sort icon toggles. Rows stay in same order. |

### Low (4)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#11** | Special chars accepted in Name | 1. Create vehicle. 2. Enter Name "Test!@#$%^&*()". 3. Submit. | Reject or sanitize. | Name stored as-is. |
| **#12** | No per-field inline error messages | 1. Click Add. 2. Leave all empty. 3. Click Submit. | Each invalid field shows "X is required" below it. | Only generic SweetAlert2 popup. No field-level feedback. |
| **#13** | No Name max length | 1. Create vehicle. 2. Enter Name with 256+ characters. 3. Submit. | Error: "Name too long" or truncate. | Name accepted without limit. |
| **#14** | No history entries created | 1. Create a vehicle. 2. Open History. | At least 1 history row (creation event). | 0 rows. "No data available". |

---

## 10. How to Run the Tests

### Prerequisites

```bash
pip install selenium pytest pytest-html openpyxl python-dotenv
```

Make sure **ChromeDriver** matches your Chrome version.

### Run All 43 Tests

```bash
pytest pages/common_settings/modules/vehicle_master/test/test_vehicle_master_validation.py -v --tb=short
```

**Expected output**: `43 passed in ~2038s (0:33:58)`

### Run by Phase

| Phase | Command | Tests |
|-------|---------|-------|
| Create Validations | `pytest ... -v -k "TestCreateForm" --tb=short` | C01–C15 |
| Dropdown Validations | `pytest ... -v -k "VM_D" --tb=short` | D01–D05 |
| Edit Validations | `pytest ... -v -k "TestEditForm" --tb=short` | E01–E05 |
| Search & Filter | `pytest ... -v -k "TestSearchFilter" --tb=short` | S01–S05 |
| Popup & UI | `pytest ... -v -k "TestPopupUI" --tb=short` | P01–P05 |
| History | `pytest ... -v -k "TestHistory" --tb=short` | H01–H08 |

*(Replace `...` with the full path shown above)*

### Run a Single Test

```bash
pytest pages/common_settings/modules/vehicle_master/test/test_vehicle_master_validation.py -v -k "VM_C09" --tb=short
```

### Command Flags

| Flag | What It Does |
|------|-------------|
| `-v` | Verbose — shows each test name and result |
| `-k "PATTERN"` | Run only tests matching the pattern (substring match on test name) |
| `--tb=short` | Short traceback on failure (less output) |
| `--tb=long` | Full traceback on failure (for debugging) |
| `--tb=no` | No traceback at all (just show pass/fail) |

### Report Location

After every run, an Excel report is auto-generated:

```
pages/common_settings/modules/vehicle_master/reports/CommonSettings_Report_YYYYMMDD_HHMMSS.xlsx
```

The report includes: test names, pass/fail status, step-by-step logs, error messages, and the 10 known issues list.

### Credentials Used

| Parameter | Value | Source |
|-----------|-------|--------|
| URL | `https://rhythmerp.algorhythms.in` | config.py |
| Login URL | `.../#/authentication/signin` | config.py |
| Email | `test@gmail.com` | config.py |
| Password | `Test@2526270` | config.py |
| Facility | First option (index 0) | config.py |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│              VEHICLE MASTER — QUICK REFERENCE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SCREEN:  Common Settings > Vehicle Master                      │
│  URL:     .../#/dynamic-screens/Vehicle%20Master                │
│  APP:     Angular Material + SweetAlert2                        │
│                                                                 │
│  FORM FIELDS:                                                   │
│    Name* (text) | Vehicle Price* (text!) | Vehicle Type* (dd)   │
│    Fuel Type* (dd) | Description (text, optional)               │
│                                                                 │
│  TABLE COLUMNS:                                                 │
│    View | Edit | History(archive!) | Name | Price | Description │
│                                                                 │
│  13 BUGS:  1 Critical | 5 High | 3 Medium | 4 Low              │
│  WORST:    Apply Filters does NOTHING (Critical)                │
│            Duplicate Name allowed (High x2)                     │
│            No numeric validation on Price (High x3)             │
│                                                                 │
│  KEY GOTCHAS:                                                   │
│    ✗ NEVER use Keys.ESCAPE                                      │
│    ✗ NEVER hardcode dropdown options                            │
│    ✗ History column CSS = "archive" not "history"               │
│    ✓ ALWAYS use JS clicks for Angular Material                  │
│    ✓ ALWAYS driver.refresh() after navigate                     │
│    ✓ ALWAYS search before Edit/History                          │
│    ✓ ALWAYS _force_close_panels() between dropdowns             │
│    ✓ ALWAYS use contains(@class,'popup-footer') not exact       │
│    ✓ History search REQUIRES Enter key                          │
│                                                                 │
│  RUN ALL:  pytest ... -v --tb=short                             │
│  RUN ONE:  pytest ... -v -k "VM_C09" --tb=short                │
│  REPORT:   .../reports/CommonSettings_Report_*.xlsx             │
└─────────────────────────────────────────────────────────────────┘
```

---

*Last Updated: 13-May-2026 | Vehicle Master Screen Knowledge Document | 43/43 Tests Passing*
