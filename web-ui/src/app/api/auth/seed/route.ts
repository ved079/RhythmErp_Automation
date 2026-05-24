import { NextResponse } from 'next/server'
import { db } from '@/lib/db'
import bcrypt from 'bcryptjs'

export async function GET() {
  try {
    const existing = await db.user.findUnique({
      where: { email: 'admin@rhythmerp.com' },
    })

    if (existing) {
      return NextResponse.json({ message: 'Admin user already exists', user: { id: existing.id, email: existing.email, name: existing.name, role: existing.role } })
    }

    const hashedPassword = await bcrypt.hash('admin123', 12)

    const user = await db.user.create({
      data: {
        email: 'admin@rhythmerp.com',
        password: hashedPassword,
        name: 'Admin',
        role: 'admin',
      },
    })

    return NextResponse.json({ message: 'Admin user created', user: { id: user.id, email: user.email, name: user.name, role: user.role } })
  } catch (error) {
    console.error('Seed error:', error)
    return NextResponse.json({ error: 'Failed to seed admin user' }, { status: 500 })
  }
}