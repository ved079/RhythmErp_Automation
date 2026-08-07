"""
test_calculations.py — Purchase Booking calculation tests.

Tests match the frontend CREATE payload format (simple line items, no
sub-details, no computed GET-response fields).
"""

import pytest
from pages.private_b2b.modules.purchase_booking.data.purchase_booking_data import (
    build_pb_item,
    build_pb_line,
    build_pb_payload,
    compute_line_amount,
    compute_master_total,
    gst_type_for_rate,
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
                   "agent_commision_amount"]:
            assert k in oc, f"Missing other_charges key: {k}"
        # transportation moved to the header level (matches manual PB 2480)
        assert "transportation_charges" in p

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


# ── Rich PB line (mirrors QC, manual PB 2480 shape) ───────────────────────────

def _qc_line(**kw):
    """Build a PB line mirroring a QC line (baseline matches record item 20)."""
    kw.setdefault("amount_detail", 192645.121)
    kw.setdefault("discount_amount", 5712.705395)
    kw.setdefault("alternate_net_qty", 219.25)
    return build_pb_line(
        item_ref_id=20,
        hsn_sac_no=4,
        alternate_uom=3,
        uom=3,
        base_rate=952.51,
        alternate_qty=225.0,
        no_of_bags=225,
        empty_bag_weight=5.75,
        empty_bags_txn_amount=5476.932,
        discount_percentage=2.88,
        labour_charges=192.0,
        **kw,
    )


class TestGstTypeForRate:
    @pytest.mark.calculation
    def test_rate_25_is_cgst_sgst(self):
        assert gst_type_for_rate(25.0) == "CGST + SGST"

    @pytest.mark.calculation
    def test_rate_5_is_igst(self):
        assert gst_type_for_rate(5.0) == "IGST"

    @pytest.mark.calculation
    def test_other_rate_is_none(self):
        assert gst_type_for_rate(18.0) is None
        assert gst_type_for_rate(0.0) is None


class TestBuildPbLine:
    @pytest.mark.calculation
    def test_mirrors_qc_fields(self):
        line = _qc_line()
        assert line["base_rate"] == 952.51
        assert line["alternate_qty"] == 225.0
        assert line["no_of_bags"] == 225
        assert line["empty_bag_weight"] == 5.75
        assert line["empty_bags_txn_amount"] == 5476.932
        assert line["alternate_net_qty"] == 219.25
        assert line["discount_percentage"] == 2.88
        assert line["txn_currency_discount_amount_details"] == 5712.705395

    @pytest.mark.calculation
    def test_gst_on_when_set_off_rate25(self):
        line = _qc_line(is_gst_set_off=True, tax_rate=25.0)
        assert line["is_gst_set_off"] is True
        assert line["gst_type"] == "CGST + SGST"
        assert line["txn_currency_cgst_rate"] == 12.5
        assert line["txn_currency_sgst_rate"] == 12.5
        assert line["txn_currency_igst_rate"] is None
        # 12.5% of 192645.121
        assert line["txn_currency_cgst_amount"] == pytest.approx(24080.640125, rel=1e-4)
        assert line["txn_currency_sgst_amount"] == line["txn_currency_cgst_amount"]
        assert line["txn_currency_tax_amount"] == pytest.approx(48161.28025, rel=1e-4)

    @pytest.mark.calculation
    def test_gst_igst_when_set_off_rate5(self):
        line = _qc_line(is_gst_set_off=True, tax_rate=5.0)
        assert line["gst_type"] == "IGST"
        assert line["txn_currency_igst_rate"] == 5.0
        assert line["txn_currency_igst_amount"] == pytest.approx(9632.25605, rel=1e-4)
        assert line["txn_currency_cgst_rate"] is None
        assert line["txn_currency_tax_amount"] == line["txn_currency_igst_amount"]

    @pytest.mark.calculation
    def test_no_gst_when_set_off_false(self):
        line = _qc_line(is_gst_set_off=False, tax_rate=25.0)
        assert line["gst_type"] is None
        assert line["txn_currency_tax_amount"] == 0.0
        assert line["txn_currency_total_txn_amount"] == pytest.approx(
            line["txn_currency_amount_detail"] - (line["txn_currency_discount_amount_details"] or 0.0) - line["labour_charges"],
            rel=1e-6,
        )

    @pytest.mark.calculation
    def test_total_is_amount_minus_discount_plus_tax_minus_labour(self):
        line = _qc_line(is_gst_set_off=True, tax_rate=25.0)
        assert line["txn_currency_total_txn_amount"] == pytest.approx(
            line["txn_currency_amount_detail"]
            - (line["txn_currency_discount_amount_details"] or 0.0)
            + line["txn_currency_tax_amount"]
            - line["labour_charges"],
            rel=1e-6,
        )

    @pytest.mark.calculation
    def test_required_rich_keys(self):
        line = _qc_line()
        required = [
            "item_ref_id", "base_rate", "alternate_qty", "no_of_bags",
            "empty_bag_weight", "empty_bags_txn_amount", "alternate_net_qty",
            "discount_percentage", "txn_currency_discount_amount_details",
            "txn_currency_amount_detail", "rate", "labour_charges",
            "is_gst_set_off", "tax_rate", "gst_type",
            "txn_currency_igst_rate", "txn_currency_igst_amount",
            "txn_currency_cgst_rate", "txn_currency_cgst_amount",
            "txn_currency_sgst_rate", "txn_currency_sgst_amount",
            "txn_currency_tax_amount", "txn_currency_total_txn_amount",
            "round_of_credit_amount", "round_of_debit_amount",
        ]
        for k in required:
            assert k in line, f"Missing rich PB key: {k}"


