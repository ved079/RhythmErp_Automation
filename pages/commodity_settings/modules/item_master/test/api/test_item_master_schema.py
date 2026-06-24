"""test_item_master_schema.py — Verify Item Master code matches live ERP schema."""
import pytest, sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
from pages.commodity_settings.modules.item_master.data.item_master_data import (
    FIELD_VALIDATION_RULES,
    ITEM_CATEGORY_OPTIONS, ITEM_GROUP_OPTIONS, ITEM_TYPE_OPTIONS,
    ITEM_ATTRIBUTE1_OPTIONS, ITEM_ATTRIBUTE2_OPTIONS, ITEM_ATTRIBUTE3_OPTIONS,
    ITEM_ATTRIBUTE4_OPTIONS, ITEM_ATTRIBUTE5_OPTIONS,
    UOM_OPTIONS, HSN_SAC_CODE_OPTIONS, BASE_UOM_OPTIONS,
    ITEM_SOURCING_OPTIONS,
    ITEM_CATEGORY_NAMES, ITEM_GROUP_NAMES, ITEM_TYPE_NAMES,
    ITEM_ATTRIBUTE1_NAMES, ITEM_ATTRIBUTE2_NAMES, ITEM_ATTRIBUTE3_NAMES,
    ITEM_ATTRIBUTE4_NAMES, ITEM_ATTRIBUTE5_NAMES,
    UOM_NAMES, HSN_SAC_CODE_NAMES, BASE_UOM_NAMES,
    ITEM_SOURCING_NAMES,
    DEFAULT_ITEM_MASTER_FK_IDS, STATUS_OPTIONS, STEPPER_NAMES,
)


@pytest.mark.schema
class TestItemMasterSchema:
    # ── Field count ────────────────────────────────────────────────────
    def test_has_20_fields(self):
        """17 root fields (incl. item_sourcing) + 3 stepper toggles = 20."""
        assert len(FIELD_VALIDATION_RULES) == 20

    def test_has_root_fields(self):
        root = {"name", "code", "description", "base_uom_conversion",
                "item_category", "item_type", "uom", "hsn_sac_code",
                "base_uom", "item_group", "item_attribute1", "item_attribute2",
                "item_attribute3", "item_attribute4", "item_attribute5", "status"}
        assert root.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_has_fk_dropdown_fields(self):
        """All 11 FK dropdown fields must be present (incl. item_sourcing)."""
        fk_fields = {"item_category", "item_type", "uom", "hsn_sac_code",
                     "base_uom", "item_group", "item_sourcing",
                     "item_attribute1", "item_attribute2", "item_attribute3",
                     "item_attribute4", "item_attribute5"}
        assert fk_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_has_stepper_toggles(self):
        stepper_toggles = {"is_critical", "include_wip_in_stock_cal", "is_packing_material"}
        assert stepper_toggles.issubset(set(FIELD_VALIDATION_RULES.keys()))

    # ── Required fields ────────────────────────────────────────────────
    def test_item_category_required(self):
        assert FIELD_VALIDATION_RULES["item_category"]["required"] is True

    def test_item_type_required(self):
        assert FIELD_VALIDATION_RULES["item_type"]["required"] is True

    def test_uom_required(self):
        assert FIELD_VALIDATION_RULES["uom"]["required"] is True

    def test_hsn_sac_code_required(self):
        assert FIELD_VALIDATION_RULES["hsn_sac_code"]["required"] is True

    def test_base_uom_required(self):
        assert FIELD_VALIDATION_RULES["base_uom"]["required"] is True

    def test_base_uom_conversion_required(self):
        assert FIELD_VALIDATION_RULES["base_uom_conversion"]["required"] is True

    def test_item_sourcing_required(self):
        assert FIELD_VALIDATION_RULES["item_sourcing"]["required"] is True

    # ── Not-required fields ────────────────────────────────────────────
    def test_name_not_required(self):
        assert FIELD_VALIDATION_RULES["name"]["required"] is False

    def test_code_not_required(self):
        assert FIELD_VALIDATION_RULES["code"]["required"] is False

    def test_description_not_required(self):
        assert FIELD_VALIDATION_RULES["description"]["required"] is False

    def test_item_group_not_required(self):
        assert FIELD_VALIDATION_RULES["item_group"]["required"] is False

    def test_item_attribute1_required(self):
        assert FIELD_VALIDATION_RULES["item_attribute1"]["required"] is True

    def test_status_not_required(self):
        assert FIELD_VALIDATION_RULES["status"]["required"] is False

    # ── Field types ────────────────────────────────────────────────────
    def test_item_category_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["item_category"]["type"] == "dropdown"

    def test_item_type_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["item_type"]["type"] == "dropdown"

    def test_uom_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["uom"]["type"] == "dropdown"

    def test_hsn_sac_code_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["hsn_sac_code"]["type"] == "dropdown"

    def test_base_uom_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["base_uom"]["type"] == "dropdown"

    def test_item_group_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["item_group"]["type"] == "dropdown"

    def test_item_attribute1_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["item_attribute1"]["type"] == "dropdown"

    def test_item_sourcing_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["item_sourcing"]["type"] == "dropdown"

    def test_status_is_toggle(self):
        assert FIELD_VALIDATION_RULES["status"]["type"] == "toggle"

    def test_is_critical_is_toggle(self):
        assert FIELD_VALIDATION_RULES["is_critical"]["type"] == "toggle"

    def test_include_wip_is_toggle(self):
        assert FIELD_VALIDATION_RULES["include_wip_in_stock_cal"]["type"] == "toggle"

    def test_is_packing_material_is_toggle(self):
        assert FIELD_VALIDATION_RULES["is_packing_material"]["type"] == "toggle"

    # ── Defaults ───────────────────────────────────────────────────────
    def test_status_default_true(self):
        assert FIELD_VALIDATION_RULES["status"]["default"] is True

    def test_is_critical_default_false(self):
        assert FIELD_VALIDATION_RULES["is_critical"]["default"] is False

    # ── FK pool checks ─────────────────────────────────────────────────
    def test_default_fk_ids_has_13_pools(self):
        """13 FK pools: 10 FK dropdowns + base_uom (same pool as uom) + item_sourcing + sourcing_type."""
        assert len(DEFAULT_ITEM_MASTER_FK_IDS) == 13

    def test_fk_pool_lengths_match_rules(self):
        for fn, r in FIELD_VALIDATION_RULES.items():
            if r["type"] == "dropdown" and "fk_options_count" in r:
                if fn in DEFAULT_ITEM_MASTER_FK_IDS:
                    assert len(DEFAULT_ITEM_MASTER_FK_IDS[fn]) == r["fk_options_count"], \
                        f"FK pool length mismatch for {fn}"

    # ── Stepper names ──────────────────────────────────────────────────
    def test_stepper_names_correct(self):
        assert STEPPER_NAMES == ["Additional Details", "Define Item Master Details",
                                 "Product Order Packeging Details"]

    # ── No duplicate FK IDs ────────────────────────────────────────────
    def test_item_category_ids_no_dup_values(self):
        v = list(ITEM_CATEGORY_OPTIONS.values())
        assert len(v) == len(set(v))

    def test_uom_ids_no_dup_values(self):
        v = list(UOM_OPTIONS.values())
        assert len(v) == len(set(v))

    def test_hsn_sac_ids_no_dup_values(self):
        v = list(HSN_SAC_CODE_OPTIONS.values())
        assert len(v) == len(set(v))
