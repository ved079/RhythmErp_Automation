# Quick Reference — Cheat Sheet

> One page. Pinned open. Everything you need at a glance.

---

## Running Tests

```bash
# Activate venv first!
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# API tests (fast, no browser)
pytest pages/{section}/modules/{module}/test/api/ -v

# UI tests (slow, needs Chrome)
pytest pages/{section}/modules/{module}/test/test_{module}_validation.py -v

# Single test
pytest pages/common_settings/modules/bank/test/api/test_bank_payload.py::TestBankPayload::test_valid_payload_returns_200 -v

# Run with keyword filter
pytest pages/common_settings/modules/bank/test/api/ -v -k "payload"

# Run without headless (see the browser)
# Set HEADLESS=false in .env or remove --headless flag
```

---

## Key URLs

| What | URL |
|------|-----|
| ERP | https://rhythmerp.algorhythms.in |
| API endpoint | POST /core/dynamic-screen-wrapper/ |
| Auth endpoint | POST /auth/login1/ |
| Tenant ID | 599 |
| Test credentials | user@admin.com / Tenant@123456789 |

---

## attribute_name Values

| Module | attribute_name |
|--------|---------------|
| Bank | `"Bank"` |
| Designation | `"Designation"` |
| Error Code Master | `"ErrorCodeMst"` |
| HSN SAC | `"HsnSac"` |
| Season | `"Season"` |
| Tax Authority | `"TaxAuthority"` |
| Tax Rate | `"TaxRate"` |
| UOM | `"Uom"` (capitalized, not UOM) |
| UOM Conversion | `"UomConversion"` |
| Vehicle Master | `"VehicleMaster"` |
| Item Master | `"ItemMaster"` |
| Item Category | `"ItemCategory"` |
| Item Group | `"ItemGroup"` |
| Item Attribute | `"ItemAttribute"` |
| Crop Master | `"CropMaster"` |
| Commodity Quality Parameter | `"CommodityQualityParameter"` |
| Commodity Base Rate | `"CommodityBaseRate"` |
| Quality Parameter Master | `"QualityParameterMaster"` |
| Services Master | `"ServicesMaster"` |
| Supplier | `"Supplier"` |
| Customer | `"Customer"` |
| Farmer | `"Farmer"` |
| Agent | `"Agent"` |
| Employee | `"Employee"` |
| Directors | `"Directors"` |
| Member | `"Member"` |
| Entity Group Definition | `"EntityGroupDefinition"` |
| Role Creation | `"Rolecreationscreen"` |
| User Creation | `"UserCreationScreen"` |
| Company Onboarding | `"CompanyOnboarding"` |

---

## Module Paths

```
pages/common_settings/modules/{module}/     → Bank, UOM, Season, etc.
pages/commodity_settings/modules/{module}/  → Item Master, Crop Master, etc.
pages/registration/modules/{module}/        → Supplier, Customer, Farmer, etc.
pages/access/modules/{module}/              → Entity Group, Role, User
pages/company_onboarding/                   → Company Onboarding
```

---

## The 6 Hard Rules

1. **JS clicks only** — `driver.execute_script("arguments[0].click()", el)`
2. **JS input only** — nativeInputValueSetter + dispatchEvent, not send_keys()
3. **Dropdowns need Angular sync** — after clicking option, call `_sync_dropdown_angular_model()`
4. **Never Keys.ESCAPE** — closes the entire form, not just overlays
5. **Never remove .cdk-overlay-container** — kills Angular's overlay engine permanently
6. **Always use row-scoped locators** for repeating sections — generic XPaths match the first row

---

## SweetAlert Patterns

| Pattern | Icon | Button | Modules |
|---------|------|--------|---------|
| A (success) | ✓ | OK | Bank, Supplier, Customer, Role Creation |
| B (validation) | ⚠ | Cancel | UOM, HSN SAC, UOM Conversion |
| Silent close | — | — | Tax Rate, Tax Authority, Error Code Mst, Entity Group |

---

## FK Chain Order (Cascading Dropdowns)

```
Country → State → District → Taluka → Village
Category → Group → Type → Attribute 1-5 (Item Master)
```

Always fill in order. Always wait 1 second between cascading selections.

---

## Test Coverage Status

| Section | Modules | API Tests | UI Tests | Gaps |
|---------|---------|-----------|----------|------|
| Common Settings | 10 | ✅ All | ✅ All | None |
| Commodity Settings | 9 | ✅ All | ✅ Most | CBR missing UI test |
| Registration | 7 | 5 of 7 | 5 of 7 | Agent, Farmer need API tests |
| Access | 3 | 0 of 3 | ✅ All | All need API tests |
| Company Onboarding | 1 | ✅ All | ✅ All | None |

---

## File Naming Convention

```
{module_name}_page.py       → Page Object
{module_name}_data.py       → FK pools + payload builder
test_{module}_validation.py → UI validation tests
test/api/conftest.py        → API test fixtures
test/api/test_*_payload.py  → API payload validation
test/api/test_*_schema.py   → API schema conformance
test/api/test_*_perf.py     → API performance benchmarks
scripts/batch_create.py     → Bulk creation script
```

---

## Common Error → Fix

| Error | Fix |
|-------|-----|
| `SessionNotCreatedException` | ChromeDriver version mismatch — `pip install webdriver-manager --upgrade` |
| `ElementClickInterceptedException` | Something overlapping — use JS click |
| `StaleElementReferenceException` | DOM changed — re-find the element |
| `TimeoutException` | Element not appearing — increase wait or check if page loaded |
| `ElementNotInteractableException` | Element exists but hidden — wait for visibility or use JS |
| 400 from API | Check FK IDs, required fields, field types |
| "Validation Failed" SweetAlert | Angular form model not updated — use `_sync_dropdown_angular_model()` |

---

## Reading Order

```
Day 1:  00_BEFORE_YOU_START → Run your first test
Day 2:  01_ERP_CRASH_COURSE → 02_HOW_THIS_REPO_WORKS
Day 3:  Angular Material Survival Guide → bank.md → uom.md
Week 2: supplier.md → Work on your assigned module
Always: THIS CHEAT SHEET (pinned open)
```
