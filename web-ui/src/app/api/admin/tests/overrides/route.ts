import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

export async function GET(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const { searchParams } = new URL(req.url)
    const testName = searchParams.get('testName')

    const where = testName ? { testName: testName.trim() } : {}

    const overrides = await db.testOverride.findMany({
      where,
      orderBy: { updatedAt: 'desc' },
    })

    return NextResponse.json({
      overrides: overrides.map(o => ({
        id: o.id,
        testName: o.testName,
        displayName: o.displayName,
        disabled: o.disabled,
        createdAt: o.createdAt.toISOString(),
        updatedAt: o.updatedAt.toISOString(),
      })),
    })
  } catch (err) {
    console.error('List overrides error:', err)
    return NextResponse.json({ error: 'Failed to list overrides' }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const body = await req.json()
    const { testName, displayName, disabled } = body

    if (!testName) {
      return NextResponse.json({ error: 'testName is required' }, { status: 400 })
    }

    const override = await db.testOverride.upsert({
      where: { testName: testName.trim() },
      update: {
        ...(displayName !== undefined ? { displayName: displayName || null } : {}),
        ...(disabled !== undefined ? { disabled } : {}),
      },
      create: {
        testName: testName.trim(),
        displayName: displayName || null,
        disabled: disabled ?? false,
      },
    })

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'update',
      targetType: 'test_override',
      targetId: override.id,
      targetLabel: override.testName,
      details: `Updated override: ${override.testName}${displayName !== undefined ? ` displayName=${displayName}` : ''}${disabled !== undefined ? ` disabled=${disabled}` : ''}`,
    })

    return NextResponse.json({
      id: override.id,
      testName: override.testName,
      displayName: override.displayName,
      disabled: override.disabled,
      createdAt: override.createdAt.toISOString(),
      updatedAt: override.updatedAt.toISOString(),
    })
  } catch (err) {
    console.error('Upsert override error:', err)
    return NextResponse.json({ error: 'Failed to save override' }, { status: 500 })
  }
}
