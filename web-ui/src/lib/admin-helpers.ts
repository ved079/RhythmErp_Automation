// ─── Admin API Helpers ──────────────────────────────────
// Shared utilities for all /api/admin/* routes:
// - Session validation (admin/qa_lead only)
// - Audit log creation

import { NextRequest } from 'next/server'
import { db } from '@/lib/db'

export interface AdminUser {
  id: string
  email: string
  name: string
  role: string
}

/**
 * Validate that the request comes from an authenticated admin or qa_lead user.
 * Returns the user object if valid, or an error response if not.
 */
export async function validateAdmin(req: NextRequest): Promise<{ user: AdminUser } | { error: Response }> {
  const token = req.cookies.get('session_token')?.value

  if (!token) {
    return { error: new Response(JSON.stringify({ error: 'Not authenticated' }), { status: 401, headers: { 'Content-Type': 'application/json' } }) }
  }

  try {
    const session = await db.session.findUnique({
      where: { token },
      include: { user: true },
    })

    if (!session || !session.user || session.expiresAt < new Date()) {
      if (session) {
        await db.session.delete({ where: { id: session.id } }).catch(() => {})
      }
      return { error: new Response(JSON.stringify({ error: 'Session expired' }), { status: 401, headers: { 'Content-Type': 'application/json' } }) }
    }

    if (session.user.role !== 'admin' && session.user.role !== 'qa_lead') {
      return { error: new Response(JSON.stringify({ error: 'Insufficient permissions' }), { status: 403, headers: { 'Content-Type': 'application/json' } }) }
    }

    return {
      user: {
        id: session.user.id,
        email: session.user.email,
        name: session.user.name,
        role: session.user.role,
      },
    }
  } catch (err) {
    console.error('validateAdmin error:', err)
    return { error: new Response(JSON.stringify({ error: 'Internal server error' }), { status: 500, headers: { 'Content-Type': 'application/json' } }) }
  }
}

/**
 * Create an audit log entry. Called after every admin action.
 */
export async function createAuditLog(params: {
  userId: string
  userName: string
  action: 'create' | 'update' | 'delete' | 'login' | 'logout' | 'reset_password' | 'toggle'
  targetType: string   // e.g. 'user', 'environment', 'setting'
  targetId?: string
  targetLabel?: string
  details?: string
}) {
  try {
    await db.auditLog.create({
      data: {
        userId: params.userId,
        userName: params.userName,
        action: params.action,
        targetType: params.targetType,
        targetId: params.targetId || '',
        targetLabel: params.targetLabel || '',
        details: params.details || '',
      },
    })
  } catch (err) {
    console.error('createAuditLog error:', err)
    // Non-blocking — don't fail the main operation if audit logging fails
  }
}
