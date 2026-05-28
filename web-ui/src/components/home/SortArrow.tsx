'use client'
import { ArrowUpDown } from 'lucide-react'

export function SortArrow({ col, sortCol, sortDir }: { col: string; sortCol: string; sortDir: 'asc' | 'desc' }) {
  const isActive = sortCol === col
  return (
    <ArrowUpDown
      className={`size-3 transition-transform duration-150 ${isActive ? 'opacity-100' : 'opacity-30'} ${isActive && sortDir === 'desc' ? 'rotate-180' : ''}`}
    />
  )
}
