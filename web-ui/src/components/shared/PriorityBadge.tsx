'use client'

import React from 'react'
import { CheckCircle2, XCircle, Loader2, Circle, ArrowUpDown } from 'lucide-react'
import { priorityConfig, type TestPriority } from '@/data/testSpecGroups'

// ─── Priority Badge ──────────────────────────────────────
export function PriorityBadge({ priority }: { priority?: TestPriority }) {
  if (!priority) return null
  const cfg = priorityConfig[priority]
  return (
    <span className={`inline-flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded-full ${cfg.color}`}>
      {cfg.label}
    </span>
  )
}

// ─── Test Status Icon ────────────────────────────────────
export function TestStatusIcon({ status, size = 4 }: { status: string; size?: number }) {
  const cls = `size-${size} shrink-0`
  switch (status) {
    case 'passed':
      return <CheckCircle2 className={`${cls} text-green-500`} />
    case 'failed':
      return <XCircle className={`${cls} text-red-500`} />
    case 'running':
      return <Loader2 className={`${cls} text-indigo-500 animate-spin`} />
    default:
      return <Circle className={`size-${Math.max(size - 0.5, 3)} text-gray-300 dark:text-gray-600`} />
  }
}

// ─── Sort Arrow (ERP-style: 150ms rotation) ─────────────
export function SortArrow({ col, sortCol, sortDir }: { col: string; sortCol: string; sortDir: 'asc' | 'desc' }) {
  const isActive = sortCol === col
  return (
    <ArrowUpDown
      className={`size-3 transition-transform duration-150 ${isActive ? 'opacity-100' : 'opacity-30'} ${isActive && sortDir === 'desc' ? 'rotate-180' : ''}`}
    />
  )
}
