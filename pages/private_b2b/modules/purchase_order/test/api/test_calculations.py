import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    build_po_payload,
    compute_expected_results,
    compute_line_amount,
    compute_line_tax,
    compute_line_total,
    compute_master_total,
    compute_discount_amount,
    compute_interest_amount,
)


class TestComputeFunctionsUnit:
    @pytest.mark.calculation
    def test_line_amount(self):
        assert compute_line_amount(10, 100) == 1000.0
        assert compute_line_amount(0, 100) == 0.0
        assert compute_line_amount(5.5, 200) == 1100.0

    @pytest.mark.calculation
    def test_line_tax(self):
        assert compute_line_tax(1000, 12) == 120.0
        assert compute_line_tax(1000, 0) == 0.0
        assert compute_line_tax(0, 12) == 0.0

    @pytest.mark.calculation
    def test_line_total(self):
        assert compute_line_total(1000, 120) == 1120.0
        assert compute_line_total(1000, 0) == 1000.0

    @pytest.mark.calculation
    def test_master_total(self):
        lines = [
            {"total_amount": 1000.0},
            {"total_amount": 2000.0},
            {"total_amount": 500.0},
        ]
        assert compute_master_total(lines) == 3500.0

    @pytest.mark.calculation
    def test_master_total_empty(self):
        assert compute_master_total([]) == 0.0

    @pytest.mark.calculation
    def test_discount_amount(self):
        assert compute_discount_amount(10000, 5) == 500.0
        assert compute_discount_amount(10000, 0) == 0.0
        assert compute_discount_amount(10000, None) == 0.0

    @pytest.mark.calculation
    def test_interest_amount(self):
        assert compute_interest_amount(10000, 10) == 1000.0
        assert compute_interest_amount(10000, 0) == 0.0
        assert compute_interest_amount(10000, None) == 0.0


class TestComputeExpectedResults:
    @pytest.mark.calculation
    def test_single_line_no_tax_no_discount(self):
        payload = build_po_payload(items=[
            {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
             "quantity": 10.0, "rate": 100.0, "expected_delivery_date": "2026-06-20"}
        ])
        expected = compute_expected_results(payload)
        assert expected["lines"][0]["txn_currency_amount_detail"] == 1000.0
        assert expected["lines"][0]["txn_currency_tax_amount_details"] == 0.0
        assert expected["lines"][0]["total_amount"] == 1000.0
        assert expected["txn_currency_total_amount"] == 1000.0
        assert expected["txn_currency_discount_amount"] == 0.0
        assert expected["txn_currency_interest_amount"] == 0.0

    @pytest.mark.calculation
    def test_multi_line_with_tax(self):
        items = [
            {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
             "quantity": 10.0, "rate": 100.0, "tax_rate": 5.0,
             "expected_delivery_date": "2026-06-20"},
            {"item_ref_id": 6, "hsn_sac_no": 2, "uom": 3,
             "quantity": 5.0, "rate": 200.0, "tax_rate": 12.0,
             "expected_delivery_date": "2026-06-25"},
        ]
        payload = build_po_payload(items=items)
        expected = compute_expected_results(payload)

        # Line 1: 10*100=1000, tax=1000*5/100=50, total=1050
        assert expected["lines"][0]["txn_currency_amount_detail"] == 1000.0
        assert expected["lines"][0]["txn_currency_tax_amount_details"] == 50.0
        assert expected["lines"][0]["total_amount"] == 1050.0

        # Line 2: 5*200=1000, tax=1000*12/100=120, total=1120
        assert expected["lines"][1]["txn_currency_amount_detail"] == 1000.0
        assert expected["lines"][1]["txn_currency_tax_amount_details"] == 120.0
        assert expected["lines"][1]["total_amount"] == 1120.0

        # Master total: 1050+1120=2170
        assert expected["txn_currency_total_amount"] == 2170.0
        assert expected["txn_currency_discount_amount"] == 0.0
        assert expected["txn_currency_interest_amount"] == 0.0

    @pytest.mark.calculation
    def test_compute_with_discount_and_interest(self):
        """Backend computes discount/interest from % when amount is 0 in payload."""
        payload = build_po_payload(
            items=[
                {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
                 "quantity": 100.0, "rate": 500.0,
                 "expected_delivery_date": "2026-06-20"}
            ],
            additional_details={
                "transportation_charges": 0,
                "txn_currency_discount_percent": 5.0,
                "txn_currency_discount_amount": 0,
                "txn_currency_interest_percent": 10.0,
                "txn_currency_interest_amount": 0,
                "remark": None,
            }
        )
        expected = compute_expected_results(payload)

        # Line: 100*500=50000, no tax -> total=50000
        assert expected["lines"][0]["txn_currency_amount_detail"] == 50000.0
        assert expected["txn_currency_total_amount"] == 50000.0

        # Backend computes: 5% of 50000 = 2500, 10% of 50000 = 5000
        assert expected["txn_currency_discount_amount"] == 2500.0
        assert expected["txn_currency_interest_amount"] == 5000.0


