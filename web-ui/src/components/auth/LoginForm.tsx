'use client'

import React, { useState, useCallback } from 'react'
import { User, Lock, Eye, XCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import type { AuthUser } from '@/types/auth'

interface LoginPageProps {
  onLogin: (user: AuthUser) => void
}

export function LoginForm({ onLogin }: LoginPageProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      setError('')
      setLoading(true)

      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        })

        const data = await res.json()

        if (!res.ok) {
          setError(data.error || 'Login failed')
          return
        }

        onLogin(data.user)
      } catch {
        setError('Network error. Please try again.')
      } finally {
        setLoading(false)
      }
    },
    [email, password, onLogin]
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-[400px]">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-green-600 flex items-center justify-center mb-4 shadow-lg shadow-green-600/20">
            <span className="text-white text-2xl font-bold">R</span>
          </div>
          <h1 className="text-[22px] font-semibold text-gray-800 dark:text-gray-100">Welcome Back !</h1>
          <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-1">Sign in to RhythmERP Automation Runner</p>
        </div>

        {/* Login Card */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg shadow-gray-200/50 dark:shadow-gray-900/50 border border-gray-100 dark:border-gray-700 p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div className="space-y-1.5">
              <Label className="text-[13px] text-gray-700 dark:text-gray-300 font-medium">Email / Username</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
                <Input
                  type="email"
                  placeholder="admin@rhythmerp.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="h-10 pl-9 text-[13px] bg-gray-50/50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 focus:bg-white dark:focus:bg-gray-700 text-gray-800 dark:text-gray-100"
                  required
                  autoFocus
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <Label className="text-[13px] text-gray-700 dark:text-gray-300 font-medium">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-10 pl-9 pr-10 text-[13px] bg-gray-50/50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 focus:bg-white dark:focus:bg-gray-700 text-gray-800 dark:text-gray-100"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors cursor-pointer"
                >
                  <Eye className="size-4" />
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="remember"
                  checked={rememberMe}
                  onCheckedChange={(v) => setRememberMe(v === true)}
                  className="size-4"
                />
                <label htmlFor="remember" className="text-[12px] text-gray-600 dark:text-gray-400 cursor-pointer select-none">
                  Remember me
                </label>
              </div>
              <button type="button" className="text-[12px] text-green-600 hover:text-green-700 font-medium cursor-pointer">
                Forgot password?
              </button>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-[12px] px-3 py-2 rounded-lg flex items-center gap-2">
                <XCircle className="size-3.5 shrink-0" />
                {error}
              </div>
            )}

            {/* Submit */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full h-10 bg-green-600 hover:bg-green-700 text-white text-[14px] font-medium gap-2 rounded-lg cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-[11px] text-gray-400 dark:text-gray-500 mt-6">
          RhythmERP Automation Runner v1.0 — Internal QA Tool
        </p>
      </div>
    </div>
  )
}
