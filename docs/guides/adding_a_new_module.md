# Adding a New Module — Step-by-Step Playbook

> The recipe for going from "there's a new ERP screen" to "fully automated with API + UI tests + batch_create." Follow these steps in order.

---

## Overview

Adding a new module takes about 4-8 hours depending on complexity. The steps are:

1. Discover the API structure
2. Build the data layer
3. Build the page object
4. Write API tests
5. Write UI validation tests
6. Write batch_create script
7. Integrate with the dashboard

---

## Step 1: Discover the API Structure

Before writing any code, you need to understand how the ERP's API handles this screen.

### 1a. Log In and Get a Token

```python
import requests

resp = requests.post("https://rhythmerp.algorhythms.in/auth/login1/", data={
    "username": "user@admin.com",
    "password": "Tenant@123456789",
    "tenant": "599"
}, headers={"X-Tenant-ID": "599"})

token = resp.cookies.get("refresh_token")
```

### 1b. Discover the Screen Structure

Use `erp_api_client.py`'s `discover_structure()`:

```python
from common.erp_api_client import RhythmERPAPIClient

client = RhythmERPAPIClient()
client.set_session_from_token(token)

structure = client.discover_structure("NewModuleName")
print(structure)
```

This tells you:
- What `attribute_name` to use
- What fields are on the screen
- Whether there are stepper children
- What FK dropdowns exist

### 1c. Discover FK Dropdown Options

```python
from common.fk_resolver import FkResolver

resolver = FkResolver(client)
fk_ids = resolver.resolve("NewModuleName")
print(fk_ids)
```

This returns `{display_name: id}` for every dropdown on the screen.

### 1d. Try a Manual API Create

```python
payload = {
    "attribute_name": "NewModuleName",
    "field1": "value1",
    "field2": 123,
    "details": [],
    "children": []
}

result = client.create_entry("NewModuleName", payload)
print(result.status_code, result.json())
```

Keep tweaking the payload until you get a 200 response. This is how you discover:
- Required vs optional fields
- Field type expectations (integer vs string)
- FK ID values that actually work
- Any hidden validation rules

---

## Step 2: Create the Module Directory Structure

```bash
mkdir -p pages/{section}/modules/{module_name}/{data,scripts,test/api}
touch pages/{section}/modules/{module_name}/__init__.py
touch pages/{section}/modules/{module_name}/data/__init__.py
touch pages/{section}/modules/{module_name}/test/__init__.py
touch pages/{section}/modules/{module_name}/test/api/__init__.py
```

---

## Step 3: Build the Data File (`*_data.py`)

Start with this template and fill in your module's specifics:

```python
"""
Data layer for {Module} automation.
Provides FK pools, payload builders, and test data generators.
"""

import random
from uuid import uuid4

# ─── FK ID Pools ────────────────────────────────────────────────
# These IDs are tenant-specific (tenant 599). Re-run FkResolver
# if the database is reset.

{FIELD_NAME}_IDS = {
    "Option 1": 100,
    "Option 2": 101,
}

DEFAULT_{MODULE}_FK_IDS = {
    "field_name": 100,  # "Option 1"
}

# ─── Field Validation Rules ─────────────────────────────────────
FIELD_VALIDATION_RULES = {
    "field_name": {
        "type": "text",
        "required": True,
        "max_length": 100,
    },
}

# ─── API Payload Builder ────────────────────────────────────────
def build_{module}_api_payload(fk_ids=None):
    """Build a valid API payload for creating a {module} entry."""
    fk = {**DEFAULT_{MODULE}_FK_IDS, **(fk_ids or {})}

    return {
        "attribute_name": "{ModuleName}",
        "field_name": f"Test {module} {uuid4().hex[:6]}",
        "fk_field": fk["field_name"],
        "details": [],
        "children": [],
    }
```

### Key Points

1. **Always use `DEFAULT_*_FK_IDS`** as the base and override via `fk_ids` parameter
2. **Randomize names** with `uuid4().hex[:6]` to avoid duplicate conflicts
3. **Document every FK pool** with a comment explaining where the IDs came from
4. **Test the payload builder** by calling it and creating an entry via `erp_api_client.py`

---

## Step 4: Build the Page Object (`*_page.py`)

### Simple Module Template

For single-form modules (like Bank, UOM, Designation):

```python
class {Module}Page:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)

    def navigate_to_page(self):
        nav_section.navigate_to(
            self.driver, self.wait,
            "{Section}", "{Module Display Name}"
        )
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        # Wait for the table or add button to be visible
        self.wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "table.mat-mdc-table")
        ))

    def fill_all_fields(self, data):
        # Fill each field using JS value-setter pattern
        self._set_input(name_input, data["name"])
        self._select_dropdown(dropdown, data["option"])

    def submit_form(self):
        submit_btn = self.driver.find_element(
            By.XPATH, "//button[contains(.,'Submit')]"
        )
        self.driver.execute_script("arguments[0].click();", submit_btn)

    def _set_input(self, element, value):
        """Set input value via JS native setter."""
        self.driver.execute_script("""
            var el = arguments[0];
            var nativeSetter = Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype, 'value'
            ).set;
            nativeSetter.call(el, arguments[1]);
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            el.dispatchEvent(new Event('blur', {bubbles: true}));
        """, element, value)
```

