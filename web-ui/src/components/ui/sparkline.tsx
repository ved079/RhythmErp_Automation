'use client'

import React from 'react'

interface SparklineProps {
  data: number[]
  width?: number
  height?: number
  strokeColor?: string
  fillColor?: string
  strokeWidth?: number
  className?: string
}

/**
 * Lightweight SVG sparkline — no external deps.
 * Renders a smooth line + optional gradient fill.
 */
export function Sparkline({
  data,
  width = 80,
  height = 24,
  strokeColor = 'currentColor',
  fillColor,
  strokeWidth = 1.5,
  className = '',
}: SparklineProps) {
  if (!data || data.length < 2) return null

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1 // avoid division by zero

  const padding = strokeWidth + 1
  const chartWidth = width - padding * 2
  const chartHeight = height - padding * 2

  // Build points
  const points = data.map((val, i) => {
    const x = padding + (i / (data.length - 1)) * chartWidth
    const y = padding + chartHeight - ((val - min) / range) * chartHeight
    return { x, y }
  })

  // Smooth curve using catmull-rom → bezier approximation
  const pathD = points.length < 3
    ? `M${points[0].x},${points[0].y} L${points[1].x},${points[1].y}`
    : buildSmoothPath(points)

  // Fill path (close to bottom)
  const fillPathD = `${pathD} L${points[points.length - 1].x},${height - padding} L${points[0].x},${height - padding} Z`

  const gradientId = `sparkline-grad-${Math.random().toString(36).slice(2, 8)}`

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={`inline-block ${className}`}
      style={{ color: strokeColor }}
    >
      {fillColor && (
        <>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={fillColor} stopOpacity={0.3} />
              <stop offset="100%" stopColor={fillColor} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <path d={fillPathD} fill={`url(#${gradientId})`} />
        </>
      )}
      <path
        d={pathD}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* End dot */}
      <circle
        cx={points[points.length - 1].x}
        cy={points[points.length - 1].y}
        r={strokeWidth + 0.5}
        fill={strokeColor}
      />
    </svg>
  )
}

/**
 * Build a smooth SVG path using cubic bezier curves
 * (catmull-rom to bezier conversion)
 */
function buildSmoothPath(points: { x: number; y: number }[]): string {
  const tension = 0.3

  let d = `M${points[0].x},${points[0].y}`

  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[Math.max(i - 1, 0)]
    const p1 = points[i]
    const p2 = points[i + 1]
    const p3 = points[Math.min(i + 2, points.length - 1)]

    const cp1x = p1.x + (p2.x - p0.x) * tension
    const cp1y = p1.y + (p2.y - p0.y) * tension
    const cp2x = p2.x - (p3.x - p1.x) * tension
    const cp2y = p2.y - (p3.y - p1.y) * tension

    d += ` C${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`
  }

  return d
}

/**
 * Get sparkline color based on trend direction
 */
export function getSparklineColor(current: number, previous?: number): { stroke: string; fill: string } {
  if (previous === undefined) {
    return { stroke: 'currentColor', fill: 'currentColor' }
  }
  if (current >= previous) {
    return { stroke: '#22c55e', fill: '#22c55e' } // green-500
  }
  return { stroke: '#ef4444', fill: '#ef4444' } // red-500
}

/**
 * Get a tiny trend arrow indicator
 */
export function TrendIndicator({ data }: { data: number[] }) {
  if (!data || data.length < 2) return null

  const latest = data[data.length - 1]
  const previous = data[data.length - 2]
  const diff = latest - previous

  if (diff === 0) {
    return <span className="text-[10px] text-gray-400">→ 0</span>
  }

  const isUp = diff > 0
  return (
    <span className={`text-[10px] font-medium ${isUp ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
      {isUp ? '↑' : '↓'} {Math.abs(diff)}%
    </span>
  )
}
