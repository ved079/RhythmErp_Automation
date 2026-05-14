# UOM — Screen Knowledge Document

> **RhythmERP** | Common Settings > UOM
> **Last Verified**: 14-May-2026 | **21/21 Tests Passing**

---

## 1. Screen Overview

**UOM (Unit of Measure)** is a master data screen in RhythmERP under **Common Settings**. It manages unit of measure records — each UOM has a Code, a Description, and a Status (Active/Inactive toggle). Unlike Designation or Vehicle Master, UOM has only 2 text fields plus a Status toggle, but features a unique 3-pattern SweetAlert2 system and a 255-character backend limit on both fields.

| Detail | Value |
|--------|-------|
| **Navigation** | Sidebar → Common Settings → UOM |
| **URL** | `https://rhythmerp.algorhythms.in/#/dynamic-screens/UOM` |
| **Framework** | Angular Material (mat-form-field, mat-error, mat-table) |
| **Alerts** | SweetAlert2 — **3 distinct patterns** (A, B, C) |
| **Validation** | UOM Code required + `type="character"` pattern. UOM Description required (no pattern). Both have 255-char backend limit. |
| **Known Bugs** | 3 (1 High, 1 Medium, 1 Low) |

### Key Differences from Designation / Vehicle Master

| Aspect | Vehicle Master | Designation | UOM |
|--------|---------------|-------------|-----|
| **Fields** | 5 (Name, Price, Type, Fuel, Description) | 3 (Name, Description, Status) | 2 + toggle (Code, Description, Status) |
| **Dropdowns** | 2 mat-select dropdowns | None | None |
| **Status** | N/A | Toggle switch | Toggle switch (`app-slide-toggle-v2`) |
| **Inline Errors** | None (SweetAlert2 only) | Yes — "Invalid Name" mat-error | Yes — mat-error on Code; red border on Description |
| **Duplicate Check** | None (BUG) | None (BUG) | **YES** — Pattern B alert |
| **SweetAlert2 Patterns** | 1 (validation) | 1 (validation) | **3** (A: validation, B: duplicate, C: backend error) |
| **Backend Char Limit** | None | None | **255 chars** (both Code and Description) |
| **Space Trimming** | Not trimmed (BUG) | Not trimmed (BUG) | **Silently trimmed** (BUG — no warning) |

### What You Can Do on This Screen

- **Create** a new UOM via ADD button → popup form → Submit
- **Edit** an existing UOM via row Edit button → popup form → Update
- **View** a UOM's details (read-only) via row View button
- **Search** UOMs by code via toolbar search bar
- **Check History** of changes via row History button → history popup
- **Toggle Status** between Active and Inactive

---

## 2. Screen Layout

### Toolbar (Top Bar)

```
+------------------------------------------------------------------+
|  [Search]  [+ ADD]  [Filter]  [Refresh]  [More]                 |
+------------------------------------------------------------------+
```

| Button | Icon | Selector | What It Does |
|--------|------|----------|-------------|
| **Search** | search icon | `button.search-btn` | Toggles search input bar. Click again to hide. |
| **ADD** | + (plus) icon | `div[mattooltip='ADD'] button` or `button[mattooltip='ADD']` | Opens Create form popup. **Tooltip may be on parent div.** |
| **Filter** | filter_list icon | `button.filter-btn` | Opens right-side filter panel. **BROKEN — Apply Filters non-functional.** |
| **Refresh** | refresh icon | Find by mat-icon text "refresh" | Refreshes table data. |
| **More** | vertical dots | `button[mattooltip='More']` | Opens menu (Export to Excel, etc.) |

### Search Bar (Hidden by Default)

After clicking the Search toggle, an input bar appears:

| Element | Selector | Notes |
|---------|----------|-------|
| Search Input | `input#erpSearchInput` | Stable ID. Hidden by default. |
| Search Behavior | Type text → press Enter | Filters table by UOM Code. Partial match supported. |

### Table

```
+------+------+---------+----------+------------------+--------+
| View | Edit | History | UOM Code | UOM Description  | Status |
|  btn |  btn |   btn   |          |                  |        |
+------+------+---------+----------+------------------+--------+
|  btn |  btn |   btn   |   MT     |  Metric Tonne    | Active |
|  btn |  btn |   btn   |   KG     |  Kilogram        | Active |
+------+------+---------+----------+------------------+--------+
```

