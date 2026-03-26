export type BrowserEngine = 'chromium' | 'firefox' | 'other'
export type OS = 'windows' | 'macos' | 'linux' | 'mobile' | 'other'
export type SystemAudioSupport = 'full' | 'tab-only' | 'dual-device' | 'limited' | 'unsupported'

export interface PlatformProfile {
  engine: BrowserEngine
  os: OS
}

interface NavigatorUAData {
  brands: Array<{ brand: string; version: string }>
  mobile: boolean
  platform: string
}

const getUAData = () =>
  (navigator as Navigator & { userAgentData?: NavigatorUAData }).userAgentData

function detectEngine(): BrowserEngine {
  // Modern Chromium browsers expose userAgentData with a "Chromium" brand
  const uaData = getUAData()
  if (uaData?.brands?.some((b) => b.brand === 'Chromium')) return 'chromium'

  const ua = navigator.userAgent
  // Firefox identifies itself in the UA string
  if (/Firefox\//.test(ua)) return 'firefox'
  // Fallback: Chrome/Edge in UA but not Firefox (covers older Chromium without userAgentData)
  if (/Chrome\//.test(ua) || /Edg\//.test(ua)) return 'chromium'

  return 'other'
}

function detectOS(): OS {
  const uaData = getUAData()

  // Check mobile first — mobile overrides any OS detection
  if (uaData?.mobile) return 'mobile'

  const ua = navigator.userAgent
  if (/Android|iPhone|iPad|iPod/.test(ua)) return 'mobile'
  // iPadOS 13+ spoofs as Macintosh; detect via touch capability
  if (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1) return 'mobile'

  // userAgentData.platform is the most reliable source when available
  if (uaData?.platform) {
    const p = uaData.platform.toLowerCase()
    if (p.includes('win')) return 'windows'
    if (p.includes('mac')) return 'macos'
    if (p.includes('linux')) return 'linux'
  }

  // Fallback to UA string parsing
  if (/Win/.test(ua)) return 'windows'
  if (/Mac/.test(ua)) return 'macos'
  if (/Linux/.test(ua)) return 'linux'

  return 'other'
}

export function detectPlatform(): PlatformProfile {
  return { engine: detectEngine(), os: detectOS() }
}

export function getSystemAudioSupport(profile?: PlatformProfile): SystemAudioSupport {
  const { engine, os } = profile ?? detectPlatform()

  // Mobile is always unsupported regardless of engine
  if (os === 'mobile') return 'unsupported'

  if (engine === 'chromium') {
    return os === 'windows' ? 'full' : 'tab-only'
  }

  if (engine === 'firefox') {
    return os === 'linux' ? 'dual-device' : 'limited'
  }

  return 'unsupported'
}
