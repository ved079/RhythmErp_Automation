# Purchase Chain — Universal PO Creation (Knowledge Base)

> This file documents the **Purchase Chain PO** feature end-to-end so that a future
> developer (or AI agent) can understand **what it does**, **why the ERP behaves the
> way it does**, and **how to recreate/extend it**. Read this before touching
> `purchase_chain.py`, `purchase_chain_endpoint.py`, `PurchaseChainSection.tsx` or the
> PO payload builder.

---

## 1. Goal

Create a **Purchase Order** through the Purchase Chain that works on **any tenant**:

- **Supplier-scoped** — ship_from / bill_from / payment terms / delivery terms /
  `po_type` / `txn_currency` all come from the chosen Supplier's detail record
  (NOT generic first-dropdown values, which can belong to another supplier and cause
  HTTP 500).
- **Item-scoped** — PO items are restricted to **one Item Category** (the ERP PO screen
  filters the Item dropdown by the selected category), each line uses the item's **real
  HSN / UOM / UOM-conversion** from Item Master.
- **Tax-aware** — `tax_rate` is resolved **per HSN** from the Tax Rate screen; items
  whose HSN has no rate can be filtered out (Tax Rate ON) or sent with `0.0` (OFF).
- `po_item_type` on the stored PO = the **selected Item Category id**.

The chain continues to Gate Pass → GRN → QC → Purchase Booking for the same supplier.

---

## 2. Verified ERP facts (ground truth, tenant 686 probes)

These are **behavioral facts learned by probing the live ERP** — do not "fix" them to
match what a UI mock suggests.

- The PO screen **schema endpoint 404s** for `"Purchase Order"` — only `"PO"` works for
  schema discovery. So header defaults are **sniffed from an existing PO** instead.
- `get_entry("Item Master", id)` exposes `item_category`, `hsn_sac_code`, `uom`,
  `base_uom`, `base_uom_conversion`. The Item Master **listing** does NOT — it only
  returns `id/name/code/uom/status`. Category / HSN must be read per item (threaded).
- **`po_item_type` is stored exactly as sent** — the ERP does NOT derive it from the
  item. Verified: forced `po_item_type=2` with a category-1 item → stored `2`.
  Therefore `po_item_type` must be set by us to the selected category id.
- The PO schema's own `po_item_type` dropdown (113 Farm / 114 Non-Farm) is **irrelevant**
  — the stored value holds the Item Category id (e.g. `1` = "Raw Materia" on 686).
- Stored PO header shape:
  - `supplier_payment_terms` / `supplier_delivery_terms` are **top-level**.
  - `supplier_details` carries **only** `supplier_ship_from` / `supplier_bill_from`.
  - No `packing_forwarding_ref_id`.
  - `tax_registration_status = "Registered"`.
- Supplier detail (`get_entry("Supplier", id)`):
  - `default_currency_ref_id` → `txn_currency`
  - `po_type_ref_id` → `po_type` (e.g. 24 Import, 25 Domestic)
  - "additional" stepper: `payment_terms_ref_id`, `delivery_terms_ref_id`
  - "address" stepper: `details[0].id` = ship_from, `details[1].id` = bill_from
  - The Supplier screen has **no** `item_category` field — there is no supplier→category
    derivation in the ERP.
- Real PO line shape (no `quantity`, no `is_gst_set_off`):
  `item_ref_id, hsn_sac_no, alternate_uom, uom, uom_conversion, alternate_quantity,
  rate, gst_type, tax_rate, txn_currency_amount_detail, txn_currency_tax_amount_details,
  total_amount, expected_delivery_date`
  - `alternate_uom` = item primary UOM (e.g. MT), `uom` = base UOM (e.g. KG)
  - `balance_qty` is computed by ERP = `alternate_qty × uom_conversion`
- Tax Rate screen (`get_entry("Tax Rate", id)`):
  - Header fields: `tax_type_ref_id` (=93 GST), `tax_authority_ref_id` (=1 GST),
    `from_date`, `to_date`.
  - Rate rows live in `children[].details[]`, each with `hsn_sac_number` + `tax_rate`.
  - One HSN can have **multiple** rates across headers (e.g. HSN 4 → 5.0, 10.0, 25.0).

---

## 3. Data flow

```
Next.js (PurchaseChainSection.tsx)
   │  fetchMasterData / fetchItemCategories  (→ /api/master-data, /api/item-categories)
   │  startPurchaseChain (SSE)               (→ /api/proxy?path=purchase-chain)
   ▼
/api/proxy/route.ts   (session auth + CSRF + X-Proxy-API-Key; body passed through raw)
   ▼
FastAPI /api/purchase-chain  (SSE stream)
   ▼
PurchaseChain (pages/private_b2b/scripts/purchase_chain.py) → ERP REST
```

