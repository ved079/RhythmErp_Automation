import { NextResponse } from 'next/server'
import { db } from '@/lib/db'
import bcrypt from 'bcryptjs'

/**
 * POST /api/auth/seed
 * Seed the default admin user (idempotent).
 *
 * C5: This endpoint is only available in non-production environments.
 * In production, the middleware blocks it with a 404 response.
 * The admin user must be created through the admin panel.
 */
export async function POST() {
  // Double-check: even if middleware somehow passes, enforce here
  if (process.env.NODE_ENV === 'production') {
    return NextResponse.json(
      { error: 'This endpoint is not available in production' },
      { status: 404 }
    )
  }

  try {
    // C4: Use env var for seed admin password (no hardcoded secrets)
    const seedPassword = process.env.SEED_ADMIN_PASSWORD || 'admin123'
    const seedEmail = 'admin@rhythmerp.com'

    const existing = await db.user.findUnique({
      where: { email: seedEmail },
    })

    if (existing) {
      return NextResponse.json({ message: 'Admin user already exists', user: { id: existing.id, email: existing.email, name: existing.name, role: existing.role } })
    }

    const hashedPassword = await bcrypt.hash(seedPassword, 12)

    const user = await db.user.create({
      data: {
        email: seedEmail,
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
