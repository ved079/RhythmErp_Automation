const _moduleCache = new Map<string, string>()

export function getCachedFolderToSidebarId(folderName: string): string {
  return _moduleCache.get(folderName) ?? folderName.toLowerCase().replace(/_/g, '-')
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
  for (const mod of data.modules ?? []) {
    if (mod.folderName && mod.name) {
      _moduleCache.set(mod.folderName, mod.name.toLowerCase().replace(/_/g, '-'))
    }
  }
}
