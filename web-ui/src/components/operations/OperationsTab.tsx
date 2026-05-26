import React from 'react';

export default function OperationsTab({ testGroups, testCasesModule }: { testGroups: TestClassGroup[]; testCasesModule?: { label: string; tests: any[] } }) {
  const testSpecGroups = testGroups
  const [searchVal, setSearchVal] = useState('')
  const [filter, setFilter] = useState<'all' | 'passed' | 'failed' | 'bug' | 'not-run'>('all')
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())
    // Auto-expand all groups when testSpecGroups changes
  useEffect(() => {
    if (testSpecGroups.length > 0) {
      setExpandedGroups(new Set(testSpecGroups.map((g) => g.className)))
    }
  }, [testSpecGroups])
  const [expandedTests, setExpandedTests] = useState<Set<string>>(new Set())

  const toggleGroup = useCallback((name: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }, [])

  const toggleTest = useCallback((id: string) => {
    setExpandedTests((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const filteredGroups = useMemo(() =>
    testSpecGroups
      .map((group) => {
        const filteredTests = group.tests.filter((test) => {
          const matchSearch =
            searchVal === '' ||
            test.id.toLowerCase().includes(searchVal.toLowerCase()) ||
            test.description.toLowerCase().includes(searchVal.toLowerCase()) ||
            test.steps.toLowerCase().includes(searchVal.toLowerCase()) ||
            test.expected.toLowerCase().includes(searchVal.toLowerCase())
          const matchFilter =
            filter === 'all' ||
            (filter === 'passed' && test.status === 'passed') ||
            (filter === 'failed' && test.status === 'failed') ||
            (filter === 'bug' && test.status === 'not-run' && !!test.error) ||
            (filter === 'not-run' && test.status === 'not-run' && !test.error)
          return matchSearch && matchFilter
        })
        return { ...group, tests: filteredTests, filteredTestCount: filteredTests.length }
      })
      .filter((g) => g.filteredTestCount > 0),
  [searchVal, filter, testSpecGroups])

  const totalTests = testSpecGroups.reduce((acc, g) => acc + g.tests.length, 0)
  const bugCount = testSpecGroups.reduce(
    (acc, g) => acc + g.tests.filter((t) => !!t.error).length,
    0
  )

  const getStatusDisplay = (test: TestSpecItem) => {
    if (test.error) {
      return { label: 'BUG', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400', icon: '\u{1F41B}' }
    }
    if (test.status === 'passed') {
      return { label: 'PASS', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400', icon: '\u2705' }
    }
    if (test.status === 'failed') {
      return { label: 'FAIL', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400', icon: '\u274C' }
    }
    return { label: '\u2014', color: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400', icon: '\u2014' }
  }

  const findTestCase = (testId: string) => testCasesModule?.tests.find((tc: any) => tc.id === testId)

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
              const allData = (window as any).__ALL_TEST_CASES__
              if (!allData) return
              import('xlsx').then((XLSX) => {
                const wb = XLSX.utils.book_new()
                for (const [key, val] of Object.entries(allData)) {
                  const mod = val as { label: string; tests: any[] }
                  const rows = mod.tests.map((t) => ({
                    '#': t.id,
                    'Description': t.description,
                    'Steps': t.steps,
                    'Expected Result': t.expected,
                    'Actual Result': t.actual,
                    'Status': t.status,
                    'Date': t.date,
                  }))
                  const ws = XLSX.utils.json_to_sheet(rows)
                  XLSX.utils.book_append_sheet(wb, ws, mod.label.substring(0, 31))
                }
                XLSX.writeFile(wb, 'RhythmERP_Test_Specifications.xlsx')
              }).catch(() => {
                alert('xlsx library not installed. Run: npm install xlsx')
              })
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
        <div className="flex items-center gap-3 text-[12px]">
          <span className="text-gray-500 dark:text-gray-400">{totalTests} tests</span>
          {bugCount > 0 && (
            <span className="text-red-500 dark:text-red-400 font-medium">{'\u{1F41B}'} {bugCount} bugs</span>
          )}
        </div>
      </div>

      <ScrollArea className="flex-1 min-h-0">
        <div className="p-4 space-y-2">
          {filteredGroups.map((group) => {
            const bugs = group.tests.filter((t) => !!t.error).length
            const bugsOnly = bugs === group.tests.length && bugs > 0
            const hasBugs = bugs > 0
            const noBugs = bugs === 0 && group.tests.length > 0

            const groupBorderColor = bugsOnly
              ? 'border-red-200 dark:border-red-800'
              : hasBugs
                ? 'border-orange-200 dark:border-orange-800'
                : 'border-gray-200 dark:border-gray-700'

            return (
              <div key={group.className} className={`border rounded-lg overflow-hidden ${groupBorderColor}`}>
                <button
                  onClick={() => toggleGroup(group.className)}
                  className="w-full flex items-center gap-3 px-4 py-3 hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors cursor-pointer"
                >
                  <ChevronRight
                    className={`size-4 text-gray-400 dark:text-gray-500 shrink-0 transition-transform duration-200 ${
                      expandedGroups.has(group.className) ? 'rotate-90' : ''
                    }`}
                  />
                  <span className="text-[13px] font-semibold text-gray-800 dark:text-gray-100 flex-1 text-left">
                    {group.className}
                  </span>
                  <span className="text-[12px] text-gray-500 dark:text-gray-400">
                    {group.tests.length} test{group.tests.length !== 1 ? 's' : ''}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {noBugs && (
                      <span className="inline-flex items-center gap-0.5 text-[11px] text-green-700 dark:text-green-400 bg-green-100 dark:bg-green-900/30 px-1.5 py-0.5 rounded-full font-medium">
                        {'\u2705'} All Clear
                      </span>
                    )}
                    {hasBugs && (
                      <span className="inline-flex items-center gap-0.5 text-[11px] text-red-700 dark:text-red-400 bg-red-100 dark:bg-red-900/30 px-1.5 py-0.5 rounded-full font-medium">
                        {'\u{1F41B}'} {bugs}
                      </span>
                    )}
                  </div>
                </button>

                {expandedGroups.has(group.className) && (
                  <div className="border-t border-gray-100 dark:border-gray-700">
                    {group.tests.map((test, idx) => {
                      const isLast = idx === group.tests.length - 1
                      const isExpanded = expandedTests.has(test.id)
                      const statusInfo = getStatusDisplay(test)
                      const tc = findTestCase(test.id)

                      return (
                        <div key={test.id}>
                          <button
                            onClick={() => toggleTest(test.id)}
                            className={`w-full flex items-center gap-3 px-4 py-2.5 pl-10 hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors cursor-pointer ${
                              !isLast ? 'border-b border-gray-50 dark:border-gray-800' : ''
                            }`}
                          >
                            {isExpanded ? (
                              <ChevronDown className="size-3 text-gray-400 dark:text-gray-500 shrink-0" />
                            ) : (
                              <ChevronRight className="size-3 text-gray-400 dark:text-gray-500 shrink-0" />
                            )}

                            <span className="text-[12px] text-gray-700 dark:text-gray-200 flex-1 text-left">
                              {test.description}
                            </span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${statusInfo.color}`}>
                              {statusInfo.icon} {statusInfo.label}
                            </span>
                          </button>

                          {isExpanded && (
                            <div className="px-10 pb-3 pl-[72px] pr-4 border-b border-gray-50 dark:border-gray-800 bg-gray-50/30 dark:bg-gray-800/20">
                              <div className="space-y-2 py-2">
                                {test.steps && (
                                  <div>
                                    <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Steps:</span>
                                    <p className="text-[12px] text-gray-600 dark:text-gray-300 mt-0.5 leading-5 whitespace-pre-line">{test.steps}</p>
                                  </div>
                                )}
                                <div>
                                  <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Expected:</span>
                                  <p className="text-[12px] text-gray-600 dark:text-gray-300 mt-0.5 leading-5">{test.expected}</p>
                                </div>
                                <div>
                                  <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actual:</span>
                                  <p className="text-[12px] text-gray-600 dark:text-gray-300 mt-0.5 leading-5">{tc?.actual || test.actual || '\u2014'}</p>
                                </div>
                                <div className="flex items-center gap-4">
                                  <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status:</span>
                                  <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${statusInfo.color}`}>
                                    {statusInfo.icon} {statusInfo.label}
                                  </span>
                                  {tc?.date && (
                                    <>
                                      <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider ml-2">Date:</span>
                                      <span className="text-[11px] text-gray-600 dark:text-gray-400">{tc.date}</span>
                                    </>
                                  )}
                                </div>
                                {test.error && (
                                  <div className="mt-1">
                                    <span className="text-[11px] font-semibold text-red-500 dark:text-red-400 uppercase tracking-wider">Bug Details:</span>
                                    <p className="text-[12px] text-red-600 dark:text-red-400 mt-0.5 leading-5 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">
                                      {test.actual}
                                    </p>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}

          {filteredGroups.length === 0 && (
            <div className="text-center py-12 text-gray-400 dark:text-gray-500">
              <Search className="size-8 mx-auto mb-2 opacity-50" />
              <p className="text-[13px]">No tests match your search criteria</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