| Column | CSS Class | Sortable? | Notes |
|--------|-----------|-----------|-------|
| View | `mat-column-view` | No | Action button column |
| Edit | `mat-column-edit` | No | Action button column. Has `mattooltip="Click to edit"` |
| **History** | **`mat-column-archive`** | No | **CRITICAL: CSS class is "archive" NOT "history"!** |
| UOM Code | `mat-column-uom_code` | Yes | Sort header present. Primary identifier. |
| UOM Description | `mat-column-uom_description` | Yes | Sort header present. May be empty. |
| Status | `mat-column-status` | Yes | Shows "Active" or "Inactive" |

### Table Selectors

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| All rows | `table#excel-table tbody tr` |
| UOM Code cells | `td.cdk-column-uom_code` or `td.mat-column-uom_code` |
| Description cells | `td.cdk-column-uom_description` or `td.mat-column-uom_description` |
| Status cells | `td.cdk-column-status` or `td.mat-column-status` |
| No data message | `td.no-data` or `tr.mat-mdc-no-data-row` |

### Row Action Buttons (Per Row)

| Action | Position | Selector | Fallback |
|--------|----------|----------|----------|
| **View** | 1st button (index 0) | `td.mat-column-view button` | Pure JS: `_click_action_button(code, 'cdk-column-view')` |
| **Edit** | 2nd button (index 1) | `td.mat-column-edit button` | Pure JS: `_click_action_button(code, 'cdk-column-edit')` |
| **History** | 3rd button (index 2) | `td.mat-column-archive button` | Pure JS: `_click_action_button(code, 'cdk-column-archive')` |

### The `_click_action_button()` Method

Unlike Designation and Vehicle Master which use standard Selenium clicks on action buttons, UOM uses a **pure JavaScript** approach via `_click_action_button(code, column_class)`. This method:

1. Finds all table rows via `document.querySelectorAll('table tbody tr')`
2. Iterates rows looking for one where any cell text matches the UOM code
3. Once the row is found, finds the button inside `td.${column_class}`
4. Clicks the button via `arguments[0].click()`

This approach is necessary because Angular Material's dynamic rendering can cause stale element issues with standard Selenium locators.

---

## 3. Add / Edit / View Form

All three modes use the **same popup container** — only the field states and footer buttons differ.

### Popup Structure

```
+---------------------------------------------+
|  UOM                    [Full] [X]           |  <- Header (.popup-header)
+---------------------------------------------+
|                                             |
|  UOM Code *        [________________]       |  <- type="character" input
|  UOM Description * [________________]       |  <- text input (required!)
|  Status            [=====O]  Active         |  <- app-slide-toggle-v2
|                                             |
+---------------------------------------------+
|              [Cancel]  [Submit/Update]       |  <- Footer (.popup-footer)
+---------------------------------------------+
```

### Field Catalog (2 Fields + Toggle)

| Field | Type | Required | Selector | Behavior |
|-------|------|----------|----------|----------|
| **UOM Code** | text input | YES | `input[name='UOM Code']` | `type="character"`. Letters only. Accepts lowercase and mixed case (saved as-is). Rejects digits and special chars. Shows `mat-error` inline. **255-char backend limit** — 256+ chars cause Pattern C error. **Leading spaces silently trimmed** by backend. |
| **UOM Description** | text input | YES | `input[name='UOM Description']` | Accepts all characters including special chars. **255-char backend limit** — 256+ chars cause Pattern C error. No pattern validation. Shows red border on error but NO mat-error text. |
| **Status** | toggle switch | NO (defaults Active) | `app-slide-toggle-v2 .slider` | Toggle between Active/Inactive. Default is Active. Click `.slider` via JS. |

### Status Toggle Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Toggle component | `app-slide-toggle-v2` | Custom Angular component — not the same as Designation's `.switch-wrapper` |
| Toggle slider | `app-slide-toggle-v2 .slider` | JS click required. Normal click may fail. |
| State label | `app-slide-toggle-v2 .state-label.on` | Has "active" class when Active. |
| Active indicator | `app-slide-toggle-v2 .state-label.on.active` | Visible when toggle is in Active state |

### Field State Comparison

| Field | Add Mode | Edit Mode | View Mode |
|-------|----------|-----------|-----------|
| UOM Code | Enabled, Empty | Enabled, Pre-filled | **Disabled**, Pre-filled |
| UOM Description | Enabled, Empty | Enabled, Pre-filled | **Disabled**, Pre-filled |
| Status | **Active (checked)** | Pre-selected | **Disabled**, Pre-selected |
| **Submit button** | **Present** | — | **ABSENT** |
| **Update button** | — | **Present** | **ABSENT** |
| **Cancel button** | Present | Present | Present (only button) |

