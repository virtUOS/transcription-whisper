import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeSlug from 'rehype-slug'
import type { Components } from 'react-markdown'
import type { HelpSectionId } from './helpSections'
import { loadContent, assetUrls, settingValues, fillSettings, shotFor } from './helpSections'
import { HelpShot } from './HelpShot'
import { useStore } from '../../store'

interface HelpContentProps {
  sectionId: HelpSectionId
}

/**
 * Resolves a markdown image src against Vite's asset URL map.
 * Accepts relative paths like "./assets/main-flow.svg" or "/src/help/assets/main-flow.svg".
 */
function resolveAssetUrl(src: string | undefined): string | undefined {
  if (!src) return undefined
  // Normalize: strip leading "./" and make relative paths absolute from /src/help/
  let key = src
  if (key.startsWith('./')) key = '/src/help/' + key.slice(2)
  if (!key.startsWith('/')) key = '/src/help/' + key
  return assetUrls[key] ?? src
}

function LightboxImage({ src, alt, ...props }: React.ImgHTMLAttributes<HTMLImageElement>) {
  const resolved = resolveAssetUrl(typeof src === 'string' ? src : undefined)
  const dialogRef = useRef<HTMLDialogElement>(null)
  return (
    <>
      <img
        src={resolved}
        alt={alt ?? ''}
        className="my-4 w-full rounded border border-gray-700 bg-gray-800/40 p-2 cursor-pointer hover:border-gray-500 transition-colors"
        onClick={() => dialogRef.current?.showModal()}
        {...props}
      />
      <dialog
        ref={dialogRef}
        onClick={(e) => { if (e.target === e.currentTarget) dialogRef.current?.close() }}
        className="backdrop:bg-black/70 bg-transparent p-4 w-[90vw] max-h-[90vh] m-auto"
      >
        <img src={resolved} alt={alt ?? ''} className="w-full object-contain rounded bg-gray-800 p-6" />
      </dialog>
    </>
  )
}

const components: Components = {
  a: ({ href, children, ...props }) => {
    const isExternal = href?.startsWith('http://') || href?.startsWith('https://')
    if (isExternal) {
      return (
        <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 underline" {...props}>
          {children}
        </a>
      )
    }
    return (
      <a href={href} className="text-blue-400 hover:text-blue-300 underline" {...props}>
        {children}
      </a>
    )
  },
  code: ({ children, ...props }) => (
    <code className="bg-gray-800 text-amber-300 px-1 py-0.5 rounded text-sm" {...props}>
      {children}
    </code>
  ),
  pre: ({ children, ...props }) => (
    <pre className="bg-gray-800 text-gray-200 p-3 rounded text-sm overflow-x-auto" {...props}>
      {children}
    </pre>
  ),
  h1: ({ children, ...props }) => (
    <h1 className="text-2xl font-semibold text-white mt-0 mb-4" {...props}>{children}</h1>
  ),
  h2: ({ children, ...props }) => (
    <h2 className="text-lg font-semibold text-white mt-6 mb-2" {...props}>{children}</h2>
  ),
  h3: ({ children, ...props }) => (
    <h3 className="text-base font-semibold text-gray-200 mt-4 mb-2" {...props}>{children}</h3>
  ),
  p: ({ children, ...props }) => (
    <p className="text-gray-300 leading-relaxed mb-3" {...props}>{children}</p>
  ),
  ul: ({ children, ...props }) => (
    <ul className="list-disc list-inside text-gray-300 mb-3 space-y-1" {...props}>{children}</ul>
  ),
  ol: ({ children, ...props }) => (
    <ol className="list-decimal list-inside text-gray-300 mb-3 space-y-1" {...props}>{children}</ol>
  ),
  li: ({ children, ...props }) => (
    <li className="text-gray-300" {...props}>{children}</li>
  ),
  img: LightboxImage,
  table: ({ children, ...props }) => (
    <div className="overflow-x-auto my-3">
      <table className="text-sm text-gray-300 border-collapse" {...props}>{children}</table>
    </div>
  ),
  th: ({ children, ...props }) => (
    <th className="border border-gray-700 px-3 py-1 bg-gray-800 text-left font-semibold" {...props}>{children}</th>
  ),
  td: ({ children, ...props }) => (
    <td className="border border-gray-700 px-3 py-1" {...props}>{children}</td>
  ),
}

function makeComponents(lang: 'de' | 'en'): Components {
  return {
    ...components,
    img: (props) => {
      const src = typeof props.src === 'string' ? props.src : ''
      const shot = shotFor(lang, src)
      return shot ? <HelpShot url={shot.url} alt={props.alt ?? ''} meta={shot.meta} /> : <LightboxImage {...props} />
    },
  }
}

const componentsByLang = { de: makeComponents('de'), en: makeComponents('en') }

export function HelpContent({ sectionId }: HelpContentProps) {
  const { i18n, t } = useTranslation()
  const lang: 'en' | 'de' = i18n.language === 'de' ? 'de' : 'en'
  const config = useStore((s) => s.config)
  const raw = loadContent(sectionId, lang)
  const markdown = raw === null ? null : fillSettings(raw, settingValues(config, lang))
  const containerRef = useRef<HTMLDivElement>(null)

  // Scroll to top whenever the section changes so users land at the section heading.
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = 0
    }
  }, [sectionId, lang])

  if (!markdown) {
    return (
      <div ref={containerRef} className="flex-1 overflow-y-auto p-6">
        <p className="text-gray-400 italic">{t('help.missingContent')}</p>
      </div>
    )
  }

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto p-6">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSlug]} components={componentsByLang[lang]}>
        {markdown}
      </ReactMarkdown>
    </div>
  )
}
