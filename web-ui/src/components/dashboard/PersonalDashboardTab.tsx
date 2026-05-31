'use client'

import React from 'react'
import { Hand, Activity, CheckCircle2, Bug, FolderTree, Play, Plus, Clock, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export interface PersonalDashboardTabProps {
  userName: string
  userRole: string
  stats: {
    totalRuns: number
    passRate: number
    bugsReported: number
    modulesTested: number
    recentRuns: Array<{
      id: string
      moduleName: string
      passed: number
      failed: number
      date: string
      rate: number
    }>
    recentBugs: Array<{
      id: string
      testDescription: string
      moduleName: string
      status: string
      createdAt: string
    }>
  }
  onRunTests?: () => void
  onReportBug?: () => void
  onSelectModule?: (moduleId: string) => void
}

export function PersonalDashboardTab({
  userName,
  userRole,
  stats,
  onRunTests,
  onReportBug,
  onSelectModule,
}: PersonalDashboardTabProps) {
  const statusLabel: Record<string, string> = {
    open: 'Open',
    in_progress: 'In Progress',
    fixed: 'Fixed',
    closed: 'Closed',
    rejected: 'Rejected',
  }
  const statusColor: Record<string, string> = {
    open: 'bg-[#F44336] text-white',
    in_progress: 'bg-[#FF9800] text-white',
    fixed: 'bg-[#4CAF50] text-white',
    closed: 'bg-[#888888] text-white',
    rejected: 'bg-gray-400 text-white',
  }

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="p-5 space-y-5">
        {/* Personal Greeting */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-[#E8F5E9] dark:bg-green-900/30 flex items-center justify-center">
            <Hand className="size-6 text-[#2E7D32] dark:text-green-400" />
          </div>
          <div>
            <h2 className="text-[20px] font-semibold text-[#333333] dark:text-gray-100 font-['Poppins']">
              Welcome back, {userName}!
            </h2>
            <p className="text-[13px] text-[#666666] dark:text-gray-400 mt-0.5 font-['Manrope']">
              Here&apos;s your personal testing overview
            </p>
          </div>
        </div>

        {/* Stat Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {/* Your Runs */}
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg bg-[#E8F5E9] dark:bg-green-900/30 flex items-center justify-center">
                <Activity className="size-4 text-[#2E7D32] dark:text-green-400" />
              </div>
              <span className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">
                Your Runs
              </span>
            </div>
            <div className="text-xl font-bold text-[#333333] dark:text-gray-100 font-['Poppins']">
              {stats.totalRuns}
            </div>
            <div className="text-[11px] text-[#888888] dark:text-gray-400 mt-1 font-['Manrope']">
              test runs completed
            </div>
          </div>

          {/* Pass Rate */}
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-green-100 dark:border-green-800/50">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg bg-[#E8F5E9] dark:bg-green-900/30 flex items-center justify-center">
                <CheckCircle2 className="size-4 text-[#2E7D32] dark:text-green-400" />
              </div>
              <span className="text-[11px] text-[#4CAF50] dark:text-green-400 font-medium uppercase tracking-wider font-['Poppins']">
                Pass Rate
              </span>
            </div>
            <div className="text-xl font-bold text-[#2E7D32] dark:text-green-400 font-['Poppins']">
              {stats.passRate.toFixed(1)}%
            </div>
            <div className="text-[11px] text-[#888888] dark:text-gray-400 mt-1 font-['Manrope']">
              across all your runs
            </div>
          </div>

          {/* Bugs Reported */}
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg bg-[#FFEBEE] dark:bg-red-900/30 flex items-center justify-center">
                <Bug className="size-4 text-[#F44336] dark:text-red-400" />
              </div>
              <span className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">
                Bugs Reported
              </span>
            </div>
            <div className="text-xl font-bold text-[#333333] dark:text-gray-100 font-['Poppins']">
              {stats.bugsReported}
            </div>
            <div className="text-[11px] text-[#888888] dark:text-gray-400 mt-1 font-['Manrope']">
              bug reports filed
            </div>
          </div>

          {/* Modules Tested */}
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg bg-[#E8F5E9] dark:bg-green-900/30 flex items-center justify-center">
                <FolderTree className="size-4 text-[#2E7D32] dark:text-green-400" />
              </div>
              <span className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">
                Modules Tested
              </span>
            </div>
            <div className="text-xl font-bold text-[#333333] dark:text-gray-100 font-['Poppins']">
              {stats.modulesTested}
            </div>
            <div className="text-[11px] text-[#888888] dark:text-gray-400 mt-1 font-['Manrope']">
              modules covered
            </div>
          </div>
        </div>

        {/* Two Column Layout: Recent Runs + Bug Reports */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Recent Runs */}
          <Card className="border-gray-100 dark:border-gray-700 shadow-sm rounded-[14px]">
            <CardHeader className="pb-3 pt-4 px-4">
              <CardTitle className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 flex items-center gap-2 font-['Poppins']">
                <Clock className="size-4 text-[#2E7D32]" />
                Recent Runs
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4">
              {stats.recentRuns.length === 0 ? (
                <div className="text-center py-8">
                  <Activity className="size-8 text-[#888888] mx-auto mb-2" />
                  <p className="text-[12px] text-[#888888] dark:text-gray-400 font-['Manrope']">
                    No runs recorded yet
                  </p>
                  <p className="text-[11px] text-[#888888] dark:text-gray-500 mt-1 font-['Manrope']">
                    Start running tests to see your history here
                  </p>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {stats.recentRuns.map((run) => (
                    <button
                      key={run.id}
                      onClick={() => onSelectModule?.(run.moduleName?.toLowerCase().replace(/\s+/g, '-'))}
                      className="w-full text-left p-3 rounded-lg hover:bg-[#E8F5E9]/50 dark:hover:bg-green-900/10 transition-colors border border-gray-50 dark:border-gray-700/50 group cursor-pointer"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[12px] font-medium text-[#333333] dark:text-gray-100 truncate font-['Manrope']">
                          {run.moduleName}
                        </span>
                        <ChevronRight className="size-3.5 text-[#888888] opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                      <div className="flex items-center gap-3 text-[11px]">
                        <span className="text-[#4CAF50] dark:text-green-400 font-medium font-['Manrope']">
                          {run.passed} passed
                        </span>
                        <span className="text-[#F44336] dark:text-red-400 font-medium font-['Manrope']">
                          {run.failed} failed
                        </span>
                        <span
                          className={`font-semibold font-['Poppins'] ${
                            run.rate >= 80
                              ? 'text-[#2E7D32] dark:text-green-400'
                              : run.rate >= 50
                                ? 'text-[#E65100] dark:text-orange-400'
                                : 'text-[#C62828] dark:text-red-400'
                          }`}
                        >
                          {run.rate.toFixed(1)}%
                        </span>
                        <span className="text-[#888888] dark:text-gray-500 ml-auto font-['Manrope']">
                          {run.date
                            ? new Date(run.date).toLocaleDateString('en-GB', {
                                day: '2-digit',
                                month: 'short',
                                hour: '2-digit',
                                minute: '2-digit',
                              })
                            : ''}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Your Bug Reports */}
          <Card className="border-gray-100 dark:border-gray-700 shadow-sm rounded-[14px]">
            <CardHeader className="pb-3 pt-4 px-4">
              <CardTitle className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 flex items-center gap-2 font-['Poppins']">
                <Bug className="size-4 text-[#F44336]" />
                Your Bug Reports
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4">
              {stats.recentBugs.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle2 className="size-8 text-[#4CAF50] mx-auto mb-2" />
                  <p className="text-[12px] text-[#888888] dark:text-gray-400 font-['Manrope']">
                    No bugs reported yet
                  </p>
                  <p className="text-[11px] text-[#888888] dark:text-gray-500 mt-1 font-['Manrope']">
                    Bugs will appear here when you report them
                  </p>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {stats.recentBugs.map((bug) => (
                    <div
                      key={bug.id}
                      className="flex items-start gap-2 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors border border-gray-50 dark:border-gray-700/50"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5 mb-1">
                          <span className="text-[12px] font-medium text-[#333333] dark:text-gray-100 truncate font-['Manrope']">
                            {bug.testDescription}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          {bug.moduleName && (
                            <Badge
                              variant="outline"
                              className="text-[10px] h-4 px-1.5 font-['Manrope']"
                            >
                              {bug.moduleName}
                            </Badge>
                          )}
                          <Badge
                            className={`text-[10px] h-4 px-1.5 ${
                              statusColor[bug.status] ?? 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {statusLabel[bug.status] ?? bug.status}
                          </Badge>
                        </div>
                      </div>
                      <span className="text-[10px] text-[#888888] dark:text-gray-500 shrink-0 font-['Manrope']">
                        {bug.createdAt
                          ? new Date(bug.createdAt).toLocaleDateString('en-GB', {
                              day: '2-digit',
                              month: 'short',
                            })
                          : ''}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
          <h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']">
            Quick Actions
          </h3>
          <div className="flex items-center gap-3 flex-wrap">
            <Button
              onClick={onRunTests}
              className="bg-[#2E7D32] hover:bg-[#1B5E20] text-white text-[12px] h-9 px-4 gap-2 font-['Roboto'] cursor-pointer"
            >
              <Play className="size-3.5" />
              Run Tests
            </Button>
            <Button
              onClick={onReportBug}
              variant="outline"
              className="text-[12px] h-9 px-4 gap-2 font-['Roboto'] border-[#2E7D32] text-[#2E7D32] hover:bg-[#E8F5E9] dark:hover:bg-green-900/20 cursor-pointer"
            >
              <Plus className="size-3.5" />
              Report a Bug
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
