import pytest
import sys
import os
from datetime import datetime

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.uom_conversion.data.uom_conversion_data import (
    build_uom_conversion_api_payload,
    generate_batch_payloads,
)


def _build_state(api_client):
    """Fetch UOM id->code map and existing conversion pairs (as code strings).
    The listing returns source_uom_code/target_uom_code as string codes, not IDs.
    Returns: (id_to_code dict, existing_code_pairs set)"""
    uom = api_client.list_entries("UOM", page=1, page_size=200)
    uom_rows = uom.get("screenmatlistingdata_set", []) if uom else []
    id_to_code = {row["id"]: row.get("uom_code", str(row["id"])) for row in uom_rows}

    conv = api_client.list_entries("UOM Conversion", page=1, page_size=500)
    conv_rows = conv.get("screenmatlistingdata_set", []) if conv else []
    existing_code_pairs = {
        (row.get("source_uom_code"), row.get("target_uom_code")) for row in conv_rows
    }
    return id_to_code, existing_code_pairs


def _fetch_unused_pair(api_client, state=None):
    """Return (src_id, tgt_id, updated_state) for a pair with no existing conversion.
    Compares by UOM code strings since that is what the listing API returns."""
    if state is None:
        state = _build_state(api_client)
    id_to_code, existing_code_pairs = state

    ids = list(id_to_code.keys())
    assert len(ids) >= 2, f"Tenant must have at least 2 UOM records. Found: {len(ids)}"

    for src_id in ids:
        for tgt_id in ids:
            if src_id == tgt_id:
                continue
            pair = (id_to_code[src_id], id_to_code[tgt_id])
            if pair not in existing_code_pairs:
                existing_code_pairs.add(pair)
                return src_id, tgt_id, (id_to_code, existing_code_pairs)

    pytest.fail("No unused (source, target) UOM pair available on this tenant.")


@pytest.mark.live_api
class TestUOMConversionLiveAPI:
    """Live CRUD tests against the real ERP API. Tenant-universal — no hardcoded IDs."""

    def test_duplicate_pair_rejected(self, api_client):
        """Create a conversion pair, then POST the same pair again — second must fail."""
        src_id, tgt_id, _ = _fetch_unused_pair(api_client)
        try:
            first = api_client.create_entry({
                "id": "", "attribute_name": "UOM Conversion",
                "source_uom_code": src_id, "target_uom_code": tgt_id,
                "conversion_factor": 5,
            })
            assert first is not None and first.get("id"), "First create must succeed"

            second = api_client.create_entry({
                "id": "", "attribute_name": "UOM Conversion",
                "source_uom_code": src_id, "target_uom_code": tgt_id,
                "conversion_factor": 10,
            })
            assert second is None or "id" not in second, \
                "Duplicate (source, target) pair must be rejected by ERP"
        finally:
            pass  # No delete API

    def test_create_boundary_cases(self, api_client):
        """Create conversions: decimal factor, large-but-valid integer, same source==target.
        Backend max is ~9 digits (< 1 billion). Decimals accepted. Bug #1 (22-digit
        scientific notation) is UI-only — API rejects oversized factors outright."""
        state = None
        try:
            # Each case needs its own unique pair — fetch 3 unused pairs
            src1, tgt1, state = _fetch_unused_pair(api_client, state)
            src2, tgt2, state = _fetch_unused_pair(api_client, state)
            src3, tgt3, state = _fetch_unused_pair(api_client, state)

            cases = [
                ("decimal_factor",      src1, tgt1, 0.5),
                ("large_valid_integer", src2, tgt2, 999999),
                ("same_source_target",  src3, src3, 1),
            ]
            for label, s, t, factor in cases:
                result = api_client.create_entry({
                    "id": "", "attribute_name": "UOM Conversion",
                    "source_uom_code": s, "target_uom_code": t,
                    "conversion_factor": factor,
                })
                assert result is not None and result.get("id"), \
                    f"Create failed for case: {label}"
        finally:
            pass  # No delete API

    def test_create_factor_types(self, api_client):
        """Verify factor type rules: integer OK, decimal OK, oversized integer rejected.
        Backend accepts up to ~9 digits (confirmed max ~522,222,222). Rejects >= 1 billion."""
        src_ok, tgt_ok, state = _fetch_unused_pair(api_client)
        src_big, tgt_big, state = _fetch_unused_pair(api_client, state)

        # Valid: 9-digit integer
        result = api_client.create_entry({
            "id": "", "attribute_name": "UOM Conversion",
            "source_uom_code": src_ok, "target_uom_code": tgt_ok,
            "conversion_factor": 522222222,
        })
        assert result is not None and result.get("id"), \
            "9-digit integer (522222222) must be accepted by backend"

        # Invalid: 10-digit integer (>= 1 billion rejected)
        result_big = api_client.create_entry({
            "id": "", "attribute_name": "UOM Conversion",
            "source_uom_code": src_big, "target_uom_code": tgt_big,
            "conversion_factor": 1111111111,
        })
        assert result_big is None or "id" not in result_big, \
            "10-digit integer must be rejected by backend"

    def test_crud_lifecycle(self, api_client):
        """Full lifecycle: create -> get -> list -> update factor -> verify.
        ERP is append-only: one update per record max, no delete API (405)."""
        try:
            src_id, tgt_id, _ = _fetch_unused_pair(api_client)
            ts_factor = (int(datetime.now().strftime("%H%M%S")) % 99999) + 1

            created = api_client.create_entry({
                "id": "", "attribute_name": "UOM Conversion",
                "source_uom_code": src_id, "target_uom_code": tgt_id,
                "conversion_factor": ts_factor,
            })
            assert created is not None and created.get("id"), "Create must return id"
            current_id = created["id"]

            # GET
            detail = api_client.get_entry("UOM Conversion", current_id)
            assert detail is not None, "GET must return the created entry"
            assert detail.get("id") == current_id
            assert detail.get("source_uom_code") == src_id
            assert detail.get("target_uom_code") == tgt_id

            # LIST — entry must appear
            listing = api_client.list_entries("UOM Conversion", page=1, page_size=200)
            assert listing is not None
            items = listing.get("screenmatlistingdata_set", [])
            assert any(item.get("id") == current_id for item in items), \
                "Created entry must appear in list"

            # UPDATE factor in ONE call (ERP allows only one update per record)
            update_payload = dict(detail)
            update_payload["conversion_factor"] = ts_factor + 1
            update_result = api_client.update_entry(current_id, update_payload)
            assert update_result is not None, "Update must succeed"
            current_id = update_result["id"]  # follow the new version id

            updated = api_client.get_entry("UOM Conversion", current_id)
            assert updated is not None
            assert updated.get("conversion_factor") == ts_factor + 1, \
                f"Factor must be updated. Got: {updated.get('conversion_factor')}"

            # NOTE: ERP append-only — one update max, no delete (405).
            # Lifecycle verified: create -> get -> list -> update -> confirm.

        finally:
            pass  # No cleanup possible — ERP has no delete and no second update
