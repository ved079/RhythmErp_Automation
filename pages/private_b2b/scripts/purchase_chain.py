"""
Purchase Chain — creates a linked PO -> Gate Pass -> GRN -> QC chain
for the same supplier.

Usage:
    python -m pages.private_b2b.scripts.purchase_chain --supplier 1 --count 3
    python -m pages.private_b2b.scripts.purchase_chain --supplier 1 --dry-run
    python -m pages.private_b2b.scripts.purchase_chain --supplier 1 --delay 1.0
"""

import argparse
import json
import os
import sys
import time
from datetime import date
from typing import Dict, List, Optional

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    ITEM_NAMES as PO_ITEM_NAMES,
    UOM_NAMES as PO_UOM_NAMES,
    HSN_SAC_NAMES as PO_HSN_NAMES,
    PO_ITEM_TYPE_NAMES,
    PO_TYPE_NAMES,
    PAYMENT_TERMS_NAMES,
    DELIVERY_TERMS_NAMES,
    PACKING_FORWARDING_NAMES,
    CURRENCY_NAMES as PO_CURRENCY_NAMES,
    DEPARTMENT_NAMES,
    DIVISION_NAMES,
    LOCATION_NAMES,
    TYPE_OF_SALE_NAMES,
)
from pages.private_b2b.modules.gate_pass.data.gate_pass_data import (
    DELIVERY_TYPE_NAMES,
    ITEM_NAMES as GP_ITEM_NAMES,
)
from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import (
    ITEM_NAMES as GRN_ITEM_NAMES,
    UOM_NAMES as GRN_UOM_NAMES,
    HSN_SAC_NAMES as GRN_HSN_NAMES,
)
from pages.private_b2b.modules.quality_check.data.quality_check_data import (
    ITEM_NAMES as QC_ITEM_NAMES,
    QUALITY_PARAMETER_NAMES,
)
from pages.private_b2b.modules.purchase_order.utils.api_purchase_order_utils import (
    POAPIUtils,
)
from pages.private_b2b.modules.gate_pass.utils.api_gate_pass_utils import (
    GPAPIUtils,
)
from pages.private_b2b.modules.goods_receipt_note.utils.api_goods_receipt_note_utils import (
    GRNAPIUtils,
)
from pages.private_b2b.modules.quality_check.utils.api_quality_check_utils import (
    QCAPIUtils,
)
from pages.private_b2b.modules.purchase_booking.utils.api_purchase_booking_utils import (
    PBAPIUtils,
)
from pages.private_b2b.scripts.chain_context import ChainContext, ChainContextDiscoverer


# ---------------------------------------------------------------------------
# Supplier lookup
# ---------------------------------------------------------------------------
SUPPLIER_NAMES = {
    1: "Maa Kalinga Commodities",
    2: "Maha Ganga Grain Processors",
    3: "Maa Ganesh Commodities & Sons",
    4: "Guru Agro Commodities & Sons",
    5: "Baba Rajput Supply Chain",
    6: "Jagdamba Yamuna Cotton Mills Corp",
    7: "Maa Sutlej Produce Associates",
    8: "Jagdamba Yamuna Commodities Pvt Ltd",
    9: "Hari Ganesh Grain Processors",
    10: "Om Maurya Oil Mills & Bros",
}


def _supplier_name(sid: int) -> str:
    return SUPPLIER_NAMES.get(sid, f"Supplier_{sid}")


# ---------------------------------------------------------------------------
# Item generator — produces items that work across PO / GP / GRN
# ---------------------------------------------------------------------------
def _generate_chain_items(
    num_items: int = 2,
    item_ref_id: int = 5,
    item_ref_ids: Optional[List[int]] = None,
    hsn_sac_no: int = 2,
    uom: int = 3,
    base_uom: int = 4,
    alternate_uom: int = 4,
) -> List[dict]:
    today = date.today().isoformat()
    ids = item_ref_ids if item_ref_ids else [item_ref_id]
    items = []
    for i in range(num_items):
        qty = 10.0 * (i + 1)
        rate = 100.0 * (i + 1)
        items.append({
            "item_ref_id": ids[i % len(ids)],
            "hsn_sac_no": hsn_sac_no,
            "uom": uom,
            "base_uom": base_uom,
            "alternate_uom": alternate_uom,
            "alternate_quantity": "1",
            "quantity": qty,
            "rate": rate,
            "no_of_bags": int(qty),
            "expected_delivery_date": today,
            "received_qty": qty,
            "accepted_qty": qty,
            "rejected_qty": 0.0,
        })
    return items


def _po_items_from(items: List[dict]) -> List[dict]:
    return [
        {
            "item_ref_id": it["item_ref_id"],
            "hsn_sac_no": it["hsn_sac_no"],
            "uom": it["uom"],
            "alternate_uom": it.get("alternate_uom"),
            "alternate_quantity": it.get("alternate_quantity", "1"),
            "quantity": it["quantity"],
            "rate": it["rate"],
            "expected_delivery_date": it["expected_delivery_date"],
        }
        for it in items
    ]


def _gp_items_from(items: List[dict]) -> List[dict]:
    return [
        {
            "item_ref_id": it["item_ref_id"],
            "no_of_bags": it["no_of_bags"],
            "alternate_quantity": it["quantity"],
            "alternate_uom": it.get("alternate_uom", it.get("uom")),
            "base_uom": it["base_uom"],
            "uom_conversion": 1.0,
            "hsn_sac_no": it["hsn_sac_no"],
        }
        for it in items
    ]


