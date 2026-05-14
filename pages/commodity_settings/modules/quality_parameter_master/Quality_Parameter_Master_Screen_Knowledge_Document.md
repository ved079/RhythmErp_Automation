# Quality Parameter Master — Screen Knowledge Document
**RhythmERP | Commodity Settings > Quality Parameter Master**
Last Verified: 14-May-2026 | 32/33 Tests Passing (1 Known Bug XFAIL)

---

## 1. Screen Overview

Quality Parameter Master is a master data screen in RhythmERP under Commodity Settings. It manages quality parameter records — each parameter has only a **Name** field. This is the simplest master screen in the ERP: one field, no dropdowns, no price, no description.

| Detail | Value |
|--------|-------|
| Navigation | Sidebar → Commodity Settings → Quality Parameter Master |
| URL | `https://rhythmerp.algorhythms.in/#/dynamic-screens/Quality%20Parameter%20Master` |
| Framework | Angular Material (mat-table, cdk-overlay, mat-dialog) |
| Alerts | SweetAlert2 (swal2-title, swal2-confirm) |
| Validation | Only 1 required field — significant gaps (see Section 8) |
| Known Bugs | 5 (1 High, 1 Medium, 3 Low) |

### What You Can Do on This Screen

- **Create** a new quality parameter via ADD button → popup form → Submit
- **Edit** an existing quality parameter via row Edit button → popup form → Update
- **View** a quality parameter's details (read-only) via row View button
- **Search** quality parameters by name via toolbar search bar

### What You CANNOT Do on This Screen

- **Delete** — no Delete option exists anywhere (BUG-005)
- **View History** — no History button or audit trail (BUG-006)
- **Filter** — Filter panel may not be present or functional on this screen

---

## 2. Screen Layout

### Toolbar (Top Bar)

```
┌──────────────────────────────────────────────────────────────────┐
│  [🔍 Search]  [+ ADD]  [≛ Filter]  [↻ Refresh]  [⋮ More]      │
└──────────────────────────────────────────────────────────────────┘
```

| Button | Icon | Selector | What It Does |
|--------|------|----------|--------------|
| Search | search icon | `button.search-btn` | Toggles search input bar. Click again to hide. |
| ADD | + (plus) icon | `div[mattooltip='ADD'] button` | Opens Create form popup. Tooltip is on parent **div**, not button. |
| Filter | filter_list icon | `div[mattooltip='Filters'] button` | Opens filter panel. May not exist on this screen. |
| Refresh | refresh icon | Find mini-fab button where mat-icon text = "refresh" | Refreshes table data. |
| More | ⋮ (vertical dots) | `div[mattooltip='More'] button` | Opens menu (Export to Excel, etc.) |

### Search Bar (Hidden by Default)

After clicking the Search toggle, an input bar appears:

| Element | Selector | Notes |
|---------|----------|-------|
| Search Input | `input#erpSearchInput` | Stable ID. Hidden by default. |
| Search Behavior | Type text → press Enter | Filters table by Name. Partial match supported. |

### Table

```
┌──────┬──────┬──────────────────────┐
│ View │ Edit │        Name          │
│  👁  │  ✏️  │                      │
├──────┼──────┼──────────────────────┤
│  btn │  btn │  Moisture Content    │
│  btn │  btn │  Protein Level       │
│  btn │  btn │  (empty — BUG-001)   │  ← spaces-only name created empty record
└──────┴──────┴──────────────────────┘
```

| Column | CSS Class | Sortable? | Notes |
|--------|-----------|-----------|-------|
| View | `mat-column-view` / `cdk-column-view` | No | Action button column |
| Edit | `mat-column-edit` / `cdk-column-edit` | No | Action button column |
| Name | `mat-column-name` / `cdk-column-name` | Yes | **Only data column** |

### Table Selectors

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| All rows | `table#excel-table tbody tr` |
| Name cells | `td.cdk-column-name` or `td.mat-column-name` or `td:nth-child(3)` |
| No data message | `td.no-data` or `tr.mat-mdc-no-data-row` |

### Row Action Buttons (Per Row)

| Action | Position | Selector | Fallback |
|--------|----------|----------|----------|
| View | 1st button (index 0) | `td.mat-column-view button` | Click row button[0] |
| Edit | 2nd button (index 1) | `td.mat-column-edit button` | Click row button[1] |
| History | **Does not exist** | N/A | No History button on QPM |

> **Key Difference from Vehicle Master**: QPM has NO History button. Vehicle Master has 3 action buttons per row (View, Edit, History). QPM has only 2 (View, Edit).

---

