'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { CheckCircle2, XCircle, Play, Key, RefreshCw, Loader2, X, AlertTriangle, Wand2, Search, Star } from 'lucide-react'
import Spinner from '@/components/ui/Spinner'
import LoadingCard from '@/components/ui/LoadingCard'
import { startPurchaseChain, fetchMasterData, fetchItemCategories, fetchItemsWithCqp, fillCqpItems, type SSEEvent, type MasterDataItem, type ItemCategory } from '@/lib/api'
import { notifySuccess } from '@/lib/notify'
import { useErpToken } from '@/hooks/useErpToken'

interface Props {
  erpToken: string
  erpTenantId: string
  onNeedsToken: () => void
  onClearToken: () => void
  userId?: string
}

function formatTime(d: Date): string {
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
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

export function PurchaseChainSection({ erpToken, erpTenantId, onNeedsToken, onClearToken, userId }: Props) {
  const { token: _erpToken, tenantId: _erpTenantId, localToken, setLocalToken, localTenantId, setLocalTenantId, handleAuthError } = useErpToken(erpToken, erpTenantId)
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
  const [loadingSteps, setLoadingSteps] = useState<{ label: string; done: boolean }[]>([])
  const [dataError, setDataError] = useState('')
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
    const token = _erpToken
    const tenant = _erpTenantId
    if (!token || !tenant) return

    setLoadingData(true)
    setDataError('')
    const steps = [
      { label: 'Fetching suppliers', done: false },
      { label: 'Fetching items', done: false },
      { label: 'Fetching categories', done: false },
      { label: 'Fetching quality params', done: false },
    ]
    setLoadingSteps([...steps])
    const tick = (i: number) => setLoadingSteps(s => s.map((x, idx) => idx === i ? { ...x, done: true } : x))
    const fetchWithRetry = async <T,>(label: string, fn: () => Promise<T>): Promise<T> => {
      try { return await fn() } catch (e) {
        const msg = e instanceof Error ? e.message : String(e)
        if (msg.includes('502') || msg.includes('503') || msg.includes('504')) {
          await new Promise(r => setTimeout(r, 2000))
          try { return await fn() } catch (e2) {
            throw new Error(`${label}: ${e2 instanceof Error ? e2.message : e2}`)
          }
        }
        throw new Error(`${label}: ${msg}`)
      }
    }
    try {
      const [supRes, itemRes, catRes, cqpRes] = await Promise.all([
        fetchWithRetry('Supplier', () => fetchMasterData('Supplier', token, tenant)).then(r => { tick(0); return r }),
        fetchWithRetry('Item Master', () => fetchMasterData('Item Master', token, tenant)).then(r => { tick(1); return r }),
        fetchWithRetry('Categories', () => fetchItemCategories(token, tenant)).then(r => { tick(2); return r }),
        fetchWithRetry('Quality Params', () => fetchItemsWithCqp(token, tenant)).then(r => { tick(3); return r }),
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
      if (!handleAuthError(err)) setDataError(err instanceof Error ? err.message : 'Failed to load master data')
    } finally {
      setLoadingData(false)
      setLoadingSteps([])
    }
  }, [_erpToken, _erpTenantId, requireTaxRate, flow, handleAuthError])

  const handleDone = useCallback(() => {
    setShowTokenInput(false)
    if (_erpToken && _erpTenantId) {
      loadMasterData()
    }
  }, [_erpToken, _erpTenantId, loadMasterData])

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
    const token = _erpToken
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
      _erpTenantId || '681',
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
      false,
    )
  }, [count, supplier, numItems, itemIds, _erpToken, _erpTenantId, activeDocs, selectedCategoryId, requireTaxRate, flow, multiGatePass, gpCount, chainSuppliers, qcDiscount, customer, enabledDocs, isRateWeightDeduction])

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
    const token = _erpToken
    const tenant = _erpTenantId
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
  }, [_erpToken, _erpTenantId, missingCqpItems])

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

  // Stable ref — always points to latest callback so effects don't go stale
  const loadMasterDataRef = useRef(loadMasterData)
  useEffect(() => { loadMasterDataRef.current = loadMasterData }, [loadMasterData])

  const hasToken = !!_erpToken && !!_erpTenantId

  // No auto-load on mount — data fetches only when the user explicitly clicks
  // "Done" in the token panel or the Refresh button.


  return (
    <div className="relative flex flex-col h-full min-h-0 gap-4">
      {loadingData && loadingSteps.length > 0 && (
        <LoadingCard message="LOADING" steps={loadingSteps} />
      )}
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
                disabled={fillingCqp || !_erpToken}
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
          {!_erpToken && (
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
          {_erpToken && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => { fetchedRef.current = false; loadMasterData() }}
                disabled={loadingData}
                className="text-[11px] text-[#3F51B5] dark:text-[#7986CB] flex items-center gap-1 hover:underline cursor-pointer disabled:opacity-50"
                title="Re-fetch suppliers, items and categories"
              >
                <RefreshCw className={`size-3 ${loadingData ? 'animate-spin' : ''}`} />
                Refresh
              </button>
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
            </div>
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