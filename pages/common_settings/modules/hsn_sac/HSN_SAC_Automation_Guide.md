Here's your **HSN SAC Screen Knowledge Document** — same format as Vehicle Master:

---

```markdown
# HSN SAC — Screen Knowledge Document

> **RhythmERP** | Common Settings > HSN SAC  
> **Last Verified**: 14-May-2026 | **20/20 Tests Passing**

---

## 1. Screen Overview

**HSN SAC** is a master data screen in RhythmERP under **Common Settings**. It manages HSN (Harmonized System of Nomenclature) and SAC (Services Accounting Code) records — each record has an HSN SAC Number, HSN SAC Type (dropdown with 4 fixed options), and a Description.

| Detail | Value |
|--------|-------|
| **Navigation** | Sidebar → Common Settings → HSN SAC |
| **URL** | `https://rhythmerp.algorhythms.in/#/dynamic-screens/HSN%20SAC` |
| **Framework** | Angular Material (mat-select, cdk-overlay, mat-dialog, mat-table) |
| **Alerts** | SweetAlert2 (swal2-title, swal2-confirm) |
| **Validation** | All 3 fields are required — no validation gaps |
| **Known Bugs** | 0 (clean module) |

### What You Can Do on This Screen

- **Create** a new HSN SAC via ADD button → popup form → Submit
- **Edit** an existing HSN SAC via row Edit button → popup form → Update
- **View** an HSN SAC's details (read-only) via row View button
- **Search** HSN SAC records by number via toolbar search bar
- **Check History** of changes via row History button → history popup

---

## 2. Screen Layout

### Toolbar (Top Bar)

```
┌──────────────────────────────────────────────────────────────────┐
│  [🔍 Search]  [+ ADD]  [ chopping Filter]  [↻ Refresh]  [⋮ More]│
└──────────────────────────────────────────────────────────────────┘
```

| Button | Icon | Selector | What It Does |
|--------|------|----------|-------------|
| **Search** | search icon | `button.search-btn` | Toggles search input bar. Click again to hide. |
| **ADD** | + (plus) icon | `//*[@mattooltip='ADD']/button` | Opens Create form popup. **Tooltip is on parent div, not button.** |
| **Filter** | filter_list icon | `//*[@mattooltip='Filters']/button` | Opens right-side filter panel. |
| **Refresh** | refresh icon | `//*[@mattooltip='REFRESH']/button` | Refreshes table data. |
| **More** | ⋮ (vertical dots) | `//button[@mattooltip='More']` | Opens menu (Export to Excel, etc.) |

### Search Bar (Hidden by Default)

After clicking the Search toggle, an input bar appears:

| Element | Selector | Notes |
|---------|----------|-------|
| Search Input | `input#erpSearchInput` | Stable ID. Hidden by default. |
| Search Behavior | Type text → press Enter | Filters table by HSN SAC Number. Partial match supported. |

### Table

```
┌──────┬──────┬─────────┬───────────────┬──────────────┐
│ View │ Edit │ History │ HSN SAC Number│ HSN SAC Type │
│  👁  │  ✏️  │   🕐    │               │              │
├──────┼──────┼─────────┼───────────────┼──────────────┤
│  btn │  btn │   btn   │   998300      │   Services   │
│  btn │  btn │   btn   │   445212      │   Commodity  │
└──────┴──────┴─────────┴───────────────┴──────────────┘
```

| Column | CSS Class | Sortable? | Notes |
|--------|-----------|-----------|-------|
| View | `mat-column-view` | No | Action button column |
| Edit | `mat-column-edit` | No | Action button column. Has `mattooltip="Click to edit"` |
| **History** | **`mat-column-archive`** | No | **CRITICAL: CSS class is "archive" NOT "history"!** |
| HSN SAC Number | `mat-column-hsn_sac_no` | Yes | 4th column (index 3 in td) |
| HSN SAC Type | `mat-column-hsn_sac_type` | Yes | 5th column (index 4 in td) |

### Table Selectors

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| All rows | `table#excel-table tbody tr` |
| HSN SAC Number cells | `td.mat-column-hsn_sac_no` |
| HSN SAC Type cells | `td.mat-column-hsn_sac_type` |