## 3. Add / Edit / View Form

All three modes use the same popup container — only the field states and footer buttons differ.

### Popup Structure

```
┌─────────────────────────────────────────────┐
│  Quality Parameter Master    [⛶] [✕]       │  ← Header (.popup-header)
├─────────────────────────────────────────────┤
│                                             │
│  Name *            [________________]       │  ← ONLY field
│                                             │
├─────────────────────────────────────────────┤
│              [Cancel]  [Submit/Update]       │  ← Footer (.popup-footer)
└─────────────────────────────────────────────┘
```

### Field Catalog (1 Field)

| Field | Type | Required | Selector | Behavior |
|-------|------|----------|----------|----------|
| Name | text input | YES | `input[name='Name']` | No max length. No trimming. Accepts special chars, spaces-only. |

> **CRITICAL GOTCHA**: The Name input attribute is `name="Name"` with a **capital N** — NOT `name="name"` (lowercase). This differs from Vehicle Master which uses lowercase. If your selector uses `input[name='name']` it will silently fail to find the element.

### Field State Comparison

| Field | Add Mode | Edit Mode | View Mode |
|-------|----------|-----------|-----------|
| Name | Enabled, Empty | Enabled, Pre-filled | Disabled, Pre-filled |
| Submit button | Present | — | ABSENT |
| Update button | — | Present | ABSENT |
| Cancel button | Present | Present | Present (only button) |

### Popup Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Popup container | `.edit_pop_up.override_edit_pop_up.popup-mode` or `.big-model` | `_is_form_popup_open()` checks this |
| Popup header | `.popup-header` | Contains title + X button |
| Popup title | `.edit_pop_up h3` or `.big-model h3` | Text: "Quality Parameter Master" |
| Close (X) button | `.popup-header button mat-icon` (text="close") | Found by icon text, not CSS class |
| Popup footer | `div[contains(@class,'popup-footer')]` | Use **contains()** — Angular adds extra classes! |
| Submit (Add) | `//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]` | JS click required |
| Update (Edit) | `//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]` | JS click required |
| Cancel | `//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]` | JS click required |

### How to Detect Current Mode

| Mode | How to Detect |
|------|--------------|
| Add Mode | Submit button visible + Update button absent + Name field enabled + empty |
| Edit Mode | Update button visible + Submit button absent + Name field enabled + pre-filled |
| View Mode | No Submit/Update button + Name field disabled + Cancel only |

---

## 4. Dropdowns

**There are NO dropdowns on the Quality Parameter Master screen.**

Unlike Vehicle Master which has Vehicle Type and Fuel Type mat-select dropdowns, QPM has only a single text input field. No mat-select logic, no CDK overlay dropdown panels, no option selection needed.

This means:
- No `_close_select_panel()` calls needed
- No `_force_close_panels()` needed between field interactions (only for general overlay cleanup)
- No dropdown option hardcoding risk

---

## 5. History

**There is NO History feature on the Quality Parameter Master screen.**

Unlike Vehicle Master which has a History button (3rd action per row, `mat-column-archive`), QPM has no History button, no history popup, and no audit trail functionality. This is a known limitation (BUG-006).

This means:
- No history popup methods needed in page object
- No history test phase
- Only 2 action buttons per row (View, Edit) instead of Vehicle Master's 3

---

## 6. SweetAlert2 Messages

RhythmERP uses SweetAlert2 for all validation and success feedback on this screen.

### Validation Failed (Warning Modal)

Appears when you Submit/Update with empty Name field.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-container` | Centered modal, z-index 1060 |
| Warning icon | `.swal2-icon.swal2-warning` | Yellow triangle |
| Title | `#swal2-title` | "Validation Failed" |
| Content | `.swal2-html-container` | "Please correct the highlighted fields" |
| OK button | `.swal2-confirm` | Text: "OK". Click to dismiss. |

**Trigger**: Submit/Update with empty Name field.

### Success — Record Added (Toast)

Appears after successful quality parameter creation.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-container` | Top-right toast |
| Success icon | `.swal2-icon.swal2-success` | Green checkmark |
| Title | `#swal2-title` | "Your record has been added successfully!" |
| OK button | `.swal2-confirm` | Auto-dismisses after ~3 seconds if not clicked |

### Success — Record Updated (Toast)

Appears after successful quality parameter edit.

| Element | Selector | Content |
|---------|----------|---------|
| Title | `#swal2-title` | "Your record has been updated successfully!" |

> **Note**: During initial manual inspection, it appeared that no success SweetAlert was shown (originally documented as BUG-004). Automated testing proved this was incorrect — the success alert DOES appear but may auto-dismiss quickly. BUG-004 is **disproved**.

