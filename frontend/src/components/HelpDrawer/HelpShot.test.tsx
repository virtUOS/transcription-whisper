import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import i18n from '../../i18n'
import { HelpShot } from './HelpShot'
import { shotFor } from './helpSections'

describe('HelpShot', () => {
  const meta = { width: 1000, height: 300, marks: [{ n: 2, x: 100, y: 30, w: 200, h: 60 }] }

  it('positions each marker box in percent of the image size', () => {
    render(<HelpShot url="/x.png" alt="Upload form" meta={meta} />)
    const badge = screen.getAllByText('2')[0]
    const box = badge.parentElement as HTMLElement
    expect(box.style.left).toBe('10%')
    expect(box.style.top).toBe('10%')
    expect(box.style.width).toBe('20%')
    expect(box.style.height).toBe('20%')
    expect(badge.getAttribute('aria-hidden')).toBe('true')
  })

  it('names the figure from the alt text', () => {
    render(<HelpShot url="/x.png" alt="Upload form" meta={meta} />)
    expect(screen.getByRole('figure', { name: 'Upload form' })).toBeTruthy()
  })
})

describe('HelpShot sizing and caption', () => {
  const meta = { width: 1000, height: 300, marks: [{ n: 2, x: 100, y: 30, w: 200, h: 60 }] }

  it('uses small badges inline and large ones in the lightbox', () => {
    const { container } = render(<HelpShot url="/x.png" alt="Upload form" meta={meta} />)
    const [inline, full] = Array.from(container.querySelectorAll('[data-testid="shot-mark"]'))
    const inlineBadge = inline.firstElementChild as HTMLElement
    const fullBadge = full.firstElementChild as HTMLElement
    expect(inlineBadge.className).toContain('h-4 w-4 text-[10px]')
    expect(inline.className).toContain('border-[1.5px]')
    expect(fullBadge.className).toContain('h-6 w-6 text-xs')
    expect(full.className).toContain('border-2')
  })

  it('renders the enlarge hint in the current language', async () => {
    await i18n.changeLanguage('en')
    const { unmount } = render(<HelpShot url="/x.png" alt="Upload form" meta={meta} />)
    expect(screen.getByText('Click to enlarge')).toBeTruthy()
    unmount()
    await i18n.changeLanguage('de')
    render(<HelpShot url="/x.png" alt="Upload form" meta={meta} />)
    expect(screen.getByText('Zum Vergrößern klicken')).toBeTruthy()
    await i18n.changeLanguage('en')
  })
})

describe('shotFor', () => {
  it('returns null for sources that are not shots or are unknown', () => {
    expect(shotFor('en', 'assets/main-flow.svg')).toBeNull()
    expect(shotFor('en', 'shots/does-not-exist.png')).toBeNull()
  })
})
