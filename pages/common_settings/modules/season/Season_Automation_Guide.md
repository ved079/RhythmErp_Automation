# Season — Screen Knowledge Document

> **RhythmERP** | Common Settings > Season  
> **Last Verified**: 18-May-2026 | **18/18 Tests Passing**

---

## 1. Screen Overview

**Season** is a master data screen in RhythmERP under **Common Settings**. It manages season records — each season has a Name, an optional Description, and a Status (Active/Inactive checkbox). This screen is significantly different from Designation in two critical ways: (1) the Name field has **no input validation** — it accepts SQL injection, XSS script tags, special characters, digits, and anything else without restriction, and (2) creating a record with a **duplicate Name causes the system to hang indefinitely** with no error message, no alert, and no recovery option other than manually closing the popup.

| Detail | Value |
|--------|-------|
| **Navigation** | Sidebar → Common Settings → Season |
| **URL** | `https://rhythmerp.algorhythms.in/#/dynamic-screens/Season` |
| **Framework** | Angular Material (mat-form-field, mat-table, mat-checkbox) |
| **Alerts** | SweetAlert2 (swal2-title, swal2-confirm) — both validation and success |
| **Validation** | Name is required only. No pattern, character, or length validation. Description optional. |
| **Known Bugs** | 4 (3 High, 1 Low) |

### Key Differences from Designation

| Aspect | Designation | Season |
|--------|-------------|--------|
| **Name Validation** | `type="character"` — letters & spaces only | **NONE** — accepts everything (SQL, XSS, special chars, digits) |
| **Duplicate Name** | Accepted with no warning (High bug) | **System HANGS indefinitely** (Critical — no response at all) |
| **Status Control** | Toggle switch (.switch-wrapper .slider) | **Angular Material checkbox** (input[type='checkbox']) |
| **Inline Errors** | "Invalid Name" mat-error visible | **None** — no per-field inline error messages |
| **Success Feedback** | SweetAlert2 toast auto-dismisses | SweetAlert2 toast auto-dismisses (same behavior) |
| **Search** | Standard Selenium approach | **JS atomic approach required** — input gets stale during animation |
| **History** | Shows "No data available" (bug) | **Only logs UPDATE events** — new records show "No data available" |
| **Popup Container** | `.big-model` | **`div.edit_pop_up`** — different class name |
| **Submit/Update Button** | Separate XPath locators | **Same `button[type='submit']`** for both — text changes in Edit mode |

### What You Can Do on This Screen

- **Create** a new season via ADD button → popup form → Submit
- **Edit** an existing season via row Edit button → popup form → Update
- **View** a season's details (read-only) via row View button
- **Search** seasons by name via toolbar search bar (JS atomic approach required)
- **Check History** of changes via row History button → history popup (only UPDATE events logged)

---

## 2. Screen Layout

### Toolbar (Top Bar)

```
+------------------------------------------------------------------+
|  [Search]  [+ ADD]  [Refresh]  [More]                            |
+------------------------------------------------------------------+
```

| Button | Icon | Selector | What It Does |
|--------|------|----------|-------------|
| **Search** | search icon | `button[aria-label='Search']` | Toggles search input bar. **CRITICAL: Input gets stale after toggle — must use JS atomic approach.** |
| **ADD** | + (plus) icon | `//button[mat-icon[text()='add']]` (primary) or `app-custom-header mat-icon` (fallback) | Opens Create form popup. Two locator strategies for reliability. |
| **Refresh** | refresh icon | `//button[mat-icon[text()='refresh']]` | Refreshes table data. Fallback: `navigate_to_season()` re-navigates. |
| **More** | vertical dots | — | Opens menu (Export to Excel, etc.) Not used in automation. |

**Note**: Unlike Designation, the Season screen does **NOT** have a Filter button or filter panel in the toolbar.

### Search Bar (Hidden by Default)

After clicking the Search toggle, an input bar appears:

| Element | Selector | Notes |
|---------|----------|-------|
| Search Input | `input#erpSearchInput` | **STALE ELEMENT RISK!** Angular destroys and recreates this input during the toggle animation. |

### The Search Stale Element Problem

This is the single most important technical challenge on the Season screen. The `search_record()` method uses a **JS atomic approach** to avoid `StaleElementReferenceException`:

| Step | What Happens | Why It's Needed |
|------|-------------|-----------------|
| 1 | JS opens search bar if needed | Pure JS — no Selenium element reference to go stale |
| 2 | JS waits for `#erpSearchInput` to appear in DOM | `WebDriverWait` for presence_of_element_located |
| 3 | JS clears + types + presses Enter in ONE `execute_script` call | **Atomic operation** — Angular can't destroy the element mid-operation |
| 4 | Selenium reads table rows after 2-second wait | DOM has settled by this point |

```python
# The JS atomic approach (simplified):
self.driver.execute_script("""
    var input = document.querySelector('#erpSearchInput');
    var nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
    ).set;
    nativeSetter.call(input, '');                    // Clear
    input.dispatchEvent(new Event('input', {bubbles: true}));
    nativeSetter.call(input, arguments[0]);          // Type
    input.dispatchEvent(new Event('input', {bubbles: true}));
    input.dispatchEvent(new KeyboardEvent('keydown', {
        key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
    }));
""", text)
```

### Table

```
+------+------+---------+--------+-------------+--------+
| View | Edit | History |  Name  | Description | Status |
|  btn |  btn |   btn   |        |             |        |
+------+------+---------+--------+-------------+--------+
|  btn |  btn |   btn   | Kharif |  Kharif...  | Active |
|  btn |  btn |   btn   |  Rabi  |             | Active |
+------+------+---------+--------+-------------+--------+
```

| Column | CSS Class | Sortable? | Notes |
|--------|-----------|-----------|-------|
| View | `tblActnBtn` (index-based) | No | Action button column |
| Edit | `tblActnBtn` (index-based) | No | Action button column |
| History | `tblActnBtn` (index-based) | No | Action button column |
| Name | Column 3 (0-based) | Yes | Primary identifier for the season |
| Description | Column 4 (0-based) | Yes | May be empty string |
| Status | Column 5 (0-based) | Yes | Shows "Active" or "Inactive" |

### Table Selectors

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| All rows | `table#excel-table tbody tr` |
| Name cells | `(//table[@id='excel-table']//tbody//tr)[{n}]/td[4]` |
| Description cells | `(//table[@id='excel-table']//tbody//tr)[{n}]/td[5]` |
| Status cells | `(//table[@id='excel-table']//tbody//tr)[{n}]/td[6]` |

### Row Action Buttons (Per Row)

| Action | Position | Selector Template | Formula |
|--------|----------|-------------------|---------|
| **View** | 1st button | `(//button[contains(@class,'tblActnBtn')])[{row*3+1}]` | Index-based positioning |
| **Edit** | 2nd button | `(//button[contains(@class,'tblActnBtn')])[{row*3+2}]` | Index-based positioning |
| **History** | 3rd button | `(//button[contains(@class,'tblActnBtn')])[{row*3+3}]` | Index-based positioning |

---

## 3. Add / Edit / View Form

All three modes use the **same popup container** — only the field states and footer buttons differ.

### Popup Structure

```
+---------------------------------------------+
|  Season                [Full] [X]            |  <- Header (.popup-header)
+---------------------------------------------+
|                                             |
|  Name *            [________________]       |  <- standard text input
|  Description       [________________]       |  <- text input (optional)
|  Status            [v]  Active              |  <- Angular Material checkbox
|                                             |
+---------------------------------------------+
|              [Cancel]  [Submit/Update]       |  <- Footer (.popup-footer)
+---------------------------------------------+
```

### Field Catalog (3 Fields)

| Field | Type | Required | Selector | Behavior |
|-------|------|----------|----------|----------|
| **Name** | text input | YES | `input[name='Name']` | Standard text input. **NO type="character" restriction**. Accepts ALL input: special characters, SQL injection, XSS script tags, digits, punctuation, spaces. No max-length. No trimming. No sanitization. This is a **SECURITY CONCERN**. |
| **Description** | text input | NO | `input[name='Description']` | Optional. Can be left empty. Accepts any characters (no validation). No max-length. |
| **Status** | Angular Material checkbox | NO (defaults Active) | `div.edit_pop_up input[type='checkbox']` | Standard Angular Material checkbox. Default is Active (checked). Uses standard `is_selected()` for state reading. Unlike Designation's toggle switch, this is a simple checkbox. |

### Status Checkbox Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Checkbox | `div.edit_pop_up input[type='checkbox']` | `is_selected()` returns True (Active) or False (Inactive). Standard Selenium checkbox. |

### Field State Comparison

