# The Angular Material Survival Guide

> **Read this before writing any page object code.** This document collects every hack, workaround, and hard-won lesson from fighting Angular Material with Selenium. It's the single biggest source of flaky tests in this project.

---

## The Core Problem

RhythmERP's frontend is built with **Angular Material** — Google's UI component library for Angular. These components look nice and work fine for humans clicking in a browser. But for Selenium automation, they are a nightmare.

Here's why: Angular Material components maintain an **internal reactive form model** that is separate from the DOM. When a human clicks a dropdown option, Angular's JavaScript updates the form model AND the DOM. When Selenium clicks, the DOM updates but **Angular's form model often does NOT**.

This means:
- You select "Current Account" from the Account Type dropdown
- The dropdown visually shows "Current Account"
- But Angular's form model still thinks the field is empty
- When you submit, Angular says "required field is missing"
- Your test fails with a confusing error

This problem affects **every mat-select, every mat-input, every toggle** in the ERP. The solutions below are what we've learned over months of debugging.

---

## Pattern 1: Setting mat-select Values

### The Problem
`mat-select` is Angular Material's custom dropdown. Clicking it opens a CDK overlay panel with `mat-option` elements. Selenium can click these options, but Angular's reactive form doesn't register the change.

### The Solution: JS Value-Setter + Event Dispatch

```python
def _sync_dropdown_angular_model(self, element, value):
    """Set a mat-select value and force Angular to recognize it."""
    script = """
    var select = arguments[0];
    var value = arguments[1];

    // Find the underlying Angular FormControl
    var formField = select.closest('mat-form-field');
    var ngControl = null;

    // Walk up to find the Angular component instance
    var parent = select;
    while (parent && !parent.__ngContext__) {
        parent = parent.parentElement;
    }

    // Set the value via Angular's model
    var setter = Object.getOwnPropertyDescriptor(
        HTMLElement.prototype, 'textContent'
    );

    // Dispatch ALL the events Angular listens to
    var events = ['focusin', 'keydown', 'change', 'input',
                  'keyup', 'focusout', 'blur'];
    events.forEach(function(eventName) {
        select.dispatchEvent(new Event(eventName, {bubbles: true}));
    });

    // Toggle CSS classes Angular uses for validation
    select.classList.remove('ng-untouched');
    select.classList.add('ng-touched');
    select.classList.remove('ng-pristine');
    select.classList.add('ng-dirty');
    select.classList.remove('ng-invalid');
    select.classList.add('ng-valid');
    """
    self.driver.execute_script(script, element, value)
```

### Why 8 Events?

We dispatch `focusin`, `keydown`, `change`, `input`, `keyup`, `focusout`, and `blur` because Angular's form control listens to different events at different lifecycle stages. Missing even one can cause the form model to not update. We also toggle CSS classes (`ng-untouched` → `ng-touched`, etc.) because Angular uses these to determine validation state.

This pattern was pioneered in the Supplier module and copied to Customer, Employee, and others. It's the most battle-tested hack in the repo.

### The Full Dropdown Interaction Sequence

For a reliable mat-select interaction, you need all 3 steps:

```python
def select_dropdown_option(self, label, option_text):
    # Step 1: Click the dropdown to open it
    dropdown = self.driver.find_element(
        By.XPATH, f"//mat-label[contains(.,'{label}')]/ancestor::mat-form-field//mat-select"
    )
    dropdown.click()

    # Step 2: Click the option from the CDK overlay
    option = self.wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//mat-option//span[contains(.,'{option_text}')]")
    ))
    option.click()

    # Step 3: Force Angular to recognize the change
    self._sync_dropdown_angular_model(dropdown, option_text)
```

Skipping step 3 is the #1 cause of "I selected the option but the form still says it's empty" failures.

---

## Pattern 2: Setting Input Values

### The Problem
Angular Material inputs (`mat-input`) use Angular's reactive forms. Selenium's `send_keys()` sometimes works, but often:
- The value appears in the DOM but Angular doesn't see it
- `element.clear()` doesn't work on Angular inputs
- Pasting via `Ctrl+A, Delete` leaves Angular's model out of sync

