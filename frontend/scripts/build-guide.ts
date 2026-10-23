// Builds the public user guide into dist/handbuch from the help markdown.
// Runs after `vite build` (see the "build" script): node scripts/build-guide.ts
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { sections } from '../src/help/sectionList.ts'
import type { ShotMeta } from '../src/help/shotMeta.ts'
import { UNIVERSITY_LINKS, renderGuidePage, renderPrivacyShell } from '../src/help/render/staticGuide.ts'
import type { GuideLang } from '../src/help/render/staticGuide.ts'

const frontendDir = resolve(import.meta.dirname, '..')
const helpDir = join(frontendDir, 'src/help')
const outDir = join(frontendDir, 'dist/handbuch')
const staticDir = join(outDir, 'static')
const LANGS = ['de', 'en'] as const

/** Latin subsets only: sans 400/600/700, serif 400/600 and serif italic 400. */
const FONTS = {
  'source-sans-3': ['latin-400-normal', 'latin-600-normal', 'latin-700-normal'],
  'source-serif-4': ['latin-400-normal', 'latin-600-normal', 'latin-400-italic'],
} as const

function write(path: string, content: string): void {
  mkdirSync(dirname(path), { recursive: true })
  writeFileSync(path, content)
}

function copy(from: string, to: string): void {
  mkdirSync(dirname(to), { recursive: true })
  copyFileSync(from, to)
}

/** Every href/src with a scheme must be mailto: or one of the university links. */
function checkUrls(page: string, html: string): void {
  const allowed: readonly string[] = Object.values(UNIVERSITY_LINKS)
  for (const [, url] of html.matchAll(/\b(?:href|src)="([^"]*)"/g)) {
    if (/^[a-z][\w+.-]*:/i.test(url) && !url.startsWith('mailto:') && !allowed.includes(url)) {
      throw new Error(`${page}: external URL ${url} is not allowed on the public guide`)
    }
  }
  if (/<script/i.test(html)) throw new Error(`${page}: <script> is not allowed on the public guide`)
}

function shotMetaFor(lang: GuideLang) {
  return (id: string): ShotMeta | undefined => {
    const base = join(helpDir, 'shots', lang, id)
    if (!existsSync(`${base}.json`) || !existsSync(`${base}.png`)) return undefined
    return JSON.parse(readFileSync(`${base}.json`, 'utf8')) as ShotMeta
  }
}

const builtOn = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Berlin' }).format(new Date())
const logoSvg = readFileSync(join(frontendDir, 'public/whisper-logo.svg'), 'utf8')

rmSync(outDir, { recursive: true, force: true })

const pages: [string, string][] = []
for (const lang of LANGS) {
  const locale = JSON.parse(readFileSync(join(frontendDir, 'src/i18n', `${lang}.json`), 'utf8')) as {
    help: { sections: Record<string, string> }
  }
  const input = sections.map((s) => {
    const tocLabel = locale.help.sections[s.id]
    if (!tocLabel) throw new Error(`src/i18n/${lang}.json has no help.sections.${s.id}`)
    const markdown = readFileSync(join(helpDir, lang, s.filename), 'utf8')
    return { id: s.id, tocLabel, markdown, feature: s.feature }
  })
  const guide = renderGuidePage({ lang, sections: input, shotMeta: shotMetaFor(lang), logoSvg, builtOn })
  pages.push([lang === 'de' ? 'index.html' : 'en/index.html', guide])
  pages.push([lang === 'de' ? 'datenschutz/index.html' : 'en/privacy/index.html', renderPrivacyShell(lang, logoSvg, builtOn)])
}

for (const [path, html] of pages) {
  checkUrls(path, html)
  write(join(outDir, path), html)
}

copy(join(helpDir, 'render/guide.css'), join(staticDir, 'guide.css'))
copy(join(frontendDir, 'public/whisper-logo.svg'), join(staticDir, 'logo.svg'))
for (const lang of LANGS) {
  for (const name of readdirSync(join(helpDir, 'assets', lang)).filter((f) => f.endsWith('.svg'))) {
    copy(join(helpDir, 'assets', lang, name), join(staticDir, 'assets', lang, name))
  }
}
// Every diagram a page references must exist in that page's language.
for (const [path, html] of pages) {
  for (const [, ref] of html.matchAll(/\bsrc="((?:\.\.\/)*static\/assets\/[^"?]+)(?:\?[^"]*)?"/g)) {
    const file = join(outDir, ref.replace(/^(?:\.\.\/)*/, ''))
    if (!existsSync(file)) throw new Error(`${path}: diagram ${ref} is missing (${file})`)
  }
}
for (const lang of LANGS) {
  for (const name of readdirSync(join(helpDir, 'shots', lang)).filter((f) => f.endsWith('.png'))) {
    copy(join(helpDir, 'shots', lang, name), join(staticDir, 'shots', lang, name))
  }
}
for (const [pkg, files] of Object.entries(FONTS)) {
  const pkgDir = join(frontendDir, 'node_modules/@fontsource', pkg)
  for (const file of files) {
    copy(join(pkgDir, 'files', `${pkg}-${file}.woff2`), join(staticDir, 'fonts', `${pkg}-${file}.woff2`))
  }
  copy(join(pkgDir, 'LICENSE'), join(staticDir, 'fonts', `${pkg}-LICENSE.txt`))
}

console.log(`[build-guide] wrote ${pages.length} pages to dist/handbuch (built on ${builtOn})`)
