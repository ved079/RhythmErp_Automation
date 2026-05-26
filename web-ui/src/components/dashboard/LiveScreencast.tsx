import React from 'react';

export default function LiveScreencast({ isRunning, onScreenshotReady }: { isRunning: boolean; onScreenshotReady?: (src: string, active: boolean) => void }) {
  const [imgSrc, setImgSrc] = useState<string>('')
  const [active, setActive] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!isRunning) {
      if (intervalRef.current) clearInterval(intervalRef.current)
      return
    }

    const poll = async () => {
      try {
        const res = await fetch('/api/proxy?path=screenshot')
        const data = await res.json()
        if (data.active && data.screenshot) {
          const src = `data:image/png;base64,${data.screenshot}`
          setImgSrc(src)
          setActive(true)
          onScreenshotReady?.(src, true)
        } else {
          setActive(false)
          onScreenshotReady?.('', false)
        }
      } catch {
        setActive(false)
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 1000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [isRunning])

  if (!active || !imgSrc) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center gap-3 bg-gray-900">
        <Loader2 className="size-8 text-green-400 animate-spin" />
        <p className="text-[13px] text-gray-400">Connecting to browser...</p>
        <p className="text-[11px] text-gray-600">Make sure FastAPI backend is running</p>
      </div>
    )
  }

  return (
    <div className="w-full h-full relative bg-black">
      <img
        src={imgSrc}
        alt="Live browser"
        className="w-full h-full object-contain"
      />
      <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-black/60 text-white text-[10px] px-2 py-1 rounded-full">
        <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
        LIVE
      </div>
    </div>
  )
}

// -”-”-” LIVE EXECUTION TAB (Browser view + Console) -”-”-”-”-”-”-”-”
