# 3. Endpoints That Actually Work + ERP Quirks

Hard-won knowledge about the Rhythm ERP API surface for the procure-to-pay screens. Do not "fix" these — they are the working reality we discovered.

---

## 3.1 PO does NOT use the dynamic-screen-wrapper for list/detail/create

The generic `/core/dynamic-screen-wrapper/{ScreenName}/` endpoints apply to the Commodity Settings screens (Supplier, Item Master, Tax Rate, ...), **but not** to the procure-to-pay documents:

| Module | List / Create | Detail |
|--------|---------------|--------|
| Purchase Order | `/procure_to_pay/purchase_order/` | `/procure_to_pay/purchase_order/{id}/` |
| Gate Pass | `/procure_to_pay/gate-pass/` | `/procure_to_pay/gate-pass/{id}/` |
| GRN | `/procure_to_pay/grn/` | `/procure_to_pay/grn/{id}/` |
| QC | `/procure_to_pay/quality-control/` | `/procure_to_pay/quality-control/{id}/` |
| Purchase Booking | `/procure_to_pay/purchase-booking/` | `/procure_to_pay/purchase-booking/{id}/` |
| Supplier detail | — | `/core/dynamic-screen-wrapper/Supplier/{id}/` |

## 3.2 List response shape

List responses return records under **`rows`**, with `screenmatlistingdata_set` as a fallback:

```js
var rows = body.rows || body.screenmatlistingdata_set || [];
```

Every list parser in this collection uses that fallback — keep it when extending.

## 3.3 No `id` / `attribute_name` on create payloads

These creates are the **raw REST shape** from the chain's payload builders (`build_po_payload` etc.) — there is no `attribute_name`, no wrapping stepper envelope, no empty-string `id`. POST the JSON body as-is.

## 3.4 PO screen schema 404s

`/core/dynamic-screen/Purchase Order/` returns 404 — **generic dropdown discovery is unusable** for `po_item_type`, `base_currency`, `txn_currency`, `parameter1/2/5/6`. That is why those come from either:

- the **stored-PO header defaults** (stage 4 of Discover), or
- the **supplier's own** `po_type_ref_id` / `default_currency_ref_id` (stage 5).

ChainContext handles the same problem with `_sniff_po_defaults()`.

## 3.5 Entry/listing quirks

- **Discover's entry request** is the Supplier list (`/core/dynamic-screen-wrapper/Supplier/?page_number=1&page_size=5`) — a 200 with the supplier list is the "this is a working request" smoke test.
- **`page_size=3`** on the stored-PO list is intentional: only the first record's detail is needed for defaults; 3 guards against an empty first page.
- **Item Master listing** does not expose per-item FK detail (only id/name/code/uom/status) — full details are fetched per row. The list `page_size=10` keeps the scan bounded.

## 3.6 The `pur_*` env-var contract

The Create requests never call the API — they read these vars and patch the body in a pre-request. The set Discover produces:

| Group | Vars |
|-------|------|
| Supplier | `pur_supplier_id`, `pur_supplier_po_type`, `pur_supplier_txn_currency`, `pur_ship_from`, `pur_bill_from`, `pur_supplier_payment_terms`, `pur_supplier_delivery_terms` |
| Item | `pur_item_ref_id`, `pur_hsn_sac_no`, `pur_uom`, `pur_alternate_uom`, `pur_uom_conversion`, `pur_tax_rate` |
| PO defaults | `pur_po_item_type`, `pur_po_type`, `pur_base_currency`, `pur_txn_currency`, `pur_parameter1`, `pur_parameter2`, `pur_parameter5`, `pur_parameter6` |
| Runtime | `pur_ctx`, `pur_sniff_status`, `pur_qty`, `pur_rate`, `pur_no_of_bags`, `pur_po_id` |