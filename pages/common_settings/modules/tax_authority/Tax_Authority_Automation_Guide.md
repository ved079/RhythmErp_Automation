# Tax Authority — Screen Knowledge Document

> **RhythmERP** | Common Settings > Tax Authority  
> **Last Verified**: 18-May-2026 | **18/18 Tests Passing**

---

## 1. Screen Overview

**Tax Authority** is a master data screen in RhythmERP under **Common Settings**. It manages tax authority records — each record has a Tax Name (text input), a Tax Type (mat-select dropdown), and a Country (searchable mat-select dropdown). All three fields are required. This screen is significantly different from Season and Designation in several critical ways: (1) there is **no success SweetAlert** after successful create or update — the form simply closes silently, forcing automation to rely on `is_form_open()` returning False as the success indicator; (2) the dropdown selections are **notoriously unreliable** due to Angular CDK overlay issues, requiring a 3-attempt click strategy and a full page-refresh retry loop; and (3) the Country dropdown is **searchable** (has a built-in search input inside the dropdown panel) with 114+ options.

| Detail | Value |
|--------|-------|
| **Navigation** | Sidebar → Common Settings → Tax Authority |
| **URL** | `https://rhythmerp.algorhythms.in/#/dynamic-screens/Tax%20Authority` |
| **Framework** | Angular Material (mat-form-field, mat-select, mat-table) |
| **Alerts** | SweetAlert2 (swal2-title, swal2-confirm) — validation only; **NO success alert** |
| **Validation** | All 3 fields required: Tax Name, Tax Type, Country. Only Tax Name shows mat-error. |
| **Known Bugs** | 4 (1 High, 1 Medium, 2 Low) |

### Key Differences from Season and Designation

| Aspect | Designation | Season | Tax Authority |
|--------|-------------|--------|---------------|
| **Form Fields** | 1 text + 1 toggle | 1 text + 1 text + 1 checkbox | **1 text + 2 dropdowns** |
| **Success Feedback** | SweetAlert2 toast | SweetAlert2 toast | **NONE — form closes silently (Bug TA-001)** |
| **Validation Alert** | SweetAlert2 "Validation Failed" | SweetAlert2 "Validation Failed" | SweetAlert2 "Validation Failed" (same) |
| **Submit/Update Buttons** | Separate XPath locators | Same `button[type='submit']` | **Separate XPath locators** (contains 'Submit' / 'Update') |
| **Status Control** | Toggle switch | Angular Material checkbox | **No status field at all** |
| **Dropdowns** | None | None | **2 mat-select dropdowns** (Tax Type + Country) |
| **Search Toggle** | `button[aria-label='Search']` | `button[aria-label='Search']` | **`button.search-btn`** (different class!) |
| **Search Input** | `input#erpSearchInput` | `input#erpSearchInput` | **`input[placeholder='Search']`** (different selector!) |
| **Duplicate Handling** | Accepted silently (bug) | System hangs indefinitely | **Validation Failed alert** (correct behavior!) |
| **Inline Errors** | "Invalid Name" mat-error | None | **"This field is required"** on Tax Name only; dropdowns get `ng-invalid` class but no visible text |
| **History Popup** | `.popup-overlay` style | `.popup-overlay` style | `.popup-overlay` style (same) |

### What You Can Do on This Screen

- **Create** a new tax authority via ADD button → popup form → Submit (no success alert)
- **Edit** an existing tax authority via row Edit button → popup form → Update (no success alert)
- **View** a tax authority's details (read-only) via row View button
- **Search** tax authorities by name via toolbar search bar (JS atomic approach)
- **Check History** of changes via row History button → history popup

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
| **Search** | search icon | `button.search-btn` | Toggles search input bar. Note: **different selector** from Season's `button[aria-label='Search']`. Uses JS atomic approach to avoid stale elements. |
| **ADD** | + (plus) icon | `//button[mat-icon[text()='add']]` | Opens Create form popup. **NO mattooltip attribute** — must use mat-icon text, not `@mattooltip='ADD'`. |
| **Refresh** | refresh icon | `//button[mat-icon[text()='refresh']]` | Refreshes table data. Fallback: `navigate_to_tax_authority()` re-navigates. |
| **More** | vertical dots | — | Opens menu (Export to Excel, etc.) Not used in automation. |

**Note**: Unlike Season and Designation, the Tax Authority screen does **NOT** have a Filter button or filter panel in the toolbar. The ADD button also lacks the `mattooltip` attribute that other Common Settings modules (Bank, Error Code Mst) have, which is documented as a consistency bug (Low severity).

### Search Bar (Hidden by Default)

After clicking the Search toggle, an input bar appears:

| Element | Selector | Notes |
|---------|----------|-------|
| Search Input | `input[placeholder='Search']` | **Different from Season's `input#erpSearchInput`!** Requires JS atomic approach to avoid stale element issues. |

### Table

```
+------+------+---------+-----------+----------+---------+
| View | Edit | History | Tax Name  | Tax Type | Country |
|  btn |  btn |   btn   |           |          |         |
+------+------+---------+-----------+----------+---------+
|  btn |  btn |   btn   | GST Auth  |   GST    |  India  |
|  btn |  btn |   btn   | VAT Auth  |   GST    |  Dubai  |
+------+------+---------+-----------+----------+---------+
```

| Column | CSS Class | Sortable? | Notes |
|--------|-----------|-----------|-------|
| View | `tblActnBtn` (index-based) | No | Action button column |
| Edit | `tblActnBtn` (index-based) | No | Action button column |
| History | `tblActnBtn` (index-based) | No | Action button column |
| Tax Name | Column 3 (0-based) | Yes | Primary identifier for the tax authority |
| Tax Type | Column 4 (0-based) | Yes | Shows dropdown value (e.g., "GST") |
| Country | Column 5 (0-based) | Yes | Shows country name (e.g., "India", "Dubai") |

### Table Selectors

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| All rows | `table#excel-table tbody tr` |
| Tax Name cells | `(//table[@id='excel-table']//tbody//tr)[{n}]/td[4]` |
| Tax Type cells | `(//table[@id='excel-table']//tbody//tr)[{n}]/td[5]` |
| Country cells | `(//table[@id='excel-table']//tbody//tr)[{n}]/td[6]` |

### Pagination

Tax Authority has a **mat-paginator** component at the bottom of the table, unlike Season which may not display pagination for smaller datasets. This is relevant when there are many records.

| Element | Selector |
|---------|----------|
| Paginator | `mat-paginator` |
| Range Label | `mat-paginator .mat-mdc-paginator-range-label` |
| Next Page | `mat-paginator button[aria-label='Next page']` |
| Previous Page | `mat-paginator button[aria-label='Previous page']` |
| First Page | `mat-paginator button[aria-label='First page']` |
| Last Page | `mat-paginator button[aria-label='Last page']` |

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
|  Tax Authority         [Full] [X]            |  <- Header (.popup-header)
+---------------------------------------------+
|                                             |
|  Tax Name *         [________________]      |  <- standard text input
|  Tax Type *         [GST            v]      |  <- mat-select dropdown
|  Country *          [India          v]      |  <- mat-select (searchable)
|                                             |
+---------------------------------------------+
|              [Cancel]  [Submit/Update]       |  <- Footer (.popup-footer)
+---------------------------------------------+
```

### Field Catalog (3 Fields)

| Field | Type | Required | Selector | Behavior |
|-------|------|----------|----------|----------|
| **Tax Name** | text input | YES | `input[name='Tax Name']` | Standard text input. No `type="character"` restriction. Accepts special characters (confirmed by C07 test). No max-length (bug — maxlength=-1). Only this field shows "This field is required" mat-error on validation failure. |
| **Tax Type** | mat-select | YES | `//mat-label[normalize-space()='Tax Type']/ancestor::mat-form-field//mat-select` | Standard Angular Material dropdown. Uses label-based XPath to locate. Currently only "GST" is available as an option. **CRITICAL: No mat-error rendered** on empty submit — field gets `ng-invalid` class but no visible error text (Bug TA-002). |
| **Country** | mat-select (searchable) | YES | `//mat-label[normalize-space()='Country']/ancestor::mat-form-field//mat-select` | Searchable dropdown with 114+ country options. Has an internal search input (`.cdk-overlay-pane input[type='text']`) that filters the list. Same mat-error gap as Tax Type. |

### Dropdown Selection — The Critical Challenge

The two dropdown fields are the most technically challenging aspect of this screen. Angular's CDK overlay system causes frequent failures where the dropdown panel opens but the click on an option is not registered by Angular's reactive forms. The automation handles this with a **3-layer defense**:

#### Layer 1: 3-Attempt Click Strategy (`_open_dropdown`)

| Attempt | Method | Why Multiple Attempts |
|---------|--------|----------------------|
| 1 | Standard Selenium `click()` | Most common — works when page is stable |
| 2 | JavaScript `arguments[0].click()` | Bypasses CDK overlay blocking |
| 3 | `ActionChains.move_to_element().click()` | Handles off-screen or partially obscured elements |

Each attempt checks if `mat-option` elements appeared in the DOM. If any attempt succeeds, the method returns True.

#### Layer 2: 3-Cycle Option Click + Verification

After opening the dropdown, the code tries to click the desired option up to 3 times. After each click, it **verifies** the trigger element's text to confirm Angular actually registered the selection. If not, it re-opens the panel and tries again.