def _grn_items_from(items: List[dict]) -> List[dict]:
    return [
        {
            "item_ref_id": it["item_ref_id"],
            "hsn_sac_no": it["hsn_sac_no"],
            "uom": it.get("base_uom", it["uom"]),
            "alternate_uom": it.get("alternate_uom", it["uom"]),
            "uom_conversion": 1.0,
            "alternate_received_qty": it["quantity"],
            "alternate_accepted_qty": it["accepted_qty"],
            "alternate_rejected_qty": it["rejected_qty"],
            "rate": it["rate"],
            "no_of_bags": it["no_of_bags"],
            "gate_pass_quantity": it["quantity"],
            "po_quantity": None,
        }
        for it in items
    ]


def _qc_items_from(items: List[dict], ctx=None) -> List[dict]:
    quality_details = (
        ctx.quality_parameters if ctx and ctx.quality_parameters
        else [
            {"item_quality_parameter_ref_id": 1, "actual_value": 1},
            {"item_quality_parameter_ref_id": 2, "actual_value": 1},
            {"item_quality_parameter_ref_id": 3, "actual_value": 1},
        ]
    )
    return [
        {
            "item_ref_id": it["item_ref_id"],
            "no_of_bags": it["no_of_bags"],
            "grn_qty": it["accepted_qty"],
            "alternate_accepted_qty": it["accepted_qty"],
            "alternate_rejected_qty": it["rejected_qty"],
            "base_rate": it["rate"],
            "deduction_percent": 0.0,
            "deduction_rate": None,
            "rate": it["rate"],
            "net_rate": it["rate"],
            "alternate_uom": it.get("uom", ctx.alternate_uom if ctx else 3),
            "uom": it.get("base_uom", ctx.base_uom if ctx else 4),
            "hsn_sac_no": it["hsn_sac_no"],
            "uom_conversion": 1.0,
            "details": quality_details,
        }
        for it in items
    ]


def _pb_items_from(items: List[dict], ctx=None) -> List[dict]:
    from pages.private_b2b.modules.purchase_booking.data.purchase_booking_data import build_pb_item
    alt_uom  = ctx.alternate_uom if ctx else 3
    base_uom = ctx.base_uom      if ctx else 4
    return [
        build_pb_item(
            item_ref_id=it["item_ref_id"],
            hsn_sac_no=it["hsn_sac_no"],
            alternate_uom=alt_uom,
            uom=base_uom,
            rate=it["rate"],
            no_of_bags=it["no_of_bags"],
        )
        for it in items
    ]


