import { useEffect, useState, useCallback } from 'react'

export type DevicePermission = 'prompt' | 'granted' | 'denied'
export type DeviceKind = 'mic' | 'camera'

const permissionName: Record<DeviceKind, PermissionName> = {
  mic: 'microphone' as PermissionName,
  camera: 'camera' as PermissionName,
}

export async function queryDevicePermission(kind: DeviceKind): Promise<DevicePermission> {
  if (!navigator.permissions?.query) return 'prompt'
  try {
    const status = await navigator.permissions.query({ name: permissionName[kind] })
    return status.state as DevicePermission
  } catch {
    // Older Safari throws TypeError for microphone/camera names
    return 'prompt'
  }
}

export function inferFromError(err: unknown): DevicePermission | null {
  if (err instanceof DOMException && err.name === 'NotAllowedError') return 'denied'
  return null
}

export function useDevicePermission(kind: DeviceKind): {
  state: DevicePermission
  refresh: () => void
} {
  const [state, setState] = useState<DevicePermission>('prompt')

  const refresh = useCallback(() => {
    queryDevicePermission(kind).then(setState)
  }, [kind])

  useEffect(() => {
    let cancelled = false
    let statusRef: PermissionStatus | null = null
    const handler = () => {
      if (!cancelled && statusRef) setState(statusRef.state as DevicePermission)
    }

    async function init() {
      if (!navigator.permissions?.query) {
        setState('prompt')
        return
      }
      try {
        const status = await navigator.permissions.query({ name: permissionName[kind] })
        if (cancelled) return
        setState(status.state as DevicePermission)
        statusRef = status
        status.addEventListener('change', handler)
      } catch {
        if (!cancelled) setState('prompt')
      }
    }

    init()
    return () => {
      cancelled = true
      if (statusRef) statusRef.removeEventListener('change', handler)
    }
  }, [kind])

  return { state, refresh }
}
