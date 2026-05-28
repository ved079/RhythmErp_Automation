// ─── /api/admin/users ───────────────────────────────────
// GET  — List all users (admin/qa_lead only)
// POST — Create a new user (bcrypt hashed password)

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import bcrypt from 'bcryptjs'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

export async function GET(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const users = await db.user.findMany({
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        status: true,
        moduleAccess: true,
        lastLogin: true,
        createdAt: true,
      },
      orderBy: { createdAt: 'desc' },
    })

    const mapped = users.map(u => ({
      id: u.id,
      email: u.email,
      name: u.name,
      role: u.role,
      status: u.status,
      moduleAccess: JSON.parse(u.moduleAccess || '[]'),
      lastLogin: u.lastLogin?.toISOString() || null,
      createdAt: u.createdAt.toISOString(),
    }))

    return NextResponse.json({ users: mapped })
  } catch (err) {
    console.error('List users error:', err)
    return NextResponse.json({ error: 'Failed to list users' }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const body = await req.json()
    const { name, email, password, role, module_access } = body

    if (!email || !name) {
      return NextResponse.json({ error: 'Name and email are required' }, { status: 400 })
    }

    // Check if email already exists
    const existing = await db.user.findUnique({ where: { email: email.toLowerCase().trim() } })
    if (existing) {
      return NextResponse.json({ error: 'A user with this email already exists' }, { status: 409 })
    }

    const hashedPassword = await bcrypt.hash(password || 'changeme', 12)

    const user = await db.user.create({
      data: {
        email: email.toLowerCase().trim(),
        name: name.trim(),
        password: hashedPassword,
        role: role || 'tester',
        status: 'active',
        moduleAccess: JSON.stringify(module_access || []),
      },
    })

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'create',
      targetType: 'user',
      targetId: user.id,
      targetLabel: `${user.name} (${user.email})`,
      details: `Created user with role: ${user.role}`,
    })

    return NextResponse.json({
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
      status: user.status,
      moduleAccess: JSON.parse(user.moduleAccess || '[]'),
    }, { status: 201 })
  } catch (err) {
    console.error('Create user error:', err)
    return NextResponse.json({ error: 'Failed to create user' }, { status: 500 })
  }
}
