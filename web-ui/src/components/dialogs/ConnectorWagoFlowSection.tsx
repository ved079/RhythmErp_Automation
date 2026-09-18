'use client'

import React, { useState, useCallback, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Play, Loader2, CheckCircle2, XCircle, RotateCcw } from 'lucide-react'
import { startConnectorWagoChain, type SSEEvent } from '@/lib/api'

const DOCS = [
  { label: 'PO',  step: 'test_create_po',  batchStep: 'test_batch_po',      colors: 'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300 border-violet-200 dark:border-violet-800' },
  { label: 'GP',  step: 'test_create_gp',  batchStep: 'test_batch_gp',      colors: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border-blue-200 dark:border-blue-800' },
  { label: 'GRN', step: 'test_create_grn', batchStep: 'test_batch_grn',     colors: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300 border-cyan-200 dark:border-cyan-800' },
  { label: 'QC',  step: 'test_create_qc',  batchStep: 'test_batch_qc_pb',   colors: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300 border-amber-200 dark:border-amber-800' },
  { label: 'PB',  step: 'test_create_pb',  batchStep: 'test_batch_qc_pb',   colors: 'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300 border-pink-200 dark:border-pink-800' },
]

type DocStatus = 'idle' | 'working' | 'done' | 'error' | 'skipped'

interface DocState {
  label: string
  status: DocStatus
  docIds: string[]   // created ref_nos (length grows as chains complete)
  retries: number
  total: number      // how many chains expected for this doc
}

export function ConnectorWagoFlowSection() {
  const [count, setCount] = useState(1)
  const [stopAt, setStopAt] = useState(DOCS.length - 1)
  const [running, setRunning] = useState(false)
  const [docs, setDocs] = useState<DocState[]>([])
  const activeDocsRef = useRef<string[]>([])

  const selectedDocs = DOCS.slice(0, stopAt + 1)

  const patchDoc = useCallback((label: string, patch: Partial<DocState>) => {
    setDocs(prev => prev.map(d => d.label === label ? { ...d, ...patch } : d))
  }, [])

  const handleRun = useCallback(async () => {
    const activeDocs = DOCS.slice(0, stopAt + 1)
    activeDocsRef.current = activeDocs.map(d => d.label)
    const n = Math.max(1, count)

    const initDocs: DocState[] = activeDocs.map((d, i) => ({
      label: d.label,
      status: i === 0 ? 'working' : 'idle',
      docIds: [],
      retries: 0,
      total: n,
    }))
    setDocs(initDocs)
    setRunning(true)

    // Deduplicate: QC and PB share test_batch_qc_pb — send it only once
    const batchSteps = [...new Set(activeDocs.map(d => d.batchStep))]

    await startConnectorWagoChain(
      n,
      (ev: SSEEvent) => {
        const msg = ev.message ?? ''
        if (!msg) return

        // DOC_CREATED:PO:PO/2026-2027/000839 — may fire N times per doc type
        const docCreated = msg.match(/DOC_CREATED:(\w+):([^\s]+)/)
        if (docCreated) {
          const [, label, docId] = docCreated
          const docDef = DOCS.find(d => d.label === label)
          setDocs(prev => {
            // Update the matched doc
            let updated = prev.map(d => {
              if (d.label !== label) return d
              const newIds = [...d.docIds, docId.trim()]
              return { ...d, docIds: newIds, status: (newIds.length >= d.total ? 'done' : 'working') as DocStatus }
            })
            // If this doc just went from idle→working, also activate batchStep siblings
            const wasIdle = prev.find(d => d.label === label)?.status === 'idle'
            if (wasIdle && docDef) {
              updated = updated.map(d => {
                const def = DOCS.find(dd => dd.label === d.label)
                if (def?.batchStep === docDef.batchStep && d.status === 'idle') {
                  return { ...d, status: 'working' }
                }
                return d
              })
            }
            // When all N for this doc are done, advance the next non-sibling doc
            const updatedDoc = updated.find(d => d.label === label)
            if (updatedDoc?.status === 'done' && docDef) {
              const activeLabels = activeDocsRef.current
              const idx = activeLabels.indexOf(label)
              let nextIdx = idx + 1
              while (nextIdx < activeLabels.length) {
                const def = DOCS.find(d => d.label === activeLabels[nextIdx])
                if (def?.batchStep !== docDef.batchStep) break
                nextIdx++
              }
              if (nextIdx < activeLabels.length) {
                const nextDef = DOCS.find(d => d.label === activeLabels[nextIdx])
                updated = updated.map(d => {
                  const def = DOCS.find(dd => dd.label === d.label)
                  if (def?.batchStep === nextDef?.batchStep && d.status === 'idle') {
                    return { ...d, status: 'working' }
                  }
                  return d
                })
              }
            }
            return updated
          })
          return
        }

        // RETRY:PO:1
        const retryM = msg.match(/RETRY:(\w+):(\d+)/)
        if (retryM) {
          patchDoc(retryM[1], { retries: parseInt(retryM[2]) })
          return
        }

        // FAILED line — mark all docs sharing this batchStep as error
        const failedM = msg.match(/::TestConnectorWagoBatchFlow::(test_batch_\w+)\s+FAILED/)
        if (failedM) {
          const failedBatchStep = failedM[1]
          const failedDocs = DOCS.filter(d => d.batchStep === failedBatchStep && activeDocsRef.current.includes(d.label))
          failedDocs.forEach(doc => patchDoc(doc.label, { status: 'error' }))
          const firstIdx = Math.min(...failedDocs.map(d => activeDocsRef.current.indexOf(d.label)).filter(i => i >= 0))
          for (let j = firstIdx + failedDocs.length; j < activeDocsRef.current.length; j++) {
            patchDoc(activeDocsRef.current[j], { status: 'skipped' })
          }
        }
      },
      () => {
        setRunning(false)
        setDocs(prev => prev.map(d =>
          d.status === 'working' ? { ...d, status: 'error' } :
          d.status === 'idle'    ? { ...d, status: 'skipped' } : d
        ))
      },
      (err: Error) => {
        setRunning(false)
        setDocs(prev => prev.map(d =>
          d.status === 'working' ? { ...d, status: 'error' } :
          d.status === 'idle'    ? { ...d, status: 'skipped' } : d
        ))
      },
      batchSteps,
    )
  }, [count, stopAt, patchDoc])

  const isDone = !running && docs.length > 0
  const allPassed = isDone && docs.every(d => d.status === 'done' || d.status === 'skipped')
  const anyFailed = isDone && docs.some(d => d.status === 'error')

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
            {running ? 'Running…' : docs.length > 0 ? 'Run again' : 'Run'}
          </Button>
        </div>
      </div>

      {/* ── Activity feed ─────────────────────────────────────── */}
      {docs.length > 0 && (
        <div className="flex-1 min-h-0 overflow-auto flex flex-col gap-4">

          {/* Done banner */}
          {isDone && (
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-[12px] font-medium ${
              !anyFailed
                ? 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                : 'bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
            }`}>
              {!anyFailed
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

          {/* Doc-type rows */}
          <div className="flex flex-col">
            {docs.map((doc, si) => {
              const docDef = DOCS.find(d => d.label === doc.label)!
              const isLast = si === docs.length - 1

              return (
                <div key={doc.label} className="flex gap-3">
                  {/* Timeline spine */}
                  <div className="flex flex-col items-center w-6 shrink-0">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                      doc.status === 'done'    ? 'bg-emerald-100 dark:bg-emerald-900/40' :
                      doc.status === 'error'   ? 'bg-red-100 dark:bg-red-900/40' :
                      doc.status === 'working' ? 'bg-[#3F51B5]/10 dark:bg-[#3F51B5]/20' :
                      'bg-gray-100 dark:bg-gray-800'
                    }`}>
                      {doc.status === 'done'    && <CheckCircle2 className="size-3.5 text-emerald-600 dark:text-emerald-400" />}
                      {doc.status === 'error'   && <XCircle className="size-3.5 text-red-500" />}
                      {doc.status === 'working' && <Loader2 className="size-3 text-[#5C6BC0] animate-spin" />}
                      {(doc.status === 'idle' || doc.status === 'skipped') && <div className="size-2 rounded-full bg-gray-300 dark:bg-gray-600" />}
                    </div>
                    {!isLast && (
                      <div className={`w-px flex-1 my-1 ${
                        doc.status === 'done' ? 'bg-emerald-200 dark:bg-emerald-800/50' : 'bg-gray-200 dark:bg-gray-700'
                      }`} />
                    )}
                  </div>

                  {/* Content */}
                  <div className={`flex flex-col pb-4 ${isLast ? 'pb-0' : ''}`}>
                    {(doc.status === 'idle' || doc.status === 'skipped') && (
                      <span className={`text-[12px] leading-6 ${doc.status === 'skipped' ? 'text-gray-400 dark:text-gray-500 line-through' : 'text-gray-400 dark:text-gray-600'}`}>
                        {doc.label}
                      </span>
                    )}

                    {doc.status === 'working' && (
                      <span className="text-[12px] text-gray-500 dark:text-gray-400 leading-6 flex items-center gap-2">
                        Working on <span className="font-medium text-gray-700 dark:text-gray-200">{doc.label}</span>
                        {doc.docIds.length > 0 && (
                          <span className="text-[10px] text-[#5C6BC0] font-medium">{doc.docIds.length}/{doc.total}</span>
                        )}
                        {doc.retries > 0 && (
                          <span className="text-[10px] text-amber-500 font-medium">retry {doc.retries}</span>
                        )}
                      </span>
                    )}

                    {doc.status === 'done' && (
                      <div className="flex flex-col gap-0.5">
                        <div className="flex items-center gap-2 leading-6">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${docDef.colors}`}>
                            {doc.label}
                          </span>
                          <span className="text-[12px] text-gray-500 dark:text-gray-400">{doc.docIds.length > 1 ? `${doc.docIds.length} created` : 'created'}</span>
                          {doc.retries > 0 && (
                            <span className="text-[10px] text-amber-500">({doc.retries} retr{doc.retries === 1 ? 'y' : 'ies'})</span>
                          )}
                        </div>
                        {/* Show ref IDs as pills */}
                        {doc.docIds.length > 0 && (
                          <div className="flex flex-wrap gap-1 pl-0.5 pb-1">
                            {doc.docIds.map((id, idx) => (
                              <span key={idx} className="text-[11px] font-mono text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded">
                                {id}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {doc.status === 'error' && (
                      <div className="flex items-center gap-2 leading-6">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300 border-red-200 dark:border-red-800">
                          {doc.label}
                        </span>
                        <span className="text-[12px] text-red-500">failed</span>
                        {doc.docIds.length > 0 && (
                          <span className="text-[11px] text-gray-400">({doc.docIds.length}/{doc.total} created before failure)</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
