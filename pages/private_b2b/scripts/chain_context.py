"""
chain_context.py
----------------
Discovers tenant-specific FK IDs from the live ERP API before running
the purchase chain. Every ID that was previously hardcoded in the data
files is resolved here by querying the same dropdown/list endpoints that
the Angular frontend uses.

Usage:
    ctx = ChainContextDiscoverer(client).discover()
    chain = PurchaseChain(client=client)
    chain.run(ctx=ctx, ...)
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log

# Screen names as registered in the ERP
_PO_SCREEN  = "Purchase Order"
_GP_SCREEN  = "Gate Pass"
_GRN_SCREEN = "Goods Receipt Note"
_QC_SCREEN  = "QC"


@dataclass
class ChainContext:
    """All tenant-specific IDs needed to build one full PO→GP→GRN→QC chain."""

    # ── Shared ───────────────────────────────────────────────────────────
    supplier_ref_id:   int
    item_ref_id:       int
    item_type_ref_id:  int   # po_item_type / item_type_ref_id
    hsn_sac_no:        int
    alternate_uom:     int   # e.g. QUIN — used in PO/GP/GRN/QC alternate qty
    base_uom:          int   # e.g. MT/KG — used as transaction UOM in GRN/QC

    # ── PO-specific ───────────────────────────────────────────────────────
    po_type:           int
    base_currency:     int
    txn_currency:      int
    parameter1:        int   # Division
    parameter2:        int   # Department
    parameter5:        int   # Type of Sale
    parameter6:        int   # Location
    payment_terms:     int
    delivery_terms:    int
    packing_forwarding: int
    supplier_ship_from: int
    supplier_bill_from: int

    # ── GP-specific ───────────────────────────────────────────────────────
    delivery_type:     int

    # ── PB-specific ───────────────────────────────────────────────────────
    supplier_ref_type: str = "Supplier"   # Role Type name string expected by PB ERP field
    pb_payment_terms: Optional[int] = None  # Payment terms from PB dropdown (may differ from PO)

    # ── QC-specific ───────────────────────────────────────────────────────
    quality_parameters: List[dict] = field(default_factory=list)
    # [{item_quality_parameter_ref_id: int, actual_value: 1}, ...]


class ChainContextDiscoverer:
    """
    Queries the ERP API to build a ChainContext for the authenticated tenant.

    Strategy per field type:
      - Dropdown fields (PO Type, Currency, Delivery Type, etc.):
          Read filter_dropdown_raw_query from the screen schema.
      - Entity FK fields (Supplier, Item, UOM, HSN/SAC, Quality Params):
          Call list_entries on the relevant screen and take the first result.

    All calls are best-effort — if a field cannot be resolved, a warning is
    logged and the hardcoded fallback from the old data files is used. This
    means the script still works on the original dev tenant even without data.
    """

    # Fallback IDs (tenant-711 values). Used only when discovery fails.
    _FALLBACKS = {
        "supplier_ref_id":    9,
        "item_ref_id":        5,
        "item_type_ref_id":   113,
        "hsn_sac_no":         2,
        "alternate_uom":      3,
        "base_uom":           4,
        "po_type":            24,
        "base_currency":      8,
        "txn_currency":       8,
        "parameter1":         1,
        "parameter2":         1,
        "parameter5":         1,
        "parameter6":         1,
        "payment_terms":      549,
        "delivery_terms":     130,
        "packing_forwarding": 89,
        "supplier_ship_from": 17,
        "supplier_bill_from": 18,
        "delivery_type":      29,
        "supplier_ref_type":  "Supplier",   # default role type name
    }

    def __init__(self, client: RhythmERPAPIClient):
        self.client = client
        self._schema_cache: dict = {}

    # ── Public ────────────────────────────────────────────────────────────

    def discover(self, item_category_id: Optional[int] = None) -> ChainContext:
        """Run all discovery calls and return a fully-populated ChainContext."""
        log.info("[Discovery] Discovering tenant FK IDs from ERP API...")

        accounting_item_ids = self._discover_accounting_item_ids()

        ctx = ChainContext(
            supplier_ref_id    = self._list_first_id("Supplier",                "supplier_ref_id"),
            item_ref_id        = self._item_ref_id_filtered(accounting_item_ids),
            item_type_ref_id   = self._dropdown_po_item_type(_PO_SCREEN,  "po_item_type",     "item_type_ref_id", item_category_id),
            hsn_sac_no         = self._schema_or_list("HSN SAC",                 _PO_SCREEN, "hsn_sac_no"),
            alternate_uom      = self._dropdown(_PO_SCREEN,  "alternate_uom",    "alternate_uom"),
            base_uom           = self._dropdown(_PO_SCREEN,  "uom",              "base_uom"),
            po_type            = self._dropdown(_PO_SCREEN,  "po_type",          "po_type"),
            base_currency      = self._dropdown(_PO_SCREEN,  "base_currency",    "base_currency"),
            txn_currency       = self._dropdown(_PO_SCREEN,  "txn_currency",     "txn_currency"),
            parameter1         = self._dropdown(_PO_SCREEN,  "parameter1",       "parameter1"),
            parameter2         = self._dropdown(_PO_SCREEN,  "parameter2",       "parameter2"),
            parameter5         = self._dropdown(_PO_SCREEN,  "parameter5",       "parameter5"),
            parameter6         = self._dropdown(_PO_SCREEN,  "parameter6",       "parameter6"),
            payment_terms      = self._dropdown(_PO_SCREEN,  "supplier_payment_terms",    "payment_terms"),
            delivery_terms     = self._dropdown(_PO_SCREEN,  "supplier_delivery_terms",   "delivery_terms"),
            packing_forwarding = self._dropdown(_PO_SCREEN,  "packing_forwarding_ref_id", "packing_forwarding"),
            supplier_ship_from = self._dropdown(_PO_SCREEN,  "supplier_ship_from",        "supplier_ship_from"),
            supplier_bill_from = self._dropdown(_PO_SCREEN,  "supplier_bill_from",        "supplier_bill_from"),
            delivery_type      = self._dropdown(_GP_SCREEN,  "delivery_type",    "delivery_type"),
            supplier_ref_type  = self._discover_supplier_ref_type(),
            pb_payment_terms   = self._dropdown_or_none("Purchase Booking", "supplier_payment_terms_ref_id"),
            quality_parameters = self._discover_quality_params(),
        )

        log.info(
            f"[Discovery] Done — supplier={ctx.supplier_ref_id}, "
            f"item={ctx.item_ref_id}, alt_uom={ctx.alternate_uom}, "
            f"base_uom={ctx.base_uom}, hsn={ctx.hsn_sac_no}, "
            f"po_type={ctx.po_type}, currency={ctx.txn_currency}, "
            f"delivery_type={ctx.delivery_type}, "
            f"qc_params={len(ctx.quality_parameters)}"
        )
        return ctx

    # ── Private helpers ───────────────────────────────────────────────────

    def _fb(self, key: str) -> Optional[int]:
        """Return the hardcoded fallback for *key*, with a warning."""
        val = self._FALLBACKS.get(key)
        log.warning(f"[Discovery] Using fallback for '{key}': {val}")
        return val

    def _schema(self, screen_name: str) -> dict:
        if screen_name not in self._schema_cache:
            result = self.client.get_screen_schema(screen_name)
            self._schema_cache[screen_name] = result or {}
        return self._schema_cache[screen_name]

    def _dropdown(self, screen_name: str, field_key: str, fb_key: str) -> int:
        """
        Return the first ID from a field's filter_dropdown_raw_query.
        Falls back to _FALLBACKS[fb_key] if no options found.
        """
        try:
            opts = self.client.get_dropdown_options(screen_name, field_key)
            if opts:
                first_id = opts[0].get("id")
                if first_id is not None:
                    log.info(
                        f"[Discovery] {screen_name}.{field_key} → {first_id} "
                        f"({opts[0].get('key', '')})"
                    )
                    return int(first_id)
        except Exception as e:
            log.warning(f"[Discovery] Schema error for {screen_name}.{field_key}: {e}")
        return self._fb(fb_key)

    def _dropdown_po_item_type(self, screen_name: str, field_key: str, fb_key: str, item_category_id: Optional[int] = None) -> int:
        """
        Return the po_item_type ID matching the selected item_category_id.
        Falls back to first dropdown option if item_category_id is None or not found.
        Falls back to _FALLBACKS[fb_key] if no options found.
        """
        try:
            opts = self.client.get_dropdown_options(screen_name, field_key)
            if not opts:
                return self._fb(fb_key)
            
            # If item_category_id is provided, find the matching po_item_type
            if item_category_id is not None:
                for opt in opts:
                    # The dropdown option key/label may contain the category ID or name
                    # We need to match by the actual category ID
                    opt_id = opt.get("id")
                    if opt_id is not None and int(opt_id) == int(item_category_id):
                        log.info(
                            f"[Discovery] {screen_name}.{field_key} matched category {item_category_id} → {opt_id} "
                            f"({opt.get('key', '')})"
                        )
                        return int(opt_id)
            
            # Fallback: use first option
            first_id = opts[0].get("id")
            if first_id is not None:
                log.info(
                    f"[Discovery] {screen_name}.{field_key} → first option {first_id} "
                    f"({opts[0].get('key', '')})"
                )
                return int(first_id)
        except Exception as e:
            log.warning(f"[Discovery] Schema error for {screen_name}.{field_key}: {e}")
        return self._fb(fb_key)

    def _list_first_id(self, screen_name: str, fb_key: str) -> int:
        """Return the first ID from list_entries for *screen_name*."""
        try:
            resp = self.client.list_entries(screen_name, page=1, page_size=5)
            if resp:
                items = resp.get("screenmatlistingdata_set") or []
                if items:
                    first_id = items[0].get("id")
                    if first_id is not None:
                        label = (
                            items[0].get("name")
                            or items[0].get("company_name")
                            or items[0].get("code")
                            or ""
                        )
                        log.info(f"[Discovery] {screen_name}[0] → {first_id} ({label})")
                        return int(first_id)
        except Exception as e:
            log.warning(f"[Discovery] List error for {screen_name}: {e}")
        return self._fb(fb_key)

    def _schema_or_list(self, list_screen: str, schema_screen: str, field_key: str) -> int:
        """
        Try schema dropdown first (fast, no extra request if schema cached).
        If empty, fall back to list_entries on *list_screen*.
        """
        try:
            opts = self.client.get_dropdown_options(schema_screen, field_key)
            if opts:
                first_id = opts[0].get("id")
                if first_id is not None:
                    log.info(
                        f"[Discovery] {schema_screen}.{field_key} (dropdown) "
                        f"→ {first_id} ({opts[0].get('key', '')})"
                    )
                    return int(first_id)
        except Exception:
            pass
        # Fall back to listing the dedicated screen
        return self._list_first_id(list_screen, field_key)

    def _dropdown_or_none(self, screen_name: str, field_key: str) -> Optional[int]:
        """Return the first dropdown option ID, or None if unavailable."""
        try:
            opts = self.client.get_dropdown_options(screen_name, field_key)
            if opts:
                first_id = opts[0].get("id")
                if first_id is not None:
                    log.info(f"[Discovery] {screen_name}.{field_key} → {first_id} ({opts[0].get('key', '')})")
                    return int(first_id)
        except Exception as e:
            log.warning(f"[Discovery] {screen_name}.{field_key}: {e}")
        return None

    def _discover_accounting_item_ids(self) -> set:
        """
        Fetch the items allowed by the Accounting Definition's Item Name filter.
        Endpoint: GET /core/dynamic-data/get_dynamic_details_data/
                  ?tbl_name=transaction_type_details&field_name=description
                  &parent_id=5&field_value=Item%20Name&flag=1
        Returns a set of int item IDs, or empty set on failure (no filtering).
        """
        try:
            resp = self.client.session.get(
                f"{self.client.BASE_URL}/core/dynamic-data/get_dynamic_details_data/",
                params={
                    "tbl_name": "transaction_type_details",
                    "field_name": "description",
                    "parent_id": "5",
                    "field_value": "Item Name",
                    "flag": "1",
                },
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list):
                    det = data[0].get("det_query_result") or []
                    ids = {int(r["id"]) for r in det if r.get("id") is not None}
                    log.info(f"[Discovery] Accounting definition item IDs: {sorted(ids)}")
                    return ids
        except Exception as e:
            log.warning(f"[Discovery] Could not fetch accounting item IDs: {e}")
        return set()

    def _item_ref_id_filtered(self, allowed_ids: set) -> int:
        """
        Return the first Item Master ID that is in *allowed_ids*.
        Falls back to _schema_or_list behaviour (first available) when
        allowed_ids is empty or nothing matches.
        """
        try:
            resp = self.client.list_entries("Item Master", page=1, page_size=50)
            if resp:
                items = resp.get("screenmatlistingdata_set") or []
                if allowed_ids:
                    for it in items:
                        iid = it.get("id")
                        if iid is not None and int(iid) in allowed_ids:
                            log.info(
                                f"[Discovery] item_ref_id (accounting-filtered) "
                                f"→ {iid} ({it.get('name', '')})"
                            )
                            return int(iid)
                    log.warning(
                        "[Discovery] No Item Master entry matched accounting definition IDs — "
                        "falling back to first available"
                    )
                if items:
                    first_id = items[0].get("id")
                    if first_id is not None:
                        log.info(f"[Discovery] item_ref_id (first) → {first_id} ({items[0].get('name', '')})")
                        return int(first_id)
        except Exception as e:
            log.warning(f"[Discovery] item_ref_id_filtered error: {e}")
        return self._schema_or_list("Item Master", _PO_SCREEN, "item_ref_id")

    def _discover_supplier_ref_type(self) -> str:
        """
        Return the role type NAME (string) for the first supplier in the list.
        The PB ERP field expects a string like "Supplier" or "Farmer", not an ID.
        We look at the supplier listing for a role_type/supplier_type field;
        if we can't find it we default to "Supplier".
        """
        _ROLE_TYPE_NAMES = {
            1769: "Farmer",
            1771: "Supplier",
            1770: "Customer",
            1814: "Operator",
            1855: "Agent",
        }
        try:
            resp = self.client.list_entries("Supplier", page=1, page_size=5)
            if resp:
                items = resp.get("screenmatlistingdata_set") or []
                if items:
                    first = items[0]
                    # Try common field names for role type
                    for field in ("role_type", "supplier_type", "type", "party_type"):
                        val = first.get(field)
                        if val is not None:
                            if isinstance(val, int) and val in _ROLE_TYPE_NAMES:
                                name = _ROLE_TYPE_NAMES[val]
                                log.info(f"[Discovery] supplier_ref_type from listing.{field}={val} → '{name}'")
                                return name
                            if isinstance(val, str) and val:
                                log.info(f"[Discovery] supplier_ref_type from listing.{field} → '{val}'")
                                return val
        except Exception as e:
            log.warning(f"[Discovery] Could not discover supplier_ref_type: {e}")
        log.info("[Discovery] supplier_ref_type → 'Supplier' (default)")
        return "Supplier"

    def _discover_quality_params(self) -> List[dict]:
        """
        Return up to 3 quality parameter dicts for QC items.
        Tries several common screen name variants.
        """
        candidate_screens = [
            "Item Quality Parameter",
            "ItemQualityParameter",
            "Quality Parameter",
            "Item Quality",
        ]
        for sname in candidate_screens:
            try:
                resp = self.client.list_entries(sname, page=1, page_size=10)
                if resp:
                    items = resp.get("screenmatlistingdata_set") or []
                    if items:
                        params = [
                            {"item_quality_parameter_ref_id": it["id"], "actual_value": 1}
                            for it in items[:3]
                        ]
                        log.info(
                            f"[Discovery] Quality params from '{sname}': "
                            f"{[p['item_quality_parameter_ref_id'] for p in params]}"
                        )
                        return params
            except Exception:
                continue

        # Last resort: try reading from QC schema
        try:
            opts = self.client.get_dropdown_options(
                _QC_SCREEN, "item_quality_parameter_ref_id"
            )
            if opts:
                params = [
                    {"item_quality_parameter_ref_id": o["id"], "actual_value": 1}
                    for o in opts[:3]
                ]
                log.info(
                    f"[Discovery] Quality params from QC schema: "
                    f"{[p['item_quality_parameter_ref_id'] for p in params]}"
                )
                return params
        except Exception:
            pass

        # Absolute fallback — IDs that exist on the dev tenant
        log.warning("[Discovery] Could not discover quality params — using fallback [1,2,3]")
        return [
            {"item_quality_parameter_ref_id": 1, "actual_value": 1},
            {"item_quality_parameter_ref_id": 2, "actual_value": 1},
            {"item_quality_parameter_ref_id": 3, "actual_value": 1},
        ]