class TestLiveCalculations:
    @pytest.mark.calculation
    @pytest.mark.smoke
    def test_single_line_calculation(self, po_api):
        result = po_api.create_and_verify_calculations(
            supplier_ref_id=1,
            parameter2=1,
            parameter3=25,
            parameter4=1,
        )
        log.info(f"PO {result['id']} calculations verified")

    @pytest.mark.calculation
    def test_multi_line_calculation(self, po_api):
        items = [
            {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
             "quantity": 10.0, "rate": 100.0,
             "expected_delivery_date": "2026-06-20"},
            {"item_ref_id": 6, "hsn_sac_no": 2, "uom": 3,
             "quantity": 5.0, "rate": 200.0,
             "expected_delivery_date": "2026-06-25"},
        ]
        payload = build_po_payload(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            items=items
        )
        result = po_api.create_and_verify_calculations(payload=payload)
        log.info(f"PO {result['id']} multi-line calculations verified")

    @pytest.mark.calculation
    def test_discount_auto_computed_from_percent(self, po_api):
        """Backend computes 5% of 5000 = 250 when amount not explicitly set."""
        payload = build_po_payload(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            items=[
                {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
                 "quantity": 20.0, "rate": 250.0,
                 "expected_delivery_date": "2026-06-20"}
            ],
            additional_details={
                "transportation_charges": 0,
                "txn_currency_discount_percent": 5.0,
                "txn_currency_discount_amount": 0,
                "txn_currency_interest_percent": None,
                "txn_currency_interest_amount": 0,
                "remark": None,
            }
        )
        result = po_api.create_and_verify_calculations(payload=payload)
        log.info(f"PO {result['id']} discount auto-compute verified (5% of 5000 = 250)")

    @pytest.mark.calculation
    def test_interest_auto_computed_from_percent(self, po_api):
        """Backend computes 8% of 3000 = 240 when amount not explicitly set."""
        payload = build_po_payload(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            items=[
                {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
                 "quantity": 30.0, "rate": 100.0,
                 "expected_delivery_date": "2026-06-20"}
            ],
            additional_details={
                "transportation_charges": 0,
                "txn_currency_discount_percent": None,
                "txn_currency_discount_amount": 0,
                "txn_currency_interest_percent": 8.0,
                "txn_currency_interest_amount": 0,
                "remark": None,
            }
        )
        result = po_api.create_and_verify_calculations(payload=payload)
        log.info(f"PO {result['id']} interest auto-compute verified (8% of 3000 = 240)")

    @pytest.mark.calculation
    def test_discount_and_interest_always_computed_from_percent(self, po_api):
        """Backend always recomputes discount/interest from percent, overriding explicit values."""
        payload = build_po_payload(
            supplier_ref_id=1, parameter2=1, parameter3=25, parameter4=1,
            items=[
                {"item_ref_id": 5, "hsn_sac_no": 2, "uom": 3,
                 "quantity": 10.0, "rate": 100.0,
                 "expected_delivery_date": "2026-06-20"}
            ],
            additional_details={
                "transportation_charges": 100.0,
                "txn_currency_discount_percent": 5.0,
                "txn_currency_discount_amount": 999.0,
                "txn_currency_interest_percent": 10.0,
                "txn_currency_interest_amount": 888.0,
                "remark": "Test PO",
            }
        )
        result = po_api.create_po(payload)
        assert result is not None
        entry_id = result.get("id") or result.get("entry_id")
        entry = po_api.get_po(entry_id)
        assert entry is not None
        add = entry.get("additional_details", {})
        # Backend recomputes: 5% of 1000 = 50, 10% of 1000 = 100
        assert float(add.get("txn_currency_discount_amount", 0)) == 50.0
        assert float(add.get("txn_currency_interest_amount", 0)) == 100.0
        # Non-computed fields pass through as-is
        assert float(add.get("transportation_charges", 0)) == 100.0
        assert add.get("remark") == "Test PO"
        log.info(f"PO {entry_id} discount/interest always recomputed from percent")
