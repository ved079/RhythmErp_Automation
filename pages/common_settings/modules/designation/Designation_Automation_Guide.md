# Designation — Screen Knowledge Document

> **RhythmERP** | Common Settings > Designation  
> **Last Verified**: 14-May-2026 | **44/44 Tests Passing**

---

## 1. Screen Overview

**Designation** is a master data screen in RhythmERP under **Common Settings**. It manages designation records — each designation has a Name, an optional Description, and a Status (Active/Inactive toggle). This screen is simpler than Vehicle Master: only 3 fields, no dropdowns, and Status is a toggle switch instead of a dropdown.

| Detail | Value |
|--------|-------|
| **Navigation** | Sidebar → Common Settings → Designation |
| **URL** | `https://rhythmerp.algorhythms.in/#/dynamic-screens/Designation` |
| **Framework** | Angular Material (mat-form-field, mat-error, mat-table) |
| **Alerts** | SweetAlert2 (swal2-title, swal2-confirm) |
| **Validation** | Name is required + pattern validation ("Invalid Name" mat-error). Description optional. |
| **Known Bugs** | 8 (1 Critical, 2 High, 2 Medium, 3 Low) |

### Key Differences from Vehicle Master

| Aspect | Vehicle Master | Designation |
|--------|---------------|-------------|
| **Fields** | 5 (Name, Price, Vehicle Type, Fuel Type, Description) | 3 (Name, Description, Status) |
| **Dropdowns** | 2 mat-select dropdowns | **None** |
| **Status** | N/A | **Toggle switch** (Active/Inactive) |
| **Inline Errors** | None (only SweetAlert2) | **Yes** — "Invalid Name" mat-error |
| **Name Validation** | No pattern check | `type="character"` — letters & spaces only |
| **Price Field** | Present | **N/A** |
| **Table Status Column** | N/A | Yes — Active/Inactive |

### What You Can Do on This Screen

- **Create** a new designation via ADD button → popup form → Submit
- **Edit** an existing designation via row Edit button → popup form → Update
- **View** a designation's details (read-only) via row View button
- **Search** designations by name via toolbar search bar
- **Filter** designations via Filter panel (BROKEN — Apply Filters does nothing)
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
| **ADD** | + (plus) icon | `div[mattooltip='ADD'] button` | Opens Create form popup. **Tooltip is on parent div, not button.** |
| **Filter** | filter_list icon | `button.filter-btn` | Opens right-side filter panel. **BROKEN — Apply Filters non-functional.** |
| **Refresh** | refresh icon | Find by mat-icon text "refresh" | Refreshes table data. |
| **More** | vertical dots | `button[mattooltip='More']` | Opens menu (Export to Excel, etc.) |

### Search Bar (Hidden by Default)

After clicking the Search toggle, an input bar appears:

| Element | Selector | Notes |
|---------|----------|-------|
| Search Input | `input#erpSearchInput` | Stable ID. Hidden by default. |
| Search Behavior | Type text → press Enter | Filters table by Name. Partial match supported. |

### Table

```
+------+------+---------+--------+-------------+--------+
| View | Edit | History |  Name  | Description | Status |
|  btn |  btn |   btn   |        |             |        |
+------+------+---------+--------+-------------+--------+
|  btn |  btn |   btn   |  CEO   |  Chief...   | Active |
|  btn |  btn |   btn   |  CFO   |             | Inactive|
+------+------+---------+--------+-------------+--------+
```

| Column | CSS Class | Sortable? | Notes |
|--------|-----------|-----------|-------|
| View | `mat-column-view` | No | Action button column |
| Edit | `mat-column-edit` | No | Action button column. Has `mattooltip="Click to edit"` |
| **History** | **`mat-column-archive`** | No | **CRITICAL: CSS class is "archive" NOT "history"!** |
| Name | `mat-column-name` | Yes | Sort header present |
| Description | `mat-column-description` | Yes | May be empty |
| Status | `mat-column-status` | Yes | Shows "Active" or "Inactive" |

