FILE = 'pages/common_settings/modules/uom_conversion/uom_conversion_page.py'
with open(FILE, 'r', encoding='utf-8') as f:
    c = f.read()

old_close = '''    def _close_select_panel(self):
        \"\"\"Close only select dropdown panel, keeping form popup open.\"\"\"
        try:
            self.driver.execute_script(\"\"\"
                var backdrops = document.querySelectorAll('.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)');
                for (var i = 0; i < backdrops.length; i++) {
                    backdrops[i].click();
                }
                document.querySelectorAll('.cdk-overlay-pane').forEach(function(p) {
                    if (!p.querySelector('.swal2-popup')) p.remove();
                });
            \"\"\")
            time.sleep(0.3)
        except Exception:
            pass'''

new_close = '''    def _close_select_panel(self):
        \"\"\"Close select dropdown panel by pressing Escape. Safe for Angular state.\"\"\"
        try:
            self.driver.execute_script(\"\"\"
                var esc = new KeyboardEvent('keydown', {key:'Escape',code:'Escape',bubbles:true});
                document.activeElement.dispatchEvent(esc);
                document.body.dispatchEvent(esc);
            \"\"\")
            time.sleep(0.3)
        except Exception:
            pass'''

if old_close in c:
    c = c.replace(old_close, new_close, 1)
    print('_close_select_panel: fixed')
else:
    print('_close_select_panel: NOT FOUND')

old_read = '''    def _read_dropdown_uoms(self):
        \"\"\"Read UOM options from Source UOM dropdown. Form must be open.\"\"\"
        log.info("Reading UOM options from Source UOM dropdown")
        js_open = \"\"\"
        var fields = document.querySelectorAll('div.edit_pop_up mat-form-field');
        for (var i = 0; i < fields.length; i++) {
            var label = fields[i].querySelector('mat-label');
            if (label && label.textContent.trim().indexOf('Source UOM') !== -1) {
                var trigger = fields[i].querySelector('.mat-mdc-select-trigger');
                if (trigger) { trigger.click(); return 'opened'; }
            }
        }
        throw new Error('Source UOM dropdown not found in form');
        \"\"\"
        self.driver.execute_script(js_open)
        time.sleep(1.5)
        js_read = \"\"\"
        var start = Date.now();
        while (Date.now() - start < 3000) {
            var opts = document.querySelectorAll('.cdk-overlay-pane mat-option .mdc-list-item__primary-text');
            if (opts.length > 0) break;
        }
        var options = document.querySelectorAll('.cdk-overlay-pane mat-option .mdc-list-item__primary-text');
        var uoms = [];
        for (var i = 0; i < options.length; i++) {
            var text = options[i].textContent.trim();
            if (text) uoms.push(text);
        }
        return uoms;
        \"\"\"
        uoms = self.driver.execute_script(js_read)
        log.info("Found " + str(len(uoms) if uoms else 0) + " UOM options in dropdown")
        self._close_select_panel()
        time.sleep(0.5)
        if not uoms:
            raise RuntimeError("No UOM options found in dropdown")
        return uoms'''

new_read = '''    def _read_dropdown_uoms(self):
        \"\"\"Open Source UOM dropdown and read all options. Leaves dropdown OPEN.\"\"\"
        log.info("Opening Source UOM dropdown to read options")
        js = \"\"\"
        var fields = document.querySelectorAll('div.edit_pop_up mat-form-field');
        for (var i = 0; i < fields.length; i++) {
            var label = fields[i].querySelector('mat-label');
            if (label && label.textContent.trim().indexOf('Source UOM') !== -1) {
                var trigger = fields[i].querySelector('.mat-mdc-select-trigger');
                if (trigger) { trigger.click(); return 'opened'; }
            }
        }
        throw new Error('Source UOM dropdown not found in form');
        \"\"\"
        self.driver.execute_script(js)
        time.sleep(1.5)
        js_read = \"\"\"
        var start = Date.now();
        while (Date.now() - start < 3000) {
            var opts = document.querySelectorAll('.cdk-overlay-pane mat-option .mdc-list-item__primary-text');
            if (opts.length > 0) break;
        }
        var options = document.querySelectorAll('.cdk-overlay-pane mat-option .mdc-list-item__primary-text');
        var uoms = [];
        for (var i = 0; i < options.length; i++) {
            var text = options[i].textContent.trim();
            if (text) uoms.push(text);
        }
        return uoms;
        \"\"\"
        uoms = self.driver.execute_script(js_read)
        log.info("Found " + str(len(uoms) if uoms else 0) + " UOM options")
        if not uoms:
            raise RuntimeError("No UOM options found in dropdown")
        return uoms'''

