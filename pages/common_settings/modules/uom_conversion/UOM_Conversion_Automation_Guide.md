# UOM Conversion — Screen Knowledge Document

> **RhythmERP** | Common Settings > UOM Conversion
> **Last Verified**: 15-May-2026 | **22/22 Tests Passing**

---

## 1. Screen Overview

**UOM Conversion** is a transaction screen in RhythmERP under **Common Settings**. It manages conversion factor records between pairs of Units of Measure — each record defines a Source UOM, a Target UOM, and a numeric Conversion Factor. Unlike the UOM master screen (which has simple text inputs), UOM Conversion features two **mat-select dropdowns** (Source UOM, Target UOM) and a **numeric input** (Conversion Factor). The screen also introduces a unique **dynamic pair generation** system and a critical **scientific notation bug** with 22+ digit factors.

| Detail | Value |
|--------|-------|
| **Navigation** | Sidebar → Common Settings → UOM Conversion |
| **URL** | `https://rhythmerp.algorhythms.in/#/dynamic-screens/UOM%20Conversion` |
| **Framework** | Angular Material MDC (mat-mdc-select, mat-form-field, mat-error, mat-table) |
| **Alerts** | SweetAlert2 — **3 distinct patterns** (A, B, C) |
| **Validation** | Source UOM required + Target UOM required + Conversion Factor required + numeric pattern. Duplicate (Source, Target) pair detection via Pattern B. |
| **Known Bugs** | 2 (1 High, 1 Low) |
| **Dropdowns** | 2 mat-select dropdowns (Source UOM, Target UOM) with search capability |

### Key Differences from UOM / Designation / Vehicle Master

| Aspect | Vehicle Master | Designation | UOM | UOM Conversion |
|--------|---------------|-------------|-----|----------------|
| **Fields** | 5 (Name, Price, Type, Fuel, Description) | 3 (Name, Description, Status) | 2 + toggle (Code, Description, Status) | 3 (Source UOM, Target UOM, Conversion Factor) |
| **Dropdowns** | 2 mat-select dropdowns | None | None | **2 mat-select dropdowns** (with search) |
| **Status** | N/A | Toggle switch | Toggle switch (`app-slide-toggle-v2`) | **No Status toggle** |
| **Key Identifier** | Vehicle Name | Designation Name | UOM Code | **(Source UOM, Target UOM) pair** |
| **Inline Errors** | None (SweetAlert2 only) | Yes — "Invalid Name" mat-error | Yes — mat-error on Code; red border on Description | Yes — mat-error on Conversion Factor; `ng-invalid` on dropdowns |
| **Duplicate Check** | None (BUG) | None (BUG) | YES — Pattern B alert | **YES** — Pattern B alert for duplicate pairs |
| **SweetAlert2 Patterns** | 1 (validation) | 1 (validation) | 3 (A: validation, B: duplicate, C: backend error) | **3** (A: validation, B: duplicate pair, C: backend error) |
| **Dynamic Data** | Fixed dropdown options | N/A | N/A | **YES** — dropdowns populated from UOM master; pair uniqueness checked live |
| **Special Bug** | N/A | N/A | 255-char backend limit | **22+ digit factor = scientific notation** (uneditable record) |

### What You Can Do on This Screen

- **Create** a new UOM Conversion via ADD button → popup form → Submit
- **Edit** an existing Conversion Factor via row Edit button → popup form → Update
- **View** a Conversion's details (read-only) via row View button
- **Search** Conversions by code via toolbar search bar
- **Check History** of changes via row History button → history popup

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
| **ADD** | + (plus) icon | `app-custom-header mat-icon` (text="add") | Opens Create form popup. **Clicked via JS** — iterates `app-custom-header mat-icon` elements. |
| **Filter** | filter_list icon | `button.filter-btn` | Opens right-side filter panel. **BROKEN — Apply Filters non-functional.** |
| **Refresh** | refresh icon | `app-custom-header mat-icon` (text="refresh") | Refreshes table data. **Clicked via JS** — same icon iteration pattern. |
| **More** | vertical dots | `button[mattooltip='More']` | Opens menu (Export to Excel, etc.) |

### Search Bar (Hidden by Default)

After clicking the Search toggle, an input bar appears:

| Element | Selector | Notes |
|---------|----------|-------|
| Search Input | `input#erpSearchInput` | Stable ID. Hidden by default. |
| Search Behavior | Type text → press Enter | Filters table by Source/Target UOM Code. Partial match supported. |

### Table

```
+------+------+---------+-----------+-----------+-------------------+
| View | Edit | History | Source    | Target    | Conversion Factor |
|  btn |  btn |   btn   | UOM Code  | UOM Code  |                   |
+------+------+---------+-----------+-----------+-------------------+
|  btn |  btn |   btn   |   KG      |   ML      |       1000        |
|  btn |  btn |   btn   |   NOS     |   PCS     |         1         |
+------+------+---------+-----------+-----------+-------------------+
```

| Column | CSS Class | Sortable? | Notes |
|--------|-----------|-----------|-------|
| View | `mat-column-view` | No | Action button column |
| Edit | `mat-column-edit` | No | Action button column |
| **History** | **`mat-column-archive`** | No | **CRITICAL: CSS class is "archive" NOT "history"!** |
| Source UOM Code | `cdk-column-source_uom_code` or `mat-column-source_uom_code` | Yes | First part of the key pair |
| Target UOM Code | `cdk-column-target_uom_code` or `mat-column-target_uom_code` | Yes | Second part of the key pair |
| Conversion Factor | `cdk-column-conversion_factor` or `mat-column-conversion_factor` | Yes | Numeric value |

