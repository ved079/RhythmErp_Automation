# Module: User Creation

> The most complex access module — 2,559 LOC page object with 4 mat-select dropdowns located by nth-of-type index (no formcontrolname attributes), 6 bugs, and 9 documented FIX entries tracking the evolution of the automation code.

## At a Glance

| Section | Value |
|---|---|
| Complexity Rank | Most complex access module |
| Steppers | None — flat form |
| Repeating Rows | None |
| API Tests | None |
| UI Tests | Yes |
| Page Object | `user_creation_page.py` (2,559 LOC) |
| Data File | `user_creation_data.py` (268 LOC) |
| Batch Create | None |
| attribute_name | `UserCreationScreen` |

## The ERP Screen

The User Creation screen creates user accounts that can log into the ERP system. Each user is associated with a role, entity, and designation, and has credentials for authentication.

**Navigation URL:** `/access/user-creation`

### Form Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| Username | Free text | Yes | ⚠️ Spaces accepted, duplicates silently fail |
| Email | Free text | Yes | ⚠️ No email format validation |
| First Name | Free text | Yes | — |
| Last Name | Free text | No | — |
| Password | Password input | Yes | — |
| User Type | mat-select dropdown | Yes | Located by nth-of-type index |
| Role | mat-select dropdown | Yes | Located by nth-of-type index |
| Entity | mat-select dropdown | Yes | Located by nth-of-type index |
| Designation | mat-select dropdown | Yes | Located by nth-of-type index; duplicate "Manager" option |
| Active | Checkbox | No | Default: checked |
| Staff | Checkbox | No | Default: unchecked |

### The 4 mat-select Dropdowns — Located by Index
The User Creation form has 4 mat-select dropdowns (User Type, Role, Entity, Designation) that have **NO `formcontrolname` attributes**. This is unique in the ERP — every other module's dropdowns have `formcontrolname`. Without these attributes, the standard locator strategy (`mat-select[formcontrolname='...']`) doesn't work.

The workaround is to locate dropdowns by their **nth-of-type index** among all `mat-select` elements on the page:
- `mat-select:nth-of-type(1)` → User Type
- `mat-select:nth-of-type(2)` → Role
- `mat-select:nth-of-type(3)` → Entity
- `mat-select:nth-of-type(4)` → Designation

This is fragile — if a new mat-select is added to the form, all indices shift. The `_find_dropdown_by_index()` method provides a fallback with error handling.

### Duplicate "Manager" Designation
The Designation dropdown contains a duplicate "Manager" option. Two separate entries with the same display text but different IDs. This means selecting "Manager" is ambiguous — you might get either one. Tests should avoid selecting "Manager" or explicitly handle the ambiguity.

## API Contract

### Endpoint
`POST /api/access/user-creation` (presumed — no API payload builder exists)

### attribute_name
`UserCreationScreen`

### Payload Structure
```json
{
  "attribute_name": "UserCreationScreen",
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "password": "string",
  "user_type_id": "FK",
  "role_id": "FK",
  "entity_id": "FK",
  "designation_id": "FK",
  "is_active": true,
  "is_staff": false,
  "details": [],
  "children": []
}
```

### FK Dependencies
The 4 dropdown fields reference:
| Field | FK Source | Notes |
|---|---|---|
| User Type | User type reference | System-defined |
| Role | Role Creation module | Created by Role Creation |
| Entity | Entity Group Definition | Created by EGD module |
| Designation | Designation reference | ~56 options, duplicate "Manager" |

No FK pools are formally defined in the data layer — all dropdown selections are made from the live UI.

## Data Layer

### Current State: Minimal
The `user_creation_data.py` file (268 LOC) provides:
- Username generation (`f"user_{random_string()}"`)
- Email generation (`f"{username}@test.com"`)
- Password generation (random strong passwords)
- First/Last name generation
- Test data dictionaries for bug regression tests

### No FK Pools
No FK ID pools are fetched. All dropdown values are selected from the live UI at runtime via the page object's dropdown interaction methods.

