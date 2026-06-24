"""
test_calculations.py — Purchase Booking calculation tests.

Tests match the frontend CREATE payload format (simple line items, no
sub-details, no computed GET-response fields).
"""

import pytest
from pages.private_b2b.modules.purchase_booking.data.purchase_booking_data import (
    build_pb_item,
    build_pb_payload,
    compute_line_amount,
    compute_master_total,
    SUPPLIER_TYPE_FARMER,
    SUPPLIER_TYPE_SUPPLIER,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _item(rate=100, no_of_bags=10, alternate_qty=None, quantity=None):
    return build_pb_item(
        item_ref_id=1, hsn_sac_no=1, alternate_uom=1, uom=1,
        rate=rate, no_of_bags=no_of_bags,
        alternate_qty=alternate_qty, quantity=quantity,
    )


def _payload(items, **kwargs):
    return build_pb_payload(
        supplier_ref_id=1, supplier_ref_type=SUPPLIER_TYPE_FARMER,
        parameter1=1, parameter2=1, parameter5=1, parameter6=1,
        base_currency=8, txn_currency=8,
        items=items, **kwargs,
    )


# ── Unit: compute_line_amount ─────────────────────────────────────────────────

class TestLineAmount:
    @pytest.mark.calculation
    def test_integer_rate_qty(self):
        assert compute_line_amount(10, 100) == 1000

    @pytest.mark.calculation
    def test_zero_rate(self):
        assert compute_line_amount(10, 0) == 0

    @pytest.mark.calculation
    def test_zero_qty(self):
        assert compute_line_amount(0, 100) == 0

    @pytest.mark.calculation
    def test_large_values(self):
        assert compute_line_amount(200, 5000) == 1_000_000


# ── Unit: compute_master_total ────────────────────────────────────────────────

class TestMasterTotal:
    @pytest.mark.calculation
    def test_single_item(self):
        assert compute_master_total([{"txn_currency_amount": 1000}]) == 1000

    @pytest.mark.calculation
    def test_two_items(self):
        items = [{"txn_currency_amount": 1000}, {"txn_currency_amount": 2000}]
        assert compute_master_total(items) == 3000

    @pytest.mark.calculation
    def test_empty(self):
        assert compute_master_total([]) == 0


# ── Unit: build_pb_item fields ────────────────────────────────────────────────

class TestBuildPbItem:
    @pytest.mark.calculation
    def test_default_alternate_qty_matches_bags(self):
        item = build_pb_item(item_ref_id=1, hsn_sac_no=1, alternate_uom=1, uom=1, rate=100, no_of_bags=5)
        assert item["alternate_qty"] == 5
        assert item["quantity"] == 5

    @pytest.mark.calculation
    def test_explicit_quantity(self):
        item = build_pb_item(item_ref_id=1, hsn_sac_no=1, alternate_uom=1, uom=1, rate=100,
                             no_of_bags=5, alternate_qty=10, quantity=8)
        assert item["alternate_qty"] == 10
        assert item["quantity"] == 8

    @pytest.mark.calculation
    def test_line_amount(self):
        item = build_pb_item(item_ref_id=1, hsn_sac_no=1, alternate_uom=1, uom=1, rate=250, no_of_bags=4)
        assert item["txn_currency_amount"] == 1000
        assert item["amount"] == 1000

    @pytest.mark.calculation
    def test_required_keys(self):
        item = build_pb_item(item_ref_id=1, hsn_sac_no=1, alternate_uom=1, uom=1, rate=100)
        required = [
            "item_ref_id", "hsn_sac_no", "no_of_bags", "alternate_qty",
            "alternate_uom", "quantity", "uom", "rate",
            "txn_currency_amount", "amount",
            "gst_percent", "igst", "cgst", "sgst",
            "is_gst_set_off", "tax_rate",
        ]
        for k in required:
            assert k in item, f"Missing key: {k}"

    @pytest.mark.calculation
    def test_no_id_field(self):
        item = build_pb_item(item_ref_id=1, hsn_sac_no=1, alternate_uom=1, uom=1, rate=100)
        assert "id" not in item

    @pytest.mark.calculation
    def test_no_sub_details(self):
        item = build_pb_item(item_ref_id=1, hsn_sac_no=1, alternate_uom=1, uom=1, rate=100)
        assert "details" not in item

    @pytest.mark.calculation
    def test_gst_fields_are_none(self):
        item = build_pb_item(item_ref_id=1, hsn_sac_no=1, alternate_uom=1, uom=1, rate=100)
        assert item["gst_percent"] is None
        assert item["igst"] is None
        assert item["cgst"] is None
        assert item["sgst"] is None
        assert item["tax_rate"] is None


# ── Master payload structure ──────────────────────────────────────────────────

class TestPayloadStructure:
    @pytest.mark.calculation
    def test_required_master_keys(self):
        p = _payload([_item()])
        required = [
            "transaction_date", "supplier_ref_id",
            "supplier_ref_type", "txn_currency_amount", "txn_currency_total_amount",
            "conversion_rate", "parameter1", "parameter2", "parameter5", "parameter6",
            "base_currency", "txn_currency", "posting_status", "gst_registration_type",
            "qc_ref_id_id", "grn_ref_id_id", "po_ref_id_id",
            "supplier_payment_terms_ref_id",
            "total_quantity", "is_tds_applicable", "section_ref_id",
            "tds_amount", "round_off_credit_amount", "round_off_debit_amount",
            "remark",
            "purchase_booking_details", "other_charges", "grn_details",
        ]
        for k in required:
            assert k in p, f"Missing master key: {k}"

    @pytest.mark.calculation
    def test_no_id_in_master(self):
        p = _payload([])
        assert "id" not in p

    @pytest.mark.calculation
    def test_no_attribute_name(self):
        p = _payload([])
        assert "attribute_name" not in p

    @pytest.mark.calculation
    def test_supplier_ref_type_farmer_is_string(self):
        p = build_pb_payload(supplier_ref_id=1, supplier_ref_type=SUPPLIER_TYPE_FARMER)
        assert isinstance(p["supplier_ref_type"], str)
        assert p["supplier_ref_type"] == "Farmer"

    @pytest.mark.calculation
    def test_supplier_ref_type_supplier_is_string(self):
        p = build_pb_payload(supplier_ref_id=1, supplier_ref_type=SUPPLIER_TYPE_SUPPLIER)
        assert p["supplier_ref_type"] == "Supplier"

    @pytest.mark.calculation
    def test_fk_refs_use_double_id_suffix(self):
        p = build_pb_payload(supplier_ref_id=1, qc_ref_id=10, grn_ref_id=20, po_ref_id=30)
        assert p["qc_ref_id_id"] == 10
        assert p["grn_ref_id_id"] == 20
        assert p["po_ref_id_id"] == 30
        assert "qc_ref_id" not in p
        assert "grn_ref_id" not in p
        assert "po_ref_id" not in p

    @pytest.mark.calculation
    def test_conversion_rate_is_str(self):
        p = _payload([])
        assert p["conversion_rate"] == "1"

    @pytest.mark.calculation
    def test_posting_status_empty_string(self):
        p = _payload([])
        assert p["posting_status"] == ""

    @pytest.mark.calculation
    def test_section_ref_id_default(self):
        p = _payload([])
        assert p["section_ref_id"] == "0"

    @pytest.mark.calculation
    def test_tds_defaults(self):
        p = _payload([])
        assert p["is_tds_applicable"] is False
        assert p["tds_amount"] == 0
        assert p["section_ref_id"] == "0"

    @pytest.mark.calculation
    def test_round_off_credit_default(self):
        p = _payload([])
        assert p["round_off_credit_amount"] == 0

    @pytest.mark.calculation
    def test_round_off_debit_default(self):
        p = _payload([])
        assert p["round_off_debit_amount"] == 0

    @pytest.mark.calculation
    def test_remark_default(self):
        p = _payload([])
        assert p["remark"] == ""

    @pytest.mark.calculation
    def test_default_currency_is_inr(self):
        p = _payload([])
        assert p["base_currency"] == 8
        assert p["txn_currency"] == 8

    @pytest.mark.calculation
    def test_other_charges_keys(self):
        p = _payload([])
        oc = p["other_charges"]
        for k in ["agent_ref_id", "is_rate_percentage", "agent_commision",
                   "agent_commision_amount", "transportation_amount"]:
            assert k in oc, f"Missing other_charges key: {k}"

    @pytest.mark.calculation
    def test_grn_details_default(self):
        p = _payload([])
        assert p["grn_details"] == []

    @pytest.mark.calculation
    def test_txn_amount_types_int(self):
        p = _payload([_item(rate=100, no_of_bags=3)])
        assert isinstance(p["txn_currency_amount"], int)
        assert isinstance(p["txn_currency_total_amount"], int)
        assert isinstance(p["total_quantity"], int)

    @pytest.mark.calculation
    def test_item_field_types_int(self):
        item = _item(rate=250, no_of_bags=4)
        assert isinstance(item["txn_currency_amount"], int)
        assert isinstance(item["amount"], int)
        assert isinstance(item["quantity"], int)
        assert isinstance(item["alternate_qty"], int)
        assert isinstance(item["rate"], int)
