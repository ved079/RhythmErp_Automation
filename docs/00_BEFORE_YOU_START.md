# Before You Start — Day 1 Survival Guide

> **Read this first.** Before you touch any code, before you run any tests, before you ask anyone for help. This document gets you from zero to running your first test.

---

## What You Need Installed

| Tool | Version | Why |
|------|---------|-----|
| **Python** | 3.12+ | The entire test framework is Python. 3.14.3 is what we develop against, but 3.12+ works. |
| **Google Chrome** | Latest | Selenium drives Chrome. No other browser is tested in CI. |
| **ChromeDriver** | Matching your Chrome version | Selenium needs this. Use `webdriver-manager` (it's in requirements.txt) so you don't manage this manually. |
| **Git** | Any recent version | Repo is on GitHub. |
| **VS Code** (recommended) | Any | With the Python extension. Not required but the whole team uses it. |

### Quick Install Check

```bash
python --version     # Should be 3.12+
google-chrome --version  # Should print a version
git --version        # Should print a version
```

If any of these fail, install them before continuing.

---

## Getting the Code

```bash
git clone https://github.com/ved079/RhythmErp_Automation.git
cd RhythmErp_Automation
```

### Set Up Virtual Environment

**Do not skip this.** The project has specific dependency versions. Installing globally will break things.

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

This installs: Selenium, pytest, openpyxl, pandas, colorama, python-dotenv, requests, and other tools.

If you get errors about `webdriver-manager`, try:
```bash
pip install webdriver-manager --upgrade
```

---

## Environment Configuration

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

### What Goes in `.env`

```ini
# ERP URL and credentials — these are the test environment credentials
RHYTHMERP_BASE_URL=https://rhythmerp.algorhythms.in
RHYTHMERP_EMAIL=user@admin.com
RHYTHMERP_PASSWORD=Tenant@123456789
RHYTHMERP_FACILITY=599

# Browser settings
BROWSER=chrome
HEADLESS=true

# Timeouts (in seconds)
EXPLICIT_WAIT=15
PAGE_LOAD_TIMEOUT=60
IMPLICIT_WAIT=5
```

> **IMPORTANT**: The `.env` file contains credentials. It is listed in `.gitignore` — NEVER commit it.

### If You're Working Off-Office / VPN

The ERP at `https://rhythmerp.algorhythms.in` needs to be reachable from your network. If you can't open it in your browser, you won't be able to run tests. Check with your lead about VPN access.

---

## Running Your First Test

### The Quick Smoke Test

Run a simple module to verify everything works end-to-end:

```bash
# Activate venv first!
pytest pages/common_settings/modules/bank/test/test_bank_validation.py -v --tb=short -k "test_create_bank" --headless
```

**What you should see:**
- Chrome opens (or runs headlessly)
- Navigates to RhythmERP
- Logs in
- Opens the Bank screen
- Creates a test entry
- A green `PASSED` in the terminal

**Common errors on first run:**

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'selenium'` | You forgot to activate venv or install requirements |
| `SessionNotCreatedException` | Chrome version doesn't match ChromeDriver. Run `pip install webdriver-manager --upgrade` |
| `TimeoutException` on login | ERP is down or unreachable. Try opening `https://rhythmerp.algorhythms.in` in your browser |
| `ElementNotInteractableException` | This is normal for some tests — the ERP has slow transitions. Try running without `--headless` to see what's happening |

### Running API Tests (No Browser Needed)

API tests are faster and more reliable. They don't need Chrome at all:

```bash
pytest pages/common_settings/modules/bank/test/api/test_bank_payload.py -v
```

If this passes, your Python environment and ERP connectivity are both working.

---

## Running With and Without Headless

By default, tests run in **headless mode** (no visible browser). This is what CI uses.

To watch the browser (useful for debugging):

```bash
# Remove --headless or set in .env:
HEADLESS=false
```

Or override on the command line:

```bash
pytest pages/common_settings/modules/bank/test/test_bank_validation.py -v --tb=long
```

> **Tip**: When debugging, run without headless and add `--tb=long` for full stack traces. When you're just verifying things work, use headless — it's 2-3x faster.

---

## Project Navigation Cheat Sheet

```
RhythmErp_Automation/
├── common/          → Shared utilities (base page, API client, FK resolver)
├── api/             → Flask API server for the web dashboard
├── web-ui/          → Next.js dashboard (separate app)
├── pages/           → ★ ALL THE ERP MODULES LIVE HERE ★
│   ├── common_settings/    → 10 modules (Bank, UOM, Season, etc.)
│   ├── commodity_settings/ → 9 modules (Item Master, Crop Master, etc.)
│   ├── registration/       → 7 modules (Supplier, Customer, Farmer, etc.)
│   ├── access/             → 3 modules (Entity Group, Role, User)
│   └── company_onboarding/ → 1 module (6-step stepper)
├── config.py        → Reads .env, provides settings
├── conftest.py      → Pytest fixtures (driver, login)
└── pytest.ini       → Pytest configuration
```

---

## What Tests Exist

There are two types of tests:

### 1. UI Validation Tests (`test/test_*_validation.py`)
- Selenium-based, drives a real browser
- Tests field validation, error messages, form behavior
- Slow (30-60 seconds per test) but tests the actual user experience
- Need Chrome + ERP access

### 2. API Tests (`test/api/test_*_payload.py`, `test_*_schema.py`, `test_*_perf.py`)
- HTTP-based, sends JSON directly to the ERP API
- Tests payload structure, response schema, performance
- Fast (0.3 seconds per entry) and reliable
- Only need ERP API access, no browser

---

## Where to Get Help

1. **Read the module-specific KT docs** in `docs/modules/` — each module has a deep dive
2. **Read the Angular Material Survival Guide** in `docs/guides/the_angular_material_survival_guide.md` — this covers 80% of the technical challenges
3. **Check existing code** — when in doubt, look at how Bank or UOM does it. They're the most stable modules
4. **Read the ERP's own behavior** — open the ERP in your browser, try the action manually, observe what happens

---

## Common Pitfalls for New People

| Pitfall | Explanation |
|---------|-------------|
| **"I changed the code but tests still fail"** | Did you forget to activate the venv? Are you running the right test file? |
| **"Tests pass locally but fail in CI"** | Probably a timing issue. CI is slower. Add explicit waits, don't rely on implicit waits. |
| **"Dropdown selection doesn't work"** | The ERP uses Angular Material. Browser-clicking a dropdown option does NOT update Angular's form model. You MUST use the JS value-setter pattern. See the Angular Material Survival Guide. |
| **"I used Keys.ESCAPE and now the form is broken"** | Never use `Keys.ESCAPE` in this project. It closes entire forms instead of just overlays. Use backdrop click + JS overlay removal instead. |
| **"My new test entry already exists"** | The ERP database is shared. If your test creates "Test Bank 123", someone else might have already created it. Always use randomized or timestamped names. |
| **"The ERP is painfully slow"** | Yes. UI tests take 30-60 seconds per action. Use API tests for speed. UI tests are for validation behavior only. |

---

## Your First Week Reading Order

```
Day 1:  THIS DOC → Run your first test → Explore the ERP manually
Day 2:  01_ERP_CRASH_COURSE → Understand what the ERP does
Day 3:  02_HOW_THIS_REPO_WORKS → Understand the code structure
Day 4:  Angular Material Survival Guide → Understand the #1 technical challenge
Day 5:  bank.md + uom.md → Read the two reference modules
Week 2: supplier.md → Read the most complex module, start working
```

**You are not expected to understand everything on Day 1.** The ERP is complex, the codebase is large, and the Angular Material quirks take time to internalize. Start with running tests, then gradually read the module docs as you work on specific modules.
