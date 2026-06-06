# Module: Commodity Quality Parameter

> Links quality parameters to specific commodities. Different from Quality Parameter Master — this is the mapping layer between items and their quality benchmarks.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Commodity Settings |
| **Complexity** | Medium-High |
| **Steppers** | 0 — popup form |
| **Repeating rows** | No |
| **API tests** | ✅ payload, schema, perf |
| **UI tests** | ✅ validation |
| **Page object** | ✅ (2,872 LOC) |
| **Data file** | ✅ (944 LOC) |
| **batch_create** | ✅ |

---

## The ERP Screen

Found under **Commodity Settings → Commodity Quality Parameter**. This screen maps quality parameters (like Moisture %, Foreign Matter %) to specific commodities (like Soybean, Wheat). A single commodity can have multiple quality parameters with different threshold values.

### Key Fields
- **Item Name** — mat-select dropdown (14+ items from CQP_USED_ITEM_IDS)
- **Quality Parameter** — mat-select (linked to Quality Parameter Master entries)
- **Parameter values** — min/max/target thresholds

### Navigation URL
`/#/commodity-settings/commodityqualityparameter`

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
attribute_name: "CommodityQualityParameter"
```

The payload includes FK references to both the Item and the Quality Parameter Master entries.

---

## Data Layer

### FK Pools

```python
CQP_USED_ITEM_IDS = {85, 86, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, ...}
DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS = {...}
```

Only specific items are usable — not all items in the Item Master are available for quality parameter mapping.

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| BUG-001 | High | Version & History buttons both use 'tbl-fav-edit' CSS class — can't programmatically distinguish them |
| BUG-002 | High | Duplicate Item Name entries in dropdown (no dedup) — same item appears multiple times |
| BUG-003 | Medium | Dates displayed as raw ISO strings in table (e.g., "2026-05-30T14:23:45.000Z") |
| BUG-004 | Medium | History popup always shows "No data available" even for entries that were versioned |

---

## War Stories

### "Version and History Use the Same CSS Class"
The Version button (which creates a new version of the parameter) and the History button (which shows previous versions) both render with the CSS class `tbl-fav-edit`. This means the page object cannot distinguish between them by CSS alone. The workaround is to use the button's position in the row or its tooltip text.

### "Duplicate Items in the Dropdown"
The Item Name dropdown shows duplicates — the same item appears 2-3 times. This is a backend bug where the API returns duplicate entries. Tests must either select the first match or handle the ambiguity.

---

## Test Coverage

| Test Type | Status | Count |
|-----------|--------|-------|
| API: Payload | ✅ Complete | ~20 tests |
| API: Schema | ✅ Complete | ~10 tests |
| API: Performance | ✅ Complete | ~5 tests |
| UI: Validation | ✅ Complete | ~15 tests |

---

## Files

```
pages/commodity_settings/modules/commodity_quality_parameter/
├── commodity_quality_parameter_page.py  (2,872 LOC)
├── data/
│   └── commodity_quality_parameter_data.py  (944 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_commodity_quality_parameter_validation.py
    └── api/
        ├── conftest.py
        ├── test_cqp_payload.py
        ├── test_cqp_schema.py
        └── test_cqp_perf.py
```