#### Layer 3: Full Page Refresh Retry (`fill_all_fields`)

If both dropdown attempts fail, the `fill_all_fields()` method closes the form, **hard-refreshes the page** via `navigate_to_tax_authority()`, reopens the Add form, and tries the entire fill operation again. This loop runs up to 3 times (max_cycles=3).

```python
# The fill_all_fields retry loop (simplified):
def fill_all_fields(self, data, max_cycles=3, is_edit=False):
    for cycle in range(1, max_cycles + 1):
        if not is_edit:
            self.navigate_to_tax_authority()   # full page refresh
            self.open_add_form()

        type_ok = self.select_tax_type(data["tax_type"])
        country_ok = self.select_country(data["country"])

        if type_ok and country_ok:
            self.fill_tax_name(data["Tax Name"])
            return True

        # Dropdowns failed — close form, loop will restart
        if is_edit:
            raise Exception("Cannot recover in Edit mode")
        self.close_form_via_cancel()
    raise Exception("Could not fill form after multiple refresh cycles")
```

#### Country Dropdown — Searchable

The Country dropdown is special because it has a **search input** inside the dropdown panel. When the panel opens, the automation:

1. Locates the search input (`.cdk-overlay-pane input[type='text']` or `.cdk-overlay-pane input`)
2. Types the country name to filter the list
3. Clicks the first `mat-option` (which should be the filtered result)
4. Verifies the trigger element shows the selected country

If the search input is not found (some dropdowns may not have search), the code proceeds to click the first option anyway.

### CDK Overlay Cleanup

After every dropdown selection (successful or not), the `_force_close_panels()` method removes leftover CDK overlay elements:

```python
def _force_close_panels(self):
    self.driver.execute_script("""
        document.querySelectorAll('.cdk-overlay-backdrop:not(.cdk-overlay-dark)').forEach(el => el.remove());
        document.querySelectorAll('.cdk-overlay-pane:not(.mat-mdc-dialog-container)').forEach(el => el.remove());
    """)
```

This prevents stale overlay panels from interfering with subsequent interactions.

### Field State Comparison

| Field | Add Mode | Edit Mode | View Mode |
|-------|----------|-----------|-----------|
| Tax Name | Enabled, Empty | Enabled, Pre-filled | **Disabled**, Pre-filled |
| Tax Type | Enabled, Empty | Enabled, Pre-selected | **Disabled**, Pre-selected |
| Country | Enabled, Empty | Enabled, Pre-selected | **Disabled**, Pre-selected |
| **Submit button** | **Present** | — | **ABSENT** |
| **Update button** | — | **Present** | **ABSENT** |
| **Cancel button** | Present | Present | Present (only button) |

### Popup Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| Popup container | `div.edit_pop_up` | `is_form_open()` checks this |
| Popup header | `.popup-header` | Contains title + X button |
| Popup title | `div.edit_pop_up .popup-header h3` | Text: "Tax Authority" |
| Close (X) button | `//div[@class='popup-actions']//button[contains(.,'close')]` | Found by text 'close' in popup-actions |
| Fullscreen button | `//div[@class='popup-actions']//button[contains(.,'fullscreen')]` | Not used in automation |
| Popup footer | `div.popup-footer` | Contains Submit/Update and Cancel buttons |
| Submit (Add) | `//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]` | In Add mode only — **separate locator** from Update |
| Update (Edit) | `//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]` | In Edit mode only — **separate locator** from Submit |
| Cancel | `//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]` | Present in all modes |

### How to Detect Current Mode

```
Add Mode:    Submit button visible (contains 'Submit') + fields enabled + empty fields
Edit Mode:   Update button visible (contains 'Update') + fields enabled + pre-filled
View Mode:   No Submit/Update button + all fields disabled + Cancel only
```

**Important**: Unlike Season where Submit and Update use the same `button[type='submit']` locator with changing text, Tax Authority uses **separate XPath locators** — one matching `contains(.,'Submit')` and one matching `contains(.,'Update')`. This means `is_form_in_view_mode()` checks for the absence of the Submit button (the Update button would also be absent in View mode).

### The Alert-First Detection Pattern

Because Tax Authority has **no success SweetAlert** (Bug TA-001), the automation cannot rely on `is_success_alert_present()` to detect successful operations. Instead, it uses an **alert-first pattern**:

```python
# Step 1: Check for validation alert FIRST
if self.is_validation_alert_present(timeout=5):
    self.handle_validation_alert()
    return False

# Step 2: Check if form closed (success)
if not self.is_form_open():
    # Form closed = record saved (no success alert — known bug)
    return True

# Step 3: Form still open, no alert — unexpected
return False
```

This pattern checks for the validation alert **before** checking if the form closed, which prevents false positives where a validation error closes the form briefly before re-opening it.

