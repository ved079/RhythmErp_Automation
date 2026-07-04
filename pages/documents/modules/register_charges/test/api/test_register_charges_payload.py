"""
test_register_charges_payload.py â€” Verify Register Charges payload structure.
"""

import sys
import os
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pages.documents.modules.register_charges.data.register_charges_data import (
    build_api_payload,
    generate_api_payload,
    generate_batch_payloads,
    generate_valid_data,
    TYPE_OF_CHARGE_IDS,
    TYPE_OF_CHARGE_NAMES,
    _generated_roc_ids,
)


class TestRegisterChargesPayloadStructure:
    """Verify the generated payload matches expected structure."""

    def test_payload_has_required_keys(self):
        payload = generate_api_payload()
        assert "id" in payload
        assert "attribute_name" in payload
        assert "roc_charge_id" in payload
        assert "type_of_charge_ref_id" in payload
        assert "amount_secured" in payload
        assert "charge_holder_details" in payload
        assert "details" in payload
        assert "children" in payload

    def test_attribute_name_is_correct(self):
        payload = generate_api_payload()
        assert payload["attribute_name"] == "Register Charges"

    def test_id_is_empty_string(self):
        payload = generate_api_payload()
        assert payload["id"] == ""

    def test_details_and_children_are_empty_lists(self):
        payload = generate_api_payload()
        assert payload["details"] == []
        assert payload["children"] == []

    def test_roc_charge_id_is_digits_only(self):
        for _ in range(20):
            payload = generate_api_payload()
            roc = payload["roc_charge_id"]
            assert roc.isdigit(), f"ROC ID '{roc}' has non-digit chars"
            assert 1 <= len(roc) <= 20, f"ROC ID length {len(roc)} out of range"

    def test_roc_charge_id_not_all_zeros(self):
        for _ in range(20):
            payload = generate_api_payload()
            roc = payload["roc_charge_id"]
            assert not re.match(r'^0+$', roc), f"ROC ID '{roc}' is all zeros"

    def test_type_of_charge_ref_id_is_valid(self):
        for _ in range(20):
            payload = generate_api_payload()
            toc = payload["type_of_charge_ref_id"]
            assert toc in TYPE_OF_CHARGE_IDS, f"Invalid Type of Charge ID: {toc}"

    def test_amount_secured_is_positive(self):
        for _ in range(20):
            payload = generate_api_payload()
            amt = payload["amount_secured"]
            assert amt > 0, f"Amount secured must be positive: {amt}"

    def test_amount_secured_format(self):
        for _ in range(50):
            payload = generate_api_payload()
            amt = payload["amount_secured"]
            amt_str = str(amt)
            assert "+" not in amt_str
            assert "-" not in amt_str[:1] or amt_str[0] != "-"

    def test_charge_holder_details_is_string(self):
        payload = generate_api_payload()
        assert isinstance(payload["charge_holder_details"], str)
        assert len(payload["charge_holder_details"]) > 0

    def test_date_of_satisfaction_is_none(self):
        payload = generate_api_payload()
        assert payload["date_of_satisfaction"] is None

    def test_roc_charge_id_unique_in_batch(self):
        _generated_roc_ids.clear()
        payloads = generate_batch_payloads(50)
        roc_ids = [p["roc_charge_id"] for p in payloads]
        assert len(roc_ids) == len(set(roc_ids)), "Duplicate ROC IDs found"


class TestRegisterChargesBuildPayload:
    """Verify build_api_payload with explicit data and overrides."""

    def test_build_with_explicit_data(self):
        data = {
            "roc_charge_id": "999999999999",
            "type_of_charge_ref_id": 1911,
            "description_of_assets_property": "Test asset",
            "amount_secured": 100000,
            "charge_holder_details": "Test Bank",
        }
        payload = build_api_payload(data=data)
        assert payload["roc_charge_id"] == "999999999999"
        assert payload["type_of_charge_ref_id"] == 1911
        assert payload["amount_secured"] == 100000
        assert payload["charge_holder_details"] == "Test Bank"

    def test_fk_overrides(self):
        payload = build_api_payload(fk_overrides={"type_of_charge_ref_id": 1910})
        assert payload["type_of_charge_ref_id"] == 1910

    def test_kwargs_override(self):
        payload = generate_api_payload(amount_secured=999999)
        assert payload["amount_secured"] == 999999

    def test_batch_with_override(self):
        payloads = generate_batch_payloads(5, type_of_charge_ref_id=1909)
        for p in payloads:
            assert p["type_of_charge_ref_id"] == 1909
            assert p["charge_holder_details"] is not None
