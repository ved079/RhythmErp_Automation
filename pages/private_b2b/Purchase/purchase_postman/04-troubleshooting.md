# 5. Troubleshooting — `pur_sniff_status` failure modes

`pur_sniff_status` is a running narrative written by **Discover Context**. Reading it is the primary debugging technique for the PO stage. Check the env var in Postman, or open **View → Show Postman Console** (`Ctrl+Alt+C`) and read `Discover done: <status>`.

---

## 5.1 Status states

| Status prefix | Meaning |
|---------------|---------|
| `Discover not run yet` | You have not run Setup → Discover Context (List PO is a pure read and never sniffs) |
| `Discover OK \| …` | All four PO deps resolved (`pur_supplier_id`, `pur_item_ref_id`, `pur_ship_from`, `pur_bill_from`); rest is the resolution narrative |
| `running \| …` (no `Discover OK`) | Discover executed but could not resolve one of the four PO deps — read the stages |
| `Discover crashed: <msg>` | Unexpected exception inside `discover()` |

## 5.2 Failure strings and fixes

| `pur_sniff_status` fragment | Root cause | Fix |
|-----------------------------|-----------|-----|
| `first request failed / non-JSON - check base_url, token, tenant_id (HTTP <code>)` | Entry Supplier GET returned non-JSON → usually 401 (expired token) or 502 | Paste a fresh token; confirm `base_url` and `tenant_id`; re-run Discover |
| `no Suppliers exist on tenant` | Supplier list is empty | Create a Supplier; or manual fallback |
| `no Supplier with both ship-from and bill-from addresses; set pur_supplier_id/ship_from/bill_from manually` | Every supplier lacks at least one registered address stepper row | Add ship+bill addresses to a Supplier in ERP; or manual fallback |
| `Item Master listing failed - set pur_item_ref_id manually` | `GET Item Master/...` errored (non-2xx) | Check token/tenant; or set `pur_item_ref_id` (+ HSN/UOM) manually |
| `no Items in Item Master - set pur_item_ref_id manually` | Item list empty | Create an Item in ERP; or manual fallback |
| `missing HSN/UOM in Item Master - trying next` | Item detail lacks `hsn_sac_code` or `uom`/`base_uom` | Pick an item with HSN + both UOMs; or manual fallback |
| `HSN <x> has no tax rate - trying next` | Item's HSN has no matching Tax Rate line | Use an item whose HSN has a tax rate; or manual fallback (then `pur_tax_rate` stays 0 and the PO is created tax-free) |
| `no item with HSN/uom and tax coverage - set pur_item_ref_id manually` | Item Master page contained no usable item | Needs an item with HSN + UOMs + tax-map coverage; or manual fallback |
| `no stored PO for header defaults` | Tenant has no Purchase Orders | Expected on fresh tenants — header params fall back to body defaults; item/supplier unaffected; Create still runs |
| `stored PO detail unavailable - body defaults used` | `GET purchase_order/{id}/` failed (400/404 seen on some tenants) | **Expected** — header params fall back; item/supplier unaffected; Create still runs |
| `stored PO defaults unavailable` | The `purchase_order/` list itself errored | Check token/tenant; Create still runs with body defaults |
| `Missing PO deps: ...` (on Create PO) | You skipped/failed Discover, or Discover couldn't resolve all four deps | Read `pur_sniff_status` in the error message; re-run Discover |
| `Missing GRN deps: ...` (on Create GRN) | Missing a prior hop (`pur_po_id`/`pur_gp_id`/`pur_supplier_id`/`pur_item_ref_id`) | Run the full **Discover → Create PO → Create GP** sequence first; see `07-grn.md` §7.6 |
| `Missing QC deps: ...` (on Create QC) | Missing a prior hop (`pur_po_id`/`pur_gp_id`/`pur_grn_id`/`pur_supplier_id`/`pur_item_ref_id`) | Run the full **Discover → Create PO → Create GP → Create GRN** sequence first; see `08-qc.md` §8.6 |
| `QC quality params unavailable in CQP - Create QC uses generic params` (Discover) | Item has no active Purchase CQP on the tenant | Expected on fresh tenants — generic [1,2,3] used; see `08-qc.md` §8.2/§8.4 |
| `CQP scan failed: ...` / `Packages scan failed: ...` (Discover) | CQP/Packages GET errored while resolving `pur_qc_params`/`pur_bags_type_id` | Check token/tenant; Create QC still falls back (generic params / bag type 20) |
| `Discover not run yet` + Postman shows **no console output at all** after running Discover | Discover's test script failed to even parse — historically caused by a stage being added at the **top level of the script with a top-level `await`** (Postman rejects it: `await is only valid in async functions`), so nothing executed | Re-import the patched collection (this was fixed in the GP patch); if you ever add a stage, put it **inside `async function discover()`** and confirm it parses before trusting it |

## 5.3 GP / GRN / QC-specific signals

See `06-gp.md` §6.6 for the GP-stage failure table (`Missing GP deps`, `delivery_type` fallback, etc.), `07-grn.md` §7.6 for GRN failures (`Missing GRN deps`, currency nuance, booking_status), and `08-qc.md` §8.6 for QC failures (`Missing QC deps`, CQP/Packages fallbacks, currency-follows-PO).

## 5.4 Manual fallback (never required, always available)

You never have to run Discover. Fill the `pur_*` vars directly in the environment:

- `pur_supplier_id`, `pur_ship_from`, `pur_bill_from`, `pur_item_ref_id` — the four hard deps.
- Optionally: `pur_hsn_sac_no`, `pur_uom`, `pur_alternate_uom`, `pur_uom_conversion`, `pur_tax_rate`, `pur_po_item_type`, `pur_po_type`, `pur_base_currency`, `pur_txn_currency`, `pur_parameter1/2/5/6`, `pur_qc_params`, `pur_bags_type_id`.

The supplier's addresses/terms come from the Supplier's own registered steppers — see `_resolve_supplier_details` in `pages/private_b2b/scripts/purchase_chain.py`.

## 5.4 Create PO failure with a non-deps error

Create PO throws `PO create failed: <raw body>` from its test script when the response lacks `id`/`entry_id`. Paste the raw body into a JSON formatter — the ERP usually returns the field-level validation errors in the body. Common causes:

- Expired token mid-run.
- Stale `pur_*` from a previous tenant (re-run Discover after switching).
- The chosen item lost its tax rate / UOM in ERP (run Discover again to re-pick).

## 5.5 Verification loop

1. Run **Discover Context**.
2. Check `pur_sniff_status` starts with `Discover OK |`.
3. Inspect `pur_ctx` — the entity summary is a compact diff vs. expectation.
4. Run **Create PO**; confirm `{"status":"Record Created Successfully","id":<id>}` and `pur_po_id` is set.
5. Optionally `Get PO Detail` (`purchase_order/{{pur_po_id}}/`) and confirm the line amounts match `amount/tax/total` from `03-po-create.md`.