'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Sparkles, Loader2, AlertTriangle, Bug, Wrench, ShieldCheck, Clock, GitBranch, Activity } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import { toast } from 'sonner'
import { withCsrf } from '@/lib/csrf-client'

interface FailureAnalysisResult {
  rootCause: string
  likelyCause: string
  fixSuggestion: string
  preventionTip: string
  relatedTests: string[]
  severityAssessment: string
  timeToFixEstimate: string
}

interface AiFailureAnalysisProps {
  open: boolean
  onClose: () => void
  testId: string
  testName: string
  error?: string
  moduleName: string
  stackTrace?: string
}

const severityStyles: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400', border: 'border-red-300 dark:border-red-700' },
  high: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-400', border: 'border-orange-300 dark:border-orange-700' },
  medium: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-400', border: 'border-yellow-300 dark:border-yellow-700' },
  low: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-400', border: 'border-green-300 dark:border-green-700' },
}

function getSeverityStyle(key: string) {
  const normalized = key?.toLowerCase() || 'medium'
  return severityStyles[normalized] || severityStyles['medium']
}

export function AiFailureAnalysis({ open, onClose, testId, testName, error, moduleName, stackTrace }: AiFailureAnalysisProps) {
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState<FailureAnalysisResult | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const prevOpenRef = useRef(false)

  async function analyzeFailure() {
    setLoading(true)
    setApiError(null)

    try {
      const res = await fetch('/api/ai/failure-analysis', withCsrf({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          testId,
          testName,
          error: error || 'Unknown error',
          moduleName,
          stackTrace: stackTrace || undefined,
          recentRuns: [],
        }),
      }))

      const data = await res.json()
      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Failed to analyze failure')
      }

      setAnalysis(data.analysis as FailureAnalysisResult)
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  function handleCopyFix() {
    if (!analysis) return
    navigator.clipboard.writeText(analysis.fixSuggestion).then(() => {
      toast.success('Fix suggestion copied to clipboard')
    }).catch(() => {
      toast.error('Failed to copy to clipboard')
    })
  }

  // Reset and analyze when dialog opens
  useEffect(() => {
    if (open && !prevOpenRef.current) {
      setAnalysis(null)
      setApiError(null)
      analyzeFailure()
    }
    prevOpenRef.current = open
  }, [open])

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-[600px] dark:bg-gray-800 dark:border-gray-700">
        <DialogHeader>
          <DialogTitle className="text-[16px] font-['Poppins'] flex items-center gap-2 text-[#333] dark:text-gray-100">
            <Bug className="size-5 text-red-500" />
            AI Failure Analysis
          </DialogTitle>
          <DialogDescription className="text-[12px] text-[#888] dark:text-gray-400 font-['Manrope']">
            Deep root cause analysis and fix suggestions powered by AI.
          </DialogDescription>
        </DialogHeader>

        {/* Test context */}
        <div className="bg-red-50 dark:bg-red-900/15 rounded-lg p-3 border border-red-100 dark:border-red-800/40 space-y-1.5">
          <div className="flex items-center gap-2 text-[12px]">
            <span className="text-gray-500 dark:text-gray-400 w-20 shrink-0">Test</span>
            <span className="font-mono font-semibold text-gray-800 dark:text-gray-100">{testId}</span>
            <span className="text-gray-400 dark:text-gray-500">—</span>
            <span className="text-gray-700 dark:text-gray-200 truncate">{testName}</span>
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
          {stackTrace && (
            <div className="flex items-start gap-2 text-[12px]">
              <span className="text-gray-500 dark:text-gray-400 w-20 shrink-0">Stack</span>
              <span className="text-red-600 dark:text-red-400 break-all font-mono text-[10px] max-h-20 overflow-y-auto">{stackTrace}</span>
            </div>
          )}
        </div>

        {/* Loading state */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-10 gap-3">
            <Loader2 className="size-8 text-red-500 animate-spin" />
            <span className="text-[13px] text-[#888] dark:text-gray-400 font-['Manrope']">AI is performing root cause analysis...</span>
            <span className="text-[11px] text-[#aaa] dark:text-gray-500 font-['Manrope']">Analyzing failure patterns and generating recommendations</span>
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
                onClick={analyzeFailure}
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
            {/* Severity & Time to Fix */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Activity className="size-3.5 text-[#888] dark:text-gray-400" />
                <span className="text-[11px] text-[#888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Severity</span>
                <Badge className={`${getSeverityStyle(analysis.severityAssessment).bg} ${getSeverityStyle(analysis.severityAssessment).text} ${getSeverityStyle(analysis.severityAssessment).border} border text-[11px] font-semibold capitalize`}>
                  {analysis.severityAssessment}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="size-3.5 text-[#888] dark:text-gray-400" />
                <span className="text-[11px] text-[#888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Time to Fix</span>
                <Badge variant="outline" className="text-[11px] font-semibold border-blue-200 dark:border-blue-700 text-blue-700 dark:text-blue-400">
                  {analysis.timeToFixEstimate}
                </Badge>
              </div>
              <Sparkles className="size-3 text-purple-400" />
            </div>

            {/* Root Cause */}
            <div className="bg-white dark:bg-gray-700/50 rounded-[10px] p-3 border border-gray-100 dark:border-gray-600/50">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="size-3.5 text-orange-500" />
                <span className="text-[11px] text-[#888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Root Cause</span>
                <Sparkles className="size-2.5 text-purple-400" />
              </div>
              <p className="text-[13px] text-[#333] dark:text-gray-100 font-['Manrope'] ml-5">{analysis.rootCause}</p>
            </div>

            {/* Likely Cause */}
            <div className="bg-white dark:bg-gray-700/50 rounded-[10px] p-3 border border-gray-100 dark:border-gray-600/50">
              <div className="flex items-center gap-2 mb-1">
                <Bug className="size-3.5 text-red-500" />
                <span className="text-[11px] text-[#888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Likely Cause</span>
              </div>
              <p className="text-[13px] text-[#333] dark:text-gray-100 font-['Manrope'] ml-5">{analysis.likelyCause}</p>
            </div>

            {/* Fix Suggestion */}
            <div className="bg-green-50 dark:bg-green-900/15 rounded-[10px] p-3 border border-green-100 dark:border-green-800/40">
              <div className="flex items-center gap-2 mb-1">
                <Wrench className="size-3.5 text-green-600" />
                <span className="text-[11px] text-green-600 dark:text-green-400 font-medium uppercase tracking-wider font-['Poppins']">Fix Suggestion</span>
                <Sparkles className="size-2.5 text-purple-400" />
              </div>
              <p className="text-[13px] text-[#333] dark:text-gray-100 font-['Manrope'] ml-5">{analysis.fixSuggestion}</p>
              <Button
                onClick={handleCopyFix}
                variant="ghost"
                size="sm"
                className="mt-2 ml-5 text-[10px] h-6 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/20 cursor-pointer px-2"
              >
                📋 Copy Fix
              </Button>
            </div>

            {/* Prevention Tip */}
            <div className="bg-blue-50 dark:bg-blue-900/15 rounded-[10px] p-3 border border-blue-100 dark:border-blue-800/40">
              <div className="flex items-center gap-2 mb-1">
                <ShieldCheck className="size-3.5 text-blue-500" />
                <span className="text-[11px] text-blue-500 dark:text-blue-400 font-medium uppercase tracking-wider font-['Poppins']">Prevention Tip</span>
                <Sparkles className="size-2.5 text-purple-400" />
              </div>
              <p className="text-[13px] text-[#333] dark:text-gray-100 font-['Manrope'] ml-5">{analysis.preventionTip}</p>
            </div>

            {/* Related Tests */}
            {analysis.relatedTests && analysis.relatedTests.length > 0 && (
              <div className="bg-white dark:bg-gray-700/50 rounded-[10px] p-3 border border-gray-100 dark:border-gray-600/50">
                <div className="flex items-center gap-2 mb-2">
                  <GitBranch className="size-3.5 text-purple-500" />
                  <span className="text-[11px] text-[#888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Related Tests (May Also Be Affected)</span>
                  <Sparkles className="size-2.5 text-purple-400" />
                </div>
                <div className="flex flex-wrap gap-1.5 ml-5">
                  {analysis.relatedTests.map((test, i) => (
                    <Badge
                      key={i}
                      variant="outline"
                      className="text-[11px] font-mono border-orange-200 dark:border-orange-700 text-orange-700 dark:text-orange-400"
                    >
                      {test}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <DialogFooter className="gap-2 pt-1">
          <Button onClick={onClose} className="cursor-pointer text-[12px] bg-transparent text-[#888] dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">
            Close
          </Button>
          {analysis && !loading && (
            <Button
              onClick={handleCopyFix}
              className="bg-green-600 hover:bg-green-700 text-white cursor-pointer text-[12px] gap-1.5"
            >
              <Wrench className="size-3.5" />
              Copy Fix Suggestion
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