### Table Selectors

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| All rows | `table#excel-table tbody tr` |
| Name cells | `td.cdk-column-name` or `td.mat-column-name` |
| Description cells | `td.cdk-column-description` or `td.mat-column-description` |
| Status cells | `td.cdk-column-status` or `td.mat-column-status` |
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
+---------------------------------------------+
|  Designation            [Full] [X]           |  <- Header (.popup-header)
+---------------------------------------------+
|                                             |
|  Name *            [________________]       |  <- type="character" input
|  Description       [________________]       |  <- text input (optional)
|  Status            [=====O]  Active         |  <- Toggle switch
|                                             |
+---------------------------------------------+
|              [Cancel]  [Submit/Update]       |  <- Footer (.popup-footer)
+---------------------------------------------+
```

### Field Catalog (3 Fields)

| Field | Type | Required | Selector | Behavior |
|-------|------|----------|----------|----------|
| **Name** | text input | YES | `input[name='Name']` | `type="character"`. Only letters & spaces allowed. Rejects digits, punctuation, special chars. Shows "Invalid Name" mat-error. No max length. No trimming. |
| **Description** | text input | NO | `input[name='Description']` | Optional. Can be left empty. Accepts any characters (no validation). |
| **Status** | toggle switch | NO (defaults Active) | `.switch-wrapper .slider` | Toggle between Active/Inactive. Default is Active (checked). Uses `input[type='checkbox']` internally. |

### Status Toggle Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Toggle slider | `.switch-wrapper .slider` | JS click required. Normal click may fail. |
| Checkbox | `.switch-wrapper input[type='checkbox']` | `is_selected()` or `get_property('checked')` for state. |
| State label | `.switch-wrapper .state-label.on` | Has "active" class when Active. |
| Toggle container | `//span[contains(@class,'main-label') and text()='Status']/ancestor::div[contains(@class,'switch-container')]` | Used for has_field_error() XPath. |

### Field State Comparison

| Field | Add Mode | Edit Mode | View Mode |
|-------|----------|-----------|-----------|
| Name | Enabled, Empty | Enabled, Pre-filled | **Disabled**, Pre-filled |
| Description | Enabled, Empty | Enabled, Pre-filled/Empty | **Disabled**, Pre-filled/Empty |
| Status | **Active (checked)** | Pre-selected | **Disabled**, Pre-selected |
| **Submit button** | **Present** | — | **ABSENT** |
| **Update button** | — | **Present** | **ABSENT** |
| **Cancel button** | Present | Present | Present (only button) |

### Popup Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Popup container | `.big-model` | _is_form_popup_open() checks this |
| Popup header | `.popup-header` | Contains title + X button |
| Popup title | `.big-model h3` | Text: "Designation" |
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

## 4. Name Validation (type="character")

The Name field uses Angular's `type="character"` attribute. This is the most important behavioral difference from Vehicle Master. Understanding what it does and does not allow is critical for automation.

### What `type="character"` Does

The `type="character"` attribute is an Angular directive that restricts input to **letters and spaces only**. It silently strips or rejects characters that don't match the pattern. When invalid content is detected, Angular shows a **"Invalid Name" mat-error** inline below the Name field.

### Accepted Characters

| Category | Examples | Accepted? |
|----------|----------|-----------|
| Uppercase letters | A-Z | YES |
| Lowercase letters | a-z | YES |
| Spaces | " " | YES |
| Digits | 0-9 | **NO** — rejected |
| Underscores | _ | **NO** — rejected |
| Special chars | @#$%^&*! | **NO** — rejected |
| **Punctuation** | **. , - ( )** | **NO — rejected** (product limitation) |

### Product Limitation: Punctuation Rejected

This is a significant product limitation. Common designation names like "Jr. Manager", "Manager, Sales", "Vice-President", and "Quality (Agri)" are **all rejected** with "Invalid Name". While the regex in the codebase (`^[a-zA-Z\s\.\,\-\(\)]+$`) technically accounts for these characters, the ERP's `type="character"` directive does not allow them in practice.

