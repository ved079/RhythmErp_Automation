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
import { Shield, Eye, EyeOff, Check, X } from 'lucide-react'

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
  const [showPassword, setShowPassword] = useState(true)

  const passwordChecks = useMemo(() => ({
    length:   password.length >= 8,
    upper:    /[A-Z]/.test(password),
    lower:    /[a-z]/.test(password),
    number:   /[0-9]/.test(password),
    special:  /[^A-Za-z0-9]/.test(password),
  }), [password])

  const strengthScore = Object.values(passwordChecks).filter(Boolean).length
  const strengthLabel = ['', 'Weak', 'Weak', 'Fair', 'Good', 'Strong'][strengthScore]
  const strengthColor = ['', '#ef4444', '#ef4444', '#f97316', '#3b82f6', '#22c55e'][strengthScore]

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
        <div className="space-y-4 py-2 max-h-[60vh] overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
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
              <div className="relative">
                <Input value={password} onChange={e => setPassword(e.target.value)} placeholder="changeme" type={showPassword ? 'text' : 'password'} className="h-9 text-sm font-['Poppins'] pr-9" />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 cursor-pointer"
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>

              {/* Strength meter — only shown once user starts typing */}
              {password.length > 0 && (
                <div className="space-y-2 pt-1">
                  {/* Bar */}
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1 flex-1">
                      {[1,2,3,4,5].map(i => (
                        <div
                          key={i}
                          className="h-1.5 flex-1 rounded-full transition-colors duration-300"
                          style={{ backgroundColor: i <= strengthScore ? strengthColor : '#e5e7eb' }}
                        />
                      ))}
                    </div>
                    <span className="text-[11px] font-medium font-['Poppins'] w-10 text-right" style={{ color: strengthColor }}>
                      {strengthLabel}
                    </span>
                  </div>

                  {/* Checklist */}
                  <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                    {([
                      { key: 'length',  label: 'Min 8 characters' },
                      { key: 'upper',   label: 'Uppercase letter' },
                      { key: 'lower',   label: 'Lowercase letter' },
                      { key: 'number',  label: 'Number' },
                      { key: 'special', label: 'Special character' },
                    ] as const).map(({ key, label }) => (
                      <div key={key} className="flex items-center gap-1.5">
                        {passwordChecks[key]
                          ? <Check className="size-3 text-green-500 shrink-0" />
                          : <X className="size-3 text-gray-300 dark:text-gray-600 shrink-0" />}
                        <span className={`text-[11px] font-['Poppins'] ${passwordChecks[key] ? 'text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-gray-500'}`}>
                          {label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
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
            disabled={!name || !email || (!editingUser && !passwordChecks.length)}
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
