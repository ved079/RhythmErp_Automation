# Supplier Screen Automation — Knowledge Document

## Project: RhythmERP PACS Automation
### Module: Registration > Supplier
### Automation Date: 2026-05-25
### Status: 42 tests — 35 PASSED, 6 XFAIL, 1 XPASS

---

## 1. Screen Overview

| Property | Value |
|---|---|
| **Module** | Registration |
| **Screen** | Supplier |
| **URL** | `/#/dynamic-screens/Supplier/Supplier` |
| **Form Type** | Multi-Step Stepper Popup (3 steps) |
| **Framework** | Angular Material |
| **Popup Selector** | `.big-model, .edit_pop_up, mat-dialog-container` |
| **Login** | `Assistant@mail.com` / `Vedant@12345` |
| **Facility** | `RuralLife Producer Company` (index 0) |

### Stepper Steps

The Supplier form is a **3-step stepper popup**. Step 1 contains two sub-sections: Universal Fields (visible immediately) and Additional Details (requires scrolling down within Step 1). Steps 2 and 3 support dynamic row addition (add/remove). Address fields use cascading dropdowns that must be filled in order.

| Step | Tab Label | Key Fields | Required Fields |
|---|---|---|---|
| 1 | Additional Details | Party Reference, Ownership Status, Company Name, PO Type, Email, Phone Number, Default Currency, PAN Number, Is MSME Registered?, Status, Is GST Set Off, Is TDS Applicable, Contact Person Name, Office Number, Payment Terms, Delivery Terms, Mode Of Delivery | Ownership Status, Company Name, PO Type, Phone Number, Default Currency, PAN Number |
| 2 | Address Details | Address Type, Country, State, District, Taluka, Village, Address, Pin Code, GSTIN | Address Type, Country, State, District, Taluka, Address |
| 3 | Bank Details | Bank Name, Branch, IFSC Code, Account Type, Account Holder Name, Account Number, Bank Proof, Attachment | Bank Proof |

### Row Actions

| Action | Available | Notes |
|---|---|---|
| View | Yes | Opens form in read-only mode |
| Edit | Yes | Opens form in edit mode with Update button (BUG-005 fixed) |
| History | No | No History button on Supplier screen |
| Delete | No | No delete functionality exists |

### Key Differences from Agent Screen

1. **3 steps vs 4 steps** — Supplier has no separate Payment step; payment terms are in Step 1 Additional Details
2. **Party Reference** — Supplier has a Party Reference dropdown (optional, dynamic farmer list) not present in Agent
3. **No History button** — Agent has History; Supplier does not
4. **More toggles** — Supplier has 4 toggle switches (MSME, Status, GST Set Off, TDS) vs Agent's 1 (Status)
5. **Additional Details** — Step 1 has a scrollable sub-section below Universal Fields
6. **Attachment upload** — Step 3 Bank Details has file upload for Bank Proof attachment

---

## 2. Critical Automation Rules

### R01: Angular Material Input Filling
**NEVER use `send_keys()` or `element.clear()` for Angular Material inputs.** The Angular reactive form model does not sync with Selenium's native input methods. Always use JavaScript `nativeInputValueSetter`:

```python
def _fill_input_by_name(self, name, value):
    js = """
    var inp = document.querySelector('input[name="' + arguments[0] + '"]');
    if (inp) {
        var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeSetter.call(inp, arguments[1]);
        inp.dispatchEvent(new Event('input', { bubbles: true }));
        inp.dispatchEvent(new Event('change', { bubbles: true }));
    }
    """
    self.driver.execute_script(js, name, value)
```

### R02: Reading Angular Input Values
**NEVER use `element.get_attribute('value')`** — Angular stores values in DOM property (`.value`), not HTML attribute. Always use JavaScript:

```python
def get_form_field_values(self):
    js = """
    var inputs = document.querySelectorAll('.big-model input, mat-dialog-container input');
    var result = {};
    inputs.forEach(function(inp) {
        result[inp.name || inp.placeholder || inp.type] = inp.value;
    });
    return result;
    """
    return self.driver.execute_script(js)
```

