'use client'

import React, { useState } from 'react'
import { Key, Eye, EyeOff, X } from 'lucide-react'
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

export function SetTokenDialog({ open, onClose, erpToken, setErpToken, erpTenantId, setErpTenantId }: Props) {
  const [showToken, setShowToken] = useState(false)

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
            Enter your ERP bearer token and tenant ID for API test runs.
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
                className={`pr-8 ${INPUT}`}
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
