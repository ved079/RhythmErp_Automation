'use client'

import React from 'react'
import { Flame, Activity, ShieldCheck } from 'lucide-react'
import type { TestPriority } from '@/lib/types'

// ─── Priority Config ────────────────────────────────────
const priorityConfig = {
  smoke: { icon: <Flame className="size-3" />, label: '🔥 Smoke', color: 'text-[#E65100] bg-[#FFF3E0] dark:text-orange-300 dark:bg-orange-900/40', dot: 'bg-[#FF9800]' },
  regression: { icon: <Activity className="size-3" />, label: '🔄 Regression', color: 'text-[#3F51B5] bg-[#DFE9FB] dark:text-indigo-300 dark:bg-indigo-900/40', dot: 'bg-[#3F51B5]' },
  sanity: { icon: <ShieldCheck className="size-3" />, label: '🛡️ Sanity', color: 'text-[#2E7D32] bg-[#E8F5E9] dark:text-green-300 dark:bg-green-900/40', dot: 'bg-[#4CAF50]' },
} as const

function PriorityBadge({ priority }: { priority?: TestPriority }) {
  if (!priority) return null
  const cfg = priorityConfig[priority]
  return (
    <span className={`inline-flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded-full ${cfg.color}`}>
      {cfg.label}
    </span>
  )
}

export { PriorityBadge, priorityConfig }
