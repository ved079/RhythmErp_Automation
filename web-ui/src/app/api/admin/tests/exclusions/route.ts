import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

export async function GET(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const { searchParams } = new URL(req.url)
    const userId = searchParams.get('userId')
    const testName = searchParams.get('testName')

    const where: Record<string, unknown> = {}
    if (userId) where.userId = userId
    if (testName) where.testName = testName

    const exclRows = await db.testUserExclusion.findMany({
      where,
      orderBy: { createdAt: 'desc' },
    })

    // Resolve user names
    const userIds = [...new Set(exclRows.map(e => e.userId))]
    const users = userIds.length > 0
      ? await db.user.findMany({ where: { id: { in: userIds } }, select: { id: true, name: true } })
      : []
    const userNameMap = Object.fromEntries(users.map(u => [u.id, u.name]))

    return NextResponse.json({
      exclusions: exclRows.map(e => ({
        id: e.id,
        testName: e.testName,
        userId: e.userId,
        userName: userNameMap[e.userId] || 'Unknown',
        createdAt: e.createdAt.toISOString(),
      })),
    })
  } catch (err) {
    console.error('List exclusions error:', err)
    return NextResponse.json({ error: 'Failed to list exclusions' }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    const body = await req.json()
    const { testName, userIds } = body

    if (!testName || !Array.isArray(userIds)) {
      return NextResponse.json({ error: 'testName and userIds[] are required' }, { status: 400 })
    }

    // Batch create exclusions (skip duplicates)
    const created = []
    for (const userId of userIds) {
      const existing = await db.testUserExclusion.findUnique({
        where: { testName_userId: { testName: testName.trim(), userId } },
      })
      if (!existing) {
        const exclusion = await db.testUserExclusion.create({
          data: { testName: testName.trim(), userId },
        })
        created.push(exclusion)
      }
    }

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'create',
      targetType: 'test_exclusion',
      targetId: testName,
      targetLabel: testName,
      details: `Added ${created.length} exclusion(s) for test: ${testName}`,
    })

    return NextResponse.json({ created: created.length }, { status: 201 })
  } catch (err) {
    console.error('Create exclusions error:', err)
    return NextResponse.json({ error: 'Failed to save exclusions' }, { status: 500 })
  }
}
