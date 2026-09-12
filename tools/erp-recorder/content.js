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
      <span id="__erp_rec_cnt">0 steps</span>
      <button class="__erp_icon_btn" id="__erp_rec_view" title="Open full view">↗</button>
      <button class="__erp_icon_btn" id="__erp_rec_min" title="Minimize">—</button>
    </div>
    <div id="__erp_rec_mini" title="Expand recorder">
      <span id="__erp_rec_dot2">●</span>
    </div>
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
  document.getElementById('__erp_rec_mini').addEventListener('click', () => {
    bar.classList.remove('mini');
  });

  function setBarState() {
    const dot  = document.getElementById('__erp_rec_dot');
    const dot2 = document.getElementById('__erp_rec_dot2');
    const lbl  = document.getElementById('__erp_rec_lbl');
    const btn  = document.getElementById('__erp_rec_btn');
    const cnt  = document.getElementById('__erp_rec_cnt');
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
  }

  function toggleRec() {
    recording = !recording;
    setBarState(); persist();
    try { chrome.runtime.sendMessage({ type: 'STATE', recording, steps }); } catch (_) {}
  }

  function clearAll() {
    steps = []; pendingSelect = null;
    recordedReadonly.clear();
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
    steps.push(step);
    setBarState(); persist();
    try { chrome.runtime.sendMessage({ type: 'STATE', recording, steps }); } catch (_) {}
    scheduleReadonlyScan();
  }

  function persist() {
    try { chrome.storage.local.set({ erp_steps: steps, erp_recording: recording }); } catch (_) {}
  }

  // ── Readonly-field recording ─────────────────────────────────────────
  function readonlyAssertCode(ro) {
    const lp = ro.label.replace(/'/g, "\\'");
    const vq = ro.value.replace(/"/g, '\\"');
    return ro.isSelect
      ? `# Assert field: ${ro.label} = "${vq}"\nassert page.locator("xpath=//mat-label[contains(.,'${lp}')]/ancestor::mat-form-field//mat-select").text_content().strip() == "${vq}"`
      : `# Assert field: ${ro.label} = "${vq}"\nassert page.locator("xpath=//mat-label[contains(.,'${lp}')]/ancestor::mat-form-field//input").input_value() == "${vq}"`;
  }

  function recordReadonly(ro) {
    if (!ro || !ro.label || !ro.value) return;
    const key = `${ro.label}:${ro.value}`;
    if (recordedReadonly.has(key)) return;
    recordedReadonly.add(key);
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
  function scanReadonlyFields() {
    if (!recording || readonlyScanning) return;
    readonlyScanning = true;
    try {
      const ffs = document.querySelectorAll(
        'mat-form-field.readonly-field, mat-form-field.mat-form-field-disabled, mat-form-field[aria-readonly="true"]'
      );
      for (const ff of ffs) {
        if (!ff.isConnected) continue;
        const ro = getReadonlyField(ff);
        if (ro) recordReadonly(ro);
      }
    } finally {
      readonlyScanning = false;
    }
  }

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
        const selVal = (
          ff.querySelector('.mat-mdc-select-value-text, .mat-mdc-select-min-line, .mat-select-min-line')
            ?.textContent || matSel.getAttribute('aria-valuetext') || ''
        ).trim();
        if (lbl && selVal) {
          return { label: lbl, value: selVal, isSelect: true };
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
      const val = (inp.value || inp.getAttribute('value') || '').trim();
      if (lbl && val) {
        return { label: lbl, value: val, isSelect: false };
      }
    }

    // Disabled native select
    const nativeSel = ff.querySelector('select[readonly], select[disabled], select[aria-disabled="true"]');
    if (nativeSel) {
      const lbl = ff.querySelector('mat-label')?.textContent.trim();
      const selVal = nativeSel.selectedOptions?.[0]?.textContent?.trim() || nativeSel.value;
      if (lbl && selVal) {
        return { label: lbl, value: selVal, isSelect: true };
      }
    }

    // mat-form-field disabled class + any element with a value
    if (isFieldDisabled) {
      const lbl = ff.querySelector('mat-label')?.textContent.trim();
      const selVal = (
        ff.querySelector('.mat-mdc-select-value-text, .mat-mdc-select-min-line, .mat-select-min-line')
          ?.textContent
      )?.trim();
      const visInp = ff.querySelector('input:not([type="hidden"]), textarea');
      const val = selVal || visInp?.value || '';
      if (lbl && val) {
        return { label: lbl, value: val, isSelect: !!selVal };
      }
    }

    return null;
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

  function recordSelect(lbl, alt, text, isFirst) {
    if (!lbl || !text) return;
    let code;
    if (isFirst) {
      code = alt
        ? `_val_select_first(page, "${lbl}", alt_label="${alt}")`
        : `_val_select_first(page, "${lbl}")`;
    } else {
      code = `_val_select_text(page, "${lbl}", "${text.replace(/"/g, '\\"')}")`;
    }
    addStep({ type: 'select', label: lbl, value: text, isFirst, code });
  }

  // Path A — option clicked/mousedown (capture). Consumes pendingSelect.
  function onOptionEvent(e) {
    const opt = e.target.closest('mat-option, mat-mdc-option');
    if (!opt || opt.classList.contains('dd-clear-option')) return;
    const text = getOptionText(opt);
    if (!pendingSelect || !text) return;

    const lbl = pendingSelect.label;
    const alt = pendingSelect.altLabel;
    pendingSelect = null; // consumed — panel-close fallback won't double-record

    if (!recording) return;

    const panel = opt.closest('.mat-mdc-select-panel, .mat-select-panel');
    const allOpts = panel
      ? [...panel.querySelectorAll('mat-option:not(.dd-clear-option), mat-mdc-option:not(.dd-clear-option)')]
      : [];
    const isFirst = allOpts.length > 0 && allOpts[0] === opt;
    recordSelect(lbl, alt, text, isFirst);
  }

  // Path B — panel removed: compare mat-select value; record if changed.
  function recordSelectOnPanelClose() {
    if (!pendingSelect) return;
    const cur = readSelectText(pendingSelect.el);
    if (!cur || cur === pendingSelect.prevText) return; // dismissed w/o selection

    const lbl = pendingSelect.label;
    const alt = pendingSelect.altLabel;
    const text = cur;
    pendingSelect = null;
    if (!recording) return;
    recordSelect(lbl, alt, text, false);
  }

  // ── Document capture listeners ─────────────────────────────────────
  // mousedown + click on mat-option: whichever fires wins (Path A).
  document.addEventListener('mousedown', onOptionEvent, true);
  document.addEventListener('click', onOptionEvent, true);

  // mat-select trigger detection (all interaction routes → set pendingSelect)
  document.addEventListener('mousedown', e => {
    if (!recording || inBar(e.target)) return;

    // Readonly field detection first (so a disabled dropdown is recorded
    // as readonly instead of opening a panel)
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
  const FLOW_TEXT = /submit|save|update|close|cancel|add|create|approve|confirm|delete|done|ok/;

  function isFlowButton(btn) {
    if (btn.classList.contains('swal2-confirm')) return false;           // swal2 detector owns it
    if (btn.closest('.mat-mdc-select-panel, .mat-select-panel')) return false;
    if (btn.closest('#__erp_rec_bar')) return false;
    const cls = btn.className || '';
    if (cls.includes('erp-add-btn') || cls.includes('add-row-btn')) return true; // ERP flow buttons
    if (btn.closest('.popup-footer, .form-footer, mat-dialog-actions, mat-dialog-title')) return true;
    if (btn.closest('.cdk-overlay-container')) return false;             // stray overlay controls
    const t = (btn.textContent || '').trim();
    return t.length > 0 && t.length < 60 && FLOW_TEXT.test(t.toLowerCase());
  }

  // Generate a locator for the clicked button, matching test-suite style
  // (see po_playwright_page.py: button.erp-add-btn, .popup-footer XPaths…).
  function buttonCode(btn) {
    const text = (btn.textContent || '').trim().replace(/\s+/g, ' ');
    const cls = btn.className || '';
    if (cls.includes('erp-add-btn')) {
      return { label: 'Add button', code: 'page.locator("button.erp-add-btn").click()' };
    }
    if (cls.includes('add-row-btn')) {
      return { label: 'Add row', code: 'page.locator("button.add-row-btn").click()' };
    }
    const footer = btn.closest('.popup-footer, .form-footer, mat-dialog-actions');
    if (footer) {
      if (footer.classList.contains('popup-footer') || footer.classList.contains('form-footer')) {
        const cls2 = footer.classList.contains('popup-footer') ? 'popup-footer' : 'form-footer';
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
    return { label: text, code: `page.get_by_role("button", name="${text}").click()` };
  }

  function recordButtonClick(e) {
    const btn = e.target.closest('button');
    if (!btn) return;
    if (!isFlowButton(btn)) return;
    const b = buttonCode(btn);
    addStep({ type: 'button', label: b.label, value: b.label, code: b.code });
  }

  // focusin on a field → keyboard users (Tab reaches a readonly/disabled
  // select, or a mat-select trigger to open)
  document.addEventListener('focusin', e => {
    if (!recording) return;
    if (inBar(e.target)) return;
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

  // ── Input recording ───────────────────────────────────────────────
  document.addEventListener('change', e => {
    if (!recording || inBar(e.target)) return;
    if (Date.now() < inputCooldownUntil) return;
    const inp = e.target;
    if (inp.tagName !== 'INPUT' && inp.tagName !== 'TEXTAREA') return;
    if (inp.type === 'checkbox' || inp.type === 'radio') return;

    const ff = inp.closest('mat-form-field');
    if (!ff) return;
    const lbl = ff.querySelector('mat-label')?.textContent.trim();
    if (!lbl) return;

    // Readonly/disabled input — record as readonly assertion
    if (inp.readOnly || inp.disabled) {
      const val = (inp.value || '').trim();
      if (val) recordReadonly({ label: lbl, value: val, isSelect: false });
      return;
    }

    // Normal editable input
    if (inp.value === '') return;
    if (lastInputByLabel[lbl] === inp.value) return;
    lastInputByLabel[lbl] = inp.value;

    addStep({
      type: 'input',
      label: lbl,
      value: inp.value,
      code: `_val_fill(page, "${lbl}", "${inp.value.replace(/"/g, '\\"')}")`
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
  const swalMO = new MutationObserver(muts => {
    if (!recording) return;
    for (const m of muts) {
      for (const node of m.addedNodes) {
        if (node.classList?.contains('swal2-container') ||
            node.querySelector?.('.swal2-container')) {
          setTimeout(() => {
            const title = (node.querySelector?.('.swal2-title') || document.querySelector('.swal2-title'))
              ?.textContent.trim() || 'Alert';
            addStep({
              type: 'swal2',
              label: title,
              code: `# swal2: "${title}"\npage.wait_for_selector(".swal2-container", timeout=10000)\npage.locator(".swal2-confirm").click()\npage.wait_for_selector(".swal2-container", state="hidden", timeout=15000)`
            });
          }, 200);
        }
      }
    }
  });
  swalMO.observe(document.body, { childList: true, subtree: false });

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
    if (!recording) return;
    if (location.href === lastUrl) return;
    lastUrl = location.href;
    suppressInputsFor(800);
    pendingSelect = null;
    recordedReadonly.clear(); // new page → readonly values must be re-asserted
    addStep({
      type: 'navigate',
      label: location.pathname,
      code: `page.goto("${location.href}")\npage.wait_for_selector("table.mat-mdc-table, .page-content, mat-form-field", timeout=20000)`
    });
  }
  window.addEventListener('hashchange', onUrlChange);
  window.addEventListener('popstate',   onUrlChange);
  try {
    const _origPush    = history.pushState.bind(history);
    const _origReplace = history.replaceState.bind(history);
    history.pushState    = function (...a) { _origPush(...a);    setTimeout(onUrlChange, 0); };
    history.replaceState = function (...a) { _origReplace(...a); setTimeout(onUrlChange, 0); };
  } catch (_) { /* Zone.js may have made these non-writable — hashchange covers hash routing */ }

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