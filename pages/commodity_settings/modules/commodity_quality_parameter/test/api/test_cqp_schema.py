"""
test_cqp_schema.py — Verify Commodity Quality Parameter code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.commodity_quality_parameter.data.commodity_quality_parameter_data import (
    FIELD_VALIDATION_RULES,
    ITEM_ID_MAP,
    TRANSACTION_TYPE_ID_MAP,
    QUALITY_PARAM_ID_MAP,
    ITEM_NAMES,
    TRANSACTION_TYPE_NAMES,
    QUALITY_PARAM_NAMES,
    DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS,
    STEPPER_NAME,
)


@pytest.mark.schema
class TestCQPSchema:
    """Verify the Commodity Quality Parameter screen schema matches our code expectations."""

    # ── Field count and presence ──

    def test_has_10_fields(self):
        """CQP should have 10 fields in FIELD_VALIDATION_RULES (5 root + 5 stepper)."""
        assert len(FIELD_VALIDATION_RULES) == 10

    def test_has_root_fields(self):
        """FIELD_VALIDATION_RULES must include all root CQP fields."""
        root = {"item_ref_id", "transaction_type", "from_date", "to_date", "revision_status"}
        assert root.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_has_stepper_fields(self):
        """FIELD_VALIDATION_RULES must include all stepper detail fields."""
        stepper = {"quality_type", "min_quality_value", "max_quality_value",
                   "rate_percentage", "multiplier"}
        assert stepper.issubset(set(FIELD_VALIDATION_RULES.keys()))

    # ── Required fields ──

    def test_item_ref_id_required(self):
        """item_ref_id should be marked as required."""
        assert FIELD_VALIDATION_RULES["item_ref_id"]["required"] is True

    def test_transaction_type_required(self):
        """transaction_type should be marked as required."""
        assert FIELD_VALIDATION_RULES["transaction_type"]["required"] is True

    def test_revision_status_not_required(self):
        """revision_status should be optional."""
        assert FIELD_VALIDATION_RULES["revision_status"]["required"] is False

    def test_quality_type_required(self):
        """quality_type in stepper should be marked as required."""
        assert FIELD_VALIDATION_RULES["quality_type"]["required"] is True

    # ── Field types ──

    def test_item_ref_id_is_dropdown(self):
        """item_ref_id should be type='dropdown'."""
        assert FIELD_VALIDATION_RULES["item_ref_id"]["type"] == "dropdown"

    def test_transaction_type_is_dropdown(self):
        """transaction_type should be type='dropdown'."""
        assert FIELD_VALIDATION_RULES["transaction_type"]["type"] == "dropdown"

    def test_from_date_is_date(self):
        """from_date should be type='date'."""
        assert FIELD_VALIDATION_RULES["from_date"]["type"] == "date"

    def test_to_date_is_date(self):
        """to_date should be type='date'."""
        assert FIELD_VALIDATION_RULES["to_date"]["type"] == "date"

    def test_revision_status_is_character(self):
        """revision_status should be type='character'."""
        assert FIELD_VALIDATION_RULES["revision_status"]["type"] == "character"

    def test_quality_type_is_dropdown(self):
        """quality_type should be type='dropdown'."""
        assert FIELD_VALIDATION_RULES["quality_type"]["type"] == "dropdown"

    def test_rate_percentage_is_toggle(self):
        """rate_percentage should be type='toggle'."""
        assert FIELD_VALIDATION_RULES["rate_percentage"]["type"] == "toggle"

    # ── FK options counts ──

    def test_item_ref_id_options_count(self):
        """item_ref_id fk_options_count should match ITEM_ID_MAP length."""
        assert FIELD_VALIDATION_RULES["item_ref_id"]["fk_options_count"] == len(ITEM_ID_MAP)

    def test_transaction_type_has_8_options(self):
        """Transaction Type should have 8 options."""
        assert FIELD_VALIDATION_RULES["transaction_type"]["fk_options_count"] == 8

    def test_quality_type_options_count(self):
        """quality_type fk_options_count should match QUALITY_PARAM_ID_MAP length."""
        assert FIELD_VALIDATION_RULES["quality_type"]["fk_options_count"] == len(QUALITY_PARAM_ID_MAP)

    # ── Toggle defaults ──

    def test_rate_percentage_default_is_false(self):
        """rate_percentage default should be False."""
        assert FIELD_VALIDATION_RULES["rate_percentage"]["default"] is False

    # ── Default FK IDs structure ──

    def test_default_fk_ids_has_item_ref_id(self):
        """DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS must have item_ref_id pool."""
        assert "item_ref_id" in DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS

    def test_default_fk_ids_has_transaction_type(self):
        """DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS must have transaction_type pool."""
        assert "transaction_type" in DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS

    def test_default_fk_ids_has_quality_type(self):
        """DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS must have quality_type pool."""
        assert "quality_type" in DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS

    def test_default_fk_ids_pools_match_source(self):
        """DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS pools should match source ID maps."""
        assert DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS["item_ref_id"] == ITEM_ID_MAP
        assert DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS["transaction_type"] == TRANSACTION_TYPE_ID_MAP
        assert DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS["quality_type"] == QUALITY_PARAM_ID_MAP

    # ── FK pool lengths match rules ──

    def test_fk_pool_lengths_match_rules(self):
        """FK pool lengths should match the fk_options_count in FIELD_VALIDATION_RULES."""
        for field_name, rules in FIELD_VALIDATION_RULES.items():
            if rules["type"] == "dropdown" and "fk_options_count" in rules:
                if field_name in DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS:
                    actual = len(DEFAULT_COMMODITY_QUALITY_PARAMETER_FK_IDS[field_name])
                    expected = rules["fk_options_count"]
                    assert actual == expected, \
                        f"{field_name}: pool has {actual} options, rules say {expected}"

    # ── Name mappings ──

    def test_item_names_matches(self):
        """ITEM_NAMES should match ITEM_ID_MAP."""
        assert ITEM_NAMES == ITEM_ID_MAP

    def test_transaction_type_names_matches(self):
        """TRANSACTION_TYPE_NAMES should match TRANSACTION_TYPE_ID_MAP."""
        assert TRANSACTION_TYPE_NAMES == TRANSACTION_TYPE_ID_MAP

    def test_quality_param_names_matches(self):
        """QUALITY_PARAM_NAMES should match QUALITY_PARAM_ID_MAP."""
        assert QUALITY_PARAM_NAMES == QUALITY_PARAM_ID_MAP

    # ── Stepper name ──

    def test_stepper_name_is_correct(self):
        """STEPPER_NAME should be 'Define Item Quality Parameter Details'."""
        assert STEPPER_NAME == "Define Item Quality Parameter Details"

    # ── No duplicate ID values ──

    def test_item_ids_no_dup_values(self):
        """ITEM_ID_MAP should not have duplicate ID values."""
        values = list(ITEM_ID_MAP.values())
        assert len(values) == len(set(values))

    def test_transaction_type_ids_no_dup_values(self):
        """TRANSACTION_TYPE_ID_MAP should not have duplicate ID values."""
        values = list(TRANSACTION_TYPE_ID_MAP.values())
        assert len(values) == len(set(values))

    def test_quality_param_ids_no_dup_values(self):
        """QUALITY_PARAM_ID_MAP should not have duplicate ID values."""
        values = list(QUALITY_PARAM_ID_MAP.values())
        assert len(values) == len(set(values))
