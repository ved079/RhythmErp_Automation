'use client'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import {
  Plus, CheckCircle2, XCircle, Trash2, Pencil, Key,
} from 'lucide-react'
import Spinner from '@/components/ui/Spinner'

interface AdminUser {
  id: string; email: string; name: string
  role: 'admin' | 'tester' | 'viewer' | 'client'
  status: 'active' | 'inactive'; lastLogin?: string; moduleAccess: string[]
}

const roleConfig: Record<string, { label: string; color: string }> = {
  admin: { label: 'Admin', color: 'text-[#3F51B5] bg-[#E8EAF6] dark:text-[#7986CB] dark:bg-[#1A237E]/30' },
  tester: { label: 'Tester', color: 'text-[#2E7D32] bg-[#E8F5E9] dark:text-[#66BB6A] dark:bg-[#1B5E20]/40' },
  viewer: { label: 'Viewer', color: 'text-[#616161] bg-[#F5F5F5] dark:text-[#9E9E9E] dark:bg-[#424242]/40' },
  client: { label: 'Client', color: 'text-[#E65100] bg-[#FFF3E0] dark:text-[#FFB74D] dark:bg-[#BF360C]/40' },
}

export function UsersSection({
  users, usersLoaded, selectedUserIds, onAdd, onEdit, onResetPassword,
  onDelete, onBulkAction, onToggleSelection, onToggleAll, onClearSelection,
  bulkActionConfirmOpen, setBulkActionConfirmOpen, bulkActionType, setBulkActionType,
}: {
  users: AdminUser[]
  usersLoaded: boolean
  selectedUserIds: Set<string>
  bulkActionConfirmOpen: boolean
  setBulkActionConfirmOpen: (v: boolean) => void
  bulkActionType: string
  setBulkActionType: (v: string) => void
  onAdd: () => void
  onEdit: (u: AdminUser) => void
  onResetPassword: (u: AdminUser) => void
  onDelete: (target: { id: string; type: string; label: string }) => void
  onBulkAction: () => void
  onToggleSelection: (id: string) => void
  onToggleAll: () => void
  onClearSelection: () => void
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Users</h2>
        <Button onClick={onAdd}
          className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Poppins'] text-xs h-8">
          <Plus className="size-3.5 mr-1" /> Add User
        </Button>
      </div>
      {selectedUserIds.size > 0 && (
        <div className="bg-[#E8EAF6] dark:bg-[#1A237E]/30 rounded-[14px] shadow-sm p-3 flex items-center gap-3 flex-wrap">
          <span className="text-xs font-semibold font-['Poppins'] text-[#3F51B5] dark:text-[#7986CB]">
            {selectedUserIds.size} selected
          </span>
          <Button size="sm" className="h-7 text-[10px] bg-green-600 hover:bg-green-700 text-white font-['Poppins']"
            onClick={() => { setBulkActionType('activate'); setBulkActionConfirmOpen(true) }}>
            <CheckCircle2 className="size-3 mr-1" /> Activate
          </Button>
          <Button size="sm" className="h-7 text-[10px] bg-orange-500 hover:bg-orange-600 text-white font-['Poppins']"
            onClick={() => { setBulkActionType('deactivate'); setBulkActionConfirmOpen(true) }}>
            <XCircle className="size-3 mr-1" /> Deactivate
          </Button>
          <Button size="sm" className="h-7 text-[10px] bg-[#F44336] hover:bg-[#D32F2F] text-white font-['Poppins']"
            onClick={() => { setBulkActionType('delete'); setBulkActionConfirmOpen(true) }}>
            <Trash2 className="size-3 mr-1" /> Delete
          </Button>
          <Button size="sm" variant="ghost" className="h-7 text-[10px] font-['Poppins'] text-[#888]"
            onClick={onClearSelection}>
            Clear
          </Button>
        </div>
      )}
      {!usersLoaded ? (
        <div className="flex justify-center py-12"><Spinner size={24} /></div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="space-y-1 p-3">
            {users.map(u => (
              <div key={u.id} className={`flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-colors ${selectedUserIds.has(u.id) ? 'bg-[#E8EAF6]/50 dark:bg-[#1A237E]/20 border-[#3F51B5]/30 dark:border-[#7986CB]/30' : 'bg-white dark:bg-gray-800/20 border-gray-100 dark:border-gray-700/40 hover:bg-gray-50/50 dark:hover:bg-gray-800/30'}`}>
                <Checkbox
                  checked={selectedUserIds.has(u.id)}
                  onCheckedChange={() => onToggleSelection(u.id)}
                />
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <Avatar className="size-7 shrink-0"><AvatarFallback className="bg-[#E8EAF6] dark:bg-[#1A237E]/30 text-[#3F51B5] dark:text-[#7986CB] text-[10px] font-semibold">
                    {u.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                  </AvatarFallback></Avatar>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-[#333] dark:text-gray-100 truncate">{u.name}</p>
                    <p className="text-[10px] text-[#888] dark:text-gray-400 truncate">{u.email}</p>
                  </div>
                </div>
                <Badge className={`text-[10px] border-0 shrink-0 ${roleConfig[u.role]?.color || ''}`}>{roleConfig[u.role]?.label || u.role}</Badge>
                <Badge className={`text-[10px] border-0 shrink-0 ${u.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}`}>{u.status}</Badge>
                <span className="text-[10px] font-['Poppins'] text-[#545454] dark:text-gray-300 shrink-0">
                  {u.moduleAccess.includes('all') ? 'All modules' : `${u.moduleAccess.length} modules`}
                </span>
                <span className="text-[10px] font-['Poppins'] text-[#888] dark:text-gray-400 shrink-0">{u.lastLogin || '—'}</span>
                <div className="flex gap-1 shrink-0">
                  <Button size="sm" variant="ghost" className="size-7 p-0" onClick={() => onEdit(u)}><Pencil className="size-3 text-[#3F51B5]" /></Button>
                  <Button size="sm" variant="ghost" className="size-7 p-0" onClick={() => onResetPassword(u)} title="Reset password"><Key className="size-3 text-[#F57C00]" /></Button>
                  <Button size="sm" variant="ghost" className="size-7 p-0" onClick={() => onDelete({ type: 'user', id: u.id, label: u.name })}><Trash2 className="size-3 text-[#F44336]" /></Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <Dialog open={bulkActionConfirmOpen} onOpenChange={setBulkActionConfirmOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100">Confirm Bulk Action</DialogTitle>
            <DialogDescription className="font-['Poppins'] text-[#888]">
              Are you sure you want to {bulkActionType === 'activate' ? 'activate' : bulkActionType === 'deactivate' ? 'deactivate' : 'delete'} <strong>{selectedUserIds.size} user(s)</strong>?
              {bulkActionType === 'delete' && ' This action cannot be undone.'}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkActionConfirmOpen(false)} className="font-['Poppins']">Cancel</Button>
            <Button onClick={onBulkAction}
              className={`text-white font-['Poppins'] ${bulkActionType === 'delete' ? 'bg-[#F44336] hover:bg-[#D32F2F]' : bulkActionType === 'deactivate' ? 'bg-orange-500 hover:bg-orange-600' : 'bg-green-600 hover:bg-green-700'}`}>
              {bulkActionType === 'activate' ? 'Activate' : bulkActionType === 'deactivate' ? 'Deactivate' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
