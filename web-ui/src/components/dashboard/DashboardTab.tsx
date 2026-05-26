'use client'

import React, { useMemo, useCallback } from 'react'
import { Progress } from '@/components/ui/progress'
import { Clock } from 'lucide-react'

interface ModuleHealth {
  moduleId: string
  moduleName: string
  parentGroup?: string
  passRate: number
  passedTests: number
  failedTests: number
  totalTests: number
  lastRun: string
}

const moduleHealthData: ModuleHealth[] = [
  // Standalone
  { moduleId: 'gst', moduleName: 'Gst', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 12, lastRun: '' },
  { moduleId: 'journal_entries', moduleName: 'Journal Entries', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 8, lastRun: '' },
  { moduleId: 'accounts_report', moduleName: 'Accounts Report', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 5, lastRun: '' },
  { moduleId: 'e_invoice', moduleName: 'E Invoice', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 6, lastRun: '' },
  { moduleId: 'material_management', moduleName: 'Material Management', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 15, lastRun: '' },
  { moduleId: 'purchase_and_sales_register', moduleName: 'Purchase And Sales Register', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 7, lastRun: '' },
  { moduleId: 'stock_aging_analysis', moduleName: 'Stock Aging Analysis', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 4, lastRun: '' },
  { moduleId: 'central_stock_register', moduleName: 'Central Stock Register', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 3, lastRun: '' },
  { moduleId: 'cost_center_allotment', moduleName: 'Cost Center Allotment', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 5, lastRun: '' },
  { moduleId: 'budgetary_control', moduleName: 'Budgetary Control', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 6, lastRun: '' },
  { moduleId: 'cheque_printing', moduleName: 'Cheque Printing', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 4, lastRun: '' },
  { moduleId: 'fixed_asset', moduleName: 'Fixed Asset', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 7, lastRun: '' },
  { moduleId: 'loan_and_advances', moduleName: 'Loan And Advances', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 5, lastRun: '' },
  { moduleId: 'inventory_valuation', moduleName: 'Inventory Valuation', parentGroup: 'Standalone', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 4, lastRun: '' },
  
  // Common Settings
  { moduleId: 'company_master', moduleName: 'Company Master', parentGroup: 'Common Settings', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 6, lastRun: '' },
  { moduleId: 'user_management', moduleName: 'User Management', parentGroup: 'Common Settings', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 8, lastRun: '' },
  { moduleId: 'role_permission', moduleName: 'Role Permission', parentGroup: 'Common Settings', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 5, lastRun: '' },
  { moduleId: 'audit_trail', moduleName: 'Audit Trail', parentGroup: 'Common Settings', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 4, lastRun: '' },
  { moduleId: 'email_sms_configuration', moduleName: 'Email Sms Configuration', parentGroup: 'Common Settings', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 3, lastRun: '' },
  { moduleId: 'workflow_approval', moduleName: 'Workflow Approval', parentGroup: 'Common Settings', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 6, lastRun: '' },
  { moduleId: 'number_format_configuration', moduleName: 'Number Format Configuration', parentGroup: 'Common Settings', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 3, lastRun: '' },
  { moduleId: 'print_configuration', moduleName: 'Print Configuration', parentGroup: 'Common Settings', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 4, lastRun: '' },
  
  // Commodity Settings
  { moduleId: 'gst_commodity', moduleName: 'Gst Commodity', parentGroup: 'Commodity Settings', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 8, lastRun: '' },
  { moduleId: 'rate_contract', moduleName: 'Rate Contract', parentGroup: 'Commodity Settings', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 6, lastRun: '' },
  { moduleId: 'weighment_scale_integration', moduleName: 'Weighment Scale Integration', parentGroup: 'Commodity Settings', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 4, lastRun: '' },
  { moduleId: 'quality_inspection', moduleName: 'Quality Inspection', parentGroup: 'Commodity Settings', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 5, lastRun: '' },
  { moduleId: 'warehouse_management', moduleName: 'Warehouse Management', parentGroup: 'Commodity Settings', passRate: 0, passedTests: 0, failedTests: 0, totalTests: 7, lastRun: '' },
]

interface ModuleGroup {
  name: string
  icon: string
  modules: ModuleHealth[]
}

