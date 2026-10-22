// @vitest-environment node
import { describe, expect, it } from 'vitest'
import { renderGuidePage, renderPrivacyShell } from './staticGuide.ts'
import type { GuidePageInput } from './staticGuide.ts'
import type { ShotMeta } from '../shotMeta.ts'

const UNIVERSITY_LINKS = [
  'https://www.uni-osnabrueck.de/datenschutzerklaerung',
  'https://www.uni-osnabrueck.de/impressum',
  'https://www.uni-osnabrueck.de/barrierefreiheit',
]

const LOGO = '<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M0 0h10v10z"/></svg>\n'

// Same marker as the Task 12 drawer test: x 100 of 1000 px wide is left:10%.
const META: ShotMeta = { width: 1000, height: 300, marks: [{ n: 2, x: 100, y: 30, w: 200, h: 60 }] }

const UPLOAD_MD = `# Hochladen

Schreiben Sie an [{{contact_email}}](mailto:{{contact_email}}). Gelöscht nach {{retention_days}} Tagen.

![Die Seite „Hochladen“](shots/upload.png)

1. Die Einstellungen.
2. **Transkribieren** startet die Transkription.

## Seite verlassen

![Ablauf](./assets/main-flow.svg)

\`\`\`
curl -d '{"model": "{{default_model}}"}'
\`\`\`

> **Große Dateien.** Lassen Sie den Tab geöffnet.

| Feld | Bedeutung |
| --- | --- |
| \`file_id\` | Pflicht. |
`

const ANALYSIS_MD = `# Analyse

## Seite verlassen

Text.
`

function input(lang: 'de' | 'en', shotMeta: (id: string) => ShotMeta | undefined = (id) => (id === 'upload' ? META : undefined)): GuidePageInput {
  return {
    lang,
    sections: [
      { id: 'upload', tocLabel: lang === 'de' ? 'Hochladen' : 'Upload', markdown: UPLOAD_MD },
      { id: 'analysis', tocLabel: lang === 'de' ? 'Analyse' : 'Analysis', markdown: ANALYSIS_MD, feature: 'llm' },
    ],
    shotMeta,
    logoSvg: LOGO,
    builtOn: '2026-10-22',
  }
}

/** What the backend does (Task 15): drop disabled blocks entirely, keep only the content of enabled ones. */
function applyFeatures(html: string, enabled: Record<string, boolean>): string {
  return html.replace(/<!--tw-feature:(\w+)-->([\s\S]*?)<!--\/tw-feature:\1-->/g, (_m, name: string, body: string) =>
    enabled[name] ? body : '',
  )
}

