// ERP Playwright Recorder — fullview.js

const TYPE_META = {
  select:        { label: 'SELECT',   color: '#7ee787' },
  input:         { label: 'INPUT',    color: '#79c0ff' },
  button:        { label: 'BUTTON',   color: '#ffa657' },
  'dialog-open': { label: 'DIALOG ▼', color: '#d2a8ff' },
  'dialog-close':{ label: 'DIALOG ▲', color: '#6e7681' },
  swal2:         { label: 'SWAL2',    color: '#f8e3a1' },
  navigate:      { label: 'NAV',      color: '#56d364' },
  row:           { label: 'ROW',      color: '#79c0ff' },
  tracking:      { label: 'TRACK',    color: '#ffa657' },
  readonly:      { label: 'READ',     color: '#a5b4fc' },
  start:         { label: 'START',    color: '#56d364' },
  search:        { label: 'SEARCH',   color: '#79c0ff' },
  error:         { label: 'ERROR',    color: '#f85149' },
  comment:       { label: 'NOTE',     color: '#6e7681' },
};

// ── Phase detection ───────────────────────────────────────────────────────
const PHASE = {
  start:         'NAVIGATE',
  navigate:      'NAVIGATE',
  'dialog-open': 'NAVIGATE',
  'dialog-close':'NAVIGATE',
  input:         'FILL FORM',
  select:        'FILL FORM',
  button:        'ACTION',
  swal2:         'ACTION',
  error:         'VALIDATION',
  comment:       'VALIDATION',
  readonly:      'VERIFY',
  tracking:      'VERIFY',
  row:           'VERIFY',
};

function phaseOf(type) { return PHASE[type] || 'ACTION'; }

