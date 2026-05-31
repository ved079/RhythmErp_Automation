// ─── /api/admin/audit-log ────────────────────────────────
// GET — List audit log entries with pagination

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin } from '@/lib/admin-helpers'

export async function GET(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const { searchParams } = new URL(req.url)
    const page = Math.max(1, parseInt(searchParams.get('page') || '1'))
    const perPage = Math.min(100, Math.max(1, parseInt(searchParams.get('perPage') || '25')))
    const action = searchParams.get('action') || undefined
    const targetType = searchParams.get('targetType') || undefined

    const where: Record<string, unknown> = {}
    if (action) where.action = action
    if (targetType) where.targetType = targetType

    const [entries, total] = await Promise.all([
      db.auditLog.findMany({
        where,
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * perPage,
        take: perPage,
      }),
      db.auditLog.count({ where }),
    ])

    const mapped = entries.map(e => ({
      id: e.id,
      userId: e.userId,
      userName: e.userName,
      action: e.action,
      targetType: e.targetType,
      targetId: e.targetId,
      targetLabel: e.targetLabel,
      details: e.details,
      createdAt: e.createdAt.toISOString(),
    }))

    return NextResponse.json({
      entries: mapped,
      pagination: {
        page,
        perPage,
        total,
        totalPages: Math.ceil(total / perPage),
      },
    })
  } catch (err) {
    console.error('List audit log error:', err)
    return NextResponse.json({ error: 'Failed to list audit log' }, { status: 500 })
  }
}
