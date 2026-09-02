"""
payment_data.py
---------------
Payload builders for the Payment screen.

Ground truth: manually saved payment GET response from tenant 666.
"""

from datetime import date
from typing import Optional


# FK for "Purchase Expense Booking" ref_type — constant across tenants.
PURCHASE_EXPENSE_BOOKING_REF_TYPE = 144


def build_payment_payload(
    party_ref_id: int,
    pb_id: int,
    pb_amount: float,
    bank_account_id: int,
    pb_transaction_date: Optional[str] = None,
    payment_method_ref_id: int = 53,
    payment_type_ref_id: int = 151,
    payment_date: Optional[str] = None,
    post: bool = True,
    # Tenant context — pulled from the PB or ChainContext
    txn_currency: int = 8,
    base_currency: int = 8,
    conversion_rate: str = "1.000000",
    parameter1: int = 1,
    parameter2: int = 1,
    parameter5: int = 1,
    parameter6: int = 1,
) -> dict:
    """Build a Payment payload for one Purchase Booking.

    Field names match the ERP's stored record exactly (verified from manual payment).
    """
    txn_date = payment_date or date.today().isoformat()
    pb_date = pb_transaction_date or txn_date
    amount_str = f"{pb_amount:.2f}"

    payload = {
        "transaction_date": txn_date,
        "payment_type_ref_id": payment_type_ref_id,
        "payment_type_ref_name": "Regular" if payment_type_ref_id == 151 else "Advance",
        "party_ref_id": party_ref_id,
        "party_ref_type": "Supplier",
        "payment_method_ref_id": payment_method_ref_id,
        "tenant_account_ref_id": bank_account_id,
        "txn_currency": txn_currency,
        "base_currency": base_currency,
        "conversion_rate": conversion_rate,
        "parameter1": parameter1,
        "parameter2": parameter2,
        "parameter5": parameter5,
        "parameter6": parameter6,
        "txn_currency_gross_amount": amount_str,
        "txn_currency_bank_charges": 0.0,
        "txn_currency_net_amount": amount_str,
        "payment_details": [
            {
                "purchase_expense_booking_ref_id": pb_id,
                "purchase_expense_booking_ref_type": PURCHASE_EXPENSE_BOOKING_REF_TYPE,
                "purchase_expense_booking_date": pb_date,
                "purchase_expense_booking_amount": pb_amount,
                "txn_currency_advance_amount_applied": pb_amount,
                "txn_currency_net_amount_detail": pb_amount,
            }
        ],
    }
    if post:
        payload["posting_status"] = "Post"
    return payload
