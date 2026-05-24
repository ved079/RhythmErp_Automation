import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

// PATCH /api/bugs/[id]/read
export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await req.json()
    const { role } = body

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