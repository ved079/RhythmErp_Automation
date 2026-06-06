# Module: Entity Group Definition

> The simplest form in the access suite — just 2 fields — but with 8 documented bugs including spaces-only acceptance, duplicate silent rejection, and no success SweetAlert to confirm creation.

## At a Glance

| Section | Value |
|---|---|
| Complexity Rank | Simplest access module |
| Steppers | None — flat form |
| Repeating Rows | None |
| API Tests | None |
| UI Tests | Yes (1,360 LOC test file) |
| Page Object | `entity_group_definition_page.py` (1,539 LOC) |
| Data File | `entity_group_definition_data.py` (241 LOC) |
| Batch Create | None |
| attribute_name | `EntityGroupDefinition` |

## The ERP Screen

The Entity Group Definition screen creates named groups with hierarchical levels. These groups are used throughout the ERP for organizing entities (companies, branches, divisions) into logical hierarchies. Despite having only 2 fields, this module has the highest bug density in the access suite.

**Navigation URL:** `/access/entity-group-definition`

### Form Fields

| Field | Type | Required | Validation |
|---|---|---|---|
| Entity Group Name | Free text | Yes | ⚠️ Almost none (see bugs) |
| Level | Number input | Yes | ⚠️ Almost none (see bugs) |

That's it. Two fields. No dropdowns, no FK lookups, no repeating rows, no stepper. Just a name and a number.

### The Table
Below the form, a data table lists all existing Entity Group Definitions with columns for:
- Entity Group Name
- Level
- Actions (Edit, Delete — but see BUG-008)

### What "Entity Group" Means in the ERP
An Entity Group is a container for organizing entities hierarchically. For example:
- **Level 1:** "Country" group → contains all country-level entities
- **Level 2:** "Region" group → contains all region-level entities
- **Level 3:** "Branch" group → contains all branch-level entities

The `Level` field defines the hierarchy depth. Lower levels are parents of higher levels. This structure is used by the Role Creation and User Creation modules to assign access rights at specific organizational levels.

## API Contract

### Endpoint
`POST /api/access/entity-group-definition` (presumed — no API payload builder exists)

### attribute_name
`EntityGroupDefinition`

### Payload Structure
```json
{
  "attribute_name": "EntityGroupDefinition",
  "entity_group_name": "string",
  "level": "integer",
  "details": [],
  "children": []
}
```

### FK Dependencies
**NONE.** This module has zero FK pools. The only two fields are free text and a number.

## Data Layer

### Current State: Minimal
The `entity_group_definition_data.py` file (241 LOC) provides:
- Entity Group Name generation (simple — `f"EntityGroup_{random_string()}"`)
- Level generation (random integer 1-10)
- Test data dictionaries for bug regression tests

### No FK Pools
No FK pools exist. No API payload builder exists. The module is purely UI-tested.

### Validation Rules (Expected vs Actual)
| Rule | Expected | Actual |
|---|---|---|
| Name: spaces only | ❌ Should reject | ✅ BUG-001: Accepts |
| Name: duplicates | ❌ Should reject | ⚠️ BUG-002: Silently rejected (no error shown) |
| Name: case-insensitive dupes | ❌ Should block | ❌ BUG-003: Not blocked |
| Name: special characters | ❌ Should reject | ✅ BUG-004: Accepts |
| Name: maxlength | ✅ Should enforce | ❌ BUG-005: No maxlength |
| Level: negative | ❌ Should reject | ✅ BUG-006: Accepts |
| Level: decimal | ❌ Should reject | ✅ BUG-006: Accepts |
| Success SweetAlert | ✅ Should show | ❌ BUG-008: No alert |

## Page Object

### Key Methods

**`fill_entity_group_name(name)`** — Types the entity group name into the text field. No special handling needed — it's a plain text input.

**`fill_level(level)`** — Types the level number. The input field accepts any numeric value including negative and decimal numbers (BUG-006).

