'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AlertTriangle, Play, Loader2, Key, X } from 'lucide-react'
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

function formatTime(d: Date): string {
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

function isValidToken(raw: string): boolean {
  const t = raw.startsWith('Bearer ') ? raw.slice(7) : raw
  return t.startsWith('eyJ') && t.split('.').length === 3 && t.length > 100
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

  if (/^PB \[\d+\] CREATED/.test(text)) return (
    <div className="flex gap-2 items-start text-emerald-600 dark:text-emerald-400">
      <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(ts)}]</span>
      <span className="text-[11px]">✓ {text}</span>
    </div>
  )

  if (/^PB \[\d+\] REJECTED/.test(text)) return (
    <div className="flex gap-2 items-start text-amber-600 dark:text-amber-400">
      <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(ts)}]</span>
      <span className="text-[11px]">— {text}</span>
    </div>
  )

  if (/^PB \[\d+\] ERROR/.test(text) || (text.includes('!!!') && text.includes('FAILED'))) return (
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
  const { token, tenantId, localToken, setLocalToken, localTenantId, setLocalTenantId, handleAuthError } = useErpToken(erpToken, erpTenantId)
  const [parallelCount, setParallelCount] = useState(3)
  const [running, setRunning] = useState(false)
  const [logs, setLogs] = useState<{ text: string; ts: Date; isErr: boolean; isDone: boolean }[]>([])
  const [showTokenInput, setShowTokenInput] = useState(!erpToken)
  const [duplicateDetected, setDuplicateDetected] = useState<boolean | null>(null)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const tokenSectionRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  useEffect(() => {
    if (showTokenInput) tokenSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [showTokenInput])

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
        if (!handleAuthError(err)) {
          setLogs(prev => [...prev, { text: `Error: ${err.message}`, ts: new Date(), isErr: true, isDone: false }])
        }
        setRunning(false)
      },
    )
  }, [token, tenantId, parallelCount, handleAuthError])

  const tokenValid = isValidToken(localToken)
  const tokenEntered = localToken.length > 0

  return (
    <div className="flex flex-col h-full min-h-0 gap-4 overflow-y-auto">
      <div className="bg-white dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex flex-col gap-4 shrink-0">

        {/* Description */}
        <div className="p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-[11px] text-amber-700 dark:text-amber-300 space-y-1">
          <p className="font-semibold">What this does</p>
          <p>Runs a full <span className="font-mono bg-amber-100 dark:bg-amber-900/40 px-1 rounded">PO → GP → GRN → QC</span> chain once, then fires <strong>N identical PB payloads simultaneously</strong> against the same QC/GRN/PO IDs.</p>
          <p>Expected: ERP should reject duplicates. If more than 1 PB is created, the ERP has no concurrency guard.</p>
        </div>

        {/* Token status + Set Token button */}
        <div className="flex items-center gap-3 flex-wrap">
          {token ? (
            <div className="flex items-center gap-2">
              <span className="inline-block size-2 rounded-full bg-green-500" />
              <span className="text-[11px] text-green-600 dark:text-green-400 font-medium">Token active</span>
              <span className="text-[10px] text-gray-400 dark:text-gray-500">· tenant {tenantId || '(none)'}</span>
              <button
                type="button"
                onClick={() => setShowTokenInput(v => !v)}
                className="ml-1 text-[10px] text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 underline cursor-pointer"
              >
                change
              </button>
              <button
                type="button"
                onClick={() => { setLocalToken(''); setLocalTenantId(''); onClearToken() }}
                className="text-[10px] text-red-500 hover:text-red-700 underline cursor-pointer"
              >
                clear
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setShowTokenInput(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 text-[12px] font-medium border border-orange-300 dark:border-orange-700 hover:bg-orange-200 dark:hover:bg-orange-900/50 cursor-pointer"
            >
              <Key className="size-3.5" />
              Set ERP Token
            </button>
          )}
        </div>

        {/* Inline token input */}
        {showTokenInput && (
          <div ref={tokenSectionRef} className="p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-[11px] text-orange-600 dark:text-orange-400 font-medium">ERP Credentials</Label>
              <button type="button" onClick={() => setShowTokenInput(false)} className="text-gray-400 hover:text-gray-600 cursor-pointer">
                <X className="size-3.5" />
              </button>
            </div>

            {/* Token field */}
            <Input
              type="text"
              value={localToken}
              onChange={e => setLocalToken(e.target.value)}
              placeholder="Paste your Bearer token (eyJ…)"
              autoComplete="off"
              style={{ WebkitTextSecurity: 'disc' } as React.CSSProperties}
              className={`h-9 text-[12px] ${tokenEntered ? (tokenValid ? 'border-green-400' : 'border-red-400') : ''}`}
            />

            {/* Token validation feedback */}
            {tokenEntered && !tokenValid && (
              <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-2.5 space-y-1.5">
                <div className="flex items-center gap-1.5">
                  <AlertTriangle className="size-3 text-red-500 shrink-0" />
                  <span className="text-[11px] font-semibold text-red-600 dark:text-red-400">
                    {!localToken.replace('Bearer ', '').startsWith('eyJ') ? 'Token must start with eyJ…' : 'Token format looks incorrect'}
                  </span>
                </div>
                <p className="text-[11px] text-red-500 dark:text-red-400">
                  Copy from DevTools → Network → any request → Authorization header.
                </p>
                <div className="rounded bg-gray-900 p-2">
                  <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">Should look like</p>
                  <p className="text-[10px] text-yellow-300 break-all leading-relaxed">
                    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.<span className="text-blue-300">eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiw…</span>.<span className="text-pink-300">SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV</span>
                  </p>
                </div>
              </div>
            )}
            {tokenEntered && tokenValid && (
              <p className="text-[11px] text-green-600 dark:text-green-400 flex items-center gap-1">
                <span className="inline-block size-2 rounded-full bg-green-500" />
                Token looks valid
              </p>
            )}

            {/* Tenant quick-select */}
            <div className="flex flex-wrap gap-1.5">
              {KNOWN_TENANTS.map(t => (
                <button
                  key={t.id}
                  onClick={() => setLocalTenantId(t.id)}
                  className={`px-2 py-0.5 rounded-full text-[11px] font-medium border transition-colors cursor-pointer ${
                    localTenantId === t.id
                      ? 'bg-orange-500 text-white border-orange-500'
                      : 'bg-white dark:bg-gray-800 text-orange-600 dark:text-orange-400 border-orange-300 dark:border-orange-700 hover:bg-orange-50 dark:hover:bg-orange-900/30'
                  }`}
                >
                  {t.id} · {t.name}
                </button>
              ))}
            </div>

            {/* Manual tenant + done */}
            <div className="flex items-center gap-2">
              <Input
                type="text"
                value={localTenantId}
                onChange={e => setLocalTenantId(e.target.value)}
                placeholder="Tenant ID (e.g. 708, 871)"
                autoComplete="off"
                className="h-9 text-[12px] w-48"
              />
              <Button
                onClick={() => setShowTokenInput(false)}
                variant="ghost"
                size="sm"
                className="h-9 text-[12px] cursor-pointer"
              >
                Done
              </Button>
            </div>
            <p className="text-[11px] text-orange-500 dark:text-orange-400">Credentials stay in your browser session only.</p>
          </div>
        )}

        {/* Controls row */}
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
            disabled={running || !token}
            className="h-9 bg-[#3F51B5] hover:bg-[#303F9F] text-white text-[12px] gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {running ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
            {running ? 'Running…' : `Run (${parallelCount}× PB simultaneous)`}
          </Button>
          {!token && (
            <span className="text-[11px] text-orange-500 dark:text-orange-400">Set ERP token first ↑</span>
          )}
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

      {/* Log panel */}
      {logs.length > 0 && (
        <div className="flex-1 min-h-[200px] bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg flex flex-col overflow-hidden">
          <div className="px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 shrink-0 flex items-center gap-2">
            <span className="text-[11px] font-medium text-gray-600 dark:text-gray-300">Run log</span>
            {running && <span className="text-[10px] text-[#3F51B5] dark:text-[#7986CB] animate-pulse">● live</span>}
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
