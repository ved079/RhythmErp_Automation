'use client'

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import {
  ArrowLeft,
  Square,
  RotateCcw,
  Loader2,
  CheckCircle2,
  XCircle,
  Circle,
  Terminal,
  Maximize2,
  X,
} from 'lucide-react'

interface TestItem {
  id: string
  name: string
  status: 'passed' | 'failed' | 'pending' | 'running'
  duration: string
}

interface TestSpecItem {
  id: string
  description: string
  status: 'passed' | 'failed' | 'not-run'
  duration: string
  steps: string
  expected: string
  error?: string
}

interface TestClassGroup {
  className: string
  tests: TestSpecItem[]
}

// ─── Live Browser Screenshot Component ────────────────────
function LiveBrowserView({
  onScreenshotReady,
}: {
  onScreenshotReady: (src: string, active: boolean) => void
}) {
  const [imgSrc, setImgSrc] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchScreenshot = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/screenshot')
        const data = await res.json()
        if (data.screenshot) {
          setImgSrc(`data:image/png;base64,${data.screenshot}`)
          onScreenshotReady(`data:image/png;base64,${data.screenshot}`, data.active)
          setLoading(false)
        } else {
          setLoading(false)
          onScreenshotReady('', false)
        }
      } catch {
        setLoading(false)
        onScreenshotReady('', false)
      }
    }

    fetchScreenshot()
    const interval = setInterval(fetchScreenshot, 2000)
    return () => clearInterval(interval)
  }, [onScreenshotReady])

  if (loading) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center gap-3 bg-black text-white">
        <Loader2 className="size-8 text-green-400 animate-spin" />
        <p className="text-[13px] text-gray-400">Connecting to browser...</p>
        <p className="text-[11px] text-gray-600">Make sure FastAPI backend is running</p>
      </div>
    )
  }

  if (!imgSrc) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center gap-3 bg-black text-white">
        <Terminal className="size-12 text-gray-600" />
        <p className="text-[13px] text-gray-400">No browser session active</p>
        <p className="text-[11px] text-gray-600">Start a test run to see live browser</p>
      </div>
    )
  }

  return (
    <div className="w-full h-full relative bg-black">
      <img src={imgSrc} alt="Live browser" className="w-full h-full object-contain" />
      <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-black/60 text-white text-[10px] px-2 py-1 rounded-full">
        <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
        LIVE
      </div>
    </div>
  )
}

