# API Testing Pattern — The 4-Layer Architecture

> How API tests are structured in this project. Every module with API tests follows this exact pattern.

---

## The 4 Test Layers

| Layer | Test File | What It Tests | Speed |
|-------|-----------|---------------|-------|
| 1. Payload Validation | `test_*_payload.py` | Valid payloads return 200, invalid return correct errors | ~0.3s per test |
| 2. Schema Conformance | `test_*_schema.py` | Response structure matches expected fields and types | ~0.3s per test |
| 3. CRUD Lifecycle | `test_*_live.py` | Create → Read → Update → Delete lifecycle (if applicable) | ~1-2s per test |
| 4. Performance | `test_*_perf.py` | Response times within acceptable limits | ~0.5s per test |

Not all modules have all 4 layers. Most have layers 1-2-4. Only Supplier and Customer have layer 3 (live tests).

---

## The conftest.py Pattern

Every module's `test/api/` directory has a `conftest.py`:

```python
import pytest
from common.erp_api_client import RhythmERPAPIClient

@pytest.fixture(scope="module")
def api_client():
    """Provide an authenticated API client for the test module."""
    client = RhythmERPAPIClient()
    client.prompt_for_token()
    yield client

@pytest.fixture
def build_payload():
    """Provide the payload builder for this module."""
    from bank.data.bank_data import build_bank_api_payload
    return build_bank_api_payload

@pytest.fixture
def cleanup_entries(api_client):
    """Track and clean up entries created during tests."""
    created_ids = []
    yield created_ids
    # Cleanup after test module completes
    for entry_id in created_ids:
        try:
            api_client.delete_entry("Bank", entry_id)
        except:
            pass
```

### Key Fixture Patterns

- **`api_client`** — module-scoped, creates one client shared across all tests
- **`build_payload`** — provides the module's payload builder function
- **`cleanup_entries`** — optional, tracks created IDs for cleanup

---

## Layer 1: Payload Validation

### What to Test

| Test Case | Description |
|-----------|-------------|
| Valid payload | All required fields with correct types → 200 |
| Missing required field | Remove each required field one at a time → 400 |
| Wrong field type | Send string where integer expected → 400 |
| FK validation | Invalid FK ID → 400 |
| Empty details/children | Verify structure requirements |
| Boundary values | Max length strings, minimum/maximum numbers |
| Special characters | SQL injection, XSS, unicode in text fields |

### Template

```python
class TestBankPayload:
    """Layer 1: Payload validation for Bank API."""

    def test_valid_payload_returns_200(self, api_client, build_payload):
        payload = build_payload()
        resp = api_client.create_entry("Bank", payload)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    @pytest.mark.parametrize("missing_field", [
        "bank_name", "ifsc_code", "account_type", "account_ref_id"
    ])
    def test_missing_required_field_returns_400(self, api_client, build_payload, missing_field):
        payload = build_payload()
        del payload[missing_field]
        resp = api_client.create_entry("Bank", payload)
        assert resp.status_code == 400

    def test_invalid_fk_id_returns_400(self, api_client, build_payload):
        payload = build_payload(fk_ids={"account_type": 999999})
        resp = api_client.create_entry("Bank", payload)
        assert resp.status_code == 400

    def test_empty_details_accepted(self, api_client, build_payload):
        payload = build_payload()
        payload["details"] = []
        resp = api_client.create_entry("Bank", payload)
        assert resp.status_code == 200
```

---

## Layer 2: Schema Conformance

### What to Test

| Test Case | Description |
|-----------|-------------|
| Response has ID | Created entry has an `id` field |
| Response has all input fields | All fields sent in payload appear in response |
| Response field types match | Integers are integers, strings are strings |
| Response has timestamps | Created/updated timestamps present |
| Response structure is consistent | Multiple creates return same structure |

### Template

```python
class TestBankSchema:
    """Layer 2: Schema conformance for Bank API."""

    def test_response_has_id(self, api_client, build_payload):
        payload = build_payload()
        resp = api_client.create_entry("Bank", payload)
        data = resp.json()
        assert "id" in data or "data" in data

    def test_response_contains_input_fields(self, api_client, build_payload):
        payload = build_payload()
        resp = api_client.create_entry("Bank", payload)
        data = resp.json()
        # Verify all payload fields appear in response
        for key, value in payload.items():
            if key not in ("attribute_name", "details", "children"):
                assert key in str(data), f"Field '{key}' not in response"
```

---

## Layer 3: CRUD Lifecycle (Live Tests)

Only implemented for Supplier and Customer. These create real entries and verify the full lifecycle.

```python
class TestSupplierLive:
    """Layer 3: Full CRUD lifecycle for Supplier API."""

    def test_create_read_update(self, api_client, build_payload):
        # CREATE
        payload = build_payload()
        create_resp = api_client.create_entry("Supplier", payload)
        assert create_resp.status_code == 200
        entry_id = create_resp.json().get("id")

        # READ
        list_resp = api_client.list_entries("Supplier")
        assert list_resp.status_code == 200

        # UPDATE
        payload["company_name"] = f"Updated {uuid4().hex[:6]}"
        update_resp = api_client.update_entry("Supplier", entry_id, payload)
        assert update_resp.status_code == 200
```

---

## Layer 4: Performance

### What to Test

| Test Case | Threshold |
|-----------|-----------|
| Single create | < 2 seconds |
| Batch create (10 entries) | < 20 seconds total |
| List entries | < 3 seconds |
| Schema discovery | < 5 seconds |

### Template

```python
class TestBankPerformance:
    """Layer 4: Performance benchmarks for Bank API."""

    def test_single_create_under_2_seconds(self, api_client, build_payload):
        import time
        payload = build_payload()
        start = time.time()
        api_client.create_entry("Bank", payload)
        elapsed = time.time() - start
        assert elapsed < 2.0, f"Create took {elapsed:.2f}s (threshold: 2.0s)"

    def test_batch_create_10_entries(self, api_client, build_payload):
        import time
        start = time.time()
        for _ in range(10):
            payload = build_payload()
            api_client.create_entry("Bank", payload)
        elapsed = time.time() - start
        assert elapsed < 20.0, f"10 creates took {elapsed:.2f}s (threshold: 20.0s)"
```

---

## Running API Tests

```bash
# Run all API tests for a module
pytest pages/common_settings/modules/bank/test/api/ -v

# Run only payload tests
pytest pages/common_settings/modules/bank/test/api/test_bank_payload.py -v

# Run with specific markers
pytest pages/common_settings/modules/bank/test/api/ -v -k "payload or schema"
```

---

## API Test vs UI Test: When to Use Which

| Scenario | Use API Test | Use UI Test |
|----------|:---:|:---:|
| Verify payload structure | ✅ | |
| Verify response schema | ✅ | |
| Verify performance | ✅ | |
| Verify form validation messages | | ✅ |
| Verify SweetAlert behavior | | ✅ |
| Verify field-level error display | | ✅ |
| Bulk data creation | ✅ | |
| Regression testing | ✅ | ✅ (limited) |
| Smoke testing | ✅ | ✅ |

**Rule of thumb**: API tests for data correctness and performance. UI tests for user experience and validation behavior. Never use UI tests for bulk data creation.
