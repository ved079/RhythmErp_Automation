'use client'

import { useState, useEffect, useCallback } from 'react'

export function useErpToken(externalToken?: string, externalTenantId?: string) {
  const [localToken, setLocalToken] = useState(() =>
    typeof window !== 'undefined' ? localStorage.getItem('erp_token') ?? '' : '',
  )
  const [localTenantId, setLocalTenantId] = useState(() =>
    typeof window !== 'undefined' ? localStorage.getItem('erp_tenant_id') ?? '' : '',
  )

  useEffect(() => {
    if (localToken) localStorage.setItem('erp_token', localToken)
    else localStorage.removeItem('erp_token')
  }, [localToken])

  useEffect(() => {
    if (localTenantId) localStorage.setItem('erp_tenant_id', localTenantId)
    else localStorage.removeItem('erp_tenant_id')
  }, [localTenantId])

  // Sync from parent when it changes (e.g. user sets token via global dialog)
  useEffect(() => {
    if (externalToken && externalToken !== localToken) setLocalToken(externalToken)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [externalToken])

  useEffect(() => {
    if (externalTenantId && externalTenantId !== localTenantId) setLocalTenantId(externalTenantId)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [externalTenantId])

  const token = localToken || externalToken || ''
  const tenantId = localTenantId || externalTenantId || ''

  const handleAuthError = useCallback((err: unknown): boolean => {
    const msg = err instanceof Error ? err.message : String(err)
    if (msg.includes('401') || msg.includes('403') || msg.toLowerCase().includes('unauthorized')) {
      setLocalToken('')
      setLocalTenantId('')
      return true
    }
    return false
  }, [])

  return {
    token,
    tenantId,
    localToken,
    setLocalToken,
    localTenantId,
    setLocalTenantId,
    handleAuthError,
  }
}
