'use client'

import React, { useState } from 'react'
import { Sparkles, Loader2, AlertTriangle, Brain, Target, ShieldAlert, FileText, Lightbulb } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ScrollArea } from '@/components/ui/scroll-area'
import { toast } from 'sonner'

interface SuggestedTest {
  name: string
  reason: string
  priority: string
  module: string
}

interface RiskArea {
  area: string
  reason: string
  severity: string
}

interface TestSuggestionsResult {
  suggestedTests: SuggestedTest[]
  riskAreas: RiskArea[]
  overallAssessment: string
}

interface AiTestSuggestionsProps {
  failedTests: Array<{ id: string; name: string; error?: string; module: string }>
  currentModule: string
}

const priorityStyles: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400', border: 'border-red-300 dark:border-red-700' },
  high: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-400', border: 'border-orange-300 dark:border-orange-700' },
  medium: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-400', border: 'border-yellow-300 dark:border-yellow-700' },
  low: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-400', border: 'border-green-300 dark:border-green-700' },
}

const severityStyles: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400', border: 'border-red-300 dark:border-red-700' },
  high: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-400', border: 'border-orange-300 dark:border-orange-700' },
  medium: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-400', border: 'border-yellow-300 dark:border-yellow-700' },
  low: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-400', border: 'border-green-300 dark:border-green-700' },
}

function getStyle(map: Record<string, { bg: string; text: string; border: string }>, key: string) {
  const normalized = key?.toLowerCase() || 'medium'
  return map[normalized] || map['medium']
}

