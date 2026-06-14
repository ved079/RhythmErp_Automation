import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OUTPUT = r"C:\Users\vedantd\Desktop\Pacs_Automation\po_exploration_part3.txt"

def log(msg):
    print(msg)
    with open(OUTPUT, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

driver = webdriver.Chrome()
driver.set_page_load_timeout(30)
driver.get("https://rhythmerp.algorhythms.in/#/authentication/signin")
time.sleep(3)

# Login
for inp in driver.find_elements(By.TAG_NAME, "input"):
    at = inp.get_attribute("type") or ""
    ph = inp.get_attribute("placeholder") or ""
    if "email" in (at + ph).lower():
        inp.clear()
        inp.send_keys("Gautams@gmail.com")
        break
for inp in driver.find_elements(By.TAG_NAME, "input"):
    at = inp.get_attribute("type") or ""
    ph = inp.get_attribute("placeholder") or ""
    if "password" in (at + ph).lower():
        inp.clear()
        inp.send_keys("Test@2526270")
        break
time.sleep(1)
ActionChains(driver).move_by_offset(10, 10).click().perform()
time.sleep(0.5)
for btn in driver.find_elements(By.TAG_NAME, "button"):
    if btn.text.strip().lower() == "login":
        btn.click()
        break
time.sleep(5)

driver.get("https://rhythmerp.algorhythms.in/#/purchase/purchase-order")
time.sleep(5)

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("ERP PO EXPLORATION - PART 3 (ROW ACTION MENU)\n")
    f.write("="*70 + "\n")

# === Now click the row-level action menu (erp-row-trigger) ===
log("=== ROW-LEVEL ACTION MENU ===")

# Find the row trigger buttons (exclude toolbar more_vert)
row_triggers = driver.find_elements(By.CSS_SELECTOR, "button.erp-row-trigger")
log(f"Found {len(row_triggers)} row trigger buttons")

if row_triggers:
    # Click the first one
    btn = row_triggers[0]
    log(f"Class: {btn.get_attribute('class')}")
    log(f"HTML: {btn.get_attribute('outerHTML')[:200]}")
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(0.3)
        btn.click()
        log("Clicked row trigger")
        time.sleep(2)
    except Exception as e:
        log(f"Click failed: {e}")
        driver.execute_script("arguments[0].click();", btn)
        log("Clicked via JS")
        time.sleep(2)

    # Now check menu
    log("\n--- Menu items after clicking row trigger ---")
    for sel in [".mat-mdc-menu-item", "[role='menuitem']", ".mat-menu-item",
                ".cdk-overlay-pane button", ".cdk-overlay-pane *"]:
        items = driver.find_elements(By.CSS_SELECTOR, sel)
        if items:
            log(f"\nWith selector '{sel}':")
            for item in items:
                try:
                    txt = item.text.strip()
                    html = item.get_attribute("outerHTML")[:200]
                    if txt:
                        log(f"  '{txt}'")
                        log(f"    HTML: {html}")
                except:
                    pass

    # Check overlay panes
    panes = driver.find_elements(By.CSS_SELECTOR, ".cdk-overlay-pane")
    log(f"\nOverlay panes: {len(panes)}")
    for pi, pane in enumerate(panes):
        try:
            txt = pane.text.strip()
            if txt:
                log(f"  Pane {pi}: {txt}")
        except:
            pass

    # Close the menu
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(0.5)
else:
    log("No row trigger buttons found")
    # Look for any button in the first row
    rows = driver.find_elements(By.CSS_SELECTOR, ".mat-mdc-row, .cdk-row, tbody tr")
    if rows:
        log(f"\nFirst row buttons:")
        btns = rows[0].find_elements(By.TAG_NAME, "button")
        for bi, b in enumerate(btns):
            log(f"  Button {bi}: class={b.get_attribute('class')} html={b.get_attribute('outerHTML')[:150]}")
        # Try clicking the last button in the row (usually the action)
        if btns:
            log("\nClicking last button in row")
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btns[-1])
                time.sleep(0.3)
                btns[-1].click()
                log("Clicked")
                time.sleep(2)
            except Exception as e:
                log(f"Failed: {e}")

            log("\n--- Menu items ---")
            for sel in [".mat-mdc-menu-item", "[role='menuitem']", ".mat-menu-item",
                        ".cdk-overlay-pane button"]:
                items = driver.find_elements(By.CSS_SELECTOR, sel)
                if items:
                    for item in items:
                        txt = item.text.strip()
                        if txt:
                            log(f"  '{txt}'")

            panes = driver.find_elements(By.CSS_SELECTOR, ".cdk-overlay-pane")
            for pi, pane in enumerate(panes):
                txt = pane.text.strip()
                if txt:
                    log(f"  Pane {pi}: {txt}")

# === Also check if there is a separate "Export" button on the toolbar ===
log("\n\n=== EXPORT BUTTON ON TOOLBAR ===")
driver.get("https://rhythmerp.algorhythms.in/#/purchase/purchase-order")
time.sleep(4)

# The first more_vert on toolbar (not erp-row-trigger) showed Export options earlier
# Click it and explore
toolbar_more = driver.find_elements(By.CSS_SELECTOR, "button.erp-outline-btn.mat-mdc-menu-trigger")
log(f"Toolbar action buttons: {len(toolbar_more)}")
for tb in toolbar_more:
    cls = tb.get_attribute("class")
    html = tb.get_attribute("outerHTML")[:150]
    log(f"  class={cls}")
    log(f"  html={html}")

if toolbar_more:
    log("\nClicking toolbar global actions (more_vert)...")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", toolbar_more[0])
    time.sleep(0.3)
    toolbar_more[0].click()
    time.sleep(2)

    log("\nToolbar global menu items:")
    for sel in [".mat-mdc-menu-item", "[role='menuitem']"]:
        for item in driver.find_elements(By.CSS_SELECTOR, sel):
            txt = item.text.strip()
            if txt:
                log(f"  '{txt}'")
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(0.5)

log("\n\n=== CHECK FOR INDIVIDUAL ROW ACTION MENU (NOT ADD ROW) ===")
# The first data row might have both an expand icon and a more_vert
# Let me inspect the first row carefully
rows = driver.find_elements(By.CSS_SELECTOR, ".mat-mdc-row")
if rows:
    row0 = rows[0]
    log(f"First row HTML (simplified):")
    log(f"  Row classes: {row0.get_attribute('class')}")
    cells = row0.find_elements(By.CSS_SELECTOR, ".mat-mdc-cell")
    for ci, cell in enumerate(cells):
        cls = cell.get_attribute("class") or ""
        txt = cell.text.strip()
        inner = (cell.get_attribute("innerHTML") or "")[:100]
        log(f"  Cell {ci}: class='{cls[:50]}' text='{txt[:40]}' inner='{inner}'")

# Look for column index of the action column
log("\n--- Checking which column index has the more_vert button ---")
headers = driver.find_elements(By.CSS_SELECTOR, ".mat-mdc-header-cell")
for hi, h in enumerate(headers):
    log(f"  Header {hi}: '{h.text.strip()}'")

driver.quit()
log("\nDone")
