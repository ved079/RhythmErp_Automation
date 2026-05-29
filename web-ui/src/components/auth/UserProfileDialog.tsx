'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { User, Lock, Clock, Loader2, Shield } from 'lucide-react'
import type { AuthUser } from '@/lib/types'

// ─── USER PROFILE DIALOG (Feature 2) ────────────────────
function UserProfileDialog({
  open,
  onClose,
  user,
}: {
  open: boolean
  onClose: () => void
  user: AuthUser
}) {
  const [lastLogin, setLastLogin] = useState<string | null>(null)
  const [loadingProfile, setLoadingProfile] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [changingPassword, setChangingPassword] = useState(false)

  useEffect(() => {
    if (open) {
      setLoadingProfile(true)
      fetch('/api/proxy?path=auth/me', { headers: { 'Content-Type': 'application/json' } })
        .then((res) => res.json())
        .then((data) => {
          if (data.last_login) setLastLogin(data.last_login)
        })
        .catch(() => { /* silent */ })
        .finally(() => setLoadingProfile(false))
    }
  }, [open])

  const handleChangePassword = useCallback(async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error('Please fill in all password fields')
      return
    }
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match')
      return
    }
    if (newPassword.length < 6) {
      toast.error('New password must be at least 6 characters')
      return
    }
    setChangingPassword(true)
    try {
      const res = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        toast.error(data.error || 'Failed to change password')
        return
      }
      toast.success('Password changed successfully')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch {
      toast.error('Network error. Please try again.')
    } finally {
      setChangingPassword(false)
    }
  }, [currentPassword, newPassword, confirmPassword])

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="max-w-[420px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <User className="size-5 text-[#3F51B5]" />
            My Profile
          </DialogTitle>
          <DialogDescription>View your account details and change password</DialogDescription>
        </DialogHeader>

        {/* User Info */}
        <div className="space-y-3">
          <div className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <Avatar className="size-12">
              <AvatarFallback className="bg-[#6777EF] text-white text-lg font-semibold">
                {user.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <div className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">{user.name}</div>
              <div className="text-[12px] text-gray-500 dark:text-gray-400">{user.email}</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">
                  {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                </span>
              </div>
            </div>
          </div>

          {/* Last Login */}
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 flex items-center gap-2">
            <Clock className="size-4 text-gray-400" />
            <div>
              <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">Last Login</div>
              <div className="text-[13px] text-gray-800 dark:text-gray-200">
                {loadingProfile ? 'Loading...' : lastLogin ? new Date(lastLogin).toLocaleString() : '—'}
              </div>
            </div>
          </div>

          <Separator />

          {/* Password Change Section */}
          <div>
            <h4 className="text-[13px] font-semibold text-gray-800 dark:text-gray-100 mb-3 flex items-center gap-1.5">
              <Lock className="size-4 text-gray-500" />
              Change Password
            </h4>
            <div className="space-y-2.5">
              <div>
                <Label className="text-[12px] text-gray-600 dark:text-gray-400">Current Password</Label>
                <Input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="h-9 text-[13px] bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600 mt-1"
                />
              </div>
              <div>
                <Label className="text-[12px] text-gray-600 dark:text-gray-400">New Password</Label>
                <Input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="h-9 text-[13px] bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600 mt-1"
                />
              </div>
              <div>
                <Label className="text-[12px] text-gray-600 dark:text-gray-400">Confirm New Password</Label>
                <Input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="h-9 text-[13px] bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600 mt-1"
                  onKeyDown={(e) => { if (e.key === 'Enter') handleChangePassword() }}
                />
              </div>
              <Button
                onClick={handleChangePassword}
                disabled={changingPassword}
                className="w-full bg-[#2D3FC7] hover:bg-[#3F51B5] text-white text-[13px] gap-1.5 cursor-pointer"
              >
                {changingPassword ? (
                  <>
                    <Loader2 className="size-4 animate-spin" />
                    Changing...
                  </>
                ) : (
                  <>
                    <Shield className="size-4" />
                    Change Password
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export { UserProfileDialog }
