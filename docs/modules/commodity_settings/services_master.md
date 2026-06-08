# Module: Services Master

> Defines services (not goods) — Transportation, Storage, Processing. Has its own HSN/SAC codes separate from commodity items.

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
| **Page object** | ✅ (1,382 LOC) |
| **Data file** | ✅ (486 LOC) |
| **batch_create** | ✅ |

---

## The ERP Screen

Found under **Commodity Settings → Services Master**. Simple popup form for defining services with their SAC codes and UOM conversion.

### Key Fields
- **Service Name** — text input, required
- **Base UOM Conversion** — text/number input
- **Status** — toggle switch

### Navigation URL
`/#/commodity-settings/servicesmaster`

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
attribute_name: "ServicesMaster"
```

---

## Data Layer

```python
DEFAULT_SERVICES_MASTER_FK_IDS = {...}  # Has some FK references
```

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| BUG-001 | High | No maxlength on Name — 300+ chars accepted, but server rejects at 255 |
| BUG-002 | High | No maxlength on Base Uom Conversion — 11+ chars accepted, server max is 10 |
| BUG-003 | High | Name accepts ALL characters — special chars, spaces-only, no restrictions |
| BUG-004 | High | Base Uom Conversion accepts ALL input — letters, special chars, negative numbers |

The common pattern here: **no client-side validation at all**. The server has limits (255 chars for name, 10 for UOM conversion) but the frontend doesn't enforce them. Users only discover the limits when the server rejects the submission.

---

## War Stories

### "Client vs Server Validation Mismatch"
Services Master exposes a common ERP pattern: the server has validation rules that the frontend doesn't implement. The name field accepts 300+ characters in the UI, but the server silently rejects anything over 255. There's no error message — the form just fails to submit. Tests must stay within server-side limits even though the UI allows more.

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
pages/commodity_settings/modules/services_master/
├── services_master_page.py        (1,382 LOC)
├── data/
│   └── services_master_data.py   (486 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_services_master_validation.py
    └── api/
        ├── conftest.py
        ├── test_services_master_payload.py
        ├── test_services_master_schema.py
        └── test_services_master_perf.py
```
