'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Key, AlertTriangle } from 'lucide-react'
import Spinner from '@/components/ui/Spinner'

interface AdminUser {
  id: string; email: string; name: string
  role: 'admin' | 'tester' | 'viewer' | 'client'
  status: 'active' | 'inactive'; lastLogin?: string; moduleAccess: string[]
}

export function ResetPasswordDialog({ open, onOpenChange, user, onReset }: {
  open: boolean; onOpenChange: (v: boolean) => void
  user: AdminUser | null; onReset: (userId: string, password: string) => void
}) {
  const [password, setPassword] = useState('changeme')
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<{ id: string; resetBy: string; date: string; password: string }[]>([])

  const [historyLoading, setHistoryLoading] = useState(false)
  const [fetchedUserId, setFetchedUserId] = useState<string | null>(null)

  if (open && user && user.id !== fetchedUserId) {
    setFetchedUserId(user.id)
    setHistoryLoading(true)
    setHistory([])
    fetch(`/api/admin/users/${user.id}/reset-password`)
      .then(res => res.ok ? res.json() : { history: [] })
      .then(data => {
        setHistory(data.history || [])
        setHistoryLoading(false)
      })
      .catch(() => { setHistory([]); setHistoryLoading(false) })
  }
  if (!open && fetchedUserId) {
    setFetchedUserId(null)
    setPassword('changeme')
    setHistory([])
  }

  if (!user) return null

  const handleReset = async () => {
    setLoading(true)
    await onReset(user.id, password)
    setLoading(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100 flex items-center gap-2">
            <Key className="size-4 text-[#F57C00]" />
            Reset Password
          </DialogTitle>
          <DialogDescription className="font-['Poppins'] text-[#888] dark:text-gray-400">
            Set a new password for <strong className="text-[#333] dark:text-gray-200">{user.name}</strong> ({user.email})
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-2">
          <div className="space-y-2">
            <Label className="font-['Poppins'] text-xs text-[#555] dark:text-gray-400">New Password</Label>
            <Input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter new password"
              className="font-['Poppins'] h-9"
            />
            <p className="text-[10px] text-[#999] dark:text-gray-500">
              Default: <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded text-[10px]">changeme</code> — min 6 characters
            </p>
          </div>

          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
            <p className="text-[11px] text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
              <AlertTriangle className="size-3 shrink-0" />
              This will invalidate all active sessions for this user. They will need to log in again.
            </p>
          </div>

          {history.length > 0 && (
            <div className="space-y-2">
              <Label className="font-['Poppins'] text-xs text-[#555] dark:text-gray-400">Recent Reset History</Label>
              <div className="space-y-1 border rounded-lg dark:border-gray-700 p-2">
                {history.map((entry) => (
                  <div key={entry.id} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white dark:bg-gray-800/20 border border-gray-100 dark:border-gray-700/40">
                    <span className="text-[11px] font-['Poppins'] flex-1">{entry.resetBy}</span>
                    <span className="text-[11px] font-['Poppins'] text-[#888] dark:text-gray-400 shrink-0">
                      {new Date(entry.date).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </span>
                    <code className="bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded text-[10px] shrink-0">{entry.password}</code>
                  </div>
                ))}
              </div>
            </div>
          )}
          {historyLoading && (
            <div className="flex justify-center py-2"><Spinner size={16} /></div>
          )}
        </div>

        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="font-['Poppins']">Cancel</Button>
          <Button onClick={handleReset} disabled={loading || password.length < 6} className="bg-[#F57C00] hover:bg-[#E65100] text-white font-['Poppins']">
            {loading ? <Spinner size={16} className="mr-1" /> : <Key className="size-3.5 mr-1" />}
            Reset Password
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
