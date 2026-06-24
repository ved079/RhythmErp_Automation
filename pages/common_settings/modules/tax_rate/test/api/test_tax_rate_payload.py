"""test_tax_rate_payload.py — Fast API payload structure tests for Tax Rate."""
import pytest, sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
from pages.common_settings.modules.tax_rate.data.tax_rate_data import (
    build_tax_rate_api_payload, generate_tax_rate_api_payloads,
    generate_batch_payloads, HSN_SAC_CODES, STEPPER_NAME,
)

# Mock FK IDs for unit tests (simulates what FkResolver would return at runtime)
MOCK_FK_IDS = {
    "tax_type_ref_id": {"GST": 93},
    "tax_authority_ref_id": {"CGST Authority": 103, "SGST Authority": 104, "IGST Authority": 105},
    "hsn_sac_number": {code: i+100 for i, code in enumerate(HSN_SAC_CODES)},
}
MOCK_HSN_SAC_IDS = MOCK_FK_IDS["hsn_sac_number"]


@pytest.mark.api
class TestTaxRateAPIPayload:
    def test_payload_has_required_keys(self):
        p = generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]
        for k in ["id", "attribute_name", "tax_rate_name", "tax_type_ref_id",
                   "tax_authority_ref_id", "from_date", "to_date",
                   "revision_status", "children"]:
            assert k in p, f"Missing key: {k}"

    def test_payload_has_children_with_stepper(self):
        p = generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]
        assert isinstance(p["children"], list)
        assert len(p["children"]) >= 1
        child = p["children"][0]
        assert child["stepper_name"] == STEPPER_NAME
        assert child["is_stepper"] is True
        assert "details" in child

    def test_payload_attribute_name(self):
        assert generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["attribute_name"] == "Tax Rate"

    def test_payload_id_is_empty(self):
        assert generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["id"] == ""

    def test_payload_tax_rate_name_is_string(self):
        assert isinstance(generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["tax_rate_name"], str)

    def test_payload_tax_type_is_integer(self):
        assert isinstance(generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["tax_type_ref_id"], int)

    def test_payload_tax_authority_is_integer(self):
        assert isinstance(generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["tax_authority_ref_id"], int)

    def test_payload_from_date_is_string(self):
        assert isinstance(generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["from_date"], str)

    def test_payload_to_date_is_string(self):
        assert isinstance(generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["to_date"], str)

    def test_payload_revision_status_is_active(self):
        assert generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["revision_status"] == "Active"

    def test_payload_tax_type_in_valid_pool(self):
        valid = set(MOCK_FK_IDS["tax_type_ref_id"].values())
        for p in generate_tax_rate_api_payloads(count=5, fk_ids=MOCK_FK_IDS):
            assert p["tax_type_ref_id"] in valid

    def test_payload_tax_authority_in_valid_pool(self):
        valid = set(MOCK_FK_IDS["tax_authority_ref_id"].values())
        for p in generate_tax_rate_api_payloads(count=5, fk_ids=MOCK_FK_IDS):
            assert p["tax_authority_ref_id"] in valid

    def test_payload_stepper_details_have_hsn_sac(self):
        p = generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]
        details = p["children"][0]["details"]
        for line in details:
            assert "hsn_sac_number" in line
            assert "tax_rate" in line

    def test_payload_stepper_hsn_sac_in_valid_pool(self):
        valid = set(MOCK_HSN_SAC_IDS.values())
        p = generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]
        for line in p["children"][0]["details"]:
            assert line["hsn_sac_number"] in valid

    def test_payload_stepper_tax_rate_is_numeric(self):
        p = generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]
        for line in p["children"][0]["details"]:
            assert isinstance(line["tax_rate"], (int, float))

    def test_build_with_explicit_values(self):
        p = build_tax_rate_api_payload(
            tax_rate_name="GST 18%", tax_type_ref_id=93, tax_authority_ref_id=103,
            from_date="2025-04-01", to_date="2026-03-31",
            tax_detail_lines=[{"hsn_sac_number": 108, "tax_rate": 18.0}],
        )
        assert p["tax_rate_name"] == "GST 18%"
        assert p["tax_type_ref_id"] == 93
        assert p["children"][0]["details"][0]["tax_rate"] == 18.0

    def test_payload_root_has_no_details(self):
        p = generate_tax_rate_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]
        assert "details" not in p

    def test_generate_raises_without_fk_ids(self):
        with pytest.raises(ValueError, match="fk_ids is required"):
            generate_tax_rate_api_payloads(count=1, fk_ids=None)


@pytest.mark.api
class TestTaxRateBatchGeneration:
    def test_batch_count(self):
        assert len(generate_batch_payloads(count=5, dropdown_ids=MOCK_FK_IDS)) == 5

    def test_batch_default_20(self):
        assert len(generate_batch_payloads(count=20, dropdown_ids=MOCK_FK_IDS)) == 20

    def test_batch_all_attribute_name(self):
        for p in generate_batch_payloads(count=10, dropdown_ids=MOCK_FK_IDS):
            assert p["attribute_name"] == "Tax Rate"

    def test_batch_all_have_children(self):
        for p in generate_batch_payloads(count=10, dropdown_ids=MOCK_FK_IDS):
            assert isinstance(p["children"], list)
            assert len(p["children"]) >= 1

    def test_batch_all_fk_valid(self):
        vt = set(MOCK_FK_IDS["tax_type_ref_id"].values())
        va = set(MOCK_FK_IDS["tax_authority_ref_id"].values())
        for p in generate_batch_payloads(count=10, dropdown_ids=MOCK_FK_IDS):
            assert p["tax_type_ref_id"] in vt
            assert p["tax_authority_ref_id"] in va

    def test_batch_raises_without_dropdown_ids(self):
        with pytest.raises(ValueError, match="dropdown_ids is required"):
            generate_batch_payloads(count=5)