# ---------------------------------------------------------------------------
# PurchaseChain class
# ---------------------------------------------------------------------------
class PurchaseChain:
    """Create a linked PO -> Gate Pass -> GRN chain for the same supplier.

    Args:
        token: JWT token (takes precedence if given).
        tenant: Tenant ID (default 711).
        client: Pre-authenticated RhythmERPAPIClient (avoids re-auth).
        delay: Seconds between API calls (default 0.3).
    """

    def __init__(
        self,
        token: str = "",
        tenant: str = "711",
        client: Optional[RhythmERPAPIClient] = None,
        delay: float = 0.3,
    ):
        self.delay = delay

        if client is not None:
            self.client = client
        else:
            self.client = RhythmERPAPIClient()
            if token:
                self.client.login_from_browser(token=token, tenant_id=tenant)
            else:
                self.client.login()

        self.po_api = POAPIUtils(self.client)
        self.gp_api = GPAPIUtils(self.client)
        self.grn_api = GRNAPIUtils(self.client)
        self.qc_api = QCAPIUtils(self.client)
        self.pb_api = PBAPIUtils(self.client)

        self.results: List[dict] = []
        self._context: Optional[ChainContext] = None  # discovered lazily

    def get_context(self) -> ChainContext:
        """Return the tenant context, discovering it on first call."""
        if self._context is None:
            self._context = ChainContextDiscoverer(self.client).discover()
        return self._context

    def run(
        self,
        supplier_ref_id: int = None,
        num_items: int = 1,
        item_ref_id: int = None,
        item_ref_ids: Optional[List[int]] = None,
        hsn_sac_no: int = None,
        po_overrides: dict = None,
        gp_overrides: dict = None,
        grn_overrides: dict = None,
        qc_overrides: dict = None,
        pb_overrides: dict = None,
        ctx: Optional[ChainContext] = None,
        documents: Optional[List[str]] = None,
    ) -> dict:
        """Execute one full PO -> GP -> GRN -> QC chain.

        If *ctx* is not given, the context is discovered automatically from
        the ERP API (tenant-safe). Explicit arguments take precedence over
        the discovered context so existing callers are not broken.

        Returns:
            dict with keys ``po``, ``gp``, ``grn``, ``qc`` containing API response data.
        """
        # Resolve context — discover once per PurchaseChain instance
        if ctx is None:
            ctx = self.get_context()

        # Which documents to create — default to full chain
        docs = set(d.upper() for d in documents) if documents else {"PO", "GP", "GRN", "QC"}

        # Explicit args override discovered values
        eff_supplier  = supplier_ref_id if supplier_ref_id is not None else ctx.supplier_ref_id
        eff_item      = item_ref_id     if item_ref_id     is not None else ctx.item_ref_id
        eff_hsn       = hsn_sac_no      if hsn_sac_no      is not None else ctx.hsn_sac_no

        items = _generate_chain_items(
            num_items=num_items,
            item_ref_id=eff_item,
            item_ref_ids=item_ref_ids,
            hsn_sac_no=eff_hsn,
            uom=ctx.alternate_uom,
            base_uom=ctx.base_uom,
            alternate_uom=ctx.alternate_uom,
        )

        po_id = po_ref = po_data = po_payload = po_entry = None
        gp_id = gp_ref = gp_data = gp_payload = None
        grn_id = grn_ref = grn_data = grn_payload = None
        qc_id = qc_ref = qc_data = qc_payload = None
        pb_id = pb_ref = pb_data = pb_payload = None

        # ---------------------------------------------------------------
        # 1. Purchase Order
        # ---------------------------------------------------------------
        if "PO" in docs:
            po_payload = self._build_po_payload(eff_supplier, items, po_overrides, ctx=ctx)
            po_data = self.po_api.create_po(po_payload)
            po_id = po_data.get("id") or po_data.get("entry_id") if po_data else None
            if not po_data or not po_id:
                raise RuntimeError(
                    f"PO creation failed (HTTP {self.po_api._last_status}); "
                    f"response: {po_data}"
                )
            po_ref = po_data.get("transaction_ref_no", str(po_id))
            log.info(f"  PO created: ID={po_id}, ref={po_ref}")

            po_entry = self.po_api.get_po(po_id)
            if po_entry:
                po_items_resp = po_entry.get("purchasing_order_items_details") or []
                sent_items = po_payload.get("purchasing_order_items_details") or []
                rate_ok = True
                for ji, sent in enumerate(sent_items):
                    got = po_items_resp[ji] if ji < len(po_items_resp) else {}
                    sr = float(sent.get("rate", 0) or 0)
                    gr = float(got.get("rate", 0) or 0)
                    if abs(sr - gr) > 0.01:
                        log.warning(f"  PO rate mismatch item[{ji}]: sent={sr}, backend={gr}")
                        rate_ok = False
                    else:
                        log.info(f"  PO rate OK item[{ji}]: rate={gr}")
                if rate_ok and po_items_resp:
                    for ji, item in enumerate(items):
                        if ji < len(po_items_resp):
                            confirmed = float(po_items_resp[ji].get("rate", 0) or 0)
                            if confirmed > 0:
                                items[ji]["rate"] = confirmed
            else:
                log.warning(f"  Could not fetch PO #{po_id} back — using sent rates")

            if self.delay:
                time.sleep(self.delay)

        # ---------------------------------------------------------------
        # 2. Gate Pass
        # ---------------------------------------------------------------
        if "GP" in docs:
            gp_payload = self._build_gp_payload(eff_supplier, items, gp_overrides, ctx=ctx)
            gp_data = self.gp_api.create_gp(gp_payload)
            gp_id = gp_data.get("id") or gp_data.get("entry_id") if gp_data else None
            if not gp_data or not gp_id:
                raise RuntimeError(
                    f"GP creation failed (HTTP {self.gp_api._last_status}); "
                    f"response: {gp_data}"
                )
            gp_ref = gp_data.get("transaction_ref_no", str(gp_id))
            log.info(f"  GP created: ID={gp_id}, ref={gp_ref}")
            if self.delay:
                time.sleep(self.delay)

        # ---------------------------------------------------------------
        # 3. GRN
        # ---------------------------------------------------------------
        if "GRN" in docs:
            grn_payload = self._build_grn_payload(
                eff_supplier, po_id, gp_id, items, grn_overrides, ctx=ctx
            )
            grn_data = self.grn_api.create_grn(grn_payload)
            grn_id = grn_data.get("id") or grn_data.get("entry_id") if grn_data else None
            if not grn_data or not grn_id:
                raise RuntimeError(
                    f"GRN creation failed (HTTP {self.grn_api._last_status}); "
                    f"response: {grn_data}"
                )
            grn_ref = grn_data.get("transaction_ref_no", str(grn_id))
            log.info(f"  GRN created: ID={grn_id}, ref={grn_ref}")
            if self.delay:
                time.sleep(self.delay)

        # ---------------------------------------------------------------
        # 4. Quality Check
        # ---------------------------------------------------------------
        if "QC" in docs:
            qc_payload = self._build_qc_payload(
                eff_supplier, po_id, gp_id, grn_id, items, qc_overrides, ctx=ctx
            )
            qc_data = self.qc_api.create_qc(qc_payload)
            qc_id = qc_data.get("id") or qc_data.get("entry_id") if qc_data else None
            if not qc_data or not qc_id:
                raise RuntimeError(
                    f"QC creation failed (HTTP {self.qc_api._last_status}); "
                    f"response: {qc_data}"
                )
            qc_ref = qc_data.get("transaction_ref_no", str(qc_id))
            log.info(f"  QC created: ID={qc_id}, ref={qc_ref}")
            if self.delay:
                time.sleep(self.delay)

        # ---------------------------------------------------------------
        # 5. Purchase Booking
        # ---------------------------------------------------------------
        if "PB" in docs:
            pb_payload = self._build_pb_payload(
                eff_supplier, qc_id, grn_id, po_id, items, pb_overrides, ctx=ctx
            )
            log.info(f"  PB payload (first 800 chars): {json.dumps(pb_payload, default=str)[:800]}")
            pb_data = self.pb_api.create_pb(pb_payload)
            pb_id = pb_data.get("id") or pb_data.get("entry_id") if pb_data else None
            if not pb_data or not pb_id:
                _pb_resp = self.pb_api._last_response
                _pb_body = _pb_resp.text[:400] if _pb_resp is not None else "no response"
                _sent = json.dumps(pb_payload, default=str)[:600]
                raise RuntimeError(
                    f"PB creation failed (HTTP {self.pb_api._last_status}); "
                    f"body: {_pb_body} | sent: {_sent}"
                )
            pb_ref = pb_data.get("transaction_ref_no", str(pb_id))
            log.info(f"  PB created: ID={pb_id}, ref={pb_ref}")

        result = {
            "po": {"id": po_id, "ref": po_ref, "data": po_data, "payload": po_payload,
                   "fetched": po_entry} if po_id else None,
            "gp": {"id": gp_id, "ref": gp_ref, "data": gp_data, "payload": gp_payload} if gp_id else None,
            "grn": {"id": grn_id, "ref": grn_ref, "data": grn_data, "payload": grn_payload} if grn_id else None,
            "qc": {"id": qc_id, "ref": qc_ref, "data": qc_data, "payload": qc_payload} if qc_id else None,
            "pb": {"id": pb_id, "ref": pb_ref, "data": pb_data, "payload": pb_payload} if pb_id else None,
        }
        self.results.append(result)
        return result

    def run_multiple(
        self,
        count: int,
        supplier_ref_id: int = 1,
        **overrides,
    ) -> List[dict]:
        """Execute *count* chains sequentially."""
        chains = []
        for i in range(count):
            log.info(f"\nChain [{i + 1}/{count}] - supplier={supplier_ref_id}")
            result = self.run(supplier_ref_id=supplier_ref_id, **overrides)
            chains.append(result)
        return chains

    # ------------------------------------------------------------------
    # Payload builders
    # ------------------------------------------------------------------
    @staticmethod
    def _build_po_payload(
        supplier_ref_id: int,
        items: List[dict],
        overrides: dict = None,
        ctx: Optional[ChainContext] = None,
    ) -> dict:
        from pages.private_b2b.modules.purchase_order.data.purchase_order_data import build_po_payload
        po_items = _po_items_from(items)
        overrides = overrides or {}
        if ctx:
            return build_po_payload(
                supplier_ref_id=supplier_ref_id,
                items=po_items,
                po_item_type=ctx.item_type_ref_id,
                po_type=ctx.po_type,
                txn_currency=ctx.txn_currency,
                base_currency=ctx.base_currency,
                parameter1=ctx.parameter1,
                parameter2=ctx.parameter2,
                parameter5=ctx.parameter5,
                parameter6=ctx.parameter6,
                supplier_details={
                    "supplier_payment_terms": ctx.payment_terms,
                    "supplier_delivery_terms": ctx.delivery_terms,
                    "packing_forwarding_ref_id": ctx.packing_forwarding,
                    "supplier_ship_from": ctx.supplier_ship_from,
                    "supplier_bill_from": ctx.supplier_bill_from,
                },
                **overrides,
            )
        # Legacy path — no context (uses data-file defaults)
        import random
        from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
            PO_TYPE_IDS, CURRENCY_IDS, DIVISION_IDS, DEPARTMENT_IDS,
            TYPE_OF_SALE_IDS, LOCATION_IDS,
            PAYMENT_TERMS_IDS, DELIVERY_TERMS_IDS, PACKING_FORWARDING_IDS,
            SUPPLIER_SHIP_FROM_IDS, SUPPLIER_BILL_FROM_IDS,
        )
        return build_po_payload(
            supplier_ref_id=supplier_ref_id,
            items=po_items,
            po_item_type=113,
            po_type=random.choice(PO_TYPE_IDS),
            txn_currency=random.choice(CURRENCY_IDS),
            base_currency=random.choice(CURRENCY_IDS),
            parameter1=random.choice(DIVISION_IDS),
            parameter2=random.choice(DEPARTMENT_IDS),
            parameter5=2,
            parameter6=1,
            supplier_details={
                "supplier_payment_terms": random.choice(PAYMENT_TERMS_IDS),
                "supplier_delivery_terms": random.choice(DELIVERY_TERMS_IDS),
                "packing_forwarding_ref_id": random.choice(PACKING_FORWARDING_IDS),
                "supplier_ship_from": random.choice(SUPPLIER_SHIP_FROM_IDS),
                "supplier_bill_from": random.choice(SUPPLIER_BILL_FROM_IDS),
            },
            **overrides,
        )

    @staticmethod
    def _build_gp_payload(
        supplier_ref_id: int,
        items: List[dict],
        overrides: dict = None,
        ctx: Optional[ChainContext] = None,
    ) -> dict:
        from pages.private_b2b.modules.gate_pass.data.gate_pass_data import build_gp_payload
        gp_items = _gp_items_from(items)
        overrides = overrides or {}
        if ctx:
            return build_gp_payload(
                supplier_ref_id=supplier_ref_id,
                items=gp_items,
                item_type_ref_id=ctx.item_type_ref_id,
                delivery_type=ctx.delivery_type,
                parameter1=ctx.parameter1,
                parameter2=ctx.parameter2,
                parameter5=ctx.parameter5,
                parameter6=ctx.parameter6,
                grn_check=True,
                qc_check=True,
                **overrides,
            )
        import random
        from pages.private_b2b.modules.gate_pass.data.gate_pass_data import (
            ITEM_TYPE_IDS, DIVISION_IDS, DEPARTMENT_IDS, DELIVERY_TYPE_IDS,
        )
        return build_gp_payload(
            supplier_ref_id=supplier_ref_id,
            items=gp_items,
            item_type_ref_id=random.choice(ITEM_TYPE_IDS),
            delivery_type=random.choice(DELIVERY_TYPE_IDS),
            parameter1=random.choice(DIVISION_IDS),
            parameter2=random.choice(DEPARTMENT_IDS),
            grn_check=True,
            qc_check=True,
            **overrides,
        )

    @staticmethod
    def _build_grn_payload(
        supplier_ref_id: int,
        po_id: int,
        gp_id: int,
        items: List[dict],
        overrides: dict = None,
        ctx: Optional[ChainContext] = None,
    ) -> dict:
        from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import build_grn_payload
        grn_items = _grn_items_from(items)
        overrides = overrides or {}
        if ctx:
            return build_grn_payload(
                supplier_ref_id=supplier_ref_id,
                gate_pass_ref_id_id=gp_id,
                po_ref_id_id=None,
                items=grn_items,
                parameter1=ctx.parameter1,
                parameter2=ctx.parameter2,
                parameter5=ctx.parameter5,
                parameter6=ctx.parameter6,
                **overrides,
            )
        import random
        from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import (
            DIVISION_IDS, DEPARTMENT_IDS, LOCATION_IDS, TYPE_OF_SALE_IDS,
        )
        return build_grn_payload(
            supplier_ref_id=supplier_ref_id,
            gate_pass_ref_id_id=gp_id,
            po_ref_id_id=None,
            items=grn_items,
            parameter1=random.choice(DIVISION_IDS),
            parameter2=random.choice(DEPARTMENT_IDS),
            parameter5=random.choice(TYPE_OF_SALE_IDS),
            parameter6=random.choice(LOCATION_IDS),
            **overrides,
        )

    @staticmethod
    def _build_qc_payload(
        supplier_ref_id: int,
        po_id: int,
        gp_id: int,
        grn_id: int,
        items: List[dict],
        overrides: dict = None,
        ctx: Optional[ChainContext] = None,
    ) -> dict:
        from pages.private_b2b.modules.quality_check.data.quality_check_data import build_qc_payload
        qc_items = _qc_items_from(items, ctx=ctx)
        overrides = overrides or {}
        if ctx:
            return build_qc_payload(
                supplier_ref_id=supplier_ref_id,
                gate_pass_ref_id_id=gp_id,
                grn_ref_id_id=grn_id,
                po_ref_id_id=po_id,
                items=qc_items,
                item_type_ref_id=ctx.item_type_ref_id,
                base_currency=ctx.base_currency,
                txn_currency=ctx.txn_currency,
                parameter1=ctx.parameter1,
                parameter2=ctx.parameter2,
                parameter5=ctx.parameter5,
                parameter6=ctx.parameter6,
                **overrides,
            )
        return build_qc_payload(
            supplier_ref_id=supplier_ref_id,
            gate_pass_ref_id_id=gp_id,
            grn_ref_id_id=grn_id,
            po_ref_id_id=po_id,
            items=qc_items,
            **overrides,
        )

    @staticmethod
    def _build_pb_payload(
        supplier_ref_id: int,
        qc_id: Optional[int],
        grn_id: Optional[int],
        po_id: Optional[int],
        items: List[dict],
        overrides: dict = None,
        ctx: Optional[ChainContext] = None,
    ) -> dict:
        from pages.private_b2b.modules.purchase_booking.data.purchase_booking_data import build_pb_payload
        pb_items = _pb_items_from(items, ctx=ctx)
        overrides = overrides or {}
        supplier_ref_type = ctx.supplier_ref_type if ctx else "Supplier"
        if ctx:
            return build_pb_payload(
                supplier_ref_id=supplier_ref_id,
                supplier_ref_type=supplier_ref_type,
                parameter1=ctx.parameter1,
                parameter2=ctx.parameter2,
                parameter5=ctx.parameter5,
                parameter6=ctx.parameter6,
                base_currency=ctx.base_currency,
                txn_currency=ctx.txn_currency,
                supplier_payment_terms_ref_id=ctx.pb_payment_terms,
                items=pb_items,
                qc_ref_id=qc_id,
                grn_ref_id=grn_id,
                po_ref_id=po_id,
                **overrides,
            )
        return build_pb_payload(
            supplier_ref_id=supplier_ref_id,
            supplier_ref_type=supplier_ref_type,
            items=pb_items,
            qc_ref_id=qc_id,
            grn_ref_id=grn_id,
            po_ref_id=po_id,
            **overrides,
        )