---

## 4. Validation

The Tax Authority screen enforces that all three fields are required, but the validation feedback is inconsistent across field types.

### What IS Validated

| # | Validation | Trigger | What Happens |
|---|-----------|---------|-------------|
| 1 | Tax Name required | Submit/Update with empty Tax Name | SweetAlert2: "Validation Failed — Please correct the highlighted fields" + mat-error "This field is required" below Tax Name. Form stays open. |
| 2 | Tax Type required | Submit/Update without selecting Tax Type | SweetAlert2: "Validation Failed" but **NO mat-error** below Tax Type — only `ng-invalid` CSS class. Form stays open. |
| 3 | Country required | Submit/Update without selecting Country | SweetAlert2: "Validation Failed" but **NO mat-error** below Country — only `ng-invalid` CSS class. Form stays open. |
| 4 | Duplicate Tax Name | Create/Update with existing Tax Name | SweetAlert2: "Validation Failed" — **correct behavior** (unlike Season which hangs). |

### The mat-error Inconsistency (Bug TA-002)

When submitting the form with all fields empty, the SweetAlert2 "Validation Failed" modal appears correctly. However, the inline error feedback differs by field type:

| Field | Has `ng-invalid` Class? | Shows mat-error Text? | Why |
|-------|------------------------|----------------------|-----|
| **Tax Name** | Yes | **Yes** — "This field is required" | Text input has built-in Angular validation message |
| **Tax Type** | Yes | **No** | mat-select does not render visible error text |
| **Country** | Yes | **No** | mat-select does not render visible error text |

The dropdown fields visually get the `ng-invalid` CSS class (which may apply a red border), but no human-readable error message is displayed below them. This is a Medium severity bug because users may not understand which fields need attention.

### What is NOT Validated (Gaps = Bugs)

| # | Missing Validation | What Should Happen | What Actually Happens | Severity |
|---|-------------------|--------------------|-----------------------|----------|
| 1 | No success confirmation | Show "Your record has been added successfully!" SweetAlert | **Form closes silently** — no toast, no popup, no confirmation. User cannot be certain the save succeeded. | **High** |
| 2 | No mat-error for dropdown fields | Show "This field is required" below Tax Type and Country | Dropdowns get `ng-invalid` class but no visible error text | **Medium** |
| 3 | No maxlength on Tax Name | Enforce reasonable character limit | maxlength=-1 (unlimited). 200+ character names accepted without warning | **Low** |
| 4 | No mattooltip on ADD button | Consistent with other Common Settings modules | ADD button has no mattooltip attribute — requires different locator strategy | **Low** |

### Tax Name Input Behavior Summary

| Input | Valid? | Error Shown | Notes |
|-------|--------|-------------|-------|
| `"GST Authority"` | YES | None | Standard valid input |
| `"TaxAuthABCDEF"` | YES | None | Random suffix for test isolation |
| `"Test@#$%^&*XYZ"` | YES | None | Special characters accepted (C07 test) |
| `"A" * 200` | YES | None | Very long name accepted (C08 test, Bug) |
| `""` (empty) | NO | "Validation Failed" SweetAlert2 + mat-error | Only case with validation |
| Existing name | NO | "Validation Failed" SweetAlert2 | **Correct behavior** — duplicate rejected |

---

## 5. No Status Control

Unlike Designation (toggle switch) and Season (checkbox), the Tax Authority screen has **no status field at all**. There is no Active/Inactive control, no toggle, no checkbox, and no status column in the table. Every tax authority record is always active — there is no way to deactivate a record through the UI.

This simplifies the automation significantly:
- No toggle/checkbox interaction code needed
- No status verification in test assertions
- No `is_selected()` or JS click workaround for status controls
- Table has one fewer column than Season (no Status column)

---

## 6. History Popup

### How to Open

Click the **History** button (3rd action button per row, archive icon) in the table. The popup opens as an overlay.

### Popup Structure

```
+-----------------------------------------------------+
|  Tax Authority History           [Full] [X]          |  <- .popup-overlay .popup-content .popup-title
+-----------------------------------------------------+
|  [Search in table]  [Refresh] [More]                 |  <- Toolbar
+------+------+------------+-------+----------+--------+
| View | Creation Time | Updated Time | Tax Name | ... |  <- Table
|  btn | 11 May 2026  | 11 May 2026  | ...      | ... |
+------+------+------------+-------+----------+--------+
|                        [Cancel]                       |  <- .popup-footer
+-----------------------------------------------------+
```

### History Selectors