### Key Notes for Automation

- **No per-field inline error messages** — there are no mat-error elements under the Name field. Only the generic SweetAlert2 popup. (Same as Vehicle Master)
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
| Filter Button | `div[mattooltip='Filters'] button` |
| Refresh Button | Find mini-fab button where mat-icon text = "refresh" |
| Search Input | `input#erpSearchInput` |

### Table

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| Table Rows | `table#excel-table tbody tr` |
| Name Cell | `td.cdk-column-name` or `td.mat-column-name` or `td:nth-child(3)` |
| View Button | `td.mat-column-view button` or `td.cdk-column-view button` |
| Edit Button | `td.mat-column-edit button` or `td.cdk-column-edit button` |
| No Data Row | `td.no-data` or `tr.mat-mdc-no-data-row` |

### Form Popup

| Element | Selector |
|---------|----------|
| Popup Open Check | `div.edit_pop_up.override_edit_pop_up.popup-mode` or `div.big-model` (is_displayed) |
| Popup Title | `.edit_pop_up h3` or `.big-model h3` |
| **Name Input** | **`input[name='Name']`** — capital N! Also try `input[name='name']`, `input[formcontrolname='name']` as fallbacks |
| Submit Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]` |
| Update Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]` |
| Cancel Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]` |
| X Close Icon | `.popup-header button mat-icon` where text = "close" |

### SweetAlert2

| Element | Selector |
|---------|----------|
| Title | `#swal2-title` |
| Confirm Button | `.swal2-confirm` |
| Container | `.swal2-container` |
| Warning Icon | `.swal2-icon.swal2-warning` |
| Success Icon | `.swal2-icon.swal2-success` |
| HTML Message | `.swal2-html-container` |

---

## 8. Validation Matrix

### What IS Validated

| # | Validation | Trigger | What Happens |
|---|-----------|---------|-------------|
| 1 | Name required (Create) | Submit with empty Name | SweetAlert2: "Validation Failed — Please correct the highlighted fields". Form stays open. |
| 2 | Name required (Edit) | Update with empty Name | SweetAlert2: "Validation Failed — Please correct the highlighted fields". Form stays open. |

### What is NOT Validated (Gaps = Bugs)

| # | Missing Validation | What Should Happen | What Actually Happens | Severity |
|---|-------------------|--------------------|-----------------------|----------|
| 1 | Spaces-only Name (Create) | Reject "   " as empty | Accepts spaces, creates empty record | **HIGH** |
| 2 | Name unique constraint | Block duplicate names | Allows duplicates in both Create & Edit | **HIGH** |
| 3 | Name max length | Restrict at 255 chars | Accepts 256+ chars | **MEDIUM** |
| 4 | No Delete option | Allow users to remove records | No Delete button anywhere on screen | **LOW** |
| 5 | No History/Audit trail | Track changes to records | No History button, no audit log | **LOW** |

> **Interesting Finding**: The Edit form DOES validate empty Name (test E03 passed), but the Create form does NOT validate spaces-only names (test C03 xfailed). This means Edit has better validation than Create.

---

## 9. Bug Registry (5 Bugs)

### High (1)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| BUG-001 | Spaces-only Name creates empty record | 1. Click ADD. 2. Enter Name as "         " (spaces only). 3. Click Submit. | Error: "Name cannot be empty" or "Please enter a valid name". | Record created with empty Name. Table shows an empty cell. |

### Medium (1)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| BUG-002 | Duplicate Name allowed | 1. Create QP with Name "Moisture". 2. Create another QP with Name "Moisture". 3. Submit. | Error: "Name already exists". | Second QP created. No warning. Both exist in table. |

### Low (3)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| BUG-003 | No maxlength on Name input | 1. Click ADD. 2. Enter Name with 256+ characters. 3. Submit. | Error: "Name too long" or truncate. | Name accepted without limit. |
| BUG-005 | No Delete option | 1. Look for Delete button on any row or in any popup. | Delete button available to remove records. | No Delete button anywhere. Records cannot be removed. |
| BUG-006 | No History/Audit trail | 1. Look for History button on any row. | History button to view change log. | No History button. No way to track changes. |

### Disproved Bugs

| Bug | Original Claim | Disproven By | Reality |
|-----|---------------|-------------|---------|
| BUG-004 | No success SweetAlert after create/update | Automated test run on 14-May-2026 | Success SweetAlert DOES appear: "Your record has been added successfully!" and "Your record has been updated successfully!". The alert auto-dismisses quickly, which is why it was missed during manual inspection. |

