'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Sparkles, Loader2, AlertTriangle, User, Tag, Shield, Target, Zap, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import { toast } from 'sonner'
import { withCsrf } from '@/lib/csrf-client'

interface BugTriageAnalysis {
  priority: string
  category: string
  suggestedAssignee: string
  rootCauseHypothesis: string
  severity: string
  impactAssessment: string
  recommendedAction: string
}

interface AiBugTriageProps {
  open: boolean
  onClose: () => void
  testId: string
  testDescription: string
  error?: string
  moduleName: string
  userName: string
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

export function AiBugTriage({ open, onClose, testId, testDescription, error, moduleName, userName }: AiBugTriageProps) {
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState<BugTriageAnalysis | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const [applied, setApplied] = useState(false)
  const prevOpenRef = useRef(false)

  async function analyzeBug() {
    setLoading(true)
    setApiError(null)
    try {
      const res = await fetch('/api/ai/bug-triage', withCsrf({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          testId,
          testDescription,
          error: error || 'Unknown error',
          moduleName,
          userName,
        }),
      }))
      const data = await res.json()
      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Failed to analyze bug')
      }
      setAnalysis(data.analysis as BugTriageAnalysis)
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  function handleApplyPriority() {
    if (!analysis) return
    setApplied(true)
    toast.success('Priority applied', {
      description: `Bug priority set to ${analysis.priority}`,
      duration: 3000,
    })
  }

  // Reset and analyze when dialog opens
  useEffect(() => {
    if (open && !prevOpenRef.current) {
      setAnalysis(null)
      setApiError(null)
      setApplied(false)
      analyzeBug()
    }
    prevOpenRef.current = open
  }, [open])

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-[560px] dark:bg-gray-800 dark:border-gray-700">
        <DialogHeader>
          <DialogTitle className="text-[16px] font-['Poppins'] flex items-center gap-2 text-[#333] dark:text-gray-100">
            <Sparkles className="size-5 text-purple-500" />
            AI Bug Triage
          </DialogTitle>
          <DialogDescription className="text-[12px] text-[#888] dark:text-gray-400 font-['Manrope']">
            AI-powered analysis of the test failure to classify and recommend actions.
          </DialogDescription>
        </DialogHeader>

        {/* Test context */}
        <div className="bg-red-50 dark:bg-red-900/15 rounded-lg p-3 border border-red-100 dark:border-red-800/40 space-y-1.5">
          <div className="flex items-center gap-2 text-[12px]">
            <span className="text-gray-500 dark:text-gray-400 w-20 shrink-0">Test ID</span>
            <span className="font-mono font-semibold text-gray-800 dark:text-gray-100">{testId}</span>
          </div>
          <div className="flex items-center gap-2 text-[12px]">
            <span className="text-gray-500 dark:text-gray-400 w-20 shrink-0">Description</span>
            <span className="text-gray-700 dark:text-gray-200">{testDescription}</span>
          </div>
          <div className="flex items-center gap-2 text-[12px]">
            <span className="text-gray-500 dark:text-gray-400 w-20 shrink-0">Module</span>
            <span className="text-gray-700 dark:text-gray-200">{moduleName}</span>
          </div>
          {error && (
            <div className="flex items-start gap-2 text-[12px]">
              <span className="text-gray-500 dark:text-gray-400 w-20 shrink-0">Error</span>
              <span className="text-red-600 dark:text-red-400 break-all">{error}</span>
            </div>
          )}
        </div>

