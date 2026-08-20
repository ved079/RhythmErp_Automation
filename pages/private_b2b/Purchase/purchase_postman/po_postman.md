# Purchase Order (PO) — Postman Knowledge Base

Index + working-state overview. Each section lives in its own file so it can be updated independently as the chain grows.

**Scope of this doc set:** the **PO, GP, GRN, and QC stages** — Setup → Discover Context, Create PO, Create GP, Create GRN, and Create QC. PB / SO sections will be added as separate files as we verify them.

---

## Table of Contents

| # | File | What it covers |
|---|------|----------------|
| 1 | `00-runbook.md` | Imports, environment vars, verified run order |
| 2 | `01-discover-context.md` | The async `discover()` script — the piece we fixed |
| 3 | `02-endpoints-quirks.md` | Endpoints that actually work + ERP schema quirks |
| 4 | `03-po-create.md` | Create PO pre-request math + required deps |
| 5 | `04-troubleshooting.md` | `pur_sniff_status` failure modes + manual fallbacks |
| 6 | `05-source-of-truth.md` | Python ↔ Postman mapping (`purchase_chain.py` / `chain_context.py`) |
| 7 | `06-gp.md` | Gate Pass — verified step (delivery_type via schema, uom_conversion fix, create mapping) |
| 8 | `07-grn.md` | GRN — verified step (real uom_conversion vs GP's 1.0, currency-1/1 reason, create mapping) |
| 9 | `08-qc.md` | QC — verified step (CQP params + Packages bag type via Discover, currency-follows-PO, create mapping) |

---

## Current Working State (confirmed)

- **Collection:** `Purchase Chain` (`purchase_collection.json`)
- **Environment:** `Purchase Chain` (`environment.json`)
- **Verified tenant:** 795 (`https://rhythmerp.algorhythms.in`) — note: the token used in this session reaches **795**; 711 now 401s on procure-to-pay, so the env default is `795`.
- **Last successful linked run:** PO **3910** → GP **2518** → GRN **2144** → QC **2143** (`QC/2026-2027/000279`) — full chain created and stored-back verified (earlier validated runs: PO 3906 → GP 2511 → GRN 2137 → QC 2129; PO 3886 → GP 2486; PO 3884; PO 3838; GP 2418; GRN 2125 reference).

### What changed most recently (the fix that made it work)

The **Discover Context** test script was rewritten from a fragile, synchronous, single-path sniff into an **async, decoupled-stage discovery** that mirrors `ChainContextDiscoverer.discover()` in `pages/private_b2b/scripts/chain_context.py`. Key behavioral changes:

1. **Stored-PO supplier is now preemptively preferred** — if an existing PO's detail carries `supplier_ref_id` + `supplier_details.supplier_ship_from/bill_from`, that supplier/address pair is taken as-is (mirrors the real business records), skipping the supplier-list scan.
2. **Item selection is guarded** — an Item Master row must have BOTH `hsn_sac_code` and both UOMs, and (when the tenant tax map is available) its HSN **must have a tax rate** or it is skipped with a visible status note.
3. **Stored-PO line seeds the item/tax** — the first line of the first stored PO detail is the ground truth for `pur_item_ref_id` / `pur_hsn_sac_no` / `pur_uom` / `pur_tax_rate`, so the Create payload is guaranteed-valid even when the Item Master scan would fail.
4. **Every stage is independently guarded** — a failing stage (e.g. the stored-PO detail GET 400/404, which happens on some tenants) never blocks the rest; it logs to `pur_sniff_status` and falls back.
5. **GP delivery_type stage added** — resolved from the Gate Pass schema dropdown (`pur_gp_delivery_type`, 29=Spot/28=Delivery), killing the old fragile List-sniff; List GP is now a pure read.
6. **`pur_ctx`** — a consolidated `{v, supplier, item, gp, po_defaults, sniff_status}` JSON is written for posterity/debugging.

**Latest bugfix (GP patch):** the first GP patch placed the new `delivery_type` stage at the *top level* of the Discover test script with a top-level `await` — a syntax error in Postman's sandbox, so the entire Discover script silently failed and Create PO reported `Discover not run yet`. Fixed by moving the stage inside `async function discover()` (first statement of its `try`). Re-verified live against the ERP: `Discover OK | delivery_type 29 from GP schema | ...` with the same values as the validated PO 3886 → GP 2486 run.

**GRN patch (this session):** Create GRN hardened to the same deps-guard pattern (`Missing GRN deps: pur_po_id, pur_gp_id, ...` + `pur_sniff_status` hint) and its currencies changed to the chain-faithful `1/1` (was `pur_base_currency || 1`, which would have sent 8 in this flow — the chain proves GRN ignores the PO's currency). See `07-grn.md`.

**QC patch (this session):** the last sniffed stage is gone. Discover Context now resolves both QC-only FKs — the item's **CQP** quality params (`pur_qc_params`, `Commodity Quality Parameter` screen) and the **bag type** (`pur_bags_type_id`, `Packages` screen) — so a fresh tenant with no stored QC works. List QC demoted to a pure read (its test script deleted the sniff). Create QC hardened to the full deps guard (`Missing QC deps: pur_po_id, pur_gp_id, pur_grn_id, pur_supplier_id, pur_item_ref_id` + `pur_sniff_status` hint). QC stores the PO's currency (8/8 on 795 — the opposite of GRN's 1/1). Verified live: QC **2143** with all 9 CQP tiers + bag type 20 stored back. See `08-qc.md`.

**No longer stale:** Create GP previously sent the item's `uom_conversion` (20 on 795); the chain hardcodes `1.0` — fixed and verified stored-back (see `06-gp.md`).

### The golden rule

**Run Setup → Discover Context first, then Create PO → Create GP → Create GRN → Create QC.** List requests are pure reads and never sniff. If anything breaks, read `pur_sniff_status` — it tells you exactly where discovery stopped. See `04-troubleshooting.md`.

---

## Repository context

- This folder: `pages/private_b2b/Purchase/purchase_postman/`
- Source of truth scripts:
  - `pages/private_b2b/scripts/purchase_chain.py`
  - `pages/private_b2b/scripts/chain_context.py`
- Payload builders: `pages/private_b2b/modules/purchase_order/data/purchase_order_data.py`