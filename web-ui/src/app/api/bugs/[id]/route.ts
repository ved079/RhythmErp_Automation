import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateSession } from '@/lib/session'

type BugStatus = 'open' | 'in_progress' | 'fixed' | 'closed' | 'rejected'

// PATCH /api/bugs/[id] — update status, assignment, etc.
// C1: Now requires authentication
export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  // C1: Auth check
  const user = await validateSession(req)
  if (!user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  try {
    const { id } = await params
    const body = await req.json()

    const existing = await db.bugReport.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'Bug report not found' }, { status: 404 })
    }

    // Non-admin users can only update their own bugs
    if (user.role !== 'admin' && existing.userId !== user.id) {
      return NextResponse.json({ error: 'Not authorized' }, { status: 403 })
    }

    // Build update data
    const updateData: Record<string, unknown> = {}

    if (body.status !== undefined) {
      // Map client status to DB enum
      const statusMap: Record<string, BugStatus> = {
        'open': 'open',
        'in-progress': 'in_progress',
        'in_progress': 'in_progress',
        'fixed': 'fixed',
        'closed': 'closed',
        'rejected': 'rejected',
      }
      const dbStatus = statusMap[body.status]
      if (!dbStatus) {
        return NextResponse.json({ error: 'Invalid status' }, { status: 400 })
      }

      // If status changed, update readByUser to false
      if (existing.status !== dbStatus) {
        updateData.readByUser = false
      }
      updateData.status = dbStatus

      // Create notification on status change
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

    // Emit WebSocket event for status change
    if (body.status && existing.status !== updateData.status) {
      try {
        await fetch('http://localhost:3003/emit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            event: 'bug_status_change',
            data: {
              bugReportId: id,
              newStatus: body.status,
              changedBy: body.changedBy || 'system',
            },
          }),
        })
      } catch {}
    }

    return NextResponse.json(mapped)
  } catch (error) {
    console.error('[BugReport] PATCH error:', error)
    return NextResponse.json({ error: 'Failed to update bug report' }, { status: 500 })
  }
}
