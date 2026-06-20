// ─── /api/runs/callback ──────────────────────────────────────
// POST — Receive run completion callback from FastAPI.
// This is a server-to-server endpoint authenticated via PROXY_API_KEY.
// It ensures run results are persisted even if the user navigated away
// from the SSE stream during a test run.

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

// C4: No hardcoded fallback — must be set via environment variable
const PROXY_API_KEY = process.env.PROXY_API_KEY || ''
// C4: Warn if PROXY_API_KEY is not set — required for production
if (!process.env.PROXY_API_KEY && process.env.NODE_ENV === 'production') {
  console.error('[SECURITY] PROXY_API_KEY is not set! Callback authentication is disabled.')
}

interface RunCallbackPayload {
  run_id: string
  module: string
  sub_module: string | null
  passed: number
  failed: number
  skipped: number
  total: number
  duration_seconds: number
  status: string
  results: Array<{
    name: string
    status: string
    duration: number
    message?: string
    traceback?: string
    screenshot?: string
  }>
  started_at: string | null
  completed_at: string | null
}

export async function POST(req: NextRequest) {
  // Verify this is from the trusted FastAPI backend
  const apiKey = req.headers.get('X-Proxy-API-Key')
  if (apiKey !== PROXY_API_KEY) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const payload: RunCallbackPayload = await req.json()

    if (!payload.run_id || !payload.module) {
      return NextResponse.json({ error: 'Missing required fields: run_id, module' }, { status: 400 })
    }

    // Build module name for display — convert folder name to sidebar ID
    const folderName = payload.sub_module || payload.module
    const dbModule = await db.testModule.findFirst({ where: { folderName }, select: { name: true } })
    const moduleId = dbModule?.name?.toLowerCase().replace(/_/g, '-') ?? folderName.toLowerCase().replace(/_/g, '-')
    const moduleName = payload.sub_module
      ? payload.sub_module.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
      : payload.module.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())

    // Format duration
    const durationMs = payload.duration_seconds * 1000
    const durationStr = durationMs > 0
      ? `${Math.floor(durationMs / 60000)}m ${Math.floor((durationMs % 60000) / 1000)}s`
      : '—'

    const rate = payload.total > 0 ? Math.round((payload.passed / payload.total) * 10000) / 100 : 0

    // Map results to the format expected by RunHistory
    const mappedResults = payload.results.map(r => ({
      testId: r.name,
      status: r.status,
      message: r.message || undefined,
      duration: r.duration || undefined,
    }))

    // Check if a run with this FastAPI run_id already exists
    // We use the moduleId + startedAt as a uniqueness check to avoid duplicates
    const existingRuns = await db.runHistory.findMany({
      where: {
        moduleId,
        startedAt: payload.started_at ? new Date(payload.started_at) : undefined,
      },
      take: 5,
      orderBy: { startedAt: 'desc' },
    })

    // If we find a matching run from the same run_id (stored in results), update it
    let existingRun = existingRuns.find(r => {
      try {
        const results = r.results ? JSON.parse(r.results) : []
        return results.some((res: { testId: string }) => {
          // Match by checking if the first result's testId matches
          return mappedResults.length > 0 && res.testId === mappedResults[0]?.testId
        })
      } catch {
        return false
      }
    })

    if (existingRun) {
      // Update existing run
      const updated = await db.runHistory.update({
        where: { id: existingRun.id },
        data: {
          passed: payload.passed,
          failed: payload.failed,
          total: payload.total,
          duration: durationStr,
          rate,
          results: JSON.stringify(mappedResults),
          status: payload.status === 'stopped' ? 'stopped' : (payload.failed > 0 ? 'failed' : 'completed'),
          completedAt: payload.completed_at ? new Date(payload.completed_at) : new Date(),
        },
      })

      return NextResponse.json({
        action: 'updated',
        id: updated.id,
        status: updated.status,
      })
    }

    // Create new run history entry
    const run = await db.runHistory.create({
      data: {
        moduleId,
        moduleName,
        passed: payload.passed,
        failed: payload.failed,
        total: payload.total,
        duration: durationStr,
        rate,
        results: JSON.stringify(mappedResults),
        status: payload.status === 'stopped' ? 'stopped' : (payload.failed > 0 ? 'failed' : 'completed'),
        startedAt: payload.started_at ? new Date(payload.started_at) : new Date(),
        completedAt: payload.completed_at ? new Date(payload.completed_at) : new Date(),
        createdBy: 'fastapi-callback',
      },
    })

    // Emit WebSocket event for real-time notification
    try {
      await fetch('http://localhost:3003/emit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event: 'run_complete',
          data: {
            runId: run.id,
            moduleName,
            passed: payload.passed,
            failed: payload.failed,
            total: payload.total,
            duration: durationStr,
            rate,
          },
        }),
      })
    } catch {}

    return NextResponse.json({
      action: 'created',
      id: run.id,
      status: run.status,
    }, { status: 201 })
  } catch (error) {
    console.error('[RunCallback] POST error:', error)
    return NextResponse.json({ error: 'Failed to process run callback' }, { status: 500 })
  }
}
