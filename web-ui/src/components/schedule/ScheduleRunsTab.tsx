'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { Plus, CalendarClock, Timer } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { toast } from 'sonner'
import type { SidebarModule } from '@/components/sidebar/SidebarModuleItem'
import {
  getScheduledRuns,
  addScheduledRun,
  deleteScheduledRun,
  updateScheduledRun,
  addNotification,
  type ScheduledRun,
} from '@/lib/bug-reports'

export function ScheduleRunsTab({ userName, sidebarModules }: { userName: string; sidebarModules: SidebarModule[] }) {
  const [runs, setRuns] = useState<ScheduledRun[]>([])
  const [showForm, setShowForm] = useState(false)
  const [moduleId, setModuleId] = useState('tax-rate')
  const [frequency, setFrequency] = useState<'one-time' | 'daily' | 'weekly'>('one-time')
  const [scheduledDate, setScheduledDate] = useState('')
  const [scheduledTime, setScheduledTime] = useState('')
  const [weeklyDay, setWeeklyDay] = useState('1')
  const [testSelection, setTestSelection] = useState<'all' | 'priority' | 'selected'>('all')
  const [countdown, setCountdown] = useState<Record<string, string>>({})

  // Load runs
  useEffect(() => {
    const loadRuns = async () => setRuns(await getScheduledRuns())
    loadRuns()
  }, [])

  // Countdown timer
  useEffect(() => {
    const tick = async () => {
      const now = new Date()
      const newCountdown: Record<string, string> = {}
      for (const run of runs) {
        if (!run.enabled) continue
        const target = new Date(run.scheduledTime)
        const diff = target.getTime() - now.getTime()
        if (diff <= 0) {
          newCountdown[run.id] = 'Due now!'
          // Trigger mock execution for demo
          if (diff > -2000) {
            await updateScheduledRun(run.id, { lastRunAt: new Date().toISOString(), enabled: false })
            await addNotification({ type: 'run_complete', title: 'Scheduled run completed', message: `Scheduled run for ${run.moduleName} completed (mock)` })
            setRuns(await getScheduledRuns())
            toast.success(`Scheduled run for ${run.moduleName} completed!`)
          }
        } else {
          const h = Math.floor(diff / 3600000)
          const m = Math.floor((diff % 3600000) / 60000)
          const s = Math.floor((diff % 60000) / 1000)
          newCountdown[run.id] = h > 0 ? `${h}h ${m}m ${s}s` : m > 0 ? `${m}m ${s}s` : `${s}s`
        }
      }
      setCountdown(newCountdown)
    }
    tick()
    const interval = setInterval(tick, 1000)
    return () => clearInterval(interval)
  }, [runs])

  const handleAddRun = useCallback(async () => {
    let scheduledTimeStr = ''
    if (frequency === 'one-time' && scheduledDate && scheduledTime) {
      scheduledTimeStr = new Date(`${scheduledDate}T${scheduledTime}`).toISOString()
    } else if (frequency === 'daily' && scheduledTime) {
      const tomorrow = new Date()
      tomorrow.setDate(tomorrow.getDate() + 1)
      scheduledTimeStr = new Date(`${tomorrow.toISOString().split('T')[0]}T${scheduledTime}`).toISOString()
    } else if (frequency === 'weekly' && scheduledTime) {
      const now = new Date()
      const dayNum = parseInt(weeklyDay)
      const daysUntil = ((dayNum - now.getDay() + 7) % 7) || 7
      const target = new Date(now)
      target.setDate(target.getDate() + daysUntil)
      scheduledTimeStr = new Date(`${target.toISOString().split('T')[0]}T${scheduledTime}`).toISOString()
    } else {
      // Quick test: 10 seconds from now
      scheduledTimeStr = new Date(Date.now() + 10000).toISOString()
    }

    if (!scheduledTimeStr) return

    const mod = sidebarModules.find((m) => m.id === moduleId) || sidebarModules.find((m) => m.children?.some((c) => c.id === moduleId))
    const modName = mod?.label || moduleId

    await addScheduledRun({
      moduleId,
      moduleName: modName,
      frequency,
      scheduledTime: scheduledTimeStr,
      testSelection,
      enabled: true,
      createdBy: userName,
    })
    setRuns(await getScheduledRuns())
    setShowForm(false)
    toast.success(`Scheduled run created for ${modName}`)
  }, [moduleId, frequency, scheduledDate, scheduledTime, weeklyDay, testSelection, userName, sidebarModules])

  const handleDelete = useCallback(async (id: string) => {
    await deleteScheduledRun(id)
    setRuns(await getScheduledRuns())
    toast.success('Schedule deleted')
  }, [])

  const handleToggle = useCallback(async (id: string, enabled: boolean) => {
    await updateScheduledRun(id, { enabled: !enabled })
    setRuns(await getScheduledRuns())
  }, [])

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    } catch { return iso }
  }

  const allModuleOptions = useMemo(() => {
    const opts: { id: string; label: string }[] = []
    for (const mod of sidebarModules) {
      if (mod.children) {
        for (const child of mod.children) {
          opts.push({ id: child.id, label: `${mod.label} > ${child.label}` })
        }
      } else {
        opts.push({ id: mod.id, label: mod.label })
      }
    }
    return opts
  }, [sidebarModules])

  return (
    <div className="flex flex-col h-full min-h-0">
      <ScrollArea className="flex-1 min-h-0">
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100 flex items-center gap-2">
              <CalendarClock className="size-4 text-green-600" />
              Run Scheduling
            </h3>
            <p className="text-[12px] text-gray-500 dark:text-gray-400 mt-0.5">Schedule future test runs</p>
          </div>
          <Button
            size="sm"
            onClick={() => setShowForm(!showForm)}
            className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white text-[12px] cursor-pointer rounded-lg font-semibold"
          >
            <Plus className="size-3.5 mr-1" /> New Schedule
          </Button>
        </div>

        {/* Create Form */}
        {showForm && (
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-[12px]">Module</Label>
                <Select value={moduleId} onValueChange={setModuleId}>
                  <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {allModuleOptions.map((opt) => (
                      <SelectItem key={opt.id} value={opt.id}>{opt.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-[12px]">Frequency</Label>
                <Select value={frequency} onValueChange={(v) => setFrequency(v as 'one-time' | 'daily' | 'weekly')}>
                  <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="one-time">One-time</SelectItem>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {frequency === 'one-time' && (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-[12px]">Date</Label>
                  <Input type="date" value={scheduledDate} onChange={(e) => setScheduledDate(e.target.value)} className="h-9 text-[12px]" />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-[12px]">Time</Label>
                  <Input type="time" value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)} className="h-9 text-[12px]" />
                </div>
              </div>
            )}

            {frequency === 'daily' && (
              <div className="space-y-1.5">
                <Label className="text-[12px]">Time</Label>
                <Input type="time" value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)} className="h-9 text-[12px] w-48" />
              </div>
            )}

            {frequency === 'weekly' && (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-[12px]">Day of Week</Label>
                  <Select value={weeklyDay} onValueChange={setWeeklyDay}>
                    <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">Monday</SelectItem>
                      <SelectItem value="2">Tuesday</SelectItem>
                      <SelectItem value="3">Wednesday</SelectItem>
                      <SelectItem value="4">Thursday</SelectItem>
                      <SelectItem value="5">Friday</SelectItem>
                      <SelectItem value="6">Saturday</SelectItem>
                      <SelectItem value="0">Sunday</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-[12px]">Time</Label>
                  <Input type="time" value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)} className="h-9 text-[12px]" />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <Label className="text-[12px]">Tests to Run</Label>
              <Select value={testSelection} onValueChange={(v) => setTestSelection(v as 'all' | 'priority' | 'selected')}>
                <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Tests</SelectItem>
                  <SelectItem value="priority">Priority Only (Smoke + Regression)</SelectItem>
                  <SelectItem value="selected">Selected Tests</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <Button size="sm" onClick={handleAddRun} className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white text-[12px] cursor-pointer rounded-lg font-semibold">
                <CalendarClock className="size-3.5 mr-1" /> Create Schedule
              </Button>
              <Button size="sm" onClick={() => { setShowForm(false); setFrequency('one-time'); setScheduledDate(''); setScheduledTime('') }} className="text-[12px] cursor-pointer bg-transparent text-[#F44336] hover:bg-red-50">
                Cancel
              </Button>
              <span className="text-[11px] text-gray-400 ml-auto">
                💡 Leave date/time empty for a 10-second quick test
              </span>
            </div>
          </div>
        )}

        {/* Upcoming Runs */}
        <div>
          <h4 className="text-[13px] font-semibold text-gray-700 dark:text-gray-200 mb-2">Upcoming Scheduled Runs</h4>
          {runs.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 text-center">
              <CalendarClock className="size-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
              <p className="text-[13px] text-gray-500 dark:text-gray-400">No scheduled runs</p>
              <p className="text-[11px] text-gray-400 mt-1">Create a schedule to automate test runs</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {runs.map((run) => (
                <div key={run.id} className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 flex items-center gap-3 ${!run.enabled ? 'opacity-50' : ''}`}>
                  <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${run.enabled ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                  <div className="flex-1 min-w-0">
                    <div className="text-[12px] font-medium text-gray-800 dark:text-gray-100 truncate">{run.moduleName}</div>
                    <div className="text-[11px] text-gray-500 dark:text-gray-400 flex items-center gap-2 mt-0.5">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        run.frequency === 'one-time' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                          : run.frequency === 'daily' ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400'
                            : 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400'
                      }`}>{run.frequency}</span>
                      <span>{formatDate(run.scheduledTime)}</span>
                      <span>•</span>
                      <span>{run.testSelection} tests</span>
                    </div>
                  </div>
                  {run.enabled && countdown[run.id] && (
                    <div className="text-[11px] font-mono text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded flex items-center gap-1">
                      <Timer className="size-3" />
                      {countdown[run.id]}
                    </div>
                  )}
                  {run.lastRunAt && (
                    <span className="text-[10px] text-gray-400">Last: {formatDate(run.lastRunAt)}</span>
                  )}
                  <button onClick={() => handleToggle(run.id, run.enabled)} className="text-[11px] text-gray-500 hover:text-gray-700 cursor-pointer px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                    {run.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button onClick={() => handleDelete(run.id)} className="text-[11px] text-red-500 hover:text-red-700 cursor-pointer px-2 py-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20">
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      </ScrollArea>
    </div>
  )
}
