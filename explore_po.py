"""
Selenium script to explore the ERP Purchase Order screen.
Opens Chrome, logs in, navigates to PO page, and inspects all UI elements.
"""
import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

OUTPUT_FILE = r"C:\Users\vedantd\Desktop\Pacs_Automation\po_exploration_results.txt"

def log(msg):
    print(msg)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def wait_and_find(driver, by, value, timeout=15):
    try:
        elem = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
        return elem
    except TimeoutException:
        log(f"  WARNING: Timeout waiting for element: {by}={value}")
        return None

def login(driver):
    log("\n" + "="*70)
    log("STEP 1: NAVIGATING TO LOGIN PAGE")
    log("="*70)
    driver.get("https://rhythmerp.algorhythms.in/#/authentication/signin")
    time.sleep(3)
    log(f"Page title: {driver.title}")
    log(f"Current URL: {driver.current_url}")

    log("\n--- Filling email field ---")
    email_input = wait_and_find(driver, By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[placeholder*='Email'], input[placeholder*='email']")
    if email_input:
        email_input.clear()
        email_input.send_keys("Gautams@gmail.com")
        log("Email entered: Gautams@gmail.com")
    else:
        inputs = driver.find_elements(By.CSS_SELECTOR, "input")
        for inp in inputs:
            at = inp.get_attribute("type") or ""
            ph = inp.get_attribute("placeholder") or ""
            if "email" in at.lower() or "email" in ph.lower():
                inp.clear()
                inp.send_keys("Gautams@gmail.com")
                log("Email entered (via fallback)")
                break

    log("\n--- Filling password field ---")
    password_input = wait_and_find(driver, By.CSS_SELECTOR, "input[type='password'], input[name='password'], input[placeholder*='Password'], input[placeholder*='password']")
    if password_input:
        password_input.clear()
        password_input.send_keys("Test@2526270")
        log("Password entered")
    else:
        inputs = driver.find_elements(By.CSS_SELECTOR, "input")
        for inp in inputs:
            at = inp.get_attribute("type") or ""
            ph = inp.get_attribute("placeholder") or ""
            if "password" in at.lower() or "password" in ph.lower():
                inp.clear()
                inp.send_keys("Test@2526270")
                log("Password entered (via fallback)")
                break

    log("\n--- Dismissing tenant dropdown ---")
    time.sleep(1)
    ActionChains(driver).move_by_offset(10, 10).click().perform()
    time.sleep(0.5)

    log("\n--- Looking for login/submit button ---")
    login_button = None
    for selector in ["button[type='submit']", ".btn-primary", "button.mat-raised-button", "button"]:
        try:
            btns = driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in btns:
                text = btn.text.strip().lower()
                if text in ("sign in", "login", "sign in to continue", "submit", "log in"):
                    login_button = btn
                    log(f"Found login button: '{btn.text.strip()}'")
                    break
            if login_button:
                break
        except:
            pass
    if not login_button:
        try:
            login_button = driver.find_element(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign')]")
            log(f"Login button via XPath: '{login_button.text.strip()}'")
        except:
            pass
    if not login_button:
        try:
            login_button = driver.find_element(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]")
            log(f"Login button via XPath2: '{login_button.text.strip()}'")
        except:
            pass
    if not login_button:
        buttons = driver.find_elements(By.TAG_NAME, "button")
        log(f"All buttons ({len(buttons)}):")
        for i, btn in enumerate(buttons):
            try:
                txt = btn.text.strip()
                html = btn.get_attribute("outerHTML")[:120]
                log(f"  Button {i}: '{txt}' | {html}")
            except:
                pass
        if buttons:
            login_button = buttons[-1]
            log(f"Falling back to last button: '{login_button.text.strip()}'")
    if login_button:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_button)
            time.sleep(0.5)
            login_button.click()
            log("Clicked login button")
        except Exception as e:
            try:
                driver.execute_script("arguments[0].click();", login_button)
                log("Clicked login button via JS")
            except Exception as e2:
                log(f"Could not click login button: {e2}")
    else:
        log("ERROR: Could not find login button")
    time.sleep(5)
    log(f"After login URL: {driver.current_url}")
    return driver

def navigate_to_po(driver):
    log("\n" + "="*70)
    log("STEP 2: NAVIGATING TO PURCHASE ORDER PAGE")
    log("="*70)
    driver.get("https://rhythmerp.algorhythms.in/#/purchase/purchase-order")
    time.sleep(5)
    log(f"PO page URL: {driver.current_url}")
    log(f"PO page title: {driver.title}")
    return driver

def explore_table_columns(driver):
    log("\n" + "="*70)
    log("STEP A: TABLE / LIST VIEW - COLUMNS")
    log("="*70)
    time.sleep(3)
    selectors = [
        "th", "thead th", "thead tr th",
        ".mat-header-cell", "mat-header-cell",
        ".ag-header-cell", ".ag-header-cell-text",
        ".k-header", "th[role='columnheader']",
        "table thead th", "[role='columnheader']",
        ".cdk-header-cell", ".ui-column-title",
        ".dx-header-cell", "p-table thead th",
        ".p-datatable-thead th", "[ref='eText']",
        ".header-cell", "[col-id]", "thead .th-inner",
    ]
    all_found = []
    for sel in selectors:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems and len(elems) > 1:
                log(f"\n{len(elems)} header cells with: {sel}")
                for i, e in enumerate(elems):
                    try:
                        text = e.text.strip()
                        html = e.get_attribute("outerHTML")[:150]
                        if text:
                            log(f"  [{i}] '{text}' | {html}")
                            all_found.append(text)
                    except:
                        pass
        except:
            pass

    log("\n--- Table body content ---")
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr, .mat-row, .ag-row, [role='row']")
        log(f"Found {len(rows)} rows")
        if rows:
            for ri, row in enumerate(rows[:3]):
                cells = row.find_elements(By.CSS_SELECTOR, "td, .mat-cell, .ag-cell, [role='gridcell']")
                cell_texts = [c.text.strip() for c in cells if c.text.strip() and len(c.text.strip()) < 100]
                if cell_texts:
                    log(f"  Row {ri}: {cell_texts}")
    except Exception as ex:
        log(f"  Error reading table body: {ex}")
    if not all_found:
        log("\n--- No headers found, dumping tables ---")
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            log(f"Found {len(tables)} tables")
            for ti, tbl in enumerate(tables):
                log(f"  Table {ti}: id={tbl.get_attribute('id')} class={tbl.get_attribute('class')}")
        except:
            pass
    return all_found
def explore_row_action_menu(driver):
    log("\n" + "="*70)
    log("STEP B: ROW ACTION MENU (three-dot menu)")
    log("="*70)
    time.sleep(2)
    action_selectors = [
        "button[aria-label*='action']", "button[aria-label*='menu']",
        "button[aria-label*='more']", ".mat-mdc-icon-button",
        "button.mat-icon-button", "i.fa-ellipsis-v", "i.fa-ellipsis-h",
        ".action-btn", ".row-action", ".menu-button", "button[mat-icon-button]",
        "[data-action='menu']", "td:last-child button", "td .btn-group button",
    ]
    action_button = None
    for sel in action_selectors:
        try:
            btns = driver.find_elements(By.CSS_SELECTOR, sel)
            if btns:
                log(f"Found {len(btns)} potential action buttons with: {sel}")
                for btn in btns:
                    try:
                        html = btn.get_attribute("outerHTML")[:200]
                        text = btn.text.strip()
                        aria = btn.get_attribute("aria-label") or ""
                        log(f"  Button: text='{text}' aria='{aria}' | {html}")
                        if not action_button:
                            action_button = btn
                    except:
                        pass
        except:
            pass
    if action_button:
        log("\n--- Clicking action button ---")
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", action_button)
            time.sleep(0.5)
            action_button.click()
            log("Clicked action button")
            time.sleep(1)
        except Exception as e:
            log(f"Could not click: {e}")
            try:
                driver.execute_script("arguments[0].click();", action_button)
                log("Clicked via JS")
                time.sleep(1)
            except Exception as e2:
                log(f"JS click failed: {e2}")
    else:
        log("No action button found in standard locations")
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        log(f"\n--- All buttons ({len(all_buttons)}) ---")
        for i, btn in enumerate(all_buttons):
            try:
                text = btn.text.strip()
                aria = btn.get_attribute("aria-label") or ""
                inner = btn.get_attribute("innerHTML")[:100]
                if any(x in (text+aria+inner).lower() for x in ["action", "menu", "more", "ellipsis", "three", "dot", "setting"]):
                    log(f"  Button {i}: '{text}' aria='{aria}' inner={inner}")
            except:
                pass

    log("\n--- Looking for dropdown menu items ---")
    time.sleep(1)
    menu_selectors = [
        ".mat-menu-item", ".mat-mdc-menu-item",
        ".dropdown-menu li", ".dropdown-menu a",
        "[role='menuitem']", ".menu-item",
        "ul.dropdown-menu li", ".cdk-overlay-container .mat-menu-item",
        ".p-menu-item", ".p-menuitem-link", ".k-menu-item",
        ".context-menu-item", ".ag-menu-option",
        "[role='menu'] [role='menuitem']", ".mat-menu-content button",
        ".mdc-list-item",
    ]
    menu_items = []
    for sel in menu_selectors:
        try:
            items = driver.find_elements(By.CSS_SELECTOR, sel)
            if items:
                log(f"\nFound {len(items)} menu items with: {sel}")
                for item in items:
                    try:
                        text = item.text.strip()
                        html = item.get_attribute("outerHTML")[:150]
                        if text:
                            log(f"  Menu option: '{text}' | {html}")
                            menu_items.append(text)
                    except:
                        pass
        except:
            pass
    try:
        log("\n--- Overlay container ---")
        overlay = driver.find_elements(By.CSS_SELECTOR, ".cdk-overlay-pane")
        log(f"Found {len(overlay)} overlay panes")
        for oi, pane in enumerate(overlay):
            try:
                pane_text = pane.text.strip()
                if pane_text:
                    log(f"  Overlay {oi}: '{pane_text}'")
            except:
                pass
    except:
        pass
    try:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
    except:
        pass
    return menu_items
def explore_add_form(driver):
    log("\n" + "="*70)
    log("STEP C: ADD FORM EXPLORATION")
    log("="*70)
    log("\n--- Looking for Add / New button ---")
    add_button = None
    if not add_button:
        try:
            add_button = driver.find_element(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add')]")
            log(f"Add button via XPath: '{add_button.text.strip()}'")
        except:
            pass
    if not add_button:
        try:
            add_button = driver.find_element(By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add') and (self::a or self::button)]")
            log(f"Add via XPath2: '{add_button.text.strip()}'")
        except:
            pass
    if not add_button:
        all_btns = driver.find_elements(By.TAG_NAME, "button")
        log(f"\n--- All buttons ({len(all_btns)}) ---")
        for i, btn in enumerate(all_btns):
            try:
                text = btn.text.strip()
                html = btn.get_attribute("outerHTML")[:150]
                log(f"  Button {i}: '{text}' | {html}")
            except:
                pass
        for btn in all_btns:
            txt = btn.text.strip().lower()
            if txt in ("add", "new", "create", "+", "+ add", "+ new", "add new", "create new"):
                add_button = btn
                log(f"Selected Add: '{btn.text.strip()}'")
                break
    if add_button:
        log("\n--- Clicking Add ---")
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_button)
            time.sleep(0.5)
            add_button.click()
            log("Clicked Add")
            time.sleep(3)
        except Exception as e:
            try:
                driver.execute_script("arguments[0].click();", add_button)
                log("Clicked Add via JS")
                time.sleep(3)
            except Exception as e2:
                log(f"Could not click Add: {e2}")
    else:
        log("ERROR: Could not find Add button")
        return False

    log("\n--- Exploring form fields ---")
    form_fields = []
    field_selectors = [
        "input", "select", "textarea", "mat-select", "mat-option",
        ".mat-form-field", ".form-group", ".form-control", "label",
        ".field-label", ".label", "mat-label", "[formcontrolname]",
        "[formControlName]", ".p-field", ".field", "p-dropdown",
        "p-inputnumber", "p-calendar", "p-autocomplete", "p-multiselect",
        "p-checkbox", "p-radioButton",
    ]
    for sel in field_selectors:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                for e in elems:
                    try:
                        tag = e.tag_name
                        text = e.text.strip()
                        ph = e.get_attribute("placeholder") or ""
                        aria_label = e.get_attribute("aria-label") or ""
                        name = e.get_attribute("name") or ""
                        fcn = e.get_attribute("formcontrolname") or e.get_attribute("formControlName") or ""
                        cls = e.get_attribute("class") or ""
                        info = f"tag={tag} text='{text[:50]}' placeholder='{ph}' aria-label='{aria_label}' name='{name}' formControlName='{fcn}' class='{cls[:60]}'"
                        if text or ph or aria_label or fcn:
                            if info not in form_fields:
                                form_fields.append(info)
                                log(f"  Field: {info}")
                    except:
                        pass
        except:
            pass

    log("\n--- Form labels ---")
    try:
        labels = driver.find_elements(By.TAG_NAME, "label")
        log(f"Found {len(labels)} labels")
        for i, lbl in enumerate(labels):
            try:
                text = lbl.text.strip()
                forr = lbl.get_attribute("for") or ""
                if text:
                    log(f"  Label {i}: '{text}' for='{forr}'")
            except:
                pass
    except:
        pass

    try:
        legends = driver.find_elements(By.TAG_NAME, "legend")
        log(f"\n--- {len(legends)} legends ---")
        for l in legends:
            try:
                log(f"  Legend: '{l.text.strip()}'")
            except:
                pass
    except:
        pass

    try:
        headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, .section-title, .card-title, .title, mat-card-title, .header-title")
        log(f"\n--- {len(headings)} headings ---")
        for h in headings:
            try:
                text = h.text.strip()
                if text:
                    log(f"  Heading: '{text}' ({h.tag_name})")
            except:
                pass
    except:
        pass

    log("\n--- Form footer buttons ---")
    try:
        form_btns = driver.find_elements(By.CSS_SELECTOR, ".card-footer button, .modal-footer button, .dialog-footer button, .form-footer button, .footer button, .actions button, .button-row button, .btn-group button, .form-actions button, button[type='submit'], button[type='button']")
        log(f"Found {len(form_btns)} form buttons")
        for btn in form_btns:
            try:
                text = btn.text.strip()
                if text:
                    log(f"  Footer button: '{text}'")
            except:
                pass
        all_btns = driver.find_elements(By.TAG_NAME, "button")
        log(f"\n--- All buttons on form ({len(all_btns)}) ---")
        for i, btn in enumerate(all_btns):
            try:
                text = btn.text.strip()
                if text:
                    log(f"  Button {i}: '{text}'")
            except:
                pass
    except:
        pass

    log("\n--- Tabs / stepper / accordion ---")
    tab_selectors = [
        ".mat-tab-label", ".mat-tab-label-content", ".nav-tabs li",
        ".nav-tabs a", ".tab", ".tab-header", "mat-step",
        ".mat-step-label", "mat-stepper", ".step", ".stepper",
        ".accordion", "mat-expansion-panel", "p-tabview",
        "p-accordionTab", "p-tabPanel", ".p-tabview-nav li",
        ".p-steps", "ul.stepper", "[role='tab']", "[role='tablist']",
    ]
    for sel in tab_selectors:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                log(f"\nFound {len(elems)} with '{sel}':")
                for e in elems:
                    try:
                        text = e.text.strip()
                        if text:
                            log(f"  '{text}'")
                    except:
                        pass
        except:
            pass
    return True
def explore_edit_form(driver):
    log("\n" + "="*70)
    log("STEP D: EDIT FORM EXPLORATION")
    log("="*70)
    log("\n--- Looking for action button in first row ---")
    action_btn = None
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, "button.mat-icon-button, button[mat-icon-button], button.mat-mdc-icon-button")
        for btn in buttons:
            try:
                html = btn.get_attribute("outerHTML")
                if "more" in html.lower() or "menu" in html.lower() or "action" in html.lower() or "ellipsis" in html.lower() or "three" in html.lower():
                    action_btn = btn
                    log("Found action button")
                    break
            except:
                pass
    except:
        pass
    if not action_btn:
        try:
            first_row = driver.find_element(By.CSS_SELECTOR, "tbody tr, .mat-row, .ag-row, [role='row']")
            action_btn = first_row.find_element(By.CSS_SELECTOR, "button, a, i, span[role='button']")
            log("Found first row button as action")
        except:
            pass
    if action_btn:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", action_btn)
            time.sleep(0.5)
            action_btn.click()
            log("Clicked action button")
            time.sleep(1)
        except Exception as e:
            log(f"Could not click: {e}")
            return False
        edit_item = None
        try:
            edit_item = driver.find_element(By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'edit')]")
            log(f"Edit menu item: '{edit_item.text.strip()}'")
        except:
            log("No Edit found by XPath")
        if not edit_item:
            try:
                menu_items = driver.find_elements(By.CSS_SELECTOR, ".mat-menu-item, .mat-mdc-menu-item, [role='menuitem'], .dropdown-menu li")
                log(f"Menu items: {len(menu_items)}")
                for item in menu_items:
                    try:
                        text = item.text.strip()
                        if text:
                            log(f"  Menu: '{text}'")
                            if "edit" in text.lower():
                                edit_item = item
                    except:
                        pass
            except:
                pass
        if edit_item:
            try:
                edit_item.click()
                log("Clicked Edit")
                time.sleep(3)
                log("\n--- Edit form fields ---")
                form_fields = []
                for sel in ["input", "select", "textarea", "mat-select", "mat-option", ".mat-form-field", ".form-group", ".form-control", "label", ".field-label", ".label", "mat-label", "[formcontrolname]", "[formControlName]"]:
                    try:
                        elems = driver.find_elements(By.CSS_SELECTOR, sel)
                        for e in elems:
                            try:
                                text = e.text.strip()
                                ph = e.get_attribute("placeholder") or ""
                                aria_label = e.get_attribute("aria-label") or ""
                                name = e.get_attribute("name") or ""
                                fcn = e.get_attribute("formcontrolname") or e.get_attribute("formControlName") or ""
                                cls = e.get_attribute("class") or ""
                                info = f"tag={e.tag_name} text='{text[:50]}' placeholder='{ph}' aria-label='{aria_label}' name='{name}' formControlName='{fcn}' class='{cls[:60]}'"
                                if text or ph or aria_label or fcn:
                                    if info not in form_fields:
                                        form_fields.append(info)
                                        log(f"  Field: {info}")
                            except:
                                pass
                    except:
                        pass
                labels = driver.find_elements(By.TAG_NAME, "label")
                log(f"\n{len(labels)} labels in edit:")
                for i, lbl in enumerate(labels):
                    try:
                        text = lbl.text.strip()
                        if text:
                            log(f"  Label {i}: '{text}'")
                    except:
                        pass
                log("\n--- Edit footer buttons ---")
                for i, btn in enumerate(driver.find_elements(By.TAG_NAME, "button")):
                    try:
                        text = btn.text.strip()
                        if text:
                            log(f"  Button {i}: '{text}'")
                    except:
                        pass
                log("\n--- Disabled/read-only fields ---")
                for inp in driver.find_elements(By.CSS_SELECTOR, "input, select, textarea"):
                    try:
                        disabled = inp.get_attribute("disabled")
                        readonly = inp.get_attribute("readonly")
                        name = inp.get_attribute("name") or inp.get_attribute("formcontrolname") or ""
                        if disabled or readonly:
                            log(f"  Disabled/Read-only: {name} disabled={disabled} readonly={readonly}")
                    except:
                        pass
                return True
            except Exception as e:
                log(f"Error in Edit: {e}")
                return False
        else:
            log("No Edit option found")
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            return False
    else:
        log("No action button found")
        return False
