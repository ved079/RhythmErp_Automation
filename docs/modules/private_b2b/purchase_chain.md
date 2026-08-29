# Purchase Chain — Developer Reference

Full PO → GP → GRN → QC → PB automation for Private B2B tenants.

---

## What It Does

Creates a linked chain of ERP documents in sequence:

```
Purchase Order → Gate Pass → Goods Receipt Note → Quality Check → Purchase Booking
```

Each step POSTs to the ERP API, reads the created record's ID, and passes it to the next step. The chain is stateless across runs — every invocation creates fresh documents.

An optional Sales Order step (`SO`) can be inserted after QC (`PO → GP → GRN → QC → SO → PB`), and a standalone GP-only flow is also supported (`GP → GRN → QC → PB`).

---

## Key Files

| File | Purpose |
|------|---------|
| `pages/private_b2b/scripts/purchase_chain.py` | Core `PurchaseChain` class + `run()` / `run_multiple()` |
| `pages/private_b2b/scripts/chain_context.py` | `ChainContext` dataclass + `ChainContextDiscoverer` |
| `api/purchase_chain_endpoint.py` | FastAPI SSE endpoint — streams progress to web UI |
| `pages/private_b2b/modules/purchase_booking/data/purchase_booking_data.py` | `build_pb_line()` / `build_pb_payload()` builders |
| `pages/private_b2b/modules/purchase_booking/utils/ad_setup.py` | Accounting Definition pre-flight (tt=5) |
| `web-ui/src/components/dialogs/PurchaseChainSection.tsx` | Web UI panel for the chain |

---

## Running

### Web UI
Navigate to **Full Purchase Flow** in the sidebar → set token → click Run.

### CLI
```bash
python -m pages.private_b2b.scripts.purchase_chain \
  --token <bearer_token> \
  --tenant <tenant_id> \
  --supplier 2 \
  --count 1
```

### FastAPI endpoint (SSE)
```
POST /api/purchase-chain
```
Streams `LogEvent` objects as SSE. The web UI consumes this via `EventSource`.

---

## Accounting Definition Pre-flight

Before any chain runs, the chain validates and repairs the tenant's **Purchase Booking Accounting Definition** (transaction_type=5).

**What it does:**
- Fetches the Chart of Accounts and resolves 4 required ledger accounts (Purchase @gst, Purchase Exempt, Cash Discount, Closing Stock)
- Fetches Type of Sale IDs (B2B=1 etc.)
- If an existing AD is found → PUTs a canonical structure preserving all existing entry/condition IDs
- If none found → POSTs a new one

**Why it exists:** Without a correct AD, PBs are created (HTTP 201) but async accounting fails and the ERP silently rolls back the PB — it never appears in the listing.

**Key constraint:** When updating an existing AD entry that has no conditions, you cannot add new conditions (ERP returns 400). The code omits `id` on new entries rather than sending `id: null`.

---

## Inventory Accounting Definition (tt=6)

The Inventory AD is **not** auto-fixed by the chain — it must be configured manually per tenant.

**Correct structure (modelled from tenant 666):**

| Entry ID | Type | Account | Conditions |
|----------|------|---------|-----------|
| Credit | Purchase @gst | param8=IN=['PURCHASE_BOOKING'], param68=IN=['Supplier'], param39=EQUAL=[True] |
| Credit | Purchase Exempt | param8=IN=['PURCHASE_BOOKING'], param68=IN=['Farmer'], param39=EQUAL=[True] |
| Credit | Purchase @gst | param8=EQUAL=['INVOICE'], param68=IN=['Supplier'], param39=EQUAL=[True] |
| Credit | Closing Stock | param8=EQUAL=['INVOICE'], param39=EQUAL=[True] |
| Debit | Closing Stock | *(no conditions — fires for all transactions)* |

**Critical:** `param39=EQUAL=[True]` (is_stock_item) is required on all Credit entries. Without it, conditions don't match and Debit≠Credit → PB rollback.

The unconditional Debit entry must remain condition-free. Adding conditions to it via PUT causes a 400 error.

---

## PB Line Amount Computation

PB lines must carry non-zero computed amounts. The ERP trusts sent values for accounting rather than recomputing from base fields.