### Validation Rules (Expected vs Actual)
| Rule | Expected | Actual |
|---|---|---|
| Username: duplicate | ❌ Should error | ✅ BUG: Silently fails, NO error shown |
| Username: maxlength | ✅ Should enforce | ❌ BUG: No maxlength |
| Username: spaces | ❌ Should reject | ✅ BUG: Spaces accepted |
| Email: format | ✅ Should validate | ❌ BUG: No validation |
| Designation: duplicate "Manager" | ❌ Should deduplicate | ✅ BUG: Duplicate option |
| mat-error visibility | ✅ All errors visible | ❌ BUG: Only 1 at a time |

## Page Object

### Key Methods

**`fill_username(username)`** — Types the username. Beware of BUG-001: duplicate usernames silently fail with no error message.

**`fill_email(email)`** — Types the email. No format validation on the client side (BUG-002).

**`fill_password(password)`** — Types the password into the password field. The field uses a standard password input with toggle visibility.

**`fill_names(first_name, last_name)`** — Types first and last names.

**`select_user_type()`** — Selects a random User Type from the first mat-select dropdown (nth-of-type(1)). Uses the JS value-setter workaround for Angular model sync.

**`select_role()`** — Selects a random Role from the second mat-select dropdown (nth-of-type(2)). Uses the JS value-setter workaround.

**`select_entity()`** — Selects a random Entity from the third mat-select dropdown (nth-of-type(3)). Uses the JS value-setter workaround.

**`select_designation()`** — Selects a random Designation from the fourth mat-select dropdown (nth-of-type(4)). Avoids the duplicate "Manager" option. Uses the JS value-setter workaround.

**`_find_dropdown_by_index(index)`** — Fallback method for locating mat-select dropdowns by their position on the page:
```python
def _find_dropdown_by_index(self, index):
    dropdowns = self.page.locator("mat-select")
    count = dropdowns.count()
    if index >= count:
        raise ValueError(f"Expected at least {index + 1} mat-select elements, found {count}")
    return dropdowns.nth(index)
```

**`set_active(is_active)`** — Sets the Active checkbox.

**`set_staff(is_staff)`** — Sets the Staff checkbox.

**`click_save()`** — Clicks the Save/Create button.

### The 9 FIX Entries

The page object code contains 9 FIX comments documenting the evolution of automation fixes:

| FIX | Description |
|---|---|
| FIX-1 | Added JS value-setter for mat-select Angular model sync. Without this, dropdown selections are visually present but the form model is null. |
| FIX-2 | Changed from `formcontrolname` locator to `nth-of-type` index. The mat-select elements don't have formcontrolname attributes. |
| FIX-3 | Added duplicate "Manager" avoidance in designation selection. Random selection could pick either duplicate, causing non-deterministic test results. |
| FIX-4 | Added wait-after-select for mat-select model propagation. Even with JS value-setter, the Angular change detection cycle needs time. |
| FIX-5 | Changed username generation to include timestamp + random to avoid collisions in parallel test runs. |
| FIX-6 | Added explicit close of mat-select panel after selection. Panels were staying open and overlapping subsequent dropdowns. |
| FIX-7 | Added scroll-into-view before interacting with lower form fields. The form is long and bottom fields may be off-screen. |
| FIX-8 | Added retry logic for Save button click. First click sometimes fails due to pending Angular change detection. |
| FIX-9 | Added fallback locator for Save button. The button text changes between "Save" and "Create" depending on the form state. |

### Tricky Bits

1. **No formcontrolname on mat-select elements** — The single biggest challenge. Every other module's dropdowns have `formcontrolname` attributes. User Creation's 4 mat-select dropdowns don't. The `_find_dropdown_by_index()` method and nth-of-type locators are the only way to interact with them, but this is fragile.

