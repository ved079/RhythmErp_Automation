"""
sales_order_data.py
-------------------
Payload builders for the "Sales Order" ERP screen.

Field names derived from the live Sales Order create (frontend Network tab) and
the stored-record shape shared for SO ids there:

  Master:  transaction_date, party_ref_id, party_ref_type, so_type_ref_id,
           supply_type_ref_id, txn_currency / base_currency / conversion_rate,
           parameter1/2/5/6, status="Pending"
  Nested:  customer_details      (customer_bill_from / customer_ship_to /
                                  payment+delivery terms)
  Details: sales_order_details[] (line items mirroring the QC lines)
    Sub:   details               (empty list)

Create endpoint: POST /sales/sales-order-new/?screen_name=Sales%20Order&viewType=create

Resolver notes:
  - party_ref_id -> the Customer's party id (customer_ref_id dropdown), with
    party_ref_type="Customer"
  - so_type_ref_id  -> "Commission" (2017 in tenant 666), resolved live by name
  - supply_type_ref_id -> "Both" (1266 in tenant 666), resolved live by name
  - customer bill_from / ship_to / payment terms / delivery terms /
    mode of delivery come from the chosen Customer record (omitted when absent).
"""

import random
from datetime import date
from typing import List, Optional


# ── Resolvers (dropdown FK lookup by label) ─────────────────────────────────

def resolve_customer_ref_id(client, screen: str = "Sales Order", field_key: str = "customer_ref_id") -> Optional[int]:
    """Return a valid customer_ref_id from the SO customer dropdown.

    The first option is the last-added customer in the ERP (matches how the SO
    screen behaves). Returns None when the tenant has no customers.
    """
    try:
        opts = client.get_dropdown_options(screen, field_key)
        for o in opts or []:
            if o.get("id"):
                return int(o["id"])
    except Exception:
        pass
    return None


def resolve_so_type_id(client, screen: str = "Sales Order", field_key: str = "so_type_ref_id",
                       label: str = "Commission", fb: Optional[int] = None) -> Optional[int]:
    """Return the so_type_ref_id whose dropdown label == *label* (default "Commission")."""
    try:
        opts = client.get_dropdown_options(screen, field_key)
        for o in opts or []:
            if str(o.get("key", "")).strip().lower() == label.strip().lower():
                return int(o["id"])
    except Exception:
        pass
    return fb


def resolve_supply_type_id(client, screen: str = "Sales Order", field_key: str = "supply_type_ref_id",
                           label: str = "Both", fb: Optional[int] = None) -> Optional[int]:
    """Return the supply_type_ref_id whose dropdown label == *label* (default "Both")."""
    try:
        opts = client.get_dropdown_options(screen, field_key)
        for o in opts or []:
            if str(o.get("key", "")).strip().lower() == label.strip().lower():
                return int(o["id"])
    except Exception:
        pass
    return fb


# ── Customer-detail extraction ───────────────────────────────────────────────

def extract_customer_details(customer_entry: Optional[dict]) -> dict:
    """Pull bill_from / ship_to / terms from a Customer detail record.

    Customer children steppers:
      - "Address Details"      -> details[] with address ids (address_type
                                 Shipping=43 / Billing=42)
      - "Additional Details"   -> payment_terms_ref_id, delivery_terms_ref_id,
                                  mode_of_delivery_ref_id
    Missing values are omitted so the ERP defaults are used.
    """
    out: dict = {}
    if not customer_entry:
        return out
    for child in customer_entry.get("children") or []:
        stepper = child.get("stepper_name") or ""
        if "Address" in stepper:
            bill = ship = None
            for row in child.get("details") or []:
                addr_type = row.get("address_type")
                rid = row.get("id")
                if rid is None:
                    continue
                if str(addr_type).strip() == "42":  # Billing
                    bill = rid
                elif str(addr_type).strip() == "43":  # Shipping
                    ship = rid
            if bill is not None:
                out["customer_bill_from"] = bill
            if ship is not None:
                out["customer_ship_to"] = ship
        elif "Additional" in stepper:
            for key in ("payment_terms_ref_id", "delivery_terms_ref_id", "mode_of_delivery_ref_id"):
                val = child.get(key)
                if val not in (None, ""):
                    out[key] = int(val)
    return out


# ── Line item builder ────────────────────────────────────────────────────────

def build_so_line(
    item_ref_id: int,
    hsn_sac_no: int,
    quantity: float,
    rate: float,
    tax_rate: float = 0.0,
    uom: int = None,
    alternate_uom: int = None,
    uom_conversion: float = 1.0,
    expected_delivery_date: str = None,
) -> dict:
    """Build one Sales Order line (shape from SO 339 + schema).

    ``quantity`` is the QC accepted qty (per the chain flow). ``rate`` is the
    item rate from the QC line. Amounts: txn = qty * rate; tax = txn * rate%.
    """
    if expected_delivery_date is None:
        expected_delivery_date = date.today().isoformat()
    txn = round(float(quantity) * float(rate), 6)
    tax = round(txn * float(tax_rate or 0.0) / 100.0, 6)
    return {
        "item_ref_id": item_ref_id,
        "hsn_sac_no": hsn_sac_no,
        "uom": uom,
        "alternate_uom": alternate_uom,
        "uom_conversion": uom_conversion,
        "quantity": quantity,
        "alternate_qty": round(float(quantity) * float(uom_conversion or 1.0), 6),
        "rate": rate,
        "txn_currency_amount": txn,
        "tax_rate": tax_rate,
        "base_currency_amount": txn,
        "txn_currency_tax_amount": tax,
        "base_currency_tax_amount": tax,
        "txn_currency_total_amount": round(txn + tax, 6),
        "base_currency_total_amount": round(txn + tax, 6),
        "expected_delivery_date": expected_delivery_date,
        "details": [],
    }


def build_so_payload(
    customer_ref_id: int,
    items: List[dict],
    so_type_ref_id: Optional[int] = None,
    supply_type_ref_id: Optional[int] = None,
    txn_currency: int = 8,
    base_currency: int = 8,
    conversion_rate: float = 1.0,
    parameter1: int = 1,
    parameter2: int = 1,
    parameter5: int = 1,
    parameter6: int = 1,
    customer_details: Optional[dict] = None,
    transaction_date: str = None,
    remarks: str = None,
    overrides: dict = None,
) -> dict:
    """Build a complete Sales Order payload.

    The ERP SO model stores the Customer as ``party_ref_id`` (the Customer's
    party id) with ``party_ref_type="Customer"`` — the value the UI resolves
    from the ``customer_ref_id`` dropdown. ``customer_details`` is the output of
    extract_customer_details() — keys not set are simply not sent.
    """
    if transaction_date is None:
        transaction_date = date.today().isoformat()
    payload = {
        "transaction_date": transaction_date,
        "party_ref_id": customer_ref_id,
        "party_ref_type": "Customer",
        "so_type_ref_id": so_type_ref_id,
        "supply_type_ref_id": supply_type_ref_id,
        "txn_currency": txn_currency,
        "base_currency": base_currency,
        "conversion_rate": conversion_rate,
        "parameter1": parameter1,
        "parameter2": parameter2,
        "parameter5": parameter5,
        "parameter6": parameter6,
        "status": "Pending",
        "sales_order_details": items or [],
    }
    if remarks is not None:
        payload["remarks"] = remarks
    if customer_details:
        payload["customer_details"] = customer_details
    if overrides:
        payload.update(overrides)
    return payload
