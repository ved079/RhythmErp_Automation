"""
ad_setup.py — Universal Purchase Booking Accounting Definition setup script.

For any RhythmERP tenant, this script:
  1. Resolves all required account IDs from the Chart of Account Definition by name.
  2. Resolves Type of Sale IDs from the PB screen's parameter6 dropdown.
  3. Builds the canonical Purchase Booking AD structure.
  4. Creates the AD if none exists, or PUTs the corrected one if it does.

Canonical AD structure (Purchase Booking, transaction_type=5):
  CR  Payable                   val=9   always        sub_ledger=True
  DR  Purchase @gst             val=10  supplier only (supplier_ref_type=Supplier)
  DR  Purchase exempt           val=10  farmer only   (supplier_ref_type=Farmer)
  DR  Input IGST                val=11  always
  DR  Input CGST                val=12  always
  DR  Input SGST                val=13  always
  CR  Round Off                 val=38  always
  DR  Round Off                 val=37  always

param5 in conditions = supplier_ref_type field ("Supplier" / "Farmer")
param6 in conditions = parameter6 field (Type of Sale FK IDs, tenant-specific)

Usage:
    python ad_setup.py --token <jwt> --tenant <id>
    python ad_setup.py --token <jwt> --tenant <id> --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient

# ── Constants ─────────────────────────────────────────────────────────────────

_PB_TRANSACTION_TYPE = "5"
_PB_AD_NAME = "Purchase Booking"

# ERP-global transaction value codes (same on every tenant)
_VAL_PAYABLE        = "9"
_VAL_PURCHASE       = "10"
_VAL_IGST           = "11"
_VAL_CGST           = "12"
_VAL_SGST           = "13"
_VAL_ROUNDOFF_DR    = "37"
_VAL_ROUNDOFF_CR    = "38"

# AD condition parameter IDs (ERP-global)
_PARAM_SUPPLIER_TYPE = 5   # maps to supplier_ref_type field
_PARAM_TYPE_OF_SALE  = 6   # maps to parameter6 field (Type of Sale)

# Operator codes
_OP_IN     = 1704
_OP_NOT_IN = 1705
_OP_AND    = 1710

# Required CoA account names → looked up by exact name on each tenant
# Value: (name_candidates, sub_ledger, description)
_REQUIRED_ACCOUNTS: list[tuple[list[str], bool, str]] = [
    (["Payable"],                             True,  "Creditors / AP"),
    (["Purchase @gst"],                       False, "Purchase (taxable)"),
    (["Purchase exempt"],                     False, "Purchase (exempt)"),
    (["Input IGST"],                          False, "Input IGST"),
    (["Input CGST"],                          False, "Input CGST"),
    (["Input SGST"],                          False, "Input SGST"),
    (["Expense Round Off", "Round Off"],      False, "Round-off"),
]


# ── CoA resolution ────────────────────────────────────────────────────────────

def fetch_coa(client: RhythmERPAPIClient) -> dict[str, int]:
    """Return {account_name: id} for the tenant's Chart of Account Definition."""
    r = client.session.get(
        f"{client.BASE_URL}/core/dynamic-screen-wrapper/Chart%20Of%20Account%20Definition/",
        params={"page_number": 1, "page_size": 500},
        timeout=15,
    )
    if r.status_code != 200:
        raise RuntimeError(f"CoA fetch failed: HTTP {r.status_code}")
    rows = r.json().get("screenmatlistingdata_set") or []
    return {row["name"]: row["id"] for row in rows if row.get("id") and row.get("name")}


def resolve_accounts(coa: dict[str, int]) -> dict[str, int]:
    """
    For each required account, try each candidate name in order.
    Returns {canonical_name: id}.  Raises if any account is missing.
    """
    resolved: dict[str, int] = {}
    missing: list[str] = []
    for candidates, _, desc in _REQUIRED_ACCOUNTS:
        found_id = None
        for name in candidates:
            if name in coa:
                found_id = coa[name]
                resolved[candidates[0]] = found_id  # key by first (canonical) name
                break
        if found_id is None:
            missing.append(f"{desc} (tried: {candidates})")
    if missing:
        raise RuntimeError(
            "Missing accounts in CoA — create them first:\n"
            + "\n".join(f"  - {m}" for m in missing)
        )
    return resolved


