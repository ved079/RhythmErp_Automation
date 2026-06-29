import Image from 'next/image'
import Spinner from './Spinner'

export default function LoadingCard() {
  return (
    <div className="h-screen flex items-center justify-center bg-[#F1F2F7] dark:bg-gray-900">
      <div className="flex flex-col items-center gap-3">
        <Image src="/agdi-logo-new.webp" alt="AgDi Automation" width={80} height={36} className="object-contain animate-pulse" />
        <Spinner size={20} />
      </div>
    </div>
  )
}
