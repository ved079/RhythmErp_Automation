"""Inspect popup HTML structure."""
import os, json
from playwright.sync_api import sync_playwright

STORAGE = "pages/common_settings/modules/tax_rate/test/playwright_auth.json"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(storage_state=STORAGE)
    page = ctx.new_page()
    page.set_default_timeout(15000)
    page.goto("https://rhythmerp.algorhythms.in/#/dynamic-screens/Tax%20Rate")
    page.wait_for_selector("table#excel-table", timeout=20000)

    # Click ADD button
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

    # Get field info from popup
    info = page.evaluate("""
        (function() {
            var popup = document.querySelector('div.edit_pop_up');
            if (!popup) return 'NO POPUP';
            var fields = popup.querySelectorAll('mat-form-field');
            var result = [];
            for (var i = 0; i < fields.length; i++) {
                var f = fields[i];
                var label = f.querySelector('mat-label');
                var labelText = label ? label.textContent.trim() : 'NO_LABEL';
                var inputs = f.querySelectorAll('input');
                var inputNames = [];
                for (var j = 0; j < inputs.length; j++) {
                    var attrs = {};
                    ['name','id','type','placeholder'].forEach(function(k) {
                        var v = inputs[j].getAttribute(k);
                        if (v) attrs[k] = v;
                    });
                    inputNames.push(JSON.stringify(attrs));
                }
                var hasSelect = f.querySelector('mat-select') !== null;
                var hasTextarea = f.querySelector('textarea') !== null;
                result.push(labelText + '|inputs:' + inputNames.join(',') + '|select:' + hasSelect + '|textarea:' + hasTextarea);
            }
            return result.join('\\n');
        })()
    """)
    print("=== POPUP FIELDS ===")
    print(info)

    # Dump full popup HTML (first 4000 chars)
    html = page.evaluate("""
        (function() {
            var popup = document.querySelector('div.edit_pop_up');
            return popup ? popup.outerHTML.substring(0,5000) : 'NO POPUP';
        })()
    """)
    with open("debug_popup.html", "w") as f:
        f.write(html)
    page.screenshot(path="debug_popup.png")
    print("Saved debug_popup.html + debug_popup.png")
    b.close()
