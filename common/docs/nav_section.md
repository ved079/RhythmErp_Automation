
# 🗺️ FPC Automation Framework: Core Navigation & Helpers

Welcome to the central documentation for the FPC Selenium Automation Framework. This guide covers the **Navigation Module**, **Helpers**, and **Authentication**. 

Because this framework interacts with a complex Angular Material application, it relies on highly specific design patterns to guarantee stability. **Please read the "Survival Guide" before contributing.**

---

## 🛑 1. The Angular Survival Guide (Mandatory Reading)

Angular Material relies heavily on dynamic DOM manipulation, animations, and invisible overlays. Standard Selenium commands (like `.click()`) will frequently fail. To keep the suite green, you **must** adhere to these three core rules:

> **⚠️ Rule 1: The JavaScript Click is King**
> Never use standard Selenium `.click()` for sidebar menus or heavily styled Angular components. Invisible overlays will intercept it and throw an `ElementClickInterceptedException`.
> * **Do:** `driver.execute_script("arguments[0].click();", element)`
> * **Don't:** `element.click()`

> **👻 Rule 2: Overlay Assassination**
> Success toasts (`.swal2-container`) and background backdrops (`.cdk-overlay-backdrop`) from previous tests linger and block the UI. 
> * **Rule:** Always clear the screen before navigating using implicit waits for invisibility, or by triggering the `ESCAPE` key.

> **⏱️ Rule 3: Respect Animation Delays**
> Angular dropdowns (`.cdk-overlay-pane`) fade out slowly. If you click a new dropdown before the old one finishes fading, Selenium grabs the dying element and throws a `StaleElementReferenceException`.
> * **Rule:** Always use a hard `time.sleep(1)` between sequential dropdown interactions to allow the DOM to stabilize.

---

## 🧭 2. Navigation Module (`nav_section.py`)

This module transitions the application from *any* current state to a target page. 

**Smart Menu Logic:** Navigation functions automatically check if a parent menu (e.g., "Sales") is already open before clicking it, preventing accidental menu collapses.

### 🌱 Master Data Management
| Target Page | Function Name | Form Ready Indicator (Waits for...) |
| :--- | :--- | :--- |
| **Farmer** | `go_to_farmer_page()` | *(Implicit UI load)* |
| **Supplier** | `go_to_supplier_page()` | *(Implicit UI load)* |
| **Agent** | `go_to_agent_page()` | *(Implicit UI load)* |
| **Customer** | `go_to_customer_page()` | `input#company_name` |
| **Employee** | `go_to_employee_page()` | `input[@formcontrolname='emp_name']` |

### 🛒 Purchase Workflow (B2B)
| Target Page | Function Name | Form Ready Indicator (Waits for...) |
| :--- | :--- | :--- |
| **Gate Pass** | `go_to_gatepass_page()` | `[formcontrolname='supplier_ref_id']` |
| **GRN** | `go_to_grn_page()` | `[formcontrolname='supplier_ref_id']` |
| **QC** | `go_to_qc_page()` | `[formcontrolname='supplier_ref_id']` |
| **Purchase Booking** | `go_to_purchase_booking_page()` | `input.search-field` |

### 📦 Sales Workflow (B2B)
| Target Page | Function Name | Form Ready Indicator (Waits for...) |
| :--- | :--- | :--- |
| **Sales Order** | `go_to_sales_order_page()` | `[formcontrolname='customer_ref_id']` |
| **Lot Creation** | `go_to_lot_creation_page()` | `table tbody tr` |
| **Dispatch Note**| `go_to_dispatch_note_page()` | `[formcontrolname='customer_ref_id']` |
| **Invoice** | `go_to_invoice_page()` | `[formcontrolname='customer_ref_id']` |
| **Receipt** | `go_to_receipt_page()` | `[formcontrolname='customer_ref_id']` |

### 📊 Reports & Lists
| Target Page | Function Name | Form Ready Indicator (Waits for...) |
| :--- | :--- | :--- |
| **Inventory Summary**| `go_to_inventory_summary()`| `button.apply` |
| **Trial Balance** | `go_to_trial_balance()` | `button.apply` |
| **List Pages** | `go_to_<module>_list()` | `table` |

#### 📝 Usage Example:
```python
from common import nav_section

def test_sales_flow(driver, wait):
    nav_section.go_to_sales_order_page(driver, wait)
    # Start filling the form...
```

---

## 🛠️ 3. Helper Functions (`helper.py`)

These utilities handle the complex logic of interacting with Angular inputs.

### `select_dropdown()`
Handles opening a `mat-select`, waiting for the overlay, searching (if applicable), and clicking the correct `mat-option`.

**Parameters:**
* `value`: The text of the option to select.
* `control_name` / `control_id`: The HTML identifier of the dropdown.
* `searchable`: Set to `True` if the dropdown contains a search input box.

```python
# Standard dropdown
select_dropdown(driver, wait, value="B2B", control_name="sale_type", searchable=False)

# Dropdown with a search filter
select_dropdown(driver, wait, value="Vedant Enterprises", control_name="customer", searchable=True)
```

### `fill_input()` & `fill_datepicker()`
Clears existing data and forces Angular to register the new value by simulating a `TAB` keypress. 

```python
# Safe Datepicker Entry
fill_datepicker(driver, wait, "10/04/2026")
```

---

## 🔐 4. Authentication (`auth_section.py`)

Handles the initial login and Tenant routing. 

```python
import config
from common import auth_section

# Uses URL, USER, PASS, and TENANT_NAME from config.py
auth_section.perform_login(driver, wait, config)
```

---

## 🩺 5. Troubleshooting Common Errors

| Error | Root Cause | How to Fix |
| :--- | :--- | :--- |
| **`ElementClickInterceptedException`** | An overlay popup or loading spinner is blocking the element you are trying to click. | Change `.click()` to `driver.execute_script("arguments[0].click();", element)` |
| **`StaleElementReferenceException`** | You grabbed an Angular dropdown option while the previous dropdown was still animating closed. | Add `time.sleep(1)` before interacting with the next dropdown. |
| **`TimeoutException` at the end of routing** | The page loaded, but your specific locator (e.g., `company_name`) changed in a recent UI update. | Inspect the DOM on the new page and update the `wait.until` locator in `nav_section.py`. |

```