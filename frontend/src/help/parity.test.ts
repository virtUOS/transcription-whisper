/// <reference types="node" />
import { readFileSync, existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { sections } from './sectionList'
import { SETTING_KEYS, placeholdersIn } from './helpText'

const here = dirname(fileURLToPath(import.meta.url))

const pathOf = (lang: 'de' | 'en', filename: string): string => join(here, lang, filename)

const read = (lang: 'de' | 'en', filename: string): string =>
  readFileSync(pathOf(lang, filename), 'utf8')

/** Heading levels in document order, ignoring fenced code blocks. */
function outline(md: string): number[] {
  const levels: number[] = []
  let fenced = false
  for (const line of md.split('\n')) {
    if (/^\s*```/.test(line)) fenced = !fenced
    if (fenced) continue
    const m = /^(#{1,6})\s/.exec(line)
    if (m) levels.push(m[1].length)
  }
  return levels
}

function imageSrcs(md: string): string[] {
  return [...md.matchAll(/!\[[^\]]*\]\(([^)\s]+)[^)]*\)/g)].map((m) => m[1]).sort()
}

describe('help content parity', () => {
  it('has a de and en file for every section', () => {
    for (const s of sections) {
      expect(existsSync(pathOf('de', s.filename)), `de/${s.filename}`).toBe(true)
      expect(existsSync(pathOf('en', s.filename)), `en/${s.filename}`).toBe(true)
    }
  })

  it('uses the same heading outline in both languages', () => {
    for (const s of sections) {
      expect(outline(read('de', s.filename)), s.filename).toEqual(outline(read('en', s.filename)))
    }
  })

  it('references the same images in both languages', () => {
    for (const s of sections) {
      expect(imageSrcs(read('de', s.filename)), s.filename).toEqual(
        imageSrcs(read('en', s.filename)),
      )
    }
  })

  it('uses only known placeholders', () => {
    const known: readonly string[] = SETTING_KEYS
    for (const s of sections) {
      for (const lang of ['de', 'en'] as const) {
        for (const key of placeholdersIn(read(lang, s.filename))) {
          expect(known, `${lang}/${s.filename}: ${key}`).toContain(key)
        }
      }
    }
  })
})