| Element | Selector | Notes |
|---------|----------|-------|
| History popup container | `.popup-overlay` | `is_history_popup_open()` checks `.popup-content` visibility |
| History title | `.popup-overlay .popup-content .popup-title` | Text: "Tax Authority History" |
| History table rows | `.popup-overlay .popup-content table tbody tr` | Data rows |
| History no-data | `.popup-overlay .popup-content .no-data` | "No data available" message for new records |
| Cancel button | `.popup-overlay .popup-footer button` | Simple selector — any button in the footer |

### The 4-Strategy Close Fallback

The `close_history_popup()` method uses a **4-strategy fallback** because the history popup can be difficult to close reliably:

| Strategy | Method | Why It Might Be Needed |
|----------|--------|----------------------|
| 1 | Click Cancel button in `.popup-footer` | Standard approach — works most of the time |
| 2 | Click X button via icon text matching | Find `.mat-icon` with text "close", navigate up to parent button, JS click |
| 3 | Force-remove overlay with JavaScript | `document.querySelectorAll('.popup-overlay').forEach(el => el.remove())` — nuclear option |
| 4 | Press Escape key | Last resort — `ActionChains.send_keys(Keys.ESCAPE)` |

This is more robust than Season's single Cancel button approach, reflecting the real-world difficulty of closing Angular CDK overlays in the test environment.

### Important Findings

| Finding | Impact |
|---------|--------|
| **History may only log UPDATE events** | Same pattern as Season — newly created records may show "No data available" in the History popup until an edit is performed. Tests H01/H02 use existing rows to avoid this issue. |
| **History content loads asynchronously** | After clicking the History button, the popup content takes 1-3 seconds to load. `wait_for_history_popup()` waits for either table rows or the popup-content element to be visible. |
| **Cancel button selector is simpler than Season** | Tax Authority uses `.popup-overlay .popup-footer button` instead of Season's unusual `mdc-button__label` span XPath. |

---

## 7. SweetAlert2 Messages

RhythmERP uses **SweetAlert2** for validation failure feedback. However, Tax Authority has a critical bug: it does **NOT** show any success SweetAlert after create or update operations.

### Validation Failed (Warning Modal)

Appears when you Submit/Update with any required field empty, or with a duplicate Tax Name.

| Element | Selector | Content |
|---------|----------|---------|
| Container | `.swal2-popup` | Centered modal |
| Title | `.swal2-title` | "Validation Failed" |
| Content | `.swal2-html-container` | "Please correct the highlighted fields" |
| OK button | `button.swal2-confirm` | Text: "OK". Click to dismiss. |

**Triggers**: Empty Tax Name, empty Tax Type, empty Country, or duplicate Tax Name on Submit/Update.

### Success — Record Added (MISSING — BUG TA-001)

| Element | Selector | Content |
|---------|----------|---------|
| — | — | **DOES NOT APPEAR** |

After a successful create, the form closes silently. No toast notification, no success popup, no confirmation message of any kind. The `is_success_alert_present()` method is kept in the codebase for consistency but will always return False unless this bug is fixed.

### Success — Record Updated (MISSING — BUG TA-001)

Same as above — no success alert after a successful update. The form just closes.

### Key Notes for Automation

- **Form closure = success** — the primary success detection method is `is_form_open()` returning False after Submit/Update
- **Alert-first pattern** — always check for validation alert BEFORE checking form closure, to avoid false positives
- **No SweetAlert for success** — unlike every other Common Settings module, Tax Authority provides zero user feedback on successful save
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
| Search Toggle | `button.search-btn` |
| ADD Button | `//button[mat-icon[text()='add']]` |
| Refresh Button | `//button[mat-icon[text()='refresh']]` |
| Search Input | `input[placeholder='Search']` (**different from Season's `#erpSearchInput`!**) |

### Table

| Element | Selector |
|---------|----------|
| Table | `table#excel-table` |
| Table Rows | `table#excel-table tbody tr` |
| Tax Name Cell | `(//table[@id='excel-table']//tbody//tr)[{n}]/td[4]` |
| Tax Type Cell | `(//table[@id='excel-table']//tbody//tr)[{n}]/td[5]` |
| Country Cell | `(//table[@id='excel-table']//tbody//tr)[{n}]/td[6]` |
| View Button | `(//button[contains(@class,'tblActnBtn')])[{row*3+1}]` |
| Edit Button | `(//button[contains(@class,'tblActnBtn')])[{row*3+2}]` |
| History Button | `(//button[contains(@class,'tblActnBtn')])[{row*3+3}]` |
| Paginator | `mat-paginator` |

### Form Popup

| Element | Selector |
|---------|----------|
| Popup Open Check | `div.edit_pop_up` (is_displayed) |
| Popup Title | `div.edit_pop_up .popup-header h3` |
| Tax Name Input | `input[name='Tax Name']` |
| Tax Type Dropdown | `//mat-label[normalize-space()='Tax Type']/ancestor::mat-form-field//mat-select` |
| Country Dropdown | `//mat-label[normalize-space()='Country']/ancestor::mat-form-field//mat-select` |
| Tax Type Option | `//mat-option//span[contains(text(),'{value}')]` |
| Country Search Input | `.cdk-overlay-pane input[type='text']` or `.cdk-overlay-pane input` |
| Country First Option | `(//mat-option)[1]` |
| Submit Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]` |
| Update Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]` |
| Cancel Button | `//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]` |
| X Close Icon | `//div[@class='popup-actions']//button[contains(.,'close')]` |