export function AiTestSuggestions({ failedTests, currentModule }: AiTestSuggestionsProps) {
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState<TestSuggestionsResult | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)

  async function fetchSuggestions() {
    if (failedTests.length === 0) {
      toast.info('No failed tests to analyze', { description: 'Run tests first to get AI suggestions.' })
      return
    }

    setLoading(true)
    setApiError(null)
    setSuggestions(null)

    try {
      const moduleHistory = [
        {
          moduleId: currentModule,
          passRate: 0,
          recentTrend: 'declining',
        },
      ]

      const res = await fetch('/api/ai/test-suggestions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          failedTests: failedTests.map((t) => ({
            id: t.id,
            name: t.name,
            error: t.error || 'No error details',
            module: t.module,
          })),
          moduleHistory,
        }),
      })

      const data = await res.json()
      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Failed to get suggestions')
      }

      setSuggestions(data.suggestions as TestSuggestionsResult)
      toast.success('AI suggestions generated', { description: 'Review the suggested tests and risk areas.' })
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-5 border border-gray-100 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain className="size-5 text-purple-500" />
          <h3 className="text-[15px] font-semibold text-[#333] dark:text-gray-100 font-['Poppins']">AI Test Suggestions</h3>
        </div>
        <Button
          onClick={fetchSuggestions}
          disabled={loading || failedTests.length === 0}
          className="bg-purple-500 hover:bg-purple-600 text-white cursor-pointer text-[12px] gap-1.5 h-8 px-4"
        >
          {loading ? (
            <>
              <Loader2 className="size-3.5 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Sparkles className="size-3.5" />
              Get AI Suggestions
            </>
          )}
        </Button>
      </div>

      {/* No failed tests info */}
      {failedTests.length === 0 && !suggestions && !loading && (
        <div className="text-center py-8">
          <Lightbulb className="size-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
          <p className="text-[13px] text-[#888] dark:text-gray-400 font-['Manrope']">No failed tests to analyze. Run tests and come back for AI suggestions.</p>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-12 gap-3">
          <Loader2 className="size-8 text-purple-500 animate-spin" />
          <span className="text-[13px] text-[#888] dark:text-gray-400 font-['Manrope']">AI is analyzing failure patterns...</span>
          <span className="text-[11px] text-[#aaa] dark:text-gray-500 font-['Manrope']">This may take a few seconds</span>
        </div>
      )}

      {/* Error state */}
      {apiError && !loading && (
        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 border border-red-200 dark:border-red-800/50 flex items-start gap-3">
          <AlertTriangle className="size-5 text-red-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-[13px] font-medium text-red-700 dark:text-red-400 font-['Poppins']">Failed to generate suggestions</p>
            <p className="text-[12px] text-red-600 dark:text-red-400 mt-1 font-['Manrope']">{apiError}</p>
            <Button
              onClick={fetchSuggestions}
              variant="outline"
              size="sm"
              className="mt-2 text-[11px] h-7 border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 cursor-pointer"
            >
              Retry
            </Button>
          </div>
        </div>
      )}

      {/* Results */}
      {suggestions && !loading && !apiError && (
        <div className="space-y-5">
          {/* Suggested Tests Table */}
          {suggestions.suggestedTests && suggestions.suggestedTests.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <FileText className="size-4 text-blue-500" />
                <span className="text-[13px] font-semibold text-[#333] dark:text-gray-100 font-['Poppins']">Suggested Tests</span>
                <Sparkles className="size-3 text-purple-400" />
                <Badge variant="secondary" className="text-[10px] ml-1">{suggestions.suggestedTests.length}</Badge>
              </div>
              <ScrollArea className="max-h-72">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead className="text-[11px] text-[#888] dark:text-gray-400 font-['Poppins'] uppercase tracking-wider">Test Name</TableHead>
                      <TableHead className="text-[11px] text-[#888] dark:text-gray-400 font-['Poppins'] uppercase tracking-wider">Reason</TableHead>
                      <TableHead className="text-[11px] text-[#888] dark:text-gray-400 font-['Poppins'] uppercase tracking-wider w-24">Priority</TableHead>
                      <TableHead className="text-[11px] text-[#888] dark:text-gray-400 font-['Poppins'] uppercase tracking-wider w-28">Module</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {suggestions.suggestedTests.map((test, i) => (
                      <TableRow key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                        <TableCell className="text-[12px] font-medium text-[#333] dark:text-gray-100 font-['Manrope']">{test.name}</TableCell>
                        <TableCell className="text-[12px] text-[#666] dark:text-gray-300 font-['Manrope'] max-w-[200px]">{test.reason}</TableCell>
                        <TableCell>
                          <Badge className={`${getStyle(priorityStyles, test.priority).bg} ${getStyle(priorityStyles, test.priority).text} ${getStyle(priorityStyles, test.priority).border} border text-[10px] font-semibold capitalize`}>
                            {test.priority}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-[12px] text-[#666] dark:text-gray-300 font-['Manrope']">{test.module}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>
            </div>
          )}

          {/* Risk Areas Cards */}
          {suggestions.riskAreas && suggestions.riskAreas.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <ShieldAlert className="size-4 text-orange-500" />
                <span className="text-[13px] font-semibold text-[#333] dark:text-gray-100 font-['Poppins']">Risk Areas</span>
                <Sparkles className="size-3 text-purple-400" />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {suggestions.riskAreas.map((area, i) => (
                  <div
                    key={i}
                    className="bg-white dark:bg-gray-700/50 rounded-[10px] p-3 border border-gray-100 dark:border-gray-600/50 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <Target className="size-3.5 text-orange-500" />
                        <span className="text-[12px] font-semibold text-[#333] dark:text-gray-100 font-['Poppins']">{area.area}</span>
                      </div>
                      <Badge className={`${getStyle(severityStyles, area.severity).bg} ${getStyle(severityStyles, area.severity).text} ${getStyle(severityStyles, area.severity).border} border text-[10px] font-semibold capitalize`}>
                        {area.severity}
                      </Badge>
                    </div>
                    <p className="text-[11px] text-[#666] dark:text-gray-300 font-['Manrope'] ml-5">{area.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Overall Assessment */}
          {suggestions.overallAssessment && (
            <div className="bg-purple-50 dark:bg-purple-900/15 rounded-[10px] p-4 border border-purple-100 dark:border-purple-800/40">
              <div className="flex items-center gap-2 mb-1.5">
                <Brain className="size-4 text-purple-500" />
                <span className="text-[12px] font-semibold text-purple-600 dark:text-purple-400 font-['Poppins'] uppercase tracking-wider">Overall Assessment</span>
                <Sparkles className="size-3 text-purple-400" />
              </div>
              <p className="text-[13px] text-[#333] dark:text-gray-100 font-['Manrope'] ml-6">{suggestions.overallAssessment}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
