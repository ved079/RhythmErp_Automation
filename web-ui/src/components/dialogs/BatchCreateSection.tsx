'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Database, CheckCircle2, XCircle, Play, Info, ShieldCheck, BadgeCheck, ChevronRight, ChevronDown, History, Download, RefreshCw, RotateCcw, Loader2, ListChecks, Tag, Plus } from 'lucide-react'
import Spinner from '@/components/ui/Spinner'
import { startBatchCreate, exportBatchExcel, fetchBatchHistory, type SSEEvent, type BatchRunSummary } from '@/lib/api'
import { notifySuccess } from '@/lib/notify'
import { BatchCompleteDialog } from './BatchCompleteDialog'
import { FarmerBatchConfig, type FarmerConfig } from './FarmerBatchConfig'

interface BatchTarget {
  module: string
  subModule: string
  label: string
}

export const MODULE_TO_BATCH: Record<string, BatchTarget | null> = {
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
  'company-onboarding': { module: 'company_onboarding', subModule: 'company_onboarding', label: 'Company Onboarding' },
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
  'purchase-booking':  { module: 'private_b2b', subModule: 'purchase_booking', label: 'Purchase → Purchase Booking' },
  'purchase-order':    { module: 'private_b2b', subModule: 'purchase_order', label: 'Purchase → Purchase Order' },
  'goods-receipt-note': { module: 'private_b2b', subModule: 'goods_receipt_note', label: 'Purchase → Goods Receipt Note' },
  'gate-pass':         { module: 'private_b2b', subModule: 'gate_pass', label: 'Purchase → Gate Pass' },
  'quality-check':     { module: 'private_b2b', subModule: 'quality_check', label: 'Purchase → Quality Check' },
  'direct-pb-flow':    { module: 'private_b2b', subModule: 'direct_pb_flow',   label: 'Purchase Flows → Direct PB Flow' },
  'po-qc-pb-flow':     { module: 'private_b2b', subModule: 'po_qc_pb_flow',   label: 'Purchase Flows → PO → QC → PB Flow' },
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

function formatDateTime(epochSecs: number): string {
  const d = new Date(epochSecs * 1000)
  return d.toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true })
}

function labelForModule(module: string, subModule: string): string {
  return `${subModule.replace(/_/g, ' ')}`.replace(/\b\w/g, c => c.toUpperCase())
}