| Field | Add Mode | Edit Mode | View Mode |
|-------|----------|-----------|-----------|
| Name | Enabled, Empty | Enabled, Pre-filled | **Disabled**, Pre-filled |
| Description | Enabled, Empty | Enabled, Pre-filled/Empty | **Disabled**, Pre-filled/Empty |
| Status | **Active (checked)** | Pre-selected | **Disabled**, Pre-selected |
| **Submit button** | **Present** | — | **ABSENT** |
| **Update button** | — | **Present** (same button, text changes) | **ABSENT** |
| **Cancel button** | Present | Present | Present (only button) |

### Popup Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Popup container | `div.edit_pop_up` | `is_form_open()` checks this |
| Popup header | `.popup-header` | Contains title + X button |
| Popup title | `div.edit_pop_up .popup-header h3` | Text: "Season" |
| Close (X) button | `//div[@class='popup-actions']//button[contains(.,'close')]` | Found by text 'close' in popup-actions |
| Fullscreen button | `//div[@class='popup-actions']//button[contains(.,'fullscreen')]` | Not used in automation |
| Popup footer | `div.popup-footer` | Contains Submit/Update and Cancel buttons |
| Submit (Add) | `div.popup-footer button[type='submit']` | In Add mode, text is "Submit" |
| Update (Edit) | `div.popup-footer button[type='submit']` | **SAME locator** — in Edit mode, text changes to "Update" |
| Cancel | `div.popup-footer button[type='button']` | `type='button'` attribute distinguishes from Submit |

### How to Detect Current Mode

```
Add Mode:    Submit button visible (type='submit') + fields enabled + empty fields
Edit Mode:   Same button visible (text='Update') + fields enabled + pre-filled
View Mode:   No Submit/Update button + all fields disabled + Cancel only
```

**Important**: Unlike Designation where Submit and Update have separate XPath locators, Season uses the **same `button[type='submit']`** for both. The button text changes automatically between "Submit" and "Update" depending on the mode. The `click_update()` method literally calls `self.click(self.SUBMIT_BUTTON)` — same locator as `click_submit()`.

---

## 4. Name Validation (or Lack Thereof)

The Season screen's Name field has **no input validation whatsoever**. This is the most critical difference from Designation (which has `type="character"` restricting input to letters and spaces only). The absence of validation creates multiple security vulnerabilities.

### What the Name Field Accepts

| Category | Examples | Accepted? | Security Risk |
|----------|----------|-----------|---------------|
| Standard text | "Kharif", "Rabi" | YES | None |
| Spaces | "  Test  " | YES | Low — no trimming |
| Digits | "123456" | YES | Low |
| Special characters | "test@season!#" | YES | Medium |
| **SQL injection** | `'; DROP TABLE Season--` | **YES** | **HIGH** — stored as-is |
| **XSS script tags** | `<script>alert('xss')</script>` | **YES** | **HIGH** — stored as raw HTML |
| Punctuation | "Jr. Manager" | YES | Low (unlike Designation which rejects) |
| Very long text | 200+ characters | YES | Low — no max-length |

### The Duplicate Name Hang (CRITICAL)

When you attempt to create a season with a Name that already exists in the database (e.g., "Rabi"), the system does **not** show an error, does **not** show an alert, and does **not** respond in any way. The form stays open and the Submit button appears to do nothing. There is no loading spinner, no network request, and no timeout. The user's only recovery option is to manually close the popup via the Cancel or X button.

This is different from Designation, where duplicates are silently accepted (a High bug). In Season, the duplicate doesn't just get accepted — the **entire system freezes** with no feedback. This is the most severe bug found in the Season module.

### No Inline Error Messages

Unlike Designation which shows "Invalid Name" `mat-error` below the Name field for invalid input, Season has **zero inline error messages**. The only validation feedback comes from the SweetAlert2 "Validation Failed" modal when submitting with an empty Name. There are no per-field error indicators, no `ng-invalid` visual cues, and no character restriction indicators.

---

## 5. Status Checkbox

The Season screen uses a **standard Angular Material checkbox** for Status instead of the toggle switch used by Designation. This is a simpler, more straightforward component for automation.

### Checkbox Behavior

| State | `is_selected()` | Display Text |
|-------|-----------------|--------------|
| **Active** | True (checked) | "Active" |
| **Inactive** | False (unchecked) | "Inactive" |
| **Default (Add)** | Active (checked) | "Active" |

### How to Read Checkbox State

