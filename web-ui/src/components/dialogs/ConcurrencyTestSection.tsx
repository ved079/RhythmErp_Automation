'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { AlertTriangle, Play, Loader2, Key, X, CheckCircle2, XCircle, Info, ChevronDown, ChevronUp } from 'lucide-react'
import { startPbConcurrencyTest, type SSEEvent } from '@/lib/api'
import { useErpToken } from '@/hooks/useErpToken'

interface Props {
  erpToken: string
  erpTenantId: string
  onNeedsToken: () => void
  onClearToken: () => void
}

const KNOWN_TENANTS = [
  { id: '795', name: 'Jalpan Builders' },
  { id: '666', name: 'Jay Kisan Ltd' },
  { id: '686', name: 'Agristack Co.' },
  { id: '751', name: 'Tech Neo' },
  { id: '895', name: 'Janardhan FPC' },
]

const ACCOUNTING_STEPS = [
  { key: 'INPUT_VALIDATION',                 label: 'Validation',      short: 'VAL' },
  { key: 'FISCAL_YEAR_CHECK',                label: 'Fiscal Year',     short: 'FY'  },
  { key: 'INVENTORY_RESERVATION',            label: 'Inventory',       short: 'INV' },
  { key: 'PURCHASE_BOOKING_ACCOUNTING_POST', label: 'PB Ledger',       short: 'PB'  },
  { key: 'INVENTORY_ACCOUNTING_POST',        label: 'Inv. Ledger',     short: 'IL'  },
  { key: 'COMPLETED',                        label: 'Complete',        short: 'OK'  },
]

type PbStatus = 'idle' | 'waiting' | 'created' | 'rejected' | 'error'

interface PbState {
  status: PbStatus
  pbId?: string
  pbRef?: string
  completedSteps: Set<string>
  failedStep?: string
  failedMsg?: string
}

function parsePbIndex(text: string): number {
  const m = text.match(/PB \[(\d+)\]/)
  return m ? parseInt(m[1]) - 1 : -1
}

function parseCreated(text: string) {
  const m = text.match(/id=(\S+)\s+ref=(\S+)/)
  return m ? { id: m[1], ref: m[2] } : {}
}

function parseStep(text: string) {
  // Matches [STEP_KEY_WITH_UNDERSCORES] STATUS: optional message
  const m = text.match(/\[([A-Z_]{4,})\] ([A-Z]+)(?:: (.+))?$/)
  return m ? { step: m[1], evStatus: m[2], msg: m[3] } : {}
}

function gridClass(n: number) {
  if (n <= 3) return `grid-cols-${n}`
  if (n === 4) return 'grid-cols-2'
  if (n <= 6)  return 'grid-cols-3'
  return 'grid-cols-4'
}

