import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

OUTPUT = r"C:\Users\vedantd\Desktop\Pacs_Automation\po_exploration_part4.txt"

def log(msg):
    print(msg)
    with open(OUTPUT, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

driver = webdriver.Chrome()
driver.set_page_load_timeout(30)

try:
    # Login
    driver.get("https://rhythmerp.algorhythms.in/#/authentication/signin")
    time.sleep(3)
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

    # Go to PO
    driver.get("https://rhythmerp.algorhythms.in/#/purchase/purchase-order")
    time.sleep(5)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("ERP PO EXPLORATION - PART 4 (COMPREHENSIVE)\n")
        f.write("="*70 + "\n")

    # Get FULL page source and save it
    log("=== PAGE HTML ANALYSIS ===")
    html = driver.page_source
    
    # Save full HTML
    with open(r"C:\Users\vedantd\Desktop\Pacs_Automation\po_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    log(f"Full HTML saved ({len(html)} chars)")

    # Find ALL table-related elements
    log("\n=== ALL <table> elements ===")
    tables = driver.find_elements(By.TAG_NAME, "table")
    log(f"Total tables: {len(tables)}")
    for ti, tbl in enumerate(tables):
        tid = tbl.get_attribute("id") or ""
        tcls = tbl.get_attribute("class") or ""
        log(f"  Table {ti}: id='{tid}' class='{tcls}'")
        # Check if it has data
        rows_t = tbl.find_elements(By.TAG_NAME, "tr")
        log(f"    Rows: {len(rows_t)}")

    # Find ALL elements with role="row" or class containing "row"
    log("\n=== ROW ELEMENTS ===")
    for sel in ["[role='row']", "[role='rowgroup']", ".mat-mdc-row", ".cdk-row", "[class*='row']"]:
        elems = driver.find_elements(By.CSS_SELECTOR, sel)
        if elems:
            log(f"  '{sel}': {len(elems)} elements")
            for ei, e in enumerate(elems[:3]):
                cls = e.get_attribute("class") or ""
                log(f"    [{ei}] class='{cls[:80]}'")

    # Find ALL header elements
    log("\n=== HEADER CELLS ===")
    for sel in ["[role='columnheader']", ".mat-mdc-header-cell", "th"]:
        elems = driver.find_elements(By.CSS_SELECTOR, sel)
        if elems:
            log(f"  '{sel}': {len(elems)} cells")
            for ei, e in enumerate(elems):
                txt = e.text.strip()
                log(f"    [{ei}] '{txt}'")

    # Find ALL buttons
    log("\n=== ALL BUTTONS WITH TEXT ===")
    btns_with_text = []
    for btn in driver.find_elements(By.TAG_NAME, "button"):
        txt = btn.text.strip()
        cls = btn.get_attribute("class") or ""
        if txt:
            btns_with_text.append((txt, cls[:80]))
            log(f"  text='{txt}' class='{cls[:80]}'")

    # Try a different approach - look at the actual table structure
    log("\n=== INSPECTING TABLE BODY STRUCTURE ===")
    # The main table might be inside an Angular Material table
    # Let me look at cdk-table or mat-table
    for sel in [".mat-mdc-table", "mat-table", ".cdk-table", "table.mat-table"]:
        tables2 = driver.find_elements(By.CSS_SELECTOR, sel)
        if tables2:
            log(f"Found {len(tables2)} with selector '{sel}'")

    # Look at the data rows more carefully
    log("\n=== LOOKING FOR ANGULAR MATERIAL TABLE ROWS ===")
    # Angular Material uses cdk-row and mat-row classes
    for cls_name in ["mat-mdc-row", "mat-row", "cdk-row", "cdk-row", "mat-mdc-table"]:
        rows_am = driver.find_elements(By.CSS_SELECTOR, f".{cls_name}")
        if rows_am:
            log(f"  .{cls_name}: {len(rows_am)} found")
            for ri, r in enumerate(rows_am[:2]):
                log(f"    Row {ri}: class='{r.get_attribute('class')}'")
                cells = r.find_elements(By.CSS_SELECTOR, ".mat-mdc-cell, .cdk-cell, td")
                log(f"      Cells: {len(cells)}")
                for ci, c in enumerate(cells[:8]):
                    ctxt = c.text.strip()
                    ccls = c.get_attribute("class") or ""
                    log(f"        Cell {ci}: text='{ctxt[:50]}' class='{ccls[:60]}'")
                    # Check for buttons inside
                    inner_btns = c.find_elements(By.TAG_NAME, "button")
                    if inner_btns:
                        for ib in inner_btns:
                            log(f"          Button: class='{ib.get_attribute('class')}' html='{ib.get_attribute('outerHTML')[:200]}'")

    # Now try clicking each button in the first data row directly by finding it
    log("\n=== TRYING TO CLICK ROW ACTION BUTTON ===")
    # The action column seems to have material-icons "more_vert"
    # Let's find the first row and click the button with material-icons "more_vert"
    for cls_name in ["mat-mdc-row", "mat-row", "cdk-row"]:
        rows_cls = driver.find_elements(By.CSS_SELECTOR, f".{cls_name}")
        if rows_cls:
            first_row = rows_cls[0]
            # Find all buttons inside that have material-icons or fa-ellipsis
            row_btns = first_row.find_elements(By.TAG_NAME, "button")
            log(f"First row has {len(row_btns)} buttons")
            for bi, rb in enumerate(row_btns):
                html = rb.get_attribute("outerHTML")[:200]
                cls = rb.get_attribute("class") or ""
                txt = rb.text.strip()
                log(f"  Button {bi}: text='{txt}' class='{cls[:60]}'")
                log(f"    HTML: {html}")

            # Try clicking the button that has "more_vert" in its innerHTML
            for rb in row_btns:
                html = (rb.get_attribute("innerHTML") or "")
                if "more_vert" in html:
                    log(f"\nClicking button with more_vert...")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", rb)
                    time.sleep(0.3)
                    rb.click()
                    time.sleep(2)

                    # Check menu
                    log("Menu items:")
                    for sel_menu in [".mat-mdc-menu-item", "[role='menuitem']", ".cdk-overlay-pane *"]:
                        menu_items = driver.find_elements(By.CSS_SELECTOR, sel_menu)
                        if menu_items:
                            for mi in menu_items:
                                mtxt = mi.text.strip()
                                if mtxt:
                                    log(f"  '{mtxt}'")
                    break
            break

    log("\n\n=== DONE ===")

finally:
    time.sleep(5)
    driver.quit()
