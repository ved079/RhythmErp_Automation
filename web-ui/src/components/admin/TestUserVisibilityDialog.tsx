'use client'

import { useState, useEffect, useMemo } from 'react'
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
import { Checkbox } from '@/components/ui/checkbox'
import { Search, EyeOff } from 'lucide-react'
import Spinner from '@/components/ui/Spinner'

interface UserItem {
  id: string
  name: string
  email: string
}

interface TestUserVisibilityDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  testName: string
  testDisplayName: string
  onSave: (userIds: string[]) => void
}

export function TestUserVisibilityDialog({
  open,
  onOpenChange,
  testName,
  testDisplayName,
  onSave,
}: TestUserVisibilityDialogProps) {
  const [users, setUsers] = useState<UserItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (!open) return
    setLoading(true)
    setSearch('')

    Promise.all([
      fetch('/api/admin/users').then(r => r.json()),
      fetch(`/api/admin/tests/exclusions?testName=${encodeURIComponent(testName)}`).then(r => r.json()),
    ]).then(([usersData, exclusionsData]) => {
      const allUsers: UserItem[] = (usersData.users || []).filter((u: { role: string }) => u.role !== 'admin')
      setUsers(allUsers)
      const hiddenIds = new Set<string>()
      for (const e of exclusionsData.exclusions || []) {
        if (e.testName === testName) hiddenIds.add(e.userId)
      }
      setSelected(hiddenIds)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [open, testName])

  const filtered = useMemo(() => {
    if (!search) return users
    const q = search.toLowerCase()
    return users.filter(u => u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q))
  }, [users, search])

  const toggle = (userId: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(userId)) next.delete(userId)
      else next.add(userId)
      return next
    })
  }

  const handleSave = () => {
    onSave(Array.from(selected))
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[420px] dark:bg-gray-800 dark:border-gray-700">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 font-['Poppins'] text-base">
            <EyeOff className="size-4 text-orange-500" />
            Hide Test For Users
          </DialogTitle>
          <DialogDescription className="font-['Manrope'] text-xs text-[#888]">
            Select users to hide &ldquo;{testDisplayName}&rdquo; from their test runner.
          </DialogDescription>
        </DialogHeader>

        <div className="relative mb-2">
          <Search className="absolute left-3 top-2.5 size-4 text-[#888]" />
          <Input
            placeholder="Search users..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-9 h-9 text-sm font-['Manrope']"
          />
        </div>

        <div className="max-h-[280px] overflow-y-auto space-y-1">
          {loading ? (
            <div className="flex justify-center py-8"><Spinner size={20} /></div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-8 text-xs text-[#888] dark:text-gray-400 font-['Manrope']">No users found</div>
          ) : (
            filtered.map(u => (
              <label
                key={u.id}
                className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors"
              >
                <Checkbox
                  checked={selected.has(u.id)}
                  onCheckedChange={() => toggle(u.id)}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-[13px] font-['Manrope'] text-[#333] dark:text-gray-100 truncate">{u.name}</div>
                  <div className="text-[11px] font-['Manrope'] text-[#888] truncate">{u.email}</div>
                </div>
                {selected.has(u.id) && (
                  <Badge variant="outline" className="text-[10px] text-orange-600 border-orange-200 bg-orange-50 dark:bg-orange-900/20 dark:border-orange-800 shrink-0">
                    Hidden
                  </Badge>
                )}
              </label>
            ))
          )}
        </div>

        <div className="flex items-center justify-between text-[11px] text-[#888] font-['Manrope']">
          <span>{selected.size} of {users.length} users hidden</span>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-[11px] text-[#888]"
            onClick={() => setSelected(new Set())}
          >
            Clear all
          </Button>
        </div>

        <DialogFooter className="gap-1.5">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="cursor-pointer font-['Manrope'] text-xs">
            Cancel
          </Button>
          <Button onClick={handleSave} className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Roboto'] cursor-pointer">
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