### The 4-Tier `get_mat_error_text()` Approach

Because Angular's `type="character"` can silently strip values without always marking the FormControl as invalid, the `get_mat_error_text()` method uses a 4-tier fallback approach:

| Tier | Strategy | When It Triggers |
|------|----------|-----------------|
| **1** | Look for visible `mat-error` elements in DOM | Standard case — Angular shows the error |
| **2** | Check Angular FormControl `ng-invalid` class | Angular marks control invalid but no visible mat-error yet |
| **3** | Compare intended value vs actual DOM value | Angular silently stripped the value (e.g., "12345" → "") |
| **4** | Direct DOM value regex validation | Spaces-only or invalid chars even when Angular says `ng-valid` |

### The `_intended_values` Tracking Mechanism

`_set_angular_input()` stores what value it **tried** to set in `self._intended_values = {'Name': '12345'}`. When `get_mat_error_text()` runs Tier 3, it compares the intended value against the actual DOM `value` attribute. If they differ (because Angular stripped the input), the method correctly identifies the field as invalid.

---

## 5. Status Toggle Switch

The Designation screen uses a **toggle switch** for Status instead of a dropdown. This is unique compared to Vehicle Master which has no Status field at all.

### Toggle Behavior

| State | Checkbox | Slider Position | Display Text |
|-------|----------|----------------|--------------|
| **Active** | `checked=true` | Right | "Active" |
| **Inactive** | `checked=false` | Left | "Inactive" |
| **Default (Add)** | Active (checked) | Right | "Active" |

### How to Read Toggle State

```python
# Method: get_toggle_state()
# Returns True (Active) or False (Inactive)

# Strategy 1: Check checkbox (preferred)
checkboxes = driver.find_elements(By.CSS_SELECTOR, ".switch-wrapper input[type='checkbox']")
for cb in checkboxes:
    if cb.is_displayed():
        return cb.is_selected()  # True=Active, False=Inactive

# Strategy 2: Check "on active" state label
on_labels = driver.find_elements(By.CSS_SELECTOR, ".switch-wrapper .state-label.on")
for label in on_labels:
    if 'active' in label.get_attribute('class'):
        return True
```

### How to Toggle

```python
# Method: toggle_status()
# Clicks the .slider element via JS click
sliders = driver.find_elements(By.CSS_SELECTOR, ".switch-wrapper .slider")
for slider in sliders:
    wrapper = slider.find_element(By.XPATH, "./ancestor::div[contains(@class,'switch-wrapper')]")
    if wrapper.is_displayed():
        driver.execute_script("arguments[0].click();", slider)
```

### Key Rules for Toggle Automation

| Rule | Why |
|------|-----|
| **Use JS click** for `.slider` | Normal Selenium click may be intercepted by Angular overlay |
| **Always verify state after toggle** | `set_toggle_state()` checks if toggle actually changed and logs a warning if not |
| **Don't assume default** | Always call `get_toggle_state()` before toggling to avoid double-toggle |
| **View mode = disabled toggle** | In View mode, the toggle is non-interactive but still shows the correct state |

---

## 6. History Popup

### How to Open

Click the **History** button (3rd action button per row, clock icon) in the table. The popup opens as an overlay.

### Popup Structure

```
+-----------------------------------------------------+
|  Designation History              [Full] [X]         |  <- .popup-header
+-----------------------------------------------------+
|  [Search in table]  [Refresh] [More]                 |  <- Toolbar
+------+------+------------+-------+-------------+-----+
| View | Creation Time | Updated Time | Name  | Desc  |  <- Table
|  btn | 11 May 2026  | 11 May 2026  | ...   |  ...  |
+------+------+------------+-------+-------------+-----+
|                        [Cancel]                       |  <- .popup-footer
+-----------------------------------------------------+
```

