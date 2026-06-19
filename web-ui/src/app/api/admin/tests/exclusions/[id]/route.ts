import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const { id } = await params
    const exclusion = await db.testUserExclusion.findUnique({ where: { id } })
    if (!exclusion) {
      return NextResponse.json({ error: 'Exclusion not found' }, { status: 404 })
    }

    await db.testUserExclusion.delete({ where: { id } })

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'delete',
      targetType: 'test_exclusion',
      targetId: id,
      targetLabel: exclusion.testName,
      details: `Removed exclusion for user ${exclusion.userId} on test: ${exclusion.testName}`,
    })

    return NextResponse.json({ success: true })
  } catch (err) {
    console.error('Delete exclusion error:', err)
    return NextResponse.json({ error: 'Failed to delete exclusion' }, { status: 500 })
  }
}
