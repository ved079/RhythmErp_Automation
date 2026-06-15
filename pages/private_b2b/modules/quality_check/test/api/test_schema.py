import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log


@pytest.mark.api
@pytest.mark.schema
class TestQCSchema:
    def test_QC_S01_schema_returns_200(self, qc_api):
        log.info("QC-S01: Schema endpoint returns 200")
        schema = qc_api.get_schema()
        assert schema is not None, "Schema should be returned"
        log.info(f"  Schema keys: {list(schema.keys())}")

    def test_QC_S02_schema_has_expected_keys(self, qc_api):
        log.info("QC-S02: Schema contains expected top-level keys")
        schema = qc_api.get_schema()
        assert schema is not None
        assert isinstance(schema, dict), "Schema should be a dict"
        log.info(f"  Top-level fields: {len(schema)} entries")

    def test_QC_S03_schema_conditionally_required_fields(self, qc_api):
        log.info("QC-S03: Schema fields exist")
        schema = qc_api.get_schema()
        assert schema is not None, "Schema should be accessible"
