import { useEffect } from 'react'
import { useStore } from '../store'

/**
 * Adds a `beforeunload` listener while an upload is in progress so the browser
 * shows its native "leave site?" warning on tab close / refresh / external nav.
 * Modern browsers ignore custom messages and show a generic dialog.
 */
export function useBeforeUnloadWarning() {
  const uploading = useStore((s) => s.uploading)

  useEffect(() => {
    if (!uploading) return
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [uploading])
}
