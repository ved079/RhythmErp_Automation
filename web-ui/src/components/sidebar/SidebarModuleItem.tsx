'use client'

import React from 'react'
import { ChevronDown, Circle } from 'lucide-react'

// ─── Types ───────────────────────────────────────────────
interface SidebarModule {
  id: string
  label: string
  badge?: string
  badgeType?: 'success' | 'warning' | 'wip' | 'none'
  children?: SidebarModule[]
  defaultExpanded?: boolean
  cartLink?: boolean
}

// ─── Sidebar Module Item ─────────────────────────────────
export function SidebarModuleItem({
  module,
  depth = 0,
  activeId,
  onSelect,
  expandedIds,
  toggleExpand,
  isLast = true,
  justExpandedId,
}: {
  module: SidebarModule
  depth?: number
  activeId: string | null
  onSelect: (id: string) => void
  expandedIds: Set<string>
  toggleExpand: (id: string) => void
  isLast?: boolean
  justExpandedId: string | null
}) {
  const hasChildren = module.children && module.children.length > 0
  const isExpanded = expandedIds.has(module.id)
  const isActive = activeId === module.id
  const isParentActive = activeId && hasChildren && module.children!.some((c) => c.id === activeId)
  const isChild = depth > 0

  const treeLineWidth = '2.7px'
  const treeLineColor = '#c8ccd4'

  return (
    <div className="relative">
      {isChild && (
        <>
          <div
            className="absolute bg-transparent z-0"
            style={{
              left: isChild && depth === 1 ? '34px' : '74px',
              top: '6px',
              width: depth === 1 ? '22px' : '16px',
              height: '16px',
              borderLeft: `${treeLineWidth} solid ${treeLineColor}`,
              borderBottom: `${treeLineWidth} solid ${treeLineColor}`,
              borderRadius: isLast ? '0 0 0 15px' : '0 0 0 15px',
            }}
          />
          {!isLast && (
            <div
              className="absolute z-0 bg-transparent"
              style={{
                left: isChild && depth === 1 ? '34px' : '74px',
                top: '22px',
                bottom: '0',
                width: treeLineWidth,
                backgroundColor: treeLineColor,
                borderRadius: '10px',
              }}
            />
          )}
        </>
      )}
      <button
        data-module-id={module.id}
        ref={(el) => {
          if (el && justExpandedId === module.id && hasChildren) {
            requestAnimationFrame(() => {
              el.scrollIntoView({ behavior: 'smooth', block: 'start' })
            })
          }
        }}
        onClick={() => {
          if (hasChildren) toggleExpand(module.id)
          else onSelect(module.id)
        }}
        className={`w-full flex items-center text-[14px] transition-all duration-200 cursor-pointer text-left font-['Poppins'] relative z-[1] ${
          isChild
            ? isActive
              ? 'text-[#1B4332] dark:text-green-300 font-semibold'
              : 'text-[#545454] dark:text-gray-300 font-medium hover:text-[#6777EF] dark:hover:text-indigo-400 hover:bg-[rgba(82,183,136,0.08)] hover:shadow-[rgba(82,183,136,0.5)_2px_0px_inset] hover:rounded-[5px]'
            : isActive
              ? 'bg-gradient-to-r from-[#DFF3E3] via-[#C8E6C9] to-[#B7E4C7] dark:bg-[#1B4332]/25 text-[#1B4332] dark:text-green-300 font-semibold shadow-[rgba(34,197,94,0.25)_2px_0px_4px_inset,rgba(34,197,94,0.15)_0px_2px_6px] rounded-[5px]'
              : isParentActive
                ? 'text-[#1B4332] dark:text-green-300 font-semibold'
                : 'text-[#545454] dark:text-gray-300 font-medium hover:text-[#6777EF] dark:hover:text-indigo-400 hover:bg-[rgba(82,183,136,0.08)] hover:shadow-[rgba(82,183,136,0.5)_2px_0px_inset] hover:rounded-[5px]'
        }`}
        style={{
          paddingLeft: isChild ? (depth === 1 ? '48px' : '80px') : '15px',
          paddingRight: '24px',
          paddingTop: '7px',
          paddingBottom: '7px',
        }}
      >
        {hasChildren ? (
          <ChevronDown
            className={`size-[18px] shrink-0 transition-transform duration-200 mr-1.5 ${
              !isExpanded ? '-rotate-90' : ''
            } ${isActive || isParentActive ? 'text-[#1B4332] dark:text-green-300' : 'text-[#495584] dark:text-gray-400'}`}
          />
        ) : isChild ? (
          <span
            className={`w-[7px] h-[7px] rounded-full shrink-0 mr-2 ${
              isActive
                ? 'bg-[#1A56DB] dark:bg-indigo-400'
                : 'border-[1.5px] border-[#777777] dark:border-gray-500'
            }`}
          />
        ) : (
          <span className="w-[18px] shrink-0 mr-1.5" />
        )}
        <span className="truncate flex-1">{module.label}</span>
        {module.cartLink && (
          <a
            href="/cart"
            onClick={(e) => e.stopPropagation()}
            className="ml-1.5 inline-flex items-center shrink-0 text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
            aria-label="Cart"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="9" cy="21" r="1" />
              <circle cx="20" cy="21" r="1" />
              <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
            </svg>
          </a>
        )}
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
        <div className="relative">
          <div
            className="absolute z-0"
            style={{
              left: '34px',
              top: '0',
              bottom: isLast ? '27px' : '0',
              width: treeLineWidth,
              backgroundColor: treeLineColor,
              borderRadius: '10px',
            }}
          />
          {module.children!.map((child, idx) => (
            <SidebarModuleItem
              key={child.id}
              module={child}
              depth={depth + 1}
              activeId={activeId}
              onSelect={onSelect}
              expandedIds={expandedIds}
              toggleExpand={toggleExpand}
              isLast={idx === module.children!.length - 1}
              justExpandedId={justExpandedId}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export type { SidebarModule }
