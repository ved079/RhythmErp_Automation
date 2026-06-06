# What's Left to Build — The Roadmap

> A prioritized list of gaps and future work. If you're looking for what to do next, start here.

---

## Priority 1: Missing API Test Suites (HIGH)

These modules have UI tests but NO API tests. API tests are faster, more reliable, and provide better regression coverage. Building these should be the first priority.

| Module | Section | Current State | Estimated Effort | Notes |
|--------|---------|---------------|-----------------|-------|
| **Agent** | Registration | UI test only | 4-6 hours | 5-step stepper, no `build_payload()` exists yet — need to discover API structure first |
| **Farmer** | Registration | UI test only | 6-8 hours | Most complex module (13 tabs), no `build_payload()` — large effort |
| **Entity Group Definition** | Access | UI test only | 2-3 hours | Simplest module (2 fields, 0 FK) — good first task |
| **Role Creation** | Access | UI test only | 3-4 hours | 2 fields + 1 FK dropdown |
| **User Creation** | Access | UI test only | 4-5 hours | 4 FK dropdowns, multiple input fields |

### How to Build These

Follow `docs/guides/adding_a_new_module.md` for each one. The order should be:

1. **Entity Group Definition** — easiest, good warm-up
2. **Role Creation** — adds FK dropdown complexity
3. **User Creation** — 4 FK dropdowns, more complex
4. **Agent** — first multi-stepper module to add API tests to
5. **Farmer** — most complex, do last when you have experience

---

## Priority 2: Missing Page Objects (MEDIUM)

These modules have API tests but NO page objects. They can only be tested via API, not through the UI.

| Module | Section | Current State | Estimated Effort | Notes |
|--------|---------|---------------|-----------------|-------|
| **Directors** | Registration | API only, no page object | 4-5 hours | Has KYC stepper child, needs UI interaction |
| **Member** | Registration | API only, no page object | 3-4 hours | Nearly identical to Directors |

Building page objects enables UI validation testing, which catches bugs that API tests miss (like missing SweetAlerts, broken dropdowns, CSS issues).

---

## Priority 3: Missing UI Validation Tests (MEDIUM)

These modules have API tests and page objects but NO UI validation tests.

| Module | Section | Current State | Estimated Effort | Notes |
|--------|---------|---------------|-----------------|-------|
| **Employee** | Registration | API + page, no UI test | 2-3 hours | Flat form, simple validation |
| **Commodity Base Rate** | Commodity | API only, no UI test | 3-4 hours | Has known bugs that should be captured as tests |

---

## Priority 4: Code Quality Improvements (LOW)

These aren't blocking but would improve maintainability.

### 4a. Fix `fill_step2_address()` Row-Scoped Locators

**File**: `pages/registration/modules/supplier/supplier_page.py`

The `fill_step2_address()` method uses generic XPath locators that always match the first address row. When there are 2 address rows (required for the dual address validation), filling the second row overwrites the first row instead. This needs row-indexed XPath locators.

The same issue exists in `fill_step3_bank()` if multiple bank rows are needed.

### 4b. Standardize Page Object Base Class

Some modules extend `BasePage`, others don't. Some use `navigate_to_page()`, others use `navigate_to_tax_authority()`. Standardizing on a common base class would reduce duplication.

Current state:
- **Extends BasePage**: Bank, HSN SAC, UOM, UOM Conversion, Season, Supplier, Customer
- **Does NOT extend BasePage**: Error Code Mst, Vehicle Master, Designation

### 4c. Remove Deprecated Code

Several modules have deprecated methods and patterns that should be cleaned up:
- Vehicle Master: `_click_action_button()` and `_click_action_button_by_index()` are deprecated
- UOM: `handle_error_toast()` is deprecated (Pattern C no longer exists)
- Season: Uses `Keys.ESCAPE` (violates the project-wide rule)

### 4d. Consolidate SweetAlert Handling

Every module implements its own SweetAlert handling. A shared utility in `common/` would reduce duplication and make it easier to handle new patterns.

---

## Priority 5: Infrastructure Improvements (LOW)

### 5a. Add a `make` or CLI Script for Common Commands

```bash
make test-api MODULE=bank        # Run API tests for a module
make test-ui MODULE=bank         # Run UI tests for a module
make batch-create MODULE=bank    # Run batch create
make add-module NAME=new_module  # Scaffold a new module
```

### 5b. Add Test Data Cleanup

Tests create entries in the shared ERP database but rarely clean them up. Over time, the database fills with test data. Adding a cleanup step (either in conftest.py teardown or as a separate script) would help.

### 5c. Better FK ID Management

FK IDs are currently hardcoded in each module's data file. If the ERP database is reset, all IDs change and every data file needs updating. The `FkResolver` can discover IDs dynamically, but it's not integrated into the test flow. Consider:
- Auto-resolving FK IDs in conftest.py before tests run
- Caching resolved IDs to disk with expiration
- Falling back to hardcoded IDs when the API is unavailable

---

## Priority 6: Dashboard Improvements (NICE-TO-HAVE)

### 6a. Real-Time Test Progress

The web dashboard shows live output but doesn't have a progress bar or estimated time remaining.

### 6b. Historical Trend Analysis

No way to see if tests are getting more or less reliable over time. Adding trend charts would help identify flaky tests.

### 6c. Test Failure Grouping

When multiple tests fail, there's no way to group failures by root cause (e.g., "5 tests failed because of FK ID changes").

---

## Summary

| Priority | Work Items | Total Estimated Hours |
|----------|-----------|----------------------|
| P1: API test suites | 5 modules | 19-26 hours |
| P2: Page objects | 2 modules | 7-9 hours |
| P3: UI validation tests | 2 modules | 5-7 hours |
| P4: Code quality | 4 items | 8-12 hours |
| P5: Infrastructure | 3 items | 6-10 hours |
| P6: Dashboard | 3 items | 10-15 hours |
| **TOTAL** | | **55-79 hours** |

---

## Quick Wins (Do These First)

If you only have a few hours, these give the most value for the least effort:

1. **Entity Group Definition API tests** (2-3 hours) — easiest module, proves you can follow the pattern
2. **Fix `fill_step2_address()` row-scoped locators** (1 hour) — prevents flaky Supplier tests
3. **Employee UI validation tests** (2-3 hours) — simplest registration module to add UI tests to
