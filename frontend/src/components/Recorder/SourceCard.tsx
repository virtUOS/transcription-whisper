import type { ReactNode } from 'react'

interface SourceCardProps {
  icon: ReactNode
  label: string
  enabled: boolean
  onToggle: (enabled: boolean) => void
  disabled?: boolean
  disabledReason?: string
  recording?: boolean
  children?: ReactNode
}

export function SourceCard({
  icon,
  label,
  enabled,
  onToggle,
  disabled = false,
  disabledReason,
  recording = false,
  children,
}: SourceCardProps) {
  const interactive = !disabled && !recording
  const effectiveOn = !disabled && enabled

  return (
    <div
      className={`rounded-lg border p-3 transition-colors ${
        effectiveOn
          ? 'border-blue-600/60 bg-blue-950/10'
          : 'border-gray-700 bg-gray-800/40'
      } ${disabled ? 'opacity-50' : ''}`}
    >
      <div className="flex items-center justify-between gap-3 min-w-0">
        <div className="flex items-center gap-3 min-w-0">
          <span className="w-7 h-7 rounded-md bg-gray-700/70 inline-flex items-center justify-center text-sm shrink-0">
            {icon}
          </span>
          <span className="font-medium text-gray-100 truncate">{label}</span>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={effectiveOn}
          aria-label={label}
          disabled={!interactive}
          onClick={() => onToggle(!enabled)}
          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors shrink-0 ${
            effectiveOn ? 'bg-blue-600' : 'bg-gray-600'
          } ${interactive ? '' : 'cursor-not-allowed'}`}
        >
          <span
            className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
              effectiveOn ? 'translate-x-[18px]' : 'translate-x-[2px]'
            }`}
          />
        </button>
      </div>
      {disabled && disabledReason && (
        <p className="mt-2 text-xs text-gray-500">{disabledReason}</p>
      )}
      {!disabled && enabled && children && (
        <div className="mt-3">{children}</div>
      )}
    </div>
  )
}