# ── Type of Sale resolution ───────────────────────────────────────────────────

def fetch_type_of_sale_ids(client: RhythmERPAPIClient) -> list[int]:
    """Return all parameter6 (Type of Sale) IDs from the PB screen dropdown."""
    opts = client.get_dropdown_options("Purchase Booking", "parameter6") or []
    ids = [int(o["id"]) for o in opts if o.get("id") is not None]
    return ids


# ── AD payload builder ────────────────────────────────────────────────────────

def _param_block() -> dict:
    return {
        "parameter1": ["All"],
        "parameter2": ["All"],
        "parameter5": ["All"],
        "parameter6": ["All"],
    }


def _condition(param_id: int, operator: int, options: list, logical_op=None) -> dict:
    return {
        "parameter": param_id,
        "operator": operator,
        "options": options,
        "logical_operator": logical_op,
        "parent_id": 0,
    }


def build_ad_payload(accounts: dict[str, int], tos_ids: list[int]) -> dict:
    """
    Build the canonical Purchase Booking AD payload.

    Purchase @gst  fires when supplier_ref_type = Supplier (any Type of Sale).
    Purchase exempt fires when supplier_ref_type = Farmer  (any Type of Sale).
    All other entries are unconditional.
    """
    payable_id    = accounts["Payable"]
    purchase_gst  = accounts["Purchase @gst"]
    purchase_ex   = accounts["Purchase exempt"]
    igst_id       = accounts["Input IGST"]
    cgst_id       = accounts["Input CGST"]
    sgst_id       = accounts["Input SGST"]
    roundoff_id   = accounts["Expense Round Off"]

    # supplier_ref_type conditions
    cond_supplier = [
        _condition(_PARAM_SUPPLIER_TYPE, _OP_IN, ["Supplier"], None),
    ]
    cond_farmer = [
        _condition(_PARAM_SUPPLIER_TYPE, _OP_IN, ["Farmer"], None),
    ]

    def entry(dr_cr, account_id, value_name, conditions=None, sub_ledger=False):
        return {
            "account_ref_id": account_id,
            "dr_cr": dr_cr,
            "value_name": value_name,
            "inter_company": "",
            "is_sub_ledger_applicable": sub_ledger,
            "parameter": _param_block(),
            "conditions": conditions or [],
            "is_screen_coa_applicable": False,
        }

    details = [
        # Creditors / AP — always, sub-ledger enabled
        entry("Credit", payable_id,   _VAL_PAYABLE,  sub_ledger=True),
        # Purchase debit — Supplier
        entry("Debit",  purchase_gst, _VAL_PURCHASE, conditions=cond_supplier),
        # Purchase debit — Farmer (exempt)
        entry("Debit",  purchase_ex,  _VAL_PURCHASE, conditions=cond_farmer),
        # Tax entries — always
        entry("Debit",  igst_id,      _VAL_IGST),
        entry("Debit",  cgst_id,      _VAL_CGST),
        entry("Debit",  sgst_id,      _VAL_SGST),
        # Round-off — always
        entry("Credit", roundoff_id,  _VAL_ROUNDOFF_CR),
        entry("Debit",  roundoff_id,  _VAL_ROUNDOFF_DR),
    ]

    return {
        "name": _PB_AD_NAME,
        "transaction_type": _PB_TRANSACTION_TYPE,
        "accounting_definition_detail": details,
    }


# ── AD create / update ────────────────────────────────────────────────────────

