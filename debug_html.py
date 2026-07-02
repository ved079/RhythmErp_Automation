"""Quick debug: inspect popup HTML."""
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    ctx = browser.new_context(
        storage_state="pages/common_settings/modules/tax_rate/test/playwright_auth.json"
    )
    page = ctx.new_page()
    page.set_default_timeout(10000)
    page.goto(
        "https://rhythmerp.algorhythms.in/#/dynamic-screens/Tax%20Rate"
    )
    page.wait_for_selector("table#excel-table", timeout=15000)

    # Click ADD
    page.evaluate("""
        var btn = document.querySelector('button.erp-add-btn');
        if (!btn) {
            var icons = document.querySelectorAll('app-custom-header mat-icon, app-custom-header i.material-icons');
            for (var i = 0; i < icons.length; i++) {
                if (icons[i].textContent.trim() === 'add') {
                    btn = icons[i].closest('button'); break;
                }
            }
        }
        if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
    """)
    page.wait_for_selector("div.edit_pop_up", timeout=10000)
    page.wait_for_timeout(1000)

    # Dump relevant HTML
    html = page.evaluate("""
        var popup = document.querySelector('div.edit_pop_up');
        if (!popup) return 'NO POPUP';
        return Array.from(popup.querySelectorAll('mat-form-field')).map(function(f) {
            var label = f.querySelector('mat-label');
            var labelText = label ? label.textContent.trim() : 'NO_LABEL';
            var inputs = f.querySelectorAll('input');
            var inputInfo = Array.from(inputs).map(function(inp) {
                return 'input[name=' + (inp.getAttribute('name') || 'null') + ']';
            }).join(', ');
            var selects = f.querySelectorAll('mat-select');
            var selectInfo = selects.length > 0 ? 'HAS_MAT_SELECT' : '';
            return labelText + ': ' + inputInfo + ' ' + selectInfo;
        }).join('\\n');
    """)
    print("=== POPUP FIELDS ===")
    print(html)

    page.screenshot(path="debug_popup.png")
    print("\nScreenshot saved.")
    input("Press Enter to close...")
    browser.close()