```python
# Direct Selenium approach — simple and reliable
checkboxes = driver.find_elements(By.CSS_SELECTOR, "div.edit_pop_up input[type='checkbox']")
for cb in checkboxes:
    if cb.is_displayed():
        return cb.is_selected()  # True=Active, False=Inactive
```

### Key Differences from Designation Toggle

| Aspect | Designation (Toggle Switch) | Season (Checkbox) |
|--------|---------------------------|-------------------|
| Component | `.switch-wrapper .slider` | `input[type='checkbox']` |
| Click method | **JS click required** (Angular overlay) | Standard Selenium click works |
| State check | `is_selected()` or check `.state-label.on` class | Simple `is_selected()` |
| Selector complexity | Multiple selectors needed | Single selector |

---

## 6. History Popup

### How to Open

Click the **History** button (3rd action button per row, archive icon) in the table. The popup opens as an overlay.

### Popup Structure

```
+-----------------------------------------------------+
|  Season History                   [Full] [X]         |  <- .popup-header
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
| History popup title | `//h3[contains(text(),'History')]` | `is_history_popup_open()` checks this h3 visibility |
| History search input | `div.popup-overlay input[aria-label='Search box']` | **MUST press Enter — no auto-filter!** |
| History table rows | `div.popup-overlay .scrollable-table-container tr` | Row 0 is header. Data rows start from index 1. |
| History no-data div | `div.popup-overlay .scrollable-table-container div[style*='text-align']` | "No data available" message for new records |
| Cancel button | `//div[contains(@class,'popup-overlay')]//div[contains(@class,'popup-footer')]//span[contains(@class,'mdc-button__label') and text()='Cancel']/..` | **Unusual locator** — navigates up from span label to parent button |

### History Table Columns (0-indexed)

| Column Index | Column Name | Content |
|-------------|-------------|---------|
| 0 | View | Action button |
| 1 | Creation Time | Timestamp |
| 2 | Updated Time | Timestamp |
| 3 | Name | Season name text |
| 4 | Description | Description text |
| 5 | Status | Active/Inactive |

### Important Findings

| Finding | Impact |
|---------|--------|
| **History only logs UPDATE events** | Newly created records show "No data available" in the History popup. Only after an edit does a history row appear. Tests T12/T13 must create+edit before checking history. |
| **History content loads asynchronously** | After clicking the History button, the popup title appears immediately but data takes 1-3 seconds to load. `wait_for_history_popup()` waits for BOTH title AND content (either rows or no-data div). |
| **History Cancel button has unusual locator** | The Cancel button is a mat-button with `mdc-button__label` span, not a standard button with text. Must locate via span label text and navigate up to parent button. |

### The `_ensure_record_has_history()` Helper Method

Because the app only logs history on UPDATE events, tests that need history data must first create a record and then edit it. The `_ensure_record_has_history()` method handles this prerequisite:

```python
def _ensure_record_has_history(self):
    """Create a record, edit it once, and return its final name."""
    # Create
    data = valid_season_with_description()
    name = data["Name"]
    self.open_add_form()
    self.fill_form(name, data["Description"])
    self.click_submit()
    self.wait_for_form_to_close(timeout=10)
    self.refresh_table()
    # Edit (this is what creates the history row)
    row_index = self.find_row_by_name(name)
    self.click_edit_button(row_index)
    self.clear_form()
    edited_name = f"HIST_{name}"
    self.fill_form(edited_name, "Edited for history test")
    self.click_update()
    self.wait_for_form_to_close(timeout=10)
    self.refresh_table()
    return edited_name
```

---

## 7. SweetAlert2 Messages

RhythmERP uses **SweetAlert2** for both validation failure and success feedback.

### Validation Failed (Warning Modal)

Appears when you Submit/Update with empty Name.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-popup` | Centered modal |
| Title | `.swal2-title` | "Validation Failed" |
| Content | `.swal2-html-container` | "Please correct the highlighted fields" |
| OK button | `button.swal2-confirm` | Text: "OK". Click to dismiss. |

**Triggers**: Empty Name on Submit/Update. This is the **only** validation the system performs.

### Success — Record Added (Toast)

Appears after successful season creation.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-popup` | Toast notification |
| Title | `.swal2-title` | "Your record has been added successfully!" |
| OK button | `button.swal2-confirm` | Auto-dismisses after ~2-3 seconds if not clicked |

### Success — Record Updated (Toast)