### Popup Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Popup container | `.big-model` or `.edit_pop_up.popup-mode` | _is_form_popup_open() checks for UOM Code input |
| Popup header | `.popup-header` | Contains title + X button |
| Popup title | `.big-model h3` | Text: "UOM" |
| Close (X) button | `.popup-header button mat-icon` (text="close") | `force_close_form_popup()` uses pure JS |
| Popup footer | `div.popup-footer` | Contains Submit/Update/Cancel |
| Submit (Add) | `div.popup-footer button` (text="Submit") | `click_with_retry()` used |
| Update (Edit) | `div.popup-footer button` (text="Update") | `click_with_retry()` used |
| Cancel | `div.popup-footer button` (text="Cancel") | `click_with_retry()` used |

### How to Detect Current Mode

```
Add Mode:    Submit button visible + Update button absent + fields enabled
Edit Mode:   Update button visible + Submit button absent + fields enabled + pre-filled
View Mode:   No Submit/Update button + all fields disabled + Cancel only
```

---

## 4. UOM Code Validation (type="character")

The UOM Code field uses Angular's `type="character"` attribute — the same as Designation's Name field. However, UOM's implementation has some key behavioral differences.

### What `type="character"` Does

The `type="character"` attribute restricts input to **letters only**. Unlike Designation (which also allows spaces), UOM Code accepts purely alphabetic characters. When invalid content is detected, Angular shows inline validation errors.

### Accepted Characters

| Category | Examples | Accepted? |
|----------|----------|-----------|
| Uppercase letters | A-Z | YES |
| Lowercase letters | a-z | YES (saved as-is) |
| Mixed case | AbCdEfGh | YES (saved as-is) |
| Spaces | " " | **YES** (but trimmed by backend — BUG) |
| Digits | 0-9 | **NO** — rejected |
| Special chars | @#$%^&*! | **NO** — rejected |
| Underscores | _ | **NO** — rejected |

### Key Difference from Designation

| Behavior | Designation Name | UOM Code |
|----------|-----------------|----------|
| Spaces in value | Accepted and preserved | Accepted but **silently trimmed by backend** |
| Digits | Rejected (mat-error) | Rejected (mat-error) |
| Special chars | Rejected (mat-error) | Rejected (mat-error) |
| Lowercase | Accepted | **Accepted** (saved as-is, not uppercased) |
| Mixed case | Accepted | **Accepted** (saved as-is) |
| Duplicate check | **None** (BUG) | **YES** — Pattern B alert |

### The `get_mat_error_text()` Method

Unlike Designation which uses a 4-tier Python approach, UOM's `get_mat_error_text()` uses **pure JavaScript** that walks the DOM parentElement chain:

1. Find the `input[name='UOM Code']` element
2. Walk up the parentElement chain (up to 20 steps)
3. At each level, check for `mat-error` child elements
4. Return the text content of the first visible `mat-error` found

This approach is more reliable than the Python 4-tier method because it directly traverses the Angular Material DOM structure rather than relying on class-based detection.

### The `has_field_error()` Method

Also pure JavaScript, checks for Angular Material error classes:

- `mat-mdc-form-field-invalid` on the form field wrapper
- `ng-invalid` on the input element
- `cdk-text-field-invalid` on the input element

If any of these classes are found, the field is considered to have an error state.

### UOM Description Error Behavior

The UOM Description field behaves differently from UOM Code when invalid:

| Aspect | UOM Code | UOM Description |
|--------|----------|-----------------|
| Error indicator | `mat-error` text ("UOM Code is required") | **Red border only** — no mat-error text |
| CSS classes | `ng-invalid` + `mat-mdc-form-field-invalid` | `mat-mdc-form-field-invalid` + `cdk-text-field-invalid` |
| Detection method | `get_mat_error_text()` finds mat-error | `has_field_error()` checks CSS classes only |

---

## 5. Status Toggle Switch

The UOM screen uses a **toggle switch** for Status, implemented via the `app-slide-toggle-v2` custom Angular component.

### Toggle Behavior

| State | Slider Position | Display Text | CSS Indicator |
|-------|----------------|--------------|---------------|
| **Active** | Right | "Active" | `.state-label.on.active` present |
| **Inactive** | Left | "Inactive" | `.state-label.on` without `.active` |
| **Default (Add)** | Right | "Active" | Active by default |

### How to Read Toggle State

```python
# Method: get_toggle_state()
# Checks .state-label.on for 'active' class
# Returns True (Active) or False (Inactive)

on_labels = driver.find_elements(By.CSS_SELECTOR,
    "app-slide-toggle-v2 .state-label.on")
for label in on_labels:
    if 'active' in label.get_attribute('class'):
        return True  # Active
return False  # Inactive
```