// ── Summary block ────────────────────────────────────────────────────────
function buildSummary(steps) {
  if (!steps.length) return [];
  const startStep = steps.find(s => s.type === 'start');
  let module = '';
  if (startStep) {
    // Try dynamic-screens/Module/SubModule first, then last 1-2 path segments
    const url = startStep.label;
    const mDyn = url.match(/dynamic-screens\/([^/?#]+)/);
    if (mDyn) {
      module = decodeURIComponent(mDyn[1]);
    } else {
      // For hash-router URLs (/#/path/to/module), extract segments from the fragment
      const hashMatch = url.match(/#\/(.+)/);
      const pathStr = hashMatch ? hashMatch[1] : url.replace(/[?#].*/, '');
      const segs = pathStr.split('/').filter(Boolean);
      module = segs.slice(-2).map(s => s.replace(/-/g, ' ')).join(' / ');
    }
  }
  const counts = {};
  steps.forEach(s => { const p = phaseOf(s.type); counts[p] = (counts[p] || 0) + 1; });
  const fills   = (counts['FILL FORM'] || 0);
  const errs    = steps.filter(s => s.type === 'error').length;
  const rdonly  = steps.filter(s => s.type === 'readonly').length;
  const navs    = steps.filter(s => s.type === 'navigate').length;
  const phases  = [...new Set(steps.map(s => phaseOf(s.type)))].join(' → ');
  const w = 46;
  const pad = (str, len) => str + ' '.repeat(Math.max(0, len - str.length));
  const row = (label, val) => `# │ ${pad(label + ': ' + val, w)} │`;
  return [
    `# ┌${'─'.repeat(w + 2)}┐`,
    row('Module',  module || '(unknown)'),
    row('Steps',   `${steps.length}  │  Fill: ${fills}  │  Errors: ${errs}  │  Readonly: ${rdonly}  │  Navs: ${navs}`),
    row('Flow',    phases),
    `# └${'─'.repeat(w + 2)}┘`,
    '',
  ];
}

// ── Stepper breadcrumb tracker ────────────────────────────────────────────
// Extracts [StepLabel] prefix from error/comment step labels.
function extractStepperLabel(s) {
  // error label: [StepLabel] "Field": "msg"
  if (s.type === 'error') {
    const m = (s.label || '').match(/^\[([^\]]+)\]/);
    return m ? m[1] : null;
  }
  // comment label: "No validation errors on [StepLabel]"
  if (s.type === 'comment') {
    const m = (s.label || '').match(/\[([^\]]+)\]/);
    if (m) return m[1];
    const mc = (s.code || '').match(/\[([^\]]+)\]/);
    return mc ? mc[1] : null;
  }
  // matsteppernext value: "Next:StepLabel"
  if (s.type === 'button' && (s.code || '').includes('matsteppernext')) {
    const m = (s.value || '').match(/^[^:]+:(.+)$/);
    return m ? m[1] : null;
  }
  return null;
}

// ── Field-type hint ───────────────────────────────────────────────────────
function fieldTypeHint(s) {
  if (s.type === 'select') return '  # [dropdown]';
  if (s.type === 'input') {
    const code = s.code || '';
    if (code.includes('@matinput') && code.includes('fill(')) return '  # [date DD/MM/YYYY]';
    if (code.includes('type="number"') || /\d{4,}/.test(s.value || '')) return '  # [number]';
    return '  # [text]';
  }
  return '';
}

// ── Auto-patch inline block ───────────────────────────────────────────────
function patchedBlock(s) {
  if (!s.patched || !s.patched.length) return [];
  // Dedup by label+rowIndex (same field can appear twice if both nth variants match)
  const seen = new Set();
  s.patched = s.patched.filter(p => {
    const k = `${p.label}:${p.rowIndex ?? ''}`;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
  const out = [];

  // Header — what triggered these auto-fills
  const trigger = s.type === 'start'    ? 'page load'
                : s.type === 'navigate' ? 'navigation'
                : s.type === 'select'   ? `selecting "${s.label}" = "${s.value}"`
                : s.type === 'input'    ? `filling "${s.label}" = "${s.value}"`
                : `"${s.label}"`;

  // Align field names for readability
  const maxLen = Math.max(...s.patched.map(p => p.label.length));
  const pad = (str, len) => str + ' '.repeat(Math.max(0, len - str.length));

  out.push(`# ╔═ Auto-filled by ${trigger}:`);
  for (const p of s.patched) {
    const rowTag = p.rowIndex != null ? ` [row ${p.rowIndex + 1}]` : '';
    const displayLabel = p.label + rowTag;
    out.push(`# ║  ${pad(displayLabel, maxLen + 8)} = "${p.value}"`);
  }
  out.push(`# ╚═ [AI: read with ${s.patched[0].isSelect ? '.text_content().strip()' : '.input_value()'}; store in variables if used downstream]`);

  // Wait guard for async select autofill
  if (s.type === 'select') {
    const p0 = s.patched[0];
    const nth = p0.rowIndex != null ? `.nth(${p0.rowIndex})` : '';
    const tgt = p0.isSelect ? 'mat-select' : 'input';
    const lp0 = p0.label.replace(/'/g, "\\'");
    out.push(`page.locator("xpath=//mat-label[contains(.,'${lp0}')]/ancestor::mat-form-field//${tgt}")${nth}.wait_for(state="visible", timeout=10000)`);
  }

  // Asserts
  for (const p of s.patched) {
    const lp = p.label.replace(/'/g, "\\'");
    const vq = p.value.replace(/"/g, '\\"');
    const nth = p.rowIndex != null ? `.nth(${p.rowIndex})` : '';
    out.push(p.isSelect
      ? `assert page.locator("xpath=//mat-label[contains(.,'${lp}')]/ancestor::mat-form-field//mat-select")${nth}.text_content().strip() == "${vq}"`
      : `assert page.locator("xpath=//mat-label[contains(.,'${lp}')]/ancestor::mat-form-field//input")${nth}.input_value() == "${vq}"`);
  }
  return out;
}

// ── Helpers for #2 and #3 ────────────────────────────────────────────────

// #2: is this step a Submit button inside a popup footer?
function isSubmitStep(s) {
  return s.type === 'button' &&
    (s.code || '').includes('popup-footer') &&
    (s.code || '').includes('Submit');
}

// #3: look backward from submitIdx for the last non-select computed field label
// (either a standalone readonly step or a patched field from a select/input step)
function findLastComputedFieldLabel(steps, submitIdx) {
  for (let j = submitIdx - 1; j >= 0; j--) {
    const s = steps[j];
    if (s.patched && s.patched.length) {
      const p = [...s.patched].reverse().find(p => !p.isSelect);
      if (p) return p.label;
    }
    if (s.type === 'readonly' && !s.isSelect) return s.label;
  }
  return null;
}

function generateCode(steps) {
  if (!steps.length) return '# No steps recorded yet.';

  // Count stepper steps for breadcrumb N/M
  const allStepperLabels = [];
  steps.forEach(s => {
    const lbl = extractStepperLabel(s);
    if (lbl && !allStepperLabels.includes(lbl)) allStepperLabels.push(lbl);
  });

  const lines = [
    '# Generated by ERP Playwright Recorder',
    '',
    ...buildSummary(steps),
  ];

  let lastPhase = null;
  let lastStepperLabel = null;

  for (let i = 0; i < steps.length; i++) {
    const s = steps[i];
    const prev = steps[i - 1];
    const phase = phaseOf(s.type);

    // ── Phase section header ──────────────────────────────────────────
    // Determine if this step will actually emit any output (suppressed steps don't)
    const willSuppress = s.type === 'button' &&
      (s.code || '').includes("mattooltip='Search'") &&
      nextStep && nextStep.type === 'search';
    if (phase !== lastPhase) {
      if (!willSuppress) {
        if (lastPhase !== null) lines.push('');
        lines.push(`# ${'═'.repeat(3)} ${phase} ${'═'.repeat(Math.max(0, 44 - phase.length))}`);
        lastPhase = phase;
      }
    } else if (prev && needsBlankLine(prev.type, s.type)) {
      lines.push('');
    }

    // ── Stepper breadcrumb (only when there are multiple steps) ──────
    const stepperLbl = extractStepperLabel(s);
    if (stepperLbl && stepperLbl !== lastStepperLabel && allStepperLabels.length > 1) {
      const idx = allStepperLabels.indexOf(stepperLbl) + 1;
      const total = allStepperLabels.length;
      lines.push(`# ── Stepper: ${stepperLbl} (${idx}/${total}) ──`);
      lastStepperLabel = stepperLbl;
    }

    // ── Navigate / dialog annotations ────────────────────────────────
    if (s.type === 'navigate')          lines.push(`# ── Navigate: ${s.label} ──`);
    else if (s.type === 'dialog-open')  lines.push(`# ── Dialog opened: "${s.label}" ──`);
    else if (s.type === 'dialog-close') lines.push(`# ── Dialog closed ──`);
    else if (s.type === 'tracking')     lines.push(`# ── PB tracking card ──`);

    // ── #2: search step before row-trigger click ──────────────────────
    // Only inject when the user didn't already record a search step for this ref
    if (s.type === 'button' && (s.code || '').includes('erp-row-trigger')) {
      const m = s.code.match(/tr:has-text\('([^']+)'\)/);
      if (m) {
        const recentSearch = steps.slice(Math.max(0, i - 6), i).some(
          ps => ps.type === 'search' || (ps.code || '').includes('erpSearchInput')
        );
        if (!recentSearch) {
          const refNo = m[1].replace(/"/g, '\\"');
          lines.push(`# [AI: filter the list before clicking the row — avoids ambiguous match when many rows exist]`);
          lines.push(`if not page.locator("input#erpSearchInput").is_visible():`);
          lines.push(`    page.locator("button[mattooltip='Search']").click()`);
          lines.push(`page.locator("input#erpSearchInput").fill("${refNo}")`);
          lines.push(`page.locator("input#erpSearchInput").press("Enter")`);
          lines.push(`page.wait_for_timeout(1000)`);
        }
      }
    }

    // ── #3: computed-fields wait before Submit ────────────────────────
    if (isSubmitStep(s)) {
      const lbl = findLastComputedFieldLabel(steps, i);
      if (lbl) {
        const lp = lbl.replace(/'/g, "\\'");
        lines.push(`# [AI: computed fields populate async — wait until non-empty before submitting]`);
        lines.push(`expect(page.locator("xpath=//mat-label[contains(.,'${lp}')]/ancestor::mat-form-field//input").first).not_to_have_value("", timeout=10000)`);
      }
    }

    // ── Main code line + field-type hint ─────────────────────────────
    // Suppress the standalone Search button click when the next step is a
    // search step (the search step already includes the if-not-visible guard)
    const nextStep = steps[i + 1];
    const isRedundantSearchBtn = s.type === 'button' &&
      (s.code || '').includes("mattooltip='Search'") &&
      nextStep && nextStep.type === 'search';

    if (!isRedundantSearchBtn) {
      const hint = fieldTypeHint(s);
      if (hint && !s.code.includes('\n')) {
        lines.push(s.code + hint);
      } else {
        lines.push(s.code);
      }
    }
    // search steps need a settle wait after Enter
    if (s.type === 'search') lines.push('page.wait_for_timeout(1000)');

    // ── Auto-patch inline block ───────────────────────────────────────
    patchedBlock(s).forEach(l => lines.push(l));
  }

  return lines.join('\n');
}

function needsBlankLine(a, b) {
  const g = {
    navigate: 0,
    'dialog-open': 1, 'dialog-close': 1,
    select: 2, input: 2,
    button: 3,
    swal2: 4, tracking: 4,
    row: 5,
    readonly: 6,
  };
  return (g[a] ?? 9) !== (g[b] ?? 9);
}

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

let currentSteps = [];
let isRecording  = false;

function render(steps, recording) {
  currentSteps = steps || [];
  isRecording  = !!recording;

  const dot = document.getElementById('dot');
  const lbl = document.getElementById('rec-lbl');
  const btn = document.getElementById('btn-toggle');
  const cnt = document.getElementById('step-count');
  cnt.textContent = currentSteps.length + (currentSteps.length === 1 ? ' step' : ' steps');

  if (recording) {
    dot.classList.add('on'); lbl.classList.add('on');
    lbl.textContent = 'RECORDING'; btn.textContent = 'Stop'; btn.classList.add('stop');
  } else {
    dot.classList.remove('on'); lbl.classList.remove('on');
    lbl.textContent = currentSteps.length ? 'PAUSED' : 'IDLE';
    btn.textContent = 'Start'; btn.classList.remove('stop');
  }

  const list = document.getElementById('step-list');
  if (!currentSteps.length) {
    list.innerHTML = `<div class="empty"><span class="empty-dot">⏺</span><span>No steps yet.<br>Start recording and interact with the ERP.</span></div>`;
  } else {
    list.innerHTML = currentSteps.map((s, i) => {
      const m = TYPE_META[s.type] || { label: s.type.toUpperCase(), color: '#484f58' };
      return `
        <div class="step-row">
          <span class="step-num">${i + 1}</span>
          <span class="step-badge" style="color:${m.color};border-color:${m.color}22;background:${m.color}11">${m.label}</span>
          <div class="step-body">
            <div class="step-label">${esc(s.label || '')}</div>
            ${s.value ? `<div class="step-val">${esc(String(s.value).slice(0, 60))}</div>` : ''}
            <div class="step-code">${esc((s.code || '').split('\n')[0].slice(0, 70))}</div>
          </div>
        </div>`;
    }).join('');
    list.scrollTop = list.scrollHeight;
  }

  document.getElementById('code-out').value = generateCode(currentSteps);
}

// ── Communicate with the recording tab ───────────────────────────────────
// fullview is its own tab; we query ALL tabs but stop after the first response.

function sendToRecordingTab(msg, cb) {
  chrome.tabs.query({}, tabs => {
    if (chrome.runtime.lastError) return;
    let responded = false;
    for (const tab of tabs) {
      if (tab.id === chrome.tabs.TAB_ID_NONE) continue;
      if (responded) break;
      chrome.tabs.sendMessage(tab.id, msg, res => {
        if (chrome.runtime.lastError) return;
        if (res && !responded) { responded = true; if (cb) cb(res); }
      });
    }
  });
}

// ── Buttons ───────────────────────────────────────────────────────────────

document.getElementById('btn-toggle').addEventListener('click', () => {
  sendToRecordingTab({ type: 'TOGGLE_REC' }, res => render(res.steps, res.recording));
});

document.getElementById('btn-clear').addEventListener('click', () => {
  chrome.storage.local.set({ erp_steps: [], erp_recording: false });
  sendToRecordingTab({ type: 'CLEAR' }, () => {});
  render([], false);
});

document.getElementById('btn-restart').addEventListener('click', () => {
  chrome.storage.local.set({ erp_steps: [], erp_recording: true });
  sendToRecordingTab({ type: 'RESTART' }, () => {});
  render([], true);
});

document.getElementById('btn-copy').addEventListener('click', () => {
  navigator.clipboard.writeText(generateCode(currentSteps)).then(() => {
    const btn = document.getElementById('btn-copy');
    const orig = btn.textContent;
    btn.textContent = 'Copied!'; btn.classList.add('copied');
    setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 1500);
  });
});

// ── Page-object generator ─────────────────────────────────────────────────

function toConstName(label) {
  return label.toUpperCase().replace(/[^A-Z0-9]+/g, '_').replace(/^_+|_+$/g, '');
}
function toDataKey(label) {
  return label.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
}
const CASCADE_TRIGGERS = new Set(['State', 'Country', 'District', 'Taluka', 'Village']);

function generatePageObject(steps) {
  if (!steps.length) return '# No steps recorded yet.';

  let moduleName = 'Module', url = '';
  const navStep = steps.find(s => s.type === 'navigate');
  if (navStep) {
    url = navStep.label || '';
    const m = url.match(/\/([^/?#]+)(?:[/?#]|$)/g);
    if (m && m.length) moduleName = m[m.length - 1].replace(/[^a-zA-Z0-9]/g, '') || 'Module';
  }

  const fieldSteps = [], constMap = {}, seen = new Set();
  for (const s of steps) {
    if (!s.label || seen.has(s.label)) continue;
    if (s.type !== 'select' && s.type !== 'input') continue;
    seen.add(s.label);
    const name = toConstName(s.label);
    constMap[s.label] = name;
    fieldSteps.push({ ...s, constName: name });
  }

  const constLines = fieldSteps.map(s => {
    const tag     = s.type === 'select' ? 'mat-select' : 'input';
    const escaped = s.label.replace(/'/g, "\\'");
    const padded  = s.constName.padEnd(26);
    return `    ${padded}= "xpath=//mat-form-field[.//mat-label[normalize-space(.)='${escaped}']]//${tag}"`;
  });

  const formLines = [];
  for (let i = 0; i < steps.length; i++) {
    const s = steps[i], next = steps[i + 1];
    if (s.type === 'select' && constMap[s.label]) {
      const val = (s.value || '').replace(/"/g, '\\"'), key = toDataKey(s.label);
      formLines.push(`        self._select_mat_option_by_text(self.${constMap[s.label]}, data.get("${key}", "${val}"))`);
      if (CASCADE_TRIGGERS.has(s.label) && next && next.type === 'select' && constMap[next.label])
        formLines.push(`        self.page.locator(self.${constMap[next.label]}).nth(0).wait_for(state="visible", timeout=10000)`);
    } else if (s.type === 'input' && constMap[s.label]) {
      const val = (s.value || '').replace(/"/g, '\\"'), key = toDataKey(s.label);
      formLines.push(`        self._fill_text(self.${constMap[s.label]}, data.get("${key}", "${val}"))`);
    } else if (s.type === 'button' && s.code && s.code.includes('matsteppernext')) {
      formLines.push(`        self._click_next()`);
    }
  }

  const lines = [
    `import random`,
    `from pages.base_playwright_page import BasePlaywrightPage`,
    ``, ``,
    `class ${moduleName}Page(BasePlaywrightPage):`,
    `    URL = "${url}"`,
    ``,
    `    # ── Selectors ─────────────────────────────────────────────────────────`,
    `    SUBMIT_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"`,
    `    CANCEL_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"`,
    `    SEARCH_INPUT = "#erpSearchInput"`,
    ``,
    ...constLines,
    ``,
    `    # ── mat-select helpers (proven pattern — do not simplify) ─────────────`,
    `    def _select_mat_option_by_text(self, selector, text, nth=0):`,
    `        self.page.locator(selector).nth(nth).click(force=True)`,
    `        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)`,
    `        options = self.page.locator(".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text").filter(has_text=text)`,
    `        matched = None`,
    `        for opt in options.all():`,
    `            if opt.inner_text().strip() == text: matched = opt; break`,
    `        if matched: matched.click(force=True)`,
    `        else: self.page.locator(".mat-mdc-select-panel mat-option").filter(has_text=text).first.click(force=True)`,
    `        try: self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)`,
    `        except Exception: pass`,
    `        self.page.wait_for_timeout(300)`,
    ``,
    `    def _select_random_mat_option(self, selector, nth=0):`,
    `        self.page.locator(selector).nth(nth).click(force=True)`,
    `        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)`,
    `        options = self.page.locator(".mat-mdc-select-panel mat-option:not(.dd-clear-option)").all()`,
    `        if options: random.choice(options).click(force=True)`,
    `        try: self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)`,
    `        except Exception: pass`,
    `        self.page.wait_for_timeout(500)`,
    ``,
    `    def _try_select_random_mat_option(self, selector, nth=0):`,
    `        self.page.locator(selector).nth(nth).click(force=True)`,
    `        try: self.page.wait_for_selector(".mat-mdc-select-panel", timeout=3000)`,
    `        except Exception: return`,
    `        options = self.page.locator(".mat-mdc-select-panel mat-option:not(.dd-clear-option)").all()`,
    `        if options: random.choice(options).click(force=True)`,
    `        try: self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)`,
    `        except Exception: pass`,
    `        self.page.wait_for_timeout(300)`,
    ``,
    `    def _fill_text(self, selector, value, nth=0):`,
    `        loc = self.page.locator(selector).nth(nth)`,
    `        loc.click(force=True); loc.fill(str(value)); loc.press("Tab")`,
    ``,
    `    def _click_next(self):`,
    `        self.page.evaluate("""`,
    `            const btns = document.querySelectorAll('button[matsteppernext]');`,
    `            for (const btn of btns) {`,
    `                if (btn.offsetParent !== null && getComputedStyle(btn).display !== 'none') {`,
    `                    btn.scrollIntoView({block:'center'}); btn.click(); break;`,
    `                }`,
    `            }""")`,
    `        self.page.wait_for_timeout(1000)`,
    ``,
    `    def _clear_overlays(self):`,
    `        self.page.evaluate("document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove())")`,
    ``,
    `    # ── Form ──────────────────────────────────────────────────────────────`,
    `    def fill_form(self, data):`,
    ...formLines,
    ``,
    `    def submit(self):`,
    `        self._clear_overlays()`,
    `        self.page.click(self.SUBMIT_BTN)`,
    ``,
    `    def open_add_form(self):`,
    `        self.page.locator("button.erp-add-btn").click()`,
    `        self.page.wait_for_timeout(1500)`,
    ``,
    `    def navigate_to_page(self):`,
    `        self.page.goto(self.URL)`,
    `        self.page.wait_for_selector("table#excel-table", timeout=15000)`,
    ``,
    `    def create_record(self, data):`,
    `        self.open_add_form()`,
    `        self.fill_form(data)`,
    `        self.submit()`,
    `        self.handle_success_alert()`,
    `        self.navigate_to_page()`,
  ];
  return lines.join('\n');
}

document.getElementById('btn-gen-po').addEventListener('click', () => {
  const code = generatePageObject(currentSteps);
  navigator.clipboard.writeText(code).then(() => {
    const btn = document.getElementById('btn-gen-po');
    btn.textContent = 'Copied!'; btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Page Obj'; btn.classList.remove('copied'); }, 1800);
  });
});

// ── Live updates via storage polling ─────────────────────────────────────

function poll() {
  chrome.storage.local.get(['erp_steps', 'erp_recording'], data => {
    if (chrome.runtime.lastError) return;
    render(data.erp_steps || [], !!data.erp_recording);
  });
}

chrome.runtime.onMessage.addListener(msg => {
  if (msg.type === 'STATE') render(msg.steps, msg.recording);
});

poll();
setInterval(poll, 600);