Appears after successful season edit.

| Element | Selector | Content |
|---------|----------|---------|
| Title | `.swal2-title` | "Your record has been updated successfully!" |

### Key Notes for Automation

- **Success toast auto-dismisses** after ~2-3 seconds. Automation uses `wait_for_form_to_close()` as the primary success detection method rather than trying to catch the fleeting success alert
- **No SweetAlert2 for duplicate names** — the system simply hangs with no popup at all
- **No SweetAlert2 for security issues** — SQL injection and XSS are silently accepted
- **SweetAlert2 confirm button may need JS click** — direct Selenium click can sometimes fail due to z-index layering

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
| Search Toggle | `button[aria-label='Search']` |
| ADD Button | `//button[mat-icon[text()='add']]` (primary), `app-custom-header mat-icon` (fallback) |
| Refresh Button | `//button[mat-icon[text()='refresh']]` |
| Search Input | `input#erpSearchInput` (**STALE after toggle!**) |

### Table

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| Table Rows | `table#excel-table tbody tr` |
| Name Cell | `(//table[@id='excel-table']//tbody//tr)[{n}]/td[4]` |
| Description Cell | `(//table[@id='excel-table']//tbody//tr)[{n}]/td[5]` |
| Status Cell | `(//table[@id='excel-table']//tbody//tr)[{n}]/td[6]` |
| View Button | `(//button[contains(@class,'tblActnBtn')])[{row*3+1}]` |
| Edit Button | `(//button[contains(@class,'tblActnBtn')])[{row*3+2}]` |
| History Button | `(//button[contains(@class,'tblActnBtn')])[{row*3+3}]` |

### Form Popup

| Element | Selector |
|---------|----------|
| Popup Open Check | `div.edit_pop_up` (is_displayed) |
| Popup Title | `div.edit_pop_up .popup-header h3` |
| Name Input | `input[name='Name']` |
| Description Input | `input[name='Description']` |
| Status Checkbox | `div.edit_pop_up input[type='checkbox']` |
| Submit Button | `div.popup-footer button[type='submit']` |
| Cancel Button | `div.popup-footer button[type='button']` |
| X Close Icon | `//div[@class='popup-actions']//button[contains(.,'close')]` |

### History Popup

| Element | Selector |
|---------|----------|
| History Open Check | `//h3[contains(text(),'History')]` |
| History Title | `//h3[contains(text(),'History')]` — text: "Season History" |
| History Table Rows | `div.popup-overlay .scrollable-table-container tr` |
| History Search Input | `div.popup-overlay input[aria-label='Search box']` |
| History Cancel | `//div[contains(@class,'popup-overlay')]//div[contains(@class,'popup-footer')]//span[contains(@class,'mdc-button__label') and text()='Cancel']/..` |

### SweetAlert2

| Element | Selector |
|---------|----------|
| Title | `.swal2-title` |
| Confirm Button | `button.swal2-confirm` |
| Popup | `.swal2-popup` |
| Message | `.swal2-html-container` |

---

## 9. Validation Matrix

### What IS Validated

| # | Validation | Trigger | What Happens |
|---|-----------|---------|-------------|
| 1 | Name required | Submit/Update with empty Name | SweetAlert2: "Validation Failed — Please correct the highlighted fields". Form stays open. |
| 2 | Description optional | Submit with empty Description | No error. Record created. |
| 3 | Status defaults to Active | Open Add form | Checkbox is checked (Active) by default. |

### What is NOT Validated (Gaps = Bugs)

| # | Missing Validation | What Should Happen | What Actually Happens | Severity |
|---|-------------------|--------------------|-----------------------|----------|
| 1 | Duplicate Season Name | Error: "Season Name already exists" | **System HANGS INDEFINITELY** — no alert, no error, no response. Complete freeze. | **High** |
| 2 | SQL injection in Name | Reject or sanitize SQL input | SQL injection payload stored as-is and rendered in list view | **High** |
| 3 | XSS script tags in Name | Reject or sanitize HTML/script input | `<script>alert('xss')</script>` stored as raw HTML in database | **High** |
| 4 | No max-length on Name or Description | Enforce reasonable character limit | 200+ character names accepted without warning | **Low** |

### Name Input Behavior Summary

