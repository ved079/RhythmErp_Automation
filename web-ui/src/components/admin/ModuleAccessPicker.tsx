'use client'

import { useState, useMemo, useCallback } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Shield,
  Zap,
  Settings,
  Building2,
  Key,
  Handshake,
  FileText,
  Search,
  X,
  Check,
  ChevronRight,
  Users,
  LayoutGrid,
  Monitor,
  Code2,
  Package,
} from 'lucide-react'

// ─── Types ────────────────────────────────────────────────────
export interface ModuleItem {
  id: string
  name: string
  label: string
  parentId?: string
  parentLabel?: string
}

export interface ModuleAccessPickerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  value: string[]
  onChange: (value: string[]) => void
  allModules: ModuleItem[]
  userName?: string
}

interface Preset {
  id: string
  label: string
  icon: React.ReactNode
  parentGroupId: string | null
  exactIds?: string[]
}

const TAB_CONFIG: { key: 'ui' | 'api' | 'batch'; label: string; icon: React.ReactNode; color: string }[] = [
  { key: 'ui',    label: 'UI Tests',     icon: <Monitor className="size-2.5" />,  color: '#1565C0' },
  { key: 'api',   label: 'API Tests',    icon: <Code2 className="size-2.5" />,    color: '#6A1B9A' },
  { key: 'batch', label: 'Batch Create', icon: <Package className="size-2.5" />,  color: '#E65100' },
]
const ALL_TABS: ('ui' | 'api' | 'batch')[] = ['ui', 'api', 'batch']

function parseEntry(entry: string): { id: string; tabs: ('ui' | 'api' | 'batch')[] | null } {
  const [id, suffix] = entry.split('|')
  if (!suffix) return { id, tabs: null }
  const tabs = suffix.split(',').filter(t => ['ui', 'api', 'batch'].includes(t)) as ('ui' | 'api' | 'batch')[]
  return { id, tabs: tabs.length === 3 ? null : tabs }
}

function buildEntry(id: string, tabs: ('ui' | 'api' | 'batch')[] | null): string {
  if (!tabs || tabs.length === 3) return id
  return `${id}|${tabs.join(',')}`
}

function getAllDescendantIds(modules: ModuleItem[], parentId: string): string[] {
  const ids: string[] = []
  for (const child of modules.filter(m => m.parentId === parentId)) {
    const hasChildren = modules.some(m => m.parentId === child.id)
    if (hasChildren) ids.push(...getAllDescendantIds(modules, child.id))
    else ids.push(child.id)
  }
  return ids
}

function resolvePresetIds(preset: Preset, allModules: ModuleItem[]): string[] {
  if (preset.exactIds) return preset.exactIds
  if (preset.parentGroupId) return getAllDescendantIds(allModules, preset.parentGroupId)
  return []
}

// ─── Tree types ───────────────────────────────────────────────
interface TreeNode { id: string; label: string; isGroup: boolean; children: TreeNode[] }

function buildTreeChildren(groupId: string, allModules: ModuleItem[], parentIds: Set<string>): TreeNode[] {
  return allModules.filter(m => m.parentId === groupId).map(child => {
    if (parentIds.has(child.id)) {
      return { id: child.id, label: child.label, isGroup: true, children: buildTreeChildren(child.id, allModules, parentIds) }
    }
    return { id: child.id, label: child.label, isGroup: false, children: [] }
  })
}

