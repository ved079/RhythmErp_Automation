import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateSession } from '@/lib/session'

// POST /api/bugs/[id]/replies — add a reply to a bug report
// C1: Now requires authentication
export async function POST(
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
    const { authorName, authorRole, message } = body

    if (!authorName || !message) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    const existing = await db.bugReport.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'Bug report not found' }, { status: 404 })
    }

    // Non-admin users can only reply to their own bugs
    if (user.role !== 'admin' && existing.userId !== user.id) {
      return NextResponse.json({ error: 'Not authorized' }, { status: 403 })
    }

    const dbRole = authorRole === 'admin' ? 'admin' : 'user'

    const reply = await db.reply.create({
      data: {
        bugReportId: id,
        authorName,
        authorRole: dbRole,
        message,
      },
    })

    // Update read flags on the bug report
    const updateData: Record<string, unknown> = {}
    if (authorRole === 'admin') {
      updateData.readByUser = false
    } else {
      updateData.readByAdmin = false
    }

    await db.bugReport.update({
      where: { id },
      data: updateData,
    })

    // Create notification
    if (authorRole === 'admin') {
      await db.notification.create({
        data: {
          type: 'reply',
          title: 'Admin replied',
          message: `Admin replied to ${id}`,
          ticketId: id,
        },
      })
    } else {
      await db.notification.create({
        data: {
          type: 'reply',
          title: 'User followed up',
          message: `User replied to ${id}`,
          ticketId: id,
        },
      })
    }

    // Emit WebSocket event for real-time notification
    try {
      await fetch('http://localhost:3003/emit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event: 'bug_reply',
          data: {
            bugReportId: id,
            replyAuthor: authorName,
            message: message.substring(0, 200),
          },
        }),
      })
    } catch {}

    return NextResponse.json(reply, { status: 201 })
  } catch (error) {
    console.error('[BugReport Replies] POST error:', error)
    return NextResponse.json({ error: 'Failed to add reply' }, { status: 500 })
  }
}
