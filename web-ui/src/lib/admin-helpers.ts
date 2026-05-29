// ─── Admin API Helpers ──────────────────────────────────
// Shared utilities for all /api/admin/* routes:
// - Session validation (admin/qa_lead only) — delegates to session.ts
// - Audit log creation

import { NextRequest } from 'next/server'
import { db } from '@/lib/db'
import { validateAdminSession, type SessionUser } from '@/lib/session'

// Re-export the admin user type for backward compatibility
export type AdminUser = SessionUser

/**
 * Validate that the request comes from an authenticated admin or qa_lead user.
 * Returns the user object if valid, or an error response if not.
 */
export async function validateAdmin(req: NextRequest): Promise<{ user: AdminUser } | { error: Response }> {
  const user = await validateAdminSession(req)

  if (!user) {
    // Check if it's an auth issue or a permissions issue
    // Try to validate session first
    const { validateSession } = await import('@/lib/session')
    const anyUser = await validateSession(req)

    if (!anyUser) {
      return { error: new Response(JSON.stringify({ error: 'Not authenticated' }), { status: 401, headers: { 'Content-Type': 'application/json' } }) }
    }

    return { error: new Response(JSON.stringify({ error: 'Insufficient permissions' }), { status: 403, headers: { 'Content-Type': 'application/json' } }) }
  }

  return { user }
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
