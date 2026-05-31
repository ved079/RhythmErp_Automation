# Pytest Runner for Login Screens Tests

This script is a **CLI wrapper** for running the pytest test suite located in `pages/login_screens/Test_cases_login/`. It provides convenient shortcuts for filtering tests (e.g., skipping manual OTP tests, running only Screen 1 tests, etc.) and integrates with the common reporting infrastructure (Excel report, screenshots) via the root `conftest.py` hooks.

---

## File Location

`pages/login_screens/Test_cases_login/runner.py`

---

## Dependencies

- Python 3.7+
- `pytest`
- The test files must be present in `pages/login_screens/Test_cases_login/`
- A root `conftest.py` (or a parent directory’s `conftest.py`) that defines:
  - Excel report generation hooks
  - Screenshot capture on failure
- The file `test_forgot_password.py` containing the actual test cases with markers:
  - `@pytest.mark.manual_otp` – for tests that require manual OTP entry

---

## Purpose

- Provide a **single entry point** to run all or a subset of login/forgot‑password tests.
- Simplify test selection via memorisable CLI flags (`--auto-only`, `--otp-only`, `--screen1`, etc.).
- Automatically add the project root to `sys.path` so that all modules (`common`, `config`, `pages`) can be imported.
- Pass appropriate arguments to `pytest.main()` while keeping verbose output (`-v`), short tracebacks (`--tb=short`), and captured stdout (`-s`).

---

## Usage Examples

Run from **any directory** (the script adjusts the path). Typically:

```bash
cd pages/login_screens/Test_cases_login
python runner.py
```

### Run all tests (including manual OTP)

```bash
python runner.py
```

Tests that require OTP will **pause** and wait for you to type the OTP from your email.

### Run only automated tests (skip OTP)

```bash
python runner.py --auto-only
```
Equivalent to: `pytest -m "not manual_otp"`

### Run only manual OTP tests

```bash
python runner.py --otp-only
```
Equivalent to: `pytest -m "manual_otp"`

### Run only Screen 1 tests (email entry)

```bash
python runner.py --screen1
```
Equivalent to: `pytest -k "Screen1"`

### Run only Screen 2 tests (OTP + password)

```bash
python runner.py --screen2
```
Equivalent to: `pytest -k "Screen2"`

### Run only full flow tests (grand finale)

```bash
python runner.py --full-flow
```
Equivalent to: `pytest -k "FullFlow"`

### Run only edge case tests (placeholder)

```bash
python runner.py --edge
```
Currently no tests are marked with `EdgeCase` – this is a placeholder for future extensions.

### Pass custom pytest arguments

Any argument not recognised by the runner is forwarded directly to `pytest`.

```bash
python runner.py -k "test_fp_s1_03" -v --html=report.html
```

---

## How It Works

1. **Path setup** – adds the project root (two levels up from the runner’s location) to `sys.path`, ensuring imports like `common`, `config`, `pages` work.
2. **Argument parsing** – checks `sys.argv[1:]` for known flags:
   - `--auto-only` → adds `-m "not manual_otp"`
   - `--otp-only` → adds `-m "manual_otp"`
   - `--screen1` → adds `-k "Screen1"`
   - `--screen2` → adds `-k "Screen2"`
   - `--full-flow` → adds `-k "FullFlow"`
   - `--edge` → adds `-k "EdgeCase"`
   - Anything else → passed through to `pytest` unchanged.
3. **Builds the base arguments**:
   - `"pages/login_screens/Test_cases_login/"` – the test folder
   - `"-v"` – verbose output
   - `"--tb=short"` – short traceback format
   - `"-s"` – allow `print()` and input prompts
4. **Calls `pytest.main(args)`** – executes the tests.
5. **Exits with the same exit code** as `pytest.main()`.

---

## Marker and Keyword Conventions

The runner assumes the following naming/marking patterns in the test file (`test_forgot_password.py`):

| Runner flag     | Pytest filter                         | Test class / method pattern                |
|----------------|---------------------------------------|---------------------------------------------|
| `--auto-only`  | `-m "not manual_otp"`                 | Tests **without** `@pytest.mark.manual_otp`|
| `--otp-only`   | `-m "manual_otp"`                     | Tests **with** `@pytest.mark.manual_otp`    |
| `--screen1`    | `-k "Screen1"`                        | `TestForgotPasswordScreen1` class           |
| `--screen2`    | `-k "Screen2"`                        | `TestForgotPasswordScreen2` class           |
| `--full-flow`  | `-k "FullFlow"`                       | `TestForgotPasswordFullFlow` class          |
| `--edge`       | `-k "EdgeCase"`                       | Future `TestForgotPasswordEdgeCase` class   |

> **Note:** The `-k` option matches **any part** of the test name or class name. Thus `-k "Screen1"` will run all methods inside `TestForgotPasswordScreen1`.

---

## Integration with Reporting

- The root `conftest.py` (if present) will automatically generate an **Excel report** after the test session finishes.
- On failure, a screenshot is captured and saved in `pages/login_screens/screenshots/`.
- The runner does **not** need to specify report paths; this is handled by the global hooks.

---

## Customising the Runner

You can easily extend the runner by adding new flags in the `if/elif` block. For example:

```python
elif "--smoke" in cli_args:
    print("\n  Running smoke tests...\n")
    exit_code = run_tests(["-m", "smoke"])
```

Then mark your smoke tests with `@pytest.mark.smoke`.

---

## Troubleshooting

| Issue                                      | Likely solution                                                      |
|--------------------------------------------|----------------------------------------------------------------------|
| `ModuleNotFoundError: No module named 'common'` | The project root was not added correctly. Check the `project_root` calculation. |
| Manual OTP tests hang or never prompt      | Ensure `-s` flag is present (it is by default). Also check that `input()` is used inside the test. |
| `--auto-only` still runs OTP tests         | Verify that the OTP tests are decorated with `@pytest.mark.manual_otp` exactly. |
| Excel report not generated                 | Make sure a `conftest.py` with `pytest_sessionfinish` hook exists in the project root or in `pages/login_screens/`. |

---

## Related Files

- `pages/login_screens/Test_cases_login/test_forgot_password.py` – the actual test cases.
- Root `conftest.py` – responsible for Excel report generation and screenshot capture.
- `common/logger.py` – used for logging inside tests (not directly used by runner).
- `config.py` – contains `LOGIN_URL`, `FP_EMAIL`, etc.

---

*Documentation generated for `runner.py` – April 2026.*
```