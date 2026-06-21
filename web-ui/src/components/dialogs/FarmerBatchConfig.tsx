'use client'

import React, { useCallback } from 'react'
import { Label } from '@/components/ui/label'

const FARMER_TYPES = [
  { value: 'fpc_member', label: 'FPC Member', desc: 'Land, Crop, KYC, Bank, Additional' },
  { value: 'borrower', label: 'Borrower Farmer', desc: 'All 13 steppers' },
  { value: 'walkin', label: 'Walk-in Farmer (Landless)', desc: 'Bank, Additional only' },
] as const

const TYPE_STEPPER_MAP: Record<string, string[]> = {
  fpc_member: ['address', 'additional_details', 'land', 'crop', 'kyc', 'bank'],
  borrower: ['address', 'other_details', 'family', 'additional_details', 'land', 'crop', 'kyc', 'vehicle', 'income', 'bank', 'irrigation', 'award', 'loan'],
  walkin: ['address', 'additional_details', 'bank'],
}

export interface FarmerConfig {
  farmer_type: string
  overrides: {
    steppers?: string[]
    farmer_category?: number[]
    address_chain?: Record<string, number>
    field_defaults?: Record<string, number>
  }
  workflow?: {
    verify?: boolean
    approve?: boolean
  }
}

interface Props {
  value: FarmerConfig
  onChange: (config: FarmerConfig) => void
}

export function FarmerBatchConfig({ value, onChange }: Props) {
  const farmerType = value?.farmer_type ?? 'fpc_member'
  const overrides = value?.overrides ?? {}
  const workflow = value?.workflow ?? {}

  const handleTypeChange = useCallback((newType: string) => {
    onChange({
      farmer_type: newType,
      overrides: { ...overrides, steppers: undefined },
      workflow,
    })
  }, [overrides, workflow, onChange])

  const setWorkflow = useCallback((key: 'verify' | 'approve', enabled: boolean) => {
    onChange({
      ...value,
      workflow: {
        ...workflow,
        [key]: enabled,
        ...(key === 'verify' && !enabled ? { approve: false } : {}),
      },
    })
  }, [value, workflow, onChange])

  return (
    <div className="space-y-3">
      {/* Farmer Type */}
      <div className="space-y-1.5">
        <Label className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">Farmer Type</Label>
        <div className="grid grid-cols-3 gap-1.5">
          {FARMER_TYPES.map((t) => (
            <button
              key={t.value}
              type="button"
              onClick={() => handleTypeChange(t.value)}
              className={`text-left px-2.5 py-2 rounded-md border text-[11px] transition-all cursor-pointer ${
                farmerType === t.value
                  ? 'border-[#3F51B5] bg-[#3F51B5]/[0.08] dark:bg-[#3F51B5]/20 text-[#3F51B5] dark:text-[#7986CB]'
                  : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500'
              }`}
            >
              <div className="font-medium">{t.label}</div>
              <div className="text-[10px] opacity-70 mt-0.5">{t.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Workflow Transitions */}
      <div className="p-3 rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50">
        <Label className="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wider font-medium">Workflow</Label>
        <div className="mt-2 space-y-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={workflow.verify ?? false}
              onChange={(e) => setWorkflow('verify', e.target.checked)}
              className="size-3.5 rounded border-gray-300 text-[#3F51B5] focus:ring-[#3F51B5] cursor-pointer"
            />
            <span className="text-[11px] text-gray-700 dark:text-gray-300">Verify after creation</span>
          </label>
          <label className={`flex items-center gap-2 cursor-pointer ${!workflow.verify ? 'opacity-40 pointer-events-none' : ''}`}>
            <input
              type="checkbox"
              checked={workflow.approve ?? false}
              disabled={!workflow.verify}
              onChange={(e) => setWorkflow('approve', e.target.checked)}
              className="size-3.5 rounded border-gray-300 text-[#3F51B5] focus:ring-[#3F51B5] cursor-pointer disabled:cursor-not-allowed"
            />
            <span className="text-[11px] text-gray-700 dark:text-gray-300">Approve after verification</span>
          </label>
        </div>
      </div>
    </div>
  )
}
