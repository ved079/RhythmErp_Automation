'use client'

import React, { useState, useRef } from 'react'
import { Sparkles, Loader2, Wand2, AlertTriangle, Play, X, Terminal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'

interface NlRunInterpretation {
  understood: boolean
  modules: string[]
  testIds: string[]
  runType: string
  priority?: string
  explanation: string
}

interface AiNlRunBarProps {
  availableModules: string[]
  availableTests: Array<{ id: string; name: string; module: string }>
  onApplySelection: (testIds: string[], runType: string) => void
}

export function AiNlRunBar({ availableModules, availableTests, onApplySelection }: AiNlRunBarProps) {
  const [command, setCommand] = useState('')
  const [loading, setLoading] = useState(false)
  const [interpretation, setInterpretation] = useState<NlRunInterpretation | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  function handleCommandChange(value: string) {
    setCommand(value)
    // Reset interpretation/error when command changes
    if (interpretation) setInterpretation(null)
    if (apiError) setApiError(null)
  }

  async function handleSubmit() {
    const trimmed = command.trim()
    if (!trimmed) return

    setLoading(true)
    setApiError(null)
    setInterpretation(null)

    try {
      const res = await fetch('/api/ai/nl-run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: trimmed,
          availableModules,
          availableTests,
        }),
      })

      const data = await res.json()
      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Failed to interpret command')
      }

      setInterpretation(data.interpretation as NlRunInterpretation)
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  function handleExecute() {
    if (!interpretation) return
    onApplySelection(interpretation.testIds, interpretation.runType)
    toast.success('AI selection applied', {
      description: `${interpretation.testIds.length} test(s) selected for ${interpretation.runType} run.`,
      duration: 3000,
    })
    setCommand('')
    setInterpretation(null)
    setApiError(null)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !loading && command.trim()) {
      e.preventDefault()
      handleSubmit()
    }
  }

  function handleClear() {
    setCommand('')
    setInterpretation(null)
    setApiError(null)
    inputRef.current?.focus()
  }

  const runTypeLabels: Record<string, string> = {
    all: 'Run All',
    priority: 'Priority Run',
    selected: 'Selected Tests',
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
      {/* Input Bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-gray-700">
        <Wand2 className="size-4 text-purple-500 shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={command}
          onChange={(e) => handleCommandChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder='Try "Run all EOD tests" or "Run smoke tests for Purchasing"'
          className="flex-1 text-[13px] text-[#333] dark:text-gray-100 font-['Manrope'] bg-transparent outline-none placeholder:text-[#aaa] dark:placeholder:text-gray-500"
          disabled={loading}
        />
        {command && !loading && (
          <button onClick={handleClear} className="cursor-pointer p-0.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
            <X className="size-3.5 text-[#888] dark:text-gray-400" />
          </button>
        )}
        <Button
          onClick={handleSubmit}
          disabled={loading || !command.trim()}
          size="sm"
          className="bg-purple-500 hover:bg-purple-600 text-white cursor-pointer text-[12px] gap-1.5 h-7 px-3"
        >
          {loading ? (
            <>
              <Loader2 className="size-3.5 animate-spin" />
              Interpreting...
            </>
          ) : (
            <>
              <Sparkles className="size-3.5" />
              Interpret
            </>
          )}
        </Button>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex items-center gap-2 px-4 py-3 bg-purple-50/50 dark:bg-purple-900/10">
          <Loader2 className="size-4 text-purple-500 animate-spin" />
          <span className="text-[12px] text-[#888] dark:text-gray-400 font-['Manrope']">AI is interpreting your command...</span>
        </div>
      )}

      {/* Error state */}
      {apiError && !loading && (
        <div className="flex items-start gap-2 px-4 py-3 bg-red-50 dark:bg-red-900/15 border-t border-red-100 dark:border-red-800/40">
          <AlertTriangle className="size-4 text-red-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-[12px] text-red-700 dark:text-red-400 font-['Manrope']">{apiError}</p>
          </div>
          <Button
            onClick={handleSubmit}
            variant="outline"
            size="sm"
            className="text-[10px] h-6 border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 cursor-pointer px-2"
          >
            Retry
          </Button>
        </div>
      )}

      {/* Interpretation Results */}
      {interpretation && !loading && !apiError && (
        <div className="px-4 py-3 bg-purple-50/50 dark:bg-purple-900/10 border-t border-purple-100 dark:border-purple-800/30 space-y-2.5">
          {/* Understanding */}
          <div className="flex items-start gap-2">
            <Sparkles className="size-3.5 text-purple-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-[12px] text-[#333] dark:text-gray-100 font-['Manrope'] font-medium">
                {interpretation.understood ? '✅ Understood' : '⚠️ Partially understood'}
              </p>
              <p className="text-[12px] text-[#666] dark:text-gray-300 font-['Manrope'] mt-0.5">{interpretation.explanation}</p>
            </div>
          </div>

          {/* Details row */}
          <div className="flex items-center gap-2 flex-wrap ml-5">
            <Badge variant="secondary" className="text-[10px] gap-1">
              <Terminal className="size-2.5" />
              {runTypeLabels[interpretation.runType] || interpretation.runType}
            </Badge>
            {interpretation.modules && interpretation.modules.length > 0 && (
              <Badge variant="secondary" className="text-[10px]">
                📦 {interpretation.modules.join(', ')}
              </Badge>
            )}
            {interpretation.priority && (
              <Badge variant="secondary" className="text-[10px]">
                🔥 {interpretation.priority}
              </Badge>
            )}
            <Badge variant="outline" className="text-[10px] text-purple-600 dark:text-purple-400 border-purple-200 dark:border-purple-700">
              {interpretation.testIds.length} test(s) selected
            </Badge>
          </div>

          {/* Execute button */}
          <div className="flex items-center gap-2 ml-5 pt-1">
            <Button
              onClick={handleExecute}
              disabled={interpretation.testIds.length === 0}
              size="sm"
              className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white cursor-pointer text-[12px] gap-1.5 h-7 px-4"
            >
              <Play className="size-3" />
              Execute Selection
            </Button>
            <Button
              onClick={handleClear}
              variant="ghost"
              size="sm"
              className="cursor-pointer text-[12px] text-[#888] dark:text-gray-400 h-7 px-3"
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