2. **Angular form model sync (same as Role Creation)** — The mat-select dropdowns don't update the Angular reactive form model on click. The JS value-setter workaround is required. This is the same issue as Role Creation BUG-006, but it affects 4 dropdowns instead of 1.

3. **Duplicate username silently fails** — If you create a user with a username that already exists, there is NO error message. No toast, no SweetAlert, no mat-error. The form just stays on screen as if nothing happened. This is extremely confusing because it looks like a successful submission that didn't navigate away. Tests must explicitly check for the user in the data table to confirm creation.

4. **Only 1 mat-error visible at a time** — When multiple fields have validation errors, only one mat-error is visible. The others exist in the DOM but are hidden. This means a test that checks for a specific error message might see a different error first. Tests must address errors one at a time, re-submit, and check for the next error.

5. **Duplicate "Manager" designation** — The Designation dropdown has two "Manager" entries with different IDs. Selecting "Manager" is ambiguous. The page object's `select_designation()` method avoids "Manager" entirely and picks from other options.

6. **nth-of-type index fragility** — If the form is modified to add or reorder mat-select elements, all index-based locators break. There's no way to make these locators robust without formcontrolname attributes being added to the source HTML.

7. **No email validation** — Any string is accepted as an email. "notanemail", "a@b", and "" (empty after required check) are all accepted.

### Locator Strategies
- Username: `input[formcontrolname='username']` (this one has formcontrolname)
- Email: `input[formcontrolname='email']` (this one has formcontrolname)
- First Name: `input[formcontrolname='first_name']`
- Last Name: `input[formcontrolname='last_name']`
- Password: `input[formcontrolname='password']` or `input[type='password']`
- User Type dropdown: `mat-select:nth-of-type(1)` — NO formcontrolname
- Role dropdown: `mat-select:nth-of-type(2)` — NO formcontrolname
- Entity dropdown: `mat-select:nth-of-type(3)` — NO formcontrolname
- Designation dropdown: `mat-select:nth-of-type(4)` — NO formcontrolname
- Active checkbox: `mat-checkbox` with label "Active"
- Staff checkbox: `mat-checkbox` with label "Staff"
- Save button: `button` with text "Save" OR "Create" (see FIX-9)
- Data table rows: `mat-row` within the table container

## Known Bugs

| Bug ID | Severity | Description |
|---|---|---|
| BUG-001 | Critical | Duplicate username silently fails with NO error message. No toast, no SweetAlert, no mat-error. User has no indication that creation failed. |
| BUG-002 | Medium | No maxlength on Username. Extremely long usernames are accepted and may break the UI. |
| BUG-003 | Medium | No email format validation. Any string is accepted as an email address. |
| BUG-004 | Low | Spaces accepted in Username. "John Doe" is a valid username, which may cause issues with login (are spaces trimmed?). |
| BUG-005 | Low | Duplicate "Manager" designation option. Two entries with the same label but different IDs. Selecting "Manager" is ambiguous. |
| BUG-006 | Medium | Only 1 mat-error visible at a time. When multiple fields have errors, the user sees them one at a time, making it hard to fix all issues at once. |

## War Stories

### The Silent Duplicate Username

An engineer ran the User Creation test suite in parallel with 4 workers. Three of the four tests passed. One failed — not with an error, but with a missing assertion. The test created a user, then checked the data table for the username. It wasn't there. The username had been generated with a timestamp, but two workers happened to generate the same timestamp within the same second. The second creation was silently rejected by the server (BUG-001), but no error was returned. The test expected either a success (user in table) or an error (toast message), but got neither. The fix was to add more entropy to the username generator (FIX-5) and to add an explicit check: if the user isn't in the table after creation, fail with a clear message.

### The Four Faceless Dropdowns

When the User Creation page object was first being written, the engineer tried the standard approach: `mat-select[formcontrolname='user_type']`. Element not found. They tried every reasonable variation of the field name. Nothing worked. After inspecting the DOM, they discovered that the 4 mat-select elements simply don't have formcontrolname attributes. The only way to tell them apart is their position on the page. This led to the nth-of-type strategy (FIX-2). But this is inherently fragile — if a designer rearranges the form or adds a new dropdown, all the indices shift. The team has lobbied the frontend developers to add formcontrolname attributes, but it hasn't happened yet.

