'use client'

import React, { useState, useCallback } from 'react'
import Image from 'next/image'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { User, Lock, Eye, EyeOff, XCircle, Loader2 } from 'lucide-react'

// ─── Types ───────────────────────────────────────────────
interface AuthUser {
  id: string
  email: string
  name: string
  role: string
  status?: string
  moduleAccess?: string[]
}

// ─── Material Outlined Field ─────────────────────────────
function MaterialOutlinedField({
  label,
  type,
  value,
  onChange,
  icon,
  required,
  autoFocus,
  suffixIcon,
  onSuffixClick,
}: {
  label: string
  type: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  icon: React.ReactNode
  required?: boolean
  autoFocus?: boolean
  suffixIcon?: React.ReactNode
  onSuffixClick?: () => void
}) {
  const [focused, setFocused] = useState(false)
  const hasValue = value.length > 0
  const floatLabel = focused || hasValue

  return (
    <div className="w-full mb-6">
      <div
        className={`relative flex items-center h-[56px] rounded-[4px] transition-colors duration-150 ${
          focused
            ? 'outline outline-2 outline-[#3F51B5] outline-offset-0'
            : 'outline outline-1 outline-[rgba(0,0,0,0.38)] outline-offset-0 dark:outline-[rgba(255,255,255,0.38)]'
        }`}
      >
        <div className="flex items-center justify-center w-[48px] shrink-0 pl-2">
          <span className={`transition-colors duration-150 ${
            focused ? 'text-[#3F51B5]' : 'text-[#212529] dark:text-gray-400'
          }`}>
            {icon}
          </span>
        </div>

        <div className="relative flex-1 h-full">
          <label
            className={`absolute left-0 transition-all duration-150 pointer-events-none font-['Manrope',sans-serif] z-10 ${
              floatLabel
                ? 'top-0 text-[12px] leading-none px-[4px] ' + (focused ? 'text-[rgba(63,81,181,0.87)]' : 'text-[rgba(0,0,0,0.6)] dark:text-gray-400') + ' bg-white dark:bg-gray-800 -translate-y-1/2'
                : 'top-[16px] text-[16px] text-[rgba(0,0,0,0.6)] dark:text-gray-400 bg-transparent'
            }`}
          >
            {label}{required && <span className="text-[#f44336] ml-0.5">*</span>}
          </label>
          <input
            type={type}
            value={value}
            onChange={onChange}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            autoFocus={autoFocus}
            required={required}
            className="w-full h-full bg-transparent text-[16px] text-[rgba(0,0,0,0.87)] dark:text-gray-100 font-['Manrope',sans-serif] outline-none border-none placeholder-transparent leading-[56px]"
          />
        </div>

        {suffixIcon && (
          <button
            type="button"
            onClick={onSuffixClick}
            className="flex items-center justify-center w-[48px] h-[48px] shrink-0 cursor-pointer text-[#212529] dark:text-gray-400 hover:bg-[rgba(0,0,0,0.04)] rounded-full transition-colors"
          >
            {suffixIcon}
          </button>
        )}
      </div>
    </div>
  )
}

// ─── Login Page ──────────────────────────────────────────
export function LoginPage({ onLogin }: { onLogin: (user: AuthUser) => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
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
    <div className="min-h-screen flex">
      {/* ─── LEFT: Login Form ─── */}
      <div className="w-full lg:w-1/3 shrink-0 flex items-center min-h-screen bg-white dark:bg-gray-800 p-4">
        <div className="w-full flex justify-center">
          <div className="w-full max-w-[300px]">
            {/* Logo */}
            <motion.div
              className="text-center mb-[20px]"
              initial={{ y: -60, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ type: 'spring', stiffness: 120, damping: 14, mass: 0.8 }}
            >
              <motion.div
                className="flex justify-center mb-0"
                initial={{ scale: 0.3, rotate: -15 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: 'spring', stiffness: 200, damping: 12, delay: 0.15 }}
              >
                <Image src="/agdi-logo-new.webp" alt="AgDi Automation" width={200} height={92} className="object-contain" priority />
              </motion.div>
            </motion.div>

            {/* Heading */}
            <div className="text-center">
              <motion.h4
                className="text-[20px] font-bold text-[#212529] dark:text-gray-100 font-['Manrope',sans-serif] mt-[24px] mb-2"
                initial={{ y: 15, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.35, duration: 0.5, ease: 'easeOut' }}
              >
                Welcome Back !
              </motion.h4>
              <motion.p
                className="text-[13px] font-medium text-[#919AA3] dark:text-gray-400 font-['Manrope',sans-serif]"
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.5, duration: 0.5, ease: 'easeOut' }}
              >
                Sign in to continue
              </motion.p>
            </div>

            {/* Form */}
            <motion.div
              className="p-2 mt-8"
              initial={{ y: 30, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.55, duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
            >
              <form onSubmit={handleSubmit}>
                <motion.div
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.65, duration: 0.4 }}
                >
                  <MaterialOutlinedField
                    label="Username"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    icon={<User className="size-[24px]" />}
                    required
                    autoFocus
                  />
                </motion.div>

                <motion.div
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.75, duration: 0.4 }}
                >
                  <MaterialOutlinedField
                    label="Password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    icon={<Lock className="size-[24px]" />}
                    required
                    suffixIcon={showPassword ? <Eye className="size-[24px]" /> : <EyeOff className="size-[24px]" />}
                    onSuffixClick={() => setShowPassword(!showPassword)}
                  />
                </motion.div>

                {/* Error message */}
                <AnimatePresence>
                  {error && (
                    <motion.div
                      className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-[12px] px-3 py-2.5 rounded-[4px] flex items-center gap-2 mb-4"
                      initial={{ height: 0, opacity: 0, scale: 0.95 }}
                      animate={{ height: 'auto', opacity: 1, scale: 1 }}
                      exit={{ height: 0, opacity: 0, scale: 0.95 }}
                      transition={{ duration: 0.25 }}
                    >
                      <XCircle className="size-3.5 shrink-0" />
                      {error}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Forgot Password */}
                <motion.div
                  className="flex justify-between items-center pt-[15px] pb-[20px]"
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.85, duration: 0.4 }}
                >
                  <div />
                  <button
                    type="button"
                    className="text-[13px] font-medium text-[#555555] dark:text-gray-400 hover:text-[#3F51B5] dark:hover:text-indigo-400 font-['Poppins',sans-serif] no-underline cursor-pointer bg-transparent border-none"
                  >
                    Forgot Password?
                  </button>
                </motion.div>

                {/* Login button */}
                <motion.div
                  className="flex justify-center"
                  initial={{ y: 15, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.95, duration: 0.4 }}
                >
                  <Button
                    type="submit"
                    disabled={loading}
                    className="h-[36px] min-w-[74px] px-6 bg-[#3F51B5] hover:bg-[#3949AB] text-white text-[14px] font-medium tracking-[1.25px] rounded-[4px] cursor-pointer transition-colors duration-150 font-['Roboto',sans-serif] normal-case"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="size-4 animate-spin mr-1" />
                        Login
                      </>
                    ) : (
                      'Login'
                    )}
                  </Button>
                </motion.div>
              </form>
            </motion.div>
          </div>
        </div>
      </div>

      {/* ─── RIGHT: Hero ─── */}
      <motion.div
        className="hidden lg:block lg:w-2/3 relative overflow-hidden"
        initial={{ x: 80, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
      >
        <img
          src="/agdi-hero-illustration.png"
          alt="AgDi - Agricultural Digital Intelligence"
          className="w-full h-full object-cover"
        />
      </motion.div>
    </div>
  )
}

export type { AuthUser }