### How to Toggle

```python
# Method: toggle_status()
# Clicks the .slider element via JS click
sliders = driver.find_elements(By.CSS_SELECTOR,
    "app-slide-toggle-v2 .slider")
for slider in sliders:
    wrapper = slider.find_element(By.XPATH,
        "./ancestor::app-slide-toggle-v2")
    if wrapper.is_displayed():
        driver.execute_script("arguments[0].click();", slider)
```

### Key Rules for Toggle Automation

| Rule | Why |
|------|-----|
| **Use JS click** for `.slider` | Normal Selenium click may be intercepted by Angular overlay |
| **Use `app-slide-toggle-v2` not `.switch-wrapper`** | UOM uses a different toggle component than Designation |
| **Always verify state after toggle** | Confirm the toggle actually changed before proceeding |
| **View mode = disabled toggle** | In View mode, the toggle is non-interactive but still shows correct state |

---

## 6. History Popup

### How to Open

Click the **History** button (3rd action button per row, clock icon) in the table. The popup opens as an overlay.

### Popup Structure

```
+-----------------------------------------------------+
|  UOM History                       [Full] [X]        |  <- app-dynamic-history header
+-----------------------------------------------------+
|  [Search in table]  [Refresh] [More]                 |  <- Toolbar
+------+------------+------------+----------+----+-----+
| View | Creation   | Updated    | UOM Code | Desc| Sts |  <- Table
|  btn | Time       | Time       |          |     |     |
+------+------------+------------+----------+----+-----+
|                        [Cancel]                       |  <- .popup-footer
+-----------------------------------------------------+
```

### History Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| History popup | `app-dynamic-history .tbl-title h2` | **Different component** from form popup — uses `app-dynamic-history` |
| History no data | `app-dynamic-history .no-data` or `app-dynamic-history img[alt='No Data Available']` | `is_history_empty()` checks both selectors |
| History no data text | `//app-dynamic-history//*[contains(text(),'No data available')]` | Fallback check for no data state |
| History search input | `app-dynamic-history input#erpSearchInput` | Search within history table |
| History table rows | `app-dynamic-history table#excel-table tbody tr` | `get_history_data()` reads all rows |
| History Cancel button | `//app-dynamic-history//div[@class='popup-footer']//button[contains(.,'Cancel')]` | `close_history_popup()` uses pure JS click |

### History Table Columns

| Column | CSS Class | Data Type | Example |
|--------|-----------|-----------|---------|
| Creation Time | `cdk-column-created_date_time` | DateTime | "11 May 2026, 10:30 AM" |
| Updated Time | `cdk-column-updated_date_time` | DateTime | "11 May 2026, 10:35 AM" |
| UOM Code | `cdk-column-uom_code` | Text | "ABCDEFGH" |
| Description | `cdk-column-uom_description` | Text | "Test UOM Description" |
| Status | `cdk-column-status` | Text | "Active" / "Inactive" |

### Important Findings

| Finding | Impact |
|---------|--------|
| **History IS populated** for UOM | Unlike Designation/Vehicle Master (which show "No data available"), UOM **does** create history entries after create and edit operations. |
| **History uses `app-dynamic-history` component** | Different selector structure from form popup. Don't reuse form popup selectors. |
| **History column CSS = "archive"** | The History action column uses class `mat-column-archive`, NOT `mat-column-history` or `cdk-column-history`. |
| **`get_history_data()` returns structured data** | Returns list of dicts with keys: `created_time`, `updated_time`, `uom_code`, `description`, `status` |

---

## 7. SweetAlert2 Messages — 3 Patterns

RhythmERP's UOM screen uses **3 distinct SweetAlert2 patterns** — more than any other screen. Understanding which pattern triggers when is critical for automation.

### Pattern A: Validation Failed (Warning Modal)

Appears when required fields are empty or the UOM Code contains invalid characters.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-container` | Centered modal, z-index 1060 |
| Warning icon | `.swal2-popup.swal2-icon-warning` | Yellow triangle |
| Title | `#swal2-title` | "Validation Failed" |
| Content | `.swal2-html-container` | "Please correct the highlighted fields" |
| OK button | `.swal2-confirm` | Text: "OK". Click to dismiss. |

**Triggers**: Empty UOM Code, empty Description, both empty, numbers in Code, special chars in Code, edit with empty Code/Description.

### Pattern B: Duplicate Code (Validation Download)