### Table Selectors

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| All rows | `table#excel-table tbody tr.mat-mdc-row` |
| Source UOM cells | `td.cdk-column-source_uom_code` or `td.mat-column-source_uom_code` |
| Target UOM cells | `td.cdk-column-target_uom_code` or `td.mat-column-target_uom_code` |
| Factor cells | `td.cdk-column-conversion_factor` or `td.mat-column-conversion_factor` |
| No data message | `td.no-data` or `tr.mat-mdc-no-data-row` |

### Row Action Buttons (Per Row)

| Action | Position | Selector | Fallback |
|--------|----------|----------|----------|
| **View** | 1st button (index 0) | `td.mat-column-view button` | Pure JS: `_click_action_button(source, target, 'view')` |
| **Edit** | 2nd button (index 1) | `td.mat-column-edit button` | Pure JS: `_click_action_button(source, target, 'edit')` |
| **History** | 3rd button (index 2) | `td.mat-column-archive button` | Pure JS: `_click_action_button(source, target, 'archive')` |

### The `_click_action_button()` Method

UOM Conversion uses a **pure JavaScript** approach for row action buttons via `_click_action_button(row_source, row_target, action_column)`. This method:

1. Finds all table rows via `document.querySelectorAll('table#excel-table tbody tr.mat-mdc-row')`
2. Iterates rows looking for one where `cdk-column-source_uom_code` matches the source AND `cdk-column-target_uom_code` matches the target
3. Once the row is found, finds the button inside `cdk-column-{action_column}`
4. Clicks the button via `arguments[0].click()`

This approach is necessary because Angular Material's dynamic rendering can cause stale element issues with standard Selenium locators. Note that the row is identified by the **(Source UOM, Target UOM) pair** rather than a single code value — this is unique to UOM Conversion.

---

## 3. Add / Edit / View Form

All three modes use the **same popup container** (`div.overflow_model`) — only the field states and footer buttons differ.

### Popup Structure

```
+-----------------------------------------------------+
|  UOM Conversion                    [Full] [X]        |  <- Header (.popup-header)
+-----------------------------------------------------+
|                                                     |
|  Source UOM *       [▼ Select...]                   |  <- mat-select dropdown
|  Target UOM *       [▼ Select...]                   |  <- mat-select dropdown
|  Conversion Factor * [________________]             |  <- type="character" input
|                                                     |
+-----------------------------------------------------+
|                [Cancel]  [Submit/Update]             |  <- Footer (.popup-footer)
+-----------------------------------------------------+
```

### Field Catalog (3 Fields, No Toggle)

