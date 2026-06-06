# How This Repo Works — Code Structure & Conventions

> A map of the codebase. What lives where, what each file type does, and the conventions you need to follow.

---

## The Big Picture

```
RhythmErp_Automation/
│
├── 📂 pages/              → All ERP modules (the core of the project)
├── 📂 common/             → Shared utilities used by all modules
├── 📂 api/                → Flask API server for the web dashboard
├── 📂 web-ui/             → Next.js dashboard (separate app)
├── 📄 config.py           → Reads .env, provides all configuration
├── 📄 conftest.py         → Pytest fixtures (driver, login, etc.)
├── 📄 pytest.ini          → Pytest configuration
├── 📄 requirements.txt    → Python dependencies
└── 📄 .env                → Your local config (NEVER commit this)
```

---

## The `pages/` Directory — Where Everything Lives

Every ERP screen has a module folder following this structure:

```
pages/{section}/modules/{module_name}/
├── __init__.py
├── {module_name}_page.py          # Page Object (Selenium interactions)
├── data/
│   ├── __init__.py
│   └── {module_name}_data.py      # Test data, FK pools, payload builder
├── scripts/
│   └── batch_create.py            # Bulk creation script
└── test/
    ├── __init__.py
    ├── conftest.py                # Module-specific pytest fixtures
    ├── test_{module}_validation.py # UI validation tests (Selenium)
    └── api/
        ├── __init__.py
        ├── conftest.py            # API test fixtures
        ├── test_{module}_payload.py  # Layer 1: Payload validation
        ├── test_{module}_schema.py    # Layer 2: Schema conformance
        └── test_{module}_perf.py      # Layer 3: Performance benchmarks
```

### Sections Map

| `pages/` Folder | ERP Section | # Modules |
|-----------------|-------------|-----------|
| `common_settings/` | Common Settings | 10 |
| `commodity_settings/` | Commodity Settings | 9 |
| `registration/` | Registration | 7 |
| `access/` | Access Control | 3 |
| `company_onboarding/` | Company Onboarding | 1 |

---

## The 4 File Types That Make a Module

### 1. The Data File (`*_data.py`)

**Purpose**: Contains all the data and configuration needed to test this module.

**What's in it**:
```python
# FK ID pools — these are database IDs for dropdown options
BANK_IDS = {"BANK 1": 1005, "Cash": 767, ...}
ACCOUNT_TYPE_IDS = {"Current": 1849, "Saving": 1850}

# Default FK IDs for quick test setup
DEFAULT_BANK_FK_IDS = {
    "account_type": 1849,
    "account_ref_id": 1005,
}

# Field validation rules — documents every field's constraints
FIELD_VALIDATION_RULES = {
    "bank_name": {"type": "text", "required": True, "max_length": 100},
    "ifsc_code": {"type": "text", "required": True, "max_length": 11},
}

# Payload builder — constructs API payloads
def build_bank_api_payload(fk_ids=None):
    fk = {**DEFAULT_BANK_FK_IDS, **(fk_ids or {})}
    return {
        "attribute_name": "Bank",
        "bank_name": f"Test Bank {uuid4().hex[:6]}",
        "ifsc_code": generate_ifsc(),
        "account_type": fk["account_type"],
        ...
    }
```

**Convention**: Always use `DEFAULT_*_FK_IDS` as the base, then override specific IDs via the `fk_ids` parameter. Never hardcode IDs in the payload builder directly.

### 2. The Page Object (`*_page.py`)

**Purpose**: Encapsulates all Selenium interactions with the ERP screen.

**What's in it**:
```python
class BankPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)

    def navigate_to_page(self):
        # Navigate to the Bank screen in the ERP

    def fill_all_fields(self, data):
        # Fill the entire form with the given data

    def submit_form(self):
        # Click Submit/Update

    def verify_entry_exists(self, name):
        # Check if an entry appears in the table
```

