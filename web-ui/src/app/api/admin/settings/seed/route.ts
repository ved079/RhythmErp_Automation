// ─── /api/admin/settings/seed ────────────────────────────
// POST — Seed default system settings (idempotent)

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

const DEFAULT_SETTINGS = [
  { key: 'app_name', label: 'Application Name', value: 'RhythmErp Automation', type: 'text' as const, description: 'The display name of the application', category: 'general', options: [] },
  { key: 'default_browser', label: 'Default Browser', value: 'chrome', type: 'select' as const, description: 'Default browser for test execution', category: 'execution', options: ['chrome', 'firefox', 'edge', 'safari'] },
  { key: 'headless_mode', label: 'Headless Mode', value: 'true', type: 'boolean' as const, description: 'Run tests in headless browser mode', category: 'execution', options: [] },
  { key: 'screenshot_on_fail', label: 'Screenshot on Failure', value: 'true', type: 'boolean' as const, description: 'Capture screenshots when tests fail', category: 'execution', options: [] },
  { key: 'max_retry_count', label: 'Max Retry Count', value: '2', type: 'number' as const, description: 'Maximum number of retries for failed tests', category: 'execution', options: [] },
  { key: 'test_timeout', label: 'Test Timeout (seconds)', value: '300', type: 'number' as const, description: 'Default timeout for test execution', category: 'execution', options: [] },
  { key: 'bug_sla_high', label: 'Bug SLA - High (hours)', value: '24', type: 'number' as const, description: 'Hours before high priority bugs are overdue', category: 'sla', options: [] },
  { key: 'bug_sla_medium', label: 'Bug SLA - Medium (hours)', value: '48', type: 'number' as const, description: 'Hours before medium priority bugs are overdue', category: 'sla', options: [] },
  { key: 'bug_sla_low', label: 'Bug SLA - Low (days)', value: '7', type: 'number' as const, description: 'Days before low priority bugs are overdue', category: 'sla', options: [] },
  { key: 'notification_email', label: 'Notification Email', value: '', type: 'text' as const, description: 'Email address for system notifications', category: 'notifications', options: [] },
  { key: 'webhook_url', label: 'Webhook URL', value: '', type: 'text' as const, description: 'Webhook URL for integration notifications', category: 'notifications', options: [] },
  { key: 'enable_scheduling', label: 'Enable Scheduling', value: 'true', type: 'boolean' as const, description: 'Allow scheduled test runs', category: 'scheduling', options: [] },
  { key: 'schedule_check_interval', label: 'Schedule Check Interval (minutes)', value: '5', type: 'number' as const, description: 'How often to check for scheduled runs', category: 'scheduling', options: [] },
  { key: 'default_password', label: 'Default New User Password', value: 'changeme', type: 'text' as const, description: 'Default password assigned to new users', category: 'security', options: [] },
  { key: 'session_timeout_days', label: 'Session Timeout (days)', value: '7', type: 'number' as const, description: 'Number of days before sessions expire', category: 'security', options: [] },
]

export async function POST(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    let created = 0
    let updated = 0

    for (const setting of DEFAULT_SETTINGS) {
      const existing = await db.systemSetting.findUnique({ where: { key: setting.key } })
      if (existing) {
        // Update label/description/type if changed, but preserve the user's value
        await db.systemSetting.update({
          where: { key: setting.key },
          data: {
            label: setting.label,
            description: setting.description,
            type: setting.type,
            category: setting.category,
            options: JSON.stringify(setting.options),
          },
        })
        updated++
      } else {
        await db.systemSetting.create({
          data: {
            key: setting.key,
            label: setting.label,
            value: setting.value,
            type: setting.type,
            description: setting.description,
            category: setting.category,
            options: JSON.stringify(setting.options),
          },
        })
        created++
      }
    }

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'update',
      targetType: 'setting',
      targetLabel: 'All Settings',
      details: `Seed/reset settings: ${created} created, ${updated} updated`,
    })

    const settings = await db.systemSetting.findMany({
      orderBy: [{ category: 'asc' }, { label: 'asc' }],
    })

    const mapped = settings.map(s => ({
      id: s.id,
      key: s.key,
      label: s.label,
      value: s.value,
      type: s.type,
      description: s.description,
      category: s.category,
      options: JSON.parse(s.options || '[]'),
    }))

    return NextResponse.json({ settings: mapped, created, updated })
  } catch (err) {
    console.error('Seed settings error:', err)
    return NextResponse.json({ error: 'Failed to seed settings' }, { status: 500 })
  }
}