---

## 4. Backend

### Request — `PurchaseChainRequest` (`api/models.py`)

| field | default | meaning |
|---|---|---|
| `count` | 1 | number of chains |
| `supplier_ref_id` | 1 | supplier |
| `num_items` | 2 | items per document |
| `item_ref_id` | 5 | fallback item id |
| `item_ref_ids` | None | per-row item ids (overrides `item_ref_id`) |
| `item_category_id` | None | restrict to category; None = auto-pick most-populated |
| `require_tax_rate` | True | True = only items whose HSN has a rate; False = all, `0.0` fallback |
| `delay` | 0.3 | seconds between calls |
| `erp_token` / `erp_tenant_id` | — / "681" | ERP credentials |
| `documents` | PO GP GRN QC | which docs to create |

### Endpoint — `api/purchase_chain_endpoint.py`
- Streams SSE `LogEvent`s; forwards `item_category_id` + `require_tax_rate` into
  `chain.run(**kwargs)`.
- Logs a `Config: category_id=…, tax_rate=ON|OFF, items=…` event per chain for
  troubleshooting category resolution.

### `PurchaseChain.run(...)` (`purchase_chain.py`)
1. Resolve context (ChainContextDiscoverer) unless passed in.
2. Resolve supplier-specific header values (`_resolve_supplier_details`).
3. Resolve Item Category:
   - `item_category_id` given → validate it exists (`_resolve_item_category`), else
     **auto-pick the most-populated** category (`cats[0]` sorted by count desc).
   - `cat_id` becomes the `po_item_type`.