// ─── Main Component ───────────────────────────────────────────
export function ModuleAccessPicker({ open, onOpenChange, value, onChange, allModules, userName }: ModuleAccessPickerProps) {
  const [localValue, setLocalValue] = useState<string[]>(value)
  const [searchQuery, setSearchQuery] = useState('')
  const [tabOverrides, setTabOverrides] = useState<Record<string, ('ui' | 'api' | 'batch')[] | null>>(() => {
    const o: Record<string, ('ui' | 'api' | 'batch')[] | null> = {}
    for (const e of value) { const { id, tabs } = parseEntry(e); if (tabs) o[id] = tabs }
    return o
  })

  const handleOpenChange = useCallback((nextOpen: boolean) => {
    if (nextOpen) {
      setLocalValue(value)
      setSearchQuery('')
      const o: Record<string, ('ui' | 'api' | 'batch')[] | null> = {}
      for (const e of value) { const { id, tabs } = parseEntry(e); if (tabs) o[id] = tabs }
      setTabOverrides(o)
    }
    onOpenChange(nextOpen)
  }, [value, onOpenChange])

  const parentIds = useMemo(() => new Set(allModules.filter(m => m.parentId).map(m => m.parentId!)), [allModules])
  const topGroups = useMemo(() => allModules.filter(m => !m.parentId && parentIds.has(m.id)), [allModules, parentIds])
  const allLeaves = useMemo(() => allModules.filter(m => !parentIds.has(m.id)), [allModules, parentIds])
  const standaloneModules = useMemo(() => allModules.filter(m => !m.parentId && !parentIds.has(m.id)), [allModules, parentIds])
  const allSelectableIds = useMemo(() => allLeaves.map(m => m.id), [allLeaves])
  const totalModuleCount = allLeaves.length

  const presets: Preset[] = useMemo(() => [
    { id: 'full-access', label: 'Full Access', icon: <Shield className="size-3.5" />, parentGroupId: null, exactIds: ['all'] },
    { id: 'registration', label: 'Registration', icon: <Users className="size-3.5" />, parentGroupId: 'registration' },
    { id: 'common-settings', label: 'Common Settings', icon: <Settings className="size-3.5" />, parentGroupId: 'common-settings' },
    { id: 'commodity-settings', label: 'Commodity Settings', icon: <Building2 className="size-3.5" />, parentGroupId: 'commodity-settings' },
    { id: 'access', label: 'Access', icon: <Key className="size-3.5" />, parentGroupId: 'access' },
    { id: 'document', label: 'Document', icon: <FileText className="size-3.5" />, parentGroupId: 'document' },
    { id: 'private-b2b', label: 'Private B2B', icon: <Handshake className="size-3.5" />, parentGroupId: 'private-b2b' },
    { id: 'company-onboarding', label: 'Company Onboarding', icon: <Building2 className="size-3.5" />, parentGroupId: null, exactIds: ['company-onboarding'] },
  ], [])

  const isFullAccess = localValue.includes('all')

  const toggleModule = useCallback((modId: string) => {
    setLocalValue(prev => {
      if (prev.includes('all')) return allSelectableIds.filter(id => id !== modId)
      const ids = prev.map(e => e.split('|')[0])
      if (ids.includes(modId)) return prev.filter(e => e.split('|')[0] !== modId)
      return [...prev, modId]
    })
  }, [allSelectableIds])

  const togglePreset = useCallback((preset: Preset) => {
    if (preset.id === 'full-access') {
      setLocalValue(prev => prev.includes('all') ? [] : ['all'])
      return
    }
    const presetIds = resolvePresetIds(preset, allModules)
    if (!presetIds.length) return
    setLocalValue(prev => {
      if (prev.includes('all')) return allSelectableIds.filter(id => !presetIds.includes(id))
      const prevIds = prev.map(e => e.split('|')[0])
      const allPresetSelected = presetIds.every(id => prevIds.includes(id))
      if (allPresetSelected) return prev.filter(e => !presetIds.includes(e.split('|')[0]))
      return [...prev, ...presetIds.filter(id => !prevIds.includes(id))]
    })
  }, [allModules, allSelectableIds])

  const toggleGroup = useCallback((groupId: string) => {
    setLocalValue(prev => {
      const groupIds = getAllDescendantIds(allModules, groupId)
      if (!groupIds.length) return prev
      const prevIds = prev.map(e => e.split('|')[0])
      if (prev.includes('all')) return allSelectableIds.filter(id => !groupIds.includes(id))
      if (groupIds.every(id => prevIds.includes(id))) return prev.filter(e => !groupIds.includes(e.split('|')[0]))
      return [...prev, ...groupIds.filter(id => !prevIds.includes(id))]
    })
  }, [allModules, allSelectableIds])

  const selectedSet = useMemo(() => {
    if (isFullAccess) return new Set(allSelectableIds)
    return new Set(localValue.map(e => e.split('|')[0]))
  }, [isFullAccess, localValue, allSelectableIds])

  const selectedCount = isFullAccess ? totalModuleCount : localValue.filter(e => e !== 'all').length

  const moduleTree = useMemo(() => {
    const nodes: TreeNode[] = []
    for (const group of topGroups) {
      nodes.push({ id: group.id, label: group.label, isGroup: true, children: buildTreeChildren(group.id, allModules, parentIds) })
    }
    for (const mod of standaloneModules) {
      nodes.push({ id: mod.id, label: mod.label, isGroup: false, children: [] })
    }
    return nodes
  }, [topGroups, standaloneModules, allModules, parentIds])

  // Selected modules grouped by parent for the right panel
  const selectedModulesList = useMemo(() => {
    if (isFullAccess) return []
    return localValue.map(rawId => {
      const id = rawId.split('|')[0]
      const mod = allModules.find(m => m.id === id)
      return { id, label: mod?.label || id, parentLabel: mod?.parentLabel }
    })
  }, [isFullAccess, localValue, allModules])

  // Group selected modules by parent for display
  const groupedSelected = useMemo(() => {
    const groups: Record<string, { id: string; label: string; parentLabel: string | undefined }[]> = {}
    for (const mod of selectedModulesList) {
      const key = mod.parentLabel || '—'
      if (!groups[key]) groups[key] = []
      groups[key].push(mod)
    }
    return groups
  }, [selectedModulesList])

  const handleApply = useCallback(() => {
    const serialized = localValue.includes('all')
      ? localValue
      : localValue.map(e => { const id = e.split('|')[0]; return buildEntry(id, tabOverrides[id] ?? null) })
    onChange(serialized)
    onOpenChange(false)
  }, [localValue, tabOverrides, onChange, onOpenChange])

  const handleCancel = useCallback(() => {
    setLocalValue(value)
    setSearchQuery('')
    const o: Record<string, ('ui' | 'api' | 'batch')[] | null> = {}
    for (const e of value) { const { id, tabs } = parseEntry(e); if (tabs) o[id] = tabs }
    setTabOverrides(o)
    onOpenChange(false)
  }, [value, onOpenChange])

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[820px] max-h-[88vh] p-0 gap-0 flex flex-col" showCloseButton={false}>

        {/* ── Header ── */}
        <DialogHeader className="px-6 pt-5 pb-4 shrink-0 border-b border-gray-300 dark:border-gray-600">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="size-8 rounded-lg bg-[#E8F5E9] flex items-center justify-center">
                <Shield className="size-4 text-[#2E7D32]" />
              </div>
              <div>
                <DialogTitle className="font-['Poppins'] text-sm font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-1.5">
                  Module Access
                  {userName && <span className="font-normal text-gray-500 dark:text-gray-400">— {userName}</span>}
                </DialogTitle>
                <DialogDescription className="font-['Poppins'] text-[11px] text-gray-400 mt-0.5">
                  Select modules on the left, configure tab access on the right.
                </DialogDescription>
              </div>
            </div>
            <div className="flex items-center gap-1.5 bg-[#E8F5E9] dark:bg-green-900/30 rounded-lg px-3 py-1.5">
              <span className="font-['Poppins'] text-lg font-bold text-[#2E7D32]">{selectedCount}</span>
              <span className="font-['Poppins'] text-[10px] text-[#2E7D32] font-medium">modules<br/>selected</span>
            </div>
          </div>

          {/* ── Presets Row ── */}
          <div className="flex items-center gap-1.5 flex-wrap mt-3">
            <span className="font-['Poppins'] text-[10px] font-semibold uppercase tracking-wider text-gray-400 mr-1 shrink-0">Presets:</span>
            {presets.map(preset => {
              const resolvedIds = resolvePresetIds(preset, allModules)
              const isActive = preset.id === 'full-access'
                ? isFullAccess
                : !isFullAccess && resolvedIds.length > 0 && resolvedIds.every(id => selectedSet.has(id))
              return (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => togglePreset(preset)}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium font-['Poppins'] border transition-all cursor-pointer ${
                    isActive
                      ? 'bg-[#2E7D32] border-[#2E7D32] text-white'
                      : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-500 text-gray-600 dark:text-gray-300 hover:border-[#A5D6A7] hover:bg-[#F1F8E9] dark:hover:bg-green-900/20'
                  }`}
                >
                  {preset.icon}
                  {preset.label}
                  {isActive && <X className="size-2.5 ml-0.5" />}
                </button>
              )
            })}
          </div>
        </DialogHeader>

        {/* ── Two-column body ── */}
        <div className="flex flex-1 min-h-0 overflow-hidden">

          {/* LEFT: Module tree */}
          <div className="w-[30%] flex flex-col border-r border-gray-300 dark:border-gray-600 overflow-y-auto min-h-0 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
            {/* Search */}
            <div className="px-4 pt-3 pb-2 shrink-0 sticky top-0 bg-white dark:bg-gray-950 z-10">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-gray-400" />
                <Input
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Search modules…"
                  className="h-8 pl-8 text-xs font-['Poppins'] border-gray-200 dark:border-gray-500"
                />
                {searchQuery && (
                  <button type="button" onClick={() => setSearchQuery('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                    <X className="size-3.5" />
                  </button>
                )}
              </div>
            </div>

            {/* Tree */}
            {isFullAccess ? (
              <div className="flex flex-col items-center justify-center p-6 text-center">
                <div className="size-12 rounded-full bg-[#E8F5E9] flex items-center justify-center mb-3">
                  <Shield className="size-6 text-[#2E7D32]" />
                </div>
                <p className="font-['Poppins'] text-sm font-semibold text-[#1B5E20]">Full Access</p>
                <p className="font-['Poppins'] text-[11px] text-gray-400 mt-1">All {totalModuleCount} modules selected. Click the preset again to deselect.</p>
              </div>
            ) : (
              <TreePanel
                nodes={moduleTree}
                selectedSet={selectedSet}
                onToggleModule={toggleModule}
                onToggleGroup={toggleGroup}
                allModules={allModules}
                searchQuery={searchQuery}
                depth={0}
              />
            )}
          </div>

          {/* RIGHT: Access config */}
          <div className="w-[70%] flex flex-col min-h-0">
            <div className="px-4 pt-3 pb-2 shrink-0 border-b border-gray-300 dark:border-gray-600">
              <div className="flex items-center gap-1.5">
                <LayoutGrid className="size-3.5 text-[#2E7D32]" />
                <span className="font-['Poppins'] text-[11px] font-semibold text-gray-700 dark:text-gray-300">Tab Access per Module</span>
              </div>
              <p className="font-['Poppins'] text-[10px] text-gray-400 mt-0.5">Toggle which tabs each module exposes to the user.</p>
            </div>

            <div className="flex-1 overflow-y-auto min-h-0 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
              {isFullAccess ? (
                <div className="flex flex-col items-center justify-center h-full p-6 text-center">
                  <Shield className="size-5 text-[#A5D6A7] mb-2" />
                  <p className="font-['Poppins'] text-[11px] text-gray-400">Full access — all tabs enabled for all modules.</p>
                </div>
              ) : selectedModulesList.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full p-6 text-center">
                  <div className="size-10 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-2">
                    <LayoutGrid className="size-4 text-gray-400" />
                  </div>
                  <p className="font-['Poppins'] text-xs text-gray-400">No modules selected yet.</p>
                  <p className="font-['Poppins'] text-[10px] text-gray-300 dark:text-gray-600 mt-0.5">Pick modules from the left panel.</p>
                </div>
              ) : (
                <div className="divide-y-2 divide-gray-300 dark:divide-gray-500">
                  {Object.entries(groupedSelected).map(([groupLabel, mods]) => (
                    <div key={groupLabel}>
                      {/* Group label */}
                      <div className="px-4 py-1.5 bg-gray-50/70 dark:bg-gray-800/40">
                        <span className="font-['Poppins'] text-[10px] font-semibold uppercase tracking-wider text-gray-400">{groupLabel}</span>
                      </div>
                      {mods.map(mod => {
                        const allowedTabs = tabOverrides[mod.id] ?? null
                        const toggleTab = (tab: 'ui' | 'api' | 'batch') => {
                          const current = allowedTabs ?? ALL_TABS
                          const next = current.includes(tab) ? current.filter(t => t !== tab) : [...current, tab]
                          setTabOverrides(prev => ({ ...prev, [mod.id]: next.length === 3 ? null : next.length === 0 ? ['ui'] : next }))
                        }
                        return (
                          <div key={mod.id} className="px-4 py-2.5 flex items-center gap-3 hover:bg-gray-50/50 dark:hover:bg-gray-800/30 group border-b border-gray-300 dark:border-gray-600 last:border-b-0">
                            <div className="flex-1 min-w-0">
                              <span className="font-['Poppins'] text-xs text-gray-700 dark:text-gray-300 truncate block">{mod.label}</span>
                            </div>
                            <div className="flex items-center gap-1 shrink-0">
                              {TAB_CONFIG.map(({ key, label, icon, color }) => {
                                const active = !allowedTabs || allowedTabs.includes(key)
                                return (
                                  <button
                                    key={key}
                                    type="button"
                                    title={label}
                                    onClick={() => toggleTab(key)}
                                    className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium font-['Poppins'] border transition-all cursor-pointer`}
                                    style={active
                                      ? { backgroundColor: color, borderColor: color, color: 'white' }
                                      : { backgroundColor: 'transparent', borderColor: '#e5e7eb', color: '#9ca3af' }
                                    }
                                  >
                                    {icon}
                                    <span className="hidden xl:inline">{label}</span>
                                  </button>
                                )
                              })}
                              <button
                                type="button"
                                onClick={() => toggleModule(mod.id)}
                                className="ml-1 p-0.5 rounded text-gray-400 hover:text-red-500 hover:bg-red-50 dark:text-gray-500 dark:hover:text-red-400 dark:hover:bg-red-900/20 transition-colors"
                                title="Remove module"
                              >
                                <X className="size-3" />
                              </button>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quick-set all tabs */}
            {!isFullAccess && selectedModulesList.length > 0 && (
              <div className="px-4 py-2.5 border-t border-gray-300 dark:border-gray-600 shrink-0 bg-gray-50/50 dark:bg-gray-900/30">
                <div className="flex items-center gap-2">
                  <span className="font-['Poppins'] text-[10px] text-gray-400 shrink-0">Set all:</span>
                  {TAB_CONFIG.map(({ key, label, icon, color }) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => {
                        // Toggle: if all selected have this tab, remove from all; else add to all
                        const allHave = selectedModulesList.every(m => {
                          const t = tabOverrides[m.id] ?? null
                          return !t || t.includes(key)
                        })
                        setTabOverrides(prev => {
                          const next = { ...prev }
                          selectedModulesList.forEach(m => {
                            const current = next[m.id] ?? ALL_TABS
                            const updated = allHave
                              ? current.filter(t => t !== key)
                              : [...new Set([...current, key])] as ('ui'|'api'|'batch')[]
                            next[m.id] = updated.length === 3 ? null : updated.length === 0 ? ['ui'] : updated
                          })
                          return next
                        })
                      }}
                      className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium font-['Poppins'] border transition-all cursor-pointer border-gray-200 dark:border-gray-500 text-gray-500 hover:text-white"
                      style={{ '--hover-color': color } as React.CSSProperties}
                      onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = color; (e.currentTarget as HTMLButtonElement).style.borderColor = color; (e.currentTarget as HTMLButtonElement).style.color = 'white' }}
                      onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = ''; (e.currentTarget as HTMLButtonElement).style.borderColor = ''; (e.currentTarget as HTMLButtonElement).style.color = '' }}
                    >
                      {icon} {label}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Footer ── */}
        <DialogFooter className="px-4 py-2 border-t border-gray-300 dark:border-gray-600 shrink-0 bg-white dark:bg-gray-950 flex items-center justify-between">
          <Button type="button" variant="outline" onClick={handleCancel} className="font-['Poppins'] text-[11px] h-7 px-3">
            Cancel
          </Button>
          <Button type="button" onClick={handleApply} className="font-['Poppins'] text-[11px] h-7 px-3 text-white bg-[#2E7D32] hover:bg-[#1B5E20]">
            Apply — {selectedCount} module{selectedCount !== 1 ? 's' : ''}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Tree Panel (left column) ─────────────────────────────────
