# Module: UOM (Unit of Measurement)

> **The Gold Standard.** Other modules explicitly reference "UOM patterns" and "UOM gold-standard speed patterns" in their docstrings. If you're building a new module, start here for the interaction patterns.

---

## At a Glance

| Aspect | Details |
|--------|---------|
| **Section** | Common Settings |
| **Complexity** | Simple-Medium |
| **Steppers** | 0 — flat form, 3 fields |
| **Repeating rows** | No |
| **API tests** | ✅ payload, schema, perf |
| **UI tests** | ✅ validation |
| **Page object** | ✅ (904 LOC) |
| **Data file** | ✅ (342 LOC) |
| **batch_create** | ✅ |

---

## The ERP Screen

UOM is found under **Common Settings → UOM**. It's a simple popup form with 3 fields:
- **UOM Code** — text input, `type="text"` (accepts numbers unlike `type="character"` in Season/Designation)
- **UOM Name** — text input, `type="character"` (letters and spaces only)
- **Status** — toggle switch (Active/Inactive)

Despite being simple, UOM has the most refined page object in the project. Every interaction is optimized for speed and reliability.

### Navigation URL
`/#/master-setup/uom`

---

## API Contract

```
POST /core/dynamic-screen-wrapper/
```

```json
{
    "attribute_name": "Uom",
    "uom_code": "QTL",
    "uom_name": "Quintal",
    "status": true,
    "details": [],
    "children": []
}
```

Note: `attribute_name` is `"Uom"` (capitalized, not `"UOM"`). Case matters.

---

## Data Layer

### FK Pools

**None.** UOM has zero FK dropdowns — it's one of only 3 modules (with Designation and Season) that have no foreign key dependencies.

### Test Data

The data file contains **46 realistic Indian measurement units** across categories:

| Category | Examples |
|----------|---------|
| Weight | KG, Quintal, MT, Gram, Tonne |
| Volume | Liter, ML, Barrel, Gallon |
| Length | Meter, CM, MM, Feet, Inch |
| Area | Hectare, Acre, Bigha, Guntha |
| Agricultural | Bags, Bundles, Crates, Dozen, Pieces |

### Payload Builder

```python
def build_uom_api_payload(fk_ids=None):
    code, name = random.choice(UOM_ENTRIES)
    return {
        "attribute_name": "Uom",
        "uom_code": code,
        "uom_name": f"Test {name}",
        "status": True,
        "details": [],
        "children": [],
    }
```

---

## Page Object

### Why UOM Is The Gold Standard

5 other modules explicitly copy UOM's patterns:
- HSN SAC: "UOM gold-standard speed patterns applied"
- Error Code Mst: "Based on Vehicle Master proven patterns" (which itself is based on UOM)
- Season: Uses UOM's search and verify patterns
- Item Attribute: Uses UOM's dropdown interaction sequence
- Services Master: Uses UOM's overlay cleanup pattern

### Key Optimizations

**1. Fast Polling Instead of Sleep**
```python
def _wait_for_page_ready(self):
    # Uses 0.1s polling with 3s timeout instead of time.sleep(3)
    WebDriverWait(self.driver, 3, poll_frequency=0.1).until(...)
```

**2. JS-Only Search**
```python
# Search button is never Selenium-clickable — always use JS
def search_record(self, value):
    search_btn = self.driver.find_element(...)
    self.driver.execute_script("arguments[0].click();", search_btn)
```

**3. Fast Table Verification**
```python
def verify_uom_exists(self, code):
    # Pure JavaScript table scan — no Selenium waits
    found = self.driver.execute_script("""
        var rows = document.querySelectorAll('table tbody tr');
        for (var r of rows) {
            if (r.cells[1].textContent.includes(arguments[0])) return true;
        }
        return false;
    """, code)
```

### The mat-error Walker

UOM has the most sophisticated error text extraction in the project. It walks 20 levels up the DOM tree to find Angular's error state:

```python
def get_mat_error_text(self, field_name):
    """Walk up the DOM tree to find mat-error for a field."""
    script = """
    var input = document.querySelector('input[name="%s"]');
    var el = input;
    for (var i = 0; i < 20; i++) {
        el = el.parentElement;
        if (!el) break;
        var err = el.querySelector('mat-error');
        if (err && err.textContent.trim()) return err.textContent.trim();
    }
    return null;
    """ % field_name
    return self.driver.execute_script(script)
```

This pattern was needed because Angular Material places `mat-error` elements at unpredictable levels in the DOM hierarchy relative to the input.

---

## Known Bugs

| Bug ID | Severity | Description |
|--------|----------|-------------|
| Pattern A/B | Medium | Two different SweetAlert validation patterns exist — must handle both |
| Pattern C | Deprecated | Auto-dismiss error toast — no longer exists on live system |
| Duplicate | Low | No duplicate name validation — duplicate UOM names accepted silently |

### SweetAlert Patterns

UOM has both Pattern A and Pattern B:
- **Pattern A**: "Please correct highlighted fields" → click OK (`.swal2-confirm`)
- **Pattern B**: "Fields validation failed" / "Download Errors" → click Cancel (`.swal2-cancel`)

---

## War Stories

### "The Search Button Is Never Clickable"
Every attempt to Selenium-click the search button failed — it's always behind a toolbar element or CDK overlay. The solution: always use `execute_script("arguments[0].click()")`. This became the default approach for every module.

### "The Deprecated Pattern C"
Early in the project, UOM had a third SweetAlert pattern — an auto-dismissing error toast. This was removed from the ERP in a later update, but the handler code remained for months. Lesson: clean up dead code when the ERP changes, or it confuses the next developer.

### "UOM Code Accepts Numbers"
Unlike Season and Designation where `type="character"` rejects digits, UOM Code uses `type="text"` which accepts anything. This inconsistency between modules is a recurring theme — never assume the same field type across modules.

---

## Test Coverage

| Test Type | Status | Count |
|-----------|--------|-------|
| API: Payload | ✅ Complete | ~20 tests |
| API: Schema | ✅ Complete | ~8 tests |
| API: Performance | ✅ Complete | ~5 tests |
| UI: Validation | ✅ Complete | ~12 tests |

---

## Files

```
pages/common_settings/modules/uom/
├── uom_page.py                     (904 LOC)
├── data/
│   └── uom_data.py                 (342 LOC)
├── scripts/
│   └── batch_create.py
└── test/
    ├── conftest.py
    ├── test_uom_validation.py
    └── api/
        ├── conftest.py
        ├── test_uom_payload.py
        ├── test_uom_schema.py
        └── test_uom_perf.py
```

---

## Why UOM Matters for You

When building a new module:
1. Copy UOM's `_wait_for_page_ready()` pattern (fast polling)
2. Copy UOM's `_force_close_panels()` pattern (safe overlay removal)
3. Copy UOM's `verify_*_exists()` pattern (JS table scan)
4. Copy UOM's `get_mat_error_text()` pattern (DOM walking)

UOM is small enough to read in 30 minutes and complete enough to show you every pattern you need. Start here, then adapt for your module's complexity.
