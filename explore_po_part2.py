import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

OUTPUT = r"C:\Users\vedantd\Desktop\Pacs_Automation\po_exploration_part2.txt"

def log(msg):
    print(msg)
    with open(OUTPUT, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    return driver

def login(driver):
    log("=== LOGIN ===")
    driver.get("https://rhythmerp.algorhythms.in/#/authentication/signin")
    time.sleep(3)

    # Fill email
    for inp in driver.find_elements(By.TAG_NAME, "input"):
        at = inp.get_attribute("type") or ""
        ph = inp.get_attribute("placeholder") or ""
        if "email" in (at + ph).lower():
            inp.clear()
            inp.send_keys("Gautams@gmail.com")
            log("Email entered")
            break

    # Fill password
    for inp in driver.find_elements(By.TAG_NAME, "input"):
        at = inp.get_attribute("type") or ""
        ph = inp.get_attribute("placeholder") or ""
        if "password" in (at + ph).lower():
            inp.clear()
            inp.send_keys("Test@2526270")
            log("Password entered")
            break

    # Dismiss tenant dropdown - click body
    time.sleep(1)
    ActionChains(driver).move_by_offset(10, 10).click().perform()
    time.sleep(0.5)

    # Click Login button
    for btn in driver.find_elements(By.TAG_NAME, "button"):
        if btn.text.strip().lower() == "login":
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(0.3)
            btn.click()
            log("Login clicked")
            break

    time.sleep(5)
    log(f"URL after login: {driver.current_url}")

def wait_and_navigate(driver, url):
    driver.get(url)
    time.sleep(5)
    log(f"Navigated to: {driver.current_url}")
def click_row_action_menu(driver):
    log("\n=== CLICK ROW ACTION MENU (more_vert) ===")
    # Find the first "more_vert" button in a data row (NOT pagination)
    # Look inside the table body rows
    rows = driver.find_elements(By.CSS_SELECTOR, ".mat-mdc-row, tbody tr, [mat-row], .cdk-row")
    log(f"Found {len(rows)} data rows")

    # Find all mat-icon-button elements that have material-icons "more_vert"
    # These are the action buttons
    icon_btns = driver.find_elements(By.CSS_SELECTOR, ".mat-mdc-icon-button .mat-mdc-button-touch-target, .mat-mdc-icon-button")
    log(f"Found {len(icon_btns)} icon buttons total")

    # Look specifically for buttons containing "more_vert" text or material-icons
    more_vert_btns = []
    for btn in driver.find_elements(By.TAG_NAME, "button"):
        try:
            inner = btn.get_attribute("innerHTML") or ""
            cls = btn.get_attribute("class") or ""
            if "more_vert" in inner or "more-vert" in cls or "ellipsis" in inner.lower():
                more_vert_btns.append(btn)
                log(f"Found more_vert button: class={cls[:60]}")
        except:
            pass

    if more_vert_btns:
        # Try clicking the first one that is in the first data row
        log("Clicking first more_vert button")
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_vert_btns[0])
            time.sleep(0.5)
            more_vert_btns[0].click()
            log("Clicked more_vert button")
            time.sleep(1.5)
        except Exception as e:
            log(f"Click failed: {e}")
            try:
                driver.execute_script("arguments[0].click();", more_vert_btns[0])
                log("Clicked via JS")
                time.sleep(1.5)
            except Exception as e2:
                log(f"JS click failed: {e2}")
    else:
        log("No more_vert buttons found")
        # Dump all buttons for analysis
        log("All buttons:")
        for i, btn in enumerate(driver.find_elements(By.TAG_NAME, "button")):
            try:
                inner = (btn.get_attribute("innerHTML") or "")[:100]
                cls = btn.get_attribute("class") or ""
                aria = btn.get_attribute("aria-label") or ""
                log(f"  [{i}] class={cls[:50]} | aria={aria} | inner={inner}")
            except:
                pass

    # Now check for the dropdown menu that should have appeared
    log("\nMenu items after click:")
    time.sleep(1)
    for sel in [".mat-mdc-menu-item", ".mat-menu-item", "[role='menuitem']",
                ".cdk-overlay-pane button", ".cdk-overlay-pane .mat-mdc-menu-item",
                ".mat-mdc-menu-content .mat-mdc-menu-item"]:
        items = driver.find_elements(By.CSS_SELECTOR, sel)
        if items:
            log(f"Found {len(items)} items with '{sel}':")
            for item in items:
                txt = item.text.strip()
                if txt:
                    log(f"  -> '{txt}'")

    # Check overlay panes
    panes = driver.find_elements(By.CSS_SELECTOR, ".cdk-overlay-pane")
    log(f"Overlay panes: {len(panes)}")
    for pi, pane in enumerate(panes):
        try:
            ptxt = pane.text.strip()
            if ptxt:
                log(f"  Pane {pi}: {ptxt[:500]}")
        except:
            pass

    # Press Escape to dismiss
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(0.5)
def check_toolbar_actions(driver):
    log("\n=== TOOLBAR ACTIONS ===")
    # Find all toolbar-like elements
    for sel in [".page-header", ".action-bar", ".toolbar", ".mat-toolbar",
                "[class*='header']", "[class*='toolbar']", "[class*='action-bar']"]:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in elems:
                txt = e.text.strip()
                if txt:
                    log(f"  [{sel}] {txt[:200]}")
        except:
            pass

    # Find all buttons in the header/toolbar area
    log("\nLooking for Add, Export, Filter, Refresh buttons in header...")
    for btn in driver.find_elements(By.TAG_NAME, "button"):
        try:
            txt = btn.text.strip()
            inner = (btn.get_attribute("innerHTML") or "")
            cls = btn.get_attribute("class") or ""
            aria = btn.get_attribute("aria-label") or ""
            if txt or "search" in inner or "filter" in inner or "refresh" in inner or "add" in inner or "export" in inner or "print" in inner or "download" in inner:
                log(f"  Toolbar button: text='{txt}' aria='{aria}' class={cls[:40]}")
        except:
            pass