function TreePanel({
  nodes, selectedSet, onToggleModule, onToggleGroup, allModules, searchQuery, depth,
}: {
  nodes: TreeNode[]
  selectedSet: Set<string>
  onToggleModule: (id: string) => void
  onToggleGroup: (id: string) => void
  allModules: ModuleItem[]
  searchQuery: string
  depth: number
}) {
  const parentIds = useMemo(() => new Set(allModules.filter(m => m.parentId).map(m => m.parentId!)), [allModules])

  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())

  const toggleExpand = useCallback((id: string) => {
    setExpandedGroups(prev => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next })
  }, [])

  const filteredNodes = useMemo(() => {
    if (!searchQuery.trim()) return nodes
    const q = searchQuery.toLowerCase()
    function matches(n: TreeNode): boolean {
      return n.label.toLowerCase().includes(q) || n.id.toLowerCase().includes(q) || n.children.some(matches)
    }
    return nodes.filter(matches)
  }, [nodes, searchQuery])

  if (!filteredNodes.length) {
    return (
      <div className="px-4 py-8 text-center">
        <p className="font-['Poppins'] text-xs text-gray-400">{searchQuery ? 'No modules match.' : 'No modules available.'}</p>
      </div>
    )
  }

  return (
    <div>
      {filteredNodes.map(node => {
        if (node.isGroup) {
          const isExpanded = expandedGroups.has(node.id)
          const groupIds = getAllDescendantIds(allModules, node.id)
          const allSel = groupIds.length > 0 && groupIds.every(id => selectedSet.has(id))
          const someSel = groupIds.some(id => selectedSet.has(id))
          const selCount = groupIds.filter(id => selectedSet.has(id)).length

          return (
            <div key={node.id}>
              <button
                type="button"
                onClick={() => onToggleGroup(node.id)}
                className={`w-full flex items-center gap-2 py-2 text-left transition-colors cursor-pointer border-b border-gray-300 dark:border-gray-600 ${
                  depth === 0
                    ? 'bg-gray-50 dark:bg-gray-900/40 hover:bg-[#F1F8E9] dark:hover:bg-green-900/10'
                    : 'hover:bg-[#F9FBE7] dark:hover:bg-green-900/10'
                }`}
                style={{ paddingLeft: `${12 + depth * 16}px`, paddingRight: '12px' }}
              >
                <span
                  role="button"
                  tabIndex={0}
                  onClick={e => { e.stopPropagation(); toggleExpand(node.id) }}
                  onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); toggleExpand(node.id) } }}
                  className="p-0.5 rounded hover:bg-[#C8E6C9] cursor-pointer focus:outline-none"
                  aria-label={isExpanded ? 'Collapse' : 'Expand'}
                >
                  <ChevronRight className={`size-3.5 text-[#2E7D32] transition-transform ${isExpanded ? 'rotate-90' : ''} pointer-events-none`} />
                </span>
                <div className={`size-3.5 rounded border-2 flex items-center justify-center shrink-0 transition-colors ${
                  allSel ? 'bg-[#2E7D32] border-[#2E7D32]' : someSel ? 'bg-[#66BB6A] border-[#2E7D32]' : 'border-gray-300 dark:border-gray-600'
                }`}>
                  {allSel && <Check className="size-2 text-white" />}
                  {someSel && !allSel && <div className="size-1.5 rounded-sm bg-white" />}
                </div>
                <span className={`font-['Poppins'] text-xs font-semibold flex-1 ${depth === 0 ? 'text-gray-800 dark:text-gray-200' : 'text-[#2E7D32]'}`}>
                  {node.label}
                </span>
                <span className={`font-['Poppins'] text-[10px] shrink-0 tabular-nums ${selCount > 0 ? 'text-[#2E7D32] font-medium' : 'text-gray-400'}`}>
                  {selCount}/{groupIds.length}
                </span>
              </button>
              {isExpanded && (
                <TreePanel
                  nodes={node.children}
                  selectedSet={selectedSet}
                  onToggleModule={onToggleModule}
                  onToggleGroup={onToggleGroup}
                  allModules={allModules}
                  searchQuery={searchQuery}
                  depth={depth + 1}
                />
              )}
            </div>
          )
        }

        // Leaf
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase()
          if (!node.label.toLowerCase().includes(q) && !node.id.toLowerCase().includes(q)) return null
        }

        const isSelected = selectedSet.has(node.id)
        return (
          <button
            key={node.id}
            type="button"
            onClick={() => onToggleModule(node.id)}
            className={`w-full flex items-center gap-2 py-1.5 text-left transition-colors cursor-pointer border-b border-gray-300 dark:border-gray-600 ${
              isSelected ? 'bg-[#E8F5E9] dark:bg-green-900/15 hover:bg-[#DCEDC8]' : 'hover:bg-gray-50 dark:hover:bg-gray-800/30'
            }`}
            style={{ paddingLeft: `${12 + depth * 16 + 22}px`, paddingRight: '12px' }}
          >
            <div className={`size-3.5 rounded border-2 flex items-center justify-center shrink-0 transition-colors ${
              isSelected ? 'bg-[#2E7D32] border-[#2E7D32]' : 'border-gray-300 dark:border-gray-600'
            }`}>
              {isSelected && <Check className="size-2 text-white" />}
            </div>
            <span className={`font-['Poppins'] text-xs flex-1 ${isSelected ? 'text-[#1B5E20] font-medium dark:text-green-300' : 'text-gray-600 dark:text-gray-400'}`}>
              {node.label}
            </span>
          </button>
        )
      })}
    </div>
  )
}
