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
import { Badge } from '@/components/ui/badge'
import {
  Shield,
  Zap,
  Settings,
  Building2,
  Key,
  Search,
  X,
  Check,
  ChevronRight,
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

// ─── Preset Definition ────────────────────────────────────────
interface Preset {
  id: string
  label: string
  description: string
  icon: React.ReactNode
  /** A parent module ID — we resolve all descendant leaf IDs at runtime */
  parentGroupId: string | null
  /** If set, these exact IDs are used instead of parentGroupId resolution */
  exactIds?: string[]
}

// ─── Color tokens ─────────────────────────────────────────────
const COLORS = {
  primary: '#2E7D32',
  light: '#E8F5E9',
  dark: '#1B5E20',
  border: '#A5D6A7',
  hover: '#C8E6C9',
  selected: '#66BB6A',
  chip: '#F1F8E9',
  chipBorder: '#C8E6C9',
  chipHover: '#DCEDC8',
} as const

// ─── Helper: get ALL descendant module IDs (not just direct children) ──
function getAllDescendantIds(modules: ModuleItem[], parentId: string): string[] {
  const ids: string[] = []
  const directChildren = modules.filter(m => m.parentId === parentId)
  for (const child of directChildren) {
    // Check if this child itself has children
    const grandChildren = modules.filter(m => m.parentId === child.id)
    if (grandChildren.length > 0) {
      // It's a sub-group, recurse
      ids.push(...getAllDescendantIds(modules, child.id))
    } else {
      // It's a leaf module, add it
      ids.push(child.id)
    }
  }
  return ids
}

// ─── Helper: resolve preset to actual module IDs ──────────
function resolvePresetIds(preset: Preset, allModules: ModuleItem[]): string[] {
  if (preset.exactIds) return preset.exactIds
  if (preset.parentGroupId) {
    return getAllDescendantIds(allModules, preset.parentGroupId)
  }
  return []
}

// ─── Component ────────────────────────────────────────────────
export function ModuleAccessPicker({
  open,
  onOpenChange,
  value,
  onChange,
  allModules,
  userName,
}: ModuleAccessPickerProps) {
  const [localValue, setLocalValue] = useState<string[]>(value)
  const [searchQuery, setSearchQuery] = useState('')

  // Sync local value when dialog opens
  const handleOpenChange = useCallback(
    (nextOpen: boolean) => {
      if (nextOpen) {
        setLocalValue(value)
        setSearchQuery('')
      }
      onOpenChange(nextOpen)
    },
    [value, onOpenChange]
  )

  // ─── Build tree structure from flat module list ──────────
  // "Groups" = modules that have children (parentId references them)
  // "Leaves" = modules that have no children referencing them
  const parentIds = useMemo(
    () => new Set(allModules.filter(m => m.parentId).map(m => m.parentId!)),
    [allModules]
  )

  // Top-level groups: have children but no parentId themselves
  const topGroups = useMemo(
    () => allModules.filter(m => !m.parentId && parentIds.has(m.id)),
    [allModules, parentIds]
  )

  // All leaf modules (no children reference them)
  const allLeaves = useMemo(
    () => allModules.filter(m => !parentIds.has(m.id)),
    [allModules, parentIds]
  )

  // Standalone modules: no parentId, no children (neither group nor child)
  const standaloneModules = useMemo(
    () => allModules.filter(m => !m.parentId && !parentIds.has(m.id)),
    [allModules, parentIds]
  )

  const totalModuleCount = allLeaves.length + standaloneModules.length

  // ─── Presets (resolved dynamically) ──────────────────────
  const presets: Preset[] = useMemo(() => [
    {
      id: 'full-access',
      label: 'Full Access',
      description: `All ${totalModuleCount} modules`,
      icon: <Shield className="size-4" style={{ color: COLORS.primary }} />,
      parentGroupId: null,
      exactIds: ['all'],
    },
    {
      id: 'registration-only',
      label: 'Registration',
      description: `${getAllDescendantIds(allModules, 'registration').length} modules`,
      icon: <Zap className="size-4" style={{ color: COLORS.primary }} />,
      parentGroupId: 'registration',
    },
    {
      id: 'common-settings-only',
      label: 'Common Settings',
      description: `${getAllDescendantIds(allModules, 'common-settings').length} modules`,
      icon: <Settings className="size-4" style={{ color: COLORS.primary }} />,
      parentGroupId: 'common-settings',
    },
    {
      id: 'commodity-settings-only',
      label: 'Commodity Settings',
      description: `${getAllDescendantIds(allModules, 'commodity-settings').length} modules`,
      icon: <Building2 className="size-4" style={{ color: COLORS.primary }} />,
      parentGroupId: 'commodity-settings',
    },
    {
      id: 'access-only',
      label: 'Access',
      description: `${getAllDescendantIds(allModules, 'access').length} modules`,
      icon: <Key className="size-4" style={{ color: COLORS.primary }} />,
      parentGroupId: 'access',
    },
    {
      id: 'company-onboarding',
      label: 'Company Onboarding',
      description: `${getAllDescendantIds(allModules, 'company-onboarding').length || 1} module`,
      icon: <Building2 className="size-4" style={{ color: COLORS.primary }} />,
      parentGroupId: null,
      exactIds: ['company-onboarding'],
    },
  ], [allModules, totalModuleCount])

  // ─── Selection logic ─────────────────────────────────────
  const isFullAccess = localValue.includes('all')

  const removeModule = useCallback((modId: string) => {
    setLocalValue(prev => prev.filter(m => m !== modId))
  }, [])

  const toggleModule = useCallback((modId: string) => {
    setLocalValue(prev => {
      if (prev.includes('all')) {
        // Convert "all" to explicit list and deselect the clicked module
        const allIds = allLeaves.map(m => m.id).concat(standaloneModules.map(m => m.id))
        return allIds.filter(id => id !== modId)
      }
      if (prev.includes(modId)) return prev.filter(m => m !== modId)
      return [...prev, modId]
    })
  }, [allLeaves, standaloneModules])

  const togglePreset = useCallback((preset: Preset) => {
    // Full Access is a special case
    if (preset.id === 'full-access') {
      setLocalValue(prev => {
        if (prev.includes('all')) return [] // Deselect all
        return ['all'] // Select all
      })
      return
    }

    const presetIds = resolvePresetIds(preset, allModules)
    setLocalValue(prev => {
      // If "all" is selected, convert to explicit and deselect this preset's modules
      if (prev.includes('all')) {
        const allIds = allLeaves.map(m => m.id).concat(standaloneModules.map(m => m.id))
        return allIds.filter(id => !presetIds.includes(id))
      }

      // Check if ALL preset modules are already selected
      const allPresetSelected = presetIds.length > 0 && presetIds.every(id => prev.includes(id))
      if (allPresetSelected) {
        // Deselect: remove this preset's modules from current selection
        return prev.filter(id => !presetIds.includes(id))
      }
      // Select: add this preset's modules to current selection (keep existing)
      const toAdd = presetIds.filter(id => !prev.includes(id))
      return [...prev, ...toAdd]
    })
  }, [allModules, allLeaves, standaloneModules])

  const toggleGroup = useCallback((groupId: string) => {
    setLocalValue(prev => {
      const groupIds = getAllDescendantIds(allModules, groupId)
      const allSelected = groupIds.every(id => prev.includes(id))
      if (prev.includes('all')) {
        // Switch from "all" to explicit: deselect this group
        const everything = allLeaves.map(m => m.id)
        return everything.filter(id => !groupIds.includes(id))
      }
      if (allSelected) {
        // Deselect all in group
        return prev.filter(id => !groupIds.includes(id))
      }
      // Select all in group
      const toAdd = groupIds.filter(id => !prev.includes(id))
      return [...prev, ...toAdd]
    })
  }, [allModules, allLeaves])

  // ─── Selected set for checking ───────────────────────────
  const selectedSet = useMemo(() => {
    if (isFullAccess) return new Set(allLeaves.map(m => m.id))
    return new Set(localValue)
  }, [isFullAccess, localValue, allLeaves])

  const selectedCount = isFullAccess ? totalModuleCount : localValue.filter(id => id !== 'all').length

  // ─── Build selected tags ────────────────────────────────
  const selectedTags = useMemo(() => {
    if (isFullAccess) return [{ id: 'all', label: 'Full Access — All Modules' }]
    return localValue.map(id => {
      const mod = allModules.find(m => m.id === id)
      return { id, label: mod?.label || id }
    })
  }, [isFullAccess, localValue, allModules])

  // ─── Build tree for the module list ─────────────────────
  const moduleTree = useMemo(() => {
    const nodes: TreeNode[] = []

    // Top-level groups (Registration, Common Settings, etc.)
    for (const group of topGroups) {
      const children = buildTreeChildren(group.id, allModules, parentIds)
      nodes.push({ id: group.id, label: group.label, isGroup: true, children })
    }

    // Standalone modules
    for (const mod of standaloneModules) {
      nodes.push({ id: mod.id, label: mod.label, isGroup: false, children: [] })
    }

    return nodes
  }, [topGroups, standaloneModules, allModules, parentIds])

  // ─── Apply / Cancel ────────────────────────────────────
  const handleApply = useCallback(() => {
    onChange(localValue)
    onOpenChange(false)
  }, [localValue, onChange, onOpenChange])

  const handleCancel = useCallback(() => {
    // Reset to original value and close
    setLocalValue(value)
    setSearchQuery('')
    onOpenChange(false)
  }, [value, onOpenChange])

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="sm:max-w-[640px] max-h-[85vh] p-0 gap-0 flex flex-col"
        showCloseButton={false}
      >
        {/* Header */}
        <DialogHeader className="px-6 pt-5 pb-3 shrink-0 border-b border-gray-100 dark:border-gray-700">
          <DialogTitle className="font-['Poppins'] text-base flex items-center gap-2 text-[#1B5E20]">
            <Shield className="size-5 text-[#2E7D32]" />
            Module Access
            {userName && (
              <span className="font-['Manrope'] font-normal text-sm text-[#666]">
                — {userName}
              </span>
            )}
          </DialogTitle>
          <DialogDescription className="font-['Manrope'] text-xs text-[#888]">
            Choose preset access levels or pick individual modules.
          </DialogDescription>
        </DialogHeader>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto min-h-0 overscroll-contain">
          <div className="px-6 py-4 space-y-5">
            {/* ── Preset Cards ── */}
            <div>
              <span className="font-['Poppins'] text-[11px] font-semibold uppercase tracking-wider text-[#2E7D32] mb-2 block">
                Quick Presets
              </span>
              <div className="grid grid-cols-3 gap-2">
                {presets.map(preset => {
                  const resolvedIds = resolvePresetIds(preset, allModules)
                  const isFullAccessPreset = preset.id === 'full-access'
                  const isActive = isFullAccessPreset
                    ? isFullAccess
                    : !isFullAccess &&
                      resolvedIds.length > 0 &&
                      resolvedIds.every(id => selectedSet.has(id))

                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => togglePreset(preset)}
                      className={`group relative text-left rounded-lg border p-2.5 transition-all duration-150 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#2E7D32] ${
                        isActive
                          ? 'border-[#2E7D32] bg-[#E8F5E9]'
                          : 'border-[#A5D6A7] hover:bg-[#C8E6C9]'
                      }`}
                    >
                      <div className="flex items-center gap-1.5 mb-0.5">
                        {preset.icon}
                        <span className="font-['Poppins'] text-[11px] font-semibold text-[#1B5E20]">
                          {preset.label}
                        </span>
                      </div>
                      <span className="font-['Manrope'] text-[10px] text-[#777]">
                        {preset.description}
                      </span>
                      {isActive && (
                        <div className="absolute top-1.5 right-1.5 rounded-full size-4 flex items-center justify-center bg-[#2E7D32]">
                          <Check className="size-2.5 text-white" />
                        </div>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* ── Search + Selected Tags ── */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-[#999]" />
                  <Input
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    placeholder="Search modules..."
                    className="h-8 pl-8 text-xs font-['Manrope'] border-[#A5D6A7]"
                  />
                </div>
                <Badge
                  variant="secondary"
                  className="font-['Manrope'] text-[10px] shrink-0 px-2 py-0.5 bg-[#E8F5E9] text-[#1B5E20]"
                >
                  {selectedCount} selected
                </Badge>
              </div>

              {/* Selected tags */}
              {selectedTags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 min-h-[24px] max-h-[72px] overflow-y-auto">
                  {selectedTags.map(tag => (
                    <Badge
                      key={tag.id}
                      variant="secondary"
                      className="font-['Manrope'] text-[10px] pl-2 pr-1 py-0.5 flex items-center gap-1 bg-[#E8F8E9] text-[#1B5E20] border border-[#C8E6C9]"
                    >
                      {tag.label}
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); removeModule(tag.id) }}
                        className="rounded-full p-0.5 transition-colors hover:bg-[#C8E6C9] focus:outline-none"
                        aria-label={`Remove ${tag.label}`}
                      >
                        <X className="size-2.5 text-[#2E7D32]" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            {/* ── Module Tree ── */}
            {isFullAccess ? (
              <div className="rounded-lg p-4 text-center bg-[#E8F5E9] border border-[#A5D6A7]">
                <Shield className="size-6 text-[#2E7D32] mx-auto mb-1" />
                <p className="font-['Manrope'] text-xs text-[#1B5E20] font-medium">
                  Full access granted — all {totalModuleCount} modules selected.
                </p>
                <p className="font-['Manrope'] text-[10px] text-[#777] mt-0.5">
                  Click any preset or deselect &quot;all&quot; tag to pick individual modules.
                </p>
              </div>
            ) : (
              <div>
                <span className="font-['Poppins'] text-[11px] font-semibold uppercase tracking-wider text-[#2E7D32] mb-2 block">
                  All Modules
                </span>
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden max-h-[280px] overflow-y-auto">
                  <ModuleTreeNode
                    nodes={moduleTree}
                    selectedSet={selectedSet}
                    onToggleModule={toggleModule}
                    onToggleGroup={toggleGroup}
                    allModules={allModules}
                    parentIds={parentIds}
                    searchQuery={searchQuery}
                    depth={0}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer — pinned at bottom */}
        <DialogFooter className="px-6 py-3 border-t border-gray-100 dark:border-gray-700 shrink-0 bg-white dark:bg-gray-900">
          <Button
            type="button"
            variant="outline"
            onClick={handleCancel}
            className="font-['Roboto'] text-xs h-8"
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleApply}
            className="font-['Roboto'] text-xs h-8 text-white bg-[#2E7D32] hover:bg-[#1B5E20]"
          >
            Apply ({selectedCount} module{selectedCount !== 1 ? 's' : ''})
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Tree Node Interface ─────────────────────────────────
interface TreeNode {
  id: string
  label: string
  isGroup: boolean
  children: TreeNode[]
}

// ─── Helper: Build children tree for a group ──────────────
function buildTreeChildren(
  groupId: string,
  allModules: ModuleItem[],
  parentIds: Set<string>
): TreeNode[] {
  const children: TreeNode[] = []
  const directChildren = allModules.filter(m => m.parentId === groupId)

  for (const child of directChildren) {
    if (parentIds.has(child.id)) {
      // It's a sub-group, recurse
      const subChildren = buildTreeChildren(child.id, allModules, parentIds)
      children.push({ id: child.id, label: child.label, isGroup: true, children: subChildren })
    } else {
      children.push({ id: child.id, label: child.label, isGroup: false, children: [] })
    }
  }

  return children
}

// ─── Recursive Tree Node Component ───────────────────────
function ModuleTreeNode({
  nodes,
  selectedSet,
  onToggleModule,
  onToggleGroup,
  allModules,
  parentIds,
  searchQuery,
  depth,
}: {
  nodes: TreeNode[]
  selectedSet: Set<string>
  onToggleModule: (id: string) => void
  onToggleGroup: (id: string) => void
  allModules: ModuleItem[]
  parentIds: Set<string>
  searchQuery: string
  depth: number
}) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(() => {
    // Auto-expand all groups by default
    const ids = new Set<string>()
    function collectGroupIds(nodes: TreeNode[]) {
      for (const n of nodes) {
        if (n.isGroup) { ids.add(n.id); collectGroupIds(n.children) }
      }
    }
    collectGroupIds(nodes)
    return ids
  })

  const toggleExpand = useCallback((id: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  // Filter by search
  const filteredNodes = useMemo(() => {
    if (!searchQuery.trim()) return nodes
    const q = searchQuery.toLowerCase().trim()

    function matchesSearch(node: TreeNode): boolean {
      if (node.label.toLowerCase().includes(q) || node.id.toLowerCase().includes(q)) return true
      return node.children.some(c => matchesSearch(c))
    }

    return nodes.filter(n => matchesSearch(n))
  }, [nodes, searchQuery])

  if (filteredNodes.length === 0) {
    return (
      <div className="px-4 py-6 text-center">
        <p className="font-['Manrope'] text-xs text-[#999]">
          {searchQuery ? 'No modules match your search.' : 'No modules available.'}
        </p>
      </div>
    )
  }

  return (
    <div>
      {filteredNodes.map(node => {
        if (node.isGroup) {
          const isExpanded = expandedGroups.has(node.id)
          const groupDescendantIds = getAllDescendantIds(allModules, node.id)
          const allSelected = groupDescendantIds.length > 0 && groupDescendantIds.every(id => selectedSet.has(id))
          const someSelected = groupDescendantIds.some(id => selectedSet.has(id))
          const selectedInGroup = groupDescendantIds.filter(id => selectedSet.has(id)).length

          return (
            <div key={node.id}>
              {/* Group Header — clickable to select/deselect whole group */}
              <button
                type="button"
                onClick={() => onToggleGroup(node.id)}
                className={`w-full flex items-center gap-2 px-4 py-2 text-left transition-colors cursor-pointer border-b border-gray-100 dark:border-gray-700/50 ${
                  depth === 0
                    ? 'bg-[#F1F8E9] dark:bg-green-900/20 hover:bg-[#DCEDC8] dark:hover:bg-green-900/30'
                    : 'bg-gray-50 dark:bg-gray-800/50 hover:bg-[#F1F8E9] dark:hover:bg-green-900/10'
                }`}
                style={{ paddingLeft: `${16 + depth * 20}px` }}
              >
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); toggleExpand(node.id) }}
                  className="p-0.5 rounded hover:bg-[#C8E6C9] dark:hover:bg-green-800/30 cursor-pointer"
                  aria-label={isExpanded ? 'Collapse' : 'Expand'}
                >
                  <ChevronRight
                    className={`size-3.5 text-[#2E7D32] transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`}
                  />
                </button>

                {/* Checkbox indicator */}
                <div className={`size-4 rounded border-2 flex items-center justify-center shrink-0 transition-colors ${
                  allSelected
                    ? 'bg-[#2E7D32] border-[#2E7D32]'
                    : someSelected
                      ? 'bg-[#66BB6A] border-[#2E7D32]'
                      : 'border-gray-300 dark:border-gray-600'
                }`}>
                  {allSelected && <Check className="size-2.5 text-white" />}
                  {someSelected && !allSelected && (
                    <div className="size-1.5 rounded-sm bg-white" />
                  )}
                </div>

                <span className={`font-['Poppins'] text-xs font-semibold flex-1 ${
                  depth === 0 ? 'text-[#1B5E20]' : 'text-[#2E7D32]'
                }`}>
                  {node.label}
                </span>

                <span className="font-['Manrope'] text-[10px] text-[#999] shrink-0">
                  {selectedInGroup}/{groupDescendantIds.length}
                </span>
              </button>

              {/* Children */}
              {isExpanded && (
                <ModuleTreeNode
                  nodes={node.children}
                  selectedSet={selectedSet}
                  onToggleModule={onToggleModule}
                  onToggleGroup={onToggleGroup}
                  allModules={allModules}
                  parentIds={parentIds}
                  searchQuery={searchQuery}
                  depth={depth + 1}
                />
              )}
            </div>
          )
        }

        // Leaf module
        const isSelected = selectedSet.has(node.id)
        // Apply search filter
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase().trim()
          if (!node.label.toLowerCase().includes(q) && !node.id.toLowerCase().includes(q)) {
            return null
          }
        }

        return (
          <button
            key={node.id}
            type="button"
            onClick={() => onToggleModule(node.id)}
            className={`w-full flex items-center gap-2 px-4 py-1.5 text-left transition-colors cursor-pointer border-b border-gray-50 dark:border-gray-800 ${
              isSelected
                ? 'bg-[#E8F5E9] dark:bg-green-900/20'
                : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
            }`}
            style={{ paddingLeft: `${16 + depth * 20 + 24}px` }}
          >
            {/* Checkbox */}
            <div className={`size-3.5 rounded border-2 flex items-center justify-center shrink-0 transition-colors ${
              isSelected
                ? 'bg-[#2E7D32] border-[#2E7D32]'
                : 'border-gray-300 dark:border-gray-600'
            }`}>
              {isSelected && <Check className="size-2 text-white" />}
            </div>

            <span className={`font-['Manrope'] text-xs flex-1 ${
              isSelected ? 'text-[#1B5E20] font-medium' : 'text-[#555] dark:text-gray-300'
            }`}>
              {node.label}
            </span>
          </button>
        )
      })}
    </div>
  )
}
