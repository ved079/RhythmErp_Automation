# Module: Commodity Base Rate

> Sets base prices per unit for each commodity. The starting point for all pricing calculations in the ERP.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Commodity Settings |
| **Complexity** | Medium |
| **Steppers** | 0 — popup form |
| **Repeating rows** | No |
| **API tests** | ✅ payload, schema, perf |
| **UI tests** | ❌ No UI validation tests |
| **Page object** | ✅ (1,686 LOC) |
| **Data file** | ✅ cbr_data.py |
| **batch_create** | ✅ |

---

## The ERP Screen

Found under **Commodity Settings → Commodity Base Rate**. Each entry defines the base price for a specific item, effective from a given date. Rates can be versioned — when the price changes, a new version is created rather than editing the existing one.

### Key Fields
- **Item Name** — mat-select dropdown (links to Item Master)
- **Item Rate** — number input (base price per unit)
- **From Date / To Date** — date range for the rate's validity
- **UOM** — unit of measurement for the rate

### Navigation URL
`/#/commodity-settings/commodity-base-rate`

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
attribute_name: "CommodityBaseRate"
```

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| BUG-001 | High | Item Rate accepts non-numeric input — no client-side validation |
| BUG-002 | Medium | Item Rate accepts zero value — should have minimum validation |
| BUG-003 | Medium | Listing shows raw ISO timestamps instead of formatted dates |
| BUG-004 | High | To Date automatically overridden to 30/12/2099 on submit regardless of user input |

BUG-004 is particularly sneaky — you set "To Date: 2026-12-31" but the ERP silently changes it to 2099-12-30. Tests that verify the saved date must account for this override.

---

## War Stories

### "The To Date Override"
Tests that create a base rate with a specific To Date were failing because the saved value didn't match. Investigation revealed the ERP always overrides To Date to 2099-12-30, regardless of what the user enters. This is a "feature" — base rates are treated as perpetually valid until a new version is created. Tests must verify against 2099-12-30, not the input value.

### "No UI Validation Tests"
This module has API tests but no UI validation tests. The page object exists and works, but nobody has written the UI validation suite yet. This is a gap — the form clearly has validation issues (BUG-001, BUG-002) that should be captured as automated tests.

---

## Test Coverage

| Test Type | Status | Count |
|-----------|--------|-------|
| API: Payload | ✅ Complete | ~20 tests |
| API: Schema | ✅ Complete | ~8 tests |
| API: Performance | ✅ Complete | ~5 tests |
| UI: Validation | ❌ Missing | — |

---

## Files

```
pages/commodity_settings/modules/commodity_base_rate/
├── commodity_base_rate_page.py    (1,686 LOC)
├── data/
│   └── cbr_data.py
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    └── api/
        ├── conftest.py
        ├── test_cbr_payload.py
        ├── test_cbr_schema.py
        └── test_cbr_perf.py
```
