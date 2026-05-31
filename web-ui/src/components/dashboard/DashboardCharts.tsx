'use client'

import { useMemo } from 'react'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import type { ModuleHealth, RunSnapshot } from '@/lib/types'

// ─── ERP Color Palette ─────────────────────────────────────
const COLORS = {
  primary: '#3F51B5',
  primaryDark: '#2D3FC7',
  success: '#22C55E',
  successAlt: '#10B981',
  danger: '#EF4444',
  dangerAlt: '#F44336',
  warning: '#FF9800',
  chartBlue: '#6777EF',
  chartSlate: '#495584',
  yellow: '#EAB308',
}

const PIE_COLORS = [
  '#3F51B5',
  '#10B981',
  '#F44336',
  '#6777EF',
  '#495584',
  '#FF9800',
  '#E91E63',
  '#00BCD4',
]

// ─── Dark mode helpers ─────────────────────────────────────
function useChartColors() {
  // We check the document class at render time; recharts will re-render on theme change
  // if the parent triggers a re-render (e.g. via next-themes)
  const isDark =
    typeof document !== 'undefined' &&
    document.documentElement.classList.contains('dark')

  return {
    axisText: isDark ? '#9CA3AF' : '#888888',
    gridLine: isDark ? '#334155' : '#E2E8F0',
    tooltipBg: isDark ? '#1F2937' : '#FFFFFF',
    tooltipText: isDark ? '#F9FAFB' : '#111827',
    tooltipBorder: isDark ? '#374151' : '#E5E7EB',
    refLine: isDark ? '#6B7280' : '#9CA3AF',
  }
}

// ─── Date formatter ────────────────────────────────────────
function formatRunDate(dateStr: string): string {
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    const day = String(d.getDate()).padStart(2, '0')
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    ]
    return `${day} ${months[d.getMonth()]}`
  } catch {
    return dateStr
  }
}

// ─── Shared No Data component ──────────────────────────────
function NoData({ height }: { height: number }) {
  return (
    <div
      className="flex items-center justify-center text-muted-foreground text-xs"
      style={{ height }}
    >
      No data available
    </div>
  )
}

// ─── Custom Tooltip Wrapper ────────────────────────────────
function ChartTooltipWrapper({
  active,
  payload,
  label,
  children,
}: {
  active?: boolean
  payload?: Array<{ value?: number; name?: string; color?: string; payload?: Record<string, unknown> }>
  label?: string
  children: React.ReactNode
}) {
  const colors = useChartColors()
  if (!active || !payload?.length) return null
  return (
    <div
      style={{
        background: colors.tooltipBg,
        border: `1px solid ${colors.tooltipBorder}`,
        color: colors.tooltipText,
        borderRadius: 8,
        padding: '8px 12px',
        fontSize: 11,
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      }}
    >
      {children}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════
// Component 1: PassRateTrendChart
// ═══════════════════════════════════════════════════════════
export function PassRateTrendChart({ runHistory }: { runHistory: RunSnapshot[] }) {
  const colors = useChartColors()

  const data = useMemo(() => {
    if (!runHistory?.length) return []
    return runHistory.slice(-20).map((run) => ({
      date: formatRunDate(run.date),
      passRate: Math.round(run.rate),
      passed: run.passed,
      failed: run.failed,
      rawDate: run.date,
    }))
  }, [runHistory])

  if (!data.length) return <NoData height={220} />

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id="passRateGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.3} />
            <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={colors.gridLine}
          vertical={false}
        />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: colors.axisText }}
          axisLine={{ stroke: colors.gridLine }}
          tickLine={false}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fontSize: 11, fill: colors.axisText }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v: number) => `${v}%`}
        />
        <ReferenceLine
          y={80}
          stroke={colors.refLine}
          strokeDasharray="6 3"
          label={{
            value: 'Target',
            position: 'right',
            fontSize: 10,
            fill: colors.refLine,
          }}
        />
        <Tooltip
          content={({ active, payload, label }) => (
            <ChartTooltipWrapper active={active} payload={payload} label={label}>
              {payload && payload[0] && (
                <div>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
                  <div style={{ color: COLORS.primary }}>
                    Pass Rate: {(payload[0].value as number)?.toFixed(0)}%
                  </div>
                  <div style={{ color: COLORS.success }}>
                    Passed: {String(payload[0].payload?.passed ?? 0)}
                  </div>
                  <div style={{ color: COLORS.danger }}>
                    Failed: {String(payload[0].payload?.failed ?? 0)}
                  </div>
                </div>
              )}
            </ChartTooltipWrapper>
          )}
        />
        <Area
          type="monotone"
          dataKey="passRate"
          stroke={COLORS.primary}
          strokeWidth={2}
          fill="url(#passRateGradient)"
          isAnimationActive={true}
          animationDuration={800}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