export function DashboardTab({ onSelectModule }: { onSelectModule: (moduleId: string) => void }) {
  const grouped = useMemo(() => {
    const order = ['Standalone', 'Common Settings', 'Commodity Settings']
    const groups: ModuleGroup[] = []
    const groupMap = new Map<string, ModuleHealth[]>()

    for (const mod of moduleHealthData) {
      const g = mod.parentGroup || 'Other'
      if (!groupMap.has(g)) groupMap.set(g, [])
      groupMap.get(g)!.push(mod)
    }

    for (const name of order) {
      const mods = groupMap.get(name)
      if (mods) groups.push({ name, icon: name === 'Common Settings' ? '⚙️' : name === 'Commodity Settings' ? '📦' : '📁', modules: mods })
    }
    for (const [name, mods] of groupMap) {
      if (!order.includes(name)) groups.push({ name, icon: '📁', modules: mods })
    }
    return groups
  }, [])

  const quickStats = useMemo(() => {
    const total = moduleHealthData.length
    const fullyPassing = moduleHealthData.filter((m) => m.totalTests > 0 && m.passRate === 100).length
    const partiallyPassing = moduleHealthData.filter((m) => m.totalTests > 0 && m.passRate > 0 && m.passRate < 100).length
    const notStarted = moduleHealthData.filter((m) => m.totalTests === 0).length
    const totalPassed = moduleHealthData.reduce((s, m) => s + m.passedTests, 0)
    const totalFailed = moduleHealthData.reduce((s, m) => s + m.failedTests, 0)
    const totalTests = moduleHealthData.reduce((s, m) => s + m.totalTests, 0)
    return { total, fullyPassing, partiallyPassing, notStarted, totalPassed, totalFailed, totalTests }
  }, [])

  const getHealthColor = useCallback((rate: number, total: number) => {
    if (total === 0) return { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-400 dark:text-gray-500', indicator: 'bg-gray-400', label: 'Not Started' }
    if (rate === 100) return { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-700 dark:text-green-400', indicator: 'bg-green-500', label: 'Healthy' }
    if (rate >= 75) return { bg: 'bg-orange-50 dark:bg-orange-900/20', text: 'text-orange-700 dark:text-orange-400', indicator: 'bg-orange-500', label: 'Partial' }
    return { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-700 dark:text-red-400', indicator: 'bg-red-500', label: 'Critical' }
  }, [])

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="p-5 space-y-5">
        {/* Page Header */}
        <div>
          <h2 className="text-[18px] font-semibold text-gray-800 dark:text-gray-100">Dashboard</h2>
          <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-0.5">Overview of all RhythmERP automation modules</p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3.5 border border-gray-100 dark:border-gray-700">
            <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider">Total Modules</div>
            <div className="text-xl font-bold text-gray-800 dark:text-gray-100 mt-1">{quickStats.total}</div>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3.5 border border-green-100 dark:border-green-800/50">
            <div className="text-[11px] text-green-600 dark:text-green-400 font-medium uppercase tracking-wider">Fully Passing</div>
            <div className="text-xl font-bold text-green-700 dark:text-green-400 mt-1">{quickStats.fullyPassing}</div>
          </div>
          <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-3.5 border border-orange-100 dark:border-orange-800/50">
            <div className="text-[11px] text-orange-600 dark:text-orange-400 font-medium uppercase tracking-wider">Partial / Critical</div>
            <div className="text-xl font-bold text-orange-700 dark:text-orange-400 mt-1">{quickStats.partiallyPassing}</div>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3.5 border border-blue-100 dark:border-blue-800/50">
            <div className="text-[11px] text-blue-600 dark:text-blue-400 font-medium uppercase tracking-wider">Overall Pass Rate</div>
            <div className="text-xl font-bold text-blue-700 dark:text-blue-400 mt-1">
              {quickStats.totalTests > 0 ? Math.round((quickStats.totalPassed / quickStats.totalTests) * 100) : 0}%
            </div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
              {quickStats.totalPassed} / {quickStats.totalTests} tests passed
            </div>
          </div>
        </div>

        {/* Module Groups */}
        {grouped.map((group) => {
          const groupTotal = group.modules.reduce((s, m) => s + m.totalTests, 0)
          const groupPassed = group.modules.reduce((s, m) => s + m.passedTests, 0)
          const groupFailed = group.modules.reduce((s, m) => s + m.failedTests, 0)
          const groupRate = groupTotal > 0 ? Math.round((groupPassed / groupTotal) * 100) : 0
          const groupHealth = getHealthColor(groupRate, groupTotal)

          return (
            <div key={group.name}>
              {/* Group Header */}
              <div className="flex items-center gap-2 mb-2.5">
                <span className="text-[14px]">{group.icon}</span>
                <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">{group.name}</h3>
                <span className="text-[12px] text-gray-500 dark:text-gray-400 ml-1">
                  {group.modules.length} modules
                </span>
                {groupTotal > 0 && (
                  <>
                    <div className="flex-1" />
                    <span className={`text-[12px] font-medium ${groupHealth.text}`}>
                      {groupRate}%
                    </span>
                    <span className="text-[11px] text-gray-400 dark:text-gray-500">
                      ({groupPassed}/{groupTotal})
                    </span>
                  </>
                )}
              </div>

              {/* Module Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2.5">
                {group.modules.map((mod) => {
                  const health = getHealthColor(mod.passRate, mod.totalTests)
                  return (
                    <button
                      key={mod.moduleId}
                      onClick={() => onSelectModule(mod.moduleId)}
                      className={`text-left p-3 rounded-lg border transition-all hover:shadow-md hover:-translate-y-0.5 cursor-pointer ${health.bg} border-gray-100 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${health.indicator}`} />
                        <span className="text-[13px] font-medium text-gray-800 dark:text-gray-100 truncate">{mod.moduleName}</span>
                      </div>
                      <div className="flex items-center gap-3 text-[11px]">
                        {mod.totalTests > 0 ? (
                          <>
                            <span className={`font-medium ${health.text}`}>{mod.passRate}%</span>
                            <span className="text-gray-400 dark:text-gray-500">
                              {mod.passedTests}/{mod.totalTests}
                            </span>
                            <Progress value={mod.passRate} className="h-1.5 flex-1 bg-gray-200 dark:bg-gray-700" />
                          </>
                        ) : (
                          <span className="text-gray-400 dark:text-gray-500">No tests yet</span>
                        )}
                      </div>
                      {mod.totalTests > 0 && (
                        <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-1.5 flex items-center gap-1">
                          <Clock className="size-2.5" />
                          {mod.lastRun}
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
    </div>
  )
}
