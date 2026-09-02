"""
payment_data.py
---------------
Payload builders for the Payment screen.

Payload shape (discovered from tenant 666 manual payment):
{
  "payment_date": "YYYY-MM-DD",
  "payment_type_ref_id": 151,          # 151=Regular, 152=Advance
  "payment_method_ref_id": 53,         # 53=Cash, 54=Cheque, 55=DD, 141=IMPS, 143=RTGS
  "tenant_account_ref_id": <bank_id>,
  "supplier_ref_id": <supplier_id>,
  "txn_currency_net_amount_detail": <amount>,  # total amount being paid
  "posting_status": "Post",            # creates and posts in one step
  "payment_details": [                 # one entry per PB being paid
    {
      "purchase_expense_booking_ref_id": <pb_id>,
      "purchase_expense_booking_amount": <pb_total_amount>,
      "txn_currency_amount_detail": <amount_paying_for_this_pb>,
    }
  ]
}
"""

from datetime import date
from typing import List, Optional


def build_payment_payload(
    supplier_ref_id: int,
    pb_id: int,
    pb_amount: float,
    bank_account_id: int,
    payment_method_ref_id: int = 53,
    payment_type_ref_id: int = 151,
    payment_date: Optional[str] = None,
    post: bool = True,
) -> dict:
    """Build a Payment payload for one Purchase Booking.

    Args:
        supplier_ref_id: The supplier FK.
        pb_id: The Purchase Booking id being paid.
        pb_amount: The PB's txn_currency_total_amount (full payment).
        bank_account_id: The bank account FK (tenant_account_ref_id).
        payment_method_ref_id: 53=Cash (default), 54=Cheque, etc.
        payment_type_ref_id: 151=Regular (default), 152=Advance.
        payment_date: ISO date string; defaults to today.
        post: When True, sets posting_status="Post" (create + post in one step).
    """
    txn_date = payment_date or date.today().isoformat()
    payload = {
        "payment_date": txn_date,
        "payment_type_ref_id": payment_type_ref_id,
        "payment_method_ref_id": payment_method_ref_id,
        "tenant_account_ref_id": bank_account_id,
        "supplier_ref_id": supplier_ref_id,
        "txn_currency_net_amount_detail": pb_amount,
        "payment_details": [
            {
                "purchase_expense_booking_ref_id": pb_id,
                "purchase_expense_booking_amount": pb_amount,
                "txn_currency_amount_detail": pb_amount,
            }
        ],
    }
    if post:
        payload["posting_status"] = "Post"
    return payload
