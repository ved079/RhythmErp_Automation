"""test_tax_rate_perf.py — Performance benchmarks for Tax Rate."""
import time, pytest, sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
from pages.common_settings.modules.tax_rate.data.tax_rate_data import (
    generate_tax_rate_api_payloads, generate_batch_payloads,
)

@pytest.mark.performance
class TestTaxRatePerformance:
    def test_payload_speed(self):
        start = time.perf_counter()
        for _ in range(100): generate_tax_rate_api_payloads(count=1)
        assert ((time.perf_counter() - start) / 100) * 1000 < 10

    def test_batch_speed(self):
        start = time.perf_counter()
        generate_batch_payloads(count=100)
        assert time.perf_counter() - start < 0.5

    @pytest.mark.skip(reason="Live API CRUD tests blocked by workflow issue")
    def test_batch_create_5(self, api_client): pass
