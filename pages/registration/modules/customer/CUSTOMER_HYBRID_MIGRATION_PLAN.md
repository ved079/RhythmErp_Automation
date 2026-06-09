# Customer Module — Hybrid Test Migration Plan v2 (Approved)

**Status:** APPROVED (with 3 pre-conditions, all addressed in commit TBD)
**Date:** 2026-06-09
**Author:** Automation Team

---

## 1. Overview

Split 46 UI-only Customer tests into 3 layers:
- **API-Only (28 tests)** — Pure API calls, no browser
- **UI-Only (13 tests)** — Browser-only interactions (popups, overlays, stepper navigation)
- **Hybrid (5 tests)** — API setup + UI verification

**Target:** ~60 min execution → <7 min (90% reduction)

---

## 2. NO-DELETE CONSTRAINT

The ERP has **NO delete functionality**:
- No DELETE endpoint
- No delete button in the UI
- No soft-delete via `status=False`

**Cleanup strategy = Track + Report**, NOT delete:
- All created IDs are tracked via `CustomerAPIUtils.track_created_id()`
- Cleanup reports generated as JSON/CSV for manual database purging
- `create_and_expect_failure()` logs warnings instead of attempting cleanup
- `delete_customer()` and `cleanup_all()` will NEVER exist in this codebase

---

## 3. Architecture

### 3.1 New Files

| File | Purpose |
|------|---------|
| `utils/__init__.py` | Package init |
| `utils/api_customer_utils.py` | API wrapper: create, get, update, search, assert_validation_error, track, report |
| `utils/customer_cleanup.py` | No-delete strategy: tracking, reporting, optional inactive marking |
| `api/__init__.py` | Package init |
| `api/endpoints.py` | Centralized URL constants |

### 3.2 New Test Files

| File | Count | Markers |
|------|-------|---------|
| `test/test_customer_api_validations.py` | ~28 | `@pytest.mark.api` |
| `test/test_customer_ui_interactions.py` | ~13 | `@pytest.mark.ui` |
| `test/test_customer_hybrid_scenarios.py` | ~5 | `@pytest.mark.hybrid` |

### 3.3 Updated Files

| File | Changes |
|------|---------|
| `test/conftest.py` | Add `api`, `hybrid` markers; add `cu_api` fixture with no-delete teardown |
| `common/erp_api_client.py` | Add `_last_raw_response` storage in `create_entry()` |

---

## 4. Pre-Conditions (COMPLETED)

These 3 items were fixed before full migration:

1. **Bug Fix:** Removed duplicate `start_screenshot_broadcast(driver)` in conftest.py
2. **Thread Safety Warning:** Added prominent comments in `RhythmERPAPIClient.create_entry()` and `CustomerAPIUtils.assert_validation_error()` stating `_last_raw_response` is NOT thread-safe
3. **Phase 6b:** Added DOM verification step before mass time.sleep() replacement (see Phase 6b below)

---

## 5. Migration Phases

### Phase 1: Foundation (2–3 hours)
- Create `utils/` and `api/` directories with `__init__.py`
- Create `api/endpoints.py` with centralized URL constants
- Finalize `utils/api_customer_utils.py` (already created as skeleton)
- Create `utils/customer_cleanup.py`
- Update conftest.py with new markers and `cu_api` fixture

### Phase 2: API-Only Tests (4–5 hours)
- Create `test_customer_api_validations.py`
- Migrate 28 validation tests from UI to pure API
- All tests use `@pytest.mark.api`
- No browser required — runs in <2 minutes

### Phase 3: UI-Only Tests (3–4 hours)
- Create `test_customer_ui_interactions.py`
- Refactor 13 UI tests: popups, overlays, stepper, CDK intercepts
- Replace ALL `time.sleep()` with `WebDriverWait`
- All tests use `@pytest.mark.ui`

### Phase 4: Hybrid Tests (2–3 hours)
- Create `test_customer_hybrid_scenarios.py`
- 5 tests: API creates data → UI verifies display
- All tests use `@pytest.mark.hybrid`

