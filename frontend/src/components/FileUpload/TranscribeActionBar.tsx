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
  const baseColor =
    variant === 'pending'
      ? 'bg-amber-600 hover:bg-amber-500'
      : 'bg-blue-600 hover:bg-blue-500'

  return (
    <div className="px-6 py-3">
      <button
        type="button"
        onClick={onClick}
        disabled={disabled || submitting}
        title={disabled && disabledReason ? disabledReason : undefined}
        className={`w-full px-6 py-3 text-white text-sm font-medium rounded-lg transition-colors ${baseColor} disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2`}
      >
        {submitting && (
          <span className="inline-block h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        )}
        {label}
      </button>
    </div>
  )
}
