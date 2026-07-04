'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { startRun, fetchRunsFromDB } from '@/lib/api'
import { withCsrf } from '@/lib/csrf-client'
import {
  CheckCircle2, XCircle, Loader2, Circle, Rocket, RotateCcw,
  History, ChevronRight, Clock, ChevronDown, ChevronUp, Key, X,
  TrendingUp, Package,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import type { RunHistoryItem } from '@/lib/api'
import type { ErpCred } from '@/lib/types'

// ── Modules to check ─────────────────────────────────────────────────────────
const SMOKE_MODULES = [
  { id: 'agent',    label: 'Agent',    module: 'registration', subModule: 'agent' },
  { id: 'employee', label: 'Employee', module: 'registration', subModule: 'employee' },
]

// ── Types ─────────────────────────────────────────────────────────────────────
type Status = 'idle' | 'running' | 'passed' | 'failed'

interface ModuleResult {
  status: Status
  log: string[]
  passed: number
  failed: number
  durationMs: number
}

// Shape stored in RunHistory.results JSON
interface DeploymentRunResults {
  type: 'deployment'
  modules: Array<{
    id: string
    label: string
    status: 'passed' | 'failed'
    passed: number
    failed: number
    durationMs: number
    log: string[]
  }>
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function StatusIcon({ status }: { status: Status | 'passed' | 'failed' }) {
  if (status === 'idle')    return <Circle       className="w-4 h-4 text-gray-400" />
  if (status === 'running') return <Loader2      className="w-4 h-4 text-blue-500 animate-spin" />
  if (status === 'passed')  return <CheckCircle2 className="w-4 h-4 text-green-500" />
  return                           <XCircle      className="w-4 h-4 text-red-500" />
}

function statusBg(status: Status) {
  if (status === 'running') return 'bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800'
  if (status === 'passed')  return 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800'
  if (status === 'failed')  return 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800'
  return 'bg-gray-50 dark:bg-gray-800/40 border-gray-200 dark:border-gray-700'
}

function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) +
    ' ' + d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
}

function formatDuration(ms: number) {
  const s = Math.floor(ms / 1000)
  const m = Math.floor(s / 60)
  if (m > 0) return `${m}m ${s % 60}s`
  return `${s}s`
}

async function saveDeploymentRun(
  modules: Array<{ id: string; label: string; status: 'passed' | 'failed'; passed: number; failed: number; durationMs: number; log: string[] }>,
  totalDurationMs: number,
) {
  const passed = modules.filter(m => m.status === 'passed').length
  const failed = modules.filter(m => m.status === 'failed').length
  const total  = modules.length
  const rate   = total > 0 ? Math.round((passed / total) * 10000) / 100 : 0
  const secs   = Math.floor(totalDurationMs / 1000)
  const mins   = Math.floor(secs / 60)
  const duration = mins > 0 ? `${mins}m ${secs % 60}s` : `${secs}s`
  const now = new Date().toISOString()
  const startedAt = new Date(Date.now() - totalDurationMs).toISOString()

  try {
    await fetch('/api/runs', withCsrf({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        moduleId: 'deployment-check',
        moduleName: 'Deployment Check',
        passed,
        failed,
        total,
        duration,
        rate,
        results: { type: 'deployment', modules } satisfies DeploymentRunResults,
        status: failed > 0 ? 'failed' : 'completed',
        startedAt,
        completedAt: now,
      }),
    }))
  } catch {
    // best-effort
  }
}

// ── Toast + Final summary types ───────────────────────────────────────────────
interface ToastData {
  id: string
  label: string
  status: 'passed' | 'failed'
  passed: number
  failed: number
  durationMs: number
  // test names that passed/failed, parsed from SSE test_end events
  testNames: string[]
}

interface FinalModuleSummary {
  id: string
  label: string
  status: 'passed' | 'failed' | 'idle'
  passed: number
  failed: number
  durationMs: number
  testNames: string[]
}

// ── Per-module completion toast ───────────────────────────────────────────────
const TOAST_DURATION_MS = 7500