def find_existing_pb_ad(client: RhythmERPAPIClient) -> dict | None:
    """Return the existing Purchase Booking AD record or None."""
    r = client.session.get(
        f"{client.BASE_URL}/core/accounting-definition/",
        params={"page_number": 1, "page_size": 100},
        timeout=15,
    )
    if r.status_code != 200:
        raise RuntimeError(f"AD listing failed: HTTP {r.status_code}")
    listing = r.json()
    rows = listing if isinstance(listing, list) else (
        listing.get("results") or listing.get("screenmatlistingdata_set") or []
    )
    return next(
        (r for r in rows if str(r.get("transaction_type", "")) == _PB_TRANSACTION_TYPE),
        None,
    )


def _fetch_existing_ad(client: RhythmERPAPIClient, ad_id: int) -> dict:
    """Fetch full AD record (top-level + detail list)."""
    r = client.session.get(
        f"{client.BASE_URL}/core/accounting-definition/{ad_id}/",
        timeout=15,
    )
    if r.status_code == 200:
        return r.json()
    return {}


def _build_from_existing(canonical_details: list[dict], existing_details: list[dict]) -> list[dict]:
    """
    Build the final detail list for a PUT by recycling existing entry/condition IDs.

    The ERP PUT serializer requires every sub-record that already has an id to echo
    that id back; new sub-records (no id) are rejected when the parent already has one.
    Strategy: assign each canonical entry to an existing entry (by semantic match first,
    then positional), then overlay the existing entry's id and condition ids onto the
    canonical entry's content.
    """
    pool = list(existing_details)
    result = []

    for canon in canonical_details:
        # Try semantic match: same dr_cr + value_name + account_ref_id
        key = (canon.get("dr_cr"), str(canon.get("value_name")), canon.get("account_ref_id"))
        match = next(
            (e for e in pool
             if e.get("dr_cr") == key[0]
             and str(e.get("value_name", "")) == key[1]
             and e.get("account_ref_id") == key[2]),
            None,
        )
        # Fallback: any leftover entry from pool (positional)
        if match is None and pool:
            match = pool[0]

        if match:
            pool.remove(match)
            # Build merged entry: canonical content + existing id
            merged = {**canon, "id": match["id"]}
            # Overlay canonical conditions with existing condition ids (by position)
            existing_conds = list(match.get("conditions") or [])
            canon_conds = list(canon.get("conditions", []))
            merged_conds = []
            for i, cc in enumerate(canon_conds):
                mc = dict(cc)
                if i < len(existing_conds):
                    mc["id"] = existing_conds[i]["id"]
                # If no existing condition id available, omit id (new condition)
                merged_conds.append(mc)
            merged["conditions"] = merged_conds
            result.append(merged)
        else:
            # No existing entry left — send without id (new creation)
            result.append(canon)

    return result


_REQUIRED_VALUE_NAMES = {
    _VAL_PAYABLE, _VAL_PURCHASE, _VAL_IGST, _VAL_CGST, _VAL_SGST,
    _VAL_ROUNDOFF_DR, _VAL_ROUNDOFF_CR,
}

# AT endpoint uses the AT record id (not the AD id)
_AT_RECORD_ID = 1


def validate_ad(existing_data: dict) -> list[str]:
    """
    Check that all required value_names are present in the existing AD.
    Returns a list of missing value_name strings (empty = all good).
    """
    details = existing_data.get("accounting_definition_detail") or []
    present = {str(d.get("value_name", "")) for d in details}
    return sorted(_REQUIRED_VALUE_NAMES - present)


# ── Accounting Template helpers ───────────────────────────────────────────────

def _fetch_at(client: RhythmERPAPIClient) -> dict:
    """Fetch the Accounting Template master record."""
    r = client.session.get(
        f"{client.BASE_URL}/core/dynamic-screen-wrapper/{_AT_RECORD_ID}/",
        timeout=15,
    )
    if r.status_code != 200:
        raise RuntimeError(f"AT fetch failed: HTTP {r.status_code}")
    return r.json()