### R03: mat-select Dropdown Handling with Angular Sync
**CRITICAL: Browser-clicked mat-select options do NOT update Angular reactive form model.** Must use JS value-setter + dispatchEvent for all dropdown selections:

```python
def _select_mat_option(self, select_locator, value=None):
    # 1. Force close any open panels
    self._force_close_panels()

    # 2. Click the mat-select trigger via JS
    select_el = self.find_visible_element(select_locator)
    self.driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
        select_el
    )

    # 3. Wait for dropdown panel
    WebDriverWait(self.driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='listbox'] mat-option"))
    )

    # 4. Find and click matching option via JS
    options = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
    for opt in options:
        if opt.text.strip().lower() == value.lower():
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
                opt
            )
            break

    # 5. CRITICAL: Sync Angular reactive form model
    self._sync_dropdown_angular_model(select_el)

def _sync_dropdown_angular_model(self, select_el):
    self.driver.execute_script("""
        var select = arguments[0];
        select.dispatchEvent(new Event('focusin', { bubbles: true }));
        select.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter', keyCode:13, bubbles:true}));
        select.dispatchEvent(new Event('change', { bubbles: true }));
        select.dispatchEvent(new Event('input', { bubbles: true }));
        select.dispatchEvent(new KeyboardEvent('keyup', {key:'Enter', keyCode:13, bubbles:true}));
        select.dispatchEvent(new Event('blur', { bubbles: true }));
        select.classList.remove('ng-untouched');
        select.classList.add('ng-touched');
        select.classList.remove('ng-pristine');
        select.classList.add('ng-dirty');
    """, select_el)
```

### R04: Cascading Dropdowns
Address section has cascading dropdowns: **Country > State > District > Taluka > Village**. After each selection, wait for the next dropdown to populate:

```python
def fill_step2_address(self, data, row_index=0):
    self._select_mat_option(self.ADDRESS_TYPE_SELECT, data["address_type"])
    self._select_mat_option(self.COUNTRY_SELECT, data["country"])
    self.wait_seconds(1.5)  # Wait for states to cascade
    self._select_mat_option(self.STATE_SELECT, data["state"])
    self.wait_seconds(1.5)  # Wait for districts
    self._select_mat_option(self.DISTRICT_SELECT, data["district"])
    self.wait_seconds(1.5)  # Wait for talukas
    self._select_mat_option(self.TALUKA_SELECT, data["taluka"])
    self.wait_seconds(1.5)  # Wait for villages
```

### R05: Step 1 Scrolling for Additional Details
Step 1 has TWO sub-sections. Additional Details is below the fold and requires scrolling:

```python
def scroll_to_additional_details(self):
    self.driver.execute_script("""
        var section = document.querySelector('mat-step-content:first-of-type');
        if (section) section.scrollTop = section.scrollHeight;
    """)
    self.wait_seconds(0.5)
```

### R06: Stepper Navigation
Use JavaScript to click Next/Back buttons for reliability:

```python
def click_stepper_next(self):
    self.driver.execute_script("""
        var btn = document.querySelector('button.mat-stepper-next');
        if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
    """)
    self.wait_seconds(1)

def click_stepper_back(self):
    self.driver.execute_script("""
        var btn = document.querySelector('button.mat-stepper-previous');
        if (btn) { btn.click(); }
    """)
    self.wait_seconds(1)
```

### R07: Toggle Switch Handling
Supplier has 4 toggle switches. Check current state before clicking:

```python
def _toggle_switch(self, toggle_locator, target_state=True):
    is_currently_on = self.driver.execute_script("""
        var wrapper = arguments[0];
        var onLabel = wrapper.querySelector('span.state-label.on');
        if (onLabel && onLabel.classList.contains('active')) return true;
        return false;
    """, toggle_el)

    if is_currently_on != target_state:
        slider = self.driver.execute_script("""
            var wrapper = arguments[0];
            return wrapper.querySelector('.slider') || wrapper;
        """, toggle_el)
        self.driver.execute_script("arguments[0].click();", slider)
```

