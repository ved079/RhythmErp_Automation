// ─── /api/admin/settings ─────────────────────────────────
// GET  — List all settings
// POST — Create a new setting (rare, mostly seeded)

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin } from '@/lib/admin-helpers'

export async function GET(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const settings = await db.systemSetting.findMany({
      orderBy: [{ category: 'asc' }, { label: 'asc' }],
    })

    const mapped = settings.map(s => ({
      id: s.id,
      key: s.key,
      label: s.label,
      value: s.value,
      type: s.type,
      description: s.description,
      category: s.category,
      options: JSON.parse(s.options || '[]'),
    }))

    return NextResponse.json({ settings: mapped })
  } catch (err) {
    console.error('List settings error:', err)
    return NextResponse.json({ error: 'Failed to list settings' }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const body = await req.json()
    const { key, label, value, type, description, category, options } = body

    if (!key || !label) {
      return NextResponse.json({ error: 'Key and label are required' }, { status: 400 })
    }

    const existing = await db.systemSetting.findUnique({ where: { key } })
    if (existing) {
      return NextResponse.json({ error: 'Setting with this key already exists' }, { status: 409 })
    }

    const setting = await db.systemSetting.create({
      data: {
        key,
        label,
        value: value || '',
        type: type || 'text',
        description: description || '',
        category: category || 'general',
        options: JSON.stringify(options || []),
      },
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
    }, { status: 201 })
  } catch (err) {
    console.error('Create setting error:', err)
    return NextResponse.json({ error: 'Failed to create setting' }, { status: 500 })
  }
}
