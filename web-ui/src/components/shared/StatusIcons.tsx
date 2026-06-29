'use client'

import React from 'react'
import { CheckCircle2, XCircle, Circle, ArrowUpDown } from 'lucide-react'
import Spinner from '@/components/ui/Spinner'

// ─── Test Status Icon ────────────────────────────────────
function TestStatusIcon({ status, size = 4 }: { status: string; size?: number }) {
  const cls = `size-${size} shrink-0`
  switch (status) {
    case 'passed':
      return <CheckCircle2 className={`${cls} text-green-500`} />
    case 'failed':
      return <XCircle className={`${cls} text-red-500`} />
    case 'running':
      return <Spinner size={size * 4} accent="#6366f1" />
    default:
      return <Circle className={`size-${Math.max(size - 0.5, 3)} text-gray-300 dark:text-gray-600`} />
  }
}

// ─── Sort Arrow (ERP-style: 150ms rotation) ─────────────
function SortArrow({ col, sortCol, sortDir }: { col: string; sortCol: string; sortDir: 'asc' | 'desc' }) {
  const isActive = sortCol === col
  return (
    <ArrowUpDown
      className={`size-3 transition-transform duration-150 ${isActive ? 'opacity-100' : 'opacity-30'} ${isActive && sortDir === 'desc' ? 'rotate-180' : ''}`}
    />
  )
}

export { TestStatusIcon, SortArrow }
