# Customer Screen Automation — Knowledge Document

## Project: RhythmERP PACS Automation
### Module: Registration > Customer
### Automation Date: 2026-05-25
### Status: 46 tests — 42 PASSED, 2 XFAIL, 2 XPASS

---

## 1. Screen Overview

| Property | Value |
|---|---|
| **Module** | Registration |
| **Screen** | Customer |
| **URL** | `/#/dynamic-screens/Customer/Customer` |
| **Form Type** | Universal Fields + 3-Step Horizontal Stepper Popup |
| **Framework** | Angular Material |
| **Popup Selector** | `.edit_pop_up.override_edit_pop_up.popup-mode, .big-model, mat-dialog-container` |
| **Login** | `RHYTHMERP_EMAIL` / `RHYTHMERP_PASSWORD` (from config.py) |
| **Unique Constraint** | PAN Number (server-side validation) |

### Form Architecture

The Customer form has a unique architecture — **universal fields are always visible ABOVE the stepper**, and the stepper contains the remaining optional/detailed fields.

**Universal Fields (always visible):**
- Party Reference (mat-select, optional)
- Ownership Status (mat-select, required)
- Company Name (text input, required, maxlength=255)
- Sale Type (mat-select, required)
- Supply Type (mat-select, required)
- Transaction Currency (mat-select, required)
- Email (text input, required, maxlength=255)
- Phone Number (number input, required)
- PAN Number (text input, required, maxlength=255, **UNIQUE**)
- Status toggle (OUTSIDE stepper, default Active)

**3-Step Horizontal Stepper:**

| Step | Label | Key Fields | Required Fields |
|---|---|---|---|
| 0 | Additional Details | Is TDS Applicable, Contact Person, Office Number, Payment Method, GST Type, Payment/Delivery/Courier Terms, Mode of Delivery, Deposite, Quantity/Rate Tolerance | None (all optional) |
| 1 | Customer Details | Address grid with Address Type, Country, State, District, Taluka, Village, Address, Pin Code, GSTIN | Address Type, Country, State, District, Taluka, Address |
| 2 | Customer Bank Details | Bank grid with Bank Name, Branch, IFSC Code, Account Type, Account Holder Name, Account Number, Bank Proof, Attachment | Account Type, Bank Proof |

### Row Actions

| Action | Available | Implementation |
|---|---|---|
| View | Yes | Via 3-dot menu trigger per row |
| Edit | Yes | Via 3-dot menu, opens form with "Update" button |
| History | Yes | Via 3-dot menu |
| Delete | No | No delete functionality exists anywhere |

---

## 2. Critical Automation Rules

### R01: Non-Linear Stepper (BUG-002)
The Customer stepper is **non-linear** — the Next button does NOT validate required fields on the current step. Users can advance through all steps with empty required fields. Validation only occurs when the **Submit** button is clicked. This is different from Agent/Bank screens.

```python
# BUG-002: This WILL succeed even with empty fields
page.open_add_form()
page.click_stepper_next()  # Step 0 → Step 1 (no validation!)
page.click_stepper_next()  # Step 1 → Step 2 (no validation!)
page.click_submit()        # Only NOW does validation fire
```

### R02: Universal Fields are Outside the Stepper
Universal fields (Company Name, Email, Phone, PAN, etc.) are NOT inside any stepper step. They are always visible at the top of the form popup, above the stepper. This means:
- They must be filled BEFORE navigating stepper steps
- They remain visible and editable from any step
- Their validation is deferred to Submit

### R03: Angular Material Input Filling
**NEVER use `send_keys()` or `element.clear()` for Angular Material inputs.** Always use JavaScript `nativeInputValueSetter`:

```python
def _fill_input_by_name(self, name, value):
    js = """
    var inp = document.querySelector('input[name="' + arguments[0] + '"]');
    if (inp) {
        var nativeSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        ).set;
        nativeSetter.call(inp, arguments[1]);
        inp.dispatchEvent(new Event('input', { bubbles: true }));
        inp.dispatchEvent(new Event('change', { bubbles: true }));
    }
    """
    self.driver.execute_script(js, name, value)
```

