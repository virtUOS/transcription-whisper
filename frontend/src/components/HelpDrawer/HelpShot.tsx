import { useRef } from 'react'
import { useTranslation } from 'react-i18next'
import type { ShotMeta } from '../../help/shotMeta'

interface HelpShotProps {
  url: string
  alt: string
  meta: ShotMeta
}

/** The screenshot with its numbered marker boxes; boxes scale with the image. */
function Overlay({ url, alt, meta, className, size }: HelpShotProps & { className: string; size: 'inline' | 'full' }) {
  const frame = size === 'inline' ? 'border-[1.5px]' : 'border-2'
  const badge = size === 'inline'
    ? '-top-2 -left-2 h-4 w-4 text-[10px]'
    : '-top-3 -left-3 h-6 w-6 text-xs'
  // Spans, not divs: the inline overlay lives inside a <button>.
  // The lightbox copy never exceeds the screenshot's natural width.
  return (
    <span
      className={size === 'full' ? 'relative mx-auto block w-full' : 'relative block'}
      style={size === 'full' ? { maxWidth: `${meta.width}px` } : undefined}
    >
      <img src={url} alt={alt} className={className} />
      {meta.marks.map((m) => (
        <span
          key={m.n}
          data-testid="shot-mark"
          className={`absolute block ${frame} border-red-500 rounded-sm pointer-events-none`}
          style={{
            left: `${(m.x / meta.width) * 100}%`,
            top: `${(m.y / meta.height) * 100}%`,
            width: `${(m.w / meta.width) * 100}%`,
            height: `${(m.h / meta.height) * 100}%`,
          }}
        >
          <span
            aria-hidden="true"
            className={`absolute ${badge} flex items-center justify-center rounded-full bg-red-500 font-bold text-white ring-2 ring-white`}
          >
            {m.n}
          </span>
        </span>
      ))}
    </span>
  )
}

export function HelpShot({ url, alt, meta }: HelpShotProps) {
  const { t } = useTranslation()
  const dialogRef = useRef<HTMLDialogElement>(null)
  return (
    <figure className="my-4">
      <button
        type="button"
        className="block w-full cursor-pointer rounded border border-gray-700 p-2 transition-colors hover:border-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        onClick={() => dialogRef.current?.showModal()}
      >
        <Overlay url={url} alt={alt} meta={meta} className="block w-full rounded" size="inline" />
      </button>
      <figcaption className="mt-1 text-center text-xs text-gray-400">{t('help.enlarge')}</figcaption>
      <dialog
        ref={dialogRef}
        onClick={(e) => { if (e.target === e.currentTarget) dialogRef.current?.close() }}
        className="backdrop:bg-black/70 bg-transparent p-4 w-[90vw] max-h-[90vh] m-auto"
      >
        <Overlay url={url} alt={alt} meta={meta} className="block w-full rounded" size="full" />
      </dialog>
    </figure>
  )
}