**`click_save()`** — Clicks the Save/Create button.

**`wait_for_success_alert()`** — ⚠️ This method exists but will ALWAYS FAIL because no success SweetAlert is shown (BUG-008). Tests should NOT call this method. Instead, verify creation by checking the data table below the form.

**`verify_in_table(name)`** — Checks that the newly created Entity Group Definition appears in the data table. This is the reliable way to confirm creation since there's no success alert.

**`handle_session_timeout()`** — Detects session timeout and performs auto re-login. This is necessary because the Entity Group Definition screen is often used in long test sessions where the session can expire mid-test.

### Tricky Bits

1. **Never use Keys.ESCAPE** — The Entity Group Definition page has a known issue where pressing Escape can close the browser tab or trigger unexpected navigation. All test code must avoid `Keys.ESCAPE`. If you need to dismiss a dialog or close a dropdown, click outside it instead.

2. **No success SweetAlert** — After creating an Entity Group Definition, no success popup appears (BUG-008). Tests cannot rely on the standard SweetAlert detection pattern used in other modules. Instead, verify creation by checking the data table.

3. **Silent duplicate rejection** — If you create an Entity Group Definition with a name that already exists, the server silently rejects it. No error is shown, no toast, no SweetAlert. The form just stays as-is. The only way to detect this is to check the data table and see that your new entry doesn't appear (BUG-002).

4. **Session timeout detection** — The page object includes session timeout detection with auto re-login. This is triggered when certain API calls return 401. The auto re-login logic:
   ```python
   def handle_session_timeout(self):
       if self.is_session_expired():
           self.re_login()
           self.navigate_to_entity_group_definition()
   ```

5. **Spaces-only names accepted** — The name field accepts names that are only whitespace (BUG-001). A name of `"   "` (three spaces) will be created successfully. This pollutes the data table with invisible entries.

### Locator Strategies
- Entity Group Name input: `input[formcontrolname='entity_group_name']`
- Level input: `input[formcontrolname='level']`
- Save button: `button` with text "Save" or icon save
- Data table rows: `mat-row` within the table container
- Table cell by column: `mat-cell:nth-of-type({column_index})` within a `mat-row`
- Edit button in row: `button[mattooltip='Edit']` within the specific `mat-row`
- ⚠️ Do NOT use `Keys.ESCAPE` anywhere on this page

## Known Bugs

| Bug ID | Severity | Description |
|---|---|---|
| BUG-001 | Medium | Entity Group Name accepts spaces-only input (e.g., `"   "`). Creates invisible entries in the data table. |
| BUG-002 | High | Duplicate Entity Group Names are silently rejected — no error message, no toast, no SweetAlert. User has no idea why their entry wasn't created. |
| BUG-003 | Medium | Case-insensitive duplicates are NOT blocked. "TestGroup" and "testgroup" are both accepted as separate entries. |
| BUG-004 | Medium | Special characters are accepted in Entity Group Name. Names like `@#$%` or `<script>alert(1)</script>` are valid. |
| BUG-005 | Low | No maxlength on Entity Group Name. Strings of 1000+ characters are accepted. |
| BUG-006 | Medium | Level field accepts negative numbers (e.g., `-5`) and decimal numbers (e.g., `3.14`). Only positive integers should be valid. |
| BUG-007 | Low | No Delete option in the actions column. Once created, Entity Group Definitions cannot be removed through the UI. |
| BUG-008 | Medium | No success SweetAlert after creation. Users get no visual confirmation that their entry was saved. |

## War Stories

### The Invisible Entity Group

A tester was running a suite of Entity Group Definition tests. One test created a group with the name `"   "` (three spaces). The test passed — the API accepted it, the form cleared, and no error appeared. But when the tester looked at the data table, there was a blank row with no visible name. Clicking on it worked (it navigated to an edit screen with the spaces-only name in the field), but it was invisible in the table. This is BUG-001 in action. The real problem came when another test tried to create a group with the same spaces-only name — BUG-002 meant it was silently rejected, but the tester couldn't see the existing entry to know why. The fix in the test suite was to always use visible, meaningful names and add a regex check `name.strip() != ""` before submission.

