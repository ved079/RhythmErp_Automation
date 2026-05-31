// ─── Admin API Helpers ──────────────────────────────────
// Shared utilities for all /api/admin/* routes:
// - Session validation (admin only) — delegates to session.ts
// - Audit log creation (with IP address)

import { NextRequest } from 'next/server'
import { db } from '@/lib/db'
import { validateAdminSession, type SessionUser } from '@/lib/session'
import { getClientIp } from '@/lib/rate-limit'

// Re-export the admin user type for backward compatibility
export type AdminUser = SessionUser

/**
 * Validate that the request comes from an authenticated admin user.
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
 * Now includes IP address for security tracking.
 */
export async function createAuditLog(params: {
  userId: string
  userName: string
  action: 'create' | 'update' | 'delete' | 'login' | 'logout' | 'reset_password' | 'toggle' | 'failed_login' | 'password_change'
  targetType: string   // e.g. 'user', 'environment', 'setting'
  targetId?: string
  targetLabel?: string
  details?: string
  ipAddress?: string
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
        ipAddress: params.ipAddress || '',
      },
    })
  } catch (err) {
    console.error('createAuditLog error:', err)
    // Non-blocking — don't fail the main operation if audit logging fails
  }
}

/**
 * Create an audit log entry with IP extracted from the request.
 * Convenience wrapper that auto-extracts the client IP.
 */
export async function createAuditLogWithRequest(
  req: NextRequest,
  params: {
    userId: string
    userName: string
    action: 'create' | 'update' | 'delete' | 'login' | 'logout' | 'reset_password' | 'toggle' | 'failed_login' | 'password_change'
    targetType: string
    targetId?: string
    targetLabel?: string
    details?: string
  }
) {
  const ipAddress = getClientIp(req)
  return createAuditLog({ ...params, ipAddress })
}
