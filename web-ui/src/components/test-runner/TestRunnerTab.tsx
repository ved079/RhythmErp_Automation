'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Play, RotateCcw, Flame, Activity, ShieldCheck, CheckCircle2, XCircle, Circle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { TestItem, TestPriority } from '@/types/dashboard';

interface TestRunnerTabProps {
  tests: TestItem[];
  testChecks: Set<string>;
  toggleTestCheck: (id: string) => void;
  isRunning: boolean;
  onRun: (selectedOnly: boolean) => void;
  onRunByPriority: (priority: TestPriority) => void;
  totalFailed: number;
  onRerunFailed: () => void;
}

const priorityConfig = {
  smoke: { color: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400' },
  regression: { color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' },
  sanity: { color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400' },
};

export function TestRunnerTab({
  tests,
  testChecks,
  toggleTestCheck,
  isRunning,
  onRun,
  onRunByPriority,
  totalFailed,
  onRerunFailed,
}: TestRunnerTabProps) {
  const pendingOrRunning = tests.filter((t) => t.status === 'pending' || t.status === 'running');
  const allSelected = pendingOrRunning.length > 0 && pendingOrRunning.every((t) => testChecks.has(t.id));

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      pendingOrRunning.forEach((t) => { if (testChecks.has(t.id)) toggleTestCheck(t.id); });
    } else {
      pendingOrRunning.forEach((t) => { if (!testChecks.has(t.id)) toggleTestCheck(t.id); });
    }
  }, [allSelected, pendingOrRunning, testChecks, toggleTestCheck]);

  const passedCount = tests.filter((t) => t.status === 'passed').length;
  const failedCount = tests.filter((t) => t.status === 'failed').length;
  const pendingCount = tests.filter((t) => t.status === 'pending').length;
  const selectedRunnable = tests.filter((t) => t.status === 'pending' && testChecks.has(t.id)).length;
  const smokeCount = tests.filter((t) => t.priority === 'smoke' && (t.status === 'pending' || t.status === 'running')).length;
  const regressionCount = tests.filter((t) => t.priority === 'regression' && (t.status === 'pending' || t.status === 'running')).length;

  // Group tests by class
  const testGroups: { name: string; tests: TestItem[] }[] = [];
  let currentGroup: string | null = null;
  for (const t of tests) {
    const cls = t.id.replace(/\d+$/, '').replace(/T/, 'Test');
    if (cls !== currentGroup) {
      currentGroup = cls;
      testGroups.push({ name: cls, tests: [] });
    }
    testGroups[testGroups.length - 1].tests.push(t);
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Action Bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-gray-700 shrink-0 flex-wrap">
        <Button
          onClick={() => onRun(false)}
          disabled={isRunning || pendingCount === 0}
          className="bg-green-600 hover:bg-green-700 text-white h-9 text-[13px] gap-2 px-5 cursor-pointer"
        >
          <Play className="size-4" />
          Run All ({pendingCount})
        </Button>
        <Button
          onClick={() => onRun(true)}
          disabled={isRunning || selectedRunnable === 0}
          className="bg-[#1976d2] hover:bg-[#1565c0] text-white h-9 text-[13px] gap-2 px-5 cursor-pointer"
        >
          <Play className="size-4" />
          Run Selected ({selectedRunnable})
        </Button>
        <Button
          onClick={handleSelectAll}
          disabled={isRunning}
          variant="outline"
          className="border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 h-9 text-[13px] gap-2 px-4 cursor-pointer"
        >
          {allSelected ? '✖ Deselect All' : '☑ Select All'}
          <span className="text-[11px] opacity-60">({selectedRunnable}/{pendingCount})</span>
        </Button>
        <Button
          onClick={() => onRunByPriority('smoke')}
          disabled={isRunning || smokeCount === 0}
          className="bg-orange-500 hover:bg-orange-600 text-white h-9 text-[13px] gap-2 px-4 cursor-pointer"
        >
          <Flame className="size-3.5" />
          Run Smoke ({smokeCount})
        </Button>
        <Button
          onClick={() => onRunByPriority('regression')}
          disabled={isRunning || regressionCount === 0}
          className="bg-blue-500 hover:bg-blue-600 text-white h-9 text-[13px] gap-2 px-4 cursor-pointer"
        >
          <Activity className="size-3.5" />
          Run Regression ({regressionCount})
        </Button>
        {totalFailed > 0 && (
          <Button
            onClick={onRerunFailed}
            disabled={isRunning}
            variant="outline"
            className="border-orange-300 dark:border-orange-700 text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20 hover:text-orange-700 h-9 text-[13px] gap-2 px-4 cursor-pointer"
          >
            <RotateCcw className="size-3.5" />
            Rerun Failed ({totalFailed})
          </Button>
        )}

        <div className="flex-1" />
        <div className="flex items-center gap-4 text-[12px]">
          <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
            <CheckCircle2 className="size-3.5" /> {passedCount} passed
          </span>
          <span className="flex items-center gap-1 text-red-500 dark:text-red-400">
            <XCircle className="size-3.5" /> {failedCount} failed
          </span>
          <span className="flex items-center gap-1 text-gray-400 dark:text-gray-500">
            <Circle className="size-3" /> {pendingCount} pending
          </span>
        </div>
      </div>

      {/* Priority filter pills */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-100 dark:border-gray-700 shrink-0 bg-gray-50/30 dark:bg-gray-800/20">
        <span className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">Priority:</span>
        <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${priorityConfig.smoke.color}`}>
          <Flame className="size-2.5" /> Smoke: {tests.filter(t => t.priority === 'smoke').length}
        </span>
        <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${priorityConfig.regression.color}`}>
          <Activity className="size-2.5" /> Regression: {tests.filter(t => t.priority === 'regression').length}
        </span>
        <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${priorityConfig.sanity.color}`}>
          <ShieldCheck className="size-2.5" /> Sanity: {tests.filter(t => t.priority === 'sanity').length}
        </span>
      </div>

      {/* Test List by Groups */}
      <ScrollArea className="flex-1 min-h-0">
        <div className="px-4 py-3 space-y-3">
          {testGroups.map((group) => {
            const groupPassed = group.tests.filter((t) => t.status === 'passed').length;
            const groupFailed = group.tests.filter((t) => t.status === 'failed').length;
            const groupPending = group.tests.filter((t) => t.status === 'pending').length;
            const groupAllSelected = group.tests.every((t) => testChecks.has(t.id) || t.status !== 'pending');
            const groupSomeSelected = group.tests.some((t) => testChecks.has(t.id));

            return (
              <div key={group.name} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                {/* Group Header */}
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
                  <Checkbox
                    checked={groupAllSelected}
                    indeterminate={groupSomeSelected && !groupAllSelected}
                    onCheckedChange={() => {
                      group.tests.forEach((t) => {
                        if (t.status === 'pending') {
                          if (groupAllSelected && testChecks.has(t.id)) {
                            toggleTestCheck(t.id);
                          } else if (!groupAllSelected && !testChecks.has(t.id)) {
                            toggleTestCheck(t.id);
                          }
                        }
                      });
                    }}
                    className="size-4 cursor-pointer"
                  />
                  <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200">{group.name}</span>
                  <div className="flex-1" />
                  <span className="text-[11px] text-green-600 dark:text-green-400">{groupPassed} ✅</span>
                  <span className="text-[11px] text-red-500 dark:text-red-400 ml-2">{groupFailed} ❌</span>
                  <span className="text-[11px] text-gray-400 dark:text-gray-500 ml-2">{groupPending} ⏳</span>
                </div>

                {/* Tests */}
                <div className="divide-y divide-gray-100 dark:divide-gray-700">
                  {group.tests.map((test) => (
                    <div
                      key={test.id}
                      className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800/30"
                    >
                      {test.status === 'pending' && (
                        <Checkbox
                          checked={testChecks.has(test.id)}
                          onCheckedChange={() => toggleTestCheck(test.id)}
                          className="size-4 cursor-pointer"
                        />
                      )}
                      <span className="text-[11px] font-mono text-gray-500 dark:text-gray-400 w-16">{test.id}</span>
                      <div className="flex-1 min-w-0">
                        <div className="text-[13px] text-gray-700 dark:text-gray-200 truncate">{test.description}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${priorityConfig[test.priority].color}`}>
                          {test.priority}
                        </span>
                        {test.status === 'passed' && (
                          <span className="text-[11px] text-green-600 dark:text-green-400">✅</span>
                        )}
                        {test.status === 'failed' && (
                          <span className="text-[11px] text-red-500 dark:text-red-400">❌</span>
                        )}
                        {test.status === 'running' && (
                          <span className="text-[11px] text-blue-500 dark:text-blue-400 animate-pulse">🔄</span>
                        )}
                        {test.status === 'pending' && (
                          <span className="text-[11px] text-gray-400">⏳</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
