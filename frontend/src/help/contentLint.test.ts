/// <reference types="node" />
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { sections } from './sectionList'
import type { HelpSectionId } from './sectionList'
import { GENDERED_DE, GENDERED_EN } from '../i18n/neutral'

/** Every section is rewritten and checked against the code, so all of them are linted. */
const LINTED: HelpSectionId[] = sections.map((s) => s.id)

/** German help addresses the reader as "Sie", never "du". */
const INFORMAL_DE = /\b(du|dich|dir|dein\w*)\b/i
/** Access routes left out by decision; the guide names only the direct URL. */
const OUT_OF_SCOPE = /KI-Toolbox|Stud\.IP|Lehrportal/
/** Per-host values come from placeholders, never literals. */
const LITERAL_EMAIL = /[\w.+-]+@[\w-]+\.[a-z]{2,}/i
const LITERAL_RETENTION = /\b(72|4320)\s*(Stunden|hours)\b|\b180\s*(Tagen?|days)\b/

const here = dirname(fileURLToPath(import.meta.url))

function read(lang: 'de' | 'en', id: HelpSectionId): string {
  const section = sections.find((s) => s.id === id)
  if (!section) throw new Error(`unknown section ${id}`)
  return readFileSync(join(here, lang, section.filename), 'utf8')
}

/** The matched text, so a failure names the offending word. */
function hit(text: string, pattern: RegExp): string | null {
  return pattern.exec(text)?.[0] ?? null
}

describe('help content lint', () => {
  for (const id of LINTED) {
    describe(id, () => {
      const de = read('de', id)
      const en = read('en', id)

      it('German uses "Sie" and gender-neutral terms', () => {
        expect(hit(de, GENDERED_DE), `de gendered term`).toBeNull()
        expect(hit(de, INFORMAL_DE), `de informal address`).toBeNull()
      })

      it('English uses gender-neutral pronouns', () => {
        expect(hit(en, GENDERED_EN), `en gendered pronoun`).toBeNull()
      })

      for (const [lang, text] of [['de', de], ['en', en]] as const) {
        it(`${lang} leaves out KI-Toolbox, Stud.IP and Lehrportal`, () => {
          expect(hit(text, OUT_OF_SCOPE)).toBeNull()
        })

        it(`${lang} has no literal e-mail address`, () => {
          expect(hit(text, LITERAL_EMAIL)).toBeNull()
        })

        it(`${lang} has no literal retention period`, () => {
          expect(hit(text, LITERAL_RETENTION)).toBeNull()
        })
      }
    })
  }
})