---

## 10. How to Run the Tests

### Prerequisites

```bash
pip install selenium pytest pytest-html openpyxl python-dotenv
```

Make sure ChromeDriver matches your Chrome version.

### Run All 33 Tests

```powershell
cd C:\RhythmERP-Automation
pytest pages/commodity_settings/modules/quality_parameter_master/test/test_quality_parameter_master_validation.py -v --tb=short
```

**Expected output**: 32 passed, 1 xfailed in ~370s (~6 min)

### Run by Phase

| Phase | Command | Tests |
|-------|---------|-------|
| Create Validations | `pytest ... -v -k "TestCreateForm" --tb=short` | C01–C12 |
| Duplicate Validations | `pytest ... -v -k "TestDuplicate" --tb=short` | D01–D03 |
| Edit Validations | `pytest ... -v -k "TestEditForm" --tb=short` | E01–E06 |
| Search & Filter | `pytest ... -v -k "TestSearchFilter" --tb=short` | S01–S05 |
| Popup & UI | `pytest ... -v -k "TestPopupUI" --tb=short` | P01–P07 |

*(Replace `...` with the full path shown above)*

### Run a Single Test

```powershell
pytest pages/commodity_settings/modules/quality_parameter_master/test/test_quality_parameter_master_validation.py -v -k "QPM_C03" --tb=short
```

### Run Only Failed Tests

```powershell
pytest pages/commodity_settings/modules/quality_parameter_master/test/test_quality_parameter_master_validation.py -v -k "QPM_C03 or QPM_E01 or QPM_E03 or QPM_P04 or QPM_P06 or QPM_P07" --tb=short
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
pages/commodity_settings/modules/quality_parameter_master/reports/CommonSettings_Report_YYYYMMDD_HHMMSS.xlsx
```

The report includes: test names, pass/fail status, step-by-step logs, error messages, and the known issues list.

### Credentials Used

| Parameter | Value | Source |
|-----------|-------|--------|
| URL | `https://rhythmerp.algorhythms.in` | config.py |
| Login URL | `.../#/authentication/signin` | config.py |
| Email | `test@gmail.com` | config.py |
| Password | `Test@2526270` | config.py |
| Facility | Agdi (first option, index 0) | config.py |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│         QUALITY PARAMETER MASTER — QUICK REFERENCE              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SCREEN:  Commodity Settings > Quality Parameter Master         │
│  URL:     .../#/dynamic-screens/Quality%20Parameter%20Master    │
│  APP:     Angular Material + SweetAlert2                        │
│                                                                 │
│  FORM FIELDS:                                                   │
│    Name* (text) — THAT'S IT. Just one field.                    │
│                                                                 │
│  TABLE COLUMNS:                                                 │
│    View | Edit | Name                                           │
│                                                                 │
│  5 BUGS:  1 High | 1 Medium | 3 Low                            │
│  WORST:   Spaces-only Name creates empty record (High)          │
│            Duplicate Name allowed (Medium)                       │
│                                                                 │
│  KEY GOTCHAS:                                                   │
│    ✗ NEVER use Keys.ESCAPE                                      │
│    ✗ Name input = input[name='Name'] — CAPITAL N!               │
│    ✗ NO dropdowns on this screen                                │
│    ✗ NO History button (unlike Vehicle Master)                  │
│    ✗ NO Delete option anywhere                                  │
│    ✓ ALWAYS use JS clicks for Angular Material                  │
│    ✓ ALWAYS driver.refresh() after navigate                     │
│    ✓ ALWAYS search before Edit                                  │
│    ✓ ALWAYS use contains(@class,'popup-footer') not exact       │
│    ✓ Success SweetAlert DOES exist (auto-dismisses quickly)     │
│                                                                 │
│  RUN ALL:  pytest ... -v --tb=short                             │
│  RUN ONE:  pytest ... -v -k "QPM_C03" --tb=short               │
│  REPORT:   .../reports/CommonSettings_Report_*.xlsx             │
│                                                                 │
│  VS VEHICLE MASTER:                                             │
│    • 1 field vs 5 fields                                        │
│    • No dropdowns vs 2 dropdowns                                │
│    • No History vs History popup                                │
│    • No Delete vs No Delete (same)                              │
│    • input[name='Name'] vs input[name='Name'] (same)            │
│    • 33 tests vs 43 tests                                       │
│    • 5 bugs vs 13 bugs                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

*Last Updated: 14-May-2026 | Quality Parameter Master Screen Knowledge Document | 32/33 Tests Passing (1 XFAIL)*