        {/* Loading state */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-10 gap-3">
            <Loader2 className="size-8 text-purple-500 animate-spin" />
            <span className="text-[13px] text-[#888] dark:text-gray-400 font-['Manrope']">AI is analyzing the bug...</span>
          </div>
        )}

        {/* Error state */}
        {apiError && !loading && (
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 border border-red-200 dark:border-red-800/50 flex items-start gap-3">
            <AlertTriangle className="size-5 text-red-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-[13px] font-medium text-red-700 dark:text-red-400 font-['Poppins']">Analysis failed</p>
              <p className="text-[12px] text-red-600 dark:text-red-400 mt-1 font-['Manrope']">{apiError}</p>
              <Button
                onClick={analyzeBug}
                variant="outline"
                size="sm"
                className="mt-2 text-[11px] h-7 border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 cursor-pointer"
              >
                Retry
              </Button>
            </div>
          </div>
        )}

        {/* Analysis results */}
        {analysis && !loading && !apiError && (
          <div className="space-y-4">
            {/* Priority & Severity row */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <Tag className="size-3.5 text-[#888] dark:text-gray-400" />
                <span className="text-[11px] text-[#888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Priority</span>
                <Badge className={`${getStyle(priorityStyles, analysis.priority).bg} ${getStyle(priorityStyles, analysis.priority).text} ${getStyle(priorityStyles, analysis.priority).border} border text-[11px] font-semibold capitalize`}>
                  {analysis.priority}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <Shield className="size-3.5 text-[#888] dark:text-gray-400" />
                <span className="text-[11px] text-[#888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Severity</span>
                <Badge className={`${getStyle(severityStyles, analysis.severity).bg} ${getStyle(severityStyles, analysis.severity).text} ${getStyle(severityStyles, analysis.severity).border} border text-[11px] font-semibold capitalize`}>
                  {analysis.severity}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <Sparkles className="size-3 text-purple-500" />
              </div>
            </div>

            {/* Category */}
            <div className="bg-white dark:bg-gray-700/50 rounded-[10px] p-3 border border-gray-100 dark:border-gray-600/50">
              <div className="flex items-center gap-2 mb-1">
                <Target className="size-3.5 text-blue-500" />
                <span className="text-[11px] text-[#888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Category</span>
              </div>
              <p className="text-[13px] text-[#333] dark:text-gray-100 font-['Manrope'] ml-5">{analysis.category}</p>
            </div>

            {/* Suggested Assignee */}
            <div className="bg-white dark:bg-gray-700/50 rounded-[10px] p-3 border border-gray-100 dark:border-gray-600/50">
              <div className="flex items-center gap-2 mb-1">
                <User className="size-3.5 text-green-500" />
                <span className="text-[11px] text-[#888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Suggested Assignee</span>
              </div>
              <p className="text-[13px] text-[#333] dark:text-gray-100 font-['Manrope'] ml-5">{analysis.suggestedAssignee}</p>
            </div>

            {/* Root Cause */}
            <div className="bg-white dark:bg-gray-700/50 rounded-[10px] p-3 border border-gray-100 dark:border-gray-600/50">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="size-3.5 text-orange-500" />
                <span className="text-[11px] text-[#888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Root Cause Hypothesis</span>
              </div>
              <p className="text-[13px] text-[#333] dark:text-gray-100 font-['Manrope'] ml-5">{analysis.rootCauseHypothesis}</p>
            </div>

            {/* Impact Assessment */}
            <div className="bg-white dark:bg-gray-700/50 rounded-[10px] p-3 border border-gray-100 dark:border-gray-600/50">
              <div className="flex items-center gap-2 mb-1">
                <Zap className="size-3.5 text-yellow-500" />
                <span className="text-[11px] text-[#888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Impact Assessment</span>
              </div>
              <p className="text-[13px] text-[#333] dark:text-gray-100 font-['Manrope'] ml-5">{analysis.impactAssessment}</p>
            </div>

            {/* Recommended Action */}
            <div className="bg-purple-50 dark:bg-purple-900/15 rounded-[10px] p-3 border border-purple-100 dark:border-purple-800/40">
              <div className="flex items-center gap-2 mb-1">
                <ChevronRight className="size-3.5 text-purple-500" />
                <span className="text-[11px] text-purple-500 font-medium uppercase tracking-wider font-['Poppins']">Recommended Action</span>
                <Sparkles className="size-3 text-purple-400" />
              </div>
              <p className="text-[13px] text-[#333] dark:text-gray-100 font-['Manrope'] ml-5">{analysis.recommendedAction}</p>
            </div>
          </div>
        )}

        <DialogFooter className="gap-2 pt-1">
          <Button onClick={onClose} className="cursor-pointer text-[12px] bg-transparent text-[#888] dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">
            Close
          </Button>
          {analysis && !loading && (
            <Button
              onClick={handleApplyPriority}
              disabled={applied}
              className="bg-purple-500 hover:bg-purple-600 text-white cursor-pointer text-[12px] gap-1.5"
            >
              {applied ? (
                <>✓ Priority Applied</>
              ) : (
                <>
                  <Sparkles className="size-3.5" />
                  Apply Priority
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
