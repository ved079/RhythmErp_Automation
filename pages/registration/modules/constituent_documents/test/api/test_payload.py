"""
test_payload.py
---------------
Tests for the Constituent Documents payload builder — no API required.
"""

import pytest
import re
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pages.registration.modules.constituent_documents.data.constituent_documents_data import (
    generate_cin_no,
    generate_date_string,
    generate_valid_data,
    build_api_payload,
    generate_batch_payloads,
)


class TestGenerateCIN:
    def test_format(self):
        cin = generate_cin_no()
        assert re.match(r"^[A-Z][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$", cin), f"CIN {cin} doesn't match pattern"

    def test_unique(self):
        cins = {generate_cin_no() for _ in range(20)}
        assert len(cins) == 20, "Generated duplicate CINs"


class TestGenerateDateString:
    def test_format(self):
        ds = generate_date_string()
        assert re.match(r"^\d{4}-\d{2}-\d{2}T18:30:00Z$", ds), f"Date {ds} doesn't match expected format"


class TestGenerateValidData:
    def test_returns_dict_with_required_keys(self):
        data = generate_valid_data()
        assert "cin_no" in data
        assert "cin_date" in data

    def test_cin_matches_pattern(self):
        data = generate_valid_data()
        assert re.match(r"^[A-Z][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$", data["cin_no"])


class TestBuildAPIPayload:
    def test_returns_dict_with_required_keys(self):
        payload = build_api_payload()
        assert "id" in payload
        assert "attribute_name" in payload
        assert "cin_no" in payload
        assert "cin_date" in payload
        assert "details" in payload

    def test_id_is_empty_string(self):
        payload = build_api_payload()
        assert payload["id"] == ""

    def test_attribute_name(self):
        payload = build_api_payload()
        assert payload["attribute_name"] == "Constituent Documents"

    def test_no_children(self):
        payload = build_api_payload()
        assert "children" not in payload

    def test_custom_data(self):
        data = {
            "cin_no": "L12345AB6789XYZ123456",
            "cin_date": "2025-01-15T18:30:00Z",
        }
        payload = build_api_payload(data=data)
        assert payload["cin_no"] == "L12345AB6789XYZ123456"
        assert payload["cin_date"] == "2025-01-15T18:30:00Z"


class TestGenerateBatchPayloads:
    def test_returns_correct_count(self):
        payloads = generate_batch_payloads(5)
        assert len(payloads) == 5

    def test_all_have_required_keys(self):
        payloads = generate_batch_payloads(3)
        for p in payloads:
            assert "cin_no" in p
            assert "cin_date" in p

    def test_unique_cins(self):
        payloads = generate_batch_payloads(10)
        cins = [p["cin_no"] for p in payloads]
        assert len(cins) == len(set(cins)), "Duplicate CINs in batch"