Appears when you try to create a UOM with a code that already exists. This is **unique to UOM** — neither Designation nor Vehicle Master have duplicate detection.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-container` | Centered modal |
| Warning icon | `.swal2-popup.swal2-icon-warning` | Yellow triangle |
| Title | `#swal2-title` | "Fields validation failed" |
| Content | `.swal2-html-container` | "Do you want to download?" |
| Cancel button | `.swal2-cancel` | Text: "Cancel". **Click THIS to dismiss.** |
| Download button | `.swal2-confirm` | Text: "Download Errors". **Do NOT click — would download file.** |

**Triggers**: Duplicate UOM Code "MT", duplicate UOM Code "KG", or any other existing code.

**CRITICAL**: Always click **Cancel** (`.swal2-cancel`), NOT the confirm button. The confirm button triggers a file download.

### Pattern C: Backend Error Toast

Appears when the backend rejects the record — specifically when either field exceeds the 255-character limit. This is **unique to UOM**.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-container` | Toast notification |
| Error icon | `.swal2-popup.swal2-icon-error` | Red X circle |
| Title | `#swal2-title` | "Failed to save record" |
| No buttons | — | Auto-dismisses after 3-6 seconds |

**Triggers**: 256-character UOM Code, 256-character UOM Description.

**Key Problem**: The error message is completely generic — "Failed to save record" — with no indication that the 256th character caused the failure, or what the character limit is. This is Bug #1 (High severity).

### Success — Record Added (Toast)

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-container` | Top-right toast |
| Success icon | `.swal2-icon.swal2-success` | Green checkmark |
| Title | `#swal2-title` | "Your record has been added successfully!" |
| OK button | `.swal2-confirm` | Auto-dismisses after ~3 seconds |

### Success — Record Updated (Toast)

| Element | Selector | Content |
|---------|----------|---------|
| Title | `#swal2-title` | "Your record has been updated successfully!" |

### Alert Pattern Summary Table

| Pattern | Icon | Title | Has Buttons? | Dismiss Method | When |
|---------|------|-------|-------------|----------------|------|
| **A** | Warning (yellow) | "Validation Failed" | Yes — "OK" | Click `.swal2-confirm` | Empty/invalid fields |
| **B** | Warning (yellow) | "Fields validation failed" | Yes — "Cancel" + "Download Errors" | Click `.swal2-cancel` | Duplicate code |
| **C** | Error (red) | "Failed to save record" | No | Wait 3-6s auto-dismiss | 256+ char backend rejection |
| Success | Success (green) | "added/updated successfully" | Yes — "OK" | Click `.swal2-confirm` or wait | Successful create/edit |

### Key Notes for Automation

