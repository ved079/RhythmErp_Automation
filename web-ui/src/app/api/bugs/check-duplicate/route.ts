import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateSession } from '@/lib/session'

export async function GET(req: NextRequest) {
  try {
    const user = await validateSession(req)
    if (!user) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }

    const { searchParams } = new URL(req.url)
    const testId = searchParams.get('testId')

    if (!testId) {
      return NextResponse.json({ error: 'testId query param required' }, { status: 400 })
    }

    const existing = await db.bugReport.findFirst({
      where: {
        testId,
        userId: user.id,
        status: { in: ['open', 'in_progress'] },
      },
      include: { replies: { orderBy: { createdAt: 'asc' } } },
    })

    if (existing) {
      const mapped = {
        ...existing,
        status: existing.status === 'in_progress' ? 'in-progress' : existing.status,
      }
      return NextResponse.json({ exists: true, bugReport: mapped })
    }

    return NextResponse.json({ exists: false })
  } catch (error) {
    console.error('[BugReport] check-duplicate error:', error)
    return NextResponse.json({ error: 'Failed to check duplicate' }, { status: 500 })
  }
}
