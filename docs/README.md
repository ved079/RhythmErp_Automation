# RhythmERP Automation — Knowledge Transfer Documentation

> Complete KT documentation for the RhythmERP automation project. Written so the next developer can pick up where the previous one left off.

---

## Quick Start

**New here?** Read these in order:

1. [`00_BEFORE_YOU_START.md`](00_BEFORE_YOU_START.md) — Get your environment set up and run your first test
2. [`01_ERP_CRASH_COURSE.md`](01_ERP_CRASH_COURSE.md) — Understand what RhythmERP does
3. [`02_HOW_THIS_REPO_WORKS.md`](02_HOW_THIS_REPO_WORKS.md) — Understand the code structure
4. [`guides/the_angular_material_survival_guide.md`](guides/the_angular_material_survival_guide.md) — Understand the #1 technical challenge

Then read the module-specific docs as you work on each module.

---

## Cross-Cutting Guides

| Doc | Purpose | Priority |
|-----|---------|----------|
| [00_BEFORE_YOU_START.md](00_BEFORE_YOU_START.md) | Day 1 survival — setup, first test, common errors | 🔴 Must read |
| [01_ERP_CRASH_COURSE.md](01_ERP_CRASH_COURSE.md) | What is RhythmERP? Business context for each section | 🔴 Must read |
| [02_HOW_THIS_REPO_WORKS.md](02_HOW_THIS_REPO_WORKS.md) | Code structure, conventions, file types | 🔴 Must read |
| [guides/the_angular_material_survival_guide.md](guides/the_angular_material_survival_guide.md) | JS hacks, never ESCAPE, dropdown patterns | 🔴 Must read |
| [guides/api_testing_pattern.md](guides/api_testing_pattern.md) | 4-layer API test architecture | 🟡 Read before writing API tests |
| [guides/adding_a_new_module.md](guides/adding_a_new_module.md) | Step-by-step recipe for new modules | 🟡 Read before building a new module |
| [guides/whats_left_to_build.md](guides/whats_left_to_build.md) | Roadmap of gaps and priorities | 🟡 Read for planning |
| [quick_reference.md](quick_reference.md) | Cheat sheet — attribute_name values, commands, rules | 🟢 Keep pinned open |

---

## Module Documentation

### ⭐ Must-Read Modules (read these 3 first)

| Module | Section | Why Read It |
|--------|---------|-------------|
| [common_settings/bank.md](modules/common_settings/bank.md) | Common Settings | The first module built — patterns everyone copies |
| [common_settings/uom.md](modules/common_settings/uom.md) | Common Settings | The gold standard — most optimized page object |
| [registration/supplier.md](modules/registration/supplier.md) | Registration | The most complex, most battle-tested module |

### Common Settings (10 modules)

| Module | Complexity | Steppers | Key Quirk |
|--------|-----------|----------|-----------|
| [bank.md](modules/common_settings/bank.md) | Medium | 0 | No formcontrolname, ALL UPPERCASE names, 5 bugs |
| [designation.md](modules/common_settings/designation.md) | Simple | 0 | Simplest module, no FK pools, duplicate names accepted |
| [season.md](modules/common_settings/season.md) | Simple | 0 | Duplicate name hangs ERP indefinitely |
| [hsn_sac.md](modules/common_settings/hsn_sac.md) | Simple | 0 | Real Indian GST codes, JSON.stringify dropdown reading |
| [error_code_mst.md](modules/common_settings/error_code_mst.md) | Simple | 0 | No success SweetAlert, custom toggle, retry on fill |
| [tax_authority.md](modules/common_settings/tax_authority.md) | Simple | 0 | Searchable dropdown, 3-tier click strategy |
| [tax_rate.md](modules/common_settings/tax_rate.md) | Complex | 1 | Only CS module with stepper, Edit is "Version", never remove .cdk-overlay-container |
| [uom.md](modules/common_settings/uom.md) | Simple-Medium | 0 | Gold standard, search button never clickable, 3 SweetAlert patterns |
| [uom_conversion.md](modules/common_settings/uom_conversion.md) | Simple-Medium | 0 | Has backup file (rewrite), 22+ digit numbers break records |
| [vehicle_master.md](modules/common_settings/vehicle_master.md) | Medium | 0 | Largest "simple" module (1896 LOC), refresh breaks toolbar |

