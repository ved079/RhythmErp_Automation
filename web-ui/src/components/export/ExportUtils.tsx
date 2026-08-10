'use client'

import React, { useState, useCallback } from 'react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import {
  Download,
  FileSpreadsheet,
  FileText,
  Printer,
  Copy,
  CheckCircle2,
} from 'lucide-react'
import Spinner from '@/components/ui/Spinner'
import { toast } from 'sonner'
import type { TestClassGroup, RunSnapshot, ModuleHealth } from '@/lib/types'
import type { BugReport } from '@/lib/bug-reports'
import { getSLADeadline } from '@/lib/bug-reports'

// ─── ERP Color Constants ──────────────────────────────────
const ERP_BLUE = '3F51B5'
const ERP_BLUE_HEX = '#3F51B5'
const STATUS_COLORS: Record<string, string> = {
  passed: '4CAF50',
  failed: 'F44336',
  bug: 'FF9800',
  todo: '9E9E9E',
  'not-run': 'E0E0E0',
}
const PRIORITY_COLORS: Record<string, string> = {
  high: 'F44336',
  medium: 'FF9800',
  low: '4CAF50',
}

// ─── Helpers ──────────────────────────────────────────────
function formatDateEN(date: Date): string {
  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).replace(/\//g, '-')
}

