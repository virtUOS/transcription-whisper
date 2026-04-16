import { useEffect, useRef, useState } from 'react'

interface TranscribeActionBarProps {
  onClick: () => void
  disabled: boolean
  disabledReason?: string
  label: string
  submitting?: boolean
  variant?: 'primary' | 'pending'
}

export function TranscribeActionBar({
  onClick,
  disabled,
  disabledReason,
  label,
  submitting = false,
  variant = 'primary',
}: TranscribeActionBarProps) {
  const inlineRef = useRef<HTMLDivElement | null>(null)
  const [showSticky, setShowSticky] = useState(false)

  useEffect(() => {
    const el = inlineRef.current
    if (!el) return
    const observer = new IntersectionObserver(
      ([entry]) => setShowSticky(!entry.isIntersecting),
      { threshold: 0 },
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const button = (sticky: boolean) => {
    const baseColor =
      variant === 'pending'
        ? 'bg-amber-600 hover:bg-amber-500'
        : 'bg-blue-600 hover:bg-blue-500'
    return (
      <button
        type="button"
        onClick={onClick}
        disabled={disabled || submitting}
        title={disabled && disabledReason ? disabledReason : undefined}
        className={`w-full ${sticky ? 'max-w-[1200px] mx-auto' : ''} px-6 py-3 text-white text-sm font-medium rounded-lg transition-colors ${baseColor} disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2`}
      >
        {submitting && (
          <span className="inline-block h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        )}
        {label}
      </button>
    )
  }

  return (
    <>
      <div ref={inlineRef} className="px-6 py-3">
        {button(false)}
      </div>
      {showSticky && (
        <div
          className="fixed left-0 right-0 bottom-0 bg-gray-900/95 backdrop-blur border-t border-gray-700 shadow-[0_-4px_12px_rgba(0,0,0,0.4)] px-6 py-3"
          style={{ paddingBottom: 'calc(0.75rem + env(safe-area-inset-bottom, 0px))' }}
        >
          {button(true)}
        </div>
      )}
    </>
  )
}
