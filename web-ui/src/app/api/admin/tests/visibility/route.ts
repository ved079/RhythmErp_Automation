import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateSession } from '@/lib/session'

export async function GET(req: NextRequest) {
  const user = await validateSession(req)
  if (!user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  try {
    // Fetch all overrides
    const overrides = await db.testOverride.findMany({
      orderBy: { updatedAt: 'desc' },
    })

    // Fetch exclusions for this user
    const exclusions = await db.testUserExclusion.findMany({
      where: { userId: user.id },
      select: { testName: true },
    })

    const excludedTestNames = new Set(exclusions.map(e => e.testName))
    const overridesMap: Record<string, { displayName?: string; disabled: boolean }> = {}
    for (const o of overrides) {
      overridesMap[o.testName] = {
        displayName: o.displayName || undefined,
        disabled: o.disabled,
      }
    }

    return NextResponse.json({
      excludedTestNames: Array.from(excludedTestNames),
      overrides: overridesMap,
    })
  } catch (err) {
    console.error('Fetch visibility error:', err)
    return NextResponse.json({ error: 'Failed to fetch visibility' }, { status: 500 })
  }
}
