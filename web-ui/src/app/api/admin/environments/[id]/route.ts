// ─── /api/admin/environments/[id] ────────────────────────
// PUT    — Update environment (including status toggle)
// DELETE — Delete environment

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

export async function PUT(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error
  const { id } = await params

  try {
    const existing = await db.environment.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'Environment not found' }, { status: 404 })
    }

    const body = await req.json()
    const updateData: Record<string, unknown> = {}

    if (body.name !== undefined) {
      updateData.name = body.name.trim()
      // Check name uniqueness if changing
      if (updateData.name !== existing.name) {
        const nameTaken = await db.environment.findUnique({ where: { name: updateData.name as string } })
        if (nameTaken) {
          return NextResponse.json({ error: 'Environment name already in use' }, { status: 409 })
        }
      }
    }
    if (body.baseUrl !== undefined) updateData.baseUrl = body.baseUrl.trim()
    if (body.browser !== undefined) updateData.browser = body.browser
    if (body.status !== undefined) updateData.status = body.status
    if (body.color !== undefined) updateData.color = body.color

    const env = await db.environment.update({
      where: { id },
      data: updateData,
    })

    const actionType = body.status !== undefined && body.status !== existing.status ? 'toggle' : 'update'
    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: actionType,
      targetType: 'environment',
      targetId: env.id,
      targetLabel: env.name,
      details: body.status !== undefined
        ? `Status changed from ${existing.status} to ${body.status}`
        : `Updated fields: ${Object.keys(updateData).join(', ')}`,
    })

    return NextResponse.json({
      id: env.id,
      name: env.name,
      baseUrl: env.baseUrl,
      browser: env.browser,
      status: env.status,
      color: env.color,
      lastUsed: env.lastUsed?.toISOString() || null,
    })
  } catch (err) {
    console.error('Update environment error:', err)
    return NextResponse.json({ error: 'Failed to update environment' }, { status: 500 })
  }
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error
  const { id } = await params

  try {
    const existing = await db.environment.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'Environment not found' }, { status: 404 })
    }

    await db.environment.delete({ where: { id } })

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'delete',
      targetType: 'environment',
      targetId: id,
      targetLabel: existing.name,
      details: `Deleted environment: ${existing.name}`,
    })

    return NextResponse.json({ message: 'Environment deleted' })
  } catch (err) {
    console.error('Delete environment error:', err)
    return NextResponse.json({ error: 'Failed to delete environment' }, { status: 500 })
  }
}