### Row Action Buttons (Per Row)

| Action | Position | Selector | Fallback |
|--------|----------|----------|----------|
| **View** | 1st button (index 0) | `td.mat-column-view button` | Click row button[0] |
| **Edit** | 2nd button (index 1) | `td.mat-column-edit button` | Click row button[1] |
| **History** | 3rd button (index 2) | `td.mat-column-archive button` | Click row button[2] |

---

## 3. Add / Edit / View Form

All three modes use the **same popup container** — only the field states and footer buttons differ.

### Popup Structure

```
┌─────────────────────────────────────────────┐
│  HSN SAC                     [⛶] [✕]       │  ← Header (.popup-header)
├─────────────────────────────────────────────┤
│                                             │
│  HSN SAC Number *  [________________]       │
│  HSN SAC Type *     [▼ Select...     ]      │  ← mat-select dropdown (4 fixed options)
│  HSN SAC Desc *     [________________]       │
│                                             │
├─────────────────────────────────────────────┤
│              [Cancel]  [Submit/Update]       │  ← Footer (.popup-footer)
└─────────────────────────────────────────────┘
```

### Field Catalog (3 Fields — ALL REQUIRED)

| Field | Type | Required | Selector | Behavior |
|-------|------|----------|----------|----------|
| **HSN SAC Number** | text input | YES | `input[name='HSN SAC Number']` | `type="character"`. Editable in both Add and Edit mode. |
| **HSN SAC Type** | mat-select dropdown | YES | `//mat-label[contains(.,'HSN SAC Type')]/ancestor::mat-form-field//mat-select` | **FIXED 4 options**: Services, Transportation, Commission, Commodity. Wrapped in `app-dropdown-v2`. |
| **HSN SAC Description** | text input | YES | `input[name='HSN SAC Description']` | `type="character"`. **REQUIRED** (unlike Vehicle Master Description which is optional). |

### Dropdown Fixed Options

The HSN SAC Type dropdown has exactly **4 static options** — they do NOT change per tenant or configuration.

| # | Option | Verified In Tests |
|---|--------|-------------------|
| 1 | Services | C01, E03 |
| 2 | Transportation | C04 |
| 3 | Commission | C02 |
| 4 | Commodity | C04, E03 |

### Field State Comparison

| Field | Add Mode | Edit Mode | View Mode |
|-------|----------|-----------|-----------|
| HSN SAC Number | Enabled, Empty | **Enabled**, Pre-filled | **Disabled**, Pre-filled |
| HSN SAC Type | Enabled, Empty | **Enabled**, Pre-selected | **Disabled**, Pre-selected |
| HSN SAC Description | Enabled, Empty | **Enabled**, Pre-filled/Empty | **Disabled**, Pre-filled/Empty |
| **Submit button** | **Present** | — | **ABSENT** |
| **Update button** | — | **Present** | **ABSENT** |
| **Cancel button** | Present | Present | Present (only button) |

> **Key Difference from Bank**: In Bank, the Bank Name field is **disabled in Edit mode**. In HSN SAC, **ALL fields are editable** in both Add and Edit mode.

### Popup Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Popup container | `.edit_pop_up.popup-mode` or `div.big-model` | `_is_form_popup_open()` checks this |
| Popup header | `.popup-header` | Contains title + X button |
| Popup title | `.big-model h3` | Text: "HSN SAC" |
| Close (X) button | `.popup-header button mat-icon` (text="close") | Found by icon text, not CSS class |
| Popup footer | `//div[contains(@class,'popup-footer')]` | **Use contains() — Angular adds extra classes!** |
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

HSN SAC Type is an **Angular Material mat-select** dropdown wrapped in `app-dropdown-v2`, with exactly **4 fixed options**. Unlike Vehicle Master, this dropdown does NOT have a built-in search input.

### How It Works

1. Click the mat-select trigger → CDK overlay panel opens
2. 4 options appear: Services, Transportation, Commission, Commodity
3. Click an option to select it → dropdown closes
4. Selected value appears in the form field

