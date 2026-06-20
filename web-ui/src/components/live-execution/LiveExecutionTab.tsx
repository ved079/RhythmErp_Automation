'use client'

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import {
  ArrowLeft, Globe, MoreHorizontal, Play, Square, RotateCcw, CheckCircle2,
  XCircle, Circle, Loader2, ClipboardList, Monitor, Maximize2, X, Terminal,
  Search, ChevronDown,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { testSpecGroups, type TestClassGroup, type TestItem } from '@/data/testSpecGroups'
import type { ScreenshotEntry } from '@/components/screenshot/ScreenshotGallery'
import { LiveScreencast } from './LiveScreencast'

interface TestProgressItem {
  id: string
  name: string
  status: 'pending' | 'running' | 'passed' | 'failed'
  duration: string
}

export function LiveExecutionTab({
  tests,
  testGroups,
  isRunning,
  runningProgress,
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
  showRawNames?: boolean
  onStop: () => void
  onBack: () => void
  onRerunFailed: () => void
  onScreenshotCaptured?: (entry: ScreenshotEntry) => void
}) {
  const consoleEndRef = useRef<HTMLDivElement>(null)
  const lastProgressRef = useRef<string>('')
  const [consoleLines, setConsoleLines] = useState<string[]>([
    '> Waiting for tests to start...',
    '> Select tests in Test Runner and click Run.',
  ])
  const [autoScroll, setAutoScroll] = useState(true)
  const [consoleSearch, setConsoleSearch] = useState('')
  const [showSearch, setShowSearch] = useState(false)

  const [tvPopupOpen, setTvPopupOpen] = useState(false)
  const [tvImgSrc, setTvImgSrc] = useState<string>('')
  const [tvActive, setTvActive] = useState(false)
  const handleScreenshotReady = useCallback((src: string, active: boolean) => {
    setTvImgSrc(src)
    setTvActive(active)
    if (active && src && onScreenshotCaptured) {
      const runningTest = tests.find((t) => t.status === 'running')
      onScreenshotCaptured({
        id: `ss-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        src,
        testName: runningTest?.name || 'Live Execution',
        timestamp: new Date().toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        moduleName: undefined,
        status: runningTest?.status === 'failed' ? 'failed' : 'passed',
      })
    }
  }, [onScreenshotCaptured, tests])

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && tvPopupOpen) setTvPopupOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [tvPopupOpen])

  const [consoleHeight, setConsoleHeight] = useState(220)
  const isResizingRef = useRef(false)
  const resizeStartRef = useRef({ y: 0, h: 0 })
  const handleConsoleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    isResizingRef.current = true
    resizeStartRef.current = { y: e.clientY, h: consoleHeight }
    const onMove = (ev: MouseEvent) => {
      if (!isResizingRef.current) return
      const delta = resizeStartRef.current.y - ev.clientY
      setConsoleHeight(Math.max(120, Math.min(500, resizeStartRef.current.h + delta)))
    }
    const onUp = () => {
      isResizingRef.current = false
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }, [consoleHeight])

  const runningTest = tests.find((t) => t.status === 'running')
  const runningTestId = runningTest?.id || null

  // ── Test progress items derived from `tests` prop ─────────
  const progressItems: TestProgressItem[] = useMemo(() => {
    return tests.map((t) => ({
      id: t.id,
      name: t.name,
      status: t.status === 'running' ? 'running' : t.status === 'passed' ? 'passed' : t.status === 'failed' ? 'failed' : 'pending',
      duration: t.duration || '',
    }))
  }, [tests])

  const passedCount = tests.filter((t) => t.status === 'passed').length
  const failedCount = tests.filter((t) => t.status === 'failed').length
  const runningCount = tests.filter((t) => t.status === 'running').length
  const completedCount = passedCount + failedCount
  const progressPercent = tests.length > 0 ? Math.round((completedCount / tests.length) * 100) : 0

  // ── Console auto-scroll ──────────────────────────────────
  useEffect(() => {
    if (autoScroll) {
      consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [consoleLines.length, autoScroll])

  // ── Console: append running progress ─────────────────────
  useEffect(() => {
    if (runningProgress && runningProgress !== lastProgressRef.current) {
      lastProgressRef.current = runningProgress
      setConsoleLines((prev) => [...prev, runningProgress])
    }
  }, [runningProgress])

  // ── Console: filtered lines for search ───────────────────
  const filteredConsoleLines = useMemo(() => {
    if (!consoleSearch.trim()) return consoleLines
    const q = consoleSearch.toLowerCase()
    return consoleLines.filter((l) => l.toLowerCase().includes(q))
  }, [consoleLines, consoleSearch])

  // ── Running step extraction from test groups ────────────
  const runningSteps = useMemo(() => {
    if (!runningTestId) return []
    for (const g of testGroups) {
      const t = g.tests.find((x) =>
        x.id === runningTestId ||
        runningTestId.endsWith('::' + x.id) ||
        runningTestId.includes(x.id)
      )
      if (t) {
        const stepsText = t.steps || t.description || ''
        const arrowSteps = stepsText.split('→').map((s) => s.trim()).filter(Boolean)
        if (arrowSteps.length > 1) return arrowSteps
        const numberedSteps = stepsText.split(/\d+\.\s+/).map((s) => s.trim()).filter(Boolean)
        if (numberedSteps.length > 1) return numberedSteps
        const newlineSteps = stepsText.split('\n').map((s) => s.trim()).filter(Boolean)
        if (newlineSteps.length > 1) return newlineSteps
        const sentenceSteps = stepsText.split(/\.\s+/).map((s) => s.trim()).filter(Boolean)
        if (sentenceSteps.length > 1) return sentenceSteps
        const trimmed = stepsText.trim()
        if (trimmed.length <= 80) return [trimmed]
        const words = trimmed.split(' ')
        const lines: string[] = []
        let current = ''
        for (const word of words) {
          if ((current + ' ' + word).trim().length > 60 && current.length > 0) {
            lines.push(current.trim())
            current = word
          } else {
            current = current ? current + ' ' + word : word
          }
        }
        if (current) lines.push(current.trim())
        return lines
      }
    }
    for (const g of testSpecGroups) {
      const t = g.tests.find((x) => x.id === runningTestId)
      if (t) {
        const arrowSteps = t.steps.split('→').map((s) => s.trim()).filter(Boolean)
        if (arrowSteps.length > 0) return arrowSteps
      }
    }
    const rt = tests.find((t) => t.id === runningTestId)
    return rt ? [rt.name] : ['Running test...']
  }, [runningTestId, testGroups, tests])

  // ── Render helpers ──────────────────────────────────────
  const statusIcon = (status: TestProgressItem['status'], size = 'size-4') => {
    if (status === 'passed') return <CheckCircle2 className={`${size} text-emerald-400`} />
    if (status === 'failed') return <XCircle className={`${size} text-red-400`} />
    if (status === 'running') return <Loader2 className={`${size} text-blue-400 animate-spin`} />
    return <Circle className={`${size} text-slate-600`} />
  }

  return (
    <>
    <div className="flex flex-col h-full min-h-0">
      {/* ── Top Bar ── */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-white/10 bg-slate-900/80 backdrop-blur-sm shrink-0">
        <Button variant="ghost" onClick={onBack} className="h-8 text-[13px] gap-1.5 text-slate-400 hover:text-white hover:bg-white/5 cursor-pointer px-2.5 rounded-lg">
          <ArrowLeft className="size-4" />
          Test Runner
        </Button>
        <div className="w-px h-5 bg-white/10" />
        {isRunning ? (
          <>
            <div className="flex items-center gap-3 flex-1">
              <Progress value={progressPercent} className="h-2 flex-1 [&>div]:bg-gradient-to-r [&>div]:from-emerald-500 [&>div]:to-emerald-400" />
              <span className="text-[13px] text-slate-300 font-semibold tabular-nums min-w-[80px]">
                {completedCount}/{tests.length}
                <span className="text-slate-500 ml-1">({progressPercent}%)</span>
              </span>
            </div>
            <div className="flex-1" />
            {runningCount > 0 && (
              <span className="text-[12px] text-blue-400 flex items-center gap-1.5 mr-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                {runningTest?.name || 'Running...'}
              </span>
            )}
            <Button onClick={onStop} className="bg-red-500/90 hover:bg-red-500 text-white h-8 text-[13px] gap-1.5 cursor-pointer rounded-lg shadow-lg shadow-red-500/20">
              <Square className="size-3.5" />
              Stop
            </Button>
          </>
        ) : completedCount > 0 ? (
          <>
            <span className="text-[13px] text-slate-400">
              Run complete — <span className="text-emerald-400 font-semibold">{passedCount} passed</span>, <span className="text-red-400 font-semibold">{failedCount} failed</span>
            </span>
            <div className="flex-1" />
            {failedCount > 0 && (
              <Button onClick={onRerunFailed} className="bg-amber-500/90 hover:bg-amber-500 text-white h-8 text-[13px] gap-1.5 cursor-pointer rounded-lg shadow-lg shadow-amber-500/20 mr-2">
                <RotateCcw className="size-3.5" />
                Rerun Failed ({failedCount})
              </Button>
            )}
            <Button onClick={onBack} className="bg-blue-500/90 hover:bg-blue-500 text-white h-8 text-[13px] gap-1.5 cursor-pointer rounded-lg shadow-lg shadow-blue-500/20">
              <RotateCcw className="size-3.5" />
              New Run
            </Button>
          </>
        ) : (
          <>
            <span className="text-[13px] text-slate-500">No test running</span>
            <div className="flex-1" />
          </>
        )}
        <div className="flex items-center gap-2 ml-2">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-[12px] font-medium tabular-nums">
            <CheckCircle2 className="size-3.5" /> {passedCount}
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 text-[12px] font-medium tabular-nums">
            <XCircle className="size-3.5" /> {failedCount}
          </span>
        </div>
      </div>

      {/* ── Main Content ── */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 px-4 pt-3 pb-2 min-h-0 flex gap-4">
          {/* Test Progress List (right panel when running or completed) */}
          {(isRunning || completedCount > 0) && tests.length > 0 && (
            <div className="w-72 shrink-0 flex flex-col rounded-xl bg-slate-900 border border-white/[0.06] shadow-2xl shadow-black/40 overflow-hidden order-1">
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06] bg-gradient-to-r from-blue-500/10 to-purple-500/10">
                <div className="flex items-center gap-2.5">
                  <div className="w-6 h-6 rounded-md bg-blue-500/20 flex items-center justify-center">
                    <ClipboardList className="size-3.5 text-blue-400" />
                  </div>
                  <span className="text-[13px] font-semibold text-slate-200">Tests</span>
                </div>
                <span className="text-[11px] text-blue-400 font-semibold tabular-nums px-2 py-0.5 rounded-full bg-blue-500/10">
                  {completedCount}/{tests.length}
                </span>
              </div>
              <div className="flex-1 overflow-auto p-2 space-y-0.5">
                {progressItems.map((item) => (
                  <div
                    key={item.id}
                    className={
                      'flex items-center gap-2 px-3 py-1.5 rounded-md text-[12px] transition-colors ' +
                      (item.status === 'passed' ? 'bg-emerald-500/[0.06] text-emerald-300/90' :
                       item.status === 'failed' ? 'bg-red-500/[0.06] text-red-300/90' :
                       item.status === 'running' ? 'bg-blue-500/[0.08] text-blue-200 ring-1 ring-blue-500/20' :
                       'text-slate-500')
                    }
                  >
                    <span className="shrink-0">{statusIcon(item.status, 'size-3.5')}</span>
                    <span className="flex-1 truncate">
                      {showRawNames ? item.id : item.name}
                    </span>
                    {item.status === 'running' && (
                      <span className="text-[10px] text-blue-400 font-medium shrink-0 flex items-center gap-1">
                        <span className="w-1 h-1 rounded-full bg-blue-400 animate-pulse" />
                        Run
                      </span>
                    )}
                    {item.duration && (
                      <span className="text-[10px] text-slate-500 tabular-nums shrink-0">{item.duration}</span>
                    )}
                  </div>
                ))}
              </div>
              {isRunning && (
                <div className="px-4 py-3 border-t border-white/[0.06] bg-slate-900/50">
                  <div className="flex items-center justify-between text-[11px] text-slate-500 mb-2">
                    <span>Overall Progress</span>
                    <span className="font-semibold text-slate-300 tabular-nums">{progressPercent}%</span>
                  </div>
                  <Progress value={progressPercent} className="h-2 bg-slate-800 [&>div]:bg-gradient-to-r [&>div]:from-blue-500 [&>div]:to-cyan-400" />
                </div>
              )}
            </div>
          )}

          {/* Live Browser View */}
          <div className="flex-1 min-w-0 flex flex-col">
            <div className="flex-1 rounded-xl border border-white/[0.08] overflow-hidden flex flex-col shadow-2xl shadow-black/30 bg-slate-900 min-h-0">
              {/* Chrome bar */}
              <div className="bg-slate-800 px-4 py-2 flex items-center gap-3 shrink-0 border-b border-white/[0.04]">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
                  <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
                  <div className="w-3 h-3 rounded-full bg-[#28c840]" />
                </div>
                <div className="flex-1 flex items-center justify-center">
                  <div className="bg-slate-900/80 rounded-lg px-4 py-1 flex items-center gap-2 text-[11px] text-slate-500 border border-white/[0.06] max-w-md w-full">
                    <Globe className="size-3.5 text-slate-600 shrink-0" />
                    <span className="truncate text-center">
                      {isRunning ? 'https://rhythmerp.com — ' + (runningTest?.name || 'Running...') : 'https://rhythmerp.com'}
                    </span>
                  </div>
                </div>
                {isRunning && runningTest && (
                  <button
                    onClick={() => setTvPopupOpen(true)}
                    className="flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
                    title="Pop-out TV Screen"
                  >
                    <Monitor className="size-3.5" />
                    <span>TV Screen</span>
                    <Maximize2 className="size-3" />
                  </button>
                )}
                <MoreHorizontal className="size-4 text-slate-600" />
              </div>

              {/* Browser content / Run summary */}
              <div className="flex-1 overflow-hidden relative bg-slate-950">
                {isRunning && runningTest ? (
                  <LiveScreencast isRunning={isRunning} onScreenshotReady={handleScreenshotReady} />
                ) : completedCount > 0 ? (
                  <div className="w-full h-full flex flex-col items-center justify-center gap-6">
                    <div className="flex items-center gap-6">
                      {failedCount === 0 ? (
                        <div className="w-20 h-20 rounded-2xl bg-emerald-500/10 flex items-center justify-center ring-1 ring-emerald-500/20">
                          <CheckCircle2 className="size-10 text-emerald-400" />
                        </div>
                      ) : (
                        <div className="w-20 h-20 rounded-2xl bg-amber-500/10 flex items-center justify-center ring-1 ring-amber-500/20">
                          <div className="flex gap-2">
                            <XCircle className="size-8 text-red-400" />
                            <CheckCircle2 className="size-8 text-emerald-400" />
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="text-center max-w-md">
                      <p className="text-[17px] font-semibold text-slate-200">Run Complete</p>
                      <p className="text-[13px] text-slate-500 mt-1.5">
                        <span className="text-emerald-400 font-semibold">{passedCount} passed</span>
                        {failedCount > 0 && <span className="text-slate-500">, </span>}
                        {failedCount > 0 && <span className="text-red-400 font-semibold">{failedCount} failed</span>}
                        {' '}of <span className="text-slate-300">{tests.length}</span> tests
                      </p>
                      <div className="flex items-center justify-center gap-3 mt-3">
                        <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                          <CheckCircle2 className="size-3 text-emerald-400" />
                          <span>{Math.round((passedCount / tests.length) * 100)}% pass rate</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-3">
                      {failedCount > 0 && (
                        <Button onClick={onRerunFailed} className="bg-amber-500/90 hover:bg-amber-500 text-white h-8 text-[12px] gap-1.5 cursor-pointer rounded-lg shadow-lg shadow-amber-500/20">
                          <RotateCcw className="size-3.5" />
                          Rerun Failed ({failedCount})
                        </Button>
                      )}
                      <Button onClick={onBack} className="bg-slate-700 hover:bg-slate-600 text-white h-8 text-[12px] gap-1.5 cursor-pointer rounded-lg">
                        <ArrowLeft className="size-3.5" />
                        Back to Runner
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center gap-4">
                    <div className="w-20 h-20 rounded-full bg-slate-800 flex items-center justify-center border border-white/[0.06]">
                      <Play className="size-8 text-slate-600 ml-1" />
                    </div>
                    <div className="text-center">
                      <p className="text-[14px] text-slate-500 font-medium">No test running</p>
                      <p className="text-[12px] text-slate-600 mt-1">Go to Test Runner, select tests and click Run</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Currently running info */}
            {isRunning && runningTest && (
              <div className="flex items-center gap-3 mt-2 px-1">
                <span className="text-[12px] text-slate-500">
                  Currently: {showRawNames ? <><span className="font-medium text-slate-300">{runningTest.id}</span><span className="text-gray-500"> — </span></> : ''}{runningTest.name}
                </span>
                <div className="w-px h-3 bg-slate-700" />
                <span className="text-[12px] text-blue-400 flex items-center gap-1.5">
                  <Loader2 className="size-3 animate-spin" />
                  Running...
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Console resize handle */}
        <div
          className="shrink-0 h-1.5 bg-slate-800 cursor-row-resize hover:bg-blue-500/50 active:bg-blue-500/50 transition-colors flex items-center justify-center group"
          onMouseDown={handleConsoleResizeStart}
        >
          <div className="w-8 h-0.5 rounded-full bg-slate-600 group-hover:bg-blue-400 transition-colors" />
        </div>

        {/* Console */}
        <div className="shrink-0 flex flex-col border-t border-white/[0.06]" style={{ height: consoleHeight }}>
          <div className="flex items-center gap-2 px-3 py-2 bg-slate-900 border-b border-white/[0.06] shrink-0">
            <Terminal className="size-3.5 text-emerald-400" />
            <span className="text-[12px] font-semibold text-slate-300 tracking-wide">LIVE CONSOLE</span>
            <div className="flex items-center gap-1 ml-auto">
              {showSearch ? (
                <div className="flex items-center gap-1 bg-slate-800 rounded px-2 py-0.5">
                  <Search className="size-3 text-slate-400" />
                  <input
                    type="text"
                    value={consoleSearch}
                    onChange={(e) => setConsoleSearch(e.target.value)}
                    placeholder="Filter..."
                    className="w-24 bg-transparent text-[11px] text-slate-300 outline-none placeholder:text-slate-600 font-mono"
                    autoFocus
                  />
                  <button onClick={() => { setShowSearch(false); setConsoleSearch('') }} className="text-slate-600 hover:text-slate-400 cursor-pointer">
                    <X className="size-3" />
                  </button>
                </div>
              ) : (
                <button onClick={() => setShowSearch(true)} className="text-slate-600 hover:text-slate-400 transition-colors cursor-pointer p-0.5" title="Filter console">
                  <Search className="size-3" />
                </button>
              )}
              <span className="text-[10px] text-slate-600 mx-1">|</span>
              <button
                onClick={() => setAutoScroll(!autoScroll)}
                className={`text-[10px] font-mono px-1.5 py-0.5 rounded transition-colors cursor-pointer ${autoScroll ? 'bg-blue-500/20 text-blue-400' : 'bg-slate-800 text-slate-500'}`}
                title={autoScroll ? 'Auto-scroll ON — click to pause' : 'Auto-scroll OFF — click to enable'}
              >
                ↕ {autoScroll ? 'ON' : 'OFF'}
              </button>
              <span className="text-[10px] text-slate-600 mx-1">|</span>
              <span className="text-[10px] text-slate-600 font-mono bg-slate-800 px-1.5 py-0.5 rounded">pytest</span>
            </div>
          </div>
          <div className="flex-1 bg-slate-950 overflow-auto p-3">
            <div className="space-y-px">
              {(consoleSearch.trim() ? filteredConsoleLines : consoleLines).map((line, i) => (
                <div key={i} className={
                  'text-xs font-mono leading-5 ' +
                  (line.includes('PASSED') || line.includes('passed')
                    ? 'text-emerald-400'
                    : line.includes('FAILED') || line.includes('ERROR') || line.includes('failed')
                      ? 'text-red-400'
                      : line.includes('Running') || line.includes('Navigating') || line.includes('Clicking') || line.includes('Typing')
                        ? 'text-amber-300'
                        : line.startsWith('>')
                          ? 'text-blue-400'
                          : 'text-slate-500')
                }>
                  {line}
                </div>
              ))}
              <div ref={consoleEndRef} />
            </div>
          </div>
        </div>
      </div>
    </div>

      {/* TV Screen Popup */}
      {tvPopupOpen && (
        <div
          className="fixed inset-0 z-[9999] bg-black/90 flex items-center justify-center p-4"
          onClick={() => setTvPopupOpen(false)}
        >
          <div
            className="relative w-full max-w-[90vw] h-[85vh] rounded-2xl overflow-hidden border-[3px] border-gray-600 flex flex-col bg-black"
            onClick={(e) => e.stopPropagation()}
            style={{ boxShadow: "0 0 0 1px rgba(255,255,255,0.08), 0 0 80px rgba(0,0,0,0.8)" }}
          >
            <div className="shrink-0 bg-gradient-to-b from-gray-800 to-gray-900 px-4 py-2 flex items-center justify-between border-b border-gray-700">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-red-500" /><div className="w-3 h-3 rounded-full bg-yellow-500" /><div className="w-3 h-3 rounded-full bg-green-500" /></div>
                {tvActive && <div className="flex items-center gap-1.5 bg-red-600/80 text-white text-[10px] font-bold px-2.5 py-0.5 rounded-full"><span className="w-2 h-2 rounded-full bg-white animate-pulse" />LIVE</div>}
              </div>
              <div className="flex-1 max-w-[600px] mx-4"><div className="bg-gray-800/80 rounded-lg px-4 py-1 flex items-center gap-2 text-[12px] text-gray-400 border border-gray-700"><Globe className="size-3.5" /><span className="truncate">https://rhythmerp.com - {runningTest?.name || "Running..."}</span></div></div>
              <button onClick={() => setTvPopupOpen(false)} className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-[12px] font-medium text-gray-300 hover:bg-gray-700 hover:text-white transition-colors cursor-pointer"><X className="size-4" /><span>Close</span></button>
            </div>
            <div className="flex-1 relative bg-black overflow-hidden">
              {tvActive && tvImgSrc ? <img src={tvImgSrc} alt="TV view" className="w-full h-full object-contain" /> : <div className="w-full h-full flex flex-col items-center justify-center gap-3"><Loader2 className="size-10 text-green-400 animate-spin" /><p className="text-[14px] text-gray-500">Connecting...</p></div>}
            </div>
            <div className="shrink-0 h-3 bg-gradient-to-t from-gray-800 to-gray-900 border-t border-gray-700 rounded-b-2xl" />
            {isRunning && runningTest && <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-black/70 text-white px-5 py-2 rounded-full flex items-center gap-3 text-[12px] border border-white/10"><Loader2 className="size-3.5 animate-spin text-blue-400" />{showRawNames ? <><span className="font-medium">{runningTest.id}</span><span className="text-gray-400">-</span></> : ''}<span className="text-gray-300">{runningTest.name}</span></div>}
          </div>
        </div>
      )}
    </>
  )
}