### History Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| History popup | `h3.popup-title` (text contains "history") | `is_history_popup_open()` checks this |
| History title | `h3.popup-title` | Text: "Designation History" |
| History search input | `.popup-body input, .popup-content input` | **MUST press Enter — no auto-filter!** |
| History table | `.big-model table tbody tr, .popup-content table tbody tr` | May be empty — "No data available" |
| Cancel button | `.popup-footer button` (text="Cancel") | Close button text is "Cancel", NOT "Close" |
| X icon | `.popup-header button mat-icon` (text="close") | Same as form popup X icon |

### Important Findings

| Finding | Impact |
|---------|--------|
| **RhythmERP does NOT create history entries** on designation creation or edit | History popup shows "No data available" — 0 rows. Tests check popup opens, not row count. |
| **History search requires Enter key** | Typing alone does NOT filter. Must press Keys.RETURN after typing. |
| **History column CSS = "archive"** | The History action column uses class `mat-column-archive`, NOT `mat-column-history` or `cdk-column-history`. |

---

## 7. SweetAlert2 Messages

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

**Triggers**: Empty Name, Name with invalid characters (special chars, digits, punctuation) on Submit/Update.

### Success — Record Added (Toast)

Appears after successful designation creation.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-container` | Top-right toast |
| Success icon | `.swal2-icon.swal2-success` | Green checkmark |
| Title | `#swal2-title` | "Your record has been added successfully!" |
| OK button | `.swal2-confirm` | Auto-dismisses after ~3 seconds if not clicked |

### Success — Record Updated (Toast)

Appears after successful designation edit.

| Element | Selector | Content |
|---------|----------|---------|
| Title | `#swal2-title` | "Your record has been updated successfully!" |

### Inline Validation (mat-error) — Unique to Designation

Unlike Vehicle Master, Designation **does show** per-field inline error messages. When the Name field contains invalid characters:

| Element | Selector | Content |
|---------|----------|---------|
| Error element | `mat-error` (inside mat-form-field) | "Invalid Name" |
| Invalid class on input | `ng-invalid` + `ng-touched` | Angular FormControl classes |

**Triggers**: Spaces-only name, digits-only name, special characters, punctuation, mixed invalid content.

### Key Notes for Automation

