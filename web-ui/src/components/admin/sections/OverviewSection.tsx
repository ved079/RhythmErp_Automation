'use client'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { useTheme } from 'next-themes'
import {
  ClipboardList, FolderTree, Globe, UsersIcon, Settings, Loader2, XCircle,
} from 'lucide-react'

interface OverviewStats {
  activeTests: number; totalModules: number; activeEnvs: number; activeUsers: number
  passRate: number; failedTests: { id: string; description: string; moduleName: string }[]
}

interface Environment {
  id: string; name: string; baseUrl: string; browser: string
  status: 'active' | 'inactive'; lastUsed?: string; color: string
}

interface AuditEntry {
  id: string; userId: string; userName: string; action: string
  targetType: string; targetId: string; targetLabel: string
  details: string; createdAt: string
}

export function OverviewSection({
  stats, tests, testsLoaded, environments, envLoaded, auditLog,
  hiddenWidgets, widgetDialogOpen, setWidgetDialogOpen, toggleWidgetVisibility,
}: {
  stats: OverviewStats
  tests: { lastResult?: string }[]
  testsLoaded: boolean
  environments: Environment[]
  envLoaded: boolean
  auditLog: AuditEntry[]
  hiddenWidgets: Set<string>
  widgetDialogOpen: boolean
  setWidgetDialogOpen: (v: boolean) => void
  toggleWidgetVisibility: (id: string) => void
}) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const passCount = tests.filter(t => t.lastResult === 'passed').length
  const failCount = tests.filter(t => t.lastResult === 'failed').length
  const notRunCount = tests.filter(t => t.lastResult === 'not-run' || !t.lastResult).length
  const total = passCount + failCount + notRunCount || 1
  const passPct = Math.round((passCount / total) * 100)
  const failPct = Math.round((failCount / total) * 100)

  const statCards = [
    { label: 'Active Tests', value: stats.activeTests, icon: ClipboardList, color: '#4CAF50', bg: '#E8F5E9' },
    { label: 'Modules', value: stats.totalModules, icon: FolderTree, color: '#3F51B5', bg: '#DFE9FB' },
    { label: 'Environments', value: stats.activeEnvs, icon: Globe, color: '#FF9800', bg: '#FFF3E0' },
    { label: 'Users', value: stats.activeUsers, icon: UsersIcon, color: '#F44336', bg: '#FFEBEE' },
  ]

  const allWidgets = [
    { id: 'stat-cards', label: 'Stat Cards' },
    { id: 'pass-rate', label: 'Pass Rate' },
    { id: 'environments', label: 'Active Environments' },
    { id: 'recent-failures', label: 'Recent Failures' },
    { id: 'recent-activity', label: 'Recent Activity' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Dashboard Overview</h2>
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => setWidgetDialogOpen(true)} title="Customize widgets">
          <Settings className="size-4 text-[#888]" />
        </Button>
      </div>
      {!hiddenWidgets.has('stat-cards') && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map(c => (
            <div key={c.label} className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700 flex items-center gap-4">
              <div className="w-11 h-11 rounded-xl flex items-center justify-center" style={{ background: c.bg }}>
                <c.icon className="size-5" style={{ color: c.color }} />
              </div>
              <div>
                <p className="text-2xl font-bold font-['Poppins'] text-[#333] dark:text-gray-100">{c.value}</p>
                <p className="text-xs text-[#888] dark:text-gray-400 font-['Manrope']">{c.label}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {!hiddenWidgets.has('pass-rate') && (
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
            <h3 className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 mb-4">Pass Rate</h3>
            <div className="flex items-center justify-center">
              <svg width="160" height="160" viewBox="0 0 160 160">
                <circle cx="80" cy="80" r="60" fill="none" stroke={isDark ? '#374151' : '#E5E7EB'} strokeWidth="18" />
                <circle cx="80" cy="80" r="60" fill="none" stroke="#4CAF50" strokeWidth="18"
                  strokeDasharray={`${passPct * 3.77} ${377 - passPct * 3.77}`} strokeDashoffset="94.25"
                  strokeLinecap="round" className="transition-all duration-700" />
                <circle cx="80" cy="80" r="60" fill="none" stroke="#F44336" strokeWidth="18"
                  strokeDasharray={`${failPct * 3.77} ${377 - failPct * 3.77}`}
                  strokeDashoffset={94.25 - passPct * 3.77} strokeLinecap="round" className="transition-all duration-700" />
                <text x="80" y="72" textAnchor="middle" className="fill-[#333] dark:fill-gray-100 text-2xl font-bold font-['Poppins']">{stats.passRate}%</text>
                <text x="80" y="92" textAnchor="middle" className="fill-[#888] dark:fill-gray-400 text-xs font-['Manrope']">Pass Rate</text>
              </svg>
            </div>
            <div className="flex justify-center gap-4 mt-3 text-xs font-['Manrope']">
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#4CAF50]" />Passed {passCount}</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#F44336]" />Failed {failCount}</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-gray-300 dark:bg-gray-600" />Not Run {notRunCount}</span>
            </div>
          </div>
        )}

        {!hiddenWidgets.has('environments') && (
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
            <h3 className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 mb-3">Active Environments</h3>
            {envLoaded ? (
              <div className="space-y-2 max-h-[200px] overflow-y-auto">
                {environments.filter(e => e.status === 'active').map(e => (
                  <div key={e.id} className="flex items-center gap-3 p-2 rounded-lg bg-[#F1F2F7] dark:bg-gray-700/50">
                    <span className={`w-2.5 h-2.5 rounded-full ${e.color || 'bg-green-500'}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[#333] dark:text-gray-100 truncate">{e.name}</p>
                      <p className="text-xs text-[#888] dark:text-gray-400 truncate">{e.baseUrl}</p>
                    </div>
                    <Badge variant="outline" className="text-[10px]">{e.browser}</Badge>
                  </div>
                ))}
                {environments.filter(e => e.status === 'active').length === 0 && <p className="text-xs text-[#888] dark:text-gray-400 text-center py-4">No active environments</p>}
              </div>
            ) : <Loader2 className="size-5 animate-spin text-[#3F51B5] mx-auto" />}
          </div>
        )}

        {!hiddenWidgets.has('recent-failures') && (
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
            <h3 className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 mb-3">Recent Failures</h3>
            {testsLoaded ? (
              <div className="space-y-2 max-h-[200px] overflow-y-auto">
                {stats.failedTests.slice(0, 6).map(t => (
                  <div key={t.id} className="flex items-start gap-2 p-2 rounded-lg bg-red-50 dark:bg-red-900/20">
                    <XCircle className="size-4 text-[#F44336] shrink-0 mt-0.5" />
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-[#333] dark:text-gray-100 truncate">{t.description}</p>
                      <p className="text-[10px] text-[#888] dark:text-gray-400">{t.moduleName}</p>
                    </div>
                  </div>
                ))}
                {stats.failedTests.length === 0 && <p className="text-xs text-[#888] dark:text-gray-400 text-center py-4">No failures 🎉</p>}
              </div>
            ) : <Loader2 className="size-5 animate-spin text-[#3F51B5] mx-auto" />}
          </div>
        )}
      </div>

      {!hiddenWidgets.has('recent-activity') && (
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 mb-3">Recent Activity</h3>
          {auditLog.length > 0 ? (
            <div className="space-y-2">
              {auditLog.slice(0, 5).map(a => (
                <div key={a.id} className="flex items-center gap-3 p-2 rounded-lg bg-[#F1F2F7] dark:bg-gray-700/50 text-xs font-['Manrope']">
                  <Badge className={`text-[9px] px-1.5 py-0 border-0 ${a.action === 'create' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : a.action === 'delete' ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300' : 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'}`}>{a.action}</Badge>
                  <span className="text-[#333] dark:text-gray-100">{a.userName}</span>
                  <span className="text-[#888] dark:text-gray-400">{a.targetLabel}</span>
                  <span className="ml-auto text-[#888] dark:text-gray-400">{new Date(a.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-[#888] dark:text-gray-400 text-center py-4">No recent activity</p>
          )}
        </div>
      )}

      <Dialog open={widgetDialogOpen} onOpenChange={setWidgetDialogOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100">Customize Widgets</DialogTitle>
            <DialogDescription className="font-['Manrope'] text-[#888]">
              Toggle which overview widgets are visible.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            {allWidgets.map(w => (
              <div key={w.id} className="flex items-center gap-3 p-2 rounded-lg bg-[#F1F2F7] dark:bg-gray-700/50">
                <Checkbox checked={!hiddenWidgets.has(w.id)} onCheckedChange={() => toggleWidgetVisibility(w.id)} />
                <span className="text-sm font-['Manrope'] text-[#333] dark:text-gray-100">{w.label}</span>
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button onClick={() => setWidgetDialogOpen(false)} className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Roboto']">Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
