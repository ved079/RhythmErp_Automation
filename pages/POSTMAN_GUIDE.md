# Rhythm ERP — Postman Collection Guide

Universal reference for building or extending Postman collections for any module.

---

## Setup (Environment Variables)

| Variable | Value |
|----------|-------|
| `base_url` | `https://rhythmerp.algorhythms.in` (or your tenant URL) |
| `token` | Bearer token from DevTools → Authorization header |
| `tenant_id` | Your tenant ID (e.g. `777`) |

---

## The One Rule: Read the batch script first

Before building any Postman request, always read:
1. **`pages/<module>/scripts/batch_create.py`** (if it exists) — source of truth for FK resolution
2. **`pages/<module>/data/<module>_data.py`** — actual payload structure

The batch script shows exactly what is hardcoded vs live-resolved. Never guess from the data file alone.

---

## API Endpoint

All Create requests go to one endpoint regardless of module:

```
POST {{base_url}}/core/dynamic-screen-wrapper/
```

List and Detail use:
```
GET {{base_url}}/core/dynamic-screen-wrapper/{ScreenName}/?page_number=1&page_size=25&search_string=&is_excel_download=false
GET {{base_url}}/core/dynamic-screen-wrapper/{ScreenName}/{{record_id}}/
```

Screen name in the URL is the `attribute_name` value from the payload, URL-encoded (e.g. `UOM%20Conversion`).

---

## ERP List Response Structure

The list endpoint always returns:

```json
{
  "screenmatlistingdata_set": [
    {"id": 84, "field1": "value", ...},
    {"id": 83, "field1": "value", ...}
  ],
  "page_total_records": 84,
  "page_has_next": true
}
```

**Key:** records are under `screenmatlistingdata_set`, NOT `results` or `data`.

---

## Payload Rules

### Flat module (no steppers)
```json
{
  "id": "",
  "attribute_name": "Screen Name",
  "field1": "value",
  "field2": 123
}
```

### Module with stepper children
```json
{
  "id": "",
  "attribute_name": "Screen Name",
  "field1": "value",
  "children": [
    {
      "stepper_name": "Stepper Tab Name",
      "is_stepper": true,
      "details": [
        {"child_field1": 1, "child_field2": "value"}
      ],
      "children": []
    }
  ]
}
```

Rules:
- `id` is always `""` (empty string) on Create
- `attribute_name` must match the ERP screen name exactly
- No Update (`PUT/PATCH`) requests — not needed
- No Delete endpoint exists on most modules

---

## FK Fields — Three Patterns

### Pattern 1: Hardcoded IDs
Some FK fields have no resolvable list screen. Use fixed values directly in the body.

Known hardcoded IDs:
| Field | Value | Module |
|-------|-------|--------|
| `tax_type_ref_id` | `93` (GST) | Tax Authority, Tax Rate |
| `country_ref_id` | `8` (India) | Tax Authority |
| `account_type` | `1849` Current, `1850` Saving | Bank |
| `hsn_sac_type` | `212` Services, `162` Transportation, `161` Commission, `159` Commodity | HSN SAC |
| `error_code_type` | `643` Farmer, `216` Debit Note, `215` Credit Note, `140` Workflow | Error Code Mst |

### Pattern 2: Live-resolved, name-based lookup
FkResolver fetches the list screen and matches by display name. Works when the data pool names match ERP entries exactly (e.g. UOM codes, Tax Authority names, HSN SAC codes).

### Pattern 3: Live-resolved, pick by index
When display names in the data pool don't match ERP entries (e.g. Vehicle Master's "Mini Truck" vs actual Accounting Template entries), just pick `ids[0]`, `ids[1]` etc. from whatever the screen returns.

---

## Pre-request Script Pattern (for live FK resolution)

Use this pattern to resolve FK IDs at request time and patch them directly into the request body. This bypasses Postman's `{{var}}` substitution timing issue (substitution happens before `sendRequest` callbacks fire).

```javascript
const baseUrl = pm.environment.get('base_url');
const token = pm.environment.get('token');
const tenantId = pm.environment.get('tenant_id');
const reqBody = JSON.parse(pm.request.body.raw);

function resolveScreen(screen, cb) {
    pm.sendRequest({
        url: baseUrl + '/core/dynamic-screen-wrapper/' + screen + '/?page_number=1&page_size=100&search_string=&is_excel_download=false',
        method: 'GET',
        header: {
            'Authorization': 'Bearer ' + token,
            'X-Tenant-ID': tenantId,
            'Content-Type': 'application/json',
        }
    }, function(err, res) {
        if (err) { console.error(err); cb([]); return; }
        const data = res.json();
        const results = data.screenmatlistingdata_set || data.results || data.data || [];
        cb(results.map(r => r.id).filter(id => id != null));
    });
}

// Resolve N screens in parallel, write body when all done
let pending = 2;
function done() { if (--pending === 0) pm.request.body.raw = JSON.stringify(reqBody, null, 2); }

resolveScreen('UOM', function(ids) {
    if (ids[0] != null) reqBody.source_uom_code = ids[0];
    if (ids[1] != null) reqBody.target_uom_code = ids[1];
    done();
});
resolveScreen('Tax%20Authority', function(ids) {
    if (ids[0] != null) reqBody.tax_authority_ref_id = ids[0];
    done();
});
```

Set `pending` to the number of `resolveScreen` calls. Each callback calls `done()` — body is written only once all screens resolve.

---

## Known Screen Name Quirks

Some FK fields point to screens with unexpected names:

| FK field | Actual screen URL name |
|----------|----------------------|
| `vehicle_type_id` | `Accounting%20Template` |
| `fuel_type_ref_id` | `Ledger%20Group` |
| `tax_type_ref_id` | No screen — hardcode `93` |
| `country_ref_id` | No screen — hardcode `8` |

Always verify by navigating to the screen in the ERP and checking the URL hash: `#/dynamic-screens/{ScreenName}`.

---

## Step-by-step: Adding a new module

1. Read `pages/<module>/scripts/batch_create.py` — note which fields use `FkResolver.resolve("Screen Name")`
2. Read `pages/<module>/data/<module>_data.py` — note the payload structure from `build_<module>_api_payload()`
3. Check `get_fk_screen_mapping()` — lists all FK fields and their screen names
4. For each FK field decide: hardcoded / live pre-request / name-based lookup
5. Build 3 requests: List, Get Detail, Create
6. Add pre-request script to Create if any live FK resolution is needed
7. No Update request needed
