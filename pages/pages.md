# PAGES Package – Complete Documentation

This document covers the **`pages`** package of the PACS Automation framework. The package contains all Page Object Modules and test suites for the application’s screens, organised into two main submodules:

- **`access_screen`** – Entity Group, Role, and User Creation screens.
- **`login_screens`** – Login and Forgot Password flows.

Each submodule is self‑contained with its own page objects, test data, pytest test cases, and reporting.

---

## 1. Package Overview

The `pages` directory is structured as follows:

```
pages/
├── __init__.py                      (empty package marker)
├── pages.md                         (this documentation file)
├── access_screen/                   → Access module (Entity Group, Role, User)
│   ├── Access_screens/              → Page objects (entity_group, role_creation, user_creation)
│   ├── access_screens_test_cases/   → pytest suite & runner
│   ├── data/                        → Test data generators
│   ├── reports/                     → Excel test reports
│   ├── screenshots/                 → Failure screenshots
│   └── report_config.py             → Report title & descriptions
└── login_screens/                   → Login module
    ├── Login_Screens_/              → Page objects (login_page, forgot_password_page)
    ├── Test_cases_login/            → pytest suite & runner
    ├── data/                        → Login test data
    ├── reports/                     → Excel test reports
    └── screenshots/                 → Failure screenshots
```

All page objects inherit from `common.base_page.BasePage`, and tests use common helpers from `common/` (logger, table_helpers, auth_helper, nav_section, report_generator, browser_utils).

---

## 2. Access Screen Module

Full documentation is available in [`access_screen/access_screen.md`](access_screen/access_screen.md).  
**Key capabilities:**

- **Entity Group Definition** – `create_entity_group()`
- **Role Creation** – `create_role()`
- **User Creation** – `create_user()` (text inputs, multi‑select, searchable dropdown)
- **Random test data** – `access_data.py` and `access_test_data.py`
- **Pytest test suite** – `user_creation_test.py` (8 tests: positive, validation, dropdown)
- **Test runner** – `access_screen_test_runner.py` with filters (`--positive`, `--validation`, etc.)
- **Excel reports** – saved in `reports/UserCreation_*.xlsx`

### Quick run

```bash
cd pages/access_screen/access_screens_test_cases
python access_screen_test_runner.py --positive
```

---

## 3. Login Screens Module

Full documentation is available in [`login_screens/login_screen.md`](login_screens/login_screen.md).  
**Key capabilities:**

- **LoginPage** – complete login flow (email, password, facility dropdown)
- **ForgotPasswordPage** – 3‑screen flow (email → OTP+password → success)
- **Test data** – `login_data.py` (invalid emails, weak passwords, edge cases)
- **Pytest test suite** – `test_forgot_password.py` (15 tests: Screen 1, Screen 2, Full Flow)
- **Manual OTP tests** – marked with `@pytest.mark.manual_otp`, includes retry logic (3 attempts)
- **Test runner** – `runner.py` with filters (`--auto-only`, `--otp-only`, `--screen1`, `--full-flow`, etc.)
- **Excel reports** – saved in `reports/ForgotPassword_*.xlsx`

### Quick run

```bash
cd pages/login_screens/Test_cases_login
python runner.py --auto-only          # skip manual OTP
python runner.py --full-flow          # run full flow (requires OTP entry)
```

---

## 4. Common Dependencies (outside `pages`)

The `pages` package relies on the following modules from the project root (`common/` and `config.py`):

| Module / File               | Purpose                                                                 |
|-----------------------------|-------------------------------------------------------------------------|
| `common.base_page.BasePage` | Base class with reusable WebDriver actions (click, type, wait, etc.).   |
| `common.logger.log`         | Structured logging with step numbers and separators.                    |
| `common.table_helpers`      | Table search and verification (used by `user_creation.py`).             |
| `common.nav_section`        | Navigation between main menu and sub‑menu items.                        |
| `common.auth_helper`        | Session login (used by `conftest.py` fixtures).                         |
| `common.report_generator`   | Generates Excel reports from test results.                              |
| `common.browser_utils`      | Driver setup and options.                                               |
| `config.py`                 | Central configuration (URLs, credentials, timeouts, etc.).              |

