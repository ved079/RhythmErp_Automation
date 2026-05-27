import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

// PATCH /api/schedules/[id] — update a scheduled run
export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await req.json()

    const existing = await db.scheduledRun.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'Scheduled run not found' }, { status: 404 })
    }

    const updateData: Record<string, unknown> = {}

    if (body.frequency !== undefined) {
      const freqMap: Record<string, string> = {
        'one-time': 'one_time',
        'one_time': 'one_time',
        'daily': 'daily',
        'weekly': 'weekly',
      }
      updateData.frequency = freqMap[body.frequency] || 'one_time'
    }

    if (body.scheduledTime !== undefined) {
      updateData.scheduledTime = new Date(body.scheduledTime)
    }

    if (body.testSelection !== undefined) {
      updateData.testSelection = body.testSelection
    }

    if (body.selectedTestIds !== undefined) {
      updateData.selectedTestIds = JSON.stringify(body.selectedTestIds)
    }

    if (body.enabled !== undefined) {
      updateData.enabled = body.enabled
    }

    if (body.lastRunAt !== undefined) {
      updateData.lastRunAt = new Date(body.lastRunAt)
    }

    const updated = await db.scheduledRun.update({
      where: { id },
      data: updateData,
    })

    const mapped = {
      ...updated,
      frequency: updated.frequency === 'one_time' ? 'one-time' : updated.frequency,
      selectedTestIds: updated.selectedTestIds ? JSON.parse(updated.selectedTestIds) : undefined,
    }

    return NextResponse.json(mapped)
  } catch (error) {
    console.error('[Schedule] PATCH error:', error)
    return NextResponse.json({ error: 'Failed to update scheduled run' }, { status: 500 })
  }
}

// DELETE /api/schedules/[id] — delete a scheduled run
export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params

    const existing = await db.scheduledRun.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'Scheduled run not found' }, { status: 404 })
    }

    await db.scheduledRun.delete({ where: { id } })

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('[Schedule] DELETE error:', error)
    return NextResponse.json({ error: 'Failed to delete scheduled run' }, { status: 500 })
  }
}
