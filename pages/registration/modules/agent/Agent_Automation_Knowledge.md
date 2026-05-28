# Agent Screen Automation — Knowledge Document

## Project: RhythmERP PACS Automation
### Module: Registration > Agent
### Automation Date: 2026-05-25
### Status: 55 tests — 53 PASSED, 2 XPASS

---

## 1. Screen Overview

| Property | Value |
|---|---|
| **Module** | Registration |
| **Screen** | Agent |
| **URL** | `/#/dynamic-screens/Agent` |
| **Form Type** | Multi-Step Stepper Popup (4 steps) |
| **Framework** | Angular Material |
| **Popup Selector** | `.edit_pop_up.override_edit_pop_up.popup-mode` |
| **Login** | `Assistant@mail.com` / `Vedant@12345` |
| **Facility** | `RuralLife Producer Company` (index 0) |

### Stepper Steps

The Agent form is a **4-step stepper popup**. Users must complete each step before advancing. Steps cannot be skipped (locked tabs have `aria-disabled="true"` until the previous step is completed).

| Step | Tab Label | Key Fields | Required Fields |
|---|---|---|---|
| 1 | Universal | Agent Name, Phone Number, Email, Status | Agent Name, Phone Number |
| 2 | Address Details | Country, State, District, Taluka, Village, Address, Pin Code, GST Number | Country, State, District, Taluka, Address |
| 3 | Payment Details | Payment Terms, Preferred Payment Method | None (all optional) |
| 4 | Bank Details | Bank Name, Branch, IFSC Code, Account Type, Account Holder Name, Account Number, Bank Proof | Bank Name, Account Type, Account Holder Name, Account Number |

### Row Actions

