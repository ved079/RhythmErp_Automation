const _moduleCache = new Map<string, string>()

const _reverseCache = new Map<string, { module: string; subModule: string | null }>()

// Hardcoded fallback maps — used when DB cache isn't populated yet
const FOLDER_TO_SIDEBAR_FALLBACK: Record<string, string> = {
  login_screens: 'login-screens',
  company_onboarding: 'company-onboarding',
  common_settings: 'common-settings',
  commodity_settings: 'commodity-settings',
  access: 'access',
  registration: 'registration',
  bank: 'bank',
  designation: 'designation',
  error_code_mst: 'error-code-master',
  hsn_sac: 'hsn-sac',
  season: 'seasons',
  tax_authority: 'tax-authority',
  tax_rate: 'tax-rate',
  uom: 'uom',
  uom_conversion: 'uom-conversion',
  vehicle_master: 'vehicle-master',
  crop_master: 'crop-master',
  item_master: 'item-master',
  quality_parameter_master: 'quality-parameter-def',
  services_master: 'services-master',
  item_category: 'item-category',
  item_group: 'item-group',
  commodity_quality_parameter: 'commodity-quality-param',
  commodity_base_rate: 'commodity-base-rate',
  item_attribute: 'item-attribute',
  entity_group_definition: 'entity-group',
  role_creation_screen: 'role-creation',
  user_creation: 'user-creation',
  farmer: 'farmer',
  customer: 'customer',
  supplier: 'supplier',
  agent: 'agent',
  member: 'member',
  private_b2b: 'private-b2b',
  purchase_booking: 'purchase-booking',
  purchase_order: 'purchase-order',
  goods_receipt_note: 'goods-receipt-note',
  gate_pass: 'gate-pass',
  quality_check: 'quality-check',
  direct_pb_flow: 'direct-pb-flow',
  po_qc_pb_flow: 'po-qc-pb-flow',
}

const SIDEBAR_TO_FOLDER_FALLBACK: Record<string, { module: string; subModule: string | null }> = {
  'login-screens': { module: 'login_screens', subModule: null },
  'company-onboarding': { module: 'company_onboarding', subModule: null },
  'common-settings': { module: 'common_settings', subModule: null },
  'commodity-settings': { module: 'commodity_settings', subModule: null },
  access: { module: 'access', subModule: null },
  registration: { module: 'registration', subModule: null },
  bank: { module: 'common_settings', subModule: 'bank' },
  designation: { module: 'common_settings', subModule: 'designation' },
  'error-code-master': { module: 'common_settings', subModule: 'error_code_mst' },
  'hsn-sac': { module: 'common_settings', subModule: 'hsn_sac' },
  seasons: { module: 'common_settings', subModule: 'season' },
  'tax-authority': { module: 'common_settings', subModule: 'tax_authority' },
  'tax-rate': { module: 'common_settings', subModule: 'tax_rate' },
  uom: { module: 'common_settings', subModule: 'uom' },
  'uom-conversion': { module: 'common_settings', subModule: 'uom_conversion' },
  'vehicle-master': { module: 'common_settings', subModule: 'vehicle_master' },
  'crop-master': { module: 'commodity_settings', subModule: 'crop_master' },
  'item-master': { module: 'commodity_settings', subModule: 'item_master' },
  'quality-parameter-def': { module: 'commodity_settings', subModule: 'quality_parameter_master' },
  'services-master': { module: 'commodity_settings', subModule: 'services_master' },
  'item-category': { module: 'commodity_settings', subModule: 'item_category' },
  'item-group': { module: 'commodity_settings', subModule: 'item_group' },
  'commodity-quality-param': { module: 'commodity_settings', subModule: 'commodity_quality_parameter' },
  'commodity-base-rate': { module: 'commodity_settings', subModule: 'commodity_base_rate' },
  'item-attribute': { module: 'commodity_settings', subModule: 'item_attribute' },
  'entity-group': { module: 'access', subModule: 'entity_group' },
  'role-creation': { module: 'access', subModule: 'role_creation_screen' },
  'user-creation': { module: 'access', subModule: 'user_creation' },
  farmer: { module: 'registration', subModule: 'farmer' },
  customer: { module: 'registration', subModule: 'customer' },
  supplier: { module: 'registration', subModule: 'supplier' },
  agent: { module: 'registration', subModule: 'agent' },
  member: { module: 'registration', subModule: 'member' },
  'private-b2b': { module: 'private_b2b', subModule: null },
  'purchase-booking': { module: 'private_b2b', subModule: 'purchase_booking' },
  'purchase-order': { module: 'private_b2b', subModule: 'purchase_order' },
  'goods-receipt-note': { module: 'private_b2b', subModule: 'goods_receipt_note' },
  'gate-pass': { module: 'private_b2b', subModule: 'gate_pass' },
  'quality-check': { module: 'private_b2b', subModule: 'quality_check' },
  'direct-pb-flow':  { module: 'private_b2b', subModule: 'direct_pb_flow' },
  'po-qc-pb-flow':   { module: 'private_b2b', subModule: 'po_qc_pb_flow' },
}

export function getCachedFolderToSidebarId(folderName: string): string {
  return _moduleCache.get(folderName) ?? FOLDER_TO_SIDEBAR_FALLBACK[folderName] ?? folderName.toLowerCase().replace(/_/g, '-')
}

export function getCachedSidebarToFolderMapping(sidebarId: string): { module: string; subModule: string | null } | null {
  return SIDEBAR_TO_FOLDER_FALLBACK[sidebarId] ?? _reverseCache.get(sidebarId) ?? null
}

export async function folderToSidebarIdFromDB(folderName: string): Promise<string | null> {
  if (_moduleCache.has(folderName)) return _moduleCache.get(folderName)!
  const fallback = FOLDER_TO_SIDEBAR_FALLBACK[folderName]
  if (fallback) return fallback
  const res = await fetch(`/api/admin/modules?folderName=${encodeURIComponent(folderName)}`)
  if (!res.ok) return null
  const data = await res.json()
  const sidebarId = data.modules?.[0]?.name?.toLowerCase().replace(/_/g, '-') ?? null
  if (sidebarId) _moduleCache.set(folderName, sidebarId)
  return sidebarId
}

export async function warmModuleCache(): Promise<void> {
  const res = await fetch('/api/admin/modules')
  if (!res.ok) return
  const data = await res.json()
  const allModules = data.modules ?? []

  const parentById = new Map<string, { folderName: string; name: string }>()

  for (const mod of allModules) {
    if (mod.folderName && mod.name) {
      const sidebarId = FOLDER_TO_SIDEBAR_FALLBACK[mod.folderName] ?? mod.folderName.toLowerCase().replace(/_/g, '-')
      _moduleCache.set(mod.folderName, sidebarId)
      parentById.set(mod.id, { folderName: mod.folderName, name: mod.name })
    }
  }

  for (const mod of allModules) {
    if (!mod.folderName || !mod.name) continue
    const sidebarId = FOLDER_TO_SIDEBAR_FALLBACK[mod.folderName] ?? mod.folderName.toLowerCase().replace(/_/g, '-')
    if (mod.parentId) {
      const parent = parentById.get(mod.parentId)
      if (parent) {
        _reverseCache.set(sidebarId, { module: parent.folderName, subModule: mod.folderName })
      }
    } else {
      _reverseCache.set(sidebarId, { module: mod.folderName, subModule: null })
    }
  }
}
