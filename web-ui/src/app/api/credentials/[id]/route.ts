import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateSession } from '@/lib/session'

async function getOwned(id: string, userId: string) {
  return db.erpCredential.findFirst({ where: { id, createdBy: userId } })
}

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const user = await validateSession(req)
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { id } = await params
  const existing = await getOwned(id, user.id)
  if (!existing) return NextResponse.json({ error: 'Not found' }, { status: 404 })

  const body = await req.json()
  const { name, email, password, tenantUrl, isDefault } = body

  if (isDefault) {
    await db.erpCredential.updateMany({
      where: { createdBy: user.id },
      data: { isDefault: false },
    })
  }

  const updated = await db.erpCredential.update({
    where: { id },
    data: {
      ...(name !== undefined && { name }),
      ...(email !== undefined && { email }),
      ...(password !== undefined && { password }),
      ...(tenantUrl !== undefined && { tenantUrl }),
      ...(isDefault !== undefined && { isDefault }),
    },
    select: { id: true, name: true, email: true, tenantUrl: true, isDefault: true, createdAt: true },
  })

  return NextResponse.json({ credential: updated })
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const user = await validateSession(req)
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { id } = await params
  const existing = await getOwned(id, user.id)
  if (!existing) return NextResponse.json({ error: 'Not found' }, { status: 404 })

  await db.erpCredential.delete({ where: { id } })
  return NextResponse.json({ ok: true })
}