### R04: mat-select Dropdown Handling (BUG-001)
**Browser-clicked mat-select options do NOT update the Angular reactive form model.** Submit will show "Validation Failed" even with all fields visually filled. Must use JS workaround:

```python
def _select_dropdown_by_label(self, label, option_text):
    # Step 1: Open the dropdown via JS
    js_open = """
    var labels = document.querySelectorAll('mat-label');
    for (var i = 0; i < labels.length; i++) {
        if (labels[i].textContent.includes(arguments[0])) {
            labels[i].click();
            break;
        }
    }
    """
    self.driver.execute_script(js_open, label)
    time.sleep(0.5)

    # Step 2: Click the option in the overlay panel
    js_click = """
    var options = document.querySelectorAll('mat-option');
    for (var i = 0; i < options.length; i++) {
        if (options[i].textContent.trim() === arguments[0]) {
            options[i].click();
            break;
        }
    }
    """
    self.driver.execute_script(js_click, option_text)
    time.sleep(0.5)
```

### R05: Cascading Dropdowns (Step 1: Address Grid)
Address grid has cascading dropdowns: **Country > State > District > Taluka > Village**. Country MUST be set to "India" for cascading to work. After each selection, wait for the next dropdown to populate:

```python
def _select_cascading_dropdown(self, label, option_text):
    self._select_dropdown_by_label(label, option_text)
    time.sleep(1.5)  # Extra wait for cascading data to load
```

### R06: Overlay Cleanup — Never Keys.ESCAPE
**NEVER use `Keys.ESCAPE`** — it closes the entire popup. Use JS overlay removal instead:

```python
def _force_close_panels(self):
    self.driver.execute_script("""
        document.querySelectorAll(
            'div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)'
        ).forEach(function(el) { el.remove(); });
        document.querySelectorAll(
            'div.cdk-overlay-pane'
        ).forEach(function(el) {
            if (!el.querySelector('mat-dialog-container')) el.remove();
        });
    """)
```

### R07: Stepper Navigation with Multiple Strategies
Angular Material stepper buttons are unreliable with Selenium clicks. Use multi-strategy JS approach:

```python
def click_stepper_next(self):
    # Close any open dropdown overlays first
    self._force_close_panels()

    # Strategy 1: CSS class match
    # Strategy 2: Text content match 'Next'
    # Strategy 3: JS querySelectorAll inside popup
    # All strategies use scrollIntoView + execute_script click
```

### R08: Row Actions via 3-Dot Menu
Customer screen uses a 3-dot menu trigger for row actions (not direct column buttons):

```python
# Click the 3-dot menu
trigger = driver.find_element(By.CSS_SELECTOR, "button.mat-mdc-menu-trigger.erp-row-trigger")
trigger.click()

# Then click the menu item
edit_btn = driver.find_element(By.XPATH, 
    "//span[contains(@class,'erp-menu-title') and text()='Edit']/ancestor::button")
edit_btn.click()
```

### R09: PAN Number Uniqueness
PAN Number has server-side unique validation. Attempting to create two customers with the same PAN will be blocked with a SweetAlert error.

---

## 3. Test Suite Structure

### File Structure
```
pages/registration/modules/customer/
    customer_page.py              # Page Object Model
    data/
        customer_data.py          # Test data generators
    test/
        conftest.py               # pytest fixtures + CSReportStore
        test_customer_validation.py  # 46 tests across 6 phases
    reports/                      # Auto-generated Excel reports
```

### Test Phases Summary

| Phase | Class | Tests | IDs | Focus |
|---|---|---|---|---|
| 1 | TestCreateFormValidations | 20 | CU-C01 to C20 | Empty, valid, boundary, email, security, PAN, deposit, stepper, unicode |
| 2 | TestDuplicateValidations | 4 | CU-D01 to D04 | PAN uniqueness, company name, email duplicates |
| 3 | TestEditFormValidations | 5 | CU-E01 to E05 | Pre-populated, modify, clear required, invalid email, update button |
| 4 | TestSearchFilter | 5 | CU-S01 to S05 | Exact, partial, no results, special chars, clear search |
| 5 | TestPopupUIBehaviors | 8 | CU-P01 to P08 | Open/close, X button, fullscreen, no delete, cancel, double-submit, stepper tabs, add row |
| 6 | TestBugSpecific | 4 | CU-B01 to B04 | BUG-001 mat-select, BUG-002 stepper, BUG-003/004 header mismatches |