### The Solution: JS nativeInputValueSetter

```python
def _set_input(self, element, value):
    """Set an input's value using JavaScript native setter."""
    script = """
    var el = arguments[0];
    var val = arguments[1];

    // Use the native setter to bypass Angular's interceptor
    var nativeSetter = Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype, 'value'
    ).set;
    nativeSetter.call(el, val);

    // Tell Angular the value changed
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    el.dispatchEvent(new Event('blur', {bubbles: true}));
    """
    self.driver.execute_script(script, element, value)
```

### Why Not Just `send_keys()`?

Because `send_keys()` types character by character, which:
- Triggers Angular's change detection on every keystroke (slow)
- Can be intercepted by Angular's validators mid-type (causing partial values)
- Doesn't work at all on some Angular inputs that have custom value accessors

The JS setter sets the entire value atomically, then tells Angular about it once.

---

## Pattern 3: Closing CDK Overlay Panels

### The Problem
Angular Material uses CDK (Component Dev Kit) overlays for dropdowns, datepickers, and dialogs. When a dropdown opens, it creates a `cdk-overlay-container` with a `cdk-overlay-pane` inside. If you don't close these properly, they stack up and block other elements.

### The NEVER: Keys.ESCAPE

```python
# ❌ NEVER DO THIS
ActionChains(driver).send_keys(Keys.ESCAPE).perform()
```

**Why?** Because in this ERP, pressing Escape closes the entire popup form, not just the dropdown. You'll lose all the data you entered. This is documented as a hard rule in Bank, Vehicle Master, Season, Item Category, Item Group, and more.

### The RIGHT Way: Backdrop Click + JS Removal

```python
def _force_close_panels(self):
    """Close all open CDK overlay panels via JavaScript."""
    script = """
    // Remove overlay backdrops (the dark background)
    document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) {
        el.click();
    });

    // Wait briefly, then remove any remaining overlay panes
    setTimeout(function() {
        document.querySelectorAll('.cdk-overlay-pane').forEach(function(pane) {
            pane.remove();
        });
    }, 200);
    """
    self.driver.execute_script(script)
```

### ⚠️ CRITICAL WARNING: Never Remove `.cdk-overlay-container`

Tax Rate's page object documents this explicitly:

> "NEVER remove `.cdk-overlay-container` or `.cdk-overlay-pane` — kills Angular's overlay rendering engine permanently"

Once you remove the overlay container element from the DOM, Angular can't create new dropdown overlays for the rest of the session. All subsequent dropdown clicks will silently fail. The page becomes unusable until you refresh.

The safe approach is to:
1. Click the backdrop first (lets Angular close the overlay naturally)
2. Only remove individual `cdk-overlay-pane` elements if the backdrop click didn't work
3. NEVER remove `cdk-overlay-container`

---

## Pattern 4: Clicking Elements That Are "Not Clickable"

### The Problem
Selenium says an element "is not clickable" because something is overlapping it. In the ERP, this happens constantly:
- CDK overlay from a previous dropdown
- A SweetAlert dialog behind the current panel
- Angular's animation still in progress
- The search button is partially behind a toolbar

### The Solution: JS Click Everything

```python
def _js_click(self, element):
    """Click via JavaScript — bypasses all visibility/overlap checks."""
    self.driver.execute_script("arguments[0].click();", element)
```

For most interactions in this project, we default to JS clicks. Selenium's native `.click()` is only used when we specifically need to test that a human could click it (i.e., accessibility testing).

### The 3-Tier Click Strategy

Some page objects implement a tiered approach:

```python
def _click_element(self, locator):
    try:
        # Tier 1: Normal Selenium click
        element = self.wait.until(EC.element_to_be_clickable(locator))
        element.click()
    except (ElementClickInterceptedException, TimeoutException):
        try:
            # Tier 2: ActionChains click (moves to element first)
            element = self.driver.find_element(*locator)
            ActionChains(self.driver).move_to_element(element).click().perform()
        except:
            # Tier 3: JavaScript click (always works)
            element = self.driver.find_element(*locator)
            self.driver.execute_script("arguments[0].click();", element)
```

