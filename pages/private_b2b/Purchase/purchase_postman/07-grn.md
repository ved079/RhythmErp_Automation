# 7. GRN (Goods Receipt Note) — verified step

Third document in the chain, consuming the GP via `gate_pass_ref_id_id` and the PO via `po_ref_id_id`.

**Verified live run (this session, tenant 795):** PO **3906** → GP **2511** → GRN **2137** — full chain from Discover, created and stored-back verified field-by-field.

---

## 7.1 Endpoints

| Request | Endpoint |
|---------|----------|
| List GRN / Create GRN | `POST/GET /procure_to_pay/grn/` |
| Get GRN Detail | `GET /procure_to_pay/grn/{id}/` |
| Schema (params dropdowns) | `GET /core/dynamic-screen/Goods%20Receipt%20Note/` |

> Same listing quirk as PO/GP: list rows show display names (`po_ref_id_id` = ref no, `supplier_ref_id` = name); **only the detail has numeric FKs**. List rows live under `screenmatlistingdata_set` (`rows` is null).

## 7.2 Why GRN needed no Discover stage

GRN is a pure Create step — it only **links** items that already exist and records received quantities. Every `pur_*` it reads is produced by **Discover Context** (supplier/item/qty/rate/params) plus the two prior Creates (`pur_po_id`, `pur_gp_id`). The GRN screen's only dropdowns are `parameter1/2/5/6`, `base_currency`, `txn_currency`, `supplier_ref_id` — the params come from the stored-PO header defaults and the rest are constants. No schema sniffing required.

## 7.3 Create GRN pre-request (mirrors `_grn_items_from` + `_build_grn_payload`)

**Hard deps guard (throws):** `pur_po_id`, `pur_gp_id`, `pur_supplier_id`, `pur_item_ref_id` — same error shape as Create PO/GP: `Missing GRN deps: ...` with the current `pur_sniff_status` and a hint to re-run Discover when it didn't complete.

Header fields:

| Body field | Source | Verified stored value |
|------------|--------|----------------------|
| `transaction_date` | today | |
| `supplier_ref_id` | `pur_supplier_id` | 1046 |
| `supplier_ref_type` | `'Supplier'` | |
| `gate_pass_ref_id_id` | `pur_gp_id` | 2511 (linked GP) |
| `po_ref_id_id` | `pur_po_id` | 3906 (linked PO) |
| `base_currency` | **`1` hardcoded** ⚠️ | 1 |
| `txn_currency` | **`1` hardcoded** ⚠️ | 1 |
| `conversion_rate` | `1.0` | 1 |
| `parameter1/2/5/6` | `pur_parameter*` | 2, 1, 1, 1 |
| `additional_details` | body default `{}` | stored as nulls with `id` |

`grn_item_details[0]`:

| Body field | Source | Verified stored value |
|------------|--------|----------------------|
| `item_ref_id` | `pur_item_ref_id` | 11 |
| `hsn_sac_no` | `pur_hsn_sac_no` | 29 |
| `uom` | `pur_uom` (base UOM) | 34 |
| `alternate_uom` | `pur_alternate_uom` (primary UOM) | 36 |
| `uom_conversion` | `pur_uom_conversion` (**real conversion**) | 20 |
| `alternate_received_qty` | `pur_qty` | 1816 |
| `alternate_accepted_qty` | `pur_qty` | 1816 |
| `alternate_rejected_qty` | `0.0` | 0 |
| `rate` | `pur_rate` | 2077.67 |
| `no_of_bags` | `pur_no_of_bags` | 1816 |
| `gate_pass_quantity` | `pur_qty` | 1816 |
| `po_quantity` | `pur_qty` | 1816 |
| `po_balance_quantity` | `pur_qty` | 1816 |

## 7.4 The two GRN nuances (don't "fix" these)

1. **`uom_conversion` is the REAL conversion — unlike GP.** GP hardcodes `1.0` (see `06-gp.md` §6.4), but GRN sends the item's actual `pur_uom_conversion` (20 on 795) — verified stored-back as `20`. Both match the Python chain (`_gp_items_from` hardcodes 1.0; `_grn_items_from` forwards the item's real conversion). Do not normalize them to the same value — they are intentionally different.
2. **Currency is hardcoded 1/1, independent of the PO's currency.** `_build_grn_payload` (chain) passes no currencies, so `build_grn_payload` uses its defaults (1, 1, conversion 1.0). Proven on this tenant: stored GRN 2125's PO (PO 3893) is `base_currency=8/txn_currency=8`, yet the GRN itself stored `1/1`. If you take GRN currency from `pur_base_currency`/`pur_txn_currency` (8 in this flow), you will produce a **non-chain** GRN — revert to `1`/`1`.

## 7.5 Test script (post-response)

```js
var id = data.id || data.entry_id;
if (!id) throw new Error('GRN create failed: ' + pm.response.text());
pm.environment.set('pur_grn_id', id);
```

Stores `pur_grn_id` for QC (`grn_ref_id_id`) and PB (`grn_ref_id`).

## 7.6 Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `Missing GRN deps: pur_po_id, pur_gp_id, ...` | Missing a previous hop — run the full **Discover → Create PO → Create GP** sequence first; read `pur_sniff_status` in the error. |
| GRN 4xx/5xx on create | Most common: body fields from a stale `pur_*` set (switch of tenant/POST without re-running Discover). Re-run Discover → PO → GP and check console. Rarely: `grn_item_details` empty/mismatched vs the GP's quantities — keep all quantities equal to `pur_qty` in the single-flow. |
| 401 on `/procure_to_pay/grn/` | Token no longer reaches the tenant (711 401s; use 795) or expired — re-paste token + `tenant_id`. |
| GRN created but shows `booking_status: Pending` | Expected — booking is downstream (Purchase Booking step), not part of GRN. |

## 7.7 Source-of-truth mapping

| Postman | Python |
|---------|--------|
| Create GRN body template | `build_grn_payload()` in `goods_receipt_note/data/goods_receipt_note_data.py` |
| Line mapping (real `uom_conversion`, quantity set) | `_grn_items_from()` in `purchase_chain.py` |
| Header build (currencies 1/1, params) | `PurchaseChain._build_grn_payload()` |
| Listing display-name quirk | `GRNAPIUtils.list_grns()` + raw response inspection |