if old_read in c:
    c = c.replace(old_read, new_read, 1)
    print('_read_dropdown_uoms: fixed')
else:
    print('_read_dropdown_uoms: NOT FOUND')

old_create = '''    def create_fresh_record(self):
        \"\"\"
        One-flow: read existing pairs from table, open form, read dropdown,
        pick fresh pair, fill fields, submit. Form opens once, never closes
        until submit. Returns dict with source_uom, target_uom, conversion_factor.
        \"\"\"
        log.info("Creating fresh UOM conversion record")
        existing = self.get_existing_pairs()
        self.open_add_form()
        time.sleep(1)
        uoms = self._read_dropdown_uoms()
        source, target = None, None
        for _ in range(50):
            s, t = random.sample(uoms, 2)
            if (s, t) not in existing:
                source, target = s, t
                break
        if not source:
            raise RuntimeError("Could not find fresh pair after 50 attempts")
        factor = str(random.randint(1, 1000))
        log.info("Fresh pair: " + source + " -> " + target + " = " + factor)
        self.select_source_uom(source)
        self.select_target_uom(target)
        self.enter_conversion_factor(factor)
        self.submit()
        return {"source_uom": source, "target_uom": target, "conversion_factor": factor}'''

new_create = '''    def _select_from_open_panel(self, uom_code):
        \"\"\"Click an option in the ALREADY OPEN dropdown panel. Does NOT reopen.\"\"\"
        log.info("Selecting from open panel: " + uom_code)
        js = \"\"\"
        var options = document.querySelectorAll('.cdk-overlay-pane mat-option');
        for (var i = 0; i < options.length; i++) {
            var text = options[i].querySelector('.mdc-list-item__primary-text');
            if (text && text.textContent.trim() === arguments[0]) {
                options[i].click();
                return 'selected: ' + arguments[0];
            }
        }
        var needle = arguments[0].toUpperCase();
        for (var i = 0; i < options.length; i++) {
            var text = options[i].querySelector('.mdc-list-item__primary-text');
            if (text && text.textContent.trim().toUpperCase().indexOf(needle) !== -1) {
                options[i].click();
                return 'selected (partial): ' + text.textContent.trim();
            }
        }
        throw new Error('Option not found in open panel: ' + arguments[0]);
        \"\"\"
        result = self.driver.execute_script(js, uom_code)
        log.info(result)
        time.sleep(0.5)

    def create_fresh_record(self):
        \"\"\"
        One-flow: read existing pairs, open form, open Source dropdown,
        read all options, pick fresh pair, select source from open dropdown,
        then open Target dropdown and select target. Form opens once.
        Dropdown state is never corrupted.
        \"\"\"
        log.info("Creating fresh UOM conversion record")
        existing = self.get_existing_pairs()
        self.open_add_form()
        time.sleep(1)

        # Open Source dropdown and read ALL options (dropdown stays OPEN)
        uoms = self._read_dropdown_uoms()

        # Pick a fresh pair
        source, target = None, None
        for _ in range(50):
            s, t = random.sample(uoms, 2)
            if (s, t) not in existing:
                source, target = s, t
                break
        if not source:
            raise RuntimeError("Could not find fresh pair after 50 attempts")
        factor = str(random.randint(1, 1000))
        log.info("Fresh pair: " + source + " -> " + target + " = " + factor)

        # Select source from the ALREADY OPEN dropdown (no reopen needed)
        self._select_from_open_panel(source)
        time.sleep(0.5)

        # Select target via normal flow (opens fresh dropdown)
        self.select_target_uom(target)

        # Fill factor and submit
        self.enter_conversion_factor(factor)
        self.submit()
        return {"source_uom": source, "target_uom": target, "conversion_factor": factor}'''

if old_create in c:
    c = c.replace(old_create, new_create, 1)
    print('create_fresh_record: fixed (+ added _select_from_open_panel)')
else:
    print('create_fresh_record: NOT FOUND')

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(c)

print()
print('Verify:')
print('  _select_from_open_panel:', '_select_from_open_panel' in c)
print('  _close_select_panel uses Escape:', 'Escape' in c.split('def _close_select_panel')[1].split('def ')[0])
print('  _read_dropdown no close:', '_close_select_panel' not in c.split('def _read_dropdown_uoms')[1].split('def ')[0])
print('  create uses _select_from_open_panel:', '_select_from_open_panel(source)' in c)
