// ERP Playwright Recorder — content script
if (window.__erpRecorderInjected) { /* already running */ }
else {
window.__erpRecorderInjected = true;

(function () {
  'use strict';

  // ── State ─────────────────────────────────────────────────────────────────
  let recording = false;
  let steps = [];
  // { label, altLabel, el, prevText } — set when a mat-select is opened.
  // `el` = the mat-select element, `prevText` = its value before opening.
  let pendingSelect = null;
  let lastUrl = location.href;
  let inputCooldownUntil = 0;

  // Track last input value by label (not DOM node — Angular replaces nodes)
  const lastInputByLabel = {};

  // Readonly fields already recorded: key = `${label}:${value}` (dedup across
  // post-step snapshots, reset on navigation / clear so page re-asserts work)
  const recordedReadonly = new Set();
  let readonlyScanTimer = null;
  let readonlyScanning = false;

  // View-mode flag: set when user opens a View form; cleared on dialog-close / nav
  let viewMode = false;

  // Fields the user clicked in view mode but where _readInputValue returned ''
  // (Angular hadn't finished binding the value yet). Retried in exitViewMode()
  // when the DOM is still live and Angular has definitely settled.
  const pendingViewCaptures = new Set();

  // Red-line validation error messages already recorded (mat-error / red-line)
  const recordedErrors = new Set();

  // Last user action (select/input/button/…) — post-step snapshots of
  // auto-patched readonly fields are grouped under it ("step-wise" output)
  let lastAction = null;

  function suppressInputsFor(ms) {
    inputCooldownUntil = Date.now() + ms;
  }

  // ── Toolbar ─────────────────────────────────────────────────────────────
  const style = document.createElement('style');
  style.textContent = `
    #__erp_rec_bar {
      position: fixed; top: 14px; right: 14px; z-index: 2147483647;
      background: #0d1117; border: 1px solid #30363d; border-radius: 8px;
      font: 11px/1 'Consolas','Monaco',monospace;
      color: #c9d1d9; box-shadow: 0 4px 20px rgba(0,0,0,.6);
      user-select: none; transition: border-color .2s, box-shadow .2s;
      overflow: hidden;
    }
    #__erp_rec_bar.recording {
      border-color: #f85149;
      box-shadow: 0 0 0 2px rgba(248,81,73,.25), 0 4px 20px rgba(0,0,0,.6);
    }
    #__erp_rec_inner {
      display: flex; align-items: center; gap: 7px;
      padding: 6px 8px 6px 10px; cursor: move;
    }
    #__erp_rec_bar.mini #__erp_rec_inner { display: none; }
    #__erp_rec_mini {
      display: none; align-items: center; justify-content: center;
      width: 32px; height: 28px; cursor: pointer;
    }
    #__erp_rec_bar.mini #__erp_rec_mini { display: flex; }

    #__erp_rec_dot { font-size: 13px; color: #484f58; transition: color .2s; line-height:1; }
    #__erp_rec_dot.on { color: #f85149; animation: __blink .9s ease-in-out infinite; }
    #__erp_rec_dot2 { font-size: 15px; color: #484f58; transition: color .2s; line-height:1; }
    #__erp_rec_dot2.on { color: #f85149; animation: __blink .9s ease-in-out infinite; }
    @keyframes __blink { 0%,100%{opacity:1} 50%{opacity:.2} }

    #__erp_rec_lbl {
      font-size: 9px; letter-spacing:.1em; color: #484f58; min-width: 38px;
      transition: color .2s;
    }
    #__erp_rec_lbl.on { color: #f85149; font-weight: 600; }

    .__erp_btn {
      background: #161b22; border: 1px solid #30363d; color: #c9d1d9;
      padding: 3px 9px; border-radius: 4px; font: 10px/1 'Consolas','Monaco',monospace;
      cursor: pointer; letter-spacing:.04em; transition: background .15s;
    }
    .__erp_btn:hover { background: #21262d; }
    .__erp_btn.stop {
      border-color: #f85149; color: #f85149; background: #1c0f0f;
      animation: __glow 1.8s ease-in-out infinite;
    }
    @keyframes __glow {
      0%,100% { box-shadow: 0 0 0 0 rgba(248,81,73,0); }
      50%      { box-shadow: 0 0 6px 2px rgba(248,81,73,.35); }
    }
    #__erp_rec_cnt { color: #484f58; font-size: 10px; min-width: 44px; text-align: right; }
    #__erp_rec_cnt.has-steps { color: #c9d1d9; }

    #__erp_rec_view_badge {
      display: none; font-size: 9px; letter-spacing: .06em; font-weight: 600;
      color: #58a6ff; background: rgba(56,139,253,.12); border: 1px solid rgba(56,139,253,.3);
      border-radius: 3px; padding: 2px 5px;
    }
    #__erp_rec_view_badge.on { display: inline-block; }
    #__erp_rec_cap_all {
      display: none; background: #0d419d; border: 1px solid #58a6ff; color: #58a6ff;
      padding: 3px 9px; border-radius: 4px; font: 10px/1 'Consolas','Monaco',monospace;
      cursor: pointer; letter-spacing: .04em; transition: background .15s;
    }
    #__erp_rec_cap_all:hover { background: #1158c7; }
    #__erp_rec_cap_all.on { display: inline-block; }

    #__erp_rec_toast {
      display: none;
      padding: 4px 10px; border-top: 1px solid #21262d;
      font: 10px/1.4 'Consolas','Monaco',monospace;
      color: #3fb950; background: #0d1117;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      max-width: 340px;
      opacity: 1; transition: opacity .4s ease;
    }
    #__erp_rec_toast.show { display: block; }
    #__erp_rec_toast.fade { opacity: 0; }

    .__erp_icon_btn {
      background: transparent; border: none; color: #484f58;
      font: 12px/1 'Consolas','Monaco',monospace; cursor: pointer;
      padding: 2px 4px; border-radius: 3px; transition: color .15s;
      flex-shrink: 0;
    }
    .__erp_icon_btn:hover { color: #c9d1d9; background: #21262d; }
  `;
  document.head.appendChild(style);

  const bar = document.createElement('div');
  bar.id = '__erp_rec_bar';
  bar.innerHTML = `
    <div id="__erp_rec_inner">
      <span id="__erp_rec_dot">●</span>
      <span id="__erp_rec_lbl">IDLE</span>
      <button class="__erp_btn" id="__erp_rec_btn">Start</button>
      <button class="__erp_btn" id="__erp_rec_clr">Clear</button>
      <span id="__erp_rec_view_badge">VIEW</span>
      <button class="__erp_btn" id="__erp_rec_cap_all" title="Capture all fields on this view form">Cap All</button>
      <span id="__erp_rec_cnt">0 steps</span>
      <button class="__erp_icon_btn" id="__erp_rec_view" title="Open full view">↗</button>
      <button class="__erp_icon_btn" id="__erp_rec_min" title="Minimize">—</button>
    </div>
    <div id="__erp_rec_mini" title="Expand recorder">
      <span id="__erp_rec_dot2">●</span>
    </div>
    <div id="__erp_rec_toast"></div>
  `;
  document.body.appendChild(bar);

  // Draggable
  let drag = false, dx = 0, dy = 0;
  document.getElementById('__erp_rec_inner').addEventListener('mousedown', e => {
    if (e.target.tagName === 'BUTTON') return;
    drag = true;
    const r = bar.getBoundingClientRect();
    dx = e.clientX - r.left; dy = e.clientY - r.top;
    e.preventDefault();
  });
  document.addEventListener('mousemove', e => {
    if (!drag) return;
    bar.style.right = 'auto'; bar.style.bottom = 'auto';
    bar.style.left = (e.clientX - dx) + 'px';
    bar.style.top  = (e.clientY - dy) + 'px';
  });
  document.addEventListener('mouseup', () => { drag = false; });

  document.getElementById('__erp_rec_btn').addEventListener('click', toggleRec);
  document.getElementById('__erp_rec_clr').addEventListener('click', clearAll);
  document.getElementById('__erp_rec_view').addEventListener('click', e => {
    e.stopPropagation();
    try {
      const url = chrome.runtime.getURL('fullview.html');
      chrome.runtime.sendMessage({ type: 'OPEN_FULLVIEW' });
      const w = window.open(url, '_blank');
      if (w) w.focus();
    } catch (_) {}
  });
  document.getElementById('__erp_rec_min').addEventListener('click', e => {
    e.stopPropagation();
    bar.classList.add('mini');
  });
  document.getElementById('__erp_rec_cap_all').addEventListener('click', e => {
    e.stopPropagation();
    if (recording && viewMode) captureAllViewFields();
  });
  document.getElementById('__erp_rec_mini').addEventListener('click', () => {
    bar.classList.remove('mini');
  });

  function setBarState() {
    const dot    = document.getElementById('__erp_rec_dot');
    const dot2   = document.getElementById('__erp_rec_dot2');
    const lbl    = document.getElementById('__erp_rec_lbl');
    const btn    = document.getElementById('__erp_rec_btn');
    const cnt    = document.getElementById('__erp_rec_cnt');
    const badge  = document.getElementById('__erp_rec_view_badge');
    const capAll = document.getElementById('__erp_rec_cap_all');
    if (recording) {
      dot.classList.add('on'); dot2.classList.add('on'); lbl.classList.add('on');
      lbl.textContent = 'REC'; btn.textContent = 'Stop'; btn.classList.add('stop');
      bar.classList.add('recording');
    } else {
      dot.classList.remove('on'); dot2.classList.remove('on'); lbl.classList.remove('on');
      lbl.textContent = steps.length ? 'PAUSED' : 'IDLE';
      btn.textContent = 'Start'; btn.classList.remove('stop');
      bar.classList.remove('recording');
    }
    cnt.textContent = steps.length + (steps.length === 1 ? ' step' : ' steps');
    cnt.classList.toggle('has-steps', steps.length > 0);
    // Show VIEW badge + Cap All button only while in view mode
    badge.classList.toggle('on',  recording && viewMode);
    capAll.classList.toggle('on', recording && viewMode);
  }

  function toggleRec() {
    recording = !recording;
    if (recording && steps.length === 0) {
      // First step of a fresh recording: remember where the replay starts.
      suppressInputsFor(600);
      addStep({
        type: 'start',
        label: location.href,
        value: location.href,
        code: `# started from\npage.goto("${location.href}")\npage.wait_for_selector("mat-form-field, table.mat-mdc-table, .page-content", timeout=20000)`
      });
    }
    setBarState(); persist();
    try { chrome.runtime.sendMessage({ type: 'STATE', recording, steps }); } catch (_) {}
  }

  function clearAll() {
    steps = []; pendingSelect = null;
    viewMode = false;
    recordedErrors.clear();
    recordedReadonly.clear();
    pendingViewCaptures.clear();
    setBarState(); persist();
    try { chrome.runtime.sendMessage({ type: 'STATE', recording, steps }); } catch (_) {}
  }

  function isDuplicateStep(step) {
    if (!steps.length) return false;
    const last = steps[steps.length - 1];
    return last.type === step.type && last.label === step.label && last.value === step.value;
  }

  function addStep(step) {
    if (isDuplicateStep(step)) return;
    step.id = Date.now() + '-' + Math.random().toString(36).slice(2);
    step.patched = [];
    step.ts = Date.now();
    // Wait-guard: a mat-select selection fires async ERP calls. If the next
    // recorded interaction happens ~2s later, that field may not be rendered
    // yet — emit a wait_for_selector targeting it before replaying the step.
    const prevStep = steps[steps.length - 1];
    if (prevStep && prevStep.type === 'select' &&
        Date.now() - (prevStep.ts || 0) < 2500 &&
        ['select', 'input', 'button'].includes(step.type)) {
      const wait = stepWaitCode(step);
      if (wait) step.code = wait + '\n' + step.code;
    }
    steps.push(step);
    // User actions anchor the "step-wise" grouping: readonly/error fields
    // surfaced afterwards are folded under the most recent action.
    if (['select', 'input', 'button', 'swal2', 'navigate', 'start'].includes(step.type)) {
      lastAction = step;
    }
    // Toast feedback for every recorded step
    const toastMsg = (() => {
      switch (step.type) {
        case 'select':   return `▾ ${step.label} → "${step.value}"`;
        case 'input':    return `✎ ${step.label} = "${step.value}"`;
        case 'button':   return `⏎ ${step.label}`;
        case 'swal2':    return `✔ ${step.value}`;
        case 'navigate': return `↗ navigated`;
        case 'start':    return `▶ recording started`;
        case 'error':    return `⚠ ${step.label}: "${step.value}"`;
        case 'readonly': return `● ${step.label} = "${step.value}"`;
        default:         return step.label ? `${step.label}` : null;
      }
    })();
    if (toastMsg) _flashToast(toastMsg, null);
    setBarState(); persist();
    try { chrome.runtime.sendMessage({ type: 'STATE', recording, steps }); } catch (_) {}
    scheduleReadonlyScan();
  }

  // Locator-based wait for the field the next step is about to interact with.
  // Falls back to a fixed pause for steps without a label-based field target.
  function stepWaitCode(step) {
    if (!step.label) return 'page.wait_for_timeout(1500)';
    const lp = step.label.replace(/'/g, "\\'");
    const nth = step.rowIndex != null ? `.nth(${step.rowIndex})` : '';
    if (step.type === 'select') {
      return `page.locator("xpath=//mat-label[contains(.,'${lp}')]/ancestor::mat-form-field//mat-select")${nth}.wait_for(state="visible", timeout=10000)`;
    }
    if (step.type === 'input') {
      return `page.locator("xpath=//mat-label[contains(.,'${lp}')]/ancestor::mat-form-field//input")${nth}.wait_for(state="visible", timeout=10000)`;
    }
    return 'page.wait_for_timeout(1500)';
  }

  function persist() {
    try { chrome.storage.local.set({ erp_steps: steps, erp_recording: recording }); } catch (_) {}
  }

  // ── Readonly-field recording ─────────────────────────────────────────
  // Occurrence index of a form-field among all fields sharing the same label.
  // Grids render the same field once per row (Quality Parameter, Actual Value,
  // Item Name…) — the index becomes the stable row number for `.nth(row_index)`.
  function rowIndexOf(el) {
    const ff = el && el.closest ? el.closest('mat-form-field') : null;
    if (!ff || !ff.querySelector) return null;
    const lbl = ff.querySelector('mat-label')?.textContent.trim();
    if (!lbl) return null;
    const all = [...document.querySelectorAll('mat-form-field')].filter(f =>
      f.querySelector('mat-label')?.textContent.trim() === lbl
    );
    return all.length < 2 ? null : all.indexOf(ff);
  }

  function readonlyAssertCode(ro) {
    const lp = ro.label.replace(/'/g, "\\'");
    const vq = ro.value.replace(/"/g, '\\"');
    const nth = ro.rowIndex != null ? `.nth(${ro.rowIndex})` : '';
    return ro.isSelect
      ? `# Assert field: ${ro.label} = "${vq}"\nassert page.locator("xpath=//mat-label[contains(.,'${lp}')]/ancestor::mat-form-field//mat-select")${nth}.text_content().strip() == "${vq}"`
      : `# Assert field: ${ro.label} = "${vq}"\nassert page.locator("xpath=//mat-label[contains(.,'${lp}')]/ancestor::mat-form-field//input")${nth}.input_value() == "${vq}"`;
  }

  let _toastTimer = null;
  function _flashToast(msg, value) {
    const t = document.getElementById('__erp_rec_toast');
    if (!t) return;
    clearTimeout(_toastTimer);
    t.textContent = value != null ? `✓ ${msg} = "${value}"` : msg;
    t.classList.remove('fade');
    t.classList.add('show');
    _toastTimer = setTimeout(() => {
      t.classList.add('fade');
      setTimeout(() => { t.classList.remove('show', 'fade'); }, 420);
    }, 2000);
  }

  function recordReadonly(ro, grouped) {
    if (!ro || !ro.label || !ro.value) return;
    const key = `${ro.label}:${ro.rowIndex ?? ''}:${ro.value}`;
    if (recordedReadonly.has(key)) return;
    recordedReadonly.add(key);
    // Toast for view-mode click captures (grouped ones don't go through addStep)
    if (grouped) _flashToast(`✓ ${ro.label}`, ro.value);
    // Auto-patched fields (surfaced by the post-step snapshot, not clicked by
    // the user) fold into the action that triggered them instead of cluttering
    // the step list. Direct clicks stay standalone ("Assert field" steps).
    if (grouped && lastAction &&
        !lastAction.patched.some(p => p.label === ro.label && p.rowIndex === ro.rowIndex && p.value === ro.value)) {
      lastAction.patched.push({
        label: ro.label,
        value: ro.value,
        isSelect: !!ro.isSelect,
        rowIndex: ro.rowIndex ?? null,
      });
      return;
    }
    addStep({ type: 'readonly', label: ro.label, value: ro.value, code: readonlyAssertCode(ro) });
  }

  function scheduleReadonlyScan() {
    clearTimeout(readonlyScanTimer);
    readonlyScanTimer = setTimeout(scanReadonlyFields, 1200);
  }

  // Snapshot every readonly/disabled field that is visible right now.
  // Called after each recorded step so fields that were auto-populated by
  // earlier actions (e.g. a disabled dropdown whose value came from a
  // preceding selection) are captured even if the user never clicked them.
  // Skipped in view mode — only explicit clicks or Cap All should capture there.
  function scanReadonlyFields() {
    if (!recording || readonlyScanning || viewMode) return;
    readonlyScanning = true;
    try {
      const ffs = document.querySelectorAll(
        'mat-form-field.readonly-field, mat-form-field.mat-form-field-disabled, mat-form-field[aria-readonly="true"]'
      );
      for (const ff of ffs) {
        if (!ff.isConnected) continue;
        const ro = getReadonlyField(ff);
        if (ro) recordReadonly(ro, true);
      }
    } finally {
      readonlyScanning = false;
    }
    scanFormErrors();
  }

  // ── Validation-error recording (red-line mat-error) ────────────────
  // Mirrors the form-auditor approach: field-level invalid detection via
  // the `mat-form-field-invalid` / `ng-invalid` classes, error text read
  // from the field's `mat-error`. No visibility gate — if the field is
  // marked invalid and carries error text, that IS what the user sees.
  // Each error also records WHICH field/label (and grid row) showed it,
  // and the assertion is scoped to that field instead of the whole page.
  function fieldContext(field) {
    const label = field.querySelector('mat-label')?.textContent.trim() || null;
    let row = null;
    const tr = field.closest('tr, [role="row"], .mat-mdc-row, .cdk-row');
    if (tr && tr.parentElement) {
      row = [...tr.parentElement.children].indexOf(tr) + 1; // 1-based
    }
    return { label, row };
  }

  function errorStepFor(field) {
    const isInvalid =
      field.classList.contains('mat-form-field-invalid') ||
      field.classList.contains('ng-invalid');
    if (!isInvalid) return null;
    const errEl = field.querySelector('mat-error');
    if (!errEl) return null;
    let msg = (errEl.textContent || '').trim().replace(/\s+/g, ' ');
    if (!msg || msg.length > 200) return null;

    const { label, row } = fieldContext(field);
    const where = label
      ? row ? `"${label}" (row ${row})` : `"${label}"`
      : row ? `row ${row}` : 'unknown field';
    const msgEsc = msg.replace(/'/g, "\\'");
    const labelEsc = label ? label.replace(/'/g, "\\'") : null;

    let code;
    if (label) {
      code = `# Validation error — ${where}: "${msg}"\nassert page.locator("xpath=//mat-label[contains(.,'${labelEsc}')]/ancestor::mat-form-field//mat-error[contains(.,'${msgEsc}')]").first.is_visible()`;
    } else {
      code = `# Validation error — ${where}: "${msg}"\nassert page.locator("xpath=//mat-error[contains(.,'${msgEsc}')]").first.is_visible()`;
    }

    return { type: 'error', label: where, value: msg, code };
  }

  function scanFormErrors() {
    if (!recording) return;
    const ffs = document.querySelectorAll('mat-form-field, .mat-mdc-form-field');
    for (const field of ffs) {
      if (!field.isConnected) continue;
      const step = errorStepFor(field);
      if (!step) continue;
      // Dedup per field+message (grid rows sharing a label each count, so
      // we know exactly which row must be fixed)
      const key = `${step.label}:${step.value}`;
      if (recordedErrors.has(key)) continue;
      recordedErrors.add(key);
      addStep(step);
    }
  }

  // Fire on class toggles too (mat-form-field-invalid, ng-invalid…), not
  // just DOM insertion — validation state can change without the mat-error
  // being re-inserted. Debounced so Angular finishes mutating first.
  let errorScanTimer = null;
  const errorMO = new MutationObserver(() => {
    if (!recording) return;
    clearTimeout(errorScanTimer);
    errorScanTimer = setTimeout(scanFormErrors, 150);
  });
  errorMO.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['class']
  });

  // ── Helpers ───────────────────────────────────────────────────────────
  function inBar(el) { return bar.contains(el); }

  function matLabel(el) {
    const ff = el.closest('mat-form-field');
    if (!ff) return null;
    return ff.querySelector('mat-label')?.textContent.trim() || null;
  }

  function dialogTitle() {
    return document.querySelector(
      'mat-dialog-container [mat-dialog-title], mat-dialog-container mat-dialog-title, mat-dialog-container h2'
    )?.textContent.trim() || 'Dialog';
  }

  /**
   * Check if a mat-form-field contains a readonly or disabled element.
   * Returns { label, value, isSelect } or null.
   *
   * The ERP marks readonly fields with:
   *  - `mat-form-field-disabled` class on the mat-form-field
   *  - `readonly`/`disabled` attributes on the input/select
   *  - `mat-mdc-select-disabled` / `mat-select-disabled` on mat-select
   *  - `aria-disabled="true"` on the select or input
   */
  function getReadonlyField(ff) {
    if (!ff || typeof ff.getAttribute !== 'function') return null;

    const ffClasses = ff.getAttribute('class') || '';
    const isFieldDisabled =
      ffClasses.includes('mat-form-field-disabled') ||
      ffClasses.includes('readonly') ||
      ff.getAttribute('aria-readonly') === 'true';

    // Readonly / disabled mat-select (dropdown that cannot be opened)
    const matSel = ff.querySelector('mat-select');
    if (matSel) {
      const selCls = matSel.getAttribute('class') || '';
      const isSelDisabled =
        selCls.includes('mat-mdc-select-disabled') ||
        selCls.includes('mat-select-disabled') ||
        matSel.hasAttribute('disabled') ||
        matSel.getAttribute('aria-disabled') === 'true' ||
        ((selCls.includes('mat-mdc-select') || selCls.includes('mat-select')) && isFieldDisabled);
      if (isSelDisabled) {
        const lbl = ff.querySelector('mat-label')?.textContent.trim();
        const selVal = _readMatSelectText(ff, matSel);
        if (lbl && selVal) {
          return { label: lbl, value: selVal, isSelect: true, rowIndex: rowIndexOf(ff) };
        }
      }
    }

    // Visible readonly / disabled input
    const inp = ff.querySelector(
      'input[readonly], input[disabled], textarea[readonly], textarea[disabled], ' +
      'input[aria-readonly="true"], input[aria-disabled="true"]'
    );
    if (inp) {
      const lbl = ff.querySelector('mat-label')?.textContent.trim();
      const val = _readInputValue(inp);
      if (lbl && val) {
        return { label: lbl, value: val, isSelect: false, rowIndex: rowIndexOf(ff) };
      }
    }

    // Disabled native select
    const nativeSel = ff.querySelector('select[readonly], select[disabled], select[aria-disabled="true"]');
    if (nativeSel) {
      const lbl = ff.querySelector('mat-label')?.textContent.trim();
      const selVal = nativeSel.selectedOptions?.[0]?.textContent?.trim() || nativeSel.value;
      if (lbl && selVal) {
        return { label: lbl, value: selVal, isSelect: true, rowIndex: rowIndexOf(ff) };
      }
    }

    // mat-form-field disabled class + any element with a value
    if (isFieldDisabled) {
      const lbl = ff.querySelector('mat-label')?.textContent.trim();
      const ms = ff.querySelector('mat-select');
      const selVal = ms ? _readMatSelectText(ff, ms) : null;
      const visInp = ff.querySelector('input:not([type="hidden"]), textarea');
      const val = selVal || (visInp ? _readInputValue(visInp) : '') || '';
      if (lbl && val) {
        return { label: lbl, value: val, isSelect: !!selVal };
      }
    }

    return null;
  }

  // ── View-mode helpers ─────────────────────────────────────────────

  // Read the current value of ANY mat-form-field regardless of disabled state.
  // Used in view mode where fields look readonly but lack Angular disabled markers.
  function getAnyFieldValue(ff) {
    if (!ff || typeof ff.querySelector !== 'function') return null;
    const lbl = ff.querySelector('mat-label')?.textContent.trim();
    if (!lbl) return null;

    const matSel = ff.querySelector('mat-select');
    if (matSel) {
      const selVal = _readMatSelectText(ff, matSel);
      if (selVal) return { label: lbl, value: selVal, isSelect: true, rowIndex: rowIndexOf(ff) };
      return null;
    }

    const inp = ff.querySelector('input:not([type="hidden"]), textarea');
    if (inp) {
      const val = _readInputValue(inp);
      if (val) return { label: lbl, value: val, isSelect: false, rowIndex: rowIndexOf(ff) };
    }

    return null;
  }

  // Read the current value from any input/textarea, handling Angular quirks:
  //  - type="number" disabled inputs: Angular's NumberValueAccessor can leave
  //    inp.value="" even though the field shows a number; try valueAsNumber and
  //    the native prototype getter as fallbacks.
  //  - defaultValue covers the HTML `value` attribute (used by some bindings).
  function _readInputValue(inp) {
    if (!inp) return '';

    // 1. Standard value property
    let v = (inp.value || '').trim();
    if (v) return v;

    // 2. type=number: valueAsNumber holds the numeric value even when .value
    //    returns '' (e.g. Angular sets inp.value but browser sanitises it away
    //    for very large integers represented as exponential notation).
    if (inp.type === 'number') {
      const n = inp.valueAsNumber;
      if (!isNaN(n) && isFinite(n)) return String(n);
    }

    // 3. defaultValue reflects the HTML `value` attribute
    v = (inp.defaultValue || '').trim();
    if (v) return v;

    // 4. Native prototype getter — bypasses any Angular property-descriptor
    //    shim that may shadow the real underlying DOM value string.
    try {
      const proto = Object.getOwnPropertyDescriptor(
        inp.tagName === 'TEXTAREA'
          ? HTMLTextAreaElement.prototype
          : HTMLInputElement.prototype,
        'value'
      );
      if (proto?.get) {
        v = (proto.get.call(inp) || '').trim();
        if (v) return v;
      }
    } catch (_) {}

    // 5. Angular Ivy __ngContext__: for disabled/readonly number inputs
    //    (e.g. Total PO Amount) Angular stores the value only in the component
    //    instance held in the nearest _nghost ancestor's LView at index [6].
    //    Walk up to the first component host element and probe common value
    //    property names on the component instance.
    try {
      let node = inp.parentElement;
      while (node && node !== document.body) {
        const attrs = node.getAttributeNames ? node.getAttributeNames() : [];
        if (attrs.some(a => a.startsWith('_nghost-'))) {
          const lv = node.__ngContext__;
          if (Array.isArray(lv)) {
            // LView[6] = component instance ("this" of the component class)
            const comp = lv[6];
            if (comp && typeof comp === 'object') {
              for (const k of ['value', '_value', 'model', 'numericValue', 'fieldValue']) {
                const cv = comp[k];
                if (cv != null && cv !== '' &&
                    typeof cv !== 'object' && typeof cv !== 'function') {
                  return String(cv);
                }
              }
            }
          }
          break; // only try the immediate component host
        }
        node = node.parentElement;
      }
    } catch (_) {}

    return '';
  }

  // Extract the displayed text from a mat-select, trying all known DOM slots
  // across Material v14/v15/v16 and handling nested span structures.
  // Returns null for placeholder text (starts with "Select ") — those are not values.
  function _readMatSelectText(ff, matSel) {
    const isPlaceholder = t => !t || /^select\s/i.test(t);

    // 1. Custom trigger template: ERP View forms often bind display text here
    //    instead of via the Angular form value (so standard value slots are empty).
    const trigger = matSel.querySelector('mat-select-trigger');
    if (trigger) {
      const t = (trigger.innerText || trigger.textContent || '').replace(/\s+/g, ' ').trim();
      if (t && !isPlaceholder(t)) return t;
    }

    // 2. Standard Angular Material value slots (set when form value is bound)
    const SLOTS = [
      '.mat-mdc-select-min-line',
      '.mat-select-min-line',
      '.mat-mdc-select-value-text',
      '.mat-select-value-text',
    ];
    for (const sel of SLOTS) {
      const el = ff.querySelector(sel);
      if (!el) continue;
      // Walk to the deepest single child to avoid reading parent+child duplicated text
      let node = el;
      while (node.children.length === 1) node = node.children[0];
      const t = (node.textContent || '').trim();
      if (t && !isPlaceholder(t)) return t;
    }

    // 3. aria-valuetext fallback (set by Angular when value is selected)
    const aria = (matSel.getAttribute('aria-valuetext') || '').trim();
    if (aria && !isPlaceholder(aria)) return aria;
    return null;
  }

  function enterViewMode() {
    viewMode = true;
    recordedReadonly.clear();
    pendingViewCaptures.clear();
    setBarState();
  }

  function exitViewMode() {
    if (!viewMode) return;
    // Last-chance retry: fields the user clicked but Angular hadn't bound yet.
    // The close button fires before Angular tears down the DOM, so fields are
    // still live and __ngContext__[6].value is now populated.
    for (const ff of pendingViewCaptures) {
      if (ff.isConnected) {
        const ro = getReadonlyField(ff) || getAnyFieldValue(ff);
        if (ro) recordReadonly(ro, true);
      }
    }
    pendingViewCaptures.clear();
    viewMode = false;
    setBarState();
  }

  // Capture All: scan every mat-form-field on the page and record each value.
  // Grouped under lastAction (the "View" step) via recordReadonly(ro, true).
  function captureAllViewFields() {
    const ffs = document.querySelectorAll('mat-form-field');
    let captured = 0;
    for (const ff of ffs) {
      if (!ff.isConnected) continue;
      // Try readonly first (more specific), then fall back to any-value reader
      const ro = getReadonlyField(ff) || getAnyFieldValue(ff);
      if (ro) { recordReadonly(ro, true); captured++; }
    }
    console.log(`[ERP Recorder] Capture All: ${captured} fields captured`);
  }

  // ── mat-select recording ──────────────────────────────────────────
  // Two independent detection paths:
  //  A) Mouse events on mat-option (mousedown + click, capture phase).
  //     Gives the exact selected text and "is first option" detection.
  //  B) MutationObserver on panel-close: if no option mouse event fired
  //     (Angular removes the option before click), we detect the value
  //     change on the mat-select and record it. This also catches
  //     keyboard-driven selection (arrows + Enter).

  function readSelectText(selEl) {
    const ff = selEl.closest?.('mat-form-field');
    const domText = ff ? (
      ff.querySelector('.mat-mdc-select-value-text, .mat-mdc-select-min-line, .mat-select-min-line, .mat-select-value-text')
        ?.textContent || ''
    ) : '';
    return (domText || selEl.getAttribute?.('aria-valuetext') || '').trim();
  }

  function setPendingSelect(selEl) {
    const ff = selEl.closest?.('mat-form-field');
    const lbl = ff?.querySelector('mat-label')?.textContent.trim()
             || selEl.getAttribute?.('aria-label') || 'unknown';
    let altLabel = null;
    if (lbl === 'Item Category') altLabel = 'PO Item Type';
    else if (lbl === 'PO Item Type') altLabel = 'Item Category';
    pendingSelect = {
      label: lbl,
      altLabel,
      el: selEl,
      prevText: readSelectText(selEl),
    };
  }

  function getOptionText(opt) {
    return (
      opt.querySelector('.mdc-list-item__primary-text, .mat-option-text, .mat-mdc-option-text')
        ?.textContent.trim()
    ) || opt.textContent.trim().replace(/\s+/g, ' ');
  }

  function recordSelect(lbl, _alt, text, isFirst, el) {
    if (!lbl || !text) return;
    // Always emit the exact selected option text so the generated script
    // reflects the value the user actually chose. `_val_select_first` picks
    // whatever is first in the rendered panel, which is unfaithful when the
    // user picked a specific option, typed to filter, or the panel is
    // virtualized — so it is no longer used for real selections.
    const ri = rowIndexOf(el);
    const suffix = ri != null ? `, row_index=${ri}` : '';
    const code = `# label is case-sensitive — matches DOM text exactly\n_val_select_text(page, "${lbl}", "${text.replace(/"/g, '\\"')}"${suffix})`;
    addStep({ type: 'select', label: lbl, value: text, isFirst, code, rowIndex: ri != null ? ri : null });
  }

  // Path A — option clicked/mousedown (capture). Consumes pendingSelect.
  function onOptionEvent(e) {
    const opt = e.target.closest('mat-option, mat-mdc-option');
    if (!opt || opt.classList.contains('dd-clear-option')) return;
    const text = getOptionText(opt);
    if (!pendingSelect || !text) return;

    const lbl = pendingSelect.label;
    const alt = pendingSelect.altLabel;
    const el = pendingSelect.el;
    pendingSelect = null; // consumed — panel-close fallback won't double-record

    if (!recording) return;

    const panel = opt.closest('.mat-mdc-select-panel, .mat-select-panel');
    const allOpts = panel
      ? [...panel.querySelectorAll('mat-option:not(.dd-clear-option), mat-mdc-option:not(.dd-clear-option)')]
      : [];
    const isFirst = allOpts.length > 0 && allOpts[0] === opt;
    recordSelect(lbl, alt, text, isFirst, el);
  }

  // Path B — panel removed: compare mat-select value; record if changed.
  function recordSelectOnPanelClose() {
    if (!pendingSelect) return;
    const cur = readSelectText(pendingSelect.el);
    if (!cur || cur === pendingSelect.prevText) return; // dismissed w/o selection

    const lbl = pendingSelect.label;
    const alt = pendingSelect.altLabel;
    const text = cur;
    const el = pendingSelect.el;
    pendingSelect = null;
    if (!recording) return;
    recordSelect(lbl, alt, text, false, el);
  }

  // ── Document capture listeners ─────────────────────────────────────
  // mousedown + click on mat-option: whichever fires wins (Path A).
  document.addEventListener('mousedown', onOptionEvent, true);
  document.addEventListener('click', onOptionEvent, true);

  // In view mode: find the mat-form-field nearest to a click, even when
  // `pointer-events:none` on disabled fields causes e.target to land on a
  // parent/sibling element rather than the field itself.
  function _ffFromEvent(e) {
    // Direct ancestor first (works when events reach the field)
    const direct = e.target.closest?.('mat-form-field');
    if (direct) return direct;
    // elementFromPoint with pointer-events temporarily forced (skip for view mode
    // where we just want the nearest field in the visual vicinity)
    if (typeof e.clientX === 'number') {
      // Expand search: check all mat-form-fields and find the one whose bounding
      // rect contains the click point (handles pointer-events:none on internals)
      const ffs = document.querySelectorAll('mat-form-field');
      for (const ff of ffs) {
        const r = ff.getBoundingClientRect();
        if (e.clientX >= r.left && e.clientX <= r.right &&
            e.clientY >= r.top  && e.clientY <= r.bottom) {
          return ff;
        }
      }
    }
    return null;
  }

  // mat-select trigger detection (all interaction routes → set pendingSelect)
  document.addEventListener('mousedown', e => {
    if (!recording || inBar(e.target)) return;

    // In view mode: capture clicked fields and flush pending captures on close.
    if (viewMode) {
      // Detect close/cancel in mousedown — fires BEFORE Angular's click handler
      // tears down the view DOM. exitViewMode() retries pendingViewCaptures
      // while all fields are still live and __ngContext__[6].value is populated.
      const btn = e.target.closest('button, [role="button"]');
      if (btn) {
        const lbl = (
          btn.getAttribute('aria-label') || btn.textContent || ''
        ).trim().toLowerCase();
        if (/\b(close|cancel)\b/.test(lbl)) {
          exitViewMode(); // flushes pendingViewCaptures now, before DOM teardown
        }
      }

      const ff = _ffFromEvent(e);
      if (ff) {
        pendingViewCaptures.add(ff);
        const ro = getReadonlyField(ff) || getAnyFieldValue(ff);
        if (ro) recordReadonly(ro, true);
      }
      return; // never open panels in view mode
    }

    // Normal mode below
    const ff = e.target.closest('mat-form-field');
    if (ff) {
      const ro = getReadonlyField(ff);
      if (ro) { recordReadonly(ro); return; }
    }

    const selEl = e.target.closest('mat-select');
    if (selEl) {
      setPendingSelect(selEl);
      return;
    }
  }, true);

  document.addEventListener('click', e => {
    if (!recording || inBar(e.target)) return;

    // Shift+click on a mat-form-field → assert current value
    if (e.shiftKey) {
      const ff = e.target.closest('mat-form-field');
      if (ff) {
        const inp = ff.querySelector('input, textarea');
        const selVal = (
          ff.querySelector('.mat-mdc-select-value-text, .mat-mdc-select-min-line, .mat-select-min-line')
            ?.textContent
        )?.trim();
        const lbl = ff.querySelector('mat-label')?.textContent.trim();
        const val = inp?.value || selVal || '';
        if (lbl && val) {
          e.preventDefault();
          recordReadonly({ label: lbl, value: val, isSelect: !!selVal });
          return;
        }
      }
    }

    const selEl = e.target.closest('mat-select');
    if (selEl) {
      setPendingSelect(selEl);
      return;
    }

    // Button clicks that drive the flow (Add / Submit / Update / Close …)
    recordButtonClick(e);
  }, true);

  // ── Button click recording ───────────────────────────────────────────
  const FLOW_TEXT = /submit|save|update|close|cancel|add|create|approve|confirm|delete|done|ok|back|next/;

  function isFlowButton(btn) {
    if (btn.closest('.swal2-actions')) return false;                     // swal2 click listener owns it
    if (btn.closest('.mat-mdc-select-panel, .mat-select-panel')) return false;
    if (btn.closest('#__erp_rec_bar')) return false;
    const cls = btn.className || '';
    if (cls.includes('erp-add-btn') || cls.includes('add-row-btn')) return true;
    if (cls.includes('apply-button') && btn.querySelector('.fa-minus, i.fa-minus')) return true;
    if (cls.includes('erp-row-trigger')) return true;
    if (btn.querySelector('.erp-menu-title')) return true;
    if (btn.matches('button[mattooltip="Search"], button[matTooltip="Search"]')) return true;
    if (btn.closest('.erp-search-container')) return true;
    if (btn.closest('.popup-footer, .form-footer, mat-dialog-actions, mat-dialog-title')) return true;
    if (btn.hasAttribute('matstepperprevious') || btn.hasAttribute('matsteppernext')) return true;
    if (btn.closest('.cdk-overlay-container')) return false;
    const t = (btn.textContent || '').trim();
    return t.length > 0 && t.length < 60 && FLOW_TEXT.test(t.toLowerCase());
  }

  // Visible label of a button, ignoring decorative icon text (e.g. material "add")
  function btnText(btn) {
    const clone = btn.cloneNode(true);
    clone.querySelectorAll('i').forEach(i => i.remove());
    return (clone.textContent || '').replace(/\s+/g, ' ').trim();
  }

  // Generate a locator for the clicked button, matching test-suite style
  // (see po_playwright_page.py: button.erp-add-btn, .popup-footer XPaths,
  // button.apply-button + .nth() for row removal).
  function buttonCode(btn) {
    const text = (btn.textContent || '').trim().replace(/\s+/g, ' ');
    const cls = btn.className || '';
    if (cls.includes('erp-add-btn')) {
      // Keep the actual button caption so similar "Add …" buttons on other
      // pages/sections are disambiguated (e.g. "Add Quality Control").
      const addText = btnText(btn);
      const safeText = addText.replace(/"/g, '\\"');
      return {
        label: addText || 'Add button',
        code: addText
          ? `page.locator("button.erp-add-btn", has_text="${safeText}").click()`
          : 'page.locator("button.erp-add-btn").click()'
      };
    }
    if (cls.includes('add-row-btn')) {
      return { label: 'Add row', code: 'page.locator("button.add-row-btn").click()' };
    }
    if (cls.includes('apply-button') && btn.querySelector('.fa-minus, i.fa-minus')) {
      // Row removal — index among all remove-row buttons (matches suite's .nth(row_index))
      const idx = [...document.querySelectorAll('button.apply-button .fa-minus, button.apply-button i.fa-minus')]
        .map(i => i.closest('button')).indexOf(btn);
      return { label: 'Remove row', code: `page.locator("button.apply-button").nth(${idx}).click()` };
    }
    if (cls.includes('erp-row-trigger')) {
      // ⋮ row action menu — prefer a ref-no scoped locator (suite's
      // _open_row_action / tr:has-text) so replay targets the same record
      // even if row order/index changes; fall back to .nth(row_index).
      const row = btn.closest('tr');
      const refCell = row && row.querySelector(
        'td.cdk-column-transaction_ref_no, td.mat-column-transaction_ref_no'
      );
      const refNo = refCell ? refCell.textContent.replace(/\s+/g, ' ').trim() : '';
      let code;
      if (refNo && refNo.length >= 2) {
        const safeRef = refNo.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        code = `page.locator("tr:has-text('${safeRef}')").first.locator("button.erp-row-trigger").click(force=True)\npage.wait_for_selector(".mat-mdc-menu-panel", timeout=8000)`;
      } else {
        const idx = [...document.querySelectorAll('button.erp-row-trigger')].indexOf(btn);
        code = `page.locator("button.erp-row-trigger").nth(${idx}).click()\npage.wait_for_selector(".mat-mdc-menu-panel", timeout=8000)`;
      }
      return { label: 'Row menu', code };
    }
    if (btn.querySelector('.erp-menu-title')) {
      // Edit / View / History / … from the action menu (suite: :has(.erp-menu-title:text-is('…')))
      const title = btn.querySelector('.erp-menu-title').textContent.trim().replace(/'/g, "\\'");
      if (title === 'View') {
        // Opening a View form → enter view mode after the form renders
        setTimeout(enterViewMode, 600);
      }
      return {
        label: title,
        code: `page.locator(".mat-mdc-menu-panel button.mat-mdc-menu-item:has(.erp-menu-title:text-is('${title}'))").click()`
      };
    }
    if (btn.matches('button[mattooltip="Search"], button[matTooltip="Search"]')) {
      // Toolbar search toggle — reveals the #erpSearchInput container
      return { label: 'Search', code: 'page.locator("button[mattooltip=\'Search\']").click()' };
    }
    if (btn.closest('.erp-search-container')) {
      // Search submit (attached magnifier in the search box) — filters the listing
      return { label: 'Search', code: 'page.locator("button.search-btn.attached").click()' };
    }
    const footer = btn.closest('.popup-footer, .form-footer, mat-dialog-actions');
    if (footer) {
      if (footer.classList.contains('popup-footer') || footer.classList.contains('form-footer')) {
        const cls2 = footer.classList.contains('popup-footer') ? 'popup-footer' : 'form-footer';
        // Closing/cancelling a popup exits view mode
        if (/close|cancel/i.test(text)) exitViewMode();
        return {
          label: text,
          code: `page.locator("xpath=//div[contains(@class,'${cls2}')]//button[contains(.,'${text}')]").click()`
        };
      }
      return {
        label: text,
        code: `page.locator("xpath=//mat-dialog-actions//button[contains(.,'${text}')]").click()`
      };
    }
    if (btn.closest('mat-dialog-title')) {
      return {
        label: 'Close',
        code: `page.locator("xpath=//mat-dialog-container//button[contains(.,'${text}')]").click()`
      };
    }
    if (btn.hasAttribute('matstepperprevious') || btn.hasAttribute('matsteppernext')) {
      const lbl = (btn.querySelector('.mdc-button__label') || btn).textContent.trim();
      const attr = btn.hasAttribute('matstepperprevious') ? 'matstepperprevious' : 'matsteppernext';
      return {
        label: lbl,
        code: `page.locator("button[${attr}]").click()`
      };
    }
    return { label: text, code: `page.get_by_role("button", name="${text}").click()` };
  }

  function recordButtonClick(e) {
    const btn = e.target.closest('button');
    if (!btn) return;
    if (!isFlowButton(btn)) return;
    const b = buttonCode(btn);
    // Exit view mode on any dismiss gesture: close icon, Cancel, Close buttons
    // regardless of which container they live in (popup-footer already handled
    // above in buttonCode, but full-page views use a standalone close icon that
    // falls to the get_by_role fallback with label "close").
    if (viewMode && /^(close|cancel)$/i.test(b.label)) {
      exitViewMode();
    }
    addStep({ type: 'button', label: b.label, value: b.label, code: b.code });
  }

  // focusin on a field → keyboard users (Tab reaches a readonly/disabled
  // select, or a mat-select trigger to open)
  document.addEventListener('focusin', e => {
    if (!recording) return;
    if (inBar(e.target)) return;
    if (viewMode) {
      const ff = e.target.closest?.('mat-form-field');
      if (ff) {
        const ro = getReadonlyField(ff) || getAnyFieldValue(ff);
        if (ro) { recordReadonly(ro, true); }
      }
      return;
    }
    const ff = e.target.closest?.('mat-form-field');
    if (ff) {
      const ro = getReadonlyField(ff);
      if (ro) { recordReadonly(ro); return; }
    }
    const selEl = e.target.closest('mat-select');
    if (selEl) setPendingSelect(selEl);
  }, true);

  // ── Panel MutationObserver ─────────────────────────────────────────
  // - When a panel with options is ADDED: record whose select it is
  //   (pendingSelect already tracks the last-opened select).
  // - When a panel is REMOVED: if pendingSelect still set and the select
  //   value changed, Path B records the selection.
  const panelMO = new MutationObserver(muts => {
    if (!recording) { pendingSelect = null; return; }
    for (const m of muts) {
      for (const node of m.removedNodes) {
        if (!node || !node.classList) continue;
        if (node.classList.contains('mat-mdc-select-panel') ||
            node.classList.contains('mat-select-panel') ||
            node.querySelector?.('.mat-mdc-select-panel, .mat-select-panel')) {
          // Give Angular a tick to update the select's displayed value
          setTimeout(recordSelectOnPanelClose, 60);
        }
      }
    }
  });
  panelMO.observe(document.body, { childList: true, subtree: true });

  // ── Checkbox recording (mat-checkbox) ────────────────────────────
  document.addEventListener('click', e => {
    if (!recording || inBar(e.target)) return;
    const cb = e.target.closest('mat-checkbox');
    if (!cb) return;
    const lbl = (cb.querySelector('.mdc-label') || cb).textContent.trim();
    if (!lbl) return;
    const safeLbl = lbl.replace(/'/g, "\\'");
    // Determine which occurrence of this label was clicked (for nth() in generated code)
    const allSame = [...document.querySelectorAll('mat-checkbox')]
      .filter(c => (c.querySelector('.mdc-label') || c).textContent.trim() === lbl);
    const nth = allSame.indexOf(cb);
    const nthSuffix = nth > 0 ? `.nth(${nth})` : '';
    // Read state after Angular's change-detection tick: use native input.checked
    // (the most reliable source — mdc-checkbox--selected and mat-mdc-checkbox-checked
    // classes lag behind and can be inverted relative to visual state).
    setTimeout(() => {
      const nativeInp = cb.querySelector('input[type="checkbox"]');
      const checked = nativeInp ? nativeInp.checked : cb.classList.contains('mat-mdc-checkbox-checked');
      addStep({
        type: 'button',
        label: nth > 0 ? `${lbl} [${nth}]` : lbl,
        value: checked ? 'checked' : 'unchecked',
        code: `page.locator("mat-checkbox:has-text('${safeLbl}') .mdc-label")${nthSuffix}.click()`
      });
    }, 50);
  }, true);

  // ── Input recording ───────────────────────────────────────────────
  document.addEventListener('change', e => {
    if (!recording || inBar(e.target)) return;
    if (Date.now() < inputCooldownUntil) return;
    const inp = e.target;
    if (inp.tagName !== 'INPUT' && inp.tagName !== 'TEXTAREA') return;
    if (inp.type === 'checkbox' || inp.type === 'radio') return;

    // Toolbar search box — not a mat-form-field. Keep comments + guarded open
    // so replay works whether or not the toggle click was recorded separately.
    if (inp.id === 'erpSearchInput') {
      const v = inp.value.trim();
      if (!v) return;
      if (lastInputByLabel['Search'] === v) return;
      lastInputByLabel['Search'] = v;
      addStep({
        type: 'search',
        label: 'Search',
        value: v,
        code: `# Search: "${v}"\nif not page.locator("input#erpSearchInput").is_visible():\n    page.locator("button[mattooltip='Search']").click()\npage.locator("input#erpSearchInput").fill("${v.replace(/"/g, '\\"')}")\npage.locator("input#erpSearchInput").press("Enter")`
      });
      return;
    }

    const ff = inp.closest('mat-form-field');
    if (!ff) return;
    const lbl = ff.querySelector('mat-label')?.textContent.trim();
    if (!lbl) return;

    // Readonly/disabled input — record as readonly assertion
    if (inp.readOnly || inp.disabled) {
      const val = (inp.value || '').trim();
      if (val) recordReadonly({ label: lbl, value: val, isSelect: false, rowIndex: rowIndexOf(ff) });
      return;
    }

    // Normal editable input. Dedup key includes the row index so identical
    // values filled into different grid rows (e.g. repeated Actual Value
    // fills) are all recorded, not swallowed by the previous row's value.
    const ri = rowIndexOf(ff);
    const dedupKey = `${lbl}:${ri ?? ''}`;
    if (inp.value === '') return;
    if (lastInputByLabel[dedupKey] === inp.value) return;
    lastInputByLabel[dedupKey] = inp.value;

    const riSuffix = ri != null ? `, row_index=${ri}` : '';
    addStep({
      type: 'input',
      label: lbl,
      value: inp.value,
      code: `# label is case-sensitive — matches DOM text exactly\n_val_fill(page, "${lbl}", "${inp.value.replace(/"/g, '\\"')}"${riSuffix})`,
      rowIndex: ri != null ? ri : null,
    });
  }, true);

  // ── Dialog detection ──────────────────────────────────────────────
  const dialogMO = new MutationObserver(muts => {
    if (!recording) return;
    for (const m of muts) {
      for (const node of m.addedNodes) {
        const tag = node.tagName?.toLowerCase();
        if (tag === 'mat-dialog-container' || node.querySelector?.('mat-dialog-container')) {
          setTimeout(() => {
            const title = dialogTitle();
            addStep({
              type: 'dialog-open',
              label: title,
              code: `# Dialog: "${title}"\npage.wait_for_selector("mat-dialog-container", timeout=10000)`
            });
          }, 150);
        }
      }
      for (const node of m.removedNodes) {
        const tag = node.tagName?.toLowerCase();
        if (tag === 'mat-dialog-container' || node.querySelector?.('mat-dialog-container')) {
          suppressInputsFor(600);
          exitViewMode(); // closing any dialog exits view mode
          addStep({
            type: 'dialog-close',
            label: 'Dialog closed',
            code: `page.wait_for_selector("mat-dialog-container", state="hidden", timeout=10000)`
          });
        }
      }
    }
  });
  dialogMO.observe(document.body, { childList: true, subtree: false });

  // ── swal2 detection ───────────────────────────────────────────────
  // Track the title of the most recently shown swal2 dialog so the click
  // handler below can reference it when recording the button press.
  let _lastSwalTitle = 'Alert';
  const swalMO = new MutationObserver(muts => {
    for (const m of muts) {
      for (const node of m.addedNodes) {
        if (node.classList?.contains('swal2-container') ||
            node.querySelector?.('.swal2-container')) {
          setTimeout(() => {
            _lastSwalTitle = (node.querySelector?.('.swal2-title') ||
              document.querySelector('.swal2-title'))?.textContent.trim() || 'Alert';
          }, 100);
        }
      }
    }
  });
  swalMO.observe(document.body, { childList: true, subtree: false });

  // Record whichever swal2 button the user actually clicks
  document.addEventListener('click', e => {
    if (!recording) return;
    const btn = e.target.closest('.swal2-confirm, .swal2-cancel, .swal2-deny');
    if (!btn) return;
    const btnText = btn.textContent.trim() || btn.getAttribute('aria-label') || '?';
    const sel = btn.classList.contains('swal2-cancel') ? '.swal2-cancel'
               : btn.classList.contains('swal2-deny')  ? '.swal2-deny'
               :                                          '.swal2-confirm';
    addStep({
      type: 'swal2',
      label: _lastSwalTitle,
      value: btnText,
      code: `# swal2: "${_lastSwalTitle}" → "${btnText}"\npage.wait_for_selector(".swal2-container", timeout=10000)\npage.locator("${sel}").click()\npage.wait_for_selector(".swal2-container", state="hidden", timeout=15000)`
    });
  }, true);

  // ── History dialog row-count capture ─────────────────────────────
  // When a .cdk-overlay-pane opens containing table#excel-table (history popup),
  // read the current row count and emit an assertion step.
  const historyPaneMO = new MutationObserver(muts => {
    if (!recording) return;
    for (const m of muts) {
      for (const node of m.addedNodes) {
        if (node.nodeType !== 1) continue;
        if (!node.classList?.contains('cdk-overlay-pane')) continue;
        setTimeout(() => {
          const empty = node.querySelector('.empty-state');
          const rows  = node.querySelectorAll('table#excel-table tbody tr');
          if (!empty && rows.length === 0) return; // not a history/list dialog
          const count = rows.length;
          const code = empty
            ? `# history: empty\nassert page.locator(".empty-state").is_visible()`
            : `# history: ${count} row(s)\nassert page.locator("table#excel-table tbody tr").count() == ${count}`;
          addStep({
            type: 'readonly',
            label: 'History rows',
            value: empty ? '0 (empty)' : String(count),
            code
          });
        }, 600);
      }
    }
  });
  historyPaneMO.observe(document.body, { childList: true, subtree: true });

  // ── tracking-card detection ───────────────────────────────────────
  const trackMO = new MutationObserver(muts => {
    if (!recording) return;
    for (const m of muts) {
      for (const node of m.addedNodes) {
        if (node.classList?.contains('tracking-card') || node.querySelector?.('.tracking-card')) {
          addStep({
            type: 'tracking',
            label: 'PB tracking card',
            code: `# PB tracking card appeared — waiting for it to finish\npage.wait_for_selector(".tracking-card", state="hidden", timeout=60000)`
          });
        }
      }
    }
  });
  trackMO.observe(document.body, { childList: true, subtree: true });

  // ── URL change ────────────────────────────────────────────────────
  function onUrlChange() {
    const prev = lastUrl;
    lastUrl = location.href;      // always stay in sync (start/first nav included)
    if (!recording) return;
    if (location.href === prev) return;
    suppressInputsFor(800);
    pendingSelect = null;
    exitViewMode(); // navigating away always exits view mode
    recordedErrors.clear();
    recordedReadonly.clear(); // new page → readonly values must be re-asserted
    addStep({
      type: 'navigate',
      label: location.href,
      value: location.href,
      code: `# Route changed: ${location.href}\npage.goto("${location.href}")\npage.wait_for_selector("table.mat-mdc-table, .page-content, mat-form-field", timeout=20000)`
    });
  }
  window.addEventListener('hashchange', onUrlChange);
  window.addEventListener('popstate',   onUrlChange);
  try {
    const _origPush    = history.pushState.bind(history);
    const _origReplace = history.replaceState.bind(history);
    history.pushState    = function (...a) { _origPush(...a);    setTimeout(onUrlChange, 0); };
    history.replaceState = function (...a) { _origReplace(...a); setTimeout(onUrlChange, 0); };
  } catch (_) { /* Zone.js may have made these non-writable - the poller below still catches roaming */ }

  // Safety net: some SPA navigations (Zone.js rewrites of history, hash
  // mutations that don't emit hashchange…) never reach the listeners above.
  // Poll the URL during recording so roaming to another page is always kept.
  if (!window.__erp_rec_url_poller) {
    window.__erp_rec_url_poller = setInterval(() => {
      if (location.href !== lastUrl) onUrlChange();
    }, 500);
  }

  // ── Message handler ───────────────────────────────────────────────
  chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
    if (msg.type === 'GET_STATE') {
      reply({ steps, recording });
    } else if (msg.type === 'CLEAR') {
      clearAll(); reply({ ok: true });
    } else if (msg.type === 'TOGGLE_REC') {
      toggleRec(); reply({ steps, recording });
    } else if (msg.type === 'RESTART') {
      steps = []; pendingSelect = null;
      recordedErrors.clear();
      recordedReadonly.clear();
      recording = true;
      setBarState(); persist();
      reply({ steps, recording });
    }
    return true;
  });

  // Restore from storage on page load
  try {
    chrome.storage.local.get(['erp_steps', 'erp_recording'], data => {
      if (data.erp_steps?.length) steps = data.erp_steps;
      if (data.erp_recording) recording = true;
      setBarState();
    });
  } catch (_) { setBarState(); }

  setBarState();
})();
} // end guard