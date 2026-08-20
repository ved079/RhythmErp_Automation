# 4. Create PO — pre-request math and required deps

`PO → Create PO` is a `POST /procure_to_pay/purchase_order/`. It reads `pur_*` env vars (built by Discover Context), generates the transaction figures in a **pre-request script**, and patches the raw body before sending. The test script saves `pur_po_id`.

---

## 4.1 Required dependencies (hard guard)

The pre-request runs first and **throws** if any of these are missing:

```js
[ 'pur_supplier_id', 'pur_item_ref_id', 'pur_ship_from', 'pur_bill_from' ]
```

Error thrown: `Missing PO deps: <missing list>. Run Setup > Discover Context first (sniff status: ...)`.

This is the primary failure point if you skipped or failed Discover — the error message embeds `pur_sniff_status`, which tells you where discovery stopped (`04-troubleshooting.md`).

## 4.2 Generated transaction figures

Fresh random values per run (mirrors `_rand_qty` / `_rand_rate` in `purchase_chain.py`):

| Field | Range | Formula |
|-------|-------|---------|
| `pur_qty` | int 500–2000 | `Math.floor(500 + Math.random() * 1500)` |
| `pur_rate` | 2-dp 500–6000 | `round(500 + Math.random() * 5500, 2)` |
| `pur_no_of_bags` | int | `Math.round(pur_qty)` |
| `pur_tax_rate` | from Discover | percentage from the item's HSN tax map |

## 4.3 The amount math (ERP does NOT auto-patch)

All three amounts are computed client-side and sent pre-filled:

```
amount = round(rate × qty, 6)                  // txn_currency_amount_detail
tax    = round(amount × tax_rate / 100, 6)     // txn_currency_tax_amount_details
total  = round(amount + tax, 6)                // total_amount
```

Rounding is `Math.round(v * 1e6) / 1e6` (6 dp) to match Python's `round(x, 6)` — keep the exact granularity or downstream verification against the stored record drifts.

## 4.4 Header fields patched from env (with fallbacks)

| Body field | Source | Fallback |
|------------|--------|----------|
| `transaction_date` | today | — |
| `supplier_ref_id` | `pur_supplier_id` | — |
| `supplier_ref_type` | `'Supplier'` | — |
| `po_item_type` / `item_category` | `pur_po_item_type` | `113` |
| `po_type` | `pur_supplier_po_type` → `pur_po_type` | `25` |
| `base_currency` | `pur_base_currency` | `1` |
| `txn_currency` | `pur_supplier_txn_currency` → `pur_txn_currency` | `1` |
| `parameter1/2/5/6` | `pur_parameter*` | `1` |
| `supplier_details.supplier_ship_from` | `pur_ship_from` | `null` |
| `supplier_details.supplier_bill_from` | `pur_bill_from` | `null` |
| `supplier_payment_terms` | `pur_supplier_payment_terms` | `null` |
| `supplier_delivery_terms` | `pur_supplier_delivery_terms` | `null` |

Line item (`purchasing_order_items_details[0]`):

| Body field | Source |
|------------|--------|
| `item_ref_id` | `pur_item_ref_id` |
| `hsn_sac_no` | `pur_hsn_sac_no` |
| `uom` | `pur_uom` (base UOM) |
| `alternate_uom` | `pur_alternate_uom` (primary UOM) |
| `uom_conversion` | `pur_uom_conversion` (default 1) |
| `alternate_quantity` | `String(pur_qty)` |
| `rate` | computed rate |
| `gst_type` | `'IGST'` (fixed for PO) |
| `tax_rate` | `pur_tax_rate` (0 when no tax) |
| `txn_currency_amount_detail` / `txn_currency_tax_amount_details` / `total_amount` | computed above |
| `expected_delivery_date` | today |

> `pur_po_type` vs `pur_supplier_po_type`: supplier-specific wins. Same for `pur_supplier_txn_currency` vs `pur_txn_currency`. This mirrors the `get_context_for_supplier()` logic in the chain.

## 4.5 Test script (post-response)

```js
var id = data.id || data.entry_id;   // both shapes seen in the wild
if (!id) throw new Error('PO create failed: ' + pm.response.text());
pm.environment.set('pur_po_id', id);
```

- Accepts `id` **or** `entry_id` from the response.
- Throws loudly with the raw body on failure (never silently passes).

## 4.6 Body template (the base JSON)

The raw body in the collection is a template of the stored-record shape from `purchase_order_data.py` (`build_po_payload` / `_po_items_from`), with zeroed FKs. The pre-request overwrites everything relevant, so the template values are placeholders — keep them in sync if the real payload builder changes field names.

Known real field set (verified on tenant 686, `/purchase_order/3242/`):

```
item_ref_id, hsn_sac_no, alternate_uom, uom, uom_conversion,
alternate_quantity, rate, gst_type, tax_rate,
txn_currency_amount_detail, txn_currency_tax_amount_details,
total_amount, expected_delivery_date
```

(no `quantity`, no `is_gst_set_off` on the PO line).

## 4.7 Downstream var contract

Create PO stores: `pur_po_id`, `pur_qty`, `pur_rate`, `pur_no_of_bags`. GP/GRN/QC/PB read these, so a successful PO run is a prerequisite for the rest of the chain.