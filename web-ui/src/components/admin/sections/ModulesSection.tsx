'use client'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Plus, Database, Pencil, Trash2, FolderTree,
  CheckCircle2, Clock, XCircle, ChevronRight, AlertTriangle,
} from 'lucide-react'
import Spinner from '@/components/ui/Spinner'

interface AdminModule {
  id: string; name: string; label: string; parentId?: string; parentLabel?: string
  badge?: string; testCount: number; sortOrder: number; status: 'active' | 'draft' | 'disabled'
  description?: string
}

export function ModulesSection({
  modules, modulesLoaded, onAdd, onEdit, onToggleStatus, onDelete, onSeed,
}: {
  modules: AdminModule[]
  modulesLoaded: boolean
  onAdd: () => void
  onEdit: (mod: AdminModule) => void
  onToggleStatus: (mod: AdminModule) => void
  onDelete: (target: { id: string; type: string; label: string }) => void
  onSeed: () => void
}) {
  const parents = modules.filter(m => !m.parentId)
  const getChildren = (parentId: string) => modules.filter(m => m.parentId === parentId)
  const activeCount = modules.filter(m => m.status === 'active').length
  const draftCount = modules.filter(m => m.status === 'draft').length
  const disabledCount = modules.filter(m => m.status === 'disabled').length

  const statusBadge = (status: string) => {
    if (status === 'active') return 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
    if (status === 'draft') return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300'
    return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Modules</h2>
        <div className="flex gap-2">
          <Button onClick={onSeed}
            className="bg-[#00897B] hover:bg-[#00695C] text-white font-['Poppins'] text-xs h-8">
            <Database className="size-3.5 mr-1" /> Seed Defaults
          </Button>
          <Button onClick={onAdd}
            className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Poppins'] text-xs h-8">
            <Plus className="size-3.5 mr-1" /> Add Module
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-green-100 dark:bg-green-900/40">
            <CheckCircle2 className="size-4 text-green-700 dark:text-green-300" />
          </div>
          <div>
            <p className="text-lg font-bold font-['Poppins'] text-[#333] dark:text-gray-100">{activeCount}</p>
            <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Poppins']">Active</p>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-yellow-100 dark:bg-yellow-900/40">
            <Clock className="size-4 text-yellow-700 dark:text-yellow-300" />
          </div>
          <div>
            <p className="text-lg font-bold font-['Poppins'] text-[#333] dark:text-gray-100">{draftCount}</p>
            <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Poppins']">Draft</p>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-red-100 dark:bg-red-900/40">
            <XCircle className="size-4 text-red-700 dark:text-red-300" />
          </div>
          <div>
            <p className="text-lg font-bold font-['Poppins'] text-[#333] dark:text-gray-100">{disabledCount}</p>
            <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Poppins']">Disabled</p>
          </div>
        </div>
      </div>

      {!modulesLoaded ? (
        <div className="flex justify-center py-12"><Spinner size={24} /></div>
      ) : modules.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-12 border border-gray-100 dark:border-gray-700 text-center">
          <FolderTree className="size-10 text-[#888] dark:text-gray-500 mx-auto mb-2" />
          <p className="text-sm text-[#888] dark:text-gray-400 font-['Poppins']">No modules configured</p>
          <p className="text-xs text-[#888] dark:text-gray-400 font-['Poppins'] mt-1">Click &quot;Seed Defaults&quot; to create default modules, or add one manually.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {parents.map(parent => {
            const children = getChildren(parent.id)
            return (
              <div key={parent.id} className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                <div className="flex items-center gap-3 p-4 bg-[#E8EAF6] dark:bg-[#1A237E]/30">
                  <FolderTree className="size-4 text-[#3F51B5]" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold font-['Poppins'] text-[#3F51B5] dark:text-[#7986CB]">{parent.label}</span>
                      <Badge className={`text-[9px] border-0 ${statusBadge(parent.status)}`}>{parent.status}</Badge>
                    </div>
                    {parent.description && <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Poppins'] mt-0.5 truncate">{parent.description}</p>}
                  </div>
                  <Badge variant="outline" className="text-[10px]">{parent.testCount} tests</Badge>
                  <div className="flex gap-1">
                    <Button size="sm" variant="ghost" className="size-7 p-0" onClick={() => onToggleStatus(parent)} title="Toggle status">
                      {parent.status === 'active' ? <CheckCircle2 className="size-3 text-green-600" /> : parent.status === 'draft' ? <Clock className="size-3 text-yellow-600" /> : <XCircle className="size-3 text-red-600" />}
                    </Button>
                    <Button size="sm" variant="ghost" className="size-7 p-0" onClick={() => onEdit(parent)}>
                      <Pencil className="size-3 text-[#3F51B5]" />
                    </Button>
                    <Button size="sm" variant="ghost" className="size-7 p-0" onClick={() => onDelete({ type: 'module', id: parent.id, label: parent.label })}>
                      <Trash2 className="size-3 text-[#F44336]" />
                    </Button>
                  </div>
                </div>
                {children.length > 0 && (
                  <div className="divide-y divide-gray-50 dark:divide-gray-700/50">
                    {children.map(child => (
                      <div key={child.id} className="flex items-center gap-3 px-4 py-2.5 ml-6 border-l-2 border-[#3F51B5]/20 dark:border-[#7986CB]/20">
                        <ChevronRight className="size-3 text-[#888] dark:text-gray-400" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-['Poppins'] text-[#333] dark:text-gray-100">{child.label}</span>
                            <Badge className={`text-[8px] border-0 px-1 py-0 ${statusBadge(child.status)}`}>{child.status}</Badge>
                          </div>
                          {child.description && <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Poppins'] truncate">{child.description}</p>}
                        </div>
                        <Badge variant="outline" className="text-[9px]">{child.testCount} tests</Badge>
                        <div className="flex gap-1">
                          <Button size="sm" variant="ghost" className="size-6 p-0" onClick={() => onToggleStatus(child)} title="Toggle status">
                            {child.status === 'active' ? <CheckCircle2 className="size-3 text-green-600" /> : child.status === 'draft' ? <Clock className="size-3 text-yellow-600" /> : <XCircle className="size-3 text-red-600" />}
                          </Button>
                          <Button size="sm" variant="ghost" className="size-6 p-0" onClick={() => onEdit(child)}>
                            <Pencil className="size-3 text-[#3F51B5]" />
                          </Button>
                          <Button size="sm" variant="ghost" className="size-6 p-0" onClick={() => onDelete({ type: 'module', id: child.id, label: child.label })}>
                            <Trash2 className="size-3 text-[#F44336]" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
          {modules.filter(m => m.parentId && !modules.find(p => p.id === m.parentId)).length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
              <div className="flex items-center gap-3 p-4 bg-orange-50 dark:bg-orange-900/20">
                <AlertTriangle className="size-4 text-orange-600" />
                <span className="text-sm font-semibold font-['Poppins'] text-orange-700 dark:text-orange-300">Orphaned Modules</span>
              </div>
              <div className="divide-y divide-gray-50 dark:divide-gray-700/50">
                {modules.filter(m => m.parentId && !modules.find(p => p.id === m.parentId)).map(child => (
                  <div key={child.id} className="flex items-center gap-3 px-4 py-2.5">
                    <ChevronRight className="size-3 text-[#888] dark:text-gray-400" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-['Poppins'] text-[#333] dark:text-gray-100">{child.label}</span>
                        <Badge className={`text-[8px] border-0 px-1 py-0 ${statusBadge(child.status)}`}>{child.status}</Badge>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" className="size-6 p-0" onClick={() => onEdit(child)}>
                        <Pencil className="size-3 text-[#3F51B5]" />
                      </Button>
                      <Button size="sm" variant="ghost" className="size-6 p-0" onClick={() => onDelete({ type: 'module', id: child.id, label: child.label })}>
                        <Trash2 className="size-3 text-[#F44336]" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