### Test Results: 42 PASSED, 2 XFAIL, 2 XPASS

| ID | Test Name | Result | Notes |
|---|---|---|---|
| CU-C03 | Spaces-Only Company Name | **XPASS** | Spaces-only name ACCEPTED — no trim validation |
| CU-C15 | Stepper Advances Empty (BUG-002) | **XFAIL** | Confirmed: stepper advances with empty required fields |
| CU-B01 | Mat Select Form Model Sync (BUG-001) | **XPASS** | JS workaround confirmed working |
| CU-B02 | Stepper Nonlinear Validation (BUG-002) | **XFAIL** | Confirmed: non-linear stepper, validation only on Submit |

---

## 4. Known Bugs

### CU-BUG-001: mat-select Does NOT Sync Angular Form Model (Critical)
- **Severity:** Critical
- **Category:** Automation
- **Test Reference:** CU-B01 (XPASS), ALL tests
- **Description:** Browser-clicked mat-select options do NOT update the Angular reactive form model. Submit fires "Validation Failed" even with all fields filled via UI clicks.
- **Workaround:** JS value-setter + dispatchEvent pattern for all dropdown selections.
- **Status:** Workaround confirmed working (CU-B01 XPASS).

### CU-BUG-002: Non-Linear Stepper (Medium)
- **Severity:** Medium
- **Category:** Validation
- **Test Reference:** CU-C15 (XFAIL), CU-B02 (XFAIL)
- **Description:** The horizontal stepper allows clicking Next to advance even when required fields are empty. No per-step validation — only Submit validates.
- **Expected:** Stepper should block advancement when required fields are empty.
- **Actual:** Next button always works. Only Submit triggers validation.
- **Status:** Confirmed.

### CU-BUG-003: Pin Code Header Shows Asterisk But Not Required (Medium)
- **Severity:** Medium
- **Category:** UI Bug
- **Test Reference:** CU-C12, CU-B03
- **Description:** Address grid header shows "Pin Code *" with asterisk, but HTML input has `required=false`. Submit succeeds without Pin Code.
- **Expected:** Header asterisk and field required attribute should match.
- **Actual:** Header is misleading — Pin Code is optional on submit.
- **Status:** Confirmed.

### CU-BUG-004: Bank Fields Headers Show Asterisks But Not Required (Medium)
- **Severity:** Medium
- **Category:** UI Bug
- **Test Reference:** CU-C13, CU-B04
- **Description:** Bank Details grid headers show asterisks for Bank Name, Branch, Account Holder Name, Account Number, but HTML inputs have `required=false`. Submit succeeds without these fields.
- **Expected:** Headers and field required attributes should match.
- **Actual:** Headers are misleading — these fields are optional on submit.
- **Status:** Confirmed.

---

## 5. Field Reference

### Universal Fields (Outside Stepper)

| Field | Type | Required | Max Length | Validation | Notes |
|---|---|---|---|---|---|
| Party Reference | mat-select | No | - | - | 500+ options, optional |
| Ownership Status | mat-select | Yes | - | Required | From live UI |
| Company Name | text input | Yes | 255 | Spaces-only accepted (BUG) | CU-C03 XPASS |
| Sale Type | mat-select | Yes | - | Required | From live UI |
| Supply Type | mat-select | Yes | - | Required | From live UI |
| Transaction Currency | mat-select | Yes | - | Required | e.g. INR |
| Email | text input | Yes | 255 | "Invalid Email" mat-error | Required, validated |
| Phone Number | number input | Yes | - | HTML5 blocks letters | 10-digit Indian mobile |
| PAN Number | text input | Yes | 255 | Server-side unique | Format: ABCDE1234F |
| Status | toggle | No | - | - | Active/Inactive, default Active |

### Step 0: Additional Details

