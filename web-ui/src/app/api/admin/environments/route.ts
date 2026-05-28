// ─── /api/admin/environments ─────────────────────────────
// GET  — List all environments
// POST — Create a new environment

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

export async function GET(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const environments = await db.environment.findMany({
      orderBy: { createdAt: 'desc' },
    })

    const mapped = environments.map(e => ({
      id: e.id,
      name: e.name,
      baseUrl: e.baseUrl,
      browser: e.browser,
      status: e.status,
      color: e.color,
      lastUsed: e.lastUsed?.toISOString() || null,
    }))

    return NextResponse.json({ environments: mapped })
  } catch (err) {
    console.error('List environments error:', err)
    return NextResponse.json({ error: 'Failed to list environments' }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const body = await req.json()
    const { name, baseUrl, browser, color } = body

    if (!name || !baseUrl) {
      return NextResponse.json({ error: 'Name and base URL are required' }, { status: 400 })
    }

    // Check uniqueness
    const existing = await db.environment.findUnique({ where: { name: name.trim() } })
    if (existing) {
      return NextResponse.json({ error: 'An environment with this name already exists' }, { status: 409 })
    }

    const env = await db.environment.create({
      data: {
        name: name.trim(),
        baseUrl: baseUrl.trim(),
        browser: browser || 'chrome',
        status: 'active',
        color: color || 'bg-green-500',
      },
    })

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'create',
      targetType: 'environment',
      targetId: env.id,
      targetLabel: env.name,
      details: `Created environment: ${env.name} (${env.baseUrl})`,
    })

    return NextResponse.json({
      id: env.id,
      name: env.name,
      baseUrl: env.baseUrl,
      browser: env.browser,
      status: env.status,
      color: env.color,
    }, { status: 201 })
  } catch (err) {
    console.error('Create environment error:', err)
    return NextResponse.json({ error: 'Failed to create environment' }, { status: 500 })
  }
}
