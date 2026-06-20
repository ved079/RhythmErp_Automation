const _moduleCache = new Map<string, string>()

const _reverseCache = new Map<string, { module: string; subModule: string | null }>()

export function getCachedFolderToSidebarId(folderName: string): string {
  return _moduleCache.get(folderName) ?? folderName.toLowerCase().replace(/_/g, '-')
}

export function getCachedSidebarToFolderMapping(sidebarId: string): { module: string; subModule: string | null } | null {
  return _reverseCache.get(sidebarId) ?? null
}

export async function folderToSidebarIdFromDB(folderName: string): Promise<string | null> {
  if (_moduleCache.has(folderName)) return _moduleCache.get(folderName)!
  const res = await fetch(`/api/admin/modules?folderName=${encodeURIComponent(folderName)}`)
  if (!res.ok) return null
  const data = await res.json()
  const sidebarId = data.modules?.[0]?.name?.toLowerCase().replace(/_/g, '-') ?? null
  if (sidebarId) _moduleCache.set(folderName, sidebarId)
  return sidebarId
}

export async function warmModuleCache(): Promise<void> {
  const res = await fetch('/api/admin/modules')
  if (!res.ok) return
  const data = await res.json()
  const allModules = data.modules ?? []

  const parentById = new Map<string, { folderName: string; name: string }>()

  for (const mod of allModules) {
    if (mod.folderName && mod.name) {
      const sidebarId = mod.name.toLowerCase().replace(/_/g, '-')
      _moduleCache.set(mod.folderName, sidebarId)
      parentById.set(mod.id, { folderName: mod.folderName, name: mod.name })
    }
  }

  for (const mod of allModules) {
    if (!mod.folderName || !mod.name) continue
    const sidebarId = mod.name.toLowerCase().replace(/_/g, '-')
    if (mod.parentId) {
      const parent = parentById.get(mod.parentId)
      if (parent) {
        _reverseCache.set(sidebarId, { module: parent.folderName, subModule: mod.folderName })
      }
    } else {
      _reverseCache.set(sidebarId, { module: mod.folderName, subModule: null })
    }
  }
}
