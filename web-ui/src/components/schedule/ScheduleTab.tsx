'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Clock, Plus, Trash2, Calendar, Bell } from 'lucide-react'

interface SidebarModule {
  id: string
  label: string
  children?: SidebarModule[]
}

interface ScheduledRun {
  id: number
  moduleName: string
  moduleId: string
  schedule: string
  frequency: 'daily' | 'weekly' | 'monthly'
  enabled: boolean
  lastRun?: string
  nextRun: string
  recipients: string[]
}

interface ScheduleTabProps {
  userName: string
  sidebarModules: SidebarModule[]
}

export default React.memo(function ScheduleTab({ userName, sidebarModules }: ScheduleTabProps) {
  const [scheduledRuns, setScheduledRuns] = useState<ScheduledRun[]>([])
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedModule, setSelectedModule] = useState('')
  const [frequency, setFrequency] = useState<'daily' | 'weekly' | 'monthly'>('daily')
  const [time, setTime] = useState('09:00')
  const [recipients, setRecipients] = useState<string[]>([userName])

  const flattenModules = (modules: SidebarModule[]): { id: string; label: string }[] => {
    let result: { id: string; label: string }[] = []
    for (const mod of modules) {
      result.push({ id: mod.id, label: mod.label })
      if (mod.children) {
        result = result.concat(flattenModules(mod.children))
      }
    }
    return result
  }

  const allModules = flattenModules(sidebarModules)

  const handleAddSchedule = () => {
    if (!selectedModule) return

    const newRun: ScheduledRun = {
      id: Date.now(),
      moduleName: allModules.find((m) => m.id === selectedModule)?.label || selectedModule,
      moduleId: selectedModule,
      schedule: time,
      frequency,
      enabled: true,
      nextRun: 'Tomorrow',
      recipients,
    }

    setScheduledRuns([...scheduledRuns, newRun])
    setIsDialogOpen(false)
    setSelectedModule('')
    setFrequency('daily')
    setTime('09:00')
  }

  const handleDeleteSchedule = (id: number) => {
    setScheduledRuns(scheduledRuns.filter((run) => run.id !== id))
  }

  const handleToggleEnabled = (id: number) => {
    setScheduledRuns(
      scheduledRuns.map((run) =>
        run.id === id ? { ...run, enabled: !run.enabled } : run
      )
    )
  }

  return (
    <div className="flex flex-col h-full overflow-auto">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">
              Scheduled Test Runs
            </h3>
            <p className="text-[12px] text-gray-500 dark:text-gray-400 mt-0.5">
              Automate your test execution on a recurring schedule
            </p>
          </div>
          <Button
            onClick={() => setIsDialogOpen(true)}
            className="h-8 cursor-pointer"
          >
            <Plus className="size-4 mr-1" />
            Add Schedule
          </Button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 border border-blue-100 dark:border-blue-800/50">
            <div className="flex items-center gap-2 mb-1">
              <Calendar className="size-4 text-blue-600 dark:text-blue-400" />
              <span className="text-[12px] text-blue-600 dark:text-blue-400 font-medium">
                Active Schedules
              </span>
            </div>
            <div className="text-xl font-bold text-blue-700 dark:text-blue-400">
              {scheduledRuns.filter((r) => r.enabled).length}
            </div>
          </div>
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 border border-purple-100 dark:border-purple-800/50">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="size-4 text-purple-600 dark:text-purple-400" />
              <span className="text-[12px] text-purple-600 dark:text-purple-400 font-medium">
                Next Run
              </span>
            </div>
            <div className="text-xl font-bold text-purple-700 dark:text-purple-400">
              {scheduledRuns.filter((r) => r.enabled)[0]?.nextRun || 'None'}
            </div>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 border border-green-100 dark:border-green-800/50">
            <div className="flex items-center gap-2 mb-1">
              <Bell className="size-4 text-green-600 dark:text-green-400" />
              <span className="text-[12px] text-green-600 dark:text-green-400 font-medium">
                Notifications
              </span>
            </div>
            <div className="text-xl font-bold text-green-700 dark:text-green-400">
              {recipients.length} Recipients
            </div>
          </div>
        </div>
      </div>

      {/* Schedule List */}
      <div className="px-4 pb-4 shrink-0">
        <ScrollArea className="h-[400px] border border-gray-200 dark:border-gray-700 rounded-md">
          {scheduledRuns.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-12">
              <Calendar className="size-12 text-gray-300 dark:text-gray-600 mb-3" />
              <p className="text-[14px] text-gray-500 dark:text-gray-400 font-medium">
                No scheduled runs yet
              </p>
              <p className="text-[12px] text-gray-400 dark:text-gray-500 mt-1">
                Click "Add Schedule" to create your first automated test run
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Module</TableHead>
                  <TableHead>Frequency</TableHead>
                  <TableHead>Schedule</TableHead>
                  <TableHead>Next Run</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {scheduledRuns.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell className="font-medium text-[13px]">
                      {run.moduleName}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className="text-[11px] capitalize"
                      >
                        {run.frequency}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-[13px] text-gray-500">
                      {run.schedule}
                    </TableCell>
                    <TableCell className="text-[13px] text-gray-500">
                      {run.nextRun}
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={
                          run.enabled
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                        }
                      >
                        {run.enabled ? 'Active' : 'Paused'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 cursor-pointer"
                          onClick={() => handleToggleEnabled(run.id)}
                        >
                          {run.enabled ? (
                            <Clock className="size-3.5 text-green-600" />
                          ) : (
                            <Clock className="size-3.5 text-gray-400" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 cursor-pointer"
                          onClick={() => handleDeleteSchedule(run.id)}
                        >
                          <Trash2 className="size-3.5 text-red-500" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </ScrollArea>
      </div>

      {/* Add Schedule Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Schedule Test Run</DialogTitle>
            <DialogDescription>
              Set up automated test execution on a recurring schedule.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="module">Select Module</Label>
              <Select value={selectedModule} onValueChange={setSelectedModule}>
                <SelectTrigger id="module">
                  <SelectValue placeholder="Choose a module to schedule" />
                </SelectTrigger>
                <SelectContent>
                  {allModules.map((mod) => (
                    <SelectItem key={mod.id} value={mod.id}>
                      {mod.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="frequency">Frequency</Label>
              <Select value={frequency} onValueChange={(v) => setFrequency(v as any)}>
                <SelectTrigger id="frequency">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="time">Time</Label>
              <Input
                id="time"
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Notification Recipients</Label>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="notify-self"
                  checked={recipients.includes(userName)}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      setRecipients([...recipients, userName])
                    } else {
                      setRecipients(recipients.filter((r) => r !== userName))
                    }
                  }}
                />
                <Label htmlFor="notify-self" className="text-[13px]">
                  Notify me ({userName})
                </Label>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsDialogOpen(false)}
              className="cursor-pointer"
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddSchedule}
              disabled={!selectedModule}
              className="cursor-pointer"
            >
              Create Schedule
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
