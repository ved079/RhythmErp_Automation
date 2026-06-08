# Module: Quality Parameter Master

> Defines quality benchmarks — Moisture %, Foreign Matter %, Damaged Grains %. The master list that Commodity Quality Parameter maps to specific items.

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
| **Page object** | ✅ (1,607 LOC) |
| **Data file** | ✅ (470 LOC) |
| **batch_create** | ✅ |

---

## The ERP Screen

Found under **Commodity Settings → Quality Parameter Master**. Simple popup form for defining quality parameter names and their units.

### Key Fields
- **Parameter Name** — text input, required
- **Status** — toggle switch (Active/Inactive)

### Navigation URL
`/#/commodity-settings/qualityparametermaster`

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
attribute_name: "QualityParameterMaster"
```

No FK pools — `DEFAULT_QUALITY_PARAMETER_MASTER_FK_IDS = {}`.

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| BUG-001 | High | Spaces-only name creates empty record — no trim/validation |
| BUG-002 | High | Duplicate names allowed — no uniqueness check |
| BUG-003 | Medium | No maxlength on input — 300+ character names accepted |
| BUG-004 | Low | No success SweetAlert after create/update — form closes silently |

This module has essentially zero client-side validation. Anything goes in the name field.

---

## War Stories

### "Zero Validation"
Quality Parameter Master is the poster child for missing validation. You can enter spaces-only names, 300+ character names, duplicate names, and special characters — the ERP accepts everything. This module is useful for demonstrating what happens when a screen has no frontend validation at all.

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
pages/commodity_settings/modules/quality_parameter_master/
├── quality_parameter_master_page.py       (1,607 LOC)
├── data/
│   └── quality_parameter_master_data.py   (470 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_quality_parameter_master_validation.py
    └── api/
        ├── conftest.py
        ├── test_quality_parameter_master_payload.py
        ├── test_quality_parameter_master_schema.py
        └── test_quality_parameter_master_perf.py
```