### Multi-Stepper Module Template

For modules with steppers (like Supplier, Customer):

```python
def create_entry(self, data):
    self.navigate_to_page()
    self._wait_for_page_ready()

    # Step 1
    self.fill_step1(data)
    self._click_next()

    # Step 2 (with repeating rows)
    self.fill_step2(data)
    self._click_next()

    # Step 3
    self.fill_step3(data)
    self._click_submit()

    return self._handle_submit_response()
```

### Key Rules

1. **All clicks via JavaScript** — `execute_script("arguments[0].click()")`
2. **All input via JS native setter** — not `send_keys()`
3. **All dropdown selections + Angular model sync** — see Angular Material Survival Guide
4. **Never use Keys.ESCAPE** — use backdrop click + JS overlay removal
5. **Never assume SweetAlert pattern** — check the actual ERP behavior

---

## Step 5: Write API Tests

### conftest.py

```python
import pytest
from common.erp_api_client import RhythmERPAPIClient

@pytest.fixture(scope="module")
def api_client():
    client = RhythmERPAPIClient()
    client.prompt_for_token()  # Or use set_session_from_token()
    yield client

@pytest.fixture
def build_payload():
    from {module}.data.{module}_data import build_{module}_api_payload
    return build_{module}_api_payload
```

### test_*_payload.py

Test that valid payloads return 200 and invalid payloads return appropriate errors:

```python
class Test{Module}Payload:
    def test_valid_payload_returns_200(self, api_client, build_payload):
        payload = build_payload()
        resp = api_client.create_entry("{ModuleName}", payload)
        assert resp.status_code == 200

    def test_missing_required_field_returns_400(self, api_client, build_payload):
        payload = build_payload()
        del payload["required_field"]
        resp = api_client.create_entry("{ModuleName}", payload)
        assert resp.status_code == 400
```

### test_*_schema.py

Verify response structure:

```python
class Test{Module}Schema:
    def test_response_has_expected_fields(self, api_client, build_payload):
        payload = build_payload()
        resp = api_client.create_entry("{ModuleName}", payload)
        data = resp.json()
        assert "id" in data
        assert "field_name" in data
```

### test_*_perf.py

Verify performance:

```python
class Test{Module}Performance:
    def test_create_completes_within_2_seconds(self, api_client, build_payload):
        import time
        payload = build_payload()
        start = time.time()
        api_client.create_entry("{ModuleName}", payload)
        elapsed = time.time() - start
        assert elapsed < 2.0
```

---

## Step 6: Write UI Validation Tests

Test that the ERP's form validation works (or doesn't):

```python
class Test{Module}Validation:
    def test_required_field_shows_error(self, logged_in_driver):
        page = {Module}Page(logged_in_driver)
        page.navigate_to_page()
        page.open_add_form()
        page.submit_form()  # Submit without filling anything
        assert page.has_field_error("field_name")
```

Focus on:
- Required field validation
- Character type validation
- Max length validation
- Duplicate detection
- SweetAlert behavior

---

## Step 7: Write batch_create Script

```python
"""Batch create {module} entries via API."""

from common.erp_api_client import RhythmERPAPIClient
from {module}.data.{module}_data import build_{module}_api_payload

def main(count=10):
    client = RhythmERPAPIClient()
    client.prompt_for_token()

    for i in range(count):
        payload = build_{module}_api_payload()
        resp = client.create_entry("{ModuleName}", payload)
        status = "✓" if resp.status_code == 200 else "✗"
        print(f"[{i+1}/{count}] {status} {payload.get('field_name', 'N/A')}")

if __name__ == "__main__":
    main()
```

**Always test with count=1 first**, then count=10. If batch_create fails 10/10, you have a data layer problem, not a script problem.

---

## Step 8: Add to Dashboard Discovery

If you want the new module to appear in the Next.js dashboard, add its display name to `api/test_discovery.py`'s `DISPLAY_NAMES` dict:

```python
DISPLAY_NAMES = {
    ...
    "new_module_name": "New Module Display Name",
}
```

---

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| "API returns 400 for valid data" | Check FK IDs — they might be wrong or belong to a different dropdown |
| "Dropdown selection doesn't register" | Use `_sync_dropdown_angular_model()` — see Angular Material Survival Guide |
| "Form submits but no entry created" | Check for hidden validation — SweetAlert might show "Validation Failed" |
| "Test passes locally but fails in CI" | Add explicit waits — CI is slower than local |
| "Duplicate name errors" | Use `uuid4().hex[:6]` in generated names |

---

## Time Estimates

| Module Type | Time | Example |
|-------------|------|---------|
| Simple (3 fields, 0 FK, no stepper) | 2-3 hours | Designation, Season, UOM |
| Medium (3-5 fields, 1-2 FK, no stepper) | 3-5 hours | Bank, HSN SAC, Tax Authority |
| Complex (5+ fields, 3+ FK, stepper) | 5-8 hours | Supplier, Customer, Company Onboarding |
