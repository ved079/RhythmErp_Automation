import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

export async function POST(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const body = await req.json()
    const { updates } = body as { updates: { testName: string; displayName?: string | null; disabled?: boolean }[] }

    if (!Array.isArray(updates) || updates.length === 0) {
      return NextResponse.json({ error: 'updates array is required and must not be empty' }, { status: 400 })
    }

    const results = await db.$transaction(
      updates.map((u) =>
        db.testOverride.upsert({
          where: { testName: u.testName.trim() },
          update: {
            ...(u.displayName !== undefined ? { displayName: u.displayName || null } : {}),
            ...(u.disabled !== undefined ? { disabled: u.disabled } : {}),
          },
          create: {
            testName: u.testName.trim(),
            displayName: u.displayName ?? null,
            disabled: u.disabled ?? false,
          },
        })
      )
    )

    // Single audit log for the batch
    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'update',
      targetType: 'test_override',
      targetId: 'batch',
      targetLabel: `${results.length} overrides`,
      details: `Batch updated ${results.length} overrides: ${results.map(r => r.testName).join(', ')}`,
    })

    return NextResponse.json({
      updated: results.length,
      overrides: results.map(o => ({
        id: o.id,
        testName: o.testName,
        displayName: o.displayName,
        disabled: o.disabled,
        createdAt: o.createdAt.toISOString(),
        updatedAt: o.updatedAt.toISOString(),
      })),
    })
  } catch (err) {
    console.error('Batch override error:', err)
    return NextResponse.json({ error: 'Failed to batch update overrides' }, { status: 500 })
  }
}
