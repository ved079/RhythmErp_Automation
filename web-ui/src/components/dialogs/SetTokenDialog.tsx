'use client'

import React, { useState, useMemo } from 'react'
import { Key, Eye, EyeOff, AlertTriangle } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

interface Props {
  open: boolean
  onClose: () => void
  erpToken: string
  setErpToken: (token: string) => void
  erpTenantId: string
  setErpTenantId: (id: string) => void
}

function validateToken(raw: string): 'empty' | 'valid' | 'bad_prefix' | 'bad_format' {
  if (!raw.trim()) return 'empty'
  const token = raw.startsWith('Bearer ') ? raw.slice(7) : raw
  if (!token.startsWith('eyJ')) return 'bad_prefix'
  const parts = token.split('.')
  if (parts.length !== 3 || token.length < 100) return 'bad_format'
  return 'valid'
}

export function SetTokenDialog({ open, onClose, erpToken, setErpToken, erpTenantId, setErpTenantId }: Props) {
  const [showToken, setShowToken] = useState(false)
  const tokenStatus = useMemo(() => validateToken(erpToken), [erpToken])

  const INPUT = 'w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-[12px] bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-[#3F51B5]/50'

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-[420px] dark:bg-gray-800 dark:border-gray-600/60">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div className="size-7 rounded-lg bg-[#3F51B5]/10 dark:bg-[#3F51B5]/20 flex items-center justify-center">
              <Key className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
            </div>
            Set API Token
          </DialogTitle>
          <DialogDescription className="text-[12px] text-gray-500 dark:text-gray-400">
            Enter your ERP bearer token and tenant ID.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-2">
          <div>
            <label className="text-[11px] text-gray-400 dark:text-gray-500 mb-1 block">Bearer Token</label>
            <div className="relative">
              <input
                type={showToken ? 'text' : 'password'}
                value={erpToken}
                onChange={e => setErpToken(e.target.value)}
                placeholder="Bearer eyJ..."
                className={`pr-8 ${INPUT} ${tokenStatus === 'valid' ? 'border-green-400 dark:border-green-600' : tokenStatus !== 'empty' ? 'border-red-400 dark:border-red-600' : ''}`}
              />
              <button
                type="button"
                onClick={() => setShowToken(s => !s)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors cursor-pointer"
                tabIndex={-1}
              >
                {showToken ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
              </button>
            </div>

            {tokenStatus !== 'empty' && tokenStatus !== 'valid' && (
              <div className="mt-2 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-3 space-y-2">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="size-3.5 text-red-500 shrink-0" />
                  <span className="text-[12px] font-semibold text-red-600 dark:text-red-400">
                    {tokenStatus === 'bad_prefix' ? 'Token must start with eyJ…' : 'Token format looks incorrect'}
                  </span>
                </div>
                <p className="text-[11px] text-red-500 dark:text-red-400 leading-relaxed">
                  {tokenStatus === 'bad_prefix'
                    ? 'Copy the token from the Authorization header in DevTools — not the full "Bearer eyJ…" line, just the part after "Bearer ".'
                    : 'The token appears too short or is missing parts. A valid JWT has 3 dot-separated sections.'}
                </p>
              </div>
            )}

            {tokenStatus === 'valid' && (
              <p className="mt-1.5 text-[11px] text-green-600 dark:text-green-400 flex items-center gap-1">
                <span className="inline-block size-2 rounded-full bg-green-500" />
                Token looks valid
              </p>
            )}
          </div>

          <div>
            <label className="text-[11px] text-gray-400 dark:text-gray-500 mb-1 block">Tenant ID</label>
            <input
              type="text"
              value={erpTenantId}
              onChange={e => setErpTenantId(e.target.value)}
              placeholder="e.g. 681"
              className={INPUT}
            />
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose} className="cursor-pointer">
            Close
          </Button>
          <Button onClick={onClose} className="bg-[#3F51B5] hover:bg-[#3949AB] cursor-pointer">
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
