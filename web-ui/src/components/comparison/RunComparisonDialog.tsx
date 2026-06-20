'use client'

import { useState, useEffect, useMemo, useCallback } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Separator } from '@/components/ui/separator'
import {
  GitCompare,
  ArrowUp,
  ArrowDown,
  Minus,
  Plus,
  CheckCircle2,
  XCircle,
  Circle,
  AlertTriangle,
  Loader2,
  Bookmark,
  BookmarkCheck,
} from 'lucide-react'
import { fetchRunDetail, type RunHistoryItem } from '@/lib/api'
import type { RunSnapshot } from '@/lib/types'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

// ─── Types ────────────────────────────────────────────────────────────

interface RunComparisonDialogProps {
  open: boolean
  onClose: () => void
  runHistory: RunSnapshot[]
  currentModuleId?: string
}

type ChangeType = 'new-pass' | 'new-fail' | 'new-test' | 'removed' | 'unchanged'

interface DiffRow {
  testName: string
  displayName: string
  baseStatus: string | null
  compareStatus: string | null
  change: ChangeType
}

type FilterType = 'all' | 'changed' | 'new-passes' | 'new-fails' | 'new-tests'

// ─── ERP Colors ───────────────────────────────────────────────────────

const ERP_PRIMARY = '#3F51B5'
const ERP_SUCCESS = '#22C55E'
const ERP_DANGER = '#F44336'
const ERP_WARNING = '#FF9800'

// ─── Chart Colors ─────────────────────────────────────────────────────

const CHART_COLORS: Record<ChangeType, string> = {
  'new-pass': ERP_SUCCESS,
  'new-fail': ERP_DANGER,
  'new-test': '#3B82F6',
  'removed': '#9CA3AF',
  'unchanged': '#D1D5DB',
}

// ─── Helpers ──────────────────────────────────────────────────────────

