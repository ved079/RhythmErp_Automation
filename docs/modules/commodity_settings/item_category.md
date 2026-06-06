# Module: Item Category

> Classifies items into categories — Grains, Pulses, Oilseeds, Spices. The first level of item classification used by Item Master.

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
| **Page object** | ✅ (1,075 LOC) |
| **Data file** | ✅ (492 LOC) |
| **batch_create** | ✅ |

---

## The ERP Screen

Found under **Commodity Settings → Item Category**. Simple popup form with just the category name.

### Key Fields
- **Category Name** — text input, required

### Navigation URL
`/#/commodity-settings/itemcategory`

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
attribute_name: "ItemCategory"
```

No FK pools — `DEFAULT_ITEM_CATEGORY_FK_IDS = {}`.

---

## Page Object Notes

- **NEVER use Keys.ESCAPE** — closes the entire popup form instead of just overlays
- Uses backdrop click + JS overlay removal pattern
- Same structure as Item Group — they're practically identical modules

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
pages/commodity_settings/modules/item_category/
├── item_category_page.py          (1,075 LOC)
├── data/
│   └── item_category_data.py     (492 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_item_category_validation.py
    └── api/
        ├── conftest.py
        ├── test_item_category_payload.py
        ├── test_item_category_schema.py
        └── test_item_category_perf.py
```
