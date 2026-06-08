# Module: Role Creation

> A 2-field form where the mat-select dropdown doesn't update the Angular model, `formcontrolname` is `"entity_type"` (not `"entityGroupName"`), and SQL injection strings are accepted as role names.

## At a Glance

| Section | Value |
|---|---|
| Complexity Rank | 2nd simplest access module |
| Steppers | None — flat form |
| Repeating Rows | None |
| API Tests | None |
| UI Tests | Yes |
| Page Object | `role_creation_page.py` (1,714 LOC) |
| Data File | `role_creation_data.py` (179 LOC) |
| Batch Create | None |
| attribute_name | `Rolecreationscreen` |

## The ERP Screen

The Role Creation screen defines roles that can be assigned to users. Each role is associated with an Entity Group, which determines the organizational scope of the role's permissions.

**Navigation URL:** `/access/role-creation`

### Form Fields

| Field | Type | Required | Validation |
|---|---|---|---|
| Role Name | Free text | Yes | ⚠️ Almost none (see bugs) |
| Entity Group Name | Dropdown (mat-select) | Yes | Must select from existing Entity Group Definitions |

### The Entity Group Name Dropdown
This dropdown is populated from the Entity Group Definitions created in the Entity Group Definition module. It's a mat-select component that displays all available entity groups.

**CRITICAL:** The `formcontrolname` for this dropdown is `"entity_type"`, NOT `"entityGroupName"` as you might expect from the field's label. This is a naming inconsistency in the frontend code that has caused confusion for every engineer who has worked on this module.

### The Data Table
Below the form, a data table lists all created roles with:
- Role Name
- Entity Group Name
- Actions (View, History — but no Delete)

### History and View Popups
Clicking "History" opens a popup showing the role's change history. Clicking "View" opens a popup showing the role's current details. **BUG:** The History popup can be opened on top of the View popup, creating stacked overlays that are difficult to close.

## API Contract

### Endpoint
`POST /api/access/role-creation` (presumed — no API payload builder exists)

### attribute_name
`Rolecreationscreen`

Note the unusual casing — it's `Rolecreationscreen`, not `RoleCreation` or `RoleCreationScreen`. This must be used exactly as-is in the payload.

### Payload Structure
```json
{
  "attribute_name": "Rolecreationscreen",
  "role_name": "string",
  "entity_type": "FK (Entity Group Definition ID)",
  "details": [],
  "children": []
}
```

### FK Dependencies (1 Pool)
| FK Pool | Source | Approx Count |
|---|---|---|
| entity_type | Entity Group Definition IDs | Varies (created by EGD module) |

Note: Despite the field being labeled "Entity Group Name" in the UI, the API field is `entity_type` and the `formcontrolname` is also `entity_type`. The ID values come from the Entity Group Definition module's created records.

## Data Layer

### Current State: Minimal
The `role_creation_data.py` file (179 LOC) provides:
- Role name generation (simple — `f"Role_{random_string()}"`)
- Test data dictionaries for bug regression tests

### No FK Pools in Data Layer
The Entity Group dropdown is populated from the live UI — there's no FK pool fetched in the data layer. The page object reads the dropdown options at runtime.

### Validation Rules (Expected vs Actual)
| Rule | Expected | Actual |
|---|---|---|
| Role Name: spaces only | ❌ Should reject | ✅ BUG: Accepts |
| Role Name: special chars | ❌ Should reject | ✅ BUG: Accepts |
| Role Name: SQL injection | ❌ Should reject | ✅ BUG: Accepts (`' OR 1=1 --`) |
| Role Name: XSS | ❌ Should reject | ✅ BUG: Accepts (`<script>alert(1)</script>`) |
| Role Name: duplicates | ❌ Should reject | ✅ BUG: Allowed |
| Role Name: maxlength | ✅ Should enforce | ❌ BUG: 500+ chars silently fail |
| mat-error visible | ✅ Should show text | ❌ BUG: No visible mat-error text |
| Delete option | ✅ Should exist | ❌ BUG: No Delete |

## Page Object

### Key Methods

**`fill_role_name(name)`** — Types the role name into the text field. The field accepts virtually any input (see bugs).

