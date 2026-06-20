"""Tests for api/models.py — Pydantic model validation."""
import pytest
from pydantic import ValidationError
from api.models import StartRunRequest, BatchCreateRequest


class TestStartRunRequest:
    def test_requires_module(self):
        with pytest.raises(ValidationError):
            StartRunRequest()

    def test_module_is_required_field(self):
        r = StartRunRequest(module="common_settings")
        assert r.module == "common_settings"

    def test_sub_module_defaults_to_none(self):
        r = StartRunRequest(module="common_settings")
        assert r.sub_module is None

    def test_all_fields(self):
        r = StartRunRequest(
            module="registration",
            sub_module="supplier",
            tests=["test_create"],
            env_url="https://example.com",
            erp_token="abc123",
            erp_tenant_id="681",
        )
        assert r.module == "registration"
        assert r.sub_module == "supplier"
        assert r.tests == ["test_create"]
        assert r.env_url == "https://example.com"
        assert r.erp_token == "abc123"
        assert r.erp_tenant_id == "681"


class TestBatchCreateRequest:
    def test_requires_module(self):
        with pytest.raises(ValidationError):
            BatchCreateRequest()

    def test_requires_sub_module(self):
        with pytest.raises(ValidationError):
            BatchCreateRequest(module="registration")

    def test_requires_erp_token(self):
        with pytest.raises(ValidationError):
            BatchCreateRequest(module="registration", sub_module="supplier")

    def test_count_defaults_to_10(self):
        r = BatchCreateRequest(module="registration", sub_module="supplier", erp_token="abc")
        assert r.count == 10

    def test_erp_tenant_id_defaults_to_681(self):
        r = BatchCreateRequest(module="registration", sub_module="supplier", erp_token="abc")
        assert r.erp_tenant_id == "681"

    def test_accepts_count_below_1(self):
        r = BatchCreateRequest(module="registration", sub_module="supplier", erp_token="abc", count=0)
        assert r.count == 0

    def test_accepts_count_above_500(self):
        r = BatchCreateRequest(module="registration", sub_module="supplier", erp_token="abc", count=1000)
        assert r.count == 1000