4. Pick items:
   - `item_ref_ids` given → used directly; each item validated to belong to `cat_id`.
   - else → items of `cat_id` from `_item_category_map` (built by
     `_resolve_item_categories`, which fetches every item's detail to read the FK).
5. **Tax rate gating** (`_resolve_tax_rates` → `{HSN: [rates]}`):
   - `require_tax_rate=True`: item whose HSN has no rate is skipped (logged); loop
     cycles ids to fill `num_items`; raises if nothing qualifies.
   - Each kept item gets `det["tax_rate"] = random.choice(rates)` — **random pick**
     (user choice), never a fixed one.
   - `require_tax_rate=False`: all items kept; rate-less → `0.0`.
6. Build + create PO (`_build_po_payload` → `build_po_payload`), then GP/GRN/QC/PB.
7. After PO create, re-fetches the PO and confirms per-line rate; adopts backend rate.

### `_build_po_payload` — key decisions
- `po_item_type = item_category_id` (the selected category id), with a sniffed/legacy
  fallback only when no category resolved.
- `supplier_details` = only ship/bill; payment/delivery/tax registration top-level.
- `tax_rate` per line comes from the item dict (set in `run()`), computed by
  `_po_items_from`:
  `amount = rate × alternate_qty`, `tax = amount × tax_rate/100`, `total = amount + tax`.

### Master-data enrichment — `api/server.py`
- `_resolve_tax_rates(client)` → `{hsn_str: [float]}` (threaded `get_entry` per header).
- `_enrich_item_categories(client, items, with_tax_rates=False)`:
  - attaches `item_category` to every Item Master row (from detail);
  - when `with_tax_rates=True` also attaches `hsn_sac_code` + `tax_rates`.
- `/api/master-data` → Item Master rows get `item_category`, `hsn_sac_code`, `tax_rates`.
- `/api/item-categories` → `[{id, name, item_count}]` sorted desc (counts via enriched rows).

---

## 5. Frontend

### `web-ui/src/lib/api.ts`
- `MasterDataItem` adds `item_category?`, `hsn_sac_code?`, `tax_rates?: number[]`.
- `fetchItemCategories(token, tenant)` → `POST ?path=item-categories` →
  `{categories: [{id,name,item_count}]}`.
- `startPurchaseChain(..., documents?, itemCategoryId?, requireTaxRate?)` → sends
  `item_category_id` and `require_tax_rate` to `/api/proxy?path=purchase-chain`.

### `web-ui/src/components/dialogs/PurchaseChainSection.tsx`
- Category dropdown (label `name (N items)`, defaults to most-populated).
- **Tax Rate ON/OFF toggle** (default ON):
  - ON → `poolFor()` keeps only items with `tax_rates.length > 0` (no fallback to
    rate-less items; shows amber warning when empty).
  - OFF → all items listed.
- Item rows auto-reset to the pool when category or the toggle changes.
- Items/Doc "All N" button uses the filtered pool.

---

## 6. Tests & validation

```bash
# Payload builder tests (purchase_order_data)
python -m pytest pages/private_b2b/modules/purchase_order/test/api/test_payload.py -v

# Syntax sanity
python -m py_compile pages/private_b2b/scripts/purchase_chain.py api/server.py \
  api/models.py api/purchase_chain_endpoint.py

# Web type check (from web-ui/)
npx tsc --noEmit
```

Live probe recipe (needs a valid ERP token):
```python
from common.erp_api_client import RhythmERPAPIClient
c = RhythmERPAPIClient()
c.login_from_browser(token="<JWT>", tenant_id="<tenant>")
# tax rates map:
from pages.private_b2b.scripts.purchase_chain import PurchaseChain
print(PurchaseChain(client=c)._resolve_tax_rates())
```

---

## 7. How to recreate the feature (checklist)

1. **Per-supplier resolution** — `_resolve_supplier_details` reads Supplier detail;
   ship/bill from address stepper, terms from additional stepper, `po_type`/`txn_currency`
   from `po_type_ref_id`/`default_currency_ref_id`. Raise a clear error if a supplier has
   no ship/bill address.
2. **Item category scoping** — `_resolve_item_categories` lists Item Category + Item
   Master, then fetches each item's detail (ThreadPoolExecutor, 8 workers) to read the
   `item_category` FK (listing lacks it). Builds `_item_category_map`; counts per category;
   sorted desc. `_resolve_item_category` validates or auto-picks `cats[0]`.
3. **`po_item_type = category id`** — pass `item_category_id` into `_build_po_payload`;
   set `po_item_type` from it (NOT Farm/Non-Farm 113/114, NOT sniffed).
4. **Tax rate resolution** — `_resolve_tax_rates` flattens all Tax Rate headers
   (`children[].details[]` → `hsn_sac_number → tax_rate`), threaded, cached.
5. **Tax Rate toggle** — `require_tax_rate` on the request; ON skips no-rate items
   (random rate per item), OFF keeps all with `0.0`. Frontend filters the item pool and
   defaults to ON.
6. **SSE plumbing** — endpoint forwards `item_category_id` + `require_tax_rate` and logs
   the resolved `Config:` so category issues are visible in the console.

---

## 8. Known gotchas / troubleshooting

- If the stored `po_item_type` does not match the category you picked, check the console
  `Config: category_id=…` line. The ERP stores **what we send**, so a wrong value means
  the id that arrived at the backend was wrong (or `(auto-pick)` was used).
- Item Master listing lacks `item_category`/`hsn` — any feature reading them must call
  `get_entry("Item Master", id)` per item (threaded). This is why counts can be slow on
  large tenants.
- A tenant where **only one category has items** (e.g. 686: all 20 items are category 1)
  means picking any other category yields an empty pool — the UI falls back to "all
  items", so validate item→category on the backend too.
- Tax Rate screen field names are `hsn_sac_number` and `tax_rate` (nested under
  `children[].details[]`), NOT `hsn_sac_code`.
- Schema discovery: `get_screen_schema("PO")` works; `"Purchase Order"` 404s.
- `_po_items_from` computes `total_amount` client-side; the ERP re-computes `balance_qty`.
- Legacy `pages/private_b2b/modules/purchase_order/scripts/batch_create.py` still uses
  hardcoded IDs and is **not** universal — do not treat it as reference for this flow.

---

## 9. Key files

| File | Role |
|---|---|
| `pages/private_b2b/scripts/purchase_chain.py` | Chain runner; category + supplier + tax-rate resolution; PO payload |
| `api/purchase_chain_endpoint.py` | SSE endpoint; forwards category / tax-rate flags |
| `api/models.py` | `PurchaseChainRequest` |
| `api/server.py` | `/api/master-data`, `/api/item-categories` + enrichment helpers |
| `pages/private_b2b/modules/purchase_order/data/purchase_order_data.py` | `build_po_payload` (top-level terms, `item_category`) |
| `web-ui/src/lib/api.ts` | `startPurchaseChain`, `fetchMasterData`, `fetchItemCategories`, types |
| `web-ui/src/components/dialogs/PurchaseChainSection.tsx` | PO chain UI (category dropdown, Tax Rate toggle) |
| `web-ui/src/app/api/proxy/route.ts` | Auth+CSRF proxy (body passed through raw — no whitelist) |