def explore_view_popup(driver):
    log("\n" + "="*70)
    log("STEP E: VIEW POPUP EXPLORATION")
    log("="*70)
    log("\n--- Looking for action button in first row ---")
    action_btn = None
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, "button.mat-icon-button, button[mat-icon-button], button.mat-mdc-icon-button, button.btn, .action-btn")
        for btn in buttons:
            try:
                html = btn.get_attribute("outerHTML")
                if "more" in html.lower() or "menu" in html.lower() or "action" in html.lower() or "ellipsis" in html.lower():
                    action_btn = btn
                    log("Found action button")
                    break
            except:
                pass
    except:
        pass
    if action_btn:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", action_btn)
            time.sleep(0.5)
            action_btn.click()
            log("Clicked action button")
            time.sleep(1)
        except Exception as e:
            log(f"Could not click: {e}")
            return
        view_item = None
        try:
            view_item = driver.find_element(By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view')]")
            log(f"View menu item: '{view_item.text.strip()}'")
        except:
            log("No View by XPath")
        if not view_item:
            try:
                menu_items = driver.find_elements(By.CSS_SELECTOR, ".mat-menu-item, .mat-mdc-menu-item, [role='menuitem'], .dropdown-menu li")
                for item in menu_items:
                    text = item.text.strip()
                    if "view" in text.lower():
                        view_item = item
                        log(f"Found View: '{text}'")
                        break
            except:
                pass
        if view_item:
            try:
                view_item.click()
                log("Clicked View")
                time.sleep(3)
                log("\n--- View popup content ---")
                dialog_selectors = [
                    ".modal-content", ".modal-body", ".modal-dialog",
                    ".mat-dialog-content", ".mat-dialog-container",
                    ".dialog", ".popup", ".popover",
                    ".cdk-dialog-container", ".card", ".card-body",
                    ".overlay-content", ".p-dialog-content", ".modal",
                    "[role='dialog']", ".view-panel",
                ]
                for sel in dialog_selectors:
                    try:
                        elems = driver.find_elements(By.CSS_SELECTOR, sel)
                        if elems:
                            log(f"Found {len(elems)} with '{sel}':")
                            for e in elems:
                                try:
                                    text = e.text.strip()
                                    if text:
                                        log(f"  Content: '{text[:500]}'")
                                except:
                                    pass
                    except:
                        pass
                log("\n--- Labels and values ---")
                view_elems = driver.find_elements(By.CSS_SELECTOR, "label, .label, .field-label, .value, .field-value, dt, dd, .view-field, .data-field, span, div")
                for e in view_elems:
                    try:
                        text = e.text.strip()
                        if text and len(text) < 150:
                            cls = e.get_attribute("class") or ""
                            if any(x in cls.lower() for x in ["label", "field", "value", "data", "title"]):
                                log(f"  '{text}' (class={cls[:60]})")
                    except:
                        pass
                log("\n--- Close buttons ---")
                close_btns = driver.find_elements(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'close')]")
                if not close_btns:
                    close_btns = driver.find_elements(By.CSS_SELECTOR, ".close, .btn-close, .dialog-close, button[aria-label='Close'], .mat-dialog-close")
                for btn in close_btns:
                    try:
                        text = btn.text.strip()
                        log(f"  Close button: '{text}'")
                    except:
                        pass
            except Exception as e:
                log(f"Error in View: {e}")
        else:
            log("No View option found")
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    else:
        log("No action button found for View")

