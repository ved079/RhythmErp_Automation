"""
test_payload.py
---------------
Tests for the Miscellaneous Documents payload builder â€” no API required.
"""

import pytest
import re
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pages.documents.modules.miscellaneous_documents.data.miscellaneous_documents_data import (
    generate_name,
    generate_document_no,
    generate_date_string,
    generate_expiry_date_string,
    generate_brief_details,
    generate_valid_data,
    build_api_payload,
    generate_batch_payloads,
    DOCUMENT_NAMES,
)


class TestGenerateName:
    def test_format(self):
        name = generate_name()
        assert re.match(r"^[A-Za-z0-9&.,()_\/\- ]+$", name), f"Name {name!r} doesn't match pattern"

    def test_unique(self):
        names = {generate_name() for _ in range(20)}
        assert len(names) == 20, "Generated duplicate names"


class TestGenerateDocumentNo:
    def test_is_integer(self):
        doc_no = generate_document_no()
        assert isinstance(doc_no, int)

    def test_unique(self):
        nos = {generate_document_no() for _ in range(20)}
        assert len(nos) == 20, "Generated duplicate document numbers"


class TestGenerateDateString:
    def test_format(self):
        ds = generate_date_string()
        assert re.match(r"^\d{4}-\d{2}-\d{2}T18:30:00Z$", ds), f"Date {ds} doesn't match expected format"


class TestGenerateExpiryDateString:
    def test_after_registered_date(self):
        reg = "2025-01-15T18:30:00Z"
        exp = generate_expiry_date_string(reg)
        assert exp > reg, f"Expiry {exp} should be after registered {reg}"

    def test_format(self):
        exp = generate_expiry_date_string()
        assert re.match(r"^\d{4}-\d{2}-\d{2}T18:30:00Z$", exp)


class TestGenerateBriefDetails:
    def test_max_length(self):
        details = generate_brief_details()
        assert len(details) <= 255, f"Brief details too long: {len(details)} chars"

    def test_non_empty(self):
        details = generate_brief_details()
        assert len(details) > 0


class TestGenerateValidData:
    def test_returns_dict_with_required_keys(self):
        data = generate_valid_data()
        assert "name" in data
        assert "document_no" in data
        assert "registered_date" in data
        assert "brief_details" in data

    def test_name_matches_pattern(self):
        data = generate_valid_data()
        assert re.match(r"^[A-Za-z0-9&.,()_\/\- ]+$", data["name"])


class TestBuildAPIPayload:
    def test_returns_dict_with_required_keys(self):
        payload = build_api_payload()
        assert "id" in payload
        assert "attribute_name" in payload
        assert "name" in payload
        assert "document_no" in payload
        assert "registered_date" in payload
        assert "brief_details" in payload

    def test_id_is_empty_string(self):
        payload = build_api_payload()
        assert payload["id"] == ""

    def test_attribute_name(self):
        payload = build_api_payload()
        assert payload["attribute_name"] == "Miscellaneous Documents"

    def test_no_children(self):
        payload = build_api_payload()
        assert "children" not in payload

    def test_custom_data(self):
        data = {
            "name": "Test Document - ABCD",
            "document_no": 12345,
            "registered_date": "2025-01-15T18:30:00Z",
            "brief_details": "A test document",
        }
        payload = build_api_payload(data=data)
        assert payload["name"] == "Test Document - ABCD"
        assert payload["document_no"] == 12345


class TestGenerateBatchPayloads:
    def test_returns_correct_count(self):
        payloads = generate_batch_payloads(5)
        assert len(payloads) == 5

    def test_all_have_required_keys(self):
        payloads = generate_batch_payloads(3)
        for p in payloads:
            assert "name" in p
            assert "document_no" in p
            assert "registered_date" in p

    def test_unique_names(self):
        payloads = generate_batch_payloads(10)
        names = [p["name"] for p in payloads]
        assert len(names) == len(set(names)), "Duplicate names in batch"

    def test_unique_document_nos(self):
        payloads = generate_batch_payloads(10)
        nos = [p["document_no"] for p in payloads]
        assert len(nos) == len(set(nos)), "Duplicate document numbers in batch"