def check_filters(driver):
    log("\n=== FILTER OPTIONS ===")
    # Look for filter input fields
    for inp in driver.find_elements(By.TAG_NAME, "input"):
        try:
            ph = inp.get_attribute("placeholder") or ""
            aria = inp.get_attribute("aria-label") or ""
            if "filter" in (ph + aria).lower() or "search" in (ph + aria).lower():
                log(f"  Filter input: placeholder='{ph}' aria='{aria}'")
        except:
            pass

    # Look for filter icon/button
    for sel in ["i.fa-filter", "i.fa-search", ".fa-filter", ".fa-search",
                "mat-icon:contains('filter')", "mat-icon:contains('search')",
                "button:has(mat-icon)", "[class*='filter']", "[class*='Filter']"]:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in elems:
                try:
                    txt = e.text.strip()
                    cls = e.get_attribute("class") or ""
                    if "filter" in cls.lower() or "search" in cls.lower() or txt.lower() in ("filter_list", "search"):
                        log(f"  Filter icon: text='{txt}' class='{cls[:50]}'")
                except:
                    pass
        except:
            pass

def check_export(driver):
    log("\n=== EXPORT / PRINT OPTIONS ===")
    for btn in driver.find_elements(By.TAG_NAME, "button"):
        try:
            txt = btn.text.strip().lower()
            inner = (btn.get_attribute("innerHTML") or "").lower()
            if txt in ("export", "print", "download", "csv", "excel", "pdf"):
                log(f"  Export button: '{btn.text.strip()}'")
            if "export" in inner or "print" in inner:
                log(f"  Possible export/print: inner={inner[:100]}")
        except:
            pass

def check_pagination(driver):
    log("\n=== PAGINATION ===")
    for sel in [".mat-paginator", ".p-paginator", ".pagination", ".paginator"]:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                for e in elems:
                    log(f"  Paginator: {e.text.strip()[:200]}")
        except:
            pass
    # Items per page
    for sel in [".mat-mdc-select-value", ".mat-select-value"]:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in elems:
                log(f"  Items per page: {e.text.strip()}")
        except:
            pass

