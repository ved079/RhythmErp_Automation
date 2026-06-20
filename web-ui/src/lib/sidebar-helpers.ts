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

  // Always-visible module IDs
  const alwaysVisible = new Set(['dashboard', 'my-tickets'])

  function filterItems(items: SidebarModule[]): SidebarModule[] {
    return items
      .filter(item => {
        if (alwaysVisible.has(item.id)) return true
        // Check if this module ID or any of its children are in the access list
        if (access.includes(item.id)) return true
        if (item.children) {
          const visibleChildren = item.children.filter(c =>
            alwaysVisible.has(c.id) || access.includes(c.id) || (c.children && c.children.some(gc => access.includes(gc.id)))
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
