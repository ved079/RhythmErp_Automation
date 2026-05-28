'use client'

import type { TestPriority } from '@/lib/types'
import { priorityConfig } from '@/lib/constants'

export function PriorityBadge({ priority }: { priority?: TestPriority }) {
  if (!priority) return null
  const cfg = priorityConfig[priority]
  return (
    <span className={`inline-flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded-full ${cfg.color}`}>
      {cfg.label}
    </span>
  )
}