**`select_entity_group(entity_group_name)`** — Selects an Entity Group from the dropdown. **CRITICAL:** This method must use the JavaScript value-setter workaround because the mat-select doesn't update the Angular reactive form model on standard click.

The standard approach (click → select option) updates the UI but leaves the Angular FormControl's value as `null`. The fix:
```python
def select_entity_group(self, entity_group_name):
    # Standard UI interaction
    dropdown = self.page.locator("mat-select[formcontrolname='entity_type']")
    dropdown.click()
    option = self.page.locator(f"mat-option:text('{entity_group_name}')")
    option.click()
    
    # JS value-setter to sync Angular model
    self.page.evaluate("""
        const select = document.querySelector("mat-select[formcontrolname='entity_type']");
        const ngControl = select.__ngContext__[8];
        if (ngControl && ngControl.control) {
            ngControl.control.setValue(/* selected value */);
            ngControl.control.markAsDirty();
        }
    """)
```

**`click_save()`** — Clicks the Save/Create button.

**`open_view_popup(role_name)`** — Clicks the View action button for a specific role.

**`open_history_popup(role_name)`** — Clicks the History action button for a specific role.

**`close_popup()`** — Closes the current popup. If both View and History popups are open, must close the top one first.

### Tricky Bits

1. **mat-select doesn't update Angular model** — The most critical technical challenge. When you click a mat-select option, the UI updates visually but the Angular reactive form model does NOT reflect the change. On form submission, `entity_type` is still `null`, causing a silent failure. The JavaScript value-setter workaround is required for every mat-select interaction.

2. **formcontrolname is "entity_type"** — NOT "entityGroupName" as the field label suggests. If you try `mat-select[formcontrolname='entityGroupName']`, the element won't be found. This naming inconsistency has caused hours of debugging for new team members.

3. **Stacked popups** — The History popup can be opened on top of the View popup. Both popups use the same overlay container, and closing the History popup reveals the View popup underneath. The page object must track which popup is on top and close them in the correct order.

4. **No visible mat-error text** — When form validation fails (e.g., empty required field), the mat-error element exists in the DOM but has no visible text. Tests that check for specific error messages will fail because there's nothing to assert against. You can check for the mat-error element's presence but not its content.

5. **500+ character role names silently fail** — Submitting a role name longer than ~500 characters doesn't show an error. The form appears to submit successfully, but the role is never created. The server likely has a maxlength constraint that isn't communicated back to the client.

6. **No Delete option** — Once a role is created, there's no way to delete it through the UI. Roles accumulate in the data table permanently. This makes test cleanup difficult — test-created roles remain in the system unless manually removed from the database.

### Locator Strategies
- Role Name input: `input[formcontrolname='role_name']`
- Entity Group dropdown: `mat-select[formcontrolname='entity_type']` (NOT 'entityGroupName'!)
- mat-select options: `mat-option` within the open panel
- Save button: `button` with text "Save" or "Create"
- Data table rows: `mat-row` within the table container
- View button: `button[mattooltip='View']` within the specific `mat-row`
- History button: `button[mattooltip='History']` within the specific `mat-row`
- Popup close button: `button[mattooltip='Close']` or `mat-icon` with text "close"

## Known Bugs

| Bug ID | Severity | Description |
|---|---|---|
| BUG-001 | Medium | Role Name accepts spaces-only input. Creates invisible entries in the data table. |
| BUG-002 | High | Role Name accepts special characters including SQL injection strings (`' OR 1=1 --`) and XSS payloads (`<script>alert(1)</script>`). |
| BUG-003 | High | Duplicate role names are allowed. "Admin" can be created multiple times. |
| BUG-004 | Medium | Role names of 500+ characters silently fail to create. No error is shown to the user. |
| BUG-005 | Medium | No visible mat-error text when validation fails. The error element exists but has no text content. |
| BUG-006 | High | mat-select dropdown doesn't update Angular reactive form model. Requires JavaScript value-setter workaround. |
| BUG-007 | Low | No Delete option in the actions column. Roles cannot be removed through the UI. |
| BUG-008 | Low | History popup stacks on top of View popup, creating confusing overlay. |

