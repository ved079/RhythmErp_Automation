# 2. Discover Context — the async discovery script

This is the piece we fixed. It's the **test script** of `Setup → Discover Context` (a `GET /core/dynamic-screen-wrapper/Supplier/?page_number=1&page_size=5` request). After the rewrite it mirrors `ChainContextDiscoverer.discover()` in `pages/private_b2b/scripts/chain_context.py`, but runs as a single async Postman sandbox function using `pm.sendRequest`.

Why async: the old script did synchronous sendRequest chaining with deeply nested callbacks (callback hell) — one failure aborted everything. The new one is serial-but-decoupled: each stage is `await`ed separately, guarded by its own checks, and appends to a running `pur_sniff_status` narrative. One failing stage never blocks the rest.

---

## 2.1 Stage map

Runs in this order inside `async function discover()`:

| # | Stage | API calls | Writes env vars | Failure behavior |
|---|-------|-----------|-----------------|------------------|
| pre | GP delivery type (runs **first**, guarded) | `GET /core/dynamic-screen/Gate%20Pass/` (schema) | `pur_gp_delivery_type` (first dropdown id: 29=Spot, 28=Delivery); narrated `delivery_type 29 from GP schema` | schema unavailable → `GP schema delivery_type unavailable - default 29` (Create GP falls back to 29) |
| 0 | Entry (the actual request) | Supplier list | — | non-JSON → `pur_sniff_status` note with HTTP code |
| 1 | Tax map | `Tax Rate/` list + first header detail | (in-memory `taxMap`) | empty map → tax stages skipped |
| 2 | Item | `Item Master/` list + each detail | `pur_item_ref_id`, `pur_hsn_sac_no`, `pur_uom`, `pur_alternate_uom`, `pur_uom_conversion` | skipped entirely if `pur_item_ref_id` already set (e.g. seeded by stage 4) |
| 3 | Tax rate for item | (reuses `taxMap`) | `pur_tax_rate` | skipped if already set |
| 4 | Stored-PO defaults | `purchase_order/` list + first detail | `pur_parameter1/2/5/6`, `pur_po_item_type`, `pur_po_type`, `pur_base_currency`, `pur_txn_currency` **+ first line seeds items/tax** | detail 400/404 (expected on some tenants) → `body defaults used`, others fall back to stages 2/3/5 |
| 5 | Supplier (if no stored-PO supplier) | each `Supplier/{id}/` detail | `pur_supplier_id`, `pur_ship_from`, `pur_bill_from`, `pur_supplier_po_type`, `pur_supplier_txn_currency`, `pur_supplier_payment_terms`, `pur_supplier_delivery_terms` | `no Supplier with both ship-from and bill-from addresses` |

## 2.2 The guards that matter

- **`set(name, value)`** helper ignores empty/undefined values — a missing field simply doesn't overwrite the env.
- **`jsonOf(r)`** returns `null` unless the `pm.sendRequest` succeeded (no error, no 4xx/5xx) and the body parsed as JSON.
- **OK check:** after all stages, if all four PO deps `['pur_supplier_id', 'pur_item_ref_id', 'pur_ship_from', 'pur_bill_from']` exist, `pur_sniff_status` is rewritten from `running | ...` to `Discover OK | ...`.
- **Crash guard:** the whole body is wrapped in `try/catch` → `Discover crashed: <message>` on unexpected exceptions (never silently pass).

## 2.3 Supplier resolution priority

1. **Stored-PO supplier (preferred):** an existing PO whose detail has `supplier_ref_id` AND `supplier_details.supplier_ship_from/bill_from` is the ground truth — mirrors the real business records (address FKs, payment/delivery terms, po_type, currency). `pur_supplier_*` is set from it directly.
2. **Supplier scan (fallback):** walk the entry Supplier list, fetch each `Supplier/{id}/` detail, and pick the **first** one that has both a ship-from and a bill-from address in its `children` steppers:
   - stepper name containing `"address"` → `details[0].id` = ship-from, `details[1].id` = bill-from
   - stepper name containing `"additional"` → `payment_terms_ref_id`, `delivery_terms_ref_id`
   - also reads `po_type_ref_id` → `pur_supplier_po_type` and `default_currency_ref_id` → `pur_supplier_txn_currency`

> Why: the generic first-dropdown values for ship/bill can point at a *different* supplier's address and cause an HTTP 500 on PO create. They must come from the chosen supplier's own registered steppers (`_resolve_supplier_details` in `purchase_chain.py`).

## 2.4 Item selection logic

1. First checks if `pur_item_ref_id` is already set (either manually or seeded by the stored-PO line, stage 4) — if so, **stage 2 is skipped entirely**.
2. Lists `Item Master/?page_number=1&page_size=10`, then walks each row:
   - fetch `Item Master/{id}/` detail
   - require `hsn_sac_code` AND both `uom` and `base_uom` — else `missing HSN/UOM in Item Master - trying next`
   - if the tenant tax map is non-empty, require `taxMap[hsn]` to be a real rate — else `HSN ... has no tax rate - trying next`
3. First usable item wins:
   - `pur_item_ref_id` = item id
   - `pur_hsn_sac_no` = `hsn_sac_code`
   - `pur_uom` = `base_uom` (base/weight UOM)
   - `pur_alternate_uom` = `uom` (primary UOM)
   - `pur_uom_conversion` = `base_uom_conversion || 1`

## 2.5 Tax map + rate

- Built once from `Tax Rate/?page_number=1&page_size=3` → first header id → `Tax Rate/{id}/` → flatten `children[*].details[*]` into `{hsn_sac_number: tax_rate}`.
- `pur_tax_rate` is set from the map using the item's HSN, but only if not already set (seeded by the stored-PO line).
- This is the literal percentage the ERP applies to the PO line (`txn_currency_tax_amount_details = txn_currency_amount_detail × tax_rate / 100`).

## 2.6 Stored-PO header defaults

Best-effort (the PO screen schema 404s, so generic dropdown discovery is unusable):

- `purchase_order/?page_number=1&page_size=3` → first id → `purchase_order/{id}/`
- Header: `parameter1/2/5/6`, `po_item_type`, `po_type`, `base_currency`, `txn_currency`
- **First line item** seeds `pur_item_ref_id`, `pur_hsn_sac_no`, `pur_uom`, `pur_alternate_uom`, `pur_uom_conversion`, `pur_tax_rate` — the existing business record is ground truth for a valid PO line.
- If the detail GET fails (400/404 on some tenants) → `stored PO detail unavailable - body defaults used`; header/item/tax fall back to stages 2/3/5 — **Create still runs**.

## 2.7 Outputs

- `pur_ctx` = `JSON.stringify({v: 1, supplier: {...}, item: {...}, gp: {delivery_type}, po_defaults: {...}, sniff_status})` — a single snapshot for debugging.
- `pur_sniff_status` — a human narrative for every run; see `04-troubleshooting.md` for the full state machine.

## 2.8 Console

`console.log('Discover done: ' + ctx.sniff_status)` — open **View → Show Postman Console** (`Ctrl+Alt+C`) to see the same reasons without expanding env vars.