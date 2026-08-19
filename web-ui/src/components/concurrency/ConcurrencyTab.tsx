'use client'

import React, { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { Plus, Share2, Play, BadgeCheck, Key, Check, X, Box, Monitor, Loader2, Terminal, RefreshCw, BarChart2, History, Search, Clock, ChevronLeft, ChevronRight, Filter } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { SetTokenDialog } from '@/components/dialogs/SetTokenDialog'
import { MODULE_TO_BATCH } from '@/components/dialogs/BatchCreateSection'
import { startBatchCreate, saveConcurrencyRun } from '@/lib/api'
import { notifySuccess } from '@/lib/notify'
import type { RunHistoryItem } from '@/lib/api'
import type { SidebarModule } from '@/components/sidebar/SidebarModuleItem'

// ── Types ──────────────────────────────────────────────────────────

interface Pc1Tenant {
  id: string
  label: string
  token: string
  tenantId: string
  moduleId: string
  sharedToPc2: boolean
}

interface AutoPatchedEntry {
  kind: 'auto-patched'
  sourceId: string
  token: string
  tenantId: string
}

interface IndependentEntry {
  kind: 'independent'
  id: string
  label: string
  token: string
  tenantId: string
  moduleId: string
}

type Pc2Entry = AutoPatchedEntry | IndependentEntry

// ── Pair colour palette ────────────────────────────────────────────
const PAIR_COLORS = [
  { accent: '#16a34a', border: 'border-green-200 dark:border-green-700/50',   bg: 'bg-green-50 dark:bg-green-900/20',   icon: 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400',   badge: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',   tokenOk: 'text-green-600 dark:text-green-400' },
  { accent: '#2563eb', border: 'border-blue-200 dark:border-blue-700/50',     bg: 'bg-blue-50 dark:bg-blue-900/20',     icon: 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400',     badge: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',     tokenOk: 'text-blue-600 dark:text-blue-400' },
  { accent: '#9333ea', border: 'border-purple-200 dark:border-purple-700/50', bg: 'bg-purple-50 dark:bg-purple-900/20', icon: 'bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400', badge: 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300', tokenOk: 'text-purple-600 dark:text-purple-400' },
  { accent: '#ea580c', border: 'border-orange-200 dark:border-orange-700/50', bg: 'bg-orange-50 dark:bg-orange-900/20', icon: 'bg-orange-100 dark:bg-orange-900/40 text-orange-600 dark:text-orange-400', badge: 'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300', tokenOk: 'text-orange-600 dark:text-orange-400' },
  { accent: '#e11d48', border: 'border-rose-200 dark:border-rose-700/50',     bg: 'bg-rose-50 dark:bg-rose-900/20',     icon: 'bg-rose-100 dark:bg-rose-900/40 text-rose-600 dark:text-rose-400',     badge: 'bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300',     tokenOk: 'text-rose-600 dark:text-rose-400' },
  { accent: '#0d9488', border: 'border-teal-200 dark:border-teal-700/50',     bg: 'bg-teal-50 dark:bg-teal-900/20',     icon: 'bg-teal-100 dark:bg-teal-900/40 text-teal-600 dark:text-teal-400',     badge: 'bg-teal-100 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300',     tokenOk: 'text-teal-600 dark:text-teal-400' },
] as const

// ── Helpers ────────────────────────────────────────────────────────

interface ModuleGroup { label: string; leaves: SidebarModule[] }

function collectGroupedLeaves(items: SidebarModule[], parentLabel?: string): { groupLabel: string; leaf: SidebarModule }[] {
  const result: { groupLabel: string; leaf: SidebarModule }[] = []
  for (const item of items) {
    if (!item.children || item.children.length === 0) {
      result.push({ groupLabel: parentLabel ?? 'Other', leaf: item })
    } else {
      result.push(...collectGroupedLeaves(item.children, item.label))
    }
  }
  return result
}

function buildModuleGroups(modules: SidebarModule[]): ModuleGroup[] {
  const pairs = collectGroupedLeaves(modules)
  const map = new Map<string, SidebarModule[]>()
  for (const { groupLabel, leaf } of pairs) {
    if (!map.has(groupLabel)) map.set(groupLabel, [])
    map.get(groupLabel)!.push(leaf)
  }
  return [...map.entries()].map(([label, leaves]) => ({ label, leaves }))
}

let _nextId = 1
function genId() { return `conc-${_nextId++}-${Date.now()}` }

// ── ModulePicker ───────────────────────────────────────────────────

const COMPANY_ONBOARDING_ID = 'company-onboarding'

function hasTests(m: SidebarModule): boolean {
  return !!m.badge || (m.badgeType !== undefined && m.badgeType !== 'none')
}

function ModulePicker({ value, onChange, groups, allLeaves }: {
  value: string
  onChange: (v: string) => void
  groups: ModuleGroup[]
  allLeaves: SidebarModule[]
}) {
  const [open, setOpen] = useState(false)
  const [activeGroup, setActiveGroup] = useState<string | null>(null)
  const [coords, setCoords] = useState<{ top?: number; bottom?: number; left: number; width: number } | null>(null)
  const ref = useRef<HTMLDivElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      const target = e.target as Node
      const insideTrigger = ref.current?.contains(target)
      const insidePanel = panelRef.current?.contains(target)
      if (!insideTrigger && !insidePanel) { setOpen(false); setActiveGroup(null) }
    }
    if (open) document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  useEffect(() => {
    if (!open || !ref.current) return
    ref.current.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    requestAnimationFrame(() => {
      if (!ref.current) return
      const r = ref.current.getBoundingClientRect()
      const dropW = 480
      const left = Math.max(8, Math.min(r.left + r.width / 2 - dropW / 2, window.innerWidth - dropW - 8))
      const panelH = panelRef.current?.offsetHeight || 340
      const spaceBelow = window.innerHeight - r.bottom - 8
      if (spaceBelow < panelH && r.top > panelH) {
        setCoords({ bottom: window.innerHeight - r.top + 4, left, width: r.width })
      } else {
        setCoords({ top: r.bottom + 4, left, width: r.width })
      }
    })
  }, [open])

  const companyOnboarding = allLeaves.find((m) => m.id === COMPANY_ONBOARDING_ID)
  const filteredGroups = groups
    .map((g) => ({ ...g, leaves: g.leaves.filter((m) => hasTests(m) && m.id !== COMPANY_ONBOARDING_ID) }))
    .filter((g) => g.leaves.length > 0)
  const selectedLabel = value ? allLeaves.find((m) => m.id === value)?.label : null
  const children = activeGroup ? filteredGroups.find((g) => g.label === activeGroup)?.leaves ?? [] : []

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => { setOpen((o) => !o); setActiveGroup(null) }}
        className="w-full h-8 flex items-center justify-between px-3 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-[13px] text-left outline-none focus:ring-2 focus:ring-[#3F51B5]/30 transition-all hover:border-gray-300 dark:hover:border-gray-500"
      >
        <span className={selectedLabel ? 'text-gray-800 dark:text-gray-100 truncate' : 'text-gray-400 dark:text-gray-500'}>
          {selectedLabel ?? 'Select module…'}
        </span>
        <svg className="size-3.5 text-gray-400 shrink-0 ml-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {open && coords && createPortal(
        <div
          ref={panelRef}
          style={{ position: 'fixed', top: coords.top, bottom: coords.bottom, left: coords.left, width: 480, zIndex: 9999 }}
          className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl shadow-2xl overflow-hidden flex flex-col"
        >
          {!activeGroup ? (
            <div className="p-2.5 flex flex-col gap-2 overflow-y-auto">
              <p className="text-[11px] uppercase tracking-wider text-gray-400 dark:text-gray-500 px-1 font-medium">Pick a module</p>
              {companyOnboarding && (
                <button
                  type="button"
                  onClick={() => { onChange(companyOnboarding.id); setOpen(false) }}
                  className={`w-full px-3 py-2 rounded-lg border text-[13px] font-medium text-left transition-colors ${
                    value === companyOnboarding.id
                      ? 'border-[#3F51B5]/50 bg-[#3F51B5]/10 text-[#3F51B5] dark:text-[#7986CB]'
                      : 'border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50 text-gray-700 dark:text-gray-200 hover:border-[#3F51B5]/40 hover:bg-[#3F51B5]/5'
                  }`}
                >
                  {companyOnboarding.label}
                </button>
              )}
              <div className="grid grid-cols-3 gap-1.5">
                {filteredGroups.map((g) => (
                  <button
                    key={g.label}
                    type="button"
                    onClick={() => setActiveGroup(g.label)}
                    className="px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50 text-[12px] font-medium text-gray-700 dark:text-gray-200 text-left hover:border-[#3F51B5]/50 hover:bg-[#3F51B5]/5 dark:hover:bg-[#3F51B5]/10 transition-colors truncate"
                  >
                    {g.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-2.5 flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setActiveGroup(null)}
                  className="text-[12px] text-[#3F51B5] dark:text-[#7986CB] hover:underline cursor-pointer shrink-0 font-medium"
                >
                  ← Back
                </button>
                <span className="text-[11px] uppercase tracking-wider text-gray-400 dark:text-gray-500 font-medium truncate">{activeGroup}</span>
              </div>
              <div className="grid grid-cols-3 gap-1.5">
                {children.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => { onChange(m.id); setOpen(false); setActiveGroup(null) }}
                    className={`px-3 py-2 rounded-lg border text-[12px] font-medium text-left transition-colors truncate ${
                      m.id === value
                        ? 'border-[#3F51B5]/50 bg-[#3F51B5]/10 text-[#3F51B5] dark:text-[#7986CB]'
                        : 'border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50 text-gray-700 dark:text-gray-200 hover:border-[#3F51B5]/50 hover:bg-[#3F51B5]/5 dark:hover:bg-[#3F51B5]/10'
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>,
        document.body
      )}
    </div>
  )
}

// ── Stepper counter control ───────────────────────────────────────

function Counter({ value, onChange }: { value: number; onChange: (n: number) => void }) {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => onChange(Math.max(0, value - 1))}
        className="size-7 rounded-lg border border-gray-200 dark:border-gray-600 flex items-center justify-center text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer text-[16px] leading-none font-medium"
      >−</button>
      <span className="w-6 text-center text-[15px] font-semibold text-gray-800 dark:text-gray-100">{value}</span>
      <button
        onClick={() => onChange(value + 1)}
        className="size-7 rounded-lg border border-gray-200 dark:border-gray-600 flex items-center justify-center text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer text-[16px] leading-none font-medium"
      >+</button>
    </div>
  )
}

// ── Wizard step type ───────────────────────────────────────────────

interface WizardStep {
  kind: 'shared' | 'pc1-only' | 'pc2-only'
  id: string
  indexInGroup: number
  totalInGroup: number
}

// ── Component ──────────────────────────────────────────────────────

export function ConcurrencyTab({ modules }: { modules: SidebarModule[] }) {
  const [pc1Tenants, setPc1Tenants] = useState<Pc1Tenant[]>([])
  const [pc2Entries, setPc2Entries] = useState<Pc2Entry[]>([])
  const [mode, setMode] = useState<'api' | 'ui'>('api')
  const [apiMode, setApiMode] = useState<'create' | 'crud'>('create')

  // wizard
  const [wizardPhase, setWizardPhase] = useState<'setup' | 'step' | 'board'>('setup')
  const [sharedCount, setSharedCount] = useState(1)
  const [pc1OnlyCount, setPc1OnlyCount] = useState(0)
  const [pc2OnlyCount, setPc2OnlyCount] = useState(0)
  const [wizardSteps, setWizardSteps] = useState<WizardStep[]>([])
  const [stepIndex, setStepIndex] = useState(0)
  const [confirmReset, setConfirmReset] = useState(false)

  // board manual-add drafts
  const [pc1DraftLabel, setPc1DraftLabel] = useState('')
  const [pc2DraftLabel, setPc2DraftLabel] = useState('')

  // token dialog
  const [tokenDialogOpenFor, setTokenDialogOpenFor] = useState<string | null>(null)
  const [dialogToken, setDialogToken] = useState('')
  const [dialogTenantId, setDialogTenantId] = useState('')

  // batch run
  const [batchCount, setBatchCount] = useState(10)
  const [cardLogs, setCardLogs] = useState<Record<string, string[]>>({})
  const [cardStatus, setCardStatus] = useState<Record<string, 'idle' | 'running' | 'done' | 'error'>>({})

  interface CardResult {
    created: string[]
    failed: { name: string; reason: string }[]
  }
  const [runResults, setRunResults] = useState<Record<string, CardResult> | null>(null)
  const [showResults, setShowResults] = useState(false)
  const resultsRef = useRef<Record<string, CardResult>>({})
  const resultJobsRef = useRef<Array<{ id: string; label: string; moduleId: string; side: 'pc1' | 'pc2' }>>([])
  const timingRef = useRef<Record<string, { startMs: number; endMs: number; events: { name: string; ms: number; side: 'created' | 'failed' }[] }>>({})
  const [runTiming, setRunTiming] = useState<typeof timingRef.current | null>(null)

  // history
  const [showHistory, setShowHistory] = useState(false)
  const [historyRuns, setHistoryRuns] = useState<RunHistoryItem[] | null>(null)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [historyDetail, setHistoryDetail] = useState<RunHistoryItem | null>(null)
  const [showHistoryDetail, setShowHistoryDetail] = useState(false)
  const [historyFilter, setHistoryFilter] = useState<'all' | 'completed' | 'failed'>('all')
  const [historyPeriod, setHistoryPeriod] = useState<'all' | 'today' | 'week' | 'month'>('all')
  const [historyPage, setHistoryPage] = useState(0)
  const fetchHistory = useCallback(async () => {
    setLoadingHistory(true)
    try {
      const res = await fetch('/api/runs?limit=100')
      if (res.ok) {
        const all: RunHistoryItem[] = await res.json()
        setHistoryRuns(all.filter(r => r.moduleId === 'concurrency'))
      }
    } catch {} finally { setLoadingHistory(false) }
  }, [])

  const moduleGroups = useMemo(() => buildModuleGroups(modules), [modules])
  const allLeaves = useMemo(() => moduleGroups.flatMap((g) => g.leaves), [moduleGroups])

  // scroll helpers
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const cardRefs = useRef<Map<string, HTMLDivElement>>(new Map())
  const pendingScrollId = useRef<string | null>(null)

  useEffect(() => {
    if (!pendingScrollId.current) return
    const el = cardRefs.current.get(pendingScrollId.current)
    if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); pendingScrollId.current = null }
  })

  const scrollToCenter = useCallback((key: string) => {
    const el = cardRefs.current.get(key)
    const container = scrollContainerRef.current
    if (!el || !container) return
    const target = el.offsetTop - container.clientHeight / 2 + el.offsetHeight / 2
    container.scrollTo({ top: Math.max(0, target), behavior: 'smooth' })
  }, [])

  // token dialog handlers
  const openTokenDialog = useCallback((id: string, side: 'pc1' | 'pc2') => {
    if (side === 'pc1') {
      const ex = pc1Tenants.find((t) => t.id === id)
      setDialogToken(ex?.token ?? '')
      setDialogTenantId(ex?.tenantId ?? '')
    } else {
      const ex = pc2Entries.find((t) => t.kind === 'auto-patched' ? t.sourceId === id : t.id === id)
      setDialogToken(ex?.token ?? '')
      setDialogTenantId(ex?.tenantId ?? '')
    }
    setTokenDialogOpenFor(`${side}:${id}`)
  }, [pc1Tenants, pc2Entries])

  const closeTokenDialog = useCallback(() => {
    if (!tokenDialogOpenFor) return
    const [side, id] = tokenDialogOpenFor.split(':') as ['pc1' | 'pc2', string]
    if (side === 'pc1') {
      setPc1Tenants((prev) => prev.map((t) => (t.id === id ? { ...t, token: dialogToken, tenantId: dialogTenantId } : t)))
    } else {
      setPc2Entries((prev) => prev.map((t) => {
        if (t.kind === 'auto-patched' && t.sourceId === id) return { ...t, token: dialogToken, tenantId: dialogTenantId }
        if (t.kind === 'independent' && t.id === id) return { ...t, token: dialogToken, tenantId: dialogTenantId }
        return t
      }))
    }
    setTokenDialogOpenFor(null)
  }, [tokenDialogOpenFor, dialogToken, dialogTenantId])

  // PC-1 helpers
  const addPc1Tenant = useCallback(() => {
    if (!pc1DraftLabel.trim()) return
    const t: Pc1Tenant = { id: genId(), label: pc1DraftLabel.trim(), token: '', tenantId: '', moduleId: '', sharedToPc2: false }
    setPc1Tenants((prev) => [...prev, t])
    setPc1DraftLabel('')
    pendingScrollId.current = `pc1-${t.id}`
  }, [pc1DraftLabel])

  const updatePc1Tenant = useCallback((id: string, patch: Partial<Pick<Pc1Tenant, 'label' | 'moduleId' | 'sharedToPc2'>>) => {
    setPc1Tenants((prev) => prev.map((t) => (t.id === id ? { ...t, ...patch } : t)))
    if (patch.sharedToPc2 === false) setPc2Entries((prev) => prev.filter((e) => !(e.kind === 'auto-patched' && e.sourceId === id)))
  }, [])

  const removePc1Tenant = useCallback((id: string) => {
    setPc1Tenants((prev) => prev.filter((t) => t.id !== id))
    setPc2Entries((prev) => prev.filter((e) => !(e.kind === 'auto-patched' && e.sourceId === id)))
  }, [])

  const shareToPc2 = useCallback((id: string) => {
    setPc1Tenants((prev) => prev.map((t) => (t.id === id ? { ...t, sharedToPc2: true } : t)))
    setPc2Entries((prev) => {
      if (prev.some((e) => e.kind === 'auto-patched' && e.sourceId === id)) return prev
      return [...prev, { kind: 'auto-patched', sourceId: id, token: '', tenantId: '' }]
    })
  }, [])

  // PC-2 helpers
  const addIndependentPc2 = useCallback(() => {
    if (!pc2DraftLabel.trim()) return
    const e: IndependentEntry = { kind: 'independent', id: genId(), label: pc2DraftLabel.trim(), token: '', tenantId: '', moduleId: '' }
    setPc2Entries((prev) => [...prev, e])
    setPc2DraftLabel('')
    pendingScrollId.current = `pc2-${e.id}`
  }, [pc2DraftLabel])

  const updateIndependentPc2 = useCallback((id: string, patch: Partial<Pick<IndependentEntry, 'label' | 'moduleId'>>) => {
    setPc2Entries((prev) => prev.map((e) => (e.kind === 'independent' && e.id === id ? { ...e, ...patch } : e)))
  }, [])

  const removePc2Entry = useCallback((entry: Pc2Entry) => {
    if (entry.kind === 'auto-patched') setPc1Tenants((prev) => prev.map((t) => (t.id === entry.sourceId ? { ...t, sharedToPc2: false } : t)))
    setPc2Entries((prev) => prev.filter((e) => e !== entry))
  }, [])

  // derived
  const findPc1Label = useCallback((id: string) => pc1Tenants.find((t) => t.id === id)?.label ?? '', [pc1Tenants])
  const findPc1ModuleId = useCallback((id: string) => pc1Tenants.find((t) => t.id === id)?.moduleId ?? '', [pc1Tenants])
  const moduleLabel = (id: string) => allLeaves.find((m) => m.id === id)?.label ?? id

  const canRun = useMemo(() => {
    for (const t of pc1Tenants) {
      if (!t.token || !t.tenantId || !t.moduleId) return false
      if (!MODULE_TO_BATCH[t.moduleId]) return false
    }
    for (const e of pc2Entries) {
      if (!e.token || !e.tenantId) return false
      if (e.kind === 'independent' && !e.moduleId) return false
      const mid = e.kind === 'auto-patched' ? findPc1ModuleId(e.sourceId) : e.moduleId
      if (!mid || !MODULE_TO_BATCH[mid]) return false
    }
    return true
  }, [pc1Tenants, pc2Entries, findPc1ModuleId])

  const isRunning = useMemo(() => Object.values(cardStatus).some((s) => s === 'running'), [cardStatus])

  const handleRun = useCallback(async () => {
    const jobs: Array<{ id: string; token: string; tenantId: string; moduleId: string }> = []

    for (const t of pc1Tenants) {
      if (t.token && t.tenantId && t.moduleId) jobs.push({ id: t.id, token: t.token, tenantId: t.tenantId, moduleId: t.moduleId })
    }
    for (const e of pc2Entries) {
      if (e.kind === 'auto-patched') {
        const src = pc1Tenants.find((t) => t.id === e.sourceId)
        if (e.token && e.tenantId && src?.moduleId) jobs.push({ id: e.sourceId + '-pc2', token: e.token, tenantId: e.tenantId, moduleId: src.moduleId })
      } else {
        if (e.token && e.tenantId && e.moduleId) jobs.push({ id: e.id, token: e.token, tenantId: e.tenantId, moduleId: e.moduleId })
      }
    }

    if (jobs.length === 0) return

    setRunResults(null)
    setShowResults(false)
    setRunTiming(null)
    resultsRef.current = {}
    timingRef.current = {}
    resultJobsRef.current = pc1Tenants.filter((t) => t.token && t.tenantId && t.moduleId && MODULE_TO_BATCH[t.moduleId]).map((t) => ({ id: t.id, label: t.label, moduleId: t.moduleId, side: 'pc1' as const }))
    for (const e of pc2Entries) {
      if (e.kind === 'auto-patched') {
        const src = pc1Tenants.find((t) => t.id === e.sourceId)
        if (e.token && e.tenantId && src?.moduleId && MODULE_TO_BATCH[src.moduleId]) {
          resultJobsRef.current.push({ id: src.id + '-pc2', label: src.label + ' (PC-2)', moduleId: src.moduleId, side: 'pc2' as const })
        }
      } else {
        if (e.token && e.tenantId && e.moduleId && MODULE_TO_BATCH[e.moduleId]) {
          resultJobsRef.current.push({ id: e.id, label: e.label, moduleId: e.moduleId, side: 'pc2' as const })
        }
      }
    }

    setCardLogs({})
    setCardStatus(Object.fromEntries(jobs.map((j) => [j.id, 'running'])))

    const runStartMs = Date.now()
    jobs.forEach(j => { timingRef.current[j.id] = { startMs: Date.now() - runStartMs, endMs: 0, events: [] } })

    await Promise.all(jobs.map((job) => {
      const target = MODULE_TO_BATCH[job.moduleId]
      if (!target) {
        setCardStatus((prev) => ({ ...prev, [job.id]: 'error' }))
        setCardLogs((prev) => ({ ...prev, [job.id]: [`Module "${job.moduleId}" not supported for batch create`] }))
        return Promise.resolve()
      }
      return startBatchCreate(
        target.module,
        target.subModule,
        batchCount,
        job.token,
        job.tenantId,
        (event) => {
          if (event.message) {
            setCardLogs((prev) => ({ ...prev, [job.id]: [...(prev[job.id] ?? []), event.message] }))
            const createdMatch = event.message.match(/^\s*\[\d+\/\d+\]\s+(?:CREATED|UPDATED)\s+#\d+\s+-\s+(.+)$/)
            const failedMatch = event.message.match(/^\s*\[\d+\/\d+\]\s+FAILED\s+-\s+(.+?):\s+(.+)/)
            if (createdMatch) {
              if (!resultsRef.current[job.id]) resultsRef.current[job.id] = { created: [], failed: [] }
              resultsRef.current[job.id].created.push(createdMatch[1].trim())
              timingRef.current[job.id]?.events.push({ name: createdMatch[1].trim(), ms: Date.now() - runStartMs, side: 'created' })
            }
            if (failedMatch) {
              if (!resultsRef.current[job.id]) resultsRef.current[job.id] = { created: [], failed: [] }
              resultsRef.current[job.id].failed.push({ name: failedMatch[1].trim(), reason: failedMatch[2].trim() })
              timingRef.current[job.id]?.events.push({ name: failedMatch[1].trim(), ms: Date.now() - runStartMs, side: 'failed' })
            }
          }
        },
        () => {
          if (timingRef.current[job.id]) timingRef.current[job.id].endMs = Date.now() - runStartMs
          setCardStatus((prev) => ({ ...prev, [job.id]: 'done' }))
        },
        () => setCardStatus((prev) => ({ ...prev, [job.id]: 'error' })),
        null,
        undefined,
      )
    }))
    const finalResults = { ...resultsRef.current }
    const finalTiming = { ...timingRef.current }
    setRunResults(finalResults)
    setRunTiming(finalTiming)
    setShowResults(true)
    resultsRef.current = {}
    timingRef.current = {}

    // Fire-and-forget save to run history + desktop notification
    const totalCreatedFinal = Object.values(finalResults).reduce((s, r) => s + (r?.created?.length ?? 0), 0)
    const totalFailedFinal = Object.values(finalResults).reduce((s, r) => s + (r?.failed?.length ?? 0), 0)
    notifySuccess('Concurrency Run Complete', `${totalCreatedFinal} created, ${totalFailedFinal} failed`)
    const pc1End = Math.max(...resultJobsRef.current.filter(j => j.side === 'pc1').map(j => finalTiming[j.id]?.endMs ?? 0), 0)
    const pc2End = Math.max(...resultJobsRef.current.filter(j => j.side === 'pc2').map(j => finalTiming[j.id]?.endMs ?? 0), 0)
    saveConcurrencyRun({
      totalCreated: Object.values(finalResults).reduce((s, r) => s + (r?.created?.length ?? 0), 0),
      totalFailed: Object.values(finalResults).reduce((s, r) => s + (r?.failed?.length ?? 0), 0),
      durationMs: Math.max(pc1End, pc2End),
      overlapMs: Math.min(pc1End, pc2End),
      conflicts: (() => {
        const pc1fn = new Set(resultJobsRef.current.filter(j => j.side === 'pc1').flatMap(j => finalResults[j.id]?.failed.map(f => f.name) ?? []))
        const pc2fn = new Set(resultJobsRef.current.filter(j => j.side === 'pc2').flatMap(j => finalResults[j.id]?.failed.map(f => f.name) ?? []))
        const pc1cn = new Set(resultJobsRef.current.filter(j => j.side === 'pc1').flatMap(j => finalResults[j.id]?.created ?? []))
        const pc2cn = new Set(resultJobsRef.current.filter(j => j.side === 'pc2').flatMap(j => finalResults[j.id]?.created ?? []))
        return [...pc1cn].filter(n => pc2fn.has(n)).length + [...pc2cn].filter(n => pc1fn.has(n)).length
      })(),
      duplicates: (() => {
        const a = new Set(resultJobsRef.current.filter(j => j.side === 'pc1').flatMap(j => finalResults[j.id]?.created ?? []))
        const b = new Set(resultJobsRef.current.filter(j => j.side === 'pc2').flatMap(j => finalResults[j.id]?.created ?? []))
        return [...a].filter(n => b.has(n))
      })(),
      jobs: resultJobsRef.current.map(j => ({
        ...j,
        created: finalResults[j.id]?.created ?? [],
        failed: finalResults[j.id]?.failed ?? [],
      })),
      timing: finalTiming,
    })
  }, [pc1Tenants, pc2Entries, batchCount, cardStatus])

  // wizard helpers
  const labelForIndex = (i: number) => String.fromCharCode(65 + i)

  const startWizard = useCallback(() => {
    const total = sharedCount + pc1OnlyCount + pc2OnlyCount
    if (total === 0) return
    const sharedTenants: Pc1Tenant[] = Array.from({ length: sharedCount }, (_, i) => ({ id: genId(), label: `Tenant ${labelForIndex(i)}`, token: '', tenantId: '', moduleId: '', sharedToPc2: true }))
    const pc1OnlyTenants: Pc1Tenant[] = Array.from({ length: pc1OnlyCount }, (_, i) => ({ id: genId(), label: `PC1-${labelForIndex(i)}`, token: '', tenantId: '', moduleId: '', sharedToPc2: false }))
    const pc2OnlyEntries: IndependentEntry[] = Array.from({ length: pc2OnlyCount }, (_, i) => ({ kind: 'independent', id: genId(), label: `PC2-${labelForIndex(i)}`, token: '', tenantId: '', moduleId: '' }))
    const autoPatched: AutoPatchedEntry[] = sharedTenants.map((t) => ({ kind: 'auto-patched', sourceId: t.id, token: '', tenantId: '' }))
    setPc1Tenants([...sharedTenants, ...pc1OnlyTenants])
    setPc2Entries([...autoPatched, ...pc2OnlyEntries])
    const steps: WizardStep[] = [
      ...sharedTenants.map((t, i) => ({ kind: 'shared' as const, id: t.id, indexInGroup: i + 1, totalInGroup: sharedCount })),
      ...pc1OnlyTenants.map((t, i) => ({ kind: 'pc1-only' as const, id: t.id, indexInGroup: i + 1, totalInGroup: pc1OnlyCount })),
      ...pc2OnlyEntries.map((e, i) => ({ kind: 'pc2-only' as const, id: e.id, indexInGroup: i + 1, totalInGroup: pc2OnlyCount })),
    ]
    setWizardSteps(steps)
    setStepIndex(0)
    setWizardPhase('step')
  }, [sharedCount, pc1OnlyCount, pc2OnlyCount])

  const nextStep = useCallback(() => {
    if (stepIndex < wizardSteps.length - 1) setStepIndex((i) => i + 1)
    else setWizardPhase('board')
  }, [stepIndex, wizardSteps.length])

  const resetWizard = useCallback(() => {
    if (!confirmReset) { setConfirmReset(true); return }
    setConfirmReset(false)
    setPc1Tenants([]); setPc2Entries([]); setWizardSteps([]); setStepIndex(0)
    setSharedCount(1); setPc1OnlyCount(0); setPc2OnlyCount(0)
    setWizardPhase('setup')
  }, [confirmReset])

  const MP = ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <ModulePicker value={value} onChange={onChange} groups={moduleGroups} allLeaves={allLeaves} />
  )

  // ── Token row reusable ────────────────────────────────────────────

  function TokenRow({ token, tenantId, onSet, colorClass }: { token: string; tenantId: string; onSet: () => void; colorClass?: string }) {
    return (
      <div className="flex items-center justify-between pt-1">
        {token ? (
          <span className={`text-[12px] flex items-center gap-1.5 ${colorClass ?? 'text-green-600 dark:text-green-400'}`}>
            <Check className="size-3.5 shrink-0" />
            Token set{tenantId && <span className="text-gray-400 dark:text-gray-500 font-normal">· {tenantId}</span>}
          </span>
        ) : (
          <span className="text-[12px] text-amber-500 dark:text-amber-400 flex items-center gap-1.5">
            <span className="text-[14px] leading-none">⚠</span> No token
          </span>
        )}
        <button
          onClick={onSet}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-gray-200 dark:border-gray-600 text-[12px] text-gray-600 dark:text-gray-300 hover:border-[#3F51B5]/50 hover:text-[#3F51B5] dark:hover:text-[#7986CB] transition-colors cursor-pointer bg-white dark:bg-gray-800"
        >
          <Key className="size-3" />{token ? 'Update' : 'Set Token'}
        </button>
      </div>
    )
  }

  function CardLogs({ cardKey }: { cardKey: string }) {
    const status = cardStatus[cardKey]
    const logs = cardLogs[cardKey]
    if (!status) return null
    return (
      <div className="mt-2 rounded-lg bg-gray-950 dark:bg-gray-950 border border-gray-800 p-2 max-h-28 overflow-y-auto">
        {status === 'running' && (!logs || logs.length === 0) && (
          <p className="text-[11px] text-gray-500 italic">Starting…</p>
        )}
        {(logs ?? []).map((line, i) => (
          <p key={i} className="text-[11px] text-gray-300 font-mono leading-relaxed">{line}</p>
        ))}
        {status === 'done' && <p className="text-[11px] text-green-400 font-mono mt-1">Done</p>}
        {status === 'error' && <p className="text-[11px] text-red-400 font-mono mt-1">Error</p>}
      </div>
    )
  }

  function RunResultsPanel({ results, jobs, runTiming, onClose }: {
    results: Record<string, CardResult>
    jobs: Array<{ id: string; label: string; moduleId: string; side: 'pc1' | 'pc2' }>
    runTiming?: Record<string, { startMs: number; endMs: number; events: { name: string; ms: number; side: 'created' | 'failed' }[] }>
    onClose: () => void
  }) {
    if (jobs.length === 0) return null
    const [viewMode, setViewMode] = useState<'bypc' | 'timeline'>('bypc')
    const totalCreated = Object.values(results).reduce((s, r) => s + (r?.created?.length ?? 0), 0)
    const totalFailed = Object.values(results).reduce((s, r) => s + (r?.failed?.length ?? 0), 0)
    const allPc1 = new Set(jobs.filter((j) => j.side === 'pc1').flatMap((j) => results[j.id]?.created ?? []))
    const allPc2 = new Set(jobs.filter((j) => j.side === 'pc2').flatMap((j) => results[j.id]?.created ?? []))
    const duplicates = [...allPc1].filter((name) => allPc2.has(name))
    const pc1FailedNames = new Set(jobs.filter((j) => j.side === 'pc1').flatMap((j) => results[j.id]?.failed.map(f => f.name) ?? []))
    const pc2FailedNames = new Set(jobs.filter((j) => j.side === 'pc2').flatMap((j) => results[j.id]?.failed.map(f => f.name) ?? []))
    const pc1CreatedNames = new Set(jobs.filter((j) => j.side === 'pc1').flatMap((j) => results[j.id]?.created ?? []))
    const pc2CreatedNames = new Set(jobs.filter((j) => j.side === 'pc2').flatMap((j) => results[j.id]?.created ?? []))
    const conflicts = [...pc1CreatedNames].filter(n => pc2FailedNames.has(n)).length + [...pc2CreatedNames].filter(n => pc1FailedNames.has(n)).length
    const pc1End = Math.max(...jobs.filter(j => j.side === 'pc1').map(j => runTiming?.[j.id]?.endMs ?? 0), 0)
    const pc2End = Math.max(...jobs.filter(j => j.side === 'pc2').map(j => runTiming?.[j.id]?.endMs ?? 0), 0)
    const totalMs = Math.max(pc1End, pc2End)
    const overlapMs = Math.min(pc1End, pc2End)
    const allEvents = jobs.flatMap(j =>
      (runTiming?.[j.id]?.events ?? []).map(e => ({ ...e, eventSide: e.side, side: j.side, jobLabel: j.label, jobId: j.id }))
    ).sort((a, b) => a.ms - b.ms)

    return createPortal(
      <>
        {/* Backdrop */}
        <div className="fixed inset-0 bg-black/40 dark:bg-black/60 z-[9998]" onClick={onClose} />
        {/* Modal */}
        <div className="fixed z-[9999] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl max-h-[80vh] overflow-y-auto bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700/50 shadow-2xl">
          <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100 dark:border-gray-700/30">
            <div className="flex items-center gap-3">
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="text-[15px] font-semibold text-gray-800 dark:text-gray-100">Load Test Complete</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-400 font-medium">Parallel Run</span>
                </div>
                <span className="text-[11px] text-gray-400 dark:text-gray-500 mt-0.5">Both PCs ran simultaneously — {totalCreated} records created in {(totalMs/1000).toFixed(1)}s</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-0.5 mr-2 bg-gray-100 dark:bg-gray-700/50 rounded-lg p-0.5">
                <button onClick={() => setViewMode('bypc')} className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors cursor-pointer ${viewMode === 'bypc' ? 'bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 shadow-xs' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}>By PC</button>
                <button onClick={() => setViewMode('timeline')} className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors cursor-pointer ${viewMode === 'timeline' ? 'bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 shadow-xs' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}>Timeline</button>
              </div>
              <Button onClick={handleRun} disabled={isRunning} className="h-8 px-3 text-[12px] gap-1.5 cursor-pointer">
                <RefreshCw className="size-3.5" />
                Run Again
              </Button>
              <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors cursor-pointer">
                <X className="size-4" />
              </button>
            </div>
          </div>

          {runTiming && totalMs > 0 && (
            <div className="px-5 py-3 border-b border-gray-100 dark:border-gray-700/30">
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-3">
                  <span className="text-[11px] font-semibold w-8 text-gray-500 dark:text-gray-400">PC-1</span>
                  <div className="flex-1 h-2 rounded-full bg-gray-100 dark:bg-gray-700/50 overflow-hidden">
                    <div className="h-full rounded-full bg-indigo-400 dark:bg-indigo-500" style={{ width: `${(pc1End / totalMs) * 100}%` }} />
                  </div>
                  <span className="text-[11px] text-gray-400 font-mono w-12 text-right">{(pc1End / 1000).toFixed(1)}s</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[11px] font-semibold w-8 text-gray-500 dark:text-gray-400">PC-2</span>
                  <div className="flex-1 h-2 rounded-full bg-gray-100 dark:bg-gray-700/50 overflow-hidden">
                    <div className="h-full rounded-full bg-purple-400 dark:bg-purple-500" style={{ width: `${(pc2End / totalMs) * 100}%` }} />
                  </div>
                  <span className="text-[11px] text-gray-400 font-mono w-12 text-right">{(pc2End / 1000).toFixed(1)}s</span>
                </div>
              </div>
              <div className="mt-2 flex items-center gap-2">
                {overlapMs > 500 ? (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">⚡ {overlapMs}ms concurrent overlap</span>
                ) : overlapMs > 0 ? (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">⚠ Runs barely overlapped ({overlapMs}ms)</span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300">⚠ No overlap — sequential</span>
                )}
              </div>
            </div>
          )}

          {viewMode === 'bypc' ? (
            <div className="grid grid-cols-2 gap-4 p-4">
              {['pc1', 'pc2'].map((side) => {
                const sideJobs = jobs.filter((j) => j.side === side)
                if (sideJobs.length === 0) return <div key={side} />
                return (
                  <div key={side} className="flex flex-col gap-3">
                    <p className="text-[11px] font-bold uppercase tracking-widest text-gray-400 dark:text-gray-500">{side === 'pc1' ? 'PC-1' : 'PC-2'}</p>
                    {sideJobs.map((job) => {
                      const r = results[job.id]
                      const t = runTiming?.[job.id]
                      const avgMs = t && t.events.length > 0 ? Math.round(t.events[t.events.length - 1].ms / t.events.length) : 0
                      if (!r) return null
                      return (
                        <div key={job.id} className="bg-gray-50 dark:bg-gray-700/30 rounded-lg border border-gray-100 dark:border-gray-700/30 p-3">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-[13px] font-medium text-gray-800 dark:text-gray-100 truncate flex-1">{job.label}</span>
                            {avgMs > 0 && <span className="text-[11px] text-gray-400 font-mono">~{avgMs}ms/record</span>}
                            <span className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-[12px] px-2 py-0.5 rounded-full shrink-0">
                              ✓ {r.created.length} created
                            </span>
                            {r.failed.length > 0 && (
                              <span className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-[12px] px-2 py-0.5 rounded-full shrink-0">
                                ✗ {r.failed.length} failed
                              </span>
                            )}
                          </div>
                          {r.created.length > 0 && (
                            <div className="max-h-32 overflow-y-auto">
                              {r.created.map((name, i) => (
                                <p key={i} className="text-[12px] text-gray-600 dark:text-gray-400 font-mono leading-relaxed">{name}</p>
                              ))}
                            </div>
                          )}
                          {r.failed.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-red-100 dark:border-red-900/30">
                              {r.failed.map((f, i) => (
                                <p key={i} className="text-[12px] text-red-600 dark:text-red-400 font-mono leading-relaxed">
                                  {f.name}: {f.reason}
                                </p>
                              ))}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="p-4">
              <div className="max-h-72 overflow-y-auto flex flex-col gap-1">
                {allEvents.map((ev, i, arr) => {
                  const prev = i > 0 ? arr[i - 1] : null
                  const concurrent = prev && ev.ms - prev.ms <= 100 && prev.side !== ev.side
                  return (
                    <div key={i} className={`flex items-center gap-2 px-2 py-1 rounded text-[12px] ${concurrent ? 'border-l-2 border-amber-400 bg-amber-50/30 dark:bg-amber-900/10' : ''}`}>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-medium ${ev.side === 'pc1' ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' : 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'}`}>
                        {ev.side === 'pc1' ? 'PC-1' : 'PC-2'}
                      </span>
                      <span className="text-[11px] text-gray-400 font-mono w-14 shrink-0">+{(ev.ms / 1000).toFixed(2)}s</span>
                      <span className={ev.eventSide === 'created' ? 'text-green-500 shrink-0' : 'text-red-500 shrink-0'}>{ev.eventSide === 'created' ? '✓' : '✗'}</span>
                      <span className="text-gray-700 dark:text-gray-300 font-mono truncate">{ev.name}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {duplicates.length > 0 && (
            <div className="mx-4 mb-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/40 text-amber-700 dark:text-amber-300 text-[13px] rounded-lg px-4 py-2">
              ⚠ {duplicates.length} duplicate{duplicates.length > 1 ? 's' : ''} detected across PCs: {duplicates.join(', ')}
            </div>
          )}
          <div className="px-5 py-2.5 border-t border-gray-100 dark:border-gray-700/30 text-[12px] text-gray-500 dark:text-gray-400">
            {runTiming && totalMs > 0 && <span>⚡ {overlapMs}ms overlap · </span>}
            <strong className="text-gray-700 dark:text-gray-200">{totalCreated}</strong> created,{' '}
            <strong className={totalFailed > 0 ? 'text-red-600 dark:text-red-400' : ''}>{totalFailed}</strong> failed
            {conflicts > 0 && <span className="text-red-600 dark:text-red-400"> · {conflicts} conflict{conflicts > 1 ? 's' : ''}</span>}
          </div>
        </div>
      </>,
      document.body
    )
  }

  // ── Setup screen ─────────────────────────────────────────────────
  if (wizardPhase === 'setup') {
    const total = sharedCount + pc1OnlyCount + pc2OnlyCount
    return (
      <div className="flex flex-col h-full min-h-0 items-center justify-center bg-gray-50 dark:bg-gray-900 px-6">
        <div className="w-full max-w-md">
          {/* Header */}
          <div className="mb-8 text-center">
            <div className="size-14 rounded-2xl bg-[#3F51B5]/10 dark:bg-[#3F51B5]/20 flex items-center justify-center mx-auto mb-4">
              <Monitor className="size-7 text-[#3F51B5] dark:text-[#7986CB]" />
            </div>
            <h1 className="text-[20px] font-semibold text-gray-900 dark:text-gray-100 mb-1.5">Concurrency Test Setup</h1>
            <p className="text-[14px] text-gray-500 dark:text-gray-400">Configure how many tenants run across PC-1 and PC-2</p>
          </div>

          {/* Counter cards */}
          <div className="flex flex-col gap-3">
            {[
              { label: 'Shared tenants', desc: 'Same tenant runs on both PC-1 and PC-2', value: sharedCount, set: setSharedCount },
              { label: 'PC-1 exclusive', desc: 'Tenants that only run on PC-1', value: pc1OnlyCount, set: setPc1OnlyCount },
              { label: 'PC-2 exclusive', desc: 'Tenants that only run on PC-2', value: pc2OnlyCount, set: setPc2OnlyCount },
            ].map(({ label, desc, value, set }) => (
              <div key={label} className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700/50 shadow-sm px-5 py-4">
                <div>
                  <p className="text-[14px] font-medium text-gray-800 dark:text-gray-100">{label}</p>
                  <p className="text-[12px] text-gray-400 dark:text-gray-500 mt-0.5">{desc}</p>
                </div>
                <Counter value={value} onChange={set} />
              </div>
            ))}
          </div>

          {total > 0 && (
            <p className="text-center text-[13px] text-gray-400 dark:text-gray-500 mt-4">
              {total} tenant{total !== 1 ? 's' : ''} — you'll label them and pick modules next
            </p>
          )}

          <Button onClick={startWizard} disabled={total === 0} className="w-full mt-4 h-10 text-[14px] gap-2 cursor-pointer">
            <Play className="size-4" />
            Start Setup
          </Button>
        </div>
      </div>
    )
  }

  // ── Step screen ──────────────────────────────────────────────────
  if (wizardPhase === 'step') {
    const step = wizardSteps[stepIndex]
    const totalSteps = wizardSteps.length
    const progress = Math.round((stepIndex / totalSteps) * 100)

    const pc1Tenant = step.kind !== 'pc2-only' ? pc1Tenants.find((t) => t.id === step.id) : undefined
    const pc2Entry = step.kind === 'pc2-only'
      ? (pc2Entries.find((e) => e.kind === 'independent' && e.id === step.id) as IndependentEntry | undefined)
      : undefined
    const currentLabel = pc1Tenant?.label ?? pc2Entry?.label ?? ''
    const currentModuleId = pc1Tenant?.moduleId ?? pc2Entry?.moduleId ?? ''

    const setCurrentLabel = (label: string) => {
      if (pc1Tenant) updatePc1Tenant(step.id, { label })
      else if (pc2Entry) updateIndependentPc2(step.id, { label })
    }
    const setCurrentModule = (moduleId: string) => {
      if (pc1Tenant) updatePc1Tenant(step.id, { moduleId })
      else if (pc2Entry) updateIndependentPc2(step.id, { moduleId })
      openTokenDialog(step.id, step.kind === 'pc2-only' ? 'pc2' : 'pc1')
    }

    const kindMeta = {
      shared: { label: 'Shared pair', color: 'bg-[#3F51B5]/10 text-[#3F51B5] dark:bg-[#3F51B5]/20 dark:text-[#7986CB]' },
      'pc1-only': { label: 'PC-1 exclusive', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' },
      'pc2-only': { label: 'PC-2 exclusive', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' },
    }[step.kind]

    return (
      <div className="flex flex-col h-full min-h-0 items-center justify-center bg-gray-50 dark:bg-gray-900 px-6">
        <div className="w-full max-w-md">
          {/* Progress */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[13px] text-gray-400 dark:text-gray-500">Step {stepIndex + 1} of {totalSteps}</span>
              <span className={`text-[12px] font-medium px-2.5 py-0.5 rounded-full ${kindMeta.color}`}>
                {kindMeta.label} {step.indexInGroup}/{step.totalInGroup}
              </span>
            </div>
            <div className="h-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full bg-[#3F51B5] dark:bg-[#7986CB] rounded-full transition-all duration-300" style={{ width: `${progress}%` }} />
            </div>
          </div>

          {/* Card */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700/50 shadow-sm overflow-hidden">
            {step.kind === 'shared' && (
              <div className="px-5 pt-4 pb-3.5 bg-[#3F51B5]/5 dark:bg-[#3F51B5]/10 border-b border-[#3F51B5]/10 dark:border-[#3F51B5]/20">
                <p className="text-[13px] text-gray-600 dark:text-gray-300">
                  This tenant runs on <strong>both</strong> PC-1 and PC-2 — configure once, auto-patched to PC-2.
                </p>
              </div>
            )}
            <div className="px-5 py-5 flex flex-col gap-4">
              <div>
                <label className="text-[12px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2 block">Label</label>
                <input
                  value={currentLabel}
                  onChange={(e) => setCurrentLabel(e.target.value)}
                  className="w-full h-10 px-3.5 rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700/50 text-[14px] text-gray-800 dark:text-gray-100 outline-none focus:ring-2 focus:ring-[#3F51B5]/30 transition-all"
                  placeholder="e.g. Tenant A"
                  autoFocus
                />
              </div>
              <div>
                <label className="text-[12px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2 block">
                  Module{step.kind === 'shared' ? ' (same on both PCs)' : ''}
                </label>
                <MP value={currentModuleId} onChange={setCurrentModule} />
              </div>
            </div>
            {step.kind === 'shared' && (
              <div className="px-5 pb-4">
                <div className="flex items-center gap-3 text-[13px] text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/30 rounded-xl px-4 py-2.5">
                  <span className="font-medium text-gray-700 dark:text-gray-200 truncate">{currentLabel || '…'}</span>
                  <svg width="36" height="10" viewBox="0 0 36 10" fill="none" className="shrink-0">
                    <line x1="0" y1="5" x2="27" y2="5" stroke="#6366f1" strokeWidth="1.5" strokeDasharray="3 2"/>
                    <path d="M22 1.5 L30 5 L22 8.5" stroke="#6366f1" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <span className="text-gray-400 shrink-0">auto-patched to PC-2</span>
                </div>
              </div>
            )}
          </div>

          {/* Nav */}
          <div className="flex gap-2.5 mt-4">
            <Button variant="outline" onClick={nextStep} className="flex-1 h-10 text-[13px] cursor-pointer text-gray-400 hover:text-gray-600">
              Skip
            </Button>
            <Button onClick={nextStep} className="flex-1 h-10 text-[14px] gap-1.5 cursor-pointer">
              {stepIndex < totalSteps - 1 ? (
                <>Next <svg className="size-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M9 18l6-6-6-6"/></svg></>
              ) : (
                <>Done <Check className="size-4" /></>
              )}
            </Button>
          </div>

          {confirmReset ? (
            <div className="flex items-center justify-center gap-3 mt-3">
              <span className="text-[13px] text-gray-500">Reset everything?</span>
              <button onClick={resetWizard} className="text-[13px] font-medium text-red-500 hover:text-red-600 cursor-pointer px-2 py-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">Yes</button>
              <button onClick={() => setConfirmReset(false)} className="text-[13px] text-gray-400 hover:text-gray-600 cursor-pointer px-2 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors">Cancel</button>
            </div>
          ) : (
            <button onClick={resetWizard} className="w-full mt-3 text-[13px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors cursor-pointer py-1.5">
              ← Start over
            </button>
          )}
        </div>

        <SetTokenDialog
          open={tokenDialogOpenFor !== null}
          onClose={closeTokenDialog}
          erpToken={dialogToken}
          setErpToken={setDialogToken}
          erpTenantId={dialogTenantId}
          setErpTenantId={setDialogTenantId}
        />
      </div>
    )
  }

  // ── Board ────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-full min-h-0">

      {/* Tab bar */}
      <div className="flex items-center gap-0 px-4 py-0 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shrink-0">
        <button className="flex items-center gap-1.5 px-3.5 py-2.5 text-[12px] font-medium border-b-2 border-[#3F51B5] text-[#3F51B5] dark:text-[#7986CB] cursor-default">
          <Terminal className="size-3.5" />
          API Tests
        </button>
        <div className="flex items-center gap-1 ml-3">
          <button
            onClick={() => setApiMode('create')}
            className={`px-3 py-1.5 text-[11px] font-medium rounded-md transition-colors cursor-pointer ${
              apiMode === 'create' ? 'bg-[#3F51B5] text-white' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            Create
          </button>
          <button
            onClick={() => setApiMode('crud')}
            className={`px-3 py-1.5 text-[11px] font-medium rounded-md transition-colors cursor-pointer ${
              apiMode === 'crud' ? 'bg-[#3F51B5] text-white' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            CRUD
          </button>
        </div>
        <div className="flex-1" />
        {confirmReset ? (
          <div className="flex items-center gap-2 mr-3">
            <span className="text-[12px] text-gray-500 dark:text-gray-400">Reset everything?</span>
            <button onClick={resetWizard} className="text-[12px] font-medium text-red-500 hover:text-red-600 cursor-pointer px-2 py-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">Yes, reset</button>
            <button onClick={() => setConfirmReset(false)} className="text-[12px] text-gray-400 hover:text-gray-600 cursor-pointer px-2 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors">Cancel</button>
          </div>
        ) : (
          <button onClick={resetWizard} className="text-[12px] text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors cursor-pointer px-3 py-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 border border-transparent hover:border-gray-200 dark:hover:border-gray-700 mr-2">
            Edit Setup
          </button>
        )}
        <Button onClick={handleRun} disabled={!canRun || isRunning} title={!canRun ? 'All tenants need a token, tenant ID, and supported module' : ''} className="h-8 px-3 text-[12px] gap-1.5 cursor-pointer">
          {isRunning ? <Loader2 className="size-3.5 animate-spin" /> : <Play className="size-3.5" />}
          {isRunning ? 'Running...' : 'Run'}
        </Button>
        {runResults && !isRunning && (
          <button onClick={() => setShowResults(true)} className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] rounded-lg border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:border-[#3F51B5]/50 hover:text-[#3F51B5] transition-colors cursor-pointer bg-white dark:bg-gray-800">
            <BarChart2 className="size-3.5" /> View Results
          </button>
        )}
        <button onClick={() => { fetchHistory(); setShowHistory(true) }} className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] rounded-lg border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:border-[#3F51B5]/50 hover:text-[#3F51B5] transition-colors cursor-pointer bg-white dark:bg-gray-800">
          <History className="size-3.5" /> History
        </button>
      </div>

      {/* Mode indicator + Records input */}
      <div key={apiMode} className="animate-fadeIn shrink-0 flex items-center gap-3 px-5 py-1.5 bg-gradient-to-r from-indigo-50/60 to-transparent dark:from-indigo-950/20 dark:to-transparent border-b border-indigo-100/50 dark:border-indigo-900/30">
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300">
          {apiMode === 'crud' ? 'CRUD' : 'Create'} Mode
        </span>
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] font-medium text-gray-500 dark:text-gray-400">Records:</span>
          <Input
            type="number"
            min={1}
            max={500}
            value={batchCount}
            onChange={(e) => setBatchCount(Math.max(1, Math.min(500, parseInt(e.target.value) || 10)))}
            disabled={isRunning}
            className="h-6 w-14 text-[11px]"
          />
        </div>
        <span className="text-[11px] text-gray-400 dark:text-gray-500">
          {apiMode === 'crud' ? 'Run full CRUD cycle per record' : `Batch-create ${batchCount} record${batchCount > 1 ? 's' : ''} per tenant`}
        </span>
      </div>

      {/* Column headers + add inputs */}
      <div className="shrink-0 grid grid-cols-[1fr_48px_1fr] bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700/50 sticky top-0 z-10">
        <div className="px-5 py-3 border-r border-gray-200 dark:border-gray-700/50">
          <p className="text-[11px] font-bold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">PC-1</p>
          <div className="flex gap-2">
            <Input
              placeholder="Label e.g. Tenant A"
              value={pc1DraftLabel}
              onChange={(e) => setPc1DraftLabel(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') addPc1Tenant() }}
              className="h-9 text-[13px] flex-1"
            />
            <Button variant="outline" size="sm" onClick={addPc1Tenant} disabled={!pc1DraftLabel.trim()} className="h-9 text-[13px] gap-1.5 shrink-0 cursor-pointer px-3">
              <Plus className="size-3.5" />Add
            </Button>
          </div>
        </div>
        <div />
        <div className="px-5 py-3">
          <p className="text-[11px] font-bold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">PC-2</p>
          <div className="flex gap-2">
            <Input
              placeholder="Label e.g. Tenant F"
              value={pc2DraftLabel}
              onChange={(e) => setPc2DraftLabel(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') addIndependentPc2() }}
              className="h-9 text-[13px] flex-1"
            />
            <Button variant="outline" size="sm" onClick={addIndependentPc2} disabled={!pc2DraftLabel.trim()} className="h-9 text-[13px] gap-1.5 shrink-0 cursor-pointer px-3">
              <Plus className="size-3.5" />Add
            </Button>
          </div>
        </div>
      </div>

      {/* Scrollable body */}
      <div ref={scrollContainerRef} className="flex-1 min-h-0 overflow-y-auto bg-gray-50 dark:bg-gray-950">

        {pc1Tenants.length === 0 && pc2Entries.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <p className="text-[14px] text-gray-400 dark:text-gray-500">No tenants yet</p>
            <p className="text-[13px] text-gray-400 dark:text-gray-500 mt-1 opacity-70">Add a label above or go back to edit setup</p>
          </div>
        )}

        {/* ── Paired rows ─────────────────────────────────────────── */}
        <div className="flex flex-col gap-3 px-4 pt-4">
          {pc1Tenants.map((t, idx) => {
            if (!t.sharedToPc2) return null
            const pc2e = pc2Entries.find((e) => e.kind === 'auto-patched' && e.sourceId === t.id)
            if (!pc2e || pc2e.kind !== 'auto-patched') return null
            const pc = PAIR_COLORS[idx % PAIR_COLORS.length]
            return (
              <div
                key={`pair-${t.id}`}
                ref={(el) => { if (el) cardRefs.current.set(`pair-${t.id}`, el); else cardRefs.current.delete(`pair-${t.id}`) }}
                onClick={() => scrollToCenter(`pair-${t.id}`)}
                className="grid grid-cols-[1fr_48px_1fr] gap-0 cursor-default"
              >
                {/* PC-1 card */}
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700/50 shadow-sm overflow-hidden">
                  <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-50 dark:bg-gray-700/40 border-b border-gray-100 dark:border-gray-700/30">
                    <div className="size-5 rounded-lg flex items-center justify-center shrink-0 bg-[#3F51B5]/10 dark:bg-[#3F51B5]/20">
                      <Box className="size-3 text-[#3F51B5] dark:text-[#7986CB]" />
                    </div>
                    <input
                      value={t.label}
                      onChange={(e) => updatePc1Tenant(t.id, { label: e.target.value })}
                      className="flex-1 text-[13px] font-semibold bg-transparent border-none outline-none text-gray-800 dark:text-gray-100 min-w-0"
                    />
                    <button
                      onClick={() => updatePc1Tenant(t.id, { sharedToPc2: false })}
                      className={`flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-md transition-colors cursor-pointer shrink-0 ${pc.badge}`}
                    >
                      <BadgeCheck className="size-3" />Shared
                    </button>
                    <button onClick={() => removePc1Tenant(t.id)} className="shrink-0 cursor-pointer ml-1" title="Remove">
                      <X className="size-3.5 text-gray-300 hover:text-red-500 dark:hover:text-red-400 transition-colors" />
                    </button>
                  </div>
                  <div className="px-4 py-3 flex flex-col gap-3">
                    <div>
                      <p className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 mb-1.5 uppercase tracking-wide">Module</p>
                      <MP value={t.moduleId} onChange={(v) => updatePc1Tenant(t.id, { moduleId: v })} />
                    </div>
                    <TokenRow token={t.token} tenantId={t.tenantId} onSet={() => openTokenDialog(t.id, 'pc1')} />
                    <CardLogs cardKey={t.id} />
                  </div>
                </div>

                {/* Connector */}
                <div className="flex items-center justify-center">
                  <svg width="48" height="14" viewBox="0 0 48 14" fill="none">
                    <line x1="0" y1="7" x2="35" y2="7" stroke={pc.accent} strokeWidth="1.5" strokeDasharray="4 2.5" />
                    <path d="M29 3 L38 7 L29 11" stroke={pc.accent} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>

                {/* PC-2 auto-patched card */}
                <div className={`bg-white dark:bg-gray-800 rounded-xl border ${pc.border} shadow-sm overflow-hidden`}>
                  <div className={`flex items-center gap-2 px-4 py-2.5 ${pc.bg} border-b border-current/10`} style={{ borderColor: `${pc.accent}20` }}>
                    <div className={`size-5 rounded-lg flex items-center justify-center shrink-0 ${pc.icon}`}>
                      <BadgeCheck className="size-3" />
                    </div>
                    <span className="flex-1 text-[13px] font-semibold text-gray-800 dark:text-gray-100 truncate">{t.label}</span>
                    <span className={`text-[11px] font-medium px-2 py-0.5 rounded-md shrink-0 ${pc.badge}`}>auto-patched</span>
                    <button onClick={() => removePc2Entry(pc2e)} className="shrink-0 cursor-pointer ml-1" title="Unshare">
                      <X className="size-3.5 text-gray-300 hover:text-red-500 dark:hover:text-red-400 transition-colors" />
                    </button>
                  </div>
                  <div className="px-4 py-3 flex flex-col gap-3">
                    <div>
                      <p className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 mb-1.5 uppercase tracking-wide">Module</p>
                      <div className="h-8 flex items-center px-3 rounded-lg border border-gray-100 dark:border-gray-700/30 bg-gray-50 dark:bg-gray-700/20 text-[13px] text-gray-500 dark:text-gray-400">
                        {t.moduleId ? moduleLabel(t.moduleId) : <span className="italic opacity-60">From PC-1</span>}
                      </div>
                    </div>
                    <TokenRow token={pc2e.token} tenantId={pc2e.tenantId} onSet={() => openTokenDialog(t.id, 'pc2')} colorClass={pc.tokenOk} />
                    <CardLogs cardKey={t.id + '-pc2'} />
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* ── Solo section: unshared PC-1 (left) + independent PC-2 (right) ── */}
        {(pc1Tenants.some((t) => !t.sharedToPc2) || pc2Entries.some((e) => e.kind === 'independent')) && (
          <div className="grid grid-cols-[1fr_48px_1fr] gap-0 px-4 pt-3 pb-4">
            {/* Unshared PC-1 */}
            <div className="flex flex-col gap-3">
              {pc1Tenants.filter((t) => !t.sharedToPc2).map((t) => (
                <div
                  key={t.id}
                  ref={(el) => { if (el) cardRefs.current.set(`pc1-${t.id}`, el); else cardRefs.current.delete(`pc1-${t.id}`) }}
                  onClick={() => scrollToCenter(`pc1-${t.id}`)}
                  className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700/50 shadow-sm overflow-hidden cursor-default"
                >
                  <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-50 dark:bg-gray-700/40 border-b border-gray-100 dark:border-gray-700/30">
                    <div className="size-5 rounded-lg flex items-center justify-center shrink-0 bg-[#3F51B5]/10 dark:bg-[#3F51B5]/20">
                      <Box className="size-3 text-[#3F51B5] dark:text-[#7986CB]" />
                    </div>
                    <input
                      value={t.label}
                      onChange={(e) => updatePc1Tenant(t.id, { label: e.target.value })}
                      className="flex-1 text-[13px] font-semibold bg-transparent border-none outline-none text-gray-800 dark:text-gray-100 min-w-0"
                    />
                    <button
                      onClick={() => shareToPc2(t.id)}
                      className="flex items-center gap-1 text-[11px] font-medium text-gray-400 hover:text-[#3F51B5] dark:hover:text-[#7986CB] px-2 py-0.5 rounded-md hover:bg-[#3F51B5]/10 transition-colors cursor-pointer shrink-0"
                    >
                      <Share2 className="size-3" />Share
                    </button>
                    <button onClick={() => removePc1Tenant(t.id)} className="shrink-0 cursor-pointer ml-1" title="Remove">
                      <X className="size-3.5 text-gray-300 hover:text-red-500 dark:hover:text-red-400 transition-colors" />
                    </button>
                  </div>
                  <div className="px-4 py-3 flex flex-col gap-3">
                    <div>
                      <p className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 mb-1.5 uppercase tracking-wide">Module</p>
                      <MP value={t.moduleId} onChange={(v) => updatePc1Tenant(t.id, { moduleId: v })} />
                    </div>
                    <TokenRow token={t.token} tenantId={t.tenantId} onSet={() => openTokenDialog(t.id, 'pc1')} />
                    <CardLogs cardKey={t.id} />
                  </div>
                </div>
              ))}
            </div>

            <div />

            {/* Independent PC-2 */}
            <div className="flex flex-col gap-3">
              {pc2Entries.filter((e) => e.kind === 'independent').length === 0 && (
                <p className="text-[13px] text-gray-400 dark:text-gray-500 italic text-center py-6">
                  Share from PC-1 or add independent tenants above
                </p>
              )}
              {pc2Entries.filter((e) => e.kind === 'independent').map((entry) => {
                if (entry.kind !== 'independent') return null
                return (
                  <div
                    key={`indep-${entry.id}`}
                    ref={(el) => { if (el) cardRefs.current.set(`pc2-${entry.id}`, el); else cardRefs.current.delete(`pc2-${entry.id}`) }}
                    onClick={() => scrollToCenter(`pc2-${entry.id}`)}
                    className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700/50 shadow-sm overflow-hidden cursor-default"
                  >
                    <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-50 dark:bg-gray-700/40 border-b border-gray-100 dark:border-gray-700/30">
                      <div className="size-5 rounded-lg flex items-center justify-center shrink-0 bg-[#3F51B5]/10 dark:bg-[#3F51B5]/20">
                        <Box className="size-3 text-[#3F51B5] dark:text-[#7986CB]" />
                      </div>
                      <input
                        value={entry.label}
                        onChange={(e) => updateIndependentPc2(entry.id, { label: e.target.value })}
                        className="flex-1 text-[13px] font-semibold bg-transparent border-none outline-none text-gray-800 dark:text-gray-100 min-w-0"
                      />
                      <button onClick={() => removePc2Entry(entry)} className="shrink-0 cursor-pointer ml-1" title="Remove">
                        <X className="size-3.5 text-gray-300 hover:text-red-500 dark:hover:text-red-400 transition-colors" />
                      </button>
                    </div>
                    <div className="px-4 py-3 flex flex-col gap-3">
                      <div>
                        <p className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 mb-1.5 uppercase tracking-wide">Module</p>
                        <MP value={entry.moduleId} onChange={(v) => updateIndependentPc2(entry.id, { moduleId: v })} />
                      </div>
                      <TokenRow token={entry.token} tenantId={entry.tenantId} onSet={() => openTokenDialog(entry.id, 'pc2')} />
                      <CardLogs cardKey={entry.id} />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Run results modal */}
      {runResults && showResults && resultJobsRef.current.length > 0 && (
        <RunResultsPanel results={runResults} jobs={resultJobsRef.current} runTiming={runTiming ?? undefined} onClose={() => setShowResults(false)} />
      )}

      {/* History dialog */}
      <Dialog open={showHistory} onOpenChange={(v) => { if (!v) setShowHistory(false) }}>
        <DialogContent className="sm:max-w-[750px] dark:bg-gray-800 dark:border-gray-600/60 p-0 gap-0">
          <DialogTitle className="sr-only">Concurrency Run History</DialogTitle>
          <DialogDescription className="sr-only">Browse past concurrency test runs</DialogDescription>

          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-600/40">
            <div className="flex items-center gap-2">
              <BarChart2 className="size-4 text-gray-500" />
              <h2 className="text-[15px] font-semibold text-gray-800 dark:text-gray-100">Concurrency History</h2>
              <span className="text-[12px] text-gray-400 dark:text-gray-500">({historyRuns?.length ?? 0} runs)</span>
            </div>
            <button onClick={() => setShowHistory(false)} className="size-6 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer">
              <X className="size-4" />
            </button>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-200 dark:border-gray-600/40 bg-gray-50/50 dark:bg-gray-800/30">
            <Filter className="size-3.5 text-gray-400 shrink-0" />
            <select value={historyFilter} onChange={(e) => { setHistoryFilter(e.target.value as typeof historyFilter); setHistoryPage(0) }}
              className="h-7 text-[12px] px-2 rounded border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 outline-none focus:border-indigo-400 cursor-pointer"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
            <select value={historyPeriod} onChange={(e) => { setHistoryPeriod(e.target.value as typeof historyPeriod); setHistoryPage(0) }}
              className="h-7 text-[12px] px-2 rounded border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 outline-none focus:border-indigo-400 cursor-pointer"
            >
              <option value="all">All Time</option>
              <option value="today">Today</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
            </select>
          </div>

          {/* Table */}
          <div className="overflow-y-auto max-h-[420px]">
            {loadingHistory ? (
              <div className="flex items-center justify-center py-12 text-gray-400 dark:text-gray-500">
                <Loader2 className="size-5 animate-spin mr-2" />
                <span className="text-[13px]">Loading…</span>
              </div>
            ) : historyRuns && historyRuns.length > 0 ? (
              (() => {
                let filtered = historyRuns
                if (historyFilter === 'completed') filtered = filtered.filter(r => r.status === 'completed')
                if (historyFilter === 'failed') filtered = filtered.filter(r => r.status === 'failed')
                if (historyPeriod !== 'all') {
                  const now = new Date()
                  const start = historyPeriod === 'today' ? new Date(now.getFullYear(), now.getMonth(), now.getDate())
                    : historyPeriod === 'week' ? new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay())
                    : new Date(now.getFullYear(), now.getMonth(), 1)
                  filtered = filtered.filter(r => new Date(r.startedAt) >= start)
                }
                const totalPages = Math.ceil(filtered.length / 15)
                const page = Math.min(historyPage, Math.max(0, totalPages - 1))
                const paginated = filtered.slice(page * 15, (page + 1) * 15)
                return (
                  <>
                    <table className="w-full">
                      <thead>
                        <tr className="text-[11px] text-gray-500 dark:text-gray-400 uppercase tracking-wider border-b border-gray-100 dark:border-gray-700/40 bg-gray-50 dark:bg-gray-800/50">
                          <th className="text-left px-4 py-2 font-medium w-10">#</th>
                          <th className="text-left px-3 py-2 font-medium">Date</th>
                          <th className="text-right px-3 py-2 font-medium">Jobs</th>
                          <th className="text-right px-3 py-2 font-medium">Created</th>
                          <th className="text-right px-3 py-2 font-medium">Failed</th>
                          <th className="text-right px-3 py-2 font-medium">Overlap</th>
                          <th className="text-right px-3 py-2 font-medium">Duration</th>
                          <th className="text-right px-3 py-2 font-medium">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 dark:divide-gray-700/40">
                        {paginated.map((run, idx) => {
                          const r = typeof run.results === 'string' ? JSON.parse(run.results) : run.results
                          const jc = r?.jobs?.length ?? 0
                          const started = new Date(run.startedAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
                          return (
                            <tr key={run.id}
                              onClick={() => { setHistoryDetail(run); setShowHistoryDetail(true) }}
                              className="text-[13px] text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors cursor-pointer"
                            >
                              <td className="px-4 py-2.5 text-gray-400 dark:text-gray-500 font-mono text-[12px]">{page * 15 + idx + 1}</td>
                              <td className="px-3 py-2.5 whitespace-nowrap text-[12px] text-gray-600 dark:text-gray-300">{started}</td>
                              <td className="px-3 py-2.5 text-right text-gray-600 dark:text-gray-300">{jc}</td>
                              <td className="px-3 py-2.5 text-right text-green-600 dark:text-green-400 font-medium">{run.passed}</td>
                              <td className={`px-3 py-2.5 text-right font-medium ${run.failed > 0 ? 'text-red-500 dark:text-red-400' : 'text-gray-400 dark:text-gray-500'}`}>{run.failed}</td>
                              <td className="px-3 py-2.5 text-right font-mono text-[12px] text-gray-500 dark:text-gray-400">{r?.overlapMs > 0 ? `${r.overlapMs}ms` : '—'}</td>
                              <td className="px-3 py-2.5 text-right font-mono text-[12px] text-gray-500 dark:text-gray-400">{run.duration}</td>
                              <td className="px-3 py-2.5 text-right">
                                <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${run.status === 'completed' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'}`}>
                                  {run.status}
                                </span>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                    {totalPages > 1 && (
                      <div className="flex items-center justify-between px-4 py-2.5 border-t border-gray-200 dark:border-gray-600/40 bg-gray-50/50 dark:bg-gray-800/30">
                        <span className="text-[12px] text-gray-500 dark:text-gray-400">{filtered.length} run{filtered.length !== 1 ? 's' : ''}</span>
                        <div className="flex items-center gap-1">
                          <button onClick={() => setHistoryPage(p => Math.max(0, p - 1))} disabled={page === 0}
                            className="size-6 flex items-center justify-center rounded text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
                          >
                            <ChevronLeft className="size-3.5" />
                          </button>
                          {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                            const start = Math.max(0, Math.min(page - 2, totalPages - 5))
                            const p = start + i
                            return (
                              <button key={p} onClick={() => setHistoryPage(p)}
                                className={`size-6 text-[12px] rounded transition-colors cursor-pointer ${p === page ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-medium' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
                              >{p + 1}</button>
                            )
                          })}
                          <button onClick={() => setHistoryPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
                            className="size-6 flex items-center justify-center rounded text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
                          >
                            <ChevronRight className="size-3.5" />
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )
              })()
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500">
                <History className="size-8 mb-2" />
                <p className="text-[13px]">No concurrency runs yet</p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* History detail dialog */}
      <Dialog open={showHistoryDetail} onOpenChange={(v) => { if (!v) setShowHistoryDetail(false) }}>
        <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto dark:bg-gray-800 dark:border-gray-600/60">
          <DialogTitle className="text-[15px] flex items-center gap-2">
            <BarChart2 className="size-4 text-[#3F51B5]" />
            Run Details
          </DialogTitle>
          <DialogDescription className="sr-only" />
          {historyDetail && (() => {
            const r = typeof historyDetail.results === 'string' ? JSON.parse(historyDetail.results) : historyDetail.results
            return (
              <div className="flex flex-col gap-4">
                {/* Summary cards */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-3 text-center">
                    <p className="text-[11px] uppercase text-gray-500 dark:text-gray-400 font-medium">Created</p>
                    <p className="text-[16px] font-bold text-green-600 dark:text-green-400 mt-0.5">{historyDetail.passed}</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-3 text-center">
                    <p className="text-[11px] uppercase text-gray-500 dark:text-gray-400 font-medium">Failed</p>
                    <p className="text-[16px] font-bold text-red-500 mt-0.5">{historyDetail.failed}</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-3 text-center">
                    <p className="text-[11px] uppercase text-gray-500 dark:text-gray-400 font-medium">Duration</p>
                    <p className="text-[16px] font-bold text-gray-700 dark:text-gray-200 font-mono mt-0.5">{historyDetail.duration}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-3 text-center">
                    <p className="text-[11px] uppercase text-gray-500 dark:text-gray-400 font-medium">Overlap</p>
                    <p className="text-[14px] font-bold text-gray-700 dark:text-gray-200 mt-0.5">{r?.overlapMs ?? 0}ms</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-3 text-center">
                    <p className="text-[11px] uppercase text-gray-500 dark:text-gray-400 font-medium">Status</p>
                    <p className={`text-[14px] font-bold mt-0.5 ${historyDetail.status === 'completed' ? 'text-green-600' : 'text-red-500'}`}>{historyDetail.status}</p>
                  </div>
                </div>

                {/* Job breakdown */}
                {r?.jobs?.length > 0 && (
                  <>
                    <h4 className="text-[13px] font-semibold text-gray-800 dark:text-gray-100">Jobs ({r.jobs.length})</h4>
                    <div className="flex flex-col gap-2 max-h-48 overflow-y-auto">
                      {r.jobs.map((job: any, i: number) => (
                        <div key={i} className="bg-gray-50 dark:bg-gray-700/20 rounded-lg border border-gray-100 dark:border-gray-700/30 p-3">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-[12px] font-medium text-gray-800 dark:text-gray-100">{job.label}</span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-medium ${job.side === 'pc1' ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700' : 'bg-purple-100 dark:bg-purple-900/30 text-purple-700'}`}>{job.side === 'pc1' ? 'PC-1' : 'PC-2'}</span>
                            <span className="text-[11px] text-green-600 ml-auto">✓ {job.created?.length ?? 0}</span>
                            {job.failed?.length > 0 && <span className="text-[11px] text-red-500">✗ {job.failed.length}</span>}
                          </div>
                          {job.created?.length > 0 && (
                            <p className="text-[11px] text-gray-500 font-mono truncate">{job.created.join(', ')}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </>
                )}

                {/* Duplicates & Conflicts */}
                {r?.duplicates?.length > 0 && (
                  <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/40 text-amber-700 dark:text-amber-300 text-[12px] rounded-lg px-3 py-2">
                    ⚠ {r.duplicates.length} duplicate{r.duplicates.length > 1 ? 's' : ''}: {r.duplicates.join(', ')}
                  </div>
                )}
                {r?.conflicts > 0 && (
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700/40 text-red-700 dark:text-red-300 text-[12px] rounded-lg px-3 py-2">
                    ✗ {r.conflicts} conflict{r.conflicts > 1 ? 's' : ''} detected
                  </div>
                )}

                <div className="text-[11px] text-gray-400 dark:text-gray-500">
                  {new Date(historyDetail.startedAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            )
          })()}
        </DialogContent>
      </Dialog>

      {/* Token dialog */}
      <SetTokenDialog
        open={tokenDialogOpenFor !== null}
        onClose={closeTokenDialog}
        erpToken={dialogToken}
        setErpToken={setDialogToken}
        erpTenantId={dialogTenantId}
        setErpTenantId={setDialogTenantId}
      />
    </div>
  )
}
