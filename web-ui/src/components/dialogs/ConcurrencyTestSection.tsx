'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AlertTriangle, Play, Loader2, Key, X, CheckCircle2, XCircle, Clock } from 'lucide-react'
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
  { id: '686', name: 'Agristack Company' },
  { id: '751', name: 'Tech Neo' },
  { id: '895', name: 'Janardhan FPC' },
]

type PbStatus = 'waiting' | 'created' | 'rejected' | 'error'

interface PbLog { text: string; ts: Date; isErr: boolean }
interface PbState { status: PbStatus; logs: PbLog[] }

function formatTime(d: Date) {
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

function isValidToken(raw: string) {
  const t = raw.startsWith('Bearer ') ? raw.slice(7) : raw
  return t.startsWith('eyJ') && t.split('.').length === 3 && t.length > 100
}

// Extract "PB [N]" index from a log line. Returns 0-based index or -1 if not a PB line.
function parsePbIndex(text: string): number {
  const m = text.match(/PB \[(\d+)\]/)
  return m ? parseInt(m[1]) - 1 : -1
}

function gridCols(n: number) {
  if (n === 2) return 'grid-cols-2'
  if (n === 3) return 'grid-cols-3'
  if (n === 4) return 'grid-cols-2'
  if (n <= 6)  return 'grid-cols-3'
  return 'grid-cols-4'
}

function PbPanel({ idx, state, running }: { idx: number; state: PbState; running: boolean }) {
  const logsEndRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.logs])

  const statusIcon =
    state.status === 'created'  ? <CheckCircle2 className="size-4 text-emerald-500 shrink-0" /> :
    state.status === 'rejected' ? <XCircle      className="size-4 text-amber-500 shrink-0" /> :
    state.status === 'error'    ? <XCircle      className="size-4 text-red-500 shrink-0" /> :
    running                     ? <Loader2      className="size-4 text-[#3F51B5] animate-spin shrink-0" /> :
                                  <Clock        className="size-4 text-gray-400 shrink-0" />

  const statusText =
    state.status === 'created'  ? 'CREATED' :
    state.status === 'rejected' ? 'REJECTED' :
    state.status === 'error'    ? 'ERROR' :
    running                     ? 'waiting…' : 'idle'

  const headerBg =
    state.status === 'created'  ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-300 dark:border-emerald-700' :
    state.status === 'rejected' ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-300 dark:border-amber-700' :
    state.status === 'error'    ? 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700' :
    'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'

  return (
    <div className="flex flex-col border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden min-h-[220px]">
      {/* Panel header */}
      <div className={`flex items-center gap-2 px-3 py-2 border-b ${headerBg} shrink-0`}>
        {statusIcon}
        <span className="text-[12px] font-semibold text-gray-800 dark:text-gray-100">PB {idx + 1}</span>
        <span className={`text-[11px] font-medium ml-auto ${
          state.status === 'created'  ? 'text-emerald-600 dark:text-emerald-400' :
          state.status === 'rejected' ? 'text-amber-600 dark:text-amber-400' :
          state.status === 'error'    ? 'text-red-600 dark:text-red-400' :
          'text-gray-500 dark:text-gray-400'
        }`}>{statusText}</span>
      </div>

      {/* Log lines */}
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5 font-mono bg-white dark:bg-gray-900">
        {state.logs.length === 0 && running && (
          <div className="text-[10px] text-gray-400 dark:text-gray-500 italic px-1 pt-1">Waiting for thread to start…</div>
        )}
        {state.logs.map((log, i) => (
          <div key={i} className={`flex gap-1.5 items-start text-[10px] ${log.isErr ? 'text-red-500 dark:text-red-400' : 'text-gray-700 dark:text-gray-300'}`}>
            <span className="text-gray-400 dark:text-gray-500 shrink-0">[{formatTime(log.ts)}]</span>
            <span className="whitespace-pre-wrap break-all">{log.text}</span>
          </div>
        ))}
        <div ref={logsEndRef} />
      </div>
    </div>
  )
}

