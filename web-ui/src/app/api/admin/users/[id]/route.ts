// ─── /api/admin/users/[id] ───────────────────────────────
// GET    — Get single user
// PUT    — Update user (name, email, role, status, moduleAccess)
// DELETE — Delete user (cannot delete self)

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error
  const { id } = await params

  try {
    const user = await db.user.findUnique({
      where: { id },
      select: {
        id: true, email: true, name: true, role: true, status: true,
        moduleAccess: true, lastLogin: true, createdAt: true,
      },
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    return NextResponse.json({
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
      status: user.status,
      moduleAccess: JSON.parse(user.moduleAccess || '[]'),
      lastLogin: user.lastLogin?.toISOString() || null,
    })
  } catch (err) {
    console.error('Get user error:', err)
    return NextResponse.json({ error: 'Failed to get user' }, { status: 500 })
  }
}

export async function PUT(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error
  const { id } = await params

  try {
    const existing = await db.user.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Don't allow admins to demote themselves
    if (existing.id === auth.user.id) {
      const body = await req.json()
      if (body.role && body.role !== 'admin') {
        return NextResponse.json({ error: 'Cannot change your own role' }, { status: 403 })
      }
      if (body.status && body.status === 'inactive') {
        return NextResponse.json({ error: 'Cannot deactivate your own account' }, { status: 403 })
      }
    }

    const body = await req.json()
    const updateData: Record<string, unknown> = {}

    if (body.name !== undefined) updateData.name = body.name.trim()
    if (body.email !== undefined) {
      updateData.email = body.email.toLowerCase().trim()
      // Check email uniqueness if changing
      if (updateData.email !== existing.email) {
        const emailTaken = await db.user.findUnique({ where: { email: updateData.email as string } })
        if (emailTaken) {
          return NextResponse.json({ error: 'Email already in use' }, { status: 409 })
        }
      }
    }
    if (body.role !== undefined) updateData.role = body.role
    if (body.status !== undefined) updateData.status = body.status
    if (body.module_access !== undefined) updateData.moduleAccess = JSON.stringify(body.module_access)

    const user = await db.user.update({
      where: { id },
      data: updateData,
    })

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'update',
      targetType: 'user',
      targetId: user.id,
      targetLabel: `${user.name} (${user.email})`,
      details: `Updated fields: ${Object.keys(updateData).join(', ')}`,
    })

    return NextResponse.json({
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
      status: user.status,
      moduleAccess: JSON.parse(user.moduleAccess || '[]'),
    })
  } catch (err) {
    console.error('Update user error:', err)
    return NextResponse.json({ error: 'Failed to update user' }, { status: 500 })
  }
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error
  const { id } = await params

  try {
    const existing = await db.user.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Cannot delete yourself
    if (existing.id === auth.user.id) {
      return NextResponse.json({ error: 'Cannot delete your own account' }, { status: 403 })
    }

    // Delete sessions first (cascade should handle this, but be safe)
    await db.session.deleteMany({ where: { userId: id } })
    await db.user.delete({ where: { id } })

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'delete',
      targetType: 'user',
      targetId: id,
      targetLabel: `${existing.name} (${existing.email})`,
      details: `Deleted user with role: ${existing.role}`,
    })

    return NextResponse.json({ message: 'User deleted' })
  } catch (err) {
    console.error('Delete user error:', err)
    return NextResponse.json({ error: 'Failed to delete user' }, { status: 500 })
  }
}