| Field | Type | Required | Selector | Behavior |
|-------|------|----------|----------|----------|
| **Source UOM** | mat-select dropdown | YES | `mat-form-field` with `mat-label` text "Source UOM" → `.mat-mdc-select-trigger` | MDC dropdown with search. Populated from UOM master data. Shows `mat-mdc-select-invalid` + `ng-invalid` classes on error. **Disabled in View mode.** |
| **Target UOM** | mat-select dropdown | YES | `mat-form-field` with `mat-label` text "Target UOM" → `.mat-mdc-select-trigger` | MDC dropdown with search. Populated from UOM master data. Same error classes as Source. **Disabled in View mode.** |
| **Conversion Factor** | text input (`type="character"`) | YES | `mat-form-field` with `mat-label` text "Conversion Factor" → `input` | Accepts integers. Rejects decimals, text, special chars, and negative values via Pattern A validation. Shows `mat-error` inline. **22+ digit values cause scientific notation bug.** Uses `type="character"` instead of `type="number"` (Bug #2). |

### Field State Comparison

| Field | Add Mode | Edit Mode | View Mode |
|-------|----------|-----------|-----------|
| Source UOM | Enabled, Empty | Enabled, Pre-selected | **Disabled**, Pre-selected |
| Target UOM | Enabled, Empty | Enabled, Pre-selected | **Disabled**, Pre-selected |
| Conversion Factor | Enabled, Empty | Enabled, Pre-filled | **Disabled**, Pre-filled |
| **Submit button** | **Present** (`button[type="submit"]`) | — | **ABSENT** |
| **Update button** | — | **Present** (`button[type="submit"]`) | **ABSENT** |
| **Cancel button** | Present (`div.popup-footer .left button`) | Present | Present (only button) |

### Popup Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Popup container | `div.overflow_model` | `is_form_open()` checks visibility of this element |
| Popup header | `.popup-header` | Contains title + X button |
| Popup actions | `.popup-actions` | Contains close (X) icon button |
| Close (X) button | `.popup-actions button` with `mat-icon` text="close" | `force_close_form_popup()` uses pure JS |
| Popup footer | `div.popup-footer` | Contains Submit/Update/Cancel |
| Submit (Add) | `div.popup-footer button[type="submit"]` | `click_save_button()` uses pure JS |
| Cancel | `div.popup-footer .left button` | `click_cancel_button()` uses pure JS; fallback to text "Cancel" match |
| Inline Error (Factor) | `mat-error` inside `mat-form-field` with label "Conversion Factor" | Found via `get_mat_error_text("Conversion Factor")` |
| Dropdown Error State | `mat-mdc-select-invalid` or `ng-invalid` on `mat-select` | Found via `is_dropdown_error("Source UOM")` / `is_dropdown_error("Target UOM")` |

### How to Detect Current Mode

```
Add Mode:    Submit button visible + Update button absent + fields enabled
Edit Mode:   Update button visible + Submit button absent + fields enabled + pre-filled
View Mode:   No Submit/Update button + all fields disabled + Cancel only
```

---

## 4. mat-select Dropdown Handling (MDC)

UOM Conversion is the **first screen** in the Common Settings automation suite that uses **Angular Material MDC dropdowns** (`mat-mdc-select`). The dropdown handling is significantly more complex than text inputs and requires a precise 5-step pure JavaScript flow.

### The `select_uom()` Method — 5-Step Flow

| Step | Action | JS Code | Purpose |
|------|--------|---------|---------|
| **1** | Click the select trigger | `fields[i].querySelector('.mat-mdc-select-trigger').click()` | Opens the dropdown panel |
| **2** | Wait for panel to appear | Poll `document.querySelector('.mat-mdc-select-panel').offsetParent` up to 15 times (0.4s each) | Ensures panel is rendered before interacting |
| **3** | Type in search input | `panel.querySelector('.search-container input')` + `nativeInputValueSetter` + `dispatchEvent('input')` | Filters options to find the target UOM code |
| **4** | Click matching option | `panel.querySelectorAll('mat-option')` → find `.mdc-list-item__primary-text` match → `click()` | Selects the exact UOM code (with partial-match fallback) |
| **5** | Cleanup leftover panels | `_force_close_panels()` — removes `.cdk-overlay-backdrop` and `.cdk-overlay-pane` elements | Prevents stale overlay panels from blocking subsequent actions |

### Dropdown Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Select trigger | `mat-form-field .mat-mdc-select-trigger` | Click to open dropdown. Uses label text to find the correct form field. |
| Select panel | `.mat-mdc-select-panel` | The dropdown options panel. Appears in CDK overlay container. |
| Search input | `.mat-mdc-select-panel .search-container input` | Type UOM code to filter options |
| Options | `.mat-mdc-select-panel mat-option` | All available UOM options |
| Option text | `mat-option .mdc-list-item__primary-text` | The display text of each option |
| Selected value text | `mat-form-field .mat-mdc-select-value-text span` | Currently selected value shown in the trigger |

### Option Matching Logic

The `select_uom()` method uses a **two-tier matching strategy**:

1. **Exact match first**: Iterate all `mat-option` elements and find one where `.mdc-list-item__primary-text` exactly equals the target UOM code.
2. **Partial match fallback**: If no exact match, convert both to uppercase and check if the option text contains the target string.

This ensures that even if the dropdown shows descriptions alongside codes, the correct option is still found.

### Key Rules for Dropdown Automation

| Rule | Why |
|------|-----|
| **Use JS `nativeInputValueSetter` for search input** | Angular's reactive forms do not detect changes set via `input.value = ...`. Must use the native setter and dispatch `input` event. |
| **Always wait for panel to appear** | The dropdown panel renders asynchronously. Without waiting, the search input won't be found. |
| **Always cleanup CDK overlays after selection** | Leftover `.cdk-overlay-backdrop` and `.cdk-overlay-pane` elements can block clicks on subsequent elements. |
| **Never use standard Selenium `Select` class** | Angular Material's `mat-select` is not a native `<select>` element. Standard Selenium methods will fail. |
| **Never use `Keys.ESCAPE`** | Can corrupt Angular's internal state. Use `_force_close_panels()` instead. |

### The `is_dropdown_error()` Method

Checks if a mat-select dropdown has an error state by looking for these CSS classes on the `mat-select` element:

- `mat-mdc-select-invalid` — Angular Material MDC invalid class
- `ng-invalid` — Angular framework invalid class

If either class is present, the dropdown is considered to have an error state. This is used in Tests 4, 5, and 7 to verify that empty dropdown submissions mark the fields as invalid.

---

## 5. Conversion Factor Validation

The Conversion Factor field uses Angular's `type="character"` attribute — the same attribute used by UOM Code and Designation Name. However, for a numeric field, this creates unexpected behavior.

### What `type="character"` Does on a Numeric Field

The `type="character"` attribute on the Conversion Factor input is **inappropriate for a numeric field**. It should be `type="number"` which would provide native browser validation (numeric keyboard on mobile, automatic min/max checking, etc.). Instead, all numeric validation is handled by the backend, resulting in:

- No native browser numeric keyboard on mobile devices
- No HTML5 `min`, `max`, or `step` validation
- All validation errors shown via SweetAlert Pattern A + `mat-error`
- Text, special characters, and decimals are typed in freely but rejected on submit

### Accepted Values

| Input | Valid? | Alert Pattern | Error Shown |
|-------|--------|---------------|-------------|
| `"10"` (integer) | YES | — | None |
| `"999"` (integer) | YES | — | None |
| `"0"` (zero) | OBSERVE — accepted or rejected depends on backend | Pattern A or Success | Varies |
| `"-5"` (negative) | OBSERVE — accepted or rejected depends on backend | Pattern A or Success | Varies |
| `"0.123"` (decimal) | **NO** | Pattern A | mat-error: "Invalid Conversion Factor" |
| `"abc"` (text) | **NO** | Pattern A | mat-error |
| `"@#$"` (special chars) | **NO** | Pattern A | mat-error |
| `""` (empty) | **NO** | Pattern A | mat-error |
| 21-digit integer | YES | Success | None |
| 22-digit integer | YES (BUG) | Success | None — but displays as scientific notation (1e+22) on re-edit |

### The `get_mat_error_text()` Method

Unlike UOM's version which walks the `parentElement` chain, UOM Conversion's `get_mat_error_text(label_text)` method directly queries `mat-form-field` elements by their label text:

1. Find all `mat-form-field` elements
2. Look for one where `mat-label` text contains the given label text (e.g. "Conversion Factor")
3. Find `mat-error` child element within that form field
4. Return its trimmed text content, or empty string if not found

This is a cleaner approach because it uses the label as a reliable anchor rather than walking the DOM tree.

### The `clear_conversion_factor_via_js()` Method

Used in Test 16 (Edit — clear Conversion Factor). Standard `clear()` methods don't work on Angular Material inputs. This method:

1. Finds the `mat-form-field` with label "Conversion Factor"
2. Focuses the input
3. Uses `nativeInputValueSetter` to set value to empty string
4. Dispatches both `input` and `change` events with `bubbles: true`

This ensures Angular's reactive forms detect the change and update validation state accordingly.

---

## 6. Dynamic Pair Generation

UOM Conversion introduces a unique challenge: **test data must be a (Source UOM, Target UOM) pair that does not already exist in the table**. Unlike UOM or Designation where you can just use a random string, UOM Conversion requires checking existing records before creating new ones.

### The Problem

- Each (Source UOM, Target UOM) pair must be **unique** — duplicates trigger Pattern B alert
- The dropdown options are **populated from the UOM master table** — you cannot use arbitrary strings
- Existing pairs in the table **change over time** as records are added or deleted
- Hardcoded UOM pairs (like "NOS → ML") may already exist, causing test failures

### The `create_fresh_record()` Method — 10-Step Flow

The `create_fresh_record()` method is the **one-flow solution** that handles everything in a single pass:

| Step | Action | Method Called | Notes |
|------|--------|-------------|-------|
| **1** | Read existing pairs from table | `get_existing_pairs()` | Returns set of tuples: `{('KG', 'ML'), ('NOS', 'PCS'), ...}` |
| **2** | Open Add form | `open_add_form()` | Popup opens once — dropdowns only exist inside the form |
| **3** | Open Source UOM dropdown | `_read_dropdown_uoms()` | Clicks trigger, waits for options, reads all `.mdc-list-item__primary-text` values |
| **4** | Pick a fresh pair | Random sampling (up to 50 attempts) | `random.sample(uoms, 2)` — checks against existing pairs set |
| **5** | Generate random factor | `random.randint(1, 1000)` | Simple integer factor |
| **6** | Select Source UOM from open dropdown | `_select_from_open_panel(source)` | Clicks option in the **already open** panel — no reopen needed |
| **7** | Select Target UOM | `select_target_uom(target)` | Opens fresh dropdown via normal 5-step flow |
| **8** | Fill Conversion Factor | `enter_conversion_factor(factor)` | JS setter + event dispatch |
| **9** | Submit | `submit()` | Clicks `button[type="submit"]` via JS |
| **10** | Handle SweetAlert | `get_swal_title()` + `handle_success_alert()` or `close_popup()` | Checks for success or failure |

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Source dropdown stays OPEN** after `_read_dropdown_uoms()` | Avoids reopening the dropdown which can cause Angular state corruption. The already-open panel is used for selection via `_select_from_open_panel()`. |
| **Target dropdown opens fresh** via `select_target_uom()` | The Target dropdown hasn't been opened yet, so it goes through the full 5-step `select_uom()` flow. |
| **50 attempts for fresh pair** | If all N*(N-1) possible pairs exist (extremely unlikely with 8+ UOMs), raises `RuntimeError`. |
| **`get_available_uoms()` vs `_read_dropdown_uoms()`** | `get_available_uoms()` is a standalone method that opens the popup, reads options, and closes everything. `_read_dropdown_uoms()` is used inside `create_fresh_record()` and leaves the dropdown open for immediate selection. |

### The `get_existing_pairs()` Method

Reads all existing (Source UOM, Target UOM) pairs directly from the visible table without needing any popup:

```javascript
var rows = table.querySelectorAll('tbody tr');
// For each row, find cdk-column-source_uom_code and cdk-column-target_uom_code
// Return array of [source, target] pairs
```

Returns a set of tuples: `{('KG', 'ML'), ('NOS', 'PCS'), ...}`.

### The `get_available_uoms()` Method (Standalone)

Opens the Add form popup temporarily, opens the Source UOM dropdown, reads all option texts, then closes everything. This is useful when you need to know what UOMs are available **before** deciding which pair to create.

**Note**: This method is more expensive than `_read_dropdown_uoms()` because it opens and closes the form. For creating records, use `create_fresh_record()` instead which avoids the extra open/close cycle.

---

## 7. History Popup

### How to Open

Click the **History** button (3rd action button per row, clock icon) in the table. The popup opens as an overlay.

### Popup Structure

```
+------------------------------------------------------------------+
|  UOM Conversion History                         [Full] [X]       |  <- Header
+------------------------------------------------------------------+
|  [Search in table]  [Refresh] [More]                              |  <- Toolbar
+------+------------+------------+-----------+-----------+---------+
| View | Creation   | Updated    | Source    | Target    | Factor  |  <- Table
|  btn | Time       | Time       | UOM Code  | UOM Code  |         |
+------+------------+------------+-----------+-----------+---------+
|                        [Cancel]                                   |  <- Footer
+------------------------------------------------------------------+
```

### History Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| History row count | `document.querySelectorAll('table tbody tr')` or `.mat-mdc-row` | `get_history_row_count()` checks both selectors |
| History data | `table tbody tr.mat-mdc-row` → `textContent.trim()` per row | `get_history_data()` returns list of row text strings |
| History close | `.swal2-confirm` or `button[mat-icon-button] mat-icon[font]` text="close" | `close_history_popup()` tries swal2-confirm first, then icon button |

### Important Findings

| Finding | Impact |
|---------|--------|
| **History IS populated** for UOM Conversion | Like UOM (but unlike Designation/Vehicle Master), UOM Conversion creates history entries after create and edit operations. |
| **History column CSS = "archive"** | The History action column uses class `mat-column-archive`, NOT `mat-column-history` or `cdk-column-history`. |
| **`get_history_data()` returns text blobs** | Unlike UOM which returns structured dicts, UOM Conversion's history data is returned as a list of raw text strings per row. |

---

## 8. SweetAlert2 Messages — 3 Patterns

RhythmERP's UOM Conversion screen uses **3 distinct SweetAlert2 patterns** — the same as UOM but triggered by different conditions.

### Pattern A: Validation Failed (Warning Modal)

Appears when required fields are empty or the Conversion Factor contains invalid characters.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-container` | Centered modal, z-index 1060 |
| Warning icon | `.swal2-popup.swal2-icon-warning` | Yellow triangle |
| Title | `#swal2-title` | "Validation Failed" |
| Content | `.swal2-html-container` | "Please correct the highlighted fields" |
| OK button | `.swal2-confirm` | Text: "OK". Click to dismiss. |

**Triggers**: Empty Source UOM, empty Target UOM, empty Conversion Factor, all fields empty, text in Factor, special chars in Factor, decimals in Factor, cleared Factor on edit.

### Pattern B: Duplicate Pair (Validation Download)

Appears when you try to create a UOM Conversion with a (Source, Target) pair that already exists.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-container` | Centered modal |
| Warning icon | `.swal2-popup.swal2-icon-warning` | Yellow triangle |
| Title | `#swal2-title` | "Fields validation failed" |
| Content | `.swal2-html-container` | "Do you want to download?" |
| Cancel button | `.swal2-cancel` | Text: "Cancel". **Click THIS to dismiss.** |
| Download button | `.swal2-confirm` | Text: "Download Errors". **Do NOT click — would download file.** |

**Triggers**: Duplicate (Source UOM, Target UOM) pair — e.g. creating "KG → ML" when that pair already exists.

**CRITICAL**: Always click **Cancel** (`.swal2-cancel`), NOT the confirm button. The confirm button triggers a file download.

### Pattern C: Backend Error Toast

Appears when the backend rejects the record for reasons not caught by frontend validation.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-container` | Toast notification |
| Error icon | `.swal2-popup.swal2-icon-error` | Red X circle |
| Title | `#swal2-title` | "Failed to save record" |
| No buttons | — | Auto-dismisses after 3-6 seconds |

**Triggers**: Backend-side validation failures not caught by the frontend.

**Note**: Pattern C is less common in UOM Conversion than in UOM (where 256+ char inputs triggered it). The primary edge case in UOM Conversion is the 22+ digit scientific notation bug, which actually **succeeds** (Pattern: Success).

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
| **B** | Warning (yellow) | "Fields validation failed" | Yes — "Cancel" + "Download Errors" | Click `.swal2-cancel` | Duplicate pair |
| **C** | Error (red) | "Failed to save record" | No | Wait 3-6s auto-dismiss | Backend rejection |
| Success | Success (green) | "added/updated successfully" | Yes — "OK" | Click `.swal2-confirm` or wait | Successful create/edit |

### Key Notes for Automation

- **Pattern B requires clicking `.swal2-cancel`**, NOT `.swal2-confirm`. Clicking confirm would download a validation report file.
- **Pattern C auto-dismisses** — no button click needed. Just wait 3-6 seconds for the container to disappear.
- **Leftover swal2-container elements** can block subsequent actions — must be JS-removed after handling.
- **Confirm/Cancel buttons need JS click** — direct Selenium click often fails due to z-index layering.
- **Same-source-and-target UOM** (e.g. "Fest → Fest") — system behavior is **OBSERVE**: it may succeed or reject depending on backend logic.

---

## 9. All Selectors (Verified)

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
| ADD Button | `app-custom-header mat-icon` (text="add") — JS click via icon iteration |
| Refresh Button | `app-custom-header mat-icon` (text="refresh") — JS click via icon iteration |
| Search Toggle | `button.search-btn` |
| Filter Button | `button.filter-btn` |
| Search Input | `input#erpSearchInput` |

### Table

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| Table Rows | `table#excel-table tbody tr.mat-mdc-row` |
| Source UOM Cell | `td.cdk-column-source_uom_code` or `td.mat-column-source_uom_code` |
| Target UOM Cell | `td.cdk-column-target_uom_code` or `td.mat-column-target_uom_code` |
| Factor Cell | `td.cdk-column-conversion_factor` or `td.mat-column-conversion_factor` |
| View Button | `td.mat-column-view button` |
| Edit Button | `td.mat-column-edit button` |
| **History Button** | **`td.mat-column-archive button`** (NOT `cdk-column-history`!) |
| No Data Row | `td.no-data` or `tr.mat-mdc-no-data-row` |

### Form Popup

| Element | Selector |
|---------|----------|
| Popup Open Check | `div.overflow_model` (is_displayed via JS `getComputedStyle`) |
| Popup Actions (close icon) | `div.overflow_model .popup-actions button` with `mat-icon` text="close" |
| Popup Footer | `div.popup-footer` |
| Submit Button | `div.popup-footer button[type="submit"]` |
| Cancel Button | `div.popup-footer .left button` (fallback: button with text "Cancel") |
| Source UOM Dropdown | `mat-form-field` with `mat-label` "Source UOM" → `.mat-mdc-select-trigger` |
| Target UOM Dropdown | `mat-form-field` with `mat-label` "Target UOM" → `.mat-mdc-select-trigger` |
| Conversion Factor Input | `mat-form-field` with `mat-label` "Conversion Factor" → `input` |
| Inline Error (Factor) | `mat-error` inside mat-form-field with label "Conversion Factor" |
| Dropdown Error State | `mat-mdc-select-invalid` or `ng-invalid` on `mat-select` element |

### Dropdown Panel (CDK Overlay)

| Element | Selector |
|---------|----------|
| Select Panel | `.mat-mdc-select-panel` |
| Search Input | `.mat-mdc-select-panel .search-container input` |
| Options | `.mat-mdc-select-panel mat-option` |
| Option Text | `mat-option .mdc-list-item__primary-text` |
| Selected Value | `mat-form-field .mat-mdc-select-value-text span` |

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

## 10. Validation Matrix

### What IS Validated

| # | Validation | Trigger | What Happens |
|---|-----------|---------|-------------|
| 1 | Source UOM required | Submit with empty Source UOM | Pattern A + `mat-mdc-select-invalid` / `ng-invalid` on Source UOM dropdown |
| 2 | Target UOM required | Submit with empty Target UOM | Pattern A + `mat-mdc-select-invalid` / `ng-invalid` on Target UOM dropdown |
| 3 | Conversion Factor required | Submit with empty Factor | Pattern A + `mat-error` under Conversion Factor |
| 4 | All fields required | Submit with nothing filled | Pattern A + errors on all 3 fields |
| 5 | Conversion Factor pattern (type="character") | Text in Factor ("abc") | Pattern A + `mat-error`: "Invalid Conversion Factor" |
| 6 | Conversion Factor pattern (special chars) | Special chars in Factor ("@#$%") | Pattern A + `mat-error` |
| 7 | Conversion Factor pattern (decimal) | Decimal in Factor ("0.123") | Pattern A + `mat-error` |
| 8 | Duplicate pair check | (Source, Target) pair already exists | Pattern B: "Fields validation failed. Do you want to download?" |
| 9 | Same source and target | Source UOM = Target UOM (e.g. "Fest → Fest") | **OBSERVE** — may succeed or reject depending on backend logic |
| 10 | Negative factor | Factor = "-5" | **OBSERVE** — may succeed or reject depending on backend logic |
| 11 | Zero factor | Factor = "0" | **OBSERVE** — may succeed or reject depending on backend logic |
| 12 | 21-digit factor | Factor = "100000000000000000000" | **Accepted** — saves and displays correctly |
| 13 | 22-digit factor | Factor = "1000000000000000000000" | **BUG** — saves but displays as scientific notation (1e+22) on re-edit |

### Conversion Factor Validation Details

| Input | Valid? | Alert Pattern | Error Shown | Detection Method |
|-------|--------|---------------|-------------|-----------------|
| `"10"` (integer) | YES | — | None | — |
| `"0.123"` (decimal) | NO | Pattern A | mat-error | `get_mat_error_text("Conversion Factor")` |
| `"abc"` (text) | NO | Pattern A | mat-error | `get_mat_error_text("Conversion Factor")` |
| `"@#$"` (special chars) | NO | Pattern A | mat-error | `get_mat_error_text("Conversion Factor")` |
| `""` (empty) | NO | Pattern A | mat-error | `get_mat_error_text("Conversion Factor")` |
| `"-5"` (negative) | OBSERVE | Pattern A or Success | Varies | `get_swal_title()` check |
| `"0"` (zero) | OBSERVE | Pattern A or Success | Varies | `get_swal_title()` check |
| 21-digit integer | YES | Success | None | `is_success_alert_present()` |
| 22-digit integer | YES (BUG) | Success | None (but displays as 1e+22 on re-edit) | `get_conversion_factor_value()` in edit form |

### What is NOT Validated (Gaps = Bugs)

| # | Missing Validation | What Should Happen | What Actually Happens | Severity |
|---|-------------------|--------------------|-----------------------|----------|
| 1 | 22+ digit conversion factor has no frontend limit | Either reject values that cannot be displayed accurately, or preserve the full numeric value so the record remains editable | Value saves and displays as 1e+22 on reopen. Update fails with "Invalid Conversion Factor". Record becomes **permanently uneditable**. | **HIGH** |
| 2 | Conversion Factor uses `type='character'` instead of `type='number'` | Input should use `type='number'` for native browser validation and numeric keyboard on mobile | Input uses `type='character'`. All numeric validation is backend-only. No native UX benefits. | **LOW** |

---

## 11. Bug Registry (2 Bugs)

### High (1)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#1** | 22+ digit factor saves but displays as scientific notation, making the record permanently uneditable | 1. Create UOM Conversion (e.g. MT → KG). 2. Enter 22-digit Conversion Factor like "1000000000000000000000". 3. Submit — succeeds. 4. Open Edit for that record. 5. Conversion Factor shows "1e+22". 6. Click Update — Pattern A "Invalid Conversion Factor" error. | System should either reject values that cannot be displayed accurately, or preserve the full numeric value so the record remains editable. | Value saves and displays as 1e+22 on reopen. Clicking Update with the scientific notation value triggers "Invalid Conversion Factor" validation. The record becomes permanently uneditable because the original value is lost. |

### Low (1)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#2** | Conversion Factor input uses `type='character'` instead of `type='number'` | 1. Inspect the Conversion Factor input element. 2. Observe `type="character"` attribute. | Input should use `type='number'` for native browser validation, numeric keyboard on mobile, and HTML5 min/max/step attributes. | Input uses `type='character'`. The browser provides no native number validation. All numeric validation is backend-only. On mobile devices, users get a text keyboard instead of a numeric keyboard. |

### Bug Impact on Tests

| Test | Bug | Impact |
|------|-----|--------|
| Test 8 (text in factor) | Bug #2 | Pattern A rejects — test passes but documents poor UX |
| Test 9 (special chars in factor) | Bug #2 | Pattern A rejects — test passes but documents poor UX |
| Test 12 (21-digit factor) | Bug #1 boundary | Accepted — saves correctly, establishes boundary |
| Test 13 (22-digit factor) | Bug #1 | Saves but displays as 1e+22 on re-edit — test confirms the bug |
| Test 14 (re-edit 22-digit record) | Bug #1 | Update fails with "Invalid Conversion Factor" — test confirms permanent uneditability |

---

## 12. Test Case Inventory (22 Tests)

### Group A — Happy Path (Add) — Tests 1-3

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| Test 1 | Add valid UOM Conversion with integer factor | Success alert + record created via `create_fresh_record()` | — |
| Test 2 | Add with decimal Conversion Factor | Pattern A — decimals rejected | — |
| Test 3 | Same Source and Target UOM (Fest → Fest) with factor=1 | **OBSERVE** — may succeed or reject | — |

### Group B — Validation (Add) — Tests 4-11

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| Test 4 | Empty Source UOM | Pattern A + `mat-mdc-select-invalid` on Source UOM + form stays open | — |
| Test 5 | Empty Target UOM | Pattern A + `mat-mdc-select-invalid` on Target UOM + form stays open | — |
| Test 6 | Empty Conversion Factor | Pattern A + `mat-error` under Factor + form stays open | — |
| Test 7 | All fields empty | Pattern A + errors on all 3 fields + form stays open | — |
| Test 8 | Text in Conversion Factor ("abc") | Pattern A + `mat-error`: "Invalid Conversion Factor" | Bug #2 (low) |
| Test 9 | Special chars in Factor ("@#$%") | Pattern A + `mat-error` | Bug #2 (low) |
| Test 10 | Negative Conversion Factor ("-5") | **OBSERVE** — accepted or rejected? | — |
| Test 11 | Zero Conversion Factor ("0") | **OBSERVE** — accepted or rejected? | — |

### Group C — Boundary/Bug — Tests 12-14

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| Test 12 | 21-digit Conversion Factor | Accepted + saves correctly | — |
| Test 13 | 22-digit Conversion Factor | **BUG** — saves but displays as 1e+22 on re-edit | Bug #1 (high) |
| Test 14 | Re-edit of 22-digit record | Update fails — "Invalid Conversion Factor" — record permanently uneditable | Bug #1 (high) |

### Group D — Edit Flow — Tests 15-18

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| Test 15 | Edit valid Conversion Factor | Success + factor updated in table | — |
| Test 16 | Edit — clear Conversion Factor | Pattern A + `mat-error` on Factor | — |
| Test 17 | View popup — read-only | All fields disabled (dropdowns + input) | — |
| Test 18 | Cancel edit — no changes saved | Original factor unchanged in table | — |

### Group E — History — Tests 19-20

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| Test 19 | History shows record | History popup has at least 1 row | — |
| Test 20 | History close button | Cancel closes popup + table visible | — |

### Group F — Cancel Flow — Tests 21-22

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| Test 21 | Cancel Add form — no record created | Row count unchanged | — |
| Test 22 | Cancel Edit form — changes not saved | Original factor unchanged in table | — |

---

## 13. How to Run the Tests

### Prerequisites

```bash
pip install selenium pytest pytest-html openpyxl python-dotenv
```

Make sure **ChromeDriver** matches your Chrome version.

### Run All 22 Tests

```bash
pytest pages/common_settings/modules/uom_conversion/test/test_uom_conversion_validation.py -v --tb=short
```

**Expected output**: `22 passed`

### Run by Test Group

| Group | Command | Tests |
|-------|---------|-------|
| Happy Path | `pytest ... -v -k "test_add_valid or test_add_decimal or test_add_same_source" --tb=short` | Tests 1-3 |
| Validation | `pytest ... -v -k "test_add_without or test_add_all_fields or test_add_text or test_add_special or test_add_negative or test_add_zero" --tb=short` | Tests 4-11 |
| Boundary/Bug | `pytest ... -v -k "test_conversion_factor_21 or test_conversion_factor_22 or test_scientific" --tb=short` | Tests 12-14 |
| Edit Flow | `pytest ... -v -k "test_edit_valid or test_edit_clear or test_edit_source_uom_disabled or test_cancel_edit_no" --tb=short` | Tests 15-18 |
| History | `pytest ... -v -k "test_history" --tb=short` | Tests 19-20 |
| Cancel Flow | `pytest ... -v -k "test_cancel_add or test_cancel_edit_form" --tb=short` | Tests 21-22 |

### Run a Single Test

```bash
pytest pages/common_settings/modules/uom_conversion/test/test_uom_conversion_validation.py -v -k "test_add_valid" --tb=short
```

### Run Only Bug-Related Tests

```bash
pytest pages/common_settings/modules/uom_conversion/test/test_uom_conversion_validation.py -v -k "test_conversion_factor_22 or test_scientific" --tb=short
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
pages/common_settings/modules/uom_conversion/reports/CommonSettings_Report_YYYYMMDD_HHMMSS.xlsx
```

The report includes: test names, pass/fail status, step-by-step logs, error messages, and the 2 known issues list.

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
|              UOM CONVERSION — QUICK REFERENCE                    |
+-----------------------------------------------------------------+
|                                                                 |
|  SCREEN:  Common Settings > UOM Conversion                      |
|  URL:     .../#/dynamic-screens/UOM%20Conversion                |
|  APP:     Angular Material MDC + SweetAlert2 (3 patterns!)      |
|                                                                 |
|  FORM FIELDS:                                                   |
|    Source UOM* (mat-select dropdown with search)                |
|    Target UOM* (mat-select dropdown with search)                |
|    Conversion Factor* (type="character" — should be "number"!)  |
|                                                                 |
|  TABLE COLUMNS:                                                 |
|    View | Edit | History(archive!) | Source | Target | Factor   |
|                                                                 |
|  2 BUGS:  1 High | 0 Medium | 1 Low                            |
|  WORST:   22+ digit factor = scientific notation = uneditable   |
|           type="character" on numeric field (Low)                |
|                                                                 |
|  SWEETALERT2 PATTERNS:                                          |
|    Pattern A: "Validation Failed" — click .swal2-confirm        |
|    Pattern B: "Fields validation failed" — click .swal2-cancel! |
|    Pattern C: "Failed to save record" — wait auto-dismiss       |
|                                                                 |
|  DROPDOWN HANDLING (5-step pure JS flow):                       |
|    1. Click .mat-mdc-select-trigger (find by mat-label text)    |
|    2. Wait for .mat-mdc-select-panel to appear                  |
|    3. Type in .search-container input (nativeInputValueSetter)  |
|    4. Click matching mat-option (.mdc-list-item__primary-text)  |
|    5. Cleanup CDK overlays (_force_close_panels)                |
|                                                                 |
|  DYNAMIC PAIR GENERATION:                                       |
|    create_fresh_record() — 10-step one-flow                     |
|    1. Read existing pairs from table                            |
|    2. Open Add form (once)                                      |
|    3. Open Source dropdown, read all options                    |
|    4. Pick fresh (source, target) pair not in existing set      |
|    5. Select source from ALREADY OPEN dropdown                  |
|    6. Select target via normal 5-step flow                      |
|    7. Fill factor + submit + handle alert                       |
|                                                                 |
|  CONVERSION FACTOR VALIDATION:                                  |
|    Accepts:  Integers (1-21 digits)                             |
|    Rejects:  decimals, text, special chars, empty               |
|    Bug:      22+ digits = scientific notation (uneditable)      |
|    Bug:      type="character" instead of type="number"          |
|    Observe:  negative, zero — accepted or rejected varies       |
|                                                                 |
|  DROPDOWN ERROR DETECTION:                                      |
|    is_dropdown_error() checks:                                  |
|      - mat-mdc-select-invalid on mat-select                     |
|      - ng-invalid on mat-select                                 |
|                                                                 |
|  KEY GOTCHAS:                                                   |
|    x NEVER click .swal2-confirm on Pattern B (downloads file!)  |
|    x NEVER use Keys.ESCAPE (corrupts Angular state)             |
|    x History column CSS = "archive" not "history"               |
|    x 22+ digit factor SAVES but becomes UNEDITABLE              |
|    x type="character" on numeric input (no native validation)   |
|    x Dropdown uses MDC (.mat-mdc-select-trigger/panel)          |
|    x Must use nativeInputValueSetter for dropdown search        |
|    x Always cleanup CDK overlays after dropdown selection       |
|    x Row identified by (Source, Target) pair, not single code  |
|    x create_fresh_record() leaves Source dropdown OPEN          |
|    CHECK ALWAYS use JS clicks for Angular Material              |
|    CHECK ALWAYS driver.refresh() after navigate                 |
|    CHECK ALWAYS search before Edit/History                      |
|    CHECK Pattern B: click CANCEL, not confirm                   |
|    CHECK Pattern C: wait for auto-dismiss (3-6s)                |
|    CHECK get_mat_error_text() uses label-based mat-field query  |
|    CHECK is_dropdown_error() checks 2 CSS classes               |
|    CHECK verify_view_popup_read_only() checks all inputs        |
|                                                                 |
|  RUN ALL:  pytest ... -v --tb=short                             |
|  RUN ONE:  pytest ... -v -k "test_13" --tb=short               |
|  REPORT:   .../reports/CommonSettings_Report_*.xlsx             |
+-----------------------------------------------------------------+
```

---

*Last Updated: 15-May-2026 | UOM Conversion Screen Knowledge Document | 22/22 Tests Passing*
