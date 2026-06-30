'use client'

import React, { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { Plus, Share2, Play, BadgeCheck, Key, Check, X, Box, Monitor } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { SetTokenDialog } from '@/components/dialogs/SetTokenDialog'
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
  const [coords, setCoords] = useState<{ top: number; left: number; width: number } | null>(null)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) { setOpen(false); setActiveGroup(null) }
    }
    if (open) document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  useEffect(() => {
    if (!open || !ref.current) return
    const r = ref.current.getBoundingClientRect()
    const dropW = 480
    const left = Math.max(8, Math.min(r.left + r.width / 2 - dropW / 2, window.innerWidth - dropW - 8))
    setCoords({ top: r.bottom + 4, left, width: r.width })
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
          style={{ position: 'fixed', top: coords.top, left: coords.left, width: 480, zIndex: 9999 }}
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
            <div>
              <div className="flex items-center gap-2 px-3 pt-2.5 pb-2 border-b border-gray-100 dark:border-gray-700">
                <button
                  type="button"
                  onClick={() => setActiveGroup(null)}
                  className="text-[12px] text-[#3F51B5] dark:text-[#7986CB] hover:underline cursor-pointer shrink-0 font-medium"
                >
                  ← Back
                </button>
                <span className="text-[12px] text-gray-400 dark:text-gray-500 truncate">{activeGroup}</span>
              </div>
              <div className="py-1 max-h-52 overflow-y-auto">
                {children.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => { onChange(m.id); setOpen(false); setActiveGroup(null) }}
                    className={`w-full text-left px-3 py-2 text-[13px] transition-colors ${
                      m.id === value
                        ? 'bg-[#3F51B5]/10 text-[#3F51B5] dark:text-[#7986CB] font-medium'
                        : 'text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50'
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
    for (const t of pc1Tenants) { if (!t.token || !t.tenantId || !t.moduleId) return false }
    for (const e of pc2Entries) {
      if (!e.token || !e.tenantId) return false
      if (e.kind === 'independent' && !e.moduleId) return false
    }
    return true
  }, [pc1Tenants, pc2Entries])

  const handleRun = useCallback(() => {
    console.log('RUN', { mode, pc1: pc1Tenants, pc2: pc2Entries })
  }, [mode, pc1Tenants, pc2Entries])

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

      {/* Top bar */}
      <div className="shrink-0 flex items-center justify-between px-5 py-3 border-b border-gray-200 dark:border-gray-700/50 bg-white dark:bg-gray-900">
        <div className="flex items-center gap-5">
          <span className="text-[13px] font-semibold text-gray-600 dark:text-gray-300">Mode</span>
          {(['api', 'ui'] as const).map((m) => (
            <label key={m} className="flex items-center gap-2 text-[13px] cursor-pointer">
              <input type="radio" name="conc-mode" value={m} checked={mode === m} onChange={() => setMode(m)} className="accent-[#3F51B5]" />
              <span className="text-gray-700 dark:text-gray-300 uppercase font-medium">{m}</span>
            </label>
          ))}
        </div>
        <div className="flex items-center gap-3">
          {confirmReset ? (
            <div className="flex items-center gap-2">
              <span className="text-[12px] text-gray-500 dark:text-gray-400">Reset everything?</span>
              <button onClick={resetWizard} className="text-[12px] font-medium text-red-500 hover:text-red-600 cursor-pointer px-2 py-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">Yes, reset</button>
              <button onClick={() => setConfirmReset(false)} className="text-[12px] text-gray-400 hover:text-gray-600 cursor-pointer px-2 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors">Cancel</button>
            </div>
          ) : (
            <button onClick={resetWizard} className="text-[13px] text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors cursor-pointer px-3 py-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 border border-transparent hover:border-gray-200 dark:hover:border-gray-700">
              Edit Setup
            </button>
          )}
          <Button onClick={handleRun} disabled={!canRun} title={!canRun ? 'All tenants need a token, tenant ID, and module' : 'Backend wiring coming soon'} className="h-9 px-4 text-[13px] gap-2 cursor-pointer">
            <Play className="size-4" />
            Run
          </Button>
        </div>
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
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

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