# ---------------------------------------------------------------------------
# Detail display — prints every field sent to the ERP
# ---------------------------------------------------------------------------

def _val(v):
    """Return a display string for a value, handling None."""
    if v is None or v == "":
        return "-"
    return str(v)


def _adj(s, w):
    """Left-justify or pad a string to width w."""
    s = str(s)
    return s.ljust(w)[:w]


def _name(lookup, key):
    """Resolve an ID to 'name (ID)' or just 'ID'."""
    if key is None or key == "":
        return "-"
    k = int(key) if not isinstance(key, int) else key
    name = lookup.get(k)
    if name:
        return f"{name} ({k})"
    return str(k)


def print_chain_details(results):
    """Print a human-readable block for each doc showing what was sent."""
    for i, r in enumerate(results):
        po = r["po"]
        gp = r["gp"]
        grn = r["grn"]
        qc = r.get("qc") or {}

        print(f"\n{'=' * 72}")
        print(f"CHAIN [{i + 1}]  PO {po['id']}  ->  GP {gp['id']}  ->  "
              f"GRN {grn['id']}  ->  QC {qc.get('id', '?')}")
        print(f"{'=' * 72}")

        # -- PO -------------------------------------------------------------------
        pp = po["payload"]
        print(f"\n-- PURCHASE ORDER  #{po['id']}  ({po['ref']})")
        print(f"   Supplier:      {_name(SUPPLIER_NAMES, pp.get('supplier_ref_id'))}")
        print(f"   PO Item Type:  {_name(PO_ITEM_TYPE_NAMES, pp.get('po_item_type'))}")
        print(f"   PO Type:       {_name(PO_TYPE_NAMES, pp.get('po_type'))}")
        print(f"   Currency:      {_name(PO_CURRENCY_NAMES, pp.get('txn_currency'))}")
        print(f"   Base Currency: {_name(PO_CURRENCY_NAMES, pp.get('base_currency'))}")
        print(f"   Conv Rate:     {_val(pp.get('conversion_rate'))}")
        print(f"   Trans Date:    {_val(pp.get('transaction_date'))}")
        sd = pp.get("supplier_details") or {}
        print(f"   Payment Terms: {_name(PAYMENT_TERMS_NAMES, sd.get('supplier_payment_terms'))}")
        print(f"   Deliv. Terms:  {_name(DELIVERY_TERMS_NAMES, sd.get('supplier_delivery_terms'))}")
        print(f"   Pack & Forw:   {_name(PACKING_FORWARDING_NAMES, sd.get('packing_forwarding_ref_id'))}")
        print(f"   Ship From:     {_val(sd.get('supplier_ship_from'))}")
        print(f"   Bill From:     {_val(sd.get('supplier_bill_from'))}")

        po_items = pp.get("purchasing_order_items_details") or []
        po_fetched = po.get("fetched") or {}
        po_fetched_items = po_fetched.get("purchasing_order_items_details") or []
        if po_items:
            print(f"   Items ({len(po_items)}):")
            for ji, item in enumerate(po_items):
                iname = _name(PO_ITEM_NAMES, item.get("item_ref_id"))
                hsn = _val(item.get("hsn_sac_no"))
                uom = _name(PO_UOM_NAMES, item.get("uom"))
                qty = _val(item.get("quantity"))
                rate = _val(item.get("rate"))
                edd = _val(item.get("expected_delivery_date"))
                # Backend confirmation
                fi = po_fetched_items[ji] if ji < len(po_fetched_items) else {}
                bqty = _val(fi.get("quantity"))
                brate = _val(fi.get("rate"))
                btotal = _val(fi.get("total_amount"))
                qty_match = "OK" if abs(float(fi.get("quantity", 0) or 0) - float(item.get("quantity", 0) or 0)) < 0.01 else "MISMATCH"
                rate_match = "OK" if abs(float(fi.get("rate", 0) or 0) - float(item.get("rate", 0) or 0)) < 0.01 else "MISMATCH"
                print(f"     [{ji + 1}] {_adj(iname, 34)} HSN:{hsn}  UOM:{uom}  "
                      f"Qty:{_adj(qty, 8)} Rate:{_adj(rate, 8)} Del:{edd}")
                print(f"           Backend:  qty={_adj(bqty, 6)} rate={_adj(brate, 6)} total={btotal}  "
                      f"(qty:{qty_match}, rate:{rate_match})")
        ad = pp.get("additional_details") or {}
        print(f"   Discount:      {_val(ad.get('txn_currency_discount_percent'))}% / "
              f"{_val(ad.get('txn_currency_discount_amount'))}")
        print(f"   Interest:      {_val(ad.get('txn_currency_interest_percent'))}% / "
              f"{_val(ad.get('txn_currency_interest_amount'))}")
        print(f"   Transport:     {_val(ad.get('transportation_charges'))}")
        print(f"   Remark:        {_val(ad.get('remark'))}")
        print(f"   ---")

        # -- GP -------------------------------------------------------------------
        gpp = gp["payload"]
        print(f"\n-- GATE PASS  #{gp['id']}  ({gp['ref']})")
        print(f"   Supplier:      {_name(SUPPLIER_NAMES, gpp.get('supplier_ref_id'))}")
        print(f"   Item Type:     {_name(PO_ITEM_TYPE_NAMES, gpp.get('item_type_ref_id'))}")
        print(f"   Delivery Type: {_name(DELIVERY_TYPE_NAMES, gpp.get('delivery_type'))}")
        print(f"   Vehicle No:    {_val(gpp.get('vehicle_no'))}")
        print(f"   Driver:        {_val(gpp.get('driver_name'))}")
        print(f"   Driver Contact:{_val(gpp.get('driver_contact_no'))}")
        print(f"   In Time:       {_val(gpp.get('in_time'))}")
        print(f"   Distance:      {_val(gpp.get('distance'))}")
        print(f"   Department:    {_name(DEPARTMENT_NAMES, gpp.get('parameter2'))}")
        print(f"   Location:      {_name(LOCATION_NAMES, gpp.get('parameter6'))}")
        print(f"   Division:      {_name(DIVISION_NAMES, gpp.get('parameter1'))}")
        print(f"   Type of Sale:  {_name(TYPE_OF_SALE_NAMES, gpp.get('parameter5'))}")
        print(f"   GrnCheck/QC:   {_val(gpp.get('grn_check'))} / {_val(gpp.get('qc_check'))}")
        gp_items = gpp.get("gate_pass_details") or []
        if gp_items:
            print(f"   Items ({len(gp_items)}):")
            for ji, item in enumerate(gp_items):
                iname = _name(GP_ITEM_NAMES, item.get("item_ref_id"))
                bags = _val(item.get("no_of_bags"))
                qty = _val(item.get("quantity"))
                uom = _name(GRN_UOM_NAMES, item.get("base_uom"))
                hsn = _val(item.get("hsn_sac_no"))
                print(f"     [{ji + 1}] {_adj(iname, 38)} Bags:{_adj(bags, 4)} "
                      f"Qty:{_adj(qty, 8)} UOM:{uom}  HSN:{hsn}")
        print(f"   ---")

        # -- GRN ------------------------------------------------------------------
        grpp = grn["payload"]
        print(f"\n-- GOODS RECEIPT NOTE  #{grn['id']}  ({grn['ref']})")
        print(f"   Supplier:      {_name(SUPPLIER_NAMES, grpp.get('supplier_ref_id'))}")
        print(f"   PO Ref:        {_val(grpp.get('po_ref_id_id'))}")
        print(f"   GP Ref:        {_val(grpp.get('gate_pass_ref_id_id'))}")
        print(f"   Base Currency: {_name(PO_CURRENCY_NAMES, grpp.get('base_currency'))}")
        print(f"   Txn Currency:  {_name(PO_CURRENCY_NAMES, grpp.get('txn_currency'))}")
        print(f"   Conv Rate:     {_val(grpp.get('conversion_rate'))}")
        print(f"   Trans Date:    {_val(grpp.get('transaction_date'))}")
        gad = grpp.get("additional_details") or {}
        print(f"   Vehicle:       {_val(gad.get('vehicle_no'))}")
        print(f"   Transporter:   {_val(gad.get('transporter_name'))}")
        print(f"   Bill No:       {_val(gad.get('supplier_bill_no'))}")
        print(f"   E-Way Bill:    {_val(gad.get('e_way_bill_no'))}")
        print(f"   Remark:        {_val(gad.get('remark'))}")
        grn_items = grpp.get("grn_item_details") or []
        if grn_items:
            print(f"   Items ({len(grn_items)}):")
            for ji, item in enumerate(grn_items):
                iname = _name(GRN_ITEM_NAMES, item.get("item_ref_id"))
                hsn = _val(item.get("hsn_sac_no"))
                uom = _name(GRN_UOM_NAMES, item.get("uom"))
                rcv = _val(item.get("received_qty"))
                acc = _val(item.get("accepted_qty"))
                rej = _val(item.get("rejected_qty"))
                rate = _val(item.get("rate"))
                bags = _val(item.get("no_of_bags"))
                poq = _val(item.get("po_quantity"))
                gpq = _val(item.get("gate_pass_quantity"))
                print(f"     [{ji + 1}] {_adj(iname, 34)} HSN:{hsn}  UOM:{uom}  "
                      f"Recv:{_adj(rcv, 6)} Acc:{_adj(acc, 6)} Rej:{_adj(rej, 6)} "
                      f"Rate:{_adj(rate, 6)} Bags:{bags}")
                print(f"             PO Qty:{_adj(poq, 5)}  GP Qty:{_adj(gpq, 5)}")
        print(f"   ---")

        # -- QC -------------------------------------------------------------------
        if qc:
            qpp = qc["payload"]
            qcad = qpp.get("qc_additional_details") or {}
            print(f"\n-- QUALITY CHECK  #{qc['id']}  ({qc['ref']})")
            print(f"   Supplier:      {_name(SUPPLIER_NAMES, qpp.get('supplier_ref_id'))}")
            print(f"   PO Ref:        {_val(qpp.get('po_ref_id_id'))}")
            print(f"   GP Ref:        {_val(qpp.get('gate_pass_ref_id_id'))}")
            print(f"   GRN Ref:       {_val(qpp.get('grn_ref_id_id'))}")
            print(f"   Vehicle No:    {_val(qcad.get('vehicle_number'))}")
            print(f"   Driver Name:   {_val(qcad.get('driver_name'))}")
            print(f"   Currency:      {_name(PO_CURRENCY_NAMES, qpp.get('txn_currency'))}")
            print(f"   Trans Date:    {_val(qpp.get('transaction_date'))}")
            qc_items = qpp.get("qc_details") or []
            if qc_items:
                print(f"   Items ({len(qc_items)}):")
                for ji, item in enumerate(qc_items):
                    iname = _name(QC_ITEM_NAMES, item.get("item_ref_id"))
                    hsn = _val(item.get("hsn_sac_no"))
                    uom = _name(GRN_UOM_NAMES, item.get("uom"))
                    grn_qty = _val(item.get("grn_qty"))
                    acc = _val(item.get("accepted_qty"))
                    rej = _val(item.get("rejected_qty"))
                    base = _val(item.get("base_rate"))
                    net = _val(item.get("net_rate"))
                    ded_pct = _val(item.get("deduction_percent"))
                    print(f"     [{ji + 1}] {_adj(iname, 34)} HSN:{hsn}  UOM:{uom}  "
                          f"GRN Qty:{_adj(grn_qty, 6)} Acc:{_adj(acc, 6)} Rej:{_adj(rej, 6)}")
                    print(f"             Base:{_adj(base, 8)} Net:{_adj(net, 8)} Ded%:{_adj(ded_pct, 5)}")
                    details = item.get("details") or []
                    if details:
                        parts = []
                        for d in details:
                            pname = _name(QUALITY_PARAMETER_NAMES, d.get("item_quality_parameter_ref_id"))
                            pval = _val(d.get("actual_value"))
                            parts.append(f"{pname}={pval}")
                        if parts:
                            print(f"             Quality:  {',  '.join(parts)}")
        print(f"")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def setup_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create linked PO -> Gate Pass -> GRN chains",
    )
    parser.add_argument(
        "--supplier", type=int, default=1,
        help="Supplier ref ID (default 1)",
    )
    parser.add_argument(
        "--count", type=int, default=1,
        help="Number of chains to create (default 1)",
    )
    parser.add_argument(
        "--token", default="",
        help="ERP JWT token",
    )
    parser.add_argument(
        "--tenant", default="711",
        help="Tenant ID (default 711)",
    )
    parser.add_argument(
        "--delay", type=float, default=0.3,
        help="Delay in seconds between steps (default 0.3)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print payloads without creating",
    )
    parser.add_argument(
        "--item-ref-id", type=int, default=5,
        help="Item ref ID for all items (default 5)",
    )
    parser.add_argument(
        "--num-items", type=int, default=2,
        help="Items per document (default 2)",
    )
    return parser