def check_status_badges(driver):
    log("\n=== STATUS BADGES ===")
    for sel in ["span.status-active", "span.status-inactive", "span.status-pending",
                "span[class*='status']", ".badge", ".status-badge"]:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                for e in elems[:5]:
                    log(f"  Status badge: '{e.text.strip()}' class='{e.get_attribute('class')}'")
        except:
            pass

def check_checkboxes(driver):
    log("\n=== CHECKBOXES ===")
    for sel in ["input[type='checkbox']", ".mat-checkbox", "mat-checkbox", "p-checkbox"]:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                for e in elems[:3]:
                    log(f"  Checkbox: tag={e.tag_name} class='{e.get_attribute('class')[:60]}'")
        except:
            pass

def check_bulk_actions(driver):
    log("\n=== BULK ACTIONS ===")
    for btn in driver.find_elements(By.TAG_NAME, "button"):
        txt = btn.text.strip().lower()
        if "bulk" in txt or "batch" in txt or "mass" in txt:
            log(f"  Bulk action: '{btn.text.strip()}'")
    # Also look for bulk action bar
    for sel in [".bulk-actions", ".bulk-action-bar", ".batch-actions"]:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                for e in elems:
                    log(f"  Bulk bar: {e.text.strip()[:200]}")
        except:
            pass
def check_add_form_details(driver):
    log("\n=== ADD FORM DETAILED EXPLORATION ===")
    # Find Add button
    add_found = False
    for btn in driver.find_elements(By.TAG_NAME, "button"):
        txt = btn.text.strip().lower()
        if txt == "add purchase order" or "add" in txt.split():
            log(f"Clicking Add button: '{btn.text.strip()}'")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(0.3)
            btn.click()
            add_found = True
            time.sleep(3)
            break

    if not add_found:
        log("Could not find Add button")
        return

    # Section headings in the form
    log("\n--- Section headers/headings ---")
    for sel in ["h1", "h2", "h3", "h4", "h5", "h6",
                ".card-header", ".card-title", ".section-title",
                ".form-section-title", ".header-title",
                "mat-card-title", "[class*='section']"]:
        try:
            for e in driver.find_elements(By.CSS_SELECTOR, sel):
                txt = e.text.strip()
                cls = e.get_attribute("class") or ""
                if txt and len(txt) < 100:
                    # Filter for actual section headers
                    if any(x in cls.lower() for x in ["section", "header", "title", "card"]) or any(x in txt.lower() for x in ["detail", "section", "supplier", "item", "additional", "purchase"]):
                        log(f"  Section: '{txt}' class='{cls[:50]}'")
        except:
            pass

    # Form labels (all)
    log("\n--- All form labels ---")
    labels = driver.find_elements(By.TAG_NAME, "label")
    log(f"Total labels: {len(labels)}")
    for lbl in labels:
        try:
            txt = lbl.text.strip()
            if txt:
                log(f"  Label: '{txt}'")
        except:
            pass

    # Form input placeholders
    log("\n--- All input placeholders ---")
    for inp in driver.find_elements(By.TAG_NAME, "input"):
        try:
            ph = inp.get_attribute("placeholder") or ""
            nm = inp.get_attribute("name") or ""
            if ph or nm:
                log(f"  Input: placeholder='{ph}' name='{nm}'")
        except:
            pass

    # Select / dropdown elements
    log("\n--- Select / dropdown elements ---")
    for sel_tag in ["mat-select", "select", "p-dropdown"]:
        try:
            for e in driver.find_elements(By.TAG_NAME, sel_tag):
                try:
                    txt = e.text.strip()
                    cls = e.get_attribute("class") or ""
                    if txt:
                        log(f"  {sel_tag}: text='{txt[:100]}' class='{cls[:40]}'")
                except:
                    pass
        except:
            pass

    # Footer buttons specifically in the form
    log("\n--- Form footer/action buttons ---")
    for btn in driver.find_elements(By.TAG_NAME, "button"):
        txt = btn.text.strip()
        cls = btn.get_attribute("class") or ""
        if txt in ("Cancel", "Submit", "Save", "Update", "Reset") or "submit" in cls or "save" in cls:
            log(f"  Footer button: '{txt}' class='{cls[:50]}'")

    # Mat-select options in form
    log("\n--- mat-select toggle elements ---")
    for ms in driver.find_elements(By.TAG_NAME, "mat-select"):
        try:
            log(f"  mat-select: text='{ms.text.strip()[:100]}'")
        except:
            pass

    # Checkbox / radio in form
    log("\n--- Radio/checkbox options in form ---")
    for sel_r in ["mat-radio-button", ".mat-radio-button", "mat-checkbox", ".mat-checkbox"]:
        try:
            for e in driver.find_elements(By.CSS_SELECTOR, sel_r):
                try:
                    txt = e.text.strip()
                    if txt:
                        log(f"  {sel_r}: '{txt}'")
                except:
                    pass
        except:
            pass