function ModuleToast({ data, onDismiss }: { data: ToastData; onDismiss: () => void }) {
  // countdown: 1 → 0 over TOAST_DURATION_MS using CSS animation via a ref
  const barRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const timer = setTimeout(onDismiss, TOAST_DURATION_MS)
    // kick off the width transition after first paint
    const raf = requestAnimationFrame(() => {
      if (barRef.current) {
        barRef.current.style.transition = `width ${TOAST_DURATION_MS}ms linear`
        barRef.current.style.width = '0%'
      }
    })
    return () => { clearTimeout(timer); cancelAnimationFrame(raf) }
  }, [onDismiss])

  const isPassed = data.status === 'passed'

  return (
    <div style={{ animation: 'slideInRight 0.3s cubic-bezier(0.16,1,0.3,1)' }} className={`pointer-events-auto w-80 rounded-xl border shadow-2xl overflow-hidden bg-white dark:bg-gray-900 ${
      isPassed ? 'border-green-200 dark:border-green-800' : 'border-red-200 dark:border-red-800'
    }`}>
      {/* Header stripe */}
      <div className={`flex items-center justify-between px-4 py-2.5 ${
        isPassed ? 'bg-green-500' : 'bg-red-500'
      }`}>
        <div className="flex items-center gap-2 text-white">
          {isPassed
            ? <CheckCircle2 className="w-4 h-4 shrink-0" />
            : <XCircle      className="w-4 h-4 shrink-0" />}
          <span className="font-semibold text-sm">{data.label}</span>
          <span className="text-xs text-white/75">{isPassed ? '— passed' : '— failed'}</span>
        </div>
        <button onClick={onDismiss} className="text-white/60 hover:text-white transition-colors">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Body */}
      <div className="px-4 py-3 space-y-2.5">
        {/* What ran */}
        <div className="flex items-start gap-2">
          <Package className="w-3.5 h-3.5 text-gray-400 mt-0.5 shrink-0" />
          <div className="text-xs text-gray-600 dark:text-gray-300 space-y-0.5">
            {data.testNames.length > 0
              ? data.testNames.map(t => (
                  <div key={t} className={`font-mono ${isPassed ? 'text-green-700 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {t}
                  </div>
                ))
              : <span className="text-gray-400 italic">smoke test</span>
            }
          </div>
        </div>

        {/* Created record info */}
        {isPassed && (
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800">
            <CheckCircle2 className="w-3 h-3 text-green-500 shrink-0" />
            <span className="text-[11px] text-green-700 dark:text-green-300">
              1 {data.label} record created successfully
            </span>
          </div>
        )}

        {/* Duration */}
        <div className="flex items-center justify-between text-[11px] text-gray-400">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" /> {formatDuration(data.durationMs)}
          </span>
          <span>{data.passed} passed{data.failed > 0 ? ` · ${data.failed} failed` : ''}</span>
        </div>
      </div>

      {/* Countdown bar */}
      <div className="h-1 bg-gray-100 dark:bg-gray-800">
        <div
          ref={barRef}
          className={`h-full ${isPassed ? 'bg-green-400' : 'bg-red-400'}`}
          style={{ width: '100%' }}
        />
      </div>
    </div>
  )
}

// ── Final summary dialog ──────────────────────────────────────────────────────
function FinalSummaryDialog({
  modules,
  totalDurationMs,
  onClose,
}: {
  modules: FinalModuleSummary[]
  totalDurationMs: number
  onClose: () => void
}) {
  const passed  = modules.filter(m => m.status === 'passed').length
  const failed  = modules.filter(m => m.status === 'failed').length
  const total   = modules.filter(m => m.status !== 'idle').length
  const passRate = total > 0 ? Math.round((passed / total) * 100) : 0
  const allGood = failed === 0

  return (
    <Dialog open onOpenChange={v => { if (!v) onClose() }}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base">
            <Rocket className="w-5 h-5 text-indigo-500" />
            Deployment Check — Results
          </DialogTitle>
          <DialogDescription>
            {allGood ? 'All modules passed.' : `${failed} module${failed > 1 ? 's' : ''} need attention.`}
          </DialogDescription>
        </DialogHeader>

        {/* Summary cards */}
        <div className="grid grid-cols-3 gap-3 mt-1">
          <div className="rounded-lg border border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50 px-3 py-2.5 text-center">
            <div className="text-2xl font-bold text-gray-800 dark:text-gray-100">{total}</div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">Modules</div>
          </div>
          <div className="rounded-lg border border-green-100 dark:border-green-900 bg-green-50 dark:bg-green-900/20 px-3 py-2.5 text-center">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">{passed}</div>
            <div className="text-[11px] text-green-600/70 dark:text-green-400/70 mt-0.5">Passed</div>
          </div>
          <div className={`rounded-lg border px-3 py-2.5 text-center ${failed > 0 ? 'border-red-100 dark:border-red-900 bg-red-50 dark:bg-red-900/20' : 'border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50'}`}>
            <div className={`text-2xl font-bold ${failed > 0 ? 'text-red-500' : 'text-gray-400 dark:text-gray-500'}`}>{failed}</div>
            <div className={`text-[11px] mt-0.5 ${failed > 0 ? 'text-red-500/70' : 'text-gray-400/70'}`}>Failed</div>
          </div>
        </div>

        {/* Pass rate bar */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <span className="flex items-center gap-1"><TrendingUp className="w-3.5 h-3.5" /> Pass rate</span>
            <span className="font-semibold text-gray-700 dark:text-gray-200">{passRate}%</span>
          </div>
          <div className="h-2 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${allGood ? 'bg-green-500' : 'bg-red-400'}`}
              style={{ width: `${passRate}%` }}
            />
          </div>
        </div>

        {/* Per-module breakdown */}
        <div className="border border-gray-100 dark:border-gray-800 rounded-lg overflow-hidden">
          <div className="grid grid-cols-[1fr_auto_auto] text-[11px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wide px-3 py-2 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
            <span>Module</span>
            <span className="text-center pr-4">Result</span>
            <span className="text-right">Time</span>
          </div>
          {modules.filter(m => m.status !== 'idle').map((m, i) => (
            <div
              key={m.id}
              className={`grid grid-cols-[1fr_auto_auto] items-center px-3 py-2.5 text-sm ${
                i > 0 ? 'border-t border-gray-50 dark:border-gray-800/60' : ''
              }`}
            >
              <span className="font-medium text-gray-700 dark:text-gray-200">{m.label}</span>
              <span className="pr-4">
                {m.status === 'passed'
                  ? <span className="inline-flex items-center gap-1 text-green-600 dark:text-green-400 text-xs font-medium"><CheckCircle2 className="w-3.5 h-3.5" /> Passed</span>
                  : <span className="inline-flex items-center gap-1 text-red-500 text-xs font-medium"><XCircle className="w-3.5 h-3.5" /> Failed</span>
                }
              </span>
              <span className="text-xs text-gray-400 text-right tabular-nums">{formatDuration(m.durationMs)}</span>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-gray-400 pt-1">
          <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> Total: {formatDuration(totalDurationMs)}</span>
          <Button size="sm" onClick={onClose} className="h-7 px-4 text-xs">
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// ── Credential dropdown ───────────────────────────────────────────────────────
function CredentialDropdown({
  credentials,
  activeCredId,
  onSelectCred,
}: {
  credentials: ErpCred[]
  activeCredId: string | null
  onSelectCred: (id: string) => void
}) {
  const [open, setOpen] = useState(false)
  const active = credentials.find(c => c.id === activeCredId)

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className={`flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-full cursor-pointer transition-colors border ${
          active
            ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800'
            : 'bg-orange-50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 border-orange-200 dark:border-orange-800'
        }`}
      >
        <Key className="w-3 h-3" />
        {active ? active.name : 'Set Credential'}
        <ChevronDown className="w-3 h-3" />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-50" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-1 z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg min-w-[240px] overflow-hidden">
            {credentials.length === 0 ? (
              <div className="px-3 py-6 text-center text-[12px] text-gray-400">No saved credentials</div>
            ) : (
              <div className="max-h-48 overflow-y-auto">
                {credentials.map(cred => (
                  <button
                    key={cred.id}
                    onClick={() => { onSelectCred(cred.id); setOpen(false) }}
                    className={`w-full flex items-center gap-2 px-3 py-2 text-[12px] text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer ${
                      cred.id === activeCredId ? 'bg-indigo-50 dark:bg-indigo-900/20' : ''
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className={`truncate font-medium ${cred.id === activeCredId ? 'text-indigo-600 dark:text-indigo-400' : 'text-gray-700 dark:text-gray-200'}`}>
                        {cred.name}
                      </div>
                      <div className="truncate text-gray-400 text-[11px]">{cred.email}</div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {cred.id === activeCredId && (
                        <span className="text-[10px] bg-indigo-600 text-white px-1.5 py-0.5 rounded-full">Active</span>
                      )}
                      {cred.isDefault && <span className="text-yellow-500 text-[12px]">★</span>}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

// ── History detail dialog ─────────────────────────────────────────────────────
function HistoryDetailDialog({ run, onClose }: { run: RunHistoryItem; onClose: () => void }) {
  const results = run.results as unknown as DeploymentRunResults | null
  const modules = results?.modules ?? []
  const passed = modules.filter(m => m.status === 'passed').length
  const failed = modules.filter(m => m.status === 'failed').length
  const [expandedLog, setExpandedLog] = useState<string | null>(null)

  return (
    <Dialog open onOpenChange={v => { if (!v) onClose() }}>
      <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Rocket className="w-5 h-5 text-indigo-500" />
            Deployment Check — {run.startedAt ? formatDate(run.startedAt) : '—'}
          </DialogTitle>
          <DialogDescription>
            {passed} passed · {failed} failed · {run.duration}
          </DialogDescription>
        </DialogHeader>

        {/* Summary pills */}
        <div className="flex gap-3 text-sm">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" /> {passed} passed
          </span>
          {failed > 0 && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 font-medium">
              <XCircle className="w-3.5 h-3.5" /> {failed} failed
            </span>
          )}
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300">
            <Clock className="w-3.5 h-3.5" /> {run.duration}
          </span>
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto">
          <div className="space-y-2 pr-2">
            {modules.map(mod => (
              <div
                key={mod.id}
                className={`rounded-lg border p-3 ${mod.status === 'passed'
                  ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/20'
                  : 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/20'}`}
              >
                <div className="flex items-center gap-2">
                  <StatusIcon status={mod.status} />
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-200 flex-1">{mod.label}</span>
                  <span className="text-xs text-gray-400">{formatDuration(mod.durationMs)}</span>
                  {mod.status === 'failed' && mod.log.length > 0 && (
                    <button
                      onClick={() => setExpandedLog(expandedLog === mod.id ? null : mod.id)}
                      className="ml-1 p-0.5 text-gray-400 hover:text-gray-600"
                    >
                      {expandedLog === mod.id ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  )}
                </div>
                {expandedLog === mod.id && mod.log.length > 0 && (
                  <div className="mt-2 text-xs font-mono text-red-700 dark:text-red-300 bg-red-100 dark:bg-red-950/50 rounded p-2 max-h-32 overflow-y-auto whitespace-pre-wrap break-all">
                    {mod.log.join('\n')}
                  </div>
                )}
              </div>
            ))}
            {modules.length === 0 && (
              <p className="text-sm text-gray-400 text-center py-8">No module detail available for this run.</p>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// ── History tab content ───────────────────────────────────────────────────────
function HistoryTab() {
  const [runs, setRuns] = useState<RunHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [detail, setDetail] = useState<RunHistoryItem | null>(null)

  useEffect(() => {
    fetchRunsFromDB(200).then(all => {
      setRuns(all.filter(r => r.moduleId === 'deployment-check'))
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center flex-1 text-gray-400 gap-2">
        <Loader2 className="w-4 h-4 animate-spin" /> Loading history…
      </div>
    )
  }

  if (runs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 gap-3 text-gray-400">
        <History className="w-10 h-10 opacity-30" />
        <p className="text-sm">No deployment check runs yet.</p>
        <p className="text-xs">Run a deployment check and it will appear here.</p>
      </div>
    )
  }

  return (
    <div className="flex-1 min-h-0 overflow-y-auto">
      <div className="space-y-2 pb-4">
        {runs.map(run => {
          const results = run.results as unknown as DeploymentRunResults | null
          const modules = results?.modules ?? []
          const failedMods = modules.filter(m => m.status === 'failed')
          const allPassed = failedMods.length === 0

          return (
            <button
              key={run.id}
              onClick={() => setDetail(run)}
              className="w-full text-left rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:border-indigo-300 dark:hover:border-indigo-600 hover:shadow-sm transition-all px-4 py-3 flex items-center gap-4"
            >
              {/* Status indicator */}
              <div className={`w-2 h-2 rounded-full shrink-0 ${allPassed ? 'bg-green-500' : 'bg-red-500'}`} />

              {/* Date + result label */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                    {run.startedAt ? formatDate(run.startedAt) : '—'}
                  </span>
                  {allPassed
                    ? <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 font-medium">All passed</span>
                    : <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 font-medium">{failedMods.length} failed</span>
                  }
                </div>
                {failedMods.length > 0 && (
                  <p className="text-xs text-gray-400 mt-0.5 truncate">
                    Failed: {failedMods.map(m => m.label).join(', ')}
                  </p>
                )}
              </div>

              {/* Stats */}
              <div className="shrink-0 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                <span className="text-green-600 dark:text-green-400">{run.passed ?? 0} ✓</span>
                {(run.failed ?? 0) > 0 && <span className="text-red-500">{run.failed} ✗</span>}
                <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{run.duration}</span>
                <ChevronRight className="w-4 h-4 text-gray-300 dark:text-gray-600" />
              </div>
            </button>
          )
        })}
      </div>
      {detail && <HistoryDetailDialog run={detail} onClose={() => setDetail(null)} />}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export function DeploymentCheckTab({
  erpToken,
  erpTenantId,
  credentials = [],
  activeCredId: parentCredId,
  getPassword,
}: {
  erpToken?: string
  erpTenantId?: string
  credentials?: ErpCred[]
  activeCredId?: string | null
  getPassword?: (id: string) => string
}) {
  const [activeTab, setActiveTab] = useState<'run' | 'history'>('run')
  // local cred selection — starts from the parent's active cred
  const [localCredId, setLocalCredId] = useState<string | null>(parentCredId ?? null)

  const activeCred = credentials.find(c => c.id === localCredId) ?? null
  const erpEmail    = activeCred?.email
  const erpPassword = activeCred ? (getPassword?.(activeCred.id) ?? '') : undefined
  const [results, setResults] = useState<Record<string, ModuleResult>>(() =>
    Object.fromEntries(SMOKE_MODULES.map(m => [m.id, { status: 'idle', log: [], passed: 0, failed: 0, durationMs: 0 }]))
  )
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState(false)
  const abortRef = useRef(false)
  const runStartRef = useRef(0)

  // per-module toast (one at a time — shows immediately after each module finishes)
  const [toast, setToast] = useState<ToastData | null>(null)
  // final analytical summary
  const [finalSummary, setFinalSummary] = useState<{ modules: FinalModuleSummary[]; totalDurationMs: number } | null>(null)

  const updateResult = useCallback((id: string, patch: Partial<ModuleResult>) => {
    setResults(prev => ({ ...prev, [id]: { ...prev[id], ...patch } }))
  }, [])

  const reset = useCallback(() => {
    abortRef.current = false
    setDone(false)
    setToast(null)
    setFinalSummary(null)
    setResults(Object.fromEntries(
      SMOKE_MODULES.map(m => [m.id, { status: 'idle', log: [], passed: 0, failed: 0, durationMs: 0 }])
    ))
  }, [])

  const runAll = useCallback(async () => {
    abortRef.current = false
    setRunning(true)
    setDone(false)
    setToast(null)
    setFinalSummary(null)
    runStartRef.current = Date.now()

    const freshResults: Record<string, ModuleResult> = Object.fromEntries(
      SMOKE_MODULES.map(m => [m.id, { status: 'idle', log: [], passed: 0, failed: 0, durationMs: 0 }])
    )
    setResults(freshResults)

    // mutable accumulator — never read React state inside the loop
    const acc: Record<string, ModuleResult & { testNames: string[] }> = Object.fromEntries(
      SMOKE_MODULES.map(m => [m.id, { status: 'idle' as Status, log: [], passed: 0, failed: 0, durationMs: 0, testNames: [] }])
    )

    for (const mod of SMOKE_MODULES) {
      if (abortRef.current) break

      acc[mod.id] = { ...acc[mod.id], status: 'running', log: [], testNames: [] }
      setResults(prev => ({ ...prev, [mod.id]: { ...prev[mod.id], status: 'running', log: [] } }))

      const start = Date.now()

      await new Promise<void>(resolve => {
        startRun(
          mod.module,
          mod.subModule,
          ['test_create_smoke'],
          (event) => {
            if (event.type === 'log' && event.message) {
              acc[mod.id].log = [...acc[mod.id].log, event.message].slice(-50)
              setResults(prev => ({
                ...prev,
                [mod.id]: { ...prev[mod.id], log: acc[mod.id].log },
              }))
            }
            // capture individual test outcomes from test_end events
            if (event.type === 'test_end' && event.test_name) {
              acc[mod.id].testNames = [...acc[mod.id].testNames, event.test_name]
            }
          },
          (summary) => {
            const durationMs = Date.now() - start
            const passed = summary.passed ?? 0
            const failed = summary.failed ?? 0
            const status: Status = failed > 0 || passed === 0 ? 'failed' : 'passed'
            acc[mod.id] = { ...acc[mod.id], status, passed, failed, durationMs }
            updateResult(mod.id, { status, passed, failed, durationMs })

            // show per-module toast
            setToast({
              id: mod.id,
              label: mod.label,
              status,
              passed,
              failed,
              durationMs,
              testNames: acc[mod.id].testNames,
            })

            resolve()
          },
          (err) => {
            const durationMs = Date.now() - start
            acc[mod.id] = { ...acc[mod.id], status: 'failed', passed: 0, failed: 1, durationMs }
            updateResult(mod.id, { status: 'failed', log: [err.message], durationMs })
            setToast({ id: mod.id, label: mod.label, status: 'failed', passed: 0, failed: 1, durationMs, testNames: [] })
            resolve()
          },
          erpToken,
          erpTenantId,
          erpEmail,
          erpPassword,
        )
      })
    }

    const totalDurationMs = Date.now() - runStartRef.current
    setRunning(false)
    setDone(true)

    // build final summary for all modules that actually ran
    const finalModules: FinalModuleSummary[] = SMOKE_MODULES.map(m => ({
      id: m.id,
      label: m.label,
      status: acc[m.id].status === 'idle' ? 'idle' : acc[m.id].status as 'passed' | 'failed',
      passed: acc[m.id].passed,
      failed: acc[m.id].failed,
      durationMs: acc[m.id].durationMs,
      testNames: acc[m.id].testNames,
    }))

    // clear the last per-module toast, then show the final summary after a short pause
    // so the user sees the last toast briefly before the summary replaces it
    setTimeout(() => {
      setToast(null)
      setFinalSummary({ modules: finalModules, totalDurationMs })
    }, 1500)

    // persist to DB
    const modulesSummary = finalModules
      .filter(m => m.status !== 'idle')
      .map(m => ({
        id: m.id,
        label: m.label,
        status: m.status as 'passed' | 'failed',
        passed: m.passed,
        failed: m.failed,
        durationMs: m.durationMs,
        log: acc[m.id].log,
      }))

    saveDeploymentRun(modulesSummary, totalDurationMs)
  }, [updateResult, erpToken, erpTenantId, erpEmail, erpPassword])

  const totalPassed  = Object.values(results).filter(r => r.status === 'passed').length
  const totalFailed  = Object.values(results).filter(r => r.status === 'failed').length
  const totalDone    = totalPassed + totalFailed
  const totalModules = SMOKE_MODULES.length

  return (
    <div className="flex flex-col flex-1 min-h-0 h-full">
      {/* Per-module toast — fixed top-right, one at a time */}
      {toast && (
        <div className="fixed top-5 right-5 z-[200] pointer-events-none flex flex-col items-end">
          <div className="pointer-events-auto">
            <ModuleToast key={toast.id + toast.durationMs} data={toast} onDismiss={() => setToast(null)} />
          </div>
        </div>
      )}

      {/* Final summary dialog */}
      {finalSummary && (
        <FinalSummaryDialog
          modules={finalSummary.modules}
          totalDurationMs={finalSummary.totalDurationMs}
          onClose={() => setFinalSummary(null)}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between px-6 pt-6 pb-4 shrink-0">
        <div className="flex items-center gap-3">
          <Rocket className="w-6 h-6 text-indigo-500" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Deployment Check</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">Runs one smoke test per module to verify nothing broke after a deployment</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <CredentialDropdown
            credentials={credentials}
            activeCredId={localCredId}
            onSelectCred={setLocalCredId}
          />
          {activeTab === 'run' && (
            <>
              {done && (
                <Button variant="outline" size="sm" onClick={reset} className="gap-1.5">
                  <RotateCcw className="w-3.5 h-3.5" /> Reset
                </Button>
              )}
              <Button
                onClick={runAll}
                disabled={running || !activeCred}
                title={!activeCred ? 'Select a credential first' : undefined}
                className="gap-2 bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50"
              >
                {running
                  ? <><Loader2 className="w-4 h-4 animate-spin" /> Running ({totalDone}/{totalModules})</>
                  : <><Rocket className="w-4 h-4" /> Run Deployment Check</>
                }
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Tab bar */}
      <div className="border-b border-gray-200 dark:border-gray-700 px-6 shrink-0">
        <div className="flex gap-0">
          {([
            { id: 'run' as const,     label: 'Run',     icon: Rocket },
            { id: 'history' as const, label: 'History', icon: History },
          ] as const).map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-1.5 px-4 h-9 text-[12px] font-medium transition-colors border-b-2 cursor-pointer ${
                activeTab === id
                  ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400 bg-white dark:bg-transparent'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex flex-col flex-1 min-h-0 px-6 pt-4">

        {/* ── RUN TAB ── */}
        {activeTab === 'run' && (
          <>
            {/* Summary bar */}
            {totalDone > 0 && (
              <div className="flex items-center gap-4 px-4 py-3 rounded-lg border bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-sm mb-4 shrink-0">
                <span className="text-gray-500 dark:text-gray-400">
                  Progress: <span className="font-medium text-gray-800 dark:text-gray-200">{totalDone}/{totalModules}</span>
                </span>
                <span className="text-green-600 dark:text-green-400 font-medium">✓ {totalPassed} passed</span>
                {totalFailed > 0 && <span className="text-red-600 dark:text-red-400 font-medium">✗ {totalFailed} failed</span>}
                {done && totalFailed === 0 && <span className="ml-auto text-green-600 dark:text-green-400 font-semibold">All systems go 🚀</span>}
                {done && totalFailed > 0  && <span className="ml-auto text-red-600 dark:text-red-400 font-semibold">{totalFailed} module{totalFailed > 1 ? 's' : ''} need attention</span>}
              </div>
            )}

            {/* Module grid */}
            <div className="flex-1 min-h-0 overflow-y-auto">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pb-4">
                {SMOKE_MODULES.map(mod => {
                  const r = results[mod.id]
                  return (
                    <div
                      key={mod.id}
                      className={`rounded-lg border p-4 transition-all duration-300 ${statusBg(r.status)}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{mod.label}</span>
                        <StatusIcon status={r.status} />
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-3">
                        {r.status === 'idle'    && <span>Waiting</span>}
                        {r.status === 'running' && <span className="text-blue-600 dark:text-blue-400">Running smoke test…</span>}
                        {(r.status === 'passed' || r.status === 'failed') && (
                          <>
                            <span>{r.passed} passed</span>
                            {r.failed > 0 && <span className="text-red-500">{r.failed} failed</span>}
                            <span className="ml-auto">{(r.durationMs / 1000).toFixed(1)}s</span>
                          </>
                        )}
                      </div>
                      {r.status === 'failed' && r.log.length > 0 && (
                        <div className="mt-2 text-xs font-mono text-red-700 dark:text-red-300 bg-red-100 dark:bg-red-950/50 rounded p-2 max-h-20 overflow-y-auto whitespace-pre-wrap break-all">
                          {r.log.slice(-5).join('\n')}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </>
        )}

        {/* ── HISTORY TAB ── */}
        {activeTab === 'history' && <HistoryTab />}
      </div>
    </div>
  )
}