function formatDuration(ms: number | null): string {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms}ms`
  const s = ms / 1000
  if (s < 60) return `${s.toFixed(1)}s`
  const m = Math.floor(s / 60)
  const rem = Math.round(s % 60)
  return `${m}m ${rem}s`
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  try {
    return new Date(dateStr).toLocaleString()
  } catch {
    return dateStr
  }
}

function passRate(passed: number, total: number): number {
  return total > 0 ? Math.round((passed / total) * 100) : 0
}

function statusIcon(status: string | null, size = 3.5) {
  const cls = `size-${size} shrink-0`
  switch (status) {
    case 'passed':
      return <CheckCircle2 className={`${cls} text-green-500`} />
    case 'failed':
      return <XCircle className={`${cls} text-red-500`} />
    case 'skipped':
      return <Circle className={`${cls} text-yellow-500`} />
    case 'error':
      return <AlertTriangle className={`${cls} text-orange-500`} />
    default:
      return <Circle className={`${cls} text-gray-300 dark:text-gray-600`} />
  }
}

function changeLabel(change: ChangeType): { icon: React.ReactNode; label: string; color: string } {
  switch (change) {
    case 'new-pass':
      return {
        icon: <ArrowUp className="size-3.5" />,
        label: 'New Pass',
        color: 'text-green-600 dark:text-green-400',
      }
    case 'new-fail':
      return {
        icon: <ArrowDown className="size-3.5" />,
        label: 'New Fail',
        color: 'text-red-600 dark:text-red-400',
      }
    case 'new-test':
      return {
        icon: <Plus className="size-3.5" />,
        label: 'New Test',
        color: 'text-blue-600 dark:text-blue-400',
      }
    case 'removed':
      return {
        icon: <Minus className="size-3.5" />,
        label: 'Removed',
        color: 'text-gray-500 dark:text-gray-400',
      }
    case 'unchanged':
      return {
        icon: <CheckCircle2 className="size-3.5" />,
        label: 'Unchanged',
        color: 'text-gray-400 dark:text-gray-500',
      }
  }
}

function rowHighlight(change: ChangeType): string {
  switch (change) {
    case 'new-pass':
      return 'bg-green-50 dark:bg-green-900/10'
    case 'new-fail':
      return 'bg-red-50 dark:bg-red-900/10'
    case 'new-test':
      return 'bg-blue-50 dark:bg-blue-900/10'
    case 'removed':
      return 'bg-gray-50 dark:bg-gray-800/30'
    case 'unchanged':
      return ''
  }
}

function changeSortOrder(change: ChangeType): number {
  switch (change) {
    case 'new-fail': return 0
    case 'new-pass': return 1
    case 'new-test': return 2
    case 'removed': return 3
    case 'unchanged': return 4
  }
}

// ─── Snapshot option label ────────────────────────────────────────────

function snapshotLabel(run: RunSnapshot): string {
  const rate = run.total > 0 ? Math.round((run.passed / run.total) * 100) : 0
  return `${run.date} · ${run.moduleId} · ${rate}% · ${run.duration}`
}

// ─── Component ────────────────────────────────────────────────────────

export default function RunComparisonDialog({
  open,
  onClose,
  runHistory,
  currentModuleId,
}: RunComparisonDialogProps) {
  // Selection state
  const [baseRunId, setBaseRunId] = useState<string>('')
  const [compareRunId, setCompareRunId] = useState<string>('')

  // Detail data
  const [baseDetail, setBaseDetail] = useState<RunHistoryItem | null>(null)
  const [compareDetail, setCompareDetail] = useState<RunHistoryItem | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Filter — default to 'changed' (shows regressions + fixes + new + removed)
  const [filter, setFilter] = useState<FilterType>('changed')

  // Filter runs by current module, then take most recent 20
  const moduleRuns = useMemo(
    () => currentModuleId ? runHistory.filter(r => r.moduleId === currentModuleId) : runHistory,
    [runHistory, currentModuleId]
  )
  const recentRuns = useMemo(() => moduleRuns.slice(0, 20), [moduleRuns])

  // Fetch details when both selected
  useEffect(() => {
    if (!open || !baseRunId || !compareRunId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setBaseDetail(null)
      setCompareDetail(null)
      setError(null)
      return
    }
    if (baseRunId === compareRunId) return

    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      setBaseDetail(null)
      setCompareDetail(null)
      try {
        const [b, c] = await Promise.all([
          fetchRunDetail(baseRunId),
          fetchRunDetail(compareRunId),
        ])
        if (!cancelled) {
          setBaseDetail(b)
          setCompareDetail(c)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load run details')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [open, baseRunId, compareRunId])

  // Reset selection when dialog closes
  useEffect(() => {
    if (!open) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setBaseRunId('')
      setCompareRunId('')
      setBaseDetail(null)
      setCompareDetail(null)
      setError(null)
      setFilter('changed')
    }
  }, [open])

  // Smart defaults: auto-select latest 2 runs for this module on open
  useEffect(() => {
    if (!open) return
    if (moduleRuns.length < 2) return
    // Don't override if user already made a selection
    if (baseRunId || compareRunId) return

    const savedBaseline = currentModuleId
      ? localStorage.getItem(`baseline_${currentModuleId}`)
      : null

    if (savedBaseline && moduleRuns.some(r => r.id === savedBaseline)) {
      setBaseRunId(savedBaseline)
      setCompareRunId(moduleRuns[0].id)
    } else {
      setBaseRunId(moduleRuns[1].id)
      setCompareRunId(moduleRuns[0].id)
    }
  }, [open, moduleRuns, currentModuleId])

  // Baseline management
  const handleSetBaseline = useCallback(() => {
    if (!currentModuleId || !compareRunId) return
    localStorage.setItem(`baseline_${currentModuleId}`, compareRunId)
    // Show a brief indicator — the icon in the button will update
  }, [currentModuleId, compareRunId])

  const savedBaselineId = currentModuleId
    ? localStorage.getItem(`baseline_${currentModuleId}`)
    : null

  const isBaseline = savedBaselineId === compareRunId

  // Build diff rows
  const diffRows = useMemo<DiffRow[]>(() => {
    if (!baseDetail || !compareDetail) return []

    type TestResult = { testId: string; status: string; message?: string; duration?: number }
    const baseMap = new Map<string, TestResult>()
    const compareMap = new Map<string, TestResult>()

    const baseResults = Array.isArray(baseDetail.results) ? baseDetail.results : []
    const compareResults = Array.isArray(compareDetail.results) ? compareDetail.results : []
    for (const r of baseResults) {
      const key = r.testId || r.name || ''
      baseMap.set(key, r as TestResult)
    }
    for (const r of compareResults) {
      const key = r.testId || r.name || ''
      compareMap.set(key, r as TestResult)
    }

    const allNames = new Set([...baseMap.keys(), ...compareMap.keys()])
    const rows: DiffRow[] = []

    for (const name of allNames) {
      const inBase = baseMap.get(name)
      const inCompare = compareMap.get(name)

      let change: ChangeType
      if (inBase && inCompare) {
        if (inBase.status === 'failed' && inCompare.status === 'passed') {
          change = 'new-pass'
        } else if (inBase.status === 'passed' && inCompare.status === 'failed') {
          change = 'new-fail'
        } else {
          change = 'unchanged'
        }
      } else if (!inBase && inCompare) {
        change = 'new-test'
      } else {
        change = 'removed'
      }

      rows.push({
        testName: name,
        displayName: name.split('::').pop() || name,
        baseStatus: inBase?.status ?? null,
        compareStatus: inCompare?.status ?? null,
        change,
      })
    }

    // Sort: changed first, then new, then unchanged
    rows.sort((a, b) => {
      const ordDiff = changeSortOrder(a.change) - changeSortOrder(b.change)
      if (ordDiff !== 0) return ordDiff
      return a.displayName.localeCompare(b.displayName)
    })

    return rows
  }, [baseDetail, compareDetail])

  // Filtered rows
  const filteredRows = useMemo(() => {
    switch (filter) {
      case 'changed':
        return diffRows.filter((r) => r.change !== 'unchanged')
      case 'new-passes':
        return diffRows.filter((r) => r.change === 'new-pass')
      case 'new-fails':
        return diffRows.filter((r) => r.change === 'new-fail')
      case 'new-tests':
        return diffRows.filter((r) => r.change === 'new-test')
      default:
        return diffRows
    }
  }, [diffRows, filter])

  // Stats for chart
  const chartStats = useMemo(() => {
    const counts: Record<ChangeType, number> = {
      'new-pass': 0,
      'new-fail': 0,
      'new-test': 0,
      'removed': 0,
      'unchanged': 0,
    }
    for (const r of diffRows) {
      counts[r.change]++
    }
    return counts
  }, [diffRows])

  const chartData = useMemo(
    () =>
      (Object.entries(chartStats) as [ChangeType, number][])
        .filter(([, v]) => v > 0)
        .map(([name, value]) => ({ name, value })),
    [chartStats]
  )

  // Summary delta
  const summaryDelta = useMemo(() => {
    if (!baseDetail || !compareDetail) return null

    const baseRate = passRate(baseDetail.passed, baseDetail.total)
    const compareRate = passRate(compareDetail.passed, compareDetail.total)
    const deltaPassed = compareDetail.passed - baseDetail.passed
    const deltaFailed = compareDetail.failed - baseDetail.failed
    const deltaRate = compareRate - baseRate

    return { deltaPassed, deltaFailed, deltaRate, baseRate, compareRate }
  }, [baseDetail, compareDetail])

  // Filter counts for tabs
  const filterCounts = useMemo(() => {
    const counts: Record<FilterType, number> = {
      all: diffRows.length,
      changed: diffRows.filter((r) => r.change !== 'unchanged').length,
      'new-passes': diffRows.filter((r) => r.change === 'new-pass').length,
      'new-fails': diffRows.filter((r) => r.change === 'new-fail').length,
      'new-tests': diffRows.filter((r) => r.change === 'new-test').length,
    }
    return counts
  }, [diffRows])

  // Format filter label
  const filterLabel = useCallback(
    (f: FilterType): string => {
      const labels: Record<FilterType, string> = {
        all: 'All',
        changed: 'Changed',
        'new-passes': 'New Passes',
        'new-fails': 'New Fails',
        'new-tests': 'New Tests',
      }
      return `${labels[f]} (${filterCounts[f]})`
    },
    [filterCounts]
  )

  // Run snapshots lookup for selection display
  const runMap = useMemo(() => {
    const m = new Map<string, RunSnapshot>()
    for (const r of recentRuns) m.set(r.id, r)
    return m
  }, [recentRuns])

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-[960px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitCompare className="size-5 text-[#3F51B5]" />
            Regression Check
          </DialogTitle>
          <DialogDescription className="text-[13px] text-gray-500 dark:text-gray-400">
            Select a baseline and target run to detect regressions, fixes, and changes
          </DialogDescription>
        </DialogHeader>

        {/* Step 1: Select Runs */}
        <div className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Baseline Run Selector */}
            <div className="space-y-1.5">
              <label className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wide flex items-center gap-1">
                <BookmarkCheck className="size-3 text-indigo-400" />
                Baseline Run
              </label>
              <Select value={baseRunId} onValueChange={setBaseRunId}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select baseline..." />
                </SelectTrigger>
                <SelectContent>
                  {recentRuns.map((run) => (
                    <SelectItem
                      key={run.id}
                      value={run.id}
                      disabled={run.id === compareRunId}
                    >
                      <span className="truncate">{snapshotLabel(run)}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {baseRunId && runMap.get(baseRunId) && (
                <div className="text-[11px] text-gray-500 dark:text-gray-400 flex items-center gap-2">
                  <span>{runMap.get(baseRunId)!.total} tests</span>
                  <span>·</span>
                  <span className="text-green-600 dark:text-green-400">
                    {runMap.get(baseRunId)!.passed} passed
                  </span>
                  <span>·</span>
                  <span className="text-red-600 dark:text-red-400">
                    {runMap.get(baseRunId)!.failed} failed
                  </span>
                </div>
              )}
            </div>

            {/* Target Run Selector */}
            <div className="space-y-1.5">
              <label className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wide">
                Target Run
              </label>
              <Select value={compareRunId} onValueChange={setCompareRunId}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select target..." />
                </SelectTrigger>
                <SelectContent>
                  {recentRuns.map((run) => (
                    <SelectItem
                      key={run.id}
                      value={run.id}
                      disabled={run.id === baseRunId}
                    >
                      <span className="truncate">{snapshotLabel(run)}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {compareRunId && runMap.get(compareRunId) && (
                <div className="text-[11px] text-gray-500 dark:text-gray-400 flex items-center gap-2">
                  <span>{runMap.get(compareRunId)!.total} tests</span>
                  <span>·</span>
                  <span className="text-green-600 dark:text-green-400">
                    {runMap.get(compareRunId)!.passed} passed
                  </span>
                  <span>·</span>
                  <span className="text-red-600 dark:text-red-400">
                    {runMap.get(compareRunId)!.failed} failed
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Quick compare buttons */}
          {moduleRuns.length >= 2 && (
            <div className="flex flex-wrap gap-1.5">
              <Button
                variant="ghost"
                size="sm"
                className="text-[11px] h-6 text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 cursor-pointer"
                onClick={() => {
                  setBaseRunId(moduleRuns[1].id)
                  setCompareRunId(moduleRuns[0].id)
                }}
              >
                Latest vs Previous
              </Button>
              {savedBaselineId && moduleRuns.some(r => r.id === savedBaselineId) && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-[11px] h-6 text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 cursor-pointer"
                  onClick={() => {
                    setBaseRunId(savedBaselineId)
                    setCompareRunId(moduleRuns[0].id)
                  }}
                >
                  Latest vs Baseline
                </Button>
              )}
            </div>
          )}
        </div>

        {/* Same run warning */}
        {baseRunId && compareRunId && baseRunId === compareRunId && (
          <div className="flex items-center gap-2 text-[12px] text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/10 rounded-md px-3 py-2">
            <AlertTriangle className="size-4 shrink-0" />
            Base and Compare runs must be different
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="size-5 text-[#3F51B5] animate-spin" />
            <span className="ml-2 text-[13px] text-gray-500 dark:text-gray-400">
              Loading run details...
            </span>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="flex items-center gap-2 text-[12px] text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/10 rounded-md px-3 py-2">
            <AlertTriangle className="size-4 shrink-0" />
            {error}
          </div>
        )}

        {/* Step 2 & 3: Comparison Results */}
        {baseDetail && compareDetail && summaryDelta && !loading && (
          <>
            <Separator />

            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              {/* Baseline Card */}
              <div className="rounded-lg border border-gray-300 dark:border-gray-500/70 bg-gray-50 dark:bg-gray-800/50 p-4">
                <div className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2 flex items-center gap-1">
                  <BookmarkCheck className="size-3" />
                  Baseline
                </div>
                <div className="text-[13px] text-gray-700 dark:text-gray-200 font-medium">
                  {formatDate(baseDetail.startedAt)}
                </div>
                <div className="grid grid-cols-3 gap-2 mt-2">
                  <div className="text-center">
                    <div className="text-[11px] text-gray-400 dark:text-gray-500">Total</div>
                    <div className="text-[14px] font-bold text-gray-800 dark:text-gray-100">
                      {baseDetail.total}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-[11px] text-gray-400 dark:text-gray-500">Passed</div>
                    <div className="text-[14px] font-bold text-green-600 dark:text-green-400">
                      {baseDetail.passed}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-[11px] text-gray-400 dark:text-gray-500">Failed</div>
                    <div className="text-[14px] font-bold text-red-600 dark:text-red-400">
                      {baseDetail.failed}
                    </div>
                  </div>
                </div>
                <div className="mt-2 text-center">
                  <div className="text-[11px] text-gray-400 dark:text-gray-500">Pass Rate</div>
                  <div
                    className={`text-[16px] font-bold ${
                      summaryDelta.baseRate >= 90
                        ? 'text-green-600 dark:text-green-400'
                        : summaryDelta.baseRate >= 75
                          ? 'text-yellow-600 dark:text-yellow-400'
                          : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {summaryDelta.baseRate}%
                  </div>
                </div>
              </div>

              {/* Target Card */}
              <div className="rounded-lg border border-gray-300 dark:border-gray-500/70 bg-gray-50 dark:bg-gray-800/50 p-4">
                <div className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                  Target
                </div>
                <div className="text-[13px] text-gray-700 dark:text-gray-200 font-medium">
                  {formatDate(compareDetail.startedAt)}
                </div>
                <div className="grid grid-cols-3 gap-2 mt-2">
                  <div className="text-center">
                    <div className="text-[11px] text-gray-400 dark:text-gray-500">Total</div>
                    <div className="text-[14px] font-bold text-gray-800 dark:text-gray-100">
                      {compareDetail.total}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-[11px] text-gray-400 dark:text-gray-500">Passed</div>
                    <div className="text-[14px] font-bold text-green-600 dark:text-green-400">
                      {compareDetail.passed}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-[11px] text-gray-400 dark:text-gray-500">Failed</div>
                    <div className="text-[14px] font-bold text-red-600 dark:text-red-400">
                      {compareDetail.failed}
                    </div>
                  </div>
                </div>
                <div className="mt-2 text-center">
                  <div className="text-[11px] text-gray-400 dark:text-gray-500">Pass Rate</div>
                  <div
                    className={`text-[16px] font-bold ${
                      summaryDelta.compareRate >= 90
                        ? 'text-green-600 dark:text-green-400'
                        : summaryDelta.compareRate >= 75
                          ? 'text-yellow-600 dark:text-yellow-400'
                          : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {summaryDelta.compareRate}%
                  </div>
                </div>
              </div>

              {/* Regression Card */}
              <div className="rounded-lg border border-red-200 dark:border-red-800/50 bg-red-50 dark:bg-red-900/10 p-4">
                <div className="text-[11px] font-semibold text-red-600 dark:text-red-400 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                  <ArrowDown className="size-3" />
                  Regressions
                </div>
                <div className="text-[28px] font-bold text-red-600 dark:text-red-400">
                  {chartStats['new-fail']}
                </div>
                <div className="text-[11px] text-red-500/70 dark:text-red-400/70 mt-0.5">
                  previously passed, now failed
                </div>
              </div>

              {/* Fix Card */}
              <div className="rounded-lg border border-green-200 dark:border-green-800/50 bg-green-50 dark:bg-green-900/10 p-4">
                <div className="text-[11px] font-semibold text-green-600 dark:text-green-400 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                  <ArrowUp className="size-3" />
                  Fixes
                </div>
                <div className="text-[28px] font-bold text-green-600 dark:text-green-400">
                  {chartStats['new-pass']}
                </div>
                <div className="text-[11px] text-green-500/70 dark:text-green-400/70 mt-0.5">
                  previously failed, now passed
                </div>
              </div>
            </div>

            {/* Visual Statistics: Donut Chart + Progress Bars */}
            {diffRows.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Donut Chart */}
                <div className="rounded-lg border border-gray-300 dark:border-gray-500/70 p-4">
                  <div className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wide mb-3">
                    Change Distribution
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-[140px] h-[140px] shrink-0">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={chartData}
                            cx="50%"
                            cy="50%"
                            innerRadius={35}
                            outerRadius={60}
                            paddingAngle={2}
                            dataKey="value"
                            stroke="none"
                          >
                            {chartData.map((entry) => (
                              <Cell
                                key={entry.name}
                                fill={CHART_COLORS[entry.name as ChangeType]}
                              />
                            ))}
                          </Pie>
                          <Tooltip
                            formatter={(value: number, name: string) => {
                              const labels: Record<string, string> = {
                                'new-pass': 'New Passes',
                                'new-fail': 'New Fails',
                                'new-test': 'New Tests',
                                'removed': 'Removed',
                                'unchanged': 'Unchanged',
                              }
                              return [`${value} test${value !== 1 ? 's' : ''}`, labels[name] || name]
                            }}
                            contentStyle={{
                              fontSize: 12,
                              borderRadius: 8,
                              border: '1px solid #e5e7eb',
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="flex-1 space-y-1.5 min-w-0">
                      {(['new-pass', 'new-fail', 'new-test', 'removed', 'unchanged'] as ChangeType[]).map(
                        (ct) => {
                          const info = changeLabel(ct)
                          const count = chartStats[ct]
                          const pct = diffRows.length > 0 ? (count / diffRows.length) * 100 : 0
                          return (
                            <div key={ct} className="flex items-center gap-2">
                              <div
                                className="w-2.5 h-2.5 rounded-full shrink-0"
                                style={{ backgroundColor: CHART_COLORS[ct] }}
                              />
                              <span className={`text-[11px] ${info.color} flex-1 truncate`}>
                                {info.label}
                              </span>
                              <span className="text-[11px] text-gray-500 dark:text-gray-400 font-mono">
                                {count}
                              </span>
                              <div className="w-16 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                                <div
                                  className="h-full rounded-full transition-all"
                                  style={{
                                    width: `${pct}%`,
                                    backgroundColor: CHART_COLORS[ct],
                                  }}
                                />
                              </div>
                            </div>
                          )
                        }
                      )}
                    </div>
                  </div>
                </div>

                {/* Summary Progress Bars */}
                <div className="rounded-lg border border-gray-300 dark:border-gray-500/70 p-4">
                  <div className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wide mb-3">
                    Test Outcomes
                  </div>
                  <div className="space-y-3">
                    {/* New Passes bar */}
                    {chartStats['new-pass'] > 0 && (
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[11px] text-green-600 dark:text-green-400 font-medium flex items-center gap-1">
                            <ArrowUp className="size-3" /> New Passes
                          </span>
                          <span className="text-[11px] text-gray-500 dark:text-gray-400">
                            {chartStats['new-pass']}
                          </span>
                        </div>
                        <div className="w-full h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full bg-green-500"
                            style={{
                              width: `${(chartStats['new-pass'] / diffRows.length) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    )}
                    {/* New Fails bar */}
                    {chartStats['new-fail'] > 0 && (
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[11px] text-red-600 dark:text-red-400 font-medium flex items-center gap-1">
                            <ArrowDown className="size-3" /> New Fails
                          </span>
                          <span className="text-[11px] text-gray-500 dark:text-gray-400">
                            {chartStats['new-fail']}
                          </span>
                        </div>
                        <div className="w-full h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full bg-red-500"
                            style={{
                              width: `${(chartStats['new-fail'] / diffRows.length) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    )}
                    {/* New Tests bar */}
                    {chartStats['new-test'] > 0 && (
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[11px] text-blue-600 dark:text-blue-400 font-medium flex items-center gap-1">
                            <Plus className="size-3" /> New Tests
                          </span>
                          <span className="text-[11px] text-gray-500 dark:text-gray-400">
                            {chartStats['new-test']}
                          </span>
                        </div>
                        <div className="w-full h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full bg-blue-500"
                            style={{
                              width: `${(chartStats['new-test'] / diffRows.length) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    )}
                    {/* Removed bar */}
                    {chartStats['removed'] > 0 && (
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[11px] text-gray-500 dark:text-gray-400 font-medium flex items-center gap-1">
                            <Minus className="size-3" /> Removed
                          </span>
                          <span className="text-[11px] text-gray-500 dark:text-gray-400">
                            {chartStats['removed']}
                          </span>
                        </div>
                        <div className="w-full h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full bg-gray-400"
                            style={{
                              width: `${(chartStats['removed'] / diffRows.length) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    )}
                    {/* If no changes */}
                    {chartStats['unchanged'] === diffRows.length && (
                      <div className="text-center py-4 text-[12px] text-gray-400 dark:text-gray-500">
                        <CheckCircle2 className="size-5 mx-auto mb-1 text-green-400" />
                        No changes detected between runs
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            <Separator />

            {/* Filter Tabs */}
            <div className="flex flex-wrap gap-1.5">
              {(
                ['all', 'changed', 'new-passes', 'new-fails', 'new-tests'] as FilterType[]
              ).map((f) => (
                <Button
                  key={f}
                  variant={filter === f ? 'default' : 'outline'}
                  size="sm"
                  className={`text-[11px] h-7 cursor-pointer ${
                    filter === f
                      ? 'bg-[#3F51B5] hover:bg-[#3F51B5]/90 text-white'
                      : ''
                  }`}
                  onClick={() => setFilter(f)}
                >
                  {filterLabel(f)}
                </Button>
              ))}
            </div>

            {/* Diff Table */}
            {filteredRows.length === 0 ? (
              <div className="text-center py-8 text-[12px] text-gray-400 dark:text-gray-500">
                No tests match the current filter
              </div>
            ) : (
              <div className="border border-gray-300 dark:border-gray-500/70 rounded-lg overflow-hidden max-h-[400px] overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-[#DFE9FB] dark:bg-indigo-900/30 hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
                      <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">
                        Test Name
                      </TableHead>
                      <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-28 text-center">
                        Base Status
                      </TableHead>
                      <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-28 text-center">
                        Compare Status
                      </TableHead>
                      <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-28 text-center">
                        Change
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredRows.map((row) => {
                      const info = changeLabel(row.change)
                      return (
                        <TableRow
                          key={row.testName}
                          className={`dark:border-gray-700 ${rowHighlight(row.change)}`}
                        >
                          <TableCell className="text-[12px]">
                            <div className="font-mono text-gray-500 dark:text-gray-400 text-[10px] truncate max-w-[300px]">
                              {row.testName}
                            </div>
                            <div className="text-gray-700 dark:text-gray-200 truncate max-w-[300px]">
                              {row.displayName}
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            {row.baseStatus ? (
                              <Badge
                                variant="outline"
                                className={`text-[10px] ${
                                  row.baseStatus === 'passed'
                                    ? 'text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                                    : row.baseStatus === 'failed'
                                      ? 'text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                                      : 'text-yellow-700 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
                                }`}
                              >
                                {statusIcon(row.baseStatus, 3)}
                                {row.baseStatus}
                              </Badge>
                            ) : (
                              <span className="text-[11px] text-gray-400 dark:text-gray-500">—</span>
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            {row.compareStatus ? (
                              <Badge
                                variant="outline"
                                className={`text-[10px] ${
                                  row.compareStatus === 'passed'
                                    ? 'text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                                    : row.compareStatus === 'failed'
                                      ? 'text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                                      : 'text-yellow-700 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
                                }`}
                              >
                                {statusIcon(row.compareStatus, 3)}
                                {row.compareStatus}
                              </Badge>
                            ) : (
                              <span className="text-[11px] text-gray-400 dark:text-gray-500">—</span>
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            <span
                              className={`text-[11px] font-medium flex items-center justify-center gap-1 ${info.color}`}
                            >
                              {info.icon}
                              {info.label}
                            </span>
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </>
        )}

        {/* Empty state when no runs selected */}
        {!baseRunId && !compareRunId && !loading && (
          <div className="text-center py-8">
            <GitCompare className="size-8 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
            <p className="text-[13px] text-gray-400 dark:text-gray-500">
              Select a Baseline and a Target run to start regression check
            </p>
          </div>
        )}

        {/* Partial selection state */}
        {((baseRunId && !compareRunId) || (!baseRunId && compareRunId)) &&
          !loading && (
            <div className="text-center py-4">
              <p className="text-[13px] text-gray-400 dark:text-gray-500">
                Select {!baseRunId ? 'a Baseline run' : 'a Target run'} to continue
              </p>
            </div>
          )}

        <DialogFooter className="flex items-center justify-between sm:justify-between">
          <div className="flex items-center gap-2">
            {compareRunId && currentModuleId && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSetBaseline}
                className={`text-[12px] gap-1.5 cursor-pointer ${
                  isBaseline
                    ? 'text-indigo-600 dark:text-indigo-400'
                    : 'text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400'
                }`}
              >
                {isBaseline ? (
                  <BookmarkCheck className="size-3.5" />
                ) : (
                  <Bookmark className="size-3.5" />
                )}
                {isBaseline ? 'Saved as Baseline' : 'Set as Baseline'}
              </Button>
            )}
          </div>
          <Button variant="outline" onClick={onClose} className="cursor-pointer">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
