import type { SidebarModule } from '@/components/sidebar/SidebarModuleItem'
import type { AuthUser } from '@/components/auth/LoginPage'
import { type ApiModule } from '@/lib/api'
import { getCachedFolderToSidebarId } from '@/lib/module-data'
import { ALL_SIDEBAR_MODULES } from '@/data/sidebarModules'

/**
 * Build sidebar by merging real API test counts into the full module list.
 * Modules without tests keep the "📝 No tests" badge.
 */
export function buildSidebarModules(apiModules: ApiModule[]): SidebarModule[] {
  // Deep clone the master list
  const sidebar: SidebarModule[] = JSON.parse(JSON.stringify(ALL_SIDEBAR_MODULES))

  // Build a lookup: sidebarId → test count from API
  const testCounts: Record<string, number> = {}
  for (const apiMod of apiModules) {
    for (const sub of apiMod.sub_modules) {
      const sid = getCachedFolderToSidebarId(sub.name)
      testCounts[sid] = sub.tests.length
    }
    // Standalone modules
    if (apiMod.sub_modules.length === 0) {
      const sid = getCachedFolderToSidebarId(apiMod.name)
      testCounts[sid] = 0
    }
  }

  // Update badges with real counts (recursive for nested groups)
  function updateBadges(items: SidebarModule[]) {
    for (const item of items) {
      const count = testCounts[item.id]
      if (count !== undefined && count > 0) {
        item.badge = `${count} tests`
        item.badgeType = 'success'
      }
      if (item.children) updateBadges(item.children)
    }
  }
  for (const mod of sidebar) {
    if (mod.children) updateBadges(mod.children)
  }

  return sidebar
}

/**
 * Filter sidebar modules based on user's role and moduleAccess.
 * - admin: full access (all modules)
 * - Others: only modules listed in moduleAccess (or 'all' for legacy)
 * - 'dashboard' and 'my-tickets' are always visible
 */
export function filterSidebarByAccess(modules: SidebarModule[], user: AuthUser): SidebarModule[] {
  // Admin gets full access
  if (user.role === 'admin') return modules

  const access = user.moduleAccess || []
  // Legacy support: ['all'] means full access
  if (access.includes('all')) return modules

  // Strip tab suffix from entries like "module-id|ui,batch" → "module-id"
  const accessIds = access.map(e => e.split('|')[0])

  // Always-visible module IDs
  const alwaysVisible = new Set(['dashboard', 'my-tickets'])

  function filterItems(items: SidebarModule[]): SidebarModule[] {
    return items
      .filter(item => {
        if (alwaysVisible.has(item.id)) return true
        // Check if this module ID or any of its children are in the access list
        if (accessIds.includes(item.id)) return true
        if (item.children) {
          const visibleChildren = item.children.filter(c =>
            alwaysVisible.has(c.id) || accessIds.includes(c.id) || (c.children && c.children.some(gc => accessIds.includes(gc.id)))
          )
          if (visibleChildren.length > 0) return true
        }
        return false
      })
      .map(item => {
        if (!item.children) return item
        // Filter children recursively
        const filteredChildren = filterItems(item.children)
        return { ...item, children: filteredChildren.length > 0 ? filteredChildren : undefined }
      })
  }

  return filterItems(modules)
}

/**
 * Parse moduleAccess entries to get allowed tabs for a specific module.
 * Entry format: "module-id" (all tabs) or "module-id|ui,api,batch" (specific tabs).
 * Returns null if all tabs are allowed, otherwise an array of allowed tab keys.
 */
export function getAllowedTabsForModule(
  moduleAccess: string[],
  moduleId: string,
): ('ui' | 'api' | 'batch')[] | null {
  if (moduleAccess.includes('all')) return null
  const entry = moduleAccess.find(e => e.split('|')[0] === moduleId)
  if (!entry) return null // no entry = no restriction (admin handled upstream)
  const parts = entry.split('|')
  if (parts.length < 2) return null // no suffix = all tabs
  const tabs = parts[1].split(',').filter(t => ['ui', 'api', 'batch'].includes(t)) as ('ui' | 'api' | 'batch')[]
  return tabs.length > 0 ? tabs : null
}