| Input | Valid? | Error Shown | Security Risk |
|-------|--------|-------------|---------------|
| `"Kharif"` | YES | None | None |
| `"Summer Crop"` | YES | None | None |
| `"Jr. Manager"` | YES | None | None (unlike Designation which rejects) |
| `"12345"` (digits) | YES | None | Low |
| `"test@season!#"` (special chars) | YES | None | Medium |
| `"'; DROP TABLE Season--"` | YES | None | **HIGH — SQL injection** |
| `"<script>alert('xss')</script>"` | YES | None | **HIGH — Stored XSS** |
| `"Rabi"` (duplicate) | **HANGS** | None — system freezes | **HIGH — No feedback** |
| `""` (empty) | NO | "Validation Failed" SweetAlert2 | None |
| `"  Spaces  "` (leading/trailing) | YES | None | Low — no trimming |

---

## 10. Bug Registry (4 Bugs)

### High (3)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#1** | Duplicate Season Name causes infinite hang | 1. Create season "Rabi" (already exists). 2. Click Submit. | Error: "Season Name already exists". | System hangs indefinitely. No alert, no error, no response. Form stays open. User must close popup manually. |
| **#2** | SQL injection accepted and stored in Name | 1. Create season. 2. Enter Name `'; DROP TABLE Season--`. 3. Submit. | System should reject or sanitize SQL injection input. | SQL injection payload is accepted, stored in the database, and rendered in the list view without any sanitization. |
| **#3** | XSS script tag accepted and stored in Name | 1. Create season. 2. Enter Name `<script>alert('xss')</script>`. 3. Submit. | System should reject or sanitize script tags and HTML input. | XSS payload is stored as raw HTML in the database and visible in the list table. If any part of the UI renders HTML, this could execute arbitrary JavaScript. |

### Low (1)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#4** | No max-length on Name or Description | 1. Create season. 2. Enter Name with 200+ characters. 3. Submit. | Error: "Name too long" or truncate. | Name accepted without limit. No character count indicator. |

---

## 11. Test Case Inventory (18 Tests)

### Group A: Happy Path — Add (T1-T2)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| T1 | Create season with Name + Description | Success — record appears in table | — |
| T2 | Create season with Name only (Description optional) | Success — record appears in table | — |

### Group B: Validation — Negative (T3-T6)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| T3 | SQL injection in Name | BUG: accepted and stored as-is | BUG #2 |
| T4 | XSS script tag in Name | BUG: stored as raw HTML, visible in list | BUG #3 |
| T5 | Duplicate Season Name | BUG: system hangs indefinitely | BUG #1 |
| T6 | Special characters in Name | BUG: accepted without validation | — (no type="character" restriction) |

### Group C: Validation — Empty Submit (T7)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| T7 | Submit with all fields blank | SweetAlert2 "Validation Failed" | — |

### Group D: Edit Flow (T8)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| T8 | Edit existing season — change Name and Description | Success — updated record in table, old name removed | — |

### Group E: View Mode (T9)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| T9 | View popup — verify fields disabled, no Submit/Update button | All fields disabled, no primary action button | — |

### Group F: Search (T10-T11)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| T10 | Search for existing season by name | Found in table | — |
| T11 | Search for non-existent season name | 0 results | — |

### Group G: History (T12-T14)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| T12 | History popup opens with data (after create+edit) | Popup visible with history rows | — |
| T13 | Search within History popup | Filters history rows correctly | — |
| T14 | Close History via Cancel button | Popup closes | — |

### Group H: Cancel Behavior (T15-T16)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| T15 | Cancel during Add — nothing saved | Form closes, record NOT in table | — |
| T16 | Cancel during Edit — original unchanged | Form closes, original record unchanged | — |

### Group I: Boundary (T17-T18)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| T17 | Name with leading/trailing spaces | Either trimmed or stored as-is (documented) | — |
| T18 | Very long name (200 chars) | BUG: no max-length validation | BUG #4 |

---

## 12. How to Run the Tests

### Prerequisites

```bash
pip install selenium pytest pytest-html openpyxl python-dotenv
```

Make sure **ChromeDriver** matches your Chrome version.

### Run All 18 Tests

```bash
pytest pages/common_settings/modules/season/test/test_season_validation.py -v --tb=short
```

**Expected output**: `18 passed`

### Run by Group

