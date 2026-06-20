'use client'

import { useState, useEffect } from 'react'

export function useSystemHealth() {
  const [systemHealthData, setSystemHealthData] = useState<Record<string, unknown> | null>(null)
  const [healthLoaded, setHealthLoaded] = useState(false)
  const [appStartTime] = useState(() => Date.now())

  useEffect(() => {
    fetch('/api/admin/system-health')
      .then(res => res.ok ? res.json() : null)
      .then(data => setSystemHealthData(data))
      .catch(() => {})
      .finally(() => setHealthLoaded(true))
  }, [])

  return { systemHealthData, healthLoaded, appStartTime }
}