def _put_at(client: RhythmERPAPIClient, at: dict) -> None:
    """PUT the Accounting Template back (minimal body, no schemas needed)."""
    body = {
        "id": at["id"],
        "create_version": False,
        "accounting_template_name": at["accounting_template_name"],
        "ledger_group_ref_id": at["ledger_group_ref_id"],
        "attribute_name": at["attribute_name"],
        "children": [
            {
                "stepper_name": child["stepper_name"],
                "children": [],
                "details": [
                    {"accounting_definition_id": d["accounting_definition_id"], "id": d["id"]}
                    for d in child.get("details", [])
                ],
            }
            for child in at.get("children", [])
        ],
    }
    r = client.session.put(
        f"{client.BASE_URL}/core/dynamic-screen-wrapper/{_AT_RECORD_ID}/",
        json=body,
        timeout=30,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"AT PUT failed: HTTP {r.status_code} — {r.text[:200]}")


def _at_child(at: dict) -> dict:
    """Return the first (only) child stepper of the AT."""
    children = at.get("children") or []
    if not children:
        raise RuntimeError("AT has no children — unexpected structure")
    return children[0]


def fix_ad_via_at_flow(
    client: RhythmERPAPIClient,
    canonical_payload: dict,
    existing_id: int,
    existing_details: list[dict],
    missing_value_names: list[str],
    dry_run: bool,
) -> None:
    """
    Fix the PB AD by temporarily detaching it from the Accounting Template:
      1. Fetch AT → remove PB row → PUT AT  (unlocks AD for new rows)
      2. Build merged detail list: keep ALL existing rows + append missing canonical rows
      3. PUT the AD
      4. Fetch AT again → re-add PB row → PUT AT  (re-locks)
    """
    print(f"\n  Auto-fix via AT flow — missing value_names: {missing_value_names}")

    # ── Step 1: fetch AT and detach PB ───────────────────────────────────────
    at = _fetch_at(client)
    child = _at_child(at)
    all_details = child.get("details", [])

    pb_rows = [d for d in all_details if d.get("accounting_definition_id") == existing_id]
    without_pb = [d for d in all_details if d.get("accounting_definition_id") != existing_id]

    if dry_run:
        print(f"  [DRY RUN] Would remove PB row(s) {[d['id'] for d in pb_rows]} from AT")
    else:
        child["details"] = without_pb
        _put_at(client, at)
        print(f"  Detached PB (AD id={existing_id}) from AT")

    # ── Step 2: build merged AD detail list ──────────────────────────────────
    # Keep ALL existing rows (preserves tenant-specific entries like Labour/Transport).
    # Append only canonical rows whose value_name is missing from existing.
    existing_value_names = {str(d.get("value_name", "")) for d in existing_details}
    canonical_details = canonical_payload.get("accounting_definition_detail", [])
    new_rows = [
        c for c in canonical_details
        if str(c.get("value_name", "")) in missing_value_names
        and str(c.get("value_name", "")) not in existing_value_names
    ]

    merged_details = list(existing_details) + new_rows

    ad_body = {
        "id": existing_id,
        "name": canonical_payload["name"],
        "transaction_type": canonical_payload["transaction_type"],
        "accounting_definition_detail": merged_details,
    }

    if dry_run:
        print(f"  [DRY RUN] Would PUT AD id={existing_id} with {len(merged_details)} entries "
              f"(+{len(new_rows)} new)")
        print(json.dumps(ad_body, indent=2))
    else:
        r = client.session.put(
            f"{client.BASE_URL}/core/accounting-definition/{existing_id}/",
            json=ad_body,
            timeout=30,
        )
        if r.status_code not in (200, 201):
            raise RuntimeError(f"AD PUT failed: HTTP {r.status_code} — {r.text[:200]}")
        print(f"  AD id={existing_id} updated — added {len(new_rows)} row(s)")

    # ── Step 3: re-attach PB to AT ────────────────────────────────────────────
    # Re-fetch AT to get the latest state (new AT detail ids from re-created rows)
    at2 = _fetch_at(client)
    child2 = _at_child(at2)
    current_details = child2.get("details", [])
    already_attached = any(d.get("accounting_definition_id") == existing_id for d in current_details)

    if not already_attached:
        # Add PB row back — send without id so ERP creates a new AT detail row
        current_details.append({"accounting_definition_id": existing_id})
        child2["details"] = current_details

        if dry_run:
            print(f"  [DRY RUN] Would re-attach AD id={existing_id} to AT")
        else:
            _put_at(client, at2)
            print(f"  Re-attached PB (AD id={existing_id}) to AT")
    else:
        print(f"  PB already attached to AT — skipping re-attach")