**Fields computed in `_pb_items_from_qc()` from QC data:**

| Field | Formula |
|-------|---------|
| `total_amount` | `grn_qty × base_rate` |
| `net_of_empty_bag_amount` | `alternate_accepted_qty × base_rate` |
| `alternate_gate_pass_quantity` | same as `grn_qty` |
| `alternate_deduction_weight` | from QC `alternate_deduction_weight` or `deduction_weight` |
| `qc_deduction_amount` | from QC `qc_deduction_amount` |
| `transaction_amount_without_discount` | `net_of_empty_bag − qc_deduction` |

If these are 0, accounting credit/debit entries compute to zero → Debit≠Credit → PB rolled back.

**Stored QC vs sent payload:** After QC creation, the chain fetches the stored QC (`GET /quality-check/{id}/`) and uses its `qc_details` for PB building, not the raw sent payload. This matches what the manual PB flow reads.

---

## PB Async Accounting — Verify & Retry

ERP returns HTTP 201 for PB creation immediately, then posts accounting asynchronously. If inventory accounting fails, the ERP silently rolls back the PB.

**Chain behaviour after PB creation:**
1. Wait 3s → GET PB by ID
2. If found → confirmed ✓
3. If 404 (rolled back) → wait 5s more, check again
4. Still not found → wait **12 seconds** (accounting processor recovery time) → retry PB creation against the same QC/GRN/PO
5. Report retry result in logs

**Why the rollback happens:** Two PBs for the same item created in quick succession both try to post to the inventory ledger simultaneously, causing a lock conflict. The 12s cooldown gives the ERP time to release the ledger lock.

**Inter-chain delay:** When running multiple chains in one request with PB enabled, a **4-second delay** is inserted between chains (in `purchase_chain_endpoint.py`) to reduce ledger conflicts.

---

## Context Discovery

`ChainContextDiscoverer` discovers tenant-specific FK IDs from live ERP data on first run. Cached in `PurchaseChain._context` for the session.

Discovered values: `supplier_ref_id`, `item_ref_id`, `hsn_sac_no`, `alternate_uom`, `base_uom`, `po_type`, `base_currency`, `txn_currency`, `parameter1–6`, `payment_terms`, `delivery_terms`, `delivery_type`, `supplier_ref_type`, `pb_payment_terms`.

`get_context_for_supplier(supplier_id)` clones the base context and overlays supplier-specific addresses + payment terms without re-running full discovery.

---

## Web UI — PurchaseChainSection

**Token / data loading rules:**
- On page mount → **no fetch** (even if a token is stored from a previous session)
- User clicks **Done** in the token panel → fetches master data
- User clicks **Refresh** → fetches master data
- If ERP returns 502/503/504 → auto-retries once after 2 seconds
- Error message names the failing screen (e.g. `"Supplier: ERP request failed"`)

**Why no auto-load:** The ERP token persists in `localStorage` across sessions. Without this rule, navigating to the page would immediately trigger 4 parallel ERP API calls and show the loading animation before the user does anything.

---

## Known ERP Behaviours

| Behaviour | Explanation |
|-----------|------------|
| PB created (201) but not in listing | Async accounting failed → ERP rolled back. Chain now detects this and retries. |
| Manual PB stuck at step 5 | ERP WebSocket connection stale. Hard-refresh the ERP browser. Unrelated to chain code. |
| Supplier #11 on tenant 839 → "Item Name duplicate in Row 2" | Accounting filter returns only 1 item for that supplier. Use supplier #2 (has 2 distinct items in category 1). |
| AD PUT returns 400 on adding conditions | Cannot add new conditions to an entry that previously had none. Code avoids this. |

---

## Tenant Setup Checklist

Before running the chain on a new tenant:

- [ ] Purchase Booking AD (tt=5) — auto-fixed by chain pre-flight
- [ ] Inventory AD (tt=6) — must be manually configured to match the structure above
- [ ] Item has HSN, primary UOM, and base UOM in Item Master
- [ ] Item has a Commodity Quality Parameter entry
- [ ] Item has a Tax Rate entry (if `require_tax_rate=True`)
- [ ] Supplier has an address (ship-from / bill-from) configured
