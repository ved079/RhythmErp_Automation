'use client'

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { fetchScreenshot } from '@/lib/api'
import { ArrowLeft, Square, RotateCcw, CheckCircle2, XCircle, Loader2, Circle, Globe, ClipboardList, MoreHorizontal, Monitor, Maximize2, Play, X, Terminal } from 'lucide-react'
import type { TestItem, TestClassGroup } from '@/lib/types'
import type { ScreenshotEntry } from '@/components/screenshot/ScreenshotGallery'
import { testSpecGroups } from '@/lib/constants'

// ─── LIVE SCREENCAST ─────────────────────────────────────
function LiveScreencast({ isRunning, onScreenshotReady }: { isRunning: boolean; onScreenshotReady?: (src: string, active: boolean) => void }) {
  const [imgSrc, setImgSrc] = useState<string>('')
  const [active, setActive] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!isRunning) {
      if (intervalRef.current) clearInterval(intervalRef.current)
      return
    }

    const poll = async () => {
      try {
        const data = await fetchScreenshot()
        if (data.active && data.screenshot) {
          const src = `data:image/png;base64,${data.screenshot}`
          setImgSrc(src)
          setActive(true)
          onScreenshotReady?.(src, true)
        } else {
          setActive(false)
          onScreenshotReady?.('', false)
        }
      } catch {
        setActive(false)
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 1000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [isRunning])

  if (!active || !imgSrc) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center gap-3 bg-gray-900">
        <Loader2 className="size-8 text-green-400 animate-spin" />
        <p className="text-[13px] text-gray-400">Connecting to browser...</p>
        <p className="text-[11px] text-gray-600">Make sure FastAPI backend is running</p>
      </div>
    )
  }

  return (
    <div className="w-full h-full relative bg-black">
      <img
        src={imgSrc}
        alt="Live browser"
        className="w-full h-full object-contain"
      />
      <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-black/60 text-white text-[10px] px-2 py-1 rounded-full">
        <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
        LIVE
      </div>
    </div>
  )
}

