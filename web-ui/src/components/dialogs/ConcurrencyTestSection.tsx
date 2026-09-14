'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AlertTriangle, Play, Loader2 } from 'lucide-react'
import { startPbConcurrencyTest, type SSEEvent } from '@/lib/api'
import { useErpToken } from '@/hooks/useErpToken'

interface Props {
  erpToken: string
  erpTenantId: string
  onNeedsToken: () => void
  onClearToken: () => void
}

function formatTime(d: Date): string {
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

function LogLine({ log }: { log: { text: string; ts: Date; isErr: boolean; isDone: boolean } }) {
  const { text, ts, isErr, isDone } = log

  if (isErr) return (
    <div className="flex gap-2 items-start text-red-500 dark:text-red-400">
      <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(ts)}]</span>
      <span className="text-[11px] whitespace-pre-wrap break-all">✕ {text}</span>
    </div>
  )

  if (isDone) {
    const isDup = text.includes('DUPLICATE')
    return (
      <div className={`flex gap-2 items-start font-semibold ${isDup ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
        <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(ts)}]</span>
        <span className="text-[11px]">{isDup ? '⚠' : '✓'} {text}</span>
      </div>
    )
  }

  const isPbCreated  = /^PB \[\d+\] CREATED/.test(text)
  const isPbRejected = /^PB \[\d+\] REJECTED/.test(text)
  const isPbError    = /^PB \[\d+\] ERROR/.test(text)
  const isAcctFail   = text.includes('!!!') && text.includes('FAILED')

  if (isPbCreated) return (
    <div className="flex gap-2 items-start text-emerald-600 dark:text-emerald-400">
      <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(ts)}]</span>
      <span className="text-[11px]">✓ {text}</span>
    </div>
  )

  if (isPbRejected) return (
    <div className="flex gap-2 items-start text-amber-600 dark:text-amber-400">
      <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(ts)}]</span>
      <span className="text-[11px]">— {text}</span>
    </div>
  )

  if (isPbError || isAcctFail) return (
    <div className="flex gap-2 items-start text-red-500 dark:text-red-400">
      <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(ts)}]</span>
      <span className="text-[11px]">{text}</span>
    </div>
  )

  return (
    <div className="flex gap-2 items-start">
      <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(ts)}]</span>
      <span className="text-[11px] text-gray-700 dark:text-gray-200 whitespace-pre-wrap break-all">{text}</span>
    </div>
  )
}

export function ConcurrencyTestSection({ erpToken, erpTenantId, onNeedsToken, onClearToken }: Props) {
  const { token, tenantId, localToken, setLocalToken, localTenantId, setLocalTenantId } = useErpToken(erpToken, erpTenantId)
  const [parallelCount, setParallelCount] = useState(3)
  const [running, setRunning] = useState(false)
  const [logs, setLogs] = useState<{ text: string; ts: Date; isErr: boolean; isDone: boolean }[]>([])
  const [showTokenInput, setShowTokenInput] = useState(false)
  const [duplicateDetected, setDuplicateDetected] = useState<boolean | null>(null)
  const logsEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const handleRun = useCallback(() => {
    if (!token) { setShowTokenInput(true); return }
    setRunning(true)
    setLogs([])
    setDuplicateDetected(null)

    startPbConcurrencyTest(
      token,
      tenantId || '681',
      parallelCount,
      (event: SSEEvent) => {
        setLogs(prev => [...prev, {
          text: event.message,
          ts: new Date(),
          isErr: event.type === 'error',
          isDone: event.type === 'run_end',
        }])
        if (event.type === 'run_end') {
          setRunning(false)
          setDuplicateDetected((event.created ?? 0) > 1)
        }
      },
      () => setRunning(false),
      (err) => {
        setLogs(prev => [...prev, { text: `Error: ${err.message}`, ts: new Date(), isErr: true, isDone: false }])
        setRunning(false)
      },
    )
  }, [token, tenantId, parallelCount])

  return (
    <div className="flex flex-col h-full min-h-0 gap-4">
      <div className="bg-white dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex flex-col gap-4">

        {/* Header description */}
        <div className="p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-[11px] text-amber-700 dark:text-amber-300 space-y-1">
          <p className="font-semibold">What this does</p>
          <p>Runs a full <span className="font-mono bg-amber-100 dark:bg-amber-900/40 px-1 rounded">PO → GP → GRN → QC</span> chain once, then fires <strong>N identical PB payloads simultaneously</strong> against the same QC/GRN/PO IDs.</p>
          <p>Expected behaviour: ERP should reject duplicates. If more than 1 PB is created, the ERP has no duplicate protection.</p>
        </div>

        {/* Controls */}
        <div className="flex items-end gap-4 flex-wrap">
          <div className="flex flex-col gap-1">
            <Label className="text-[11px] text-gray-600 dark:text-gray-400">Parallel PB submissions</Label>
            <Input
              type="number"
              min={2}
              max={10}
              value={parallelCount}
              onChange={e => setParallelCount(Math.max(2, Math.min(10, parseInt(e.target.value) || 3)))}
              disabled={running}
              className="h-9 w-24 text-[12px]"
            />
          </div>
          <Button
            onClick={handleRun}
            disabled={running}
            className="h-9 bg-[#3F51B5] hover:bg-[#303F9F] text-white text-[12px] gap-2 cursor-pointer"
          >
            {running ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
            {running ? 'Running…' : `Run (${parallelCount}× PB)`}
          </Button>
        </div>

        {/* Token input (inline) */}
        {showTokenInput && (
          <div className="p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg space-y-2">
            <Label className="text-[11px] text-orange-600 dark:text-orange-400 font-medium">ERP Token</Label>
            <Input
              type="text"
              value={localToken}
              onChange={e => setLocalToken(e.target.value)}
              placeholder="Paste Bearer token (eyJ…)"
              autoComplete="off"
              style={{ WebkitTextSecurity: 'disc' } as React.CSSProperties}
              className="h-9 text-[12px]"
            />
            <div className="flex items-center gap-2">
              <Input
                type="text"
                value={localTenantId}
                onChange={e => setLocalTenantId(e.target.value)}
                placeholder="Tenant ID"
                className="h-9 text-[12px] w-32"
              />
              <Button size="sm" variant="ghost" onClick={() => setShowTokenInput(false)} className="h-9 text-[12px] cursor-pointer">
                Done
              </Button>
            </div>
          </div>
        )}

        {/* Duplicate detection banner */}
        {duplicateDetected === true && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-lg flex items-start gap-2">
            <AlertTriangle className="size-4 text-red-500 shrink-0 mt-0.5" />
            <div className="text-[12px] text-red-700 dark:text-red-300">
              <p className="font-semibold">Duplicate PBs created — ERP has no concurrency guard</p>
              <p className="text-[11px] mt-0.5">Multiple Purchase Bookings were accepted for the same QC/GRN/PO. The accounting ledger has been posted multiple times.</p>
            </div>
          </div>
        )}
        {duplicateDetected === false && (
          <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-300 dark:border-emerald-700 rounded-lg text-[12px] text-emerald-700 dark:text-emerald-300">
            ✓ ERP correctly rejected duplicate PBs — only 1 booking was created.
          </div>
        )}
      </div>

      {/* Log panel */}
      {logs.length > 0 && (
        <div className="flex-1 min-h-0 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg flex flex-col overflow-hidden">
          <div className="px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 shrink-0">
            <span className="text-[11px] font-medium text-gray-600 dark:text-gray-300">Run log</span>
            {running && <span className="ml-2 text-[10px] text-[#3F51B5] dark:text-[#7986CB] animate-pulse">● live</span>}
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-0.5 font-mono">
            {logs.map((log, i) => <LogLine key={i} log={log} />)}
            <div ref={logsEndRef} />
          </div>
        </div>
      )}
    </div>
  )
}
