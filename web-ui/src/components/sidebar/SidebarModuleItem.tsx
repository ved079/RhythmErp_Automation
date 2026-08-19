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
  userIcon?: boolean
  toolIcon?: boolean
  bookIcon?: boolean
  menuIcon?: boolean
  homeIcon?: boolean
  tagIcon?: boolean
  keyIcon?: boolean
  rocketIcon?: boolean
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

  const treeLineWidth = '2px'
  const treeLineColor = 'color-mix(in srgb, currentColor 18%, transparent)'

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
              ? 'text-[#1B4332] dark:text-white rounded-[5px] font-semibold'
              : 'text-[#545454] dark:text-gray-400 font-medium hover:text-[#6777EF] dark:hover:text-gray-200 hover:bg-[rgba(82,183,136,0.08)] dark:hover:bg-white/[0.04] hover:shadow-[rgba(82,183,136,0.5)_2px_0px_inset] hover:rounded-[5px]'
            : isActive
              ? 'text-[#1B4332] dark:text-white font-semibold rounded-[5px]'
              : isParentActive
                ? 'text-[#1B4332] dark:text-white font-semibold rounded-[5px]'
                : 'text-[#545454] dark:text-gray-400 font-medium hover:text-[#6777EF] dark:hover:text-gray-200 hover:bg-[rgba(82,183,136,0.08)] dark:hover:bg-white/[0.04] hover:shadow-[rgba(82,183,136,0.5)_2px_0px_inset] hover:rounded-[5px]'
        }`}
        style={(() => {
          const isDarkMode = typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
          const base = {
            paddingLeft: isChild ? (depth === 1 ? '48px' : '80px') : '15px',
            paddingRight: '24px',
            paddingTop: '7px',
            paddingBottom: '7px',
          }
          if (!isDarkMode) {
            if (!isChild && isActive) return { ...base, background: 'linear-gradient(to right, #DFF3E3, #C8E6C9, #B7E4C7)', boxShadow: 'rgba(34,197,94,0.25) 2px 0px 4px inset, rgba(34,197,94,0.15) 0px 2px 6px' }
            return base
          }
          if (isActive || isParentActive || (isChild && isActive)) return { ...base, background: 'rgba(255,255,255,0.06)', boxShadow: '2px 0 0 0 #818cf8 inset' }
          return base
        })()}
      >
        {module.cartLink ? (
          <a
            href="/cart"
            onClick={(e) => e.stopPropagation()}
            className="size-[18px] shrink-0 mr-1.5 inline-flex items-center justify-center text-[#6b7280] hover:text-[#111827] dark:hover:text-gray-200 transition-colors"
            aria-label="Shopping Cart"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="9" cy="21" r="1" />
              <circle cx="20" cy="21" r="1" />
              <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
            </svg>
          </a>
        ) : module.userIcon ? (
          <svg className="size-[18px] shrink-0 mr-[10px] text-[#6b7280]" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        ) : module.toolIcon ? (
          <svg className="size-[18px] shrink-0 mr-[10px] text-[#6b7280]" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
          </svg>
        ) : module.bookIcon ? (
          <svg className="size-[18px] shrink-0 mr-[10px] text-[#6b7280]" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
        ) : module.menuIcon ? (
          <svg className="size-[18px] shrink-0 mr-[10px] text-[#6b7280]" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        ) : module.homeIcon ? (
          <svg className="size-[18px] shrink-0 mr-[10px] text-[#6b7280]" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
            <polyline points="9 22 9 12 15 12 15 22" />
          </svg>
        ) : module.tagIcon ? (
          <svg className="size-[18px] shrink-0 mr-[10px] text-[#6b7280]" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20.59 13.41L13.42 20.58a2 2 0 0 1-2.83 0L2.59 12.58a2 2 0 0 1 0-2.83l7.17-7.17a2 2 0 0 1 1.42-.58H19a2 2 0 0 1 2 2v6.59a2 2 0 0 1-.58 1.42z" />
            <line x1="7" y1="7" x2="7.01" y2="7" />
          </svg>
        ) : module.keyIcon ? (
          <svg className="size-[18px] shrink-0 mr-[10px] text-[#6b7280]" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4" />
          </svg>
        ) : module.rocketIcon ? (
          <svg className="size-[18px] shrink-0 mr-[10px] text-[#6366f1]" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" />
            <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" />
            <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" />
            <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" />
          </svg>
        ) : hasChildren ? (
          <ChevronDown
            className={`size-[18px] shrink-0 transition-transform duration-200 mr-1.5 ${
              !isExpanded ? '-rotate-90' : ''
            } ${isActive || isParentActive ? 'text-[#1B4332] dark:text-gray-200' : 'text-[#495584] dark:text-gray-500'}`}
          />
        ) : isChild ? (
          <span className={`w-[5px] h-[5px] rounded-full shrink-0 mr-2.5 ${isActive ? 'bg-[#1A56DB] dark:bg-indigo-400' : 'bg-gray-300 dark:bg-gray-600'}`} />
        ) : (
          <span className="w-[18px] shrink-0 mr-1.5" />
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
