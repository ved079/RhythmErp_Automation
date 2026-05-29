// ─── /api/admin/modules/[id] ─────────────────────────────
// GET    — Get a single module
// PUT    — Update a module (including status toggle)
// DELETE — Delete a module (blocked if bugs reference it)

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error
  const { id } = await params

  try {
    const mod = await db.testModule.findUnique({ where: { id } })
    if (!mod) {
      return NextResponse.json({ error: 'Module not found' }, { status: 404 })
    }

    return NextResponse.json({
      id: mod.id,
      name: mod.name,
      label: mod.label,
      parentId: mod.parentId,
      parentLabel: mod.parentLabel,
      description: mod.description,
      sortOrder: mod.sortOrder,
      testCount: mod.testCount,
      status: mod.status,
      createdAt: mod.createdAt.toISOString(),
      updatedAt: mod.updatedAt.toISOString(),
    })
  } catch (err) {
    console.error('Get module error:', err)
    return NextResponse.json({ error: 'Failed to get module' }, { status: 500 })
  }
}

export async function PUT(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error
  const { id } = await params

  try {
    const existing = await db.testModule.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'Module not found' }, { status: 404 })
    }

    const body = await req.json()
    const updateData: Record<string, unknown> = {}

    if (body.name !== undefined) {
      updateData.name = body.name.trim()
      // Check name uniqueness if changing
      if (updateData.name !== existing.name) {
        const nameTaken = await db.testModule.findUnique({ where: { name: updateData.name as string } })
        if (nameTaken) {
          return NextResponse.json({ error: 'Module name already in use' }, { status: 409 })
        }
      }
    }
    if (body.label !== undefined) updateData.label = body.label.trim()
    if (body.parentId !== undefined) updateData.parentId = body.parentId || null
    if (body.parentLabel !== undefined) updateData.parentLabel = body.parentLabel?.trim() || null
    if (body.description !== undefined) updateData.description = body.description.trim()
    if (body.sortOrder !== undefined) updateData.sortOrder = body.sortOrder
    if (body.testCount !== undefined) updateData.testCount = body.testCount
    if (body.status !== undefined) updateData.status = body.status

    // If parentId is being set, validate it exists
    if (body.parentId) {
      const parent = await db.testModule.findUnique({ where: { id: body.parentId } })
      if (!parent) {
        return NextResponse.json({ error: 'Parent module not found' }, { status: 400 })
      }
    }

    const mod = await db.testModule.update({
      where: { id },
      data: updateData,
    })

    const actionType = body.status !== undefined && body.status !== existing.status ? 'toggle' : 'update'
    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: actionType,
      targetType: 'module',
      targetId: mod.id,
      targetLabel: mod.label,
      details: body.status !== undefined
        ? `Status changed from ${existing.status} to ${body.status}`
        : `Updated fields: ${Object.keys(updateData).join(', ')}`,
    })

    return NextResponse.json({
      id: mod.id,
      name: mod.name,
      label: mod.label,
      parentId: mod.parentId,
      parentLabel: mod.parentLabel,
      description: mod.description,
      sortOrder: mod.sortOrder,
      testCount: mod.testCount,
      status: mod.status,
      createdAt: mod.createdAt.toISOString(),
      updatedAt: mod.updatedAt.toISOString(),
    })
  } catch (err) {
    console.error('Update module error:', err)
    return NextResponse.json({ error: 'Failed to update module' }, { status: 500 })
  }
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error
  const { id } = await params

  try {
    const existing = await db.testModule.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'Module not found' }, { status: 404 })
    }

    // Soft check: don't delete if bugs reference this module name
    const bugCount = await db.bugReport.count({
      where: { moduleName: existing.name },
    })
    if (bugCount > 0) {
      return NextResponse.json(
        { error: `Cannot delete module: ${bugCount} bug report(s) reference this module` },
        { status: 409 },
      )
    }

    // Also check if any children reference this module as parent
    const childCount = await db.testModule.count({
      where: { parentId: id },
    })
    if (childCount > 0) {
      return NextResponse.json(
        { error: `Cannot delete module: ${childCount} child module(s) exist. Remove or reassign children first.` },
        { status: 409 },
      )
    }

    await db.testModule.delete({ where: { id } })

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'delete',
      targetType: 'module',
      targetId: id,
      targetLabel: existing.label,
      details: `Deleted module: ${existing.name} (${existing.label})`,
    })

    return NextResponse.json({ message: 'Module deleted' })
  } catch (err) {
    console.error('Delete module error:', err)
    return NextResponse.json({ error: 'Failed to delete module' }, { status: 500 })
  }
}