| Field | Type | Required | Notes |
|---|---|---|---|
| Is TDS Applicable | toggle | No | No/Yes, default No |
| Contact Person Name | text input | No | maxlength=255 |
| Office Number | text input | No | maxlength=255 |
| Preferred Payment Method | mat-select | No | RTGS, IMPS, DD, Cheque, Cash |
| Gst Registration Type | mat-select | No | From live UI |
| Payment Terms | mat-select | No | 9 options |
| Delivery Terms | mat-select | No | From live UI |
| Mode Of Delivery | mat-select | No | From live UI |
| Courier Terms | mat-select | No | From live UI |
| Deposite | number input | No | Default=0, positive expected |
| Quantity Tolerance | number input | No | - |
| Rate Tolerance | number input | No | - |

### Step 1: Customer Details (Address Grid — Repeatable Rows)

| Field | Type | Required | Notes |
|---|---|---|---|
| Address Type | mat-select | Yes | From live UI |
| Country | mat-select | Yes | 30 countries, cascading |
| State | mat-select | Yes | 36 states (India), cascading |
| District | mat-select | Yes | Dynamic, cascading |
| Taluka | mat-select | Yes | Dynamic, cascading |
| Village | mat-select | No | Dynamic, cascading |
| Address | text input | Yes | maxlength=255 |
| Pin Code | text input | No* | BUG-003: header shows asterisk but optional |
| GSTIN | text input | No | 15-char format |

### Step 2: Customer Bank Details (Bank Grid — Repeatable Rows)

| Field | Type | Required | Notes |
|---|---|---|---|
| Bank Name | text input | No* | BUG-004: header shows asterisk but optional |
| Branch | text input | No* | BUG-004: header shows asterisk but optional |
| IFSC Code | text input | No | maxlength=255 |
| Account Type | mat-select | Yes | Current, Saving |
| Account Holder Name | text input | No* | BUG-004: header shows asterisk but optional |
| Account Number | text input | No* | BUG-004: header shows asterisk but optional |
| Bank Proof | mat-select | Yes | Cancelled Cheque, Passbook |
| Attachment | file input | No | .png/.jpg/.pdf |

*Header shows asterisk but HTML says optional — see BUG-003 and BUG-004.

---

## 6. Dropdown Options Reference

| Dropdown | Location | Notes |
|---|---|---|
| Party Reference | Universal | 500+ options (dynamic) |
| Ownership Status | Universal | From live UI |
| Sale Type | Universal | From live UI |
| Supply Type | Universal | From live UI |
| Transaction Currency | Universal | INR and others |
| Country | Step 1 Grid | 30 countries (must be India for cascading) |
| State (India) | Step 1 Grid | 36 states, cascades from Country |
| District | Step 1 Grid | Dynamic, cascades from State |
| Taluka | Step 1 Grid | Dynamic, cascades from District |
| Village | Step 1 Grid | Dynamic, cascades from Taluka |
| Address Type | Step 1 Grid | From live UI |
| Preferred Payment Method | Step 0 | RTGS, IMPS, DD, Cheque, Cash |
| Gst Registration Type | Step 0 | From live UI |
| Payment Terms | Step 0 | 9 options: 21/14/7 Days, Wallet, RTGS, Advance, Immediate, 60/30 Days |
| Delivery Terms | Step 0 | From live UI |
| Mode Of Delivery | Step 0 | From live UI |
| Courier Terms | Step 0 | From live UI |
| Account Type | Step 2 Grid | Current, Saving |
| Bank Proof | Step 2 Grid | Cancelled Cheque, Passbook |

---

## 7. Execution Guide

### Run All Tests
```powershell
python -m pytest pages/registration/modules/customer/test/test_customer_validation.py -v --tb=short
```

### Run Specific Phase
```powershell
# Phase 1: Create Validations
python -m pytest pages/registration/modules/customer/test/test_customer_validation.py::TestCreateFormValidations -v

# Phase 2: Duplicate Validations
python -m pytest pages/registration/modules/customer/test/test_customer_validation.py::TestDuplicateValidations -v

# Phase 6: Bug Specific
python -m pytest pages/registration/modules/customer/test/test_customer_validation.py::TestBugSpecific -v
```