def try_view_popup(driver):
    log("\n=== VIEW POPUP ===")
    # Navigate back to list view
    driver.get("https://rhythmerp.algorhythms.in/#/purchase/purchase-order")
    time.sleep(4)

    # Find the first more_vert button
    rows = driver.find_elements(By.CSS_SELECTOR, ".mat-mdc-row, tbody tr")
    if not rows:
        log("No data rows found")
        return

    first_row = rows[0]
    more_btn = first_row.find_elements(By.CSS_SELECTOR, "button")
    if not more_btn:
        log("No buttons in first row")
        return

    log(f"Clicking button in first row: innerHTML={more_btn[0].get_attribute('innerHTML')[:100]}")
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_btn[0])
        time.sleep(0.3)
        more_btn[0].click()
        log("Clicked row action button")
        time.sleep(1.5)
    except Exception as e:
        log(f"Click failed: {e}")
        return

    # Check for View in menu
    view_item = None
    for sel in [".mat-mdc-menu-item", ".mat-menu-item", "[role='menuitem']"]:
        items = driver.find_elements(By.CSS_SELECTOR, sel)
        for item in items:
            txt = item.text.strip()
            log(f"  Menu item: '{txt}'")
            if "view" in txt.lower():
                view_item = item

    if view_item:
        log("Clicking View menu item")
        view_item.click()
        time.sleep(3)

        # Read view content
        log("\n--- View popup content ---")
        for sel in [".mat-dialog-container", ".mat-dialog-content",
                    ".cdk-dialog-container", "[role='dialog']",
                    ".modal-content", ".modal-body", ".p-dialog-content"]:
            for e in driver.find_elements(By.CSS_SELECTOR, sel):
                txt = e.text.strip()
                if txt:
                    log(f"  {sel}: {txt[:800]}")
                    break
    else:
        log("No View option in menu")
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)

def main():
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("ERP PO EXPLORATION - PART 2 (DETAILED)\n")
        f.write("="*70 + "\n")

    driver = init_driver()
    driver.set_page_load_timeout(30)

    try:
        login(driver)
        wait_and_navigate(driver, "https://rhythmerp.algorhythms.in/#/purchase/purchase-order")

        check_toolbar_actions(driver)
        check_filters(driver)
        check_export(driver)
        check_pagination(driver)
        check_status_badges(driver)
        check_checkboxes(driver)
        check_bulk_actions(driver)

        # Try to click row action menu and get menu items
        click_row_action_menu(driver)

        # Go to Add form and explore details
        driver.get("https://rhythmerp.algorhythms.in/#/purchase/purchase-order")
        time.sleep(3)
        check_add_form_details(driver)

        # Try View popup
        try_view_popup(driver)

        log("\n=== EXPLORATION COMPLETE ===")
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc())
    finally:
        time.sleep(3)
        driver.quit()

    print(f"\nResults written to: {OUTPUT}")

if __name__ == "__main__":
    main()