### Dropdown Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Dropdown trigger | `//mat-label[contains(.,'HSN SAC Type')]/ancestor::mat-form-field//mat-select` | Found by mat-label text |
| Options panel | `div.mat-mdc-select-panel` | The active dropdown list |
| Option elements | `div.mat-mdc-select-panel mat-option` or `[role='option']` | 4 fixed options |
| Overlay backdrop | `.cdk-overlay-backdrop` | Click to close dropdown without selecting |
| Leftover panels | `div.cdk-overlay-pane:not(.mat-mdc-dialog-container)` | Must be force-removed after selection |

### Key Rules for Automation

| Rule | Why |
|------|-----|
| **Options CAN be hardcoded** | Only 4 static options — never change. Safe to hardcode in data generators. |
| **Use JS click for trigger** | Normal Selenium clicks intercepted by `app-dropdown-v2` wrapper. |
| **Force close after selection** | Call `_force_close_panels()` after selecting — removes lingering overlay elements. |
| **Page refresh workaround available** | If dropdown doesn't open, `fill_all_fields()` retries: close form → refresh → reopen → refill. Max 3 attempts. |
| **Dropdown FIRST in fill order** | `_fill_all_fields_once()` fills Dropdown → Text fields (not the other way around). If refresh happens, text fields would be wiped. |

---

## 5. History Popup

### How to Open

Click the **History** button (3rd action button per row, clock icon) in the table. The popup opens as an overlay.

### Popup Structure

```
┌─────────────────────────────────────────────────────┐
│  HSN SAC History                      [⛶] [✕]       │  ← .popup-header
├─────────────────────────────────────────────────────┤
│  [🔍 Search in table]  [↻] [⋮]                     │  ← Toolbar
├─────────────────────────────────────────────────────┤
│                                                     │
│               No data available.                    │
│                                                     │
├─────────────────────────────────────────────────────┤
│                        [Cancel]                      │  ← .popup-footer
└─────────────────────────────────────────────────────┘
```

### History Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| History popup | `.popup-content` | z-index: 1000 |
| History title | `h3.popup-title` | Text: "HSN SAC History" |
| History search input | `.popup-body input[placeholder='Search in table']` | **MUST press Enter — no auto-filter!** |
| History table rows | `.popup-body table tbody tr` | May be empty — "No data available" |
| No data message | `//p[contains(text(),'No data available')]` | Shown when no history entries exist |
| Cancel button | `//div[contains(@class,'popup-content')]//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]` | JS click required |
| X icon | `.popup-content button mat-icon` (text="close") | Same as form popup X icon |

### Important Findings

| Finding | Impact |
|---------|--------|
| **RhythmERP does NOT create history entries** on HSN SAC creation or edit | History popup shows "No data available" — 0 rows. Tests verify popup opens, not row count. |
| **History search requires Enter key** | Typing alone does NOT filter. Must press Keys.RETURN after typing. |
| **History column CSS = "archive"** | The History action column uses class `mat-column-archive`, NOT `mat-column-history`. |

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

**Triggers**: Empty HSN SAC Number (C02), empty HSN SAC Type (C03), empty Description (C04), all empty (C05), empty field in Edit (E05).

### Success — Record Added (Toast)

Appears after successful HSN SAC creation.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-container` | Top-right toast |
| Success icon | `.swal2-icon.swal2-success` | Green checkmark |
| Title | `#swal2-title` | "Your record has been added successfully!" |
| OK button | `.swal2-confirm` | Auto-dismisses after ~3 seconds if not clicked |

### Success — Record Updated (Toast)

Appears after successful HSN SAC edit.

| Element | Selector | Content |
|---------|----------|---------|
| Title | `#swal2-title` | "Your record has been updated successfully!" |

### Key Notes for Automation

- **All 3 fields are required** — no per-field inline error messages, only the generic SweetAlert2 popup.
- **Success toast auto-dismisses** after ~3 seconds. Automation must click the confirm button or wait for container to disappear.
- **Leftover swal2-container elements** can block subsequent actions — must be JS-removed after handling via `_cleanup_swal2()`.
- **Confirm button needs JS click** — direct Selenium click often fails due to z-index layering.

---

## 7. All Selectors (Verified)

### Login Page

