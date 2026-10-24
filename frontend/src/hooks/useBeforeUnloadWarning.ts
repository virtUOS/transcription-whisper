import { useEffect } from 'react'
import { useStore } from '../store'

let skipNextUnload = false

/**
 * Lets the very next `beforeunload` pass without the browser prompt. Call it right before an
 * in-app navigation the user has already confirmed, so they are not asked twice.
 */
export function allowNextUnload() {
  skipNextUnload = true
  // Never leave the guard disarmed if the navigation does not happen.
  setTimeout(() => { skipNextUnload = false }, 0)
}

/**
 * Adds a `beforeunload` listener while an upload or recording is at stake so the browser
 * shows its native "leave site?" warning on tab close / refresh / external nav.
 * Modern browsers ignore custom messages and show a generic dialog.
 */
export function useBeforeUnloadWarning() {
  const atStake = useStore((s) => s.leaveReason() !== null)

  useEffect(() => {
    if (!atStake) return
    const handler = (e: BeforeUnloadEvent) => {
      if (skipNextUnload) {
        skipNextUnload = false
        return
      }
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [atStake])
}