### History Popup

| Element | Selector |
|---------|----------|
| History Open Check | `.popup-overlay .popup-content` (visibility) |
| History Title | `.popup-overlay .popup-content .popup-title` |
| History Table Rows | `.popup-overlay .popup-content table tbody tr` |
| History No Data | `.popup-overlay .popup-content .no-data` |
| History Cancel | `.popup-overlay .popup-footer button` |

### SweetAlert2

| Element | Selector |
|---------|----------|
| Title | `.swal2-title` |
| Confirm Button | `button.swal2-confirm` |
| Cancel Button | `button.swal2-cancel` |
| Popup | `.swal2-popup` |
| Message | `.swal2-html-container` |

---

## 9. Validation Matrix

### What IS Validated

| # | Validation | Trigger | What Happens |
|---|-----------|---------|-------------|
| 1 | Tax Name required | Submit/Update with empty Tax Name | SweetAlert2: "Validation Failed" + mat-error "This field is required" below Tax Name. Form stays open. |
| 2 | Tax Type required | Submit/Update without Tax Type | SweetAlert2: "Validation Failed". No mat-error text. Form stays open. |
| 3 | Country required | Submit/Update without Country | SweetAlert2: "Validation Failed". No mat-error text. Form stays open. |
| 4 | Duplicate Tax Name rejected | Create with existing Tax Name | SweetAlert2: "Validation Failed". **Correct behavior** (unlike Season). |
| 5 | Duplicate on edit rejected | Edit to use another record's Tax Name | SweetAlert2: "Validation Failed". Correct behavior. |

### What is NOT Validated (Gaps = Bugs)

| # | Missing Validation | What Should Happen | What Actually Happens | Severity |
|---|-------------------|--------------------|-----------------------|----------|
| 1 | Success confirmation after create/update | Show SweetAlert2 "Your record has been added/updated successfully!" | **No success alert at all** — form closes silently. User gets zero confirmation. | **High** |
| 2 | mat-error for Tax Type and Country on empty submit | Show "This field is required" below both dropdowns | Dropdowns get `ng-invalid` CSS class but no visible error message text | **Medium** |
| 3 | Max-length on Tax Name | Enforce reasonable character limit | maxlength=-1 (unlimited). 200+ character names accepted without warning | **Low** |
| 4 | mattooltip on ADD button | Consistent with other Common Settings modules (Bank, Error Code Mst) | ADD button has no mattooltip — requires `//button[mat-icon[text()='add']]` instead of `//*[@mattooltip='ADD']` | **Low** |

### Form Input Behavior Summary

| Input | Valid? | Error Shown | Notes |
|-------|--------|-------------|-------|
| `"TaxAuthABCDEF"` (valid) | YES | None | Standard valid input |
| `"Test@#$%^&*XYZ"` (special chars) | YES | None | Special characters accepted (C07) |
| `"A" * 200` (very long) | YES | None | No maxlength (Bug, C08) |
| `""` (empty Tax Name) | NO | "Validation Failed" + mat-error | Only field with visible mat-error |
| No Tax Type selected | NO | "Validation Failed", NO mat-error | Bug TA-002 |
| No Country selected | NO | "Validation Failed", NO mat-error | Bug TA-002 |
| Duplicate Tax Name | NO | "Validation Failed" | Correct behavior (C06, E05) |

---

## 10. Bug Registry (4 Bugs)

### High (1)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#1 (TA-001)** | No success SweetAlert after create/update | 1. Fill all fields correctly. 2. Click Submit. | SweetAlert2 "Your record has been added successfully!" with OK button. | Form closes silently. No success toast or popup displayed. User cannot confirm the save operation succeeded without checking the table manually. |

### Medium (1)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#2 (TA-002)** | Missing mat-error for Tax Type and Country dropdowns | 1. Open Add form. 2. Click Submit without filling any fields. | All 3 required fields should show "This field is required" mat-error below the field. | Only Tax Name shows mat-error. Tax Type and Country have `ng-invalid` class but no visible error message text. User must guess which dropdown needs attention. |

### Low (2)

