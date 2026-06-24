"""test_tax_authority_payload.py — Fast API payload structure tests for Tax Authority."""
import pytest, sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
from pages.common_settings.modules.tax_authority.data.tax_authority_data import (
    build_tax_authority_api_payload, generate_tax_authority_api_payloads,
    generate_batch_payloads,
)

MOCK_FK_IDS = {
    "tax_type_ref_id": {"GST": 93},
    "country_ref_id": {"India": 1, "Dubai": 2, "USA": 3},
}

@pytest.mark.api
class TestTaxAuthorityAPIPayload:
    def test_payload_has_required_keys(self):
        p = generate_tax_authority_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]
        for k in ["id", "attribute_name", "tax_name", "tax_type_ref_id", "country_ref_id"]:
            assert k in p

    def test_payload_is_flat_no_children(self):
        p = generate_tax_authority_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]
        assert "children" not in p and "details" not in p

    def test_payload_attribute_name(self):
        assert generate_tax_authority_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["attribute_name"] == "Tax Authority"

    def test_payload_id_is_empty(self):
        assert generate_tax_authority_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["id"] == ""

    def test_payload_tax_name_is_string(self):
        assert isinstance(generate_tax_authority_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["tax_name"], str)

    def test_payload_tax_type_is_integer(self):
        assert isinstance(generate_tax_authority_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["tax_type_ref_id"], int)

    def test_payload_country_is_integer(self):
        assert isinstance(generate_tax_authority_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["country_ref_id"], int)

    def test_payload_tax_type_in_valid_pool(self):
        valid = set(MOCK_FK_IDS["tax_type_ref_id"].values())
        for p in generate_tax_authority_api_payloads(count=5, fk_ids=MOCK_FK_IDS):
            assert p["tax_type_ref_id"] in valid

    def test_payload_country_in_valid_pool(self):
        valid = set(MOCK_FK_IDS["country_ref_id"].values())
        for p in generate_tax_authority_api_payloads(count=5, fk_ids=MOCK_FK_IDS):
            assert p["country_ref_id"] in valid

    def test_build_with_explicit_values(self):
        p = build_tax_authority_api_payload("Test Auth", 93, 1)
        assert p["tax_name"] == "Test Auth"
        assert p["tax_type_ref_id"] == 93
        assert p["country_ref_id"] == 1

    def test_generate_raises_without_fk_ids(self):
        with pytest.raises(ValueError, match="fk_ids is required"):
            generate_tax_authority_api_payloads(count=1, fk_ids=None)

@pytest.mark.api
class TestTaxAuthorityBatchGeneration:
    def test_batch_count(self):
        assert len(generate_batch_payloads(count=5, dropdown_ids=MOCK_FK_IDS)) == 5

    def test_batch_default_20(self):
        assert len(generate_batch_payloads(count=20, dropdown_ids=MOCK_FK_IDS)) == 20

    def test_batch_all_attribute_name(self):
        for p in generate_batch_payloads(count=10, dropdown_ids=MOCK_FK_IDS):
            assert p["attribute_name"] == "Tax Authority"

    def test_batch_all_fk_valid(self):
        vt = set(MOCK_FK_IDS["tax_type_ref_id"].values())
        vc = set(MOCK_FK_IDS["country_ref_id"].values())
        for p in generate_batch_payloads(count=10, dropdown_ids=MOCK_FK_IDS):
            assert p["tax_type_ref_id"] in vt
            assert p["country_ref_id"] in vc

    def test_batch_all_flat(self):
        for p in generate_batch_payloads(count=10, dropdown_ids=MOCK_FK_IDS):
            assert "children" not in p and "details" not in p

    def test_batch_raises_without_dropdown_ids(self):
        with pytest.raises(ValueError, match="dropdown_ids is required"):
            generate_batch_payloads(count=5)
