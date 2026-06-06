# Module: Agent

> The only registration module with zero FK pools — all dropdowns are picked from the live UI at runtime, making it API-test-incapable and uniquely dependent on the application being fully operational.

## At a Glance

| Section | Value |
|---|---|
| Complexity Rank | 5th (simple stepper, unusual dropdown strategy) |
| Steppers | 5 (Universal → Address Details → Payment Details → Bank Details → Submit) |
| Repeating Rows | None — all steps are flat forms |
| API Tests | None |
| UI Tests | Yes |
| Page Object | `agent_page.py` (1,503 LOC) |
| Data File | `agent_data.py` (373 LOC) |
| Batch Create | None |
| attribute_name | `Agent` |

## The ERP Screen

The Agent registration screen creates agent entities in the ERP system. Agents are field representatives who handle customer acquisition and transaction processing on behalf of the organization.

**Navigation URL:** `/registration/agent`

### Step 1: Universal
Agent identity and basic information:
- Agent Name (free text, required)
- Agent Code (auto-generated or manual entry)
- Contact Number (required)
- Email (required)
- Date of Birth
- Gender (dropdown)
- Agent Type (dropdown)
- Status (toggle)

### Step 2: Address Details
Address information with a twist — see "Hardcoded Cascading Address" below:
- Address Line 1 (required)
- Address Line 2
- Country (dropdown — always India)
- State (dropdown — always Maharashtra)
- District (dropdown — always Pune)
- Taluka (dropdown — always Haveli)
- City/Village (dropdown)
- Pin Code
- Landmark

### Step 3: Payment Details
Payment configuration for the agent:
- Payment Mode (dropdown — Cash/Bank/Online)
- Payment Frequency (dropdown — Monthly/Quarterly/Yearly)
- Commission Percentage
- Bank Account for Commission

### Step 4: Bank Details
Agent's personal bank information:
- Bank Name
- Branch Name
- Account Number
- Account Holder Name
- IFSC Code
- Account Type (dropdown — Savings/Current)
- Is Primary (checkbox)

### Step 5: Submit
Review and submit the agent registration. No editable fields in this step — just a summary and the Submit button.

## API Contract

### Endpoint
`POST /api/registration/agent` (presumed — no API payload builder exists)

### attribute_name
`Agent`

### Payload Structure
⚠️ **NO API PAYLOAD BUILDER EXISTS.** The Agent module is currently UI-only. The payload structure is inferred from UI fields:

```json
{
  "attribute_name": "Agent",
  "name": "string",
  "agent_code": "string",
  "contact_number": "string",
  "email": "string",
  "dob": "YYYY-MM-DD",
  "gender_id": "FK",
  "agent_type_id": "FK",
  "status": 1,
  "details": [],
  "children": [
    {
      "attribute_name": "AgentAddress",
      "details": [
        {
          "address_line_1": "string",
          "address_line_2": "string",
          "country_id": "FK",
          "state_id": "FK",
          "district_id": "FK",
          "taluka_id": "FK",
          "city_village_id": "FK",
          "pin_code": "string",
          "landmark": "string"
        }
      ]
    },
    {
      "attribute_name": "AgentPayment",
      "details": [
        {
          "payment_mode": "string",
          "payment_frequency": "string",
          "commission_percentage": "number"
        }
      ]
    },
    {
      "attribute_name": "AgentBank",
      "details": [
        {
          "bank_name": "string",
          "branch_name": "string",
          "account_number": "string",
          "account_holder_name": "string",
          "ifsc_code": "string",
          "account_type": "string",
          "is_primary": true
        }
      ]
    }
  ]
}
```

### FK Dependencies
⚠️ **ZERO FK POOLS.** The Agent module has no FK pool definitions at all. All dropdown values are selected from the live UI at runtime using `select_random_from_dropdown_by_label()`. This means:
- Tests cannot run without the application being fully operational
- No pre-validation of dropdown option availability
- Tests are slower because each dropdown interaction requires waiting for the UI
- API tests are impossible without reverse-engineering FK IDs from the UI

## Data Layer

### Current State: Runtime UI Selection
The `agent_data.py` file (373 LOC) provides:
- Agent name generation (basic — timestamp-based)
- Contact number generation (Indian format)
- Email generation
- Date of birth generation

### No FK Pools — The `select_random_from_dropdown_by_label()` Pattern
Since there are no FK pools, every dropdown is handled by:
1. Clicking the mat-select trigger
2. Waiting for the options panel to open
3. Getting all visible `mat-option` elements
4. Selecting one at random
5. Clicking it