| Group | Command | Tests |
|-------|---------|-------|
| Happy Path | `pytest ... -v -k "TestSeasonHappyPath" --tb=short` | T1-T2 |
| Validation | `pytest ... -v -k "TestSeasonValidation" --tb=short` | T3-T6 |
| Empty Submit | `pytest ... -v -k "TestSeasonEmptySubmit" --tb=short` | T7 |
| Edit Flow | `pytest ... -v -k "TestSeasonEditFlow" --tb=short` | T8 |
| View Mode | `pytest ... -v -k "TestSeasonViewMode" --tb=short` | T9 |
| Search | `pytest ... -v -k "TestSeasonSearch" --tb=short` | T10-T11 |
| History | `pytest ... -v -k "TestSeasonHistory" --tb=short` | T12-T14 |
| Cancel | `pytest ... -v -k "TestSeasonCancel" --tb=short` | T15-T16 |
| Boundary | `pytest ... -v -k "TestSeasonBoundary" --tb=short` | T17-T18 |

*(Replace `...` with the full path shown above)*

### Run a Single Test

```bash
pytest pages/common_settings/modules/season/test/test_season_validation.py -v -k "test_05" --tb=short
```

### Run Only Bug-Related Tests

```bash
pytest pages/common_settings/modules/season/test/test_season_validation.py -v -k "test_03 or test_04 or test_05 or test_18" --tb=short
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
pages/common_settings/modules/season/reports/CommonSettings_Report_YYYYMMDD_HHMMSS.xlsx
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
|              SEASON — QUICK REFERENCE                            |
+-----------------------------------------------------------------+
|                                                                 |
|  SCREEN:  Common Settings > Season                              |
|  URL:     .../#/dynamic-screens/Season                          |
|  APP:     Angular Material + SweetAlert2                        |
|                                                                 |
|  FORM FIELDS:                                                   |
|    Name* (NO validation!) | Description (optional)              |
|    Status (checkbox, default=Active)                            |
|                                                                 |
|  TABLE COLUMNS:                                                 |
|    View | Edit | History | Name | Description | Status          |
|                                                                 |
|  4 BUGS:  3 High | 1 Low                                       |
|  WORST:    Duplicate Name → INFINITE HANG (High)                |
|            SQL injection stored as-is (High)                    |
|            XSS script tags stored as HTML (High)                |
|                                                                 |
|  NAME VALIDATION:                                               |
|    NONE! Accepts: everything (SQL, XSS, special chars, digits)  |
|    Only rejects: empty Name (Validation Failed SweetAlert2)     |
|                                                                 |
|  STATUS CHECKBOX:                                               |
|    Selector: div.edit_pop_up input[type='checkbox']             |
|    Default:  Active (checked)                                   |
|    State:    .is_selected() — True=Active, False=Inactive       |
|                                                                 |
|  SEARCH — CRITICAL:                                             |
|    Input gets STALE after toggle animation                      |
|    MUST use JS atomic approach (clear+type+Enter in one call)   |
|    clear_search() = re-navigate to Season URL                   |
|                                                                 |
|  HISTORY — CRITICAL:                                            |
|    Only logs UPDATE events (not CREATE)                         |
|    Tests MUST use _ensure_record_has_history() helper           |
|    Cancel button via mdc-button__label span XPath               |
|                                                                 |
|  KEY GOTCHAS:                                                   |
|    x NEVER use Keys.ESCAPE (except history Cancel fallback)     |
|    x NEVER hardcode dropdown options                            |
|    x Duplicate Name = SYSTEM HANG (no recovery except Cancel)   |
|    x SQL injection and XSS are ACCEPTED (security bugs)         |
|    x Search input is STALE after toggle animation               |
|    x Submit/Update button = SAME locator (button[type='submit'])|
|    x History Cancel = unusual span-to-button XPath              |
|    CHECK ALWAYS use JS atomic approach for search               |
|    CHECK ALWAYS use _ensure_record_has_history() for T12/T13    |
|    CHECK ALWAYS wait_for_form_to_close() for success detection  |
|    CHECK ALWAYS refresh_table() after create/edit               |
|    CHECK ALWAYS clear_search() = navigate_to_season() re-nav   |
|    CHECK driver.refresh() NOT used in navigate_to_season()      |
|                                                                 |
|  RUN ALL:  pytest ... -v --tb=short                             |
|  RUN ONE:  pytest ... -v -k "test_05" --tb=short               |
|  REPORT:   .../reports/CommonSettings_Report_*.xlsx             |
+-----------------------------------------------------------------+
```

---

*Last Updated: 18-May-2026 | Season Screen Knowledge Document | 18/18 Tests Passing*