| Element | Selector |
|---------|----------|
| Email Input | `input[formcontrolname="email"]` |
| Password Input | `input[formcontrolname="password"]` |
| Tenant Dropdown | `mat-select` |
| Tenant Option | `.cdk-overlay-container mat-option` |
| Login Button | `button[type="submit"][color="primary"]` — **REQUIRES JS CLICK** |

### Toolbar

| Element | Selector |
|---------|----------|
| Search Toggle | `button.search-btn` |
| ADD Button | `//*[@mattooltip='ADD']/button` |
| Filter Button | `//*[@mattooltip='Filters']/button` |
| Refresh Button | `//*[@mattooltip='REFRESH']/button` |
| More Button | `//button[@mattooltip='More']` |
| Search Input | `input#erpSearchInput` |

### Table

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| Table Rows | `table#excel-table tbody tr` |
| HSN SAC Number Cell | `td.mat-column-hsn_sac_no` |
| HSN SAC Type Cell | `td.mat-column-hsn_sac_type` |
| View Button | `td.mat-column-view button` |
| Edit Button | `td.mat-column-edit button` |
| **History Button** | **`td.mat-column-archive button`** (NOT `cdk-column-history`!) |

### Form Popup

| Element | Selector |
|---------|----------|
| Popup Open Check | `div.big-model` (is_displayed) |
| Popup Title | `.big-model h3` — text: "HSN SAC" |
| HSN SAC Number Input | `input[name='HSN SAC Number']` |
| HSN SAC Type Select | `//mat-label[contains(.,'HSN SAC Type')]/ancestor::mat-form-field//mat-select` |
| HSN SAC Description Input | `input[name='HSN SAC Description']` |
| Submit Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]` |
| Update Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]` |
| Cancel Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]` |
| X Close Icon | `.popup-header button mat-icon` where text = "close" |

### History Popup

| Element | Selector |
|---------|----------|
| History Open Check | `.popup-content` (is_displayed) |
| History Title | `h3.popup-title` — text: "HSN SAC History" |
| History Search Input | `.popup-body input[placeholder='Search in table']` |
| History Table Rows | `.popup-body table tbody tr` |
| No Data Message | `//p[contains(text(),'No data available')]` |
| History Cancel | `//div[contains(@class,'popup-content')]//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]` |
| History X Icon | `.popup-content button mat-icon` text = "close" |

### SweetAlert2

| Element | Selector |
|---------|----------|
| Title | `#swal2-title` |
| Confirm Button | `.swal2-confirm` |
| Container | `.swal2-container` |
| Warning Icon | `.swal2-icon.swal2-warning` |
| Success Icon | `.swal2-icon.swal2-success` |
| Content | `.swal2-html-container` |

### Dropdown Options

| Element | Selector |
|---------|----------|
| Options Panel | `div.mat-mdc-select-panel` |
| Option Elements | `div.mat-mdc-select-panel mat-option` or `[role='option']` |
| Overlay Backdrop | `.cdk-overlay-backdrop` |

---

## 8. Validation Matrix

### Required Field Validations (ALL WORKING)

| # | Validation | Trigger | What Happens | Test |
|---|-----------|---------|-------------|------|
| 1 | HSN SAC Number required | Submit/Update with empty Number | SweetAlert2: "Validation Failed — Please correct the highlighted fields". Form stays open. | **C02** ✅ |
| 2 | HSN SAC Type required | Submit/Update with no Type selected | Same as above. | **C03** ✅ |
| 3 | HSN SAC Description required | Submit/Update with empty Description | Same as above. | **C04** ✅ |
| 4 | All fields required | Submit with no fields filled | Same as above. | **C05** ✅ |

### No Validation Gaps

Unlike Vehicle Master (which has 10+ missing validations), HSN SAC has **no validation gaps for the fields it manages**. The module is simple and clean — 3 fields, all required, all validated correctly.

---

## 9. Bug Registry

### No Bugs Found

HSN SAC is a **clean module** with zero bugs discovered during automation.

| # | Observation | Severity | Details |
|---|-------------|----------|---------|
| — | No bugs found | — | All 20 tests passed on first run. No retries needed. |

### Known Behaviors (Not Bugs)

| # | Behavior | Notes |
|---|----------|-------|
| 1 | History shows 0 rows after creation | ERP does not create history entries. Tests verify popup opens, not row content. |
| 2 | Duplicate HSN SAC Number may be allowed | System does not block duplicate numbers — verified in C06. No crash either way. |