### The Silent Duplicate

A QA engineer was manually testing the Entity Group Definition screen. They created "Region Group" successfully (they thought). Then they tried to create "Region Group" again. The form cleared, no error appeared, and it looked like it succeeded. But checking the data table showed only one "Region Group" entry. The duplicate was silently rejected (BUG-002). This is particularly dangerous because users may not realize their second entry wasn't created, leading them to assume data exists when it doesn't. In automation, the test must explicitly check the data table row count to confirm creation.

### The Negative Level Hierarchy

Someone created an Entity Group Definition with Level `-1`. Then another with Level `0`. Then `3.14`. All were accepted (BUG-006). The hierarchy system, which expects positive integers (1, 2, 3...), now has entries at levels -1, 0, and 3.14. The Role Creation module, which uses these levels to build access hierarchies, couldn't make sense of the non-integer levels. The dropdown showed "-1" and "3.14" as selectable hierarchy levels, confusing users. The lesson: even the simplest form can produce complex downstream problems when validation is missing.

### The Missing SweetAlert

Every other module in the ERP shows a green SweetAlert popup confirming successful creation. Entity Group Definition doesn't (BUG-008). This wasn't always the case — it used to have a SweetAlert, but a UI update broke it and nobody noticed for months because there were no visual regression tests. The automation team discovered it when their `wait_for_success_alert()` method started timing out. The workaround was to verify creation via the data table instead of the alert.

## Test Coverage

| Test Type | Status | Count |
|---|---|---|
| API Create Tests | ❌ None | 0 |
| API Update Tests | ❌ None | 0 |
| API Validation Tests | ❌ None | 0 |
| UI Create Tests | ✅ Passing | ~15 |
| UI Bug Regression Tests | ✅ Passing | ~8 |
| UI Negative Tests | ✅ Passing | ~10 |
| UI Session Timeout | ✅ Passing | ~3 |

## Files

```
access/
├── entity_group_definition_page.py   1,539 LOC   # Page object
├── entity_group_definition_data.py     241 LOC   # Data layer
└── test_entity_group_definition_ui.py 1,360 LOC   # UI tests (large!)
```

## What's Missing

1. **API tests** — Zero API test coverage. No create, update, delete, or validation tests via API. Given the module's simplicity (2 fields), API tests would be trivial to write and would provide fast feedback on server-side validation changes.

2. **API payload builder** — No `build_entity_group_payload()` exists. This blocks API testing and batch creation.

3. **Batch creation** — No `generate_batch_payloads()`. Creating multiple Entity Group Definitions requires one-at-a-time UI interaction.

4. **Delete functionality tests** — BUG-007 means there's no Delete option in the UI. But what about the API? Can Entity Group Definitions be deleted via API? No test verifies this.

5. **Edit flow tests** — While the Edit button exists in the data table, there are no dedicated tests for editing an existing Entity Group Definition. Can you change the name? Change the level? What validation applies in edit mode?

6. **Downstream integration tests** — No tests verify that Entity Group Definitions created here are correctly used by Role Creation and User Creation modules. The hierarchy levels should be selectable in those modules' dropdowns.

7. **Session timeout robustness** — While the page object has session timeout detection, it's not comprehensively tested. What happens if the session expires mid-save? Mid-edit?

8. **Data table pagination** — No tests verify behavior when the table exceeds one page of results. Do pagination controls work? Does search/filter work?

9. **Concurrent creation** — No tests verify what happens when two users create Entity Group Definitions with the same name simultaneously.

10. **Special characters security testing** — BUG-004 accepts special characters including `<script>` tags. No security test verifies whether XSS is actually exploitable or if the data table sanitizes output.
