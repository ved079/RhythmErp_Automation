'use client';

interface NavToastProps {
  label: string;
  parent?: string | null;
}

export function NavToast({ label, parent }: NavToastProps) {
  return (
    <div
      className={`pointer-events-none absolute top-3 left-1/2 z-50 transition-all duration-300 ease-out`}
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
  );
}
