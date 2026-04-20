
# Authentication Module Reference (`auth_section.py`)

This module handles the login process for the FPC ERP system. It navigates to the login page, enters credentials, selects the correct tenant, and confirms successful authentication.

## Function

### `perform_login(driver, wait, config)`

Performs the complete login workflow.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `driver` | `WebDriver` | Selenium WebDriver instance controlling the browser. |
| `wait` | `WebDriverWait` | WebDriverWait instance for handling dynamic elements. |
| `config` | `module` | Configuration module containing `URL`, `USER`, `PASS`, and `TENANT_NAME`. |

**Steps Executed:**

1. Navigates to `config.URL`.
2. Locates the username input (`formcontrolname="username"`), clears it, and enters `config.USER`.
3. Locates the password input (`formcontrolname="password"`), clears it, and enters `config.PASS`.
4. Clicks the first submit button.
5. Waits 2 seconds for the tenant selection dropdown to appear.
6. Clicks the tenant dropdown (`<mat-select>`) using JavaScript.
7. Selects the tenant option whose text contains `config.TENANT_NAME`.
8. Clicks the final submit button to complete login.
9. Logs `✅ Login Successful`.

**Example Usage:**

```python
import config
from common import auth_section

# Inside your test setup
auth_section.perform_login(driver, wait, config)
```

## Logging Output

The function uses the module-level logger configured with timestamps and severity levels.

**Example Console Output:**

```
10:15:32 | INFO     | Step 1: Logging in...
10:15:35 | INFO     | ✅ Login Successful
```

## Element Locators Used

| Element | Locator Type | Locator Value |
|---------|--------------|---------------|
| Username input | XPath | `//input[@formcontrolname='username']` |
| Password input | XPath | `//input[@formcontrolname='password']` |
| First submit button | XPath | `//button[@type='submit']` |
| Tenant dropdown | Tag Name | `mat-select` |
| Tenant option | XPath | `//mat-option//span[contains(text(), '{config.TENANT_NAME}')]` |
| Final submit button | XPath | `//button[@type='submit']` |

## Maintenance Notes

- If the login page fields change (e.g., different `formcontrolname` values), update the corresponding XPath selectors.
- The tenant selection uses `contains(text(), ...)` to allow partial matches. Ensure `config.TENANT_NAME` is unique enough to select the correct tenant.
- JavaScript clicks (`driver.execute_script("arguments[0].click();", element)`) are used for dropdowns and final submit to avoid potential interception by Angular Material overlays.
```