| Action | Available | Notes |
|---|---|---|
| View | Yes | Opens form in read-only mode |
| Edit | Yes | Opens form in edit mode with Update button |
| History | Yes | Opens audit trail popup |
| Delete | No | No delete functionality exists |

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
    var inputs = document.querySelectorAll('.edit_pop_up input');
    var result = {};
    inputs.forEach(function(inp) {
        result[inp.name || inp.placeholder || inp.type] = inp.value;
    });
    return result;
    """
    return self.driver.execute_script(js)
```

### R03: mat-select Dropdown Handling
**NEVER use direct Selenium clicks on mat-select elements.** Angular Material dropdowns require JS to open the panel and select options:

```python
def _open_dropdown_by_label(self, label):
    js = """
    var label = document.querySelector("mat-label");
    var labels = document.querySelectorAll("mat-label");
    for (var i = 0; i < labels.length; i++) {
        if (labels[i].textContent.includes(arguments[0])) {
            labels[i].click();
            break;
        }
    }
    """
    self.driver.execute_script(js, label)
    time.sleep(0.5)  # Wait for overlay panel to open

def _select_option_by_text(self, option_text):
    js = """
    var options = document.querySelectorAll('mat-option');
    for (var i = 0; i < options.length; i++) {
        if (options[i].textContent.trim() === arguments[0]) {
            options[i].click();
            break;
        }
    }
    """
    self.driver.execute_script(js, option_text)
```

### R04: Cascading Dropdowns
Address section has cascading dropdowns: **Country > State > District > Taluka > Village**. After each selection, wait for the next dropdown to populate:

```python
def _select_cascading_dropdown(self, label, option_text):
    self._open_dropdown_by_label(label)
    time.sleep(1)  # Extra wait for cascading data
    self._select_option_by_text(option_text)
    time.sleep(1.5)  # Wait for next level to cascade
```

### R05: Stepper Navigation
Use JavaScript to click Next/Back buttons for reliability:

```python
def click_next(self):
    js = """
    var btn = document.querySelector('button.mat-stepper-next');
    if (btn) { btn.scrollIntoView(true); btn.click(); }
    """
    self.driver.execute_script(js)
    time.sleep(1)

def click_back(self):
    js = """
    var btn = document.querySelector('button.mat-stepper-previous');
    if (btn) { btn.click(); }
    """
    self.driver.execute_script(js)
    time.sleep(1)
```

### R06: SweetAlert2 Handling
The application uses SweetAlert2 for success and validation messages:

```python
def get_swal_title(self):
    try:
        title = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#swal2-title"))
        )
        return title.text
    except:
        return None

def handle_validation_warning(self):
    title = self.get_swal_title()
    if title and ("Validation" in title or "Failed" in title or "Error" in title):
        confirm = self.driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
        confirm.click()
        return True
    return False
```

### R07: No Keys.ESCAPE
**NEVER use `Keys.ESCAPE`** to close dropdowns or modals. Use JavaScript DOM removal instead:

```python
def force_close_form_popup(self):
    js = "var el = document.querySelector('.edit_pop_up'); if (el) el.remove();"
    self.driver.execute_script(js)
```

---

## 3. Test Suite Structure

### File Structure
```
pages/registration/modules/agent/
    agent_page.py              # Page Object Model
    data/
        agent_data.py          # Test data generators
    test/
        conftest.py            # pytest fixtures + CSReportStore
        test_agent_validation.py  # 55 tests across 7 phases
    reports/                   # Auto-generated Excel reports
```

### Test Phases Summary

| Phase | Class | Tests | IDs | Focus |
|---|---|---|---|---|
| 1 | TestUniversalStepValidations | 15 | AGT-U01 to U15 | Required fields, valid/invalid inputs, boundary, security |
| 2 | TestAddressStepValidations | 10 | AGT-A01 to A10 | Cascading dropdowns, pin code, GST, navigation |
| 3 | TestPaymentStepValidations | 5 | AGT-P01 to P05 | Optional fields, dropdown options, navigation |
| 4 | TestBankDetailsValidations | 10 | AGT-B01 to B10 | Bank fields, IFSC, empty submit, navigation |
| 5 | TestStepperNavigation | 5 | AGT-N01 to N05 | Step count, labels, no-skip, full navigation, cancel |
| 6 | TestCreateHappyPath | 5 | AGT-C01 to C05 | Valid/minimal create, read values, duplicate, refresh |
| 7 | TestBugSpecific | 5 | AGT-X01 to X05 | JS value read, state preservation, rapid clicks |

### Test Results: 53 PASSED, 2 XPASS

| ID | Test Name | Result | Notes |
|---|---|---|---|
| AGT-U13 | SQL Injection | **XPASS** | BUG: `'; DROP TABLE Agent; --` was ACCEPTED |
| AGT-U14 | XSS Payload | **XPASS** | BUG: `<script>alert('xss')</script>` was ACCEPTED |
| All others | — | PASSED | — |

---

## 4. Known Bugs

### AGT-BUG-001: SQL Injection Accepted (Critical)
- **Severity:** Critical
- **Category:** Security
- **Test Reference:** AGT-U13
- **Description:** When a SQL injection payload (`'; DROP TABLE Agent; --`) is entered as the Agent Name, the server accepts it without sanitization and creates the agent successfully. This indicates no server-side input validation or sanitization for SQL injection patterns.
- **Expected:** Server should reject or sanitize SQL injection payloads.
- **Actual:** Agent created with the malicious name. No error returned.

### AGT-BUG-002: XSS Payload Accepted (Critical)
- **Severity:** Critical
- **Category:** Security
- **Test Reference:** AGT-U14
- **Description:** When an XSS payload (`<script>alert('xss')</script>`) is entered as the Agent Name, the server accepts it and creates the agent. This is a stored XSS vulnerability — when the agent name is rendered in the table or any view, the script tag could execute in another user's browser.
- **Expected:** Server should reject or sanitize HTML/JavaScript tags in input fields.
- **Actual:** Agent created with script tag. Stored XSS vulnerability confirmed.

---

## 5. Field Reference

### Step 1: Universal

| Field | Type | Required | Max Length | Valid Pattern | Notes |
|---|---|---|---|---|---|
| Agent Name | text input | Yes | 255 | Alphanumeric + spaces | Leading/trailing spaces trimmed |
| Phone Number | number input | Yes | - | Digits only | 10-digit Indian mobile |
| Email | text input | No | 255 | Standard email format | Optional |
| Status | toggle | No | - | Active/Inactive | Default: Active |

### Step 2: Address Details (Repeatable Rows)

| Field | Type | Required | Max Length | Notes |
|---|---|---|---|---|
| Country | mat-select | Yes | - | 30 countries, cascades to State |
| State | mat-select | Yes | - | 36 states (India), cascades from Country |
| District | mat-select | Yes | - | Dynamic, cascades from State |
| Taluka | mat-select | Yes | - | Dynamic, cascades from District |
| Village | mat-select | No | - | Dynamic, cascades from Taluka |
| Address | text input | Yes | 255 | Alphanumeric + spaces |
| Pin Code | text input | No | 255 | 6-digit numeric |
| GST Number | text input | No | 255 | 15-char GST format |

### Step 3: Payment Details

| Field | Type | Required | Options |
|---|---|---|---|
| Payment Terms | mat-select | No | 21 Days, 14 Days, 7 Days, Wallet, RTGS, Advance, Immediate, 60 Days, 30 Days |
| Preferred Payment Method | mat-select | No | RTGS, IMPS, DD, Cheque, Cash |

### Step 4: Bank Details (Repeatable Rows)

| Field | Type | Required | Max Length | Notes |
|---|---|---|---|---|
| Bank Name | text input | Yes | 255 | Free text |
| Branch | text input | No | 255 | Free text |
| IFSC Code | text input | No | 255 | 11-char format (4 alpha + 7 alphanumeric) |
| Account Type | mat-select | Yes | - | Current, Saving |
| Account Holder Name | text input | Yes | 255 | Free text |
| Account Number | text input | Yes | 255 | Numeric, 10-16 digits |
| Bank Proof | mat-select | No | - | Cancelled Cheque, Passbook |

---

## 6. Dropdown Options Reference

| Dropdown | Total Options | Options |
|---|---|---|
| Country | 30 | Saudi Arabia, South Africa, Argentina, India, Turkey, Egypt, United States, United Kingdom, Canada, Australia, Germany, France, Japan, China, Brazil, Russia, Italy, Spain, Mexico, South Korea, Indonesia, Netherlands, Switzerland, Sweden, Norway, Denmark, Thailand, Malaysia, Singapore, New Zealand |
| State (India) | 36 | Ladakh, Andhra Pradesh, Jammu and Kashmir, Himachal Pradesh, Punjab, Chandigarh, Uttarakhand, Haryana, Delhi, Rajasthan, Uttar Pradesh, Bihar, Sikkim, Arunachal Pradesh, Nagaland, Manipur, Mizoram, Tripura, Meghalaya, Assam, West Bengal, Jharkhand, Odisha, Chhattisgarh, Madhya Pradesh, Gujarat, Dadra & Nagar Haveli and Daman & Diu, Maharashtra, Karnataka, Goa, Lakshadweep, Kerala, Tamil Nadu, Puducherry, Andaman & Nicobar Islands, Telangana |
| Payment Terms | 9 | 21 Days, 14 Days, 7 Days, Wallet, RTGS, Advance, Immediate, 60 Days, 30 Days |
| Preferred Payment Method | 5 | RTGS, IMPS, DD, Cheque, Cash |
| Account Type | 2 | Current, Saving |
| Bank Proof | 2 | Cancelled Cheque, Passbook |

---

## 7. Execution Guide

### Run All Tests
```powershell
python -m pytest pages/registration/modules/agent/test/test_agent_validation.py -v --tb=short
```

### Run Specific Phase
```powershell
# Phase 1: Universal
python -m pytest pages/registration/modules/agent/test/test_agent_validation.py::TestUniversalStepValidations -v

# Phase 2: Address
python -m pytest pages/registration/modules/agent/test/test_agent_validation.py::TestAddressStepValidations -v

# Phase 6: Happy Path only
python -m pytest pages/registration/modules/agent/test/test_agent_validation.py::TestCreateHappyPath -v
```

### Run Individual Test
```powershell
python -m pytest pages/registration/modules/agent/test/test_agent_validation.py::TestCreateHappyPath::test_AGT_C01_valid_create -v
```

### Generate HTML Report
```powershell
python -m pytest pages/registration/modules/agent/test/test_agent_validation.py -v --html=agent_report.html --self-contained-html
```

### Execution Environment
| Property | Value |
|---|---|
| Python | 3.14.3 |
| pytest | 9.0.2 |
| Browser | Microsoft Edge (WebDriver) |
| OS | Windows 11 (10.0.26200) |
| Execution Time | ~24 min 39s (1479s) |
| Conftest | Session-scoped driver, function-scoped page fixture |
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

## 9. Lessons Learned from Bank Screen (Applied to Agent)

1. **Angular Material inputs require JS value-setter** — `send_keys()` and `get_attribute('value')` do not work. This was the #1 lesson from the Bank screen automation (BUG-004) and is baked into every Agent method.

2. **mat-select clicks don't sync Angular form model** — Direct Selenium clicks on mat-option may visually select but fail to update the reactive form. Always use JS to open the dropdown panel and click options in the overlay.

3. **Cascading dropdowns need extra wait** — After selecting a parent dropdown option, the child dropdown needs time to load data from the API. Always add a 1-2 second wait between cascading selections.

4. **Stepper navigation needs JS** — Angular Material stepper buttons don't reliably respond to Selenium's `element.click()`. Use `execute_script` to click Next/Back buttons.

5. **Never use Keys.ESCAPE** — Can cause unpredictable behavior with Angular overlays. Use DOM manipulation instead.

6. **State leakage is real** — Always verify that closing and reopening a form produces a clean state. Previous form data can persist in Angular components.