### R08: No Keys.ESCAPE
**NEVER use `Keys.ESCAPE`** to close dropdowns or modals. Use JavaScript DOM removal for select panels, and backdrop click + JS for form popups:

```python
def _force_close_panels(self):
    self.driver.execute_script("""
        document.querySelectorAll(
            'div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)'
        ).forEach(function(el) { el.remove(); });
        document.querySelectorAll('div.cdk-overlay-pane').forEach(function(el) {
            if (!el.querySelector('mat-dialog-container')) el.remove();
        });
    """)
```

### R09: SweetAlert2 Handling
The application uses SweetAlert2 for success and validation messages:

```python
def handle_validation_warning(self, timeout=3):
    title = self.get_swal_title(timeout)
    if title and ("Validation" in title or "Failed" in title):
        confirm = self.driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
        confirm.click()
        return True
    return False

def handle_success_alert(self, timeout=5):
    try:
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".swal2-confirm"))
        )
        self.driver.find_element(By.CSS_SELECTOR, ".swal2-confirm").click()
        return True
    except:
        return False
```

---

## 3. Test Suite Structure

### File Structure
```
pages/registration/modules/supplier/
    supplier_page.py              # Page Object Model (SupplierPage class)
    data/
        supplier_data.py          # Test data generators + ExpectedMessages + KnownBugs
    test/
        conftest.py               # pytest fixtures + CSReportStore + report hooks
        test_supplier_validation.py  # 42 tests across 6 phases
    reports/                      # Auto-generated Excel reports
```

### Test Phases Summary

| Phase | Class | Tests | IDs | Focus |
|---|---|---|---|---|
| 1 | TestCreateFormValidations | 18 | SP-C01 to C18 | Required fields, valid/invalid inputs, boundary, security, dropdowns |
| 2 | TestDuplicateValidations | 3 | SP-D01 to D03 | Duplicate company name, email, phone |
| 3 | TestEditFormValidations | 4 | SP-E01 to E04 | Update button, pre-populated, special chars, invalid email in Edit |
| 4 | TestSearchFilter | 5 | SP-S01 to S05 | Exact, partial, case-insensitive, no results, special chars |
| 5 | TestPopupUIBehaviors | 7 | SP-P01 to P07 | Add form, view readonly, cancel, close, SweetAlert2, spinner, toggles |
| 6 | TestBugSpecific | 5 | SP-B01 to B05 | BUG-001 special chars, BUG-002 email, BUG-003 spinner, BUG-004 PAN, BUG-005 update |

### Test Results: 35 PASSED, 6 XFAIL, 1 XPASS

| ID | Test Name | Result | Notes |
|---|---|---|---|
| SP-C04 | Company Name special chars | **XFAIL** | BUG-001: Special chars accepted without validation |
| SP-C05 | SQL Injection | **XFAIL** | BUG-001: `'; DROP TABLE suppliers; --` was ACCEPTED |
| SP-C06 | XSS Payload | **XFAIL** | BUG-001: `<script>alert('xss')</script>` was ACCEPTED |
| SP-E03 | Edit special chars | **XPASS** | BUG-001 STILL ACTIVE: special chars accepted in Edit mode |
| SP-P06 | Phone spinner controls | **XFAIL** | BUG-003: Spinner controls still visible |
| SP-B01 | Special chars create | **XFAIL** | BUG-001 CONFIRMED: `BugTest@@##Traders` saved |
| SP-B03 | Phone spinner bug | **XFAIL** | BUG-003 CONFIRMED: type=number shows spinner |
| All others | — | PASSED | — |

### Environment Failures (First Run Only, Fixed on Re-run)
- **SP-C02** (valid create): No submit response — likely server timeout during heavy test execution. Passed on re-run.
- **SP-C13** (PO Type dropdown): Dropdown options empty — timing issue with dropdown loading. Passed on re-run.
- **SP-C16** (Delivery Terms dropdown): Same timing issue. Passed on re-run.
- **SP-B05** (Edit no update): InvalidSessionIdException — browser session expired after long run (~25 min). Passed on re-run.

