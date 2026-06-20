'use client'

import { Badge } from '@/components/ui/badge'
import { Loader2 } from 'lucide-react'
import {
  Activity, Database, HardDrive, Zap, Timer, FolderTree,
} from 'lucide-react'
import { useSystemHealth } from '@/hooks/admin/useSystemHealth'

export function SystemHealthSection({
  modulesLoaded,
}: {
  modulesLoaded: boolean
}) {
  const { systemHealthData, healthLoaded, appStartTime } = useSystemHealth()
  const uptimeSeconds = Math.floor((Date.now() - appStartTime) / 1000)
  const formatUptime = (s: number) => {
    const d = Math.floor(s / 86400); const h = Math.floor((s % 86400) / 3600); const m = Math.floor((s % 3600) / 60)
    return d > 0 ? `${d}d ${h}h ${m}m` : h > 0 ? `${h}h ${m}m` : `${m}m`
  }

  const dbStats = (systemHealthData?.dbStats || {}) as Record<string, number>
  const dbFileSize = (systemHealthData?.dbFileSize || '—') as string
  const lastRun = (systemHealthData?.lastRun || null) as { id: string; moduleName: string; status: string; completedAt: string } | null
  const activeModules = (systemHealthData?.activeModules || 0) as number
  const totalTestCases = (systemHealthData?.totalTestCases || 0) as number
  const serverUptime = (systemHealthData?.serverUptime || 0) as number

  const statusColor = (ok: boolean, warn = false) =>
    ok ? 'bg-green-500' : warn ? 'bg-yellow-500' : 'bg-red-500'

  const apiOk = modulesLoaded
  const dbOk = dbStats.users !== undefined
  const lastRunOk = lastRun?.status === 'completed'

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">System Health</h2>
      {!healthLoaded ? (
        <div className="flex justify-center py-12"><Loader2 className="size-6 animate-spin text-[#3F51B5]" /></div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#E8EAF6] dark:bg-[#1A237E]/30">
                  <Activity className="size-5 text-[#3F51B5] dark:text-[#7986CB]" />
                </div>
                <div>
                  <p className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">API Connectivity</p>
                  <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Backend API status</p>
                </div>
                <span className={`ml-auto w-3 h-3 rounded-full ${statusColor(apiOk)}`} />
              </div>
              <p className="text-xs font-['Manrope'] text-[#545454] dark:text-gray-300">
                {apiOk ? 'API is reachable and responding' : 'API connection failed'}
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#E0F2F1] dark:bg-[#004D40]/40">
                  <Database className="size-5 text-[#00897B] dark:text-[#4DB6AC]" />
                </div>
                <div>
                  <p className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Database</p>
                  <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">SQLite record counts</p>
                </div>
                <span className={`ml-auto w-3 h-3 rounded-full ${statusColor(dbOk)}`} />
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs font-['Manrope']">
                <span className="text-[#888] dark:text-gray-400">Users: <strong className="text-[#333] dark:text-gray-100">{dbStats.users ?? '—'}</strong></span>
                <span className="text-[#888] dark:text-gray-400">Runs: <strong className="text-[#333] dark:text-gray-100">{dbStats.runs ?? '—'}</strong></span>
                <span className="text-[#888] dark:text-gray-400">Bugs: <strong className="text-[#333] dark:text-gray-100">{dbStats.bugs ?? '—'}</strong></span>
                <span className="text-[#888] dark:text-gray-400">Modules: <strong className="text-[#333] dark:text-gray-100">{dbStats.modules ?? '—'}</strong></span>
                <span className="text-[#888] dark:text-gray-400">Envs: <strong className="text-[#333] dark:text-gray-100">{dbStats.environments ?? '—'}</strong></span>
                <span className="text-[#888] dark:text-gray-400">Notifs: <strong className="text-[#333] dark:text-gray-100">{dbStats.notifications ?? '—'}</strong></span>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#FFF3E0] dark:bg-[#BF360C]/40">
                  <HardDrive className="size-5 text-[#F57C00] dark:text-[#FFB74D]" />
                </div>
                <div>
                  <p className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Disk Usage</p>
                  <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Database file size</p>
                </div>
                <span className={`ml-auto w-3 h-3 rounded-full ${statusColor(true)}`} />
              </div>
              <p className="text-2xl font-bold font-['Poppins'] text-[#333] dark:text-gray-100">{dbFileSize}</p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#F3E5F5] dark:bg-[#4A148C]/40">
                  <Zap className="size-5 text-[#7B1FA2] dark:text-[#CE93D8]" />
                </div>
                <div>
                  <p className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Last Run</p>
                  <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Most recent test run</p>
                </div>
                <span className={`ml-auto w-3 h-3 rounded-full ${statusColor(lastRunOk, !lastRun && !lastRunOk)}`} />
              </div>
              {lastRun ? (
                <div className="space-y-1">
                  <p className="text-xs font-medium text-[#333] dark:text-gray-100 font-['Manrope']">{lastRun.moduleName}</p>
                  <Badge className={`text-[10px] border-0 ${lastRun.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : lastRun.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300'}`}>{lastRun.status}</Badge>
                  <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">{lastRun.completedAt ? new Date(lastRun.completedAt).toLocaleString() : 'In progress'}</p>
                </div>
              ) : (
                <p className="text-xs text-[#888] dark:text-gray-400 font-['Manrope']">No runs yet</p>
              )}
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#E8F5E9] dark:bg-[#1B5E20]/40">
                  <Timer className="size-5 text-[#2E7D32] dark:text-[#66BB6A]" />
                </div>
                <div>
                  <p className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Uptime</p>
                  <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Since page loaded</p>
                </div>
                <span className="ml-auto w-3 h-3 rounded-full bg-green-500" />
              </div>
              <p className="text-2xl font-bold font-['Poppins'] text-[#333] dark:text-gray-100">{formatUptime(uptimeSeconds)}</p>
              <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Server: {formatUptime(serverUptime)}</p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#E8EAF6] dark:bg-[#1A237E]/30">
                  <FolderTree className="size-5 text-[#3F51B5] dark:text-[#7986CB]" />
                </div>
                <div>
                  <p className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Modules & Tests</p>
                  <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Active counts</p>
                </div>
                <span className={`ml-auto w-3 h-3 rounded-full ${statusColor(activeModules > 0)}`} />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-['Manrope']">
                  <span className="text-[#888] dark:text-gray-400">Active Modules</span>
                  <strong className="text-[#333] dark:text-gray-100">{activeModules}</strong>
                </div>
                <div className="flex items-center justify-between text-xs font-['Manrope']">
                  <span className="text-[#888] dark:text-gray-400">Total Test Cases</span>
                  <strong className="text-[#333] dark:text-gray-100">{totalTestCases}</strong>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
