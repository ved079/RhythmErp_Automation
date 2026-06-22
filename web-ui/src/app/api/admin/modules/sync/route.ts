// ─── /api/admin/modules/sync ────────────────────────────────
// POST — Sync modules from FastAPI discovery to the TestModule table.
// Keeps the Next.js DB in sync with the actual test modules on disk.

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdminSession } from '@/lib/session'
import { createAuditLog } from '@/lib/admin-helpers'

// Display name mappings for folder names
const DISPLAY_NAMES: Record<string, string> = {
  login_screens: 'Login Screens',
  company_onboarding: 'Company Onboarding',
  common_settings: 'Common Settings',
  commodity_settings: 'Commodity Settings',
  access_screen: 'Access',
  registration: 'Registration',
  bank: 'Bank',
  designation: 'Designation',
  error_code_mst: 'Error Code Master',
  hsn_sac: 'HSN/SAC',
  season: 'Season',
  tax_authority: 'Tax Authority',
  tax_rate: 'Tax Rate',
  uom: 'UOM',
  uom_conversion: 'UOM Conversion',
  vehicle_master: 'Vehicle Master',
  crop_master: 'Crop Master',
  item_master: 'Item Master',
  quality_parameter_master: 'Quality Parameter Master',
  services_master: 'Services Master',
  item_category: 'Item Category',
  item_group: 'Item Group',
  commodity_quality_parameter: 'Commodity Quality Parameter',
  commodity_base_rate: 'Commodity Base Rate',
  item_attribute: 'Item Attribute',
  entity_group_definition: 'Entity Group Definition',
  role_creation_screen: 'Role Creation Screen',
  user_creation: 'User Creation Screen',
  farmer: 'Farmer',
  customer: 'Customer',
  supplier: 'Supplier',
  agent: 'Agent',
  member: 'Member',
  private_b2b: 'Private (B2B)',
  purchase_order: 'Purchase Order',
  goods_receipt_note: 'Goods Receipt Note',
  gate_pass: 'Gate Pass',
  quality_check: 'Quality Check',
}

// Parent mappings for sub-modules
const PARENT_MAP: Record<string, { name: string; label: string }> = {
  bank: { name: 'common_settings', label: 'Common Settings' },
  designation: { name: 'common_settings', label: 'Common Settings' },
  error_code_mst: { name: 'common_settings', label: 'Common Settings' },
  hsn_sac: { name: 'common_settings', label: 'Common Settings' },
  season: { name: 'common_settings', label: 'Common Settings' },
  tax_authority: { name: 'common_settings', label: 'Common Settings' },
  tax_rate: { name: 'common_settings', label: 'Common Settings' },
  uom: { name: 'common_settings', label: 'Common Settings' },
  uom_conversion: { name: 'common_settings', label: 'Common Settings' },
  vehicle_master: { name: 'common_settings', label: 'Common Settings' },
  crop_master: { name: 'commodity_settings', label: 'Commodity Settings' },
  item_master: { name: 'commodity_settings', label: 'Commodity Settings' },
  quality_parameter_master: { name: 'commodity_settings', label: 'Commodity Settings' },
  services_master: { name: 'commodity_settings', label: 'Commodity Settings' },
  item_category: { name: 'commodity_settings', label: 'Commodity Settings' },
  item_group: { name: 'commodity_settings', label: 'Commodity Settings' },
  commodity_quality_parameter: { name: 'commodity_settings', label: 'Commodity Settings' },
  commodity_base_rate: { name: 'commodity_settings', label: 'Commodity Settings' },
  item_attribute: { name: 'commodity_settings', label: 'Commodity Settings' },
  entity_group_definition: { name: 'access', label: 'Access' },
  role_creation_screen: { name: 'access', label: 'Access' },
  user_creation: { name: 'access', label: 'Access' },
  farmer: { name: 'registration', label: 'Registration' },
  customer: { name: 'registration', label: 'Registration' },
  supplier: { name: 'registration', label: 'Registration' },
  agent: { name: 'registration', label: 'Registration' },
  member: { name: 'document', label: 'Document' },
  purchase_order: { name: 'private_b2b', label: 'Private (B2B)' },
  goods_receipt_note: { name: 'private_b2b', label: 'Private (B2B)' },
  gate_pass: { name: 'private_b2b', label: 'Private (B2B)' },
  quality_check: { name: 'private_b2b', label: 'Private (B2B)' },
}