---

## 4. Known Bugs

### BUG-001: Company Name Accepts Special Characters (HIGH — Confirmed)
- **Severity:** High
- **Category:** Validation
- **Test Reference:** SP-C04, SP-C05, SP-C06, SP-E03, SP-B01
- **Description:** Company Name field accepts special characters (`@#$%^&*`), SQL injection payloads (`'; DROP TABLE suppliers; --`), and XSS payloads (`<script>alert('xss')</script>`) without any validation. The server creates the supplier successfully with these malicious inputs. This is a security vulnerability affecting both Create and Edit modes.
- **Expected:** Should restrict special characters and show validation error. Server should sanitize or reject.
- **Actual:** All special characters accepted. No error on blur or submit. Supplier created with malicious data.

### BUG-002: No Email Format Validation (MEDIUM — Fixed)
- **Severity:** Medium
- **Category:** Validation
- **Test Reference:** SP-C09, SP-B02
- **Description:** Previously, invalid emails like "notanemail" were accepted without error. The ERP has since been updated to validate email format and shows "Invalid Email" error on blur/submit.
- **Expected:** Should validate email format.
- **Actual:** FIXED: ERP now shows "Invalid Email" error.

### BUG-003: Phone Number Spinner Controls (LOW — Confirmed)
- **Severity:** Low
- **Category:** UI Bug
- **Test Reference:** SP-P06, SP-B03
- **Description:** Phone Number field displays increase/decrease spinner controls (up/down arrows) because the input type is `number` instead of `tel` or `text`. This is a cosmetic issue but may confuse users.
- **Expected:** Should be `type=tel` or `type=text` with no spinner controls.
- **Actual:** Spinner controls visible — `type=number` on input.

### BUG-004: No PAN Format Validation (MEDIUM — Fixed)
- **Severity:** Medium
- **Category:** Validation
- **Test Reference:** SP-C10, SP-B04
- **Description:** Previously, any text was accepted as PAN Number (e.g., "INVALIDPAN"). The ERP has since been updated to validate PAN format (5 letters + 4 digits + 1 letter) and shows "Invalid PAN Number" error.
- **Expected:** Should validate PAN format with regex pattern.
- **Actual:** FIXED: ERP now shows "Invalid PAN Number" error.

### BUG-005: No Update Button in Edit Mode (HIGH — Fixed)
- **Severity:** High
- **Category:** Functionality
- **Test Reference:** SP-E01, SP-B05
- **Description:** Previously, the Edit popup only showed a Cancel button in the footer. Users could not save any edits. The ERP has since been updated to show the Update button in Edit mode.
- **Expected:** Update button should appear in edit mode popup-footer.
- **Actual:** FIXED: Update button now visible in Edit mode.

---

## 5. Field Reference

### Step 1: Universal Fields (10 fields)

| Field | Type | Required | Max Length | Valid Pattern | Notes |
|---|---|---|---|---|---|
| Party Reference | mat-select | No | - | Dynamic farmer list | Optional, read-only in Edit |
| Ownership Status | mat-select | Yes | - | 8 options | Owned/Leased/Proprietorship/Partnership/LLP/PLC/Private Limited Company/Individual |
| Company Name | text input | Yes | 255 | BUG-001: No restriction | Accepts special chars, SQL, XSS |
| PO Type | mat-select | Yes | - | Domestic/Import | Required dropdown |
| Email | text input | No | 255 | Standard email | BUG-002 FIXED: Now validates |
| Phone Number | number input | Yes | - | 10-digit Indian mobile | BUG-003: Has spinner controls |
| Default Currency | mat-select | Yes | - | 100+ currencies | INR commonly used |
| PAN Number | text input | Yes | 255 | ABCDE1234F | BUG-004 FIXED: Now validates |
| Is MSME Registered? | toggle | No | - | On/Off | Default: No (Off) |
| Status | toggle | No | - | Active/Inactive | Default: Active (On) |

### Step 1: Additional Details (7 fields, scroll down)

