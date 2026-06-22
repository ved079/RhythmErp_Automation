// ─── /api/admin/modules/seed ─────────────────────────────
// POST — Seed default test modules from the sidebar structure (idempotent)

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

interface SeedModule {
  name: string
  label: string
  parentId?: string // resolved after parent creation
  parentLabel?: string
  description: string
  sortOrder: number
  status: 'active' | 'draft' | 'disabled'
}

const DEFAULT_MODULES: Omit<SeedModule, 'parentId'>[] = [
  // ── Registration (parent) ────────────────────────────
  { name: 'registration', label: 'Registration', parentLabel: undefined, description: 'Registration module group', sortOrder: 1, status: 'active' },
  { name: 'registration-farmer', label: 'Farmer', parentLabel: 'Registration', description: 'Farmer registration', sortOrder: 1, status: 'active' },
  { name: 'registration-supplier', label: 'Supplier', parentLabel: 'Registration', description: 'Supplier registration', sortOrder: 2, status: 'active' },
  { name: 'registration-customer', label: 'Customer', parentLabel: 'Registration', description: 'Customer registration', sortOrder: 3, status: 'active' },
  { name: 'registration-agent', label: 'Agent', parentLabel: 'Registration', description: 'Agent registration', sortOrder: 4, status: 'active' },

  // ── Company Onboarding (standalone) ──────────────────
  { name: 'company-onboarding', label: 'Company Onboarding', parentLabel: undefined, description: 'Company onboarding module', sortOrder: 2, status: 'active' },

  // ── Common Settings (parent) ─────────────────────────
  { name: 'common-settings', label: 'Common Settings', parentLabel: undefined, description: 'Common settings module group', sortOrder: 3, status: 'active' },
  { name: 'common-settings-uom', label: 'UOM', parentLabel: 'Common Settings', description: 'Unit of Measurement', sortOrder: 1, status: 'active' },
  { name: 'common-settings-uom-conversion', label: 'UOM Conversion', parentLabel: 'Common Settings', description: 'UOM conversion settings', sortOrder: 2, status: 'active' },
  { name: 'common-settings-designation', label: 'Designation', parentLabel: 'Common Settings', description: 'Designation settings', sortOrder: 3, status: 'active' },
  { name: 'common-settings-bank', label: 'Bank', parentLabel: 'Common Settings', description: 'Bank settings', sortOrder: 4, status: 'active' },
  { name: 'common-settings-seasons', label: 'Seasons', parentLabel: 'Common Settings', description: 'Seasons configuration', sortOrder: 5, status: 'active' },
  { name: 'common-settings-hsn-sac', label: 'HSN SAC', parentLabel: 'Common Settings', description: 'HSN/SAC code master', sortOrder: 6, status: 'active' },
  { name: 'common-settings-error-code-master', label: 'Error Code Master', parentLabel: 'Common Settings', description: 'Error code master', sortOrder: 7, status: 'active' },
  { name: 'common-settings-vehicle-master', label: 'Vehicle Master', parentLabel: 'Common Settings', description: 'Vehicle master data', sortOrder: 8, status: 'active' },
  { name: 'common-settings-tax-authority', label: 'Tax Authority', parentLabel: 'Common Settings', description: 'Tax authority configuration', sortOrder: 9, status: 'active' },
  { name: 'common-settings-tax-rate', label: 'Tax Rate', parentLabel: 'Common Settings', description: 'Tax rate configuration', sortOrder: 10, status: 'active' },

  // ── Commodity Settings (parent) ──────────────────────
  { name: 'commodity-settings', label: 'Commodity Settings', parentLabel: undefined, description: 'Commodity settings module group', sortOrder: 4, status: 'active' },
  { name: 'commodity-item-attribute', label: 'Item Attribute', parentLabel: 'Commodity Settings', description: 'Item attribute configuration', sortOrder: 1, status: 'active' },
  { name: 'commodity-quality-parameter-master', label: 'Quality Parameter Master', parentLabel: 'Commodity Settings', description: 'Quality parameter master', sortOrder: 2, status: 'active' },
  { name: 'commodity-quality-parameter', label: 'Commodity Quality Parameter', parentLabel: 'Commodity Settings', description: 'Commodity quality parameter mapping', sortOrder: 3, status: 'active' },
  { name: 'commodity-base-rate', label: 'Commodity Base Rate', parentLabel: 'Commodity Settings', description: 'Commodity base rate settings', sortOrder: 4, status: 'active' },
  { name: 'commodity-item-master', label: 'Item Master', parentLabel: 'Commodity Settings', description: 'Item master data', sortOrder: 5, status: 'active' },
  { name: 'commodity-crop-master', label: 'Crop Master', parentLabel: 'Commodity Settings', description: 'Crop master data', sortOrder: 6, status: 'active' },
  { name: 'commodity-services-master', label: 'Services Master', parentLabel: 'Commodity Settings', description: 'Services master data', sortOrder: 7, status: 'active' },
  { name: 'commodity-item-category', label: 'Item Category', parentLabel: 'Commodity Settings', description: 'Item category configuration', sortOrder: 8, status: 'active' },
  { name: 'commodity-item-group', label: 'Item Group', parentLabel: 'Commodity Settings', description: 'Item group configuration', sortOrder: 9, status: 'active' },

  // ── Access (parent) ─────────────────────────────────
  { name: 'access', label: 'Access', parentLabel: undefined, description: 'Access management module group', sortOrder: 5, status: 'active' },
  { name: 'access-entity-group-definition', label: 'Entity Group Definition', parentLabel: 'Access', description: 'Entity group definition', sortOrder: 1, status: 'active' },
  { name: 'access-role-creation-screen', label: 'Role Creation Screen', parentLabel: 'Access', description: 'Role creation screen', sortOrder: 2, status: 'active' },
  { name: 'access-role-screen-link', label: 'Role Screen Link', parentLabel: 'Access', description: 'Role screen link configuration', sortOrder: 3, status: 'active' },
  { name: 'access-user-creation-screen', label: 'User Creation Screen', parentLabel: 'Access', description: 'User creation screen', sortOrder: 4, status: 'active' },
  { name: 'access-screen-api-link', label: 'Screen API Link', parentLabel: 'Access', description: 'Screen API link configuration', sortOrder: 5, status: 'active' },

  // ── Document (parent) ───────────────────────────────
  { name: 'document', label: 'Document', parentLabel: undefined, description: 'Document module group', sortOrder: 6, status: 'active' },
  { name: 'member', label: 'Member', parentLabel: 'Document', description: 'Member registration documents', sortOrder: 1, status: 'active' },

  // ── Private (B2B) parent ────────────────────────────
  { name: 'private-b2b', label: 'Private (B2B)', parentLabel: undefined, description: 'Private B2B module group', sortOrder: 7, status: 'active' },
  { name: 'private-b2b-purchase-order', label: 'Purchase Order', parentLabel: 'Private (B2B)', description: 'Purchase order management', sortOrder: 1, status: 'active' },
  { name: 'private-b2b-goods-receipt-note', label: 'Goods Receipt Note', parentLabel: 'Private (B2B)', description: 'Goods receipt note management', sortOrder: 2, status: 'active' },
  { name: 'private-b2b-gate-pass', label: 'Gate Pass', parentLabel: 'Private (B2B)', description: 'Gate pass management', sortOrder: 3, status: 'active' },
  { name: 'private-b2b-quality-check', label: 'Quality Check', parentLabel: 'Private (B2B)', description: 'Quality check management', sortOrder: 4, status: 'active' },
]

