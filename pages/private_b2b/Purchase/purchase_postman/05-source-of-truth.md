# 6. Source-of-Truth Mapping (Python ↔ Postman)

Every Postman takeover of a tenant FK / payload field has a corresponding function in the chain scripts. When the collection breaks, diff against these — the Python code is the source of truth.

- `pages/private_b2b/scripts/purchase_chain.py`
- `pages/private_b2b/scripts/chain_context.py`
- `pages/private_b2b/modules/purchase_order/data/purchase_order_data.py`

---

## 6.1 Discovery (Discover Context ↔ chain_context.py)

| Postman (Discover Context test script) | Python | Notes |
|----------------------------------------|--------|-------|
| Whole discovery flow | `ChainContextDiscoverer.discover()` | Same stages, same fallbacks |
| Supplier scan → ship/bill from address stepper | `PurchaseChain._resolve_supplier_details()` | address stepper `details[0]`=ship, `details[1]`=bill; additional stepper = terms |
| Stored-PO preferred supplier | `_sniff_po_defaults()` + `supplier_details` read | real-business-record ground truth |
| Supplier `po_type_ref_id` / `default_currency_ref_id` | `_resolve_supplier_details()` `out.po_type` / `out.txn_currency` | per-supplier PO header values (schema 404s) |
| Item scan (HSN + UOMs + tax guard) | `_resolve_item_detail()` + `_resolve_tax_rates()` | HSN = `hsn_sac_code`, uom = `uom`, base_uom = `base_uom` |
| Tax map | `_resolve_tax_rates()` | `Tax Rate/{id}/` → `children[*].details[*]` `{hsn_sac_number, tax_rate}` |
| Item category scoping | `_resolve_item_categories()` / `_resolve_item_category()` | PO Item dropdown is category-scoped (chain-only; Postman currently uses the first usable item) |

## 6.2 Create PO payload ↔ purchase_order_data.py

| Postman | Python |
|---------|--------|
| Body template | `build_po_payload()` in `purchase_order/data/purchase_order_data.py` |
| Line shape | `_po_items_from()` in `purchase_chain.py` |
| qty / rate ranges | `_QTY_MIN`/`_QTY_MAX` (500–2000), `_RATE_MIN`/`_RATE_MAX` (500–6000) |
| amount / tax / total | `_po_items_from()` (round 6dp) |
| `gst_type = 'IGST'` | `_po_items_from(items, gst_type="IGST")` |

## 6.3 Field-semantics cheat sheet (from `_po_items_from` docstring)

- `alternate_uom` = item **primary** UOM (e.g. MT)
- `uom` = item **base** UOM (e.g. KG)
- `alternate_quantity` is a **string** on the PO line
- ERP expects amounts pre-filled:
  - `txn_currency_amount_detail` = `rate × alternate_quantity`
  - `txn_currency_tax_amount_details` = that × `tax_rate / 100`
  - `total_amount` = amount + tax
- PO line has **no** `quantity` and **no** `is_gst_set_off`

## 6.4 Known reference values

Python fallback context (`chain_context.py._FALLBACKS`, tenant-711 values) — useful when sanity-checking a Discover result:

| Field | Fallback |
|-------|----------|
| `item_type_ref_id` (po_item_type) | 113 |
| `po_type` | 24 (chain fallback) / 25 (collection default) |
| `base_currency` / `txn_currency` | 8 |
| `parameter1/2/5/6` | 1 |
| `payment_terms` / `delivery_terms` | 549 / 130 |
| `supplier_ship_from` / `supplier_bill_from` | 17 / 18 |

> These are **fallbacks**, not guarantees — Discover/`pur_ctx` values are the runtime truth.

## 6.5 What the Postman port changed on purpose

| Change | Why |
|--------|-----|
| Async `discover()` instead of nested callbacks | One failing stage used to abort everything; now it narrates and falls back |
| Supplier from stored PO preferred | Mirrors real business records exactly (address FKs, terms) |
| Item tax-map guard | Can't land on an un-taxable item |
| Stored-PO first line seeds item/tax | Existing record is guaranteed-valid ground truth |
| `pur_ctx` consolidated JSON | Single snapshot for debugging / reproduction |
| List requests demoted to pure reads | They no longer sniff; Discover owns all state-building |