### Commodity Settings (9 modules)

| Module | Complexity | Key Quirk |
|--------|-----------|-----------|
| [item_master.md](modules/commodity_settings/item_master.md) | High | 7-dropdown cascade ORDER matters |
| [crop_master.md](modules/commodity_settings/crop_master.md) | Medium | Has custom report generator |
| [commodity_quality_parameter.md](modules/commodity_settings/commodity_quality_parameter.md) | Medium-High | Version/History same CSS class, duplicate items in dropdown |
| [commodity_base_rate.md](modules/commodity_settings/commodity_base_rate.md) | Medium | To Date overridden to 2099, no UI validation tests |
| [item_attribute.md](modules/commodity_settings/item_attribute.md) | Simple-Medium | mat-select Angular model bug |
| [item_category.md](modules/commodity_settings/item_category.md) | Simple | Never use Keys.ESCAPE |
| [item_group.md](modules/commodity_settings/item_group.md) | Simple | Same pattern as item_category |
| [quality_parameter_master.md](modules/commodity_settings/quality_parameter_master.md) | Simple-Medium | Zero validation — accepts anything |
| [services_master.md](modules/commodity_settings/services_master.md) | Simple-Medium | Client/server validation mismatch |

### Registration (7 modules)

| Module | Complexity | Key Quirk |
|--------|-----------|-----------|
| [supplier.md](modules/registration/supplier.md) | High | Dual address required, Luhn GSTIN, 7 helper scripts |
| [customer.md](modules/registration/customer.md) | High | 14 FK pools, imports from supplier, empty details[] |
| [farmer.md](modules/registration/farmer.md) | Very High | 13 tabs, 7 bugs, trailing tab chars, name collisions |
| [company_onboarding.md](modules/registration/company_onboarding.md) | High | 6-step stepper + update flow, 15-attempt address retry |
| [agent.md](modules/registration/agent.md) | Medium | 5-step stepper, no API tests yet |
| [employee.md](modules/registration/employee.md) | Simple | Flat form, only Status is required |
| [directors.md](modules/registration/directors.md) | Medium | No page object, API only, "distintive_number" typo |
| [member.md](modules/registration/member.md) | Medium | No page object, API only, phone accepts 3 digits |

### Access (3 modules)

| Module | Complexity | Key Quirk |
|--------|-----------|-----------|
| [entity_group_definition.md](modules/access/entity_group_definition.md) | Simple | 8 bugs in 2 fields, no SweetAlert |
| [role_creation.md](modules/access/role_creation.md) | Simple-Medium | formcontrolname is "entity_type", SQL injection accepted |
| [user_creation.md](modules/access/user_creation.md) | Medium | 4 dropdowns with no formcontrolname, 9 FIX entries |

---

## The 6 Hard Rules

1. **JS clicks only** — never use Selenium's `.click()` for Angular Material
2. **JS input only** — nativeInputValueSetter, not `send_keys()`
3. **Dropdowns need Angular sync** — call `_sync_dropdown_angular_model()` after every selection
4. **Never Keys.ESCAPE** — it closes the entire form
5. **Never remove .cdk-overlay-container** — kills Angular's overlay engine
6. **Always use row-scoped locators** for repeating sections

---

## Test Coverage Summary

| Section | Modules | API Tests | UI Tests | Remaining |
|---------|---------|-----------|----------|-----------|
| Common Settings | 10 | ✅ 30 | ✅ 10 | — |
| Commodity Settings | 9 | ✅ 27 | ✅ 8 | CBR missing UI test |
| Registration | 7 | ✅ 17 | ✅ 5 | Agent, Farmer need API tests |
| Access | 3 | ❌ 0 | ✅ 3 | All need API tests |
| Company Onboarding | 1 | ✅ 3 | ✅ 2 | — |
| **Total** | **30** | **~77** | **~28** | **5 modules need API tests** |

---

*Last updated: June 2026*