export function BatchCreateSection({ moduleId, erpToken, erpTenantId, onNeedsToken, onClearToken }: Props) {
  const [tab, setTab] = useState<'create' | 'history'>('create')
  const [count, setCount] = useState(10)
  const [itemsPerPb, setItemsPerPb] = useState(20)
  const [qtyPerChain, setQtyPerChain] = useState(24)
  const [running, setRunning] = useState(false)
  const [logs, setLogs] = useState<{ text: string; ts: Date; isErr: boolean; isDone: boolean }[]>([])
  const [created, setCreated] = useState(0)
  const [failed, setFailed] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const [batchRunId, setBatchRunId] = useState<string | null>(null)
  const [showCompleteDialog, setShowCompleteDialog] = useState(false)
  const [authError, setAuthError] = useState(false)
  const [attrNumber, setAttrNumber] = useState(1)
  const [farmerConfig, setFarmerConfig] = useState<FarmerConfig>({
    farmer_types: ['fpc_member'],
    overrides: {},
  })
  const [history, setHistory] = useState<BatchRunSummary[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null)
  const [cbrLocations, setCbrLocations] = useState<{ id: number; name: string; occupied: boolean }[]>([])
  const [selectedLocations, setSelectedLocations] = useState<Set<number>>(new Set())
  const [cbrLocationsLoading, setCbrLocationsLoading] = useState(false)
  const [showCbrCreateLocations, setShowCbrCreateLocations] = useState(false)
  const [newLocationCount, setNewLocationCount] = useState(5)
  const [creatingLocations, setCreatingLocations] = useState(false)
  const [cbrCreateMode, setCbrCreateMode] = useState<'auto' | 'manual'>('auto')
  const [manualLocationInputs, setManualLocationInputs] = useState<string[]>([''])
  // Item Master: category picker
  const [itemCatMode, setItemCatMode] = useState<'random' | 'pick'>('random')
  const [itemCategories, setItemCategories] = useState<{ name: string; id: number; count: number }[]>([])
  const [itemCatLoading, setItemCatLoading] = useState(false)
  const [itemCatFetched, setItemCatFetched] = useState(false)
  const [selectedItemCat, setSelectedItemCat] = useState<{ name: string; id: number; count: number } | null>(null)
  // UOM Conversion: all-pairs mode
  const [uomCount, setUomCount] = useState<number | null>(null)
  const [uomLoading, setUomLoading] = useState(false)
  const [uomFetched, setUomFetched] = useState(false)
  const [uomFactor, setUomFactor] = useState('1')

  const [cqpPreview, setCqpPreview] = useState<{ total_items: number; existing_count: number; missing: { id: number; name: string }[] } | null>(null)
  const [cqpPreviewLoading, setCqpPreviewLoading] = useState(false)
  const [showCqpConfirm, setShowCqpConfirm] = useState(false)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const startTimeRef = useRef<number>(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true)
    try {
      const data = await fetchBatchHistory()
      // Filter to runs for this module
      const target = MODULE_TO_BATCH[moduleId]
      setHistory(target ? data.filter(r => r.sub_module === target.subModule) : data)
    } catch {
      setHistory([])
    } finally {
      setHistoryLoading(false)
    }
  }, [moduleId])

  useEffect(() => {
    if (tab === 'history') loadHistory()
  }, [tab, loadHistory])

  const target = MODULE_TO_BATCH[moduleId]

  const fetchCbrLocations = useCallback(async (keepSelection = false) => {
    if (target?.subModule !== 'commodity_base_rate' || !erpToken) return
    setCbrLocationsLoading(true)
    try {
      const csrfToken = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/)?.[1] ?? ''
      const res = await fetch('/api/proxy?path=batch-create/cbr-locations', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': decodeURIComponent(csrfToken) },
        body: JSON.stringify({ erp_token: erpToken, erp_tenant_id: erpTenantId }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const locs = Array.isArray(data.locations) ? data.locations : []
      setCbrLocations(locs)
      if (!keepSelection) {
        const autoSelected = new Set<number>()
        for (const loc of locs) {
          if (!loc.occupied) autoSelected.add(loc.id)
        }
        setSelectedLocations(autoSelected)
      }
    } catch {
      setCbrLocations([])
      setSelectedLocations(new Set())
    } finally {
      setCbrLocationsLoading(false)
    }
  }, [target?.subModule, erpToken, erpTenantId])

  useEffect(() => {
    if (target?.subModule !== 'commodity_base_rate' || !erpToken) {
      setCbrLocations([])
      setSelectedLocations(new Set())
      setCbrLocationsLoading(false)
      return
    }
    fetchCbrLocations(false)
  }, [target?.subModule, erpToken, erpTenantId, fetchCbrLocations])

  // Always-fresh refs so fetchItemCategories never uses a stale closure value
  const erpTokenRef = useRef(erpToken)
  const erpTenantIdRef = useRef(erpTenantId)
  useEffect(() => { erpTokenRef.current = erpToken }, [erpToken])
  useEffect(() => { erpTenantIdRef.current = erpTenantId }, [erpTenantId])

  // Reset item category state when token changes so a fresh fetch runs
  const prevTokenRef = useRef(erpToken)
  useEffect(() => {
    if (prevTokenRef.current !== erpToken) {
      prevTokenRef.current = erpToken
      setItemCatFetched(false)
      setItemCategories([])
      setSelectedItemCat(null)
      setUomFetched(false)
      setUomCount(null)
    }
  }, [erpToken])

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

  const handleRun = useCallback((fillAll = false) => {
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

    let batchConfig: Record<string, unknown> | undefined
    if (target.subModule === 'farmer') {
      batchConfig = farmerConfig
    } else if (target.subModule === 'item_master') {
      batchConfig = selectedItemCat ? { item_category: selectedItemCat.id } : {}
    } else if (target.subModule === 'item_attribute') {
      batchConfig = { attr_number: attrNumber }
    } else if (target.subModule === 'direct_pb_flow') {
      batchConfig = { item_range: '58-77', items_per_pb: itemsPerPb }
    } else if (target.subModule === 'po_qc_pb_flow') {
      batchConfig = { items_per_chain: qtyPerChain }
    } else if (target.subModule === 'uom_conversion') {
      batchConfig = { conversion_factor: parseFloat(uomFactor) || 1 }
    } else if (target.subModule === 'commodity_base_rate') {
      batchConfig = { selected_location_ids: Array.from(selectedLocations) }
    } else if (fillAll) {
      batchConfig = { fill_all: true }
    }
    startBatchCreate(
      target.module,
      target.subModule,
      (fillAll || target.subModule === 'uom_conversion') ? 9999 : count,
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
        notifySuccess('Batch Create Complete', `${created} created, ${failed} failed`)
      },
      (err) => {
        setLogs((prev) => [...prev, { text: `ERROR: ${err.message}`, ts: new Date(), isErr: true, isDone: false }])
        setRunning(false)
      },
      undefined,
      batchConfig,
      target.subModule === 'commodity_base_rate' ? Array.from(selectedLocations) : undefined,
    )
  }, [target, erpToken, erpTenantId, count, itemsPerPb, qtyPerChain, farmerConfig, onNeedsToken, selectedLocations])

  const fetchItemCategories = useCallback(async () => {
    if (!erpTokenRef.current) { onNeedsToken(); return }
    setItemCatLoading(true)
    let options: { name: string; id: number; count: number }[] = []
    for (let attempt = 0; attempt < 8; attempt++) {
      if (attempt > 0) await new Promise(r => setTimeout(r, 3000))
      try {
        const csrfToken = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/)?.[1] ?? ''
        const res = await fetch('/api/proxy?path=batch-create/fetch-fk', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': decodeURIComponent(csrfToken) },
          body: JSON.stringify({ erp_token: erpTokenRef.current, erp_tenant_id: erpTenantIdRef.current, screen: 'Item Category' }),
        })
        const data = await res.json()
        options = data.options ?? []
        if (options.length > 0) break
      } catch { /* retry */ }
    }
    setItemCategories(options)
    setItemCatFetched(true)
    setItemCatLoading(false)
  }, [onNeedsToken])

  // Auto-fetch categories when token becomes available while in pick mode
  useEffect(() => {
    if (itemCatMode === 'pick' && erpToken && !itemCatFetched && !itemCatLoading) {
      fetchItemCategories()
    }
  }, [itemCatMode, erpToken, itemCatFetched, itemCatLoading, fetchItemCategories])

  // UOM Conversion: fetch UOM count from ERP when module is active + token available
  const fetchUomCount = useCallback(async () => {
    if (!erpTokenRef.current) return
    setUomLoading(true)
    let n = 0
    for (let attempt = 0; attempt < 8; attempt++) {
      if (attempt > 0) await new Promise(r => setTimeout(r, 3000))
      try {
        const csrfToken = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/)?.[1] ?? ''
        const res = await fetch('/api/proxy?path=batch-create/fetch-fk', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': decodeURIComponent(csrfToken) },
          body: JSON.stringify({ erp_token: erpTokenRef.current, erp_tenant_id: erpTenantIdRef.current, screen: 'UOM' }),
        })
        const data = await res.json()
        n = (data.options ?? []).length
        if (n > 0) break
      } catch { /* retry */ }
    }
    setUomCount(n)
    setUomFetched(true)
    setUomLoading(false)
  }, [])

  useEffect(() => {
    if (target?.subModule === 'uom_conversion' && erpToken && !uomFetched && !uomLoading) {
      fetchUomCount()
    }
  }, [target?.subModule, erpToken, uomFetched, uomLoading, fetchUomCount])

  const handleFillAllPreview = useCallback(async () => {
    if (!erpToken) { onNeedsToken(); return }
    setCqpPreviewLoading(true)
    setCqpPreview(null)
    try {
      const csrfToken = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/)?.[1] ?? ''
      const res = await fetch('/api/proxy?path=batch-create/cqp-fill-preview', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': decodeURIComponent(csrfToken) },
        body: JSON.stringify({ erp_token: erpToken, erp_tenant_id: erpTenantId, module: 'commodity_settings', sub_module: 'commodity_quality_parameter', count: 9999 }),
      })
      const data = await res.json()
      console.log('[CQP-PREVIEW] response:', data)
      setCqpPreview({ total_items: data.total_items ?? 0, existing_count: data.existing_count ?? 0, missing: data.missing ?? [] })
      setShowCqpConfirm(true)
    } catch {
      // silent
    } finally {
      setCqpPreviewLoading(false)
    }
  }, [erpToken, erpTenantId, onNeedsToken])

  const handleDownload = useCallback(async () => {
    if (!batchRunId) return
    try {
      await exportBatchExcel(batchRunId)
    } catch {
      setLogs((prev) => [...prev, { text: 'ERROR: Failed to download Excel', ts: new Date(), isErr: true, isDone: false }])
    }
  }, [batchRunId])

  const handleHistoryDownload = useCallback(async (runId: string) => {
    setDownloadingId(runId)
    try {
      await exportBatchExcel(runId)
    } catch {
      // silent
    } finally {
      setDownloadingId(null)
    }
  }, [])

  const total = created + failed
  const progress = running && total > 0 ? Math.round((total / Math.max(total, 1)) * 100) : (created + failed > 0 ? 100 : 0)
  const barPercent = running ? Math.min(Math.round(((created + failed) / (count || 1)) * 100), 100) : (created + failed > 0 ? 100 : 0)

  return (
    <div className="border border-gray-300 dark:border-gray-500/70 rounded-lg shadow-sm overflow-visible">
      {/* Header + tabs */}
      <div className="bg-gradient-to-r from-[#3F51B5]/[0.07] to-[#3F51B5]/[0.03] dark:from-[#3F51B5]/20 dark:to-[#3F51B5]/10 border-b border-gray-300 dark:border-gray-500/70">
        <div className="flex items-center gap-2 px-4 pt-2.5 pb-0">
          <Database className="size-4 text-[#3F51B5] dark:text-[#7986CB] shrink-0" />
          <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200 flex-1">Batch Data Creation</span>
          <button onClick={() => { onClearToken(); onNeedsToken(); }} className="flex items-center gap-1 text-[11px] px-2 py-1 rounded-md cursor-pointer text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
            <RotateCcw className="size-3" />
            Reset Token
          </button>
        </div>
        <div className="flex gap-0 px-4 mt-2">
          {(['create', 'history'] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium border-b-2 transition-colors cursor-pointer ${
                tab === t
                  ? 'border-[#3F51B5] text-[#3F51B5] dark:text-[#7986CB]'
                  : 'border-transparent text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300'
              }`}
            >
              {t === 'create' ? <Play className="size-3" /> : <History className="size-3" />}
              {t === 'create' ? 'Create' : 'History'}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* History tab */}
        {tab === 'history' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-gray-500 dark:text-gray-400">
                {history.length > 0 ? `${history.length} run${history.length !== 1 ? 's' : ''}` : 'No runs yet'}
              </span>
              <button
                type="button"
                onClick={loadHistory}
                disabled={historyLoading}
                className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-[#3F51B5] cursor-pointer disabled:opacity-40"
              >
                <RefreshCw className={`size-3 ${historyLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>

            {historyLoading ? (
              <div className="flex items-center justify-center py-8 text-gray-400">
                <Loader2 className="size-4 animate-spin mr-2" />
                <span className="text-[12px]">Loading...</span>
              </div>
            ) : history.length === 0 ? (
              <div className="flex flex-col items-center gap-2 py-8 text-gray-400 dark:text-gray-500">
                <History className="size-7" />
                <span className="text-[12px]">No batch runs yet for this module</span>
              </div>
            ) : (
              <ScrollArea className="h-72">
                <div className="space-y-1.5">
                  {history.map((run) => {
                    const isExpanded = expandedRunId === run.run_id
                    const isFarmer = run.sub_module === 'farmer'
                    return (
                      <div key={run.run_id} className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                        {/* Run row */}
                        <div className="flex items-center gap-3 px-3 py-2.5 bg-white dark:bg-gray-800/50">
                          <div className={`size-2 rounded-full shrink-0 ${run.failed === 0 ? 'bg-emerald-500' : run.created === 0 ? 'bg-red-500' : 'bg-yellow-500'}`} />

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-[12px] font-medium text-gray-800 dark:text-gray-100">
                                {labelForModule(run.module, run.sub_module)}
                              </span>
                              <span className="text-[10px] text-gray-400 dark:text-gray-500">{formatDateTime(run.timestamp)}</span>
                            </div>
                            <div className="flex items-center gap-3 mt-0.5">
                              <span className="flex items-center gap-1 text-[11px]">
                                <CheckCircle2 className="size-3 text-emerald-500" />
                                <span className="text-emerald-600 dark:text-emerald-400 font-medium">{run.created}</span>
                                <span className="text-gray-400">created</span>
                              </span>
                              {run.failed > 0 && (
                                <span className="flex items-center gap-1 text-[11px]">
                                  <XCircle className="size-3 text-red-500" />
                                  <span className="text-red-500 font-medium">{run.failed}</span>
                                  <span className="text-gray-400">failed</span>
                                </span>
                              )}
                              <span className="text-[10px] text-gray-400">{run.elapsed_seconds}s</span>
                            </div>
                          </div>

                          <button
                            type="button"
                            onClick={() => handleHistoryDownload(run.run_id)}
                            disabled={downloadingId === run.run_id}
                            className="flex items-center gap-1 px-2 py-1 rounded text-[11px] border border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-[#3F51B5]/50 hover:text-[#3F51B5] dark:hover:text-[#7986CB] transition-colors cursor-pointer disabled:opacity-40 shrink-0"
                          >
                            {downloadingId === run.run_id ? <Loader2 className="size-3 animate-spin" /> : <Download className="size-3" />}
                            Excel
                          </button>

                          {isFarmer && (
                            <button
                              type="button"
                              onClick={() => setExpandedRunId(isExpanded ? null : run.run_id)}
                              className="p-1 text-gray-400 hover:text-[#3F51B5] cursor-pointer transition-colors shrink-0"
                            >
                              {isExpanded ? <ChevronDown className="size-3.5" /> : <ChevronRight className="size-3.5" />}
                            </button>
                          )}
                        </div>

                        {/* Farmer records table */}
                        {isFarmer && isExpanded && run.records.length > 0 && (
                          <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40">
                            <table className="w-full text-[11px]">
                              <thead>
                                <tr className="border-b border-gray-200 dark:border-gray-700">
                                  <th className="text-left px-3 py-1.5 text-[10px] text-gray-400 uppercase tracking-wider font-medium w-6">#</th>
                                  <th className="text-left px-2 py-1.5 text-[10px] text-gray-400 uppercase tracking-wider font-medium">Name</th>
                                  <th className="text-center px-2 py-1.5 text-[10px] text-gray-400 uppercase tracking-wider font-medium">Verified</th>
                                  <th className="text-center px-2 py-1.5 text-[10px] text-gray-400 uppercase tracking-wider font-medium">Approved</th>
                                  <th className="text-center px-2 py-1.5 text-[10px] text-gray-400 uppercase tracking-wider font-medium">Status</th>
                                </tr>
                              </thead>
                              <tbody>
                                {run.records.map((rec, idx) => {
                                  const verified = rec.status === 'verified' || rec.status === 'approved'
                                  const approved = rec.status === 'approved'
                                  return (
                                    <tr key={idx} className="border-b border-gray-100 dark:border-gray-800 last:border-0">
                                      <td className="px-3 py-1.5 text-gray-400">{idx + 1}</td>
                                      <td className="px-2 py-1.5 text-gray-700 dark:text-gray-200 font-medium max-w-[120px] truncate">{rec.name}</td>
                                      <td className="px-2 py-1.5 text-center">
                                        {verified
                                          ? <CheckCircle2 className="size-3.5 text-emerald-500 inline" />
                                          : <XCircle className="size-3.5 text-gray-300 dark:text-gray-600 inline" />}
                                      </td>
                                      <td className="px-2 py-1.5 text-center">
                                        {approved
                                          ? <CheckCircle2 className="size-3.5 text-emerald-500 inline" />
                                          : <XCircle className="size-3.5 text-gray-300 dark:text-gray-600 inline" />}
                                      </td>
                                      <td className="px-2 py-1.5 text-center">
                                        <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium ${
                                          rec.status === 'approved' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400' :
                                          rec.status === 'verified' ? 'bg-sky-100 dark:bg-sky-900/30 text-sky-700 dark:text-sky-400' :
                                          rec.status === 'failed'   ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400' :
                                                                       'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                                        }`}>
                                          {rec.status}
                                        </span>
                                      </td>
                                    </tr>
                                  )
                                })}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </ScrollArea>
            )}
          </div>
        )}

        {tab === 'create' && (
          <>
          {!target ? (
          <div className="flex flex-col items-center gap-3 py-8 text-gray-400 dark:text-gray-500">
            <Info className="size-8" />
            <span className="text-[13px]">Batch creation not available for this module</span>
          </div>
        ) : (
          <>
            {/* Module label */}
            <div className="flex items-center gap-2 bg-[#3F51B5]/[0.08] dark:bg-[#3F51B5]/10 rounded-md px-3 py-2">
              <span className="text-[11px] font-medium text-[#3F51B5] dark:text-[#7986CB] uppercase tracking-wider">Creating</span>
              <span className="text-[13px] font-semibold text-gray-800 dark:text-gray-100">{target.label}</span>
            </div>

            {/* CBR location picker — only after token is entered */}
            {target.subModule === 'commodity_base_rate' && !erpToken && (
              <div className="flex flex-col items-center gap-3 py-6 text-gray-400 dark:text-gray-500">
                <Info className="size-7" />
                <span className="text-[12px] text-center">Enter your ERP token to fetch available locations.</span>
                <Button onClick={onNeedsToken} className="h-8 text-[12px] bg-[#3F51B5] hover:bg-[#3949AB] cursor-pointer gap-1.5">
                  Enter Token
                </Button>
              </div>
            )}
            {target.subModule === 'commodity_base_rate' && erpToken && (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-800/60 border-b border-gray-200 dark:border-gray-700">
                  <span className="text-[11px] font-medium text-gray-500 dark:text-gray-400">
                    {cbrLocationsLoading ? 'Loading...' : `${cbrLocations.filter(l => !l.occupied).length} available`}
                  </span>
                  <button
                    type="button"
                    onClick={() => fetchCbrLocations(true)}
                    disabled={cbrLocationsLoading}
                    className="text-[10px] text-[#3F51B5] dark:text-[#7986CB] hover:underline cursor-pointer flex items-center gap-1 disabled:opacity-50"
                  >
                    <RefreshCw className={`size-3 ${cbrLocationsLoading ? 'animate-spin' : ''}`} />
                    Refresh
                  </button>
                </div>
                {/* Body */}
                <div className="p-2">
                  {cbrLocationsLoading && cbrLocations.length === 0 ? (
                    <div className="flex items-center justify-center gap-2 py-6 text-gray-400 dark:text-gray-500">
                      <Loader2 className="size-3.5 animate-spin" />
                      <span className="text-[11px]">Fetching locations from ERP...</span>
                    </div>
                  ) : (() => {
                    const available = cbrLocations.filter(l => !l.occupied)
                    const hasLocations = cbrLocations.length > 0
                    if (available.length === 0) {
                      return (
                        <div className="space-y-3 py-2">
                          {hasLocations && <div className="text-[11px] text-gray-400 dark:text-gray-500 text-center">All locations have CBR entries.</div>}
                          <Button
                            variant="outline"
                            onClick={() => setShowCbrCreateLocations(true)}
                            disabled={running}
                            className="w-full h-8 text-[11px] border-dashed border-[#3F51B5]/40 text-[#3F51B5] dark:text-[#7986CB] hover:bg-[#3F51B5]/10 cursor-pointer gap-1.5"
                          >
                            <Plus className="size-3" />
                            Add New Locations
                          </Button>
                        </div>
                      )
                    }
                    return (
                      <div className="space-y-2">
                        <ScrollArea className="" style={{ height: Math.min(Math.ceil(available.length / 3) * 32 + 8, 160) }}>
                          <div className="flex flex-wrap gap-1.5">
                            {available.map(loc => {
                              const selected = selectedLocations.has(loc.id)
                              return (
                                <button
                                  key={loc.id}
                                  type="button"
                                  onClick={() => {
                                    setSelectedLocations(prev => {
                                      const next = new Set(prev)
                                      if (next.has(loc.id)) next.delete(loc.id)
                                      else next.add(loc.id)
                                      return next
                                    })
                                  }}
                                  className={`px-2.5 py-1 rounded-full text-[11px] font-medium border transition-all cursor-pointer ${
                                    selected
                                      ? 'bg-[#3F51B5] dark:bg-[#5C6BC0] border-[#3F51B5] dark:border-[#5C6BC0] text-white shadow-sm'
                                      : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-[#3F51B5]/50 dark:hover:border-[#7986CB]/50'
                                  }`}
                                >
                                  {loc.name}
                                </button>
                              )
                            })}
                          </div>
                        </ScrollArea>
                        <div className="flex items-center justify-between border-t border-gray-100 dark:border-gray-800 pt-2">
                          <div className="flex items-center gap-2">
                            <button type="button" onClick={() => setSelectedLocations(new Set(available.map(l => l.id)))} className="text-[10px] text-[#3F51B5] dark:text-[#7986CB] hover:underline cursor-pointer">Select All</button>
                            <span className="text-gray-300 dark:text-gray-600 text-[10px]">|</span>
                            <button type="button" onClick={() => setSelectedLocations(new Set())} className="text-[10px] text-[#3F51B5] dark:text-[#7986CB] hover:underline cursor-pointer">None</button>
                          </div>
                          <span className="text-[10px] text-gray-400 dark:text-gray-500">{selectedLocations.size} selected</span>
                        </div>
                      </div>
                    )
                  })()}
                </div>
              </div>
            )}

            {/* Controls row */}
            <div className="flex items-end gap-3 flex-wrap">
              {target.subModule !== 'uom_conversion' && target.subModule !== 'commodity_base_rate' && (
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
              )}
              {target.subModule === 'direct_pb_flow' && (
                <div className="space-y-1 w-24">
                  <Label className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">Items / PB</Label>
                  <Input
                    type="number"
                    min={1}
                    max={20}
                    value={itemsPerPb}
                    disabled={running}
                    onChange={(e) => setItemsPerPb(Math.max(1, Math.min(20, parseInt(e.target.value) || 20)))}
                    className="h-8 text-[12px]"
                  />
                </div>
              )}
              {target.subModule === 'po_qc_pb_flow' && (
                <div className="space-y-1 w-24">
                  <Label className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">Items / Chain</Label>
                  <Input
                    type="number"
                    min={1}
                    max={10000}
                    value={qtyPerChain}
                    disabled={running}
                    onChange={(e) => setQtyPerChain(Math.max(1, parseInt(e.target.value) || 100))}
                    className="h-8 text-[12px]"
                  />
                </div>
              )}
              <Button
                onClick={() => handleRun(false)}
                disabled={running || (target.subModule === 'commodity_base_rate' && selectedLocations.size === 0)}
                className="h-8 text-[12px] bg-[#3F51B5] hover:bg-[#3949AB] cursor-pointer gap-1.5"
              >
                {running ? <Loader2 className="size-3.5 animate-spin" /> : <Play className="size-3.5" />}
                {running ? 'Creating...' : target.subModule === 'uom_conversion' ? 'Create All Pairs' : 'Create'}
              </Button>
              {target.subModule === 'commodity_quality_parameter' && (
                <Button
                  onClick={handleFillAllPreview}
                  disabled={running || cqpPreviewLoading}
                  variant="outline"
                  className="h-8 text-[12px] border-[#3F51B5]/40 text-[#3F51B5] dark:text-[#7986CB] hover:bg-[#3F51B5]/10 cursor-pointer gap-1.5"
                >
                  {cqpPreviewLoading ? <Loader2 className="size-3.5 animate-spin" /> : <ListChecks className="size-3.5" />}
                  {cqpPreviewLoading ? 'Checking...' : 'Fill All Items'}
                </Button>
              )}
            </div>

            {/* UOM Conversion: all-pairs panel */}
            {target.subModule === 'uom_conversion' && (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 space-y-3">
                {/* Preview line */}
                <div className="flex items-center gap-2 text-[12px]">
                  {uomLoading ? (
                    <>
                      <Loader2 className="size-3.5 animate-spin text-[#3F51B5]" />
                      <span className="text-gray-400">Fetching UOMs from ERP...</span>
                    </>
                  ) : uomFetched && uomCount !== null ? (
                    <span className="text-gray-600 dark:text-gray-300">
                      <span className="font-semibold text-[#3F51B5] dark:text-[#7986CB]">{uomCount} UOMs</span>
                      {' '}found → up to{' '}
                      <span className="font-semibold">{uomCount * (uomCount - 1)}</span>
                      {' '}pairs will be created{' '}
                      <span className="text-gray-400">(existing skipped automatically)</span>
                    </span>
                  ) : !erpToken ? (
                    <span className="text-gray-400 text-[11px]">Set your ERP token to load UOM count</span>
                  ) : (
                    <span className="text-gray-400 text-[11px]">Loading...</span>
                  )}
                  {uomFetched && (
                    <button onClick={fetchUomCount} className="ml-auto text-[11px] text-gray-400 hover:text-[#3F51B5] hover:underline cursor-pointer shrink-0">
                      Refresh
                    </button>
                  )}
                </div>
                {/* Factor input */}
                <div className="flex items-center gap-3">
                  <Label className="text-[11px] text-gray-500 dark:text-gray-400 font-medium whitespace-nowrap">Conversion Factor</Label>
                  <Input
                    type="number"
                    min={0.0001}
                    step="any"
                    value={uomFactor}
                    disabled={running}
                    onChange={(e) => setUomFactor(e.target.value)}
                    className="h-8 text-[12px] w-28"
                  />
                  <span className="text-[11px] text-gray-400">applied to all pairs</span>
                </div>
              </div>
            )}

            {/* Item Master: category picker */}
            {target.subModule === 'item_master' && (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 space-y-2.5">
                <div className="flex items-center gap-2">
                  <Tag className="size-3.5 text-[#3F51B5] dark:text-[#7986CB] shrink-0" />
                  <span className="text-[11px] font-medium text-gray-600 dark:text-gray-300">Item Category</span>
                  <div className="flex items-center gap-1 ml-auto rounded-md border border-gray-200 dark:border-gray-700 overflow-hidden">
                    {(['random', 'pick'] as const).map(mode => (
                      <button
                        key={mode}
                        type="button"
                        disabled={running}
                        onClick={() => { setItemCatMode(mode); if (mode === 'pick' && !itemCatFetched) fetchItemCategories() }}
                        className={`px-2.5 py-1 text-[11px] font-medium transition-colors cursor-pointer ${
                          itemCatMode === mode
                            ? 'bg-[#3F51B5] text-white'
                            : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                        }`}
                      >
                        {mode === 'random' ? 'Random' : 'Pick'}
                      </button>
                    ))}
                  </div>
                </div>

                {itemCatMode === 'pick' && (
                  <div>
                    {itemCatLoading ? (
                      <div className="flex items-center gap-2 text-[11px] text-gray-400 px-1">
                        <Loader2 className="size-3 animate-spin" />
                        Fetching categories from ERP...
                      </div>
                    ) : !itemCatFetched ? (
                      null
                    ) : itemCategories.length === 0 ? (
                      <div className="text-[11px] text-gray-400">
                        No categories found.{' '}
                        <button onClick={fetchItemCategories} className="text-[#3F51B5] hover:underline cursor-pointer">Retry</button>
                      </div>
                    ) : (
                      <>
                        <div className="flex flex-wrap gap-1.5">
                          {itemCategories.map(cat => {
                            const active = selectedItemCat?.id === cat.id
                            return (
                              <button
                                key={cat.id}
                                type="button"
                                disabled={running}
                                onClick={() => setSelectedItemCat(active ? null : cat)}
                                className={`px-2.5 py-1 rounded-full text-[11px] font-medium border transition-colors cursor-pointer whitespace-nowrap ${
                                  active
                                    ? 'bg-[#3F51B5] text-white border-[#3F51B5]'
                                    : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-[#3F51B5] hover:text-[#3F51B5] dark:hover:text-[#7986CB]'
                                }`}
                              >
                                {cat.name}{` · ${cat.count} items`}
                              </button>
                            )
                          })}
                        </div>
                        {itemCatFetched && (
                          <button onClick={fetchItemCategories} className="text-[11px] text-gray-400 hover:text-[#3F51B5] hover:underline cursor-pointer mt-1.5">
                            Reload from ERP
                          </button>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Module-specific config */}
            {target.subModule === 'farmer' && (
              <div className="border-t border-gray-100 dark:border-gray-700 pt-3">
                <FarmerBatchConfig value={farmerConfig} onChange={setFarmerConfig} />
              </div>
            )}
            {target.subModule === 'item_attribute' && (
              <div className="border-t border-gray-100 dark:border-gray-700 pt-3">
                <Label className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">Attribute Number</Label>
                <div className="flex gap-1.5 mt-1.5">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button
                      key={n}
                      type="button"
                      onClick={() => setAttrNumber(n)}
                      className={`px-3 py-1.5 rounded text-[12px] font-medium border transition-colors cursor-pointer ${
                        attrNumber === n
                          ? 'bg-[#3F51B5] text-white border-[#3F51B5]'
                          : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-[#3F51B5]/50'
                      }`}
                    >
                      IA{n}
                    </button>
                  ))}
                </div>
              </div>
            )}

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
                        : 'linear-gradient(90deg, #3F51B5, #5C6BC0)',
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
              <div className="rounded-xl overflow-hidden border border-gray-800 dark:border-gray-700 bg-[#0d1117]">
                {/* Terminal header */}
                <div className="flex items-center gap-1.5 px-3 py-2 bg-[#161b22] border-b border-gray-800">
                  <span className="size-2.5 rounded-full bg-red-500/70" />
                  <span className="size-2.5 rounded-full bg-yellow-500/70" />
                  <span className="size-2.5 rounded-full bg-green-500/70" />
                  <span className="ml-2 text-[10px] text-gray-500 font-mono">batch output</span>
                  {running && <Loader2 className="size-3 text-[#7986CB] animate-spin ml-auto" />}
                </div>
                <ScrollArea className="h-44">
                  <div className="p-3 space-y-0.5">
                    {logs.map((line, i) => {
                      const t = line.text.trim()
                      const isRecord = /^\[\d+\/\d+\]/.test(t)
                      const isVerified = t.includes('verified') && !t.includes('FAILED')
                      const isApproved = t.includes('approved') && !t.includes('FAILED')
                      const isWorkflowOk = isVerified || isApproved
                      const isWorkflowFail = t.includes('FAILED') || t.includes('ERROR')
                      const isSummary = t.startsWith('Batch create complete')
                      const isUpToDate = t.startsWith('Created 0 payloads')

                      return (
                        <div key={i} className="flex items-start gap-2 group">
                          <span className="text-[10px] font-mono text-gray-600 select-none shrink-0 pt-0.5 w-16 text-right">
                            {formatTime(line.ts)}
                          </span>
                          <span className="shrink-0 pt-0.5">
                            {isWorkflowFail ? <XCircle className="size-3 text-red-400" /> :
                             isApproved     ? <BadgeCheck className="size-3 text-emerald-400" /> :
                             isVerified     ? <ShieldCheck className="size-3 text-sky-400" /> :
                             isSummary      ? <CheckCircle2 className="size-3 text-emerald-400" /> :
                             isRecord       ? <ChevronRight className="size-3 text-[#7986CB]" /> :
                                              <span className="size-3 inline-block" />}
                          </span>
                          <span className={`text-[11px] font-mono leading-5 break-all ${
                            isWorkflowFail ? 'text-red-400' :
                            isApproved     ? 'text-emerald-400' :
                            isVerified     ? 'text-sky-400' :
                            isSummary      ? 'text-emerald-300 font-medium' :
                            isRecord       ? 'text-gray-100' :
                                             'text-gray-500'
                          }`}>
                            {t}
                            {isUpToDate && (
                              <span className="ml-2 text-blue-400 not-italic">
                                — all records already exist in ERP. Try adding new locations to create more.
                              </span>
                            )}
                          </span>
                        </div>
                      )
                    })}
                    <div ref={logsEndRef} />
                  </div>
                </ScrollArea>
              </div>
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

            {/* CQP Fill All confirmation dialog */}
            {showCqpConfirm && cqpPreview && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
                <div className="bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-sm mx-4 p-5 space-y-4">
                  <div className="flex items-center gap-2">
                    <ListChecks className="size-4 text-[#3F51B5]" />
                    <span className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">Fill All Items</span>
                  </div>
                  <div className="text-[12px] text-gray-600 dark:text-gray-300 space-y-1">
                    <p><span className="font-medium">{cqpPreview.total_items}</span> total items in ERP</p>
                    <p><span className="font-medium text-emerald-600 dark:text-emerald-400">{cqpPreview.existing_count}</span> already have CQP entries</p>
                    <p><span className="font-medium text-[#3F51B5] dark:text-[#7986CB]">{cqpPreview.missing.length}</span> missing — will be created</p>
                  </div>
                  {cqpPreview.missing.length > 0 ? (
                    <div className="max-h-36 overflow-y-auto rounded-md border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-2 space-y-0.5">
                      {cqpPreview.missing.map((item) => (
                        <div key={item.id} className="text-[11px] text-gray-700 dark:text-gray-300 truncate">• {item.name}</div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[12px] text-emerald-600 dark:text-emerald-400 font-medium">All items already have CQP entries.</p>
                  )}
                  <div className="flex gap-2 justify-end">
                    <Button variant="outline" onClick={() => setShowCqpConfirm(false)} className="h-8 text-[12px] cursor-pointer">Cancel</Button>
                    {cqpPreview.missing.length > 0 && (
                      <Button
                        onClick={() => { setShowCqpConfirm(false); handleRun(true) }}
                        className="h-8 text-[12px] bg-[#3F51B5] hover:bg-[#3949AB] cursor-pointer gap-1.5"
                      >
                        <Play className="size-3" />
                        Create {cqpPreview.missing.length} entries
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* CBR Create Locations dialog */}
            {showCbrCreateLocations && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
                <div className="bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-sm mx-4 p-5 space-y-4">
                  <div className="flex items-center gap-2">
                    <Plus className="size-4 text-[#3F51B5]" />
                    <span className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">Add New Locations</span>
                  </div>
                  <div className="text-[12px] text-gray-600 dark:text-gray-300">
                    <p>Create new Location entries in the ERP.</p>
                  </div>

                  {/* Mode toggle */}
                  <div className="flex rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                    <button
                      type="button"
                      onClick={() => setCbrCreateMode('auto')}
                      className={`flex-1 py-1.5 text-[11px] font-medium transition-colors cursor-pointer ${cbrCreateMode === 'auto' ? 'bg-[#3F51B5] text-white' : 'bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
                    >
                      Auto Generate
                    </button>
                    <button
                      type="button"
                      onClick={() => setCbrCreateMode('manual')}
                      className={`flex-1 py-1.5 text-[11px] font-medium transition-colors cursor-pointer ${cbrCreateMode === 'manual' ? 'bg-[#3F51B5] text-white' : 'bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
                    >
                      Enter Names
                    </button>
                  </div>

                  {cbrCreateMode === 'auto' ? (
                    <div className="space-y-2">
                      <Label className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">How many locations to create?</Label>
                      <Input
                        type="number"
                        min={1}
                        max={50}
                        value={newLocationCount}
                        disabled={creatingLocations}
                        onChange={(e) => setNewLocationCount(Math.max(1, Math.min(50, parseInt(e.target.value) || 5)))}
                        className="h-8 text-[12px]"
                      />
                      <p className="text-[10px] text-gray-400 dark:text-gray-500">Names assigned from Maharashtra locations pool.</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Label className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">How many locations to create?</Label>
                      <Input
                        type="number"
                        min={1}
                        max={50}
                        value={manualLocationInputs.length}
                        disabled={creatingLocations}
                        onChange={(e) => {
                          const n = Math.max(1, Math.min(50, parseInt(e.target.value) || 1))
                          setManualLocationInputs(prev => {
                            if (n > prev.length) return [...prev, ...Array(n - prev.length).fill('')]
                            return prev.slice(0, n)
                          })
                        }}
                        className="h-8 text-[12px]"
                      />
                      <div className="space-y-1.5 max-h-48 overflow-y-auto">
                        {manualLocationInputs.map((val, i) => {
                          const trimmed = val.trim().toLowerCase()
                          const existsInErp = trimmed.length > 0 && cbrLocations.some(l => l.name.toLowerCase() === trimmed)
                          const duplicateInForm = trimmed.length > 0 && manualLocationInputs.filter((n, j) => j !== i && n.trim().toLowerCase() === trimmed).length > 0
                          const hasError = existsInErp || duplicateInForm
                          return (
                            <div key={i}>
                              <Input
                                type="text"
                                value={val}
                                disabled={creatingLocations}
                                onChange={(e) => {
                                  setManualLocationInputs(prev => {
                                    const next = [...prev]
                                    next[i] = e.target.value
                                    return next
                                  })
                                }}
                                placeholder={`Location ${i + 1}`}
                                className={`h-8 text-[12px] ${hasError ? 'border-red-400 dark:border-red-500 focus:ring-red-400/50' : ''}`}
                              />
                              {hasError && (
                                <p className="text-[10px] text-red-500 dark:text-red-400 mt-0.5">
                                  {existsInErp ? 'Already exists in ERP' : 'Duplicate name'}
                                </p>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  <div className="flex gap-2 justify-end">
                    <Button variant="outline" onClick={() => { setShowCbrCreateLocations(false); setCbrCreateMode('auto'); setManualLocationInputs(['']) }} disabled={creatingLocations} className="h-8 text-[12px] cursor-pointer">Cancel</Button>
                    <Button
                      onClick={async () => {
                        setCreatingLocations(true)
                        try {
                          let namesToCreate: string[] = []
                          if (cbrCreateMode === 'auto') {
                            const LOCATION_POOL = [
                              'Nagpur','Nashik','Kolhapur','Solapur','Amravati','Sangli','Satara','Akola',
                              'Latur','Dhule','Nanded','Jalgaon','Thane','Kalyan','Dombivli','Bhiwandi',
                              'Panvel','Karjat','Khopoli','Lonavala','Khandala','Igatpuri','Matheran',
                              'Mahabaleshwar','Panchgani','Alibag','Chiplun','Ratnagiri','Guhagar','Dapoli',
                              'Murud','Ganpatipule','Malvan','Vengurla','Sawantwadi','Amboli','Kolad','Roha',
                              'Pen','Karad','Phaltan','Pandharpur','Miraj','Ichalkaranji','Tasgaon','Barshi',
                              'Ausa','Nilanga','Udgir','Parbhani','Gangakhed','Sailu','Jintur','Partur',
                              'Manwath','Hinganghat','Wardha','Pulgaon','Arvi','Umred','Bhandara','Gondia',
                              'Tumsar','Tirora','Pauni','Chandrapur','Ballarpur','Warora','Bhadravati',
                              'Brahmapuri','Gadchiroli','Yavatmal','Wani','Digras','Darwha','Pusad',
                              'Umarkhed','Kinwat','Mahur','Ghatanji','Washim','Risod','Malegaon','Lonar',
                              'Mehkar','Chikhli','Nandura','Khamgaon','Shegaon','Akot','Jalna','Paithan',
                              'Kannad','Sillod','Bhokardan','Shirdi','Trimbak','Sinnar',
                            ]
                            const existingNames = new Set(cbrLocations.map(l => l.name.toLowerCase()))
                            const availableNames = LOCATION_POOL.filter(n => !existingNames.has(n.toLowerCase()))
                            namesToCreate = availableNames.slice(0, newLocationCount)
                          } else {
                            namesToCreate = manualLocationInputs.map(n => n.trim()).filter(n => n.length > 0)
                          }
                          if (namesToCreate.length === 0) {
                            notifySuccess('No Names', cbrCreateMode === 'auto' ? 'All predefined location names are already in use.' : 'Enter at least one location name.')
                            setCreatingLocations(false)
                            return
                          }
                          const csrfToken = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/)?.[1] ?? ''
                          const res = await fetch('/api/proxy?path=batch-create/cbr-create-locations', {
                            method: 'POST',
                            credentials: 'include',
                            headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': decodeURIComponent(csrfToken) },
                            body: JSON.stringify({
                              erp_token: erpToken,
                              erp_tenant_id: erpTenantId,
                              locations: namesToCreate.map(name => ({ name })),
                            }),
                          })
                          const data = await res.json()
                          const createdCount = (data.created ?? []).length
                          const failedCount = (data.failed ?? []).length
                          if (createdCount > 0) {
                            notifySuccess('Locations Created', `${createdCount} location${createdCount !== 1 ? 's' : ''} created successfully${failedCount > 0 ? `, ${failedCount} failed` : ''}`)
                            // Refresh location list
                            await fetchCbrLocations(true)
                            // Auto-select newly created locations
                            const createdIds = new Set((data.created ?? []).map((c: { id: number }) => c.id))
                            setSelectedLocations(prev => {
                              const next = new Set(prev)
                              for (const loc of cbrLocations) {
                                if (createdIds.has(loc.id)) next.add(loc.id)
                              }
                              return next
                            })
                          } else {
                            notifySuccess('No Locations Created', 'Failed to create locations. Check your ERP token.')
                          }
                        } catch {
                          notifySuccess('Error', 'Failed to create locations. Please try again.')
                        } finally {
                          setCreatingLocations(false)
                          setShowCbrCreateLocations(false)
                          setCbrCreateMode('auto')
                          setManualLocationInputs([''])
                        }
                      }}
                      disabled={creatingLocations || (cbrCreateMode === 'manual' && (() => {
                        const filled = manualLocationInputs.filter(n => n.trim())
                        if (filled.length === 0) return true
                        const erpNames = new Set(cbrLocations.map(l => l.name.toLowerCase()))
                        return filled.some(n => {
                          const t = n.trim().toLowerCase()
                          return erpNames.has(t) || filled.filter(m => m.trim().toLowerCase() === t).length > 1
                        })
                      })())}
                      className="h-8 text-[12px] bg-[#3F51B5] hover:bg-[#3949AB] cursor-pointer gap-1.5"
                    >
                      {creatingLocations ? <Loader2 className="size-3 animate-spin" /> : <Plus className="size-3" />}
                      {creatingLocations ? 'Creating...' : cbrCreateMode === 'auto' ? `Create ${newLocationCount} Location${newLocationCount !== 1 ? 's' : ''}` : `Create ${manualLocationInputs.filter(n => n.trim()).length} Location${manualLocationInputs.filter(n => n.trim()).length !== 1 ? 's' : ''}`}
                    </Button>
                  </div>
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
          </>
        )}
      </div>
    </div>
  )
}
