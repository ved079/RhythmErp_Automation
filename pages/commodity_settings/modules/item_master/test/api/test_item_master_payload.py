"""test_item_master_payload.py — Fast API payload structure tests for Item Master."""
import pytest, sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
from pages.commodity_settings.modules.item_master.data.item_master_data import (
    build_item_master_api_payload, generate_item_master_payloads,
    generate_batch_payloads,
    ITEM_CATEGORY_OPTIONS, ITEM_GROUP_OPTIONS, ITEM_TYPE_OPTIONS,
    ITEM_ATTRIBUTE1_OPTIONS, ITEM_ATTRIBUTE2_OPTIONS, ITEM_ATTRIBUTE3_OPTIONS,
    ITEM_ATTRIBUTE4_OPTIONS, ITEM_ATTRIBUTE5_OPTIONS,
    UOM_OPTIONS, HSN_SAC_CODE_OPTIONS, BASE_UOM_OPTIONS,
    DEFAULT_ITEM_MASTER_FK_IDS, STEPPER_NAMES,
)


@pytest.mark.api
class TestItemMasterAPIPayload:
    def test_payload_has_required_keys(self):
        p = generate_item_master_payloads(count=1)[0]
        for k in ["id", "attribute_name", "name", "code", "description",
                   "item_category", "item_type", "uom", "hsn_sac_code",
                   "base_uom", "base_uom_conversion", "status", "children"]:
            assert k in p, f"Missing key: {k}"

    def test_payload_has_children_with_steppers(self):
        p = generate_item_master_payloads(count=1)[0]
        assert isinstance(p["children"], list)
        assert len(p["children"]) >= 1
        for child in p["children"]:
            assert child["is_stepper"] is True
            assert "stepper_name" in child
            assert "details" in child

    def test_payload_attribute_name(self):
        assert generate_item_master_payloads(count=1)[0]["attribute_name"] == "Item Master"

    def test_payload_id_empty(self):
        assert generate_item_master_payloads(count=1)[0]["id"] == ""

    def test_payload_name_is_string(self):
        assert isinstance(generate_item_master_payloads(count=1)[0]["name"], str)

    def test_payload_code_is_string(self):
        assert isinstance(generate_item_master_payloads(count=1)[0]["code"], str)

    def test_payload_description_is_string(self):
        assert isinstance(generate_item_master_payloads(count=1)[0]["description"], str)

    def test_payload_item_category_is_integer(self):
        assert isinstance(generate_item_master_payloads(count=1)[0]["item_category"], int)

    def test_payload_item_type_is_integer(self):
        assert isinstance(generate_item_master_payloads(count=1)[0]["item_type"], int)

    def test_payload_uom_is_integer(self):
        assert isinstance(generate_item_master_payloads(count=1)[0]["uom"], int)

    def test_payload_hsn_sac_code_is_integer(self):
        assert isinstance(generate_item_master_payloads(count=1)[0]["hsn_sac_code"], int)

    def test_payload_base_uom_is_integer(self):
        assert isinstance(generate_item_master_payloads(count=1)[0]["base_uom"], int)

    def test_payload_base_uom_conversion_is_string(self):
        assert isinstance(generate_item_master_payloads(count=1)[0]["base_uom_conversion"], str)

    def test_payload_status_is_boolean(self):
        assert isinstance(generate_item_master_payloads(count=1)[0]["status"], bool)

    def test_payload_root_has_no_details(self):
        """Root payload should NOT have a 'details' key — details live in children."""
        p = generate_item_master_payloads(count=1)[0]
        assert "details" not in p

    def test_payload_has_3_children(self):
        p = generate_item_master_payloads(count=1)[0]
        assert len(p["children"]) == 3

    def test_payload_stepper_names_correct(self):
        p = generate_item_master_payloads(count=1)[0]
        actual_names = [c["stepper_name"] for c in p["children"]]
        assert actual_names == STEPPER_NAMES

    def test_payload_stepper1_has_toggles(self):
        """Stepper 'Additional Details' (children[0]) must have 3 toggles."""
        p = generate_item_master_payloads(count=1)[0]
        child0 = p["children"][0]
        assert "is_critical" in child0
        assert "include_wip_in_stock_cal" in child0
        assert "is_packing_material" in child0

    def test_payload_fk_ids_in_valid_pools(self):
        """All 10 FK IDs must be valid IDs from their respective option pools."""
        p = generate_item_master_payloads(count=1)[0]
        valid_cat = set(ITEM_CATEGORY_OPTIONS.values())
        valid_grp = set(ITEM_GROUP_OPTIONS.values())
        valid_type = set(ITEM_TYPE_OPTIONS.values())
        valid_attr1 = set(ITEM_ATTRIBUTE1_OPTIONS.values())
        valid_attr2 = set(ITEM_ATTRIBUTE2_OPTIONS.values())
        valid_attr3 = set(ITEM_ATTRIBUTE3_OPTIONS.values())
        valid_attr4 = set(ITEM_ATTRIBUTE4_OPTIONS.values())
        valid_attr5 = set(ITEM_ATTRIBUTE5_OPTIONS.values())
        valid_uom = set(UOM_OPTIONS.values())
        valid_hsn = set(HSN_SAC_CODE_OPTIONS.values())
        valid_buom = set(BASE_UOM_OPTIONS.values())

        assert p["item_category"] in valid_cat
        assert p["item_group"] in valid_grp
        assert p["item_type"] in valid_type
        assert p["item_attribute1"] in valid_attr1
        assert p["item_attribute2"] in valid_attr2
        assert p["item_attribute3"] in valid_attr3
        assert p["item_attribute4"] in valid_attr4
        assert p["item_attribute5"] in valid_attr5
        assert p["uom"] in valid_uom
        assert p["hsn_sac_code"] in valid_hsn
        assert p["base_uom"] in valid_buom

    def test_build_with_explicit_values(self):
        p = build_item_master_api_payload(
            category="Food Grains", group="GRN001", item_type="Farm",
            attr1="Wheat", attr2="Premium Grade", attr3="Product Grade",
            attr4="Multi Layered", attr5="Organic Certified",
            uom="KG", base_uom="KG", hsn="1001",
            description="Explicit build test",
            base_uom_conversion="5",
            is_critical=True, include_wip=True, is_packing_material=True,
            status=False,
        )
        assert p["description"] == "Explicit build test"
        assert p["item_category"] == ITEM_CATEGORY_OPTIONS["Food Grains"]
        assert p["item_group"] == ITEM_GROUP_OPTIONS["GRN001"]
        assert p["item_type"] == ITEM_TYPE_OPTIONS["Farm"]
        assert p["item_attribute1"] == ITEM_ATTRIBUTE1_OPTIONS["Wheat"]
        assert p["base_uom_conversion"] == "5"
        assert p["status"] is False
        assert p["children"][0]["is_critical"] is True
        assert p["children"][0]["include_wip_in_stock_cal"] is True
        assert p["children"][0]["is_packing_material"] is True


