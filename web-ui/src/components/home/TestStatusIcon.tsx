'use client'

import { CheckCircle2, XCircle, Loader2, Circle } from 'lucide-react'

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