### Phase 5: Validation & Cutover (2–3 hours)
- Run all 3 test suites independently
- Verify marker filtering works: `pytest -m api`, `pytest -m ui`, `pytest -m hybrid`
- Confirm no regressions vs. original 46 tests
- Remove or archive `test_customer_validation.py`
- Generate final cleanup report

### Phase 6: time.sleep() Elimination (3–4 hours)
- Replace all 68 `time.sleep()` / `wait_seconds()` calls in `customer_page.py`
- Each replacement uses appropriate `WebDriverWait` with EC conditions
- Full enumeration with line numbers provided separately

### **Phase 6b: DOM Verification (1–2 hours)**
> **MANDATORY** — Before mass-replacing all time.sleep() calls, each proposed
> WebDriverWait selector MUST be verified against the live ERP DOM.

Steps:
1. Open live ERP Customer screen in browser
2. For each of the 68 time.sleep() replacements, inspect the target element
3. Verify the proposed CSS/XPath selector matches the actual DOM
4. Document any selector adjustments needed in a verification log
5. Only after all selectors are verified, proceed with mass replacement

This prevents mass breakage from theoretical selectors that may not
match the actual Angular Material rendered DOM.

### Phase 7: Final Review (1–2 hours)
- Code review of all new files
- Update `Customer_Automation_Knowledge.md`
- Final push and tag

---

## 6. Timeline (Updated for No-Delete + Phase 6b)

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Foundation | 2–3 hrs | 2–3 hrs |
| Phase 2: API Tests | 4–5 hrs | 6–8 hrs |
| Phase 3: UI Tests | 3–4 hrs | 9–12 hrs |
| Phase 4: Hybrid Tests | 2–3 hrs | 11–15 hrs |
| Phase 5: Validation | 2–3 hrs | 13–18 hrs |
| Phase 6: sleep Elimination | 3–4 hrs | 16–22 hrs |
| **Phase 6b: DOM Verification** | **1–2 hrs** | **17–24 hrs** |
| Phase 7: Final Review | 1–2 hrs | 18–26 hrs |

**Total estimated:** 18–26 hours (increased from original 16–22 due to no-delete constraints and Phase 6b)

---

## 7. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| API payload structure differs from UI | High | Use `discover_structure("Customer")` to verify; test with single entry first |
| Angular Material overlays block UI tests | Medium | JS-first interaction pattern already proven (BUG-001 fix) |
| Cascading dropdown IDs change across tenants | Medium | FkResolver auto-discovers at runtime; never hardcode |
| Thread safety of `_last_raw_response` | Medium | Warning comments added; parallel API tests disabled until client refactored |
| **Test data accumulation** | **High** | **No-delete constraint means every test run adds permanent data. Mitigation: (1) timestamped+UUID prefixes for easy identification, (2) cleanup reports after every session, (3) scheduled manual DB purging, (4) optional inactive marking via PUT if supported** |
| Phase 6b selector mismatches | Medium | DOM verification against live ERP before mass replacement |
| FK ID pool drift | Low | DEFAULT_CUSTOMER_FK_IDS never modified; FkResolver refreshes from live API |

---

## 8. JSON Payload Structure (Customer Create/Update)

### 8.1 Create Payload (POST /core/dynamic-screen-wrapper/)