// ─── LIVE EXECUTION TAB (Browser view + Console) ────────
function LiveExecutionTab({
  tests,
  testGroups,
  isRunning,
  runningProgress,
  onStop,
  onBack,
  onRerunFailed,
  onScreenshotCaptured,
}: {
  tests: TestItem[]
  testGroups: TestClassGroup[]
  isRunning: boolean
  runningProgress: string
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
  const [currentStepIndex, setCurrentStepIndex] = useState(-1)
  const prevRunningTestIdRef = useRef<string | null>(null)
  const stepTimerRef = useRef<NodeJS.Timeout | null>(null)


  const [tvPopupOpen, setTvPopupOpen] = useState(false)
  const [tvImgSrc, setTvImgSrc] = useState<string>('')
  const [tvActive, setTvActive] = useState(false)
  const handleScreenshotReady = useCallback((src: string, active: boolean) => {
    setTvImgSrc(src)
    setTvActive(active)
    // Save to screenshot gallery for Phase 4
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

  useEffect(() => {
    if (stepTimerRef.current) {
      clearInterval(stepTimerRef.current)
      stepTimerRef.current = null
    }
    if (runningTestId && runningTestId !== prevRunningTestIdRef.current) {
      prevRunningTestIdRef.current = runningTestId
      if (runningSteps.length > 0) {
        setCurrentStepIndex(0)
        let idx = 0
        stepTimerRef.current = setInterval(() => {
          idx++
          if (idx < runningSteps.length) {
            setCurrentStepIndex(idx)
          } else {
            if (stepTimerRef.current) clearInterval(stepTimerRef.current)
            stepTimerRef.current = null
          }
        }, 150)
      } else {
        setCurrentStepIndex(-1)
      }
    } else if (!runningTestId) {
      setCurrentStepIndex(-1)
      prevRunningTestIdRef.current = null
    }
    return () => {
      if (stepTimerRef.current) {
        clearInterval(stepTimerRef.current)
        stepTimerRef.current = null
      }
    }
  }, [runningTestId, runningSteps.length])

  useEffect(() => {
    if (runningProgress && runningProgress !== lastProgressRef.current) {
      lastProgressRef.current = runningProgress
      setConsoleLines((prev) => [...prev, runningProgress])
    }
  }, [runningProgress])

  useEffect(() => {
    consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [consoleLines.length])

  const passedCount = tests.filter((t) => t.status === 'passed').length
  const failedCount = tests.filter((t) => t.status === 'failed').length
  const completedCount = passedCount + failedCount
  const progressPercent = tests.length > 0 ? Math.round((completedCount / tests.length) * 100) : 0

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
          {/* Step Progress Panel */}
          {isRunning && runningTest && runningSteps.length > 0 && (
            <div className="w-72 shrink-0 flex flex-col rounded-xl bg-slate-900 border border-white/[0.06] shadow-2xl shadow-black/40 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06] bg-gradient-to-r from-blue-500/10 to-purple-500/10">
                <div className="flex items-center gap-2.5">
                  <div className="w-6 h-6 rounded-md bg-blue-500/20 flex items-center justify-center">
                    <ClipboardList className="size-3.5 text-blue-400" />
                  </div>
                  <span className="text-[13px] font-semibold text-slate-200">Test Steps</span>
                </div>
                <span className="text-[11px] text-blue-400 font-semibold tabular-nums px-2 py-0.5 rounded-full bg-blue-500/10">
                  {Math.min(currentStepIndex + 1, runningSteps.length)}/{runningSteps.length}
                </span>
              </div>
              <div className="flex-1 overflow-auto p-3 space-y-1.5">
                {runningSteps.map((step, idx) => {
                  const isCompleted = idx < currentStepIndex
                  const isCurrent = idx === currentStepIndex
                  return (
                    <div key={idx} className={
                      'flex items-start gap-2 px-3 py-2 rounded-lg text-[12px] transition-all duration-200 ' +
                      (isCompleted
                        ? 'bg-emerald-500/[0.07] text-emerald-300/80'
                        : isCurrent
                          ? 'bg-blue-500/[0.12] text-blue-200 ring-1 ring-blue-500/30 shadow-lg shadow-blue-500/5'
                          : 'text-slate-600 hover:text-slate-500')
                    }>
                      <span className="text-[10px] font-mono tabular-nums mt-0.5 w-4 shrink-0 text-right opacity-40">{idx + 1}</span>
                      {isCompleted ? (
                        <CheckCircle2 className="size-4 text-emerald-400/70 shrink-0 mt-0.5" />
                      ) : isCurrent ? (
                        <Loader2 className="size-4 text-blue-400 shrink-0 mt-0.5 animate-spin" />
                      ) : (
                        <Circle className="size-3.5 text-slate-700 shrink-0 mt-1" />
                      )}
                      <span className="flex-1 leading-relaxed">{step}</span>
                      {isCurrent && (
                        <span className="text-[10px] text-blue-400 font-medium shrink-0 mt-0.5 flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                          Run
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
              <div className="px-4 py-3 border-t border-white/[0.06] bg-slate-900/50">
                <div className="flex items-center justify-between text-[11px] text-slate-500 mb-2">
                  <span>Progress</span>
                  <span className="font-semibold text-slate-300 tabular-nums">
                    {Math.round(((currentStepIndex + 1) / runningSteps.length) * 100)}%
                  </span>
                </div>
                <Progress value={((currentStepIndex + 1) / runningSteps.length) * 100} className="h-2 bg-slate-800 [&>div]:bg-gradient-to-r [&>div]:from-blue-500 [&>div]:to-cyan-400" />
              </div>
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

              {/* Browser content */}
              <div className="flex-1 overflow-hidden relative bg-slate-950">
                {isRunning && runningTest ? (
                  <LiveScreencast isRunning={isRunning} onScreenshotReady={handleScreenshotReady} />
                ) : completedCount > 0 ? (
                  <div className="w-full h-full flex flex-col items-center justify-center gap-3">
                    <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 flex items-center justify-center">
                      <CheckCircle2 className="size-8 text-emerald-400" />
                    </div>
                    <div className="text-center">
                      <p className="text-[15px] font-semibold text-slate-200">Run Complete</p>
                      <p className="text-[13px] text-slate-500 mt-1">{passedCount} passed, {failedCount} failed</p>
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
                  Currently: <span className="font-medium text-slate-300">{runningTest.id}</span> — {runningTest.name}
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
            <span className="text-[10px] text-slate-600 ml-auto font-mono bg-slate-800 px-1.5 py-0.5 rounded">pytest</span>
          </div>
          <div className="flex-1 bg-slate-950 overflow-auto p-3">
            <div className="space-y-px">
              {consoleLines.map((line, i) => (
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
            {isRunning && runningTest && <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-black/70 text-white px-5 py-2 rounded-full flex items-center gap-3 text-[12px] border border-white/10"><Loader2 className="size-3.5 animate-spin text-blue-400" /><span className="font-medium">{runningTest.id}</span><span className="text-gray-400">-</span><span className="text-gray-300">{runningTest.name}</span></div>}
          </div>
        </div>
      )}
    </>
  )
}

export { LiveScreencast, LiveExecutionTab }
