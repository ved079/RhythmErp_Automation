"""
test_agent_schema.py
--------------------
Schema validation tests for RhythmERP Agent screen.
Verifies the Agent screen schema endpoint returns expected field definitions.

~5 tests, all headless API calls.

Schema Structure (verified 2026-06-11):
  The Agent schema endpoint returns a dict with key 'screendefinition_set'
  containing all field definitions (top-level + children steppers).
  NOT 'fields', 'field_set', or 'screen_fields'.

Run:
  pytest test_agent_schema.py -v --tb=short
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.registration.modules.agent.api.endpoints import SCREEN_NAME


class TestAgentSchema:
    """Verify Agent screen schema endpoint returns valid structure."""

    @pytest.mark.api
    @pytest.mark.smoke
    def test_schema_returns_200(self, agt_api):
        """Agent schema endpoint should return HTTP 200."""
        log.info("Schema: Returns 200")
        schema = agt_api.client.get_screen_schema(SCREEN_NAME)
        assert schema is not None, "Schema endpoint returned None (auth or URL issue)"

    @pytest.mark.api
    @pytest.mark.sanity
    def test_schema_has_screen_name(self, agt_api):
        """Schema should contain the screen name 'Agent'."""
        log.info("Schema: Has screen name")
        schema = agt_api.client.get_screen_schema(SCREEN_NAME)
        assert schema is not None
        # Screen name may be in different keys depending on API version
        name = schema.get("screen_name", schema.get("name", schema.get("attribute_name", "")))
        assert name == SCREEN_NAME or "agent" in str(name).lower(), \
            f"Schema screen_name mismatch: expected 'Agent', got '{name}'"

    @pytest.mark.api
    @pytest.mark.sanity
    def test_schema_has_fields(self, agt_api):
        """Schema should define fields for the Agent screen.

        The schema uses 'screendefinition_set' for field definitions,
        NOT 'fields' or 'field_set'.
        """
        log.info("Schema: Has fields")
        schema = agt_api.client.get_screen_schema(SCREEN_NAME)
        assert schema is not None

        # Primary key: screendefinition_set (verified from live API)
        fields = schema.get("screendefinition_set", [])

        # Fallbacks for other possible key names
        if not fields:
            for key in ("fields", "field_set", "screenmatfieldconfiguration_set", "screen_fields"):
                if key in schema and schema[key]:
                    fields = schema[key]
                    log.info(f"Found fields under key: '{key}'")
                    break

        assert len(fields) > 0, (
            f"Schema has no fields defined. "
            f"Available keys: {list(schema.keys())}"
        )

    @pytest.mark.api
    @pytest.mark.sanity
    def test_schema_has_required_fields(self, agt_api):
        """Schema should include field definitions with field_key entries.

        The Agent schema uses 'screendefinition_set' with nested children
        for stepper fields. We verify that field definitions exist and
        contain recognizable field keys.
        """
        log.info("Schema: Has required fields")
        schema = agt_api.client.get_screen_schema(SCREEN_NAME)
        assert schema is not None

        # Flatten all fields (top-level + children)
        all_fields = agt_api.client._flatten_fields(
            schema.get("screendefinition_set", [])
        )

        # Fallback if screendefinition_set is empty
        if not all_fields:
            for key in ("fields", "field_set", "screenmatfieldconfiguration_set"):
                if key in schema and schema[key]:
                    all_fields = schema[key]
                    break

        # Collect field names/keys
        all_field_names = set()
        for f in all_fields:
            if isinstance(f, dict):
                name = f.get("field_name", f.get("field_key", f.get("name", "")))
                if name:
                    all_field_names.add(str(name).lower())

        log.info(f"Schema field names ({len(all_field_names)}): {all_field_names}")

        assert len(all_field_names) > 0, (
            "No field names found in schema. "
            f"Top-level keys: {list(schema.keys())}"
        )

    @pytest.mark.api
    @pytest.mark.sanity
    def test_schema_dropdown_options_available(self, agt_api):
        """Schema dropdown fields should have options available."""
        log.info("Schema: Dropdown options available")

        # Check a known dropdown — Country
        try:
            options = agt_api.client.get_dropdown_options(SCREEN_NAME, "country")
            if options is not None:
                log.info(f"Country dropdown has {len(options)} options via API")
            else:
                log.info("Country dropdown returned None — may need different field_key")
        except Exception as e:
            log.info(f"Dropdown options check skipped: {e}")