---

## Pattern 5: Handling SweetAlert2 Dialogs

### The Problem
The ERP uses SweetAlert2 for success/error messages. These appear as full-screen overlays that block all interaction until dismissed. Different modules use different SweetAlert patterns.

### The 3 SweetAlert Patterns

**Pattern A**: "Please correct highlighted fields" — Warning icon, OK button
```python
def _handle_pattern_a(self):
    ok_btn = self.driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
    ok_btn.click()
```

**Pattern B**: "Fields validation failed" / "Download Errors" — Cancel button
```python
def _handle_pattern_b(self):
    cancel_btn = self.driver.find_element(By.CSS_SELECTOR, ".swal2-cancel")
    cancel_btn.click()
```

**Pattern C**: Auto-dismissing error toast — no action needed
```python
# Just wait for it to disappear
time.sleep(1)
```

### Which Modules Use Which Pattern?

| Pattern | Modules |
|---------|---------|
| A + B | UOM, HSN SAC, UOM Conversion |
| Silent close (no SweetAlert) | Tax Rate, Tax Authority, Error Code Mst, Entity Group |
| Success SweetAlert | Bank, Supplier, Customer, Role Creation |
| Custom per action | Farmer (varies by tab) |

**Always check which pattern your module uses** before writing alert handling code. Don't assume a success SweetAlert appears — many modules silently close the form on success.

---

## Pattern 6: Row-Scoped Locators for Repeating Sections

### The Problem
Modules like Supplier and Customer have repeating address rows and bank rows. When there are 2 address rows, a generic XPath like:

```python
ADDRESS_TYPE_SELECT = ("xpath", "//mat-label[contains(.,'Address Type')]/ancestor::mat-form-field//mat-select")
```

Will ALWAYS match the first row's dropdown. When you try to fill the second row, you end up modifying the first row again.

### The Solution: Row-Index-Scoped XPaths

```python
def fill_address_row(self, row_index, data):
    """Fill a specific address row by its 1-based index."""
    row_xpath = f"(//div[contains(@class,'address-row')])[{row_index}]"

    # Scope all locators to this specific row
    address_type = self.driver.find_element(
        By.XPATH, f"{row_xpath}//mat-label[contains(.,'Address Type')]/ancestor::mat-form-field//mat-select"
    )
    country = self.driver.find_element(
        By.XPATH, f"{row_xpath}//mat-label[contains(.,'Country')]/ancestor::mat-form-field//mat-select"
    )
    # ... etc
```

The key is using XPath's `(//selector)[index]` syntax to scope to a specific row instance, then making all child locators relative to that row.

---

## Pattern 7: Searchable Dropdowns

### The Problem
Some dropdowns (like Country in address forms) are searchable — they have a text input at the top of the option list. You can type to filter, then select from the filtered results.

### The Solution: Type → Wait → Click

```python
def select_searchable_dropdown(self, dropdown_element, search_text):
    # 1. Open the dropdown
    dropdown_element.click()

    # 2. Find the search input inside the overlay
    search_input = self.wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, ".cdk-overlay-pane input")
    ))

    # 3. Type the search text
    self._set_input(search_input, search_text)

    # 4. Wait for filtered options to appear
    option = self.wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//mat-option//span[contains(.,'{search_text}')]")
    ))

    # 5. Click the option
    option.click()
```

This is used in Tax Authority (country selection), Supplier (address cascading), and Company Onboarding.

---

## Pattern 8: Cascading Dropdowns

### The Problem
Address forms have cascading dropdowns: Country → State → District → Taluka → Village. Selecting a Country loads that country's States. You MUST wait for the next dropdown to populate before selecting from it.

### The Solution: Select + Wait + Select

```python
def fill_cascading_address(self, country, state, district, taluka):
    # Select country
    self.select_dropdown("Country", country)
    time.sleep(1)  # Wait for state dropdown to populate

    # Select state
    self.select_dropdown("State", state)
    time.sleep(1)  # Wait for district dropdown to populate

    # Select district
    self.select_dropdown("District", district)
    time.sleep(1)  # Wait for taluka dropdown to populate

    # Select taluka
    self.select_dropdown("Taluka", taluka)
```

