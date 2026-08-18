# Registration — Postman Collection

**File:** `registration_collection.json`

---

## Modules Covered

| Module | Requests | FK Fields | Notes |
|--------|----------|-----------|-------|
| Supplier | List, Get Detail, Create | None | Letters/spaces only in company name. No special chars. |
| Customer | List, Get Detail, Create | None | Flat form |
| Employee | List, Get Detail, Create | None | Flat form |
| Agent | List, Get Detail, Create | None | Flat form |
| Farmer | List, Get Detail, Create | `farmer_category` (hardcoded) | Multi-type: FPC Member, Borrower, etc. |

---

## Key Rules Discovered

### Supplier
- `company_name`: letters and spaces only — ERP enforces `^[A-Za-z ]+`. No dots, ampersands, underscores, or digits.
- Common mistakes: `"Trading Co."` (dot rejected), `"& Sons"` (ampersand rejected)
- Suffixes like `"Trading"`, `"Sons"`, `"Bros"` are safe

### Farmer
- `farmer_category` maps to type: `FPC Member` uses category `1593`, `Borrower` uses `1594`
- The batch UI supports multi-select farmer types — each type generates its own set of payloads
- Stepper children are filtered per type (not all steppers apply to all types)
- `FARMER_TYPE_CONFIG` in `farmer_data.py` is the source of truth for category IDs and allowed steppers

---

## Payload Source

All payloads built from `generate_*_api_payload()` functions in each module's `data/` file.
No hardcoded values — payloads generated fresh from the data pool each time.

---

## What's Not Included
- No Update requests (not needed)
- No Delete requests (not available on most modules)

---

## See Also
- `pages/POSTMAN_GUIDE.md` — universal guide for building/extending collections
