'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Loader2, Package, CheckCircle2, XCircle, Play, Key, RefreshCw, RotateCcw } from 'lucide-react'
import { startPurchaseChain, fetchMasterData, type SSEEvent, type MasterDataItem } from '@/lib/api'

interface Props {
  erpToken: string
  erpTenantId: string
  onNeedsToken: () => void
  onClearToken: () => void
}

function formatTime(d: Date): string {
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

export function PurchaseChainSection({ erpToken, erpTenantId, onNeedsToken, onClearToken }: Props) {
  const [count, setCount] = useState(1)
  const [enabledDocs, setEnabledDocs] = useState<Set<string>>(new Set(['PO', 'GP', 'GRN', 'QC']))
  const [supplier, setSupplier] = useState<number | null>(null)
  const [numItems, setNumItems] = useState(2)
  const [itemIds, setItemIds] = useState<number[]>([])
  const [running, setRunning] = useState(false)
  const [logs, setLogs] = useState<{ text: string; ts: Date; isErr: boolean; isDone: boolean }[]>([])
  const [created, setCreated] = useState(0)
  const [failed, setFailed] = useState(0)
  const [suppliers, setSuppliers] = useState<MasterDataItem[]>([])
  const [items, setItems] = useState<MasterDataItem[]>([])
  const [loadingData, setLoadingData] = useState(false)
  const [dataError, setDataError] = useState('')
  const [localToken, setLocalToken] = useState('')
  const [localTenantId, setLocalTenantId] = useState('')
  const [showTokenInput, setShowTokenInput] = useState(false)
  const [activeMenu, setActiveMenu] = useState<{type: 'supplier' | 'item' | number; pos: {top: number; left: number; width: number}} | null>(null)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const tokenSectionRef = useRef<HTMLDivElement>(null)
  const startTimeRef = useRef<number>(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const fetchedRef = useRef(false)
  const supplierBtnRef = useRef<HTMLButtonElement>(null)
  const itemBtnRef = useRef<HTMLButtonElement>(null)
  const rowBtnRefs = useRef<(HTMLButtonElement | null)[]>([])

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

  // Fetch suppliers and items when credentials are available
  const loadMasterData = useCallback(async () => {
    const token = erpToken || localToken
    const tenant = localTenantId || erpTenantId
    if (!token || !tenant) return

    setLoadingData(true)
    setDataError('')
    try {
      const [supRes, itemRes] = await Promise.all([
        fetchMasterData('Supplier', token, tenant),
        fetchMasterData('Item Master', token, tenant),
      ])
      setSuppliers(supRes)
      setItems(itemRes)
      if (supRes.length > 0 && supplier === null) setSupplier(supRes[0].id)
      if (itemRes.length > 0 && itemIds.length === 0) {
        setItemIds(itemRes.slice(0, numItems).map(i => i.id))
      }
      fetchedRef.current = true
    } catch (err) {
      setDataError(err instanceof Error ? err.message : 'Failed to load master data')
    } finally {
      setLoadingData(false)
    }
  }, [erpToken, localToken, localTenantId, erpTenantId])

  const handleDone = useCallback(() => {
    setShowTokenInput(false)
    const token = erpToken || localToken
    const tenant = localTenantId || erpTenantId
    if (token && tenant) {
      loadMasterData()
    }
  }, [erpToken, localToken, localTenantId, erpTenantId, loadMasterData])

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
        }
      },
      () => {
        setRunning(false)
      },
      (err: Error) => {
        setLogs((prev) => [...prev, { text: `Error: ${err.message}`, ts: new Date(), isErr: true, isDone: false }])
        setRunning(false)
      },
      Array.from(enabledDocs),
    )
  }, [count, supplier, numItems, itemIds, erpToken, localToken, localTenantId, erpTenantId, enabledDocs])

  const handleStop = useCallback(() => {
    setRunning(false)
    setLogs((prev) => [...prev, { text: 'Stopped by user', ts: new Date(), isErr: true, isDone: false }])
  }, [])

  const selectedSupplier = suppliers.find((s) => s.id === supplier)

  return (
    <div className="flex flex-col h-full min-h-0 gap-4">
      {/* Controls panel */}
      <div className="bg-white dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg flex flex-col min-h-0 max-h-[80%] shrink-0">
        <div className="p-4 pb-0 overflow-y-auto flex-1 min-h-0">
          <div className="flex items-center gap-2 mb-4">
          <Package className="size-4 text-[#3F51B5]" />
          <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">Purchase Chain</h3>
          <span className="text-[11px] text-gray-400 dark:text-gray-500">One Click Chain</span>
          {(erpToken || localToken) && (
            <button
              onClick={loadMasterData}
              disabled={loadingData}
              className="ml-auto text-[11px] text-[#3F51B5] dark:text-[#7986CB] hover:text-[#3949AB] dark:hover:text-[#9FA8DA] flex items-center gap-1 transition-colors cursor-pointer"
              title="Refresh data from ERP"
            >
              <RotateCcw className={`size-3 ${loadingData ? 'animate-spin' : ''}`} />
              {loadingData ? 'Loading...' : 'Refresh'}
            </button>
          )}
        </div>

        {/* Document selector */}
        <div className="flex items-center gap-2 mb-4">
          <span className="text-[11px] text-gray-500 dark:text-gray-400 shrink-0">Create:</span>
          {(['PO', 'GP', 'GRN', 'QC'] as const).map((doc, idx, arr) => {
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
                  className={`px-3 py-1 rounded-full text-[11px] font-medium border transition-colors cursor-pointer disabled:cursor-not-allowed ${
                    on
                      ? 'bg-[#3F51B5] border-[#3F51B5] text-white'
                      : 'bg-transparent border-gray-300 dark:border-gray-600 text-gray-400 dark:text-gray-500'
                  }`}
                >
                  {doc}
                </button>
                {idx < arr.length - 1 && (
                  <span className={`text-[11px] ${enabledDocs.has(arr[idx + 1]) ? 'text-[#3F51B5]' : 'text-gray-300 dark:text-gray-600'}`}>→</span>
                )}
              </React.Fragment>
            )
          })}
        </div>

        {dataError && (
          <div className="mb-3 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-[11px] text-red-600 dark:text-red-400">
            {dataError}
          </div>
        )}

        <div className="grid grid-cols-4 gap-4 mb-4">
          {/* Supplier selector */}
          <div className="relative">
            <Label className="text-[11px] text-gray-500 dark:text-gray-400 mb-1 block">Supplier</Label>
            {loadingData && suppliers.length === 0 ? (
              <div className="h-9 flex items-center text-[12px] text-gray-400 dark:text-gray-500 gap-1.5">
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
                  className="w-full px-3 py-2 text-[12px] text-left bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer flex items-center justify-between"
                >
                  <span className="truncate">{selectedSupplier ? selectedSupplier.name : 'Select supplier...'}</span>
                  <svg className={`size-3 text-gray-400 transition-transform shrink-0 ${activeMenu?.type === 'supplier' ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </button>
              </>
            )}
          </div>

          {/* Item selector — per-row when numItems > 1 */}
          <div className={`relative ${numItems > 1 ? 'col-span-1' : ''}`}>
            <Label className="text-[11px] text-gray-500 dark:text-gray-400 mb-1 block">
              Item{numItems > 1 ? ' (each row)' : ''}
            </Label>
            {loadingData && items.length === 0 ? (
              <div className="h-9 flex items-center text-[12px] text-gray-400 dark:text-gray-500 gap-1.5">
                <Loader2 className="size-3 animate-spin" />
                Loading...
              </div>
            ) : numItems === 1 ? (
              /* Single dropdown */
              <>
                <button
                  ref={itemBtnRef}
                  type="button"
                  onClick={() => {
                    if (activeMenu?.type === 'item') { setActiveMenu(null); return }
                    const r = itemBtnRef.current?.getBoundingClientRect()
                    if (r) setActiveMenu({ type: 'item', pos: { top: r.bottom + 4, left: r.left, width: r.width } })
                  }}
                  className="w-full px-3 py-2 text-[12px] text-left bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer flex items-center justify-between"
                >
                  <span className="truncate">{items.find(i => i.id === itemIds[0])?.name ?? 'Select item...'}</span>
                  <svg className={`size-3 text-gray-400 transition-transform shrink-0 ${activeMenu?.type === 'item' ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </button>
              </>
            ) : null}
          </div>

          {/* Number of chains */}
          <div>
            <Label className="text-[11px] text-gray-500 dark:text-gray-400 mb-1 block">Chains</Label>
            <Input
              type="number"
              min={1}
              max={50}
              value={count}
              onChange={(e) => setCount(Math.max(1, Math.min(50, parseInt(e.target.value) || 1)))}
              className="h-9 text-[12px]"
              disabled={running}
            />
          </div>

          {/* Items per chain */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <Label className="text-[11px] text-gray-500 dark:text-gray-400">Items / Doc</Label>
              {items.length > 1 && (
                <button
                  type="button"
                  onClick={() => {
                    setNumItems(items.length)
                    setItemIds(items.map(i => i.id))
                  }}
                  className="text-[10px] text-[#3F51B5] dark:text-[#7986CB] hover:underline cursor-pointer"
                >
                  All {items.length}
                </button>
              )}
            </div>
            <Input
              type="number"
              min={1}
              max={items.length > 0 ? items.length : 20}
              value={numItems}
              onChange={(e) => {
                const max = items.length > 0 ? items.length : 20
                const v = Math.max(1, Math.min(max, parseInt(e.target.value) || 1))
                setNumItems(v)
                setItemIds((prev) => {
                  if (prev.length === v) return prev
                  if (prev.length === 0 && items.length > 0) {
                    const max = items.length
                    return items.slice(0, Math.min(v, max)).map(i => i.id)
                  }
                  if (prev.length < v) {
                    const used = new Set(prev)
                    const available = items.filter(i => !used.has(i.id)).map(i => i.id)
                    const fill = []
                    for (let idx = 0; fill.length < v - prev.length; idx++) {
                      fill.push(available[idx % available.length] ?? prev[prev.length - 1] ?? items[0].id)
                    }
                    return [...prev, ...fill]
                  }
                  return prev.slice(0, v)
                })
              }}
              className="h-9 text-[12px]"
              disabled={running}
            />
          </div>
        </div>

        {numItems > 1 && items.length > 0 && (
          <div className="mb-4">
            <Label className="text-[11px] text-gray-500 dark:text-gray-400 mb-1.5 block">Items per row</Label>
            <div className={`grid gap-2 ${numItems > 8 ? 'grid-cols-2' : 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4'} ${numItems > 6 ? 'max-h-52 overflow-y-auto pr-1' : ''}`}>
              {Array.from({ length: numItems }).map((_, idx) => (
                <div key={idx}>
                  <Label className="text-[10px] text-gray-400 dark:text-gray-500 mb-0.5 block">Row {idx + 1}</Label>
                  <button
                    type="button"
                    ref={(el) => { rowBtnRefs.current[idx] = el }}
                    onClick={() => {
                      if (activeMenu?.type === idx) { setActiveMenu(null); return }
                      const r = rowBtnRefs.current[idx]?.getBoundingClientRect()
                      if (r) setActiveMenu({ type: idx, pos: { top: r.bottom + 4, left: r.left, width: Math.max(r.width, 200) } })
                    }}
                    className="w-full px-2.5 py-1.5 text-[12px] text-left bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer flex items-center justify-between"
                  >
                    <span className="truncate">{items.find(i => i.id === itemIds[idx])?.name ?? 'Select...'}</span>
                    <svg className={`size-3 text-gray-400 transition-transform shrink-0 ${activeMenu?.type === idx ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                  </button>
                </div>
              ))}
            </div>
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
                className="h-9 text-[12px] flex-1"
              />
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
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 shrink-0 flex items-center gap-2">
          {!running ? (
            <Button
              onClick={handleStart}
              disabled={running || supplier === null || itemIds.length === 0 || loadingData}
              className="h-8 text-[12px] gap-1.5 cursor-pointer"
            >
              <Play className="size-3.5" />
              Run {count > 1 ? `${count}×` : ''} {Array.from(enabledDocs).join(' → ')}
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
            >
              <Key className="size-3" />
              Set Token
            </Button>
          )}
          {(erpToken || localToken) && (
            <button
              onClick={() => { setLocalToken(''); setLocalTenantId(''); setSuppliers([]); setItems([]); setSupplier(null); setItemIds([]); fetchedRef.current = false; onClearToken() }}
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
        </div>
      </div>

      {/* Logs panel */}
      <div className="flex-1 min-h-0 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-gray-50 dark:bg-gray-900/50">
        <div className="flex items-center justify-between px-4 py-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shrink-0">
          <span className="text-[12px] font-medium text-gray-500 dark:text-gray-400">
            Console Output
            {logs.length > 0 && <span className="ml-2 text-gray-400 dark:text-gray-500">({logs.length} lines)</span>}
          </span>
          {created + failed > 0 && (
            <span className="text-[11px]">
              <span className="text-emerald-600 dark:text-emerald-400">{created} created</span>
              {failed > 0 && <span className="text-red-500 dark:text-red-400 ml-2">{failed} failed</span>}
            </span>
          )}
        </div>
        <ScrollArea className="h-full">
          <div className="p-3 font-mono text-[12px] leading-relaxed">
            {logs.length === 0 && !running && (
              <p className="text-gray-400 dark:text-gray-500 italic">Configure and click "Run" to start the purchase chain.</p>
            )}
            {logs.length === 0 && running && (
              <p className="text-[#3F51B5] dark:text-[#7986CB] animate-pulse">Starting...</p>
            )}
            {logs.map((log, i) => (
              <div key={i} className={`flex gap-2 ${log.isErr ? 'text-red-500 dark:text-red-400' : log.isDone ? 'text-emerald-600 dark:text-emerald-400 font-semibold' : 'text-gray-700 dark:text-gray-200'}`}>
                <span className="text-gray-400 dark:text-gray-500 shrink-0 w-16">[{formatTime(log.ts)}]</span>
                <span className="whitespace-pre-wrap break-all">{log.text}</span>
              </div>
            ))}
            {running && <div className="text-[#3F51B5] dark:text-[#7986CB] animate-pulse">▌</div>}
            <div ref={logsEndRef} />
          </div>
        </ScrollArea>
      </div>

      {/* Floating dropdown menu via portal */}
      {activeMenu && typeof document !== 'undefined' && createPortal(
        <>
          <div className="fixed inset-0 z-50" onClick={() => setActiveMenu(null)} />
          <div
            className="fixed z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg max-h-48 overflow-y-auto"
            style={{ top: activeMenu.pos.top, left: activeMenu.pos.left, width: activeMenu.pos.width }}
          >
            {(activeMenu.type === 'supplier' ? suppliers : items).length === 0 ? (
              <div className="px-3 py-2 text-[12px] text-gray-400 dark:text-gray-500">No data loaded</div>
            ) : (
              (activeMenu.type === 'supplier' ? suppliers : items).map((i) => {
                const selected = activeMenu.type === 'supplier'
                  ? i.id === supplier
                  : activeMenu.type === 'item'
                    ? i.id === itemIds[0]
                    : i.id === itemIds[activeMenu.type as number]
                return (
                  <button
                    key={i.id}
                    type="button"
                    onClick={() => {
                      if (activeMenu.type === 'supplier') {
                        setSupplier(i.id)
                      } else if (activeMenu.type === 'item') {
                        setItemIds([i.id])
                      } else {
                        setItemIds((prev) => { const next = [...prev]; next[activeMenu.type as number] = i.id; return next })
                      }
                      setActiveMenu(null)
                    }}
                    className={`w-full px-3 py-1.5 text-[12px] text-left hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer ${selected ? 'bg-[#3F51B5]/10 dark:bg-[#3F51B5]/20 text-[#3F51B5] dark:text-[#7986CB] font-medium' : 'text-gray-700 dark:text-gray-200'}`}
                  >
                    {i.name}
                  </button>
                )
              })
            )}
          </div>
        </>,
        document.body
      )}
    </div>
  )
}
