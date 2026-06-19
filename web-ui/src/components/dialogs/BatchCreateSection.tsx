'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Loader2, Database, CheckCircle2, XCircle, Play, Info } from 'lucide-react'
import { startBatchCreate, exportBatchExcel, type SSEEvent } from '@/lib/api'
import { BatchCompleteDialog } from './BatchCompleteDialog'

interface BatchTarget {
  module: string
  subModule: string
  label: string
}

const MODULE_TO_BATCH: Record<string, BatchTarget | null> = {
  employee:     { module: 'registration', subModule: 'employee', label: 'Registration → Employee' },
  supplier:     { module: 'registration', subModule: 'supplier', label: 'Registration → Supplier' },
  customer:     { module: 'registration', subModule: 'customer', label: 'Registration → Customer' },
  agent:        { module: 'registration', subModule: 'agent', label: 'Registration → Agent' },
  farmer:       { module: 'registration', subModule: 'farmer', label: 'Registration → Farmer' },
  directors:    { module: 'registration', subModule: 'directors', label: 'Document → Directors' },
  member:       { module: 'registration', subModule: 'member', label: 'Document → Member' },
  'constituent-documents':  { module: 'registration', subModule: 'constituent_documents', label: 'Document → Constituent Documents' },
  'miscellaneous-documents': { module: 'registration', subModule: 'miscellaneous_documents', label: 'Document → Miscellaneous Documents' },
  'register-of-loan':       { module: 'registration', subModule: 'register_of_loan', label: 'Document → Register of Loan' },
  'register-charges':       { module: 'registration', subModule: 'register_charges', label: 'Document → Register Charges' },
  'company-onboarding': { module: 'company_onboarding', subModule: 'company', label: 'Company Onboarding' },
  uom:            { module: 'common_settings', subModule: 'uom', label: 'Common Settings → UOM' },
  'uom-conversion':  { module: 'common_settings', subModule: 'uom_conversion', label: 'Common Settings → UOM Conversion' },
  designation:    { module: 'common_settings', subModule: 'designation', label: 'Common Settings → Designation' },
  bank:           { module: 'common_settings', subModule: 'bank', label: 'Common Settings → Bank' },
  seasons:        { module: 'common_settings', subModule: 'season', label: 'Common Settings → Seasons' },
  'hsn-sac':      { module: 'common_settings', subModule: 'hsn_sac', label: 'Common Settings → HSN SAC' },
  'error-code-master': { module: 'common_settings', subModule: 'error_code_mst', label: 'Common Settings → Error Code Master' },
  'vehicle-master':    { module: 'common_settings', subModule: 'vehicle_master', label: 'Common Settings → Vehicle Master' },
  'tax-authority':     { module: 'common_settings', subModule: 'tax_authority', label: 'Common Settings → Tax Authority' },
  'tax-rate':     { module: 'common_settings', subModule: 'tax_rate', label: 'Common Settings → Tax Rate' },
  'item-attribute':         { module: 'commodity_settings', subModule: 'item_attribute', label: 'Commodity Settings → Item Attribute' },
  'quality-parameter-def':   { module: 'commodity_settings', subModule: 'quality_parameter_master', label: 'Commodity Settings → Quality Parameter Master' },
  'commodity-quality-param': { module: 'commodity_settings', subModule: 'commodity_quality_parameter', label: 'Commodity Settings → Commodity Quality Parameter' },
  'commodity-base-rate':     { module: 'commodity_settings', subModule: 'commodity_base_rate', label: 'Commodity Settings → Commodity Base Rate' },
  'item-master':    { module: 'commodity_settings', subModule: 'item_master', label: 'Commodity Settings → Item Master' },
  'crop-master':    { module: 'commodity_settings', subModule: 'crop_master', label: 'Commodity Settings → Crop Master' },
  'services-master': { module: 'commodity_settings', subModule: 'services_master', label: 'Commodity Settings → Services Master' },
  'item-category':  { module: 'commodity_settings', subModule: 'item_category', label: 'Commodity Settings → Item Category' },
  'item-group':     { module: 'commodity_settings', subModule: 'item_group', label: 'Commodity Settings → Item Group' },
  'purchase-order':    { module: 'private_b2b', subModule: 'purchase_order', label: 'Purchase → Purchase Order' },
  'goods-receipt-note': { module: 'private_b2b', subModule: 'goods_receipt_note', label: 'Purchase → Goods Receipt Note' },
  'gate-pass':         { module: 'private_b2b', subModule: 'gate_pass', label: 'Purchase → Gate Pass' },
  'quality-check':     { module: 'private_b2b', subModule: 'quality_check', label: 'Purchase → Quality Check' },
}

