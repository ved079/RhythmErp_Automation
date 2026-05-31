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
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Shield,
  Zap,
  Settings,
  Building2,
  Key,
  Search,
  X,
  Plus,
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
  moduleIds: string[]
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

// ─── Helper: recursively get all leaf module IDs under a parent ──
function getLeafIds(modules: ModuleItem[], parentId: string): string[] {
  const directChildren = modules.filter(m => m.parentId === parentId)
  const leaves: string[] = []
  for (const child of directChildren) {
    const subLeaves = getLeafIds(modules, child.id)
    if (subLeaves.length > 0) {
      leaves.push(...subLeaves)
    } else {
      leaves.push(child.id)
    }
  }
  return leaves
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

  // Build the flat list of selectable modules (leaf modules + standalone parents)
  const selectableModules = useMemo(() => {
    const parentIds = new Set(allModules.filter(m => m.parentId).map(m => m.parentId!))
    return allModules.filter(m => !parentIds.has(m.id))
  }, [allModules])

  // Group modules by parentId for display
  const modulesByParent = useMemo(() => {
    const groups: Record<string, ModuleItem[]> = {}
    for (const mod of allModules) {
      const key = mod.parentId || '__standalone__'
      if (!groups[key]) groups[key] = []
      groups[key].push(mod)
    }
    return groups
  }, [allModules])

  // Standalone modules (no parentId, no children)
  const standaloneModules = useMemo(() => {
    const parentIds = new Set(allModules.filter(m => m.parentId).map(m => m.parentId!))
    return allModules.filter(m => !m.parentId && !parentIds.has(m.id))
  }, [allModules])

  // Parent modules (modules that have children)
  const parentModules = useMemo(() => {
    const parentIds = new Set(allModules.filter(m => m.parentId).map(m => m.parentId!))
    return allModules.filter(m => parentIds.has(m.id))
  }, [allModules])

  // All selectable IDs (excluding 'all')
  const allSelectableIds = useMemo(
    () => selectableModules.map(m => m.id),
    [selectableModules]
  )

  const totalModuleCount = allSelectableIds.length

  // ─── Presets ──────────────────────────────────────────────
  const presets: Preset[] = useMemo(() => {
    const registrationIds = getLeafIds(allModules, 'registration')
    const commonSettingsIds = getLeafIds(allModules, 'common-settings')
    const commoditySettingsIds = getLeafIds(allModules, 'commodity-settings')
    const accessIds = getLeafIds(allModules, 'access')

    return [
      {
        id: 'full-access',
        label: 'Full Access',
        description: `All ${totalModuleCount} modules`,
        icon: <Shield className="size-5" style={{ color: COLORS.primary }} />,
        moduleIds: ['all'],
      },
      {
        id: 'registration-only',
        label: 'Registration Only',
        description: `${registrationIds.length} modules`,
        icon: <Zap className="size-5" style={{ color: COLORS.primary }} />,
        moduleIds: registrationIds,
      },
      {
        id: 'common-settings-only',
        label: 'Common Settings Only',
        description: `${commonSettingsIds.length} modules`,
        icon: <Settings className="size-5" style={{ color: COLORS.primary }} />,
        moduleIds: commonSettingsIds,
      },
      {
        id: 'commodity-settings-only',
        label: 'Commodity Settings Only',
        description: `${commoditySettingsIds.length} modules`,
        icon: <Building2 className="size-5" style={{ color: COLORS.primary }} />,
        moduleIds: commoditySettingsIds,
      },
      {
        id: 'access-only',
        label: 'Access Only',
        description: `${accessIds.length} modules`,
        icon: <Key className="size-5" style={{ color: COLORS.primary }} />,
        moduleIds: accessIds,
      },
      {
        id: 'company-onboarding',
        label: 'Company Onboarding',
        description: '1 module',
        icon: <Building2 className="size-5" style={{ color: COLORS.primary }} />,
        moduleIds: ['company-onboarding'],
      },
    ]
  }, [allModules, totalModuleCount])

  // ─── Selection logic ─────────────────────────────────────
  const isFullAccess = localValue.includes('all')

  const addModule = useCallback((modId: string) => {
    setLocalValue(prev => {
      if (prev.includes('all')) {
        // If currently "all", switch to just this module
        return [modId]
      }
      if (prev.includes(modId)) return prev
      return [...prev, modId]
    })
  }, [])

  const removeModule = useCallback((modId: string) => {
    setLocalValue(prev => prev.filter(m => m !== modId))
  }, [])

  const applyPreset = useCallback((preset: Preset) => {
    setLocalValue(preset.moduleIds)
  }, [])

  // ─── Available modules (filtered by search, excluding already selected) ──
  const selectedSet = useMemo(() => {
    if (isFullAccess) return new Set(allSelectableIds)
    return new Set(localValue)
  }, [isFullAccess, localValue, allSelectableIds])

  const filteredAvailable = useMemo(() => {
    if (isFullAccess) return []

    const query = searchQuery.toLowerCase().trim()
    const modules = selectableModules.filter(m => !selectedSet.has(m.id))

    if (!query) return modules

    return modules.filter(
      m =>
        m.label.toLowerCase().includes(query) ||
        m.id.toLowerCase().includes(query) ||
        (m.parentLabel && m.parentLabel.toLowerCase().includes(query))
    )
  }, [isFullAccess, selectableModules, selectedSet, searchQuery])

  // ─── Selected count for display ─────────────────────────
  const selectedCount = isFullAccess ? totalModuleCount : localValue.length

  // ─── Build selected tags ────────────────────────────────
  const selectedTags = useMemo(() => {
    if (isFullAccess) {
      return [{ id: 'all', label: 'Full Access — All Modules' }]
    }
    return localValue.map(id => {
      const mod = allModules.find(m => m.id === id)
      return { id, label: mod?.label || id }
    })
  }, [isFullAccess, localValue, allModules])

  // ─── Apply / Cancel ────────────────────────────────────
  const handleApply = useCallback(() => {
    onChange(localValue)
    onOpenChange(false)
  }, [localValue, onChange, onOpenChange])

  const handleCancel = useCallback(() => {
    onOpenChange(false)
  }, [onOpenChange])

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="sm:max-w-[620px] p-0 gap-0 overflow-hidden"
        showCloseButton={false}
      >
        {/* Header */}
        <DialogHeader className="px-6 pt-6 pb-0">
          <DialogTitle
            className="font-['Poppins'] text-base flex items-center gap-2"
            style={{ color: COLORS.dark }}
          >
            <Shield className="size-5" style={{ color: COLORS.primary }} />
            Module Access
            {userName && (
              <span className="font-['Manrope'] font-normal text-sm" style={{ color: '#666' }}>
                — {userName}
              </span>
            )}
          </DialogTitle>
          <DialogDescription className="font-['Manrope'] text-xs" style={{ color: '#888' }}>
            Choose preset access levels or pick individual modules.
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 py-4 space-y-4">
          {/* Preset Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
            {presets.map(preset => {
              const isActive =
                isFullAccess && preset.id === 'full-access'
                  ? true
                  : !isFullAccess &&
                    preset.moduleIds.length > 0 &&
                    preset.moduleIds.length === localValue.length &&
                    preset.moduleIds.every(id => localValue.includes(id))

              return (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => applyPreset(preset)}
                  className="group relative text-left rounded-lg border p-3 transition-all duration-150 cursor-pointer focus:outline-none focus-visible:ring-2"
                  style={{
                    borderColor: isActive ? COLORS.primary : COLORS.border,
                    backgroundColor: isActive ? COLORS.light : 'transparent',
                  }}
                  onMouseEnter={e => {
                    if (!isActive) {
                      ;(e.currentTarget as HTMLElement).style.backgroundColor = COLORS.hover
                    }
                  }}
                  onMouseLeave={e => {
                    if (!isActive) {
                      ;(e.currentTarget as HTMLElement).style.backgroundColor = 'transparent'
                    }
                  }}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {preset.icon}
                    <span
                      className="font-['Poppins'] text-xs font-semibold"
                      style={{ color: isActive ? COLORS.dark : '#333' }}
                    >
                      {preset.label}
                    </span>
                  </div>
                  <span
                    className="font-['Manrope'] text-[11px]"
                    style={{ color: '#777' }}
                  >
                    {preset.description}
                  </span>
                  {isActive && (
                    <div
                      className="absolute top-2 right-2 rounded-full size-4 flex items-center justify-center"
                      style={{ backgroundColor: COLORS.primary }}
                    >
                      <svg
                        className="size-3 text-white"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={3}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                </button>
              )
            })}
          </div>

          {/* Search + Selected Tags */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search
                  className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5"
                  style={{ color: '#999' }}
                />
                <Input
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Search modules..."
                  className="h-8 pl-8 text-xs font-['Manrope']"
                  style={{ borderColor: COLORS.border }}
                />
              </div>
              <Badge
                variant="secondary"
                className="font-['Manrope'] text-[10px] shrink-0 px-2 py-0.5"
                style={{ backgroundColor: COLORS.light, color: COLORS.dark }}
              >
                {selectedCount} selected
              </Badge>
            </div>

            {/* Selected tags */}
            {selectedTags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 min-h-[28px]">
                {selectedTags.map(tag => (
                  <Badge
                    key={tag.id}
                    variant="secondary"
                    className="font-['Manrope'] text-[11px] pl-2 pr-1 py-0.5 flex items-center gap-1 cursor-default"
                    style={{
                      backgroundColor: COLORS.light,
                      color: COLORS.dark,
                      borderColor: COLORS.border,
                    }}
                  >
                    {tag.label}
                    <button
                      type="button"
                      onClick={() => removeModule(tag.id)}
                      className="rounded-full p-0.5 transition-colors hover:bg-[#C8E6C9] focus:outline-none"
                      aria-label={`Remove ${tag.label}`}
                    >
                      <X className="size-3" style={{ color: COLORS.primary }} />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Available Modules */}
          {!isFullAccess && (
            <div className="space-y-2">
              <span
                className="font-['Manrope'] text-xs font-medium"
                style={{ color: '#555' }}
              >
                Available:
              </span>

              <ScrollArea className="max-h-[180px]">
                <div className="space-y-3 pr-2">
                  {/* Group by parent */}
                  {parentModules.map(parent => {
                    const children = (modulesByParent[parent.id] || []).filter(
                      m => !selectedSet.has(m.id)
                    )
                    const filteredChildren = searchQuery
                      ? children.filter(
                          m =>
                            m.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            m.id.toLowerCase().includes(searchQuery.toLowerCase())
                        )
                      : children

                    if (filteredChildren.length === 0) return null

                    return (
                      <div key={parent.id}>
                        <span
                          className="font-['Manrope'] text-[10px] font-semibold uppercase tracking-wide"
                          style={{ color: COLORS.primary }}
                        >
                          {parent.label}
                        </span>
                        <div className="flex flex-wrap gap-1.5 mt-1">
                          {filteredChildren.map(mod => (
                            <button
                              key={mod.id}
                              type="button"
                              onClick={() => addModule(mod.id)}
                              className="group/chip inline-flex items-center gap-1 rounded-md border px-2 py-1 text-[11px] font-['Manrope'] transition-all duration-100 cursor-pointer focus:outline-none focus-visible:ring-1"
                              style={{
                                borderColor: COLORS.chipBorder,
                                backgroundColor: COLORS.chip,
                                color: COLORS.dark,
                              }}
                              onMouseEnter={e => {
                                ;(e.currentTarget as HTMLElement).style.backgroundColor =
                                  COLORS.chipHover
                                ;(e.currentTarget as HTMLElement).style.borderColor =
                                  COLORS.selected
                              }}
                              onMouseLeave={e => {
                                ;(e.currentTarget as HTMLElement).style.backgroundColor =
                                  COLORS.chip
                                ;(e.currentTarget as HTMLElement).style.borderColor =
                                  COLORS.chipBorder
                              }}
                            >
                              <Plus className="size-3 opacity-50 group-hover/chip:opacity-100 transition-opacity" />
                              {mod.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    )
                  })}

                  {/* Standalone modules */}
                  {standaloneModules
                    .filter(m => {
                      if (selectedSet.has(m.id)) return false
                      if (!searchQuery) return true
                      return (
                        m.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        m.id.toLowerCase().includes(searchQuery.toLowerCase())
                      )
                    })
                    .length > 0 && (
                    <div>
                      {parentModules.length > 0 && (
                        <span
                          className="font-['Manrope'] text-[10px] font-semibold uppercase tracking-wide"
                          style={{ color: COLORS.primary }}
                        >
                          Other
                        </span>
                      )}
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {standaloneModules
                          .filter(m => {
                            if (selectedSet.has(m.id)) return false
                            if (!searchQuery) return true
                            return (
                              m.label
                                .toLowerCase()
                                .includes(searchQuery.toLowerCase()) ||
                              m.id.toLowerCase().includes(searchQuery.toLowerCase())
                            )
                          })
                          .map(mod => (
                            <button
                              key={mod.id}
                              type="button"
                              onClick={() => addModule(mod.id)}
                              className="group/chip inline-flex items-center gap-1 rounded-md border px-2 py-1 text-[11px] font-['Manrope'] transition-all duration-100 cursor-pointer focus:outline-none focus-visible:ring-1"
                              style={{
                                borderColor: COLORS.chipBorder,
                                backgroundColor: COLORS.chip,
                                color: COLORS.dark,
                              }}
                              onMouseEnter={e => {
                                ;(e.currentTarget as HTMLElement).style.backgroundColor =
                                  COLORS.chipHover
                                ;(e.currentTarget as HTMLElement).style.borderColor =
                                  COLORS.selected
                              }}
                              onMouseLeave={e => {
                                ;(e.currentTarget as HTMLElement).style.backgroundColor =
                                  COLORS.chip
                                ;(e.currentTarget as HTMLElement).style.borderColor =
                                  COLORS.chipBorder
                              }}
                            >
                              <Plus className="size-3 opacity-50 group-hover/chip:opacity-100 transition-opacity" />
                              {mod.label}
                            </button>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* No results */}
                  {filteredAvailable.length === 0 && (
                    <p
                      className="font-['Manrope'] text-[11px] py-2 text-center"
                      style={{ color: '#999' }}
                    >
                      {searchQuery
                        ? 'No modules match your search.'
                        : 'All modules have been selected.'}
                    </p>
                  )}
                </div>
              </ScrollArea>
            </div>
          )}

          {/* Full access message */}
          {isFullAccess && (
            <div
              className="rounded-md p-3 text-center"
              style={{ backgroundColor: COLORS.light }}
            >
              <p className="font-['Manrope'] text-xs" style={{ color: COLORS.dark }}>
                Full access granted — all {totalModuleCount} modules are selected.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <DialogFooter className="px-6 pb-4 pt-2">
          <Button
            variant="outline"
            onClick={handleCancel}
            className="font-['Roboto'] text-xs h-8"
          >
            Cancel
          </Button>
          <Button
            onClick={handleApply}
            className="font-['Roboto'] text-xs h-8 text-white"
            style={{ backgroundColor: COLORS.primary }}
            onMouseEnter={e => {
              ;(e.currentTarget as HTMLElement).style.backgroundColor = COLORS.dark
            }}
            onMouseLeave={e => {
              ;(e.currentTarget as HTMLElement).style.backgroundColor = COLORS.primary
            }}
          >
            Apply ({selectedCount} module{selectedCount !== 1 ? 's' : ''})
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
