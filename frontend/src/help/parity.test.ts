/// <reference types="node" />
import { readFileSync, existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { sections } from './sectionList'
import { SETTING_KEYS, placeholdersIn } from './helpText'
import { pngSize } from './pngSize'
import type { ShotMeta } from './shotMeta'

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

/** Ids of `![alt](shots/<id>.png)` references, in document order. */
function shotIds(md: string): string[] {
  return [...md.matchAll(/!\[[^\]]*\]\(shots\/([\w-]+)\.png\)/g)].map((m) => m[1])
}

/**
 * For each shot reference, the number of items in the ordered list that directly
 * follows it (blank lines allowed in between; 0 when no list follows).
 */
function listItemsAfterShots(md: string): { id: string; items: number }[] {
  const lines = md.split('\n')
  const out: { id: string; items: number }[] = []
  lines.forEach((line, i) => {
    const m = /^!\[[^\]]*\]\(shots\/([\w-]+)\.png\)\s*$/.exec(line.trim())
    if (!m) return
    let j = i + 1
    while (j < lines.length && lines[j].trim() === '') j++
    let items = 0
    for (; j < lines.length; j++) {
      const l = lines[j]
      if (/^\d+[.)]\s/.test(l)) items++
      else if (l.trim() === '' || /^\s+\S/.test(l)) continue
      else break
    }
    out.push({ id: m[1], items: items })
  })
  return out
}

describe('shot reference helpers', () => {
  const ok = '![Form](shots/upload.png)\n\n1. One\n2. Two\n   more\n\n3. Three\n\nAfter.\n'
  const bad = '![Form](shots/upload.png)\n\n1. One\n2. Two\n\nAfter.\n1. Other list\n'

  it('counts the ordered list items right after a shot', () => {
    expect(shotIds(ok)).toEqual(['upload'])
    expect(listItemsAfterShots(ok)).toEqual([{ id: 'upload', items: 3 }])
    expect(listItemsAfterShots(bad)).toEqual([{ id: 'upload', items: 2 }])
  })

  it('counts zero when no list follows', () => {
    expect(listItemsAfterShots('![x](shots/a.png)\n\nText\n')).toEqual([{ id: 'a', items: 0 }])
  })
})

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

  it('has every referenced diagram in both languages', () => {
    for (const s of sections) {
      for (const lang of ['de', 'en'] as const) {
        for (const src of imageSrcs(read(lang, s.filename)).filter((x) => x.startsWith('./assets/'))) {
          expect(src, `${lang}/${s.filename}`).toMatch(/^\.\/assets\/[\w-]+\.svg$/)
          for (const l of ['de', 'en'] as const) {
            expect(existsSync(join(here, 'assets', l, src.slice('./assets/'.length))), `${l}: ${src} (from ${lang}/${s.filename})`).toBe(true)
          }
        }
      }
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

  it('has a png and json for every referenced shot', () => {
    for (const s of sections) {
      const ids = shotIds(read('de', s.filename))
      expect(shotIds(read('en', s.filename)), s.filename).toEqual(ids)
      const counts: Record<string, number> = {}
      for (const lang of ['de', 'en'] as const) {
        for (const id of ids) {
          const base = join(here, 'shots', lang, id)
          const where = `${lang}/${id}`
          expect(existsSync(`${base}.png`), `${where}.png`).toBe(true)
          expect(existsSync(`${base}.json`), `${where}.json`).toBe(true)
          const meta = JSON.parse(readFileSync(`${base}.json`, 'utf8')) as ShotMeta
          const size = pngSize(readFileSync(`${base}.png`))
          expect(size, `${where} png size`).toEqual({ width: meta.width, height: meta.height })
          const ns = meta.marks.map((m) => m.n)
          expect(ns, `${where} mark numbers`).toEqual(ns.map((_, i) => i + 1))
          if (lang === 'de') counts[id] = ns.length
          else expect(ns.length, `${id} marks de vs en`).toBe(counts[id])
        }
        for (const { id, items } of listItemsAfterShots(read(lang, s.filename))) {
          expect(items, `${lang}/${s.filename}: list after ${id}`).toBe(counts[id])
        }
      }
    }
  })
})