interface Props {
  moduleId: string
  erpToken: string
  erpTenantId: string
  onNeedsToken: () => void
  onClearToken: () => void
}

function formatTime(d: Date): string {
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

export function BatchCreateSection({ moduleId, erpToken, erpTenantId, onNeedsToken, onClearToken }: Props) {
  const [count, setCount] = useState(10)
  const [running, setRunning] = useState(false)
  const [logs, setLogs] = useState<{ text: string; ts: Date; isErr: boolean; isDone: boolean }[]>([])
  const [created, setCreated] = useState(0)
  const [failed, setFailed] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const [batchRunId, setBatchRunId] = useState<string | null>(null)
  const [showCompleteDialog, setShowCompleteDialog] = useState(false)
  const [authError, setAuthError] = useState(false)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const startTimeRef = useRef<number>(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const target = MODULE_TO_BATCH[moduleId]

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  useEffect(() => {
    if (running) {
      startTimeRef.current = Date.now()
      timerRef.current = setInterval(() => {
        setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000))
      }, 200)
    } else {
      if (timerRef.current) clearInterval(timerRef.current)
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [running])

  const handleRun = useCallback(() => {
    if (!target) return
    if (!erpToken) {
      onNeedsToken()
      return
    }
    setRunning(true)
    setLogs([])
    setCreated(0)
    setFailed(0)
    setElapsed(0)
    setBatchRunId(null)
    setShowCompleteDialog(false)
    setAuthError(false)

    startBatchCreate(
      target.module,
      target.subModule,
      count,
      erpToken,
      erpTenantId,
      (event: SSEEvent) => {
        const ts = event.timestamp ? new Date(event.timestamp) : new Date()
        const text = event.message
        const isErr = text.includes('FAILED') || text.includes('ERROR')
        const isDone = text.includes('complete')
        setLogs((prev) => [...prev, { text, ts, isErr, isDone }])
        if (event.type === 'run_end') {
          const m = event.message.match(/(\d+) created/)
          const f = event.message.match(/(\d+) failed/)
          if (m) setCreated(parseInt(m[1]))
          if (f) setFailed(parseInt(f[1]))
        }
        if (event.type === 'auth_error') {
          setAuthError(true)
        }
      },
      (runId: string | null) => {
        setRunning(false)
        if (runId) setBatchRunId(runId)
        setShowCompleteDialog(true)
      },
      (err) => {
        setLogs((prev) => [...prev, { text: `ERROR: ${err.message}`, ts: new Date(), isErr: true, isDone: false }])
        setRunning(false)
      },
    )
  }, [target, erpToken, erpTenantId, count, onNeedsToken])

  const handleDownload = useCallback(async () => {
    if (!batchRunId) return
    try {
      await exportBatchExcel(batchRunId)
    } catch {
      setLogs((prev) => [...prev, { text: 'ERROR: Failed to download Excel', ts: new Date(), isErr: true, isDone: false }])
    }
  }, [batchRunId])

  const total = created + failed
  const progress = running && total > 0 ? Math.round((total / Math.max(total, 1)) * 100) : (created + failed > 0 ? 100 : 0)
  const barPercent = running ? Math.min(Math.round(((created + failed) / (count || 1)) * 100), 100) : (created + failed > 0 ? 100 : 0)

  return (
    <div className="border border-gray-300 dark:border-gray-500/70 rounded-lg overflow-hidden shadow-sm">
      <div className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950/30 dark:to-blue-950/20 border-b border-gray-300 dark:border-gray-500/70">
        <Database className="size-4 text-indigo-600 dark:text-indigo-400" />
        <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200 flex-1">Batch Data Creation</span>
      </div>

      <div className="p-4 space-y-4">
        {!target ? (
          <div className="flex flex-col items-center gap-3 py-8 text-gray-400 dark:text-gray-500">
            <Info className="size-8" />
            <span className="text-[13px]">Batch creation not available for this module</span>
          </div>
        ) : (
          <>
            {/* Module label */}
            <div className="flex items-center gap-2 bg-indigo-50/60 dark:bg-indigo-950/20 rounded-md px-3 py-2">
              <span className="text-[11px] font-medium text-indigo-500 dark:text-indigo-400 uppercase tracking-wider">Creating</span>
              <span className="text-[13px] font-semibold text-gray-800 dark:text-gray-100">{target.label}</span>
            </div>

            {/* Controls row */}
            <div className="flex items-end gap-3">
              <div className="space-y-1 w-20">
                <Label className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">Count</Label>
                <Input
                  type="number"
                  min={1}
                  max={500}
                  value={count}
                  disabled={running}
                  onChange={(e) => setCount(Math.max(1, Math.min(500, parseInt(e.target.value) || 10)))}
                  className="h-8 text-[12px]"
                />
              </div>
              <Button
                onClick={handleRun}
                disabled={running}
                className="h-8 text-[12px] bg-indigo-600 hover:bg-indigo-700 cursor-pointer gap-1.5"
              >
                {running ? <Loader2 className="size-3.5 animate-spin" /> : <Play className="size-3.5" />}
                {running ? 'Creating...' : 'Create'}
              </Button>
            </div>

            {/* Progress bar + counters */}
            {(running || created + failed > 0) && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
                  <span>
                    {running ? 'Creating records...' : 'Complete'}
                  </span>
                  <span>{barPercent}%</span>
                </div>
                <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500 ease-out"
                    style={{
                      width: `${barPercent}%`,
                      background: failed > 0 && barPercent === 100
                        ? 'linear-gradient(90deg, #22c55e 0%, #ef4444 100%)'
                        : barPercent === 100
                        ? '#22c55e'
                        : 'linear-gradient(90deg, #6366f1, #8b5cf6)',
                    }}
                  />
                </div>
                <div className="flex items-center gap-4 text-[12px]">
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="size-3 text-green-500" />
                    <span className="text-green-600 dark:text-green-400 font-medium">{created}</span>
                    <span className="text-gray-500 dark:text-gray-400">created</span>
                  </span>
                  {failed > 0 && (
                    <span className="flex items-center gap-1">
                      <XCircle className="size-3 text-red-500" />
                      <span className="text-red-600 dark:text-red-400 font-medium">{failed}</span>
                      <span className="text-gray-500 dark:text-gray-400">failed</span>
                    </span>
                  )}
                  <span className="text-gray-400 dark:text-gray-500">
                    {running
                      ? `${elapsed}s`
                      : `${elapsed}s`
                    }
                  </span>
                </div>
              </div>
            )}

            {/* Log output */}
            {logs.length > 0 && (
              <ScrollArea className="h-36 rounded-lg bg-gray-950 p-3 border border-gray-800">
                <div className="space-y-1">
                  {logs.map((line, i) => (
                    <div
                      key={i}
                      className={`text-[11px] font-mono leading-5 ${line.isErr ? 'text-red-400' : line.isDone ? 'text-emerald-400' : 'text-gray-300'}`}
                    >
                      <span className="text-gray-600 mr-2 select-none">{formatTime(line.ts)}</span>
                      {line.isErr ? (
                        <XCircle className="size-2.5 inline mr-1 -mt-0.5 text-red-400" />
                      ) : line.isDone ? (
                        <CheckCircle2 className="size-2.5 inline mr-1 -mt-0.5 text-emerald-400" />
                      ) : null}
                      {line.text}
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              </ScrollArea>
            )}

            {/* Auth error banner */}
            {authError && (
              <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-3 space-y-2">
                <p className="text-[12px] text-red-700 dark:text-red-400 font-medium">ERP token is invalid or expired</p>
                <div className="flex gap-2">
                  <Button onClick={onNeedsToken} className="h-7 text-[11px] bg-red-600 hover:bg-red-700 cursor-pointer">
                    Update Token
                  </Button>
                  <Button onClick={onClearToken} variant="outline" className="h-7 text-[11px] border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 cursor-pointer">
                    Reset Token
                  </Button>
                </div>
              </div>
            )}

            {/* Batch Complete Dialog */}
            <BatchCompleteDialog
              open={showCompleteDialog}
              onClose={() => setShowCompleteDialog(false)}
              created={created}
              failed={failed}
              elapsedSeconds={elapsed}
              onDownload={handleDownload}
            />
          </>
        )}
      </div>
    </div>
  )
}
