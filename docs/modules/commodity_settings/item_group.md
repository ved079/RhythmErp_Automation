# Module: Item Group

> Groups items for reporting — Food Grains, Cash Crops, Plantation. Second level of item classification after Item Category.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Commodity Settings |
| **Complexity** | Simple |
| **Steppers** | 0 — popup form |
| **Repeating rows** | No |
| **API tests** | ✅ payload, schema, perf |
| **UI tests** | ✅ validation |
| **Page object** | ✅ (1,470 LOC) |
| **Data file** | ✅ (462 LOC) |
| **batch_create** | ✅ |

---

## The ERP Screen

Found under **Commodity Settings → Item Group**. Simple popup form for defining item groups.

### Key Fields
- **Group Name** — text input, required

### Navigation URL
`/#/commodity-settings/itemgroup`

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
attribute_name: "ItemGroup"
```

No FK pools — `DEFAULT_ITEM_GROUP_FK_IDS = {}`.

---

## Page Object Notes

- **NEVER use Keys.ESCAPE** — closes the entire popup form instead of just overlays
- Same pattern as Item Category — they're practically identical
- Uses backdrop click + JS overlay removal pattern

---

## Test Coverage

| Test Type | Status | Count |
|-----------|--------|-------|
| API: Payload | ✅ Complete | ~15 tests |
| API: Schema | ✅ Complete | ~8 tests |
| API: Performance | ✅ Complete | ~5 tests |
| UI: Validation | ✅ Complete | ~10 tests |

---

## Files

```
pages/commodity_settings/modules/item_group/
├── item_group_page.py             (1,470 LOC)
├── data/
│   └── item_group_data.py        (462 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_item_group_validation.py
    └── api/
        ├── conftest.py
        ├── test_item_group_payload.py
        ├── test_item_group_schema.py
        └── test_item_group_perf.py
```