**Key patterns**:
- Every page object has `navigate_to_page()`, `fill_all_fields()`, and a submit method
- Page objects use JavaScript for most interactions (not Selenium's native `.click()` or `.send_keys()`) because Angular Material doesn't respond to native events reliably
- Page objects NEVER import from test files. Data flows one way: test → page object

### 3. UI Validation Tests (`test_*_validation.py`)

**Purpose**: Tests that the ERP's form validation behaves correctly.

**What they test**:
- Required field validation (submit with empty fields)
- Character type validation (numbers in name fields, special chars, etc.)
- Max length validation
- Duplicate entry detection
- SweetAlert behavior on success and failure

**What they DON'T test**:
- Business logic correctness
- API response structure
- Performance

### 4. API Tests (`test/api/test_*_payload.py`, `*_schema.py`, `*_perf.py`)

**Purpose**: Tests the ERP's API directly, bypassing the UI.

| Test File | What It Tests |
|-----------|---------------|
| `test_*_payload.py` | Valid payloads return 200, invalid payloads return appropriate errors |
| `test_*_schema.py` | Response structure matches expected schema |
| `test_*_perf.py` | Response times are within acceptable limits |

**Why API tests matter**: They run in 0.3 seconds per entry vs 30-60 seconds for UI tests. They're also more reliable because they don't depend on browser rendering.

---

## The `common/` Directory — Shared Infrastructure

| File | What It Does |
|------|-------------|
| `base_page.py` | Base class with `find_element()`, `click()`, `type_text()` (all with JS fallbacks for Angular), screenshot capture, alert handling |
| `erp_api_client.py` | `RhythmERPAPIClient` — authenticates via `/auth/login1/`, then provides `create_entry()`, `list_entries()`, `batch_create()`, `get_screen_schema()`, `discover_structure()` |
| `fk_resolver.py` | `FkResolver` — resolves FK dropdown IDs from live ERP with disk caching. Has hardcoded `KNOWN_IDS` for stable values, falls back to live API |
| `auth_helper.py` | `AuthSection` — wraps login page for reusable authentication in tests |
| `browser_utils.py` | `get_chrome_driver()` / `get_edge_driver()` — browser factories with test profile, no autofill, sandbox settings |
| `nav_section.py` | `navigate_to()` — navigates the PrimeNG tree sidebar by module name and page name |
| `logger.py` | `CustomLogger` — colored console output (cyan info, green pass, red fail, yellow warning) |
| `report_generator.py` | `generate_report()` — creates Excel reports with Summary, Test Guide, Details, and Screenshots tabs |
| `screenshot_broadcast.py` | Background thread capturing screenshots every 2s for the live dashboard |
| `table_helpers.py` | `verify_in_table()` — reusable table search and verification |

---

## The `api/` Directory — Flask Test Server

This is the backend for the Next.js web dashboard. It:

1. **Discovers** test modules by scanning `pages/` directory
2. **Runs** pytest via subprocess and streams results as Server-Sent Events (SSE)
3. **Broadcasts** live screenshots to the dashboard
4. **Persists** run results to SQLite

You don't need to modify this unless you're changing the dashboard. The test runner reads your test file docstrings to display human-readable test names in the UI.

---

## The `web-ui/` Directory — Next.js Dashboard

A full Next.js application with:
- Test runner UI (select module, run tests, see live output)
- Results dashboard with charts and history
- Admin panel for user management
- AI integration for failure analysis

This is a separate app. To run it:
```bash
cd web-ui
npm install
npm run dev
# Open http://localhost:3000
```

---

## Conventions You Must Follow

### Naming

| Convention | Example |
|-----------|---------|
| Module folder name | `bank`, `hsn_sac`, `item_master` (snake_case) |
| Page object class | `BankPage`, `HsnSacPage`, `ItemMasterPage` (PascalCase) |
| Data file | `bank_data.py`, `hsn_sac_data.py` |
| FK pool variables | `BANK_IDS`, `ACCOUNT_TYPE_IDS` (UPPER_SNAKE) |
| Default FK dict | `DEFAULT_BANK_FK_IDS` |
| Test function names | `test_create_bank_with_valid_data` |
| Payload builder | `build_bank_api_payload()` |

### Test Organization

- **UI validation tests** go in `test/test_{module}_validation.py`
- **API tests** go in `test/api/` with 3 separate files
- **No mixing** — UI tests and API tests are separate because they have different fixtures and different speeds

### The FK Pool Pattern

Every data file has FK ID pools that map human-readable names to database IDs:

```python
ACCOUNT_TYPE_IDS = {"Current": 1849, "Saving": 1850}
```

These IDs are tenant-specific and were discovered by hitting the ERP's dropdown API endpoints. If the ERP database is reset, these IDs may change. The `FkResolver` in `common/fk_resolver.py` can re-discover them automatically.

### The JS-First Interaction Pattern

**This is the most important convention in the entire project.**

Angular Material components do NOT respond to Selenium's native `.click()` and `.send_keys()` reliably. Our page objects use JavaScript for everything:

```python
# WRONG — this clicks the dropdown option but Angular doesn't register it
select_element.click()
option.click()

# RIGHT — set the value via JavaScript and dispatch Angular events
driver.execute_script("""
    var setter = Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype, 'value'
    ).set;
    setter.call(input, 'my value');
    input.dispatchEvent(new Event('input', {bubbles: true}));
""")
```

See `docs/guides/the_angular_material_survival_guide.md` for the full deep-dive on this.

### Never Use Keys.ESCAPE

Every page object has a `_force_close_panels()` method that removes CDK overlays via JavaScript DOM removal. Using `Keys.ESCAPE` in this ERP will close the entire form popup, losing all entered data. This is documented in multiple modules as a hard rule.

### The Submission Tracking Pattern

Most page objects maintain a global list for tracking:

```python
SP_SUBMISSIONS = []  # Supplier
CO_SUBMISSIONS = []  # Company Onboarding
```

This is used for reporting — after a batch run, you can see what was created and what failed.

---

## How Tests Are Discovered

The web dashboard discovers tests by:
1. Scanning `pages/{section}/modules/{module}/test/` directories
2. Using Python's AST parser to read test function names and docstrings
3. Mapping folder names to display names via `api/test_discovery.py`'s `DISPLAY_NAMES` dict

If you add a new test function, make sure it has a docstring — that's what shows up in the dashboard.

---

## The `config.py` Pattern

All configuration comes from `.env` via `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()

RHYTHMERP_BASE_URL = os.getenv("RHYTHMERP_BASE_URL", "https://rhythmerp.algorhythms.in")
RHYTHMERP_EMAIL = os.getenv("RHYTHMERP_EMAIL", "user@admin.com")
```

If you need a new config value:
1. Add it to `config.py` with a sensible default
2. Add it to `.env.example`
3. Document it in your module's KT doc

---

## Common File Sizes

| File Type | Typical Size | Largest |
|-----------|-------------|---------|
| Page object | 900-1,500 LOC | Farmer: 4,027 LOC |
| Data file | 250-500 LOC | Supplier: 1,441 LOC |
| UI validation test | 200-500 LOC | User Creation: 1,599 LOC |
| API test file | 100-300 LOC | Supplier payload: ~300 LOC |
| batch_create script | 80-150 LOC | Standard pattern |

If your page object is going over 2,000 LOC, consider whether you're duplicating logic that should be in `common/base_page.py` or in a shared helper.