## War Stories

### The formcontrolname Mystery

A new engineer was tasked with writing Role Creation tests. They opened the ERP in a browser, inspected the Entity Group Name dropdown, and saw the label "Entity Group Name". They wrote: `mat-select[formcontrolname='entityGroupName']`. The element was not found. They tried variations: `'entity_group_name'`, `'EntityGroupName'`, `'entityGroup'`. None worked. After 30 minutes of increasingly frustrated DOM inspection, they found it: `formcontrolname='entity_type'`. The label says "Entity Group Name" but the form control is called "entity_type". Nobody knows why. The frontend developer who named it has left the company. The naming lives on, confusing every new person who touches this module.

### The SQL Injection That Worked

During a security review, the team tested the Role Name field with various injection payloads. `' OR 1=1 --` was accepted and created as a role name. `<script>alert(1)</script>` was also accepted. The role name was stored in the database and displayed in the data table without any sanitization. While the ERP is an internal tool and the risk is lower than a public-facing application, the lack of input validation is a compliance concern. The test suite now includes regression tests for these cases, but they're marked as `@pytest.mark.xfail` because the bugs are known and unfixed.

### The Phantom Role

A tester created a role with a 600-character name (a string of "A"s). The form appeared to submit successfully — no error, no timeout. But the role never appeared in the data table. It wasn't in the database either. The server had a silent maxlength constraint that rejected the payload, but the error wasn't communicated to the client. The form stayed on screen as if nothing happened. This is BUG-004 — long role names silently fail. The test suite now has a boundary test that verifies this behavior and documents the ~500 character limit.

### The Stacked Popup Puzzle

A tester clicked "View" on a role, then clicked "History" on the same role without closing the View popup first. The History popup appeared on top of the View popup. They closed the History popup, expecting to be back on the main screen. Instead, the View popup was still there. Confused, they clicked "Close" again and finally got back to the main screen. In automation, this requires careful popup state tracking. The page object maintains a `_popup_stack` list to track which popups are open and closes them in LIFO order.

## Test Coverage

| Test Type | Status | Count |
|---|---|---|
| API Create Tests | ❌ None | 0 |
| API Update Tests | ❌ None | 0 |
| API Validation Tests | ❌ None | 0 |
| UI Create Tests | ✅ Passing | ~12 |
| UI Bug Regression Tests | ✅ Passing | ~8 |
| UI Popup Tests | ✅ Passing | ~4 |
| UI Negative Tests | ✅ Passing | ~6 |

## Files

```
access/
├── role_creation_page.py   1,714 LOC   # Page object
├── role_creation_data.py     179 LOC   # Data layer
└── test_role_creation_ui.py ~800 LOC   # UI tests
```

## What's Missing

1. **API tests** — Zero API test coverage. No create, update, delete, or validation tests via API. Given the security concerns (SQL injection, XSS), API-level validation testing is critical.

2. **API payload builder** — No `build_role_payload()` exists. This blocks API testing and batch creation.

3. **Security testing** — While the test suite includes regression tests for SQL injection and XSS inputs, there's no comprehensive security test suite. No tests for: stored XSS exploitation, SQL injection in the Entity Group dropdown, CSRF, or privilege escalation.

4. **Delete functionality** — No Delete option exists in the UI. No test verifies whether roles can be deleted via API. Test-created roles accumulate permanently.

5. **Edit flow** — No tests for editing an existing role. Can you change the role name? Change the entity group? What validation applies?

6. **Role-User integration** — No tests verify that a created role can be assigned to a user in the User Creation module. The end-to-end flow of Create Role → Assign to User → Verify Permissions is untested.

7. **Entity Group dependency** — No test verifies what happens when an Entity Group Definition is deleted (if possible) while roles reference it. Is the FK constraint enforced?

8. **Duplicate role name handling** — BUG-003 allows duplicates, but no test verifies what happens downstream when two roles have the same name. Which one gets assigned to a user?

9. **History popup content validation** — Tests open the History popup but don't validate the content. Does it correctly show creation date, modification date, user who made changes?

10. **Concurrent creation** — No tests verify what happens when two users create roles with the same name simultaneously. Is there a race condition?