### The Missing Email Validation

A test was written to verify that invalid email addresses are rejected. It submitted "notanemail" as the email. The API returned 201 Created. The test was marked as failing — it expected a 400. But the server genuinely accepted "notanemail" as a valid email. There is no server-side email format validation (BUG-003). The test was updated to a `@pytest.mark.xfail` documenting the bug. The real risk is downstream: password reset emails, notification emails, and email-based login will all fail for users with invalid emails, but the system allows their creation.

### The Solo mat-error

A tester left the Username field empty and clicked Save. A mat-error appeared: "Username is required." They then left both Username and Email empty and clicked Save. Still only one mat-error: "Username is required." They filled the Username and clicked Save again. Now the mat-error changed to "Email is required." One at a time, one at a time. This is BUG-006 — only one mat-error is visible at a time. In automation, this means you can't write a test that checks for multiple error messages simultaneously. You have to address each error sequentially and re-submit.

## Test Coverage

| Test Type | Status | Count |
|---|---|---|
| API Create Tests | ❌ None | 0 |
| API Update Tests | ❌ None | 0 |
| API Validation Tests | ❌ None | 0 |
| UI Create Tests | ✅ Passing | ~15 |
| UI Bug Regression Tests | ✅ Passing | ~6 |
| UI Dropdown Tests | ✅ Passing | ~8 |
| UI Negative Tests | ✅ Passing | ~6 |
| UI Checkbox Tests | ✅ Passing | ~3 |

## Files

```
access/
├── user_creation_page.py   2,559 LOC   # Page object — largest in access
├── user_creation_data.py     268 LOC   # Data layer
└── test_user_creation_ui.py ~900 LOC   # UI tests
```

## What's Missing

1. **API tests** — Zero API test coverage. No create, update, delete, or validation tests via API. Given BUG-001 (silent duplicate failure), API testing would provide clearer feedback on error responses.

2. **API payload builder** — No `build_user_payload()` exists. This blocks API testing and batch user creation.

3. **formcontrolname attributes** — The most impactful improvement would be frontend changes to add `formcontrolname` attributes to the 4 mat-select elements. This would eliminate the fragile nth-of-type locator strategy and make the automation more robust.

4. **Duplicate username detection** — No test verifies that duplicate usernames are properly handled. BUG-001 means they silently fail, but there's no test that explicitly demonstrates this behavior and checks for the absence of error messages.

5. **Login integration** — No test verifies that a created user can actually log in. Does the password work? Does the username with spaces work? Does the user see the correct role-based permissions?

6. **Edit/Update flow** — No tests for editing an existing user. Can you change the role? Change the password? Deactivate a user? Change the email?

7. **Delete functionality** — No tests for deleting a user. Is there a Delete option? Can users be deactivated via the Active checkbox?

8. **Role-Entity-Designation consistency** — No tests verify that the selected Role, Entity, and Designation are compatible. Can you assign a Region-level role to a Country-level entity? What happens?

9. **Staff flag implications** — No tests verify what the Staff flag actually does. Does it grant admin access? Does it bypass role permissions? Is it the Django `is_staff` flag?

10. **Concurrent creation stress test** — No tests verify behavior when multiple users are created simultaneously with similar usernames. BUG-001 makes this a real risk in parallel test execution.

11. **Password policy** — No tests for password requirements. Is there a minimum length? Complexity requirement? Can you use "password" or "123456"?

12. **Dropdown option dependency** — No tests verify that the Role dropdown options depend on the selected Entity Group, or that the Entity options depend on the Role. If these cascading dependencies exist, they're not tested.

13. **Session management** — No tests verify what happens when a user's session expires while they're on the User Creation form. Is the data preserved? Is there auto-save?
