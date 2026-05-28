'use client'

import React, { useState, useEffect } from 'react'

export function NavToast({ label, parent }: { label: string; parent?: string | null }) {
  const [visible, setVisible] = useState(true)
  const [fading, setFading] = useState(false)

  useEffect(() => {
    const fadeTimer = setTimeout(() => setFading(true), 1200)
    const hideTimer = setTimeout(() => setVisible(false), 1600)
    return () => { clearTimeout(fadeTimer); clearTimeout(hideTimer) }
  }, [])

  if (!visible) return null

  return (
    <div
      className={`pointer-events-none absolute top-3 left-1/2 z-50 transition-all duration-300 ease-out ${
        fading ? 'opacity-0' : 'opacity-100'
      }`}
      style={{ transform: `translateX(-50%) translateY(${fading ? '-4px' : '0px'})` }}
    >
      <div className="flex items-center gap-2 bg-gray-900/90 dark:bg-gray-100/90 text-white dark:text-gray-900 text-[12px] font-medium px-3.5 py-1.5 rounded-full shadow-lg shadow-black/20 backdrop-blur-sm whitespace-nowrap">
        {parent && (
          <>
            <span className="opacity-50">{parent}</span>
            <span className="opacity-30 mx-0.5">›</span>
          </>
        )}
        <span>{label}</span>
      </div>
    </div>
  )
}
