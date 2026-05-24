import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

type BugStatus = 'open' | 'in_progress' | 'fixed'

// PATCH /api/bugs/[id]
export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await req.json()

    const existing = await db.bugReport.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'Bug report not found' }, { status: 404 })
    }

    const updateData: Record<string, unknown> = {}

    if (body.status !== undefined) {
      const statusMap: Record<string, BugStatus> = {
        'open': 'open',
        'in-progress': 'in_progress',
        'in_progress': 'in_progress',
        'fixed': 'fixed',
      }
      const dbStatus = statusMap[body.status]
      if (!dbStatus) {
        return NextResponse.json({ error: 'Invalid status' }, { status: 400 })
      }

      if (existing.status !== dbStatus) {
        updateData.readByUser = false
      }
      updateData.status = dbStatus

      if (existing.status !== dbStatus) {
        await db.notification.create({
          data: {
            type: 'status_change',
            title: 'Status updated',
            message: `${id} status changed to ${body.status}`,
            ticketId: id,
          },
        })
      }
    }

    if (body.assignedTo !== undefined) updateData.assignedTo = body.assignedTo
    if (body.assignedToName !== undefined) updateData.assignedToName = body.assignedToName
    if (body.readByUser !== undefined) updateData.readByUser = body.readByUser
    if (body.readByAdmin !== undefined) updateData.readByAdmin = body.readByAdmin

    const updated = await db.bugReport.update({
      where: { id },
      data: updateData,
      include: { replies: { orderBy: { createdAt: 'asc' } } },
    })

    const mapped = {
      ...updated,
      status: updated.status === 'in_progress' ? 'in-progress' : updated.status,
      replies: updated.replies.map((rep) => ({ ...rep })),
    }

    return NextResponse.json(mapped)
  } catch (error) {
    console.error('[BugReport] PATCH error:', error)
    return NextResponse.json({ error: 'Failed to update bug report' }, { status: 500 })
  }
}