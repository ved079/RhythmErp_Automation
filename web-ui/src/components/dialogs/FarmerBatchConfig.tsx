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
  farmer_types: string[]
  overrides: {
    steppers?: string[]
    farmer_category?: number[]
    address_chain?: Record<string, number>
    field_defaults?: Record<string, number>
  }
}

interface Props {
  value: FarmerConfig
  onChange: (config: FarmerConfig) => void
}

export function FarmerBatchConfig({ value, onChange }: Props) {
  const selectedTypes: string[] = value?.farmer_types ?? ['fpc_member']
  const overrides = value?.overrides ?? {}

  const toggleType = useCallback((type: string) => {
    const current = selectedTypes
    const next = current.includes(type)
      ? current.filter((t) => t !== type)
      : [...current, type]
    if (next.length === 0) return
    onChange({ farmer_types: next, overrides: { ...overrides, steppers: undefined } })
  }, [selectedTypes, overrides, onChange])

  return (
    <div className="space-y-1.5">
      <Label className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">Farmer Type</Label>
      <div className="grid grid-cols-3 gap-1.5">
        {FARMER_TYPES.map((t) => {
          const active = selectedTypes.includes(t.value)
          return (
            <button
              key={t.value}
              type="button"
              onClick={() => toggleType(t.value)}
              className={`text-left px-2.5 py-2 rounded-md border text-[11px] transition-all cursor-pointer ${
                active
                  ? 'border-[#3F51B5] bg-[#3F51B5]/[0.08] dark:bg-[#3F51B5]/20 text-[#3F51B5] dark:text-[#7986CB]'
                  : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500'
              }`}
            >
              <div className="font-medium">{t.label}</div>
              <div className="text-[10px] opacity-70 mt-0.5">{t.desc}</div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
