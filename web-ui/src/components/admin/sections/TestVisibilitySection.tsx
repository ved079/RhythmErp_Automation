'use client'

import React, { useState, useEffect, useCallback } from 'react'
import {
  EyeOff, RotateCcw, FolderTree, ChevronRight,
  Search, Pencil, Eye, Monitor, Server, List, AlertTriangle,
  CheckCircle2, XCircle, Save, EyeOff as EyeOffIcon,
  ChevronDown,
} from 'lucide-react'
import Spinner from '@/components/ui/Spinner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '@/components/ui/dialog'
import { withCsrf } from '@/lib/csrf-client'
import { TestUserVisibilityDialog } from '@/components/admin/TestUserVisibilityDialog'
import { toast } from 'sonner'

export function TestVisibilitySection() {
  const [overrides, setOverrides] = useState<Record<string, { displayName?: string; disabled: boolean }>>({})
  const [syncingTests, setSyncingTests] = useState(false)
  const [exclusionCounts, setExclusionCounts] = useState<Record<string, number>>({})
  const [modulesTree, setModulesTree] = useState<{ name: string; display: string; sub_modules: { name: string; display: string; tests: { name: string; display_name: string; type?: string }[] }[] }[]>([])
  const [testVisibilitySearch, setTestVisibilitySearch] = useState('')
  const [selectedVisModule, setSelectedVisModule] = useState<string>('')
  const [selectedVisSubModule, setSelectedVisSubModule] = useState<string>('')
  const [visSelectedTests, setVisSelectedTests] = useState<Set<string>>(new Set())
  const [visCollapsedSubs, setVisCollapsedSubs] = useState<Set<string>>(new Set())
  const [batchActionLoading, setBatchActionLoading] = useState(false)
  const [visSelectedType, setVisSelectedType] = useState<'all' | 'ui' | 'api' | null>(null)
  const [visActionMode, setVisActionMode] = useState<'name' | 'visibility' | null>(null)
  const [showRawNames, setShowRawNames] = useState(() => typeof window !== 'undefined' && localStorage.getItem('showRawNames') === 'true')
  const [visibilityDialogOpen, setVisibilityDialogOpen] = useState(false)
  const [visibilityDialogTest, setVisibilityDialogTest] = useState<{ testName: string; displayName: string } | null>(null)
  const [editingOverrideName, setEditingOverrideName] = useState<string | null>(null)
  const [editingNameValue, setEditingNameValue] = useState('')
  const [visDetailOpen, setVisDetailOpen] = useState(false)
  const [visDetailTest, setVisDetailTest] = useState<{ testName: string; displayName: string; testType: string; disabled: boolean; excluded: number } | null>(null)

  const loadOverrides = useCallback(async () => {
    try {
      const [ovRes, exRes] = await Promise.all([
        fetch('/api/admin/tests/overrides'),
        fetch('/api/admin/tests/exclusions'),
      ])
      if (ovRes.ok) {
        const ovData = await ovRes.json()
        const map: Record<string, { displayName?: string; disabled: boolean }> = {}
        for (const o of ovData.overrides || []) {
          map[o.testName] = { displayName: o.displayName, disabled: o.disabled }
        }
        setOverrides(map)
      }
      if (exRes.ok) {
        const exData = await exRes.json()
        const counts: Record<string, number> = {}
        for (const e of exData.exclusions || []) {
          counts[e.testName] = (counts[e.testName] || 0) + 1
        }
        setExclusionCounts(counts)
      }
    } catch { /* silent */ }
  }, [])

  const loadModulesTree = useCallback(async () => {
    try {
      const res = await fetch('/api/proxy?path=modules')
      if (res.ok) {
        const data = await res.json()
        setModulesTree(data.modules || [])
      }
    } catch { /* silent */ }
  }, [])

  useEffect(() => {
    loadOverrides()
    loadModulesTree()
  }, [loadOverrides, loadModulesTree])

  const syncTestsFromBackend = useCallback(async () => {
    setSyncingTests(true)
    try {
      const res = await fetch('/api/proxy?path=modules')
      if (!res.ok) { toast.error('Failed to fetch modules from backend'); return }
      const data = await res.json()
      const modules: { name: string; sub_modules: { name: string; tests: { name: string; display_name?: string }[] }[] }[] = data.modules || []
      const testNames: { name: string; displayName: string }[] = []
      for (const mod of modules) {
        for (const sub of mod.sub_modules) {
          for (const t of sub.tests) {
            testNames.push({ name: t.name, displayName: t.display_name || t.name.split('::').pop() || t.name })
          }
        }
      }
      if (testNames.length === 0) { toast.error('No tests found in backend'); return }
      setModulesTree(modules as any)
      let upserted = 0
      for (const t of testNames) {
        const r = await fetch('/api/admin/tests/overrides', withCsrf({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ testName: t.name, displayName: t.displayName }),
        }))
        if (r.ok) upserted++
      }
      toast.success(`Synced ${upserted} tests from backend`)
      loadOverrides()
    } catch (e) {
      toast.error('Sync failed: ' + (e instanceof Error ? e.message : 'Unknown error'))
    } finally {
      setSyncingTests(false)
    }
  }, [loadOverrides])

  const hasOverrides = Object.keys(overrides).length > 0
  const searchLower = testVisibilitySearch.toLowerCase()

  const testMatches = (t: { name: string; display_name: string; type?: string }) =>
    (visSelectedType === 'all' || (t.type || 'ui') === visSelectedType) &&
    (!searchLower || t.name.toLowerCase().includes(searchLower) || t.display_name.toLowerCase().includes(searchLower))

  const saveOverride = async (tName: string, data: { displayName?: string | null; disabled?: boolean }) => {
    try {
      const res = await fetch('/api/admin/tests/overrides', withCsrf({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ testName: tName, ...data }),
      }))
      if (res.ok) loadOverrides()
    } catch { /* silent */ }
  }

  const batchUpdate = async (updates: { testName: string; disabled?: boolean; displayName?: string | null }[]) => {
    if (updates.length === 0) return
    setBatchActionLoading(true)
    try {
      const res = await fetch('/api/admin/tests/overrides/batch', withCsrf({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ updates }),
      }))
      if (res.ok) {
        setVisSelectedTests(new Set())
        loadOverrides()
        toast.success(`Updated ${updates.length} test${updates.length !== 1 ? 's' : ''}`)
      } else {
        toast.error('Batch update failed')
      }
    } catch {
      toast.error('Batch update failed')
    } finally {
      setBatchActionLoading(false)
    }
  }

  const saveExclusions = async (tName: string, userIds: string[]) => {
    try {
      const exRes = await fetch(`/api/admin/tests/exclusions?testName=${encodeURIComponent(tName)}`)
      if (!exRes.ok) return
      const exData = await exRes.json()
      const currentIds = new Set(exData.exclusions?.map((e: { userId: string }) => e.userId) || [])
      const toRemove = (exData.exclusions || []).filter((e: { userId: string }) => !userIds.includes(e.userId))
      for (const e of toRemove) {
        await fetch(`/api/admin/tests/exclusions/${e.id}`, withCsrf({ method: 'DELETE' }))
      }
      const toAdd = userIds.filter(id => !currentIds.has(id))
      if (toAdd.length > 0) {
        await fetch('/api/admin/tests/exclusions', withCsrf({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ testName: tName, userIds: toAdd }),
        }))
      }
      loadOverrides()
    } catch { /* silent */ }
  }

  const commitRename = async () => {
    if (!editingOverrideName) return
    await saveOverride(editingOverrideName, { displayName: editingNameValue || null })
    setEditingOverrideName(null)
    setEditingNameValue('')
  }

  const handleDetailRename = async () => {
    if (!visDetailTest) return
    await saveOverride(visDetailTest.testName, { displayName: editingNameValue || null })
    setEditingNameValue('')
    setVisDetailOpen(false)
  }

  const toggleTestSelection = (testName: string) => {
    setVisSelectedTests(prev => {
      const next = new Set(prev)
      if (next.has(testName)) next.delete(testName); else next.add(testName)
      return next
    })
  }

  if (!hasOverrides) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Test Visibility</h2>
          <Button onClick={syncTestsFromBackend} disabled={syncingTests} className="h-8 text-xs bg-[#2D3FC7] hover:bg-[#3F51B5] cursor-pointer gap-1.5">
            {syncingTests ? <Spinner size={14} /> : <RotateCcw className="size-3.5" />}
            {syncingTests ? 'Syncing...' : 'Sync from Backend'}
          </Button>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-6 border border-gray-100 dark:border-gray-700 text-center">
          <EyeOff className="size-8 mx-auto mb-2 text-[#888]" />
          <p className="text-sm text-[#888] font-['Poppins']">No test overrides yet. Click &quot;Sync from Backend&quot; to discover tests, then hide or rename them.</p>
        </div>
      </div>
    )
  }

  const totalDisabled = Object.values(overrides).filter(o => o.disabled).length
  const totalHidden = Object.values(exclusionCounts).reduce((a, c) => a + c, 0)
  const moduleOptions = modulesTree.length > 0
    ? modulesTree.map(m => ({ value: m.name, label: m.display }))
    : []
  const selectedMod = selectedVisModule ? modulesTree.find(m => m.name === selectedVisModule) : null
  const activeSubModules = selectedMod && selectedVisSubModule && selectedVisSubModule !== '__all__'
    ? selectedMod.sub_modules.filter(s => s.name === selectedVisSubModule)
    : selectedMod?.sub_modules || []
  const selectedModTests = activeSubModules.flatMap(s => s.tests.map(t => ({
      ...t,
      modName: selectedMod!.name,
      modDisplay: selectedMod!.display,
      subName: s.name,
      subDisplay: s.display,
    })))
  const allSelectedDisabled = selectedModTests.length > 0 && selectedModTests.every(t => overrides[t.name]?.disabled)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 whitespace-nowrap">Test Visibility</h2>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs font-['Poppins'] shrink-0">{Object.keys(overrides).length} overrides</Badge>
            {totalDisabled > 0 && <Badge variant="outline" className="text-xs text-red-600 border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800 shrink-0">{totalDisabled} disabled</Badge>}
            {totalHidden > 0 && <Badge variant="outline" className="text-xs text-orange-600 border-orange-200 bg-orange-50 dark:bg-orange-900/20 dark:border-orange-800 shrink-0">{totalHidden} hidden</Badge>}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {visActionMode !== null && (
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-[#888]" />
              <Input
                value={testVisibilitySearch}
                onChange={e => setTestVisibilitySearch(e.target.value)}
                placeholder="Search tests..."
                className="h-8 pl-8 pr-3 text-[12px] font-['Poppins'] w-48"
              />
            </div>
          )}
          <Button onClick={syncTestsFromBackend} disabled={syncingTests} className="h-8 text-xs bg-[#2D3FC7] hover:bg-[#3F51B5] cursor-pointer gap-1.5">
            {syncingTests ? <Spinner size={14} /> : <RotateCcw className="size-3.5" />}
            {syncingTests ? 'Syncing...' : 'Sync'}
          </Button>
        </div>
      </div>

      {selectedVisModule && (
        <div className="flex items-center flex-wrap gap-0.5 text-[12px] font-['Poppins'] bg-gray-50 dark:bg-gray-800/50 rounded-lg px-2.5 py-1.5 border border-gray-100 dark:border-gray-700/50">
          <button onClick={() => { setSelectedVisModule(''); setSelectedVisSubModule(''); setVisSelectedTests(new Set()); setTestVisibilitySearch(''); setVisSelectedType(null); setVisActionMode(null) }}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-[#888] hover:text-white hover:bg-[#3F51B5] transition-all">
            <FolderTree className="size-3.5" />
            <span>Modules</span>
          </button>
          <ChevronRight className="size-3 text-[#ccc] shrink-0" />
          <button onClick={() => { setSelectedVisSubModule(''); setVisSelectedTests(new Set()); setTestVisibilitySearch(''); setVisSelectedType(null); setVisActionMode(null) }}
            className={`px-2 py-1 rounded-md transition-all flex items-center gap-1.5 ${
              !selectedVisSubModule && visSelectedType === null
                ? 'bg-[#3F51B5] text-white font-semibold'
                : 'text-[#888] hover:text-white hover:bg-[#3F51B5]'
            }`}>
            <FolderTree className="size-3.5" />
            <span>{selectedMod?.display}</span>
          </button>
          {selectedVisSubModule && (
            <>
              <ChevronRight className="size-3 text-[#ccc] shrink-0" />
              <button onClick={() => { setVisSelectedType(null); setVisActionMode(null); setVisSelectedTests(new Set()) }}
                className={`px-2 py-1 rounded-md transition-all flex items-center gap-1.5 ${
                  visSelectedType === null
                    ? 'bg-[#3F51B5] text-white font-semibold'
                    : 'text-[#888] hover:text-white hover:bg-[#3F51B5]'
                }`}>
                <FolderTree className="size-3.5" />
                <span>{selectedVisSubModule === '__all__' ? 'All sub-modules' : selectedMod?.sub_modules.find(s => s.name === selectedVisSubModule)?.display || selectedVisSubModule}</span>
              </button>
            </>
          )}
          {visSelectedType !== null && (
            <>
              <ChevronRight className="size-3 text-[#ccc] shrink-0" />
              <button onClick={() => { setVisActionMode(null) }}
                className={`px-2 py-1 rounded-md transition-all flex items-center gap-1.5 ${
                  visActionMode === null
                    ? 'bg-[#3F51B5] text-white font-semibold'
                    : 'text-[#888] hover:text-white hover:bg-[#3F51B5]'
                }`}>
                {visSelectedType === 'all' ? <List className="size-3.5" /> : visSelectedType === 'ui' ? <Monitor className="size-3.5" /> : <Server className="size-3.5" />}
                <span>{visSelectedType === 'all' ? 'All' : visSelectedType.toUpperCase()}</span>
              </button>
            </>
          )}
          {visActionMode !== null && (
            <>
              <ChevronRight className="size-3 text-[#ccc] shrink-0" />
              <span className="px-2 py-1 rounded-md bg-[#3F51B5] text-white font-semibold flex items-center gap-1.5">
                {visActionMode === 'name' ? <Pencil className="size-3.5" /> : <Eye className="size-3.5" />}
                <span>{visActionMode === 'name' ? 'Rename' : 'Visibility'}</span>
              </span>
            </>
          )}
        </div>
      )}

      {!selectedVisModule ? (
        <>
          <p className="text-[13px] text-[#888] font-['Poppins']">Select a module to manage test visibility</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {moduleOptions.map(mo => {
              const mod = modulesTree.find(x => x.name === mo.value)
              if (!mod) return null
              const modTotal = mod.sub_modules.reduce((a, s) => a + s.tests.length, 0)
              const modDisabled = mod.sub_modules.reduce((a, s) => a + s.tests.filter(t => overrides[t.name]?.disabled).length, 0)
              const modHidden = mod.sub_modules.reduce((a, s) => a + s.tests.filter(t => (exclusionCounts[t.name] || 0) > 0).length, 0)
              return (
                <button key={mo.value} onClick={() => { setSelectedVisModule(mo.value); setSelectedVisSubModule(''); setVisSelectedTests(new Set()); setTestVisibilitySearch(''); setVisSelectedType(null); setVisActionMode(null) }}
                  className="text-left bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 hover:shadow-md hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 transition-all cursor-pointer group">
                  <div className="flex items-center gap-2.5 mb-2.5">
                    <div className="w-8 h-8 rounded-lg bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center group-hover:bg-[#C5CAE9] dark:group-hover:bg-[#1A237E]/50 transition-colors">
                      <FolderTree className="size-4 text-[#3F51B5]" />
                    </div>
                    <span className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 group-hover:text-[#3F51B5] transition-colors">{mod.display}</span>
                  </div>
                  <div className="flex items-center gap-2.5 text-[11px] font-['Poppins']">
                    <span className="text-[#888]">{modTotal} test{modTotal !== 1 ? 's' : ''}</span>
                    {modDisabled > 0 && <span className="text-red-500 font-medium">{modDisabled} off</span>}
                    {modHidden > 0 && <span className="text-orange-500 font-medium">{modHidden} hid</span>}
                  </div>
                  <div className="mt-1.5 text-[10px] text-[#999] font-['Poppins']">{mod.sub_modules.length} sub-module{mod.sub_modules.length !== 1 ? 's' : ''}</div>
                </button>
              )
            })}
          </div>
        </>
      ) : !selectedVisSubModule ? (
        <>
          <p className="text-[13px] text-[#888] font-['Poppins']">Select a sub-module in <span className="font-semibold text-[#333] dark:text-gray-100">{selectedMod?.display}</span></p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {activeSubModules.map(sm => {
              const smDisabled = sm.tests.filter(t => overrides[t.name]?.disabled).length
              const smHidden = sm.tests.filter(t => (exclusionCounts[t.name] || 0) > 0).length
              return (
                <button key={sm.name} onClick={() => { setSelectedVisSubModule(sm.name); setVisSelectedTests(new Set()); setVisSelectedType(null); setVisActionMode(null) }}
                  className="text-left bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 hover:shadow-md hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 transition-all cursor-pointer group">
                  <div className="flex items-center gap-2.5 mb-2">
                    <div className="w-8 h-8 rounded-lg bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center group-hover:bg-[#C5CAE9] dark:group-hover:bg-[#1A237E]/50 transition-colors">
                      <FolderTree className="size-4 text-[#3F51B5]" />
                    </div>
                    <span className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 group-hover:text-[#3F51B5] transition-colors">{sm.display}</span>
                  </div>
                  <div className="flex items-center gap-2.5 text-[11px] font-['Poppins']">
                    <span className="text-[#888]">{sm.tests.length} test{sm.tests.length !== 1 ? 's' : ''}</span>
                    {smDisabled > 0 && <span className="text-red-500 font-medium">{smDisabled} off</span>}
                    {smHidden > 0 && <span className="text-orange-500 font-medium">{smHidden} hid</span>}
                  </div>
                </button>
              )
            })}
            <button onClick={() => { setSelectedVisSubModule('__all__'); setVisSelectedTests(new Set()); setVisSelectedType(null); setVisActionMode(null) }}
              className="col-span-full text-center bg-gradient-to-r from-[#2D3FC7]/5 via-transparent to-[#2D3FC7]/5 dark:from-[#1A237E]/20 dark:to-[#1A237E]/20 rounded-xl border-2 border-dashed border-[#3F51B5]/30 dark:border-[#7986CB]/30 p-4 hover:border-[#3F51B5]/60 dark:hover:border-[#7986CB]/60 hover:from-[#2D3FC7]/10 hover:to-[#2D3FC7]/10 dark:hover:from-[#1A237E]/30 dark:hover:to-[#1A237E]/30 transition-all cursor-pointer">
              <div className="flex items-center justify-center gap-2">
                <List className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
                <span className="text-sm font-semibold font-['Poppins'] text-[#3F51B5] dark:text-[#7986CB]">Load All Sub-modules</span>
              </div>
              <p className="text-[11px] text-[#888] font-['Poppins'] mt-1">{selectedModTests.length} tests total</p>
            </button>
          </div>
        </>
      ) : visSelectedType === null ? (
        <div className="space-y-3">
          <p className="text-[13px] text-[#888] font-['Poppins']">Select test type to view in <span className="font-semibold text-[#333] dark:text-gray-100">{selectedMod?.display} &rsaquo; {selectedVisSubModule === '__all__' ? 'All sub-modules' : selectedMod?.sub_modules.find(s => s.name === selectedVisSubModule)?.display}</span></p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {(['all', 'ui', 'api'] as const).filter(type => {
              if (type === 'all') return true
              const allTypes = new Set(selectedMod!.sub_modules.flatMap(s => s.tests.map(t => t.type || 'ui')))
              return allTypes.has(type)
            }).map(type => (
              <button key={type} onClick={() => { setVisSelectedType(type); setVisActionMode(null) }}
                className="text-left bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 hover:shadow-md hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 transition-all cursor-pointer group">
                <div className="w-10 h-10 rounded-lg bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center mb-3 group-hover:bg-[#C5CAE9] dark:group-hover:bg-[#1A237E]/50 transition-colors">
                  {type === 'all' ? <List className="size-5 text-[#3F51B5]" /> : type === 'ui' ? <Monitor className="size-5 text-[#3F51B5]" /> : <Server className="size-5 text-[#3F51B5]" />}
                </div>
                <div className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 group-hover:text-[#3F51B5] transition-colors">
                  {type === 'all' ? 'All Tests' : type === 'ui' ? 'UI Tests' : 'API Tests'}
                </div>
                <div className="text-[11px] text-[#888] font-['Poppins'] mt-1.5">
                  {type === 'all'
                    ? `${selectedModTests.length} tests total`
                    : `${selectedModTests.filter(t => (t.type || 'ui') === type).length} ${type.toUpperCase()} tests`
                  }
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : !selectedMod ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-8 border border-gray-100 dark:border-gray-700 text-center">
          <AlertTriangle className="size-10 text-orange-500 mx-auto mb-2" />
          <p className="text-sm text-[#888] dark:text-gray-400 font-['Poppins']">Module data not loaded. Sync from backend first.</p>
        </div>
      ) : visActionMode === null ? (
        <div className="space-y-3">
          <p className="text-[13px] text-[#888] font-['Poppins']">What would you like to do with <span className="font-semibold text-[#333] dark:text-gray-100">{selectedMod?.display} &rsaquo; {selectedVisSubModule === '__all__' ? 'All sub-modules' : selectedMod?.sub_modules.find(s => s.name === selectedVisSubModule)?.display} &rsaquo; {visSelectedType === 'all' ? 'All' : visSelectedType?.toUpperCase()} tests</span></p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button onClick={() => setVisActionMode('name')}
              className="text-left bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 hover:shadow-md hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 transition-all cursor-pointer group">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center shrink-0 group-hover:bg-[#C5CAE9] dark:group-hover:bg-[#1A237E]/50 transition-colors">
                  <Pencil className="size-5 text-[#3F51B5]" />
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 group-hover:text-[#3F51B5] transition-colors">Change Name</div>
                  <p className="text-[12px] text-[#888] font-['Poppins'] mt-1 leading-relaxed">Rename display names of tests. Click any test card to edit.</p>
                  <div className="flex items-center gap-3 mt-2 text-[11px] font-['Poppins']">
                    <span className="text-[#888]">{selectedModTests.length} tests</span>
                    <span className="text-[#3F51B5] font-medium">{Object.keys(overrides).length} renamed</span>
                  </div>
                </div>
              </div>
            </button>
            <button onClick={() => setVisActionMode('visibility')}
              className="text-left bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 hover:shadow-md hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 transition-all cursor-pointer group">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center shrink-0 group-hover:bg-[#C5CAE9] dark:group-hover:bg-[#1A237E]/50 transition-colors">
                  <Eye className="size-5 text-[#3F51B5]" />
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 group-hover:text-[#3F51B5] transition-colors">Change Visibility</div>
                  <p className="text-[12px] text-[#888] font-['Poppins'] mt-1 leading-relaxed">Enable or disable tests and control per-user visibility.</p>
                  <div className="flex items-center gap-3 mt-2 text-[11px] font-['Poppins']">
                    <span className="text-[#888]">{selectedModTests.length} tests</span>
                    {totalDisabled > 0 && <span className="text-red-500 font-medium">{totalDisabled} disabled</span>}
                    {totalHidden > 0 && <span className="text-orange-500 font-medium">{totalHidden} hidden</span>}
                  </div>
                </div>
              </div>
            </button>
          </div>
        </div>
      ) : !selectedMod ? (
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-8 border border-gray-100 dark:border-gray-700 text-center">
          <AlertTriangle className="size-10 text-orange-500 mx-auto mb-2" />
          <p className="text-sm text-[#888] dark:text-gray-400 font-['Poppins']">Module data not loaded. Sync from backend first.</p>
        </div>
      ) : visActionMode === 'name' ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between px-4 py-2.5 bg-gradient-to-r from-[#E8EAF6] to-transparent dark:from-[#1A237E]/20 dark:to-transparent rounded-xl border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold font-['Poppins'] text-[#3F51B5] dark:text-[#7986CB]">Rename Tests</span>
              <span className="text-[11px] text-[#888] font-['Poppins']">{selectedMod.display} &rsaquo; {visSelectedType === 'all' ? 'All' : visSelectedType?.toUpperCase()}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-[#888] font-['Poppins']">raw</span>
              <Switch checked={showRawNames} onCheckedChange={(val) => { setShowRawNames(val); localStorage.setItem('showRawNames', String(val)) }} className="shrink-0 scale-75" />
            </div>
          </div>
          {activeSubModules.map(sub => {
            const filteredTests = sub.tests.filter(testMatches)
            if (filteredTests.length === 0) return null
            const subKey = `${selectedMod.name}::${sub.name}`
            return (
              <div key={subKey} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-50 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-800/50">
                  <Pencil className="size-3.5 text-[#888]" />
                  <span className="text-xs font-semibold font-['Poppins'] text-[#555] dark:text-gray-300">{sub.display}</span>
                  <span className="text-[11px] text-[#888] font-['Poppins']">— {filteredTests.length} test{filteredTests.length !== 1 ? 's' : ''}</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2.5 p-3">
                  {filteredTests.map(t => {
                    const ov = overrides[t.name]
                    const displayName = ov?.displayName || t.display_name || t.name.split('::').pop() || t.name
                    const testType = t.type || 'ui'
                    const cardKey = `${selectedMod.name}::${sub.name}::${t.name}`
                    const hasCustomName = ov?.displayName != null && ov.displayName !== t.display_name
                    return (
                      <button key={cardKey} onClick={() => { setVisDetailTest({ testName: t.name, displayName, testType, disabled: false, excluded: 0 }); setEditingNameValue(displayName); setVisDetailOpen(true) }}
                        className="text-left bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 hover:shadow-sm transition-all cursor-pointer group w-full">
                        <div className="flex items-start gap-2 px-3 pt-3 pb-2">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className={`text-[13px] font-['Poppins'] leading-tight block truncate text-[#333] dark:text-gray-100 group-hover:text-[#3F51B5] transition-colors ${hasCustomName ? 'font-semibold' : ''}`}>{displayName}</span>
                              {hasCustomName && (
                                <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 border-[#3F51B5]/30 text-[#3F51B5] dark:text-[#7986CB] shrink-0 font-['Poppins']">edited</Badge>
                              )}
                            </div>
                            <div className="flex items-center gap-1.5 mt-1.5">
                              <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                                testType === 'api'
                                  ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                                  : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                              }`}>{testType.toUpperCase()}</span>
                            </div>
                          </div>
                        </div>
                        {showRawNames && (
                          <div className="px-3 pb-2.5">
                            <div className="text-[10px] font-mono text-[#999] dark:text-gray-500 truncate leading-relaxed" title={t.name}>{t.name}</div>
                          </div>
                        )}
                      </button>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between px-4 py-2.5 bg-gradient-to-r from-[#E8EAF6] to-transparent dark:from-[#1A237E]/20 dark:to-transparent rounded-xl border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold font-['Poppins'] text-[#3F51B5] dark:text-[#7986CB]">{selectedMod.display}</span>
              <span className="text-[11px] text-[#888] font-['Poppins']">{selectedModTests.length} test{selectedModTests.length !== 1 ? 's' : ''}</span>
              {selectedModTests.filter(t => overrides[t.name]?.disabled).length > 0 && (
                <span className="text-[11px] text-red-500 font-medium font-['Poppins']">{selectedModTests.filter(t => overrides[t.name]?.disabled).length} disabled</span>
              )}
              {selectedModTests.filter(t => (exclusionCounts[t.name] || 0) > 0).length > 0 && (
                <span className="text-[11px] text-orange-500 font-medium font-['Poppins']">{selectedModTests.filter(t => (exclusionCounts[t.name] || 0) > 0).length} hidden</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-[#888] font-['Poppins']">Toggle all</span>
              <Switch checked={!allSelectedDisabled} onCheckedChange={() => { batchUpdate(selectedModTests.map(t => ({ testName: t.name, disabled: !allSelectedDisabled }))) }}
                disabled={batchActionLoading} className="shrink-0 scale-75" />
            </div>
          </div>
          {activeSubModules.map(sub => {
            const filteredTests = sub.tests.filter(testMatches)
            if (filteredTests.length === 0) return null
            const subKey = `${selectedMod.name}::${sub.name}`
            const subDisabled = filteredTests.filter(t => overrides[t.name]?.disabled).length
            const subHidden = filteredTests.filter(t => (exclusionCounts[t.name] || 0) > 0).length
            const subAllSelected = filteredTests.every(t => visSelectedTests.has(t.name))
            const subSomeSelected = filteredTests.some(t => visSelectedTests.has(t.name))
            return (
              <div key={subKey} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-50 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-800/50">
                  <button onClick={() => setVisCollapsedSubs(prev => { const n = new Set(prev); if (n.has(subKey)) n.delete(subKey); else n.add(subKey); return n })}
                    className="p-0.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                    <ChevronRight className={`size-3.5 text-[#888] dark:text-gray-400 transition-transform ${visCollapsedSubs.has(subKey) ? '' : 'rotate-90'}`} />
                  </button>
                  <Checkbox checked={subSomeSelected && !subAllSelected ? 'indeterminate' : subAllSelected}
                    onCheckedChange={() => {
                      if (subAllSelected) {
                        setVisSelectedTests(prev => { const n = new Set(prev); filteredTests.forEach(t => n.delete(t.name)); return n })
                      } else {
                        setVisSelectedTests(prev => { const n = new Set(prev); filteredTests.forEach(t => n.add(t.name)); return n })
                      }
                    }} className="shrink-0" />
                  <span className="text-xs font-semibold font-['Poppins'] text-[#555] dark:text-gray-300">{sub.display}</span>
                  <span className="text-[11px] text-[#888] font-['Poppins']">— {filteredTests.length} test{filteredTests.length !== 1 ? 's' : ''}</span>
                  {subDisabled > 0 && <span className="text-[11px] text-red-500 font-medium font-['Poppins']">{subDisabled} off</span>}
                  {subHidden > 0 && <span className="text-[11px] text-orange-500 font-medium font-['Poppins']">{subHidden} hid</span>}
                </div>
                {!visCollapsedSubs.has(subKey) && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 p-3">
                    {filteredTests.map(t => {
                      const ov = overrides[t.name]
                      const displayName = ov?.displayName || t.display_name || t.name.split('::').pop() || t.name
                      const disabled = ov?.disabled ?? false
                      const excluded = exclusionCounts[t.name] || 0
                      const testType = t.type || 'ui'
                      const cardKey = `${selectedMod.name}::${sub.name}::${t.name}`
                      return (
                        <div key={cardKey} onClick={() => { setVisDetailTest({ testName: t.name, displayName, testType, disabled, excluded }); setVisDetailOpen(true) }}
                          className={`relative bg-white dark:bg-gray-800 rounded-xl border transition-all cursor-pointer ${
                            visSelectedTests.has(t.name)
                              ? 'border-[#3F51B5]/50 dark:border-[#7986CB]/50 shadow-sm ring-1 ring-[#3F51B5]/20 dark:ring-[#7986CB]/20'
                              : 'border-gray-100 dark:border-gray-700 hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 hover:shadow-sm'
                          } ${disabled ? 'opacity-60' : ''}`}>
                          <div className="flex items-start gap-2 px-3 pt-3 pb-2">
                            <Checkbox checked={visSelectedTests.has(t.name)} onCheckedChange={() => toggleTestSelection(t.name)}
                              onClick={e => e.stopPropagation()} className="mt-0.5 shrink-0" />
                            <div className="flex-1 min-w-0">
                              <span className="text-[13px] font-['Poppins'] leading-tight block truncate text-[#333] dark:text-gray-100">{displayName}</span>
                              <div className="flex items-center gap-1.5 mt-1.5">
                                <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                                  testType === 'api'
                                    ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                                    : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                                }`}>{testType.toUpperCase()}</span>
                                {disabled && (
                                  <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-300">Off</span>
                                )}
                                {excluded > 0 && (
                                  <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-300 flex items-center gap-1"><EyeOffIcon className="size-3" />{excluded}</span>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="px-3 pb-2.5">
                            <div className="text-[10px] font-mono text-[#999] dark:text-gray-500 truncate leading-relaxed" title={t.name}>{t.name}</div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {visSelectedTests.size > 0 && selectedVisModule && selectedMod && visActionMode === 'visibility' && (
        <div className="sticky bottom-4 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-500/70 px-4 py-3 flex items-center justify-between z-10 backdrop-blur-sm bg-white/95 dark:bg-gray-800/95">
          <span className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">{visSelectedTests.size} test{visSelectedTests.size !== 1 ? 's' : ''} selected</span>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" disabled={batchActionLoading}
              onClick={() => batchUpdate(Array.from(visSelectedTests).map(n => ({ testName: n, disabled: true })))}
              className="h-8 text-xs font-['Poppins']">
              {batchActionLoading ? <Spinner size={12} /> : <XCircle className="size-3 mr-1" />}
              Disable
            </Button>
            <Button size="sm" variant="outline" disabled={batchActionLoading}
              onClick={() => batchUpdate(Array.from(visSelectedTests).map(n => ({ testName: n, disabled: false })))}
              className="h-8 text-xs font-['Poppins']">
              {batchActionLoading ? <Spinner size={12} /> : <CheckCircle2 className="size-3 mr-1" />}
              Enable
            </Button>
            <Button size="sm" variant="outline" disabled={batchActionLoading}
              onClick={() => batchUpdate(Array.from(visSelectedTests).map(n => ({ testName: n, displayName: null, disabled: false })))}
              className="h-8 text-xs text-red-600 font-['Poppins']">
              <RotateCcw className="size-3 mr-1" />
              Reset
            </Button>
            <Button size="sm" variant="default" className="h-8 text-xs bg-[#2D3FC7] hover:bg-[#3F51B5] font-['Poppins']"
              onClick={() => {
                const first = selectedModTests.find(t => t.name === Array.from(visSelectedTests)[0])
                setVisibilityDialogTest({ testName: Array.from(visSelectedTests)[0], displayName: first ? (overrides[first.name]?.displayName || first.display_name) : '' })
                setVisibilityDialogOpen(true)
              }}>
              <EyeOff className="size-3 mr-1" />
              Hide for Users
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setVisSelectedTests(new Set())} className="h-8 text-xs font-['Poppins'] text-[#888]">
              Clear
            </Button>
          </div>
        </div>
      )}

      <TestUserVisibilityDialog
        open={visibilityDialogOpen}
        onOpenChange={setVisibilityDialogOpen}
        testName={visibilityDialogTest?.testName || ''}
        testDisplayName={visibilityDialogTest?.displayName || ''}
        onSave={(userIds) => { if (visibilityDialogTest) saveExclusions(visibilityDialogTest.testName, userIds) }}
      />

      <Dialog open={visDetailOpen} onOpenChange={setVisDetailOpen}>
        <DialogContent className="sm:max-w-[440px]">
          <DialogHeader>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center">
                {visActionMode === 'name' ? <Pencil className="size-4 text-[#3F51B5]" /> : <Eye className="size-4 text-[#3F51B5]" />}
              </div>
              <div>
                <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100 text-base">
                  {visActionMode === 'name' ? 'Rename Test' : 'Test Visibility'}
                </DialogTitle>
                <p className="text-[11px] font-['Poppins'] text-[#888] mt-0.5 font-mono truncate max-w-[360px]">{visDetailTest?.testName || ''}</p>
              </div>
            </div>
          </DialogHeader>

          {visActionMode === 'name' && visDetailTest && (
            <div className="space-y-4 py-1">
              <div>
                <label className="text-xs font-medium font-['Poppins'] text-[#555] dark:text-gray-300 mb-1.5 block">Display Name</label>
                <div className="relative">
                  <Input value={editingNameValue} onChange={e => setEditingNameValue(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') handleDetailRename(); if (e.key === 'Escape') setVisDetailOpen(false) }}
                    className="h-10 text-[13px] font-['Poppins'] pr-20" autoFocus placeholder="Enter display name..." />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2">
                    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                      visDetailTest.testType === 'api'
                        ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                        : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                    }`}>{visDetailTest.testType.toUpperCase()}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 pt-1">
                <Button onClick={handleDetailRename} className="h-9 text-xs bg-[#2D3FC7] hover:bg-[#3F51B5] font-['Poppins'] flex-1">
                  <Save className="size-3.5 mr-1.5" />Save Name
                </Button>
                <Button variant="outline" onClick={() => { saveOverride(visDetailTest.testName, { displayName: null }); setVisDetailOpen(false) }}
                  className="h-9 text-xs font-['Poppins'] text-red-600 flex-1">
                  <RotateCcw className="size-3 mr-1.5" />Revert
                </Button>
              </div>
            </div>
          )}

          {visActionMode === 'visibility' && visDetailTest && (
            <div className="space-y-3 py-1">
              <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className={`w-2 h-2 rounded-full ${visDetailTest.disabled ? 'bg-red-400' : 'bg-green-400'}`} />
                  <span className="text-sm font-['Poppins'] text-[#333] dark:text-gray-100">Test Status</span>
                </div>
                <div className="flex items-center gap-2.5">
                  <Switch checked={!visDetailTest.disabled}
                    onCheckedChange={v => { saveOverride(visDetailTest.testName, { disabled: !v }); setVisDetailTest(prev => prev ? { ...prev, disabled: !v } : null) }} />
                  <span className={`text-xs font-medium font-['Poppins'] ${visDetailTest.disabled ? 'text-red-500' : 'text-green-600'}`}>
                    {visDetailTest.disabled ? 'Disabled' : 'Enabled'}
                  </span>
                </div>
              </div>

              <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <EyeOff className="size-3.5 text-[#888]" />
                    <span className="text-xs font-['Poppins'] text-[#555] dark:text-gray-300">Hidden from users</span>
                  </div>
                  <span className="text-xs font-semibold font-['Poppins'] text-orange-600">{visDetailTest.excluded} user{visDetailTest.excluded !== 1 ? 's' : ''}</span>
                </div>
                <Button variant="outline" onClick={() => { setVisibilityDialogTest({ testName: visDetailTest.testName, displayName: visDetailTest.displayName }); setVisibilityDialogOpen(true) }}
                  className="w-full h-8 text-xs font-['Poppins'] justify-center">
                  <EyeOff className="size-3 mr-1.5" />
                  {visDetailTest.excluded > 0 ? 'Manage Hidden Users' : 'Hide from Users'}
                </Button>
              </div>

              <Button variant="outline" onClick={() => { saveOverride(visDetailTest.testName, { displayName: null, disabled: false }); setVisDetailOpen(false) }}
                className="w-full h-9 text-xs font-['Poppins'] text-red-600 justify-center">
                <RotateCcw className="size-3.5 mr-1.5" />Revert to Defaults
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