---

## 10. How to Run the Tests

### Prerequisites

```bash
pip install selenium pytest pytest-html openpyxl python-dotenv
```

Make sure **ChromeDriver** matches your Chrome version.

### Run All 20 Tests

```bash
pytest pages/common_settings/modules/hsn_sac/test/test_hsn_sac_validation.py -v --tb=short
```

**Expected output**: `20 passed in ~480s (0:08:00)`

### Run by Phase

| Phase | Command | Tests |
|-------|---------|-------|
| Create Validations | `pytest ... -v -k "TestCreateForm" --tb=short` | C01–C06 |
| View Behaviors | `pytest ... -v -k "TestViewForm" --tb=short` | V01–V03 |
| Edit Validations | `pytest ... -v -k "TestEditForm" --tb=short` | E01–E05 |
| History | `pytest ... -v -k "TestHistory" --tb=short` | H01–H03 |
| Table Operations | `pytest ... -v -k "TestTable" --tb=short` | T01–T03 |

*(Replace `...` with the full path shown above)*

### Run a Single Test

```bash
pytest pages/common_settings/modules/hsn_sac/test/test_hsn_sac_validation.py -v -k "test_C01" --tb=short
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
pages/common_settings/modules/hsn_sac/reports/CommonSettings_Report_YYYYMMDD_HHMMSS.xlsx
```

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
│                  HSN SAC — QUICK REFERENCE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SCREEN:  Common Settings > HSN SAC                            │
│  URL:     .../#/dynamic-screens/HSN%20SAC                      │
│  APP:     Angular Material + SweetAlert2                        │
│                                                                 │
│  FORM FIELDS (ALL REQUIRED):                                    │
│    HSN SAC Number* (text) | HSN SAC Type* (dd, 4 fixed)       │
│    HSN SAC Description* (text)                                  │
│                                                                 │
│  DROPDOWN OPTIONS (FIXED — safe to hardcode):                   │
│    Services | Transportation | Commission | Commodity           │
│                                                                 │
│  TABLE COLUMNS:                                                 │
│    View | Edit | History(archive!) | HSN SAC Number | Type     │
│                                                                 │
│  0 BUGS — clean module                                          │
│                                                                 │
│  KEY DIFFERENCES FROM VEHICLE MASTER:                           │
│    ✓ Only 3 fields (vs VM's 5)                                 │
│    ✓ All 3 required (VM Description is optional)               │
│    ✓ 4 FIXED dropdown options (VM has dynamic)                  │
│    ✓ ALL fields editable in Edit (VM same, Bank Name locked)    │
│    ✓ No validation gaps (VM has 10+)                            │
│    ✓ Dropdown wrapped in app-dropdown-v2 (refresh workaround)    │
│                                                                 │
│  KEY GOTCHAS:                                                   │
│    ✗ NEVER use Keys.ESCAPE                                      │
│    ✗ NEVER hardcode Vehicle Master dropdowns (but HSN is OK!)   │
│    ✗ History column CSS = "archive" not "history"               │
│    ✓ ALWAYS use JS clicks for Angular Material                  │
│    ✓ ALWAYS driver.refresh() after navigate                     │
│    ✓ ALWAYS search before Edit/View/History                     │
│    ✓ ALWAYS _force_close_panels() after dropdown selection      │
│    ✓ ALWAYS use contains(@class,'popup-footer') not exact       │
│    ✓ History search REQUIRES Enter key                          │
│    ✓ Fill Dropdown FIRST, then text fields (refresh workaround) │
│                                                                 │
│  RUN ALL:  pytest ... -v --tb=short                             │
│  RUN ONE:  pytest ... -v -k "test_C01" --tb=short              │
│  REPORT:   .../reports/CommonSettings_Report_*.xlsx             │
└─────────────────────────────────────────────────────────────────┘
```

---

*Last Updated: 14-May-2026 | HSN SAC Screen Knowledge Document | 20/20 Tests Passing*
```

---

Save this as `HSN_SAC_Automation_Guide.md` next to your Vehicle Master one. Same format, same sections, zero fluff. 💪