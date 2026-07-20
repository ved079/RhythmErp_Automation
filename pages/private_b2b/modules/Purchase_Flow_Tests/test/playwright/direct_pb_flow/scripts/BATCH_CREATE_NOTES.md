# Direct PB Batch Create — Notes

## What this does

Creates Purchase Booking entries via the ERP API for the **Eco Green Pvt Ltd** tenant (tenant 712)
without any PO / QC / GRN reference — a standalone "direct" purchase booking.

---

## Files

| File | Purpose |
|---|---|
| `scripts/batch_create.py` | CLI runner — resolves FK IDs live, builds payloads, POSTs to ERP |
| `data/direct_pb_data.py` | Payload builders and calculation helpers — fully isolated from the general `purchase_booking/` module |

---

## Usage

```bash
# Basic — 1 PB, items 58-77 (default)
python batch_create.py --token <jwt> --tenant 712 --count 1

# Multiple PBs
python batch_create.py --token <jwt> --tenant 712 --count 5

# Preview without creating
python batch_create.py --token <jwt> --tenant 712 --count 1 --dry-run

# Pin a specific supplier
python batch_create.py --token <jwt> --tenant 712 --count 3 --supplier 2

# Custom item range (all items in range go into each PB as separate rows)
python batch_create.py --token <jwt> --tenant 712 --count 1 --item-range 58-77

# Random N items per PB from the full usable pool (only when --item-range is omitted)
python batch_create.py --token <jwt> --tenant 712 --count 3 --items-per-pb 5
```

**Default item range is `58-77` (20 items) — every PB gets all 20 as separate line rows.**

---

## What gets resolved live from ERP

Every run calls the ERP before building payloads — nothing is hardcoded except the item range.

| What | ERP call | Field used |
|---|---|---|
| Supplier IDs | `Supplier` listing | `id` |
| Item IDs + names | `Item Master` listing | `id`, `name` |
| HSN SAC No per item | `Item Master` detail | `hsn_sac_code` |
| Alternate UOM per item | `Item Master` detail | `uom` (primary UOM) |
| Base UOM per item | `Item Master` detail | `base_uom` |
| UOM conversion per item | `Item Master` detail | `base_uom_conversion` |
| Division | PB dropdown `parameter1` | `id` |
| Department | PB dropdown `parameter2` | `id` |
| Location | PB dropdown `parameter5` | `id` |
| Type of Sale | PB dropdown `parameter6` | `id` |
| Payment terms | PB dropdown `supplier_payment_terms_ref_id` | `id` |

Items that come back without a valid HSN or UOM are silently skipped — the script won't crash.

---

## Key field discoveries (from real ERP GET response)

These tripped us up and are worth remembering.

### Item Master field names vs PB line field names

The Item Master detail response uses **different names** from what the PB line expects:

| Item Master field | PB line field | Notes |
|---|---|---|
| `hsn_sac_code` | `hsn_sac_no` | Different name entirely |
| `uom` | `alternate_uom` | Primary UOM → goes to alternate slot |
| `base_uom` | `uom` | Base/weight UOM → goes to main UOM slot |
| `base_uom_conversion` | `uom_conversion` | Conversion factor (e.g. 0.001) |

**Easy to get backwards** — `alternate_uom` is the item's *primary* UOM, `uom` is the item's *base* UOM.

### Master payload fields

| Field | Wrong assumption | Correct value |
|---|---|---|
| `conversion_rate` | `"1"` (string) | `1.0` (float) |
| `section_ref_id` | `"0"` (string) | `0` (int) |
| `is_tds_applicable` | `False` | `None` |
| `posting_status` | `""` | `None` |
| `remark` | `""` | `None` |
| `other_charges.agent_commision_amount` | `0` | `None` |

### Line item computed fields

The ERP expects these to be **pre-calculated and sent** — it does not recompute from rate/qty:

| Field | Formula |
|---|---|
| `alternate_net_qty` | `alternate_qty - empty_bag_weight` |
| `txn_currency_amount_detail` | `rate × alternate_net_qty - labour_charges` |
| `txn_currency_discount_amount_details` | `txn_currency_amount_detail × discount_percentage / 100` |
| `txn_currency_total_txn_amount` | `txn_currency_amount_detail - txn_currency_discount_amount_details` |

Master `txn_currency_amount` and `txn_currency_total_amount` = sum of all line `txn_currency_total_txn_amount`.

Note: the discount field on the line is `txn_currency_discount_amount_details` (not `discount_amount`).

### Qty Details sub-array

Each line item has a nested `details` list — this mirrors the Quantity Details popup in the UI:

```json
"details": [
  {
    "no_of_bags_subdetails": 5,
    "quantity_sub_details": 500.0
  }
]
```

One entry per popup row. For batch create we always send one entry matching the line's `no_of_bags` and `alternate_qty`.

### No reference IDs

This is a direct PB — always send:

```json
"qc_ref_id_id": null,
"grn_ref_id_id": null,
"po_ref_id_id": null
```

### `supplier_ref_type`

Must be the string `"Farmer"` (not an integer). The general PB module uses integer constants
mapped to strings — this module skips that indirection and hardcodes `"Farmer"` directly since
this flow only ever uses farmer suppliers.

---

## What failed and why (debugging log)

### First attempt — HTTP 500 `"Failed to create Purchase Booking"`

Root causes found by fetching an existing PB via GET and comparing:

1. `alternate_uom` and `uom` were swapped — was passing `base_uom` as `alternate_uom`
2. `conversion_rate` was `"1"` (string) — should be `1.0` (float)
3. `section_ref_id` was `"0"` (string) — should be `0` (int)
4. `is_tds_applicable` was `False` — should be `None`
5. Discount field named `discount_amount` — correct name is `txn_currency_discount_amount_details`
6. `other_charges.agent_commision_amount` was `0` — should be `None`

### Item detail fetch — all items skipped

First pass used `hsn_sac_no`, `alternate_uom`, `uom_conversion` as key names on the Item Master
GET response. The actual field names are `hsn_sac_code`, `uom`, `base_uom`, `base_uom_conversion`.
Fixed by inspecting a raw GET response for one item before building the resolver.

---

## Confirmed working

| Run | Result |
|---|---|
| 1 PB, 1 item | ID=1853 ✅ |
| 2 PBs, 3 items each | ID=1854, 1855 ✅ |
| 1 PB, 20 items (58-77) | ID=1856 ✅ |
