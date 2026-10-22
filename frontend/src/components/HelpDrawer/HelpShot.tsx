import { useRef } from 'react'
import type { ShotMeta } from '../../help/shotMeta'

interface HelpShotProps {
  url: string
  alt: string
  meta: ShotMeta
}

/** The screenshot with its numbered marker boxes; boxes scale with the image. */
function Overlay({ url, alt, meta, className }: HelpShotProps & { className: string }) {
  return (
    <div className="relative">
      <img src={url} alt={alt} className={className} />
      {meta.marks.map((m) => (
        <div
          key={m.n}
          data-testid="shot-mark"
          className="absolute border-2 border-red-500 rounded-sm pointer-events-none"
          style={{
            left: `${(m.x / meta.width) * 100}%`,
            top: `${(m.y / meta.height) * 100}%`,
            width: `${(m.w / meta.width) * 100}%`,
            height: `${(m.h / meta.height) * 100}%`,
          }}
        >
          <span
            aria-hidden="true"
            className="absolute -top-3 -left-3 flex h-6 w-6 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white ring-2 ring-white"
          >
            {m.n}
          </span>
        </div>
      ))}
    </div>
  )
}

export function HelpShot({ url, alt, meta }: HelpShotProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  return (
    <figure aria-label={alt} className="my-4">
      <div
        className="cursor-pointer rounded border border-gray-700 p-2 transition-colors hover:border-gray-500"
        onClick={() => dialogRef.current?.showModal()}
      >
        <Overlay url={url} alt={alt} meta={meta} className="block w-full rounded" />
      </div>
      <dialog
        ref={dialogRef}
        onClick={(e) => { if (e.target === e.currentTarget) dialogRef.current?.close() }}
        className="backdrop:bg-black/70 bg-transparent p-4 w-[90vw] max-h-[90vh] m-auto"
      >
        <Overlay url={url} alt={alt} meta={meta} className="block w-full rounded" />
      </dialog>
    </figure>
  )
}
