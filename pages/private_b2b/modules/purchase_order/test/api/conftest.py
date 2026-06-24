import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)


def pytest_configure(config):
    config.addinivalue_line("markers", "api: API payload and CRUD tests")
    config.addinivalue_line("markers", "schema: Schema and structure verification")
    config.addinivalue_line("markers", "calculation: Computed field verification")
    config.addinivalue_line("markers", "performance: Speed and benchmark tests")
    config.addinivalue_line("markers", "live: Tests that require a live ERP token (ERP_TOKEN env var)")
    config.addinivalue_line("markers", "integrity: Data consistency and mutation tests")
