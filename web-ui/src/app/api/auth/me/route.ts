import { NextRequest, NextResponse } from 'next/server'
import { validateSession } from '@/lib/session'

export async function GET(request: NextRequest) {
  try {
    const user = await validateSession(request)

    if (!user) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }

    return NextResponse.json({ user })
  } catch (error) {
    console.error('Me error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