- **Pattern B requires clicking `.swal2-cancel`**, NOT `.swal2-confirm`. Clicking confirm would download a validation report file, which is undesirable in automated tests.
- **Pattern C auto-dismisses** — no button click needed. Just wait 3-6 seconds for the container to disappear.
- **Success toast auto-dismisses** after ~3 seconds. The form popup also auto-closes on success (Bug #3 — causes cosmetic ERROR in logs when Cancel cleanup tries to click the already-gone Cancel button).
- **Leftover swal2-container elements** can block subsequent actions — must be JS-removed after handling.
- **Confirm/Cancel buttons need JS click** — direct Selenium click often fails due to z-index layering.

---

## 8. All Selectors (Verified)

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
| ADD Button | `div[mattooltip='ADD'] button` or `button[mattooltip='ADD']` |
| Filter Button | `button.filter-btn` |
| Refresh Button | Find mini-fab button where mat-icon text = "refresh" |
| Search Input | `input#erpSearchInput` |

### Table

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| Table Rows | `table#excel-table tbody tr` |
| UOM Code Cell | `td.cdk-column-uom_code` or `td.mat-column-uom_code` |
| Description Cell | `td.cdk-column-uom_description` or `td.mat-column-uom_description` |
| Status Cell | `td.cdk-column-status` or `td.mat-column-status` |
| View Button | `td.mat-column-view button` |
| Edit Button | `td.mat-column-edit button` |
| **History Button** | **`td.mat-column-archive button`** (NOT `cdk-column-history`!) |
| No Data Row | `td.no-data` or `tr.mat-mdc-no-data-row` |

### Form Popup

| Element | Selector |
|---------|----------|
| Popup Open Check | `input[name='UOM Code']` (is_displayed) |
| Popup Title | `.big-model h3` |
| UOM Code Input | `input[name='UOM Code']` |
| UOM Description Input | `input[name='UOM Description']` |
| Status Toggle Slider | `app-slide-toggle-v2 .slider` |
| Status State Label | `app-slide-toggle-v2 .state-label.on` |
| Submit Button | `div.popup-footer button` (text="Submit") |
| Update Button | `div.popup-footer button` (text="Update") |
| Cancel Button | `div.popup-footer button` (text="Cancel") |
| X Close Icon | `.popup-header button mat-icon` text = "close" |
| Inline Error (Code) | `mat-error` inside mat-form-field (found via JS parentElement chain) |
| Error State (Description) | Red border — `mat-mdc-form-field-invalid` class (no mat-error text) |

### History Popup

| Element | Selector |
|---------|----------|
| History Header | `app-dynamic-history .tbl-title h2` |
| History No Data | `app-dynamic-history .no-data` or `app-dynamic-history img[alt='No Data Available']` |
| History Search Input | `app-dynamic-history input#erpSearchInput` |
| History Table Rows | `app-dynamic-history table#excel-table tbody tr` |
| History Cancel | `//app-dynamic-history//div[@class='popup-footer']//button[contains(.,'Cancel')]` |
| History X Icon | `.popup-header button mat-icon` text = "close" |

### SweetAlert2

| Element | Selector |
|---------|----------|
| Title | `#swal2-title` |
| Confirm Button | `.swal2-confirm` |
| Cancel Button | `.swal2-cancel` |
| Container | `.swal2-container` |
| Warning Icon | `.swal2-popup.swal2-icon-warning` |
| Error Icon | `.swal2-popup.swal2-icon-error` |
| Success Icon | `.swal2-icon.swal2-success` |

---

## 9. Validation Matrix

### What IS Validated

| # | Validation | Trigger | What Happens |
|---|-----------|---------|-------------|
| 1 | UOM Code required | Submit/Update with empty Code | Pattern A: "Validation Failed — Please correct the highlighted fields" + mat-error under Code field |
| 2 | UOM Description required | Submit/Update with empty Description | Pattern A: "Validation Failed" + red border on Description (no mat-error text) |
| 3 | Both required | Submit with both empty | Pattern A + mat-error on Code + red border on Description |
| 4 | UOM Code pattern (type="character") | Invalid characters in Code | Pattern A + mat-error inline |
| 5 | Duplicate UOM Code | Code matches existing record (MT, KG, etc.) | Pattern B: "Fields validation failed. Do you want to download?" |
| 6 | Backend 255-char limit (Code) | 256+ chars in Code | Pattern C: "Failed to save record" (generic error) |
| 7 | Backend 255-char limit (Description) | 256+ chars in Description | Pattern C: "Failed to save record" (generic error) |
| 8 | Numbers in UOM Code | Code like "ABC12345" | Pattern A + mat-error inline |
| 9 | Special chars in UOM Code | Code like "AB!@#$%^" | Pattern A + mat-error inline |
| 10 | Special chars in Description | Description like "Test@#$%^&*()" | **Accepted** — no validation on Description content |

### UOM Code Validation Details

| Input | Valid? | Alert Pattern | Error Shown | Tier That Catches It |
|-------|--------|---------------|-------------|---------------------|
| `"ABCDEFGH"` (uppercase) | YES | — | None | — |
| `"abcdefgh"` (lowercase) | YES | — | None | — |
| `"AbCdEfGh"` (mixed case) | YES | — | None | — |
| `"ABC12345"` (digits) | NO | Pattern A | mat-error | JS parentElement chain |
| `"AB!@#$%^"` (special chars) | NO | Pattern A | mat-error | JS parentElement chain |
| `"  ABCDEFGH"` (leading space) | YES* | — | None (trimmed silently) | *Spaces trimmed by backend — BUG |
| `"MT"` (duplicate) | NO | Pattern B | Validation download | Duplicate detection |
| `""` (empty) | NO | Pattern A | mat-error | Required field check |
| 256-char Code | NO | Pattern C | Generic backend error | Backend rejection |

### What is NOT Validated (Gaps = Bugs)

| # | Missing Validation | What Should Happen | What Actually Happens | Severity |
|---|-------------------|--------------------|-----------------------|----------|
| 1 | 255-char limit has no frontend validation | Show field-level error before submit | Generic "Failed to save record" from backend — no indication of limit | **HIGH** |
| 2 | Leading/trailing spaces silently trimmed | Preserve spaces or warn user | Spaces silently trimmed by backend — no warning | **MEDIUM** |
| 3 | Success auto-closes form + ERROR in logs | Form stays open or Cancel handles gracefully | Form auto-closes; Cancel cleanup logs cosmetic ERROR | **LOW** |

---

## 10. Bug Registry (3 Bugs)

### High (1)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#1** | 255-char backend limit with generic error | 1. Create UOM. 2. Enter 256+ char Code or Description. 3. Submit. | Clear field-level error indicating the 255-character maximum. | Generic "Failed to save record" toast (Pattern C). No indication of the character limit or which field caused the failure. |

### Medium (1)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#2** | Leading/trailing spaces silently trimmed | 1. Create UOM. 2. Enter Code with leading spaces like "  ABCDEFGH". 3. Submit. | Either preserve spaces or warn user they will be removed. | UOM saved as "ABCDEFGH" — spaces silently trimmed without any warning. User has no idea the value was modified. |

### Low (1)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#3** | Success auto-close causes cosmetic ERROR in logs | 1. Create UOM successfully. 2. SweetAlert confirms and form auto-closes. 3. Test cleanup tries Cancel. | Cancel should handle already-closed form silently. | Cancel click fails with ERROR log. Then force_close_form_popup() handles it. This ERROR could mask real issues in test logs. |

### Bug Impact on Tests

| Test | Bug | Impact |
|------|-----|--------|
| Test 12 (256-char Description) | Bug #1 | Pattern C generic error — test passes but documents the poor UX |
| Test 14 (256-char Code) | Bug #1 | Pattern C generic error — same as Test 12 |
| Test 24 (Leading space trimmed) | Bug #2 | UOM created with trimmed code — test documents the silent trimming |
| Test 20 (Lowercase code) | Bug #3 | Auto-close ERROR in logs — test still passes |
| Test 21 (Mixed case code) | Bug #3 | Auto-close ERROR in logs — test still passes |
| Test 24 (Leading space) | Bug #3 | Auto-close ERROR in logs — test still passes |
| Test 25 (Special chars Description) | Bug #3 | Auto-close ERROR in logs — test still passes |

---

## 11. Test Case Inventory (21 Tests)

### Smoke Test (1 test)

| Test | File | Description | Expected Result | Bug? |
|------|------|-------------|----------------|------|
| UOM-01 | `test_uom.py` | Create and verify UOM | UOM created and found in table via search | — |

### Full E2E Flow (1 test, 5 steps)

| Test | File | Description | Expected Result | Bug? |
|------|------|-------------|----------------|------|
| UOM-02 | `test_uom_full_flow.py` | Create → View → History(empty) → Edit → History(with data) | All 5 steps pass: Create success, View read-only, History empty, Edit success, History has data | — |

### Validation Tests (19 tests)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| UOM-07 | Empty UOM Code | Pattern A + mat-error under Code | — |
| UOM-08 | Empty UOM Description | Pattern A + red border on Description | — |
| UOM-09 | Both fields empty | Pattern A + mat-error on Code + red border on Description | — |
| UOM-10 | Duplicate code "MT" | Pattern B (validation download) | — |
| UOM-11 | Duplicate code "KG" | Pattern B (validation download) | — |
| UOM-12 | 256-char Description | Pattern C ("Failed to save record") | Bug #1 |
| UOM-13 | 255-char Description | Accepted + cleanup edit | — |
| UOM-14 | 256-char Code | Pattern C ("Failed to save record") | Bug #1 |
| UOM-15 | 255-char Code | Accepted | — |
| UOM-16 | Cancel add form | UOM not created | — |
| UOM-17 | Edit empty Description | Pattern A + error state | — |
| UOM-18 | Edit empty Code | Pattern A + mat-error | — |
| UOM-19 | Submit untouched form | Pattern A + both fields invalid | — |
| UOM-20 | Lowercase code | Accepted as-is | Bug #3 (cosmetic) |
| UOM-21 | Mixed case code | Accepted as-is | Bug #3 (cosmetic) |
| UOM-22 | Numbers in code | Rejected (Pattern A) | — |
| UOM-23 | Special chars in code | Rejected (Pattern A) | — |
| UOM-24 | Leading space code | Auto-trimmed by backend | Bug #2, Bug #3 |
| UOM-25 | Special chars in Description | Accepted as-is | Bug #3 (cosmetic) |

---

## 12. How to Run the Tests

### Prerequisites

```bash
pip install selenium pytest pytest-html openpyxl python-dotenv
```

Make sure **ChromeDriver** matches your Chrome version.

### Run All 21 Tests

```bash
pytest pages/common_settings/modules/uom/test/ -v --tb=short
```

**Expected output**: `21 passed`

### Run by Test File

| File | Command | Tests |
|------|---------|-------|
| Smoke test | `pytest .../test_uom.py -v --tb=short` | UOM-01 |
| Full flow | `pytest .../test_uom_full_flow.py -v --tb=short` | UOM-02 |
| Validations | `pytest .../test_uom_validation.py -v --tb=short` | UOM-07 to UOM-25 |

### Run a Single Test

```bash
pytest pages/common_settings/modules/uom/test/test_uom_validation.py -v -k "test_07" --tb=short
```

### Run Only Bug-Related Tests

```bash
pytest pages/common_settings/modules/uom/test/test_uom_validation.py -v -k "test_12 or test_14 or test_24" --tb=short
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
pages/common_settings/modules/uom/reports/CommonSettings_Report_YYYYMMDD_HHMMSS.xlsx
```

The report includes: test names, pass/fail status, step-by-step logs, error messages, and the 3 known issues list.

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
+-----------------------------------------------------------------+
|              UOM — QUICK REFERENCE                               |
+-----------------------------------------------------------------+
|                                                                 |
|  SCREEN:  Common Settings > UOM                                 |
|  URL:     .../#/dynamic-screens/UOM                             |
|  APP:     Angular Material + SweetAlert2 (3 patterns!)          |
|                                                                 |
|  FORM FIELDS:                                                   |
|    UOM Code* (type="character") | UOM Description* (required)  |
|    Status (app-slide-toggle-v2, default=Active)                 |
|                                                                 |
|  TABLE COLUMNS:                                                 |
|    View | Edit | History(archive!) | UOM Code | Desc | Status  |
|                                                                 |
|  3 BUGS:  1 High | 1 Medium | 1 Low                            |
|  WORST:   255-char limit = generic "Failed to save" (High)      |
|           Leading spaces silently trimmed (Medium)               |
|           Success auto-close = cosmetic ERROR in logs (Low)     |
|                                                                 |
|  SWEETALERT2 PATTERNS:                                          |
|    Pattern A: "Validation Failed" — click .swal2-confirm        |
|    Pattern B: "Fields validation failed" — click .swal2-cancel! |
|    Pattern C: "Failed to save record" — wait auto-dismiss       |
|                                                                 |
|  UOM CODE VALIDATION (type="character"):                        |
|    Accepts:  A-Z a-z (lowercase & mixed saved as-is)            |
|    Rejects:  digits, special chars, underscores                 |
|    Error:    mat-error via JS parentElement chain                |
|    Backend:  255-char limit (256+ = Pattern C)                  |
|    Spaces:   Silently trimmed (BUG — no warning)                |
|                                                                 |
|  DUPLICATE CHECK: YES! (unlike Designation/Vehicle Master)      |
|    Triggers Pattern B alert for existing codes (MT, KG, etc.)   |
|                                                                 |
|  STATUS TOGGLE:                                                 |
|    Component: app-slide-toggle-v2 (NOT .switch-wrapper!)        |
|    Selector: app-slide-toggle-v2 .slider (JS click!)            |
|    Default:  Active                                             |
|    State:    .state-label.on + 'active' class                   |
|                                                                 |
|  KEY GOTCHAS:                                                   |
|    x NEVER click .swal2-confirm on Pattern B (downloads file!)  |
|    x NEVER use Keys.ESCAPE                                      |
|    x History column CSS = "archive" not "history"               |
|    x UOM Description has NO mat-error text (red border only)    |
|    x 256+ chars = Pattern C (generic error, no field detail)    |
|    x Toggle uses app-slide-toggle-v2 not .switch-wrapper        |
|    x Action buttons use pure JS _click_action_button()          |
|    CHECK ALWAYS use JS clicks for Angular Material              |
|    CHECK ALWAYS driver.refresh() after navigate                 |
|    CHECK ALWAYS search before Edit/History                      |
|    CHECK Pattern B: click CANCEL, not confirm                   |
|    CHECK Pattern C: wait for auto-dismiss (3-6s)                |
|    CHECK get_mat_error_text() uses JS parentElement chain       |
|    CHECK has_field_error() checks 3 CSS classes                 |
|                                                                 |
|  RUN ALL:  pytest ... -v --tb=short                             |
|  RUN ONE:  pytest ... -v -k "test_07" --tb=short               |
|  REPORT:   .../reports/CommonSettings_Report_*.xlsx             |
+-----------------------------------------------------------------+
```

---

*Last Updated: 14-May-2026 | UOM Screen Knowledge Document | 21/21 Tests Passing*
