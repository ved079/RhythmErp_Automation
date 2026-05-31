'use client'

import React, { useState, useEffect } from 'react'
import { useTheme } from 'next-themes'

// ─── NAV TOAST ───────────────────────────────────────────
// Style selector — change this to switch: 'style_a' thru 'style_x'
export const NAV_TOAST_STYLE = 'style_x' as const

export type NavToastStyleType = typeof NAV_TOAST_STYLE

function NavToast({ label, parent }: { label: string; parent?: string | null }) {
  const [visible, setVisible] = useState(true)
  const [phase, setPhase] = useState<'enter' | 'hold' | 'exit'>('enter')
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  useEffect(() => {
    const holdTimer = setTimeout(() => setPhase('hold'), 50)
    const exitTimer = setTimeout(() => setPhase('exit'), 1400)
    const hideTimer = setTimeout(() => setVisible(false), 1850)
    return () => { clearTimeout(holdTimer); clearTimeout(exitTimer); clearTimeout(hideTimer) }
  }, [])

  if (!visible) return null

  const isEntering = phase === 'enter'
  const isExiting = phase === 'exit'
  const animStyle = {
    transform: `translateX(-50%) translateY(${isEntering ? '-12px' : isExiting ? '-8px' : '0px'})`,
    opacity: isEntering ? 0 : isExiting ? 0 : 1,
    transition: 'all 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
  }

  // ── Style A: Big Logo Shadow ──
  // Larger card with a HUGE logo sitting in the background, text sits on top
  if (NAV_TOAST_STYLE === 'style_a') {
    return (
      <div className="pointer-events-none absolute top-3 left-1/2 z-50" style={animStyle}>
        <div
          className="relative flex items-center gap-3 pl-2 pr-5 py-1.5 rounded-xl whitespace-nowrap overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)',
            border: '1.5px solid #2E7D32',
            boxShadow: '0 4px 20px rgba(27,67,50,0.14), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          {/* Logo chip on left */}
          <div className="w-7 h-7 rounded-lg shrink-0 overflow-hidden flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #2E7D32, #1B4332)' }}>
            <img src="/agdi-logo-new.webp" alt="" className="w-5 h-5 object-contain brightness-0 invert opacity-90" />
          </div>
          {/* Big background logo ghost */}
          <img
            src="/agdi-logo-new.webp"
            alt=""
            className="absolute right-[-4px] top-1/2 -translate-y-1/2 w-16 h-16 opacity-[0.04] object-contain pointer-events-none"
          />
          {parent && (
            <>
              <span className="text-[#495584] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <span className="text-[#2E7D32]/30 text-[10px]">/</span>
            </>
          )}
          <span className="text-[#1B4332] text-[13px] font-['Manrope'] font-bold relative z-10">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style B: Logo Canvas ──
  // Wide pill where the entire background IS the logo, super faint, text floats over it
  if (NAV_TOAST_STYLE === 'style_b') {
    return (
      <div className="pointer-events-none absolute top-3 left-1/2 z-50" style={animStyle}>
        <div
          className="relative flex items-center gap-2.5 px-5 py-2 rounded-full whitespace-nowrap overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)',
            border: '1.5px solid #2E7D32',
            boxShadow: '0 3px 16px rgba(27,67,50,0.12), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          {/* Full-width repeated logo as texture */}
          <img
            src="/agdi-logo-new.webp"
            alt=""
            className="absolute inset-0 w-full h-full opacity-[0.04] object-cover object-center pointer-events-none scale-150"
          />
          <div className="w-2 h-2 rounded-full shrink-0" style={{ background: 'linear-gradient(135deg, #4CAF50, #2E7D32)' }} />
          {parent && (
            <>
              <span className="text-[#495584] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <svg width="8" height="8" viewBox="0 0 8 8" className="shrink-0 opacity-40">
                <path d="M3 1.5L5.5 4L3 6.5" stroke="#1B4332" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </>
          )}
          <span className="text-[#1B4332] text-[13px] font-['Manrope'] font-bold relative z-10">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style C: Compact Logo Stamp ──
  // Tight like the original goated pill but with a tiny logo icon replacing the dot
  if (NAV_TOAST_STYLE === 'style_c') {
    return (
      <div className="pointer-events-none absolute top-3 left-1/2 z-50" style={animStyle}>
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-full whitespace-nowrap"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)',
            border: '1.5px solid #2E7D32',
            boxShadow: '0 2px 12px rgba(27,67,50,0.12), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          {/* Tiny logo circle instead of dot */}
          <div className="w-5 h-5 rounded-full shrink-0 overflow-hidden flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #2E7D32, #4CAF50)' }}>
            <img src="/agdi-logo-new.webp" alt="" className="w-3 h-3 object-contain brightness-0 invert opacity-90" />
          </div>
          {parent && (
            <>
              <span className="text-[#495584] text-[10px] font-['Manrope'] font-medium">{parent}</span>
              <span className="text-[#2E7D32]/25 text-[10px]">·</span>
            </>
          )}
          <span className="text-[#1B4332] text-[12px] font-['Manrope'] font-bold">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style D: Hero Banner ──
  // Bigger card, logo watermark fills entire right half, left accent bar, bolder feel
  if (NAV_TOAST_STYLE === 'style_d') {
    return (
      <div className="pointer-events-none absolute top-3 left-1/2 z-50" style={animStyle}>
        <div
          className="relative flex items-center gap-3 pl-3 pr-6 py-2.5 rounded-lg whitespace-nowrap overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3 0%, #C8E6C9 40%, #FFFFFF 100%)',
            border: '1.5px solid #2E7D32',
            borderLeft: '4px solid #2E7D32',
            boxShadow: '0 4px 24px rgba(27,67,50,0.18), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          {/* Massive logo taking right half as bg */}
          <img
            src="/agdi-logo-new.webp"
            alt=""
            className="absolute right-[-6px] top-1/2 -translate-y-1/2 w-20 h-20 opacity-[0.05] object-contain pointer-events-none rotate-[-10deg]"
          />
          <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: 'linear-gradient(135deg, #4CAF50, #2E7D32)' }} />
          {parent && (
            <>
              <span className="text-[#495584] text-[12px] font-['Manrope'] font-semibold">{parent}</span>
              <svg width="10" height="10" viewBox="0 0 8 8" className="shrink-0 opacity-50">
                <path d="M3 1.5L5.5 4L3 6.5" stroke="#1B4332" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </>
          )}
          <span className="text-[#1B4332] text-[14px] font-['Manrope'] font-bold relative z-10">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style E: Split Badge ──
  // Two-tone split — left half dark green with white logo, right half white with text
  if (NAV_TOAST_STYLE === 'style_e') {
    return (
      <div className="pointer-events-none absolute top-3 left-1/2 z-50" style={animStyle}>
        <div
          className="flex items-center rounded-full whitespace-nowrap overflow-hidden"
          style={{
            border: '1.5px solid #2E7D32',
            boxShadow: '0 3px 16px rgba(27,67,50,0.14)',
          }}
        >
          {/* Dark green left half with logo */}
          <div className="flex items-center justify-center w-8 h-8 shrink-0" style={{ background: 'linear-gradient(135deg, #1B4332, #2E7D32)' }}>
            <img src="/agdi-logo-new.webp" alt="" className="w-5 h-5 object-contain brightness-0 invert opacity-90" />
          </div>
          {/* White right half with text */}
          <div className="flex items-center gap-1.5 px-3 py-1.5" style={{ background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)' }}>
            {parent && (
              <>
                <span className="text-[#495584] text-[10px] font-['Manrope'] font-medium">{parent}</span>
                <span className="text-[#2E7D32]/30 text-[8px]">/</span>
              </>
            )}
            <span className="text-[#1B4332] text-[12px] font-['Manrope'] font-bold">{label}</span>
          </div>
        </div>
      </div>
    )
  }

  // ── Style F: Pulse Logo Ring ──
  // Logo icon with animated pulse ring, pill shape, subtle and alive
  if (NAV_TOAST_STYLE === 'style_f') {
    return (
      <div className="pointer-events-none absolute top-3 left-1/2 z-50" style={animStyle}>
        <div
          className="flex items-center gap-2.5 px-4 py-1.5 rounded-full whitespace-nowrap"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)',
            border: '1.5px solid #2E7D32',
            boxShadow: '0 3px 16px rgba(27,67,50,0.12), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          {/* Logo with pulse ring */}
          <div className="relative shrink-0">
            <div className="absolute inset-0 w-6 h-6 rounded-full animate-ping opacity-20" style={{ background: '#2E7D32' }} />
            <div className="w-6 h-6 rounded-full overflow-hidden flex items-center justify-center relative" style={{ background: 'linear-gradient(135deg, #2E7D32, #4CAF50)' }}>
              <img src="/agdi-logo-new.webp" alt="" className="w-4 h-4 object-contain brightness-0 invert opacity-90" />
            </div>
          </div>
          {parent && (
            <>
              <span className="text-[#495584] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <svg width="8" height="8" viewBox="0 0 8 8" className="shrink-0 opacity-40">
                <path d="M3 1.5L5.5 4L3 6.5" stroke="#1B4332" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </>
          )}
          <span className="text-[#1B4332] text-[12px] font-['Manrope'] font-bold">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style G: Leaf Trail ──
  // Multiple tiny logo dots trailing off to the right, like a leaf trail effect
  if (NAV_TOAST_STYLE === 'style_g') {
    return (
      <div className="pointer-events-none absolute top-3 left-1/2 z-50" style={animStyle}>
        <div
          className="relative flex items-center gap-2 pl-1.5 pr-4 py-1 rounded-xl whitespace-nowrap overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)',
            border: '1.5px solid #2E7D32',
            boxShadow: '0 3px 16px rgba(27,67,50,0.14), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          {/* Logo chip */}
          <div className="w-7 h-7 rounded-lg shrink-0 overflow-hidden flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #2E7D32, #1B4332)' }}>
            <img src="/agdi-logo-new.webp" alt="" className="w-5 h-5 object-contain brightness-0 invert opacity-90" />
          </div>
          {parent && (
            <>
              <span className="text-[#495584] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <span className="text-[#2E7D32]/30 text-[10px]">/</span>
            </>
          )}
          <span className="text-[#1B4332] text-[13px] font-['Manrope'] font-bold">{label}</span>
          {/* Trailing ghost logos */}
          <img src="/agdi-logo-new.webp" alt="" className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 opacity-[0.06] object-contain pointer-events-none" />
          <img src="/agdi-logo-new.webp" alt="" className="absolute right-1 top-1/2 -translate-y-1/2 w-3 h-3 opacity-[0.04] object-contain pointer-events-none" />
        </div>
      </div>
    )
  }

  // ── Style H: Reverse Stamp ──
  // Dark green body with white text, logo watermark ghost inside — the inverse vibe
  if (NAV_TOAST_STYLE === 'style_h') {
    return (
      <div className="pointer-events-none absolute top-3 left-1/2 z-50" style={animStyle}>
        <div
          className="relative flex items-center gap-2 px-4 py-1.5 rounded-full whitespace-nowrap overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, #1B4332, #2E7D32)',
            border: '1.5px solid #4CAF50',
            boxShadow: '0 4px 20px rgba(27,67,50,0.3), inset 0 1px 0 rgba(255,255,255,0.06)',
          }}
        >
          {/* Ghost logo watermark */}
          <img
            src="/agdi-logo-new.webp"
            alt=""
            className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 opacity-[0.08] object-contain pointer-events-none brightness-0 invert"
          />
          <div className="w-2 h-2 rounded-full shrink-0 animate-pulse" style={{ background: '#4CAF50' }} />
          {parent && (
            <>
              <span className="text-[#C8E6C9] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <svg width="8" height="8" viewBox="0 0 8 8" className="shrink-0 opacity-50">
                <path d="M3 1.5L5.5 4L3 6.5" stroke="#C8E6C9" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </>
          )}
          <span className="text-white text-[12px] font-['Manrope'] font-bold relative z-10">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style I: Neon Glow ──
  // Logo chip with a neon green glow halo around the entire toast
  if (NAV_TOAST_STYLE === 'style_i') {
    return (
      <div className="pointer-events-none absolute top-3 left-1/2 z-50" style={animStyle}>
        <div
          className="flex items-center gap-2.5 pl-1.5 pr-4 py-1.5 rounded-xl whitespace-nowrap"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)',
            border: '1.5px solid #2E7D32',
            boxShadow: '0 0 12px rgba(76,175,80,0.25), 0 0 24px rgba(76,175,80,0.1), 0 3px 16px rgba(27,67,50,0.12), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          <div className="w-7 h-7 rounded-lg shrink-0 overflow-hidden flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #2E7D32, #1B4332)' }}>
            <img src="/agdi-logo-new.webp" alt="" className="w-5 h-5 object-contain brightness-0 invert opacity-90" />
          </div>
          {parent && (
            <>
              <span className="text-[#495584] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <span className="text-[#2E7D32]/30 text-[10px]">/</span>
            </>
          )}
          <span className="text-[#1B4332] text-[13px] font-['Manrope'] font-bold">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style J: Typewriter Tag ──
  // Minimal — just the logo dot and text with a monospace/tracking feel, ultra clean
  if (NAV_TOAST_STYLE === 'style_j') {
    return (
      <div className="pointer-events-none absolute top-3 left-1/2 z-50" style={animStyle}>
        <div
          className="flex items-center gap-2.5 px-4 py-1.5 rounded-full whitespace-nowrap"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)',
            border: '1.5px solid #2E7D32',
            boxShadow: '0 2px 12px rgba(27,67,50,0.12), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          <img src="/agdi-logo-new.webp" alt="" className="w-5 h-5 object-contain opacity-70 shrink-0" />
          {parent && (
            <>
              <span className="text-[#495584] text-[10px] font-['Manrope'] font-semibold uppercase tracking-[0.2em]">{parent}</span>
              <span className="text-[#2E7D32]/20">→</span>
            </>
          )}
          <span className="text-[#1B4332] text-[12px] font-['Manrope'] font-bold tracking-wide">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style K: Floating Glass Card ──
  // Elevated card with a thick bottom border, logo as a badge, feels like a notification card
  if (NAV_TOAST_STYLE === 'style_k') {
    return (
      <div className="pointer-events-none absolute top-3 left-1/2 z-50" style={animStyle}>
        <div
          className="relative flex items-center gap-2.5 pl-2 pr-4 py-2 rounded-lg whitespace-nowrap overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)',
            border: '1.5px solid #2E7D32',
            borderBottom: '3px solid #2E7D32',
            boxShadow: '0 6px 24px rgba(27,67,50,0.15), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          <div className="w-7 h-7 rounded-full shrink-0 overflow-hidden flex items-center justify-center ring-2 ring-[#2E7D32]/20" style={{ background: 'linear-gradient(135deg, #2E7D32, #4CAF50)' }}>
            <img src="/agdi-logo-new.webp" alt="" className="w-4 h-4 object-contain brightness-0 invert opacity-90" />
          </div>
          {parent && (
            <>
              <span className="text-[#495584] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <span className="text-[#2E7D32]/25 text-[10px]">›</span>
            </>
          )}
          <span className="text-[#1B4332] text-[13px] font-['Manrope'] font-bold">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style L: Eco Strip ──
  // Horizontal strip with gradient left bar + logo watermark repeated as a pattern in the bg
  if (NAV_TOAST_STYLE === 'style_l') {
    return (
      <div className="pointer-events-none absolute top-3 left-1/2 z-50" style={animStyle}>
        <div
          className="relative flex items-center gap-2.5 pl-3.5 pr-5 py-2 rounded-lg whitespace-nowrap overflow-hidden"
          style={{
            background: 'linear-gradient(90deg, #DFF3E3 0%, #FFFFFF 60%)',
            border: '1.5px solid #2E7D32',
            borderLeft: '5px solid #2E7D32',
            boxShadow: '0 3px 16px rgba(27,67,50,0.12), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          {/* Repeated logo pattern in bg */}
          <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: "url('/agdi-logo-new.webp')", backgroundRepeat: 'repeat', backgroundSize: '24px 24px' }} />
          <div className="w-2 h-2 rounded-full shrink-0" style={{ background: 'linear-gradient(135deg, #4CAF50, #2E7D32)' }} />
          {parent && (
            <>
              <span className="text-[#495584] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <svg width="8" height="8" viewBox="0 0 8 8" className="shrink-0 opacity-40">
                <path d="M3 1.5L5.5 4L3 6.5" stroke="#1B4332" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </>
          )}
          <span className="text-[#1B4332] text-[12px] font-['Manrope'] font-bold relative z-10">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style M: Corner Ribbon ──
  // Diagonal ribbon pinned at the top-right corner of the content area
  if (NAV_TOAST_STYLE === 'style_m') {
    return (
      <div className="pointer-events-none absolute top-0 right-0 z-50 overflow-hidden" style={{ width: '150px', height: '80px' }}>
        <div
          className="absolute top-4 right-[-36px] flex items-center gap-2 px-10 py-1.5 whitespace-nowrap"
          style={{
            background: 'linear-gradient(135deg, #1B4332, #2E7D32)',
            transform: 'rotate(45deg)',
            boxShadow: '0 2px 8px rgba(27,67,50,0.3)',
            borderTop: '1px solid rgba(76,175,80,0.3)',
            borderBottom: '1px solid rgba(76,175,80,0.3)',
          }}
        >
          <img src="/agdi-logo-new.webp" alt="" className="w-3 h-3 object-contain brightness-0 invert opacity-80 shrink-0" />
          <span className="text-white text-[10px] font-['Manrope'] font-bold tracking-wide">{parent ? `${parent} / ` : ''}{label}</span>
        </div>
      </div>
    )
  }

  // ── Style N: Left Edge Tag ──
  // Vertical tab that slides out from the left edge of the content area
  if (NAV_TOAST_STYLE === 'style_n') {
    return (
      <div className="pointer-events-none absolute left-0 top-1/2 -translate-y-1/2 z-50" style={animStyle}>
        <div
          className="flex items-center gap-2 pl-3 pr-4 py-2.5 rounded-r-xl whitespace-nowrap"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)',
            border: '1.5px solid #2E7D32',
            borderLeft: '4px solid #2E7D32',
            boxShadow: '4px 0 16px rgba(27,67,50,0.15), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          <div className="w-6 h-6 rounded-full shrink-0 overflow-hidden flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #2E7D32, #4CAF50)' }}>
            <img src="/agdi-logo-new.webp" alt="" className="w-3.5 h-3.5 object-contain brightness-0 invert opacity-90" />
          </div>
          <div className="flex flex-col">
            {parent && <span className="text-[#495584] text-[9px] font-['Manrope'] font-medium uppercase tracking-wider leading-tight">{parent}</span>}
            <span className="text-[#1B4332] text-[12px] font-['Manrope'] font-bold leading-tight">{label}</span>
          </div>
        </div>
      </div>
    )
  }

  // ── Style O: Floating Orb ──
  // Circular bubble that floats near the top, with label inside — like a map pin
  if (NAV_TOAST_STYLE === 'style_o') {
    return (
      <div className="pointer-events-none absolute top-4 left-1/2 z-50" style={{ ...animStyle, transform: `translateX(-50%) translateY(${isEntering ? '-16px' : isExiting ? '-10px' : '0px'}) scale(${isEntering ? '0.8' : '1'})`, transition: 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)' }}>
        <div className="relative flex flex-col items-center">
          <div
            className="flex items-center gap-2 px-4 py-2 rounded-full whitespace-nowrap"
            style={{
              background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)',
              border: '2px solid #2E7D32',
              boxShadow: '0 0 16px rgba(76,175,80,0.2), 0 4px 20px rgba(27,67,50,0.15)',
            }}
          >
            <img src="/agdi-logo-new.webp" alt="" className="w-4 h-4 object-contain opacity-70 shrink-0" />
            {parent && (
              <>
                <span className="text-[#495584] text-[10px] font-['Manrope'] font-medium">{parent}</span>
                <span className="text-[#2E7D32]/30 text-[8px]">›</span>
              </>
            )}
            <span className="text-[#1B4332] text-[12px] font-['Manrope'] font-bold">{label}</span>
          </div>
          {/* Arrow pointing down */}
          <div className="w-3 h-3 -mt-1.5 rotate-45" style={{ background: '#DFF3E3', borderRight: '2px solid #2E7D32', borderBottom: '2px solid #2E7D32' }} />
        </div>
      </div>
    )
  }

  // ── Style P: Bottom Snackbar ──
  // Slides up from the bottom center — like a material snackbar with logo
  if (NAV_TOAST_STYLE === 'style_p') {
    return (
      <div className="pointer-events-none absolute bottom-4 left-1/2 z-50" style={{
        transform: `translateX(-50%) translateY(${isEntering ? '20px' : isExiting ? '20px' : '0px'})`,
        opacity: isEntering ? 0 : isExiting ? 0 : 1,
        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
      }}>
        <div
          className="flex items-center gap-3 pl-2 pr-5 py-2 rounded-2xl whitespace-nowrap"
          style={{
            background: 'linear-gradient(135deg, #1B4332, #2E7D32)',
            boxShadow: '0 8px 32px rgba(27,67,50,0.35), inset 0 1px 0 rgba(255,255,255,0.06)',
          }}
        >
          <div className="w-8 h-8 rounded-xl shrink-0 overflow-hidden flex items-center justify-center" style={{ background: 'rgba(255,255,255,0.12)' }}>
            <img src="/agdi-logo-new.webp" alt="" className="w-5 h-5 object-contain brightness-0 invert opacity-90" />
          </div>
          {parent && (
            <>
              <span className="text-[#C8E6C9] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <span className="text-[#4CAF50]/40 text-[10px]">/</span>
            </>
          )}
          <span className="text-white text-[13px] font-['Manrope'] font-semibold">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style Q: Spotlight Flash ──
  // Full-width bar that flashes across the top with a shimmer sweep animation
  if (NAV_TOAST_STYLE === 'style_q') {
    return (
      <div className="pointer-events-none absolute top-0 left-0 right-0 z-50" style={{
        opacity: isEntering ? 0 : isExiting ? 0 : 1,
        transition: 'opacity 0.3s ease',
      }}>
        <div
          className="relative flex items-center justify-center gap-3 py-2 overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, #1B4332, #2E7D32)',
            boxShadow: '0 2px 12px rgba(27,67,50,0.2)',
          }}
        >
          {/* Shimmer sweep */}
          <div className="absolute inset-0" style={{
            background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.08) 50%, transparent 100%)',
            animation: 'shimmer 1.5s ease-in-out',
          }} />
          <img src="/agdi-logo-new.webp" alt="" className="w-4 h-4 object-contain brightness-0 invert opacity-70 shrink-0" />
          {parent && (
            <>
              <span className="text-[#C8E6C9] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <span className="text-[#4CAF50]/40">/</span>
            </>
          )}
          <span className="text-white text-[13px] font-['Manrope'] font-semibold">{label}</span>
        </div>
        <style>{`@keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }`}</style>
      </div>
    )
  }

  // ── Style R: Dock Bubble ──
  // macOS dock-style — bounces up from bottom-center with spring physics, rounded card
  if (NAV_TOAST_STYLE === 'style_r') {
    return (
      <div className="pointer-events-none absolute bottom-8 left-1/2 z-50" style={{
        transform: `translateX(-50%) translateY(${isEntering ? '40px' : isExiting ? '30px' : '0px'}) scale(${isEntering ? '0.6' : '1'})`,
        opacity: isEntering ? 0 : isExiting ? 0 : 1,
        transition: 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
      }}>
        <div
          className="flex items-center gap-3 pl-2.5 pr-5 py-2 rounded-2xl whitespace-nowrap"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)',
            border: '1.5px solid #2E7D32',
            boxShadow: '0 8px 32px rgba(27,67,50,0.2), 0 2px 8px rgba(27,67,50,0.1), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          <div className="w-8 h-8 rounded-xl shrink-0 overflow-hidden flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #2E7D32, #4CAF50)' }}>
            <img src="/agdi-logo-new.webp" alt="" className="w-5 h-5 object-contain brightness-0 invert opacity-90" />
          </div>
          <div className="flex flex-col">
            {parent && <span className="text-[#495584] text-[9px] font-['Manrope'] font-medium uppercase tracking-wider">{parent}</span>}
            <span className="text-[#1B4332] text-[13px] font-['Manrope'] font-bold">{label}</span>
          </div>
        </div>
      </div>
    )
  }

  // ── Style S: Morph Blob ──
  // Top-center but with a blob/organic shape, wobbly border-radius that morphs
  if (NAV_TOAST_STYLE === 'style_s') {
    return (
      <div className="pointer-events-none absolute top-3 left-1/2 z-50" style={animStyle}>
        <div
          className="flex items-center gap-2.5 px-5 py-2 whitespace-nowrap"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)',
            border: '1.5px solid #2E7D32',
            borderRadius: '30px 60px 30px 60px',
            boxShadow: '0 4px 20px rgba(27,67,50,0.15), inset 0 1px 0 rgba(255,255,255,0.8)',
            animation: 'morph 2s ease-in-out infinite alternate',
          }}
        >
          <img src="/agdi-logo-new.webp" alt="" className="w-4 h-4 object-contain opacity-70 shrink-0" />
          {parent && (
            <>
              <span className="text-[#495584] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <span className="text-[#2E7D32]/25 text-[10px]">→</span>
            </>
          )}
          <span className="text-[#1B4332] text-[12px] font-['Manrope'] font-bold">{label}</span>
        </div>
        <style>{`@keyframes morph { 0% { border-radius: 30px 60px 30px 60px; } 100% { border-radius: 60px 30px 60px 30px; } }`}</style>
      </div>
    )
  }

  // ── Style T: Side Rail Pill ──
  // Slides out from the left edge (sidebar side), vertically centered — Option A color scheme
  if (NAV_TOAST_STYLE === 'style_t') {
    return (
      <div className="pointer-events-none absolute left-0 top-1/3 z-50" style={{
        transform: `translateX(${isEntering ? '-100%' : isExiting ? '-100%' : '0'})`,
        opacity: isEntering ? 0 : isExiting ? 0 : 1,
        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
      }}>
        <div
          className="relative flex items-center gap-2.5 pl-1.5 pr-4 py-1.5 rounded-r-xl whitespace-nowrap overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3, #FFFFFF)',
            border: '1.5px solid #2E7D32',
            borderLeft: '3px solid #2E7D32',
            boxShadow: '4px 0 16px rgba(27,67,50,0.14), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          {/* Logo chip */}
          <div className="w-7 h-7 rounded-lg shrink-0 overflow-hidden flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #2E7D32, #1B4332)' }}>
            <img src="/agdi-logo-new.webp" alt="" className="w-5 h-5 object-contain brightness-0 invert opacity-90" />
          </div>
          {/* Big background logo ghost */}
          <img
            src="/agdi-logo-new.webp"
            alt=""
            className="absolute right-[-4px] top-1/2 -translate-y-1/2 w-16 h-16 opacity-[0.04] object-contain pointer-events-none"
          />
          {parent && (
            <>
              <span className="text-[#495584] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <span className="text-[#2E7D32]/30 text-[10px]">/</span>
            </>
          )}
          <span className="text-[#1B4332] text-[13px] font-['Manrope'] font-bold relative z-10">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style U: Sidebar Active Echo ──
  // Uses the EXACT sidebar active item gradient + inset shadow — feels like the active item reached out
  if (NAV_TOAST_STYLE === 'style_u') {
    return (
      <div className="pointer-events-none absolute left-0 top-1/3 z-50" style={{
        transform: `translateX(${isEntering ? '-100%' : isExiting ? '-100%' : '0'})`,
        opacity: isEntering ? 0 : isExiting ? 0 : 1,
        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
      }}>
        <div
          className="relative flex items-center gap-2.5 pl-1.5 pr-4 py-1.5 rounded-r-xl whitespace-nowrap overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, #DFF3E3, #C8E6C9, #B7E4C7)',
            border: '1px solid #C8E6C9',
            borderLeft: '3px solid #2E7D32',
            boxShadow: 'rgba(34,197,94,0.25) 4px 0px 6px inset, rgba(34,197,94,0.15) 0px 2px 6px, 4px 0 16px rgba(27,67,50,0.1)',
          }}
        >
          <div className="w-6 h-6 rounded-md shrink-0 overflow-hidden flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #2E7D32, #1B4332)' }}>
            <img src="/agdi-logo-new.webp" alt="" className="w-4 h-4 object-contain brightness-0 invert opacity-90" />
          </div>
          {parent && (
            <>
              <span className="text-[#495584] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <svg width="8" height="8" viewBox="0 0 8 8" className="shrink-0 opacity-50">
                <path d="M3 1.5L5.5 4L3 6.5" stroke="#1B4332" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </>
          )}
          <span className="text-[#1B4332] text-[13px] font-['Manrope'] font-semibold">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style V: Indigo Pulse ──
  // Uses the primary #3F51B5 indigo + #DFE9FB accent — the app's action color, feels like a notification
  if (NAV_TOAST_STYLE === 'style_v') {
    return (
      <div className="pointer-events-none absolute left-0 top-1/3 z-50" style={{
        transform: `translateX(${isEntering ? '-100%' : isExiting ? '-100%' : '0'})`,
        opacity: isEntering ? 0 : isExiting ? 0 : 1,
        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
      }}>
        <div
          className="relative flex items-center gap-2.5 pl-1.5 pr-4 py-1.5 rounded-r-xl whitespace-nowrap overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, #DFE9FB, #FFFFFF)',
            border: '1px solid #C5CAE9',
            borderLeft: '3px solid #3F51B5',
            boxShadow: '4px 0 16px rgba(63,81,181,0.12), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          <div className="w-6 h-6 rounded-md shrink-0 overflow-hidden flex items-center justify-center" style={{ background: '#3F51B5' }}>
            <img src="/agdi-logo-new.webp" alt="" className="w-4 h-4 object-contain brightness-0 invert opacity-90" />
          </div>
          {parent && (
            <>
              <span className="text-[#495584] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <svg width="8" height="8" viewBox="0 0 8 8" className="shrink-0 opacity-50">
                <path d="M3 1.5L5.5 4L3 6.5" stroke="#3F51B5" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </>
          )}
          <span className="text-[#1B4332] text-[13px] font-['Manrope'] font-semibold">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style W: Notification Badge ──
  // Uses the soft indigo #6777EF + #E8F5E9 green — the unread notification palette
  if (NAV_TOAST_STYLE === 'style_w') {
    return (
      <div className="pointer-events-none absolute left-0 top-1/3 z-50" style={{
        transform: `translateX(${isEntering ? '-100%' : isExiting ? '-100%' : '0'})`,
        opacity: isEntering ? 0 : isExiting ? 0 : 1,
        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
      }}>
        <div
          className="relative flex items-center gap-2.5 pl-1.5 pr-4 py-1.5 rounded-r-xl whitespace-nowrap overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, #E8F5E9, #FFFFFF)',
            border: '1px solid #C8E6C9',
            borderLeft: '3px solid #6777EF',
            boxShadow: '4px 0 16px rgba(103,119,239,0.12), inset 0 1px 0 rgba(255,255,255,0.8)',
          }}
        >
          <div className="w-6 h-6 rounded-full shrink-0 overflow-hidden flex items-center justify-center" style={{ background: '#6777EF' }}>
            <img src="/agdi-logo-new.webp" alt="" className="w-3.5 h-3.5 object-contain brightness-0 invert opacity-90" />
          </div>
          {parent && (
            <>
              <span className="text-[#495584] text-[11px] font-['Manrope'] font-medium">{parent}</span>
              <svg width="8" height="8" viewBox="0 0 8 8" className="shrink-0 opacity-50">
                <path d="M3 1.5L5.5 4L3 6.5" stroke="#6777EF" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </>
          )}
          <span className="text-[#1B4332] text-[13px] font-['Manrope'] font-semibold">{label}</span>
        </div>
      </div>
    )
  }

  // ── Style X: Sidebar Gradient Body ──
  // Uses the sidebar's own gradient — adapts to dark mode with the slate palette
  if (NAV_TOAST_STYLE === 'style_x') {
    // Dark mode colors (from the app's dark theme: slate scale + green-400/indigo-400 accents)
    const darkBg = 'linear-gradient(135deg, #1e293b, #1e293b, #334155)'
    const darkBorder = '#334155'
    const darkLeftAccent = '#4ade80'
    const darkShadow = '4px 0 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.04)'
    const darkChevron = '#4ade80'
    const darkParentText = '#94a3b8'
    const darkLabelText = '#4ade80'
    const darkSepColor = '#94a3b8'

    // Light mode colors (sidebar's own gradient)
    const lightBg = 'linear-gradient(135deg, #F7FBF8, #EAF5EC, #D6EDDC)'
    const lightBorder = '#D4E3D9'
    const lightLeftAccent = '#2E7D32'
    const lightShadow = '4px 0 12px rgba(27,67,50,0.08), inset 0 1px 0 rgba(255,255,255,0.6)'
    const lightChevron = '#2E7D32'
    const lightParentText = '#545454'
    const lightLabelText = '#1B4332'
    const lightSepColor = '#545454'

    return (
      <div className="pointer-events-none absolute left-0 top-1/3 z-50" style={{
        transform: `translateX(${isEntering ? '-100%' : isExiting ? '-100%' : '0'})`,
        opacity: isEntering ? 0 : isExiting ? 0 : 1,
        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
      }}>
        <div
          className="relative flex items-center gap-2 pl-3 pr-4 py-1.5 rounded-r-xl whitespace-nowrap overflow-hidden"
          style={{
            background: isDark ? darkBg : lightBg,
            border: `1px solid ${isDark ? darkBorder : lightBorder}`,
            borderLeft: `3px solid ${isDark ? darkLeftAccent : lightLeftAccent}`,
            boxShadow: isDark ? darkShadow : lightShadow,
          }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" className="shrink-0" style={{ opacity: isDark ? 0.7 : 0.6 }}>
            <path d="M5 2.5L9.5 7L5 11.5" stroke={isDark ? darkChevron : lightChevron} strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          {parent && (
            <>
              <span className="text-[11px] font-['Manrope'] font-medium" style={{ color: isDark ? darkParentText : lightParentText }}>{parent}</span>
              <svg width="8" height="8" viewBox="0 0 8 8" className="shrink-0" style={{ opacity: isDark ? 0.4 : 0.4 }}>
                <path d="M3 1.5L5.5 4L3 6.5" stroke={isDark ? darkSepColor : lightSepColor} strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </>
          )}
          <span className="text-[13px] font-['Manrope'] font-semibold" style={{ color: isDark ? darkLabelText : lightLabelText }}>{label}</span>
        </div>
      </div>
    )
  }

  return null
}

export default NavToast