def explore_status_and_other_features(driver):
    log("\n" + "="*70)
    log("STEP F: STATUS, CHECKBOXES, EXPORT, BULK, FILTERS")
    log("="*70)
    log("\n--- Status indicators ---")
    status_selectors = [
        ".status", ".badge", ".tag", ".status-badge",
        "span[class*='status']", "div[class*='status']",
        ".chip", "mat-chip", "span[class*='badge']", ".pill",
    ]
    for sel in status_selectors:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                log(f"Found {len(elems)} with '{sel}':")
                for e in elems[:10]:
                    try:
                        text = e.text.strip()
                        cls = e.get_attribute("class") or ""
                        if text:
                            log(f"  Status: '{text}' class='{cls[:60]}'")
                    except:
                        pass
        except:
            pass

    log("\n--- Checkboxes ---")
    checkbox_selectors = [
        "input[type='checkbox']", ".mat-checkbox", "mat-checkbox",
        "p-checkbox", ".checkbox", "th input[type='checkbox']",
        "thead input[type='checkbox']", ".select-all",
        ".selection-checkbox", "[role='checkbox']",
    ]
    for sel in checkbox_selectors:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                log(f"Found {len(elems)} with '{sel}':")
                for e in elems[:5]:
                    try:
                        html = e.get_attribute("outerHTML")[:150]
                        checked = e.get_attribute("checked") or "false"
                        log(f"  Checkbox: checked={checked} | {html}")
                    except:
                        pass
        except:
            pass

    log("\n--- Export/Print/Download ---")
    try:
        export_btn = driver.find_element(By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'export') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'print') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download')]")
        log(f"Found: '{export_btn.text.strip()}'")
    except:
        log("No Export/Print/Download found")

    log("\n--- Bulk actions ---")
    try:
        bulk_elems = driver.find_elements(By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bulk')]")
        if bulk_elems:
            for e in bulk_elems:
                log(f"  Bulk: '{e.text.strip()}'")
        else:
            log("No bulk actions found")
    except:
        pass

    log("\n--- Filters ---")
    filter_selectors = [
        ".filter", ".filters", ".filter-row",
        "input[placeholder*='filter']", "input[placeholder*='Filter']",
        ".search-box", ".search-box input", ".quick-filter",
        "th input", "thead input", "mat-form-field.filter",
        ".p-filter", "p-columnFilter", ".column-filter",
        "i.fa-filter", "button .fa-filter", ".show-filter",
    ]
    for sel in filter_selectors:
        try:
            if ":contains(" in sel:
                continue
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                log(f"Found filters with '{sel}':")
                for e in elems[:5]:
                    try:
                        text = e.text.strip()
                        ph = e.get_attribute("placeholder") or ""
                        cls = e.get_attribute("class") or ""
                        log(f"  Filter: '{text}' placeholder='{ph}' class='{cls[:60]}'")
                    except:
                        pass
        except:
            pass
def explore_toolbar(driver):
    log("\n" + "="*70)
    log("STEP G: TOOLBAR / HEADER ACTIONS")
    log("="*70)
    toolbar_selectors = [
        ".toolbar", ".header-toolbar", ".action-bar",
        ".page-header", ".top-bar", ".mat-toolbar",
    ]
    for sel in toolbar_selectors:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                log(f"\nToolbar with '{sel}':")
                for e in elems:
                    try:
                        text = e.text.strip()
                        html = e.get_attribute("outerHTML")[:300]
                        log(f"  Content: '{text[:200]}'")
                    except:
                        pass
        except:
            pass
    log("\n--- Visible page text (first 3000 chars) ---")
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        log(body.text.strip()[:3000])
    except:
        pass

def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("ERP PURCHASE ORDER SCREEN EXPLORATION RESULTS\n")
        f.write("="*70 + "\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n")
    driver = None
    try:
        driver = init_driver()
        driver.set_page_load_timeout(30)
        login(driver)
        navigate_to_po(driver)
        explore_table_columns(driver)
        explore_row_action_menu(driver)
        explore_add_form(driver)
        explore_status_and_other_features(driver)
        explore_toolbar(driver)
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
        except:
            pass
        navigate_to_po(driver)
        explore_edit_form(driver)
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
        except:
            pass
        navigate_to_po(driver)
        explore_view_popup(driver)
        log("\n" + "="*70)
        log("EXPLORATION COMPLETE")
        log("="*70)
    except Exception as e:
        log(f"\nFATAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())
    finally:
        if driver:
            log("\nClosing browser...")
            try:
                time.sleep(5)
                driver.quit()
            except:
                pass
    print(f"\nResults written to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