def dry_run_dump(supplier_ref_id: int, count: int, num_items: int, item_ref_id: int):
    items = _generate_chain_items(num_items=num_items, item_ref_id=item_ref_id)
    print(f"\n{'=' * 60}")
    print(f"DRY RUN - {count} chain(s), supplier={supplier_ref_id} "
          f"({_supplier_name(supplier_ref_id)})")
    print(f"{'=' * 60}")

    for i in range(count):
        print(f"\n--- Chain [{i + 1}/{count}] ---")

        po = PurchaseChain._build_po_payload(supplier_ref_id, items)
        gp = PurchaseChain._build_gp_payload(supplier_ref_id, items)
        grn = PurchaseChain._build_grn_payload(
            supplier_ref_id, po_id="<PO_ID>", gp_id="<GP_ID>", items=items,
        )
        qc = PurchaseChain._build_qc_payload(
            supplier_ref_id, po_id="<PO_ID>", gp_id="<GP_ID>", grn_id="<GRN_ID>", items=items,
        )

        print(f"\n  PO payload:")
        print(json.dumps(po, indent=2, default=str)[:500])
        print(f"\n  GP payload:")
        print(json.dumps(gp, indent=2, default=str)[:500])
        print(f"\n  GRN payload:")
        print(json.dumps(grn, indent=2, default=str)[:500])
        print(f"\n  QC payload:")
        print(json.dumps(qc, indent=2, default=str)[:500])

    print(f"\nDry run complete. No entries created.")