function formatDateENLong(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function formatDateTimeEN(dateStr: string): string {
  return new Date(dateStr).toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function autoSizeColumns(ws: unknown, minWidth = 10, maxWidth = 50): void {
  const worksheet = ws as { columns?: Array<{ width?: number }> & Record<string, unknown> }
  if (!worksheet['!cols']) return
  const cols = worksheet['!cols'] as Array<{ wch?: number }>
  for (let i = 0; i < cols.length; i++) {
    const w = cols[i]?.wch ?? minWidth
    cols[i] = { wch: Math.min(Math.max(w, minWidth), maxWidth) }
  }
}

function setHeaderStyle(ws: unknown, colCount: number): void {
  const worksheet = ws as Record<string, unknown>
  for (let c = 0; c < colCount; c++) {
    const cellRef = `${String.fromCharCode(65 + c)}1`
    const cell = worksheet[cellRef] as Record<string, unknown> | undefined
    if (cell) {
      cell.s = {
        fill: { fgColor: { rgb: ERP_BLUE } },
        font: { bold: true, color: { rgb: 'FFFFFF' }, sz: 11 },
        alignment: { horizontal: 'center', vertical: 'center' },
      }
    }
  }
}

function setStatusCellColor(cell: Record<string, unknown>, status: string, colorMap: Record<string, string>): void {
  const rgb = colorMap[status]
  if (rgb) {
    cell.s = {
      ...(cell.s as Record<string, unknown> || {}),
      fill: { fgColor: { rgb } },
      font: { color: { rgb: 'FFFFFF' }, bold: true, sz: 10 },
      alignment: { horizontal: 'center' },
    }
  }
}

function setPassRateCellColor(cell: Record<string, unknown>, rate: number): void {
  const rgb = rate >= 80 ? '4CAF50' : rate >= 50 ? 'FF9800' : 'F44336'
  cell.s = {
    ...(cell.s as Record<string, unknown> || {}),
    fill: { fgColor: { rgb } },
    font: { color: { rgb: 'FFFFFF' }, bold: true },
    alignment: { horizontal: 'center' },
  }
}

function triggerDownload(workbook: unknown, fileName: string): void {
  const XLSX = window.XLSX as unknown as { writeFile: (wb: unknown, name: string) => void }
  XLSX.writeFile(workbook, fileName)
}

// ─── 1. Export Test Results to Excel ──────────────────────
export async function exportTestResultsToExcel(
  testGroups: TestClassGroup[],
  moduleName: string
): Promise<void> {
  try {
    const XLSX = await import('xlsx')
    // Store on window for triggerDownload
    ;(window as unknown as Record<string, unknown>).XLSX = XLSX

    const wb = XLSX.utils.book_new()

    // Sheet 1: Test Specifications
    const allTests = testGroups.flatMap((g) => g.tests)
    const specData = allTests.map((t) => ({
      ID: t.id,
      'Screen Name': t.screenName || '—',
      Description: t.description,
      Status: t.status.toUpperCase(),
      Steps: t.steps,
      Expected: t.expected,
      Actual: t.actual,
      Priority: t.priority ? t.priority.charAt(0).toUpperCase() + t.priority.slice(1) : '—',
      Date: t.date ? formatDateENLong(t.date) : '—',
    }))

    const ws1 = XLSX.utils.json_to_sheet(specData)
    const colCount1 = 9
    setHeaderStyle(ws1, colCount1)

    // Status conditional formatting
    specData.forEach((_, idx) => {
      const row = idx + 2 // 1-indexed, row 1 is header
      const cellRef = `D${row}`
      const cell = (ws1 as Record<string, unknown>)[cellRef] as Record<string, unknown> | undefined
      if (cell) {
        const status = allTests[idx].status
        setStatusCellColor(cell, status, STATUS_COLORS)
      }
    })

    // Auto-size columns
    ws1['!cols'] = Array.from({ length: colCount1 }, () => ({ wch: 15 }))
    autoSizeColumns(ws1)

    XLSX.utils.book_append_sheet(wb, ws1, 'Test Specifications')

    // Sheet 2: Summary
    const statusCounts: Record<string, number> = {
      passed: 0,
      failed: 0,
      bug: 0,
      todo: 0,
      'not-run': 0,
    }
    allTests.forEach((t) => {
      if (statusCounts[t.status] !== undefined) statusCounts[t.status]++
    })
    const totalTests = allTests.length
    const passRate = totalTests > 0 ? ((statusCounts.passed / totalTests) * 100).toFixed(1) : '0.0'

    const summaryData = [
      { Status: 'Passed', Count: statusCounts.passed },
      { Status: 'Failed', Count: statusCounts.failed },
      { Status: 'Bug', Count: statusCounts.bug },
      { Status: 'To Do', Count: statusCounts.todo },
      { Status: 'Not Run', Count: statusCounts['not-run'] },
      { Status: 'TOTAL', Count: totalTests },
      { Status: 'Pass Rate', Count: `${passRate}%` },
    ]

    const ws2 = XLSX.utils.json_to_sheet(summaryData)
    setHeaderStyle(ws2, 2)
    ws2['!cols'] = [{ wch: 15 }, { wch: 12 }]
    XLSX.utils.book_append_sheet(wb, ws2, 'Summary')

    const date = formatDateEN(new Date())
    const fileName = `RhythmERP_TestResults_${moduleName}_${date}.xlsx`
    triggerDownload(wb, fileName)

    toast.success('Test results exported', {
      description: `${fileName} downloaded successfully`,
    })
  } catch (error) {
    console.error('Export test results error:', error)
    toast.error('Export failed', {
      description: 'Could not export test results to Excel',
    })
  }
}

// ─── 2. Export Run History to Excel ───────────────────────
export async function exportRunHistoryToExcel(runs: RunSnapshot[]): Promise<void> {
  try {
    const XLSX = await import('xlsx')
    ;(window as unknown as Record<string, unknown>).XLSX = XLSX

    const wb = XLSX.utils.book_new()

    // Sheet 1: Run History
    const historyData = runs.map((r) => ({
      Date: formatDateENLong(r.date),
      Module: r.moduleId,
      Total: r.total,
      Passed: r.passed,
      Failed: r.failed,
      'Pass Rate': `${r.rate.toFixed(1)}%`,
      Duration: r.duration,
    }))

    const ws1 = XLSX.utils.json_to_sheet(historyData)
    const colCount1 = 7
    setHeaderStyle(ws1, colCount1)

    // Pass rate conditional formatting
    runs.forEach((r, idx) => {
      const row = idx + 2
      const cellRef = `F${row}`
      const cell = (ws1 as Record<string, unknown>)[cellRef] as Record<string, unknown> | undefined
      if (cell) {
        setPassRateCellColor(cell, r.rate)
      }
    })

    ws1['!cols'] = Array.from({ length: colCount1 }, () => ({ wch: 15 }))
    autoSizeColumns(ws1)
    XLSX.utils.book_append_sheet(wb, ws1, 'Run History')

    // Sheet 2: Trend Analysis
    const moduleMap = new Map<string, RunSnapshot[]>()
    runs.forEach((r) => {
      const existing = moduleMap.get(r.moduleId) || []
      existing.push(r)
      moduleMap.set(r.moduleId, existing)
    })

    const trendData: Array<Record<string, string | number>> = []
    moduleMap.forEach((moduleRuns, moduleId) => {
      const sorted = [...moduleRuns].sort(
        (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
      )
      const last5 = sorted.slice(-5)
      const avgRate =
        last5.length > 0
          ? (last5.reduce((sum, r) => sum + r.rate, 0) / last5.length).toFixed(1)
          : '0.0'
      const avgDuration = last5.length > 0
        ? last5.reduce((sum, r) => sum + parseDuration(r.duration), 0) / last5.length
        : 0
      const totalPassed = sorted.reduce((s, r) => s + r.passed, 0)
      const totalFailed = sorted.reduce((s, r) => s + r.failed, 0)
      const totalTests = sorted.reduce((s, r) => s + r.total, 0)

      trendData.push({
        Module: moduleId,
        'Total Runs': sorted.length,
        'Total Tests': totalTests,
        'Total Passed': totalPassed,
        'Total Failed': totalFailed,
        'Last 5 Avg Rate': `${avgRate}%`,
        'Last 5 Avg Duration (s)': Math.round(avgDuration),
        'Last Run': sorted.length > 0 ? formatDateENLong(sorted[sorted.length - 1].date) : '—',
        Trend:
          sorted.length >= 2
            ? sorted[sorted.length - 1].rate >= sorted[0].rate
              ? 'Improving'
              : 'Declining'
            : '—',
      })
    })

    const ws2 = XLSX.utils.json_to_sheet(trendData)
    const colCount2 = Object.keys(trendData[0] || {}).length || 9
    setHeaderStyle(ws2, colCount2)
    ws2['!cols'] = Array.from({ length: colCount2 }, () => ({ wch: 18 }))
    autoSizeColumns(ws2)
    XLSX.utils.book_append_sheet(wb, ws2, 'Trend Analysis')

    const date = formatDateEN(new Date())
    const fileName = `RhythmERP_RunHistory_${date}.xlsx`
    triggerDownload(wb, fileName)

    toast.success('Run history exported', {
      description: `${fileName} downloaded successfully`,
    })
  } catch (error) {
    console.error('Export run history error:', error)
    toast.error('Export failed', {
      description: 'Could not export run history to Excel',
    })
  }
}

/** Parse duration strings like "1m 30s" or "45s" into seconds */
function parseDuration(d: string): number {
  if (!d || d === '—') return 0
  const minMatch = d.match(/(\d+)m/)
  const secMatch = d.match(/(\d+)s/)
  const mins = minMatch ? parseInt(minMatch[1], 10) : 0
  const secs = secMatch ? parseInt(secMatch[1], 10) : 0
  return mins * 60 + secs
}

// ─── 3. Export Bug Reports to Excel ───────────────────────
export async function exportBugReportsToExcel(bugs: BugReport[]): Promise<void> {
  try {
    const XLSX = await import('xlsx')
    ;(window as unknown as Record<string, unknown>).XLSX = XLSX

    const wb = XLSX.utils.book_new()

    // Sheet 1: Bug Reports
    const bugData = bugs.map((b) => {
      const slaDeadline = getSLADeadline(b.priority, b.createdAt)
      const isOverdue = new Date() > slaDeadline && b.status !== 'fixed'
      return {
        ID: b.id.substring(0, 8).toUpperCase(),
        'Test ID': b.testId,
        Description: b.testDescription,
        Module: b.moduleName,
        Priority: b.priority.toUpperCase(),
        Status: b.status.replace('-', ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
        Reporter: b.reporterName,
        'Assigned To': b.assignedToName || '—',
        'Created Date': formatDateTimeEN(b.createdAt),
        SLA: isOverdue ? 'OVERDUE' : b.status === 'fixed' ? 'Resolved' : formatDateENLong(slaDeadline.toISOString()),
      }
    })

    const ws1 = XLSX.utils.json_to_sheet(bugData)
    const colCount1 = 10
    setHeaderStyle(ws1, colCount1)

    // Priority conditional formatting (column E = index 4)
    bugs.forEach((b, idx) => {
      const row = idx + 2
      const priorityRef = `E${row}`
      const cell = (ws1 as Record<string, unknown>)[priorityRef] as Record<string, unknown> | undefined
      if (cell) {
        setStatusCellColor(cell, b.priority, PRIORITY_COLORS)
      }
    })

    ws1['!cols'] = Array.from({ length: colCount1 }, (_, i) => ({ wch: i === 2 ? 30 : 15 }))
    autoSizeColumns(ws1)
    XLSX.utils.book_append_sheet(wb, ws1, 'Bug Reports')

    // Sheet 2: Summary by Module
    const moduleBugs = new Map<string, BugReport[]>()
    bugs.forEach((b) => {
      const existing = moduleBugs.get(b.moduleName) || []
      existing.push(b)
      moduleBugs.set(b.moduleName, existing)
    })

    const moduleSummaryData: Array<Record<string, string | number>> = []
    moduleBugs.forEach((moduleBugsList, moduleName) => {
      const high = moduleBugsList.filter((b) => b.priority === 'high').length
      const medium = moduleBugsList.filter((b) => b.priority === 'medium').length
      const low = moduleBugsList.filter((b) => b.priority === 'low').length
      const open = moduleBugsList.filter((b) => b.status === 'open').length
      const inProgress = moduleBugsList.filter((b) => b.status === 'in-progress').length
      const fixed = moduleBugsList.filter((b) => b.status === 'fixed').length
      moduleSummaryData.push({
        Module: moduleName,
        'Total Bugs': moduleBugsList.length,
        'High Priority': high,
        'Medium Priority': medium,
        'Low Priority': low,
        Open: open,
        'In Progress': inProgress,
        Fixed: fixed,
      })
    })

    const ws2 = XLSX.utils.json_to_sheet(moduleSummaryData)
    const colCount2 = Object.keys(moduleSummaryData[0] || {}).length || 8
    setHeaderStyle(ws2, colCount2)
    ws2['!cols'] = Array.from({ length: colCount2 }, () => ({ wch: 16 }))
    autoSizeColumns(ws2)
    XLSX.utils.book_append_sheet(wb, ws2, 'Summary by Module')

    // Sheet 3: Summary by Priority
    const prioritySummaryData = [
      {
        Priority: 'HIGH',
        Count: bugs.filter((b) => b.priority === 'high').length,
        Open: bugs.filter((b) => b.priority === 'high' && b.status === 'open').length,
        'In Progress': bugs.filter((b) => b.priority === 'high' && b.status === 'in-progress').length,
        Fixed: bugs.filter((b) => b.priority === 'high' && b.status === 'fixed').length,
        'Overdue': bugs.filter(
          (b) => b.priority === 'high' && b.status !== 'fixed' && new Date() > getSLADeadline(b.priority, b.createdAt)
        ).length,
      },
      {
        Priority: 'MEDIUM',
        Count: bugs.filter((b) => b.priority === 'medium').length,
        Open: bugs.filter((b) => b.priority === 'medium' && b.status === 'open').length,
        'In Progress': bugs.filter((b) => b.priority === 'medium' && b.status === 'in-progress').length,
        Fixed: bugs.filter((b) => b.priority === 'medium' && b.status === 'fixed').length,
        'Overdue': bugs.filter(
          (b) => b.priority === 'medium' && b.status !== 'fixed' && new Date() > getSLADeadline(b.priority, b.createdAt)
        ).length,
      },
      {
        Priority: 'LOW',
        Count: bugs.filter((b) => b.priority === 'low').length,
        Open: bugs.filter((b) => b.priority === 'low' && b.status === 'open').length,
        'In Progress': bugs.filter((b) => b.priority === 'low' && b.status === 'in-progress').length,
        Fixed: bugs.filter((b) => b.priority === 'low' && b.status === 'fixed').length,
        'Overdue': bugs.filter(
          (b) => b.priority === 'low' && b.status !== 'fixed' && new Date() > getSLADeadline(b.priority, b.createdAt)
        ).length,
      },
      {
        Priority: 'TOTAL',
        Count: bugs.length,
        Open: bugs.filter((b) => b.status === 'open').length,
        'In Progress': bugs.filter((b) => b.status === 'in-progress').length,
        Fixed: bugs.filter((b) => b.status === 'fixed').length,
        'Overdue': bugs.filter(
          (b) => b.status !== 'fixed' && new Date() > getSLADeadline(b.priority, b.createdAt)
        ).length,
      },
    ]

    const ws3 = XLSX.utils.json_to_sheet(prioritySummaryData)
    const colCount3 = 6
    setHeaderStyle(ws3, colCount3)
    ws3['!cols'] = Array.from({ length: colCount3 }, () => ({ wch: 14 }))
    autoSizeColumns(ws3)
    XLSX.utils.book_append_sheet(wb, ws3, 'Summary by Priority')

    const date = formatDateEN(new Date())
    const fileName = `RhythmERP_BugReports_${date}.xlsx`
    triggerDownload(wb, fileName)

    toast.success('Bug reports exported', {
      description: `${fileName} downloaded successfully`,
    })
  } catch (error) {
    console.error('Export bug reports error:', error)
    toast.error('Export failed', {
      description: 'Could not export bug reports to Excel',
    })
  }
}

// ─── 4. Generate Report Summary (Markdown) ───────────────
export function generateReportSummary(
  runs: RunSnapshot[],
  bugs: BugReport[],
  moduleHealth: ModuleHealth[]
): string {
  const now = new Date()
  const dateStr = now.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
  const timeStr = now.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
  })

  const totalRuns = runs.length
  const totalTests = runs.reduce((s, r) => s + r.total, 0)
  const totalPassed = runs.reduce((s, r) => s + r.passed, 0)
  const overallRate = totalTests > 0 ? ((totalPassed / totalTests) * 100).toFixed(1) : '0.0'
  const activeBugs = bugs.filter((b) => b.status !== 'fixed').length
  const highPriorityOpen = bugs.filter(
    (b) => b.priority === 'high' && b.status !== 'fixed'
  ).length

  // Section 1: Executive Summary
  let md = `# RhythmERP Automation Report\n\n`
  md += `**Generated:** ${dateStr} at ${timeStr}\n\n`
  md += `---\n\n`
  md += `## 1. Executive Summary\n\n`
  md += `| Metric | Value |\n|---|---|\n`
  md += `| Total Runs | ${totalRuns} |\n`
  md += `| Total Tests Executed | ${totalTests} |\n`
  md += `| Overall Pass Rate | ${overallRate}% |\n`
  md += `| Active Bugs | ${activeBugs} |\n`
  md += `| High Priority Open Bugs | ${highPriorityOpen} |\n\n`

  // Section 2: Module Health Overview
  md += `## 2. Module Health Overview\n\n`
  md += `| Module | Pass Rate | Total Tests | Passed | Failed | Last Run |\n`
  md += `|---|---|---|---|---|---|\n`
  moduleHealth.forEach((m) => {
    md += `| ${m.moduleName} | ${m.passRate.toFixed(1)}% | ${m.totalTests} | ${m.passedTests} | ${m.failedTests} | ${m.lastRun} |\n`
  })
  md += `\n`

  // Section 3: Critical Bugs
  const criticalBugs = bugs.filter(
    (b) => b.priority === 'high' && b.status !== 'fixed'
  )
  md += `## 3. Critical Bugs (High Priority, Unresolved)\n\n`
  if (criticalBugs.length === 0) {
    md += `*No critical bugs at this time.* \n\n`
  } else {
    md += `| ID | Test | Module | Status | Reporter | SLA |\n`
    md += `|---|---|---|---|---|---|\n`
    criticalBugs.forEach((b) => {
      const slaDeadline = getSLADeadline(b.priority, b.createdAt)
      const isOverdue = new Date() > slaDeadline
      const slaLabel = isOverdue ? 'OVERDUE' : formatDateENLong(slaDeadline.toISOString())
      md += `| ${b.id.substring(0, 8).toUpperCase()} | ${b.testDescription} | ${b.moduleName} | ${b.status} | ${b.reporterName} | ${slaLabel} |\n`
    })
    md += `\n`
  }

  // Section 4: Recent Run Results
  const recentRuns = [...runs]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 5)
  md += `## 4. Recent Run Results (Last 5)\n\n`
  md += `| Date | Module | Total | Passed | Failed | Pass Rate | Duration |\n`
  md += `|---|---|---|---|---|---|---|\n`
  recentRuns.forEach((r) => {
    md += `| ${formatDateENLong(r.date)} | ${r.moduleId} | ${r.total} | ${r.passed} | ${r.failed} | ${r.rate.toFixed(1)}% | ${r.duration} |\n`
  })
  md += `\n`

  // Section 5: Recommendations
  md += `## 5. Recommendations\n\n`
  const recommendations: string[] = []

  // Rule 1: Low pass rate modules
  const lowRateModules = moduleHealth.filter((m) => m.passRate < 50 && m.totalTests > 0)
  if (lowRateModules.length > 0) {
    recommendations.push(
      `**Critical:** ${lowRateModules.map((m) => `**${m.moduleName}** (${m.passRate.toFixed(1)}%)`).join(', ')} — pass rate below 50%. Immediate investigation required.`
    )
  }

  // Rule 2: Modules with declining trend
  moduleHealth.forEach((m) => {
    if (m.trend && m.trend.length >= 3) {
      const recentTrend = m.trend.slice(-3)
      const isDeclining = recentTrend[2] < recentTrend[0]
      if (isDeclining && m.totalTests > 0) {
        recommendations.push(
          `**Declining:** **${m.moduleName}** shows a downward trend in pass rate over recent runs.`
        )
      }
    }
  })

  // Rule 3: High overdue bugs
  const overdueBugs = bugs.filter(
    (b) => b.status !== 'fixed' && new Date() > getSLADeadline(b.priority, b.createdAt)
  )
  if (overdueBugs.length > 0) {
    recommendations.push(
      `**SLA Breach:** ${overdueBugs.length} bug(s) have exceeded their SLA deadline. Escalation recommended.`
    )
  }

  // Rule 4: Many open bugs in a single module
  const moduleOpenBugs = new Map<string, number>()
  bugs
    .filter((b) => b.status === 'open')
    .forEach((b) => {
      moduleOpenBugs.set(b.moduleName, (moduleOpenBugs.get(b.moduleName) || 0) + 1)
    })
  moduleOpenBugs.forEach((count, mod) => {
    if (count >= 3) {
      recommendations.push(
        `**Bug Concentration:** **${mod}** has ${count} open bugs. Consider a focused bug-fix sprint.`
      )
    }
  })

  // Rule 5: No runs recently
  const staleModules = moduleHealth.filter(
    (m) => m.lastRun === '—' && m.totalTests > 0
  )
  if (staleModules.length > 0) {
    recommendations.push(
      `**No Coverage:** ${staleModules.map((m) => `**${m.moduleName}**`).join(', ')} — no test runs recorded. Schedule baseline runs.`
    )
  }

  // Rule 6: Overall health
  if (Number(overallRate) >= 80 && activeBugs === 0) {
    recommendations.push(
      `**Healthy:** Overall automation health is good with ${overallRate}% pass rate and no active bugs. Keep up the good work!`
    )
  }

  if (recommendations.length === 0) {
    md += `*No specific recommendations at this time. Continue monitoring.*\n`
  } else {
    recommendations.forEach((r, i) => {
      md += `${i + 1}. ${r}\n`
    })
  }

  md += `\n---\n`
  md += `\n*Report generated by RhythmERP Automation Runner*\n`

  return md
}

// ─── 5. Export Report to PDF (Print) ──────────────────────
export function exportReportToPDF(
  runs: RunSnapshot[],
  bugs: BugReport[],
  moduleHealth: ModuleHealth[],
  moduleName?: string
): void {
  try {
    const now = new Date()
    const dateStr = now.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    })
    const timeStr = now.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
    })

    const totalRuns = runs.length
    const totalTests = runs.reduce((s, r) => s + r.total, 0)
    const totalPassed = runs.reduce((s, r) => s + r.passed, 0)
    const overallRate = totalTests > 0 ? ((totalPassed / totalTests) * 100).toFixed(1) : '0.0'
    const activeBugs = bugs.filter((b) => b.status !== 'fixed').length
    const highPriorityOpen = bugs.filter(
      (b) => b.priority === 'high' && b.status !== 'fixed'
    ).length
    const rateColor = Number(overallRate) >= 80 ? '#4CAF50' : Number(overallRate) >= 50 ? '#FF9800' : '#F44336'

    // Module health rows
    const moduleRows = moduleHealth
      .map(
        (m) => `
      <tr>
        <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">${m.moduleName}</td>
        <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:center;color:${m.passRate >= 80 ? '#4CAF50' : m.passRate >= 50 ? '#FF9800' : '#F44336'};font-weight:600;">${m.passRate.toFixed(1)}%</td>
        <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:center;">${m.totalTests}</td>
        <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:center;color:#4CAF50;">${m.passedTests}</td>
        <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:center;color:#F44336;">${m.failedTests}</td>
        <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:center;">${m.lastRun}</td>
      </tr>`
      )
      .join('')

    // Critical bugs
    const criticalBugs = bugs.filter((b) => b.priority === 'high' && b.status !== 'fixed')
    const criticalBugRows =
      criticalBugs.length === 0
        ? '<tr><td colspan="5" style="padding:12px;text-align:center;color:#666;">No critical bugs at this time</td></tr>'
        : criticalBugs
            .map((b) => {
              const slaDeadline = getSLADeadline(b.priority, b.createdAt)
              const isOverdue = new Date() > slaDeadline
              return `
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">${b.id.substring(0, 8).toUpperCase()}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">${b.testDescription}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">${b.moduleName}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:center;"><span style="background:${b.status === 'open' ? '#F44336' : '#FF9800'};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">${b.status.replace('-', ' ')}</span></td>
          <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:center;color:${isOverdue ? '#F44336' : '#666'};font-weight:${isOverdue ? '600' : '400'};">${isOverdue ? 'OVERDUE' : formatDateENLong(slaDeadline.toISOString())}</td>
        </tr>`
            })
            .join('')

    // Recent runs
    const recentRuns = [...runs]
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
      .slice(0, 5)
    const recentRunRows = recentRuns
      .map(
        (r) => `
      <tr>
        <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">${formatDateENLong(r.date)}</td>
        <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">${r.moduleId}</td>
        <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:center;">${r.total}</td>
        <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:center;color:#4CAF50;">${r.passed}</td>
        <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:center;color:#F44336;">${r.failed}</td>
        <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:center;color:${r.rate >= 80 ? '#4CAF50' : r.rate >= 50 ? '#FF9800' : '#F44336'};font-weight:600;">${r.rate.toFixed(1)}%</td>
        <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:center;">${r.duration}</td>
      </tr>`
      )
      .join('')

    // Recommendations
    const md = generateReportSummary(runs, bugs, moduleHealth)
    const recSection = md.split('## 5. Recommendations\n\n')[1]?.split('\n---')[0] || ''
    const recItems = recSection
      .split('\n')
      .filter((l) => l.trim().startsWith('*') || l.trim().match(/^\d+\./))
      .map((l) => `<li style="margin-bottom:6px;">${l.replace(/^\d+\.\s*/, '').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</li>`)
      .join('')

    const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>RhythmERP Automation Report</title>
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Poppins', sans-serif; color: #1a1a2e; line-height: 1.6; background: #fff; }
    .page { max-width: 900px; margin: 0 auto; padding: 40px; }
    .header { background: ${ERP_BLUE_HEX}; color: #fff; padding: 32px 40px; border-radius: 12px; margin-bottom: 32px; display: flex; align-items: center; justify-content: space-between; }
    .header h1 { font-family: 'Poppins', sans-serif; font-size: 24px; font-weight: 700; margin-bottom: 4px; }
    .header p { font-size: 13px; opacity: 0.85; }
    .header .logo-area { width: 48px; height: 48px; background: rgba(255,255,255,0.15); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 700; }
    .section { margin-bottom: 28px; page-break-inside: avoid; }
    .section h2 { font-family: 'Poppins', sans-serif; font-size: 17px; font-weight: 600; color: ${ERP_BLUE_HEX}; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 2px solid #e8eaf6; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th { background: ${ERP_BLUE_HEX}; color: #fff; padding: 10px 12px; text-align: left; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
    th:first-child { border-radius: 6px 0 0 0; }
    th:last-child { border-radius: 0 6px 0 0; }
    .metrics { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 20px; }
    .metric-card { background: #f5f5ff; border-radius: 10px; padding: 16px; text-align: center; border: 1px solid #e8eaf6; }
    .metric-card .value { font-family: 'Poppins', sans-serif; font-size: 22px; font-weight: 700; color: ${ERP_BLUE_HEX}; }
    .metric-card .label { font-size: 11px; color: #666; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.5px; }
    .footer { text-align: center; font-size: 11px; color: #999; margin-top: 40px; padding-top: 16px; border-top: 1px solid #e0e0e0; }
    ul.recommendations { padding-left: 20px; }
    ul.recommendations li { margin-bottom: 8px; font-size: 13px; }
    @media print {
      body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      .section { page-break-inside: avoid; }
      .header { -webkit-print-color-adjust: exact; }
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="header">
      <div>
        <h1>RhythmERP Automation Report</h1>
        <p>${moduleName ? `Module: ${moduleName} | ` : ''}Generated: ${dateStr} at ${timeStr}</p>
      </div>
      <div class="logo-area">R</div>
    </div>

    <div class="section">
      <h2>1. Executive Summary</h2>
      <div class="metrics">
        <div class="metric-card">
          <div class="value">${totalRuns}</div>
          <div class="label">Total Runs</div>
        </div>
        <div class="metric-card">
          <div class="value">${totalTests}</div>
          <div class="label">Tests Executed</div>
        </div>
        <div class="metric-card">
          <div class="value" style="color:${rateColor}">${overallRate}%</div>
          <div class="label">Pass Rate</div>
        </div>
        <div class="metric-card">
          <div class="value" style="color:${activeBugs > 0 ? '#F44336' : '#4CAF50'}">${activeBugs}</div>
          <div class="label">Active Bugs</div>
        </div>
        <div class="metric-card">
          <div class="value" style="color:${highPriorityOpen > 0 ? '#F44336' : '#4CAF50'}">${highPriorityOpen}</div>
          <div class="label">Critical Bugs</div>
        </div>
      </div>
    </div>

    <div class="section">
      <h2>2. Module Health Overview</h2>
      <table>
        <thead>
          <tr><th>Module</th><th>Pass Rate</th><th>Total</th><th>Passed</th><th>Failed</th><th>Last Run</th></tr>
        </thead>
        <tbody>${moduleRows}</tbody>
      </table>
    </div>

    <div class="section">
      <h2>3. Critical Bugs</h2>
      <table>
        <thead>
          <tr><th>ID</th><th>Test</th><th>Module</th><th>Status</th><th>SLA</th></tr>
        </thead>
        <tbody>${criticalBugRows}</tbody>
      </table>
    </div>

    <div class="section">
      <h2>4. Recent Run Results</h2>
      <table>
        <thead>
          <tr><th>Date</th><th>Module</th><th>Total</th><th>Passed</th><th>Failed</th><th>Pass Rate</th><th>Duration</th></tr>
        </thead>
        <tbody>${recentRunRows}</tbody>
      </table>
    </div>

    <div class="section">
      <h2>5. Recommendations</h2>
      <ul class="recommendations">${recItems || '<li style="color:#666;">No specific recommendations at this time.</li>'}</ul>
    </div>

    <div class="footer">
      Report generated by RhythmERP Automation Runner &mdash; ${dateStr} ${timeStr}
    </div>
  </div>

  <script>
    window.onload = function() { window.print(); }
  </script>
</body>
</html>`

    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(html)
      printWindow.document.close()
      toast.success('Print dialog opened', {
        description: 'Use the browser print dialog to save as PDF',
      })
    } else {
      toast.error('Popup blocked', {
        description: 'Please allow popups to generate the PDF report',
      })
    }
  } catch (error) {
    console.error('Export PDF error:', error)
    toast.error('PDF generation failed', {
      description: 'Could not generate print-friendly report',
    })
  }
}

// ─── ExportMenu Component ─────────────────────────────────
export interface ExportMenuProps {
  testGroups?: TestClassGroup[]
  runHistory?: RunSnapshot[]
  bugReports?: BugReport[]
  moduleHealth?: ModuleHealth[]
  moduleName?: string
}

export function ExportMenu({
  testGroups,
  runHistory,
  bugReports,
  moduleHealth,
  moduleName,
}: ExportMenuProps) {
  const [loadingAction, setLoadingAction] = useState<string | null>(null)

  const hasTestData = testGroups && testGroups.length > 0 && testGroups.some((g) => g.tests.length > 0)
  const hasRunHistory = runHistory && runHistory.length > 0
  const hasBugReports = bugReports && bugReports.length > 0
  const hasModuleHealth = moduleHealth && moduleHealth.length > 0

  const handleExportTestResults = useCallback(async () => {
    if (!testGroups) return
    setLoadingAction('test')
    await exportTestResultsToExcel(testGroups, moduleName || 'All')
    setLoadingAction(null)
  }, [testGroups, moduleName])

  const handleExportRunHistory = useCallback(async () => {
    if (!runHistory) return
    setLoadingAction('runHistory')
    await exportRunHistoryToExcel(runHistory)
    setLoadingAction(null)
  }, [runHistory])

  const handleExportBugReports = useCallback(async () => {
    if (!bugReports) return
    setLoadingAction('bugs')
    await exportBugReportsToExcel(bugReports)
    setLoadingAction(null)
  }, [bugReports])

  const handleCopySummary = useCallback(async () => {
    if (!runHistory || !bugReports || !moduleHealth) return
    setLoadingAction('copy')
    try {
      const summary = generateReportSummary(runHistory, bugReports, moduleHealth)
      await navigator.clipboard.writeText(summary)
      toast.success('Report summary copied', {
        description: 'Markdown report copied to clipboard',
      })
    } catch {
      toast.error('Copy failed', {
        description: 'Could not copy report to clipboard',
      })
    }
    setLoadingAction(null)
  }, [runHistory, bugReports, moduleHealth])

  const handlePrintPDF = useCallback(() => {
    if (!runHistory || !bugReports || !moduleHealth) return
    setLoadingAction('pdf')
    exportReportToPDF(runHistory, bugReports, moduleHealth, moduleName)
    setLoadingAction(null)
  }, [runHistory, bugReports, moduleHealth, moduleName])

  const renderIcon = (action: string, Icon: React.ElementType) => {
    if (loadingAction === action) {
      return <Spinner size={16} />
    }
    return <Icon className="size-4" />
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2 text-[13px]">
          <Download className="size-4" />
          Export
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="text-[12px] text-muted-foreground">
          Excel Reports
        </DropdownMenuLabel>
        <DropdownMenuItem
          disabled={!hasTestData || loadingAction === 'test'}
          onClick={handleExportTestResults}
          className="text-[13px] gap-2"
        >
          {renderIcon('test', FileSpreadsheet)}
          Export Test Results
        </DropdownMenuItem>
        <DropdownMenuItem
          disabled={!hasRunHistory || loadingAction === 'runHistory'}
          onClick={handleExportRunHistory}
          className="text-[13px] gap-2"
        >
          {renderIcon('runHistory', FileSpreadsheet)}
          Export Run History
        </DropdownMenuItem>
        <DropdownMenuItem
          disabled={!hasBugReports || loadingAction === 'bugs'}
          onClick={handleExportBugReports}
          className="text-[13px] gap-2"
        >
          {renderIcon('bugs', FileSpreadsheet)}
          Export Bug Reports
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuLabel className="text-[12px] text-muted-foreground">
          Quick Reports
        </DropdownMenuLabel>
        <DropdownMenuItem
          disabled={!hasRunHistory || !hasBugReports || !hasModuleHealth || loadingAction === 'copy'}
          onClick={handleCopySummary}
          className="text-[13px] gap-2"
        >
          {renderIcon('copy', Copy)}
          Copy Report Summary
        </DropdownMenuItem>
        <DropdownMenuItem
          disabled={!hasRunHistory || !hasBugReports || !hasModuleHealth || loadingAction === 'pdf'}
          onClick={handlePrintPDF}
          className="text-[13px] gap-2"
        >
          {renderIcon('pdf', Printer)}
          Print Report (PDF)
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