class TestRichPayloadAggregates:
    @pytest.mark.calculation
    def test_header_amount_sum_of_detail(self):
        lines = [
            _qc_line(amount_detail=100.0, is_gst_set_off=False),
            _qc_line(amount_detail=200.0, is_gst_set_off=False),
        ]
        p = build_pb_payload(supplier_ref_id=1, supplier_ref_type=SUPPLIER_TYPE_FARMER, items=lines)
        assert p["txn_currency_amount"] == pytest.approx(300.0, rel=1e-6)

    @pytest.mark.calculation
    def test_header_discount_sum_of_details(self):
        lines = [
            _qc_line(discount_amount=10.0, amount_detail=100.0, is_gst_set_off=False),
            _qc_line(discount_amount=20.0, amount_detail=200.0, is_gst_set_off=False),
        ]
        p = build_pb_payload(supplier_ref_id=1, supplier_ref_type=SUPPLIER_TYPE_FARMER, items=lines)
        assert p["txn_currency_discount_amount"] == pytest.approx(30.0, rel=1e-6)

    @pytest.mark.calculation
    def test_header_total_sum_of_total_txn(self):
        lines = [
            _qc_line(amount_detail=100.0, is_gst_set_off=True, tax_rate=25.0),
            _qc_line(amount_detail=200.0, is_gst_set_off=False),
        ]
        p = build_pb_payload(supplier_ref_id=1, supplier_ref_type=SUPPLIER_TYPE_FARMER, items=lines)
        expected = sum(l["txn_currency_total_txn_amount"] for l in lines)
        assert p["txn_currency_total_amount"] == pytest.approx(expected, rel=1e-6)

    @pytest.mark.calculation
    def test_transport_on_header_not_other_charges(self):
        lines = [_qc_line(is_gst_set_off=False)]
        p = build_pb_payload(supplier_ref_id=1, supplier_ref_type=SUPPLIER_TYPE_FARMER,
                             items=lines, transportation_charges=250)
        assert p["transportation_charges"] == 250
        assert "transportation_amount" not in p["other_charges"]

    @pytest.mark.calculation
    def test_total_quantity_is_net_qty_sum(self):
        lines = [
            _qc_line(alternate_net_qty=219.25, is_gst_set_off=False),
            _qc_line(alternate_net_qty=272.95, is_gst_set_off=False),
        ]
        p = build_pb_payload(supplier_ref_id=1, supplier_ref_type=SUPPLIER_TYPE_FARMER, items=lines)
        assert p["total_quantity"] == pytest.approx(492.20, rel=1e-6)
