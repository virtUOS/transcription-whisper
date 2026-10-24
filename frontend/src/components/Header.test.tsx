import { afterEach, describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import i18n from '../i18n'
import { Header } from './Header'

describe('Header', () => {
  afterEach(() => {
    i18n.addResource(i18n.language, 'translation', 'title', 'transkribierBAR')
  })

  it('sets the trailing "BAR" of the title in the accent colour', () => {
    render(<Header />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent(/^transkribierBAR$/)
    const accent = heading.querySelector('span')
    expect(accent).toHaveTextContent(/^BAR$/)
    expect(accent).toHaveClass('text-orange-400')
  })

  it('renders a title without the "BAR" ending as plain text', () => {
    i18n.addResource(i18n.language, 'translation', 'title', 'Something else')
    render(<Header />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent(/^Something else$/)
    expect(heading.querySelector('span')).toBeNull()
  })
})
