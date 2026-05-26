'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Search, FileSpreadsheet } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import type { TestClassGroup, TestSpecItem } from '@/types/dashboard';

interface OperationsTabProps {
  testGroups: TestClassGroup[];
  testCasesModule?: { label: string; tests: any[] };
}

export function OperationsTab({ testGroups, testCasesModule }: OperationsTabProps) {
  const testSpecGroups = testGroups;
  const [searchVal, setSearchVal] = useState('');
  const [filter, setFilter] = useState<'all' | 'passed' | 'failed' | 'bug' | 'not-run'>('all');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [expandedTests, setExpandedTests] = useState<Set<string>>(new Set());

  // Auto-expand all groups when testSpecGroups changes
  useEffect(() => {
    if (testSpecGroups.length > 0) {
      setExpandedGroups(new Set(testSpecGroups.map((g) => g.className)));
    }
  }, [testSpecGroups]);

  const toggleGroup = useCallback((name: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }, []);

  const toggleTest = useCallback((id: string) => {
    setExpandedTests((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const filteredGroups = useMemo(() =>
    testSpecGroups
      .map((group) => {
        const filteredTests = group.tests.filter((test) => {
          const matchSearch =
            searchVal === '' ||
            test.id.toLowerCase().includes(searchVal.toLowerCase()) ||
            test.description.toLowerCase().includes(searchVal.toLowerCase()) ||
            test.steps.toLowerCase().includes(searchVal.toLowerCase()) ||
            test.expected.toLowerCase().includes(searchVal.toLowerCase());
          const matchFilter =
            filter === 'all' ||
            (filter === 'passed' && test.status === 'passed') ||
            (filter === 'failed' && test.status === 'failed') ||
            (filter === 'bug' && test.status === 'not-run' && !!test.error) ||
            (filter === 'not-run' && test.status === 'not-run' && !test.error);
          return matchSearch && matchFilter;
        });
        return { ...group, tests: filteredTests, filteredTestCount: filteredTests.length };
      })
      .filter((g) => g.filteredTestCount > 0),
  [searchVal, filter, testSpecGroups]);

  const totalTests = testSpecGroups.reduce((acc, g) => acc + g.tests.length, 0);
  const bugCount = testSpecGroups.reduce(
    (acc, g) => acc + g.tests.filter((t) => !!t.error).length,
    0
  );

  const getStatusDisplay = (test: TestSpecItem) => {
    if (test.error) {
      return { label: 'BUG', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400', icon: '\u{1F41B}' };
    }
    if (test.status === 'passed') {
      return { label: 'PASS', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400', icon: '\u2705' };
    }
    if (test.status === 'failed') {
      return { label: 'FAIL', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400', icon: '\u274C' };
    }
    return { label: '—', color: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400', icon: '—' };
  };

  const findTestCase = (testId: string) => testCasesModule?.tests.find((tc: any) => tc.id === testId);

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-gray-700 shrink-0 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-gray-400" />
          <Input
            placeholder="Search tests..."
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            className="h-8 pl-8 text-[13px] bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600 text-gray-800 dark:text-gray-100"
          />
        </div>
        <Button
          variant="outline"
          className="h-8 text-[13px] gap-1.5 border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300"
          onClick={() => {
            if (typeof window !== 'undefined') {
              const allData = (window as any).__ALL_TEST_CASES__;
              if (!allData) return;
              import('xlsx').then((XLSX) => {
                const wb = XLSX.utils.book_new();
                for (const [key, val] of Object.entries(allData)) {
                  const mod = val as { label: string; tests: any[] };
                  const rows = mod.tests.map((t) => ({
                    '#': t.id,
                    'Description': t.description,
                    'Steps': t.steps,
                    'Expected Result': t.expected,
                    'Actual Result': t.actual,
                    'Status': t.status,
                    'Date': t.date,
                  }));
                  const ws = XLSX.utils.json_to_sheet(rows);
                  XLSX.utils.book_append_sheet(wb, ws, mod.label.substring(0, 31));
                }
                XLSX.writeFile(wb, 'RhythmERP_Test_Specifications.xlsx');
              }).catch(() => {
                alert('xlsx library not installed. Run: npm install xlsx');
              });
            }
          }}
        >
          <FileSpreadsheet className="size-3.5" />
          Export to Excel
        </Button>
        <Select value={filter} onValueChange={(v) => setFilter(v as typeof filter)}>
          <SelectTrigger className="h-8 w-28 text-[13px] bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="passed">Passed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="bug">Bug</SelectItem>
          </SelectContent>
        </Select>
        <div className="flex-1" />
        <Separator orientation="vertical" className="h-5 mx-1" />
        {bugCount > 0 && (
          <span className="text-red-500 dark:text-red-400 font-medium">{'\u{1F41B}'} {bugCount} bugs</span>
        )}
        <span className="text-[12px] text-gray-500 dark:text-gray-400">{totalTests} tests</span>
      </div>

      {/* Test Groups */}
      <ScrollArea className="flex-1 min-h-0">
        <div className="px-4 py-3 space-y-3">
          {filteredGroups.map((group) => {
            const isExpanded = expandedGroups.has(group.className);
            const groupPassed = group.tests.filter((t) => t.status === 'passed').length;
            const groupFailed = group.tests.filter((t) => t.status === 'failed').length;
            const groupBugs = group.tests.filter((t) => !!t.error).length;

            return (
              <div key={group.className} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                {/* Group Header */}
                <div
                  className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                  onClick={() => toggleGroup(group.className)}
                >
                  <span className="text-[11px] text-gray-400">{isExpanded ? '▼' : '▶'}</span>
                  <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200">{group.className}</span>
                  <div className="flex-1" />
                  <span className="text-[11px] text-green-600 dark:text-green-400">{groupPassed} ✅</span>
                  <span className="text-[11px] text-red-500 dark:text-red-400 ml-2">{groupFailed} ❌</span>
                  {groupBugs > 0 && (
                    <span className="text-[11px] text-orange-500 dark:text-orange-400 ml-2">{'\u{1F41B}'} {groupBugs}</span>
                  )}
                </div>

                {/* Tests */}
                {isExpanded && (
                  <div className="divide-y divide-gray-100 dark:divide-gray-700">
                    {group.tests.map((test) => {
                      const isTestExpanded = expandedTests.has(test.id);
                      const status = getStatusDisplay(test);
                      const testCase = findTestCase(test.id);

                      return (
                        <div key={test.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                          <div
                            className="flex items-start gap-2 px-3 py-2 cursor-pointer"
                            onClick={() => toggleTest(test.id)}
                          >
                            <span className="text-[10px] text-gray-400 mt-0.5">{isTestExpanded ? '▼' : '▶'}</span>
                            <span className="text-[11px] font-mono text-gray-500 dark:text-gray-400 mt-0.5">{test.id}</span>
                            <div className="flex-1 min-w-0">
                              <div className="text-[13px] text-gray-700 dark:text-gray-200 truncate">{test.description}</div>
                              <div className="flex items-center gap-2 mt-1">
                                <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${status.color}`}>
                                  {status.icon} {status.label}
                                </span>
                                {testCase && (
                                  <Badge variant="secondary" className="text-[9px] h-4">
                                    TC: {testCase.id}
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>

                          {isTestExpanded && (
                            <div className="px-3 pb-3 pl-8 space-y-2">
                              <div className="text-[12px]">
                                <span className="font-semibold text-gray-600 dark:text-gray-300">Steps: </span>
                                <span className="text-gray-700 dark:text-gray-200">{test.steps}</span>
                              </div>
                              <div className="text-[12px]">
                                <span className="font-semibold text-gray-600 dark:text-gray-300">Expected: </span>
                                <span className="text-gray-700 dark:text-gray-200">{test.expected}</span>
                              </div>
                              {test.actual && (
                                <div className="text-[12px]">
                                  <span className="font-semibold text-gray-600 dark:text-gray-300">Actual: </span>
                                  <span className="text-gray-700 dark:text-gray-200">{test.actual}</span>
                                </div>
                              )}
                              {test.error && (
                                <div className="text-[12px] text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
                                  <span className="font-semibold">Error: </span>{test.error}
                                </div>
                              )}
                              {test.date && (
                                <div className="text-[11px] text-gray-400">Run: {test.date}</div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
