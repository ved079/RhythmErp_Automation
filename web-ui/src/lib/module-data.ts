export async function folderToSidebarIdFromDB(folderName: string): Promise<string | null> {
  const res = await fetch(`/api/admin/modules?folderName=${encodeURIComponent(folderName)}`)
  if (!res.ok) return null
  const data = await res.json()
  return data.modules?.[0]?.name?.toLowerCase().replace(/_/g, '-') ?? null
}
