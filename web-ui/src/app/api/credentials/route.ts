import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateSession } from '@/lib/session'

export async function GET(req: NextRequest) {
  const user = await validateSession(req)
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const credentials = await db.erpCredential.findMany({
    where: { createdBy: user.id },
    select: { id: true, name: true, email: true, password: true, tenantUrl: true, isDefault: true, createdAt: true },
    orderBy: [{ isDefault: 'desc' }, { createdAt: 'asc' }],
  })

  return NextResponse.json({ credentials })
}

export async function POST(req: NextRequest) {
  const user = await validateSession(req)
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const body = await req.json()
  const { name, email, password, tenantUrl, isDefault } = body

  if (!name || !email || !password || !tenantUrl) {
    return NextResponse.json({ error: 'name, email, password and tenantUrl are required' }, { status: 400 })
  }

  if (isDefault) {
    await db.erpCredential.updateMany({
      where: { createdBy: user.id },
      data: { isDefault: false },
    })
  }

  const credential = await db.erpCredential.create({
    data: { name, email, password, tenantUrl, isDefault: !!isDefault, createdBy: user.id },
    select: { id: true, name: true, email: true, tenantUrl: true, isDefault: true, createdAt: true },
  })

  return NextResponse.json({ credential }, { status: 201 })
}