// ═══════════════════════════════════════════════════════════
// Component 2: ModuleHealthBarChart
// ═══════════════════════════════════════════════════════════
export function ModuleHealthBarChart({ moduleHealth }: { moduleHealth: ModuleHealth[] }) {
  const colors = useChartColors()

  const data = useMemo(() => {
    if (!moduleHealth?.length) return []
    return [...moduleHealth]
      .sort((a, b) => b.totalTests - a.totalTests)
      .slice(0, 10)
      .map((m) => ({
        name: m.moduleName.length > 18 ? m.moduleName.slice(0, 16) + '…' : m.moduleName,
        fullName: m.moduleName,
        passRate: Math.round(m.passRate),
        totalTests: m.totalTests,
        fill:
          m.passRate >= 80
            ? COLORS.success
            : m.passRate >= 50
              ? COLORS.yellow
              : COLORS.danger,
      }))
  }, [moduleHealth])

  if (!data.length) return <NoData height={280} />

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 5, right: 20, left: 0, bottom: 0 }}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={colors.gridLine}
          horizontal={false}
        />
        <XAxis
          type="number"
          domain={[0, 100]}
          tick={{ fontSize: 11, fill: colors.axisText }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v: number) => `${v}%`}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fontSize: 11, fill: colors.axisText }}
          axisLine={false}
          tickLine={false}
          width={90}
        />
        <Tooltip
          content={({ active, payload }) => (
            <ChartTooltipWrapper active={active} payload={payload}>
              {payload && payload[0] && (
                <div>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>
                    {String(payload[0].payload?.fullName ?? '')}
                  </div>
                  <div>
                    Pass Rate:{' '}
                    <span style={{ color: String(payload[0].payload?.fill ?? '') }}>
                      {(payload[0].value as number)?.toFixed(0)}%
                    </span>
                  </div>
                  <div>Total Tests: {String(payload[0].payload?.totalTests ?? 0)}</div>
                </div>
              )}
            </ChartTooltipWrapper>
          )}
        />
        <Bar
          dataKey="passRate"
          radius={[0, 4, 4, 0]}
          isAnimationActive={true}
          animationDuration={800}
        >
          {data.map((entry, idx) => (
            <Cell key={idx} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ═══════════════════════════════════════════════════════════
// Component 3: BugDistributionPie
// ═══════════════════════════════════════════════════════════
export function BugDistributionPie({ moduleHealth }: { moduleHealth: ModuleHealth[] }) {
  const colors = useChartColors()

  const { data, totalFailed } = useMemo(() => {
    if (!moduleHealth?.length) return { data: [], totalFailed: 0 }
    const filtered = moduleHealth
      .filter((m) => m.failedTests > 0)
      .sort((a, b) => b.failedTests - a.failedTests)
    const total = filtered.reduce((s, m) => s + m.failedTests, 0)
    return {
      data: filtered.map((m) => ({
        name: m.moduleName.length > 16 ? m.moduleName.slice(0, 14) + '…' : m.moduleName,
        fullName: m.moduleName,
        value: m.failedTests,
        percent: total > 0 ? Math.round((m.failedTests / total) * 100) : 0,
      })),
      totalFailed: total,
    }
  }, [moduleHealth])

  if (!data.length) return <NoData height={220} />

  // Custom label renderer
  const renderCustomLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
  }: {
    cx?: number
    cy?: number
    midAngle?: number
    innerRadius?: number
    outerRadius?: number
    percent?: number
  }) => {
    if (!cx || !cy || !innerRadius || !outerRadius || !percent || percent < 5) return null
    const RADIAN = Math.PI / 180
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)
    return (
      <text
        x={x}
        y={y}
        fill="#fff"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={10}
        fontWeight={600}
      >
        {`${percent}%`}
      </text>
    )
  }

  return (
    <div style={{ position: 'relative', height: 220 }}>
      {/* Center label */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
          pointerEvents: 'none',
          zIndex: 1,
        }}
      >
        <div style={{ fontSize: 18, fontWeight: 700, color: colors.tooltipText }}>
          {totalFailed}
        </div>
        <div style={{ fontSize: 10, color: colors.axisText }}>Bugs</div>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={80}
            dataKey="value"
            labelLine={false}
            label={renderCustomLabel}
            isAnimationActive={true}
            animationDuration={800}
          >
            {data.map((_entry, idx) => (
              <Cell
                key={idx}
                fill={PIE_COLORS[idx % PIE_COLORS.length]}
                stroke="none"
              />
            ))}
          </Pie>
          <Tooltip
            content={({ active, payload }) => (
              <ChartTooltipWrapper active={active} payload={payload}>
                {payload && payload[0] && (
                  <div>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>
                      {String(payload[0].payload?.fullName ?? '')}
                    </div>
                    <div>Failed Tests: {String(payload[0].value ?? 0)}</div>
                    <div>
                      Percentage: {String(payload[0].payload?.percent ?? 0)}%
                    </div>
                  </div>
                )}
              </ChartTooltipWrapper>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════
// Component 4: TestExecutionTimeline
// ═══════════════════════════════════════════════════════════
export function TestExecutionTimeline({ runHistory }: { runHistory: RunSnapshot[] }) {
  const colors = useChartColors()

  const data = useMemo(() => {
    if (!runHistory?.length) return []
    return runHistory.slice(-20).map((run) => ({
      date: formatRunDate(run.date),
      passed: run.passed,
      failed: run.failed,
      total: run.total,
      passRate: Math.round(run.rate),
    }))
  }, [runHistory])

  if (!data.length) return <NoData height={220} />

  return (
    <ResponsiveContainer width="100%" height={220}>
      <ComposedChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={colors.gridLine}
          vertical={false}
        />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: colors.axisText }}
          axisLine={{ stroke: colors.gridLine }}
          tickLine={false}
        />
        <YAxis
          yAxisId="left"
          tick={{ fontSize: 11, fill: colors.axisText }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          domain={[0, 100]}
          tick={{ fontSize: 11, fill: colors.axisText }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v: number) => `${v}%`}
        />
        <Tooltip
          content={({ active, payload, label }) => (
            <ChartTooltipWrapper active={active} payload={payload} label={label}>
              {payload && payload.length > 0 && (
                <div>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
                  {payload.map((item, idx) => (
                    <div key={idx} style={{ color: item.color }}>
                      {item.name}: {item.name === 'passRate'
                        ? `${(item.value as number)?.toFixed(0)}%`
                        : String(item.value ?? 0)}
                    </div>
                  ))}
                </div>
              )}
            </ChartTooltipWrapper>
          )}
        />
        <Legend
          wrapperStyle={{ fontSize: 11 }}
          formatter={(value: string) => {
            const labels: Record<string, string> = {
              passed: 'Passed',
              failed: 'Failed',
              passRate: 'Pass Rate',
            }
            return (
              <span style={{ fontSize: 11, color: colors.axisText }}>
                {labels[value] ?? value}
              </span>
            )
          }}
        />
        <Bar
          yAxisId="left"
          dataKey="passed"
          stackId="tests"
          fill={COLORS.success}
          radius={[0, 0, 0, 0]}
          isAnimationActive={true}
          animationDuration={800}
        />
        <Bar
          yAxisId="left"
          dataKey="failed"
          stackId="tests"
          fill={COLORS.danger}
          radius={[2, 2, 0, 0]}
          isAnimationActive={true}
          animationDuration={800}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="passRate"
          stroke={COLORS.primary}
          strokeWidth={2}
          dot={{ r: 3, fill: COLORS.primary }}
          isAnimationActive={true}
          animationDuration={1000}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