This pattern is implemented in `select_random_from_dropdown_by_label(label)`:
```python
def select_random_from_dropdown_by_label(self, label):
    trigger = self.page.locator(f"mat-select:has(mat-select-trigger:text('{label}'))")
    trigger.click()
    options = self.page.locator("mat-option")
    count = options.count()
    if count == 0:
        raise ValueError(f"No options found for dropdown: {label}")
    random_index = random.randint(0, count - 1)
    options.nth(random_index).click()
```

### Different Dropdown Interaction Pattern
The Agent module uses a **different dropdown interaction pattern** than Supplier and Customer. Where Supplier/Customer use:
```python
self._select_mat_option(field_name, value_id)
```
Agent uses:
```python
self.select_random_from_dropdown_by_label(label)
```
This is because there are no FK IDs to select — the test doesn't know what options are available until the UI opens the dropdown. The "by label" approach finds the dropdown by its visible label text rather than by `formcontrolname`.

### Hardcoded Cascading Address
The `fill_address_step(data)` method **ignores the `addr_data` parameter** for the cascading dropdowns. Instead, it hardcodes:
- Country: **India**
- State: **Maharashtra**
- District: **Pune**
- Taluka: **Haveli**

Only City/Village and Pin Code use the provided data. This was done as a pragmatic shortcut because:
1. The cascading address dropdowns are flaky (same issue as Company Onboarding)
2. There are no FK pools to provide valid address chains
3. The hardcoded values are known to work reliably
4. Testing address variations is not a priority for Agent registration

```python
def fill_address_step(self, addr_data):
    # Hardcoded cascading — ignore addr_data for these
    self._select_dropdown_option("Country", "India")
    self._select_dropdown_option("State", "Maharashtra")
    self._select_dropdown_option("District", "Pune")
    self._select_dropdown_option("Taluka", "Haveli")
    # Use provided data for the rest
    self._fill_field("city_village", addr_data.get("city_village"))
    self._fill_field("pin_code", addr_data.get("pin_code"))
    self._fill_field("address_line_1", addr_data.get("address_line_1"))
    self._fill_field("address_line_2", addr_data.get("address_line_2"))
```

### Validation Rules
- **Agent Name**: Free text, no format validation observed
- **Contact Number**: Indian phone format expected
- **Email**: Standard email format
- **Pin Code**: 6-digit Indian pin code
- **IFSC Code**: 11-character format
- **Commission Percentage**: Numeric, but boundary validation unclear

## Page Object

### Key Methods

**`fill_universal_step(data)`** — Fills Step 1 (Universal) fields. Uses `select_random_from_dropdown_by_label()` for all dropdowns.

**`fill_address_step(addr_data)`** — Fills Step 2. Hardcodes India→Maharashtra→Pune→Haveli for the cascading address. Only City, Pin Code, and address lines use the `addr_data` parameter.

**`fill_payment_step(data)`** — Fills Step 3 (Payment Details). Dropdowns selected randomly from UI.

**`fill_bank_step(data)`** — Fills Step 4 (Bank Details). Similar to other modules' bank detail fillers.

**`navigate_to_step(step_number)`** — Clicks stepper headers to navigate between the 5 steps.

**`submit_agent()`** — Clicks the Submit button on Step 5.

**`select_random_from_dropdown_by_label(label)`** — The core dropdown interaction method. Finds the dropdown by its visible label, opens it, and picks a random option. This is the Agent module's unique dropdown pattern.

### Tricky Bits

1. **No FK pools = No API testing** — The absence of FK ID pools means there's no way to construct an API payload programmatically. Even if someone writes a `build_agent_payload()` function, they'd need to reverse-engineer all the FK IDs from the UI first. This is the biggest architectural gap in the module.

2. **Hardcoded address ignores input data** — `fill_address_step(addr_data)` takes an `addr_data` parameter but ignores it for the 4 cascading dropdowns. A new team member might pass custom address data expecting it to be used for State/District/Taluka and be confused when it's always Maharashtra/Pune/Haveli.

3. **Different dropdown pattern from other modules** — The `select_random_from_dropdown_by_label(label)` pattern is different from the `_select_mat_option(field_name, value)` pattern used in Supplier and Customer. This can cause confusion when switching between modules. Copy-pasting Customer dropdown code into Agent tests will not work.

4. **Random dropdown selection = non-deterministic tests** — Because options are selected at random, the same test may create agents with different dropdown values on different runs. This makes debugging harder because you can't reproduce the exact data state.

5. **No repeating rows** — Unlike Customer and Farmer, Agent has no repeating grid rows. All steps are flat forms. This simplifies the page object but means less coverage for grid interaction patterns.

