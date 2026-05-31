# PACS Automation

Automated testing suite for the **PACS Application** using Selenium, pytest, and Python. Covers Login, Forgot Password, and Access Module screens with Excel reports and failure screenshots.

---

## 📋 Table of Contents

- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Step 1 — Install Python](#-step-1--install-python)
- [Step 2 — Install Git](#-step-2--install-git)
- [Step 3 — Install VS Code](#-step-3--install-vs-code)
- [Step 4 — Clone the Repository](#-step-4--clone-the-repository)
- [Step 5 — Setup Virtual Environment](#-step-5--setup-virtual-environment)
- [Step 6 — Install Dependencies](#-step-6--install-dependencies)
- [Step 7 — Configure Environment Variables](#-step-7--configure-environment-variables)
- [Project Structure](#-project-structure)
- [Running Tests](#-running-tests)
- [Understanding Reports](#-understanding-reports)
- [Troubleshooting](#-troubleshooting)
- [Git Workflow](#-git-workflow)

---

## 🛠 Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.14.3 | Programming language |
| Selenium | 4.41.0 | Browser automation |
| pytest | 9.0.2 | Test framework & runner |
| webdriver-manager | 4.0.2 | Auto ChromeDriver management |
| openpyxl | 3.1.5 | Excel report generation |
| pandas | 3.0.2 | Data handling for reports |
| python-dotenv | 1.2.2 | Load environment variables from `.env` |

---

## 📦 Prerequisites

Before you begin, make sure you have:

- **Windows 10 or 11** (this guide is for Windows)
- **Google Chrome** browser installed ([Download](https://www.google.com/chrome/))
- **Internet access** to the GitLab server (`172.16.16.147`)
- **VS Code** as your code editor ([Download](https://code.visualstudio.com/))

---

## 📥 Step 1 — Install Python

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download **Python 3.14.3** (or latest 3.10+)
3. Run the installer
4. **⚠️ IMPORTANT: Check the box "Add Python to PATH"** at the bottom of the installer

   <!-- Add screenshot: Python installer with "Add to PATH" checkbox checked -->

5. Click "Install Now"
6. Verify the installation — open PowerShell and type:
   ```powershell
   python --version
   ```
   You should see: `Python 3.14.3`

> **If you see "python is not recognized"** — Python was not added to PATH. Re-run the installer, click "Modify", and check the "Add to PATH" option.

---

## 📥 Step 2 — Install Git

1. Go to [git-scm.com/download/win](https://git-scm.com/download/win)
2. Download and run the installer
3. Keep all default options — click "Next" through the setup
4. Verify the installation:
   ```powershell
   git --version
   ```
   You should see: `git version 2.x.x`

---

## 📥 Step 3 — Install VS Code

1. Go to [code.visualstudio.com](https://code.visualstudio.com/)
2. Download and install VS Code
3. Open VS Code → click **Extensions** (square icon on left sidebar, or press `Ctrl+Shift+X`)
4. Install these extensions:
   - **Python** (by Microsoft) — provides syntax highlighting, IntelliSense, debugging
   - **GitLens** (by GitKraken) — shows git history, blame info (optional but helpful)

   <!-- Add screenshot: VS Code Extensions panel showing Python extension -->

---

## 📥 Step 4 — Clone the Repository

1. Open **PowerShell** (press `Windows Key`, type `PowerShell`, press Enter)
2. Navigate to your Desktop:
   ```powershell
   cd Desktop
   ```
3. Clone the project:
   ```powershell
   git clone http://172.16.16.147/mayank49/automation-selenium-python.git -b common_flow_from_pacs_for_erp
   ```
4. Open the project in VS Code:
   ```powershell
   cd automation-selenium-python
   code .
   ```
   > The `code .` command opens the current folder in VS Code

5. When VS Code opens, if it prompts **"Select Python Interpreter"** — click the bottom-right status bar where it says Python, then select the Python 3.14 interpreter from the dropdown.

   <!-- Add screenshot: VS Code bottom bar showing Python interpreter selection -->

---

## 📥 Step 5 — Setup Virtual Environment

A virtual environment keeps your project's dependencies separate from other Python projects on your PC.

1. Open the **terminal inside VS Code** (press `` Ctrl+` `` or go to Terminal → New Terminal)
2. Create a virtual environment:
   ```powershell
   python -m venv venv
   ```
3. Activate it:
   ```powershell
   .\venv\Scripts\Activate
   ```
4. You should see `(venv)` appear at the start of your terminal prompt:
   ```
   (venv) PS C:\Users\YourName\Desktop\automation-selenium-python>
   ```

> **You must activate the venv every time you open a new terminal!** If you forget, commands like `pytest` won't work. Just run the activation command above.

---

## 📥 Step 6 — Install Dependencies

With the virtual environment activated, install all required packages:

```powershell
pip install -r requirements.txt
```

Wait for it to finish (may take 1-2 minutes). You should see "Successfully installed..." at the end.

To verify everything is installed:
```powershell
pip list
```

> **Common issue**: If you get "pip is not recognized", make sure the virtual environment is activated (you should see `(venv)` in the prompt).

---

## 📥 Step 7 — Configure Environment Variables

The project needs credentials and URLs to run. These are stored in a `.env` file.

1. In VS Code, look at the project root — you should see a file called `.env`
2. If `.env` does NOT exist, create one:
   - Right-click in the file explorer panel → **New File**
   - Name it exactly `.env` (the dot at the beginning is important)
3. Open `.env` and fill in the values:

```env
# ============================================
# PACS Automation - Environment Configuration
# ============================================

# --- Application URL ---
PACS_BASE_URL=https://pacstest.algorhythms.in

# --- Login Credentials (for Access Module tests) ---
PACS_EMAIL=<your_email@example.com>
PACS_PASSWORD=<your_password>
PACS_FACILITY=<your_facility>

# --- Forgot Password Credentials (for Forgot Password tests) ---
FP_EMAIL=<forgot_password_test_email>
FP_CURRENT_PASSWORD=<current_password>
FP_NEW_PASSWORD=<new_password>
FP_ALT_PASSWORD=<alternate_password>
FP_USERNAME=<username>
FP_TENANT=<tenant_name>
FP_OLD_PASSWORD_1=<old_password_1>
FP_OLD_PASSWORD_2=<old_password_2>
FP_OLD_PASSWORD_3=<old_password_3>

# --- Browser ---
BROWSER=chrome
HEADLESS=false

# --- Timeouts ---
EXPLICIT_WAIT=15
PAGE_LOAD_TIMEOUT=30
```

4. Replace the `<...>` placeholders with actual values. Ask your team lead for the correct credentials.

> **⚠️ NEVER commit your `.env` file to Git!** It is already listed in `.gitignore` so it won't be uploaded. The `.env.example` file (template with dummy values) is safe to share.

---

## 📁 Project Structure

```
automation-selenium-python/
│
├── config.py                          # All URLs, credentials, paths — single source of truth
├── conftest.py                        # pytest fixtures and hooks (runs before/after tests)
├── pytest.ini                         # pytest configuration (custom markers)
├── requirements.txt                   # Python packages to install
├── .env                               # Your credentials (NOT committed to Git)
├── .gitignore                         # Files Git should ignore
│
├── common/                            # Shared utilities used across all modules
│   ├── auth_helper.py                 # Login/logout helper functions
│   ├── base_page.py                   # Base Selenium class (click, type, wait, screenshot)
│   ├── browser_utils.py               # ChromeDriver setup and configuration
│   ├── logger.py                      # Logging utility (logger instead of print)
│   ├── nav_section.py                 # PrimeNG tree navigator (navigate to any screen)
│   ├── report_generator.py            # Excel report generator (4-sheet format)
│   ├── table_helpers.py               # Table search & verify utility
│   └── test_data.py                   # Random test data generators
│
├── data/                              # Test data files
│   └── login_data.py                  # Forgot password test data
│
├── pages/                             # All page objects and runners
│   │
│   ├── login_screens/                 # Login & Forgot Password module
│   │   ├── Login_Screens_/            # Page Object classes
│   │   │   ├── login_page.py          # Login page interactions
│   │   │   └── forgot_password_page.py# Forgot password page interactions
│   │   ├── Test_cases_login/          # Test cases and runner
│   │   │   ├── test_forgot_password.py# 15 pytest test cases
│   │   │   └── runner.py              # Runner with filters (auto/OTP/screen1/etc.)
│   │   ├── reports/                   # Excel reports saved here
│   │   └── screenshots/               # Failure screenshots saved here
│   │
│   └── access_screen/                 # Access Module (Entity, Role, User)
│       ├── Access_screens/            # Screen automation files
│       │   ├── entity_group.py        # Entity Group creation
│       │   ├── role_creation.py       # Role creation
│       │   ├── user_creation.py       # User creation
│       │   └── main_access.py         # Flat linear runner
│       ├── access_screens_test_cases/ # Future pytest tests for access module
│       └── reports/                   # Access module reports
```

---


## ▶️ Running Tests

### Before You Run — Activate Virtual Environment

Every time you open a new terminal, activate the virtual environment first:

1. Open terminal in VS Code (press `` Ctrl+` ``)
2. Run:
   ```powershell
   .\venv\Scripts\Activate
   ```
3. You should see `(venv)` appear at the start of your prompt:
   ```
   (venv) PS C:\Users\YourName\Desktop\automation-selenium-python>
   ```

> **If you don't see `(venv)`**, the activation failed. Check that the `venv` folder exists in your project root. If it doesn't, go back to [Step 5 — Setup Virtual Environment](#-step-5--setup-virtual-environment).

---

### Forgot Password Tests (pytest)

```powershell
# Run ALL 15 tests (auto + OTP)
python pages\login_screens\Test_cases_login\runner.py

# Run only automatic tests (skip tests that need manual OTP input)
python pages\login_screens\Test_cases_login\runner.py --auto-only

# Run only OTP tests (have your email ready)
python pages\login_screens\Test_cases_login\runner.py --otp-only

# Run only Screen 1 tests (Email Entry)
python pages\login_screens\Test_cases_login\runner.py --screen1

# Run only Screen 2 tests (OTP & Password)
python pages\login_screens\Test_cases_login\runner.py --screen2

# Run only Full Flow tests
python pages\login_screens\Test_cases_login\runner.py --full-flow

# Run a single test by name
pytest pages/login_screens/Test_cases_login/test_forgot_password.py -k "test_fp_s1_01" -v
```

### Access Module Tests (module runner)

```powershell
python pages\access_screen\Access_screens\main_access.py
```

> This launches Chrome, logs in, navigates through Access screens (Entity Group, Role Creation, User Creation), creates entries, and verifies them in the table.

### Run with pytest directly (alternative)

```powershell
# All forgot password tests with verbose output
pytest pages/login_screens/Test_cases_login/test_forgot_password.py -v

# Only failed tests from last run (re-run failures)
pytest pages/login_screens/Test_cases_login/test_forgot_password.py --lf

# Generate HTML report alongside Excel
pytest pages/login_screens/Test_cases_login/test_forgot_password.py --html=reports/report.html --self-contained-html
```

---

## 📊 Understanding Reports

### Excel Reports

After running tests, an Excel report is automatically generated with **4 sheets**:

| Sheet | What It Shows |
|---|---|
| **Summary** | Pass/fail counts per category with pass rate percentage |
| **Test Guide** | Plain English explanation of what each test checks — for non-technical readers |
| **Details** | Technical details: test method name, status, error message, duration |
| **Screenshots** | Paths to failure screenshots for failed tests |

Reports are saved to:
- Forgot Password: `pages/login_screens/reports/`
- Access Module: `pages/access_screen/reports/`

### Screenshots

When a test **fails**, a screenshot is automatically captured showing exactly what was on screen at the time of failure. Screenshots are saved to:
- Forgot Password: `pages/login_screens/screenshots/`
- Access Module: `pages/access_screen/screenshots/` (when implemented)

### How to Read a Failed Test

1. Open the Excel report → go to **Test Guide** sheet
2. Find the row with **FAIL** in red
3. Read the **"Why?"** column for a plain English explanation
4. Go to **Screenshots** sheet → find the matching test → open the screenshot image
5. For technical details, check the **Details** sheet

---

## 🔧 Troubleshooting

### "python is not recognized"
- Python was not added to PATH. Reinstall Python and check **"Add to PATH"** during installation.

### "pytest is not recognized"
- You forgot to activate the virtual environment. Run:
  ```powershell
  .\venv\Scripts\Activate
  ```

### "ModuleNotFoundError: No module named 'selenium'"
- Dependencies not installed. Run:
  ```powershell
  pip install -r requirements.txt
  ```

### "ModuleNotFoundError: No module named 'pages'"
- You're running a test file with `python` instead of `pytest`. Always use:
  ```powershell
  pytest pages/login_screens/Test_cases_login/test_forgot_password.py -v
  ```

### Chrome browser doesn't open
- Make sure Google Chrome is installed and updated to the latest version.
- `webdriver-manager` auto-downloads the correct ChromeDriver, so no manual setup needed.

### "User cancelled dialog" when doing git push
- Windows Credential Manager is asking for GitLab credentials. Enter your username and password when the popup appears. Check **"Remember my credentials"** to avoid this in the future.
- If the popup doesn't appear, open Windows Start → search **Credential Manager** → Windows Credentials → remove any `git:http://172.16.16.147` entries, then try again.

### "collected 0 items" — no tests found
- Check that the test path is correct. Run:
  ```powershell
  python pages\login_screens\Test_cases_login\runner.py
  ```
- This uses the runner which has the correct test path configured.

### Old test results in `reports/` or `screenshots/` at root
- These are from before the restructure. You can safely delete them:
  ```powershell
  Remove-Item reports\*.xlsx
  Remove-Item screenshots\*.png
  ```
- New reports go to `pages/login_screens/reports/` and `pages/login_screens/screenshots/`.

### Virtual environment issues
- Delete and recreate:
  ```powershell
  Remove-Item -Recurse -Force venv
  python -m venv venv
  .\venv\Scripts\Activate
  pip install -r requirements.txt
  ```

---

## 🔄 Git Workflow

### Daily Workflow

```powershell
# Always pull before starting work
git pull

# Check what you changed
git status

# Stage your changes
git add -A

# Commit with a message
git commit -m "describe what you did"

# Push to remote
git push
```

### Branch Info

| Branch | Purpose |
|---|---|
| `common_flow_from_pacs_for_erp` | Active development branch — all work happens here |

### Commit Message Conventions

- Use **lowercase** messages
- Describe **what** you changed, not **why**
- Examples:
  ```
  add entity group creation and verification
  fix dropdown click for role creation
  restructure login screens into module folder
  update config paths for screenshots and reports
  ```

### Common Git Commands

```powershell
# See current branch
git branch

# See what changed
git status

# See diff (line-by-line changes)
git diff

# Undo unstaged changes (BE CAREFUL)
git restore .

# See commit history
git log --oneline -10

# Stash changes temporarily
git stash
git stash pop
```

---

## 🏗 Built With

- [Python](https://www.python.org/) — Programming language
- [Selenium](https://www.selenium.dev/) — Browser automation framework
- [pytest](https://docs.pytest.org/) — Test framework
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel file handling
- [PrimeNG](https://primeng.org/) — UI framework (the app being tested)
