'use client'

import { useRouter } from 'next/navigation'
import { Shield, User } from 'lucide-react'

const PANEL_KEY = 'admin_panel_default'

export function getPanelPreference(): 'admin' | 'user' {
  if (typeof window === 'undefined') return 'admin'
  return (localStorage.getItem(PANEL_KEY) as 'admin' | 'user') || 'admin'
}

export function setPanelPreference(panel: 'admin' | 'user') {
  localStorage.setItem(PANEL_KEY, panel)
}

interface PanelToggleProps {
  activePanel: 'admin' | 'user'
}

export function PanelToggle({ activePanel }: PanelToggleProps) {
  const router = useRouter()

  const handleSwitch = (panel: 'admin' | 'user') => {
    if (panel === activePanel) return
    router.push(panel === 'admin' ? '/admin' : '/')
  }

  return (
    <div className="flex items-center rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden h-7" title="Switch panels">
      <button
        onClick={() => handleSwitch('admin')}
        className={`flex items-center gap-1 px-2 h-full text-[10px] font-medium transition-colors cursor-pointer ${
          activePanel === 'admin'
            ? 'bg-[#3F51B5] text-white'
            : 'bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
        }`}
      >
        <Shield className="size-3" />
        Admin
      </button>
      <button
        onClick={() => handleSwitch('user')}
        className={`flex items-center gap-1 px-2 h-full text-[10px] font-medium transition-colors cursor-pointer ${
          activePanel === 'user'
            ? 'bg-[#3F51B5] text-white'
            : 'bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
        }`}
      >
        <User className="size-3" />
        User
      </button>
    </div>
  )
}