export async function POST(req: NextRequest) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error

  try {
    let created = 0
    let updated = 0
    const parentIdMap: Record<string, string> = {}

    // First pass: create/update all parent modules (no parentLabel)
    for (const mod of DEFAULT_MODULES) {
      if (!mod.parentLabel) {
        const existing = await db.testModule.findUnique({ where: { name: mod.name } })
        if (existing) {
          await db.testModule.update({
            where: { name: mod.name },
            data: {
              label: mod.label,
              description: mod.description,
              sortOrder: mod.sortOrder,
              status: mod.status,
            },
          })
          updated++
          parentIdMap[mod.label] = existing.id
        } else {
          created++
          const newMod = await db.testModule.create({
            data: {
              name: mod.name,
              label: mod.label,
              parentId: null,
              parentLabel: null,
              description: mod.description,
              sortOrder: mod.sortOrder,
              testCount: 0,
              status: mod.status,
            },
          })
          parentIdMap[mod.label] = newMod.id
        }
      }
    }

    // Second pass: create/update all child modules
    for (const mod of DEFAULT_MODULES) {
      if (mod.parentLabel) {
        const resolvedParentId = parentIdMap[mod.parentLabel] || null

        const existing = await db.testModule.findUnique({ where: { name: mod.name } })
        if (existing) {
          await db.testModule.update({
            where: { name: mod.name },
            data: {
              label: mod.label,
              parentId: resolvedParentId,
              parentLabel: mod.parentLabel,
              description: mod.description,
              sortOrder: mod.sortOrder,
              status: mod.status,
            },
          })
          updated++
        } else {
          created++
          await db.testModule.create({
            data: {
              name: mod.name,
              label: mod.label,
              parentId: resolvedParentId,
              parentLabel: mod.parentLabel,
              description: mod.description,
              sortOrder: mod.sortOrder,
              testCount: 0,
              status: mod.status,
            },
          })
        }
      }
    }

    // Created count is already tracked incrementally above

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'update',
      targetType: 'module',
      targetLabel: 'All Modules',
      details: `Seed/reset modules: ${created} created, ${updated} updated`,
    })

    const modules = await db.testModule.findMany({
      orderBy: [{ sortOrder: 'asc' }, { label: 'asc' }],
    })

    const mapped = modules.map(m => ({
      id: m.id,
      name: m.name,
      label: m.label,
      parentId: m.parentId,
      parentLabel: m.parentLabel,
      description: m.description,
      sortOrder: m.sortOrder,
      testCount: m.testCount,
      status: m.status,
      createdAt: m.createdAt.toISOString(),
      updatedAt: m.updatedAt.toISOString(),
    }))

    return NextResponse.json({ modules: mapped, created, updated })
  } catch (err) {
    console.error('Seed modules error:', err)
    return NextResponse.json({ error: 'Failed to seed modules' }, { status: 500 })
  }
}