function absoluteUrls(html: string): string[] {
  return [...html.matchAll(/https?:\/\/[^\s"'<>)]+/g)].map((m) => m[0])
}

const de = renderGuidePage(input('de'))
const en = renderGuidePage(input('en'))

describe('renderGuidePage: feature blocks', () => {
  it('wraps the gated section and its TOC entry in tw-feature markers', () => {
    expect(de).toMatch(/<!--tw-feature:llm-->\s*<section id="analysis">[\s\S]*?<\/section>\s*<!--\/tw-feature:llm-->/)
    expect(de).toMatch(/<!--tw-feature:llm-->\s*<li><a href="#analysis">Analyse<\/a><\/li>\s*<!--\/tw-feature:llm-->/)
    expect(de).not.toMatch(/<!--tw-feature:\w+-->\s*<section id="upload">/)
  })

  it('removes the section, its TOC entry and its empty group cleanly when the feature is off', () => {
    const off = applyFeatures(de, { llm: false, privacy: false })
    expect(off).not.toContain('analysis')
    expect(off).not.toContain('KI-Funktionen')
    expect(off).not.toContain('tw-feature')
    expect(off).toContain('<section id="upload">')
    expect(off).toContain('<a href="#upload">Hochladen</a>')
    expect(off).not.toContain('datenschutz/')
  })

  it('keeps everything but the markers when the feature is on', () => {
    const on = applyFeatures(de, { llm: true, privacy: true })
    expect(on).toContain('<section id="analysis">')
    expect(on).toContain('<a href="#analysis">Analyse</a>')
    expect(on).toContain('KI-Funktionen')
    expect(on).toContain('href="datenschutz/"')
    expect(on).not.toContain('tw-feature')
  })
})

describe('renderGuidePage: settings', () => {
  it('turns placeholders into sentinels in link text and href', () => {
    expect(de).toContain('<a href="mailto:__TW_SETTING_contact_email__">__TW_SETTING_contact_email__</a>')
  })

  it('keeps sentinels literal instead of reading their underscores as emphasis', () => {
    expect(de).toContain('Gelöscht nach __TW_SETTING_retention_days__ Tagen.')
    expect(de).not.toMatch(/<(strong|em)>TW_SETTING/)
    expect(de).not.toContain('{{')
  })

  it('fills sentinels inside code blocks too', () => {
    expect(de).toMatch(/<code>[^<]*"model": "__TW_SETTING_default_model__"[^<]*<\/code>/)
  })

  it('shows the app version and the build date in the masthead', () => {
    expect(de).toContain('__TW_SETTING_app_version__')
    expect(de).toContain('<time datetime="2026-10-22">22. Oktober 2026</time>')
    expect(en).toContain('<time datetime="2026-10-22">22 October 2026</time>')
  })
})

describe('renderGuidePage: headings', () => {
  it('shifts headings down one level and prefixes their ids with the section id', () => {
    expect(de).toContain('<h2 id="upload--hochladen">Hochladen</h2>')
    expect(de).toContain('<h3 id="upload--seite-verlassen">Seite verlassen</h3>')
    expect(de).toContain('<h3 id="analysis--seite-verlassen">Seite verlassen</h3>')
    expect(de).not.toMatch(/<h1 id=/)
  })

  it('anchors each section on its bare section id', () => {
    expect(de).toContain('<section id="upload">')
    expect(de).toContain('<a href="#upload">Hochladen</a>')
  })
})

describe('renderGuidePage: shots and assets', () => {
  it('renders a shot paragraph as a figure with marker overlays', () => {
    expect(de).not.toMatch(/<p>\s*<figure/)
    expect(de).toContain('<figure class="shot">')
    expect(de).toContain('<a class="shotbox" href="static/shots/de/upload.png">')
    expect(de).toContain('<img src="static/shots/de/upload.png" width="1000" height="300" alt="Die Seite „Hochladen“">')
    expect(de).toContain('<span class="mark" style="left:10%;top:10%;width:20%;height:20%" aria-hidden="true"><i>2</i></span>')
  })

  it('points asset images at static/assets', () => {
    expect(de).toContain('src="static/assets/main-flow.svg"')
    expect(de).not.toContain('./assets/')
  })

  it('uses ../static/ on the English page', () => {
    expect(en).toContain('href="../static/guide.css"')
    expect(en).toContain('src="../static/shots/en/upload.png"')
    expect(en).toContain('src="../static/assets/main-flow.svg"')
    expect(en).not.toMatch(/(src|href)="static\//)
  })

  it('fails the build when a shot has no recorded markers', () => {
    expect(() => renderGuidePage(input('de', () => undefined))).toThrow(/upload/)
  })
})

describe('renderGuidePage: links and page frame', () => {
  it('links the language switch and the app', () => {
    expect(de).toContain('<html lang="de">')
    expect(en).toContain('<html lang="en">')
    expect(de).toMatch(/<a href="en\/" hreflang="en" lang="en">English<\/a>/)
    expect(en).toMatch(/<a href="\.\.\/" hreflang="de" lang="de">Deutsch<\/a>/)
    expect(de).toMatch(/<a class="cta" href="\.\.\/">Direkt zu transkribierBAR/)
    expect(en).toMatch(/<a class="cta" href="\.\.\/\.\.\/">Open transkribierBAR/)
  })

  it('has the contact, the gated privacy link and the three university links in the footer', () => {
    expect(de).toMatch(/<footer[\s\S]*mailto:__TW_SETTING_contact_email__[\s\S]*<\/footer>/)
    expect(de).toMatch(/<!--tw-feature:privacy--><li><a href="datenschutz\/">Datenschutzhinweise<\/a><\/li><!--\/tw-feature:privacy-->/)
    expect(en).toMatch(/<!--tw-feature:privacy--><li><a href="privacy\/">Privacy notice<\/a><\/li><!--\/tw-feature:privacy-->/)
    for (const url of UNIVERSITY_LINKS) {
      expect(de).toContain(`<a href="${url}" target="_blank" rel="noopener">`)
    }
  })

  it('has a skip link, a labelled TOC and the brand name with BAR in the accent span', () => {
    expect(de).toContain('<a class="skip" href="#main">')
    expect(de).toContain('<main id="main">')
    expect(de).toContain('<nav class="toc" aria-label="Inhalt">')
    expect(de).toContain('<h1>transkribier<span class="bar">BAR</span></h1>')
    expect(de).toContain('aria-hidden="true"')
  })

  it('groups the TOC like the mockup', () => {
    const page = renderGuidePage({ ...input('de'), sections: [
      { id: 'about', tocLabel: 'Über', markdown: '# Über\n' },
      { id: 'refinement', tocLabel: 'Verfeinerung', markdown: '# Verfeinerung\n', feature: 'llm' },
      { id: 'format-viewer', tocLabel: 'Formatansicht', markdown: '# Formatansicht\n' },
      { id: 'presets', tocLabel: 'Voreinstellungen', markdown: '# Voreinstellungen\n' },
    ] })
    const toc = page.slice(page.indexOf('<nav class="toc"'), page.indexOf('</nav>', page.indexOf('<nav class="toc"')))
    const order = [...toc.matchAll(/class="grp">([^<]+)<|href="#([\w-]+)"/g)].map((m) => m[1] ?? m[2])
    expect(order).toEqual(['Überblick', 'about', 'Transkribieren', 'format-viewer', 'KI-Funktionen', 'refinement', 'Weiteres', 'presets'])
    // The body follows the TOC.
    const body = [...page.matchAll(/<section id="([\w-]+)">/g)].map((m) => m[1])
    expect(body).toEqual(['about', 'format-viewer', 'refinement', 'presets'])
  })

  it('makes no third-party references and has no script', () => {
    for (const page of [de, en]) {
      expect(page).not.toContain('<script')
      for (const url of absoluteUrls(page)) expect(UNIVERSITY_LINKS).toContain(url)
    }
  })
})

describe('renderPrivacyShell', () => {
  const pde = renderPrivacyShell('de', LOGO, '2026-10-22')
  const pen = renderPrivacyShell('en', LOGO, '2026-10-22')

  it('carries the notice sentinels', () => {
    expect(pde).toContain('<article class="notice" lang="__TW_NOTICE_LANG__">__TW_PRIVACY_NOTICE__</article>')
    expect(pen).toContain('__TW_PRIVACY_NOTICE__')
  })

  it('resolves its links from one or two levels below the guide', () => {
    expect(pde).toContain('<html lang="de">')
    expect(pde).toContain('href="../static/guide.css"')
    expect(pen).toContain('href="../../static/guide.css"')
    expect(pde).toMatch(/<a href="\.\.\/en\/privacy\/" hreflang="en" lang="en">English<\/a>/)
    expect(pen).toMatch(/<a href="\.\.\/\.\.\/datenschutz\/" hreflang="de" lang="de">Deutsch<\/a>/)
    expect(pde).toMatch(/<a class="cta" href="\.\.\/\.\.\/">/)
    expect(pen).toMatch(/<a class="cta" href="\.\.\/\.\.\/\.\.\/">/)
    expect(pde).toContain('<a href="../">')
    expect(pen).toContain('<a href="../">')
  })

  it('has the footer links and no third-party references', () => {
    for (const page of [pde, pen]) {
      expect(page).not.toContain('<script')
      expect(page).toContain('mailto:__TW_SETTING_contact_email__')
      for (const url of absoluteUrls(page)) expect(UNIVERSITY_LINKS).toContain(url)
      for (const url of UNIVERSITY_LINKS) expect(page).toContain(url)
    }
  })
})
