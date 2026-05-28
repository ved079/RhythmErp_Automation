// ─── /api/admin/settings/[id] ────────────────────────────
// PUT — Update a setting's value

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

export async function PUT(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error
  const { id } = await params

  try {
    const existing = await db.systemSetting.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'Setting not found' }, { status: 404 })
    }

    const body = await req.json()
    const updateData: Record<string, unknown> = {}

    if (body.value !== undefined) updateData.value = String(body.value)
    if (body.label !== undefined) updateData.label = body.label
    if (body.description !== undefined) updateData.description = body.description
    if (body.category !== undefined) updateData.category = body.category
    if (body.type !== undefined) updateData.type = body.type
    if (body.options !== undefined) updateData.options = JSON.stringify(body.options)

    const setting = await db.systemSetting.update({
      where: { id },
      data: updateData,
    })

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'update',
      targetType: 'setting',
      targetId: setting.id,
      targetLabel: setting.label,
      details: body.value !== undefined
        ? `Changed value from "${existing.value}" to "${body.value}"`
        : `Updated fields: ${Object.keys(updateData).join(', ')}`,
    })

    return NextResponse.json({
      id: setting.id,
      key: setting.key,
      label: setting.label,
      value: setting.value,
      type: setting.type,
      description: setting.description,
      category: setting.category,
      options: JSON.parse(setting.options || '[]'),
    })
  } catch (err) {
    console.error('Update setting error:', err)
    return NextResponse.json({ error: 'Failed to update setting' }, { status: 500 })
  }
}
