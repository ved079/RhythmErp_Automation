import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from common.logger import log
from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import (
    compute_line_amount,
    compute_master_total,
    compute_expected_results,
    assert_calculations_match,
)


class TestGRNCalculations:
    @pytest.mark.api
    def test_calc_line_amount(self):
        log.info("GRN-CALC-01: line_amount = received_qty * rate")
        assert compute_line_amount(10, 20) == 200
        assert compute_line_amount(0, 100) == 0
        assert compute_line_amount(100.5, 2.5) == 251.25

    @pytest.mark.api
    def test_calc_master_total(self):
        log.info("GRN-CALC-02: master_total = sum of line amounts")
        lines = [{"amount": 100}, {"amount": 200}, {"amount": 50}]
        assert compute_master_total(lines) == 350
        assert compute_master_total([]) == 0

    @pytest.mark.api
    def test_calc_expected_results_single_item(self):
        log.info("GRN-CALC-03: Expected results for single item")
        payload = {
            "grn_item_details": [
                {"accepted_qty": 10.0, "rate": 20.0},
            ]
        }
        expected = compute_expected_results(payload)
        assert len(expected["lines"]) == 1
        assert expected["lines"][0]["amount"] == 200.0

    @pytest.mark.api
    def test_calc_expected_results_multiple_items(self):
        log.info("GRN-CALC-04: Expected results for multiple items")
        payload = {
            "grn_item_details": [
                {"accepted_qty": 10.0, "rate": 20.0},
                {"accepted_qty": 5.0, "rate": 30.0},
                {"accepted_qty": 2.0, "rate": 100.0},
            ]
        }
        expected = compute_expected_results(payload)
        assert len(expected["lines"]) == 3
        assert expected["lines"][0]["amount"] == 200.0
        assert expected["lines"][1]["amount"] == 150.0
        assert expected["lines"][2]["amount"] == 200.0
        assert expected["master_total"] == 550.0

    @pytest.mark.api
    def test_assert_match_passes(self):
        log.info("GRN-CALC-05: assert_calculations_match passes for correct data")
        entry = {
            "grn_item_details": [
                {"txn_currency_amount_detail": 200.0},
            ]
        }
        expected = {
            "lines": [{"amount": 200.0}],
        }
        assert_calculations_match(entry, expected)

    @pytest.mark.api
    def test_assert_match_fails_on_mismatch(self):
        log.info("GRN-CALC-06: assert_calculations_match raises on mismatch")
        entry = {
            "grn_item_details": [
                {"txn_currency_amount_detail": 999.0},
            ]
        }
        expected = {
            "lines": [{"amount": 200.0}],
        }
        with pytest.raises(AssertionError, match="Calculation mismatch"):
            assert_calculations_match(entry, expected)