def apply_ad(client: RhythmERPAPIClient, payload: dict, existing_id: int | None, dry_run: bool) -> None:
    import copy

    if existing_id:
        existing_data = _fetch_existing_ad(client, existing_id)
        missing = validate_ad(existing_data)
        if not missing:
            print(f"\n  AD id={existing_id} already has all required entries — no changes needed.")
            return
        # Auto-fix via AT detach → AD PUT → AT re-attach
        fix_ad_via_at_flow(
            client=client,
            canonical_payload=copy.deepcopy(payload),
            existing_id=existing_id,
            existing_details=existing_data.get("accounting_definition_detail") or [],
            missing_value_names=missing,
            dry_run=dry_run,
        )
        return

    # AD doesn't exist yet — create it
    send_payload = copy.deepcopy(payload)

    if dry_run:
        print(f"\n[DRY RUN] Would POST /core/accounting-definition/")
        print(json.dumps(send_payload, indent=2))
        return

    url = f"{client.BASE_URL}/core/accounting-definition/"
    r = client.session.post(url, json=send_payload, timeout=30)
    if r.status_code in (200, 201):
        result = r.json()
        print(f"\n  Created AD id={result.get('id')} '{payload['name']}'")
    else:
        print(f"\n  ERROR: HTTP {r.status_code}")
        print(f"  {r.text[:500]}")
        raise RuntimeError(f"AD create failed: HTTP {r.status_code} — {r.text[:200]}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Set up Purchase Booking Accounting Definition")
    parser.add_argument("--token",   required=True, help="ERP JWT token")
    parser.add_argument("--tenant",  required=True, help="Tenant ID")
    parser.add_argument("--dry-run", action="store_true", help="Print payload, do not write")
    args = parser.parse_args()

    client = RhythmERPAPIClient()
    client.login_from_browser(token=args.token, tenant_id=args.tenant)

    sep = "-" * 60
    print(f"\n{sep}")
    print(f"  AD Setup — tenant {args.tenant}")
    print(sep)

    # ── Resolve accounts
    print("\nResolving Chart of Accounts...")
    coa = fetch_coa(client)
    print(f"  {len(coa)} accounts found")
    accounts = resolve_accounts(coa)
    for name, aid in accounts.items():
        print(f"    {name:30s} -> id={aid}")

    # ── Type of Sale IDs
    print("\nResolving Type of Sale options (parameter6)...")
    tos_ids = fetch_type_of_sale_ids(client)
    print(f"  IDs: {tos_ids}")

    # ── Find existing AD
    print("\nChecking existing Accounting Definition...")
    existing = find_existing_pb_ad(client)
    if existing:
        print(f"  Found: id={existing['id']} name='{existing.get('name')}' — will replace")
    else:
        print("  Not found — will create new")

    existing_id = existing["id"] if existing else None

    # ── Build payload
    payload = build_ad_payload(accounts, tos_ids)

    # ── Apply
    apply_ad(client, payload, existing_id, dry_run=args.dry_run)

    if not args.dry_run:
        print(f"\n{sep}")
        print("  Done. Run batch_create.py --dry-run to verify AD filter passes.")
        print(sep)


if __name__ == "__main__":
    main()
