'use client'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Plus, Pencil, Trash2, Globe } from 'lucide-react'
import Spinner from '@/components/ui/Spinner'

interface Environment {
  id: string; name: string; baseUrl: string; browser: string
  status: 'active' | 'inactive'; lastUsed?: string; color: string
}

export function EnvironmentsSection({
  environments, envLoaded, onAdd, onEdit, onToggle, onDelete,
}: {
  environments: Environment[]
  envLoaded: boolean
  onAdd: () => void
  onEdit: (env: Environment) => void
  onToggle: (env: Environment) => void
  onDelete: (target: { id: string; type: string; label: string }) => void
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Environments</h2>
        <Button onClick={onAdd}
          className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Roboto'] text-xs h-8">
          <Plus className="size-3.5 mr-1" /> Add Environment
        </Button>
      </div>
      {!envLoaded ? (
        <div className="flex justify-center py-12"><Spinner size={24} /></div>
      ) : environments.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-12 border border-gray-100 dark:border-gray-700 text-center">
          <Globe className="size-10 text-[#888] dark:text-gray-500 mx-auto mb-2" />
          <p className="text-sm text-[#888] dark:text-gray-400 font-['Manrope']">No environments configured</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {environments.map(env => (
            <div key={env.id} className={`bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700 border-l-4 ${env.status === 'active' ? 'border-l-[#4CAF50]' : 'border-l-gray-400 dark:border-l-gray-600'}`}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${env.color || 'bg-green-500'}`} />
                  <h3 className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">{env.name}</h3>
                </div>
                <Badge className={`text-[9px] border-0 ${env.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}`}>
                  {env.status}
                </Badge>
              </div>
              <div className="space-y-1 text-xs font-['Manrope']">
                <p className="text-[#545454] dark:text-gray-300"><span className="text-[#888] dark:text-gray-400">URL:</span> {env.baseUrl}</p>
                <p className="text-[#545454] dark:text-gray-300"><span className="text-[#888] dark:text-gray-400">Browser:</span> {env.browser}</p>
                {env.lastUsed && <p className="text-[#545454] dark:text-gray-300"><span className="text-[#888] dark:text-gray-400">Last used:</span> {env.lastUsed}</p>}
              </div>
              <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <Button size="sm" variant="outline" className="h-7 text-[10px] font-['Roboto']"
                  onClick={() => onEdit(env)}><Pencil className="size-3 mr-1" /> Edit</Button>
                <Button size="sm" variant="outline" className="h-7 text-[10px] font-['Roboto']"
                  onClick={() => onToggle(env)}>{env.status === 'active' ? 'Deactivate' : 'Activate'}</Button>
                <Button size="sm" variant="ghost" className="h-7 text-[10px] text-[#F44336] hover:text-[#D32F2F] hover:bg-red-50 dark:hover:bg-red-900/20 font-['Roboto']"
                  onClick={() => onDelete({ type: 'environment', id: env.id, label: env.name })}><Trash2 className="size-3" /></Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
