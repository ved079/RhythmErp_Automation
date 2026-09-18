'use client'

import React, { useState, useCallback, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Play, Loader2, CheckCircle2, XCircle, RotateCcw } from 'lucide-react'
import { startConnectorWagoChain, type SSEEvent } from '@/lib/api'

const CLASS_NAME = 'TestConnectorWagoFlow'

const DOCS = [
  { label: 'PO',  step: 'test_create_po',  colors: 'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300 border-violet-200 dark:border-violet-800' },
  { label: 'GP',  step: 'test_create_gp',  colors: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border-blue-200 dark:border-blue-800' },
  { label: 'GRN', step: 'test_create_grn', colors: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300 border-cyan-200 dark:border-cyan-800' },
  { label: 'QC',  step: 'test_create_qc',  colors: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300 border-amber-200 dark:border-amber-800' },
  { label: 'PB',  step: 'test_create_pb',  colors: 'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300 border-pink-200 dark:border-pink-800' },
]

type StepStatus = 'idle' | 'working' | 'done' | 'error'

interface FlowStep {
  label: string
  step: string
  status: StepStatus
  docId?: string
}

interface FlowRun {
  flowIdx: number
  steps: FlowStep[]
}

export function ConnectorWagoFlowSection() {
  const [count, setCount] = useState(1)
  const [stopAt, setStopAt] = useState(DOCS.length - 1)
  const [running, setRunning] = useState(false)
  const [flows, setFlows] = useState<FlowRun[]>([])
  const currentFlowRef = useRef(1)
  const activeStepsRef = useRef(DOCS.map(d => d.step))

  const selectedDocs = DOCS.slice(0, stopAt + 1)

  const setStepField = useCallback((flowIdx: number, stepLabel: string, patch: Partial<FlowStep>) => {
    setFlows(prev => prev.map(f =>
      f.flowIdx !== flowIdx ? f : {
        ...f,
        steps: f.steps.map(s => s.label === stepLabel ? { ...s, ...patch } : s),
      }
    ))
  }, [])

  const handleRun = useCallback(async () => {
    const selectedSteps = DOCS.slice(0, stopAt + 1).map(d => d.step)
    activeStepsRef.current = selectedSteps
    currentFlowRef.current = 1

    const initFlows: FlowRun[] = Array.from({ length: count }, (_, i) => ({
      flowIdx: i + 1,
      steps: DOCS.slice(0, stopAt + 1).map(d => ({ label: d.label, step: d.step, status: 'idle' as StepStatus })),
    }))
    // mark first step of first flow as working
    if (initFlows[0]) initFlows[0].steps[0] = { ...initFlows[0].steps[0], status: 'working' }

    setFlows(initFlows)
    setRunning(true)

    await startConnectorWagoChain(
      count,
      (ev: SSEEvent) => {
        const msg = ev.message ?? ''
        if (!msg) return

        // new chain starting
        const chainHdr = msg.match(/^Chain \[(\d+)\/\d+\]/)
        if (chainHdr) {
          const idx = parseInt(chainHdr[1])
          currentFlowRef.current = idx
          setFlows(prev => prev.map(f =>
            f.flowIdx !== idx ? f : {
              ...f,
              steps: f.steps.map((s, si) => ({ ...s, status: si === 0 ? 'working' : 'idle' })),
            }
          ))
          return
        }

        const flow = currentFlowRef.current

        // DOC_CREATED:PO:PO/2026-2027/000839
        const docCreated = msg.match(/^DOC_CREATED:(\w+):(.+)$/)
        if (docCreated) {
          const [, label, docId] = docCreated
          setStepField(flow, label, { status: 'done', docId: docId.trim() })
          // mark next step working
          const steps = activeStepsRef.current
          const doc = DOCS.find(d => d.label === label)
          if (doc) {
            const idx = steps.indexOf(doc.step)
            if (idx >= 0 && idx < steps.length - 1) {
              const nextDoc = DOCS[idx + 1]
              if (nextDoc) setStepField(flow, nextDoc.label, { status: 'working' })
            }
          }
          return
        }

        // FAILED line — mark current working step as error
        const failedM = msg.match(/::TestConnectorWagoFlow::(test_create_\w+)\s+FAILED/)
        if (failedM) {
          const step = failedM[1]
          const doc = DOCS.find(d => d.step === step)
          if (doc) setStepField(flow, doc.label, { status: 'error' })
        }
      },
      () => {
        setRunning(false)
        // any still-working steps → error
        setFlows(prev => prev.map(f => ({
          ...f,
          steps: f.steps.map(s => s.status === 'working' ? { ...s, status: 'error' } : s),
        })))
      },
      (err: Error) => {
        setRunning(false)
        setFlows(prev => prev.map(f => ({
          ...f,
          steps: f.steps.map(s => s.status === 'working' ? { ...s, status: 'error' } : s),
        })))
      },
      selectedSteps,
    )
  }, [count, stopAt, setStepField])

  const isDone = !running && flows.length > 0
  const allPassed = isDone && flows.every(f => f.steps.every(s => s.status === 'done'))
  const anyFailed = isDone && flows.some(f => f.steps.some(s => s.status === 'error'))

  return (
    <div className="flex flex-col gap-5 h-full min-h-0">

      {/* ── Config ──────────────────────────────────────────────── */}
      <div className="flex items-start gap-5 p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/30 shrink-0 flex-wrap">
        <div className="flex flex-col gap-1">
          <Label className="text-[11px] text-gray-500">Flows</Label>
          <Input
            type="number" min={1} max={20} value={count}
            onChange={e => setCount(Math.max(1, Math.min(20, parseInt(e.target.value) || 1)))}
            className="h-7 text-[12px] w-20"
            disabled={running}
          />
        </div>

        {/* Step selector */}
        <div className="flex flex-col gap-2">
          <Label className="text-[11px] text-gray-500">Run up to</Label>
          <div className="flex items-center gap-0">
            {DOCS.map((doc, i) => {
              const active = i <= stopAt
              const isStop = i === stopAt
              return (
                <React.Fragment key={doc.label}>
                  {i > 0 && (
                    <div className={`h-px w-5 shrink-0 transition-colors ${active ? 'bg-gray-400 dark:bg-gray-500' : 'bg-gray-200 dark:bg-gray-700'}`} />
                  )}
                  <button
                    type="button"
                    onClick={() => !running && setStopAt(i)}
                    disabled={running}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-semibold border transition-all focus:outline-none ${
                      active ? `${doc.colors} ${isStop ? 'ring-2 ring-[#3F51B5]/60 ring-offset-1 dark:ring-offset-gray-900' : ''}` :
                      'bg-white dark:bg-gray-900 text-gray-400 dark:text-gray-600 border-gray-200 dark:border-gray-700'
                    } ${running ? 'cursor-not-allowed' : 'hover:scale-105 cursor-pointer'}`}
                  >
                    {doc.label}
                  </button>
                </React.Fragment>
              )
            })}
          </div>
        </div>

        <div className="ml-auto flex items-end">
          <Button
            size="sm" onClick={handleRun} disabled={running}
            className="h-8 px-4 gap-1.5 text-[12px] bg-[#3F51B5] hover:bg-[#3949AB] text-white"
          >
            {running ? <Loader2 className="size-3.5 animate-spin" /> : <Play className="size-3.5" />}
            {running ? 'Running…' : flows.length > 0 ? 'Run again' : 'Run'}
          </Button>
        </div>
      </div>

      {/* ── Activity feed ─────────────────────────────────────── */}
      {flows.length > 0 && (
        <div className="flex-1 min-h-0 overflow-auto flex flex-col gap-4">

          {/* Done banner */}
          {isDone && (
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-[12px] font-medium ${
              allPassed
                ? 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                : 'bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
            }`}>
              {allPassed
                ? <><CheckCircle2 className="size-4" /> All flows completed</>
                : <><XCircle className="size-4" /> Some steps failed</>
              }
              <button
                type="button" onClick={handleRun}
                className="ml-auto flex items-center gap-1 text-[11px] opacity-70 hover:opacity-100"
              >
                <RotateCcw className="size-3" /> Run again
              </button>
            </div>
          )}

          {/* Flow cards */}
          {flows.map(flow => (
            <div key={flow.flowIdx} className="flex flex-col gap-0">
              {/* Flow label (only when multiple flows) */}
              {count > 1 && (
                <div className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 mb-2 uppercase tracking-wider">
                  Flow {flow.flowIdx}
                </div>
              )}

              {/* Steps */}
              <div className="flex flex-col">
                {flow.steps.map((step, si) => {
                  const doc = DOCS.find(d => d.label === step.label)!
                  const isLast = si === flow.steps.length - 1

                  return (
                    <div key={step.label} className="flex gap-3">
                      {/* Timeline spine */}
                      <div className="flex flex-col items-center w-6 shrink-0">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                          step.status === 'done'    ? 'bg-emerald-100 dark:bg-emerald-900/40' :
                          step.status === 'error'   ? 'bg-red-100 dark:bg-red-900/40' :
                          step.status === 'working' ? 'bg-[#3F51B5]/10 dark:bg-[#3F51B5]/20' :
                          'bg-gray-100 dark:bg-gray-800'
                        }`}>
                          {step.status === 'done'    && <CheckCircle2 className="size-3.5 text-emerald-600 dark:text-emerald-400" />}
                          {step.status === 'error'   && <XCircle className="size-3.5 text-red-500" />}
                          {step.status === 'working' && <Loader2 className="size-3 text-[#5C6BC0] animate-spin" />}
                          {step.status === 'idle'    && <div className="size-2 rounded-full bg-gray-300 dark:bg-gray-600" />}
                        </div>
                        {!isLast && (
                          <div className={`w-px flex-1 my-1 ${
                            step.status === 'done' ? 'bg-emerald-200 dark:bg-emerald-800/50' : 'bg-gray-200 dark:bg-gray-700'
                          }`} />
                        )}
                      </div>

                      {/* Content */}
                      <div className={`flex flex-col pb-4 ${isLast ? 'pb-0' : ''}`}>
                        {step.status === 'idle' && (
                          <span className="text-[12px] text-gray-400 dark:text-gray-600 leading-6">{step.label}</span>
                        )}

                        {step.status === 'working' && (
                          <span className="text-[12px] text-gray-500 dark:text-gray-400 leading-6">
                            Working on <span className="font-medium text-gray-700 dark:text-gray-200">{step.label}</span>…
                          </span>
                        )}

                        {step.status === 'done' && (
                          <div className="flex items-center gap-2 leading-6">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${doc.colors}`}>
                              {step.label}
                            </span>
                            <span className="text-[12px] text-gray-500 dark:text-gray-400">created</span>
                            {step.docId && (
                              <span className="text-[12px] font-mono font-medium text-gray-800 dark:text-gray-100">{step.docId}</span>
                            )}
                          </div>
                        )}

                        {step.status === 'error' && (
                          <div className="flex items-center gap-2 leading-6">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300 border-red-200 dark:border-red-800">
                              {step.label}
                            </span>
                            <span className="text-[12px] text-red-500">failed</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
