'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Calendar, Clock, Trash2, ToggleLeft, ToggleRight, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import type { ScheduledRun, SidebarModule } from '@/types/dashboard';
import { getScheduledRuns, addScheduledRun, deleteScheduledRun, updateScheduledRun, addNotification } from '@/lib/bug-reports';

interface ScheduleRunsTabProps {
  userName: string;
  sidebarModules: SidebarModule[];
}

export function ScheduleRunsTab({ userName, sidebarModules }: ScheduleRunsTabProps) {
  const [runs, setRuns] = useState<ScheduledRun[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [moduleId, setModuleId] = useState('tax-rate');
  const [frequency, setFrequency] = useState<'one-time' | 'daily' | 'weekly'>('one-time');
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [weeklyDay, setWeeklyDay] = useState('1');
  const [testSelection, setTestSelection] = useState<'all' | 'priority' | 'selected'>('all');
  const [countdown, setCountdown] = useState<Record<string, string>>({});

  // Load runs
  useEffect(() => {
    const loadRuns = async () => setRuns(await getScheduledRuns());
    loadRuns();
  }, []);

  // Countdown timer
  useEffect(() => {
    const tick = async () => {
      const now = new Date();
      const newCountdown: Record<string, string> = {};
      for (const run of runs) {
        if (!run.enabled) continue;
        const target = new Date(run.scheduledTime);
        const diff = target.getTime() - now.getTime();
        if (diff <= 0) {
          newCountdown[run.id] = 'Due now!';
          if (diff > -2000) {
            await updateScheduledRun(run.id, { lastRunAt: new Date().toISOString(), enabled: false });
            await addNotification({ type: 'run_complete', title: 'Scheduled run completed', message: `Scheduled run for ${run.moduleName} completed (mock)` });
            setRuns(await getScheduledRuns());
            toast.success(`Scheduled run for ${run.moduleName} completed!`);
          }
        } else {
          const h = Math.floor(diff / 3600000);
          const m = Math.floor((diff % 3600000) / 60000);
          const s = Math.floor((diff % 60000) / 1000);
          newCountdown[run.id] = h > 0 ? `${h}h ${m}m ${s}s` : m > 0 ? `${m}m ${s}s` : `${s}s`;
        }
      }
      setCountdown(newCountdown);
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [runs]);

  const handleSave = useCallback(async () => {
    let scheduledTimeStr = '';
    if (frequency === 'one-time' && scheduledDate && scheduledTime) {
      scheduledTimeStr = new Date(`${scheduledDate}T${scheduledTime}`).toISOString();
    } else if (frequency === 'daily' && scheduledTime) {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      scheduledTimeStr = new Date(`${tomorrow.toISOString().split('T')[0]}T${scheduledTime}`).toISOString();
    } else if (frequency === 'weekly' && scheduledTime) {
      const now = new Date();
      const dayNum = parseInt(weeklyDay);
      const daysUntil = ((dayNum - now.getDay() + 7) % 7) || 7;
      const target = new Date(now);
      target.setDate(target.getDate() + daysUntil);
      scheduledTimeStr = new Date(`${target.toISOString().split('T')[0]}T${scheduledTime}`).toISOString();
    } else {
      scheduledTimeStr = new Date(Date.now() + 10000).toISOString();
    }

    if (!scheduledTimeStr) return;

    const mod = sidebarModules.find((m) => m.id === moduleId) || sidebarModules.find((m) => m.children?.some((c) => c.id === moduleId));
    const modName = mod?.label || moduleId;

    await addScheduledRun({
      moduleId,
      moduleName: modName,
      frequency,
      scheduledTime: scheduledTimeStr,
      testSelection,
      enabled: true,
      createdBy: userName,
    });
    setRuns(await getScheduledRuns());
    setShowForm(false);
    toast.success(`Scheduled run created for ${modName}`);
  }, [moduleId, frequency, scheduledDate, scheduledTime, weeklyDay, testSelection, userName, sidebarModules]);

  const handleDelete = useCallback(async (id: string) => {
    await deleteScheduledRun(id);
    setRuns(await getScheduledRuns());
    toast.success('Schedule deleted');
  }, []);

  const handleToggle = useCallback(async (id: string, enabled: boolean) => {
    await updateScheduledRun(id, { enabled: !enabled });
    setRuns(await getScheduledRuns());
  }, []);

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  if (showForm) {
    return (
      <div className="p-4 space-y-4">
        <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">Schedule New Run</h3>
        <div className="space-y-3">
          <div>
            <Label className="text-[13px]">Module</Label>
            <Select value={moduleId} onValueChange={setModuleId}>
              <SelectTrigger className="text-[13px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {sidebarModules.map((mod) => (
                  <SelectItem key={mod.id} value={mod.id}>{mod.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-[13px]">Frequency</Label>
            <Select value={frequency} onValueChange={(v) => setFrequency(v as typeof frequency)}>
              <SelectTrigger className="text-[13px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="one-time">One-time</SelectItem>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {frequency === 'one-time' && (
            <>
              <div>
                <Label className="text-[13px]">Date</Label>
                <Input type="date" value={scheduledDate} onChange={(e) => setScheduledDate(e.target.value)} className="text-[13px]" />
              </div>
              <div>
                <Label className="text-[13px]">Time</Label>
                <Input type="time" value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)} className="text-[13px]" />
              </div>
            </>
          )}
          {frequency === 'daily' && (
            <div>
              <Label className="text-[13px]">Time</Label>
              <Input type="time" value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)} className="text-[13px]" />
            </div>
          )}
          {frequency === 'weekly' && (
            <>
              <div>
                <Label className="text-[13px]">Day</Label>
                <Select value={weeklyDay} onValueChange={setWeeklyDay}>
                  <SelectTrigger className="text-[13px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">Sunday</SelectItem>
                    <SelectItem value="1">Monday</SelectItem>
                    <SelectItem value="2">Tuesday</SelectItem>
                    <SelectItem value="3">Wednesday</SelectItem>
                    <SelectItem value="4">Thursday</SelectItem>
                    <SelectItem value="5">Friday</SelectItem>
                    <SelectItem value="6">Saturday</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-[13px]">Time</Label>
                <Input type="time" value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)} className="text-[13px]" />
              </div>
            </>
          )}
          <div>
            <Label className="text-[13px]">Test Selection</Label>
            <Select value={testSelection} onValueChange={(v) => setTestSelection(v as typeof testSelection)}>
              <SelectTrigger className="text-[13px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tests</SelectItem>
                <SelectItem value="priority">Priority Tests Only</SelectItem>
                <SelectItem value="selected">Selected Tests</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex gap-2 pt-2">
            <Button onClick={handleSave} className="flex-1 bg-green-600 hover:bg-green-700 text-white cursor-pointer">
              Save Schedule
            </Button>
            <Button onClick={() => setShowForm(false)} variant="outline" className="flex-1 cursor-pointer">
              Cancel
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">Scheduled Runs</h3>
        <Button onClick={() => setShowForm(true)} className="bg-green-600 hover:bg-green-700 text-white h-8 text-[13px] gap-1.5 cursor-pointer">
          <Plus className="size-3.5" />
          New Schedule
        </Button>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-3">
          {runs.length === 0 ? (
            <div className="text-center text-gray-400 text-[13px] py-8">No scheduled runs yet</div>
          ) : (
            runs.map((run) => (
              <div key={run.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 bg-gray-50/50 dark:bg-gray-800/30">
                <div className="flex items-start gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Calendar className="size-3.5 text-gray-400" />
                      <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200">{run.moduleName}</span>
                    </div>
                    <div className="mt-1 text-[11px] text-gray-500 dark:text-gray-400">
                      {run.frequency} • {formatDate(run.scheduledTime)} • Created by {run.createdBy}
                    </div>
                    {countdown[run.id] && (
                      <div className="mt-1 flex items-center gap-1 text-[11px] text-orange-600 dark:text-orange-400">
                        <Clock className="size-3" />
                        {countdown[run.id]}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="size-7 cursor-pointer"
                      onClick={() => handleToggle(run.id, run.enabled)}
                    >
                      {run.enabled ? <ToggleRight className="size-5 text-green-600" /> : <ToggleLeft className="size-5 text-gray-400" />}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="size-7 text-red-500 hover:text-red-700 cursor-pointer"
                      onClick={() => handleDelete(run.id)}
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
