# Module: Item Attribute

> Defines attributes that can be applied to items — Color, Size, Moisture Content, etc. Items can have up to 5 attributes linked via Item Master.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Commodity Settings |
| **Complexity** | Simple-Medium |
| **Steppers** | 0 — popup form |
| **Repeating rows** | No |
| **API tests** | ✅ payload, schema, perf |
| **UI tests** | ✅ validation |
| **Page object** | ✅ (1,197 LOC) |
| **Data file** | ✅ (654 LOC) |
| **batch_create** | ✅ |

---

## The ERP Screen

Found under **Commodity Settings → Item Attribute**. Simple popup form for defining item attributes with their associated UOM.

### Key Fields
- **Attribute Name** — text input, required
- **UOM** — mat-select dropdown (links to UOM Master)

### Navigation URL
`/#/commodity-settings/itemattribute`

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
attribute_name: "ItemAttribute"
```

---

## Data Layer

### FK Pools

```python
UOM_IDS = {"KG": 1, "Quintal": 2, "MT": 3, ...}
DEFAULT_ITEM_ATTRIBUTE_FK_IDS = {...}
```

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| BUG-001 | High | Duplicate Names ALLOWED — no uniqueness constraint |
| BUG-002 | High | Browser-clicked mat-select values don't register in Angular form model |
| BUG-003 | Medium | History popup shows "No data available" even for entries with history |
| BUG-004 | High | No maxlength attribute / no client-side length validation |

BUG-002 is the same Angular Material issue seen across the entire project. See the Angular Material Survival Guide for the fix.

---

## Test Coverage

| Test Type | Status | Count |
|-----------|--------|-------|
| API: Payload | ✅ Complete | ~15 tests |
| API: Schema | ✅ Complete | ~8 tests |
| API: Performance | ✅ Complete | ~5 tests |
| UI: Validation | ✅ Complete | ~12 tests |

---

## Files

```
pages/commodity_settings/modules/item_attribute/
├── item_attribute_page.py         (1,197 LOC)
├── data/
│   └── item_attribute_data.py    (654 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_item_attribute_validation.py
    └── api/
        ├── conftest.py
        ├── test_item_attribute_payload.py
        ├── test_item_attribute_schema.py
        └── test_item_attribute_perf.py
```