- **SweetAlert2 confirm button needs JS click** — direct Selenium click often fails due to z-index layering
- **Success toast auto-dismisses** after ~3 seconds. Automation must either click the confirm button quickly or wait for the container to disappear
- **Leftover swal2-container elements** can block subsequent actions — must be JS-removed after handling
- **Both inline mat-error AND SweetAlert2 can appear together** — Submit with an invalid Name triggers both the inline "Invalid Name" and the SweetAlert2 "Validation Failed"

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
| Description Cell | `td.cdk-column-description` or `td.mat-column-description` |
| Status Cell | `td.cdk-column-status` or `td.mat-column-status` |
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
| Description Input | `input[name='Description']` |
| Status Toggle Slider | `.switch-wrapper .slider` |
| Status Checkbox | `.switch-wrapper input[type='checkbox']` |
| Status Label | `.switch-wrapper .state-label.on` |
| Submit Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]` |
| Update Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]` |
| Cancel Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]` |
| X Close Icon | `.popup-header button mat-icon` where text = "close" |
| Inline Error | `mat-error` (inside mat-form-field) |

### History Popup

| Element | Selector |
|---------|----------|
| History Open Check | `h3.popup-title` where text contains "history" |
| History Title | `h3.popup-title` — text: "Designation History" |
| History Table Rows | `.big-model table tbody tr, .popup-content table tbody tr` |
| History Search Input | `.popup-body input, .popup-content input` |
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

---

## 9. Validation Matrix

### What IS Validated

| # | Validation | Trigger | What Happens |
|---|-----------|---------|-------------|
| 1 | Name required | Submit/Update with empty Name | SweetAlert2: "Validation Failed — Please correct the highlighted fields". Form stays open. |
| 2 | Name pattern (type="character") | Invalid characters entered in Name | Inline mat-error: "Invalid Name". Also SweetAlert2 on Submit. |
| 3 | Description optional | Submit with empty Description | No error. Record created. |
| 4 | Status defaults to Active | Open Add form | Toggle is checked (Active) by default. |

### Name Validation Details

| Input | Valid? | Error Shown | Tier That Catches It |
|-------|--------|-------------|---------------------|
| `"Manager"` | YES | None | — |
| `"Senior Manager"` | YES | None | — |
| `"     "` (spaces only) | NO | "Invalid Name" | Tier 4 (spaces-only) |
| `"12345"` (digits) | NO | "Invalid Name" | Tier 3 (value stripped) |
| `"Test@Name"` (special chars) | NO | "Invalid Name" | Tier 1 (mat-error) |
| `"Jr. Manager"` (punctuation) | NO | "Invalid Name" | Tier 1 (mat-error) |
| `""` (empty) | NO | "Validation Failed" | SweetAlert2 (no inline) |

### What is NOT Validated (Gaps = Bugs)

| # | Missing Validation | What Should Happen | What Actually Happens | Severity |
|---|-------------------|--------------------|-----------------------|----------|
| 1 | Apply Filters non-functional | Filter table rows | Nothing happens. No request sent. Zero effect. | **CRITICAL** |
| 2 | Duplicate Name allowed (Create) | Error: "Name already exists" | Second designation created. No warning. | **HIGH** |
| 3 | Duplicate Name allowed (Edit) | Error: "Name already exists" | Edit succeeds. Two designations with same Name. | **HIGH** |
| 4 | Punctuation rejected in Name | Accept `. , - ( )` as valid | `type="character"` rejects all punctuation | **MEDIUM** (product limitation) |
| 5 | Spaces not trimmed in Name | Trim leading/trailing spaces | Stores "  Name  " with spaces | **MEDIUM** |
| 6 | No Name max length | Restrict at 255 chars | Accepts 256+ chars | **LOW** |
| 7 | No Description max length | Restrict at some limit | Accepts 500+ chars | **LOW** |
| 8 | No history entries created | At least 1 history row (creation event) | 0 rows. "No data available". | **LOW** |

---

## 10. Bug Registry (8 Bugs)

### Critical (1)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#1** | Apply Filters completely non-functional | 1. Click Filter button. 2. Select any filter category. 3. Click "Apply Filters". | Table filters to matching rows. | Nothing happens. No request sent. Zero effect. |

### High (2)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#2** | Duplicate Name allowed (Create) | 1. Create designation "CEO". 2. Create another designation "CEO". | Error: "Name already exists". | Second designation created. No warning. |
| **#3** | Duplicate Name allowed (Edit) | 1. Edit a designation. 2. Change its Name to another existing designation's Name. | Error: "Name already exists". | Edit succeeds. Two designations with same Name. |

### Medium (2)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#4** | Punctuation rejected in Name | 1. Create designation. 2. Enter Name "Jr. Manager" or "Vice-President". 3. Submit. | Accept common punctuation in designation names. | "Invalid Name" error — `type="character"` rejects `. , - ( )`. Product limitation. |
| **#5** | Spaces not trimmed in Name | 1. Create designation. 2. Enter Name "  SpaceTest  ". 3. Submit. | Name trimmed to "SpaceTest". | Name stored as "  SpaceTest  " with spaces. |

### Low (3)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#6** | No Name max length | 1. Create designation. 2. Enter Name with 256+ characters. 3. Submit. | Error: "Name too long" or truncate. | Name accepted without limit. |
| **#7** | No Description max length | 1. Create designation. 2. Enter Description with 500+ characters. 3. Submit. | Error: "Description too long" or truncate. | Description accepted without limit. |
| **#8** | No history entries created | 1. Create a designation. 2. Open History. | At least 1 history row (creation event). | 0 rows. "No data available". |

---

## 11. Test Case Inventory (44 Tests)

### Phase 1: Create Form Validations (C01-C15)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| C01 | Submit with all fields empty | SweetAlert2 "Validation Failed" | — |
| C02 | Submit with only Name filled | Success (Description optional, Status defaults Active) | — |
| C03 | Name with leading/trailing spaces | Either accepted (BUG) or pattern validation | BUG #5 |
| C04 | Name with spaces only | "Invalid Name" mat-error | — |
| C05 | Name with special chars @#$%^&* | "Invalid Name" mat-error + SweetAlert2 | — |
| C06 | Name with digits only | "Invalid Name" mat-error | — |
| C07 | Name with mixed valid+invalid (Test@Name) | "Invalid Name" mat-error | — |
| C08 | Duplicate Name (Create) | BUG: accepted without warning | BUG #2 |
| C09 | 256-character Name | BUG: no max length validation | BUG #6 |
| C10 | Name with punctuation (. , - ( )) | "Invalid Name" — type="character" rejects | BUG #4 |
| C11 | Only Description filled (no Name) | SweetAlert2 "Validation Failed" | — |
| C12 | Special chars in Description | Accepted (no validation on Description) | — |
| C13 | Very long Description (500 chars) | Accepted (no max length) | BUG #7 |
| C14 | Inline mat-error messages visible | "Invalid Name" shown below Name field | — |
| C15 | 255-character valid Name | Success (boundary test) | — |

### Phase 2: Status Toggle Validations (S01-S06)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| S01 | Default Status is Active | Toggle checked, display text "Active" | — |
| S02 | Toggle to Inactive | Toggle unchecked, display text "Inactive" | — |
| S03 | Create with Inactive status | Success + "Inactive" shown in table | — |
| S04 | Toggle state in Edit mode | Pre-populated correctly, can toggle | — |
| S05 | Toggle disabled in View mode | View mode: no Submit/Update, inputs disabled | — |
| S06 | Toggle back and forth (4x) | State consistent after each toggle | — |

### Phase 3: Edit Form Validations (E01-E05)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| E01 | Edit with duplicate Name | BUG: accepted without warning | BUG #3 |
| E02 | Edit with special chars Name | "Invalid Name" mat-error | — |
| E03 | Edit pre-populated fields | Name/Description/Status match created data | — |
| E04 | Edit with digits-only Name | "Invalid Name" mat-error | — |
| E05 | Edit change Status Active → Inactive | Success + "Inactive" in table after refresh | — |

### Phase 4: Search & Filter (F01-F05)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| F01 | Search exact match | Found in table | — |
| F02 | Search partial match | Found in table | — |
| F03 | Search non-existent name | Not found (0 results) | — |
| F04 | Filter panel opens | Panel visible after Filter button click | — |
| F05 | Apply Filters button | BUG: no effect | BUG #1 |

### Phase 5: Popup UI Behaviors (P01-P05)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| P01 | Add form Cancel | Form opens then closes | — |
| P02 | Add form close via X | Form closes | — |
| P03 | View popup read-only | Inputs disabled, no Submit/Update | — |
| P04 | Edit popup has Update (not Submit) | Update visible, Submit absent | — |
| P05 | Inline error keeps form open | "Invalid Name" + Submit = form stays open | — |

### Phase 6: History Validations (H01-H08)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| H01 | History popup opens | Popup visible | — |
| H02 | History shows no data | 0 rows (RhythmERP doesn't create entries) | BUG #8 |
| H03 | History close via Cancel | Popup closes | — |
| H04 | History close via X | Popup closes | — |
| H05 | History search input exists | Search input visible in popup | — |
| H06 | History search requires Enter | Must press Enter to filter | — |
| H07 | History search no match | No results for non-existent term | — |
| H08 | History table columns present | Correct column headers visible | — |

---

## 12. How to Run the Tests

### Prerequisites

```bash
pip install selenium pytest pytest-html openpyxl python-dotenv
```

Make sure **ChromeDriver** matches your Chrome version.

### Run All 44 Tests

```bash
pytest pages/common_settings/modules/designation/test/test_designation_validation.py -v --tb=short
```

**Expected output**: `44 passed`

### Run by Phase

| Phase | Command | Tests |
|-------|---------|-------|
| Create Validations | `pytest ... -v -k "TestCreateForm" --tb=short` | C01-C15 |
| Status Toggle | `pytest ... -v -k "TestStatusToggle" --tb=short` | S01-S06 |
| Edit Validations | `pytest ... -v -k "TestEditForm" --tb=short` | E01-E05 |
| Search & Filter | `pytest ... -v -k "TestSearchFilter" --tb=short` | F01-F05 |
| Popup & UI | `pytest ... -v -k "TestPopupUI" --tb=short` | P01-P05 |
| History | `pytest ... -v -k "TestHistory" --tb=short` | H01-H08 |

*(Replace `...` with the full path shown above)*

### Run a Single Test

```bash
pytest pages/common_settings/modules/designation/test/test_designation_validation.py -v -k "test_C04" --tb=short
```

### Run Only Failed Tests

```bash
pytest pages/common_settings/modules/designation/test/test_designation_validation.py -v -k "test_C01 or test_C10" --tb=short
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
pages/common_settings/modules/designation/reports/CommonSettings_Report_YYYYMMDD_HHMMSS.xlsx
```

The report includes: test names, pass/fail status, step-by-step logs, error messages, and the known issues list.

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
|              DESIGNATION — QUICK REFERENCE                       |
+-----------------------------------------------------------------+
|                                                                 |
|  SCREEN:  Common Settings > Designation                         |
|  URL:     .../#/dynamic-screens/Designation                     |
|  APP:     Angular Material + SweetAlert2                        |
|                                                                 |
|  FORM FIELDS:                                                   |
|    Name* (type="character"!) | Description (optional)           |
|    Status (toggle switch, default=Active)                       |
|                                                                 |
|  TABLE COLUMNS:                                                 |
|    View | Edit | History(archive!) | Name | Description | Status|
|                                                                 |
|  8 BUGS:  1 Critical | 2 High | 2 Medium | 3 Low               |
|  WORST:    Apply Filters does NOTHING (Critical)                |
|            Duplicate Name allowed (High x2)                     |
|            Punctuation rejected in Name (Medium, product limit) |
|                                                                 |
|  NAME VALIDATION (type="character"):                            |
|    Accepts:  A-Z a-z spaces ONLY                                |
|    Rejects:  digits, punctuation, special chars, underscores    |
|    Error:    "Invalid Name" (mat-error inline)                  |
|                                                                 |
|  STATUS TOGGLE:                                                 |
|    Selector: .switch-wrapper .slider (JS click!)                |
|    Default:  Active (checked)                                   |
|    State:    .switch-wrapper input[type='checkbox'].is_selected()|
|                                                                 |
|  KEY GOTCHAS:                                                   |
|    x NEVER use Keys.ESCAPE                                      |
|    x NEVER hardcode dropdown options                            |
|    x History column CSS = "archive" not "history"               |
|    x type="character" rejects punctuation (. , - ( ))           |
|    x Punctuation = "Invalid Name" (product limitation)          |
|    CHECK ALWAYS use JS clicks for Angular Material              |
|    CHECK ALWAYS driver.refresh() after navigate                 |
|    CHECK ALWAYS search before Edit/History                      |
|    CHECK ALWAYS use contains(@class,'popup-footer') not exact   |
|    CHECK ALWAYS use _set_angular_input() for Name field         |
|    CHECK ALWAYS use .slider (JS click) for toggle               |
|    CHECK History search REQUIRES Enter key                      |
|    CHECK get_mat_error_text() uses 4-tier fallback              |
|                                                                 |
|  RUN ALL:  pytest ... -v --tb=short                             |
|  RUN ONE:  pytest ... -v -k "test_C04" --tb=short              |
|  REPORT:   .../reports/CommonSettings_Report_*.xlsx             |
+-----------------------------------------------------------------+
```

---

*Last Updated: 14-May-2026 | Designation Screen Knowledge Document | 44/44 Tests Passing*
