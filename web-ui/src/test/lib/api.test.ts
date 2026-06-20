import { describe, it, expect } from 'vitest'
import { folderToSidebarId, sidebarToFolderMapping } from '@/lib/api'

describe('folderToSidebarId', () => {
  it('converts known folder "entity_group" to "entity-group"', () => {
    expect(folderToSidebarId('entity_group')).toBe('entity-group')
  })

  it('converts known folder "error_code_mst" to "error-code-master"', () => {
    expect(folderToSidebarId('error_code_mst')).toBe('error-code-master')
  })

  it('converts known folder "login_screens" to "login"', () => {
    expect(folderToSidebarId('login_screens')).toBe('login')
  })

  it('returns the folder name as-is for unknown folders', () => {
    expect(folderToSidebarId('unknown_module')).toBe('unknown_module')
  })

  it('handles empty string', () => {
    expect(folderToSidebarId('')).toBe('')
  })
})

describe('sidebarToFolderMapping', () => {
  it('returns null for an unknown sidebar ID', () => {
    expect(sidebarToFolderMapping('nonexistent-id')).toBeNull()
  })

  it('maps "login" to login_screens top-level module', () => {
    const result = sidebarToFolderMapping('login')
    expect(result).toEqual({ module: 'login_screens', subModule: null })
  })

  it('maps "entity-group" to access module (first matching sub-module)', () => {
    const result = sidebarToFolderMapping('entity-group')
    expect(result).toEqual({ module: 'access', subModule: 'entity_group_definition' })
  })

  it('maps "error-code-master" to common_settings module', () => {
    const result = sidebarToFolderMapping('error-code-master')
    expect(result).toEqual({ module: 'common_settings', subModule: 'error_code_mst' })
  })

  it('maps "company-onboarding" to top-level module', () => {
    const result = sidebarToFolderMapping('company-onboarding')
    expect(result).toEqual({ module: 'company_onboarding', subModule: null })
  })
})
