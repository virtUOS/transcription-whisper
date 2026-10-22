import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
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

describe('shotFor', () => {
  it('returns null for sources that are not shots or are unknown', () => {
    expect(shotFor('en', 'assets/main-flow.svg')).toBeNull()
    expect(shotFor('en', 'shots/does-not-exist.png')).toBeNull()
  })
})
