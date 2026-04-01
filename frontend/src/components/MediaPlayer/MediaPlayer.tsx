import { useEffect, useRef, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import videojs from 'video.js'
import 'video.js/dist/video-js.css'
import { useStore } from '../../store'
import { api } from '../../api/client'
import type { Utterance } from '../../api/types'

function formatVttTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000)
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60
  const millis = ms % 1000
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(millis).padStart(3, '0')}`
}

function generateVtt(utterances: Utterance[], speakerMappings: Record<string, string>): string {
  let vtt = 'WEBVTT\n\n'
  for (const u of utterances) {
    const start = formatVttTime(u.start)
    const end = formatVttTime(u.end)
    const speaker = u.speaker ? (speakerMappings[u.speaker] || u.speaker) : ''
    const prefix = speaker ? `[${speaker}]: ` : ''
    vtt += `${start} --> ${end}\n${prefix}${u.text}\n\n`
  }
  return vtt
}

interface Props {
  fileId: string
  mediaType: string
  hasVideo: boolean
  onCollapsedChange?: (collapsed: boolean) => void
}

export function MediaPlayer({ fileId, mediaType, hasVideo, onCollapsedChange }: Props) {
  const { t } = useTranslation()
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const playerRef = useRef<ReturnType<typeof videojs> | null>(null)
  const trackRef = useRef<HTMLTrackElement | null>(null)
  const blobUrlRef = useRef<string | null>(null)
  const setCurrentTime = useStore((s) => s.setCurrentTime)
  const seekTo = useStore((s) => s.seekTo)
  const setSeekTo = useStore((s) => s.setSeekTo)
  const transcriptionResult = useStore((s) => s.transcriptionResult)
  const speakerMappings = useStore((s) => s.speakerMappings)

  const [playbackError, setPlaybackError] = useState<string | null>(null)
  const [mediaNotFound, setMediaNotFound] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  const toggleCollapsed = () => {
    const next = !collapsed
    setCollapsed(next)
    onCollapsedChange?.(next)
    const player = playerRef.current
    if (player) {
      player.audioOnlyMode(next)
    }
  }

  const mimeTypes: Record<string, string> = {
    mp4: 'video/mp4',
    webm: 'video/webm',
    mov: 'video/quicktime',
    mp3: 'audio/mpeg',
    wav: 'audio/wav',
    m4a: 'audio/mp4',
    aac: 'audio/aac',
    opus: 'audio/opus',
    ogg: 'audio/ogg',
  }
  const mediaUrl = api.getMediaUrl(fileId)

  useEffect(() => {
    if (!videoRef.current) return

    const player = videojs(videoRef.current, {
      controls: true,
      responsive: true,
      fluid: true,
      sources: [{
        src: mediaUrl,
        type: mimeTypes[mediaType] || 'audio/mpeg',
      }],
      ...(hasVideo ? {} : { audioOnlyMode: true, height: 50 }),
    })

    player.on('timeupdate', () => {
      setCurrentTime(Math.floor(player.currentTime()! * 1000))
    })

    let triedFallback = false
    player.on('error', () => {
      const error = player.error()
      const isNotFound = error?.code === 4 // MEDIA_ERR_SRC_NOT_SUPPORTED (covers 404)

      if (!triedFallback) {
        triedFallback = true
        player.src({ src: api.getMediaFallbackUrl(fileId), type: 'audio/mpeg' })
        if (hasVideo) {
          player.audioOnlyMode(true)
        }
      } else {
        // Both sources failed — check if file is missing vs unsupported
        if (isNotFound) {
          setMediaNotFound(true)
          setPlaybackError(t('player.mediaNotFound'))
        } else {
          setPlaybackError(t('player.playbackFailed'))
        }
        // Don't dispose here — let useEffect cleanup handle it.
        // Disposing removes the <video> DOM node, which causes React
        // reconciliation to crash with removeChild errors.
      }
    })

    playerRef.current = player
    return () => {
      player.dispose()
      if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current)
    }
  }, [fileId, mediaType, hasVideo, mediaUrl, setCurrentTime])

  // Generate and update captions track reactively from store data
  const vttContent = useMemo(() => {
    if (!hasVideo || collapsed || !transcriptionResult?.utterances?.length) return null
    return generateVtt(transcriptionResult.utterances, speakerMappings)
  }, [hasVideo, collapsed, transcriptionResult?.utterances, speakerMappings])

  useEffect(() => {
    const player = playerRef.current
    if (!player || !hasVideo) return

    player.ready(() => {
      // Always remove old track first
      if (trackRef.current) {
        player.removeRemoteTextTrack(trackRef.current as unknown as ReturnType<typeof player.addRemoteTextTrack>)
        trackRef.current = null
      }
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current)
        blobUrlRef.current = null
      }

      if (!vttContent) return

      // Create new blob URL and track
      const blob = new Blob([vttContent], { type: 'text/vtt' })
      const url = URL.createObjectURL(blob)
      blobUrlRef.current = url

      const trackEl = player.addRemoteTextTrack({
        kind: 'captions',
        srclang: 'auto',
        label: 'Subtitles',
        src: url,
        default: false,
      }, false)

      trackRef.current = trackEl as unknown as HTMLTrackElement
    })
  }, [vttContent, hasVideo])

  useEffect(() => {
    if (seekTo !== null && playerRef.current) {
      playerRef.current.currentTime(seekTo / 1000)
      if (playerRef.current.paused()) {
        playerRef.current.play()
      }
      setSeekTo(null)
    }
  }, [seekTo, setSeekTo])

  const handleDownload = () => {
    const a = document.createElement('a')
    a.href = mediaUrl
    a.download = ''
    a.click()
  }

  return (
    <div className={`mx-6 my-2 ${hasVideo && !collapsed ? 'flex flex-col items-center' : hasVideo ? '' : 'max-h-16'}`}>
      {playbackError && (
        <div className="p-4 bg-gray-800 rounded-lg border border-gray-700 text-center">
          <p className="text-gray-400 text-sm">{playbackError}</p>
          {!mediaNotFound && (
            <button
              onClick={handleDownload}
              className="mt-2 px-3 py-1 text-sm text-blue-400 hover:text-blue-300 transition-colors"
            >
              {t('player.download')}
            </button>
          )}
        </div>
      )}
      {hasVideo && !playbackError && (
        <div className="flex justify-end w-full px-1">
          <button
            onClick={toggleCollapsed}
            className="text-xs text-gray-400 hover:text-white transition-colors py-1"
          >
            {collapsed ? t('player.showVideo') : t('player.minimize')}
          </button>
        </div>
      )}
      {/* Keep <video> in DOM always so video.js dispose doesn't race with React */}
      <div data-vjs-player className={`${hasVideo && !collapsed ? 'w-full overflow-hidden' : ''} ${playbackError ? 'hidden' : ''} ${collapsed ? 'max-h-12' : ''}`}>
        <video ref={videoRef} className="video-js vjs-theme-city" />
      </div>
      {!playbackError && (
        <button
          onClick={handleDownload}
          className="mt-2 px-3 py-1 text-sm text-gray-400 hover:text-white transition-colors"
        >
          {t('player.download')}
        </button>
      )}
    </div>
  )
}