def main():
    parser = setup_argparse()
    args = parser.parse_args()

    token = args.token or os.environ.get("ERP_TOKEN", "")
    if not token:
        print("ERROR: No token provided. Use --token or set ERP_TOKEN env var.")
        sys.exit(1)

    supplier = args.supplier
    count = args.count
    sname = _supplier_name(supplier)

    if args.dry_run:
        dry_run_dump(supplier, count, args.num_items, args.item_ref_id)
        return

    chain = PurchaseChain(
        token=token,
        tenant=args.tenant,
        delay=args.delay,
    )

    print(f"\n{'=' * 60}")
    print(f"Creating {count} purchase chain(s) - supplier={supplier} ({sname})")
    print(f"{'=' * 60}")

    start = time.time()
    results = chain.run_multiple(
        count=count,
        supplier_ref_id=supplier,
        num_items=args.num_items,
        item_ref_id=args.item_ref_id,
    )
    elapsed = time.time() - start

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    for i, r in enumerate(results):
        po = r["po"]
        gp = r["gp"]
        grn = r["grn"]
        qc = r.get("qc", {})
        qc_part = f"QC {qc.get('id', '?')} ({qc.get('ref', '?')})" if qc else "QC (skipped)"
        print(f"  Chain [{i + 1}]:  PO {po['id']} ({po['ref']})  ->  "
              f"GP {gp['id']} ({gp['ref']})  ->  "
              f"GRN {grn['id']} ({grn['ref']})  ->  "
              f"{qc_part}")

    print(f"\n  Total time: {elapsed:.1f}s  ({elapsed / count:.1f}s per chain)")
    print(f"  All {count} chain(s) completed successfully.")

    print_chain_details(results)
    print()


if __name__ == "__main__":
    main()