| Bug | Description | Steps to Reproduce | Expected | Actual |
|-----|-------------|-------------------|----------|--------|
| **#3** | No maxlength on Tax Name | 1. Enter 200+ character Tax Name. 2. Submit. | Error or truncation at reasonable limit. | maxlength=-1 (unlimited). Extremely long names accepted without warning. |
| **#4** | ADD button has no mattooltip | 1. Inspect ADD button element. | `mattooltip="ADD"` attribute present (consistent with Bank, Error Code Mst). | No mattooltip attribute. Automation must use `//button[mat-icon[text()='add']]` instead of `//*[@mattooltip='ADD']`. |

---

## 11. Test Case Inventory (18 Tests)

### Class 1: TestCreateFormValidations (C01-C08)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| C01 | Submit form without filling any field | SweetAlert2 "Validation Failed" | — |
| C02 | Submit without Tax Name (fill dropdowns only) | SweetAlert2 "Validation Failed" | — |
| C03 | Submit without Tax Type (fill Tax Name + Country) | SweetAlert2 "Validation Failed" | — |
| C04 | Submit without Country (fill Tax Name + Tax Type) | SweetAlert2 "Validation Failed" | — |
| C05 | Create valid record with all fields | Record created, appears in table | BUG #1 (no success alert) |
| C06 | Create duplicate Tax Name | SweetAlert2 "Validation Failed" | — (correct behavior) |
| C07 | Tax Name with special characters | Record created (or rejected — test is flexible) | — (documents behavior) |
| C08 | Very long Tax Name (200 chars) | Record created | BUG #3 (no maxlength) |

### Class 2: TestViewFormBehaviors (V01-V03)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| V01 | View form — all fields disabled, no Submit button | All fields disabled, no action button | — |
| V02 | View form — displays correct data from record | Tax Name matches created record | — |
| V03 | View form — Cancel closes popup | Popup closes | — |

### Class 3: TestEditFormValidations (E01-E05)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| E01 | Edit form has Update button (not Submit) | Update button visible, Submit button absent | — |
| E02 | Edit form — all fields are enabled | Tax Name is enabled | — |
| E03 | Edit form — pre-filled with existing data | Tax Name matches row data | — |
| E04 | Edit record — update changes table | New name appears, old name removed | BUG #1 (no success alert) |
| E05 | Edit to duplicate Tax Name | SweetAlert2 "Validation Failed" | — (correct behavior) |

### Class 4: TestHistoryValidations (H01-H02)

| Test | Description | Expected Result | Bug? |
|------|-------------|----------------|------|
| H01 | History popup opens with correct title | "Tax Authority" in title | — |
| H02 | History popup — Cancel closes it | Popup closes | — |

### Test Data Generators

| Function | Purpose | Key Data |
|----------|---------|----------|
| `valid_tax_authority_data()` | Standard valid record | Tax Name with random suffix, Tax Type=GST, Country=India |
| `valid_tax_authority_dubai()` | Valid record with Dubai | Country=Dubai |
| `valid_tax_authority_usa()` | Valid record with USA | Country=United States |
| `invalid_empty_tax_name()` | Empty Tax Name test | Tax Name="" |
| `invalid_very_long_tax_name(200)` | Maxlength test | Tax Name="AAA..." (200 chars) |
| `special_chars_tax_name()` | Special character test | Tax Name="Test@#$%^&*{random}" |
| `duplicate_tax_authority_data(name)` | Duplicate test | Uses existing record's name |

---

## 12. How to Run the Tests

### Prerequisites

```bash
pip install selenium pytest pytest-html openpyxl python-dotenv
```

Make sure **ChromeDriver** matches your Chrome version.

### Run All 18 Tests

```bash
pytest pages/common_settings/modules/tax_authority/test/test_tax_authority_validation.py -v --tb=short
```

**Expected output**: `18 passed`

### Run by Class

| Class | Command | Tests |
|-------|---------|-------|
| Create Validations | `pytest ... -v -k "TestCreateFormValidations" --tb=short` | C01-C08 |
| View Behaviors | `pytest ... -v -k "TestViewFormBehaviors" --tb=short` | V01-V03 |
| Edit Validations | `pytest ... -v -k "TestEditFormValidations" --tb=short` | E01-E05 |
| History | `pytest ... -v -k "TestHistoryValidations" --tb=short` | H01-H02 |

*(Replace `...` with the full path shown above)*

### Run by Individual Test

```bash
pytest pages/common_settings/modules/tax_authority/test/test_tax_authority_validation.py -v -k "test_empty_form_submit" --tb=short
```

### Run Only Bug-Related Tests

```bash
pytest pages/common_settings/modules/tax_authority/test/test_tax_authority_validation.py -v -k "test_create_valid_record or test_very_long_tax_name or test_special_characters" --tb=short
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
pages/common_settings/modules/tax_authority/reports/CommonSettings_Report_YYYYMMDD_HHMMSS.xlsx
```

