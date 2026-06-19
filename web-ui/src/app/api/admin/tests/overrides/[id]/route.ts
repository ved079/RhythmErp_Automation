import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const { id } = await params
    const override = await db.testOverride.findUnique({ where: { id } })
    if (!override) {
      return NextResponse.json({ error: 'Override not found' }, { status: 404 })
    }

    await db.testOverride.delete({ where: { id } })

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'delete',
      targetType: 'test_override',
      targetId: id,
      targetLabel: override.testName,
      details: `Deleted override: ${override.testName}`,
    })

    return NextResponse.json({ success: true })
  } catch (err) {
    console.error('Delete override error:', err)
    return NextResponse.json({ error: 'Failed to delete override' }, { status: 500 })
  }
}
