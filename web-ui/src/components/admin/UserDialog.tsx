'use client'

import { useState, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { ModuleAccessPicker, type ModuleItem } from '@/components/admin/ModuleAccessPicker'
import { ALL_SIDEBAR_MODULES } from '@/data/sidebarModules'
import { Shield } from 'lucide-react'

interface AdminModule {
  id: string; name: string; label: string; parentId?: string; parentLabel?: string
  badge?: string; testCount: number; sortOrder: number; status: 'active' | 'draft' | 'disabled'
  description?: string
}

interface AdminUser {
  id: string; email: string; name: string
  role: 'admin' | 'tester' | 'viewer' | 'client'
  status: 'active' | 'inactive'; lastLogin?: string; moduleAccess: string[]
}

export function UserDialog({ open, onOpenChange, editingUser, onSave, allModules }: {
  open: boolean; onOpenChange: (v: boolean) => void
  editingUser: AdminUser | null; onSave: (data: Partial<AdminUser> & { password?: string }) => void
  allModules: AdminModule[]
}) {
  const [name, setName] = useState(editingUser?.name || '')
  const [email, setEmail] = useState(editingUser?.email || '')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<string>(editingUser?.role || 'tester')
  const [status, setStatus] = useState<string>(editingUser?.status || 'active')
  const [moduleAccess, setModuleAccess] = useState<string[]>(editingUser?.moduleAccess || [])
  const [modulePickerOpen, setModulePickerOpen] = useState(false)

  const pickerModules: ModuleItem[] = useMemo(() => {
    const result: ModuleItem[] = []
    for (const sm of ALL_SIDEBAR_MODULES) {
      if (sm.id === 'dashboard' || sm.id === 'my-tickets') continue
      result.push({
        id: sm.id, name: sm.id, label: sm.label,
        parentId: undefined, parentLabel: undefined,
      })
      if (sm.children) {
        for (const child of sm.children) {
          if (child.children) {
            for (const grandChild of child.children) {
              result.push({
                id: grandChild.id, name: grandChild.id, label: grandChild.label,
                parentId: child.id, parentLabel: child.label,
              })
            }
            result.push({
              id: child.id, name: child.id, label: child.label,
              parentId: sm.id, parentLabel: sm.label,
            })
          } else {
            result.push({
              id: child.id, name: child.id, label: child.label,
              parentId: sm.id, parentLabel: sm.label,
            })
          }
        }
      }
    }
    result.push({
      id: 'concurrency-testing', name: 'concurrency-testing', label: 'Concurrency Testing',
      parentId: undefined, parentLabel: undefined,
    })
    return result
  }, [])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100">{editingUser ? 'Edit User' : 'Add User'}</DialogTitle>
          <DialogDescription className="font-['Poppins'] text-[#888]">
            {editingUser ? 'Update user details and permissions.' : 'Create a new user account.'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2 max-h-[60vh] overflow-y-auto">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs font-['Poppins']">Name</Label>
              <Input value={name} onChange={e => setName(e.target.value)} placeholder="Full Name" className="h-9 text-sm font-['Poppins']" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-['Poppins']">Email</Label>
              <Input value={email} onChange={e => setEmail(e.target.value)} placeholder="email@example.com" type="email" className="h-9 text-sm font-['Poppins']" />
            </div>
          </div>
          {!editingUser && (
            <div className="space-y-1.5">
              <Label className="text-xs font-['Poppins']">Password</Label>
              <Input value={password} onChange={e => setPassword(e.target.value)} placeholder="changeme" type="password" className="h-9 text-sm font-['Poppins']" />
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs font-['Poppins']">Role</Label>
              <Select value={role} onValueChange={setRole}>
                <SelectTrigger className="h-9 text-sm"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="tester">Tester</SelectItem>
                  <SelectItem value="viewer">Viewer</SelectItem>
                  <SelectItem value="client">Client</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-['Poppins']">Status</Label>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="h-9 text-sm"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-['Poppins']">Module Access</Label>
            <Button
              type="button"
              variant="outline"
              className="w-full justify-start text-left h-auto min-h-[36px] py-2 px-3 font-['Poppins'] text-xs"
              onClick={() => setModulePickerOpen(true)}
            >
              <Shield className="size-4 mr-2 shrink-0 text-[#2E7D32]" />
              {moduleAccess.includes('all')
                ? 'Full Access (all modules)'
                : moduleAccess.length === 0
                  ? 'No modules selected — click to assign'
                  : `${moduleAccess.length} module${moduleAccess.length !== 1 ? 's' : ''} selected`}
            </Button>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="font-['Poppins']">Cancel</Button>
          <Button onClick={() => onSave({ name, email, password: password || undefined, role: role as AdminUser['role'], status: status as AdminUser['status'], moduleAccess })}
            disabled={!name || !email}
            className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Poppins']">
            {editingUser ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
      <ModuleAccessPicker
        open={modulePickerOpen}
        onOpenChange={setModulePickerOpen}
        value={moduleAccess}
        onChange={setModuleAccess}
        allModules={pickerModules}
        userName={name || undefined}
      />
    </Dialog>
  )
}
