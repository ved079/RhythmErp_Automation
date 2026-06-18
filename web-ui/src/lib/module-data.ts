/**
 * Module data and sidebar builder utilities for RhythmERP Automation Runner.
 * Contains the master sidebar module list, test spec data, and functions
 * to build/filter sidebar modules based on API data and user access.
 */

import { type ApiModule, type ApiSubModule, folderToSidebarId, sidebarToFolderMapping } from '@/lib/api'
import { type SidebarModule, type TestClassGroup, type TestItem, type TestSpecItem } from '@/lib/types'

// ─── Full sidebar module tree ────────────────────────────
// This is the master list of ALL sidebar modules (with or without tests).
// API data enriches these with real test counts.

export const ALL_SIDEBAR_MODULES: SidebarModule[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'company-onboarding', label: 'Company Onboarding', userIcon: true },
  {
    id: 'registration',
    label: 'Registration',
    defaultExpanded: true,
    children: [
      { id: 'employee', label: 'Employee', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'supplier', label: 'Supplier', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'customer', label: 'Customer', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'agent', label: 'Agent', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'farmer', label: 'Farmer', badge: '📝 No tests', badgeType: 'none' as const },
    ],
  },
  {
    id: 'document',
    label: 'Document',
    defaultExpanded: true,
    children: [
      { id: 'directors', label: 'Directors', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'member', label: 'Member', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'constituent-documents', label: 'Constituent Documents', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'miscellaneous-documents', label: 'Miscellaneous Documents', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'register-of-loan', label: 'Register of Loan', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'register-charges', label: 'Register Charges', badge: '📝 No tests', badgeType: 'none' as const },
    ],
  },
  {
    id: 'private-b2b',
    label: 'Private (B2B)',
    defaultExpanded: true,
    cartLink: true,
    children: [
      {
        id: 'purchase-group',
        label: 'Purchase',
        defaultExpanded: true,
        children: [
          { id: 'purchase-order', label: 'Purchase Order', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'goods-receipt-note', label: 'Goods Receipt Note', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'gate-pass', label: 'Gate Pass', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'quality-check', label: 'Quality Check', badge: '📝 No tests', badgeType: 'none' as const },
        ],
      },
    ],
  },
  {
    id: 'common-settings',
    label: 'Common Settings',
    defaultExpanded: true,
    children: [
      { id: 'uom', label: 'UOM', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'uom-conversion', label: 'UOM Conversion', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'designation', label: 'Designation', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'bank', label: 'Bank', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'seasons', label: 'Seasons', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'hsn-sac', label: 'HSN SAC', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'error-code-master', label: 'Error Code Master', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'vehicle-master', label: 'Vehicle Master', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'tax-authority', label: 'Tax Authority', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'tax-rate', label: 'Tax Rate', badge: '📝 No tests', badgeType: 'none' as const },
    ],
  },
  {
    id: 'commodity-settings',
    label: 'Commodity Settings',
    children: [
      {
        id: 'commodity-attributes-group',
        label: 'Commodity Attributes',
        defaultExpanded: true,
        children: [
          { id: 'item-attribute', label: 'Item Attribute', badge: '📝 No tests', badgeType: 'none' as const },
        ],
      },
      { id: 'quality-parameter-def', label: 'Quality Parameter Master', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'commodity-quality-param', label: 'Commodity Quality Parameter', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'commodity-base-rate', label: 'Commodity Base Rate', badge: '📝 No tests', badgeType: 'none' as const },
      {
        id: 'commodity-master-group',
        label: 'Commodity Master',
        defaultExpanded: true,
        children: [
          { id: 'item-master', label: 'Item Master', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'crop-master', label: 'Crop Master', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'services-master', label: 'Services Master', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'item-category', label: 'Item Category', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'item-group', label: 'Item Group', badge: '📝 No tests', badgeType: 'none' as const },
        ],
      },
    ],
  },
  {
    id: 'access',
    label: 'Access',
    defaultExpanded: true,
    children: [
      { id: 'entity-group', label: 'Entity Group Definition', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'role-creation', label: 'Role Creation Screen', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'role-screen-link', label: 'Role Screen Link', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'user-creation', label: 'User Creation Screen', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'screen-api-link', label: 'Screen API Link', badge: '📝 No tests', badgeType: 'none' as const },
    ],
  },
  { id: 'my-tickets', label: 'My Tickets' },
]