### Locator Strategies
- Stepper headers: `mat-step-header` by index
- Form fields: `input[formcontrolname='<field>']` where available
- Dropdown by label: `mat-select` found by visible label text (unique to Agent)
- mat-select options: `mat-option` within the open panel
- Submit button: `button` with text "Submit"

## Known Bugs

| Bug ID | Severity | Description |
|---|---|---|
| — | — | No formally tracked bugs. The module's simplicity means fewer surface areas for bugs. |

**Known Issues:**
- Hardcoded address limits test coverage for non-Maharashtra addresses
- Random dropdown selection makes tests non-deterministic
- No way to verify dropdown selection was accepted by the form model

## War Stories

### The Ignored Address Data

A new engineer was tasked with extending the Agent tests to cover address variations — different states, districts, and talukas. They wrote comprehensive test data covering addresses in Kerala, Gujarat, and Tamil Nadu. They passed this data to `fill_address_step()` and ran the tests. Every single test created an agent in Maharashtra, Pune, Haveli — the hardcoded values. After an hour of debugging, they discovered the hardcoded cascading logic. The `addr_data` parameter was a red herring — it was only used for City and Pin Code. The lesson: always read the method implementation, not just the signature.

### The Random Dropdown Dilemma

During a demo to stakeholders, the automation suite ran the Agent creation test three times. Each time, the agent was created with a different "Agent Type" — first "Field Agent", then "Collection Agent", then "Verification Agent". The stakeholders asked why the test wasn't consistent. The answer was that without FK pools, the only way to fill dropdowns was to pick randomly from whatever the UI offered. This led to a discussion about whether Agent should be brought up to the same FK-pool standard as other modules, but it was deprioritized because Agent is a low-traffic module.

### The Dropdown Pattern Mismatch

An engineer who had been working on Customer tests was asked to add a new field to the Agent test. They opened the Agent page object, saw the dropdown pattern, and instinctively wrote `self._select_mat_option("agent_type", agent_type_id)`. The method didn't exist in the Agent page object. After checking the class, they realized Agent uses a completely different dropdown interaction pattern. They had to rewrite the code to use `self.select_random_from_dropdown_by_label("Agent Type")`. This is a recurring source of confusion for engineers who work across multiple modules.

## Test Coverage

| Test Type | Status | Count |
|---|---|---|
| API Create Tests | ❌ None | 0 |
| API Update Tests | ❌ None | 0 |
| API Validation Tests | ❌ None | 0 |
| API Batch Create | ❌ None | 0 |
| UI Create Tests | ✅ Passing | ~8 |
| UI Stepper Navigation | ✅ Passing | ~4 |
| UI Payment Step | ✅ Passing | ~3 |
| UI Bank Step | ✅ Passing | ~3 |
| Knowledge Doc | ✅ Exists | 1 (379 LOC) |

## Files

```
registration/
├── agent_page.py       1,503 LOC   # Page object
├── agent_data.py         373 LOC   # Data layer (minimal)
├── test_agent_ui.py     ~200 LOC   # UI automation tests
├── Agent_Automation_Knowledge.md  379 LOC # Knowledge transfer doc
└── (no API test files)              # Major gap
```

## What's Missing

1. **FK pool definitions** — The most critical gap. Without FK pools, the module cannot support API testing, batch creation, or deterministic test data. Every dropdown selection is a live UI interaction, making tests slow and fragile.

2. **API payload builder** — No `build_agent_payload()` exists. This blocks all API testing, batch creation, and data seeding.

3. **API tests** — Zero API test coverage. No create, update, delete, or validation tests via API.

4. **Batch creation** — No `generate_batch_payloads()`. Agents must be created one at a time through the UI.

5. **Address variation testing** — The hardcoded India→Maharashtra→Pune→Haveli address means zero test coverage for agents in other states or districts. This is a significant gap for a national ERP.

6. **Deterministic dropdown selection** — The random selection pattern makes tests non-reproducible. Even if the same test passes 99 times, the 100th run might select a different dropdown option that triggers an unknown bug.

7. **Negative test cases** — Missing tests for: invalid email format, duplicate agent codes, commission percentage boundaries (0%, 100%, negative), missing required fields.

8. **Update flow** — No update/edit tests for existing agents. The page object has no update-specific methods.

9. **Cross-module integration** — No tests verify that an agent created through registration can be used in downstream modules (transactions, commission calculations, etc.).

10. **Alignment with other modules** — The Agent module's dropdown pattern differs from Supplier/Customer. It should be refactored to use the same FK-pool-based approach for consistency and API testing capability.