The report includes: test names, pass/fail status, step-by-step logs, error messages, and the known issues list. Report generation is handled by the shared `CSReportStore` from `pages/common_settings.cs_report_generator`.

### Conftest Behavior

The Tax Authority conftest uses **hard browser refresh** (`driver.refresh()`) for both pre-test setup and post-test teardown, which is different from Season's approach of just re-navigating via URL. This aggressive cleanup strategy is necessary because:

1. Angular CDK overlay panels can persist across tests
2. Dropdown state can become corrupted after a failed selection
3. The stuck-state recovery (`_recover_from_stuck_state()`) may not catch all edge cases

The conftest also implements a **one-retry** navigation pattern — if the first `navigate_to_tax_authority()` call fails, it performs a hard refresh and tries once more before raising the error.

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
|              TAX AUTHORITY — QUICK REFERENCE                     |
+-----------------------------------------------------------------+
|                                                                 |
|  SCREEN:  Common Settings > Tax Authority                       |
|  URL:     .../#/dynamic-screens/Tax%20Authority                 |
|  APP:     Angular Material + SweetAlert2                        |
|                                                                 |
|  FORM FIELDS:                                                   |
|    Tax Name* (text) | Tax Type* (mat-select) | Country* (search)|
|    NO STATUS FIELD — no Active/Inactive control                 |
|                                                                 |
|  TABLE COLUMNS:                                                 |
|    View | Edit | History | Tax Name | Tax Type | Country        |
|                                                                 |
|  4 BUGS:  1 High | 1 Medium | 2 Low                            |
|  WORST:    No success SweetAlert after create/update (High)     |
|            Missing mat-error for dropdowns (Medium)             |
|                                                                 |
|  VALIDATION:                                                    |
|    All 3 fields required. Duplicate name correctly rejected.    |
|    Only Tax Name shows mat-error on empty submit.               |
|    No maxlength on Tax Name. Special chars accepted.            |
|                                                                 |
|  DROPDOWN SELECTION — CRITICAL:                                 |
|    Uses 3-attempt click strategy (Selenium -> JS -> Actions)    |
|    fill_all_fields() has 3-cycle retry with page refresh        |
|    CDK overlay cleanup after every selection                    |
|    Country is SEARCHABLE — types in overlay search input        |
|    NEVER assume dropdown works on first try                     |
|                                                                 |
|  SUCCESS DETECTION — CRITICAL:                                  |
|    NO success SweetAlert (BUG TA-001)                           |
|    Use alert-first pattern: check validation alert FIRST        |
|    Then check is_form_open() returning False = success          |
|    is_success_alert_present() ALWAYS returns False              |
|                                                                 |
|  SEARCH:                                                        |
|    Toggle: button.search-btn (NOT button[aria-label='Search'])  |
|    Input:  input[placeholder='Search'] (NOT #erpSearchInput)    |
|    MUST use JS atomic approach (same as Season)                 |
|    clear_search() = JS clear + toggle off, or re-navigate       |
|                                                                 |
|  HISTORY:                                                       |
|    close_history_popup() has 4-strategy fallback                |
|    (Cancel -> X button -> JS force remove -> Escape)            |
|    May only log UPDATE events (same as Season)                  |
|                                                                 |
|  BUTTONS:                                                       |
|    Submit and Update = SEPARATE XPath locators                  |
|    ADD button has no mattooltip (use mat-icon text)             |
|                                                                 |
|  KEY GOTCHAS:                                                   |
|    x NEVER rely on is_success_alert_present() — always False    |
|    x NEVER assume dropdown selection succeeds — use fill_all_   |
|      fields() with retry, not individual select_ calls          |
|    x NEVER use #@mattooltip='ADD' — button has no tooltip       |
|    x NEVER use input#erpSearchInput — wrong selector            |
|    x NEVER use button[aria-label='Search'] — wrong selector     |
|    x driver.refresh() IS used in conftest (unlike Season)      |
|    CHECK ALWAYS use alert-first pattern for create/update       |
|    CHECK ALWAYS use fill_all_fields() for form filling          |
|    CHECK ALWAYS run _force_close_panels() after dropdown select |
|    CHECK ALWAYS handle "form closed = success" (no toast)       |
|    CHECK ALWAYS do hard refresh in teardown (conftest)          |
|                                                                 |
|  RUN ALL:  pytest ... -v --tb=short                             |
|  RUN ONE:  pytest ... -v -k "test_empty_form_submit" --tb=short|
|  REPORT:   .../reports/CommonSettings_Report_*.xlsx             |
+-----------------------------------------------------------------+
```

---

*Last Updated: 18-May-2026 | Tax Authority Screen Knowledge Document | 18/18 Tests Passing*
