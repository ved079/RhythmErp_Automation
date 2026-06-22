'use client'

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import {
  ArrowLeft, Globe, Play, Square, RotateCcw, CheckCircle2,
  XCircle, Circle, Loader2, ClipboardList, Monitor, Maximize2, X,
  Terminal, Search, ChevronDown, ChevronRight, Clock, Copy, Check,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { type TestClassGroup, type TestItem } from '@/data/testSpecGroups'
import type { ScreenshotEntry } from '@/components/screenshot/ScreenshotGallery'
import { LiveScreencast } from './LiveScreencast'

// ── Helpers ──────────────────────────────────────────────────────

function formatElapsed(s: number) {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return m > 0 ? `${m}m ${sec}s` : `${sec}s`
}

function getTestShortName(test: TestItem, showRaw: boolean): string {
  if (showRaw) return test.id.split('::').pop() ?? test.id
  return test.name
}

function classLabelFromId(id: string): string {
  const parts = id.split('::')
  if (parts.length >= 3) {
    // e.g. "TestCreateForm" → "Create Form"
    return (parts[parts.length - 2] ?? '')
      .replace(/^Test/, '')
      .replace(/([A-Z])/g, ' $1')
      .trim()
  }
  return ''
}

// ── Status icon ───────────────────────────────────────────────────

function StatusIcon({ status, size = 'size-3.5' }: { status: TestItem['status']; size?: string }) {
  if (status === 'passed') return <CheckCircle2 className={`${size} text-emerald-400 shrink-0`} />
  if (status === 'failed') return <XCircle className={`${size} text-red-400 shrink-0`} />
  if (status === 'running') return <Loader2 className={`${size} text-[#7986CB] animate-spin shrink-0`} />
  return <Circle className={`${size} text-slate-700 shrink-0`} />
}

// ── Split progress bar ────────────────────────────────────────────

function SplitBar({ passed, failed, total }: { passed: number; failed: number; total: number }) {
  if (total === 0) return <div className="h-1.5 rounded-full bg-slate-800" />
  const passW = Math.round((passed / total) * 100)
  const failW = Math.round((failed / total) * 100)
  return (
    <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden flex gap-px">
      {passW > 0 && <div className="h-full bg-emerald-500 transition-all duration-500 rounded-l-full" style={{ width: `${passW}%` }} />}
      {failW > 0 && <div className="h-full bg-red-500 transition-all duration-500" style={{ width: `${failW}%` }} />}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────

export function LiveExecutionTab({
  tests,
  testGroups,
  isRunning,
  runningProgress,
  consoleLogs,
  showRawNames,
  onStop,
  onBack,
  onRerunFailed,
  onScreenshotCaptured,
}: {
  tests: TestItem[]
  testGroups: TestClassGroup[]
  isRunning: boolean
  runningProgress: string
  consoleLogs?: string[]
  showRawNames?: boolean
  onStop: () => void
  onBack: () => void
  onRerunFailed: () => void
  onScreenshotCaptured?: (entry: ScreenshotEntry) => void
}) {
  // ── Console state ─────────────────────────────────────────────
  const consoleEndRef = useRef<HTMLDivElement>(null)
  const lastProgressRef = useRef<string>('')
  const [consoleLines, setConsoleLines] = useState<string[]>([])
  const [consoleOpen, setConsoleOpen] = useState(false)
  const [consoleTab, setConsoleTab] = useState<'live' | 'log'>('live')
  const [autoScroll, setAutoScroll] = useState(true)
  const [consoleSearch, setConsoleSearch] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const [copied, setCopied] = useState(false)

  // ── Elapsed timers ────────────────────────────────────────────
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const elapsedIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const [testElapsed, setTestElapsed] = useState(0)
  const testStartTimeRef = useRef<number | null>(null)
  const testElapsedIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // ── Test errors captured from console stream ─────────────────
  const lastRunningIdRef = useRef<string | null>(null)
  const [testErrors, setTestErrors] = useState<Record<string, string>>({})

  // ── Expanded failed row ───────────────────────────────────────
  const [expandedFailId, setExpandedFailId] = useState<string | null>(null)

  // ── TV popup ──────────────────────────────────────────────────
  const [tvPopupOpen, setTvPopupOpen] = useState(false)
  const [tvImgSrc, setTvImgSrc] = useState<string>('')

  // ── Derived counts ────────────────────────────────────────────
  const runningTest = tests.find(t => t.status === 'running')
  const passedCount = tests.filter(t => t.status === 'passed').length
  const failedCount = tests.filter(t => t.status === 'failed').length
  const completedCount = passedCount + failedCount
  const progressPercent = tests.length > 0 ? Math.round((completedCount / tests.length) * 100) : 0

  // ── Effects ───────────────────────────────────────────────────

  // Run elapsed timer
  useEffect(() => {
    if (isRunning) {
      setElapsedSeconds(0)
      elapsedIntervalRef.current = setInterval(() => setElapsedSeconds(s => s + 1), 1000)
    } else {
      if (elapsedIntervalRef.current) clearInterval(elapsedIntervalRef.current)
    }
    return () => { if (elapsedIntervalRef.current) clearInterval(elapsedIntervalRef.current) }
  }, [isRunning])

  // Per-test elapsed timer — resets when running test changes
  useEffect(() => {
    if (elapsedIntervalRef.current) clearInterval(testElapsedIntervalRef.current!)
    if (runningTest) {
      testStartTimeRef.current = Date.now()
      setTestElapsed(0)
      testElapsedIntervalRef.current = setInterval(() => {
        setTestElapsed(Math.floor((Date.now() - (testStartTimeRef.current ?? Date.now())) / 1000))
      }, 200)
    }
    return () => { if (testElapsedIntervalRef.current) clearInterval(testElapsedIntervalRef.current) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runningTest?.id])

  // Track last running test id for error capture
  useEffect(() => {
    if (runningTest) lastRunningIdRef.current = runningTest.id
  }, [runningTest])

  // Append console lines + capture errors
  useEffect(() => {
    if (!runningProgress || runningProgress === lastProgressRef.current) return
    lastProgressRef.current = runningProgress
    setConsoleLines(prev => [...prev, runningProgress])
    if (runningProgress.includes('FAILED') || runningProgress.includes('ERROR')) {
      const targetId = lastRunningIdRef.current
      if (targetId) {
        setTestErrors(prev => ({ ...prev, [targetId]: runningProgress }))
      }
    }
  }, [runningProgress])

  // Auto-scroll
  useEffect(() => {
    if (autoScroll && consoleOpen) {
      consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [consoleLines.length, autoScroll, consoleOpen])

  // Escape closes TV popup
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') setTvPopupOpen(false) }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // Screenshot handler
  const handleScreenshotReady = useCallback((src: string, active: boolean) => {
    setTvImgSrc(src)
    if (active && src && onScreenshotCaptured) {
      onScreenshotCaptured({
        id: `ss-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        src,
        testName: runningTest?.name ?? 'Live Execution',
        timestamp: new Date().toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        moduleName: undefined,
        status: runningTest?.status === 'failed' ? 'failed' : 'passed',
      })
    }
  }, [onScreenshotCaptured, runningTest])

  // ── Test list grouping ─────────────────────────────────────────
  const groupedTests = useMemo(() => {
    const map = new Map<string, TestItem[]>()
    for (const t of tests) {
      const label = classLabelFromId(t.id) || 'Tests'
      if (!map.has(label)) map.set(label, [])
      map.get(label)!.push(t)
    }
    return Array.from(map.entries()).map(([label, items]) => ({ label, items }))
  }, [tests])

  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())
  const toggleGroup = useCallback((label: string) => {
    setCollapsedGroups(prev => {
      const next = new Set(prev)
      next.has(label) ? next.delete(label) : next.add(label)
      return next
    })
  }, [])

  // ── Console filtered ──────────────────────────────────────────
  const activeLines = consoleTab === 'log' ? (consoleLogs ?? []) : consoleLines
  const displayLines = useMemo(() => {
    if (!consoleSearch.trim()) return activeLines
    const q = consoleSearch.toLowerCase()
    return activeLines.filter(l => l.toLowerCase().includes(q))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeLines, consoleSearch])

  // ── Render ────────────────────────────────────────────────────
  return (
    <>
      <div className="flex flex-col h-full min-h-0 overflow-hidden bg-[#0f1117]">

        {/* ── TOP BAR ─────────────────────────────────────────── */}
        <div className="flex items-center gap-2 px-3 py-2 border-b border-white/[0.07] bg-[#151929] shrink-0">
          <Button variant="ghost" onClick={onBack}
            className="h-7 text-[12px] gap-1.5 text-slate-400 hover:text-white hover:bg-white/[0.06] cursor-pointer px-2.5 rounded-md shrink-0"
          >
            <ArrowLeft className="size-3.5" />
            Runner
          </Button>

          <div className="w-px h-4 bg-white/[0.08] shrink-0" />

          {isRunning ? (
            <>
              {/* Elapsed */}
              <span className="flex items-center gap-1.5 text-[12px] font-mono tabular-nums text-slate-400 shrink-0">
                <Clock className="size-3 text-slate-600" />
                {formatElapsed(elapsedSeconds)}
              </span>

              <div className="w-px h-4 bg-white/[0.08] shrink-0" />

              {/* Progress bar */}
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <div className="flex-1 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div className="h-full rounded-full bg-gradient-to-r from-[#3F51B5] to-emerald-500 transition-all duration-300"
                    style={{ width: `${progressPercent}%` }} />
                </div>
                <span className="text-[12px] font-mono tabular-nums text-slate-400 shrink-0">
                  {completedCount}<span className="text-slate-600">/</span>{tests.length}
                </span>
              </div>

              {/* Running test name */}
              {runningTest && (
                <>
                  <div className="w-px h-4 bg-white/[0.08] shrink-0" />
                  <span className="text-[12px] text-slate-400 truncate max-w-[200px] shrink-0 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#7986CB] animate-pulse shrink-0" />
                    <span className="truncate">{getTestShortName(runningTest, showRawNames ?? false)}</span>
                  </span>
                </>
              )}

              <Button onClick={onStop}
                className="ml-2 bg-red-500/90 hover:bg-red-500 text-white h-7 text-[12px] gap-1.5 cursor-pointer rounded-md shadow-md shadow-red-500/20 shrink-0"
              >
                <Square className="size-3" />
                Stop
              </Button>
            </>
          ) : completedCount > 0 ? (
            <>
              <span className="text-[12px] text-slate-400 shrink-0">
                Done in <span className="font-mono text-slate-300">{formatElapsed(elapsedSeconds)}</span>
                {' — '}
                <span className="text-emerald-400 font-semibold">{passedCount} passed</span>
                {failedCount > 0 && <><span className="text-slate-600">, </span><span className="text-red-400 font-semibold">{failedCount} failed</span></>}
              </span>
              <div className="flex-1" />
              {failedCount > 0 && (
                <Button onClick={onRerunFailed}
                  className="bg-amber-500/90 hover:bg-amber-500 text-white h-7 text-[12px] gap-1.5 cursor-pointer rounded-md shadow-md shadow-amber-500/20 shrink-0"
                >
                  <RotateCcw className="size-3" />
                  Rerun Failed ({failedCount})
                </Button>
              )}
              <Button onClick={onBack}
                className="bg-[#3F51B5]/90 hover:bg-[#3F51B5] text-white h-7 text-[12px] gap-1.5 cursor-pointer rounded-md shrink-0"
              >
                <RotateCcw className="size-3" />
                New Run
              </Button>
            </>
          ) : (
            <span className="text-[12px] text-slate-600">Select tests and click Run to start</span>
          )}

          {/* Pass / fail pills + console button */}
          <div className="flex items-center gap-1.5 ml-auto shrink-0">
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[11px] font-mono tabular-nums">
              <CheckCircle2 className="size-3" /> {passedCount}
            </span>
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 text-[11px] font-mono tabular-nums">
              <XCircle className="size-3" /> {failedCount}
            </span>
            <div className="w-px h-4 bg-white/[0.08] mx-1" />
            <button
              onClick={() => setConsoleOpen(o => !o)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[12px] transition-colors cursor-pointer ${
                consoleOpen
                  ? 'bg-[#3F51B5]/30 text-[#9FA8DA] border border-[#3F51B5]/40'
                  : 'text-slate-500 hover:text-slate-200 hover:bg-white/[0.06] border border-transparent'
              }`}
            >
              <Terminal className="size-3.5" />
              Console
              {consoleLines.length > 0 && (
                <span className="text-[10px] font-mono tabular-nums opacity-70">{consoleLines.length}</span>
              )}
            </button>
          </div>
        </div>

        {/* ── MAIN CONTENT ────────────────────────────────────── */}
        <div className="flex-1 overflow-hidden flex min-h-0">
          <div className="flex gap-3 px-3 pt-3 pb-2 flex-1 min-h-0 min-w-0">

            {/* ── TEST LIST (always visible) ─────────────────── */}
            <div className="w-60 shrink-0 flex flex-col rounded-xl bg-[#0d1117] border border-white/[0.07] overflow-hidden">

              {/* List header */}
              <div className="px-3 pt-3 pb-2.5 border-b border-white/[0.06] shrink-0">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    <ClipboardList className="size-3.5 text-[#5C6BC0]" />
                    <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-widest">Tests</span>
                  </div>
                  <span className="text-[11px] font-mono tabular-nums text-slate-600">
                    {completedCount}<span className="text-slate-700">/</span>{tests.length}
                  </span>
                </div>
                <SplitBar passed={passedCount} failed={failedCount} total={tests.length} />
                <div className="flex items-center gap-3 mt-2">
                  <span className="flex items-center gap-1 text-[10px] text-emerald-400/70 font-mono tabular-nums">
                    <CheckCircle2 className="size-2.5" />{passedCount}
                  </span>
                  <span className="flex items-center gap-1 text-[10px] text-red-400/70 font-mono tabular-nums">
                    <XCircle className="size-2.5" />{failedCount}
                  </span>
                  <span className="flex items-center gap-1 text-[10px] text-slate-700 font-mono tabular-nums ml-auto">
                    <Circle className="size-2.5" />{tests.filter(t => t.status === 'pending').length}
                  </span>
                </div>
              </div>

              {/* Test rows */}
              <div className="flex-1 overflow-auto">
                {groupedTests.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full gap-2 pb-4">
                    <Play className="size-6 text-slate-800" />
                    <p className="text-[11px] text-slate-700 text-center px-4">No tests selected.<br />Go to Test Runner to select.</p>
                  </div>
                ) : groupedTests.map(({ label, items }) => {
                  const isCollapsed = collapsedGroups.has(label)
                  const groupPassed = items.filter(t => t.status === 'passed').length
                  const groupFailed = items.filter(t => t.status === 'failed').length
                  const hasRunning = items.some(t => t.status === 'running')
                  return (
                    <div key={label}>
                      {/* Group header — only show if more than one group */}
                      {groupedTests.length > 1 && (
                        <button onClick={() => toggleGroup(label)}
                          className="w-full flex items-center gap-1.5 px-3 py-1.5 text-left hover:bg-white/[0.03] transition-colors cursor-pointer border-b border-white/[0.04] group"
                        >
                          {isCollapsed
                            ? <ChevronRight className="size-3 text-slate-600 shrink-0" />
                            : <ChevronDown className="size-3 text-slate-600 shrink-0" />}
                          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider truncate flex-1">
                            {label}
                          </span>
                          {hasRunning && <span className="w-1.5 h-1.5 rounded-full bg-[#7986CB] animate-pulse shrink-0" />}
                          <span className="text-[10px] font-mono text-slate-700 shrink-0 tabular-nums">{groupPassed}/{items.length}</span>
                        </button>
                      )}

                      {/* Test rows */}
                      {!isCollapsed && items.map((test, idx) => {
                        const isExpanded = expandedFailId === test.id
                        const error = testErrors[test.id]
                        return (
                          <div key={test.id}>
                            <div
                              onClick={() => test.status === 'failed' ? setExpandedFailId(isExpanded ? null : test.id) : undefined}
                              className={`flex items-center gap-2 px-3 py-1.5 border-b border-white/[0.025] text-[11.5px] transition-all ${
                                test.status === 'running'
                                  ? 'bg-[#3F51B5]/[0.14] border-l-[2px] border-l-[#5C6BC0]'
                                  : test.status === 'failed'
                                    ? `bg-red-500/[0.05] ${isExpanded ? '' : 'cursor-pointer hover:bg-red-500/[0.08]'}`
                                    : test.status === 'passed'
                                      ? 'opacity-50 hover:opacity-75'
                                      : 'cursor-default'
                              }`}
                            >
                              <StatusIcon status={test.status} />
                              <span className={`flex-1 truncate font-mono leading-tight ${
                                test.status === 'running' ? 'text-slate-100' :
                                test.status === 'passed' ? 'text-slate-500' :
                                test.status === 'failed' ? 'text-red-300/90' :
                                'text-slate-600'
                              }`}>
                                {getTestShortName(test, showRawNames ?? false)}
                              </span>
                              {test.status === 'running' && (
                                <span className="text-[10px] font-mono tabular-nums text-[#7986CB] shrink-0">
                                  {testElapsed}s
                                </span>
                              )}
                              {test.status !== 'running' && test.duration && (
                                <span className="text-[10px] font-mono tabular-nums text-slate-700 shrink-0">
                                  {test.duration}
                                </span>
                              )}
                              {test.status === 'pending' && (
                                <span className="text-[10px] font-mono text-slate-800 shrink-0">
                                  #{idx + 1}
                                </span>
                              )}
                              {test.status === 'failed' && (
                                <ChevronDown className={`size-3 text-slate-600 shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                              )}
                            </div>

                            {/* Expanded error */}
                            {isExpanded && (
                              <div className="px-3 py-2.5 bg-red-950/20 border-b border-red-900/20 border-l-[2px] border-l-red-500/40">
                                {error ? (
                                  <pre className="text-[10.5px] font-mono text-red-300/80 whitespace-pre-wrap leading-relaxed max-h-28 overflow-auto">
                                    {error.replace(/^.*?FAILED.*?:\s*/i, '')}
                                  </pre>
                                ) : (
                                  <p className="text-[10.5px] text-slate-600 italic">No error captured — check console output.</p>
                                )}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* ── BROWSER VIEW ──────────────────────────────── */}
            <div className="flex-1 min-w-0 flex flex-col">
              <div className="flex-1 min-h-0 rounded-xl border border-white/[0.08] overflow-hidden flex flex-col bg-[#0d1117] shadow-2xl shadow-black/40">

                {/* Chrome bar */}
                <div className="bg-[#161b22] px-3 py-2 flex items-center gap-3 shrink-0 border-b border-white/[0.05]">
                  <div className="flex items-center gap-1.5 shrink-0">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
                    <div className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
                    <div className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
                  </div>
                  <div className="flex-1 flex items-center justify-center">
                    <div className="bg-slate-900/80 rounded-md px-3 py-1 flex items-center gap-1.5 text-[11px] text-slate-500 border border-white/[0.05] max-w-sm w-full">
                      <Globe className="size-3 text-slate-600 shrink-0" />
                      <span className="truncate text-center">
                        {isRunning && runningTest
                          ? `rhythmerp.com — ${getTestShortName(runningTest, showRawNames ?? false)}`
                          : 'rhythmerp.com'}
                      </span>
                    </div>
                  </div>
                  {isRunning && runningTest && (
                    <button onClick={() => setTvPopupOpen(true)}
                      className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-slate-500 hover:text-slate-200 hover:bg-white/[0.06] transition-colors cursor-pointer shrink-0"
                    >
                      <Monitor className="size-3.5" />
                      <Maximize2 className="size-2.5" />
                    </button>
                  )}
                </div>

                {/* Browser content */}
                <div className="flex-1 overflow-hidden relative bg-slate-950">
                  {isRunning && runningTest ? (
                    <LiveScreencast isRunning={isRunning} onScreenshotReady={handleScreenshotReady} />
                  ) : completedCount > 0 ? (
                    /* ── Completion screen ── */
                    <div className="w-full h-full flex flex-col items-center justify-center gap-6 p-8">
                      {/* Icon */}
                      <div className={`w-16 h-16 rounded-2xl flex items-center justify-center ring-1 ${
                        failedCount === 0
                          ? 'bg-emerald-500/10 ring-emerald-500/20'
                          : 'bg-red-500/10 ring-red-500/20'
                      }`}>
                        {failedCount === 0
                          ? <CheckCircle2 className="size-8 text-emerald-400" />
                          : <div className="flex gap-1.5"><XCircle className="size-7 text-red-400" /><CheckCircle2 className="size-7 text-emerald-400" /></div>
                        }
                      </div>

                      {/* Stats */}
                      <div className="text-center">
                        <p className="text-[18px] font-semibold text-slate-100">
                          {failedCount === 0 ? 'All tests passed' : 'Run complete'}
                        </p>
                        <p className="text-[13px] text-slate-500 mt-1">
                          <span className="text-emerald-400 font-semibold">{passedCount} passed</span>
                          {failedCount > 0 && <><span className="text-slate-600">, </span><span className="text-red-400 font-semibold">{failedCount} failed</span></>}
                          <span className="text-slate-600"> · {tests.length} total · {formatElapsed(elapsedSeconds)}</span>
                        </p>
                      </div>

                      {/* Split progress bar */}
                      <div className="w-64">
                        <SplitBar passed={passedCount} failed={failedCount} total={tests.length} />
                        <div className="flex justify-between mt-1.5 text-[10px] font-mono text-slate-600">
                          <span>{progressPercent}% passed</span>
                          {failedCount > 0 && <span className="text-red-500/70">{Math.round((failedCount / tests.length) * 100)}% failed</span>}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2">
                        {failedCount > 0 && (
                          <Button onClick={onRerunFailed}
                            className="bg-amber-500/90 hover:bg-amber-500 text-white h-8 text-[12px] gap-1.5 cursor-pointer rounded-lg shadow-lg shadow-amber-500/20"
                          >
                            <RotateCcw className="size-3.5" />
                            Rerun Failed ({failedCount})
                          </Button>
                        )}
                        <Button onClick={onBack}
                          className="bg-slate-700 hover:bg-slate-600 text-white h-8 text-[12px] gap-1.5 cursor-pointer rounded-lg"
                        >
                          <ArrowLeft className="size-3.5" />
                          Back to Runner
                        </Button>
                      </div>
                    </div>
                  ) : (
                    /* ── Idle / no run ── */
                    <div className="w-full h-full flex flex-col items-center justify-center gap-3">
                      <div className="w-14 h-14 rounded-full bg-slate-900 flex items-center justify-center border border-white/[0.05]">
                        <Play className="size-6 text-slate-700 ml-0.5" />
                      </div>
                      <p className="text-[13px] text-slate-600">No test running</p>
                      <p className="text-[11px] text-slate-700">Select tests in Test Runner and click Run</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* ── CONSOLE POPUP ───────────────────────────────────────── */}
      {consoleOpen && (
        <div className="fixed inset-0 z-[9998] flex items-end justify-center pb-6 px-6 pointer-events-none">
          {/* Backdrop — only the panel itself captures clicks */}
          <div className="absolute inset-0 bg-black/40 pointer-events-auto" onClick={() => setConsoleOpen(false)} />

          <div className="relative pointer-events-auto w-full max-w-4xl h-[60vh] min-h-[340px] flex flex-col rounded-2xl overflow-hidden border border-white/[0.1] shadow-2xl shadow-black/60"
            style={{ background: '#0d1117' }}
          >
            {/* Header */}
            <div className="flex items-center gap-2 px-4 border-b border-white/[0.07] bg-[#10151c] shrink-0">
              {/* Tab switcher */}
              <Terminal className="size-4 text-[#7986CB] shrink-0 my-2.5" />
              <div className="flex items-center gap-0.5 my-2">
                {([
                  { id: 'live', label: 'SSE Stream', count: consoleLines.length },
                  { id: 'log', label: 'Run Log', count: consoleLogs?.length ?? 0 },
                ] as const).map(tab => (
                  <button key={tab.id}
                    onClick={() => { setConsoleTab(tab.id); setConsoleSearch('') }}
                    className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-[12px] font-medium transition-colors cursor-pointer ${
                      consoleTab === tab.id
                        ? 'bg-[#3F51B5]/30 text-[#9FA8DA]'
                        : 'text-slate-500 hover:text-slate-300 hover:bg-white/[0.05]'
                    }`}
                  >
                    {tab.label}
                    <span className={`text-[10px] font-mono tabular-nums px-1 rounded ${
                      consoleTab === tab.id ? 'text-[#7986CB]' : 'text-slate-700'
                    }`}>{tab.count}</span>
                  </button>
                ))}
              </div>

              <div className="flex-1" />

              {/* Search */}
              {showSearch ? (
                <div className="flex items-center gap-2 bg-slate-800/80 border border-white/[0.08] rounded-lg px-3 py-1">
                  <Search className="size-3.5 text-slate-500 shrink-0" />
                  <input
                    type="text" value={consoleSearch} onChange={e => setConsoleSearch(e.target.value)}
                    placeholder="filter lines…" autoFocus
                    className="w-36 bg-transparent text-[12px] text-slate-200 outline-none placeholder:text-slate-600 font-mono"
                  />
                  {consoleSearch && (
                    <span className="text-[11px] text-slate-500 font-mono tabular-nums shrink-0">{displayLines.length}</span>
                  )}
                  <button onClick={() => { setShowSearch(false); setConsoleSearch('') }}
                    className="text-slate-600 hover:text-slate-300 cursor-pointer shrink-0"
                  ><X className="size-3.5" /></button>
                </div>
              ) : (
                <button onClick={() => setShowSearch(true)}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-white/[0.06] transition-colors cursor-pointer"
                  title="Search output"
                ><Search className="size-4" /></button>
              )}

              {/* Auto-scroll toggle */}
              <button
                onClick={() => setAutoScroll(!autoScroll)}
                title={autoScroll ? 'Auto-scroll on' : 'Auto-scroll off'}
                className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
                  autoScroll ? 'text-[#7986CB] bg-[#3F51B5]/20' : 'text-slate-500 hover:text-slate-200 hover:bg-white/[0.06]'
                }`}
              ><ChevronDown className="size-4" /></button>

              {/* Clear */}
              <button onClick={() => setConsoleLines([])}
                className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                title="Clear console"
              >
                <svg className="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>

              {/* Copy */}
              <button
                onClick={() => {
                  navigator.clipboard.writeText(displayLines.join('\n')).then(() => {
                    setCopied(true)
                    setTimeout(() => setCopied(false), 2000)
                  })
                }}
                title="Copy all lines"
                className={`p-1.5 rounded-lg transition-colors cursor-pointer ${copied ? 'text-emerald-400 bg-emerald-500/10' : 'text-slate-500 hover:text-slate-200 hover:bg-white/[0.06]'}`}
              >
                {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
              </button>

              {/* Close */}
              <button onClick={() => setConsoleOpen(false)}
                className="p-1.5 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-white/[0.06] transition-colors cursor-pointer ml-1"
              ><X className="size-4" /></button>
            </div>

            {/* Output */}
            <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden font-mono text-[12.5px] leading-[1.7]"
              style={{ background: '#090c11' }}
            >
              {consoleLines.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full gap-3">
                  <Terminal className="size-8 text-slate-800" />
                  <p className="text-slate-600">No output yet — waiting for tests to run…</p>
                </div>
              ) : (
                <table className="w-full border-collapse">
                  <tbody>
                    {displayLines.map((line, i) => {
                      const isPassed = /PASSED|\bpassed\b/.test(line)
                      const isFailed = /FAILED|ERROR|\bfailed\b/.test(line)
                      const isAction = !isPassed && !isFailed && (
                        /Running|Navigating|Clicking|Typing| → /.test(line)
                      )
                      const isInfo = line.startsWith('>')
                      return (
                        <tr key={i} className={`group border-b border-white/[0.02] ${
                          isFailed ? 'bg-red-950/25 hover:bg-red-950/35' :
                          isPassed ? 'bg-emerald-950/15 hover:bg-emerald-950/25' :
                          'hover:bg-white/[0.025]'
                        }`}>
                          <td className="select-none text-right px-3 py-0 w-10 text-[11px] text-slate-700 group-hover:text-slate-500 tabular-nums align-top pt-[2px]">
                            {i + 1}
                          </td>
                          <td className={`px-3 py-0 select-text whitespace-pre-wrap break-all ${
                            isPassed ? 'text-emerald-400' :
                            isFailed ? 'text-red-300' :
                            isAction ? 'text-amber-200' :
                            isInfo ? 'text-[#9FA8DA]' :
                            'text-slate-200'
                          }`}>
                            {isPassed && <span className="text-emerald-500 mr-2 select-none">✓</span>}
                            {isFailed && <span className="text-red-400 mr-2 select-none">✗</span>}
                            {isInfo && !isPassed && !isFailed && <span className="text-[#5C6BC0] mr-2 select-none">›</span>}
                            {line.replace(/^>?\s*/, '')}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
              <div ref={consoleEndRef} />
            </div>
          </div>
        </div>
      )}

      {/* ── TV POPUP ─────────────────────────────────────────── */}
      {tvPopupOpen && (
        <div className="fixed inset-0 z-[9999] bg-black/90 flex items-center justify-center p-4"
          onClick={() => setTvPopupOpen(false)}
        >
          <div className="relative w-full max-w-[90vw] h-[86vh] rounded-2xl overflow-hidden border border-white/[0.08] flex flex-col bg-black shadow-2xl"
            onClick={e => e.stopPropagation()}
          >
            {/* TV bar */}
            <div className="shrink-0 bg-[#161b22] px-4 py-2 flex items-center gap-3 border-b border-white/[0.06]">
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
              </div>
              {tvImgSrc && (
                <div className="flex items-center gap-1.5 bg-red-600/80 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
                  <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />LIVE
                </div>
              )}
              <div className="flex-1 max-w-sm mx-auto">
                <div className="bg-slate-900/80 rounded-md px-3 py-1 flex items-center gap-1.5 text-[11px] text-slate-500 border border-white/[0.05]">
                  <Globe className="size-3 shrink-0" />
                  <span className="truncate">rhythmerp.com — {runningTest?.name ?? 'Running…'}</span>
                </div>
              </div>
              <button onClick={() => setTvPopupOpen(false)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[12px] text-slate-400 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer ml-auto"
              >
                <X className="size-3.5" /> Close
              </button>
            </div>

            {/* TV content */}
            <div className="flex-1 relative bg-black overflow-hidden">
              {tvImgSrc
                ? <img src={tvImgSrc} alt="Live view" className="w-full h-full object-contain" />
                : <div className="w-full h-full flex flex-col items-center justify-center gap-3">
                    <Loader2 className="size-10 text-[#5C6BC0] animate-spin" />
                    <p className="text-[13px] text-slate-600">Connecting to browser…</p>
                  </div>
              }
              {isRunning && runningTest && (
                <div className="absolute bottom-5 left-1/2 -translate-x-1/2 bg-black/70 backdrop-blur-sm text-white px-4 py-2 rounded-full flex items-center gap-2.5 text-[12px] border border-white/[0.08]">
                  <Loader2 className="size-3.5 animate-spin text-[#7986CB]" />
                  <span className="text-slate-300">{getTestShortName(runningTest, showRawNames ?? false)}</span>
                  <span className="text-slate-600 font-mono tabular-nums">{testElapsed}s</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
