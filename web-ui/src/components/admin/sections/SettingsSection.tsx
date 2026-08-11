'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { withCsrf } from '@/lib/csrf-client'
import { toast } from 'sonner'
import {
  RotateCcw, Save, Settings as SettingsIcon,
} from 'lucide-react'
import Spinner from '@/components/ui/Spinner'

interface SystemSetting {
  id: string; key: string; label: string; value: string
  type: 'text' | 'number' | 'boolean' | 'select'; description: string; category: string
  options?: string[]
}

export function SettingsSection() {
  const [settings, setSettings] = useState<SystemSetting[]>([])
  const [settingsLoaded, setSettingsLoaded] = useState(false)

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const res = await fetch('/api/admin/settings')
        if (!res.ok) throw new Error('Failed')
        const data = await res.json()
        setSettings(data.settings || [])
      } catch { /* empty */ } finally { setSettingsLoaded(true) }
    }
    loadSettings()
  }, [])

  const handleSaveSetting = async (setting: SystemSetting, newValue: string) => {
    try {
      const res = await fetch(`/api/admin/settings/${setting.id}`, withCsrf({
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: newValue }),
      }))
      if (!res.ok) throw new Error('Failed to save')
      setSettings(prev => prev.map(s => s.id === setting.id ? { ...s, value: newValue } : s))
      toast.success('Setting saved', { description: `"${setting.key}" has been updated.` })
    } catch (err) { toast.error('Save failed', { description: err instanceof Error ? err.message : 'Could not save the setting.' }) }
  }

  const handleSeedSettings = async () => {
    try {
      const res = await fetch('/api/admin/settings/seed', withCsrf({ method: 'POST' }))
      if (!res.ok) throw new Error('Failed to reset')
      const data = await res.json()
      setSettings(data.settings || [])
      toast.success('Settings reset', { description: 'All settings have been restored to their defaults.' })
    } catch (err) { toast.error('Reset failed', { description: err instanceof Error ? err.message : 'Could not reset settings.' }) }
  }

  // Track only locally-modified (unsaved) values
  const [dirtyMap, setDirtyMap] = useState<Record<string, string>>({})

  const getLocalValue = (s: SystemSetting) => dirtyMap[s.id] ?? s.value

  const setLocalValue = (id: string, value: string) => {
    setDirtyMap(prev => ({ ...prev, [id]: value }))
  }

  const categories = [...new Set(settings.map(s => s.category))]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Settings</h2>
        <Button variant="outline" onClick={handleSeedSettings} className="text-xs h-8 font-['Poppins']">
          <RotateCcw className="size-3.5 mr-1" /> Reset to Defaults
        </Button>
      </div>
      {!settingsLoaded ? (
        <div className="flex justify-center py-12"><Spinner size={24} /></div>
      ) : settings.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-12 border border-gray-100 dark:border-gray-700 text-center">
          <SettingsIcon className="size-10 text-[#888] dark:text-gray-500 mx-auto mb-2" />
          <p className="text-sm text-[#888] dark:text-gray-400 font-['Poppins']">No settings loaded</p>
        </div>
      ) : (
        <div className="space-y-6">
          {categories.map(cat => (
            <div key={cat} className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
              <div className="px-5 py-3 bg-[#E8EAF6] dark:bg-[#1A237E]/30">
                <h3 className="text-sm font-semibold font-['Poppins'] text-[#3F51B5] dark:text-[#7986CB]">{cat}</h3>
              </div>
              <div className="divide-y divide-gray-50 dark:divide-gray-700/50">
                {settings.filter(s => s.category === cat).map(s => (
                  <div key={s.id} className="flex items-center gap-4 px-5 py-4">
                    <div className="flex-1 min-w-0">
                      <Label className="text-xs font-medium text-[#333] dark:text-gray-100 font-['Poppins']">{s.label}</Label>
                      <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Poppins'] mt-0.5">{s.description}</p>
                    </div>
                    <div className="w-48 shrink-0">
                      {s.type === 'boolean' ? (
                        <div className="flex items-center gap-2">
                          <Switch checked={getLocalValue(s) === 'true'}
                            onCheckedChange={v => setLocalValue(s.id, String(v))} />
                          <span className="text-[10px] text-[#888] dark:text-gray-400 font-['Poppins']">{getLocalValue(s) === 'true' ? 'On' : 'Off'}</span>
                        </div>
                      ) : s.type === 'select' ? (
                        <Select value={getLocalValue(s)} onValueChange={v => setLocalValue(s.id, v)}>
                          <SelectTrigger className="h-8 text-xs"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            {(s.options || ['info', 'debug', 'warning', 'error']).map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}
                          </SelectContent>
                        </Select>
                      ) : (
                        <Input type={s.type} value={getLocalValue(s)} onChange={e => setLocalValue(s.id, e.target.value)}
                          className="h-8 text-xs font-['Poppins']" />
                      )}
                    </div>
                    <Button size="sm" onClick={() => { handleSaveSetting(s, getLocalValue(s)); setDirtyMap(prev => { const n = { ...prev }; delete n[s.id]; return n }) }}
                      disabled={getLocalValue(s) === s.value}
                      className="h-7 text-[10px] bg-[#3F51B5] hover:bg-[#2D3FC7] text-white font-['Poppins']">
                      <Save className="size-3 mr-1" /> Save
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