// ── Step dot component ─────────────────────────────────────────────────────────
function StepNode({
  done, failed, active, isLast,
}: { done: boolean; failed: boolean; active: boolean; isLast: boolean }) {
  return (
    <div className="flex flex-col items-center" style={{ width: 18 }}>
      <div className={`
        relative size-[18px] rounded-full border-2 flex items-center justify-center shrink-0
        transition-all duration-400
        ${done   ? 'bg-emerald-500 border-emerald-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]' :
          failed ? 'bg-red-500 border-red-500' :
          active ? 'border-[#6366F1] bg-[#6366F1]/10' :
                   'border-gray-600 bg-transparent'}
      `}>
        {done   && <svg viewBox="0 0 12 12" fill="none" className="size-2.5"><path d="M2 6l3 3 5-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>}
        {failed && <svg viewBox="0 0 12 12" fill="none" className="size-2.5"><path d="M2 2l8 8M10 2l-8 8" stroke="white" strokeWidth="2" strokeLinecap="round"/></svg>}
        {active && !done && !failed && (
          <span className="absolute inset-0 rounded-full border-2 border-[#6366F1] animate-ping opacity-60" />
        )}
      </div>
      {!isLast && (
        <div
          className="w-px flex-1 mt-0.5 transition-colors duration-500"
          style={{ minHeight: 20, background: done ? '#22C55E' : 'rgb(55,65,81)' }}
        />
      )}
    </div>
  )
}

// ── Per-PB panel ───────────────────────────────────────────────────────────────
function PbPanel({ idx, state, running }: { idx: number; state: PbState; running: boolean }) {
  const firstPendingIdx = ACCOUNTING_STEPS.findIndex(s =>
    !state.completedSteps.has(s.key) && state.failedStep !== s.key
  )

  const borderColor =
    state.status === 'created'  ? 'border-emerald-500/40' :
    state.status === 'rejected' ? 'border-amber-500/40' :
    state.status === 'error'    ? 'border-red-500/40' :
    running                     ? 'border-[#6366F1]/30' :
                                  'border-gray-700/60'

  const headerBg =
    state.status === 'created'  ? 'bg-emerald-500/8' :
    state.status === 'rejected' ? 'bg-amber-500/8' :
    state.status === 'error'    ? 'bg-red-500/8' :
    running                     ? 'bg-[#6366F1]/5' :
                                  'bg-gray-800/40'

  return (
    <div className={`flex flex-col rounded-xl border ${borderColor} bg-gray-900/80 overflow-hidden transition-colors duration-300`}>

      {/* Header */}
      <div className={`${headerBg} px-4 py-2.5 flex items-center justify-between border-b border-white/5`}>
        <div className="flex items-center gap-2">
          {state.status === 'created'  && <CheckCircle2 className="size-3.5 text-emerald-400 shrink-0" />}
          {(state.status === 'rejected' || state.status === 'error') && <XCircle className="size-3.5 text-red-400 shrink-0" />}
          {(state.status === 'waiting' || state.status === 'idle') && running &&
            <Loader2 className="size-3.5 text-[#6366F1] animate-spin shrink-0" />}
          {(state.status === 'waiting' || state.status === 'idle') && !running &&
            <div className="size-3.5 rounded-full border border-gray-600 shrink-0" />}
          <span className="text-[13px] font-bold text-white tracking-tight" style={{ fontFamily: 'var(--font-jb, "JetBrains Mono", monospace)' }}>
            PB {idx + 1}
          </span>
        </div>

        <span className={`
          text-[9px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded
          ${state.status === 'created'  ? 'bg-emerald-500/15 text-emerald-400' :
            state.status === 'rejected' ? 'bg-amber-500/15 text-amber-400' :
            state.status === 'error'    ? 'bg-red-500/15 text-red-400' :
            running                     ? 'bg-[#6366F1]/15 text-[#6366F1]' :
                                          'bg-gray-700/50 text-gray-500'}
        `}>
          {state.status === 'created'  ? 'Created' :
           state.status === 'rejected' ? 'Rejected' :
           state.status === 'error'    ? 'Error' :
           running                     ? 'Firing' : 'Idle'}
        </span>
      </div>

      {/* PB ID */}
      {state.pbId && (
        <div className="px-4 py-2 bg-gray-800/30 border-b border-white/5 flex items-center gap-2">
          <span className="text-[9px] uppercase tracking-widest text-gray-500">id</span>
          <span className="font-mono text-[11px] text-gray-200">{state.pbId}</span>
          {state.pbRef && state.pbRef !== state.pbId && (
            <>
              <span className="text-gray-700">·</span>
              <span className="text-[9px] uppercase tracking-widest text-gray-500">ref</span>
              <span className="font-mono text-[11px] text-gray-200">{state.pbRef}</span>
            </>
          )}
        </div>
      )}

      {/* Step pipeline */}
      <div className="flex-1 px-4 py-3">
        {ACCOUNTING_STEPS.map((s, i) => {
          const done   = state.completedSteps.has(s.key)
          const failed = state.failedStep === s.key
          const active = !done && !failed && running && i === firstPendingIdx
          const isLast = i === ACCOUNTING_STEPS.length - 1

          return (
            <div key={s.key} className="flex items-start gap-3" style={{ minHeight: isLast ? 18 : 38 }}>
              <StepNode done={done} failed={failed} active={active} isLast={isLast} />
              <div className="flex-1 pt-px">
                <span className={`
                  text-[11px] font-medium transition-colors duration-300
                  ${done   ? 'text-emerald-400' :
                    failed ? 'text-red-400' :
                    active ? 'text-[#818CF8]' :
                             'text-gray-600'}
                `}>{s.label}</span>
                {failed && state.failedMsg && (
                  <p className="text-[10px] text-red-400/80 mt-0.5 leading-tight">{state.failedMsg}</p>
                )}
              </div>
              {done && (
                <span className="text-[10px] text-emerald-500/70 pt-px font-mono shrink-0">✓</span>
              )}
              {active && running && (
                <Loader2 className="size-2.5 text-[#6366F1] animate-spin mt-1 shrink-0" />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Chain doc pills ────────────────────────────────────────────────────────────
function ChainDocs({ text }: { text: string }) {
  const docs: { label: string; ref: string }[] = []
  for (const [label, re] of [['PO', /PO=(\S+)/], ['GRN', /GRN=(\S+)/], ['QC', /QC=(\S+)/]] as [string, RegExp][]) {
    const m = text.match(re)
    if (m) docs.push({ label, ref: m[1] })
  }
  if (!docs.length) return null
  return (
    <div className="flex items-center gap-1 flex-wrap">
      {docs.map(({ label, ref }, i) => (
        <React.Fragment key={label}>
          {i > 0 && <span className="text-gray-600 text-[9px]">→</span>}
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-gray-800 text-[10px]">
            <span className="text-gray-500 font-bold uppercase tracking-wide text-[8px]">{label}</span>
            <span className="font-mono text-gray-300">{ref.split('/').pop()}</span>
          </span>
        </React.Fragment>
      ))}
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────
export function ConcurrencyTestSection({ erpToken, erpTenantId, onNeedsToken, onClearToken }: Props) {
  const { token, tenantId, localToken, setLocalToken, localTenantId, setLocalTenantId, handleAuthError } = useErpToken(erpToken, erpTenantId)
  const [parallelCount, setParallelCount] = useState(3)
  const [running, setRunning]   = useState(false)
  const [showTokenInput, setShowTokenInput] = useState(false)
  const [showInfo, setShowInfo] = useState(false)
  const [chainPhase, setChainPhase] = useState<'idle' | 'building' | 'ready'>('idle')
  const [chainDoneText, setChainDoneText] = useState('')
  const [pbStates, setPbStates] = useState<PbState[]>([])
  const [duplicateDetected, setDuplicateDetected] = useState<boolean | null>(null)
  const [createdCount, setCreatedCount] = useState(0)
  const tokenSectionRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (showTokenInput) tokenSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [showTokenInput])

  const handleRun = useCallback(() => {
    if (!token) { setShowTokenInput(true); return }
    const n = parallelCount
    setRunning(true)
    setChainPhase('building')
    setChainDoneText('')
    setDuplicateDetected(null)
    setCreatedCount(0)
    setPbStates(Array.from({ length: n }, () => ({ status: 'waiting' as PbStatus, completedSteps: new Set<string>() })))

    startPbConcurrencyTest(
      token, tenantId || '681', n,
      (event: SSEEvent) => {
        const text = event.message

        if (event.type === 'run_end') {
          setRunning(false)
          setDuplicateDetected((event.created ?? 0) > 1)
          setCreatedCount(event.created ?? 0)
          return
        }

        const pbIdx = parsePbIndex(text)

        if (pbIdx >= 0 && pbIdx < n) {
          setPbStates(prev => prev.map((s, i) => {
            if (i !== pbIdx) return s
            const updated: PbState = { ...s, completedSteps: new Set(s.completedSteps) }

            if (/PB \[\d+\] CREATED/.test(text)) {
              const { id, ref } = parseCreated(text)
              updated.status = 'created'
              updated.pbId = id
              updated.pbRef = ref
            } else if (/PB \[\d+\] REJECTED/.test(text)) {
              updated.status = 'rejected'
            } else if (/PB \[\d+\] ERROR/.test(text)) {
              updated.status = 'error'
            } else {
              const { step, evStatus, msg } = parseStep(text)
              if (step && (evStatus === 'SUCCESS' || evStatus === 'COMPLETED')) {
                updated.completedSteps.add(step)
              } else if (step && evStatus === 'FAILED') {
                updated.failedStep = step
                updated.failedMsg = msg
                updated.status = 'error'
              }
            }
            return updated
          }))
        } else {
          if (text.includes('Step 1 done')) {
            setChainPhase('ready')
            setChainDoneText(text)
          }
        }
      },
      () => setRunning(false),
      (err) => {
        if (!handleAuthError(err)) {
          setChainPhase('idle')
        }
        setRunning(false)
      },
    )
  }, [token, tenantId, parallelCount, handleAuthError])

  const tokenValid = (() => {
    const t = localToken.startsWith('Bearer ') ? localToken.slice(7) : localToken
    return t.startsWith('eyJ') && t.split('.').length === 3 && t.length > 100
  })()

  const hasRun = pbStates.length > 0

  return (
    <div className="flex flex-col h-full min-h-0 gap-3" style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>

      {/* ── Config bar ──────────────────────────────────────────────────────── */}
      <div className="bg-gray-900 border border-gray-700/60 rounded-xl p-3 flex flex-col gap-0 shrink-0">
        <div className="flex items-center gap-3 flex-wrap">

          {/* Token */}
          {token ? (
            <div className="flex items-center gap-2 min-w-0">
              <span className="size-1.5 rounded-full bg-emerald-400 shrink-0" />
              <span className="text-[11px] text-gray-400 font-mono">{tenantId || '—'}</span>
              <button type="button" onClick={() => setShowTokenInput(v => !v)} className="text-[10px] text-[#818CF8] hover:text-[#6366F1] cursor-pointer transition-colors">change</button>
              <button type="button" onClick={() => { setLocalToken(''); setLocalTenantId(''); onClearToken() }} className="text-[10px] text-red-500/70 hover:text-red-400 cursor-pointer transition-colors">clear</button>
            </div>
          ) : (
            <button type="button" onClick={() => setShowTokenInput(true)} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-orange-500/10 text-orange-400 text-[11px] font-medium border border-orange-500/20 hover:bg-orange-500/15 cursor-pointer transition-colors">
              <Key className="size-3" />Token
            </button>
          )}

          <div className="h-3 w-px bg-gray-700 shrink-0" />

          {/* Count stepper */}
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-gray-500">Parallel</span>
            <div className="flex items-center gap-0 rounded-lg overflow-hidden border border-gray-700 bg-gray-800">
              <button type="button" disabled={running || parallelCount <= 2} onClick={() => setParallelCount(v => Math.max(2, v - 1))}
                className="w-7 h-7 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-700 disabled:opacity-30 cursor-pointer transition-colors text-[14px]">−</button>
              <span className="w-7 text-center text-[13px] font-bold text-white" style={{ fontFamily: 'JetBrains Mono, monospace' }}>{parallelCount}</span>
              <button type="button" disabled={running || parallelCount >= 10} onClick={() => setParallelCount(v => Math.min(10, v + 1))}
                className="w-7 h-7 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-700 disabled:opacity-30 cursor-pointer transition-colors text-[14px]">+</button>
            </div>
          </div>

          {/* Run */}
          <button
            type="button"
            onClick={handleRun}
            disabled={running || !token}
            className="flex items-center gap-1.5 h-8 px-4 rounded-lg text-[12px] font-semibold text-white cursor-pointer transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ background: running ? '#4B4FCB' : 'linear-gradient(135deg, #6366F1 0%, #818CF8 100%)', boxShadow: running ? 'none' : '0 0 16px rgba(99,102,241,0.3)' }}
          >
            {running ? <Loader2 className="size-3.5 animate-spin" /> : <Play className="size-3.5 fill-white" />}
            {running ? 'Running…' : 'Run Test'}
          </button>

          <button type="button" onClick={() => setShowInfo(v => !v)} className="ml-auto text-gray-600 hover:text-gray-400 cursor-pointer transition-colors">
            <Info className="size-3.5" />
          </button>
        </div>

        {/* Info */}
        {showInfo && (
          <div className="text-[11px] text-gray-500 leading-relaxed mt-3 pt-3 border-t border-gray-800">
            Runs <span className="font-mono text-gray-300">PO → GP → GRN → QC</span> once, then fires N identical PB payloads simultaneously against the same document IDs.
            Each panel shows its thread's accounting pipeline in real time. If more than 1 PB is created, the ERP has no duplicate protection at the booking level.
          </div>
        )}

        {/* Token input */}
        {showTokenInput && (
          <div ref={tokenSectionRef} className="mt-3 pt-3 border-t border-gray-800 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-widest text-orange-500/80 font-semibold">ERP Token</span>
              <button type="button" onClick={() => setShowTokenInput(false)} className="text-gray-600 hover:text-gray-400 cursor-pointer"><X className="size-3.5" /></button>
            </div>
            <input
              type="text"
              value={localToken}
              onChange={e => setLocalToken(e.target.value)}
              placeholder="Paste Bearer token (eyJ…)"
              autoComplete="off"
              style={{ WebkitTextSecurity: 'disc', fontFamily: 'JetBrains Mono, monospace' } as React.CSSProperties}
              className={`w-full h-8 px-3 rounded-lg border text-[11px] bg-gray-800 text-gray-200 outline-none transition-colors
                ${localToken ? (tokenValid ? 'border-emerald-500/60' : 'border-red-500/50') : 'border-gray-700'}
                focus:border-[#6366F1]/60`}
            />
            {localToken && !tokenValid && (
              <p className="text-[10px] text-red-400 flex items-center gap-1"><AlertTriangle className="size-2.5 shrink-0" />Must start with eyJ… · 3 dot-separated parts</p>
            )}
            {localToken && tokenValid && (
              <p className="text-[10px] text-emerald-400 flex items-center gap-1"><span className="size-1.5 rounded-full bg-emerald-400 inline-block" />Token valid</p>
            )}
            <div className="flex flex-wrap gap-1.5">
              {KNOWN_TENANTS.map(t => (
                <button key={t.id} onClick={() => setLocalTenantId(t.id)}
                  className={`px-2 py-0.5 rounded text-[10px] font-medium border transition-colors cursor-pointer
                    ${localTenantId === t.id ? 'bg-[#6366F1]/20 text-[#818CF8] border-[#6366F1]/50' : 'bg-transparent text-gray-500 border-gray-700 hover:border-[#6366F1]/40 hover:text-gray-300'}`}>
                  <span className="font-mono">{t.id}</span> {t.name}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={localTenantId}
                onChange={e => setLocalTenantId(e.target.value)}
                placeholder="Tenant ID"
                className="h-8 px-3 w-32 rounded-lg border border-gray-700 bg-gray-800 text-[11px] font-mono text-gray-200 outline-none focus:border-[#6366F1]/60 transition-colors"
              />
              <button onClick={() => setShowTokenInput(false)} className="h-8 px-3 rounded-lg border border-gray-700 text-[11px] text-gray-400 hover:text-gray-200 hover:border-gray-600 cursor-pointer transition-colors">Done</button>
            </div>
          </div>
        )}
      </div>

      {/* ── Chain phase strip ────────────────────────────────────────────────── */}
      {chainPhase !== 'idle' && (
        <div className="bg-gray-900 border border-gray-700/60 rounded-xl px-4 py-2.5 flex items-center gap-3 shrink-0">
          {chainPhase === 'building'
            ? <Loader2 className="size-3.5 text-[#6366F1] animate-spin shrink-0" />
            : <CheckCircle2 className="size-3.5 text-emerald-400 shrink-0" />}
          <span className="text-[11px] font-medium text-gray-400">
            {chainPhase === 'building' ? 'Building chain…' : 'Chain ready'}
          </span>
          {chainPhase === 'ready' && chainDoneText && (
            <>
              <span className="text-gray-700 text-[10px]">·</span>
              <ChainDocs text={chainDoneText} />
            </>
          )}
          {chainPhase === 'ready' && running && (
            <>
              <span className="text-gray-700 text-[10px]">·</span>
              <div className="flex items-center gap-1.5">
                <Loader2 className="size-3 text-[#6366F1] animate-spin" />
                <span className="text-[10px] text-[#818CF8]">firing {parallelCount} threads</span>
              </div>
            </>
          )}
        </div>
      )}

      {/* ── PB panels ────────────────────────────────────────────────────────── */}
      {hasRun && (
        <div className={`grid gap-3 ${gridClass(pbStates.length)} flex-1 min-h-0`}>
          {pbStates.map((state, i) => (
            <PbPanel key={i} idx={i} state={state} running={running} />
          ))}
        </div>
      )}

      {/* ── Result banner ────────────────────────────────────────────────────── */}
      {duplicateDetected === true && (
        <div className="shrink-0 rounded-xl border border-red-500/30 bg-red-500/5 px-4 py-3 flex items-start gap-3">
          <AlertTriangle className="size-4 text-red-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-[12px] font-semibold text-red-400">
              {createdCount} duplicate PBs created — ERP has no concurrency guard
            </p>
            <p className="text-[11px] text-red-500/70 mt-0.5">
              All {createdCount} Purchase Bookings were accepted for the same QC/GRN/PO. Accounting entries have been posted {createdCount}×.
            </p>
          </div>
        </div>
      )}
      {duplicateDetected === false && (
        <div className="shrink-0 rounded-xl border border-emerald-500/30 bg-emerald-500/5 px-4 py-3">
          <p className="text-[12px] font-semibold text-emerald-400">✓ ERP rejected duplicate submissions</p>
          <p className="text-[11px] text-emerald-500/60 mt-0.5">Only 1 PB was created and posted.</p>
        </div>
      )}
    </div>
  )
}