// ─── LIVE EXECUTION TAB (Browser view + Console) ────────
export function LiveExecutionTab({
  tests,
  testGroups,
  isRunning,
  runningProgress,
  onStop,
  onBack,
  onRerunFailed,
}: {
  tests: TestItem[]
  testGroups: TestClassGroup[]
  isRunning: boolean
  runningProgress: string
  onStop: () => void
  onBack: () => void
  onRerunFailed: () => void
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
  }, [])

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
                {progressPercent}%
              </span>
            </div>
            <Button
              variant="destructive"
              size="sm"
              onClick={onStop}
              className="h-8 text-[13px] gap-1.5 bg-red-500/90 hover:bg-red-600 cursor-pointer px-3 rounded-lg"
            >
              <Square className="size-3.5 fill-current" />
              Stop
            </Button>
          </>
        ) : (
          <>
            <div className="flex items-center gap-2 text-sm text-slate-300">
              <CheckCircle2 className="size-4 text-emerald-400" />
              <span className="font-medium">{passedCount}</span>
              <span className="text-slate-500">passed</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-300">
              <XCircle className="size-4 text-red-400" />
              <span className="font-medium">{failedCount}</span>
              <span className="text-slate-500">failed</span>
            </div>
            {failedCount > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRerunFailed}
                className="h-8 text-[13px] gap-1.5 border-white/10 hover:bg-white/5 cursor-pointer px-3 rounded-lg"
              >
                <RotateCcw className="size-3.5" />
                Rerun Failed
              </Button>
            )}
          </>
        )}
      </div>

      {/* ── Browser View ── */}
      <div className="flex-1 min-h-0 bg-black">
        <LiveBrowserView onScreenshotReady={handleScreenshotReady} />
      </div>

      {/* ── Console Resizer ── */}
      <div
        className="h-2.5 cursor-row-resize flex items-center justify-center bg-slate-900/50 hover:bg-slate-800 transition-colors shrink-0"
        onMouseDown={handleConsoleResizeStart}
      >
        <div className="w-8 h-0.5 bg-slate-600 rounded-full" />
      </div>

      {/* ── Console Panel ── */}
      <div style={{ height: consoleHeight }} className="flex flex-col bg-slate-950 shrink-0">
        <div className="flex items-center justify-between px-3 py-2 border-t border-white/5 bg-slate-900/50">
          <div className="flex items-center gap-2 text-[11px] text-slate-400">
            <Terminal className="size-3.5" />
            <span className="font-medium uppercase tracking-wide">Console Output</span>
          </div>
          {tvActive && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setTvPopupOpen(true)}
              className="h-6 text-[11px] gap-1.5 text-slate-400 hover:text-white hover:bg-white/5 cursor-pointer px-2 rounded"
            >
              <Maximize2 className="size-3.5" />
              Full Screen
            </Button>
          )}
        </div>
        <ScrollArea className="flex-1 p-3 font-mono text-[11px] leading-relaxed">
          {consoleLines.map((line, i) => {
            const isError = line.toLowerCase().includes('failed') || line.toLowerCase().includes('error') || line.startsWith('❌')
            const isSuccess = line.toLowerCase().includes('passed') || line.startsWith('✅')
            const isStep = line.startsWith('▶') || line.startsWith('➤')
            return (
              <div
                key={i}
                className={`py-0.5 ${
                  isError ? 'text-red-400' : isSuccess ? 'text-emerald-400' : isStep ? 'text-blue-400' : 'text-slate-300'
                }`}
              >
                {line}
              </div>
            )
          })}
          <div ref={consoleEndRef} />
        </ScrollArea>
      </div>

      {/* ── Current Step Indicator ── */}
      {isRunning && currentStepIndex >= 0 && runningSteps.length > 0 && (
        <div className="absolute bottom-[260px] left-1/2 -translate-x-1/2 px-4 py-2.5 bg-slate-900/95 backdrop-blur-md border border-white/10 rounded-xl shadow-2xl max-w-[600px] w-[90%]">
          <div className="flex items-center gap-2 mb-1.5">
            <Loader2 className="size-3.5 text-blue-400 animate-spin" />
            <span className="text-[11px] text-slate-400 uppercase tracking-wide font-semibold">Current Step</span>
          </div>
          <p className="text-[13px] text-white font-medium leading-snug">
            {runningSteps[currentStepIndex]}
          </p>
          <div className="flex items-center gap-1 mt-2">
            {runningSteps.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 rounded-full transition-all ${
                  i === currentStepIndex ? 'w-6 bg-blue-500' : i < currentStepIndex ? 'w-1.5 bg-emerald-500' : 'w-1.5 bg-slate-700'
                }`}
              />
            ))}
          </div>
        </div>
      )}
    </div>

    {/* ── Full-Screen TV Popup ── */}
    {tvPopupOpen && tvImgSrc && (
      <div className="fixed inset-0 z-[100] bg-black/95 backdrop-blur-md flex items-center justify-center p-8">
        <div className="relative w-full h-full max-w-[90vw] max-h-[90vh]">
          <img src={tvImgSrc} alt="Full screen" className="w-full h-full object-contain" />
          <button
            onClick={() => setTvPopupOpen(false)}
            className="absolute top-4 right-4 p-2 bg-black/60 hover:bg-black/80 rounded-full text-white transition-colors cursor-pointer"
          >
            <X className="size-5" />
          </button>
        </div>
      </div>
    )}
    </>
  )
}

// Need to import testSpecGroups from page.tsx or pass as prop
// This is a placeholder - will be fixed when integrating with page.tsx
const testSpecGroups: TestClassGroup[] = []
