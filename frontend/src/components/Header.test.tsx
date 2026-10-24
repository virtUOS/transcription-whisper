import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { useStore } from '../store'
import { useBeforeUnloadWarning } from '../hooks/useBeforeUnloadWarning'
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

describe('Header logout with something at stake', () => {
  function Harness() {
    useBeforeUnloadWarning()
    return <Header />
  }

  function setup(confirmAnswer: boolean) {
    const unloadEvents: BeforeUnloadEvent[] = []
    // Chromium fires beforeunload synchronously inside the href assignment; mimic that.
    vi.stubGlobal('location', {
      set href(_url: string) {
        const e = new Event('beforeunload', { cancelable: true }) as BeforeUnloadEvent
        window.dispatchEvent(e)
        unloadEvents.push(e)
      },
    })
    vi.spyOn(window, 'confirm').mockReturnValue(confirmAnswer)
    useStore.getState().reset()
    useStore.setState({ config: { logout_url: '/logout' } as never })
    // An uploaded recording that was not submitted: confirmLeave changes no state, so the
    // guard stays armed and only allowNextUnload keeps the browser quiet.
    useStore.setState({
      currentView: 'record',
      file: { id: 'f1', original_filename: 'r.webm', file_size: 1 } as never,
    })
    render(<Harness />)
    return unloadEvents
  }

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
    useStore.getState().reset()
  })

  it('does not show the browser prompt after the user confirmed the logout', () => {
    const events = setup(true)
    fireEvent.click(screen.getAllByText(/log ?out|abmelden/i)[0])
    expect(events).toHaveLength(1)
    expect(events[0].defaultPrevented).toBe(false)
  })

  it('keeps the guard armed when the logout is declined', () => {
    const events = setup(false)
    fireEvent.click(screen.getAllByText(/log ?out|abmelden/i)[0])
    expect(events).toHaveLength(0)
    const e = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(e)
    expect(e.defaultPrevented).toBe(true)
  })
})
