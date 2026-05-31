import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateSession } from '@/lib/session'

// PATCH /api/bugs/[id]/read — mark as read by user or admin
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
    const { role } = body // 'user' or 'admin'

    const existing = await db.bugReport.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'Bug report not found' }, { status: 404 })
    }

    const updateData = role === 'admin' ? { readByAdmin: true } : { readByUser: true }

    await db.bugReport.update({
      where: { id },
      data: updateData,
    })

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('[BugReport Read] PATCH error:', error)
    return NextResponse.json({ error: 'Failed to mark as read' }, { status: 500 })
  }
}
