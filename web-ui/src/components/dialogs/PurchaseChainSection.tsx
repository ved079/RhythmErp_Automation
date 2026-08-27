'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { CheckCircle2, XCircle, Play, Key, RefreshCw, Loader2, X, AlertTriangle, Wand2, Search, Star, FileSpreadsheet, Download, FileText, ChevronDown, FileBarChart2 } from 'lucide-react'
import Spinner from '@/components/ui/Spinner'
import { startPurchaseChain, fetchMasterData, fetchItemCategories, fetchItemsWithCqp, fillCqpItems, verifyJV, fetchPBList, fetchPBItems, fetchAccountingDef, type SSEEvent, type MasterDataItem, type ItemCategory, type JVVerifyStep, type PBListItem, type PBItemLine, type AccountingDefDetail} from '@/lib/api'
import { notifySuccess } from '@/lib/notify'

interface Props {
  erpToken: string
  erpTenantId: string
  onNeedsToken: () => void
  onClearToken: () => void
  userId?: string
  showJVCheck?: boolean
}

function formatTime(d: Date): string {
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

const XL_BORDER = '<Borders><Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D6D6D6"/><Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D6D6D6"/><Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D6D6D6"/><Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D6D6D6"/></Borders>'

function escXml(v: string | number | null | undefined): string {
  return String(v ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const DOC_COLORS: Record<string, string> = {
  PO:  'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300',
  GP:  'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  GRN: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300',
  QC:  'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  PB:  'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300',
  SO:  'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
}

function DocPill({ label, id }: { label: string; id?: string }) {
  const cls = DOC_COLORS[label] ?? 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold ${cls}`}>
      {label}{id && <span className="font-normal opacity-70">#{id}</span>}
    </span>
  )
}

function DocChain({ raw }: { raw: string }) {
  // "PO 3614 → GP 2196 → GRN 1850 → QC 1890 → SO 434"
  const parts = raw.split(/\s*→\s*/)
  return (
    <span className="inline-flex items-center gap-1 flex-wrap">
      {parts.map((p, i) => {
        const [label, id] = p.trim().split(' ')
        return (
          <React.Fragment key={i}>
            {i > 0 && <span className="text-gray-400 dark:text-gray-500 text-[10px]">→</span>}
            <DocPill label={label} id={id} />
          </React.Fragment>
        )
      })}
    </span>
  )
}

function renderLogLine(log: { text: string; ts: Date; isErr: boolean; isDone: boolean }) {
  const t = log.text

  // Error
  if (log.isErr) {
    return (
      <div className="flex gap-2 items-start text-red-500 dark:text-red-400">
        <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(log.ts)}]</span>
        <span className="flex items-center gap-1.5"><span className="text-[11px]">✕</span><span className="whitespace-pre-wrap break-all text-[11px]">{t}</span></span>
      </div>
    )
  }

  // Done summary  "Done — 2 chains created, 0 failed (25.9s)"
  if (log.isDone || t.startsWith('Done —')) {
    const m = t.match(/(\d+) chains? created.*?(\d+) failed.*?\(([\d.]+s)\)/)
    return (
      <div className="flex gap-2 items-start text-emerald-600 dark:text-emerald-400 font-semibold">
        <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(log.ts)}]</span>
        {m ? (
          <span className="flex items-center gap-2 flex-wrap text-[11px]">
            <span>✓ Done</span>
            <span className="font-normal text-gray-500 dark:text-gray-400">—</span>
            <span className="text-emerald-600 dark:text-emerald-400">{m[1]} created</span>
            {parseInt(m[2]) > 0 && <span className="text-red-500">{m[2]} failed</span>}
            <span className="font-normal text-gray-400 dark:text-gray-500">{m[3]}</span>
          </span>
        ) : (
          <span className="text-[11px]">{t}</span>
        )}
      </div>
    )
  }

  // Chain OK  "Chain [1] OK — PO 3614 → GP 2196 → ..."
  const chainOk = t.match(/^Chain \[(\d+)\] OK — (.+?) \(([\d.]+s)\)$/)
  if (chainOk) {
    return (
      <div className="flex gap-2 items-start">
        <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(log.ts)}]</span>
        <span className="flex items-center gap-2 flex-wrap">
          <span className="text-emerald-600 dark:text-emerald-400 text-[10px] font-semibold">Chain {chainOk[1]} ✓</span>
          <DocChain raw={chainOk[2]} />
          <span className="text-gray-400 dark:text-gray-500 text-[10px]">{chainOk[3]}</span>
        </span>
      </div>
    )
  }

  // Chain FAILED  "Chain [1] FAILED — ..."
  const chainFail = t.match(/^Chain \[(\d+)\] FAILED/)
  if (chainFail) {
    return (
      <div className="flex gap-2 items-start text-red-500 dark:text-red-400">
        <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(log.ts)}]</span>
        <span className="text-[11px]">Chain {chainFail[1]} ✕ — {t.replace(/^Chain \[\d+\] FAILED — ?/, '')}</span>
      </div>
    )
  }

  // Chain header  "Chain [1/2] — supplier=2543"
  const chainHdr = t.match(/^Chain \[(\d+)\/(\d+)\]/)
  if (chainHdr) {
    return (
      <div className="flex gap-2 items-start">
        <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(log.ts)}]</span>
        <span className="text-[#3F51B5] dark:text-[#7986CB] font-semibold text-[11px]">
          Chain {chainHdr[1]} / {chainHdr[2]}
        </span>
      </div>
    )
  }

  // Documents to create  "Documents to create: PO → GP → GRN → QC → SO"
  const docsLine = t.match(/^Documents to create: (.+)$/)
  if (docsLine) {
    return (
      <div className="flex gap-2 items-start">
        <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(log.ts)}]</span>
        <span className="flex items-center gap-1.5 flex-wrap text-[10px] text-gray-500 dark:text-gray-400">
          Flow: <DocChain raw={docsLine[1].replace(/→/g, '→').replace(/\s+/g, ' ')} />
        </span>
      </div>
    )
  }

  // Starting  "Starting N purchase chain(s) — ..."
  if (t.startsWith('Starting ')) {
    const m = t.match(/Starting (\d+) purchase chain/)
    return (
      <div className="flex gap-2 items-start">
        <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(log.ts)}]</span>
        <span className="text-[#3F51B5] dark:text-[#7986CB] font-semibold text-[11px]">
          Starting {m ? `${m[1]} chain${parseInt(m[1]) > 1 ? 's' : ''}` : ''}…
        </span>
      </div>
    )
  }

  // Suppress noisy technical lines
  if (t.startsWith('Discovering') || t.startsWith('Discovery complete') || t.startsWith('Config:')) {
    return null
  }

  return (
    <div className="flex gap-2 items-start">
      <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16 text-[10px]">[{formatTime(log.ts)}]</span>
      <span className="whitespace-pre-wrap break-all text-[11px] text-gray-700 dark:text-gray-200">{t}</span>
    </div>
  )
}

/**
 * Items selectable for the PO: restricted to one category (falling back to all
 * when no category matches) and, when Tax Rate is ON, only items whose HSN has
 * at least one configured tax rate. Unlike the category fallback, the tax-rate
 * filter never falls back to rate-less items — ON means only items with rates.
 *
 * When a non-empty CQP whitelist is provided (item IDs that have a Commodity
 * Quality Parameter entry), items outside it are excluded — the QC step 500s
 * on items without a CQP entry.
 */
function poolFor(
  items: MasterDataItem[],
  categoryId: number | null,
  requireTaxRate: boolean,
  cqpItemIds: number[] | null,
): MasterDataItem[] {
  let pool = items
  if (categoryId != null) {
    const filtered = items.filter((i) => i.item_category === categoryId)
    if (filtered.length > 0) pool = filtered
  }
  if (requireTaxRate) {
    pool = pool.filter((i) => (i.tax_rates?.length ?? 0) > 0)
  }
  if (cqpItemIds && cqpItemIds.length > 0) {
    const cqpSet = new Set(cqpItemIds)
    pool = pool.filter((i) => cqpSet.has(i.id))
  }
  return pool
}

export function PurchaseChainSection({ erpToken, erpTenantId, onNeedsToken, onClearToken, userId, showJVCheck = false }: Props) {
  const [count, setCount] = useState(1)
  const [chainSuppliers, setChainSuppliers] = useState<(number | null)[]>([])
  const [sameSupplier, setSameSupplier] = useState(false)
  const [enabledDocs, setEnabledDocs] = useState<Set<string>>(new Set(['PO', 'GP', 'GRN', 'QC', 'PB']))
  const [supplier, setSupplier] = useState<number | null>(null)
  const [numItems, setNumItems] = useState(2)
  const [itemIds, setItemIds] = useState<number[]>([])
  const [running, setRunning] = useState(false)
  const [logs, setLogs] = useState<{ text: string; ts: Date; isErr: boolean; isDone: boolean }[]>([])
  const [created, setCreated] = useState(0)
  const [failed, setFailed] = useState(0)
  const [suppliers, setSuppliers] = useState<MasterDataItem[]>([])
  const [items, setItems] = useState<MasterDataItem[]>([])
  const [customers, setCustomers] = useState<MasterDataItem[]>([])
  const [customer, setCustomer] = useState<number | null>(null)
  const [cqpItemIds, setCqpItemIds] = useState<number[] | null>(null)
  const [fillingCqp, setFillingCqp] = useState(false)
  const [cqpFillLog, setCqpFillLog] = useState('')
  const [runSummary, setRunSummary] = useState<{ created: number; failed: number; total: number; elapsed: string } | null>(null)
  const [categories, setCategories] = useState<ItemCategory[]>([])
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null)
  const [requireTaxRate, setRequireTaxRate] = useState(true)
  const [starredFlow, setStarredFlow] = useState<'po' | 'gp' | 'so' | null>(null)
  const [flow, setFlow] = useState<'po' | 'gp' | 'so'>('po')
  const [multiGatePass, setMultiGatePass] = useState(false)
  const [gpCount, setGpCount] = useState(2)
  const [qcDiscount, setQcDiscount] = useState(false)
  const [isRateWeightDeduction, setIsRateWeightDeduction] = useState(false)
  const [loadingData, setLoadingData] = useState(false)
  const [dataError, setDataError] = useState('')
  const [localToken, setLocalToken] = useState('')
  const [localTenantId, setLocalTenantId] = useState('')
  const [showTokenInput, setShowTokenInput] = useState(false)
  const [showLogs, setShowLogs] = useState(false)
  const [activeMenu, setActiveMenu] = useState<{type: 'supplier' | 'category' | 'customer' | 'item' | number | `chainSup:${number}`; pos: {top: number; left: number; width: number}} | null>(null)
  const [dropdownSearch, setDropdownSearch] = useState('')
  const logsEndRef = useRef<HTMLDivElement>(null)
  const tokenSectionRef = useRef<HTMLDivElement>(null)
  const tokenErrorRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const startTimeRef = useRef<number>(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const [elapsed, setElapsed] = useState(0)
  // JV check mode state
  const [pbRefNo, setPbRefNo] = useState('')
  const [selectedPB, setSelectedPB] = useState<PBListItem | null>(null)
  const [jvSteps, setJvSteps] = useState<JVVerifyStep[]>([])
  const [verifying, setVerifying] = useState(false)
  const [jvError, setJvError] = useState('')
  const [pbList, setPbList] = useState<PBListItem[]>([])
  const [pbListLoading, setPbListLoading] = useState(false)
  const [pbListError, setPbListError] = useState('')
  const [pbSearch, setPbSearch] = useState('')
  const [pbListOpen, setPbListOpen] = useState(true)
  const [pbItems, setPbItems] = useState<PBItemLine[]>([])
  const [pbItemsLoading, setPbItemsLoading] = useState(false)
  const [jvAccountRows, setJvAccountRows] = useState<{ account_name: string; dr_cr: string; commodity: string; amount: number | null }[]>([])
  const [accountingDef, setAccountingDef] = useState<AccountingDefDetail[]>([])
  const [accountingDefLoading, setAccountingDefLoading] = useState(false)
  const [notAppliedOpen, setNotAppliedOpen] = useState(false)

  // On mount (or when userId changes): restore this user's starred flow from localStorage.
  useEffect(() => {
    const key = userId ? `pc_starred_flow:${userId}` : 'pc_starred_flow'
    const saved = localStorage.getItem(key) as 'po' | 'gp' | 'so' | null
    if (saved) {
      setStarredFlow(saved)
      setFlow(saved)
      setEnabledDocs(new Set(saved === 'so' ? ['PO', 'GP', 'GRN', 'QC', 'SO'] : saved === 'gp' ? ['GP', 'GRN', 'QC', 'PB'] : ['PO', 'GP', 'GRN', 'QC', 'PB']))
    }
  }, [userId])

  const fetchedRef = useRef(false)
  const supplierBtnRef = useRef<HTMLButtonElement>(null)
  const categoryBtnRef = useRef<HTMLButtonElement>(null)
  const itemBtnRef = useRef<HTMLButtonElement>(null)
  const customerBtnRef = useRef<HTMLButtonElement>(null)
  const rowBtnRefs = useRef<(HTMLButtonElement | null)[]>([])
  const chainSupBtnRefs = useRef<(HTMLButtonElement | null)[]>([])

  useEffect(() => {
    if (running) {
      startTimeRef.current = Date.now()
      timerRef.current = setInterval(() => {
        setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000))
      }, 1000)
    } else {
      if (timerRef.current) clearInterval(timerRef.current)
      timerRef.current = null
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [running])

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  useEffect(() => {
    if (showTokenInput) {
      tokenSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [showTokenInput])

  // Scroll the token error banner into view within the scrollable container
  useEffect(() => {
    if (!localToken) return
    const t = localToken.startsWith('Bearer ') ? localToken.slice(7) : localToken
    const isInvalid = !(t.startsWith('eyJ') && t.split('.').length === 3 && t.length > 100)
    if (isInvalid) {
      requestAnimationFrame(() => {
        if (!tokenErrorRef.current || !scrollContainerRef.current) return
        const container = scrollContainerRef.current
        const el = tokenErrorRef.current
        const containerRect = container.getBoundingClientRect()
        const elRect = el.getBoundingClientRect()
        const offset = elRect.top - containerRect.top + container.scrollTop - container.clientHeight / 2 + el.offsetHeight / 2
        container.scrollTo({ top: offset, behavior: 'smooth' })
      })
    }
  }, [localToken])

  // Fetch suppliers, items and item categories when credentials are available
  const loadMasterData = useCallback(async () => {
    const token = erpToken || localToken
    const tenant = localTenantId || erpTenantId
    if (!token || !tenant) return

    setLoadingData(true)
    setDataError('')
    try {
      const [supRes, itemRes, catRes, cqpRes] = await Promise.all([
        fetchMasterData('Supplier', token, tenant),
        fetchMasterData('Item Master', token, tenant),
        fetchItemCategories(token, tenant),
        fetchItemsWithCqp(token, tenant),
      ])
      setSuppliers(supRes)
      setItems(itemRes)
      setCategories(catRes)
      setCqpItemIds(cqpRes)
      const defaultCat = catRes.find((c) => c.item_count > 0)
      const defaultCatId = defaultCat ? defaultCat.id : (catRes[0] ? catRes[0].id : null)
      setSelectedCategoryId(defaultCatId)
      const usable = poolFor(itemRes, selectedCategoryId ?? null, flow === 'gp' ? false : requireTaxRate, cqpRes)
      if (supRes.length > 0 && supplier === null) setSupplier(supRes[0].id)
      if (usable.length > 0 && itemIds.length === 0) {
        setItemIds(usable.slice(0, numItems).map(i => i.id))
      }
      // Customers drive the Sales Order header — fetch on SO flow so the
      // dropdown is populated before the user hits Run.
      if (flow === 'so') {
        try {
          const custRes = await fetchMasterData('Customer', token, tenant)
          setCustomers(custRes)
          if (customer === null && custRes.length > 0) setCustomer(custRes[0].id)
        } catch {
          setCustomers([])
        }
      }
      fetchedRef.current = true
    } catch (err) {
      setDataError(err instanceof Error ? err.message : 'Failed to load master data')
    } finally {
      setLoadingData(false)
    }
  }, [erpToken, localToken, localTenantId, erpTenantId, requireTaxRate, flow])

  const handleDone = useCallback(() => {
    setShowTokenInput(false)
    const token = erpToken || localToken
    const tenant = localTenantId || erpTenantId
    if (token && tenant) {
      loadMasterData()
    }
  }, [erpToken, localToken, localTenantId, erpTenantId, loadMasterData])

  // Document order for the selected flow: full chain starts with PO,
  // standalone GP starts directly at the Gate Pass.
  const docOrder = React.useMemo(
    () =>
      flow === 'gp'
        ? ['GP', 'GRN', 'QC', 'PB']
        : flow === 'so'
          ? ['PO', 'GP', 'GRN', 'QC', 'SO', 'PB']
          : ['PO', 'GP', 'GRN', 'QC', 'PB'],
    [flow],
  )

  // Documents actually enabled for the run (order for the selected flow ∩ set).
  const activeDocs = React.useMemo(
    () => docOrder.filter((d) => enabledDocs.has(d)),
    [docOrder, enabledDocs],
  )

  const handleStart = useCallback(() => {
    const token = erpToken || localToken
    if (!token) {
      setShowTokenInput(true)
      return
    }
    if (supplier === null || itemIds.length === 0) return
    setRunning(true)
    setLogs([])
    setCreated(0)
    setFailed(0)
    setElapsed(0)
    setShowLogs(true)

    const activeTaxRate = flow === 'gp' ? false : requireTaxRate

    startPurchaseChain(
      count,
      supplier,
      numItems,
      itemIds,
      token,
      localTenantId || erpTenantId || '681',
      (event: SSEEvent) => {
        setLogs((prev) => [...prev, {
          text: event.message,
          ts: new Date(),
          isErr: event.type === 'error',
          isDone: event.type === 'run_end',
        }])
        if (event.type === 'run_end') {
          setRunning(false)
          setCreated(event.created ?? created)
          setFailed(event.failed ?? failed)
          setRunSummary({
            created: event.created ?? created,
            failed: event.failed ?? failed,
            total: event.total ?? count,
            elapsed: elapsed.toFixed(1),
          })
          notifySuccess('Purchase Chain Complete', `${event.created ?? created} created, ${event.failed ?? failed} failed`)
        }
      },
      () => {
        setRunning(false)
      },
      (err: Error) => {
        setLogs((prev) => [...prev, { text: `Error: ${err.message}`, ts: new Date(), isErr: true, isDone: false }])
        setRunning(false)
      },
      activeDocs,
      selectedCategoryId ?? undefined,
      activeTaxRate,
      multiGatePass,
      gpCount,
      count > 1 ? chainSuppliers.filter((s): s is number => s != null) : [],
      qcDiscount,
      flow === 'so' && enabledDocs.has('SO') ? customer : null,
      isRateWeightDeduction,
      showJVCheck,
    )
  }, [count, supplier, numItems, itemIds, erpToken, localToken, localTenantId, erpTenantId, activeDocs, selectedCategoryId, requireTaxRate, flow, multiGatePass, gpCount, chainSuppliers, qcDiscount, customer, enabledDocs, isRateWeightDeduction])

  const handleStop = useCallback(() => {
    setRunning(false)
    setLogs((prev) => [...prev, { text: 'Stopped by user', ts: new Date(), isErr: true, isDone: false }])
  }, [])

  // Items selectable for the PO (category-scoped + tax-rate filter).
  // Standalone GP flow has no tax-rate concept, so the filter is skipped.
  const catItems = React.useMemo(
    () => poolFor(items, selectedCategoryId, flow === 'gp' ? false : requireTaxRate, cqpItemIds),
    [items, selectedCategoryId, requireTaxRate, flow, cqpItemIds],
  )

  // Items in the selected category that lack a CQP entry — the QC step 500s on
  // those, so we surface them so the user can auto-fill before running.
  const missingCqpItems = React.useMemo(() => {
    if (cqpItemIds == null) return []
    const cqpSet = new Set(cqpItemIds)
    const categoryPool = poolFor(items, selectedCategoryId, false, null)
    return categoryPool.filter((i) => !cqpSet.has(i.id))
  }, [items, selectedCategoryId, cqpItemIds])

  const handleCqpFill = useCallback(async () => {
    const token = erpToken || localToken
    const tenant = localTenantId || erpTenantId
    if (!token || !tenant || missingCqpItems.length === 0) return
    setFillingCqp(true)
    setCqpFillLog('')
    try {
      const ids = missingCqpItems.map((i) => i.id)
      const res = await fillCqpItems(token, tenant, ids)
      const created = res.created.length
      const failed = res.failed.length
      const skipped = res.skipped.length
      setCqpFillLog(
        `CQP auto-fill: ${created} created, ${skipped} already had entries, ${failed} failed.`,
      )
      if (created > 0) {
        // Refresh the CQP set so the newly-filled items enter the item pool.
        const fresh = await fetchItemsWithCqp(token, tenant)
        setCqpItemIds(fresh)
      }
    } catch (err) {
      setCqpFillLog(`CQP auto-fill failed: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setFillingCqp(false)
    }
  }, [erpToken, localToken, localTenantId, erpTenantId, missingCqpItems])

  // When the Tax Rate toggle flips, re-reset the selected rows to the pool.
  const resetItemsFromPool = useCallback((pool: MasterDataItem[], count: number) => {
    if (pool.length === 0) { setItemIds([]); return }
    setItemIds(pool.slice(0, Math.max(1, count)).map((i) => i.id))
  }, [])

  // On category change: auto-reset the selected item rows to the category's items.
  const handleCategorySelect = (id: number) => {
    setSelectedCategoryId(id)
    resetItemsFromPool(poolFor(items, id, requireTaxRate, cqpItemIds), numItems)
    setActiveMenu(null)
  }

  useEffect(() => {
    if (fetchedRef.current) {
      resetItemsFromPool(catItems, numItems)
    }
  }, [requireTaxRate, selectedCategoryId, flow])

  const selectedSupplier = suppliers.find((s) => s.id === supplier)
  const selectedCategory = categories.find((c) => c.id === selectedCategoryId)

  // Clamp the floating dropdown within the viewport so it never renders off-screen.
  const dropdownPos = React.useMemo(() => {
    if (!activeMenu) return null
    const POS_MARGIN = 8
    const MAX_H = 192 // matches max-h-48
    const MIN_W = 200
    const WANT_W = 260 // prefer a wider panel so long names stay readable
    const vw = typeof window !== 'undefined' ? window.innerWidth : 0
    const vh = typeof window !== 'undefined' ? window.innerHeight : 0

    // Always open below the button; cap height so it never overflows the viewport.
    const top = activeMenu.pos.top
    const maxHeight = Math.min(MAX_H, vh - top - POS_MARGIN)

    // Anchor the panel to the trigger button (same left edge). Widen it if the
    // viewport has room to the right; only fall back to the right edge when there
    // genuinely isn't enough space to keep it attached.
    const left = activeMenu.pos.left
    const width = activeMenu.pos.width
    return { top, left, width, maxHeight }
  }, [activeMenu])

  const loadPBList = useCallback(async () => {
    const token = erpToken || localToken
    const tenant = localTenantId || erpTenantId
    if (!token || !tenant) return
    setPbListLoading(true)
    setPbListError('')
    try {
      const list = await fetchPBList(token, tenant)
      setPbList(list)
    } catch (err) {
      setPbListError(err instanceof Error ? err.message : String(err))
    } finally {
      setPbListLoading(false)
    }
  }, [erpToken, localToken, localTenantId, erpTenantId])

  const handleVerify = async (refOverride?: string) => {
    const token = erpToken || localToken
    const tenant = localTenantId || erpTenantId
    const ref = (refOverride ?? pbRefNo).trim()
    if (!token || !tenant || !ref) return
    setVerifying(true)
    setJvSteps([])
    setJvError('')
    setJvAccountRows([])
    setAccountingDef([])
    try {
      const [jvRes] = await Promise.all([
        verifyJV(token, tenant, ref),
        // Fetch accounting definition in parallel
        (async () => {
          setAccountingDefLoading(true)
          try {
            const def = await fetchAccountingDef(token, tenant, '5')
            setAccountingDef(def.details)
          } catch { /* silently skip */ }
          finally { setAccountingDefLoading(false) }
        })(),
      ])
      setJvSteps(jvRes.steps)
      setJvAccountRows(jvRes.account_rows ?? [])
    } catch (err) {
      setJvError(err instanceof Error ? err.message : String(err))
    } finally {
      setVerifying(false)
    }
  }

  // PB vs JV comparison rows — shared by the on-screen sheet and the export.
  const jvCompRows = React.useMemo<{ label: string; pb: string; jv: string; indent?: boolean }[] | null>(() => {
    const fieldsStep = jvSteps.find(s => s.fields)
    if (!selectedPB || !fieldsStep) return null
    const jvCommodity = fieldsStep.fields?.find(f => f.field === 'Commodity')?.value || '—'
    const uniqueItems = [...new Set(pbItems.map(i => i.name))]
    // jvCommodity may be comma-joined list for multi-item PBs
    const jvCommodityList = jvCommodity !== '—' ? jvCommodity.split(',').map(s => s.trim().toLowerCase()) : []
    const commodityRows: { label: string; pb: string; jv: string }[] =
      pbItems.length > 0
        ? uniqueItems.map((name, idx) => {
            const nameL = name.trim().toLowerCase()
            const matchedJv = jvCommodityList.find(c => c === nameL || c.includes(nameL) || nameL.includes(c))
            return { label: idx === 0 ? 'Commodity' : '', pb: name, jv: matchedJv ? name : '—' }
          })
        : [{ label: 'Commodity', pb: pbItemsLoading ? 'Loading…' : '—', jv: jvCommodity }]
    const fmtAmt = (n: number) => n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    const jvDr = jvAccountRows.filter(r => r.dr_cr === 'Debit').reduce((s, r) => s + (r.amount ?? 0), 0)
    const pbAmtStr = selectedPB.amount != null ? fmtAmt(Number(selectedPB.amount)) : '—'
    const jvAmtStr = jvAccountRows.length > 0 ? fmtAmt(jvDr) : '—'
    // Per-item tax rows interleaved after each commodity row
    // Match JV tax row by amount (exact). Track used rows by absolute index into jvAccountRows
    // so IGST and CGST/SGST lookups don't corrupt each other's "used" state.
    const usedJvRowIndices = new Set<number>()
    const jvTaxRow = (keyword: string, pbAmt: number) => {
      const candidates = jvAccountRows
        .map((r, i) => ({ r, i }))
        .filter(({ r, i }) => r.dr_cr === 'Debit' && r.account_name.toLowerCase().includes(keyword) && !usedJvRowIndices.has(i))
      const match = candidates.find(({ r }) => r.amount != null && Math.abs((r.amount ?? 0) - pbAmt) < 0.02)
        ?? candidates[0]
      if (match) usedJvRowIndices.add(match.i)
      return match?.r?.amount != null ? fmtAmt(match.r.amount) : jvAccountRows.length > 0 ? '—' : '—'
    }
    const commodityWithTax: { label: string; pb: string; jv: string }[] = []
    for (const item of pbItems.length > 0 ? pbItems : []) {
      const nameL = item.name.trim().toLowerCase()
      const jvCommodityList = jvCommodity !== '—' ? jvCommodity.split(',').map(s => s.trim().toLowerCase()) : []
      const matchedJv = jvCommodityList.find(c => c === nameL || c.includes(nameL) || nameL.includes(c))
      commodityWithTax.push({ label: 'Commodity', pb: item.name, jv: matchedJv ? item.name : '—' })
      if (item.igst_amount != null && item.igst_amount > 0) {
        commodityWithTax.push({ label: 'IGST Amount', pb: fmtAmt(item.igst_amount), jv: jvTaxRow('igst', item.igst_amount), indent: true })
      } else {
        if (item.cgst_amount != null && item.cgst_amount > 0)
          commodityWithTax.push({ label: 'CGST Amount', pb: fmtAmt(item.cgst_amount), jv: jvTaxRow('cgst', item.cgst_amount), indent: true })
        if (item.sgst_amount != null && item.sgst_amount > 0)
          commodityWithTax.push({ label: 'SGST Amount', pb: fmtAmt(item.sgst_amount), jv: jvTaxRow('sgst', item.sgst_amount), indent: true })
      }
    }
    const finalCommodityRows = commodityWithTax.length > 0 ? commodityWithTax : commodityRows
    return [
      { label: 'Division',            pb: selectedPB.division    || '—', jv: fieldsStep.fields?.find(f => f.field === 'Division')?.value    || '—' },
      { label: 'Department',          pb: selectedPB.department  || '—', jv: fieldsStep.fields?.find(f => f.field === 'Department')?.value  || '—' },
      { label: 'Type of Sale',        pb: selectedPB.type_of_sale || '—', jv: fieldsStep.fields?.find(f => f.field === 'Type of Sale')?.value || '—' },
      { label: 'Location',            pb: selectedPB.location    || '—', jv: fieldsStep.fields?.find(f => f.field === 'Location')?.value    || '—' },
      ...finalCommodityRows,
      { label: 'Transaction Amount',  pb: pbAmtStr,  jv: jvAmtStr },
    ]
  }, [jvSteps, selectedPB, pbItems, pbItemsLoading, jvAccountRows])

  // Export the JV verification report as a formatted Excel workbook using
  // SpreadsheetML (XML Spreadsheet 2003) — supports fonts, fills, borders and
  // number formats without any extra dependency.
  const exportJvReport = useCallback(() => {
    const found = jvSteps.find(s => s.n === 1)
    const fieldsStep = jvSteps.find(s => s.fields)
    const balanceStep = jvSteps.find(s => s.detail && !s.fields)
    if (!selectedPB || (!found && !fieldsStep)) return
    const fieldMismatch = (jvCompRows ?? []).some(r => r.pb !== '—' && r.jv !== '—' && r.pb.trim().toLowerCase() !== r.jv.trim().toLowerCase())
    const _defMap = new Map<string, typeof accountingDef[0]>()
    for (const d of accountingDef) { const k = d.account_name.trim().toLowerCase()+'|'+(d.dr_cr||'').toLowerCase(); if (!_defMap.has(k)) _defMap.set(k,d) }
    const accountRowFail = jvAccountRows.some(r => { const def=_defMap.get(r.account_name.trim().toLowerCase()+'|'+(r.dr_cr||'').toLowerCase()); return !def||def.dr_cr!==r.dr_cr })
    const jvDrTotal = jvAccountRows.filter(r=>r.dr_cr==='Debit').reduce((s,r)=>s+(r.amount??0),0)
    const amountMismatch = selectedPB.amount!=null && jvAccountRows.length>0 && Math.abs(Number(selectedPB.amount)-jvDrTotal)>0.02
    const ok = jvSteps.length > 0 && jvSteps.every(s => s.ok) && !fieldMismatch && !accountRowFail && !amountMismatch
    const balMatch = balanceStep?.detail?.match(/DR\s*=\s*([\d,]+\.?\d*)\s+\|CR\|\s*=\s*([\d,]+\.?\d*)/)
    const amountNum = selectedPB.amount != null ? Number(selectedPB.amount) : null

    // 5 columns: Account/Label(140) | Value/DrCr(145) | Amount(95) | Condition/Value(165) | Status(90)
    const cell = (style: string, value: string | number, mergeAcross?: number) => {
      const type = typeof value === 'number' ? 'Number' : 'String'
      return `<Cell${mergeAcross != null ? ` ss:MergeAcross="${mergeAcross}"` : ''}${style ? ` ss:StyleID="${style}"` : ''}><Data ss:Type="${type}">${escXml(value)}</Data></Cell>`
    }
    const emptyCell = (style = 'sVal') => `<Cell ss:StyleID="${style}"><Data ss:Type="String"></Data></Cell>`

    const rows: string[] = []

    // Title banner (spans all 5 cols via mergeAcross=4)
    rows.push(`<Row ss:Height="28">${cell('sTitle', 'JV VERIFICATION REPORT', 3)}${cell(ok ? 'sPass' : 'sFail', ok ? '\u2713 PASSED' : '\u2715 FAILED')}</Row>`)
    rows.push(`<Row ss:Height="16">${cell('sMeta', `Document: ${pbRefNo}`, 2)}${cell('sMeta', `Generated: ${new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}`, 2)}</Row>`)
    rows.push('<Row ss:Height="8"/>')

    // Document Details
    rows.push(`<Row ss:Height="19">${cell('sSection', 'DOCUMENT DETAILS', 4)}</Row>`)
    rows.push(`<Row>${cell('sLabel', 'Supplier')}${cell('sVal', selectedPB.supplier ?? '\u2014', 3)}</Row>`)
    rows.push(`<Row>${cell('sLabel', 'Amount')}${amountNum != null ? cell('sMoney', amountNum) : cell('sVal', '\u2014')}${cell('sLabel', 'Date')}${cell('sVal', selectedPB.date ?? '\u2014')}${emptyCell()}</Row>`)
    rows.push('<Row ss:Height="8"/>')

    // Journal Voucher
    rows.push(`<Row ss:Height="19">${cell('sSection', 'JOURNAL VOUCHER', 4)}</Row>`)
    rows.push(`<Row>${cell('sLabel', 'JV Entry')}${cell(found ? (found.ok ? 'sPassText' : 'sFailText') : 'sDim', found ? (found.ok ? 'Entry found in JV report' : `Not found \u2014 ${found.detail ?? ''}`) : 'Not checked', 3)}</Row>`)
    if (balMatch) {
      const drNum = Number(balMatch[1].replace(/,/g, ''))
      const crNum = Number(balMatch[2].replace(/,/g, ''))
      rows.push(`<Row>${cell('sLabel', 'Balance Check')}${cell('sDr', drNum)}${cell('sCr', crNum)}${cell(balanceStep?.ok ? 'sPass' : 'sFail', balanceStep?.ok ? 'BALANCED \u2713' : 'UNBALANCED \u2715')}${emptyCell()}</Row>`)
    }
    rows.push('<Row ss:Height="8"/>')

    // Field Cross-Check
    const xrows = jvCompRows ?? fieldsStep?.fields?.map(f => ({ label: f.field, pb: '\u2014', jv: f.value })) ?? []
    if (xrows.length > 0) {
      rows.push(`<Row ss:Height="19">${cell('sSection', 'ACCOUNTING FIELD CROSS-CHECK', 4)}</Row>`)
      rows.push(`<Row>${cell('sHead', 'Field')}${cell('sHead', 'Purchase Booking')}${cell('sHeadC', '\u2194')}${cell('sHead', 'Journal Voucher')}${cell('sHeadC', 'Match')}</Row>`)
      for (const r of xrows) {
        const match = r.pb !== '\u2014' && r.jv !== '\u2014' && r.pb.trim().toLowerCase() === r.jv.trim().toLowerCase()
        const unknown = r.pb === '\u2014' || r.jv === '\u2014'
        rows.push(`<Row>${cell(r.label ? 'sLabel' : 'sDim', r.label || '')}${cell(unknown ? 'sDim' : 'sVal', r.pb)}${emptyCell('sDimC')}${cell(unknown ? 'sDim' : 'sVal', r.jv)}${cell(unknown ? 'sDimC' : match ? 'sPass' : 'sFail', unknown ? '\u2014' : match ? 'PASS' : 'FAIL')}</Row>`)
      }
      rows.push('<Row ss:Height="8"/>')
    }

    // Accounting Definition — Applied Rules
    if (jvAccountRows.length > 0 && accountingDef.length > 0) {
      const normName = (s: string) => s.trim().toLowerCase()
      const defByName = new Map<string, typeof accountingDef[0]>()
      for (const d of accountingDef) {
        const k = normName(d.account_name) + '|' + (d.dr_cr || '').toLowerCase()
        if (!defByName.has(k)) defByName.set(k, d)
      }
      const groups = new Map<string, typeof jvAccountRows>()
      for (const row of jvAccountRows) {
        const key = row.commodity || ''
        if (!groups.has(key)) groups.set(key, [])
        groups.get(key)!.push(row)
      }
      const sortedKeys = [...groups.keys()].sort((a, b) =>
        a === '' ? 1 : b === '' ? -1 : a.localeCompare(b),
      )
      const jvAccountNameSet = new Set(jvAccountRows.map(r => normName(r.account_name)))
      const notApplied = accountingDef.filter((d, i, arr) => {
        const k = normName(d.account_name)
        const firstIdx = arr.findIndex(x => normName(x.account_name) === k && x.dr_cr === d.dr_cr)
        return firstIdx === i && !jvAccountNameSet.has(k)
      })

      rows.push(`<Row ss:Height="19">${cell('sSection', 'ACCOUNTING DEFINITION \u2014 APPLIED RULES', 4)}</Row>`)
      rows.push(`<Row>${cell('sHead', 'Account')}${cell('sHeadC', 'Dr/Cr')}${cell('sHeadR', 'Amount')}${cell('sHead', 'Rule / Condition')}${cell('sHeadC', 'Status')}</Row>`)

      for (const commodity of sortedKeys) {
        rows.push(`<Row ss:Height="15">${cell('sGroup', commodity ? commodity.toUpperCase() : 'SHARED \u2014 all items', 4)}</Row>`)
        const groupRows = groups.get(commodity)!
        let groupDr = 0, groupCr = 0
        for (const row of groupRows) {
          const def = defByName.get(normName(row.account_name) + '|' + (row.dr_cr || '').toLowerCase())
          const drCrMatch = !!def && def.dr_cr === row.dr_cr
          const status = !def ? 'EXTRA' : drCrMatch ? 'PASS' : 'WRONG TYPE'
          const condText = def?.condition_text || (def ? 'Always applies' : '\u2014')
          const amtStyle = row.dr_cr === 'Debit' ? 'sDr' : 'sCr'
          if (row.amount != null) { row.dr_cr === 'Debit' ? (groupDr += row.amount) : (groupCr += row.amount) }
          const amtCell = row.amount != null ? cell(amtStyle, row.amount) : emptyCell('sValR')
          rows.push(`<Row>${cell('sVal', row.account_name)}${cell('sDrCrBadge', row.dr_cr)}${amtCell}${cell('sCond', condText)}${cell(status === 'PASS' ? 'sPass' : status === 'EXTRA' ? 'sFail' : 'sWarn', status)}</Row>`)
        }
        if (groupRows.length > 1) {
          rows.push(`<Row ss:Height="15">${emptyCell('sSubtotalL')}${cell('sSubtotalL', 'Subtotal')}${cell('sSubtotalR', groupDr || '')}${cell('sSubtotalR', groupCr || '')}${emptyCell('sSubtotalL')}</Row>`)
        }
      }

      // Grand totals row
      const totalDr = jvAccountRows.filter(r => r.dr_cr === 'Debit' && r.amount != null).reduce((s, r) => s + r.amount!, 0)
      const totalCr = jvAccountRows.filter(r => r.dr_cr === 'Credit' && r.amount != null).reduce((s, r) => s + r.amount!, 0)
      const balanced = Math.abs(totalDr - totalCr) < 0.01
      rows.push(`<Row ss:Height="18">${cell('sTotalL', 'TOTALS', 1)}${cell('sTotalDr', totalDr)}${cell('sTotalCr', totalCr)}${cell(balanced ? 'sPass' : 'sFail', balanced ? 'DR = CR \u2713' : 'DR \u2260 CR \u2715')}</Row>`)

      if (notApplied.length > 0) {
        rows.push('<Row ss:Height="8"/>')
        rows.push(`<Row ss:Height="15">${cell('sGroupMuted', 'NOT APPLIED THIS TRANSACTION', 4)}</Row>`)
        rows.push(`<Row>${cell('sHeadMuted', 'Account')}${cell('sHeadMuted', 'Dr/Cr')}${cell('sHeadMuted', '\u2014')}${cell('sHeadMuted', 'Why not applied (condition)')}${cell('sHeadMuted', '\u2014')}</Row>`)
        for (const def of notApplied) {
          rows.push(`<Row>${cell('sDim', def.account_name)}${cell('sDimC', def.dr_cr)}${emptyCell('sDim')}${cell('sDim', def.condition_text || (def.has_conditions ? 'Conditional \u2014 condition not met' : 'Always applies'))}${cell('sDimC', 'n/a')}</Row>`)
        }
      }
    }
    rows.push('<Row ss:Height="12"/>')
    rows.push(`<Row ss:Height="14">${cell('sMeta', 'Generated by Pacs Automation \u2014 JV Verification Report', 4)}</Row>`)

    const XL_BORDER_DARK = '<Borders><Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B0B0B0"/><Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B0B0B0"/><Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B0B0B0"/><Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B0B0B0"/></Borders>'
    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
<Styles>
<Style ss:ID="Default" ss:Name="Normal"><Font ss:FontName="Calibri" ss:Size="10" ss:Color="#212121"/><Alignment ss:Vertical="Center"/></Style>
<Style ss:ID="sTitle"><Font ss:Bold="1" ss:Size="15" ss:Color="#FFFFFF"/><Interior ss:Color="#283593" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="2"/></Style>
<Style ss:ID="sMeta"><Font ss:Italic="1" ss:Size="9" ss:Color="#546E7A"/><Alignment ss:Vertical="Center" ss:Indent="1"/></Style>
<Style ss:ID="sSection"><Font ss:Bold="1" ss:Size="10" ss:Color="#1A237E"/><Interior ss:Color="#C5CAE9" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sLabel"><Font ss:Bold="1" ss:Size="10" ss:Color="#37474F"/><Interior ss:Color="#ECEFF1" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sVal"><Font ss:Color="#212121"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sValR"><Font ss:Color="#212121"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sMoney"><Font ss:Color="#212121"/><NumberFormat ss:Format="#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sDr"><Font ss:Bold="1" ss:Color="#0D47A1"/><NumberFormat ss:Format="&quot;DR  &quot;#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sCr"><Font ss:Bold="1" ss:Color="#4A148C"/><NumberFormat ss:Format="&quot;CR  &quot;#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sHead"><Font ss:Bold="1" ss:Size="10" ss:Color="#FFFFFF"/><Interior ss:Color="#3949AB" ss:Pattern="Solid"/><Alignment ss:Horizontal="Left" ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sHeadC"><Font ss:Bold="1" ss:Size="10" ss:Color="#FFFFFF"/><Interior ss:Color="#3949AB" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sHeadR"><Font ss:Bold="1" ss:Size="10" ss:Color="#FFFFFF"/><Interior ss:Color="#3949AB" ss:Pattern="Solid"/><Alignment ss:Horizontal="Right" ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sHeadMuted"><Font ss:Bold="1" ss:Size="9" ss:Color="#ECEFF1"/><Interior ss:Color="#607D8B" ss:Pattern="Solid"/><Alignment ss:Horizontal="Left" ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sPass"><Font ss:Bold="1" ss:Size="10" ss:Color="#1B5E20"/><Interior ss:Color="#A5D6A7" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sFail"><Font ss:Bold="1" ss:Size="10" ss:Color="#B71C1C"/><Interior ss:Color="#EF9A9A" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sWarn"><Font ss:Bold="1" ss:Size="10" ss:Color="#BF360C"/><Interior ss:Color="#FFCC80" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sPassText"><Font ss:Bold="1" ss:Color="#2E7D32"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sFailText"><Font ss:Bold="1" ss:Color="#C62828"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sDim"><Font ss:Color="#78909C"/><Interior ss:Color="#F9FAFB" ss:Pattern="Solid"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sDimC"><Font ss:Color="#78909C"/><Interior ss:Color="#F9FAFB" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sGroup"><Font ss:Bold="1" ss:Italic="1" ss:Size="9" ss:Color="#1A237E"/><Interior ss:Color="#E8EAF6" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sGroupMuted"><Font ss:Bold="1" ss:Italic="1" ss:Size="9" ss:Color="#546E7A"/><Interior ss:Color="#ECEFF1" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sDrCrBadge"><Font ss:Bold="1" ss:Size="9" ss:Color="#37474F"/><Interior ss:Color="#ECEFF1" ss:Pattern="Solid"/><Alignment ss:Horizontal="Center" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sCond"><Font ss:FontName="Consolas" ss:Size="9" ss:Color="#37474F"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sTotalL"><Font ss:Bold="1" ss:Size="10" ss:Color="#212121"/><Interior ss:Color="#CFD8DC" ss:Pattern="Solid"/><Alignment ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sTotalDr"><Font ss:Bold="1" ss:Color="#0D47A1"/><Interior ss:Color="#BBDEFB" ss:Pattern="Solid"/><NumberFormat ss:Format="&quot;DR  &quot;#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sTotalCr"><Font ss:Bold="1" ss:Color="#4A148C"/><Interior ss:Color="#E1BEE7" ss:Pattern="Solid"/><NumberFormat ss:Format="&quot;CR  &quot;#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sSubtotalL"><Font ss:Italic="1" ss:Color="#546E7A"/><Interior ss:Color="#F5F5F5" ss:Pattern="Solid"/><Alignment ss:Horizontal="Right" ss:Vertical="Center" ss:Indent="1"/>${XL_BORDER_DARK}</Style>
<Style ss:ID="sSubtotalR"><Font ss:Italic="1" ss:Color="#546E7A"/><Interior ss:Color="#F5F5F5" ss:Pattern="Solid"/><NumberFormat ss:Format="#,##0.00"/><Alignment ss:Horizontal="Right" ss:Vertical="Center"/>${XL_BORDER_DARK}</Style>
</Styles>
<Worksheet ss:Name="JV Report">
<Table ss:DefaultRowHeight="18">
<Column ss:Width="140"/>
<Column ss:Width="145"/>
<Column ss:Width="95"/>
<Column ss:Width="165"/>
<Column ss:Width="90"/>
${rows.join('\n')}
</Table>
</Worksheet>
</Workbook>`

    const blob = new Blob([xml], { type: 'application/vnd.ms-excel;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${pbRefNo.replace(/[\\/]/g, '-')}_JV_Report.xls`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }, [selectedPB, jvSteps, jvCompRows, jvAccountRows, accountingDef, pbRefNo])

  // PDF export — same content as the .xls export but laid out as a styled A4
  // report (jsPDF) that opens in a new browser tab instead of downloading.
  const exportJvPdf = useCallback(async () => {
    const found = jvSteps.find(s => s.n === 1)
    const fieldsStep = jvSteps.find(s => s.fields)
    const balanceStep = jvSteps.find(s => s.detail && !s.fields)
    if (!selectedPB || (!found && !fieldsStep)) return
    const fieldMismatch = (jvCompRows ?? []).some(r => r.pb !== '—' && r.jv !== '—' && r.pb.trim().toLowerCase() !== r.jv.trim().toLowerCase())
    const _defMap = new Map<string, typeof accountingDef[0]>()
    for (const d of accountingDef) { const k = d.account_name.trim().toLowerCase()+'|'+(d.dr_cr||'').toLowerCase(); if (!_defMap.has(k)) _defMap.set(k,d) }
    const accountRowFail = jvAccountRows.some(r => { const def=_defMap.get(r.account_name.trim().toLowerCase()+'|'+(r.dr_cr||'').toLowerCase()); return !def||def.dr_cr!==r.dr_cr })
    const jvDrTotal = jvAccountRows.filter(r=>r.dr_cr==='Debit').reduce((s,r)=>s+(r.amount??0),0)
    const amountMismatch = selectedPB.amount!=null && jvAccountRows.length>0 && Math.abs(Number(selectedPB.amount)-jvDrTotal)>0.02
    const ok = jvSteps.length > 0 && jvSteps.every(s => s.ok) && !fieldMismatch && !accountRowFail && !amountMismatch
    const balMatch = balanceStep?.detail?.match(/DR\s*=\s*([\d,]+\.?\d*)\s+\|CR\|\s*=\s*([\d,]+\.?\d*)/)
    const amountNum = selectedPB.amount != null ? Number(selectedPB.amount) : null

    const { jsPDF } = await import('jspdf')
    const doc = new jsPDF({ unit: 'mm', format: 'a4' })
    const PW = 210, PH = 297, M = 14, CW = PW - M * 2 // 182mm content width

    const safe = (v: string | number | null | undefined) =>
      String(v ?? '')
        .replace(/\u20B9/g, 'Rs. ').replace(/[\u2014\u2013]/g, '-').replace(/[\u2018\u2019]/g, "'")
        .replace(/[\u201C\u201D]/g, '"').replace(/\u00B7/g, '|').replace(/\u2265/g, '>=')
        .replace(/\u2264/g, '<=').replace(/\u00D7/g, 'x').replace(/\u00A0/g, ' ')
        .replace(/\u2194/g, '<->').replace(/\u2260/g, '!=').replace(/\u2713/g, 'OK').replace(/\u2715/g, 'X')

    const fmt = (n: number) => n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

    // ── Palette ──
    const NAVY: [number,number,number]    = [40, 53, 147]
    const NAVY_D: [number,number,number]  = [26, 35, 126]
    const HEAD_BG: [number,number,number] = [57, 73, 171]
    const SEC_BG: [number,number,number]  = [197, 202, 233]
    const LBL_BG: [number,number,number]  = [236, 239, 241]
    const BDR: [number,number,number]     = [176, 176, 176]
    const TXT: [number,number,number]     = [33, 33, 33]
    const TXT_MED: [number,number,number] = [33, 33, 33] // used for condition/rule text — same as body so small mono stays readable
    const TXT_DIM: [number,number,number] = [84, 100, 114] // ~5.5:1 on white — muted but AA-readable
    const DR_T: [number,number,number]    = [13, 71, 161]
    const CR_T: [number,number,number]    = [74, 20, 140]
    const GRN_F: [number,number,number]   = [165, 214, 167], GRN_T: [number,number,number] = [27, 94, 32]
    const RED_F: [number,number,number]   = [239, 154, 154], RED_T: [number,number,number] = [183, 28, 28]
    const AMB_F: [number,number,number]   = [255, 204, 128], AMB_T: [number,number,number] = [191, 54, 12]
    const DR_F: [number,number,number]    = [187, 222, 251]
    const CR_F: [number,number,number]    = [225, 190, 231]
    const TOT_F: [number,number,number]   = [207, 216, 220]
    const STATUS_S: Record<string,{fill:[number,number,number];text:[number,number,number]}|undefined> = {
      PASS:{fill:GRN_F,text:GRN_T}, MATCHED:{fill:GRN_F,text:GRN_T}, PASSED:{fill:GRN_F,text:GRN_T},
      FAIL:{fill:RED_F,text:RED_T}, EXTRA:{fill:RED_F,text:RED_T}, MISMATCHED:{fill:RED_F,text:RED_T}, FAILED:{fill:RED_F,text:RED_T},
      'WRONG TYPE':{fill:AMB_F,text:AMB_T},
    }

    let y = M
    const need = (h: number) => { if (y + h > PH - M - 8) { doc.addPage(); y = M } }

    type CS = {
      t: string; span?: number; align?: 'L'|'C'|'R'
      color?: [number,number,number]; fill?: [number,number,number]|null
      bold?: boolean; italic?: boolean; size?: number; mono?: boolean; lbl?: boolean
    }

    // Factory — builds a row renderer for a given column-width array (mm).
    // Cell text wraps within its column (splitTextToSize); the row grows to
    // fit the tallest cell (capped at MAX_LINES, then ellipsised) so content
    // never spills into the neighbouring column.
    const makeRow = (cols: number[]) => (cells: CS[], h = 6.5) => {
      const PAD = 2.5
      const MAX_LINES = 5
      // Pass 1 — measure wrapped lines per cell (font must be set before split)
      let colIdx = 0
      const measured = cells.map((c) => {
        const span = c.span ?? 1
        const cw = cols.slice(colIdx, colIdx + span).reduce((a, b) => a + b, 0)
        const fs = c.size ?? (c.lbl ? 8 : 9)
        doc.setFont(c.mono ? 'courier' : 'helvetica', (c.bold || c.lbl) && c.italic ? 'bolditalic' : c.bold || c.lbl ? 'bold' : c.italic ? 'italic' : 'normal')
        doc.setFontSize(fs)
        let lines: string[] = doc.splitTextToSize(safe(c.t), cw - PAD * 2)
        if (lines.length > MAX_LINES) {
          lines = lines.slice(0, MAX_LINES)
          lines[MAX_LINES - 1] = lines[MAX_LINES - 1].replace(/.{3}$/, '') + '...'
        }
        colIdx += span
        return { c, cw, fs, lines }
      })
      // Row height grows to fit the tallest wrapped cell
      const rh = Math.max(h, ...measured.map(m => m.lines.length * m.fs * 0.353 * 1.25 + 2.4))
      need(rh)

      // Pass 2 — draw
      doc.setDrawColor(...BDR)
      let cx = M
      for (const { c, cw, fs, lines } of measured) {
        if (c.fill !== null) {
          const bg = c.fill ?? (c.lbl ? LBL_BG : null)
          if (bg) { doc.setFillColor(...bg); doc.rect(cx, y, cw, rh, 'FD') }
          else doc.rect(cx, y, cw, rh, 'S')
        }
        doc.setFont(c.mono ? 'courier' : 'helvetica', (c.bold || c.lbl) && c.italic ? 'bolditalic' : c.bold || c.lbl ? 'bold' : c.italic ? 'italic' : 'normal')
        doc.setFontSize(fs)
        doc.setTextColor(...(c.color ?? (c.lbl ? TXT_MED : TXT)))
        const tx = c.align==='C' ? cx+cw/2 : c.align==='R' ? cx+cw-PAD : cx+PAD
        const alignOpt = c.align==='C' ? 'center' as const : c.align==='R' ? 'right' as const : 'left' as const
        const lineStep = fs * 0.353 * 1.25
        let ly = y + (rh - lines.length * lineStep) / 2 + fs * 0.353 * 0.9
        for (const ln of lines) {
          doc.text(ln, tx, ly, { align: alignOpt })
          ly += lineStep
        }
        cx += cw
      }
      y += rh
    }

    // 4-col layout for cross-check [Field | PB | JV | Match]
    const COLS4: number[] = [42, 58, 58, 24]
    const row4 = makeRow(COLS4)
    // 5-col layout for AD section [Account | Dr/Cr | Amount | Condition | Status]
    // Condition column is widest — long rule strings wrap there, never overflow.
    const COLS5: number[] = [40, 16, 34, 70, 22]
    const row5 = makeRow(COLS5)

    const sectionHeader = (title: string) => {
      need(14); y += 4
      doc.setFillColor(...SEC_BG); doc.rect(M, y, CW, 7.5, 'F')
      doc.setDrawColor(...BDR); doc.rect(M, y, CW, 7.5, 'S')
      doc.setFont('helvetica', 'bold'); doc.setFontSize(9); doc.setTextColor(...NAVY_D)
      doc.text(title.toUpperCase(), M+3, y+5)
      y += 7.5
    }

    const groupBand = (title: string, muted = false) => {
      need(7)
      const bg: [number,number,number] = muted ? [236,239,241] : [232,234,246]
      const tc: [number,number,number] = muted ? TXT_DIM : NAVY_D
      doc.setFillColor(...bg); doc.rect(M, y, CW, 6, 'F')
      doc.setDrawColor(...BDR); doc.rect(M, y, CW, 6, 'S')
      doc.setFont('helvetica', 'bolditalic'); doc.setFontSize(8); doc.setTextColor(...tc)
      doc.text(safe(title), M+3, y+4)
      y += 6
    }

    // ── Title banner ──
    doc.setFillColor(...NAVY); doc.rect(M, y, CW, 16, 'F')
    doc.setFont('helvetica','bold'); doc.setFontSize(15); doc.setTextColor(255,255,255)
    doc.text('JV VERIFICATION REPORT', M+4, y+10.5)
    const chipText = ok ? 'PASSED' : 'FAILED'
    const st = STATUS_S[chipText]!
    doc.setFontSize(10)
    const chipW = doc.getTextWidth(chipText)+7
    doc.setFillColor(...st.fill); doc.roundedRect(PW-M-chipW-2, y+4.5, chipW, 7.5, 1.5, 1.5, 'F')
    doc.setTextColor(...st.text); doc.text(chipText, PW-M-chipW+1, y+9.5)
    y += 16

    // meta line
    doc.setFont('helvetica','italic'); doc.setFontSize(8); doc.setTextColor(...TXT_DIM)
    y += 5
    doc.text(safe(`Document: ${pbRefNo}   |   Generated: ${new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}`), M+1, y)
    y += 3

    // ── Document Details ──
    sectionHeader('Document Details')
    row4([{ t:'Supplier', lbl:true }, { t:safe(selectedPB.supplier??'-'), span:3 }])
    row4([
      { t:'Amount', lbl:true },
      amountNum!=null ? { t:`Rs. ${fmt(amountNum)}`, align:'R', bold:true, color:TXT } : { t:'-', color:TXT_DIM },
      { t:'Date', lbl:true },
      { t:safe(selectedPB.date??'-') },
    ])

    // ── Journal Voucher ──
    sectionHeader('Journal Voucher')
    row4([
      { t:'JV Entry', lbl:true },
      found
        ? { t: found.ok ? 'Entry found in JV report' : `Not found - ${found.detail??''}`, span:3, bold:true, color:found.ok?GRN_T:RED_T }
        : { t:'Not checked', span:3, color:TXT_DIM },
    ])
    if (balMatch) {
      const drNum = Number(balMatch[1].replace(/,/g,''))
      const crNum = Number(balMatch[2].replace(/,/g,''))
      const bOk = !!balanceStep?.ok
      row4([
        { t:'Balance Check', lbl:true },
        { t:`DR  ${fmt(drNum)}`, mono:true, color:DR_T, size:8 },
        { t:`CR  ${fmt(crNum)}`, mono:true, color:CR_T, size:8 },
        { t:bOk?'BALANCED':'UNBALANCED', align:'C', bold:true, size:8, fill:bOk?GRN_F:RED_F, color:bOk?GRN_T:RED_T },
      ])
    }

    // ── Accounting Field Cross-check ──
    const xrows = jvCompRows ?? fieldsStep?.fields?.map(f => ({ label:f.field, pb:'\u2014', jv:f.value })) ?? []
    if (xrows.length > 0) {
      sectionHeader('Accounting Field Cross-check')
      row4([
        { t:'Field',            fill:HEAD_BG, color:[255,255,255], size:8 },
        { t:'Purchase Booking', fill:HEAD_BG, color:[255,255,255], size:8 },
        { t:'Journal Voucher',  fill:HEAD_BG, color:[255,255,255], size:8 },
        { t:'Match',            fill:HEAD_BG, color:[255,255,255], size:8, align:'C' },
      ], 7)
      for (const r of xrows) {
        const match = r.pb!=='\u2014' && r.jv!=='\u2014' && r.pb.trim().toLowerCase()===r.jv.trim().toLowerCase()
        const unk = r.pb==='\u2014' || r.jv==='\u2014'
        row4([
          { t:r.label||'', lbl:!!r.label, color:r.label?undefined:TXT_DIM },
          { t:safe(r.pb), color:unk?TXT_DIM:TXT },
          { t:safe(r.jv), color:unk?TXT_DIM:TXT },
          unk
            ? { t:'-', align:'C', color:TXT_DIM }
            : { t:match?'PASS':'FAIL', align:'C', bold:true, size:8, fill:match?GRN_F:RED_F, color:match?GRN_T:RED_T },
        ])
      }
    }

    // ── Accounting Definition — Applied Rules ──
    if (jvAccountRows.length > 0 && accountingDef.length > 0) {
      const normName = (s: string) => s.trim().toLowerCase()
      const defByName = new Map<string, typeof accountingDef[0]>()
      for (const d of accountingDef) { const k=normName(d.account_name)+'|'+(d.dr_cr||'').toLowerCase(); if(!defByName.has(k)) defByName.set(k,d) }
      const groups = new Map<string, typeof jvAccountRows>()
      for (const ar of jvAccountRows) { const key=ar.commodity||''; if(!groups.has(key)) groups.set(key,[]); groups.get(key)!.push(ar) }
      const sortedKeys = [...groups.keys()].sort((a,b) => a===''?1:b===''?-1:a.localeCompare(b))
      const jvNameSet = new Set(jvAccountRows.map(r => normName(r.account_name)))
      const notApplied = accountingDef.filter((d,i,arr) => {
        const k=normName(d.account_name)
        return arr.findIndex(x=>normName(x.account_name)===k&&x.dr_cr===d.dr_cr)===i && !jvNameSet.has(k)
      })

      sectionHeader('Accounting Definition - Applied Rules')
      row5([
        { t:'Account',        fill:HEAD_BG, color:[255,255,255], size:8 },
        { t:'Dr/Cr',          fill:HEAD_BG, color:[255,255,255], size:8, align:'C' },
        { t:'Amount',         fill:HEAD_BG, color:[255,255,255], size:8, align:'R' },
        { t:'Rule / Condition', fill:HEAD_BG, color:[255,255,255], size:8 },
        { t:'Status',         fill:HEAD_BG, color:[255,255,255], size:8, align:'C' },
      ], 7)

      let totalDr = 0, totalCr = 0
      for (const commodity of sortedKeys) {
        groupBand(commodity ? commodity.toUpperCase() : 'SHARED - all items')
        const gRows = groups.get(commodity)!
        let gDr = 0, gCr = 0
        for (const ar of gRows) {
          const def = defByName.get(normName(ar.account_name)+'|'+(ar.dr_cr||'').toLowerCase())
          const match = !!def && def.dr_cr===ar.dr_cr
          const status = !def?'EXTRA':match?'PASS':'WRONG TYPE'
          const rawCond = def?.condition_text||(def?'Always applies':'-')
          const cond = rawCond.replace(/\s+AND\s+/gi, '\nAND ')
          const ss = STATUS_S[status]!
          const isDr = ar.dr_cr==='Debit'
          const amtCol: [number,number,number] = isDr ? DR_T : CR_T
          if (ar.amount!=null) { isDr?(gDr+=ar.amount):(gCr+=ar.amount) }
          row5([
            { t:safe(ar.account_name), bold:true, color:TXT },
            { t:safe(ar.dr_cr), color:isDr?DR_T:CR_T, size:8, align:'C', bold:true },
            { t:ar.amount!=null?fmt(ar.amount):'-', bold:true, color:ar.amount!=null?amtCol:TXT_DIM, size:8, align:'R' },
            { t:safe(cond), color:TXT, size:7.5 },
            { t:status, align:'C', bold:true, size:8, fill:ss.fill, color:ss.text },
          ])
        }
        totalDr+=gDr; totalCr+=gCr
        // per-commodity subtotal when >1 rows
        if (gRows.length>1 && (gDr>0 || gCr>0)) {
          row5([
            { t:'', fill:null },
            { t:'Subtotal', size:7.5, color:TXT_DIM, span:1 },
            { t:gDr>0?fmt(gDr):gCr>0?fmt(gCr):'-', mono:true, color:gDr>0?DR_T:CR_T, size:7.5, align:'R' },
            { t:'', fill:null },
            { t:'', fill:null },
          ], 5.5)
        }
      }
      // totals from the full account rows list (avoids scoping issues)
      const tDr = jvAccountRows.filter(r=>r.dr_cr==='Debit'&&r.amount!=null).reduce((s,r)=>s+r.amount!,0)
      const tCr = jvAccountRows.filter(r=>r.dr_cr==='Credit'&&r.amount!=null).reduce((s,r)=>s+r.amount!,0)
      const balanced = Math.abs(tDr-tCr)<0.01
      need(9)
      // Draw totals bar manually for full-width control
      need(8)
      doc.setFillColor(...TOT_F); doc.rect(M, y, CW, 8, 'FD')
      doc.setFont('helvetica','bold'); doc.setFontSize(9); doc.setTextColor(...TXT)
      doc.text('TOTALS', M+3, y+5.2)
      doc.setFont('helvetica','bold'); doc.setFontSize(9); doc.setTextColor(...DR_T)
      doc.setFillColor(...DR_F); doc.rect(M+COLS5[0], y, COLS5[1]+COLS5[2], 8, 'FD')
      doc.text(`DR  ${fmt(tDr)}`, M+COLS5[0]+COLS5[1]+COLS5[2]-2, y+5.2, { align:'right' })
      doc.setFont('helvetica','bold'); doc.setFontSize(9); doc.setTextColor(...CR_T)
      doc.setFillColor(...CR_F); doc.rect(M+COLS5[0]+COLS5[1]+COLS5[2], y, COLS5[3], 8, 'FD')
      doc.text(`CR  ${fmt(tCr)}`, M+COLS5[0]+COLS5[1]+COLS5[2]+COLS5[3]-2, y+5.2, { align:'right' })
      const bSt = balanced ? GRN_F : RED_F
      const bTc = balanced ? GRN_T : RED_T
      const bTxt = balanced ? 'DR = CR  OK' : 'DR != CR  !'
      doc.setFillColor(...bSt); doc.rect(M+COLS5[0]+COLS5[1]+COLS5[2]+COLS5[3], y, COLS5[4], 8, 'FD')
      doc.setFont('helvetica','bold'); doc.setFontSize(8); doc.setTextColor(...bTc)
      doc.text(bTxt, M+COLS5[0]+COLS5[1]+COLS5[2]+COLS5[3]+COLS5[4]/2, y+5.2, { align:'center' })
      doc.setDrawColor(...BDR); doc.rect(M, y, CW, 8, 'S')
      y += 8

      if (notApplied.length > 0) {
        y += 3
        groupBand('NOT APPLIED THIS TRANSACTION', true)
        row5([
          { t:'Account',           fill:HEAD_BG, color:[255,255,255], size:7.5 },
          { t:'Dr/Cr',             fill:HEAD_BG, color:[255,255,255], size:7.5, align:'C' },
          { t:'-',                 fill:HEAD_BG, color:[255,255,255], size:7.5, align:'C' },
          { t:'Why not applied',   fill:HEAD_BG, color:[255,255,255], size:7.5 },
          { t:'-',                 fill:HEAD_BG, color:[255,255,255], size:7.5, align:'C' },
        ], 6)
        for (const d of notApplied) {
          row5([
            { t:safe(d.account_name), color:TXT_DIM },
            { t:safe(d.dr_cr), color:TXT_DIM, size:8, align:'C' },
            { t:'-', color:TXT_DIM, size:8, align:'C' },
            { t:safe((d.condition_text||(d.has_conditions?'Conditional - condition not met':'Always applies')).replace(/\s+AND\s+/gi,'\nAND ')), color:TXT_DIM, size:7.5 },
            { t:'n/a', color:TXT_DIM, size:8, align:'C' },
          ])
        }
      }
    }

    // ── Footer ──
    need(10); y += 5
    doc.setDrawColor(...BDR); doc.line(M, y-1, M+CW, y-1)
    doc.setFont('helvetica','italic'); doc.setFontSize(7.5); doc.setTextColor(...TXT_DIM)
    doc.text(safe(`Generated by RhythmERP Automation - JV Verification  |  ${pbRefNo}`), M, y+2)

    const filename = `${pbRefNo.replace(/[\\/]/g, '-')}_JV_Report.pdf`
    const blob = doc.output('blob')
    const pdfUrl = URL.createObjectURL(blob)
    const dlBtn = `<a href="${pdfUrl}" download="${filename}" style="position:fixed;top:8px;right:12px;z-index:9999;padding:6px 14px;background:#3F51B5;color:#fff;border-radius:6px;font:13px/1 sans-serif;text-decoration:none">⬇ Download</a>`
    const win = window.open('', '_blank')
    if (win) {
      win.document.write(
        `<!doctype html><html><head><title>${filename}</title></head>` +
        `<body style="margin:0;height:100vh">${dlBtn}` +
        `<embed src="${pdfUrl}" type="application/pdf" width="100%" height="100%"/>` +
        `</body></html>`
      )
      win.document.close()
    }
    setTimeout(() => URL.revokeObjectURL(pdfUrl), 120_000)
  }, [selectedPB, jvSteps, jvCompRows, jvAccountRows, accountingDef, pbRefNo])

  if (showJVCheck) {
    const token = erpToken || localToken
    const tenant = localTenantId || erpTenantId
    const canVerify = !!token && !!tenant && !!pbRefNo.trim() && !verifying
    return (
      <div className="relative flex flex-col h-full min-h-0 gap-4">
        <div className="bg-white dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg flex flex-col min-h-0 flex-1 overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 shrink-0 flex items-center gap-2">
            <Search className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
            <span className="text-[13px] font-semibold text-gray-800 dark:text-gray-100">JV Verification</span>
            <span className="text-[11px] text-gray-400 dark:text-gray-500">— look up a Purchase Booking's Journal Voucher</span>
          </div>

          <div ref={scrollContainerRef} className="p-4 overflow-y-auto flex-1 min-h-0 space-y-4">
            {/* Token panel — same as full purchase flow */}
            {showTokenInput && (
              <div ref={tokenSectionRef} className="p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
                <Label className="text-[11px] text-orange-600 dark:text-orange-400 mb-1.5 block font-medium">ERP Credentials</Label>
                <div className="flex items-center gap-2 mb-2">
                  <Input
                    type="password"
                    value={localToken}
                    onChange={(e) => setLocalToken(e.target.value)}
                    placeholder="Paste your Bearer token here..."
                    className={`h-9 text-[12px] flex-1 ${
                      localToken && (localToken.startsWith('Bearer ') ? localToken.slice(7) : localToken).startsWith('eyJ') && localToken.split('.').length === 3 && localToken.length > 100
                        ? 'border-green-400'
                        : localToken ? 'border-red-400' : ''
                    }`}
                  />
                </div>
                {(() => {
                  if (!localToken) return null
                  const t = localToken.startsWith('Bearer ') ? localToken.slice(7) : localToken
                  const isValid = t.startsWith('eyJ') && t.split('.').length === 3 && t.length > 100
                  if (isValid) return (
                    <p className="text-[11px] text-green-600 dark:text-green-400 flex items-center gap-1 mb-2">
                      <span className="inline-block size-2 rounded-full bg-green-500" />
                      Token looks valid
                    </p>
                  )
                  return (
                    <div ref={tokenErrorRef} className="mb-2 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-2.5 space-y-1.5">
                      <div className="flex items-center gap-1.5">
                        <AlertTriangle className="size-3 text-red-500 shrink-0" />
                        <span className="text-[11px] font-semibold text-red-600 dark:text-red-400">
                          {!t.startsWith('eyJ') ? 'Token must start with eyJ…' : 'Token format looks incorrect'}
                        </span>
                      </div>
                      <p className="text-[11px] text-red-500 dark:text-red-400">
                        Copy from DevTools → Network → any request → Authorization header. Remove the "Bearer " prefix.
                      </p>
                    </div>
                  )
                })()}
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {[
                    { id: '795', name: 'Jalpan Builders' },
                    { id: '666', name: 'Jay Kisan Ltd' },
                    { id: '686', name: 'Agristack Company' },
                    { id: '751', name: 'Tech Neo' },
                  ].map(t => (
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
                <div className="flex items-center gap-2">
                  <Input
                    type="text"
                    value={localTenantId}
                    onChange={(e) => setLocalTenantId(e.target.value)}
                    placeholder="Tenant ID (e.g. 708, 711)"
                    className="h-9 text-[12px] w-48"
                  />
                  <Button
                    onClick={() => { setShowTokenInput(false); loadPBList() }}
                    variant="ghost"
                    size="sm"
                    className="h-9 text-[12px] cursor-pointer"
                  >
                    Done
                  </Button>
                </div>
                <p className="text-[11px] text-orange-500 dark:text-orange-400 mt-1.5">Credentials stay in your browser session. Clear below to reset.</p>
              </div>
            )}

            {/* PB list — only shown when token panel is closed */}
            {!showTokenInput && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label className="text-[11px] text-gray-700 dark:text-gray-300">Select Purchase Booking</Label>
                  <button
                    onClick={loadPBList}
                    disabled={pbListLoading}
                    className="text-[11px] text-[#3F51B5] dark:text-[#7986CB] flex items-center gap-1 hover:underline cursor-pointer disabled:opacity-50"
                  >
                    <RefreshCw className={`size-3 ${pbListLoading ? 'animate-spin' : ''}`} />
                    Refresh
                  </button>
                </div>

                {pbListError && (
                  <p className="text-[11px] text-red-500 dark:text-red-400 mb-2">{pbListError}</p>
                )}

                {pbListLoading && pbList.length === 0 && (
                  <div className="flex items-center gap-2 text-[12px] text-gray-500 dark:text-gray-400 py-4">
                    <Loader2 className="size-4 animate-spin" />
                    Fetching purchase bookings…
                  </div>
                )}

                {!pbListLoading && pbList.length === 0 && !pbListError && (
                  <p className="text-[12px] text-gray-400 dark:text-gray-500 py-2">
                    No purchase bookings found. Click Refresh or check your token.
                  </p>
                )}

                {pbList.length > 0 && pbListOpen && (
                  <>
                    <Input
                      value={pbSearch}
                      onChange={(e) => setPbSearch(e.target.value)}
                      placeholder="Search by ref no or supplier…"
                      className="h-8 text-[12px] mb-2"
                    />
                    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden max-h-64 overflow-y-auto">
                      {pbList
                        .filter(pb => {
                          const q = pbSearch.toLowerCase()
                          return !q || pb.ref_no.toLowerCase().includes(q) || pb.supplier.toLowerCase().includes(q)
                        })
                        .map((pb) => (
                          <button
                            key={pb.ref_no}
                            onClick={() => {
                              setPbRefNo(pb.ref_no); setSelectedPB(pb); setPbListOpen(false); handleVerify(pb.ref_no)
                              if (pb.id) {
                                setPbItemsLoading(true); setPbItems([])
                                fetchPBItems(localToken || erpToken, localTenantId || erpTenantId, pb.id)
                                  .then(items => setPbItems(items))
                                  .catch(() => {})
                                  .finally(() => setPbItemsLoading(false))
                              }
                            }}
                            disabled={verifying}
                            className="w-full text-left px-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0 hover:bg-[#3F51B5]/5 dark:hover:bg-[#3F51B5]/10 transition-colors cursor-pointer disabled:opacity-50"
                          >
                            <div className="flex items-center justify-between gap-3">
                              <span className="text-[12px] font-mono font-semibold text-gray-800 dark:text-gray-100 shrink-0">{pb.ref_no}</span>
                              {pb.amount && (
                                <span className="text-[11px] text-gray-500 dark:text-gray-400 shrink-0 font-medium">
                                  ₹{Number(pb.amount).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                                </span>
                              )}
                            </div>
                            {pb.supplier && (
                              <div className="mt-0.5 flex items-center justify-between gap-2">
                                <span className="text-[11px] text-gray-600 dark:text-gray-300 truncate font-medium">{pb.supplier}</span>
                                {pb.date && <span className="text-[10px] text-gray-400 dark:text-gray-500 shrink-0">{pb.date}</span>}
                              </div>
                            )}
                            {(pb.division || pb.department || pb.type_of_sale || pb.location) && (
                              <div className="mt-1 flex flex-wrap gap-1">
                                {[pb.division, pb.department, pb.type_of_sale, pb.location].filter(Boolean).map((tag) => (
                                  <span key={tag} className="px-1.5 py-0.5 rounded text-[10px] bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}
                          </button>
                        ))
                      }
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Results view — shown after a PB is selected */}
            {pbRefNo && !pbListOpen && (() => {
              const fieldMismatch = (jvCompRows ?? []).some(r =>
                r.pb !== '—' && r.jv !== '—' && r.pb.trim().toLowerCase() !== r.jv.trim().toLowerCase()
              )
              // computed later but needed for verdict — derive early
              const _defByNameEarly = new Map<string, typeof accountingDef[0]>()
              for (const d of accountingDef) {
                const k = d.account_name.trim().toLowerCase() + '|' + (d.dr_cr || '').toLowerCase()
                if (!_defByNameEarly.has(k)) _defByNameEarly.set(k, d)
              }
              const accountRowFail = jvAccountRows.some(row => {
                const def = _defByNameEarly.get(row.account_name.trim().toLowerCase() + '|' + (row.dr_cr || '').toLowerCase())
                return !def || def.dr_cr !== row.dr_cr  // EXTRA or WRONG TYPE
              })
              const pbAmt = selectedPB?.amount != null ? Number(selectedPB.amount) : null
              const jvDrTotal = jvAccountRows.filter(r => r.dr_cr === 'Debit').reduce((s, r) => s + (r.amount ?? 0), 0)
              const amountMismatch = pbAmt != null && jvAccountRows.length > 0 && Math.abs(pbAmt - jvDrTotal) > 0.02
              const passed = jvSteps.length > 0 && jvSteps.every(s => s.ok) && !fieldMismatch && !accountRowFail && !amountMismatch
              const failed = jvSteps.length > 0 && !passed
              const foundStep = jvSteps.find(s => s.n === 1)
              const fieldsStep = jvSteps.find(s => s.fields)
              const balanceStep = jvSteps.find(s => s.detail && !s.fields)
              const balM = balanceStep?.detail?.match(/DR\s*=\s*([\d,]+\.?\d*)\s+[|]CR[|]\s*=\s*([\d,]+\.?\d*)/)

              const normName = (s: string) => s.trim().toLowerCase()
              const fmtAmt = (n: number | null | undefined) =>
                n != null ? n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'

              const defByName = new Map<string, typeof accountingDef[0]>()
              for (const d of accountingDef) {
                const k = normName(d.account_name) + '|' + (d.dr_cr || '').toLowerCase()
                if (!defByName.has(k)) defByName.set(k, d)
              }
              const groups = new Map<string, typeof jvAccountRows>()
              for (const row of jvAccountRows) {
                const key = row.commodity || ''
                if (!groups.has(key)) groups.set(key, [])
                groups.get(key)!.push(row)
              }
              const sortedKeys = [...groups.keys()].sort((a, b) => a===''?1:b===''?-1:a.localeCompare(b))
              const jvNameSet = new Set(jvAccountRows.map(r => normName(r.account_name)))
              const notApplied = accountingDef.filter((d, i, arr) => {
                const k = normName(d.account_name)
                return arr.findIndex(x => normName(x.account_name)===k && x.dr_cr===d.dr_cr)===i && !jvNameSet.has(k)
              })
              const totalDr = jvAccountRows.filter(r => r.dr_cr==='Debit').reduce((s,r)=>s+(r.amount??0),0)
              const totalCr = jvAccountRows.filter(r => r.dr_cr==='Credit').reduce((s,r)=>s+(r.amount??0),0)
              const hasAmounts = jvAccountRows.some(r => r.amount!=null)
              const balanced = Math.abs(totalDr-totalCr)<0.02

              const xrows = jvCompRows ?? fieldsStep?.fields?.map(f => ({ label: f.field, pb: '—', jv: f.value })) ?? []

              // shared class constants
              const SECTION_STRIP = 'px-4 py-1.5 bg-gray-100 dark:bg-gray-800/80 border-y border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-widest text-gray-500 dark:text-gray-400'
              const pill = (color: 'green'|'blue'|'purple'|'red'|'gray', label: string) => {
                const cls = {
                  green:  'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-700',
                  blue:   'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border-blue-200 dark:border-blue-700',
                  purple: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300 border-purple-200 dark:border-purple-700',
                  red:    'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300 border-red-200 dark:border-red-700',
                  gray:   'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 border-gray-200 dark:border-gray-600',
                }[color]
                return <span className={`inline-flex items-center px-1.5 py-px rounded text-[10px] font-semibold border ${cls}`}>{label}</span>
              }
              const statusColor = (s: string): 'green'|'red'|'gray' =>
                s==='PASS' ? 'green' : s==='EXTRA' || s==='WRONG TYPE' ? 'red' : 'gray'

              const renderCond = (condText: string) =>
                <span className="text-[12px] font-medium text-gray-800 dark:text-gray-200">{condText || 'Always applies'}</span>

              return (
                <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden bg-white dark:bg-gray-900 shadow-sm">

                  {/* 1. Header bar */}
                  <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2 min-w-0">
                      <FileBarChart2 className="size-3.5 shrink-0 text-[#3F51B5] dark:text-[#7986CB]" />
                      <span className="text-[12px] font-mono font-bold text-gray-800 dark:text-gray-100 truncate">{pbRefNo}</span>
                      {!verifying && jvSteps.length > 0 && (passed ? pill('green', '✓ Passed') : pill('red', '✕ Failed'))}
                      {verifying && <Loader2 className="size-3.5 animate-spin text-[#3F51B5] shrink-0" />}
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <button onClick={exportJvPdf} disabled={verifying || jvSteps.length === 0}
                        className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed">
                        <FileText className="size-3" />PDF
                      </button>
                      <button onClick={exportJvReport} disabled={verifying || jvSteps.length === 0}
                        className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed">
                        <Download className="size-3" />.xls
                      </button>
                      <button
                        onClick={() => { setPbListOpen(true); setJvSteps([]); setJvError(''); setPbRefNo(''); setSelectedPB(null); setPbItems([]) }}
                        className="text-[11px] flex items-center gap-1 h-7 px-2 rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 hover:text-[#3F51B5] dark:hover:text-[#7986CB] hover:border-[#3F51B5]/50 dark:hover:border-[#7986CB]/50 transition-colors cursor-pointer">
                        <RefreshCw className="size-3" />Change
                      </button>
                    </div>
                  </div>

                  {/* 2. Summary grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-gray-100 dark:divide-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <div className="px-4 py-3">
                      <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">Supplier</div>
                      <div className="text-[13px] font-medium text-gray-800 dark:text-gray-100 truncate">{selectedPB?.supplier ?? '—'}</div>
                    </div>
                    <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 sm:border-t-0">
                      <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">Amount</div>
                      <div className="text-[13px] font-mono font-medium text-gray-800 dark:text-gray-100 truncate">
                        {selectedPB?.amount
                          ? <>₹{Number(selectedPB.amount).toLocaleString('en-IN',{maximumFractionDigits:0})}{selectedPB.date && <span className="text-gray-400 dark:text-gray-500 font-sans font-normal"> · {selectedPB.date}</span>}</>
                          : <span className="font-sans font-normal">{selectedPB?.date ?? '—'}</span>}
                      </div>
                    </div>
                    <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 sm:border-t-0">
                      <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">Journal Voucher</div>
                      <div className={`text-[13px] font-medium ${foundStep ? (foundStep.ok ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400') : 'text-gray-400 dark:text-gray-500'}`}>
                        {foundStep ? (foundStep.ok ? '✓ Entry found' : '✕ Not found') : verifying ? 'Checking…' : '—'}
                      </div>
                    </div>
                    <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 sm:border-t-0">
                      <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium mb-0.5">Balance Check</div>
                      <div className={`text-[13px] font-medium ${balanceStep ? (balanceStep.ok ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400') : 'text-gray-400 dark:text-gray-500'}`}>
                        {balanceStep
                          ? (balanceStep.ok
                            ? <>✓ Matched{balM && <span className="text-[11px] font-mono font-normal ml-1 text-gray-400 dark:text-gray-500">(DR={balM[1]})</span>}</>
                            : '✕ Unbalanced')
                          : verifying ? 'Checking…' : '—'}
                      </div>
                    </div>
                  </div>

                  {/* errors */}
                  {jvError && !verifying && (
                    <div className="mx-4 my-3 px-3 py-2 rounded bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-[11px] text-red-600 dark:text-red-400">{jvError}</div>
                  )}

                  {/* 3. Field cross-check — real table */}
                  {xrows.length > 0 && (
                    <>
                      <div className={SECTION_STRIP}>Field cross-check</div>
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse text-[12px]">
                          <thead>
                            <tr className="bg-gray-50 dark:bg-gray-800/80">
                              {(['Field','Purchase Booking','Journal Voucher','Match'] as const).map(h => (
                                <th key={h} className={`px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left${h==='Match'?' w-14 text-center':''}`}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {xrows.map((row, ri) => {
                              const match = row.pb!=='—' && row.jv!=='—' && row.pb.trim().toLowerCase()===row.jv.trim().toLowerCase()
                              const unk = row.pb==='—' || row.jv==='—'
                              const fail = !unk && !match
                              if (row.indent) {
                                return (
                                  <tr key={ri} className={fail ? 'bg-red-50 dark:bg-red-900/20' : 'bg-gray-50/60 dark:bg-gray-800/30'}>
                                    <td className={`pl-7 pr-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[11px] ${fail ? 'text-red-600 dark:text-red-400' : 'text-gray-400 dark:text-gray-500'}`}>
                                      <span className="mr-1 opacity-50">·</span>{row.label}
                                    </td>
                                    <td className={`px-3 py-1.5 border border-gray-200 dark:border-gray-700 font-mono text-[11px] ${fail ? 'text-red-600 dark:text-red-400 font-semibold' : 'text-gray-500 dark:text-gray-400'}`}>{row.pb}</td>
                                    <td className={`px-3 py-1.5 border border-gray-200 dark:border-gray-700 font-mono text-[11px] ${fail ? 'text-red-600 dark:text-red-400 font-semibold' : 'text-gray-500 dark:text-gray-400'}`}>{row.jv}</td>
                                    <td className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-center">
                                      {unk ? <span className="text-gray-300 dark:text-gray-600">—</span>
                                        : match ? <CheckCircle2 className="size-3 text-emerald-400 inline" />
                                        : <XCircle className="size-3 text-red-500 inline" />}
                                    </td>
                                  </tr>
                                )
                              }
                              return (
                                <tr key={ri} className={fail ? 'bg-red-50 dark:bg-red-900/20' : 'bg-white dark:bg-gray-900 hover:bg-gray-50/50 dark:hover:bg-gray-800/30'}>
                                  <td className={`px-3 py-2 border border-gray-200 dark:border-gray-700 font-medium ${fail ? 'text-red-700 dark:text-red-300' : 'text-gray-700 dark:text-gray-300'}`}>{row.label||'—'}</td>
                                  <td className={`px-3 py-2 border border-gray-200 dark:border-gray-700 font-mono ${fail ? 'text-red-600 dark:text-red-400 font-semibold' : row.pb==='—'?'text-gray-300 dark:text-gray-600':''}`}>{row.pb}</td>
                                  <td className={`px-3 py-2 border border-gray-200 dark:border-gray-700 font-mono ${fail ? 'text-red-600 dark:text-red-400 font-semibold' : row.jv==='—'?'text-gray-300 dark:text-gray-600':''}`}>{row.jv}</td>
                                  <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-center">
                                    {unk ? <span className="text-gray-300 dark:text-gray-600">—</span>
                                      : match ? <CheckCircle2 className="size-3.5 text-emerald-500 inline" />
                                      : <XCircle className="size-3.5 text-red-500 inline" />}
                                  </td>
                                </tr>
                              )
                            })}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}

                  {/* 4 + 5. Accounting entries — single continuous table */}
                  {(jvAccountRows.length > 0 || accountingDefLoading) && (
                    <>
                      <div className={SECTION_STRIP}>Accounting entries</div>
                      {accountingDefLoading ? (
                        <div className="px-4 py-4 text-[11px] text-gray-400 dark:text-gray-500 italic flex items-center gap-2">
                          <Loader2 className="size-3 animate-spin" />Loading accounting definition…
                        </div>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="w-full border-collapse text-[12px]">
                            <thead>
                              <tr className="bg-gray-50 dark:bg-gray-800/80">
                                <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left w-12">DR/CR</th>
                                <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left">Account</th>
                                <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left w-20">Status</th>
                                <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left">Condition</th>
                                <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-right w-28">Amount</th>
                              </tr>
                            </thead>
                            <tbody>
                              {sortedKeys.map(commodity => {
                                const rows = groups.get(commodity)!
                                const gDr = rows.filter(r=>r.dr_cr==='Debit').reduce((s,r)=>s+(r.amount??0),0)
                                const gCr = rows.filter(r=>r.dr_cr==='Credit').reduce((s,r)=>s+(r.amount??0),0)
                                const hasGrpAmt = rows.some(r=>r.amount!=null)
                                return (
                                  <React.Fragment key={commodity||'__shared__'}>
                                    <tr className="bg-indigo-50 dark:bg-indigo-950/40">
                                      <td colSpan={5} className="px-3 py-1.5 border border-indigo-100 dark:border-indigo-900/60">
                                        <div className="flex items-center justify-between">
                                          <span className="text-[11px] font-semibold text-indigo-700 dark:text-indigo-300 uppercase tracking-wide">
                                            {commodity || 'Shared — all items'}
                                          </span>
                                          <span className="text-[10px] font-mono text-indigo-400 dark:text-indigo-500">{rows.length} {rows.length===1?'entry':'entries'}</span>
                                        </div>
                                      </td>
                                    </tr>
                                    {rows.map((row, ri) => {
                                      const def = defByName.get(normName(row.account_name)+'|'+(row.dr_cr||'').toLowerCase())
                                      const drCrMatch = !!def && def.dr_cr===row.dr_cr
                                      const status = !def?'EXTRA':drCrMatch?'PASS':'WRONG TYPE'
                                      const condText = def?.condition_text||(def?'Always applies':'')
                                      const isDebit = row.dr_cr==='Debit'
                                      return (
                                        <tr key={ri} className="bg-white dark:bg-gray-900 hover:bg-gray-50/50 dark:hover:bg-gray-800/20">
                                          <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-center">
                                            {isDebit ? pill('blue','DR') : pill('purple','CR')}
                                          </td>
                                          <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 font-medium text-gray-800 dark:text-gray-100">{row.account_name}</td>
                                          <td className="px-3 py-2 border border-gray-200 dark:border-gray-700">{pill(statusColor(status), status)}</td>
                                          <td className="px-3 py-2 border border-gray-200 dark:border-gray-700">
                                            {condText ? renderCond(condText) : <span className="text-gray-300 dark:text-gray-600">—</span>}
                                          </td>
                                          <td className={`px-3 py-2 border border-gray-200 dark:border-gray-700 text-right font-mono font-semibold ${isDebit?'text-blue-700 dark:text-blue-300':'text-purple-700 dark:text-purple-300'}`}>
                                            {fmtAmt(row.amount)}
                                          </td>
                                        </tr>
                                      )
                                    })}
                                    {hasGrpAmt && rows.length > 1 && (
                                      <tr className="bg-gray-50 dark:bg-gray-800/50">
                                        <td colSpan={4} className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] text-gray-400 dark:text-gray-500 font-medium">Subtotal</td>
                                        <td className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-right font-mono text-[11px]">
                                          {gDr>0 && <span className="text-blue-600 dark:text-blue-400">DR {fmtAmt(gDr)}</span>}
                                          {gDr>0 && gCr>0 && <span className="text-gray-300 dark:text-gray-600 mx-1">·</span>}
                                          {gCr>0 && <span className="text-purple-600 dark:text-purple-400">CR {fmtAmt(gCr)}</span>}
                                        </td>
                                      </tr>
                                    )}
                                  </React.Fragment>
                                )
                              })}
                            </tbody>
                            {hasAmounts && (
                              <tfoot>
                                <tr className="bg-white dark:bg-gray-900">
                                  <td colSpan={4} className="px-3 py-2.5 border-t-2 border border-gray-300 dark:border-gray-500 font-bold text-[12px] text-gray-700 dark:text-gray-200">Total</td>
                                  <td className="px-3 py-2.5 border-t-2 border border-gray-300 dark:border-gray-500 text-right">
                                    <div className="flex items-center justify-end gap-1.5 font-mono text-[12px] font-semibold">
                                      <span className="text-blue-700 dark:text-blue-300">DR {fmtAmt(totalDr)}</span>
                                      <span className={balanced?'text-emerald-600 dark:text-emerald-400':'text-red-500 dark:text-red-400'}>{balanced?'=':'≠'}</span>
                                      <span className="text-purple-700 dark:text-purple-300">CR {fmtAmt(totalCr)}</span>
                                      {balanced ? <CheckCircle2 className="size-3 text-emerald-500" /> : <XCircle className="size-3 text-red-500" />}
                                    </div>
                                  </td>
                                </tr>
                              </tfoot>
                            )}
                          </table>
                        </div>
                      )}

                      {/* 6. Not-applied rules — collapsible, own bordered table */}
                      {notApplied.length > 0 && (
                        <div className="border-t border-gray-100 dark:border-gray-800">
                          <button
                            onClick={() => setNotAppliedOpen(o => !o)}
                            className="flex items-center gap-1.5 w-full px-4 py-2 text-[11px] text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800/40 transition-colors cursor-pointer"
                          >
                            <ChevronDown className={`size-3.5 transition-transform duration-150 ${notAppliedOpen?'rotate-180':''}`} />
                            {notApplied.length} rule{notApplied.length!==1?'s':''} not applied this transaction
                          </button>
                          {notAppliedOpen && (
                            <div className="overflow-x-auto border-t border-gray-100 dark:border-gray-800">
                              <table className="w-full border-collapse text-[12px]">
                                <thead>
                                  <tr className="bg-gray-50 dark:bg-gray-800/60">
                                    <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left w-12">DR/CR</th>
                                    <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left">Account</th>
                                    <th className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 text-left">Why not applied</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {notApplied.map((def, ri) => (
                                    <tr key={ri} className="bg-gray-50/50 dark:bg-gray-800/20">
                                      <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-center">
                                        {pill('gray', def.dr_cr==='Debit'?'DR':'CR')}
                                      </td>
                                      <td className="px-3 py-2 border border-gray-200 dark:border-gray-700 text-gray-400 dark:text-gray-500">{def.account_name}</td>
                                      <td className="px-3 py-2 border border-gray-200 dark:border-gray-700">
                                        {(def.condition_text || def.has_conditions)
                                          ? renderCond(def.condition_text || 'Conditional — condition not met')
                                          : <span className="text-gray-300 dark:text-gray-600 italic">Always applies</span>}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </div>
              )
            })()}
          </div>

          {/* Bottom bar */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700 shrink-0 flex items-center gap-2">
            {!(erpToken || localToken) ? (
              <Button
                onClick={() => setShowTokenInput(true)}
                variant="outline"
                size="sm"
                className="h-8 text-[12px] gap-1.5 cursor-pointer"
              >
                <Key className="size-3" />
                Set Token
              </Button>
            ) : (
              <button
                onClick={() => { setLocalToken(''); setLocalTenantId(''); setJvSteps([]); setJvError(''); setPbRefNo('') }}
                className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1 hover:text-red-500 dark:hover:text-red-400 transition-colors cursor-pointer"
                title="Clear token"
              >
                <CheckCircle2 className="size-3" />
                Token set
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative flex flex-col h-full min-h-0 gap-4">
      {/* Controls panel */}
      <div className="bg-white dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg flex flex-col min-h-0 flex-1 overflow-hidden">
        {/* Flow selector — pinned to the top of the panel */}
        <div className="grid grid-cols-3 border-b border-gray-300 dark:border-gray-600 shrink-0" data-tour="pc-flow">
          {([
            { id: 'po', label: 'PO → GP → GRN → QC → PB' },
            { id: 'so', label: 'PO → GP → GRN → QC → SO → PB' },
            { id: 'gp', label: 'GP → GRN → QC → PB' },
          ] as const).map((f, i) => (
            <div
              key={f.id}
              className={`relative flex items-center justify-center border-b-2 transition-colors ${
                flow === f.id
                  ? 'bg-white dark:bg-gray-900 border-[#3F51B5] shadow-sm'
                  : 'bg-gray-50 dark:bg-gray-800/50 border-transparent'
              } ${i > 0 ? 'border-l border-gray-300 dark:border-gray-600' : ''}`}
            >
              <button
                type="button"
                onClick={() => {
                  setFlow(f.id)
                  setMultiGatePass(false)
                  setEnabledDocs(new Set(f.id === 'so' ? ['PO', 'GP', 'GRN', 'QC', 'SO'] : f.id === 'gp' ? ['GP', 'GRN', 'QC', 'PB'] : ['PO', 'GP', 'GRN', 'QC', 'PB']))
                }}
                disabled={running}
                className={`flex-1 px-3 pl-2 pr-7 py-2 text-[11px] font-medium transition-colors cursor-pointer disabled:cursor-not-allowed text-center ${
                  flow === f.id
                    ? 'text-[#3F51B5] dark:text-[#7986CB]'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
                }`}
              >
                {f.label}
              </button>
              <button
                type="button"
                title={starredFlow === f.id ? 'Remove default' : 'Set as default flow'}
                onClick={(e) => {
                  e.stopPropagation()
                  const key = userId ? `pc_starred_flow:${userId}` : 'pc_starred_flow'
                  const next = starredFlow === f.id ? null : f.id
                  setStarredFlow(next)
                  if (next) localStorage.setItem(key, next)
                  else localStorage.removeItem(key)
                }}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 p-0.5 rounded transition-colors cursor-pointer"
              >
                <Star
                  className={`size-3 transition-colors ${
                    starredFlow === f.id
                      ? 'fill-amber-400 text-amber-400'
                      : 'text-gray-300 dark:text-gray-600 hover:text-amber-400'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
        <div ref={scrollContainerRef} className="p-4 pb-0 overflow-y-auto flex-1 min-h-0">

        {/* Document selector + toggles — equally spaced row */}
        <div className="border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-100/60 dark:bg-gray-800/50 px-3 py-2 mb-4 flex flex-wrap gap-x-4 gap-y-2 items-start justify-between shadow-md" data-tour="pc-docs">
          <div className="flex flex-col gap-0.5 items-center" title="Click a document to customize the flow">
            <div className="flex items-center gap-1.5 flex-wrap justify-center">
              <span className="text-[12px] text-gray-700 dark:text-gray-300 shrink-0">Create:</span>
              {docOrder.map((doc, idx, arr) => {
                const on = enabledDocs.has(doc)
                const toggle = () => {
                  setEnabledDocs(prev => {
                    const next = new Set(prev)
                    if (on) {
                      // disabling: also disable all that depend on this doc
                      const deps = arr.slice(idx)
                      deps.forEach(d => next.delete(d))
                    } else {
                      // enabling: also enable all prerequisites
                      const prereqs = arr.slice(0, idx + 1)
                      prereqs.forEach(d => next.add(d))
                    }
                    return next
                  })
                }
                return (
                  <React.Fragment key={doc}>
                    <button
                      type="button"
                      onClick={toggle}
                      disabled={running}
                      className={`px-2 py-1 rounded text-[11px] font-semibold border transition-colors cursor-pointer disabled:cursor-not-allowed ${
                        on
                          ? 'bg-[#3F51B5] border-[#3F51B5] text-white'
                          : 'bg-transparent border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400'
                      }`}
                    >
                      {doc}
                    </button>
                    {idx < arr.length - 1 && (
                      <span className={`text-[11px] ${enabledDocs.has(arr[idx + 1]) ? 'text-[#3F51B5]' : 'text-gray-400 dark:text-gray-600'}`}>→</span>
                    )}
                  </React.Fragment>
                )
              })}
            </div>
            <span className="text-[10px] text-gray-600 dark:text-gray-400">Click a document to customize the flow</span>
          </div>

          {flow !== 'gp' && (
          <>

          <div className="flex flex-col gap-0.5 items-center" data-tour="pc-tax">
            <div className="flex items-center gap-1.5 flex-wrap justify-center">
              <span className="text-[12px] text-gray-700 dark:text-gray-300 shrink-0">Tax:</span>
              <div className="flex rounded-md overflow-hidden border border-gray-300 dark:border-gray-600 shadow-sm">
                <button
                  type="button"
                  onClick={() => setRequireTaxRate(true)}
                  disabled={running}
                  className={`px-2.5 py-1 text-[11px] font-semibold transition-colors cursor-pointer disabled:cursor-not-allowed ${
                    requireTaxRate ? 'bg-[#3F51B5] text-white' : 'bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  ON
                </button>
                <button
                  type="button"
                  onClick={() => setRequireTaxRate(false)}
                  disabled={running}
                  className={`px-2.5 py-1 text-[11px] font-semibold border-l border-gray-300 dark:border-gray-600 transition-colors cursor-pointer disabled:cursor-not-allowed ${
                    !requireTaxRate ? 'bg-[#3F51B5] text-white' : 'bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  OFF
                </button>
              </div>
            </div>
            <span className="text-[10px] text-gray-600 dark:text-gray-400">
              {requireTaxRate ? 'Items with a tax rate only' : 'All items (0.0 rate when none)'}
            </span>
          </div>

          {enabledDocs.has('QC') && (
          <div className="flex flex-col gap-0.5 items-center" data-tour="pc-qcdiscount">
            <div className="flex items-center gap-1.5 flex-wrap justify-center">
              <span className="text-[12px] text-gray-700 dark:text-gray-300 shrink-0">QC Discount:</span>
              <div className="flex rounded-md overflow-hidden border border-gray-300 dark:border-gray-600 shadow-sm">
                <button
                  type="button"
                  onClick={() => setQcDiscount(true)}
                  disabled={running}
                  className={`px-2.5 py-1 text-[11px] font-semibold transition-colors cursor-pointer disabled:cursor-not-allowed ${
                    qcDiscount ? 'bg-[#3F51B5] text-white' : 'bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  ON
                </button>
                <button
                  type="button"
                  onClick={() => setQcDiscount(false)}
                  disabled={running}
                  className={`px-2.5 py-1 text-[11px] font-semibold border-l border-gray-300 dark:border-gray-600 transition-colors cursor-pointer disabled:cursor-not-allowed ${
                    !qcDiscount ? 'bg-[#3F51B5] text-white' : 'bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  OFF
                </button>
              </div>
            </div>
            <span className="text-[10px] text-gray-600 dark:text-gray-400">
              {qcDiscount ? 'Random discount on QC lines' : 'No discount filled in QC'}
            </span>
          </div>
          )}

          <div className="flex flex-col gap-0.5 items-center" data-tour="pc-weight-deduction">
            <div className="flex items-center gap-1.5 flex-wrap justify-center">
              <span className="text-[12px] text-gray-700 dark:text-gray-300 shrink-0">Weight Deduction:</span>
              <div className="flex rounded-md overflow-hidden border border-gray-300 dark:border-gray-600 shadow-sm">
                <button
                  type="button"
                  onClick={() => setIsRateWeightDeduction(true)}
                  disabled={running}
                  className={`px-2.5 py-1 text-[11px] font-semibold transition-colors cursor-pointer disabled:cursor-not-allowed ${
                    isRateWeightDeduction ? 'bg-[#3F51B5] text-white' : 'bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  ON
                </button>
                <button
                  type="button"
                  onClick={() => setIsRateWeightDeduction(false)}
                  disabled={running}
                  className={`px-2.5 py-1 text-[11px] font-semibold border-l border-gray-300 dark:border-gray-600 transition-colors cursor-pointer disabled:cursor-not-allowed ${
                    !isRateWeightDeduction ? 'bg-[#3F51B5] text-white' : 'bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  OFF
                </button>
              </div>
            </div>
            <span className="text-[10px] text-gray-600 dark:text-gray-400">
              {isRateWeightDeduction ? 'Weight × Rate deduction' : 'Rate-based % deduction'}
            </span>
          </div>

          <div className="flex flex-col gap-0.5 items-center" data-tour="pc-multigp">
            <div className="flex items-center gap-1.5 flex-wrap justify-center">
              <span className="text-[12px] text-gray-700 dark:text-gray-300 shrink-0">Multi GP:</span>
              <div className="flex rounded-md overflow-hidden border border-gray-300 dark:border-gray-600 shadow-sm">
                <button
                  type="button"
                  onClick={() => {
                    setMultiGatePass(true)
                    setEnabledDocs(new Set(flow === 'so' ? ['PO', 'GP', 'GRN', 'QC', 'SO'] : ['PO', 'GP', 'GRN', 'QC', 'PB']))
                  }}
                  disabled={running}
                  className={`px-2.5 py-1 text-[11px] font-semibold transition-colors cursor-pointer disabled:cursor-not-allowed ${
                    multiGatePass ? 'bg-[#3F51B5] text-white' : 'bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  ON
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMultiGatePass(false)
                    setEnabledDocs(new Set(flow === 'so' ? ['PO', 'GP', 'GRN', 'QC', 'SO'] : ['PO', 'GP', 'GRN', 'QC', 'PB']))
                  }}
                  disabled={running}
                  className={`px-2.5 py-1 text-[11px] font-semibold border-l border-gray-300 dark:border-gray-600 transition-colors cursor-pointer disabled:cursor-not-allowed ${
                    !multiGatePass ? 'bg-[#3F51B5] text-white' : 'bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  OFF
                </button>
              </div>
              {multiGatePass && (
                <div className="flex items-center gap-1">
                  <span className="text-[12px] text-gray-700 dark:text-gray-300 shrink-0">GPs:</span>
                  <Input
                    type="number"
                    min={2}
                    max={10}
                    value={gpCount}
                    onChange={(e) => setGpCount(Math.max(2, Math.min(10, parseInt(e.target.value) || 2)))}
                    className="h-7 w-12 text-[12px] px-1.5"
                    disabled={running}
                  />
                </div>
              )}
            </div>
            <span className="text-[10px] text-gray-600 dark:text-gray-400">
              {multiGatePass
                ? 'Split PO — each GP gets its own GRN, QC & PB'
                : 'One gate pass for the whole PO'}
            </span>
          </div>
          </>
          )}
        </div>

        {dataError && (
          <div className="mb-3 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-[11px] text-red-600 dark:text-red-400 space-y-1">
            <p>{dataError}</p>
            <p className="text-red-500 dark:text-red-400">Try a hard refresh <kbd className="px-1 py-0.5 rounded bg-red-100 dark:bg-red-900/40 font-mono text-[10px]">Ctrl+Shift+R</kbd> and re-enter your token — the ERP session may have expired.</p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Item Category selector */}
          <div className="relative" data-tour="pc-category">
            <Label className="text-[11px] text-gray-700 dark:text-gray-300 mb-1 block">Item Category</Label>
            {loadingData && categories.length === 0 ? (
              <div className="h-9 flex items-center text-[12px] text-gray-600 dark:text-gray-400 gap-1.5">
                <Loader2 className="size-3 animate-spin" />
                Loading...
              </div>
            ) : (
              <button
                ref={categoryBtnRef}
                type="button"
                onClick={() => {
                  if (activeMenu?.type === 'category') { setActiveMenu(null); return }
                  const r = categoryBtnRef.current?.getBoundingClientRect()
                  if (r) setActiveMenu({ type: 'category', pos: { top: r.bottom + 4, left: r.left, width: r.width } })
                }}
                className="w-full px-3 py-2 text-[12px] text-left bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer flex items-center justify-between"
              >
                <span className="truncate">{selectedCategory ? `${selectedCategory.name} (${selectedCategory.item_count})` : 'Select category...'}</span>
                <svg className={`size-3 text-gray-500 transition-transform shrink-0 ${activeMenu?.type === 'category' ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
              </button>
            )}
          </div>

          {/* Supplier selector */}
          <div className="relative" data-tour="pc-supplier">
            <Label className="text-[11px] text-gray-700 dark:text-gray-300 mb-1 block">Supplier</Label>
            {loadingData && suppliers.length === 0 ? (
              <div className="h-9 flex items-center text-[12px] text-gray-600 dark:text-gray-400 gap-1.5">
                <Loader2 className="size-3 animate-spin" />
                Loading...
              </div>
            ) : (
              <>
                <button
                  ref={supplierBtnRef}
                  type="button"
                  onClick={() => {
                    if (activeMenu?.type === 'supplier') { setActiveMenu(null); return }
                    const r = supplierBtnRef.current?.getBoundingClientRect()
                    if (r) setActiveMenu({ type: 'supplier', pos: { top: r.bottom + 4, left: r.left, width: r.width } })
                  }}
                className="h-9 w-full px-3 py-0 text-[12px] text-left bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer flex items-center justify-between"
                >
                  <span className="truncate">{selectedSupplier ? selectedSupplier.name : 'Select supplier...'}</span>
                  <svg className={`size-3 text-gray-500 transition-transform shrink-0 ${activeMenu?.type === 'supplier' ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </button>
              </>
            )}
          </div>
        </div>

        {flow === 'so' && enabledDocs.has('SO') && (
        <div className="mb-4">
          {/* Customer selector — SO header customer; only relevant for the SO flow */}
          <div className="relative max-w-full sm:max-w-xs" data-tour="pc-customer">
            <Label className="text-[11px] text-gray-700 dark:text-gray-300 mb-1 block">Customer (SO)</Label>
            {loadingData && customers.length === 0 ? (
              <div className="h-9 flex items-center text-[12px] text-gray-600 dark:text-gray-400 gap-1.5">
                <Loader2 className="size-3 animate-spin" />
                Loading...
              </div>
            ) : (
              <button
                ref={customerBtnRef}
                type="button"
                onClick={() => {
                  if (activeMenu?.type === 'customer') { setActiveMenu(null); return }
                  const r = customerBtnRef.current?.getBoundingClientRect()
                  if (r) setActiveMenu({ type: 'customer', pos: { top: r.bottom + 4, left: r.left, width: r.width } })
                }}
                className="h-9 w-full px-3 py-0 text-[12px] text-left bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer flex items-center justify-between"
              >
                <span className="truncate">
                  {customer != null
                    ? (customers.find((c) => c.id === customer)?.name ?? `Customer ${customer}`)
                    : customers.length > 0 ? 'Select customer...' : 'No customers found'}
                </span>
                <svg className={`size-3 text-gray-500 transition-transform shrink-0 ${activeMenu?.type === 'customer' ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
              </button>
            )}
            {customers.length === 0 && !loadingData && (
              <p className="text-[10px] text-amber-600 dark:text-amber-400 mt-1">No Customers in ERP — SO will fail. Add a Customer first.</p>
            )}
          </div>
        </div>
        )}

        {/* Chains — own row */}
        <div className="mb-4">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-end gap-2">
            <div className="flex flex-col gap-0.5" data-tour="pc-chains">
              <Label className="text-[10px] text-gray-600 dark:text-gray-400 block">Chains</Label>
              <Input
                type="number"
                min={1}
                max={50}
                value={count}
                onChange={(e) => {
                  const v = Math.max(1, Math.min(50, parseInt(e.target.value) || 1))
                  setCount(v)
                  setChainSuppliers((prev) => {
                    if (prev.length === v) return prev
                    const next = prev.slice(0, v)
                    const ids = suppliers.map((s) => s.id)
                    if (ids.length === 0) {
                      while (next.length < v) next.push(null)
                      return next
                    }
                    if (sameSupplier) {
                      while (next.length < v) next.push(supplier ?? ids[0])
                      return next
                    }
                    const used = new Set(next.filter((x): x is number => x != null))
                    let k = 0
                    for (let i = 0; i < v; i++) {
                      if (next[i] != null) continue
                      let id = ids[k % ids.length]
                      let tries = 0
                      while (used.has(id) && tries < ids.length) { k++; id = ids[k % ids.length]; tries++ }
                      k++; used.add(id); next[i] = id
                    }
                    return next
                  })
                }}
                className="h-9 text-[12px] w-24"
                disabled={running}
              />
            </div>
            <div className="flex flex-col gap-0.5">
              <button
                type="button"
                disabled={running}
                onClick={() => {
                  const next = !sameSupplier
                  setSameSupplier(next)
                  if (next && supplier != null) {
                    setChainSuppliers(Array(count).fill(supplier))
                  } else if (!next && suppliers.length > 0) {
                    const ids = suppliers.map((s) => s.id)
                    setChainSuppliers(Array.from({ length: count }, (_, i) => ids[i % ids.length]))
                  }
                }}
                className={`h-9 px-3 rounded-md text-[11px] font-semibold border transition-colors cursor-pointer disabled:cursor-not-allowed ${
                  sameSupplier
                    ? 'bg-[#3F51B5] border-[#3F51B5] text-white'
                    : 'bg-transparent border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                Same Supplier
              </button>
            </div>
            </div>
            {loadingData && items.length === 0 && (
              <div className="h-9 flex items-center text-[12px] text-gray-600 dark:text-gray-400 gap-1.5">
                <Loader2 className="size-3 animate-spin" />
                Loading...
              </div>
            )}
            {count > 1 && chainSuppliers.map((chainSup, idx) => (
              <div key={idx} className="flex flex-col gap-0.5">
                <Label className="text-[10px] text-gray-600 dark:text-gray-400 block">Chain {idx + 1}</Label>
                <button
                  type="button"
                  ref={(el) => { chainSupBtnRefs.current[idx] = el }}
                  onClick={() => {
                    if (activeMenu?.type === `chainSup:${idx}`) { setActiveMenu(null); return }
                    const r = chainSupBtnRefs.current[idx]?.getBoundingClientRect()
                    if (r) setActiveMenu({ type: `chainSup:${idx}` as never, pos: { top: r.bottom + 4, left: r.left, width: Math.max(r.width, 200) } })
                  }}
                  className="h-9 w-56 px-2.5 py-0 text-[12px] text-left bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer flex items-center justify-between"
                >
                  <span className="truncate">
                    {chainSup != null
                      ? (suppliers.find(s => s.id === chainSup)?.name ?? `Supplier ${chainSup}`)
                      : 'Select supplier...'}
                  </span>
                  <svg className={`size-3 text-gray-500 transition-transform shrink-0 ${activeMenu?.type === `chainSup:${idx}` ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Items per doc — own row */}
        <div className="mb-4">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex flex-col gap-0.5" data-tour="pc-items">
              <Label className="text-[10px] text-gray-600 dark:text-gray-400 block">Items / Doc</Label>
              <Input
                type="number"
                min={1}
                max={catItems.length > 0 ? catItems.length : 20}
                value={numItems}
                onChange={(e) => {
                  const max = catItems.length > 0 ? catItems.length : 20
                  const v = Math.max(1, Math.min(max, parseInt(e.target.value) || 1))
                  setNumItems(v)
                  setItemIds((prev) => {
                    if (prev.length === v) return prev
                    if (prev.length === 0 && catItems.length > 0) {
                      const max = catItems.length
                      return catItems.slice(0, Math.min(v, max)).map(i => i.id)
                    }
                    if (prev.length < v) {
                      const used = new Set(prev)
                      const available = catItems.filter(i => !used.has(i.id)).map(i => i.id)
                      if (available.length === 0) {
                        // No loaded items yet (e.g. token not set) — keep rows empty.
                        return prev
                      }
                      const fill: number[] = []
                      for (let idx = 0; fill.length < v - prev.length; idx++) {
                        fill.push(available[idx % available.length] ?? prev[prev.length - 1] ?? catItems[0].id)
                      }
                      return [...prev, ...fill]
                    }
                    return prev.slice(0, v)
                  })
                }}
                className="h-9 text-[12px] w-24"
                disabled={running}
              />
            </div>
            {catItems.length > 1 && (
              <button
                type="button"
                onClick={() => {
                  setNumItems(catItems.length)
                  setItemIds(catItems.map(i => i.id))
                }}
                className="mt-4 self-start text-[10px] text-[#3F51B5] dark:text-[#7986CB] hover:underline cursor-pointer"
              >
                All {catItems.length}
              </button>
            )}
            {numItems === 1 && (
              <div className="flex flex-col gap-0.5">
                <Label className="text-[10px] text-gray-600 dark:text-gray-400 block">Item</Label>
                <button
                  ref={itemBtnRef}
                  type="button"
                  onClick={() => {
                    if (activeMenu?.type === 'item') { setActiveMenu(null); return }
                    const r = itemBtnRef.current?.getBoundingClientRect()
                    if (r) setActiveMenu({ type: 'item', pos: { top: r.bottom + 4, left: r.left, width: r.width } })
                  }}
                  className="h-9 w-full px-3 py-0 text-[12px] text-left bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer flex items-center justify-between"
                >
                  <span className="truncate">{catItems.find(i => i.id === itemIds[0])?.name ?? 'Select item...'}</span>
                  <svg className={`size-3 text-gray-500 transition-transform shrink-0 ${activeMenu?.type === 'item' ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </button>
              </div>
            )}
            {numItems > 1 && Array.from({ length: numItems }).map((_, idx) => (
              <div key={idx} className="flex flex-col gap-0.5">
                <Label className="text-[10px] text-gray-600 dark:text-gray-400 block">Item {idx + 1}</Label>
                <button
                  type="button"
                  ref={(el) => { rowBtnRefs.current[idx] = el }}
                  onClick={() => {
                    if (activeMenu?.type === idx) { setActiveMenu(null); return }
                    const r = rowBtnRefs.current[idx]?.getBoundingClientRect()
                    if (r) setActiveMenu({ type: idx, pos: { top: r.bottom + 4, left: r.left, width: Math.max(r.width, 200) } })
                  }}
                  className="h-9 w-56 px-2.5 py-0 text-[12px] text-left bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer flex items-center justify-between"
                >
                  <span className="truncate">{catItems.find(i => i.id === itemIds[idx])?.name ?? 'Select...'}</span>
                  <svg className={`size-3 text-gray-500 transition-transform shrink-0 ${activeMenu?.type === idx ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Per-chain supplier selection — only when running multiple chains */}
        {requireTaxRate && catItems.length === 0 && items.length > 0 && (
          <div className="mb-3 p-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded text-[11px] text-amber-600 dark:text-amber-400">
            No items in this category have a tax rate. Toggle Tax Rate OFF to list all items.
          </div>
        )}

        {/* Inline token input */}
        {showTokenInput && (
          <div ref={tokenSectionRef} className="mb-3 p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
            <Label className="text-[11px] text-orange-600 dark:text-orange-400 mb-1.5 block font-medium">ERP Credentials</Label>
            <div className="flex items-center gap-2 mb-2">
              <Input
                type="password"
                value={localToken}
                onChange={(e) => setLocalToken(e.target.value)}
                placeholder="Paste your Bearer token here..."
                className={`h-9 text-[12px] flex-1 ${
                  localToken && (localToken.startsWith('Bearer ') ? localToken.slice(7) : localToken).startsWith('eyJ') && localToken.split('.').length === 3 && localToken.length > 100
                    ? 'border-green-400'
                    : localToken ? 'border-red-400' : ''
                }`}
              />
            </div>
            {/* Token validation warning */}
            {(() => {
              if (!localToken) return null
              const t = localToken.startsWith('Bearer ') ? localToken.slice(7) : localToken
              const isValid = t.startsWith('eyJ') && t.split('.').length === 3 && t.length > 100
              if (isValid) return (
                <p className="text-[11px] text-green-600 dark:text-green-400 flex items-center gap-1 mb-2">
                  <span className="inline-block size-2 rounded-full bg-green-500" />
                  Token looks valid
                </p>
              )
              return (
                <div ref={tokenErrorRef} className="mb-2 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-2.5 space-y-1.5">
                  <div className="flex items-center gap-1.5">
                    <AlertTriangle className="size-3 text-red-500 shrink-0" />
                    <span className="text-[11px] font-semibold text-red-600 dark:text-red-400">
                      {!t.startsWith('eyJ') ? 'Token must start with eyJ…' : 'Token format looks incorrect'}
                    </span>
                  </div>
                  <p className="text-[11px] text-red-500 dark:text-red-400">
                    Copy from DevTools → Network → any request → Authorization header. Remove the "Bearer " prefix.
                  </p>
                  <div className="rounded bg-gray-900 p-2 space-y-1">
                    <p className="text-[10px] text-gray-400 uppercase tracking-wider">Should look like</p>
                    <p className="text-[10px] text-yellow-300 break-all leading-relaxed">eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.<span className="text-blue-300">eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiw…</span>.<span className="text-pink-300">SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV</span></p>
                    <p className="text-[10px] text-gray-500">3 dot-separated parts · starts with eyJ · 200+ chars</p>
                  </div>
                </div>
              )
            })()}

            <div className="flex flex-wrap gap-1.5 mb-2">
              {[
                { id: '795', name: 'Jalpan Builders' },
                { id: '666', name: 'Jay Kisan Ltd' },
                { id: '686', name: 'Agristack Company' },
                { id: '751', name: 'Tech Neo' },
              ].map(t => (
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
            <div className="flex items-center gap-2">
              <Input
                type="text"
                value={localTenantId}
                onChange={(e) => setLocalTenantId(e.target.value)}
                placeholder="Tenant ID (e.g. 708, 711)"
                className="h-9 text-[12px] w-48"
              />
              <Button
                onClick={handleDone}
                variant="ghost"
                size="sm"
                className="h-9 text-[12px] cursor-pointer"
              >
                Done
              </Button>
            </div>
            <p className="text-[11px] text-orange-500 dark:text-orange-400 mt-1.5">Credentials stay in your browser session. Clear below to reset.</p>
          </div>
        )}
        </div>{/* end scrollable area */}

        {/* Sticky bottom bar */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 shrink-0 flex flex-col gap-2">
          {missingCqpItems.length > 0 && !running && (
            <div className="flex items-center gap-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-300 dark:border-amber-700 rounded-lg px-3 py-2">
              <AlertTriangle className="size-4 text-amber-500 dark:text-amber-400 shrink-0" />
              <span className="text-[12px] text-amber-700 dark:text-amber-300 flex-1">
                {missingCqpItems.length} item{missingCqpItems.length !== 1 ? 's' : ''} in this category have no QC parameters — the QC step will fail without them.
              </span>
              <Button
                onClick={handleCqpFill}
                disabled={fillingCqp || !(erpToken || localToken)}
                size="sm"
                className="h-7 text-[11px] gap-1 cursor-pointer bg-amber-500 hover:bg-amber-600 text-white"
              >
                {fillingCqp ? <Loader2 className="size-3 animate-spin" /> : <Wand2 className="size-3" />}
                {fillingCqp ? 'Filling...' : 'Auto-fill now'}
              </Button>
            </div>
          )}
          {cqpFillLog && (
            <p className="text-[11px] text-gray-500 dark:text-gray-400">{cqpFillLog}</p>
          )}
          <div className="flex items-center gap-2">
          {!running ? (
            <Button
              onClick={handleStart}
              disabled={running || supplier === null || itemIds.length === 0 || loadingData}
              className="h-8 text-[12px] gap-1.5 cursor-pointer"
              data-tour="pc-run"
            >
              <Play className="size-3.5" />
              Run {count > 1 ? `${count}×` : ''} {activeDocs.join(' → ')}
            </Button>
          ) : (
            <Button
              onClick={handleStop}
              variant="destructive"
              className="h-8 text-[12px] gap-1.5 cursor-pointer"
            >
              <XCircle className="size-3.5" />
              Stop
            </Button>
          )}
          {!(erpToken || localToken) && (
            <Button
              onClick={() => setShowTokenInput(true)}
              variant="outline"
              size="sm"
              className="h-8 text-[12px] gap-1.5 cursor-pointer"
              data-tour="pc-token"
            >
              <Key className="size-3" />
              Set Token
            </Button>
          )}
          {(erpToken || localToken) && (
            <button
              onClick={() => {
                setLocalToken(''); setLocalTenantId('')
                setSuppliers([]); setItems([]); setCategories([])
                setSelectedCategoryId(null); setSupplier(null); setItemIds([])
                setCount(1); setChainSuppliers([]); setSameSupplier(false)
                setNumItems(2); setCustomer(null); setCustomers([])
                setLogs([]); setCreated(0); setFailed(0); setRunSummary(null); setShowLogs(false)
                setCqpItemIds(null); setCqpFillLog('')
                fetchedRef.current = false
                onClearToken()
              }}
              className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1 hover:text-red-500 dark:hover:text-red-400 transition-colors cursor-pointer"
              title="Clear token"
            >
              <CheckCircle2 className="size-3" />
              Token set
            </button>
          )}
          {running && (
            <span className="text-[11px] text-[#3F51B5] dark:text-[#7986CB] flex items-center gap-1 animate-pulse">
              <Loader2 className="size-3 animate-spin" />
              Running... {elapsed}s
            </span>
          )}
          <button
            onClick={() => setShowLogs(v => !v)}
            className={`ml-auto text-[11px] px-2.5 py-1 rounded-md border transition-colors cursor-pointer ${showLogs ? 'bg-[#3F51B5]/10 border-[#3F51B5]/40 text-[#3F51B5] dark:text-[#7986CB]' : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'}`}
            title="Toggle console popup"
            data-tour="pc-console"
          >
            Console
            {logs.length > 0 && <span className="ml-1 text-gray-500 dark:text-gray-400">({logs.length})</span>}
          </button>
          </div>
        </div>
      </div>

      {/* Floating live log panel — appears on run start, dismissed with results popup */}
      {showLogs && (
        <div className="absolute bottom-4 right-4 z-40 flex flex-col w-[300px] h-[220px] bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shrink-0">
            <div className="flex items-center gap-2">
              {running
                ? <span className="size-2 rounded-full bg-[#3F51B5] animate-pulse shrink-0" />
                : <span className="size-2 rounded-full bg-emerald-500 shrink-0" />}
              <span className="text-[11px] font-semibold text-gray-700 dark:text-gray-300">
                {running ? 'Running…' : 'Complete'}
              </span>
              {created + failed > 0 && (
                <span className="text-[10px] text-gray-500 dark:text-gray-400">
                  · <span className="text-emerald-600 dark:text-emerald-400">{created} ✓</span>
                  {failed > 0 && <span className="text-red-500 dark:text-red-400 ml-1">{failed} ✕</span>}
                </span>
              )}
            </div>
            <button
              onClick={() => setShowLogs(false)}
              className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors cursor-pointer"
            >
              <X className="size-3.5" />
            </button>
          </div>
          {/* Log body */}
          <ScrollArea className="flex-1 min-h-0">
            <div className="p-3 font-mono text-[11px] leading-relaxed space-y-1">
              {logs.length === 0 && running && (
                <p className="text-[#3F51B5] dark:text-[#7986CB] animate-pulse">Starting...</p>
              )}
              {logs.map((log, i) => (
                <div key={i}>{renderLogLine(log)}</div>
              ))}
              {running && <div className="text-[#3F51B5] dark:text-[#7986CB] animate-pulse mt-1">▌</div>}
              <div ref={logsEndRef} />
            </div>
          </ScrollArea>
        </div>
      )}

      {/* Floating dropdown menu via portal */}
      {activeMenu && typeof document !== 'undefined' && createPortal(
        <>
          <div className="fixed inset-0 z-50" onClick={() => { setActiveMenu(null); setDropdownSearch('') }} />
          <div
            className="fixed z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg"
            style={dropdownPos ?? { top: activeMenu.pos.top, left: activeMenu.pos.left, width: activeMenu.pos.width, maxHeight: 192 }}
          >
            <div className="px-2 py-1.5 border-b border-gray-200 dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 z-10">
              <div className="flex items-center gap-1.5 rounded bg-gray-100 dark:bg-gray-700/50 px-2 py-1">
                <Search className="size-3.5 text-gray-400" />
                <input
                  autoFocus
                  value={dropdownSearch}
                  onChange={(e) => setDropdownSearch(e.target.value)}
                  placeholder="Search…"
                  className="flex-1 bg-transparent outline-none text-[12px] text-gray-700 dark:text-gray-200 placeholder:text-gray-400"
                />
              </div>
            </div>
            <div className="overflow-y-auto" style={{ maxHeight: (dropdownPos?.maxHeight ?? 192) - 36 }}>
              {(() => {
                const list = activeMenu.type === 'supplier' || typeof activeMenu.type === 'string' && activeMenu.type.startsWith('chainSup:')
                  ? suppliers
                  : activeMenu.type === 'customer'
                    ? customers
                    : activeMenu.type === 'category'
                      ? categories
                      : catItems
                const q = dropdownSearch.trim().toLowerCase()
                const filtered = q ? list.filter((i) => i.name.toLowerCase().includes(q)) : list
                return filtered.length === 0 ? (
                  <div className="px-3 py-2 text-[12px] text-gray-600 dark:text-gray-400">No results found</div>
                ) : (
                  filtered.map((i) => {
                  const mType = activeMenu.type
                  const isChainSup = typeof mType === 'string' && mType.startsWith('chainSup:')
                  const chainIdx = isChainSup ? parseInt((mType as string).split(':')[1]) : -1
                  const selected = isChainSup
                    ? i.id === chainSuppliers[chainIdx]
                    : activeMenu.type === 'supplier'
                      ? i.id === supplier
                      : activeMenu.type === 'customer'
                        ? i.id === customer
                        : activeMenu.type === 'category'
                          ? i.id === selectedCategoryId
                          : activeMenu.type === 'item'
                            ? i.id === itemIds[0]
                            : i.id === itemIds[activeMenu.type as number]
                  return (
                    <button
                      key={i.id}
                      type="button"
                      onClick={() => {
                        if (isChainSup) {
                          setChainSuppliers((prev) => { const next = [...prev]; next[chainIdx] = i.id; return next })
                        } else if (activeMenu.type === 'supplier') {
                          setSupplier(i.id)
                        } else if (activeMenu.type === 'customer') {
                          setCustomer(i.id)
                        } else if (activeMenu.type === 'category') {
                          handleCategorySelect(i.id)
                          return
                        } else if (activeMenu.type === 'item') {
                          setItemIds([i.id])
                        } else {
                          setItemIds((prev) => { const next = [...prev]; next[activeMenu.type as number] = i.id; return next })
                        }
                        setActiveMenu(null)
                        setDropdownSearch('')
                      }}
                      className={`w-full px-3 py-1.5 text-[12px] text-left hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer ${selected ? 'bg-[#3F51B5]/10 dark:bg-[#3F51B5]/20 text-[#3F51B5] dark:text-[#7986CB] font-medium' : 'text-gray-700 dark:text-gray-200'}`}
                    >
                      {activeMenu.type === 'category' && 'item_count' in i ? `${i.name} (${i.item_count})` : i.name}
                    </button>
                  )
                })
              )
            })()}
            </div>
          </div>
        </>,
        document.body
      )}

      {/* Run completion popup */}
      {runSummary && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 dark:bg-black/60">
          <div className="flex flex-col w-[90vw] max-w-sm bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-hidden">
            <div className={`px-5 py-4 border-b border-gray-200 dark:border-gray-600/40 flex items-center gap-3 ${runSummary.failed > 0 ? 'bg-red-50 dark:bg-red-900/15' : 'bg-green-50 dark:bg-green-900/15'}`}>
              <div className={`size-10 rounded-full flex items-center justify-center shrink-0 ${runSummary.failed > 0 ? 'bg-red-100 dark:bg-red-900/30' : 'bg-green-100 dark:bg-green-900/30'}`}>
                {runSummary.failed > 0
                  ? <XCircle className="size-5 text-red-600 dark:text-red-400" />
                  : <CheckCircle2 className="size-5 text-green-600 dark:text-green-400" />}
              </div>
              <div className="min-w-0">
                <h3 className={`text-[15px] font-semibold ${runSummary.failed > 0 ? 'text-red-800 dark:text-red-300' : 'text-green-800 dark:text-green-300'}`}>
                  {runSummary.failed > 0 ? 'Run Finished with Errors' : 'Run Complete'}
                </h3>
                <p className="text-[12px] text-gray-500 dark:text-gray-400 truncate">
                  {runSummary.created} of {runSummary.total} chain{runSummary.total !== 1 ? 's' : ''} created · {runSummary.elapsed}s
                </p>
              </div>
            </div>
            <div className="grid grid-cols-3 border-b border-gray-200 dark:border-gray-600/40">
              <div className="px-4 py-3 text-center border-r border-gray-200 dark:border-gray-600/40">
                <div className="text-[11px] text-gray-500 dark:text-gray-400">Created</div>
                <div className="text-[18px] font-bold text-green-600 dark:text-green-400">{runSummary.created}</div>
              </div>
              <div className="px-4 py-3 text-center border-r border-gray-200 dark:border-gray-600/40">
                <div className="text-[11px] text-gray-500 dark:text-gray-400">Failed</div>
                <div className={`text-[18px] font-bold ${runSummary.failed > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-400'}`}>{runSummary.failed}</div>
              </div>
              <div className="px-4 py-3 text-center">
                <div className="text-[11px] text-gray-500 dark:text-gray-400">Total</div>
                <div className="text-[18px] font-bold text-gray-700 dark:text-gray-200">{runSummary.total}</div>
              </div>
            </div>
            <div className="flex items-center justify-end gap-2 px-4 py-3">
              <Button
                onClick={() => { setRunSummary(null); setShowLogs(false) }}
                size="sm"
                className="h-8 text-[12px] gap-1.5 cursor-pointer bg-[#2D3FC7] hover:bg-[#3F51B5] text-white"
              >
                <CheckCircle2 className="size-3.5" />
                Done
              </Button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}