The `time.sleep(1)` between selections is unavoidable — the ERP makes an API call to load the next level's options. Without the wait, the dropdown will be empty or show stale options.

Some modules (Company Onboarding) implement `_fill_address_location_with_retry()` with up to 15 attempts, because the cascading dropdowns sometimes fail to populate even after waiting.

---

## Pattern 9: The "Never Trust Angular" Rule

### General Principles

1. **Never trust `.is_displayed()`** — Angular Material components can be in the DOM but visually hidden. Use `EC.visibility_of_element_located()` instead.

2. **Never trust `.text` on Angular elements** — The text might be in a child element or a projected content node. Always use `textContent` via JavaScript:
   ```python
   text = driver.execute_script("return arguments[0].textContent.trim();", element)
   ```

3. **Never trust that a click registered** — Always verify the state change after clicking. If you clicked "Submit", verify the form closed or the success alert appeared.

4. **Never assume dropdown options are stable** — Options can change between environments, between deploys, or even between sessions. Always use the `FK_POOL` pattern with fallback to live resolution.

5. **Never assume the form is ready** — Always wait for the page to load before interacting. Use `_wait_for_page_ready()` or explicit waits on key elements.

---

## Quick Reference: What To Use When

| Task | Use This | Not This |
|------|----------|----------|
| Click a button | `driver.execute_script("arguments[0].click()", el)` | `element.click()` |
| Type in an input | JS nativeInputValueSetter + dispatchEvent | `element.send_keys()` |
| Select a dropdown option | Click option + `_sync_dropdown_angular_model()` | Just click the option |
| Close a dropdown overlay | Backdrop click + JS pane removal | `Keys.ESCAPE` |
| Read element text | `execute_script("return el.textContent")` | `element.text` |
| Wait for page load | Wait for key element visibility | `time.sleep(5)` |
| Handle SweetAlert | Check for `.swal2-confirm` or `.swal2-cancel` | Assume pattern A everywhere |

---

## The Debug Toolkit

When something doesn't work and you can't figure out why:

### 1. Dump Angular Form State
```javascript
// In browser console or via execute_script
document.querySelectorAll('input, mat-select, textarea').forEach(function(el) {
    var formControl = el.closest('[formControlName]');
    if (formControl) {
        var controlName = formControl.getAttribute('formControlName');
        var classes = formControl.className;
        console.log(controlName, ':', classes, ':', el.value);
    }
});
```

### 2. Check for Hidden Overlays
```javascript
var overlays = document.querySelectorAll('.cdk-overlay-pane');
console.log('Open overlays:', overlays.length);
overlays.forEach(function(o, i) { console.log(i, o.innerHTML.substring(0, 100)); });
```

### 3. Force-Set a Value When Nothing Else Works
```javascript
// Nuclear option — directly set Angular's FormGroup value
var ngElement = document.querySelector('[formGroupName]');
if (ngElement && ngElement.__ngContext__) {
    // Access the Angular component's form group
    // This is brittle and version-dependent
}
```

---

## Module-Specific Gotchas

| Module | Gotcha |
|--------|--------|
| **Bank** | No `formcontrolname` attributes — only `name` attributes with exact case |
| **Season** | Duplicate name "Rabi" causes ERP to hang indefinitely |
| **UOM** | Search button is never Selenium-clickable — always use JS click |
| **UOM Conversion** | Has backup file from a major rewrite — don't use the old patterns |
| **Tax Rate** | Date fields have `name=null` — must use mat-label traversal |
| **Vehicle Master** | Angular refresh button breaks the toolbar permanently |
| **Farmer** | Trailing tab characters in HTML `name` attributes — `input[name='No Of Owner\t']` |
| **Farmer** | `name='Address'` appears in 3 different tabs — must scope locators to active panel |
| **Item Master** | Dropdown fill ORDER matters: Category → Group → Type → Attr1-5 |
| **Entity Group** | No success SweetAlert — form just closes silently |

Each of these cost hours to discover. The module-specific KT docs go into more detail on each one.