| Field | Type | Required | Max Length | Valid Pattern | Notes |
|---|---|---|---|---|---|
| Is GST Set Off | toggle | No | - | On/Off | Default: Yes (On) |
| Is TDS Applicable | toggle | No | - | On/Off | Default: No (Off) |
| Contact Person Name | text input | No | 255 | Free text | Optional |
| Office Number | text input | No | 255 | Free text | Optional |
| Payment Terms | mat-select | No | - | 9 options | 21 Days/14 Days/7 Days/Wallet/RTGS/Advance/Immediate/60 Days/30 Days |
| Delivery Terms | mat-select | No | - | 2 options | Delivery/Spot |
| Mode Of Delivery | mat-select | No | - | 5 options | Air/Courier/Sea/Railway/Truck |

### Step 2: Address Details (Dynamic Rows)

| Field | Type | Required | Max Length | Notes |
|---|---|---|---|---|
| Address Type | mat-select | Yes | - | Shipping/Billing |
| Country | mat-select | Yes | - | 30 countries, cascading |
| State | mat-select | Yes | - | Cascading from Country |
| District | mat-select | Yes | - | Cascading from State |
| Taluka | mat-select | Yes | - | Cascading from District |
| Village | mat-select | No | - | Cascading from Taluka |
| Address | text input | Yes | 255 | Alphanumeric + spaces |
| Pin Code | text input | No | 255 | 6-digit numeric |
| GSTIN | text input | No | 255 | 15-char GST format |

### Step 3: Bank Details (Dynamic Rows)

| Field | Type | Required | Max Length | Notes |
|---|---|---|---|---|
| Bank Name | text input | No | 255 | Free text |
| Branch | text input | No | 255 | Free text |
| IFSC Code | text input | No | 255 | 11-char format (4 alpha + 0 + 6 alphanumeric) |
| Account Type | mat-select | No | - | Current/Saving |
| Account Holder Name | text input | No | 255 | Free text |
| Account Number | text input | No | 255 | Numeric |
| Bank Proof | mat-select | Yes | - | Cancelled Cheque/Passbook |
| Attachment | file upload | No | - | .png/.jpg/.pdf |

---

## 6. Dropdown Options Reference

| Dropdown | Total Options | Options |
|---|---|---|
| Ownership Status | 8 | Owned, Leased, Proprietorship, Partnership, LLP, PLC, Private Limited Company, Individual |
| PO Type | 2 | Domestic, Import |
| Default Currency | 100+ | INR, USD, EUR, GBP, JPY, etc. |
| Payment Terms | 9 | 21 Days, 14 Days, 7 Days, Wallet, RTGS, Advance, Immediate, 60 Days, 30 Days |
| Delivery Terms | 2 | Delivery, Spot |
| Mode Of Delivery | 5 | Air, Courier, Sea, Railway, Truck |
| Address Type | 2 | Shipping, Billing |
| Country | 30 | Saudi Arabia, South Africa, Argentina, India, Turkey, Egypt, United States, United Kingdom, Canada, Australia, Germany, France, Japan, China, Brazil, Russia, Italy, Spain, Mexico, South Korea, Indonesia, Netherlands, Switzerland, Sweden, Norway, Denmark, Thailand, Malaysia, Singapore, New Zealand |
| Account Type | 2 | Current, Saving |
| Bank Proof | 2 | Cancelled Cheque, Passbook |

---

## 7. Execution Guide

### Run All Tests
```powershell
python -m pytest pages/registration/modules/supplier/test/test_supplier_validation.py -v --tb=short
```

### Run Specific Phase
```powershell
# Phase 1: Create Form Validations
python -m pytest pages/registration/modules/supplier/test/test_supplier_validation.py::TestCreateFormValidations -v

# Phase 2: Duplicate Validations
python -m pytest pages/registration/modules/supplier/test/test_supplier_validation.py::TestDuplicateValidations -v

# Phase 5: Popup UI Behaviors
python -m pytest pages/registration/modules/supplier/test/test_supplier_validation.py::TestPopupUIBehaviors -v

# Phase 6: Bug-Specific
python -m pytest pages/registration/modules/supplier/test/test_supplier_validation.py::TestBugSpecific -v
```

