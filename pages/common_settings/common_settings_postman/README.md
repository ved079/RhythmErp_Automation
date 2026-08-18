# Common Settings — Postman Collection

**File:** `common_settings_collection.json`

---

## Modules Covered

| Module | Requests | FK Resolution | Notes |
|--------|----------|---------------|-------|
| UOM | List, Get Detail, Create | None | Flat, no FKs |
| UOM Conversion | List, Get Detail, Create | Pre-request: List UOM → picks ids[0], ids[1] | source/target are UOM record IDs |
| Bank | List, Get Detail, Create | Hardcoded | account_type: 1849/1850, account_ref_id from GL chart |
| Designation | List, Get Detail, Create | None | Flat, no FKs |
| Error Code Mst | List, Get Detail, Create | Hardcoded | error_code_type: 643/216/215/140 |
| HSN SAC | List, Get Detail, Create | Hardcoded | hsn_sac_type: 212/162/161/159 |
| Season | List, Get Detail, Create | None | Flat, no FKs |
| Tax Authority | List, Get Detail, Create | Hardcoded | tax_type_ref_id: 93, country_ref_id: 8 |
| Tax Rate | List, Get Detail, Create | Pre-request: Tax Authority + HSN SAC | tax_type_ref_id: 93 hardcoded; has stepper children |
| Vehicle Master | List, Get Detail, Create | Pre-request: Accounting Template + Ledger Group | vehicle_type/fuel_type pick by index |

---

## FK Resolution Details

### Hardcoded IDs (no live resolution needed)

| Field | ID | Meaning |
|-------|----|---------|
| `tax_type_ref_id` | `93` | GST |
| `country_ref_id` | `8` | India |
| `account_type` | `1849` / `1850` | Current / Saving |
| `error_code_type` | `643` Farmer, `216` Debit Note, `215` Credit Note, `140` Workflow | — |
| `hsn_sac_type` | `212` Services, `162` Transportation, `161` Commission, `159` Commodity | — |

### Live-resolved via Pre-request Script

| Module | Resolves from screen | Patches field |
|--------|---------------------|---------------|
| UOM Conversion | `UOM` | `source_uom_code` (ids[0]), `target_uom_code` (ids[1]) |
| Tax Rate | `Tax%20Authority` | `tax_authority_ref_id` (ids[0]) |
| Tax Rate | `HSN%20SAC` | `children[0].details[0].hsn_sac_number` (ids[0]) |
| Vehicle Master | `Accounting%20Template` | `vehicle_type_id` (ids[0]) |
| Vehicle Master | `Ledger%20Group` | `fuel_type_ref_id` (ids[0]) |

---

## Quirks Found

### ERP response key
List endpoint returns records under `screenmatlistingdata_set` — not `results` or `data`.
Pre-request scripts use: `data.screenmatlistingdata_set || data.results || data.data || []`

### Postman `{{var}}` timing issue
Setting env vars inside a `pm.sendRequest` callback doesn't work — Postman substitutes `{{vars}}` before the callback fires. Fix: parse `pm.request.body.raw`, mutate the object, write it back:
```javascript
const reqBody = JSON.parse(pm.request.body.raw);
// ... resolve IDs ...
reqBody.source_uom_code = ids[0];
pm.request.body.raw = JSON.stringify(reqBody, null, 2);
```

### Vehicle Master screen names
`vehicle_type_id` and `fuel_type_ref_id` don't have dedicated "Vehicle Type" / "Fuel Type" screens.
Actual screen URLs: `Accounting%20Template` and `Ledger%20Group`.
These screens return entries with ERP-specific names (not "Mini Truck" / "Diesel") so resolution picks by index, not by name.

### Tax Type / Country screens
No resolvable list screen exists for these in the ERP. IDs hardcoded in both Postman collection and batch scripts.

---

## Batch Script Fixes Applied

Same issues found in batch scripts were fixed:

- **`tax_authority_data.py`** — removed FkResolver requirement, hardcoded `TAX_TYPE_REF_ID=93` and `COUNTRY_REF_ID=8`
- **`tax_rate_data.py`** — removed "Tax Type" from `get_fk_screen_mapping()`, hardcoded `TAX_TYPE_REF_ID=93`
- **`vehicle_master_data.py`** — fixed screen names to "Accounting Template" / "Ledger Group"; changed from name-based dict lookup to index-based cycling through available IDs
- **`common/fk_resolver.py`** — added "Accounting Template" and "Ledger Group" to `SCREEN_NAME_FIELDS`

---

## What's Not Included
- No Update requests
- No Delete requests

---

## See Also
- `pages/POSTMAN_GUIDE.md` — universal guide for building/extending collections