@pytest.mark.api
class TestItemMasterBatchGeneration:
    def test_batch_correct_count(self):
        assert len(generate_batch_payloads(count=5)) == 5

    def test_batch_default_20(self):
        assert len(generate_batch_payloads()) == 20

    def test_batch_all_attribute_name(self):
        for p in generate_batch_payloads(count=10):
            assert p["attribute_name"] == "Item Master"

    def test_batch_all_have_children(self):
        for p in generate_batch_payloads(count=10):
            assert isinstance(p["children"], list)
            assert len(p["children"]) == 3

    def test_batch_all_fk_valid(self):
        vc = set(ITEM_CATEGORY_OPTIONS.values())
        vt = set(ITEM_TYPE_OPTIONS.values())
        vu = set(UOM_OPTIONS.values())
        vh = set(HSN_SAC_CODE_OPTIONS.values())
        vb = set(BASE_UOM_OPTIONS.values())
        for p in generate_batch_payloads(count=10):
            assert p["item_category"] in vc
            assert p["item_type"] in vt
            assert p["uom"] in vu
            # hsn_sac_code may be None if data pool code not in options dict
            if p["hsn_sac_code"] is not None:
                assert p["hsn_sac_code"] in vh
            assert p["base_uom"] in vb

    def test_batch_all_status_true(self):
        for p in generate_batch_payloads(count=10):
            assert p["status"] is True

    def test_batch_root_has_no_details(self):
        for p in generate_batch_payloads(count=10):
            assert "details" not in p