```json
{
  "id": "",
  "attribute_name": "Customer",
  "party_ref_id": null,
  "ownership_status_ref_id": 7,
  "name": "AutoCust_20260609143000_a1b2c3d4",
  "supply_type_ref_id": 225,
  "sale_type_ref_id": 1265,
  "default_currency_ref_id": 1,
  "email_id": "autocust_20260609143000_123@testmail.com",
  "mobile_no": 9876543210,
  "pan_no": "ABCDE1234F",
  "status": true,
  "vendor_code": null,
  "ref_id": null,
  "ref_type": null,
  "children": [
    {
      "stepper_name": "Additional Details",
      "is_stepper": true,
      "details": [],
      "children": [],
      "display_name_as": "Contact Person",
      "office_no": "",
      "is_tds_applicable": false,
      "is_gst_set_off": true,
      "customer_status": null,
      "customer_type_ref_id": null,
      "packing_material_ref_id": null,
      "preferred_payment_method_ref_id": 55,
      "gst_registration_status": 49,
      "gst_registration_type": 50,
      "payment_terms_ref_id": 131,
      "delivery_terms_ref_id": 129,
      "mode_of_delivery_ref_id": 30,
      "courier_terms_ref_id": 52,
      "deposit": 5000.0,
      "quantity_tolerance": 10.5,
      "rate_tolerance": 5.0
    },
    {
      "stepper_name": "Address Details",
      "is_stepper": true,
      "details": [
        {
          "address_type": 43,
          "country_ref_id_id": 8,
          "state_ref_id_id": 22,
          "district_ref_id_id": 393,
          "sub_district_ref_id_id": 5463,
          "village_ref_id_id": null,
          "address": "123 MG Road, Pune",
          "pin_code": 411001,
          "gstin": "27ABCDE1234F1Z5",
          "same_as_above": null,
          "address2": null,
          "demo_details": null,
          "details": []
        }
      ],
      "children": []
    },
    {
      "stepper_name": "Customer Bank Details",
      "is_stepper": true,
      "details": [
        {
          "bank_name": "Bank",
          "bank_branch_code": "Mumbai Branch",
          "bank_ifsc_code": "SBIN0001234",
          "account_type": 1849,
          "bank_account_holder_name": "Shree Traders Electronics",
          "bank_account_no": 123456789012,
          "bank_doc_id": 36,
          "bank_attachment_path": null,
          "details": []
        }
      ],
      "children": []
    }
  ]
}
```

### 8.2 Update Payload (PUT /core/dynamic-screen-wrapper/Customer/{id}/)

Same structure as Create, but:
- `"id"` is set to the existing customer's database ID (not empty string)
- Only changed fields need to differ from the original

---

## 9. conftest.py Marker Registration (conftest.py ONLY, no pytest.ini)

```python
def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: Critical happy-path tests")
    config.addinivalue_line("markers", "sanity: Core feature validation tests")
    config.addinivalue_line("markers", "regression: Full suite")
    config.addinivalue_line("markers", "bug: Known/confirmed bug tests")
    config.addinivalue_line("markers", "ui: Popup, dialog, form UI behavior")
    config.addinivalue_line("markers", "api: API-only tests — no browser needed")
    config.addinivalue_line("markers", "hybrid: API setup + UI verification")
    config.addinivalue_line("markers", "critical: Must-pass tests for CI gate")
```

---

## 10. Hybrid Test Sample (CU_B01)

```python
@pytest.mark.hybrid
def test_CU_B01_api_create_then_ui_verify_dropdown(cu_page, cu_api):
    \"\"\"CU_B01: API creates customer, UI verifies mat-select dropdown options.\"\"\"

    # --- API Setup ---
    result = cu_api.create_customer(name_prefix="HybridB01")
    assert result is not None, "API customer creation failed"
    customer_id = result["id"]
    company_name = result.get("name", "")

    # --- UI Verification ---
    cu_page.navigate_to_page()
    cu_page.click_add_button()
    assert cu_page.is_add_form_open(), "Add form did not open"

    # Search for the created customer
    cu_page.search_customer(company_name)
    assert cu_page.is_customer_in_results(company_name), \
        f"Created customer '{company_name}' not found in search results"

    # Open the customer for editing to verify dropdown values
    cu_page.click_edit_on_customer(company_name)

    # Verify GST Registration Status dropdown has correct options
    gst_options = cu_page.get_mat_select_options("Gst Registration Status")
    option_texts = [opt.text for opt in gst_options]
    assert "Registered" in option_texts, "'Registered' not in GST status options"
    assert "Unregistered" in option_texts, "'Unregistered' not in GST status options"

    # Verify Account Type dropdown has correct options
    acct_options = cu_page.get_mat_select_options("Account Type")
    acct_texts = [opt.text for opt in acct_options]
    assert "Current" in acct_texts, "'Current' not in Account Type options"
    assert "Saving" in acct_texts, "'Saving' not in Account Type options"
```

---

## End of Plan v2
