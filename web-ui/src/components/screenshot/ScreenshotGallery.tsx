'use client'

import React, { useCallback, useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  Camera,
  ChevronLeft,
  ChevronRight,
  Columns,
  Download,
  SlidersHorizontal,
  ZoomIn,
  ZoomOut,
  X,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

// ─── Types ──────────────────────────────────────────────

export interface ScreenshotEntry {
  id: string
  src: string // base64 data URL or URL
  testName: string
  timestamp: string
  moduleName?: string
  status?: 'passed' | 'failed' | 'error'
}

// ─── Helpers ────────────────────────────────────────────

function ensureDataUrl(src: string): string {
  if (src.startsWith('data:')) return src
  if (src.startsWith('http')) return src
  return `data:image/png;base64,${src}`
}

function formatTimestamp(ts: string): string {
  try {
    const d = new Date(ts)
    if (isNaN(d.getTime())) return ts
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return ts
  }
}

function statusColor(status?: string): string {
  switch (status) {
    case 'passed':
      return 'bg-[#22C55E] text-white'
    case 'failed':
      return 'bg-[#F44336] text-white'
    case 'error':
      return 'bg-orange-500 text-white'
    default:
      return 'bg-muted text-muted-foreground'
  }
}

// ─── Component 1: ScreenshotGallery ─────────────────────

interface ScreenshotGalleryProps {
  screenshots: ScreenshotEntry[]
  onRefresh?: () => void
  loading?: boolean
}

export function ScreenshotGallery({ screenshots, onRefresh, loading }: ScreenshotGalleryProps) {
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null)
  const [lightboxKey, setLightboxKey] = useState(0)

  const openLightbox = (index: number) => {
    setLightboxIndex(index)
    setLightboxKey((k) => k + 1)
  }
  const closeLightbox = () => setLightboxIndex(null)

  // Loading skeleton
  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">Screenshots</h3>
          <Skeleton className="h-9 w-24" />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="aspect-[4/3] w-full rounded-lg" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Empty state
  if (screenshots.length === 0) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">Screenshots</h3>
          {onRefresh && (
            <Button variant="outline" size="sm" onClick={onRefresh}>
              Refresh
            </Button>
          )}
        </div>
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <Camera className="size-12 mb-3 opacity-40" />
          <p className="text-sm font-medium">No screenshots captured yet</p>
          <p className="text-xs mt-1">Screenshots will appear here after test runs</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-foreground">
          Screenshots
          <span className="ml-2 text-sm font-normal text-muted-foreground">
            ({screenshots.length})
          </span>
        </h3>
        {onRefresh && (
          <Button variant="outline" size="sm" onClick={onRefresh}>
            Refresh
          </Button>
        )}
      </div>

      <div className="max-h-[600px] overflow-y-auto pr-1 custom-scrollbar">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {screenshots.map((entry, index) => (
            <button
              key={entry.id}
              type="button"
              onClick={() => openLightbox(index)}
              className="group text-left rounded-lg border border-border bg-card overflow-hidden transition-all duration-200 hover:scale-[1.02] hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-[#3F51B5]/50"
            >
              <div className="aspect-[4/3] w-full overflow-hidden bg-muted">
                <img
                  src={ensureDataUrl(entry.src)}
                  alt={`Screenshot: ${entry.testName}`}
                  className="size-full object-cover transition-transform duration-200 group-hover:scale-105"
                  loading="lazy"
                />
              </div>
              <div className="p-2.5 space-y-1">
                <div className="flex items-start gap-1.5">
                  <p className="text-xs font-medium text-foreground truncate flex-1">
                    {entry.testName}
                  </p>
                  {entry.status && (
                    <Badge className={`text-[10px] px-1.5 py-0 shrink-0 ${statusColor(entry.status)}`}>
                      {entry.status}
                    </Badge>
                  )}
                </div>
                <p className="text-[10px] text-muted-foreground">
                  {formatTimestamp(entry.timestamp)}
                </p>
                {entry.moduleName && (
                  <p className="text-[10px] text-muted-foreground truncate">
                    {entry.moduleName}
                  </p>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Lightbox — key remounts component on each open */}
      <ScreenshotLightbox
        key={lightboxKey}
        open={lightboxIndex !== null}
        onClose={closeLightbox}
        screenshots={screenshots}
        initialIndex={lightboxIndex ?? 0}
      />

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: hsl(var(--border));
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: hsl(var(--muted-foreground) / 0.5);
        }
      `}</style>
    </div>
  )
}

// ─── Component 2: ScreenshotLightbox ────────────────────

interface ScreenshotLightboxProps {
  open: boolean
  onClose: () => void
  screenshots: ScreenshotEntry[]
  initialIndex?: number
}

export function ScreenshotLightbox({
  open,
  onClose,
  screenshots,
  initialIndex = 0,
}: ScreenshotLightboxProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isPanning, setIsPanning] = useState(false)
  const [showMetadata, setShowMetadata] = useState(false)
  const panStart = useRef({ x: 0, y: 0, panX: 0, panY: 0 })
  const containerRef = useRef<HTMLDivElement>(null)

  const current = screenshots[currentIndex]

  const resetZoomPan = useCallback(() => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }, [])

  const goToPrev = useCallback(() => {
    setCurrentIndex((i) => (i > 0 ? i - 1 : screenshots.length - 1))
    resetZoomPan()
  }, [screenshots.length, resetZoomPan])

  const goToNext = useCallback(() => {
    setCurrentIndex((i) => (i < screenshots.length - 1 ? i + 1 : 0))
    resetZoomPan()
  }, [screenshots.length, resetZoomPan])

  // Keyboard navigation
  useEffect(() => {
    if (!open) return
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowLeft':
          goToPrev()
          break
        case 'ArrowRight':
          goToNext()
          break
        case 'Escape':
          onClose()
          break
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, goToPrev, goToNext, onClose])

  // Click to zoom toggle
  const handleImageClick = useCallback(() => {
    if (zoom > 1) {
      setZoom(1)
      setPan({ x: 0, y: 0 })
    } else {
      setZoom(2)
    }
  }, [zoom])

  // Mouse wheel zoom
  const handleWheel = useCallback(
    (e: React.WheelEvent) => {
      e.preventDefault()
      const delta = e.deltaY > 0 ? -0.2 : 0.2
      setZoom((z) => Math.min(Math.max(1, z + delta), 5))
      if (zoom + delta <= 1) {
        setPan({ x: 0, y: 0 })
      }
    },
    [zoom]
  )

  // Pan handlers
  const handlePanStart = useCallback(
    (e: React.PointerEvent) => {
      if (zoom <= 1) return
      setIsPanning(true)
      panStart.current = {
        x: e.clientX,
        y: e.clientY,
        panX: pan.x,
        panY: pan.y,
      }
      ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
    },
    [zoom, pan]
  )

  const handlePanMove = useCallback(
    (e: React.PointerEvent) => {
      if (!isPanning) return
      const dx = e.clientX - panStart.current.x
      const dy = e.clientY - panStart.current.y
      setPan({
        x: panStart.current.panX + dx,
        y: panStart.current.panY + dy,
      })
    },
    [isPanning]
  )

  const handlePanEnd = useCallback(() => {
    setIsPanning(false)
  }, [])

  // Download
  const handleDownload = useCallback(() => {
    if (!current) return
    const link = document.createElement('a')
    link.href = ensureDataUrl(current.src)
    link.download = `${current.testName.replace(/[^a-zA-Z0-9_-]/g, '_')}_${current.id}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }, [current])

  if (!open || screenshots.length === 0) return null

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          ref={containerRef}
          className="fixed inset-0 z-[200] flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/90"
            onClick={onClose}
          />

          {/* Close button */}
          <button
            type="button"
            onClick={onClose}
            className="absolute top-4 right-4 z-10 size-10 flex items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
            aria-label="Close lightbox"
          >
            <X className="size-5" />
          </button>

          {/* Top info bar */}
          <div className="absolute top-4 left-4 right-16 z-10 flex items-center gap-3">
            <div className="bg-black/50 text-white px-3 py-1.5 rounded-lg text-sm font-medium truncate max-w-[60%]">
              {current.testName}
            </div>
            {current.status && (
              <Badge className={`text-xs ${statusColor(current.status)}`}>
                {current.status}
              </Badge>
            )}
            <div className="bg-black/50 text-white px-2 py-0.5 rounded-full text-xs">
              {currentIndex + 1} of {screenshots.length}
            </div>
          </div>

          {/* Image container */}
          <motion.div
            className="relative z-[1] flex items-center justify-center max-w-[90vw] max-h-[80vh]"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <img
              key={current.id}
              src={ensureDataUrl(current.src)}
              alt={`Screenshot: ${current.testName}`}
              className="max-w-full max-h-[80vh] object-contain select-none"
              style={{
                transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
                cursor: zoom > 1 ? (isPanning ? 'grabbing' : 'grab') : 'zoom-in',
                transition: isPanning ? 'none' : 'transform 0.2s ease',
              }}
              onClick={handleImageClick}
              onWheel={handleWheel}
              onPointerDown={handlePanStart}
              onPointerMove={handlePanMove}
              onPointerUp={handlePanEnd}
              onPointerCancel={handlePanEnd}
              draggable={false}
            />
          </motion.div>

          {/* Navigation arrows */}
          {screenshots.length > 1 && (
            <>
              <button
                type="button"
                onClick={goToPrev}
                className="absolute left-4 top-1/2 -translate-y-1/2 z-10 size-10 flex items-center justify-center rounded-full bg-white shadow-lg hover:bg-gray-100 transition-colors"
                aria-label="Previous screenshot"
              >
                <ChevronLeft className="size-5 text-gray-800" />
              </button>
              <button
                type="button"
                onClick={goToNext}
                className="absolute right-4 top-1/2 -translate-y-1/2 z-10 size-10 flex items-center justify-center rounded-full bg-white shadow-lg hover:bg-gray-100 transition-colors"
                aria-label="Next screenshot"
              >
                <ChevronRight className="size-5 text-gray-800" />
              </button>
            </>
          )}

          {/* Bottom controls */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 flex items-center gap-2">
            {/* Zoom controls */}
            <button
              type="button"
              onClick={() => {
                setZoom((z) => Math.max(1, z - 0.5))
                if (zoom - 0.5 <= 1) setPan({ x: 0, y: 0 })
              }}
              disabled={zoom <= 1}
              className="size-9 flex items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 disabled:opacity-40 transition-colors"
              aria-label="Zoom out"
            >
              <ZoomOut className="size-4" />
            </button>
            <span className="bg-black/50 text-white px-2 py-0.5 rounded-full text-xs min-w-[3rem] text-center">
              {Math.round(zoom * 100)}%
            </span>
            <button
              type="button"
              onClick={() => setZoom((z) => Math.min(5, z + 0.5))}
              disabled={zoom >= 5}
              className="size-9 flex items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 disabled:opacity-40 transition-colors"
              aria-label="Zoom in"
            >
              <ZoomIn className="size-4" />
            </button>

            <div className="w-px h-5 bg-white/20 mx-1" />

            {/* Toggle metadata */}
            <button
              type="button"
              onClick={() => setShowMetadata((v) => !v)}
              className={`size-9 flex items-center justify-center rounded-full transition-colors ${
                showMetadata ? 'bg-white/30 text-white' : 'bg-white/10 text-white hover:bg-white/20'
              }`}
              aria-label="Toggle metadata"
            >
              <Camera className="size-4" />
            </button>

            {/* Download */}
            <button
              type="button"
              onClick={handleDownload}
              className="size-9 flex items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
              aria-label="Download screenshot"
            >
              <Download className="size-4" />
            </button>
          </div>

          {/* Metadata panel */}
          <AnimatePresence>
            {showMetadata && (
              <motion.div
                className="absolute right-4 top-16 z-10 w-64 bg-black/80 backdrop-blur-sm rounded-lg border border-white/10 p-4 space-y-3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.15 }}
              >
                <h4 className="text-sm font-semibold text-white">Details</h4>
                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-white/50">Test Name</span>
                    <p className="text-white truncate">{current.testName}</p>
                  </div>
                  {current.moduleName && (
                    <div>
                      <span className="text-white/50">Module</span>
                      <p className="text-white">{current.moduleName}</p>
                    </div>
                  )}
                  <div>
                    <span className="text-white/50">Timestamp</span>
                    <p className="text-white">{formatTimestamp(current.timestamp)}</p>
                  </div>
                  {current.status && (
                    <div>
                      <span className="text-white/50">Status</span>
                      <Badge className={`ml-2 text-[10px] ${statusColor(current.status)}`}>
                        {current.status}
                      </Badge>
                    </div>
                  )}
                  <div>
                    <span className="text-white/50">ID</span>
                    <p className="text-white font-mono text-[10px]">{current.id}</p>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// ─── Component 3: ScreenshotCompare ─────────────────────

type CompareMode = 'side-by-side' | 'overlay'

interface ScreenshotCompareProps {
  left: ScreenshotEntry | null
  right: ScreenshotEntry | null
  onClose: () => void
}

export function ScreenshotCompare({ left, right, onClose }: ScreenshotCompareProps) {
  const [mode, setMode] = useState<CompareMode>('side-by-side')
  const [sliderPos, setSliderPos] = useState(50)
  const [syncZoom, setSyncZoom] = useState(1)
  const [containerWidth, setContainerWidth] = useState(0)
  const isDragging = useRef(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // Track container width via ResizeObserver
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width)
      }
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [mode])

  // Slider drag
  const handleSliderDown = useCallback((e: React.PointerEvent) => {
    isDragging.current = true
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
  }, [])

  const handleSliderMove = useCallback(
    (e: React.PointerEvent) => {
      if (!isDragging.current || !containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const x = e.clientX - rect.left
      const pct = Math.min(Math.max((x / rect.width) * 100, 5), 95)
      setSliderPos(pct)
    },
    []
  )

  const handleSliderUp = useCallback(() => {
    isDragging.current = false
  }, [])

  if (!left || !right) {
    return (
      <div className="fixed inset-0 z-[200] flex items-center justify-center">
        <div className="absolute inset-0 bg-black/80" onClick={onClose} />
        <div className="relative z-10 bg-card rounded-lg p-8 text-center">
          <p className="text-muted-foreground">Select two screenshots to compare</p>
          <Button variant="outline" size="sm" className="mt-4" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      className="fixed inset-0 z-[200] flex flex-col"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/90" onClick={onClose} />

      {/* Header */}
      <div className="relative z-10 flex items-center justify-between px-4 py-3 bg-black/60 backdrop-blur-sm border-b border-white/10">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold text-white">Screenshot Compare</h3>
          <div className="flex items-center gap-1 bg-white/10 rounded-lg p-0.5">
            <button
              type="button"
              onClick={() => setMode('side-by-side')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs transition-colors ${
                mode === 'side-by-side'
                  ? 'bg-white/20 text-white'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              <Columns className="size-3.5" />
              Side by Side
            </button>
            <button
              type="button"
              onClick={() => setMode('overlay')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs transition-colors ${
                mode === 'overlay'
                  ? 'bg-white/20 text-white'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              <SlidersHorizontal className="size-3.5" />
              Swipe
            </button>
          </div>
        </div>

        {/* Sync zoom */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              setSyncZoom((z) => Math.max(1, z - 0.25))
            }}
            disabled={syncZoom <= 1}
            className="size-7 flex items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 disabled:opacity-40 transition-colors"
            aria-label="Zoom out"
          >
            <ZoomOut className="size-3.5" />
          </button>
          <span className="text-xs text-white/70 min-w-[3rem] text-center">
            {Math.round(syncZoom * 100)}%
          </span>
          <button
            type="button"
            onClick={() => setSyncZoom((z) => Math.min(3, z + 0.25))}
            disabled={syncZoom >= 3}
            className="size-7 flex items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 disabled:opacity-40 transition-colors"
            aria-label="Zoom in"
          >
            <ZoomIn className="size-3.5" />
          </button>

          <div className="w-px h-5 bg-white/20 mx-2" />

          <button
            type="button"
            onClick={onClose}
            className="size-8 flex items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
            aria-label="Close compare"
          >
            <X className="size-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="relative z-[1] flex-1 overflow-hidden flex items-center justify-center p-4">
        {mode === 'side-by-side' ? (
          <div className="flex gap-4 h-full max-h-full w-full max-w-[95vw]">
            {/* Left panel */}
            <div className="flex-1 flex flex-col min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-medium text-white/80 bg-white/10 px-2 py-0.5 rounded">
                  Before
                </span>
                <span className="text-xs text-white/50 truncate">{left.testName}</span>
                {left.status && (
                  <Badge className={`text-[10px] ${statusColor(left.status)}`}>{left.status}</Badge>
                )}
              </div>
              <div className="flex-1 overflow-auto rounded-lg border border-white/10 bg-black/40 flex items-center justify-center">
                <img
                  src={ensureDataUrl(left.src)}
                  alt={`Before: ${left.testName}`}
                  className="max-w-full max-h-full object-contain"
                  style={{ transform: `scale(${syncZoom})`, transformOrigin: 'center' }}
                  draggable={false}
                />
              </div>
            </div>

            {/* Right panel */}
            <div className="flex-1 flex flex-col min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-medium text-white/80 bg-white/10 px-2 py-0.5 rounded">
                  After
                </span>
                <span className="text-xs text-white/50 truncate">{right.testName}</span>
                {right.status && (
                  <Badge className={`text-[10px] ${statusColor(right.status)}`}>{right.status}</Badge>
                )}
              </div>
              <div className="flex-1 overflow-auto rounded-lg border border-white/10 bg-black/40 flex items-center justify-center">
                <img
                  src={ensureDataUrl(right.src)}
                  alt={`After: ${right.testName}`}
                  className="max-w-full max-h-full object-contain"
                  style={{ transform: `scale(${syncZoom})`, transformOrigin: 'center' }}
                  draggable={false}
                />
              </div>
            </div>
          </div>
        ) : (
          /* Overlay / Swipe mode */
          <div
            ref={containerRef}
            className="relative w-full max-w-[90vw] max-h-[80vh] aspect-[4/3] rounded-lg overflow-hidden border border-white/10 select-none"
            onPointerMove={handleSliderMove}
            onPointerUp={handleSliderUp}
            onPointerCancel={handleSliderUp}
          >
            {/* Right image (behind, full) */}
            <img
              src={ensureDataUrl(right.src)}
              alt={`After: ${right.testName}`}
              className="absolute inset-0 size-full object-contain"
              style={{ transform: `scale(${syncZoom})`, transformOrigin: 'center' }}
              draggable={false}
            />

            {/* Left image (clipped) */}
            <div
              className="absolute inset-0 overflow-hidden"
              style={{ width: `${sliderPos}%` }}
            >
              <img
                src={ensureDataUrl(left.src)}
                alt={`Before: ${left.testName}`}
                className="size-full object-contain"
                style={{
                  transform: `scale(${syncZoom})`,
                  transformOrigin: 'center',
                  minWidth: containerWidth > 0 ? `${containerWidth}px` : '100%',
                }}
                draggable={false}
              />
            </div>

            {/* Slider line */}
            <div
              className="absolute top-0 bottom-0 z-10"
              style={{ left: `${sliderPos}%` }}
            >
              <div className="absolute inset-y-0 -translate-x-1/2 w-0.5 bg-white shadow-[0_0_8px_rgba(255,255,255,0.5)]" />
              <button
                type="button"
                onPointerDown={handleSliderDown}
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 size-8 rounded-full bg-white shadow-lg flex items-center justify-center cursor-ew-resize touch-none"
                aria-label="Drag slider"
              >
                <SlidersHorizontal className="size-4 text-gray-800" />
              </button>
            </div>

            {/* Labels */}
            <div className="absolute top-2 left-2 z-20 bg-black/60 text-white text-[10px] px-1.5 py-0.5 rounded">
              Before
            </div>
            <div className="absolute top-2 right-2 z-20 bg-black/60 text-white text-[10px] px-1.5 py-0.5 rounded">
              After
            </div>
          </div>
        )}
      </div>
    </motion.div>
  )
}