export function ConcurrencyTestSection({ erpToken, erpTenantId, onNeedsToken, onClearToken }: Props) {
  const { token, tenantId, localToken, setLocalToken, localTenantId, setLocalTenantId, handleAuthError } = useErpToken(erpToken, erpTenantId)
  const [parallelCount, setParallelCount] = useState(3)
  const [running, setRunning]   = useState(false)
  const [showTokenInput, setShowTokenInput] = useState(!erpToken)
  const [generalLogs, setGeneralLogs] = useState<{ text: string; ts: Date; isErr: boolean }[]>([])
  const [pbStates, setPbStates]   = useState<PbState[]>([])
  const [duplicateDetected, setDuplicateDetected] = useState<boolean | null>(null)
  const tokenSectionRef = useRef<HTMLDivElement>(null)
  const generalEndRef   = useRef<HTMLDivElement>(null)

  useEffect(() => {
    generalEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [generalLogs])

  useEffect(() => {
    if (showTokenInput) tokenSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [showTokenInput])

  const handleRun = useCallback(() => {
    if (!token) { setShowTokenInput(true); return }

    const n = parallelCount
    setRunning(true)
    setGeneralLogs([])
    setDuplicateDetected(null)
    setPbStates(Array.from({ length: n }, () => ({ status: 'waiting' as PbStatus, logs: [] })))

    startPbConcurrencyTest(
      token,
      tenantId || '681',
      n,
      (event: SSEEvent) => {
        const ts   = new Date()
        const text = event.message
        const isErr = event.type === 'error'

        if (event.type === 'run_end') {
          setRunning(false)
          setDuplicateDetected((event.created ?? 0) > 1)
          setGeneralLogs(prev => [...prev, { text, ts, isErr: false }])
          return
        }

        const pbIdx = parsePbIndex(text)

        if (pbIdx >= 0 && pbIdx < n) {
          // Route to the right PB panel
          setPbStates(prev => {
            const next = prev.map((s, i) => i !== pbIdx ? s : { ...s, logs: [...s.logs, { text: text.trim(), ts, isErr }] })
            // Update panel status from the headline line
            if (/PB \[\d+\] CREATED/.test(text))  next[pbIdx] = { ...next[pbIdx], status: 'created' }
            if (/PB \[\d+\] REJECTED/.test(text)) next[pbIdx] = { ...next[pbIdx], status: 'rejected' }
            if (/PB \[\d+\] ERROR/.test(text))    next[pbIdx] = { ...next[pbIdx], status: 'error' }
            return next
          })
        } else {
          // General line (Step 1, payload, threads finished, etc.)
          setGeneralLogs(prev => [...prev, { text, ts, isErr }])
        }
      },
      () => setRunning(false),
      (err) => {
        if (!handleAuthError(err)) {
          setGeneralLogs(prev => [...prev, { text: `Error: ${err.message}`, ts: new Date(), isErr: true }])
        }
        setRunning(false)
      },
    )
  }, [token, tenantId, parallelCount, handleAuthError])

  const tokenValid   = isValidToken(localToken)
  const tokenEntered = localToken.length > 0

  return (
    <div className="flex flex-col h-full min-h-0 gap-3 overflow-y-auto">

      {/* ── Config card ─────────────────────────────────────────────────────── */}
      <div className="bg-white dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex flex-col gap-3 shrink-0">

        {/* Description */}
        <div className="p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-[11px] text-amber-700 dark:text-amber-300 space-y-1">
          <p className="font-semibold">What this does</p>
          <p>Runs <span className="font-mono bg-amber-100 dark:bg-amber-900/40 px-1 rounded">PO → GP → GRN → QC</span> once, then fires <strong>N identical PB payloads simultaneously</strong> against the same QC/GRN/PO. Each PB gets its own live panel below.</p>
        </div>

        {/* Token status */}
        <div className="flex items-center gap-3 flex-wrap">
          {token ? (
            <div className="flex items-center gap-2">
              <span className="inline-block size-2 rounded-full bg-green-500" />
              <span className="text-[11px] text-green-600 dark:text-green-400 font-medium">Token active</span>
              <span className="text-[10px] text-gray-400 dark:text-gray-500">· tenant {tenantId || '(none)'}</span>
              <button type="button" onClick={() => setShowTokenInput(v => !v)} className="ml-1 text-[10px] text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 underline cursor-pointer">change</button>
              <button type="button" onClick={() => { setLocalToken(''); setLocalTenantId(''); onClearToken() }} className="text-[10px] text-red-500 hover:text-red-700 underline cursor-pointer">clear</button>
            </div>
          ) : (
            <button type="button" onClick={() => setShowTokenInput(true)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 text-[12px] font-medium border border-orange-300 dark:border-orange-700 hover:bg-orange-200 cursor-pointer">
              <Key className="size-3.5" />Set ERP Token
            </button>
          )}
        </div>

        {/* Inline token panel */}
        {showTokenInput && (
          <div ref={tokenSectionRef} className="p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-[11px] text-orange-600 dark:text-orange-400 font-medium">ERP Credentials</Label>
              <button type="button" onClick={() => setShowTokenInput(false)} className="text-gray-400 hover:text-gray-600 cursor-pointer"><X className="size-3.5" /></button>
            </div>
            <Input
              type="text"
              value={localToken}
              onChange={e => setLocalToken(e.target.value)}
              placeholder="Paste your Bearer token (eyJ…)"
              autoComplete="off"
              style={{ WebkitTextSecurity: 'disc' } as React.CSSProperties}
              className={`h-9 text-[12px] ${tokenEntered ? (tokenValid ? 'border-green-400' : 'border-red-400') : ''}`}
            />
            {tokenEntered && !tokenValid && (
              <div className="rounded border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-2 space-y-1">
                <div className="flex items-center gap-1.5">
                  <AlertTriangle className="size-3 text-red-500 shrink-0" />
                  <span className="text-[11px] font-semibold text-red-600 dark:text-red-400">Token format looks incorrect — must start with eyJ…</span>
                </div>
                <div className="rounded bg-gray-900 p-2">
                  <p className="text-[10px] text-yellow-300 break-all">eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.<span className="text-blue-300">eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiw…</span>.<span className="text-pink-300">SflKxwRJSMeKKF2QT4fw…</span></p>
                </div>
              </div>
            )}
            {tokenEntered && tokenValid && (
              <p className="text-[11px] text-green-600 dark:text-green-400 flex items-center gap-1">
                <span className="inline-block size-2 rounded-full bg-green-500" />Token looks valid
              </p>
            )}
            <div className="flex flex-wrap gap-1.5">
              {KNOWN_TENANTS.map(t => (
                <button key={t.id} onClick={() => setLocalTenantId(t.id)} className={`px-2 py-0.5 rounded-full text-[11px] font-medium border transition-colors cursor-pointer ${localTenantId === t.id ? 'bg-orange-500 text-white border-orange-500' : 'bg-white dark:bg-gray-800 text-orange-600 dark:text-orange-400 border-orange-300 dark:border-orange-700 hover:bg-orange-50'}`}>
                  {t.id} · {t.name}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <Input type="text" value={localTenantId} onChange={e => setLocalTenantId(e.target.value)} placeholder="Tenant ID (e.g. 708, 871)" autoComplete="off" className="h-9 text-[12px] w-48" />
              <Button onClick={() => setShowTokenInput(false)} variant="ghost" size="sm" className="h-9 text-[12px] cursor-pointer">Done</Button>
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="flex items-end gap-4 flex-wrap">
          <div className="flex flex-col gap-1">
            <Label className="text-[11px] text-gray-600 dark:text-gray-400">Parallel PB submissions</Label>
            <Input
              type="number" min={2} max={10} value={parallelCount}
              onChange={e => setParallelCount(Math.max(2, Math.min(10, parseInt(e.target.value) || 3)))}
              disabled={running} className="h-9 w-24 text-[12px]"
            />
          </div>
          <Button
            onClick={handleRun}
            disabled={running || !token}
            className="h-9 bg-[#3F51B5] hover:bg-[#303F9F] text-white text-[12px] gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {running ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
            {running ? 'Running…' : `Run (${parallelCount}× PB)`}
          </Button>
          {!token && <span className="text-[11px] text-orange-500 dark:text-orange-400">Set ERP token first ↑</span>}
        </div>

        {/* Result banners */}
        {duplicateDetected === true && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-lg flex items-start gap-2">
            <AlertTriangle className="size-4 text-red-500 shrink-0 mt-0.5" />
            <div className="text-[12px] text-red-700 dark:text-red-300">
              <p className="font-semibold">Duplicate PBs created — ERP has no concurrency guard</p>
              <p className="text-[11px] mt-0.5">Multiple Purchase Bookings were accepted for the same QC/GRN/PO. Accounting entries have been posted multiple times.</p>
            </div>
          </div>
        )}
        {duplicateDetected === false && (
          <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-300 dark:border-emerald-700 rounded-lg text-[12px] text-emerald-700 dark:text-emerald-300 font-medium">
            ✓ ERP correctly rejected duplicate submissions — only 1 PB was created.
          </div>
        )}
      </div>

      {/* ── General log strip (Step 1, payload, summary) ──────────────────── */}
      {generalLogs.length > 0 && (
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shrink-0">
          <div className="px-3 py-1.5 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 flex items-center gap-2">
            <span className="text-[10px] font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Chain log</span>
            {running && <span className="text-[10px] text-[#3F51B5] dark:text-[#7986CB] animate-pulse">● live</span>}
          </div>
          <div className="p-2 space-y-0.5 font-mono max-h-36 overflow-y-auto">
            {generalLogs.map((log, i) => (
              <div key={i} className={`flex gap-1.5 items-start text-[10px] ${log.isErr ? 'text-red-500 dark:text-red-400' : 'text-gray-600 dark:text-gray-300'}`}>
                <span className="text-gray-400 shrink-0">[{formatTime(log.ts)}]</span>
                <span className="whitespace-pre-wrap break-all">{log.text}</span>
              </div>
            ))}
            <div ref={generalEndRef} />
          </div>
        </div>
      )}

      {/* ── Per-PB panels ─────────────────────────────────────────────────── */}
      {pbStates.length > 0 && (
        <div className={`grid gap-3 ${gridCols(pbStates.length)} flex-1 min-h-0`}>
          {pbStates.map((state, i) => (
            <PbPanel key={i} idx={i} state={state} running={running} />
          ))}
        </div>
      )}
    </div>
  )
}
