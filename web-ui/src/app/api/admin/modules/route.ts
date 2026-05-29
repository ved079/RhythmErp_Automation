// ─── /api/admin/modules ──────────────────────────────────
// GET  — List all modules (sorted by sortOrder, parents + children)
// POST — Create a new module

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

export async function GET(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const modules = await db.testModule.findMany({
      orderBy: [{ sortOrder: 'asc' }, { label: 'asc' }],
    })

    const mapped = modules.map(m => ({
      id: m.id,
      name: m.name,
      label: m.label,
      parentId: m.parentId,
      parentLabel: m.parentLabel,
      description: m.description,
      sortOrder: m.sortOrder,
      testCount: m.testCount,
      status: m.status,
      createdAt: m.createdAt.toISOString(),
      updatedAt: m.updatedAt.toISOString(),
    }))

    return NextResponse.json({ modules: mapped })
  } catch (err) {
    console.error('List modules error:', err)
    return NextResponse.json({ error: 'Failed to list modules' }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const body = await req.json()
    const { name, label, parentId, parentLabel, description, sortOrder, status } = body

    if (!name || !label) {
      return NextResponse.json({ error: 'Name and label are required' }, { status: 400 })
    }

    // Check uniqueness
    const existing = await db.testModule.findUnique({ where: { name: name.trim() } })
    if (existing) {
      return NextResponse.json({ error: 'A module with this name already exists' }, { status: 409 })
    }

    // If parentId is provided, validate it exists
    if (parentId) {
      const parent = await db.testModule.findUnique({ where: { id: parentId } })
      if (!parent) {
        return NextResponse.json({ error: 'Parent module not found' }, { status: 400 })
      }
    }

    const mod = await db.testModule.create({
      data: {
        name: name.trim(),
        label: label.trim(),
        parentId: parentId || null,
        parentLabel: parentLabel?.trim() || null,
        description: description?.trim() || '',
        sortOrder: sortOrder ?? 0,
        testCount: 0,
        status: status || 'active',
      },
    })

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'create',
      targetType: 'module',
      targetId: mod.id,
      targetLabel: mod.label,
      details: `Created module: ${mod.name} (${mod.label})${mod.parentLabel ? ` under ${mod.parentLabel}` : ''}`,
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
    }, { status: 201 })
  } catch (err) {
    console.error('Create module error:', err)
    return NextResponse.json({ error: 'Failed to create module' }, { status: 500 })
  }
}