These are documented separately in the `common/` directory.

---

## 5. Configuration (`config.py`)

Both submodules require the following variables in `config.py`:

```python
# General
LOGIN_URL = "https://.../signin"
FORGOT_PASSWORD_URL = "https://.../forgot-password"
EXPLICIT_WAIT = 30

# Login
PACS_EMAIL = "user@example.com"
PACS_PASSWORD = "password"
PACS_FACILITY = "facility_name"

# Forgot Password
FP_EMAIL = "valid_user@example.com"
FP_NEW_PASSWORD = "NewPass@123"
FP_CURRENT_PASSWORD = "OldPass@123"
FP_OLD_PASSWORDS = ["pass1", "pass2"]
FP_USERNAME = "valid_user@example.com"
FP_TENANT = "tenant_name"

# Access Screen (optional – used by main_access.py)
MODULE_LOGIN_URL = LOGIN_URL   # or specific URL
```

All other test‑specific data is defined inside the `data/` folders of each submodule.

---

## 6. Running All Tests Together

You can run the entire `pages` test suite by calling the runners from a root script, for example:

```python
# run_all_pages_tests.py
import subprocess

subprocess.run(["python", "pages/access_screen/access_screens_test_cases/access_screen_test_runner.py"])
subprocess.run(["python", "pages/login_screens/Test_cases_login/runner.py", "--auto-only"])
```

Or use `pytest` directly on the whole `pages` folder (requires a root `conftest.py` that knows how to handle both submodules):

```bash
pytest pages/ -v --tb=short
```

However, note that the two submodules have different fixtures and may conflict. The recommended approach is to run them separately using their dedicated runners.

---

## 7. Reporting and Screenshots

Both submodules produce:

- **Excel reports** inside their respective `reports/` folders.
- **Screenshots** on test failure inside their `screenshots/` folders.

The report generation is handled by the root `conftest.py` (or the one inside each test folder). The `report_config.py` in `access_screen` customises the report title and test descriptions.

---

## 8. Extending the Package

To add a new screen module (e.g., `dashboard_screen/`):

1. Create a subdirectory under `pages/` with the same structure:
   - `page_objects/` – one or more page classes.
   - `tests/` – pytest test files and a runner.
   - `data/` – test data generators.
   - `reports/` and `screenshots/` folders.
2. Follow the patterns established in `access_screen` and `login_screens`:
   - Page objects inherit from `BasePage`.
   - Use `common.table_helpers` for table verification.
   - Use `common.nav_section` for navigation.
   - Include a `report_config.py` if you need custom report titles.
   - Provide a runner script that filters by markers or keywords.
3. Update this `pages.md` to include the new module.

---

## 9. Troubleshooting Common Issues

| Issue                                          | Likely solution                                                          |
|------------------------------------------------|--------------------------------------------------------------------------|
| `ModuleNotFoundError: No module named 'common'`| Ensure the project root is in `sys.path` (the runners already do this). |
| Dropdown not opening in Angular Material       | Use native `click()` on the trigger, not JavaScript.                    |
| OTP test hangs                                 | Run with `-s` flag (included in runners). Make sure `input()` is used.   |
| Excel report not generated                     | Check that `conftest.py` with `pytest_sessionfinish` is present.         |
| Conflicting fixtures between submodules        | Do not run both test suites in the same pytest session. Use separate runners. |

---

## 10. Final Notes

- The `pages` package is designed to be **modular** – each screen module can be copied, adapted, and run independently.
- All sensitive credentials are stored in `config.py` (which should be excluded from version control).
- The `common/` directory provides reusable plumbing; changes there affect all modules.
- For detailed information about a specific submodule, refer to its own `README.md` or the markdown files inside its `docs/` folder.

---

*This documentation covers the entire `pages` package as of April 2026. For the latest version, check the source files and the individual submodule docs.*
```