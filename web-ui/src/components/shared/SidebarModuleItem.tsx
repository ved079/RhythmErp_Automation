'use client'

import React from 'react'
import { ChevronDown, CheckCircle2, XCircle, Loader2, Circle } from 'lucide-react'
import type { SidebarModule } from '@/types/dashboard'

interface SidebarModuleItemProps {
  module: SidebarModule
  depth?: number
  activeId: string | null
  onSelect: (id: string) => void
  expandedIds: Set<string>
  toggleExpand: (id: string) => void
}

export function SidebarModuleItem({
  module,
  depth = 0,
  activeId,
  onSelect,
  expandedIds,
  toggleExpand,
}: SidebarModuleItemProps) {
  const hasChildren = module.children && module.children.length > 0
  const isExpanded = expandedIds.has(module.id)
  const isActive = activeId === module.id
  const isParentActive = activeId && hasChildren && module.children!.some((c) => c.id === activeId)

  return (
    <div>
      <button
        onClick={() => {
          if (hasChildren) toggleExpand(module.id)
          else onSelect(module.id)
        }}
        className={`w-full flex items-center gap-1.5 px-3 py-[7px] text-[13px] rounded-md transition-colors cursor-pointer text-left ${
          isActive
            ? 'bg-[#c8e6c9] dark:bg-[#2d4a2d] text-gray-900 dark:text-gray-100 font-medium shadow-sm'
            : isParentActive
              ? 'bg-[#c8e6c9]/50 dark:bg-[#2d4a2d]/50 text-gray-800 dark:text-gray-200 font-medium'
              : 'text-gray-700 dark:text-gray-300 hover:bg-[#c8e6c9]/40 dark:hover:bg-[#2d4a2d]/30'
        }`}
        style={{ paddingLeft: `${depth * 16 + 12}px` }}
      >
        {hasChildren ? (
          <ChevronDown
            className={`size-3.5 shrink-0 transition-transform duration-200 ${
              !isExpanded ? '-rotate-90' : ''
            }`}
          />
        ) : (
          <span className="w-3.5 shrink-0" />
        )}
        <span className="truncate flex-1">{module.label}</span>
        {module.badge && (
          <span
            className={`text-[11px] ml-auto shrink-0 ${
              module.badgeType === 'success'
                ? 'text-green-700 dark:text-green-400'
                : module.badgeType === 'warning'
                  ? 'text-orange-700 dark:text-orange-400'
                  : module.badgeType === 'wip'
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-500 dark:text-gray-400'
            }`}
          >
            {module.badge}
          </span>
        )}
      </button>
      {hasChildren && isExpanded && (
        <div className="mt-0.5">
          {module.children!.map((child) => (
            <SidebarModuleItem
              key={child.id}
              module={child}
              depth={depth + 1}
              activeId={activeId}
              onSelect={onSelect}
              expandedIds={expandedIds}
              toggleExpand={toggleExpand}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function TestStatusIcon({ status, size = 4 }: { status: string; size?: number }) {
  const cls = `size-${size} shrink-0`
  switch (status) {
    case 'passed':
      return <CheckCircle2 className={`${cls} text-green-500`} />
    case 'failed':
      return <XCircle className={`${cls} text-red-500`} />
    case 'running':
      return <Loader2 className={`${cls} text-blue-500 animate-spin`} />
    default:
      return <Circle className={`size-${Math.max(size - 0.5, 3)} text-gray-300 dark:text-gray-600`} />
  }
}