// Top-level modules
const TOP_MODULES = ['login_screens', 'company_onboarding', 'common_settings', 'commodity_settings', 'access', 'registration', 'document', 'private_b2b']

export async function POST(req: NextRequest) {
  const user = await validateAdminSession(req)
  if (!user) {
    return NextResponse.json({ error: 'Not authorized' }, { status: 401 })
  }

  try {
    const body = await req.json()
    const modules = body.modules as Array<{
      name: string
      display: string
      sub_modules: Array<{
        name: string
        display: string
        tests: Array<{ name: string; display_name: string; docstring: string | null }>
      }>
    }>

    if (!Array.isArray(modules)) {
      return NextResponse.json({ error: 'Invalid modules data' }, { status: 400 })
    }

    let created = 0
    let updated = 0

    // Ensure top-level parent modules exist
    for (const topName of TOP_MODULES) {
      const existing = await db.testModule.findUnique({ where: { name: topName } })
      if (!existing) {
        await db.testModule.create({
          data: {
            name: topName,
            label: DISPLAY_NAMES[topName] || topName,
            folderName: topName,
            status: 'active',
            testCount: 0,
            sortOrder: TOP_MODULES.indexOf(topName),
          },
        })
        created++
      }
    }

    // Process each module from FastAPI
    for (const mod of modules) {
      // If the module has sub-modules, process each sub-module
      if (mod.sub_modules && mod.sub_modules.length > 0) {
        for (const sub of mod.sub_modules) {
          const testCount = sub.tests?.length || 0
          const parent = PARENT_MAP[sub.name] || { name: mod.name, label: mod.display }
          const existing = await db.testModule.findUnique({ where: { name: sub.name } })

          // Find parent ID
          const parentModule = await db.testModule.findUnique({ where: { name: parent.name } })

          if (existing) {
            await db.testModule.update({
              where: { name: sub.name },
              data: {
                label: sub.display || DISPLAY_NAMES[sub.name] || sub.name,
                folderName: sub.name,
                testCount,
                parentId: parentModule?.id || null,
                parentLabel: parent.label,
                status: 'active',
              },
            })
            updated++
          } else {
            await db.testModule.create({
              data: {
                name: sub.name,
                label: sub.display || DISPLAY_NAMES[sub.name] || sub.name,
                folderName: sub.name,
                parentId: parentModule?.id || null,
                parentLabel: parent.label,
                testCount,
                status: 'active',
              },
            })
            created++
          }
        }
      } else {
        // Standalone module (no sub-modules)
        const testCount = 0
        const existing = await db.testModule.findUnique({ where: { name: mod.name } })

        if (existing) {
          await db.testModule.update({
            where: { name: mod.name },
            data: {
              label: mod.display || DISPLAY_NAMES[mod.name] || mod.name,
              folderName: mod.name,
              testCount,
              status: 'active',
            },
          })
          updated++
        } else {
          await db.testModule.create({
            data: {
              name: mod.name,
              label: mod.display || DISPLAY_NAMES[mod.name] || mod.name,
              folderName: mod.name,
              testCount,
              status: 'active',
            },
          })
          created++
        }
      }
    }

    await createAuditLog({
      userId: user.id,
      userName: user.name,
      action: 'update',
      targetType: 'module',
      targetLabel: 'Module Sync',
      details: `Synced modules from FastAPI: ${created} created, ${updated} updated`,
    })

    return NextResponse.json({ created, updated, total: created + updated })
  } catch (error) {
    console.error('[Module Sync] POST error:', error)
    return NextResponse.json({ error: 'Failed to sync modules' }, { status: 500 })
  }
}