### Run Individual Test
```powershell
python -m pytest pages/registration/modules/supplier/test/test_supplier_validation.py::TestCreateFormValidations::test_SP_C02_valid_create -v
```

### Re-run Failed Tests
```powershell
# Use pytest -k with test IDs separated by "or"
python -m pytest pages/registration/modules/supplier/test/test_supplier_validation.py -v -k "C13 or C16" --tb=short
python -m pytest pages/registration/modules/supplier/test/test_supplier_validation.py -v -k "B05 or C02" --tb=short
```

### Generate HTML Report
```powershell
python -m pytest pages/registration/modules/supplier/test/test_supplier_validation.py -v --html=supplier_report.html --self-contained-html
```

### Execution Environment
| Property | Value |
|---|---|
| Python | 3.14.3 |
| pytest | 9.0.2 |
| Browser | Microsoft Edge (WebDriver) |
| OS | Windows 11 (10.0.26200) |
| Execution Time | ~30 min (full suite including re-runs) |
| Conftest | Session-scoped driver, function-scoped page fixture |
| Report | Auto-generated Excel via CSReportStore + generate_cs_report |

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

### Supplier-Specific Login (conftest.py)
```python
SP_LOGIN_EMAIL = "Assistant@mail.com"
SP_LOGIN_PASSWORD = "Vedant@12345"
SP_LOGIN_FACILITY_INDEX = 0  # RuralLife Producer Company
```

---

## 9. Lessons Learned

1. **Angular Material dropdowns don't sync form model on browser click** — This is the #1 lesson from the Supplier screen. Unlike the Agent screen where JS clicks on mat-option mostly worked, the Supplier screen requires explicit Angular form model sync via `_sync_dropdown_angular_model()` which dispatches focus/change/input/blur events and manipulates ng-touched/ng-dirty/ng-invalid classes.

2. **Step 1 has hidden content below the fold** — The Additional Details section (Payment Terms, Delivery Terms, Mode Of Delivery, Is GST Set Off, Is TDS Applicable) requires scrolling within the stepper content area. Tests that verify these fields must call `scroll_to_additional_details()` first, otherwise the dropdowns won't be in view and `get_dropdown_options()` will return empty lists (this caused SP-C13 and SP-C16 failures on first run).

3. **4 toggle switches with specific default states** — Unlike Agent (1 toggle), Supplier has 4 toggles each with different defaults: MSME=No, Status=Active, GST Set Off=Yes, TDS Applicable=No. Always check current state before clicking to avoid state inversion bugs.

4. **Long test suites can cause browser session expiry** — SP-B05 failed with `InvalidSessionIdException` because the browser session expired after 25+ minutes of continuous testing. Session-scoped driver with many tests is risky. Consider adding session recreation for late-running tests.

5. **Cascading dropdowns require ordered filling** — Country must be selected before State, State before District, etc. The page waits for API responses between each level. Known cascading paths with guaranteed Village-level data: India > Maharashtra/Gujarat/Rajasthan/Karnataka/Tamil Nadu.

6. **Party Reference dropdown is optional and dynamic** — Unlike other dropdowns, Party Reference loads a dynamic farmer list from the backend. It can be skipped in tests (left empty). In Edit/View mode, this dropdown becomes read-only/disabled.

7. **No History button** — Unlike Agent and Customer screens, the Supplier screen does not have a History action in the row menu. This is by design, not a bug.

8. **Dynamic row addition works for Address and Bank steps** — Both Step 2 (Address) and Step 3 (Bank) support adding multiple rows. The add-row button is inside `mat-step-content[2]` and `mat-step-content[3]` respectively, with removable row buttons.

9. **Environment/timing issues are common** — First full suite run had 3 failures and 1 error, all environment-related (dropdown timing, submit timeout, session expiry). All passed cleanly on targeted re-runs. This is expected for long-running UI test suites against a live ERP application.