### Run Individual Test
```powershell
python -m pytest pages/registration/modules/customer/test/test_customer_validation.py::TestCreateFormValidations::test_CU_C02_valid_create -v
```

### Generate HTML Report
```powershell
python -m pytest pages/registration/modules/customer/test/test_customer_validation.py -v --html=customer_report.html --self-contained-html
```

### Execution Environment
| Property | Value |
|---|---|
| Python | 3.14.3 |
| pytest | 9.0.2 |
| Browser | Microsoft Edge (WebDriver) |
| OS | Windows 11 (10.0.26200) |
| Execution Time | ~1 hr 00 min 08 sec (3608s) |
| Conftest | Session-scoped driver, function-scoped cu_page fixture |
| Report | Auto-generated Excel via CSReportStore |

---

## 8. Config Imports

```python
from config import (
    RHYTHMERP_BASE_URL,
    RHYTHMERP_LOGIN_URL,
    RHYTHMERP_EMAIL,
    RHYTHMERP_PASSWORD,
    EXPLICIT_WAIT
)
```

### Base Class
```python
from common.base_page import BasePage
```

### Logger
```python
from common.logger import log
```

### Browser Driver
```python
from common.browser_utils import get_driver
```

### Report Generator
```python
from pages.common_settings.cs_report_generator import CSReportStore, generate_cs_report
```

---

## 9. Key Differences from Agent and Bank Screens

| Feature | Customer | Agent | Bank |
|---|---|---|---|
| **Form Layout** | Universal + 3-step stepper | 4-step stepper | Simple popup (no stepper) |
| **Stepper Type** | Non-linear (BUG-002) | Linear (locked tabs) | N/A |
| **Universal Fields** | 9 fields ABOVE stepper | Inside Step 1 | All in popup |
| **Address Grid** | Step 1 (cascading dropdowns) | Step 2 (cascading dropdowns) | N/A |
| **Bank Grid** | Step 2 | Step 4 | N/A (single row) |
| **Unique Field** | PAN Number (server-side) | Agent Name | Bank Name |
| **Status Toggle** | OUTSIDE stepper | Inside Step 1 | Inside popup |
| **mat-select BUG** | Critical (BUG-001) | Present | Critical (BUG-004) |
| **Row Actions** | 3-dot menu trigger | Column buttons | Column buttons |
| **No Delete** | Confirmed | Confirmed | Confirmed |
| **Step Headers Clickable** | Yes (CU-P07) | No (locked) | N/A |

---

## 10. Lessons Learned

1. **Non-linear stepper is the biggest gotcha** — Unlike Agent where steps are locked, Customer's stepper allows free navigation. Validation only fires on Submit. Tests must account for this by filling all steps before submitting.

2. **Universal fields outside stepper** — Company Name, Email, Phone, PAN, and all dropdowns are NOT inside any step. They must be filled before navigating.

3. **BUG-001 requires JS workaround for ALL dropdowns** — Every mat-select must use the JS click pattern (open via label click, select via option click in overlay). Without this, form submission always fails with "Validation Failed".

4. **PAN Number is server-side unique** — Cannot create two customers with the same PAN. Tests must generate unique PAN for each customer.

5. **3-dot menu for row actions** — Unlike Agent/Bank which have direct View/Edit/History column buttons, Customer uses a 3-dot menu trigger that opens a dropdown with action options.

6. **Address and Bank grids are repeatable** — Each has an "add" button (mat-mdc-icon-button mat-primary with mat-icon='add'). Address grid uses the first add button, Bank grid uses the second.

7. **Header asterisk bugs (BUG-003, BUG-004)** — Several fields show asterisks in grid headers suggesting they're required, but the HTML inputs have required=false. Submit succeeds without them. This is a UI inconsistency, not a functional bug.

8. **Execution time is ~1 hour** — Customer tests take significantly longer than Agent (~25 min) due to more complex form filling (9 universal dropdowns + 11 step0 fields + address grid with 5 cascading dropdowns + bank grid).
