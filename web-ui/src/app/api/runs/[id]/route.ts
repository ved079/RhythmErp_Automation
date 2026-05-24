import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

// GET /api/runs/[id]
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params

    const run = await db.runHistory.findUnique({ where: { id } })
    if (!run) {
      return NextResponse.json({ error: 'Run not found' }, { status: 404 })
    }

    const mapped = {
      ...run,
      results: run.results ? JSON.parse(run.results) : null,
    }

    return NextResponse.json(mapped)
  } catch (error) {
    console.error('[RunHistory] GET [id] error:', error)
    return NextResponse.json({ error: 'Failed to fetch run' }, { status: 500 })
  }
}

// PATCH /api/runs/[id]
export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await req.json()

    const existing = await db.runHistory.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'Run not found' }, { status: 404 })
    }

    const updateData: Record<string, unknown> = {}

    if (body.passed !== undefined) updateData.passed = body.passed
    if (body.failed !== undefined) updateData.failed = body.failed
    if (body.total !== undefined) updateData.total = body.total
    if (body.duration !== undefined) updateData.duration = body.duration
    if (body.rate !== undefined) updateData.rate = body.rate
    if (body.results !== undefined) updateData.results = JSON.stringify(body.results)
    if (body.status !== undefined) updateData.status = body.status
    if (body.completedAt !== undefined) updateData.completedAt = new Date(body.completedAt)

    const updated = await db.runHistory.update({
      where: { id },
      data: updateData,
    })

    const mapped = {
      ...updated,
      results: updated.results ? JSON.parse(updated.results) : null,
    }

    return NextResponse.json(mapped)
  } catch (error) {
    console.error('[RunHistory] PATCH [id] error:', error)
    return NextResponse.json({ error: 'Failed to update run' }, { status: 500 })
  }
}