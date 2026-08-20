# Purchase Chain — Postman Collection

**File:** `purchase_collection.json`

Covers the procure-to-pay flow: **PO → Gate Pass (GP) → Goods Receipt Note (GRN) → Quality Check (QC) → Purchase Booking (PB)** — exactly as `pages/private_b2b/scripts/purchase_chain.py` builds it.

Start with **Setup → Discover Context**, which resolves the tenant FK values once (supplier, item, tax rate, stored-PO header defaults, GP `delivery_type`) into `pur_*` vars + a consolidated `pur_ctx` JSON. Then run the Creates; no stored PO is required.

---

## Modules Covered

| Module | Requests | Linked To | Notes |
|--------|----------|-----------|-------|
| Setup | Discover Context | — | One-shot tenant discovery: supplier (with addresses), PO-usable item (Item Master), HSN tax rate, best-effort stored-PO header defaults, GP `delivery_type` (schema dropdown) → `pur_*` + `pur_ctx`; no stored PO required |
| Purchase Order (PO) | List, Get Detail, Create | — | Reads `pur_*` built by Discover |
| Gate Pass (GP) | List, Get Detail, Create | PO (`po_ref_id_id`) | `delivery_type` resolved by Discover (GP schema dropdown) → `pur_gp_delivery_type` |
| Goods Receipt Note (GRN) | List, Get Detail, Create | PO + GP | Single-flow qty: `po_quantity = po_balance_quantity = gate_pass_quantity`; real `uom_conversion` (unlike GP's 1.0); currency 1/1 always — see `07-grn.md` |
| Quality Check (QC) | List, Get Detail, Create | PO + GP + GRN | Quality params from the item's CQP + bag type from Packages (both resolved by Discover); all amounts computed in pre-request |
| Purchase Booking (PB) | List, Get Detail, Create | PO + GRN + QC | Mirrors the QC lines exactly; GST split computed in pre-request |

---

## Key Rules Discovered

### Run order (mandatory)
First run **Setup → Discover Context** once (rebuilds `pur_*` for the tenant; e.g. when switching tenants). Then run the five **Create** requests in order: **PO → GP → GRN → QC → PB**.
Each Create's test script stores its record id in a `pur_*` env var that the next Create reads:

```
Discover     → pur_ctx + pur_supplier_id/item/addresses/tax_rate etc.
Create PO    → pur_po_id
Create GP    → reads pur_po_id         → pur_gp_id
Create GRN   → reads pur_po_id, pur_gp_id → pur_grn_id
Create QC    → reads pur_po_id, pur_gp_id, pur_grn_id → pur_qc_id + pur_qc_lines
Create PB    → reads pur_qc_id, pur_grn_id, pur_po_id + pur_qc_lines → pur_pb_id
```

### Endpoints (match `purchase_chain.py`)
The procure-to-pay screens do **not** use `/core/dynamic-screen-wrapper/` for list/create/detail:

| Module | Endpoint |
|--------|----------|
| PO | `/procure_to_pay/purchase_order/` |
| GP | `/procure_to_pay/gate-pass/` |
| GRN | `/procure_to_pay/grn/` |
| QC | `/procure_to_pay/quality-control/` |
| PB | `/procure_to_pay/purchase-booking/` |

List responses return rows under `rows` (fallback `screenmatlistingdata_set`).
Only Supplier detail is fetched via `/core/dynamic-screen-wrapper/Supplier/{id}/`.
No `id`/`attribute_name` fields on these creates — payloads are the raw REST shape from the chain's payload builders.

### Discovery (Setup → Discover Context does the heavy lifting)
Mirrors `ChainContextDiscoverer.discover()`. The entry request is `GET /core/dynamic-screen-wrapper/Supplier/?page_number=1&page_size=5`; its test script runs serial, **decoupled** stages. Each stage is guarded independently and updates `pur_sniff_status`, so one failing stage (e.g. the stored-PO detail GET failing with 400/404 — your tenant) never blocks the rest:

1. **Supplier** — if the stored PO detail resolves and carries a supplier (`supplier_ref_id` + `supplier_details.supplier_ship_from/bill_from`), it is **preferred as-is** (mirrors the existing business records exactly: address FKs, payment/delivery terms, po_type, currency). Otherwise it scans the supplier list, fetches each detail (`Supplier/{id}/`), and picks the **first one with both ship-from and bill-from addresses** (address stepper), reading `po_type_ref_id`, `default_currency_ref_id`, and payment/delivery terms from the "additional" stepper → `pur_supplier_id`, `pur_ship_from`, `pur_bill_from`, `pur_supplier_po_type`, `pur_supplier_txn_currency`, `pur_supplier_payment_terms`, `pur_supplier_delivery_terms`. (Existing POs' `supplier_ref_id` in the *listing* is a display name — only the *detail* has the numeric FK.)
2. **Item** — a shared `fetchTaxMap` helper loads the tenant's HSN→tax map once (`Tax Rate/{id}/` detailing rows). Then `Item Master/?page_number=1&page_size=10` is walked in order: each `Item Master/{id}/` detail is checked for `hsn_sac_code` + both UOMs, and — where the tax map is available — the item is **skipped (with a clear status) if its HSN has no tax rate**, so Discover can't land you on an un-taxable item. First usable item → `pur_item_ref_id`, `pur_hsn_sac_no`, `pur_alternate_uom`, `pur_uom`, `pur_uom_conversion`. If an item was already seeded from a stored PO (stage 4 below) this stage is skipped entirely.
3. **Tax rate** — reuses the tax map: first `tax_rate` whose `hsn_sac_number` matches the item HSN → `pur_tax_rate` (the literal percentage the ERP applies to the PO line; verifiable from any existing PO's `txn_currency_tax_amount_details = txn_currency_amount_detail × tax_rate / 100`). Skipped when already seeded.
4. **Stored-PO defaults (item + header)** — best-effort: `GET /procure_to_pay/purchase_order/?page_number=1&page_size=3` → first `id` → detail → header `pur_parameter1/2/5/6`, `pur_po_item_type`, `pur_po_type`, `pur_base_currency`, `pur_txn_currency`; **and its first line item seeds `pur_item_ref_id`, `pur_hsn_sac_no`, `pur_uom`, `pur_alternate_uom`, `pur_uom_conversion`, `pur_tax_rate`** — the existing business record is the ground truth for a guaranteed-valid PO line. If the detail GET fails, header/item/tax fall back to the stage-2/3/5 results — the Create still runs.
5. **GP delivery type** — best-effort: reads the Gate Pass screen schema (`/core/dynamic-screen/Gate Pass/`), field `delivery_type` → first dropdown option (29 = Spot, 28 = Delivery) → `pur_gp_delivery_type`; falls back to default 29 if the schema is unavailable. Mirrors `ChainContextDiscoverer`'s `delivery_type` discovery.
6. **QC quality params (CQP)** — best-effort: walks `Commodity Quality Parameter` for the item seeded in stage 2/4, fetches each candidate detail, keeps the first active Purchase CQP matching `item_ref_id == pur_item_ref_id` with `from_date <= today`, and flattens `children[0].details[]` into `pur_qc_params` (`item_quality_parameter_ref_id = quality_type`, `actual_value = min_quality_value`). No CQP → var left unset (Create QC falls back to generic [1,2,3]). Mirrors `_resolve_cqp_params`.
7. **QC bag type (Packages)** — best-effort: `GET /core/dynamic-screen-wrapper/Packages/` → prefer a row whose name contains jute/joot else the first row → `Packages/{id}/` detail's `packages_line_details[0].type_of_bags_ref_id` (fallback: row's own `id`) → `pur_bags_type_id`. Mirrors `_resolve_bags_type_id`.

Finally it writes the consolidated **`pur_ctx`** JSON (`{v, supplier, item, gp, qc, po_defaults, sniff_status}`).

**List requests are now pure reads** — they just point at existing records for inspection and no longer sniff. Create GRN and Create QC are also sniff-free (they read only `pur_*` built by Discover/Prior Creates). PB still runs its old List sniff for PB terms until Discover gains that stage — the PO, GP, GRN and QC stages are complete.

### Quantity / rate
A single item is used per document. Create PO draws fresh random values (qty 500–2000, rate 500–6000) and stores them as `pur_qty` / `pur_rate` / `pur_no_of_bags`; every downstream step reuses them so the whole chain stays consistent. Amounts are rounded to 6 decimals to match Python's `round(x, 6)`.

### Troubleshooting: "Missing PO deps" on Create PO
Create PO requires `pur_supplier_id`, `pur_item_ref_id`, `pur_ship_from` and `pur_bill_from`. If any are empty, its pre-request throws `Missing PO deps: ...` and includes the current discovery status (`pur_sniff_status`, set by **Discover Context**).

- **`pur_sniff_status` tells you where Discover stopped:**
  - **`Discover not run yet`** → you have not run **Setup → Discover Context** (List PO is a pure read and never sniffs).
  - **`Discover OK | …`** → all four PO deps resolved; the rest of the status is the resolution narrative.
  - **`running | …`** (no `Discover OK`) → Discover executed but could not resolve one of the four PO deps — read on for the failing stage.
  - **`first request failed / non-JSON - check base_url, token, tenant_id`** → the entry Supplier GET returned a non-JSON body (usually a 401/502): paste the real token, set `tenant_id`, and confirm `base_url` in the Purchase Chain environment, then re-run.
  - `no Suppliers exist on tenant` / `no Supplier with both ship-from and bill-from addresses` → add addresses to a Supplier (or set `pur_supplier_id`, `pur_ship_from`, `pur_bill_from` manually).
  - `Item Master detail failed` / `missing HSN/UOM in Item Master` / `HSN ... has no tax rate - trying next` → Discover needs an item with HSN + primary/base UOM + a matching Tax Rate line, or set `pur_item_ref_id` (+ HSN/UOM) manually. `no item with HSN/uom and tax coverage` means the Item Master page had no usable item.
  - `stored PO detail unavailable - body defaults used` → expected on some tenants; header params fall back to body defaults, item/supplier are unaffected.
- **Manual fallback:** you never have to run Discover. Fill the required `pur_*` vars directly in the environment (the supplier's addresses/terms come from the Supplier's own registered steppers — see `_resolve_supplier_details` in `purchase_chain.py`).
- Discover's console messages show the same reasons — open **View → Show Postman Console** (⌘⌥C / Ctrl+Alt+C).

### QC math (pre-request, port of `_compute_qc_line_fields`)
All QC line fields are computed client-side — the ERP does not auto-patch on POST. Inputs come from **Discover** (`pur_qc_params` = the item's CQP tiers, `pur_bags_type_id` = Packages bag type) instead of an old List-QC sniff — see `08-qc.md`:

```
total_amount            = base_rate × grn_qty
empty_bags_txn_amount   = empty_bag_weight × base_rate
alternate_accepted_qty  = grn_qty − empty_bag_weight
qc_deduction_rate       = base_rate × deduction_percent / 100
deduction_weight        = grn_qty × deduction_percent / 100
qc_deduction_amount     = total_amount × deduction_percent / 100
subtotal                = total_amount − empty_bags − qc_deduction_amount
c_d_deduction           = subtotal × discount_rate / 100   (null when 0)
txn_currency_amount     = subtotal − c_d_deduction
rate                    = txn_currency_amount / alternate_accepted_qty
quantity_deduction      = Math.ceil(deduction_weight)
```

Random inputs per run: empty bag weight 0–12 kg, deduction 0–5%, discount 0–5%.

### PB math (pre-request, port of `build_pb_line` / `build_pb_payload`)
PB lines mirror the QC lines saved by Create QC (`pur_qc_lines`):

```
amount_detail  = qc.txn_currency_amount − labour_charges            (labour 10–300)
gst_type       = random IGST or CGST+SGST when tax_rate > 0          (matches chain)
totaltxn       = amount_detail − discount + tax − labour
```

Header aggregates: `txn_currency_amount` = Σ amount_detail, `txn_currency_total_amount` = Σ total_txn, `txn_currency_discount_amount` = Σ discount_details, `total_quantity` = Σ alternate_net_qty. Transportation 0–500, round-off 0–1.

---

## Payload Source

Bodies mirror the payload builders in:

- `pages/private_b2b/modules/purchase_order/data/purchase_order_data.py` (`build_po_payload` / `_po_items_from`)
- `pages/private_b2b/modules/gate_pass/data/gate_pass_data.py` (`build_gp_payload` / `_gp_items_from`)
- `pages/private_b2b/modules/goods_receipt_note/data/goods_receipt_note_data.py` (`build_grn_payload` / `_grn_items_from`)
- `pages/private_b2b/modules/quality_check/data/quality_check_data.py` (`build_qc_payload` / `_qc_items_from`)
- `pages/private_b2b/modules/purchase_booking/data/purchase_booking_data.py` (`build_pb_payload` / `build_pb_line`)

No hardcoded tenant FK values — everything resolvable is sniffed from existing records.

---

## What's Not Included

- No Sales Order (SO) step — the chain's optional 6th document is out of scope for now
- No multi-gate-pass / multi-item flow yet (1 item per document)
- No Update requests (not needed)
- No Delete requests (not available)

---

## See Also

- `pages/POSTMAN_GUIDE.md` — universal guide for building/extending collections
- `pages/private_b2b/scripts/purchase_chain.py` — source of truth for the flow